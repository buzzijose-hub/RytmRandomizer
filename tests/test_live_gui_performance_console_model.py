"""Tests for the passive Cockpit performance console packet."""

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


def test_performance_console_model_composes_live_cockpit_sections() -> None:
    from rytm_randomizer.reports.live_gui_performance_console_model import (
        build_live_gui_performance_console_model,
    )

    model = build_live_gui_performance_console_model(session_label="Warehouse arc")

    assert model.console_version == "live-gui-performance-console-v1"
    assert model.source_module == "reports.live_gui_performance_console_model"
    assert len(model.console_id) == 16
    assert model.session_label == "Warehouse arc"
    assert model.console_status == "mock-safe"
    assert model.hardware_mode == "passive"

    assert model.device_inventory["device_count"] == 2
    device_ids = [card["device_id"] for card in model.device_inventory["cards"]]
    assert device_ids == ["analog_rytm_mk2", "analog_four_mk2"]

    assert model.rytm_pad_surface["pad_count"] == 12
    assert len(model.rytm_pad_surface["cards"]) == 12
    assert model.rytm_pad_surface["cards"][0]["pad"] == 1
    assert model.rytm_pad_surface["cards"][-1]["pad"] == 12

    assert model.performance_flow["flow_id"] == "oxi-rytm-a4-performance-flow"
    assert model.performance_flow["analog_four_set_plan"]["set_name"] == "warehouse-arc"
    assert model.performance_flow["analog_four_set_plan"]["current_macro"] == "home"
    assert model.performance_flow["steps"][1]["key"] == "kit-core"

    assert model.style_queue["deck_status"] == "passive-ready"
    assert len(model.style_queue["crate_cards"]) >= 7
    assert len(model.style_queue["queue_cards"]) >= 3
    assert len(model.style_queue["journal_cards"]) >= 1

    assert model.snapshot_history["session_label"] == "Warehouse arc"
    assert model.snapshot_history["entry_count"] == 3
    assert model.snapshot_history["current_id"] == "console-snap-03"
    assert model.command_queue["session_label"] == "Warehouse arc"
    assert model.command_queue["last_actions"][0]["snapshot_id"] == "console-snap-03"
    assert model.safety_checklist["checklist_status"] == "passed"
    assert model.safety_checklist["arm_gate"]["enabled"] is False

    assert "open_midi_port_without_arm" in model.blocked_actions
    assert "a4_outbound_macro_send" in model.blocked_actions
    assert "dispatch queued command from model" in model.blocked_actions
    assert "send MIDI from snapshot history" in model.blocked_actions
    assert "no MIDI sending" in model.safety_lines
    assert "no port opening" in model.safety_lines
    assert "no hardware mutation" in model.safety_lines
    assert model.replay_commands == (
        "python -m rytm_randomizer.cli live-gui-performance-console-report",
        "python -m rytm_randomizer.cli live-gui-performance-console-report --json",
    )


def test_performance_console_model_rejects_blank_session_label() -> None:
    from rytm_randomizer.reports.live_gui_performance_console_model import (
        build_live_gui_performance_console_model,
    )

    with pytest.raises(ValueError, match="session_label must not be blank"):
        build_live_gui_performance_console_model(session_label="   ")


def test_performance_console_model_ignores_malformed_optional_payload_sequences(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.reports import live_gui_performance_console_model as report

    monkeypatch.setattr(
        report,
        "live_gui_device_inventory_model_payload",
        lambda _source: {
            "device_count": 2,
            "blocked_actions": "not-a-sequence",
            "safety": "not-a-sequence",
        },
    )

    model = report.build_live_gui_performance_console_model()

    assert "not-a-sequence" not in model.blocked_actions
    assert "not-a-sequence" not in model.safety_lines


def test_performance_console_payload_is_json_safe_and_passive() -> None:
    before_modules = set(sys.modules)

    from rytm_randomizer.reports.live_gui_performance_console_model import (
        live_gui_performance_console_model_payload,
    )

    payload = live_gui_performance_console_model_payload()
    json.dumps(payload, sort_keys=True)

    model = payload["live_gui_performance_console"]
    assert model["console_version"] == "live-gui-performance-console-v1"
    assert model["device_inventory"]["cards"][1]["device_id"] == "analog_four_mk2"
    assert model["rytm_pad_surface"]["pad_count"] == 12
    assert model["performance_flow"]["analog_four_set_plan"]["step_count"] == 5
    assert model["snapshot_history"]["entries"][0]["snapshot_id"] == "console-snap-01"
    assert payload["safety"][0] == "passive/read-only"

    imported_modules = set(sys.modules) - before_modules
    assert not (set(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES) & imported_modules)


def test_performance_console_report_is_operator_readable() -> None:
    from rytm_randomizer.reports.live_gui_performance_console_model import (
        build_live_gui_performance_console_model,
        format_live_gui_performance_console_model_report,
    )

    lines = format_live_gui_performance_console_model_report(
        build_live_gui_performance_console_model(session_label="Warehouse arc")
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Cockpit performance console model"
    assert "Console summary:" in lines
    assert "- session: Warehouse arc" in lines
    assert "- status: mock-safe" in lines
    assert "Device rail:" in lines
    assert "- analog_rytm_mk2 / Elektron Analog Rytm MKII / 12 tracks" in lines
    assert "- analog_four_mk2 / Elektron Analog Four MKII / 4 tracks" in lines
    assert "Rytm pad surface:" in lines
    assert "- pads: 12" in lines
    assert "Performance flow:" in lines
    assert "- current: capture-anchor" in lines
    assert "A4 set plan:" in lines
    assert "- set: warehouse-arc" in lines
    assert "Style queue and journal:" in lines
    assert "Snapshot history:" in lines
    assert "- current: console-snap-03" in lines
    assert "Command queue:" in lines
    assert "Safety checklist:" in lines
    assert "Blocked active actions:" in lines
    assert "Safety:" in text
    assert "no MIDI sending" in text


def test_performance_console_cli_text_and_json_modes(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    assert main(["live-gui-performance-console-report"]) == 0
    text_output = capsys.readouterr().out
    assert "RytmRandomizer passive Cockpit performance console model" in text_output
    assert "A4 set plan:" in text_output
    assert "no MIDI sending" in text_output

    assert main(["live-gui-performance-console-report", "--json"]) == 0
    json_output = capsys.readouterr().out
    payload = json.loads(json_output)
    model = payload["live_gui_performance_console"]
    assert model["console_status"] == "mock-safe"
    assert model["device_inventory"]["device_count"] == 2
    assert model["performance_flow"]["analog_four_set_plan"]["set_name"] == "warehouse-arc"


def test_performance_console_cli_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    assert main(["live-gui-performance-console-report", "--arm"]) == 2
    captured = capsys.readouterr()

    assert captured.out == ""
    assert "live-gui-performance-console-report accepts only optional --json" in captured.err
