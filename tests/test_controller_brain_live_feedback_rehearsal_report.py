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


def test_feedback_rehearsal_composes_dispatch_decisions_into_feedback_frames() -> None:
    from rytm_randomizer.reports.controller_brain_live_feedback_rehearsal import (
        build_controller_brain_live_feedback_rehearsal_report,
        format_controller_brain_live_feedback_rehearsal_report,
    )

    report = build_controller_brain_live_feedback_rehearsal_report(session_label="Warehouse arc")

    assert report.feedback_rehearsal_version == "controller-brain-live-feedback-rehearsal-v1"
    assert report.feedback_rehearsal_status == "feedback-output-blocked"
    assert report.session_label == "Warehouse arc"
    assert report.source_report == "controller-brain-live-dispatch-rehearsal-report"
    assert report.source_dispatch_rehearsal_version == (
        "controller-brain-live-dispatch-rehearsal-v1"
    )
    assert report.source_dispatch_rehearsal_status == "shadow-dispatch-blocked"
    assert report.source_dispatch_decision_count == 27
    assert report.feedback_frame_count == 27
    assert report.feedback_zone_count == 3
    assert report.output_gate_count == 6
    assert report.blocked_output_gate_count == 6

    first_frame = report.feedback_frames[0]
    assert first_frame.frame_key == "feedback.frame.state.global-preview-depth"
    assert first_frame.source_decision_key == "dispatch.decision.state.global-preview-depth"
    assert first_frame.feedback_zone == "state-reducer"
    assert first_frame.led_state == "safe-ready"
    assert first_frame.encoder_ring == "preview-depth"
    assert first_frame.display_line == "global preview depth -> blocked shadow state-reducer"
    assert first_frame.output_status == "blocked-metadata-only"
    assert first_frame.passive is True

    zone_names = {zone.name for zone in report.feedback_zones}
    assert zone_names == {"state-reducer", "queue-reducer", "audit-ledger"}

    text = "\n".join(format_controller_brain_live_feedback_rehearsal_report(report))
    assert "RytmRandomizer passive controller brain live feedback rehearsal" in text
    assert "Controller brain live feedback rehearsal:" in text
    assert "- source dispatch: controller-brain-live-dispatch-rehearsal-report" in text
    assert "- feedback frames: 27" in text
    assert (
        "- feedback.frame.state.global-preview-depth: state-reducer / blocked-metadata-only" in text
    )
    assert "- led-output: blocked / blocked=True" in text
    assert "Source: rytm_randomizer.reports.controller_brain_live_feedback_rehearsal" in text


def test_feedback_rehearsal_keeps_all_feedback_outputs_blocked() -> None:
    from rytm_randomizer.reports.controller_brain_live_feedback_rehearsal import (
        build_controller_brain_live_feedback_rehearsal_report,
    )

    report = build_controller_brain_live_feedback_rehearsal_report()
    gates = {gate.name: gate for gate in report.output_gates}

    assert gates["controller-output"].status == "blocked"
    assert gates["led-output"].status == "blocked"
    assert gates["ring-output"].status == "blocked"
    assert gates["display-output"].status == "blocked"
    assert gates["websocket-feedback"].status == "blocked"
    assert gates["hardware-feedback"].status == "blocked"
    assert all(gate.blocked for gate in report.output_gates)

    assert "emit controller feedback" in report.blocked_actions
    assert "write controller LED state" in report.blocked_actions
    assert "write controller encoder ring state" in report.blocked_actions
    assert "write controller display text" in report.blocked_actions
    assert "dispatch Cockpit WebSocket feedback" in report.blocked_actions
    assert "open controller output adapter" in report.blocked_actions
    assert "controller-brain feedback rehearsal metadata only" in report.safety_lines
    assert "composes controller-brain dispatch rehearsal only" in report.safety_lines
    assert "feedback frames are metadata only" in report.safety_lines
    assert "no controller feedback emission" in report.safety_lines
    assert "no WebSocket feedback dispatch" in report.safety_lines
    assert "no MIDI controller output" in report.safety_lines
    assert "no MIDI sending" in report.safety_lines
    assert "no port opening" in report.safety_lines


