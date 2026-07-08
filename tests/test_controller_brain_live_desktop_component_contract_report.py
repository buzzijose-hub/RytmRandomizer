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


def test_desktop_component_contract_composes_app_plan_into_disabled_contracts() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_component_contract import (
        build_controller_brain_live_desktop_component_contract_report,
        format_controller_brain_live_desktop_component_contract_report,
    )

    report = build_controller_brain_live_desktop_component_contract_report(
        session_label="Warehouse arc",
        component_contract_label="Warehouse component contracts",
        selector_prefix="rr-controller",
    )

    assert report.desktop_component_contract_version == (
        "controller-brain-live-desktop-component-contract-v1"
    )
    assert report.desktop_component_contract_status == "desktop-component-contract-passive"
    assert report.session_label == "Warehouse arc"
    assert report.component_contract_label == "Warehouse component contracts"
    assert report.selector_prefix == "rr-controller"
    assert report.source_report == "controller-brain-live-desktop-app-plan-report"
    assert report.source_desktop_app_plan_version == "controller-brain-live-desktop-app-plan-v1"
    assert report.source_desktop_app_plan_status == "desktop-app-plan-passive"
    assert report.source_route_count == 6
    assert report.source_component_file_hint_count == 27
    assert report.source_state_slice_count == 27
    assert report.component_contract_count == 27
    assert report.prop_contract_count == 27
    assert report.event_contract_count == 27
    assert report.test_hook_count == 27
    assert report.fixture_contract_count == 27
    assert report.acceptance_check_count == 7

    first_contract = report.component_contracts[0]
    assert first_contract.component_contract_key == (
        "desktop.contract.component.state.global-preview-depth"
    )
    assert first_contract.source_component_file_key == (
        "desktop.file.component.state.global-preview-depth"
    )
    assert first_contract.source_component_key == ("desktop.component.state.global-preview-depth")
    assert first_contract.route_key == "desktop.route.controller-feedback-preview"
    assert first_contract.selector == "rr-controller-state-global-preview-depth"
    assert first_contract.suggested_module == (
        "future_controller_brain/components/state_global_preview_depth.py"
    )
    assert first_contract.enabled is False
    assert first_contract.passive is True

    first_prop = report.prop_contracts[0]
    assert first_prop.prop_contract_key == "desktop.prop.state.global-preview-depth"
    assert first_prop.component_contract_key == first_contract.component_contract_key
    assert first_prop.prop_name == "viewModel"
    assert first_prop.source_state_slice_key == "desktop.state.state.global-preview-depth"
    assert first_prop.initial_state == "disabled"
    assert first_prop.passive is True

    first_event = report.event_contracts[0]
    assert first_event.event_contract_key == "desktop.event.state.global-preview-depth"
    assert first_event.component_contract_key == first_contract.component_contract_key
    assert first_event.event_name == "onIntentPreview"
    assert first_event.enabled is False
    assert first_event.blocked_action == "dispatch Cockpit WebSocket commands"

    first_hook = report.test_hooks[0]
    assert first_hook.test_hook_key == "desktop.test.state.global-preview-depth"
    assert first_hook.component_contract_key == first_contract.component_contract_key
    assert first_hook.test_id == "rr-controller-state-global-preview-depth"
    assert first_hook.passive is True

    first_fixture = report.fixture_contracts[0]
    assert first_fixture.fixture_contract_key == "desktop.fixture.state.global-preview-depth"
    assert first_fixture.component_contract_key == first_contract.component_contract_key
    assert first_fixture.fixture_key == "fixture.state.global-preview-depth"
    assert first_fixture.write_file is False

    text = "\n".join(format_controller_brain_live_desktop_component_contract_report(report))
    assert "RytmRandomizer passive controller brain live desktop component contract" in text
    assert "Controller brain live desktop component contract:" in text
    assert "- source desktop app plan: controller-brain-live-desktop-app-plan-report" in text
    assert "- component contracts: 27" in text
    assert "- prop contracts: 27" in text
    assert "- event contracts: 27" in text
    assert "rr-controller-state-global-preview-depth" in text
    assert (
        "Source: rytm_randomizer.reports.controller_brain_live_desktop_component_contract" in text
    )


