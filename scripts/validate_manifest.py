#!/usr/bin/env python3
"""Validate an auto-update channel manifest and report typed refusals.

This is a **thin CLI** over ``release_lib.validate_manifest`` (reuse
contract R1/R5): every validation rule lives in ``scripts/release_lib.py``
exactly once, and this module only handles argument parsing, file
reading, exit codes, and the GitHub step-summary rendering. It must
never grow a validation rule of its own — a rule added here would be a
fork that the Rust and TypeScript consumers could not see.

Three workflow sites invoke this script, each as a one-liner:

* ``manifest-validate.yml`` — on every push to the ``releases`` branch.
* ``release.yml`` — before the generated ``beta.json`` is committed.
* ``promote.yml`` — before ``stable.json`` is committed.

Usage::

    python scripts/validate_manifest.py releases/stable.json
    python scripts/validate_manifest.py releases/*.json --summary

Exit codes:

* ``0`` — every manifest validated clean.
* ``1`` — at least one manifest was refused; each violation's typed code
  and bounded message are printed and, with ``--summary``, written to
  ``$GITHUB_STEP_SUMMARY``.
* ``2`` — invocation error: a path is missing, unreadable, or not JSON.

Observability contract (Gate 7): every refusal carries a typed code from
``release_lib``'s taxonomy — never a raw ``str(err)`` passthrough — and
no emitted line contains an absolute filesystem path. Paths are rendered
relative to the repository root, and a path outside the repository is
reduced to its basename.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Final, Protocol, runtime_checkable

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

#: Written to ``$GITHUB_STEP_SUMMARY`` when ``--summary`` is passed. The
#: workflow step summary is the operator-facing surface, so it names the
#: failing rule rather than dumping a traceback (spec §9.7).
SUMMARY_ENV_VAR: Final[str] = "GITHUB_STEP_SUMMARY"

#: Typed codes this CLI owns. Everything else comes from ``release_lib``.
#: They exist so a read/parse failure is still a coded refusal rather
#: than a bare exception string.
CODE_UNREADABLE: Final[str] = "manifest_unreadable"
CODE_NOT_JSON: Final[str] = "manifest_not_json"
CODE_NOT_OBJECT: Final[str] = "manifest_not_object"

EXIT_OK: Final[int] = 0
EXIT_REFUSED: Final[int] = 1
EXIT_INVOCATION_ERROR: Final[int] = 2

#: Upper bound on any single emitted message. Manifest content is
#: partly attacker-shaped (URLs, base64 signatures); an unbounded echo
#: into a public CI step summary is a log-injection surface.
MAX_MESSAGE_CHARS: Final[int] = 200


@runtime_checkable
class ManifestViolationLike(Protocol):
    """The violation shape ``release_lib.validate_manifest`` returns.

    Declared structurally so this CLI type-checks without importing the
    concrete class at module scope, and so the contract this script
    depends on is stated in one readable place.
    """

    @property
    def code(self) -> str:
        """Typed taxonomy code, e.g. ``unknown_channel``."""

    @property
    def message(self) -> str:
        """Bounded, path-free explanation of the refused rule."""


class _Refusal:
    """A refusal raised by this CLI itself (read / parse / shape)."""

    def __init__(self, code: str, message: str) -> None:
        self._code = code
        self._message = message

    @property
    def code(self) -> str:
        """Typed taxonomy code."""

        return self._code

    @property
    def message(self) -> str:
        """Bounded, path-free explanation."""

        return self._message


def _display_path(path: Path) -> str:
    """Return a repo-relative, absolute-path-free label for ``path``.

    An absolute path in CI output leaks the runner's directory layout
    and, worse, makes the same failure render differently on every
    machine. A path outside the repository degrades to its basename.
    """

    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


def _bound(message: str) -> str:
    """Truncate ``message`` to the emission cap, marking the elision."""

    if len(message) <= MAX_MESSAGE_CHARS:
        return message
    return message[: MAX_MESSAGE_CHARS - 1] + "…"


def _load_document(path: Path) -> tuple[object | None, _Refusal | None]:
    """Read ``path`` as JSON, returning ``(document, refusal)``.

    Exactly one element of the pair is ``None``. Read and decode errors
    become typed refusals rather than propagating an exception whose
    string would carry the absolute path.
    """

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None, _Refusal(
            CODE_UNREADABLE,
            "manifest file could not be read (missing, unreadable, or not UTF-8)",
        )
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as error:
        return None, _Refusal(
            CODE_NOT_JSON,
            f"manifest is not valid JSON at line {error.lineno} column {error.colno}",
        )
    return document, None


def _load_validator() -> Callable[[Mapping[str, object]], Iterable[ManifestViolationLike]]:
    """Import and return ``release_lib.validate_manifest`` (reuse contract R1).

    Loaded by absolute file path rather than by bare name so the CLI works
    from any working directory and without ``scripts/`` on ``sys.path`` --
    the three workflow call sites invoke it as
    ``python scripts/validate_manifest.py`` from the repo root, and
    ``manifest-validate.yml`` invokes it from a sparse checkout under
    ``.validator/``. A bare ``import release_lib`` would resolve in the
    first case and fail in the last.

    Raises ``ImportError`` when the sibling module is absent, which
    ``main`` turns into the invocation-error exit code with an explanation.
    """

    module_path = Path(__file__).resolve().parent / "release_lib.py"
    # `spec_from_file_location` happily builds a spec for a path that does
    # not exist; the failure only surfaces as FileNotFoundError at
    # exec_module time. Check first so an absent toolkit is one clear
    # ImportError rather than an OSError from inside the import machinery.
    if not module_path.is_file():
        raise ImportError(f"the release toolkit {module_path.name} is not present beside this CLI")
    spec = importlib.util.spec_from_file_location("_rytm_release_lib", module_path)
    # `spec` and `spec.loader` are Optional in the importlib contract. A
    # stock loader fills both for a real .py file, but the branch is kept
    # (and tested by stubbing the factory) so a None never propagates into
    # an AttributeError three frames deeper than the actual cause.
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load the release toolkit from {module_path.name}")
    module = importlib.util.module_from_spec(spec)
    # Register BEFORE exec_module. release_lib defines frozen slots dataclasses,
    # and dataclasses resolves ``cls.__module__`` through ``sys.modules`` while
    # building the class body — an unregistered module makes that lookup return
    # None and the import dies with ``AttributeError: 'NoneType' object has no
    # attribute '__dict__'``. Without this line every invocation of this CLI
    # crashes, taking all three manifest-validation sites with it.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(spec.name, None)
        raise
    validator = getattr(module, "validate_manifest", None)
    if validator is None:
        raise ImportError("release_lib does not export validate_manifest")
    return validator


def _violations_for(path: Path) -> list[ManifestViolationLike | _Refusal]:
    """Return every violation for one manifest path, typed and bounded."""

    document, refusal = _load_document(path)
    if refusal is not None:
        return [refusal]
    if not isinstance(document, dict):
        return [
            _Refusal(
                CODE_NOT_OBJECT,
                "manifest root must be a JSON object",
            )
        ]

    return list(_load_validator()(document))


def _render_report(
    results: Sequence[tuple[str, Sequence[ManifestViolationLike | _Refusal]]],
) -> str:
    """Render the Markdown report shared by stdout and the step summary."""

    lines: list[str] = ["## Manifest validation", ""]
    for label, violations in results:
        if not violations:
            lines.append(f"- **PASS** `{label}`")
            continue
        lines.append(f"- **FAIL** `{label}` — {len(violations)} violation(s):")
        for violation in violations:
            lines.append(f"  - `{violation.code}` — {_bound(violation.message)}")
    lines.append("")
    return "\n".join(lines)


def _write_summary(report: str) -> None:
    """Append ``report`` to the GitHub step summary when one is configured.

    Outside Actions the variable is unset and this is a no-op, so the same
    ``--summary`` invocation works locally without special-casing.
    """

    summary_path = os.environ.get(SUMMARY_ENV_VAR)
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write(report)


def _parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    """Parse the CLI arguments."""

    parser = argparse.ArgumentParser(
        prog="validate_manifest.py",
        description=(
            "Validate one or more auto-update channel manifests against the "
            "v1 schema. Thin CLI over release_lib.validate_manifest."
        ),
    )
    parser.add_argument(
        "manifests",
        nargs="+",
        type=Path,
        help="Path(s) to manifest JSON files (e.g. releases/stable.json).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help=(
            "Also append the Markdown report to $GITHUB_STEP_SUMMARY so the "
            "workflow step names the failing rule."
        ),
    )
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    """Validate every named manifest; return the process exit code."""

    arguments = _parse_arguments(sys.argv[1:] if argv is None else argv)

    results: list[tuple[str, Sequence[ManifestViolationLike | _Refusal]]] = []
    try:
        for path in arguments.manifests:
            results.append((_display_path(path), _violations_for(path)))
    except ImportError:
        print(
            "[validate_manifest] scripts/release_lib.py is required but was "
            "not importable; the validator intentionally owns no rules of "
            "its own (reuse contract R1).",
            file=sys.stderr,
        )
        return EXIT_INVOCATION_ERROR

    report = _render_report(results)
    print(report, end="")
    if arguments.summary:
        _write_summary(report)

    refused = any(violations for _, violations in results)
    return EXIT_REFUSED if refused else EXIT_OK


if __name__ == "__main__":  # pragma: no cover - process entry point
    sys.exit(main())
