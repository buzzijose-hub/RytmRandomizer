"""Guard the ``scripts/`` vs ``Scripts/`` case convention.

Lowercase ``scripts/`` is the canonical location for repo tooling. Older
branches may still carry two legacy PowerShell files under ``Scripts/``.
This compatibility guard permits only those historic capitalised paths and
requires each legacy tool at exactly one of its original or lowercase paths.
The root-perimeter guard can enforce the stricter all-lowercase convention
on migrated branches.

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
**at most** the two grandfathered ``.ps1`` files. Each legacy tool remains
tracked exactly once, allowing a move to lowercase without permitting deletion
or duplicate casing. Every other script belongs in lowercase ``scripts/``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

# The only two files allowed under the capitalised spelling. Each tool must
# remain tracked at exactly one of its original or lowercase paths, so a
# casing migration cannot silently delete it or introduce duplicate copies.
# New tooling is cross-platform Python under lowercase ``scripts/``.
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


def test_legacy_powershell_tools_have_exactly_one_tracked_location() -> None:
    tracked = set(_tracked_paths())
    invalid: dict[str, list[str]] = {}
    for original in sorted(_GRANDFATHERED_CAPITALISED):
        lowercase = "scripts/" + original.partition("/")[2]
        present = sorted(tracked & {original, lowercase})
        if len(present) != 1:
            invalid[original] = present

    assert not invalid, (
        "Each legacy PowerShell tool must remain tracked at exactly one of "
        "its original Scripts/ path or its lowercase scripts/ path. "
        "Missing tools and duplicate casing are forbidden. "
        f"Invalid tracked locations: {invalid}."
    )
