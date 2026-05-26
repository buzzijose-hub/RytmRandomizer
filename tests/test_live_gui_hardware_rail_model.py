"""Tests for the passive live GUI hardware rail model."""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.fast


def test_hardware_rail_default_state_is_mock_safe_and_locked() -> None:
    from rytm_randomizer.reports.live_gui_hardware_rail_model import (
        build_live_gui_hardware_rail_model,
        format_live_gui_hardware_rail_model,
        to_live_gui_hardware_rail_model_json,
    )

    report = build_live_gui_hardware_rail_model(session_label="Warehouse live session")

    assert report.model_version == "live-gui-hardware-rail-v1"
    assert len(report.rail_id) == 16
    assert report.session_label == "Warehouse live session"
    assert report.device_label == "Analog Rytm MKII"
    assert report.rail_status == "mock-safe"
    assert report.mode_label == "Simulation / Mock"
    assert report.dry_run_active is True
    assert report.hardware_requested is False
    assert report.port_status == "none"
    assert report.selected_port_name is None
    assert report.available_ports == ()
    assert report.safety_check_count == 4
    assert report.safety_checks_passed == 4
    assert report.failing_safety_checks == ()
    assert report.arm_status == "locked"
    assert report.arm_locked is True
    assert report.required_actions == (
        "select-midi-port",
        "disable-dry-run-before-hardware",
        "request-hardware-arm",
    )
    assert "no MIDI port opened" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert "no hardware mutation" in report.blocked_actions

    cards_by_key = {card.key: card for card in report.cards}
    assert cards_by_key["mock-dry-run"].status == "active"
    assert cards_by_key["mock-dry-run"].severity == "safe"
    assert cards_by_key["midi-port"].status == "none"
    assert cards_by_key["midi-port"].summary == "No MIDI port selected or opened."
    assert cards_by_key["arm-hardware"].status == "locked"
    assert cards_by_key["arm-hardware"].severity == "blocked"
    arm_action = cards_by_key["arm-hardware"].actions[0]
    assert arm_action.key == "arm-hardware"
    assert arm_action.enabled is False
    assert arm_action.reason == "dry-run mode is active"

    payload = to_live_gui_hardware_rail_model_json(report)
    assert payload["live_gui_hardware_rail"]["rail_status"] == "mock-safe"
    assert payload["live_gui_hardware_rail"]["cards"][0]["key"] == "mock-dry-run"
    assert payload["safety"][0] == "passive/read-only"
    json.dumps(payload, sort_keys=True)

    lines = format_live_gui_hardware_rail_model(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive live GUI hardware rail model"
    assert "Hardware rail summary:" in lines
    assert "- rail status: mock-safe" in lines
    assert "Right rail cards:" in lines
    assert "mock-dry-run: active" in text
    assert "- no MIDI port opened" in lines


def test_hardware_rail_ready_state_enables_arm_metadata_only() -> None:
    from rytm_randomizer.reports.live_gui_hardware_rail_model import (
        build_live_gui_hardware_rail_model,
    )

    report = build_live_gui_hardware_rail_model(
        session_label="Warehouse live session",
        device_label="Analog Rytm MKII",
        available_ports=(
            "Elektron Analog Rytm MKII 1",
            "Elektron Analog Four MKII 2",
        ),
        selected_port_name="Elektron Analog Rytm MKII 1",
        dry_run_active=False,
        hardware_requested=True,
    )

    assert report.rail_status == "ready"
    assert report.port_status == "selected"
    assert report.selected_port_name == "Elektron Analog Rytm MKII 1"
    assert report.available_ports == (
        "Elektron Analog Rytm MKII 1",
        "Elektron Analog Four MKII 2",
    )
    assert report.arm_status == "ready"
    assert report.arm_locked is False
    assert report.required_actions == ("operator-confirm-arm",)
    assert report.replay_commands == (
        "python -m rytm_randomizer.cli live-gui-hardware-rail-report "
        "--session 'Warehouse live session' "
        "--device 'Analog Rytm MKII' "
        "--port 'Elektron Analog Rytm MKII 1' "
        "--hardware-requested "
        "--dry-run off",
    )

    cards_by_key = {card.key: card for card in report.cards}
    assert cards_by_key["mock-dry-run"].status == "off"
    assert cards_by_key["midi-port"].status == "selected"
    assert cards_by_key["midi-port"].details == (
        "selected port: Elektron Analog Rytm MKII 1",
        "available ports: Elektron Analog Rytm MKII 1, Elektron Analog Four MKII 2",
    )
    arm_action = cards_by_key["arm-hardware"].actions[0]
    assert arm_action.enabled is True
    assert arm_action.reason == "all passive readiness prerequisites are satisfied"


def test_hardware_rail_blocks_arm_for_failed_safety_check() -> None:
    from rytm_randomizer.reports.live_gui_hardware_rail_model import (
        build_live_gui_hardware_rail_model,
    )

    report = build_live_gui_hardware_rail_model(
        available_ports=("Elektron Analog Rytm MKII 1",),
        selected_port_name="Elektron Analog Rytm MKII 1",
        dry_run_active=False,
        hardware_requested=True,
        safety_checks={
            "no_conflicting_sessions": True,
            "guards_enabled": True,
            "snapshot_compatible": False,
            "parameter_limits_safe": True,
        },
    )

    assert report.rail_status == "blocked"
    assert report.arm_status == "blocked"
    assert report.arm_locked is True
    assert report.safety_check_count == 4
    assert report.safety_checks_passed == 3
    assert report.failing_safety_checks == ("snapshot-compatible",)
    assert report.required_actions == ("resolve-safety-checks",)
    arm_card = next(card for card in report.cards if card.key == "arm-hardware")
    assert arm_card.summary == "Hardware arm is blocked by failed safety checks."
    assert arm_card.actions[0].enabled is False
    assert arm_card.actions[0].reason == "failed safety checks: snapshot-compatible"


def test_hardware_rail_locked_reasons_cover_no_port_and_no_request() -> None:
    from rytm_randomizer.reports.live_gui_hardware_rail_model import (
        build_live_gui_hardware_rail_model,
    )

    no_port_report = build_live_gui_hardware_rail_model(
        dry_run_active=False,
        hardware_requested=True,
    )
    no_port_arm_card = next(card for card in no_port_report.cards if card.key == "arm-hardware")
    assert no_port_report.required_actions == ("select-midi-port",)
    assert no_port_arm_card.actions[0].reason == "no MIDI port selected"

    no_request_report = build_live_gui_hardware_rail_model(
        available_ports=("Elektron Analog Rytm MKII 1",),
        selected_port_name="Elektron Analog Rytm MKII 1",
        dry_run_active=False,
        hardware_requested=False,
    )
    no_request_arm_card = next(
        card for card in no_request_report.cards if card.key == "arm-hardware"
    )
    assert no_request_report.required_actions == ("request-hardware-arm",)
    assert no_request_arm_card.actions[0].reason == "hardware arm has not been requested"


def test_hardware_rail_handles_missing_selected_port_and_dedupes_ports() -> None:
    from rytm_randomizer.reports.live_gui_hardware_rail_model import (
        build_live_gui_hardware_rail_model,
    )

    report = build_live_gui_hardware_rail_model(
        available_ports=(
            " Elektron Analog Rytm MKII 1 ",
            "Elektron Analog Rytm MKII 1",
            "Elektron Analog Four MKII 2",
        ),
        selected_port_name="Missing Port",
        dry_run_active=False,
        hardware_requested=True,
    )

    assert report.available_ports == (
        "Elektron Analog Rytm MKII 1",
        "Elektron Analog Four MKII 2",
    )
    assert report.port_status == "missing"
    assert report.selected_port_name == "Missing Port"
    assert report.arm_status == "locked"
    assert report.required_actions == ("select-valid-midi-port",)
    midi_card = next(card for card in report.cards if card.key == "midi-port")
    assert midi_card.status == "missing"
    assert midi_card.summary == "Selected MIDI port is not in the available passive list."


def test_hardware_rail_validation_edges() -> None:
    from rytm_randomizer.reports.live_gui_hardware_rail_model import (
        build_live_gui_hardware_rail_model,
    )

    with pytest.raises(ValueError, match="session_label"):
        build_live_gui_hardware_rail_model(session_label=" ")

    with pytest.raises(ValueError, match="device_label"):
        build_live_gui_hardware_rail_model(device_label=" ")

    with pytest.raises(ValueError, match="available_ports"):
        build_live_gui_hardware_rail_model(available_ports=(" ",))

    with pytest.raises(ValueError, match="safety_checks"):
        build_live_gui_hardware_rail_model(safety_checks={"guards_enabled": True})
