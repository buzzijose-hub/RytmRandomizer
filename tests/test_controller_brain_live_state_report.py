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


def test_live_state_composes_runbook_into_controller_state_rows() -> None:
    from rytm_randomizer.reports.controller_brain_live_state import (
        build_controller_brain_live_state_report,
        format_controller_brain_live_state_report,
    )

    report = build_controller_brain_live_state_report(session_label="Warehouse arc")

    assert report.live_state_version == "controller-brain-live-state-v1"
    assert report.live_state_status == "passive-bridge-blocked"
    assert report.session_label == "Warehouse arc"
    assert report.source_report == "controller-brain-live-runbook-report"
    assert report.source_runbook_version == "controller-brain-live-runbook-v1"
    assert report.controller_profile_key == "generic-16-encoder-performance"
    assert report.state_row_count == 9
    assert report.queued_intent_count == 9
    assert report.audit_event_count == 9

    by_intent = {row.intent_key: row for row in report.state_rows}
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
    assert by_intent["global.preview_depth"].state_key == "state.global-preview-depth"
    assert by_intent["global.preview_depth"].preview_state == "preview-staged"
    assert by_intent["global.preview_depth"].fire_state == "blocked"
    assert by_intent["global.preview_depth"].queued_intent_key == ("queued.global-preview-depth")
    assert by_intent["macro.industrial"].operator_goal == "choose the industrial macro direction"
    assert by_intent["snapshot.panic_home"].recovery_action == "captured_anchor"
    assert {row.fire_policy for row in report.state_rows} == {
        "blocked until approved controller bridge"
    }

    text = "\n".join(format_controller_brain_live_state_report(report))
    assert "RytmRandomizer passive controller brain live state" in text
    assert "Controller brain live state:" in text
    assert "- source runbook: controller-brain-live-runbook-report" in text
    assert "- state row: state.global-preview-depth -> global.preview_depth" in text
    assert "- queued.global-preview-depth: preview-staged / blocked" in text
    assert "- audit.global-preview-depth: stage=queued fire=blocked" in text
    assert "Source: rytm_randomizer.reports.controller_brain_live_state" in text


def test_live_state_readiness_blocks_active_controller_bridge_paths() -> None:
    from rytm_randomizer.reports.controller_brain_live_state import (
        build_controller_brain_live_state_report,
    )

    report = build_controller_brain_live_state_report()
    gates = {gate.name: gate for gate in report.readiness_gates}

    assert gates["controller-template"].status == "ready"
    assert gates["state-reducer"].status == "ready"
    assert gates["audit-ledger"].status == "ready"
    assert gates["controller-input"].status == "blocked"
    assert gates["raw-cc-capture"].status == "blocked"
    assert gates["websocket-dispatch"].status == "blocked"
    assert gates["midi-output"].status == "blocked"
    assert gates["hardware-send"].status == "blocked"
    assert gates["snapshot-mutation"].status == "blocked"

    assert "apply live state reducer" in report.blocked_actions
    assert "dispatch controller runtime event" in report.blocked_actions
    assert "write controller audit ledger" in report.blocked_actions
    assert "emit controller feedback" in report.blocked_actions
    assert "open MIDI controller input" in report.blocked_actions
    assert "MIDI learn or raw CC capture" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "send hardware MIDI" in report.blocked_actions
    assert "controller-brain live state metadata only" in report.safety_lines
    assert "composes controller-brain live runbook only" in report.safety_lines
    assert "no MIDI controller input" in report.safety_lines
    assert "no WebSocket command dispatch" in report.safety_lines
    assert "no MIDI sending" in report.safety_lines
    assert "no port opening" in report.safety_lines
    assert "no snapshot mutation" in report.safety_lines


