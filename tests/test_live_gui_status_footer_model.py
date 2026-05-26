"""Tests for passive live GUI status/footer model reporting."""

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


def test_live_gui_status_footer_model_defaults_to_mock_safe_closed_hardware_state():
    from rytm_randomizer.reports.live_gui_status_footer_model import (
        build_live_gui_status_footer_model,
        format_live_gui_status_footer_model,
        to_live_gui_status_footer_model_json,
    )

    report = build_live_gui_status_footer_model(session_label="Warehouse rehearsal")

    assert report.status_footer_version == "live-gui-status-footer-model-v1"
    assert len(report.status_footer_id) == 16
    assert report.session_label == "Warehouse rehearsal"
    assert [item.key for item in report.items] == [
        "safety",
        "midi-port",
        "hardware",
        "mode",
        "send-state",
        "version",
    ]
    assert [item.order for item in report.items] == list(range(6))
    assert report.items[0].label == "Mock Safe"
    assert report.items[0].state == "safe"
    assert report.items[1].label == "No MIDI Port Open"
    assert report.items[1].state == "closed"
    assert report.items[2].label == "Hardware Off"
    assert report.items[2].action_enabled is False
    assert report.items[3].label == "Simulation / Mock"
    assert report.items[4].label == "no unsaved sends"
    assert report.items[5].value == "v1.34.0"
    assert "open MIDI port from status footer" in report.blocked_actions
    assert "send MIDI from status footer" in report.blocked_actions
    assert "arm hardware from status footer" in report.blocked_actions
    assert report.replay_commands == (
        "python -m rytm_randomizer.cli live-gui-status-footer-model-report "
        "--session-label 'Warehouse rehearsal'",
    )

    lines = format_live_gui_status_footer_model(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive live GUI status/footer model"
    assert "Status/footer summary:" in lines
    assert "Footer items:" in lines
    assert "Blocked active actions:" in lines
    assert "Passive GUI status/footer metadata only" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_live_gui_status_footer_model_json(report)
    footer = payload["live_gui_status_footer_model"]
    assert footer["status_footer_version"] == "live-gui-status-footer-model-v1"
    assert footer["status_footer_id"] == report.status_footer_id
    assert footer["items"][0]["key"] == "safety"
    assert footer["items"][1]["value"] == "No MIDI port selected"
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_status_footer_model_represents_detected_port_preview_and_unsaved_sends():
    from rytm_randomizer.reports.live_gui_status_footer_model import (
        build_live_gui_status_footer_model,
        to_live_gui_status_footer_model_json,
    )

    report = build_live_gui_status_footer_model(
        midi_port_name="Elektron Analog Rytm MKII 1",
        midi_port_open=False,
        hardware_connected=True,
        preview_active=True,
        unsaved_send_count=2,
    )

    midi = report.items[1]
    hardware = report.items[2]
    mode = report.items[3]
    send_state = report.items[4]
    assert midi.label == "MIDI Port Detected"
    assert midi.value == "Elektron Analog Rytm MKII 1"
    assert midi.state == "detected"
    assert hardware.label == "Hardware Detected / Off"
    assert hardware.state == "detected-off"
    assert mode.label == "Preview / Dry Run"
    assert mode.state == "preview"
    assert send_state.label == "2 unsaved sends"
    assert send_state.severity == "warning"

    payload = to_live_gui_status_footer_model_json(report)
    assert payload["live_gui_status_footer_model"]["items"][4]["value"] == (
        "Review or discard before arming hardware"
    )


def test_live_gui_status_footer_model_can_describe_open_or_guarded_states_without_io():
    from rytm_randomizer.reports.live_gui_status_footer_model import (
        build_live_gui_status_footer_model,
    )

    open_report = build_live_gui_status_footer_model(
        safety_state="armed",
        midi_port_name="Elektron Analog Rytm MKII 1",
        midi_port_open=True,
        hardware_connected=True,
        hardware_enabled=True,
        simulation_mode=False,
        app_version="v1.34.0-beta.3",
    )
    assert open_report.items[0].label == "Armed Metadata"
    assert open_report.items[0].severity == "warning"
    assert open_report.items[1].label == "MIDI Port Open"
    assert open_report.items[1].state == "open"
    assert open_report.items[2].label == "Hardware On"
    assert open_report.items[2].severity == "warning"
    assert open_report.items[3].label == "Operator Review"
    assert open_report.items[5].value == "v1.34.0-beta.3"
    assert "no MIDI sending" in open_report.safety_lines

    guarded_report = build_live_gui_status_footer_model(safety_state="blocked")
    assert guarded_report.items[0].label == "Blocked"
    assert guarded_report.items[0].severity == "critical"

    review_report = build_live_gui_status_footer_model(safety_state="review-needed")
    assert review_report.items[0].label == "Review Needed"
    assert review_report.items[0].severity == "warning"

    with pytest.raises(ValueError, match="session_label"):
        build_live_gui_status_footer_model(session_label=" ")

    with pytest.raises(ValueError, match="unsupported safety_state"):
        build_live_gui_status_footer_model(safety_state="unsafe")

    with pytest.raises(ValueError, match="unsaved_send_count"):
        build_live_gui_status_footer_model(unsaved_send_count=-1)


def test_live_gui_status_footer_model_json_is_serializable_and_passive():
    before_modules = set(sys.modules)

    from rytm_randomizer.reports.live_gui_status_footer_model import (
        build_live_gui_status_footer_model,
        to_live_gui_status_footer_model_json,
    )

    report = build_live_gui_status_footer_model()
    json.dumps(to_live_gui_status_footer_model_json(report), sort_keys=True)

    imported_modules = set(sys.modules) - before_modules
    assert not (set(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES) & imported_modules)
    assert all("no " in action for action in report.safety_lines if action.startswith("no "))
