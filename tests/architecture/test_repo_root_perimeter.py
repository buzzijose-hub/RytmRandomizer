"""Repo-root safety perimeter — extend enforcement past ``rytm_randomizer/``.

The rest of the architecture suite anchors on ``PACKAGE_ROOT =
rytm_randomizer/`` and rglobs within it. That leaves every repo-root Python
tree (``tooling/``, ``Scripts/``, ``tests/`` helpers, and any future
``tools/``) outside the no-side-effects / lazy-MIDI / passivity gates. PR
#213 exposed the hole: a second armed-MIDI entry point landed in a brand-new
top-level ``tools/`` package and sailed past ``test_no_new_top_level_modules``
and the lazy-``mido`` rules, because both are package-scoped.

This module closes the hole with two repo-wide checks:

1. **Top-level directory allowlist.** A frozen set of permitted repo-root
   directories; a PR that adds a new one (``calibration/``, ``tools/``,
   ``output/`` …) fails until the directory is deliberately allowlisted with
   a stated home policy. Mirrors the proven ``_ALLOWED_TOP_LEVEL`` pattern in
   ``test_no_new_top_level_modules.py``.

2. **Repo-wide MIDI-import scan.** ``import mido`` / ``import rtmidi`` (in any
   form, at any nesting) is forbidden anywhere outside the two sanctioned
   boundary modules ``rytm_randomizer/real_midi_adapter.py`` and
   ``rytm_randomizer/mido_provider.py`` — enforced across the WHOLE repo, not
   just the package. This is the mechanical backstop for the Live-but-Passive
   safety model (docs/superpowers/plans/2026-07-18-rival-program.md §1) and
   for CLAUDE.md hard rule 7.

See the sibling ``test_armed_entry_points.py`` for the transmit-path
whitelist that complements the raw-import scan here.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

# Permitted repo-root directories. Adding a new top-level directory requires a
# deliberate allowlist entry + a one-line home-policy statement in the PR body
# (Gate 9 spirit, extended to the repo root). Dot-directories (.git, .github,
# .venv, .claude, …) and generated caches are excluded from the scan entirely
# (see ``_IGNORED_ROOT_NAMES``) rather than allowlisted.
_ALLOWED_ROOT_DIRS: Final[frozenset[str]] = frozenset(
    {
        # NOTE dual casing: git tracks BOTH ``Scripts/`` (PowerShell operator
        # scripts) and ``scripts/`` (Python repo/CI scripts). On macOS's
        # case-insensitive filesystem they materialize as ONE directory (the
        # first-created casing wins in ``iterdir``); on case-sensitive Linux
        # CI they check out as TWO. Both must therefore be allowlisted.
        "Scripts",  # PowerShell operator scripts (closeout/quick_status)
        "scripts",  # Python repo/CI scripts (create_pr, gates, captures)
        "agent-memory",  # shared cross-agent memory store
        "captures",  # raw operator-supplied SysEx capture evidence
        "desktop",  # Tauri shell + React cockpit
        "docs",  # documentation, plans, diagrams
        "installer-assets",  # packaging icons / metadata
        "rytm_randomizer",  # the Python package
        "tests",  # the test suite
        "tooling",  # dev tooling (see _SCHEDULED_FOR_RETIREMENT below)
    }
)

# Directory basenames never scanned (VCS, envs, editor/agent config, caches).
_IGNORED_ROOT_NAMES: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".github",
        ".venv",
        ".claude",
        ".agents",
        ".codex",
        ".githooks",
        ".ruff_cache",
        ".pytest_cache",
        ".mypy_cache",
        "__pycache__",
        ".idea",
        ".vscode",
        ".devcontainer",
        "node_modules",
    }
)

# The modules permitted to import the MIDI backend. ``real_midi_adapter`` and
# ``mido_provider`` are the classic seam; ``midi_io`` also carries a lazy
# in-method ``import mido`` inside ``send_cc`` (midi_io.py:163) — the real
# critical send path. CLAUDE.md hard rule 7 (as corrected in this bundle)
# names exactly this three-module boundary and bans top-level mido imports
# everywhere; this scan is its repo-wide mechanical enforcement.
_MIDI_IMPORT_BOUNDARY: Final[frozenset[str]] = frozenset(
    {
        "rytm_randomizer/real_midi_adapter.py",
        "rytm_randomizer/mido_provider.py",
        "rytm_randomizer/midi_io.py",
    }
)

# Known dead scripts carrying top-level ``import mido`` (and ``import msvcrt``)
# that are Windows-locked and slated for removal in WS-1 of the rival-program
# bundle. Allowlisting them here keeps the gate GREEN on the current tree while
# the retirement PR is prepared; the retirement commit deletes both the files
# and these entries together (enforced by ``test_scheduled_retirements_still_exist``).
_SCHEDULED_FOR_RETIREMENT: Final[frozenset[str]] = frozenset(
    {
        "tooling/capture_tools/rytm_capture_bd_sharp_anchor_v01.py",
        "tooling/capture_tools/rytm_capture_bd_sharp_anchor_v02.py",
        "tooling/capture_tools/rytm_capture_generic_lfo_v01.py",
        "tooling/capture_tools/rytm_capture_syraw_morph_v01.py",
    }
)

_MIDI_IMPORT_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?:import\s+(?:mido|rtmidi|python_rtmidi)\b" r"|from\s+(?:mido|rtmidi|python_rtmidi)\b)",
    re.MULTILINE,
)


def _repo_root_entries() -> list[Path]:
    """Return non-ignored top-level entries under the repo root."""

    return [entry for entry in PROJECT_ROOT.iterdir() if entry.name not in _IGNORED_ROOT_NAMES]


def _all_repo_python_files() -> list[Path]:
    """Every ``*.py`` under a non-ignored repo-root directory (recursive).

    Root-level ``*.py`` files (e.g. ``conftest.py``) are included too.
    """

    files: list[Path] = list(PROJECT_ROOT.glob("*.py"))
    for entry in _repo_root_entries():
        if entry.is_dir():
            files.extend(
                p
                for p in entry.rglob("*.py")
                if not any(part in _IGNORED_ROOT_NAMES for part in p.parts)
            )
    return sorted(files)


def test_no_unallowlisted_repo_root_directories() -> None:
    """Every top-level directory must be explicitly allowlisted.

    A new repo-root directory (``tools/``, ``calibration/``, ``output/`` …)
    fails this test until it is added to ``_ALLOWED_ROOT_DIRS`` with a stated
    home policy. This is the repo-root analogue of Gate 9 and the mechanism
    that would have caught PR #213's ``tools/`` package.
    """

    present_dirs = {e.name for e in _repo_root_entries() if e.is_dir()}
    unexpected = sorted(present_dirs - _ALLOWED_ROOT_DIRS)
    assert not unexpected, (
        "New top-level directory detected outside the allowlist. Add it to "
        "``_ALLOWED_ROOT_DIRS`` with a one-line home-policy note in the PR "
        "body, or relocate its contents into an existing tree.\n"
        "  Unallowlisted directories:\n    " + "\n    ".join(unexpected)
    )


def test_allowlisted_root_directories_still_exist() -> None:
    """Every ``_ALLOWED_ROOT_DIRS`` entry must still exist on disk.

    Case-insensitive comparison: on macOS the dual-cased ``Scripts``/
    ``scripts`` pair materializes as a single directory (one casing visible in
    ``iterdir``), while Linux checks out both. An entry counts as present if
    any on-disk directory matches it case-insensitively.
    """

    present_casefold = {e.name.casefold() for e in _repo_root_entries() if e.is_dir()}
    stale = sorted(
        entry for entry in _ALLOWED_ROOT_DIRS if entry.casefold() not in present_casefold
    )
    assert not stale, (
        "``_ALLOWED_ROOT_DIRS`` lists directories that no longer exist. "
        "Remove the stale entries in the same PR that deleted them.\n"
        "  Stale entries:\n    " + "\n    ".join(stale)
    )


def test_no_midi_imports_outside_the_boundary_repo_wide() -> None:
    """``import mido`` / ``import rtmidi`` only in the two boundary modules.

    Scans the WHOLE repository (not just ``rytm_randomizer/``). Any file that
    imports the MIDI backend and is neither one of the two sanctioned boundary
    modules nor a scheduled-for-retirement dead script is a violation — this is
    the mechanical backstop for the Live-but-Passive safety model and CLAUDE.md
    hard rule 7.
    """

    offenders: list[str] = []
    for path in _all_repo_python_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel in _MIDI_IMPORT_BOUNDARY or rel in _SCHEDULED_FOR_RETIREMENT:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if _MIDI_IMPORT_RE.search(text):
            offenders.append(rel)
    assert not offenders, (
        "MIDI backend imported outside the sanctioned boundary "
        "(``real_midi_adapter.py`` / ``mido_provider.py``). Route MIDI access "
        "through the provider/adapter seam; never import ``mido``/``rtmidi`` "
        "directly elsewhere.\n"
        "  Offending files:\n    " + "\n    ".join(sorted(offenders))
    )


def test_scheduled_retirements_still_exist() -> None:
    """Keep ``_SCHEDULED_FOR_RETIREMENT`` honest: no phantom entries.

    Once a scheduled dead script is deleted, its entry must be removed here in
    the same commit — otherwise the allowlist rots into a graveyard and a
    newly-added file could silently inherit a retirement exemption.
    """

    missing = sorted(rel for rel in _SCHEDULED_FOR_RETIREMENT if not (PROJECT_ROOT / rel).exists())
    assert not missing, (
        "``_SCHEDULED_FOR_RETIREMENT`` lists files that no longer exist. "
        "Delete the corresponding allowlist entries in the same commit that "
        "removed the files.\n"
        "  Stale entries:\n    " + "\n    ".join(missing)
    )
