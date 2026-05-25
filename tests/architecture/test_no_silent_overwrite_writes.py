"""Forbid ``Path.write_text/write_bytes`` in cockpit/profiles/ outside ``atomic_write``.

This test exists because CODE_REVIEW.md PR 7 (finding M7) closed a
data-loss footgun in ``ProfileRegistry.save``: the original code did
``target.write_text(...)`` with no ``exist_ok=False`` check, silently
overwriting any prior profile file with the same id. ``write_text`` is
also non-atomic on POSIX and Windows — a crash mid-write would leave
the operator's profile half-truncated.

PR 7 routed ``save`` through ``cockpit.export.writer.atomic_write``
(sibling tempfile + fsync + ``os.replace``, ``overwrite=False`` by
default). This test prevents the next contributor from re-introducing
a direct ``write_text`` / ``write_bytes`` / ``open(..., "w")`` /
``open(..., "wb")`` call in the persistence layer.

Scope
-----

We check ``rytm_randomizer/cockpit/profiles/`` and
``rytm_randomizer/cockpit/wizard/`` (the two layers that persist user
content). Other modules can use ``write_text`` legitimately
(temp-file helpers, the writer module itself, etc.).

Allowed writes:

* ``open(..., "r")`` / read-mode opens — not a write.
* The ``atomic_write`` implementation in
  ``cockpit/export/writer.py`` — that's the canonical surface.
* Anything in the ``__pycache__`` cache or test fixtures.

See also:
* ``CODE_REVIEW.md`` finding M7.
* ``CODE_REVIEW_PROGRESS.md`` row RR4g.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import pytest

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
SCOPE_DIRS: Final[tuple[Path, ...]] = (
    PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "profiles",
    PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "wizard",
)

# The forbidden method names (called on a Path object) + the forbidden
# open-mode strings. These are the only known ways to perform a
# non-atomic write.
_FORBIDDEN_PATH_METHODS: Final[frozenset[str]] = frozenset(
    {"write_text", "write_bytes"}
)
_WRITE_MODE_LETTERS: Final[frozenset[str]] = frozenset(
    {"w", "wb", "a", "ab", "w+", "wb+", "a+", "ab+"}
)

# The rule activates once PR 7 lands atomic_write into the profiles
# layer. Until then this test is dormant.
_ATOMIC_WRITE_SHIPPED_MARKER: Final[Path] = (
    PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "profiles" / "registry.py"
)


def _atomic_write_in_profiles() -> bool:
    """Return True once PR 7's ``save -> atomic_write`` migration has shipped."""

    if not _ATOMIC_WRITE_SHIPPED_MARKER.is_file():
        return False
    return "atomic_write" in _ATOMIC_WRITE_SHIPPED_MARKER.read_text(encoding="utf-8")


pytestmark = [
    pytest.mark.fast,
    pytest.mark.skipif(
        not _atomic_write_in_profiles(),
        reason="profiles/registry.py does not import atomic_write yet — RR4g activates once PR 7 lands",
    ),
]


def _violations_in(path: Path) -> list[str]:
    """Find every direct non-atomic-write call in *path*."""

    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    findings: list[str] = []

    for node in ast.walk(tree):
        # Pattern 1: <expr>.write_text(...) / .write_bytes(...)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _FORBIDDEN_PATH_METHODS
        ):
            rel = path.relative_to(PROJECT_ROOT).as_posix()
            findings.append(
                f"{rel}:{node.lineno} `.{node.func.attr}(...)` — direct "
                "non-atomic write. Route through "
                "`cockpit.export.writer.atomic_write(target, encoded, "
                "overwrite=False)` to get crash-safety + overwrite guard."
            )
            continue

        # Pattern 2: open(<expr>, "w" or "wb" or ...)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open"
        ):
            # find a mode argument: positional [1] or keyword "mode="
            mode_value: str | None = None
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                v = node.args[1].value
                if isinstance(v, str):
                    mode_value = v
            for kw in node.keywords:
                if (
                    kw.arg == "mode"
                    and isinstance(kw.value, ast.Constant)
                    and isinstance(kw.value.value, str)
                ):
                    mode_value = kw.value.value
            if mode_value and mode_value in _WRITE_MODE_LETTERS:
                rel = path.relative_to(PROJECT_ROOT).as_posix()
                findings.append(
                    f"{rel}:{node.lineno} `open(..., {mode_value!r})` — "
                    "direct non-atomic write. Route through "
                    "`cockpit.export.writer.atomic_write(...)`."
                )

    return findings


def _scope_python_files() -> list[Path]:
    out: list[Path] = []
    for d in SCOPE_DIRS:
        if not d.is_dir():
            continue
        out.extend(p for p in d.rglob("*.py") if "__pycache__" not in p.parts)
    return sorted(out)


def test_no_direct_non_atomic_writes_in_persistence_layer() -> None:
    """``Path.write_text`` / ``write_bytes`` / ``open(..., 'w')`` in the
    persistence layer is forbidden.

    Regression guard: CODE_REVIEW.md M7 was an instance of this exact
    anti-pattern (``target.write_text(...)`` in ``ProfileRegistry.save``).
    PR 7 routed everything through ``atomic_write``; this test catches
    the next contributor who reaches for the convenient-but-unsafe
    write API.

    Failure message names the file, line, offending call, and the
    canonical fix recipe.
    """

    violations: list[str] = []
    for path in _scope_python_files():
        violations.extend(_violations_in(path))

    assert not violations, (
        "Direct non-atomic writes in cockpit/profiles or cockpit/wizard "
        "— CODE_REVIEW.md M7 regression. Route through atomic_write:"
        "\n  " + "\n  ".join(violations)
    )
