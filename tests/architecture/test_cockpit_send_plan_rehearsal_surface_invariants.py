"""Architecture invariants for the cockpit send-plan rehearsal surface contract."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
MODULE_PATH: Final[Path] = (
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "cockpit_send_plan_rehearsal_surface.py"
)
EXPECTED_CLI_COMMAND_NAME: Final[str] = "cockpit-send-plan-rehearsal-surface-report"
FORBIDDEN_IMPORTS: Final[frozenset[str]] = frozenset(
    {
        "mido",
        "rtmidi",
        "pythonrtmidi",
        "real_midi_adapter",
        "midi_io",
        "cockpit.ws.server",
        "subprocess",
        "socket",
        "threading",
        "asyncio",
    }
)


def _imported_modules() -> set[str]:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"), filename=str(MODULE_PATH))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


def test_rehearsal_surface_module_lives_under_reports() -> None:
    assert MODULE_PATH.is_file()
    assert MODULE_PATH.parent.name == "reports"
    assert MODULE_PATH.name == "cockpit_send_plan_rehearsal_surface.py"


def test_rehearsal_surface_contract_version_and_command_are_pinned() -> None:
    from rytm_randomizer.reports import cockpit_send_plan_rehearsal_surface as surface

    assert surface.SEND_PLAN_REHEARSAL_SURFACE_VERSION == ("cockpit-send-plan-rehearsal-surface-v1")
    assert surface.SEND_PLAN_REHEARSAL_SURFACE_VERSION.endswith("-v1")
    assert surface._COMMAND_NAME == EXPECTED_CLI_COMMAND_NAME


def test_rehearsal_surface_safety_lines_pin_passive_boundary() -> None:
    from rytm_randomizer.reports import cockpit_send_plan_rehearsal_surface as surface

    assert "passive/read-only" in surface.SAFETY_LINES
    assert "no MIDI sending" in surface.SAFETY_LINES
    assert "no port opening" in surface.SAFETY_LINES
    assert "no hardware mutation" in surface.SAFETY_LINES


def test_rehearsal_surface_enum_sets_are_pinned() -> None:
    from rytm_randomizer.reports import cockpit_send_plan_rehearsal_surface as surface

    assert set(surface.SURFACE_STATUS_VALUES) == {"ready", "blocked"}
    assert set(surface.SCREEN_STATE_VALUES) == {
        "send-ready-review",
        "send-blocked-review",
    }
    assert set(surface.SEND_CONTROL_STATE_VALUES) == {"review-required", "disabled"}


def test_rehearsal_surface_panel_specs_are_pinned() -> None:
    from rytm_randomizer.reports import cockpit_send_plan_rehearsal_surface as surface

    assert tuple(spec.panel_key for spec in surface.PANEL_SPECS) == (
        "summary",
        "pad-packets",
        "readiness-checks",
        "safety-locks",
    )


def test_rehearsal_surface_imports_no_active_runtime_boundaries() -> None:
    imported = _imported_modules()
    violations = sorted(
        module
        for module in imported
        if module in FORBIDDEN_IMPORTS
        or module.partition(".")[0] in FORBIDDEN_IMPORTS
        or module.endswith(".real_midi_adapter")
        or module.endswith(".midi_io")
        or module.endswith(".cockpit.ws.server")
    )
    assert not violations
