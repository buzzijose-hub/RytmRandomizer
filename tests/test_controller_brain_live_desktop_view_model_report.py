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


def test_desktop_view_model_composes_component_contract_into_disabled_state() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_view_model import (
        build_controller_brain_live_desktop_view_model_report,
        format_controller_brain_live_desktop_view_model_report,
    )

    report = build_controller_brain_live_desktop_view_model_report(
        session_label="Warehouse arc",
        view_model_label="Warehouse view model",
        state_prefix="warehouse-state",
    )

    assert report.desktop_view_model_version == "controller-brain-live-desktop-view-model-v1"
    assert report.desktop_view_model_status == "desktop-view-model-passive"
    assert report.session_label == "Warehouse arc"
    assert report.view_model_label == "Warehouse view model"
    assert report.state_prefix == "warehouse-state"
    assert report.source_report == "controller-brain-live-desktop-component-contract-report"
    assert report.source_desktop_component_contract_version == (
        "controller-brain-live-desktop-component-contract-v1"
    )
    assert report.source_desktop_component_contract_status == ("desktop-component-contract-passive")
    assert report.source_component_contract_count == 27
    assert report.source_prop_contract_count == 27
    assert report.source_event_contract_count == 27
    assert report.component_view_model_count == 27
    assert report.state_binding_count == 27
    assert report.disabled_action_model_count == 27
    assert report.render_assertion_count == 27
    assert report.acceptance_check_count == 7

    first_view_model = report.component_view_models[0]
    assert first_view_model.view_model_key == "desktop.viewmodel.state.global-preview-depth"
    assert first_view_model.component_contract_key == (
        "desktop.contract.component.state.global-preview-depth"
    )
    assert first_view_model.selector == "rr-controller-state-global-preview-depth"
    assert first_view_model.state_key == "warehouse-state.state.global-preview-depth"
    assert first_view_model.enabled is False
    assert first_view_model.passive is True

    first_binding = report.state_bindings[0]
    assert first_binding.state_binding_key == "desktop.binding.state.global-preview-depth"
    assert first_binding.view_model_key == first_view_model.view_model_key
    assert first_binding.prop_name == "viewModel"
    assert first_binding.source_prop_contract_key == "desktop.prop.state.global-preview-depth"
    assert first_binding.fallback_state == "disabled"

    first_action = report.disabled_action_models[0]
    assert first_action.action_model_key == "desktop.action.state.global-preview-depth"
    assert first_action.view_model_key == first_view_model.view_model_key
    assert first_action.event_name == "onIntentPreview"
    assert first_action.control_state == "disabled"
    assert first_action.enabled is False
    assert first_action.blocked_action == "dispatch Cockpit WebSocket commands"

    first_assertion = report.render_assertions[0]
    assert first_assertion.render_assertion_key == "desktop.assert.state.global-preview-depth"
    assert first_assertion.test_id == "rr-controller-state-global-preview-depth"
    assert first_assertion.required_state == "disabled"
    assert first_assertion.passive is True

    text = "\n".join(format_controller_brain_live_desktop_view_model_report(report))
    assert "RytmRandomizer passive controller brain live desktop view model" in text
    assert "Controller brain live desktop view model:" in text
    assert "- source desktop component contract:" in text
    assert "- component view models: 27" in text
    assert "- state bindings: 27" in text
    assert "- disabled action models: 27" in text
    assert "warehouse-state.state.global-preview-depth" in text
    assert "Source: rytm_randomizer.reports.controller_brain_live_desktop_view_model" in text


