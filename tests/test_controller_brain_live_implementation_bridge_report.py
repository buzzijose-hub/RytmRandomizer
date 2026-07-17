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


def test_implementation_bridge_composes_cockpit_cards_into_bindings() -> None:
    from rytm_randomizer.reports.controller_brain_live_implementation_bridge import (
        build_controller_brain_live_implementation_bridge_report,
        format_controller_brain_live_implementation_bridge_report,
    )

    report = build_controller_brain_live_implementation_bridge_report(session_label="Warehouse arc")

    assert report.implementation_bridge_version == (
        "controller-brain-live-implementation-bridge-v1"
    )
    assert report.implementation_bridge_status == "implementation-bridge-passive"
    assert report.session_label == "Warehouse arc"
    assert report.source_report == "controller-brain-live-cockpit-handoff-report"
    assert report.source_cockpit_handoff_version == "controller-brain-live-cockpit-handoff-v1"
    assert report.source_cockpit_handoff_status == "cockpit-handoff-passive"
    assert report.source_handoff_card_count == 27
    assert report.binding_count == 27
    assert report.fixture_bundle_count == 5
    assert report.implementation_gate_count == 6

    first_binding = report.implementation_bindings[0]
    assert first_binding.binding_key == "implementation.binding.state.global-preview-depth"
    assert first_binding.source_card_key == "cockpit.card.state.global-preview-depth"
    assert first_binding.component_key == "controller-feedback-preview-card"
    assert first_binding.selector == "controller-feedback-preview-card--global-preview-depth"
    assert first_binding.view_model_path == (
        "$.controller_brain_live_implementation_bridge.implementation_bindings[0]"
    )
    assert first_binding.disabled is True
    assert first_binding.status == "disabled-binding-ready"
    assert first_binding.blocked_action == "emit controller feedback"

    assert {bundle.bundle_key for bundle in report.fixture_bundles} == {
        "fixture-cockpit-handoff-json",
        "fixture-implementation-bindings-json",
        "fixture-disabled-controls-json",
        "fixture-implementation-gates-json",
        "fixture-replay-commands-json",
    }
    assert {gate.gate_key for gate in report.implementation_gates} == {
        "source-handoff-ready",
        "binding-coverage",
        "fixture-coverage",
        "disabled-control-coverage",
        "replay-command",
        "passive-boundary",
    }

    text = "\n".join(format_controller_brain_live_implementation_bridge_report(report))
    assert "RytmRandomizer passive controller brain live implementation bridge" in text
    assert "Controller brain live implementation bridge:" in text
    assert "- source handoff: controller-brain-live-cockpit-handoff-report" in text
    assert "- implementation bindings: 27" in text
    assert "- fixture bundles: 5" in text
    assert "- implementation gates: 6" in text
    assert "implementation.binding.state.global-preview-depth" in text
    assert "Source: rytm_randomizer.reports.controller_brain_live_implementation_bridge" in text


def test_implementation_bridge_stays_passive_and_blocks_runtime_paths() -> None:
    from rytm_randomizer.reports.controller_brain_live_implementation_bridge import (
        build_controller_brain_live_implementation_bridge_report,
    )

    report = build_controller_brain_live_implementation_bridge_report()

    assert "controller-brain implementation bridge metadata only" in report.safety_lines
    assert "implementation bindings are declarative metadata only" in report.safety_lines
    assert "fixture bundles are metadata only" in report.safety_lines
    assert "no GUI launch" in report.safety_lines
    assert "no GUI renderer start" in report.safety_lines
    assert "no runtime reducer execution" in report.safety_lines
    assert "no WebSocket dispatch" in report.safety_lines
    assert "no controller feedback emission" in report.safety_lines
    assert "no MIDI controller output" in report.safety_lines
    assert "no MIDI sending" in report.safety_lines
    assert "no port opening" in report.safety_lines
    assert "no snapshot mutation" in report.safety_lines

    assert "launch Cockpit GUI runtime" in report.blocked_actions
    assert "mount implementation bindings" in report.blocked_actions
    assert "execute live state reducer" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "emit controller feedback" in report.blocked_actions
    assert "open MIDI output" in report.blocked_actions
    assert "mutate a snapshot" in report.blocked_actions
    assert all(binding.disabled for binding in report.implementation_bindings)
    assert all(bundle.passive for bundle in report.fixture_bundles)
    assert all(gate.passive for gate in report.implementation_gates)


