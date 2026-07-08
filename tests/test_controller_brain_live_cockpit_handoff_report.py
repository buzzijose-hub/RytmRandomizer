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


def test_cockpit_handoff_composes_feedback_frames_into_gui_ready_cards() -> None:
    from rytm_randomizer.reports.controller_brain_live_cockpit_handoff import (
        build_controller_brain_live_cockpit_handoff_report,
        format_controller_brain_live_cockpit_handoff_report,
    )

    report = build_controller_brain_live_cockpit_handoff_report(session_label="Warehouse arc")

    assert report.cockpit_handoff_version == "controller-brain-live-cockpit-handoff-v1"
    assert report.cockpit_handoff_status == "cockpit-handoff-passive"
    assert report.session_label == "Warehouse arc"
    assert report.source_report == "controller-brain-live-feedback-rehearsal-report"
    assert report.source_feedback_rehearsal_version == (
        "controller-brain-live-feedback-rehearsal-v1"
    )
    assert report.source_feedback_rehearsal_status == "feedback-output-blocked"
    assert report.source_feedback_frame_count == 27
    assert report.handoff_card_count == 27
    assert report.cockpit_panel_count == 4
    assert report.blocked_control_count == 7

    first_card = report.handoff_cards[0]
    assert first_card.card_key == "cockpit.card.state.global-preview-depth"
    assert first_card.source_frame_key == "feedback.frame.state.global-preview-depth"
    assert first_card.panel_key == "controller-feedback-preview"
    assert first_card.display_title == "Global Preview Depth"
    assert first_card.feedback_zone == "state-reducer"
    assert first_card.control_state == "disabled-preview-only"
    assert first_card.action_status == "blocked-passive-handoff"
    assert first_card.disabled_control == "Emit Feedback"
    assert first_card.passive is True

    panel_names = {panel.panel_key for panel in report.cockpit_panels}
    assert panel_names == {
        "controller-feedback-preview",
        "controller-output-gates",
        "blocked-runtime-controls",
        "operator-replay",
    }

    text = "\n".join(format_controller_brain_live_cockpit_handoff_report(report))
    assert "RytmRandomizer passive controller brain live Cockpit handoff" in text
    assert "Controller brain live Cockpit handoff:" in text
    assert "- source feedback: controller-brain-live-feedback-rehearsal-report" in text
    assert "- handoff cards: 27" in text
    assert (
        "- cockpit.card.state.global-preview-depth: "
        "controller-feedback-preview / blocked-passive-handoff"
    ) in text
    assert "- controller-feedback-preview: 27 card(s)" in text
    assert "Source: rytm_randomizer.reports.controller_brain_live_cockpit_handoff" in text


def test_cockpit_handoff_keeps_all_controls_disabled_and_passive() -> None:
    from rytm_randomizer.reports.controller_brain_live_cockpit_handoff import (
        build_controller_brain_live_cockpit_handoff_report,
    )

    report = build_controller_brain_live_cockpit_handoff_report()
    controls = {control.control_key: control for control in report.blocked_controls}

    assert controls["controller-input"].status == "blocked"
    assert controls["runtime-reducer"].status == "blocked"
    assert controls["websocket-dispatch"].status == "blocked"
    assert controls["controller-output"].status == "blocked"
    assert controls["controller-feedback"].status == "blocked"
    assert controls["midi-output"].status == "blocked"
    assert controls["snapshot-mutation"].status == "blocked"
    assert all(control.disabled for control in report.blocked_controls)

    assert "open controller input adapter" in report.blocked_actions
    assert "execute live state reducer" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "emit controller feedback" in report.blocked_actions
    assert "open MIDI output" in report.blocked_actions
    assert "mutate a snapshot" in report.blocked_actions
    assert "controller-brain Cockpit handoff metadata only" in report.safety_lines
    assert "composes controller-brain feedback rehearsal only" in report.safety_lines
    assert "handoff cards are GUI-ready metadata only" in report.safety_lines
    assert "no WebSocket dispatch" in report.safety_lines
    assert "no controller feedback emission" in report.safety_lines
    assert "no MIDI controller output" in report.safety_lines
    assert "no MIDI sending" in report.safety_lines
    assert "no port opening" in report.safety_lines


