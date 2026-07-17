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


def test_dispatch_rehearsal_composes_bridge_packets_into_shadow_decisions() -> None:
    from rytm_randomizer.reports.controller_brain_live_dispatch_rehearsal import (
        build_controller_brain_live_dispatch_rehearsal_report,
        format_controller_brain_live_dispatch_rehearsal_report,
    )

    report = build_controller_brain_live_dispatch_rehearsal_report(session_label="Warehouse arc")

    assert report.dispatch_rehearsal_version == "controller-brain-live-dispatch-rehearsal-v1"
    assert report.dispatch_rehearsal_status == "shadow-dispatch-blocked"
    assert report.session_label == "Warehouse arc"
    assert report.source_report == "controller-brain-live-bridge-readiness-report"
    assert report.source_bridge_readiness_version == ("controller-brain-live-bridge-readiness-v1")
    assert report.source_bridge_readiness_status == "blocked-awaiting-controller-bridge"
    assert report.source_contract_packet_count == 27
    assert report.dispatch_decision_count == 27
    assert report.dispatch_group_count == 3
    assert report.transport_gate_count == 7
    assert report.blocked_transport_gate_count == 7

    first_decision = report.dispatch_decisions[0]
    assert first_decision.decision_key == "dispatch.decision.state.global-preview-depth"
    assert first_decision.source_packet_key == "bridge.packet.state.global-preview-depth"
    assert first_decision.dispatch_group == "state-reducer"
    assert first_decision.shadow_command == "shadow.state-reducer.global-preview-depth"
    assert first_decision.dispatch_status == "blocked-shadow-only"
    assert first_decision.passive is True

    group_names = {group.name for group in report.dispatch_groups}
    assert group_names == {"state-reducer", "queue-reducer", "audit-ledger"}

    text = "\n".join(format_controller_brain_live_dispatch_rehearsal_report(report))
    assert "RytmRandomizer passive controller brain live dispatch rehearsal" in text
    assert "Controller brain live dispatch rehearsal:" in text
    assert "- source bridge: controller-brain-live-bridge-readiness-report" in text
    assert "- dispatch decisions: 27" in text
    assert (
        "- dispatch.decision.state.global-preview-depth: state-reducer / blocked-shadow-only"
        in text
    )
    assert "- websocket-dispatch: blocked / blocked=True" in text
    assert "Source: rytm_randomizer.reports.controller_brain_live_dispatch_rehearsal" in text


def test_dispatch_rehearsal_keeps_all_active_transport_paths_blocked() -> None:
    from rytm_randomizer.reports.controller_brain_live_dispatch_rehearsal import (
        build_controller_brain_live_dispatch_rehearsal_report,
    )

    report = build_controller_brain_live_dispatch_rehearsal_report()
    gates = {gate.name: gate for gate in report.transport_gates}

    assert gates["controller-input"].status == "blocked"
    assert gates["gesture-runtime"].status == "blocked"
    assert gates["websocket-dispatch"].status == "blocked"
    assert gates["controller-feedback"].status == "blocked"
    assert gates["midi-output"].status == "blocked"
    assert gates["hardware-send"].status == "blocked"
    assert gates["snapshot-mutation"].status == "blocked"
    assert all(gate.blocked for gate in report.transport_gates)

    assert "open controller input adapter" in report.blocked_actions
    assert "execute live state reducer" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "emit controller feedback" in report.blocked_actions
    assert "open MIDI output" in report.blocked_actions
    assert "send hardware MIDI" in report.blocked_actions
    assert "mutate a snapshot" in report.blocked_actions
    assert "controller-brain dispatch rehearsal metadata only" in report.safety_lines
    assert "composes controller-brain bridge readiness only" in report.safety_lines
    assert "shadow dispatch decisions are metadata only" in report.safety_lines
    assert "no runtime reducer execution" in report.safety_lines
    assert "no WebSocket command dispatch" in report.safety_lines
    assert "no controller feedback emission" in report.safety_lines
    assert "no MIDI sending" in report.safety_lines
    assert "no port opening" in report.safety_lines
    assert "no snapshot mutation" in report.safety_lines


