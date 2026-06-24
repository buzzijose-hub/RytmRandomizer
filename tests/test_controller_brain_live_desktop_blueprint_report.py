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


def test_desktop_blueprint_composes_implementation_bridge_into_regions() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_blueprint import (
        build_controller_brain_live_desktop_blueprint_report,
        format_controller_brain_live_desktop_blueprint_report,
    )

    report = build_controller_brain_live_desktop_blueprint_report(session_label="Warehouse arc")

    assert report.desktop_blueprint_version == "controller-brain-live-desktop-blueprint-v1"
    assert report.desktop_blueprint_status == "desktop-blueprint-passive"
    assert report.session_label == "Warehouse arc"
    assert report.source_report == "controller-brain-live-implementation-bridge-report"
    assert report.source_implementation_bridge_version == (
        "controller-brain-live-implementation-bridge-v1"
    )
    assert report.source_implementation_bridge_status == "implementation-bridge-passive"
    assert report.source_binding_count == 27
    assert report.region_count == 6
    assert report.component_contract_count == 27
    assert report.view_model_binding_count == 27
    assert report.fixture_hint_count == 5
    assert report.acceptance_check_count == 7

    first_region = report.desktop_regions[0]
    assert first_region.region_key == "desktop.region.controller-feedback-preview"
    assert first_region.label == "Controller Feedback Preview"
    assert first_region.layout_area == "feedback-preview"
    assert first_region.enabled is False
    assert first_region.passive is True

    first_component = report.component_contracts[0]
    assert first_component.component_key == "desktop.component.state.global-preview-depth"
    assert first_component.source_binding_key == (
        "implementation.binding.state.global-preview-depth"
    )
    assert first_component.region_key == "desktop.region.controller-feedback-preview"
    assert first_component.selector == "controller-feedback-preview-card--global-preview-depth"
    assert first_component.status == "disabled-component-ready"
    assert first_component.enabled is False
    assert first_component.passive is True
    assert first_component.blocked_action == "mount component contracts"
    assert first_component.source_blocked_action == "emit controller feedback"

    text = "\n".join(format_controller_brain_live_desktop_blueprint_report(report))
    assert "RytmRandomizer passive controller brain live desktop blueprint" in text
    assert "Controller brain live desktop blueprint:" in text
    assert (
        "- source implementation bridge: controller-brain-live-implementation-bridge-report" in text
    )
    assert "- desktop regions: 6" in text
    assert "- component contracts: 27" in text
    assert "- view-model bindings: 27" in text
    assert "desktop.component.state.global-preview-depth" in text
    assert "Source: rytm_randomizer.reports.controller_brain_live_desktop_blueprint" in text


def test_desktop_blueprint_stays_passive_and_blocks_runtime_paths() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_blueprint import (
        build_controller_brain_live_desktop_blueprint_report,
    )

    report = build_controller_brain_live_desktop_blueprint_report()

    assert "passive/read-only" in report.safety_lines
    assert "controller-brain desktop blueprint metadata only" in report.safety_lines
    assert "desktop regions are declarative metadata only" in report.safety_lines
    assert "component contracts are declarative metadata only" in report.safety_lines
    assert "view-model bindings are declarative metadata only" in report.safety_lines
    assert "fixture hints are metadata only" in report.safety_lines
    assert "acceptance checks are metadata only" in report.safety_lines
    assert "no GUI launch" in report.safety_lines
    assert "no GUI renderer start" in report.safety_lines
    assert "no runtime reducer execution" in report.safety_lines
    assert "no WebSocket dispatch" in report.safety_lines
    assert "no controller feedback emission" in report.safety_lines
    assert "no MIDI controller output" in report.safety_lines
    assert "no MIDI sending" in report.safety_lines
    assert "no port opening" in report.safety_lines
    assert "no snapshot mutation" in report.safety_lines
    assert "no file writing" in report.safety_lines

    assert "launch Cockpit GUI runtime" in report.blocked_actions
    assert "start GUI renderer" in report.blocked_actions
    assert "mount desktop regions" in report.blocked_actions
    assert "mount component contracts" in report.blocked_actions
    assert "execute live state reducer" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "emit controller feedback" in report.blocked_actions
    assert "open MIDI output" in report.blocked_actions
    assert "mutate a snapshot" in report.blocked_actions
    assert "write fixture files" in report.blocked_actions
    assert all(region.enabled is False for region in report.desktop_regions)
    assert all(region.passive for region in report.desktop_regions)
    assert all(component.enabled is False for component in report.component_contracts)
    assert all(component.passive for component in report.component_contracts)
    assert all(binding.enabled is False for binding in report.view_model_bindings)
    assert all(binding.passive for binding in report.view_model_bindings)
    assert all(hint.passive for hint in report.fixture_hints)
    assert all(check.passive for check in report.acceptance_checks)


