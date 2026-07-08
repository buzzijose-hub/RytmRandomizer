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


def test_bridge_readiness_composes_live_state_contract_packets() -> None:
    from rytm_randomizer.reports.controller_brain_live_bridge_readiness import (
        build_controller_brain_live_bridge_readiness_report,
        format_controller_brain_live_bridge_readiness_report,
    )

    report = build_controller_brain_live_bridge_readiness_report(session_label="Warehouse arc")

    assert report.bridge_readiness_version == "controller-brain-live-bridge-readiness-v1"
    assert report.bridge_readiness_status == "blocked-awaiting-controller-bridge"
    assert report.session_label == "Warehouse arc"
    assert report.source_report == "controller-brain-live-state-report"
    assert report.source_live_state_version == "controller-brain-live-state-v1"
    assert report.source_live_state_status == "passive-bridge-blocked"
    assert report.state_row_count == 9
    assert report.queued_intent_count == 9
    assert report.audit_event_count == 9
    assert report.contract_packet_count == 27
    assert report.ready_gate_count == 3
    assert report.blocked_gate_count == 7

    first_packet = report.contract_packets[0]
    assert first_packet.packet_key == "bridge.packet.state.global-preview-depth"
    assert first_packet.source_key == "state.global-preview-depth"
    assert first_packet.source_kind == "state_row"
    assert first_packet.target_bridge_role == "state-reducer"
    assert first_packet.status == "ready"
    assert first_packet.passive is True

    packet_roles = {packet.target_bridge_role for packet in report.contract_packets}
    assert packet_roles == {"state-reducer", "queue-reducer", "audit-ledger"}

    text = "\n".join(format_controller_brain_live_bridge_readiness_report(report))
    assert "RytmRandomizer passive controller brain live bridge readiness" in text
    assert "Controller brain live bridge readiness:" in text
    assert "- source state: controller-brain-live-state-report" in text
    assert "- contract packets: 27" in text
    assert "- bridge.packet.state.global-preview-depth: state-reducer / ready" in text
    assert "- state-contract: ready / ready=True" in text
    assert "- controller-input: blocked / ready=False" in text
    assert "Source: rytm_randomizer.reports.controller_brain_live_bridge_readiness" in text


def test_bridge_readiness_gates_keep_runtime_paths_blocked() -> None:
    from rytm_randomizer.reports.controller_brain_live_bridge_readiness import (
        build_controller_brain_live_bridge_readiness_report,
    )

    report = build_controller_brain_live_bridge_readiness_report()
    gates = {gate.name: gate for gate in report.bridge_readiness_gates}

    assert gates["state-contract"].status == "ready"
    assert gates["queue-contract"].status == "ready"
    assert gates["audit-contract"].status == "ready"
    assert gates["controller-input"].status == "blocked"
    assert gates["gesture-runtime"].status == "blocked"
    assert gates["websocket-dispatch"].status == "blocked"
    assert gates["midi-output"].status == "blocked"
    assert gates["hardware-send"].status == "blocked"
    assert gates["feedback-output"].status == "blocked"
    assert gates["snapshot-mutation"].status == "blocked"

    assert "open controller input adapter" in report.blocked_actions
    assert "execute live state reducer" in report.blocked_actions
    assert "dispatch controller runtime command" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "emit controller feedback" in report.blocked_actions
    assert "open MIDI output" in report.blocked_actions
    assert "send hardware MIDI" in report.blocked_actions
    assert "mutate a snapshot" in report.blocked_actions
    assert "controller-brain bridge readiness metadata only" in report.safety_lines
    assert "composes controller-brain live state only" in report.safety_lines
    assert "no MIDI controller input" in report.safety_lines
    assert "no WebSocket command dispatch" in report.safety_lines
    assert "no runtime reducer execution" in report.safety_lines
    assert "no controller feedback emission" in report.safety_lines
    assert "no MIDI sending" in report.safety_lines
    assert "no port opening" in report.safety_lines
    assert "no snapshot mutation" in report.safety_lines