def test_desktop_component_contract_stays_passive_and_blocks_runtime_paths() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_component_contract import (
        build_controller_brain_live_desktop_component_contract_report,
    )

    report = build_controller_brain_live_desktop_component_contract_report()

    assert "passive/read-only" in report.safety_lines
    assert "controller-brain desktop component contract metadata only" in report.safety_lines
    assert "component contracts are declarative metadata only" in report.safety_lines
    assert "prop contracts are declarative metadata only" in report.safety_lines
    assert "event contracts are disabled metadata only" in report.safety_lines
    assert "test hooks are declarative metadata only" in report.safety_lines
    assert "fixture contracts are advisory metadata only" in report.safety_lines
    assert "no GUI launch" in report.safety_lines
    assert "no app launch" in report.safety_lines
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
    assert "launch desktop app shell" in report.blocked_actions
    assert "start GUI renderer" in report.blocked_actions
    assert "mount component contracts" in report.blocked_actions
    assert "write component files" in report.blocked_actions
    assert "execute live state reducer" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "emit controller feedback" in report.blocked_actions
    assert "open MIDI output" in report.blocked_actions
    assert "mutate a snapshot" in report.blocked_actions
    assert all(contract.enabled is False for contract in report.component_contracts)
    assert all(contract.passive for contract in report.component_contracts)
    assert all(prop.passive for prop in report.prop_contracts)
    assert all(event.enabled is False for event in report.event_contracts)
    assert all(event.passive for event in report.event_contracts)
    assert all(hook.passive for hook in report.test_hooks)
    assert all(fixture.write_file is False for fixture in report.fixture_contracts)
    assert all(fixture.passive for fixture in report.fixture_contracts)
    assert all(check.passive for check in report.acceptance_checks)


def test_desktop_component_contract_json_payload_is_deterministic_and_runtime_safe() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_component_contract import (
        build_controller_brain_live_desktop_component_contract_payload,
    )

    first = build_controller_brain_live_desktop_component_contract_payload(
        session_label="Warehouse arc",
        component_contract_label="Warehouse component contracts",
        selector_prefix="warehouse-controller",
    )
    second = build_controller_brain_live_desktop_component_contract_payload(
        session_label="Warehouse arc",
        component_contract_label="Warehouse component contracts",
        selector_prefix="warehouse-controller",
    )

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    model = first["controller_brain_live_desktop_component_contract"]
    assert model["desktop_component_contract_version"] == (
        "controller-brain-live-desktop-component-contract-v1"
    )
    assert model["desktop_component_contract_status"] == "desktop-component-contract-passive"
    assert model["component_contract_label"] == "Warehouse component contracts"
    assert model["selector_prefix"] == "warehouse-controller"
    assert model["source_report"] == "controller-brain-live-desktop-app-plan-report"
    assert model["component_contract_count"] == 27
    assert model["prop_contract_count"] == 27
    assert model["event_contract_count"] == 27
    assert model["test_hook_count"] == 27
    assert model["fixture_contract_count"] == 27
    assert model["acceptance_check_count"] == 7
    assert model["component_contracts"][0]["selector"] == (
        "warehouse-controller-state-global-preview-depth"
    )
    assert model["prop_contracts"][0]["prop_name"] == "viewModel"
    assert model["event_contracts"][0]["event_name"] == "onIntentPreview"
    assert model["test_hooks"][0]["test_id"] == "warehouse-controller-state-global-preview-depth"
    assert model["fixture_contracts"][0]["write_file"] is False
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
        "component_contracts",
        "prop_contracts",
        "event_contracts",
        "test_hooks",
        "fixture_contracts",
        "acceptance_checks",
    ):
        assert all(forbidden_keys.isdisjoint(row) for row in model[collection_name])


def test_desktop_component_contract_cli_supports_text_json_and_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_live_desktop_component_contract import (
        CONTROLLER_BRAIN_LIVE_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_LIVE_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND.args_parser([]) == {
        "component_contract_label": "Controller brain desktop component contract",
        "selector_prefix": "rr-controller",
        "json_output": False,
    }
    assert CONTROLLER_BRAIN_LIVE_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND.args_parser(
        [
            "--component-contract-label",
            "Warehouse component contracts",
            "--selector-prefix",
            "warehouse-controller",
            "--json",
        ]
    ) == {
        "component_contract_label": "Warehouse component contracts",
        "selector_prefix": "warehouse-controller",
        "json_output": True,
    }
    with pytest.raises(
        ValueError,
        match=(
            "controller-brain-live-desktop-component-contract-report accepts --json, "
            "--component-contract-label, and --selector-prefix only"
        ),
    ):
        CONTROLLER_BRAIN_LIVE_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND.args_parser(["--arm"])
    with pytest.raises(ValueError, match="component_contract_label must not be blank"):
        CONTROLLER_BRAIN_LIVE_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND.args_parser(
            ["--component-contract-label", " "]
        )
    with pytest.raises(ValueError, match="selector_prefix must not be blank"):
        CONTROLLER_BRAIN_LIVE_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND.args_parser(
            ["--selector-prefix", " "]
        )
    with pytest.raises(ValueError, match="selector_prefix must use letters"):
        CONTROLLER_BRAIN_LIVE_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND.args_parser(
            ["--selector-prefix", "bad prefix"]
        )
    with pytest.raises(
        ValueError,
        match="controller-brain-live-desktop-component-contract-report accepts --json",
    ):
        CONTROLLER_BRAIN_LIVE_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND.args_parser(
            ["--component-contract-label"]
        )
    assert (
        CONTROLLER_BRAIN_LIVE_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND.error_formatter(
            ValueError("bad input")
        )
        == "Error: bad input"
    )

    assert main(["controller-brain-live-desktop-component-contract-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain live desktop component contract" in (
        captured.out
    )
    assert "rr-controller-state-global-preview-depth" in captured.out
    assert "desktop-component-contract-passive" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "controller-brain-live-desktop-component-contract-report",
                "--component-contract-label",
                "Warehouse component contracts",
                "--selector-prefix",
                "warehouse-controller",
                "--json",
            ]
        )
        == 0
    )
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_live_desktop_component_contract"]
    assert model["desktop_component_contract_status"] == "desktop-component-contract-passive"
    assert model["selector_prefix"] == "warehouse-controller"


