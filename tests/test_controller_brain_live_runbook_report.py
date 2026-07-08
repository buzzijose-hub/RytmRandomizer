from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
    "rytm_randomizer.mido_provider",
)


def test_live_runbook_composes_controller_oxi_and_console_packets() -> None:
    from rytm_randomizer.reports.controller_brain_live_runbook import (
        build_controller_brain_live_runbook_report,
        format_controller_brain_live_runbook_report,
    )

    report = build_controller_brain_live_runbook_report(session_label="Warehouse arc")

    assert report.runbook_version == "controller-brain-live-runbook-v1"
    assert report.runbook_status == "passive-ready"
    assert report.session_label == "Warehouse arc"
    assert report.controller_profile_key == "generic-16-encoder-performance"
    assert report.controller_template_row_count == 112
    assert report.controller_page_count == 7
    assert report.gesture_count == 9
    assert report.live_chapter_count == 7
    assert report.console_status == "mock-safe"
    assert report.console_hardware_mode == "passive"
    assert report.source_reports == (
        "controller-brain-rehearsal-report",
        "oxi-live-set-strategy-report",
        "live-gui-performance-console-report",
    )

    by_intent = {step.intent_key: step for step in report.runbook_steps}
    assert tuple(by_intent) == (
        "global.preview_depth",
        "macro.industrial",
        "rytm.pad5.source_amount",
        "rytm.pad6.source_amount",
        "rytm.pad12.source_amount",
        "a4.track1.macro_depth",
        "crate.dark_hypnotic",
        "queue.next_1",
        "snapshot.panic_home",
    )
    assert by_intent["global.preview_depth"].stage_action == "adjust passive preview depth"
    assert by_intent["macro.industrial"].stage_action == "stage Rytm macro industrial"
    assert by_intent["rytm.pad5.source_amount"].stage_action == "stage Pad 5 SRC movement"
    assert by_intent["rytm.pad6.source_amount"].stage_action == "stage Pad 6 SRC movement"
    assert (
        by_intent["rytm.pad12.source_amount"].stage_action == "confirm optional Pad 12 SRC mapping"
    )
    assert by_intent["a4.track1.macro_depth"].stage_action == "review A4 macro runway"
    assert by_intent["crate.dark_hypnotic"].stage_action == "select Dark Hypnotic crate"
    assert by_intent["queue.next_1"].stage_action == "stage upcoming queue move"
    assert by_intent["snapshot.panic_home"].stage_action == "recover captured anchor"
    assert {step.fire_policy for step in report.runbook_steps} == {
        "blocked until approved controller bridge"
    }
    assert by_intent["snapshot.panic_home"].recovery_action == "captured_anchor"

    text = "\n".join(format_controller_brain_live_runbook_report(report))
    assert "RytmRandomizer passive controller brain live runbook" in text
    assert "Controller profile: generic-16-encoder-performance" in text
    assert "- runbook step: global.preview_depth -> adjust passive preview depth" in text
    assert "- runbook step: snapshot.panic_home -> recover captured anchor" in text
    assert "Source: rytm_randomizer.reports.controller_brain_live_runbook" in text


def test_live_runbook_readiness_blocks_all_active_controller_and_hardware_paths() -> None:
    from rytm_randomizer.reports.controller_brain_live_runbook import (
        build_controller_brain_live_runbook_report,
    )

    report = build_controller_brain_live_runbook_report()
    gates = {gate.name: gate for gate in report.readiness_gates}

    assert gates["controller-template"].status == "ready"
    assert gates["controller-template"].ready is True
    assert gates["controller-input"].status == "blocked"
    assert gates["controller-input"].ready is False
    assert gates["raw-cc-capture"].status == "blocked"
    assert gates["websocket-dispatch"].status == "blocked"
    assert gates["midi-output"].status == "blocked"
    assert gates["hardware-send"].status == "blocked"
    assert gates["snapshot-mutation"].status == "blocked"

    assert "open MIDI controller input" in report.blocked_actions
    assert "MIDI learn or raw CC capture" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "open MIDI output" in report.blocked_actions
    assert "send hardware MIDI" in report.blocked_actions
    assert "send operator package from Cockpit console" in report.blocked_actions
    assert "no MIDI controller input" in report.safety_lines
    assert "no WebSocket command dispatch" in report.safety_lines
    assert "no MIDI sending" in report.safety_lines
    assert "no port opening" in report.safety_lines


