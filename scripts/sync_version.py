"""Propagate the repo-root ``VERSION`` into every derived declaration.

A thin CLI over :mod:`release_lib` (R1) — this script owns no SemVer logic and
no manifest schema; it only knows *where* the derived version literals live and
how to rewrite each file's syntax without disturbing the rest of the file.

The four derived sites (spec §2.2 plus the briefcase block):

* ``pyproject.toml`` ``[tool.briefcase] version`` — briefcase has no
  dynamic-version hook, so unlike ``[project]`` (which reads ``VERSION`` via
  ``[tool.hatch.version]``) this literal must be written. It is **not** a
  stale duplicate: briefcase stamps it onto the ``.msi`` / ``.pkg`` /
  AppImage that ``.github/workflows/installers.yml`` builds.
* ``desktop/shell/Cargo.toml`` ``[package] version``
* ``desktop/shell/tauri.conf.json`` top-level ``version``
* ``desktop/web/package.json`` top-level ``version``

Usage (from the repo root)::

    python scripts/sync_version.py            # rewrite the derived files
    python scripts/sync_version.py --check    # verify, write nothing

Exit codes: ``0`` in sync (or written), ``1`` drift under ``--check``, ``2``
the toolkit refused (bad or missing ``VERSION``, unlocatable target literal).

Rewrites are surgical and span-scoped so the JSON files keep their exact
formatting, key order, and trailing newline; running the script twice is a
no-op. ``tests/architecture/test_version_single_source.py`` pins the result in
CI.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

if __package__ in {None, ""}:  # pragma: no cover - import shim, exercised via subprocess
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from release_lib import (  # noqa: E402  (after the sys.path shim above)
    PROJECT_ROOT,
    ReleaseError,
    Version,
    ViolationCode,
    log_event,
    read_version_file,
    redact_path,
)

EXIT_OK: Final[int] = 0
EXIT_DRIFT: Final[int] = 1
EXIT_REFUSED: Final[int] = 2


@dataclass(frozen=True, slots=True)
class DerivedSite:
    """One file whose version literal is derived from ``VERSION``.

    ``pattern`` must capture the literal in group ``version`` and match
    exactly once in the file; ``relative_path`` doubles as the display label.
    """

    relative_path: str
    pattern: re.Pattern[str]

    @property
    def label(self) -> str:
        return self.relative_path


#: Ordered so output is deterministic across runs and platforms.
DERIVED_SITES: Final[tuple[DerivedSite, ...]] = (
    DerivedSite(
        "pyproject.toml",
        # Every column-0 `version = "..."` in the file. Exactly one is
        # expected (the [tool.briefcase] literal); [project] is dynamic and
        # contributes none. Matching them ALL rather than anchoring on the
        # briefcase header is deliberate: a reintroduced hand-authored
        # `[project] version` then becomes a 2-declaration REFUSAL instead of
        # being silently skipped while the stale literal ships.
        re.compile(r'(?m)^version = "(?P<version>[^"]+)"'),
    ),
    DerivedSite(
        "desktop/shell/Cargo.toml",
        # Same rule: any column-0 literal. Dependency versions are indented or
        # written as inline tables, so they never match here.
        re.compile(r'(?m)^version = "(?P<version>[^"]+)"'),
    ),
    DerivedSite(
        "desktop/shell/tauri.conf.json",
        re.compile(r'(?m)^\s*"version": "(?P<version>[^"]+)",?$'),
    ),
    DerivedSite(
        "desktop/web/package.json",
        re.compile(r'(?m)^\s*"version": "(?P<version>[^"]+)",?$'),
    ),
)


@dataclass(frozen=True, slots=True)
class SiteResult:
    """Outcome for one derived site."""

    site: DerivedSite
    previous: str
    canonical: str

    @property
    def in_sync(self) -> bool:
        return self.previous == self.canonical


def _read_site(site: DerivedSite, project_root: Path) -> tuple[str, re.Match[str]]:
    """Return ``(text, match)`` for ``site``; refuse if the literal is not unique."""
    path = project_root / site.relative_path
    if not path.is_file():
        raise ReleaseError(ViolationCode.VERSION_FILE_MISSING, redact_path(path))
    text = path.read_text(encoding="utf-8")
    matches = list(site.pattern.finditer(text))
    if len(matches) != 1:
        raise ReleaseError(
            ViolationCode.VERSION_MALFORMED,
            f"{site.label} has {len(matches)} version declarations, expected 1",
        )
    return text, matches[0]


def _rewrite(text: str, match: re.Match[str], canonical: str) -> str:
    """Replace only the captured version literal, leaving every other byte intact."""
    start, end = match.span("version")
    return f"{text[:start]}{canonical}{text[end:]}"


def sync_versions(
    canonical: Version, *, check_only: bool, project_root: Path | None = None
) -> tuple[SiteResult, ...]:
    """Bring every derived site to ``canonical`` (or report drift under ``check_only``).

    Returns one :class:`SiteResult` per site, in :data:`DERIVED_SITES` order.
    Raises :class:`ReleaseError` when a target file is missing or its version
    literal is not uniquely locatable — a refusal, never a guess.
    """
    root = project_root or PROJECT_ROOT
    canonical_text = str(canonical)
    results: list[SiteResult] = []
    for site in DERIVED_SITES:
        text, match = _read_site(site, root)
        previous = match.group("version")
        results.append(SiteResult(site=site, previous=previous, canonical=canonical_text))
        if previous == canonical_text or check_only:
            continue
        (root / site.relative_path).write_text(
            _rewrite(text, match, canonical_text), encoding="utf-8"
        )
        log_event(
            "release.version.synced",
            file=site.label,
            previous=previous,
            current=canonical_text,
        )
    return tuple(results)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. See the module docstring for exit codes."""
    parser = argparse.ArgumentParser(
        prog="sync_version.py",
        description="Propagate the repo-root VERSION into every derived declaration.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify only: exit 1 on drift and write nothing.",
    )
    args = parser.parse_args(argv)

    try:
        canonical = read_version_file()
        results = sync_versions(canonical, check_only=args.check)
    except ReleaseError as error:
        # Typed refusal: the code is the contract, the detail is path-redacted.
        print(f"sync_version: refused ({error.code.value}): {error.detail}", file=sys.stderr)
        log_event("release.version.sync_refused", code=error.code.value, detail=error.detail)
        return EXIT_REFUSED

    drifted = [result for result in results if not result.in_sync]
    if not drifted:
        print(f"sync_version: {len(results)} declarations already at {canonical}.")
        return EXIT_OK

    if args.check:
        print(
            f"sync_version: {len(drifted)} declaration(s) drifted from VERSION.",
            file=sys.stderr,
        )
        for result in drifted:
            print(
                f"  {result.site.label}: {result.previous} != {result.canonical}",
                file=sys.stderr,
            )
        print("  run `just version-sync` to fix.", file=sys.stderr)
        return EXIT_DRIFT

    for result in drifted:
        print(f"sync_version: {result.site.label}: {result.previous} -> {result.canonical}")
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover - CLI dispatch
    sys.exit(main())
