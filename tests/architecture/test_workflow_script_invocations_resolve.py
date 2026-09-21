"""Every ``python scripts/<name>.py <subcommand>`` in a workflow resolves.

A workflow step that shells out to a repo script is a contract between two
files that nothing type-checks: the YAML names a path and a subcommand, and
the script has to actually implement a command-line entry point that accepts
it. Python makes the failure silent — running a module with no
``if __name__ == "__main__"`` block executes the module body, prints nothing,
writes nothing, and **exits 0**. The workflow step goes green having done
nothing at all.

That is not hypothetical. The auto-update program's first parallel run had
``release.yml`` and ``promote.yml`` both invoking
``python scripts/release_lib.py generate --channel ... --output ...`` while
``release_lib.py`` shipped as an importable library with no ``__main__``.
Every release would have reported success and published no manifest; the
operator's first symptom would have been the NEXT step failing with
"manifest could not be read", pointing two steps downstream of the cause.

This test closes that gap mechanically: it parses every workflow's ``run:``
bodies for ``python scripts/<name>.py`` invocations and asserts the named
script exists and defines a ``__main__`` entry point.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR: Final[Path] = PROJECT_ROOT / ".github" / "workflows"

#: ``python scripts/foo.py`` / ``python3 scripts/foo.py`` / ``.venv/bin/python scripts/foo.py``
_SCRIPT_INVOCATION: Final[re.Pattern[str]] = re.compile(
    r"python[0-9.]*\s+(?:-[A-Za-z]+\s+)*(scripts/[A-Za-z0-9_./-]+\.py)"
)

#: A real command-line entry point.
_MAIN_GUARD: Final[re.Pattern[str]] = re.compile(
    r"^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:", re.MULTILINE
)


def _invocations() -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for workflow in sorted(WORKFLOWS_DIR.glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        for match in _SCRIPT_INVOCATION.finditer(text):
            found.append((workflow, match.group(1)))
    return found


def test_every_workflow_script_invocation_names_an_existing_file() -> None:
    missing = [
        f"{workflow.name} -> {script}"
        for workflow, script in _invocations()
        if not (PROJECT_ROOT / script).is_file()
    ]
    assert not missing, (
        "Workflow steps invoke scripts that do not exist:\n  "
        + "\n  ".join(missing)
        + "\nA missing script fails the step loudly, but a step that names the "
        "wrong path is usually a rename that skipped one call site."
    )


def test_every_workflow_invoked_script_has_a_main_entry_point() -> None:
    inert = []
    for workflow, script in _invocations():
        path = PROJECT_ROOT / script
        if not path.is_file():
            continue  # covered by the sibling test
        if not _MAIN_GUARD.search(path.read_text(encoding="utf-8")):
            inert.append(f"{workflow.name} runs `python {script}`")

    assert not inert, (
        "These workflow steps invoke a Python file that has no "
        '`if __name__ == "__main__":` entry point:\n  '
        + "\n  ".join(inert)
        + "\n\nRunning such a file executes the module body, writes nothing, and "
        "EXITS 0 — the step reports success having done nothing, and the failure "
        "surfaces later at whatever consumes the output it never produced.\n"
        "Fix: give the script a __main__ block that dispatches its subcommands "
        "and exits non-zero on error, or call the library from a thin CLI that has one."
    )