def test_implementation_bridge_json_payload_is_deterministic_and_runtime_safe() -> None:
    from rytm_randomizer.reports.controller_brain_live_implementation_bridge import (
        build_controller_brain_live_implementation_bridge_payload,
    )

    first = build_controller_brain_live_implementation_bridge_payload(session_label="Warehouse arc")
    second = build_controller_brain_live_implementation_bridge_payload(
        session_label="Warehouse arc"
    )

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    model = first["controller_brain_live_implementation_bridge"]
    assert model["implementation_bridge_version"] == (
        "controller-brain-live-implementation-bridge-v1"
    )
    assert model["implementation_bridge_status"] == "implementation-bridge-passive"
    assert model["source_report"] == "controller-brain-live-cockpit-handoff-report"
    assert model["source_handoff_card_count"] == 27
    assert model["binding_count"] == 27
    assert model["fixture_bundle_count"] == 5
    assert model["implementation_gate_count"] == 6
    assert model["implementation_bindings"][0]["binding_key"] == (
        "implementation.binding.state.global-preview-depth"
    )
    assert model["implementation_bindings"][0]["source_card_key"] == (
        "cockpit.card.state.global-preview-depth"
    )
    assert model["fixture_bundles"][0]["bundle_key"] == "fixture-cockpit-handoff-json"
    assert model["implementation_gates"][-1]["gate_key"] == "passive-boundary"
    assert first["safety"][0] == "passive/read-only"

    forbidden_keys = {"midi_cc", "cc", "channel", "port", "controller_port"}
    for collection_name in (
        "implementation_bindings",
        "fixture_bundles",
        "implementation_gates",
    ):
        assert all(forbidden_keys.isdisjoint(row) for row in model[collection_name])


def test_implementation_bridge_cli_supports_text_json_and_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_live_implementation_bridge import (
        CONTROLLER_BRAIN_LIVE_IMPLEMENTATION_BRIDGE_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_LIVE_IMPLEMENTATION_BRIDGE_CLI_COMMAND.args_parser([]) == {
        "json_output": False
    }
    assert CONTROLLER_BRAIN_LIVE_IMPLEMENTATION_BRIDGE_CLI_COMMAND.args_parser(["--json"]) == {
        "json_output": True
    }
    with pytest.raises(
        ValueError,
        match="controller-brain-live-implementation-bridge-report accepts only optional --json",
    ):
        CONTROLLER_BRAIN_LIVE_IMPLEMENTATION_BRIDGE_CLI_COMMAND.args_parser(["--arm"])

    assert main(["controller-brain-live-implementation-bridge-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain live implementation bridge" in (captured.out)
    assert "implementation.binding.state.global-preview-depth" in captured.out
    assert "implementation-bridge-passive" in captured.out
    assert captured.err == ""

    assert main(["controller-brain-live-implementation-bridge-report", "--json"]) == 0
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_live_implementation_bridge"]
    assert model["implementation_bridge_status"] == "implementation-bridge-passive"
    assert model["implementation_bindings"][-1]["source_card_key"] == (
        "cockpit.card.audit.snapshot-panic-home"
    )

    assert main(["controller-brain-live-implementation-bridge-report", "--arm"]) == 2
    captured_error = capsys.readouterr()
    assert captured_error.out == ""
    assert "accepts only optional --json" in captured_error.err


def test_implementation_bridge_cli_imports_no_real_midi_modules() -> None:
    forbidden_modules = repr(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main(["controller-brain-live-implementation-bridge-report", "--json"])
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


def test_implementation_bridge_help_mentions_disabled_runtime_bridge() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("controller-brain-live-implementation-bridge-report")

    assert help_text.startswith(
        "RytmRandomizer passive CLI: controller-brain-live-implementation-bridge-report"
    )
    assert "controller-brain live implementation bridge" in help_text
    assert "implementation bindings" in help_text
    assert "fixture bundles" in help_text
    assert "implementation gates" in help_text
    assert "no GUI launch" in help_text
    assert "no runtime reducer execution" in help_text
    assert "no WebSocket dispatch" in help_text
    assert "no controller feedback emission" in help_text
    assert "no MIDI controller output" in help_text
    assert "no MIDI sending" in help_text


def test_implementation_bridge_defensive_helpers_keep_contract_stable() -> None:
    from rytm_randomizer.reports import controller_brain_live_implementation_bridge as bridge

    assert bridge._implementation_slug("cockpit.card.state.global_preview_depth") == (
        "cockpit-card-state-global-preview-depth"
    )
    assert bridge._implementation_unique_tuple(("a",), ("a", "b")) == ("a", "b")
    assert bridge._implementation_count(("a", "b")) == 2
    assert bridge._selector_from_key("implementation.binding.state.global-preview-depth") == (
        "controller-feedback-preview-card--global-preview-depth"
    )

    binding = bridge.ControllerBrainImplementationBinding(
        binding_key="implementation.binding.custom",
        order=3,
        source_card_key="cockpit.card.custom",
        component_key="controller-feedback-preview-card",
        selector="controller-feedback-preview-card--custom",
        view_model_path="$.custom",
        status="disabled-binding-ready",
        disabled=True,
        evidence="custom evidence",
        blocked_action="none",
    )

    assert bridge._binding_to_payload(binding) == {
        "binding_key": "implementation.binding.custom",
        "order": 3,
        "source_card_key": "cockpit.card.custom",
        "component_key": "controller-feedback-preview-card",
        "selector": "controller-feedback-preview-card--custom",
        "view_model_path": "$.custom",
        "status": "disabled-binding-ready",
        "disabled": True,
        "evidence": "custom evidence",
        "blocked_action": "none",
    }