def test_bridge_readiness_json_payload_is_deterministic_and_side_effect_free() -> None:
    from rytm_randomizer.reports.controller_brain_live_bridge_readiness import (
        build_controller_brain_live_bridge_readiness_payload,
    )

    first = build_controller_brain_live_bridge_readiness_payload(session_label="Warehouse arc")
    second = build_controller_brain_live_bridge_readiness_payload(session_label="Warehouse arc")

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    model = first["controller_brain_live_bridge_readiness"]
    assert model["bridge_readiness_version"] == ("controller-brain-live-bridge-readiness-v1")
    assert model["bridge_readiness_status"] == "blocked-awaiting-controller-bridge"
    assert model["source_report"] == "controller-brain-live-state-report"
    assert model["source_live_state_version"] == "controller-brain-live-state-v1"
    assert model["state_row_count"] == 9
    assert model["queued_intent_count"] == 9
    assert model["audit_event_count"] == 9
    assert model["contract_packet_count"] == 27
    assert model["ready_gate_count"] == 3
    assert model["blocked_gate_count"] == 7
    assert model["contract_packets"][0]["packet_key"] == (
        "bridge.packet.state.global-preview-depth"
    )
    assert model["contract_packets"][0]["target_bridge_role"] == "state-reducer"
    assert model["bridge_readiness_gates"][0]["name"] == "state-contract"
    assert model["bridge_readiness_gates"][0]["ready"] is True
    assert model["bridge_readiness_gates"][-1]["name"] == "snapshot-mutation"
    assert first["safety"][0] == "passive/read-only"

    forbidden_keys = {"midi_cc", "cc", "channel", "port", "controller_port"}
    for collection_name in ("contract_packets", "bridge_readiness_gates"):
        assert all(forbidden_keys.isdisjoint(row) for row in model[collection_name])


def test_bridge_readiness_cli_supports_text_json_and_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_live_bridge_readiness import (
        CONTROLLER_BRAIN_LIVE_BRIDGE_READINESS_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_LIVE_BRIDGE_READINESS_CLI_COMMAND.args_parser([]) == {
        "json_output": False
    }
    assert CONTROLLER_BRAIN_LIVE_BRIDGE_READINESS_CLI_COMMAND.args_parser(["--json"]) == {
        "json_output": True
    }
    with pytest.raises(
        ValueError,
        match="controller-brain-live-bridge-readiness-report accepts only optional --json",
    ):
        CONTROLLER_BRAIN_LIVE_BRIDGE_READINESS_CLI_COMMAND.args_parser(["--arm"])

    assert main(["controller-brain-live-bridge-readiness-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain live bridge readiness" in captured.out
    assert "bridge.packet.state.global-preview-depth" in captured.out
    assert "blocked-awaiting-controller-bridge" in captured.out
    assert captured.err == ""

    assert main(["controller-brain-live-bridge-readiness-report", "--json"]) == 0
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_live_bridge_readiness"]
    assert model["bridge_readiness_status"] == "blocked-awaiting-controller-bridge"
    assert model["contract_packets"][-1]["source_key"] == "audit.snapshot-panic-home"

    assert main(["controller-brain-live-bridge-readiness-report", "--arm"]) == 2
    captured_error = capsys.readouterr()
    assert captured_error.out == ""
    assert "accepts only optional --json" in captured_error.err


def test_bridge_readiness_cli_imports_no_real_midi_modules() -> None:
    forbidden_modules = repr(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main(["controller-brain-live-bridge-readiness-report", "--json"])
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


def test_bridge_readiness_help_mentions_passive_bridge_contract() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("controller-brain-live-bridge-readiness-report")

    assert help_text.startswith(
        "RytmRandomizer passive CLI: controller-brain-live-bridge-readiness-report"
    )
    assert "controller-brain live bridge readiness" in help_text
    assert "contract packets" in help_text
    assert "controller input adapter" in help_text
    assert "no MIDI controller input" in help_text
    assert "no WebSocket command dispatch" in help_text
    assert "no MIDI sending" in help_text


def test_bridge_readiness_defensive_helpers_keep_contract_stable() -> None:
    from rytm_randomizer.reports import controller_brain_live_bridge_readiness as bridge_readiness

    assert bridge_readiness._bridge_readiness_slug("global.preview_depth") == (
        "global-preview-depth"
    )
    assert bridge_readiness._bridge_readiness_unique_tuple(("a",), ("a", "b")) == (
        "a",
        "b",
    )
    assert bridge_readiness._bridge_readiness_count(("a", "b")) == 2

    packet = bridge_readiness.ControllerBrainBridgeContractPacket(
        packet_key="bridge.packet.custom",
        order=3,
        source_key="state.custom",
        source_kind="state_row",
        target_bridge_role="state-reducer",
        status="ready",
        passive=True,
        evidence="custom evidence",
        blocked_action="none",
    )

    assert bridge_readiness._bridge_readiness_contract_packet_to_payload(packet) == {
        "packet_key": "bridge.packet.custom",
        "order": 3,
        "source_key": "state.custom",
        "source_kind": "state_row",
        "target_bridge_role": "state-reducer",
        "status": "ready",
        "passive": True,
        "evidence": "custom evidence",
        "blocked_action": "none",
    }