def test_desktop_component_contract_cli_imports_no_real_midi_modules() -> None:
    code = (
        "import sys\n"
        "from rytm_randomizer.cli import main\n"
        "raise SystemExit(main(['controller-brain-live-desktop-component-contract-report']))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "RytmRandomizer passive controller brain live desktop component contract" in (
        completed.stdout
    )

    probe = (
        "import sys\n"
        "from rytm_randomizer.cli import main\n"
        "main(['controller-brain-live-desktop-component-contract-report'])\n"
        f"for name in {FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES!r}:\n"
        "    if name in sys.modules:\n"
        "        raise SystemExit(f'forbidden import: {name}')\n"
    )
    probe_completed = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe_completed.returncode == 0, probe_completed.stderr


def test_desktop_component_contract_help_text_documents_passive_contracts() -> None:
    from rytm_randomizer.help_text import HELP_TEXT

    help_text = HELP_TEXT["controller-brain-live-desktop-component-contract-report"]()

    assert "disabled future component API contracts" in help_text
    assert "--component-contract-label" in help_text
    assert "--selector-prefix" in help_text
    assert "component selectors" in help_text
    assert "prop contracts" in help_text
    assert "event contracts" in help_text
    assert "test hooks" in help_text
    assert "no GUI launch" in help_text
    assert "no WebSocket dispatch" in help_text
    assert "no MIDI sending" in help_text
    assert "no file writing" in help_text


def test_desktop_component_contract_helper_edges_are_deterministic() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_component_contract import (
        ControllerBrainDesktopComponentContractBinding,
        _component_contract_key_from_component_file_key,
        _desktop_component_contract_count,
        _desktop_component_contract_slug,
        _desktop_component_contract_unique_tuple,
        _normalize_component_contract_label,
        _normalize_selector_prefix,
        _prop_contract_key_from_state_slice_key,
    )

    assert _desktop_component_contract_slug("desktop.component.state.global_preview_depth") == (
        "desktop-component-state-global-preview-depth"
    )
    assert _desktop_component_contract_unique_tuple(("a",), ("a", "b")) == ("a", "b")
    assert _desktop_component_contract_count(("a", "b")) == 2
    assert (
        _component_contract_key_from_component_file_key(
            "desktop.file.component.state.global-preview-depth"
        )
        == "desktop.contract.component.state.global-preview-depth"
    )
    assert (
        _prop_contract_key_from_state_slice_key("desktop.state.state.global-preview-depth")
        == "desktop.prop.state.global-preview-depth"
    )
    assert _normalize_component_contract_label("  Warehouse  ") == "Warehouse"
    assert _normalize_selector_prefix(" rr-controller ") == "rr-controller"

    binding = ControllerBrainDesktopComponentContractBinding(
        component_contract_key="desktop.contract.component.state.global-preview-depth",
        order=1,
        source_component_file_key="desktop.file.component.state.global-preview-depth",
        source_component_key="desktop.component.state.global-preview-depth",
        route_key="desktop.route.controller-feedback-preview",
        suggested_module="future_controller_brain/components/state_global_preview_depth.py",
        selector="rr-controller-state-global-preview-depth",
        component_type="controller-brain-card",
        status="component-contract-disabled",
        enabled=False,
        passive=True,
        evidence="future component contract only",
        blocked_action="mount component contracts",
    )
    assert binding.component_contract_key == "desktop.contract.component.state.global-preview-depth"