def test_feedback_rehearsal_json_payload_is_deterministic_and_side_effect_free() -> None:
    from rytm_randomizer.reports.controller_brain_live_feedback_rehearsal import (
        build_controller_brain_live_feedback_rehearsal_payload,
    )

    first = build_controller_brain_live_feedback_rehearsal_payload(session_label="Warehouse arc")
    second = build_controller_brain_live_feedback_rehearsal_payload(session_label="Warehouse arc")

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    model = first["controller_brain_live_feedback_rehearsal"]
    assert model["feedback_rehearsal_version"] == ("controller-brain-live-feedback-rehearsal-v1")
    assert model["feedback_rehearsal_status"] == "feedback-output-blocked"
    assert model["source_report"] == "controller-brain-live-dispatch-rehearsal-report"
    assert model["source_dispatch_rehearsal_version"] == (
        "controller-brain-live-dispatch-rehearsal-v1"
    )
    assert model["source_dispatch_decision_count"] == 27
    assert model["feedback_frame_count"] == 27
    assert model["feedback_zone_count"] == 3
    assert model["output_gate_count"] == 6
    assert model["blocked_output_gate_count"] == 6
    assert model["feedback_frames"][0]["frame_key"] == ("feedback.frame.state.global-preview-depth")
    assert model["feedback_frames"][0]["display_line"] == (
        "global preview depth -> blocked shadow state-reducer"
    )
    assert model["feedback_zones"][0]["name"] == "state-reducer"
    assert model["output_gates"][-1]["name"] == "hardware-feedback"
    assert first["safety"][0] == "passive/read-only"

    forbidden_keys = {"midi_cc", "cc", "channel", "port", "controller_port"}
    for collection_name in ("feedback_frames", "feedback_zones", "output_gates"):
        assert all(forbidden_keys.isdisjoint(row) for row in model[collection_name])


def test_feedback_rehearsal_cli_supports_text_json_and_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_live_feedback_rehearsal import (
        CONTROLLER_BRAIN_LIVE_FEEDBACK_REHEARSAL_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_LIVE_FEEDBACK_REHEARSAL_CLI_COMMAND.args_parser([]) == {
        "json_output": False
    }
    assert CONTROLLER_BRAIN_LIVE_FEEDBACK_REHEARSAL_CLI_COMMAND.args_parser(["--json"]) == {
        "json_output": True
    }
    with pytest.raises(
        ValueError,
        match="controller-brain-live-feedback-rehearsal-report accepts only optional --json",
    ):
        CONTROLLER_BRAIN_LIVE_FEEDBACK_REHEARSAL_CLI_COMMAND.args_parser(["--arm"])

    assert main(["controller-brain-live-feedback-rehearsal-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain live feedback rehearsal" in captured.out
    assert "feedback.frame.state.global-preview-depth" in captured.out
    assert "feedback-output-blocked" in captured.out
    assert captured.err == ""

    assert main(["controller-brain-live-feedback-rehearsal-report", "--json"]) == 0
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_live_feedback_rehearsal"]
    assert model["feedback_rehearsal_status"] == "feedback-output-blocked"
    assert model["feedback_frames"][-1]["source_decision_key"] == (
        "dispatch.decision.audit.snapshot-panic-home"
    )

    assert main(["controller-brain-live-feedback-rehearsal-report", "--arm"]) == 2
    captured_error = capsys.readouterr()
    assert captured_error.out == ""
    assert "accepts only optional --json" in captured_error.err


def test_feedback_rehearsal_cli_imports_no_real_midi_modules() -> None:
    forbidden_modules = repr(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main(["controller-brain-live-feedback-rehearsal-report", "--json"])
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


def test_feedback_rehearsal_help_mentions_passive_feedback_outputs() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("controller-brain-live-feedback-rehearsal-report")

    assert help_text.startswith(
        "RytmRandomizer passive CLI: controller-brain-live-feedback-rehearsal-report"
    )
    assert "controller-brain live feedback rehearsal" in help_text
    assert "feedback frames" in help_text
    assert "controller output adapter" in help_text
    assert "no MIDI controller output" in help_text
    assert "no WebSocket feedback dispatch" in help_text
    assert "no MIDI sending" in help_text


def test_feedback_rehearsal_defensive_helpers_keep_contract_stable() -> None:
    from rytm_randomizer.reports import (
        controller_brain_live_feedback_rehearsal as feedback_rehearsal,
    )

    assert (
        feedback_rehearsal._feedback_rehearsal_slug("dispatch.decision.state.global_preview_depth")
        == "dispatch-decision-state-global-preview-depth"
    )
    assert feedback_rehearsal._feedback_rehearsal_unique_tuple(("a",), ("a", "b")) == (
        "a",
        "b",
    )
    assert feedback_rehearsal._feedback_rehearsal_count(("a", "b")) == 2
    assert feedback_rehearsal._feedback_label_from_suffix("global-preview-depth") == (
        "global preview depth"
    )

    frame = feedback_rehearsal.ControllerBrainFeedbackFrame(
        frame_key="feedback.frame.custom",
        order=3,
        source_decision_key="dispatch.decision.custom",
        feedback_zone="state-reducer",
        led_state="safe-ready",
        encoder_ring="custom",
        display_line="custom display",
        output_status="blocked-metadata-only",
        passive=True,
        evidence="custom evidence",
        blocked_action="none",
    )

    assert feedback_rehearsal._feedback_frame_to_payload(frame) == {
        "frame_key": "feedback.frame.custom",
        "order": 3,
        "source_decision_key": "dispatch.decision.custom",
        "feedback_zone": "state-reducer",
        "led_state": "safe-ready",
        "encoder_ring": "custom",
        "display_line": "custom display",
        "output_status": "blocked-metadata-only",
        "passive": True,
        "evidence": "custom evidence",
        "blocked_action": "none",
    }