def test_desktop_view_model_stays_passive_and_blocks_runtime_paths() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_view_model import (
        build_controller_brain_live_desktop_view_model_report,
    )

    report = build_controller_brain_live_desktop_view_model_report()

    assert "passive/read-only" in report.safety_lines
    assert "controller-brain desktop view model metadata only" in report.safety_lines
    assert "component view models are declarative metadata only" in report.safety_lines
    assert "state bindings are declarative metadata only" in report.safety_lines
    assert "disabled action models are metadata only" in report.safety_lines
    assert "render assertions are metadata only" in report.safety_lines
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
    assert "mount component view models" in report.blocked_actions
    assert "execute live state reducer" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "emit controller feedback" in report.blocked_actions
    assert "open MIDI output" in report.blocked_actions
    assert "mutate a snapshot" in report.blocked_actions
    assert all(view_model.enabled is False for view_model in report.component_view_models)
    assert all(view_model.passive for view_model in report.component_view_models)
    assert all(binding.passive for binding in report.state_bindings)
    assert all(action.enabled is False for action in report.disabled_action_models)
    assert all(action.passive for action in report.disabled_action_models)
    assert all(assertion.passive for assertion in report.render_assertions)
    assert all(check.passive for check in report.acceptance_checks)


def test_desktop_view_model_json_payload_is_deterministic_and_runtime_safe() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_view_model import (
        build_controller_brain_live_desktop_view_model_payload,
    )

    first = build_controller_brain_live_desktop_view_model_payload(
        session_label="Warehouse arc",
        view_model_label="Warehouse view model",
        state_prefix="warehouse-state",
    )
    second = build_controller_brain_live_desktop_view_model_payload(
        session_label="Warehouse arc",
        view_model_label="Warehouse view model",
        state_prefix="warehouse-state",
    )

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    model = first["controller_brain_live_desktop_view_model"]
    assert model["desktop_view_model_version"] == ("controller-brain-live-desktop-view-model-v1")
    assert model["desktop_view_model_status"] == "desktop-view-model-passive"
    assert model["view_model_label"] == "Warehouse view model"
    assert model["state_prefix"] == "warehouse-state"
    assert model["component_view_model_count"] == 27
    assert model["state_binding_count"] == 27
    assert model["disabled_action_model_count"] == 27
    assert model["render_assertion_count"] == 27
    assert model["acceptance_check_count"] == 7
    assert model["component_view_models"][0]["state_key"] == (
        "warehouse-state.state.global-preview-depth"
    )
    assert model["state_bindings"][0]["fallback_state"] == "disabled"
    assert model["disabled_action_models"][0]["control_state"] == "disabled"
    assert model["render_assertions"][0]["required_state"] == "disabled"
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
        "component_view_models",
        "state_bindings",
        "disabled_action_models",
        "render_assertions",
        "acceptance_checks",
    ):
        assert all(forbidden_keys.isdisjoint(row) for row in model[collection_name])


def test_desktop_view_model_cli_supports_text_json_and_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_live_desktop_view_model import (
        CONTROLLER_BRAIN_LIVE_DESKTOP_VIEW_MODEL_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_LIVE_DESKTOP_VIEW_MODEL_CLI_COMMAND.args_parser([]) == {
        "view_model_label": "Controller brain desktop view model",
        "state_prefix": "rr-state",
        "json_output": False,
    }
    assert CONTROLLER_BRAIN_LIVE_DESKTOP_VIEW_MODEL_CLI_COMMAND.args_parser(
        [
            "--view-model-label",
            "Warehouse view model",
            "--state-prefix",
            "warehouse-state",
            "--json",
        ]
    ) == {
        "view_model_label": "Warehouse view model",
        "state_prefix": "warehouse-state",
        "json_output": True,
    }
    with pytest.raises(
        ValueError,
        match=(
            "controller-brain-live-desktop-view-model-report accepts --json, "
            "--view-model-label, and --state-prefix only"
        ),
    ):
        CONTROLLER_BRAIN_LIVE_DESKTOP_VIEW_MODEL_CLI_COMMAND.args_parser(["--arm"])
    with pytest.raises(ValueError, match="view_model_label must not be blank"):
        CONTROLLER_BRAIN_LIVE_DESKTOP_VIEW_MODEL_CLI_COMMAND.args_parser(
            ["--view-model-label", " "]
        )
    with pytest.raises(ValueError, match="state_prefix must not be blank"):
        CONTROLLER_BRAIN_LIVE_DESKTOP_VIEW_MODEL_CLI_COMMAND.args_parser(["--state-prefix", " "])
    with pytest.raises(ValueError, match="state_prefix must use letters"):
        CONTROLLER_BRAIN_LIVE_DESKTOP_VIEW_MODEL_CLI_COMMAND.args_parser(
            ["--state-prefix", "bad prefix"]
        )
    with pytest.raises(
        ValueError,
        match="controller-brain-live-desktop-view-model-report accepts --json",
    ):
        CONTROLLER_BRAIN_LIVE_DESKTOP_VIEW_MODEL_CLI_COMMAND.args_parser(["--view-model-label"])
    assert (
        CONTROLLER_BRAIN_LIVE_DESKTOP_VIEW_MODEL_CLI_COMMAND.error_formatter(
            ValueError("bad input")
        )
        == "Error: bad input"
    )

    assert main(["controller-brain-live-desktop-view-model-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain live desktop view model" in captured.out
    assert "rr-state.state.global-preview-depth" in captured.out
    assert "desktop-view-model-passive" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "controller-brain-live-desktop-view-model-report",
                "--view-model-label",
                "Warehouse view model",
                "--state-prefix",
                "warehouse-state",
                "--json",
            ]
        )
        == 0
    )
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_live_desktop_view_model"]
    assert model["desktop_view_model_status"] == "desktop-view-model-passive"
    assert model["state_prefix"] == "warehouse-state"


