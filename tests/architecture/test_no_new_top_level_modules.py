"""Gate 9 — module-organization hygiene: no new top-level modules.

Per ``docs/PLAN_REQUIREMENTS.md`` Gate 9, adding a new top-level module under
``rytm_randomizer/`` requires architect sign-off and an explicit allowlist
entry. The default home for any new concept is a subpackage (``data/``,
``engines/``, ``guardrails/``, ``observability/``, ``state/``,
``style_analysis/``, ``behavior/``, ``devices/``, ``snapshot/``, ``reports/``,
or a brand-new subpackage with a one-line ``__init__.py`` docstring).

The PR #21 lesson: 33 new top-level files is not a refactor, it is a flood.
Subpackages keep the dependency-direction tests in
``test_import_direction.py`` enforceable; flat top-level adds erode that.

This test hard-codes the post-Wave-1 baseline as ``_ALLOWED_TOP_LEVEL`` and
fails if any file appears at ``rytm_randomizer/*.py`` that is not in the set.
Subpackage files (``rytm_randomizer/<sub>/*.py``) are NOT checked here —
new subpackages remain encouraged.

To add a new top-level module legitimately:

1. Get architect sign-off (recorded in the WS plan body).
2. Add the file name to ``_ALLOWED_TOP_LEVEL`` in the same PR.
3. The reviewer rejects step 2 if step 1 is missing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "rytm_randomizer"

# Post-Wave-1 baseline of allowed top-level ``rytm_randomizer/*.py`` files.
# Adding a new top-level module requires architect sign-off + an explicit
# allowlist entry (Gate 9). Default home for new code is a subpackage.
_ALLOWED_TOP_LEVEL: Final[frozenset[str]] = frozenset(
    {
        "__init__.py",
        "active_boundary.py",
        "app.py",
        "cli.py",
        "cli_registry.py",
        "commands.py",
        "constants.py",
        "group_runner.py",
        "help_text.py",
        "inspection.py",
        "midi_io.py",
        "mido_provider.py",
        "mock_message_mapper.py",
        "mock_midi.py",
        "mock_runtime_active_bridge.py",
        "profile_lookup.py",
        "profiles.py",
        "project_status_report.py",
        "randomization.py",
        "real_midi_adapter.py",
        "registry.py",
        "runtime_plan.py",
        "scene_runner.py",
        "scenes.py",
        "shell.py",
        "validation.py",
    }
)


def _top_level_python_files() -> list[str]:
    """Return the sorted basenames of every ``rytm_randomizer/*.py`` file.

    Subpackage files (``rytm_randomizer/<sub>/*.py``) are NOT returned —
    they are governed by the import-direction tests, not this gate.
    """

    return sorted(p.name for p in PACKAGE_ROOT.glob("*.py"))


def test_no_unallowlisted_top_level_modules() -> None:
    """Every ``rytm_randomizer/*.py`` file must appear in ``_ALLOWED_TOP_LEVEL``.

    Enforces Gate 9 of ``docs/PLAN_REQUIREMENTS.md`` (module-organization
    hygiene). The default home for a new concept is a subpackage; a flat
    top-level addition needs architect sign-off and an allowlist entry.
    """

    present = set(_top_level_python_files())
    unexpected = sorted(present - _ALLOWED_TOP_LEVEL)
    assert not unexpected, (
        "New top-level modules detected. Gate 9 requires architect sign-off "
        "AND an explicit ``_ALLOWED_TOP_LEVEL`` entry. Default home for new "
        "code is a subpackage (``data/``, ``engines/``, ``guardrails/``, "
        "``observability/``, ``state/``, ``style_analysis/``, ``behavior/``, "
        "``devices/``, ``snapshot/``, ``reports/``, or a new one).\n"
        "  Unallowlisted top-level files:\n    " + "\n    ".join(unexpected)
    )


def test_allowlist_does_not_include_deleted_files() -> None:
    """Every entry in ``_ALLOWED_TOP_LEVEL`` must still exist on disk.

    Prevents the allowlist from rotting: if a module is deleted as part of a
    sweep, the corresponding entry must be removed in the same PR. This
    keeps the allowlist a precise mirror of "what was approved" rather than
    a graveyard of historical files.
    """

    present = set(_top_level_python_files())
    missing = sorted(_ALLOWED_TOP_LEVEL - present)
    assert not missing, (
        "``_ALLOWED_TOP_LEVEL`` lists files that no longer exist on disk. "
        "Remove the stale entries in the same PR that deleted the files.\n"
        "  Stale entries:\n    " + "\n    ".join(missing)
    )