def test_live_runbook_json_payload_is_deterministic_and_gui_ready() -> None:
    from rytm_randomizer.reports.controller_brain_live_runbook import (
        build_controller_brain_live_runbook_payload,
    )

    first = build_controller_brain_live_runbook_payload(session_label="Warehouse arc")
    second = build_controller_brain_live_runbook_payload(session_label="Warehouse arc")

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    model = first["controller_brain_live_runbook"]
    assert model["runbook_version"] == "controller-brain-live-runbook-v1"
    assert model["controller_template_row_count"] == 112
    assert model["controller_page_count"] == 7
    assert model["live_chapter_count"] == 7
    assert model["console_status"] == "mock-safe"
    assert model["source_reports"] == [
        "controller-brain-rehearsal-report",
        "oxi-live-set-strategy-report",
        "live-gui-performance-console-report",
    ]
    assert model["runbook_steps"][0]["intent_key"] == "global.preview_depth"
    assert model["runbook_steps"][-1]["intent_key"] == "snapshot.panic_home"
    assert model["readiness_gates"][0]["name"] == "controller-template"
    assert model["readiness_gates"][1]["ready"] is False
    assert first["safety"][0] == "passive/read-only"

    forbidden_keys = {"midi_cc", "cc", "channel", "port", "controller_port"}
    assert all(forbidden_keys.isdisjoint(step) for step in model["runbook_steps"])
    assert all(forbidden_keys.isdisjoint(gate) for gate in model["readiness_gates"])


def test_live_runbook_cli_supports_text_json_and_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_live_runbook import (
        CONTROLLER_BRAIN_LIVE_RUNBOOK_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_LIVE_RUNBOOK_CLI_COMMAND.args_parser([]) == {"json_output": False}
    assert CONTROLLER_BRAIN_LIVE_RUNBOOK_CLI_COMMAND.args_parser(["--json"]) == {
        "json_output": True
    }
    with pytest.raises(
        ValueError,
        match="controller-brain-live-runbook-report accepts only optional --json",
    ):
        CONTROLLER_BRAIN_LIVE_RUNBOOK_CLI_COMMAND.args_parser(["--arm"])

    assert main(["controller-brain-live-runbook-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain live runbook" in captured.out
    assert "blocked until approved controller bridge" in captured.out
    assert captured.err == ""

    assert main(["controller-brain-live-runbook-report", "--json"]) == 0
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_live_runbook"]
    assert model["runbook_status"] == "passive-ready"
    assert model["runbook_steps"][-1]["intent_key"] == "snapshot.panic_home"

    assert main(["controller-brain-live-runbook-report", "--arm"]) == 2
    captured_error = capsys.readouterr()
    assert captured_error.out == ""
    assert "accepts only optional --json" in captured_error.err


def test_live_runbook_cli_imports_no_real_midi_modules() -> None:
    forbidden_modules = repr(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main(["controller-brain-live-runbook-report", "--json"])
assert exit_code == 0, exit_code
for module_name in {forbidden_modules}:
    assert module_name not in sys.modules, module_name
"""
    passive_result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert passive_result.returncode == 0, passive_result.stderr


def test_live_runbook_help_mentions_passive_controller_contract() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("controller-brain-live-runbook-report")

    assert help_text.startswith("RytmRandomizer passive CLI: controller-brain-live-runbook-report")
    assert "controller-brain live runbook" in help_text
    assert "no MIDI controller input" in help_text
    assert "no WebSocket command dispatch" in help_text
    assert "no MIDI sending" in help_text


def test_live_runbook_defensive_payload_helpers_keep_malformed_inputs_passive() -> None:
    from rytm_randomizer.reports import controller_brain_live_runbook as runbook

    assert runbook._runbook_payload_dict({"bad": []}, "bad") == {}
    assert runbook._runbook_payload_list({"bad": ()}, "bad") == []
    assert runbook._runbook_payload_string({"bad": 1}, "bad") == ""
    assert runbook._runbook_payload_int({"bad": "1"}, "bad") == 0
    assert runbook._runbook_string_tuple({"bad": "not-a-sequence"}, "bad") == ()
    assert runbook._runbook_stage_action("custom.intent") == "stage intent custom.intent"

    steps = runbook._runbook_steps(
        (
            {
                "step": 1,
                "resolved_intent_key": "custom.intent",
                "assignment_key": "custom.assignment",
            },
            "malformed-outcome",
        )
    )

    assert len(steps) == 1
    assert steps[0].intent_key == "custom.intent"
    assert steps[0].stage_action == "stage intent custom.intent"