def test_dispatch_rehearsal_json_payload_is_deterministic_and_side_effect_free() -> None:
    from rytm_randomizer.reports.controller_brain_live_dispatch_rehearsal import (
        build_controller_brain_live_dispatch_rehearsal_payload,
    )

    first = build_controller_brain_live_dispatch_rehearsal_payload(session_label="Warehouse arc")
    second = build_controller_brain_live_dispatch_rehearsal_payload(session_label="Warehouse arc")

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    model = first["controller_brain_live_dispatch_rehearsal"]
    assert model["dispatch_rehearsal_version"] == ("controller-brain-live-dispatch-rehearsal-v1")
    assert model["dispatch_rehearsal_status"] == "shadow-dispatch-blocked"
    assert model["source_report"] == "controller-brain-live-bridge-readiness-report"
    assert model["source_bridge_readiness_version"] == ("controller-brain-live-bridge-readiness-v1")
    assert model["source_contract_packet_count"] == 27
    assert model["dispatch_decision_count"] == 27
    assert model["dispatch_group_count"] == 3
    assert model["transport_gate_count"] == 7
    assert model["blocked_transport_gate_count"] == 7
    assert model["dispatch_decisions"][0]["decision_key"] == (
        "dispatch.decision.state.global-preview-depth"
    )
    assert model["dispatch_decisions"][0]["shadow_command"] == (
        "shadow.state-reducer.global-preview-depth"
    )
    assert model["dispatch_groups"][0]["name"] == "state-reducer"
    assert model["transport_gates"][-1]["name"] == "snapshot-mutation"
    assert first["safety"][0] == "passive/read-only"

    forbidden_keys = {"midi_cc", "cc", "channel", "port", "controller_port"}
    for collection_name in ("dispatch_decisions", "dispatch_groups", "transport_gates"):
        assert all(forbidden_keys.isdisjoint(row) for row in model[collection_name])


def test_dispatch_rehearsal_cli_supports_text_json_and_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_live_dispatch_rehearsal import (
        CONTROLLER_BRAIN_LIVE_DISPATCH_REHEARSAL_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_LIVE_DISPATCH_REHEARSAL_CLI_COMMAND.args_parser([]) == {
        "json_output": False
    }
    assert CONTROLLER_BRAIN_LIVE_DISPATCH_REHEARSAL_CLI_COMMAND.args_parser(["--json"]) == {
        "json_output": True
    }
    with pytest.raises(
        ValueError,
        match="controller-brain-live-dispatch-rehearsal-report accepts only optional --json",
    ):
        CONTROLLER_BRAIN_LIVE_DISPATCH_REHEARSAL_CLI_COMMAND.args_parser(["--arm"])

    assert main(["controller-brain-live-dispatch-rehearsal-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain live dispatch rehearsal" in captured.out
    assert "dispatch.decision.state.global-preview-depth" in captured.out
    assert "shadow-dispatch-blocked" in captured.out
    assert captured.err == ""

    assert main(["controller-brain-live-dispatch-rehearsal-report", "--json"]) == 0
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_live_dispatch_rehearsal"]
    assert model["dispatch_rehearsal_status"] == "shadow-dispatch-blocked"
    assert model["dispatch_decisions"][-1]["source_packet_key"] == (
        "bridge.packet.audit.snapshot-panic-home"
    )

    assert main(["controller-brain-live-dispatch-rehearsal-report", "--arm"]) == 2
    captured_error = capsys.readouterr()
    assert captured_error.out == ""
    assert "accepts only optional --json" in captured_error.err


def test_dispatch_rehearsal_cli_imports_no_real_midi_modules() -> None:
    forbidden_modules = repr(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main(["controller-brain-live-dispatch-rehearsal-report", "--json"])
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


def test_dispatch_rehearsal_help_mentions_passive_shadow_dispatch() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("controller-brain-live-dispatch-rehearsal-report")

    assert help_text.startswith(
        "RytmRandomizer passive CLI: controller-brain-live-dispatch-rehearsal-report"
    )
    assert "controller-brain live dispatch rehearsal" in help_text
    assert "shadow dispatch decisions" in help_text
    assert "controller input adapter" in help_text
    assert "no MIDI controller input" in help_text
    assert "no WebSocket command dispatch" in help_text
    assert "no MIDI sending" in help_text


def test_dispatch_rehearsal_defensive_helpers_keep_contract_stable() -> None:
    from rytm_randomizer.reports import (
        controller_brain_live_dispatch_rehearsal as dispatch_rehearsal,
    )

    assert (
        dispatch_rehearsal._dispatch_rehearsal_slug("bridge.packet.state.global_preview_depth")
        == "bridge-packet-state-global-preview-depth"
    )
    assert dispatch_rehearsal._dispatch_rehearsal_unique_tuple(("a",), ("a", "b")) == (
        "a",
        "b",
    )
    assert dispatch_rehearsal._dispatch_rehearsal_count(("a", "b")) == 2

    decision = dispatch_rehearsal.ControllerBrainDispatchDecision(
        decision_key="dispatch.decision.custom",
        order=3,
        source_packet_key="bridge.packet.custom",
        source_kind="state_row",
        dispatch_group="state-reducer",
        shadow_command="shadow.state-reducer.custom",
        dispatch_status="blocked-shadow-only",
        passive=True,
        evidence="custom evidence",
        blocked_action="none",
    )

    assert dispatch_rehearsal._dispatch_decision_to_payload(decision) == {
        "decision_key": "dispatch.decision.custom",
        "order": 3,
        "source_packet_key": "bridge.packet.custom",
        "source_kind": "state_row",
        "dispatch_group": "state-reducer",
        "shadow_command": "shadow.state-reducer.custom",
        "dispatch_status": "blocked-shadow-only",
        "passive": True,
        "evidence": "custom evidence",
        "blocked_action": "none",
    }