def test_live_state_json_payload_is_deterministic_and_bridge_ready() -> None:
    from rytm_randomizer.reports.controller_brain_live_state import (
        build_controller_brain_live_state_payload,
    )

    first = build_controller_brain_live_state_payload(session_label="Warehouse arc")
    second = build_controller_brain_live_state_payload(session_label="Warehouse arc")

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    model = first["controller_brain_live_state"]
    assert model["live_state_version"] == "controller-brain-live-state-v1"
    assert model["live_state_status"] == "passive-bridge-blocked"
    assert model["source_report"] == "controller-brain-live-runbook-report"
    assert model["source_runbook_version"] == "controller-brain-live-runbook-v1"
    assert model["state_row_count"] == 9
    assert model["queued_intent_count"] == 9
    assert model["audit_event_count"] == 9
    assert model["state_rows"][0]["state_key"] == "state.global-preview-depth"
    assert model["state_rows"][0]["fire_state"] == "blocked"
    assert model["queued_intents"][0]["queued_intent_key"] == "queued.global-preview-depth"
    assert model["queued_intents"][0]["preview_state"] == "preview-staged"
    assert model["audit_events"][0]["audit_event_key"] == "audit.global-preview-depth"
    assert model["audit_events"][0]["fire_state"] == "blocked"
    assert model["readiness_gates"][0]["name"] == "controller-template"
    assert first["safety"][0] == "passive/read-only"

    forbidden_keys = {"midi_cc", "cc", "channel", "port", "controller_port"}
    for collection_name in ("state_rows", "queued_intents", "audit_events"):
        assert all(forbidden_keys.isdisjoint(row) for row in model[collection_name])


def test_live_state_cli_supports_text_json_and_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_live_state import (
        CONTROLLER_BRAIN_LIVE_STATE_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_LIVE_STATE_CLI_COMMAND.args_parser([]) == {"json_output": False}
    assert CONTROLLER_BRAIN_LIVE_STATE_CLI_COMMAND.args_parser(["--json"]) == {"json_output": True}
    with pytest.raises(
        ValueError,
        match="controller-brain-live-state-report accepts only optional --json",
    ):
        CONTROLLER_BRAIN_LIVE_STATE_CLI_COMMAND.args_parser(["--arm"])

    assert main(["controller-brain-live-state-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain live state" in captured.out
    assert "queued.global-preview-depth" in captured.out
    assert "blocked until approved controller bridge" in captured.out
    assert captured.err == ""

    assert main(["controller-brain-live-state-report", "--json"]) == 0
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_live_state"]
    assert model["live_state_status"] == "passive-bridge-blocked"
    assert model["audit_events"][-1]["intent_key"] == "snapshot.panic_home"

    assert main(["controller-brain-live-state-report", "--arm"]) == 2
    captured_error = capsys.readouterr()
    assert captured_error.out == ""
    assert "accepts only optional --json" in captured_error.err


def test_live_state_cli_imports_no_real_midi_modules() -> None:
    forbidden_modules = repr(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main(["controller-brain-live-state-report", "--json"])
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


def test_live_state_help_mentions_passive_state_contract() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("controller-brain-live-state-report")

    assert help_text.startswith("RytmRandomizer passive CLI: controller-brain-live-state-report")
    assert "controller-brain live state" in help_text
    assert "queued intents" in help_text
    assert "audit events" in help_text
    assert "no MIDI controller input" in help_text
    assert "no WebSocket command dispatch" in help_text
    assert "no MIDI sending" in help_text


def test_live_state_defensive_helpers_keep_malformed_inputs_passive() -> None:
    from rytm_randomizer.reports import controller_brain_live_state as live_state

    assert live_state._live_state_unique_tuple(("a",), ("a", "b")) == ("a", "b")
    assert live_state._state_slug("macro.industrial_mode") == "macro-industrial-mode"
    assert live_state._state_row_count(("a", "b")) == 2

    row = live_state._state_row_from_runbook_step(
        live_state.ControllerBrainRunbookStep(
            step=99,
            intent_key="custom.intent",
            controller_assignment="page.encoder",
            controller_gesture="turn",
            value_delta=7,
            operator_goal="custom goal",
            stage_action="stage custom",
            inspect_action="inspect custom",
            fire_policy="blocked until approved controller bridge",
            recovery_action="recover custom",
            target_device="Analog Rytm MKII",
            target_scope="Pad 5",
            lane="src",
            safety_tier="safe",
            readiness="passive",
            blocked_action="dispatch controller gesture to active runtime",
            notes="custom notes",
        )
    )

    assert row.state_key == "state.custom-intent"
    assert row.queued_intent_key == "queued.custom-intent"
    assert row.audit_event_key == "audit.custom-intent"
    assert row.operator_goal == "custom goal"
