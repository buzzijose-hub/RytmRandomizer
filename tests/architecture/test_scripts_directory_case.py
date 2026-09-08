"""Guard the ``scripts/`` vs ``Scripts/`` case convention.

The repo intentionally tracks two directory spellings (``CONTRIBUTING.md``
§ "When writing scripts"): lowercase ``scripts/`` holds cross-platform
Python tooling, and capitalised ``Scripts/`` holds two legacy
PowerShell-only duplicates kept for Windows operator convenience.

On a case-insensitive filesystem (macOS default, Windows) those two
spellings collapse into **one physical directory**. A new file written to
``scripts/foo.py`` can therefore be staged by ``git add`` under the
*other* spelling — ``Scripts/foo.py`` — with no error and no visible
difference on disk. The file then lands in the wrong tracked path, and on
a case-*sensitive* filesystem (Linux CI, most contributors' containers)
it materialises in a directory where nothing imports or executes it.

This bit a parallel-agent run on 2026-09-07: four independent agents
wrote new Python tooling to ``scripts/`` and had it staged as
``Scripts/``. One noticed and hand-corrected the index with
``git update-index --cacheinfo``; the others did not.

The rule this test enforces: ``Scripts/`` (capitalised) contains
**only** the two grandfathered ``.ps1`` files. Every other script —
and every new one — belongs in lowercase ``scripts/``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

# The only two files allowed under the capitalised spelling. This set is
# frozen and may only shrink: the convention is that new tooling is
# cross-platform Python under lowercase ``scripts/``.
_GRANDFATHERED_CAPITALISED: Final[frozenset[str]] = frozenset(
    {
        "Scripts/closeout_check.ps1",
        "Scripts/quick_status.ps1",
    }
)


def _tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.splitlines()


def test_capitalised_scripts_dir_holds_only_grandfathered_powershell_files() -> None:
    tracked = {p for p in _tracked_paths() if p.startswith("Scripts/")}
    unexpected = tracked - _GRANDFATHERED_CAPITALISED

    assert not unexpected, (
        "New files are tracked under the capitalised `Scripts/` spelling: "
        f"{sorted(unexpected)}.\n\n"
        "On macOS/Windows `scripts/` and `Scripts/` are the SAME physical "
        "directory, so `git add scripts/foo.py` can silently stage "
        "`Scripts/foo.py`. On Linux CI that path is a different directory "
        "and nothing there is imported or executed.\n\n"
        "Fix: restage under the lowercase path, e.g.\n"
        "  git rm --cached Scripts/foo.py\n"
        "  sha=$(git hash-object -w scripts/foo.py)\n"
        "  git update-index --add --cacheinfo 100644,$sha,scripts/foo.py\n\n"
        "Per CONTRIBUTING.md, `Scripts/` holds only the two legacy "
        "PowerShell duplicates; new tooling is Python under `scripts/`."
    )


def test_grandfathered_capitalised_files_still_exist() -> None:
    # Keeps the allowlist honest: if a legacy .ps1 is ever deleted or
    # migrated to Python, this fails and the allowlist shrinks with it.
    tracked = {p for p in _tracked_paths() if p.startswith("Scripts/")}
    missing = _GRANDFATHERED_CAPITALISED - tracked

    assert not missing, (
        f"Grandfathered capitalised script(s) no longer tracked: {sorted(missing)}. "
        "Remove them from _GRANDFATHERED_CAPITALISED — the allowlist may only shrink."
    )