def test_desktop_blueprint_json_payload_is_deterministic_and_runtime_safe() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_blueprint import (
        build_controller_brain_live_desktop_blueprint_payload,
    )

    first = build_controller_brain_live_desktop_blueprint_payload(session_label="Warehouse arc")
    second = build_controller_brain_live_desktop_blueprint_payload(session_label="Warehouse arc")

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    model = first["controller_brain_live_desktop_blueprint"]
    assert model["desktop_blueprint_version"] == "controller-brain-live-desktop-blueprint-v1"
    assert model["desktop_blueprint_status"] == "desktop-blueprint-passive"
    assert model["source_report"] == "controller-brain-live-implementation-bridge-report"
    assert model["source_binding_count"] == 27
    assert model["region_count"] == 6
    assert model["component_contract_count"] == 27
    assert model["view_model_binding_count"] == 27
    assert model["fixture_hint_count"] == 5
    assert model["acceptance_check_count"] == 7
    assert model["component_contracts"][0]["source_binding_key"] == (
        "implementation.binding.state.global-preview-depth"
    )
    assert model["fixture_hints"][0]["fixture_key"] == "desktop.fixture.cockpit-handoff-json"
    assert model["acceptance_checks"][-1]["check_key"] == "passive-boundary"
    assert first["safety"][0] == "passive/read-only"

    forbidden_keys = {
        "midi_cc",
        "cc",
        "channel",
        "port",
        "controller_port",
        "websocket_url",
        "socket",
        "file_path",
    }
    for collection_name in (
        "desktop_regions",
        "component_contracts",
        "view_model_bindings",
        "fixture_hints",
        "acceptance_checks",
    ):
        assert all(forbidden_keys.isdisjoint(row) for row in model[collection_name])


def test_desktop_blueprint_cli_supports_text_json_and_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_live_desktop_blueprint import (
        CONTROLLER_BRAIN_LIVE_DESKTOP_BLUEPRINT_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_LIVE_DESKTOP_BLUEPRINT_CLI_COMMAND.args_parser([]) == {
        "json_output": False
    }
    assert CONTROLLER_BRAIN_LIVE_DESKTOP_BLUEPRINT_CLI_COMMAND.args_parser(["--json"]) == {
        "json_output": True
    }
    with pytest.raises(
        ValueError,
        match="controller-brain-live-desktop-blueprint-report accepts only optional --json",
    ):
        CONTROLLER_BRAIN_LIVE_DESKTOP_BLUEPRINT_CLI_COMMAND.args_parser(["--arm"])

    assert main(["controller-brain-live-desktop-blueprint-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain live desktop blueprint" in (captured.out)
    assert "desktop.component.state.global-preview-depth" in captured.out
    assert "desktop-blueprint-passive" in captured.out
    assert captured.err == ""

    assert main(["controller-brain-live-desktop-blueprint-report", "--json"]) == 0
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_live_desktop_blueprint"]
    assert model["desktop_blueprint_status"] == "desktop-blueprint-passive"
    assert model["component_contracts"][-1]["source_binding_key"] == (
        "implementation.binding.audit.snapshot-panic-home"
    )

    assert main(["controller-brain-live-desktop-blueprint-report", "--arm"]) == 2
    captured_error = capsys.readouterr()
    assert captured_error.out == ""
    assert "accepts only optional --json" in captured_error.err


def test_desktop_blueprint_cli_imports_no_real_midi_modules() -> None:
    forbidden_modules = repr(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main(["controller-brain-live-desktop-blueprint-report", "--json"])
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


def test_desktop_blueprint_help_mentions_disabled_desktop_blueprint() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("controller-brain-live-desktop-blueprint-report")

    assert help_text.startswith(
        "RytmRandomizer passive CLI: controller-brain-live-desktop-blueprint-report"
    )
    assert "controller-brain live desktop blueprint" in help_text
    assert "desktop regions" in help_text
    assert "component contracts" in help_text
    assert "view-model bindings" in help_text
    assert "fixture hints" in help_text
    assert "acceptance checks" in help_text
    assert "no GUI launch" in help_text
    assert "no runtime reducer execution" in help_text
    assert "no WebSocket dispatch" in help_text
    assert "no controller feedback emission" in help_text
    assert "no MIDI controller output" in help_text
    assert "no MIDI sending" in help_text
    assert "no file writing" in help_text


def test_desktop_blueprint_defensive_helpers_keep_contract_stable() -> None:
    from rytm_randomizer.reports import controller_brain_live_desktop_blueprint as blueprint

    assert (
        blueprint._desktop_blueprint_slug("implementation.binding.state.global_preview_depth")
        == "implementation-binding-state-global-preview-depth"
    )
    assert blueprint._desktop_blueprint_unique_tuple(("a",), ("a", "b")) == (
        "a",
        "b",
    )
    assert blueprint._desktop_blueprint_count(("a", "b")) == 2
    assert (
        blueprint._component_key_from_binding_key(
            "implementation.binding.state.global-preview-depth"
        )
        == "desktop.component.state.global-preview-depth"
    )
    assert (
        blueprint._region_key_from_component_key("controller-feedback-preview-card")
        == "desktop.region.controller-feedback-preview"
    )

    component = blueprint.ControllerBrainDesktopComponentContract(
        component_key="desktop.component.custom",
        order=3,
        source_binding_key="implementation.binding.custom",
        region_key="desktop.region.custom",
        selector="custom--selector",
        view_model_path="$.custom",
        status="disabled-component-ready",
        enabled=False,
        passive=True,
        evidence="custom evidence",
        blocked_action="none",
        source_blocked_action="source block",
    )

    assert blueprint._component_contract_to_payload(component) == {
        "component_key": "desktop.component.custom",
        "order": 3,
        "source_binding_key": "implementation.binding.custom",
        "region_key": "desktop.region.custom",
        "selector": "custom--selector",
        "view_model_path": "$.custom",
        "status": "disabled-component-ready",
        "enabled": False,
        "passive": True,
        "evidence": "custom evidence",
        "blocked_action": "none",
        "source_blocked_action": "source block",
    }