def test_desktop_view_model_cli_imports_no_real_midi_modules() -> None:
    code = (
        "import sys\n"
        "from rytm_randomizer.cli import main\n"
        "raise SystemExit(main(['controller-brain-live-desktop-view-model-report']))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "RytmRandomizer passive controller brain live desktop view model" in (completed.stdout)

    probe = (
        "import sys\n"
        "from rytm_randomizer.cli import main\n"
        "main(['controller-brain-live-desktop-view-model-report'])\n"
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


def test_desktop_view_model_help_text_documents_passive_view_models() -> None:
    from rytm_randomizer.help_text import HELP_TEXT

    help_text = HELP_TEXT["controller-brain-live-desktop-view-model-report"]()

    assert "future component view models" in help_text
    assert "--view-model-label" in help_text
    assert "--state-prefix" in help_text
    assert "state bindings" in help_text
    assert "disabled action models" in help_text
    assert "render assertions" in help_text
    assert "no GUI launch" in help_text
    assert "no WebSocket dispatch" in help_text
    assert "no MIDI sending" in help_text
    assert "no file writing" in help_text


def test_desktop_view_model_helper_edges_are_deterministic() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_view_model import (
        ControllerBrainDesktopComponentViewModel,
        _desktop_view_model_count,
        _desktop_view_model_slug,
        _desktop_view_model_unique_tuple,
        _normalize_desktop_state_prefix,
        _normalize_view_model_label,
        _state_key_from_component_contract_key,
        _view_model_key_from_component_contract_key,
    )

    assert _desktop_view_model_slug("desktop.component.state.global_preview_depth") == (
        "desktop-component-state-global-preview-depth"
    )
    assert _desktop_view_model_unique_tuple(("a",), ("a", "b")) == ("a", "b")
    assert _desktop_view_model_count(("a", "b")) == 2
    assert (
        _view_model_key_from_component_contract_key(
            "desktop.contract.component.state.global-preview-depth"
        )
        == "desktop.viewmodel.state.global-preview-depth"
    )
    assert (
        _state_key_from_component_contract_key(
            "desktop.contract.component.state.global-preview-depth",
            state_prefix="rr-state",
        )
        == "rr-state.state.global-preview-depth"
    )
    assert _normalize_view_model_label("  Warehouse  ") == "Warehouse"
    assert _normalize_desktop_state_prefix(" rr-state ") == "rr-state"

    view_model = ControllerBrainDesktopComponentViewModel(
        view_model_key="desktop.viewmodel.state.global-preview-depth",
        order=1,
        component_contract_key="desktop.contract.component.state.global-preview-depth",
        selector="rr-controller-state-global-preview-depth",
        state_key="rr-state.state.global-preview-depth",
        component_type="controller-brain-card",
        status="view-model-disabled",
        enabled=False,
        passive=True,
        evidence="future view model only",
        blocked_action="mount component view models",
    )
    assert view_model.state_key == "rr-state.state.global-preview-depth"
