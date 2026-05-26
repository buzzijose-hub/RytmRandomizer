"""Tests for passive live GUI safety-checklist and arm-gate modeling."""

from __future__ import annotations

import json
import sys

import pytest

pytestmark = pytest.mark.fast

FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)


def test_safety_checklist_model_defaults_to_mock_safe_locked_arm_gate() -> None:
    from rytm_randomizer.reports.live_gui_safety_checklist_model import (
        build_live_gui_safety_checklist_model,
        format_live_gui_safety_checklist_model,
        to_live_gui_safety_checklist_model_json,
    )

    report = build_live_gui_safety_checklist_model(session_label="Warehouse rehearsal")

    assert report.safety_checklist_version == "live-gui-safety-checklist-model-v1"
    assert len(report.safety_checklist_id) == 16
    assert report.session_label == "Warehouse rehearsal"
    assert report.checklist_status == "passed"
    assert report.passed_count == 4
    assert report.total_count == 4
    assert [item.key for item in report.items] == [
        "conflicting-sessions",
        "guards-enabled",
        "snapshot-compatible",
        "parameter-limits",
    ]
    assert all(item.status == "passed" for item in report.items)
    assert report.arm_gate.state == "locked"
    assert report.arm_gate.enabled is False
    assert report.arm_gate.reason == (
        "Arm Hardware stays locked until SEND readiness, dry run, MIDI port, and hardware metadata are all ready."
    )
    assert report.arm_gate.requirements == (
        "send plan ready",
        "dry run complete",
        "MIDI port open",
        "hardware connected",
    )
    assert "arm hardware from safety checklist" in report.blocked_actions
    assert "open MIDI port from safety checklist" in report.blocked_actions
    assert report.replay_commands == (
        "python -m rytm_randomizer.cli live-gui-safety-checklist-model-report "
        "--session-label 'Warehouse rehearsal'",
    )

    lines = format_live_gui_safety_checklist_model(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive live GUI safety-checklist model"
    assert "Safety checklist summary:" in lines
    assert "- checklist: 4 / 4 passed" in lines
    assert "- arm hardware: locked" in lines
    assert "- conflicting-sessions: passed - No conflicting sessions detected" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_live_gui_safety_checklist_model_json(report)
    checklist = payload["live_gui_safety_checklist_model"]
    assert checklist["safety_checklist_version"] == "live-gui-safety-checklist-model-v1"
    assert checklist["safety_checklist_id"] == report.safety_checklist_id
    assert checklist["items"][0]["key"] == "conflicting-sessions"
    assert checklist["arm_gate"]["state"] == "locked"
    assert payload["safety"][0] == "passive/read-only"


def test_safety_checklist_model_can_declare_future_arm_ready_metadata() -> None:
    from rytm_randomizer.reports.live_gui_safety_checklist_model import (
        build_live_gui_safety_checklist_model,
    )

    report = build_live_gui_safety_checklist_model(
        midi_port_name="Elektron Analog Rytm MKII 1",
        midi_port_open=True,
        hardware_connected=True,
        send_plan_ready=True,
        dry_run_complete=True,
    )

    assert report.checklist_status == "passed"
    assert report.arm_gate.state == "ready-to-arm"
    assert report.arm_gate.enabled is True
    assert report.arm_gate.reason == (
        "Future GUI may enable Arm Hardware after explicit operator confirmation."
    )
    assert report.arm_gate.midi_port_name == "Elektron Analog Rytm MKII 1"
    assert report.arm_gate.hardware_connected is True
    assert "no hardware mutation" in report.safety_lines


def test_safety_checklist_model_blocks_on_failed_safety_rows() -> None:
    from rytm_randomizer.reports.live_gui_safety_checklist_model import (
        build_live_gui_safety_checklist_model,
    )

    report = build_live_gui_safety_checklist_model(
        conflicting_session_count=2,
        guards_enabled=False,
        snapshot_compatible=False,
        parameter_limits_ok=False,
        send_plan_ready=True,
        dry_run_complete=True,
        midi_port_name="Elektron Analog Rytm MKII 1",
        midi_port_open=True,
        hardware_connected=True,
    )

    assert report.checklist_status == "blocked"
    assert report.passed_count == 0
    assert report.arm_gate.state == "blocked"
    assert report.arm_gate.enabled is False
    assert report.arm_gate.reason == "Resolve blocked safety checklist rows before arming."
    assert [item.status for item in report.items] == ["blocked", "blocked", "blocked", "blocked"]
    assert report.items[0].message == "2 conflicting session(s) detected"
    assert report.items[0].operator_action == "Close or resolve conflicting sessions first."
    assert report.items[1].operator_action == "Re-enable all safety guards before arm review."
    assert report.items[2].operator_action == "Load a compatible snapshot before arm review."
    assert (
        report.items[3].operator_action == "Regenerate or lower mutation depth before arm review."
    )


def test_safety_checklist_model_validation_edges() -> None:
    from rytm_randomizer.reports.live_gui_safety_checklist_model import (
        build_live_gui_safety_checklist_model,
    )

    with pytest.raises(ValueError, match="session_label"):
        build_live_gui_safety_checklist_model(session_label=" ")

    with pytest.raises(ValueError, match="conflicting_session_count"):
        build_live_gui_safety_checklist_model(conflicting_session_count=-1)

    with pytest.raises(ValueError, match="midi_port_name"):
        build_live_gui_safety_checklist_model(midi_port_name=" ")


def test_safety_checklist_model_json_is_serializable_and_passive() -> None:
    before_modules = set(sys.modules)

    from rytm_randomizer.reports.live_gui_safety_checklist_model import (
        build_live_gui_safety_checklist_model,
        to_live_gui_safety_checklist_model_json,
    )

    report = build_live_gui_safety_checklist_model()
    json.dumps(to_live_gui_safety_checklist_model_json(report), sort_keys=True)

    imported_modules = set(sys.modules) - before_modules
    assert not (set(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES) & imported_modules)
    assert all("no " in action for action in report.safety_lines if action.startswith("no "))
