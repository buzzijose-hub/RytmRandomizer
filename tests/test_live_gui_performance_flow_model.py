"""Tests for the passive live GUI performance flow model."""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.fast


def test_performance_flow_model_exposes_cockpit_steps_and_safety() -> None:
    from rytm_randomizer.reports.live_gui_performance_flow_model import (
        build_live_gui_performance_flow_model,
    )

    model = build_live_gui_performance_flow_model()

    assert model.model_version == "live-gui-performance-flow-model-v1"
    assert model.source_module == "reports.live_gui_performance_flow_model"
    assert model.flow_id == "oxi-rytm-a4-performance-flow"
    assert model.flow_status == "mock-safe"
    assert model.current_step_key == "capture-anchor"
    assert tuple(step.key for step in model.steps) == (
        "capture-anchor",
        "kit-core",
        "hard-groove",
        "industrial",
        "dub-pressure",
        "transition",
        "home",
    )
    assert model.steps[0].rytm_command == "kit/resnapshot"
    assert model.steps[0].analog_four_action == "A4 soft-capture reference"
    assert model.steps[1].send_policy == "stage-review-send"
    assert model.steps[-1].recovery_action == "kit/resnapshot"
    assert "a4_outbound_macro_send" in model.blocked_actions
    assert "unattended_hardware_behavior" in model.blocked_actions
    assert "no MIDI sending" in model.safety_lines
    assert "no port opening" in model.safety_lines
    assert model.analog_four_readiness.readiness == "review-ready"
    assert (
        model.analog_four_readiness.command
        == "python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report "
        "hard-groove --seed 0 --intensity 4 --limit 4"
    )
    assert "a4_outbound_macro_send" in model.analog_four_readiness.blocked_active_actions
    assert model.analog_four_set_plan.set_name == "warehouse-arc"
    assert model.analog_four_set_plan.current_macro == "home"
    assert model.analog_four_set_plan.up_next_macros == (
        "hard-groove",
        "dub-pressure",
        "industrial-transition",
        "home",
    )
    assert model.analog_four_set_plan.step_count == 5
    assert (
        model.analog_four_set_plan.replay_command
        == "python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --json"
    )
    assert "A4 full macro SEND" in model.analog_four_set_plan.blocked_active_actions


def test_performance_flow_payload_is_gui_ready_and_json_safe() -> None:
    from rytm_randomizer.reports.live_gui_performance_flow_model import (
        build_live_gui_performance_flow_model,
        live_gui_performance_flow_model_payload,
    )

    model = build_live_gui_performance_flow_model()
    payload = live_gui_performance_flow_model_payload(model)

    json.dumps(payload, sort_keys=True)
    flow_payload = payload["live_gui_performance_flow_model"]
    assert flow_payload["model_version"] == model.model_version
    assert flow_payload["source_module"] == "reports.live_gui_performance_flow_model"
    assert flow_payload["flow_status"] == "mock-safe"
    assert flow_payload["current_step_key"] == "capture-anchor"
    assert flow_payload["steps"][0]["key"] == "capture-anchor"
    assert flow_payload["steps"][3]["key"] == "industrial"
    assert isinstance(flow_payload["steps"], list)
    assert isinstance(flow_payload["blocked_actions"], list)
    assert isinstance(flow_payload["safety_lines"], list)
    assert flow_payload["replay_commands"] == list(model.replay_commands)
    assert flow_payload["analog_four_readiness"] == {
        "readiness": "review-ready",
        "command": model.analog_four_readiness.command,
        "summary": model.analog_four_readiness.summary,
        "blocked_active_actions": list(model.analog_four_readiness.blocked_active_actions),
    }
    assert flow_payload["analog_four_set_plan"] == {
        "set_name": "warehouse-arc",
        "current_macro": "home",
        "up_next_macros": [
            "hard-groove",
            "dub-pressure",
            "industrial-transition",
            "home",
        ],
        "step_count": 5,
        "replay_command": (
            "python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --json"
        ),
        "summary": model.analog_four_set_plan.summary,
        "blocked_active_actions": list(model.analog_four_set_plan.blocked_active_actions),
    }


def test_performance_flow_report_is_operator_readable_and_passive() -> None:
    from rytm_randomizer.reports.live_gui_performance_flow_model import (
        build_live_gui_performance_flow_model,
        format_live_gui_performance_flow_model_report,
    )

    lines = format_live_gui_performance_flow_model_report(build_live_gui_performance_flow_model())
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive live GUI performance flow model"
    assert "Performance flow:" in text
    assert "- current: capture-anchor | kit/resnapshot | receive-only | safe" in text
    assert "- next: kit-core | kit-core | stage-review-send | staged" in text
    assert "Analog Four review-only actions stay candidate metadata." in text
    assert "Passive safety:" in text
    assert "no GUI launch" in text
    assert "no MIDI sending" in text
    assert "no port opening" in text
    assert "A4 macro readiness:" in text
    assert "analog-four-oxi-macro-readiness-report hard-groove" in text
    assert "full macro SEND remains blocked" in text
    assert "A4 set plan:" in text
    assert "- set: warehouse-arc" in text
    assert "- current macro: home" in text
    assert "- up next: hard-groove, dub-pressure, industrial-transition, home" in text
    assert "analog-four-oxi-macro-set-planner-report --json" in text

    kit_core_lines = format_live_gui_performance_flow_model_report(
        build_live_gui_performance_flow_model(current_step_key="kit-core")
    )
    assert "- anchor: capture-anchor | kit/resnapshot | receive-only | safe" in "\n".join(
        kit_core_lines
    )


def test_performance_flow_cli_text_and_json_modes(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    assert main(["live-gui-performance-flow-model-report"]) == 0
    text_output = capsys.readouterr().out
    assert "RytmRandomizer passive live GUI performance flow model" in text_output
    assert "Performance flow:" in text_output
    assert "no MIDI sending" in text_output

    assert main(["live-gui-performance-flow-model-report", "--json"]) == 0
    json_output = capsys.readouterr().out
    payload = json.loads(json_output)
    flow_payload = payload["live_gui_performance_flow_model"]
    assert flow_payload["flow_id"] == "oxi-rytm-a4-performance-flow"
    assert flow_payload["steps"][0]["key"] == "capture-anchor"
    assert "open_midi_port_without_arm" in flow_payload["blocked_actions"]
    assert flow_payload["analog_four_readiness"]["readiness"] == "review-ready"
    assert flow_payload["analog_four_set_plan"]["set_name"] == "warehouse-arc"
    assert flow_payload["analog_four_set_plan"]["current_macro"] == "home"


def test_performance_flow_cli_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    assert main(["live-gui-performance-flow-model-report", "--arm"]) == 2
    captured = capsys.readouterr()

    assert captured.out == ""
    assert "live-gui-performance-flow-model-report accepts only optional --json" in captured.err