def test_cockpit_handoff_json_payload_is_deterministic_and_gui_safe() -> None:
    from rytm_randomizer.reports.controller_brain_live_cockpit_handoff import (
        build_controller_brain_live_cockpit_handoff_payload,
    )

    first = build_controller_brain_live_cockpit_handoff_payload(session_label="Warehouse arc")
    second = build_controller_brain_live_cockpit_handoff_payload(session_label="Warehouse arc")

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    model = first["controller_brain_live_cockpit_handoff"]
    assert model["cockpit_handoff_version"] == "controller-brain-live-cockpit-handoff-v1"
    assert model["cockpit_handoff_status"] == "cockpit-handoff-passive"
    assert model["source_report"] == "controller-brain-live-feedback-rehearsal-report"
    assert model["source_feedback_frame_count"] == 27
    assert model["handoff_card_count"] == 27
    assert model["cockpit_panel_count"] == 4
    assert model["blocked_control_count"] == 7
    assert model["handoff_cards"][0]["card_key"] == ("cockpit.card.state.global-preview-depth")
    assert model["handoff_cards"][0]["display_title"] == "Global Preview Depth"
    assert model["cockpit_panels"][0]["panel_key"] == "controller-feedback-preview"
    assert model["blocked_controls"][-1]["control_key"] == "snapshot-mutation"
    assert first["safety"][0] == "passive/read-only"

    forbidden_keys = {"midi_cc", "cc", "channel", "port", "controller_port"}
    for collection_name in ("handoff_cards", "cockpit_panels", "blocked_controls"):
        assert all(forbidden_keys.isdisjoint(row) for row in model[collection_name])


def test_cockpit_handoff_cli_supports_text_json_and_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_live_cockpit_handoff import (
        CONTROLLER_BRAIN_LIVE_COCKPIT_HANDOFF_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_LIVE_COCKPIT_HANDOFF_CLI_COMMAND.args_parser([]) == {
        "json_output": False
    }
    assert CONTROLLER_BRAIN_LIVE_COCKPIT_HANDOFF_CLI_COMMAND.args_parser(["--json"]) == {
        "json_output": True
    }
    with pytest.raises(
        ValueError,
        match="controller-brain-live-cockpit-handoff-report accepts only optional --json",
    ):
        CONTROLLER_BRAIN_LIVE_COCKPIT_HANDOFF_CLI_COMMAND.args_parser(["--arm"])

    assert main(["controller-brain-live-cockpit-handoff-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain live Cockpit handoff" in captured.out
    assert "cockpit.card.state.global-preview-depth" in captured.out
    assert "cockpit-handoff-passive" in captured.out
    assert captured.err == ""

    assert main(["controller-brain-live-cockpit-handoff-report", "--json"]) == 0
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_live_cockpit_handoff"]
    assert model["cockpit_handoff_status"] == "cockpit-handoff-passive"
    assert model["handoff_cards"][-1]["source_frame_key"] == (
        "feedback.frame.audit.snapshot-panic-home"
    )

    assert main(["controller-brain-live-cockpit-handoff-report", "--arm"]) == 2
    captured_error = capsys.readouterr()
    assert captured_error.out == ""
    assert "accepts only optional --json" in captured_error.err


def test_cockpit_handoff_cli_imports_no_real_midi_modules() -> None:
    forbidden_modules = repr(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main(["controller-brain-live-cockpit-handoff-report", "--json"])
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


def test_cockpit_handoff_help_mentions_disabled_gui_handoff() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("controller-brain-live-cockpit-handoff-report")

    assert help_text.startswith(
        "RytmRandomizer passive CLI: controller-brain-live-cockpit-handoff-report"
    )
    assert "controller-brain live Cockpit handoff" in help_text
    assert "GUI-ready handoff cards" in help_text
    assert "disabled Cockpit controls" in help_text
    assert "no WebSocket dispatch" in help_text
    assert "no controller feedback emission" in help_text
    assert "no MIDI controller output" in help_text
    assert "no MIDI sending" in help_text


def test_cockpit_handoff_defensive_helpers_keep_contract_stable() -> None:
    from rytm_randomizer.reports import controller_brain_live_cockpit_handoff as handoff

    assert handoff._cockpit_handoff_slug("feedback.frame.state.global_preview_depth") == (
        "feedback-frame-state-global-preview-depth"
    )
    assert handoff._cockpit_handoff_unique_tuple(("a",), ("a", "b")) == ("a", "b")
    assert handoff._cockpit_handoff_count(("a", "b")) == 2
    assert handoff._cockpit_title_from_suffix("global-preview-depth") == ("Global Preview Depth")

    card = handoff.ControllerBrainCockpitHandoffCard(
        card_key="cockpit.card.custom",
        order=3,
        source_frame_key="feedback.frame.custom",
        panel_key="controller-feedback-preview",
        display_title="Custom",
        display_line="custom display",
        feedback_zone="state-reducer",
        led_state="safe-ready",
        encoder_ring="custom",
        control_state="disabled-preview-only",
        action_status="blocked-passive-handoff",
        disabled_control="Emit Feedback",
        passive=True,
        evidence="custom evidence",
        blocked_action="none",
    )

    assert handoff._handoff_card_to_payload(card) == {
        "card_key": "cockpit.card.custom",
        "order": 3,
        "source_frame_key": "feedback.frame.custom",
        "panel_key": "controller-feedback-preview",
        "display_title": "Custom",
        "display_line": "custom display",
        "feedback_zone": "state-reducer",
        "led_state": "safe-ready",
        "encoder_ring": "custom",
        "control_state": "disabled-preview-only",
        "action_status": "blocked-passive-handoff",
        "disabled_control": "Emit Feedback",
        "passive": True,
        "evidence": "custom evidence",
        "blocked_action": "none",
    }
