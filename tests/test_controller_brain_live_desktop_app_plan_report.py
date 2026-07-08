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


def test_desktop_app_plan_composes_blueprint_into_disabled_app_shell() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_app_plan import (
        build_controller_brain_live_desktop_app_plan_report,
        format_controller_brain_live_desktop_app_plan_report,
    )

    report = build_controller_brain_live_desktop_app_plan_report(
        session_label="Warehouse arc",
        app_plan_label="Warehouse controller desktop",
        framework_target="desktop-python",
    )

    assert report.desktop_app_plan_version == "controller-brain-live-desktop-app-plan-v1"
    assert report.desktop_app_plan_status == "desktop-app-plan-passive"
    assert report.session_label == "Warehouse arc"
    assert report.app_plan_label == "Warehouse controller desktop"
    assert report.framework_target == "desktop-python"
    assert report.source_report == "controller-brain-live-desktop-blueprint-report"
    assert report.source_desktop_blueprint_version == ("controller-brain-live-desktop-blueprint-v1")
    assert report.source_desktop_blueprint_status == "desktop-blueprint-passive"
    assert report.source_region_count == 6
    assert report.source_component_contract_count == 27
    assert report.route_count == 6
    assert report.component_file_hint_count == 27
    assert report.state_slice_count == 27
    assert report.style_token_count == 6
    assert report.acceptance_check_count == 7

    first_route = report.app_routes[0]
    assert first_route.route_key == "desktop.route.controller-feedback-preview"
    assert first_route.source_region_key == "desktop.region.controller-feedback-preview"
    assert first_route.layout_area == "feedback-preview"
    assert first_route.shell_target == "operator-dashboard"
    assert first_route.enabled is False
    assert first_route.passive is True

    first_component = report.component_file_hints[0]
    assert first_component.component_file_key == (
        "desktop.file.component.state.global-preview-depth"
    )
    assert first_component.source_component_key == ("desktop.component.state.global-preview-depth")
    assert first_component.route_key == "desktop.route.controller-feedback-preview"
    assert first_component.suggested_module == (
        "future_controller_brain/components/state_global_preview_depth.py"
    )
    assert first_component.status == "component-file-hint-ready"
    assert first_component.passive is True

    first_state = report.state_slices[0]
    assert first_state.state_slice_key == "desktop.state.state.global-preview-depth"
    assert first_state.source_component_key == ("desktop.component.state.global-preview-depth")
    assert first_state.reducer_hint == "reduce-state-global-preview-depth"
    assert first_state.initial_state == "disabled"
    assert first_state.enabled is False

    text = "\n".join(format_controller_brain_live_desktop_app_plan_report(report))
    assert "RytmRandomizer passive controller brain live desktop app plan" in text
    assert "Controller brain live desktop app plan:" in text
    assert "- source desktop blueprint: controller-brain-live-desktop-blueprint-report" in text
    assert "- app routes: 6" in text
    assert "- component file hints: 27" in text
    assert "- state slices: 27" in text
    assert "desktop.file.component.state.global-preview-depth" in text
    assert "Source: rytm_randomizer.reports.controller_brain_live_desktop_app_plan" in text


def test_desktop_app_plan_stays_passive_and_blocks_runtime_paths() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_app_plan import (
        build_controller_brain_live_desktop_app_plan_report,
    )

    report = build_controller_brain_live_desktop_app_plan_report()

    assert "passive/read-only" in report.safety_lines
    assert "controller-brain desktop app plan metadata only" in report.safety_lines
    assert "app routes are declarative metadata only" in report.safety_lines
    assert "component file hints are advisory metadata only" in report.safety_lines
    assert "state slices are declarative metadata only" in report.safety_lines
    assert "style tokens are declarative metadata only" in report.safety_lines
    assert "acceptance checks are metadata only" in report.safety_lines
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
    assert "mount desktop routes" in report.blocked_actions
    assert "write component files" in report.blocked_actions
    assert "execute live state reducer" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "emit controller feedback" in report.blocked_actions
    assert "open MIDI output" in report.blocked_actions
    assert "mutate a snapshot" in report.blocked_actions
    assert all(route.enabled is False for route in report.app_routes)
    assert all(route.passive for route in report.app_routes)
    assert all(hint.passive for hint in report.component_file_hints)
    assert all(slice_.enabled is False for slice_ in report.state_slices)
    assert all(slice_.passive for slice_ in report.state_slices)
    assert all(token.passive for token in report.style_tokens)
    assert all(check.passive for check in report.acceptance_checks)


def test_desktop_app_plan_json_payload_is_deterministic_and_runtime_safe() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_app_plan import (
        build_controller_brain_live_desktop_app_plan_payload,
    )

    first = build_controller_brain_live_desktop_app_plan_payload(
        session_label="Warehouse arc",
        app_plan_label="Warehouse controller desktop",
        framework_target="test-harness",
    )
    second = build_controller_brain_live_desktop_app_plan_payload(
        session_label="Warehouse arc",
        app_plan_label="Warehouse controller desktop",
        framework_target="test-harness",
    )

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    model = first["controller_brain_live_desktop_app_plan"]
    assert model["desktop_app_plan_version"] == "controller-brain-live-desktop-app-plan-v1"
    assert model["desktop_app_plan_status"] == "desktop-app-plan-passive"
    assert model["app_plan_label"] == "Warehouse controller desktop"
    assert model["framework_target"] == "test-harness"
    assert model["source_report"] == "controller-brain-live-desktop-blueprint-report"
    assert model["route_count"] == 6
    assert model["component_file_hint_count"] == 27
    assert model["state_slice_count"] == 27
    assert model["style_token_count"] == 6
    assert model["acceptance_check_count"] == 7
    assert model["app_routes"][0]["source_region_key"] == (
        "desktop.region.controller-feedback-preview"
    )
    assert model["component_file_hints"][0]["source_component_key"] == (
        "desktop.component.state.global-preview-depth"
    )
    assert model["state_slices"][0]["state_slice_key"] == (
        "desktop.state.state.global-preview-depth"
    )
    assert model["style_tokens"][0]["token_key"] == "controller-brain.color.surface"
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
        "app_routes",
        "component_file_hints",
        "state_slices",
        "style_tokens",
        "acceptance_checks",
    ):
        assert all(forbidden_keys.isdisjoint(row) for row in model[collection_name])


def test_desktop_app_plan_cli_supports_text_json_and_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_live_desktop_app_plan import (
        CONTROLLER_BRAIN_LIVE_DESKTOP_APP_PLAN_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_LIVE_DESKTOP_APP_PLAN_CLI_COMMAND.args_parser([]) == {
        "app_plan_label": "Controller brain desktop app plan",
        "framework_target": "desktop-python",
        "json_output": False,
    }
    assert CONTROLLER_BRAIN_LIVE_DESKTOP_APP_PLAN_CLI_COMMAND.args_parser(
        [
            "--app-plan-label",
            "Warehouse controller desktop",
            "--framework-target",
            "web-desktop",
            "--json",
        ]
    ) == {
        "app_plan_label": "Warehouse controller desktop",
        "framework_target": "web-desktop",
        "json_output": True,
    }
    with pytest.raises(
        ValueError,
        match="controller-brain-live-desktop-app-plan-report accepts --json, --app-plan-label, and --framework-target only",
    ):
        CONTROLLER_BRAIN_LIVE_DESKTOP_APP_PLAN_CLI_COMMAND.args_parser(["--arm"])
    with pytest.raises(ValueError, match="app_plan_label must not be blank"):
        CONTROLLER_BRAIN_LIVE_DESKTOP_APP_PLAN_CLI_COMMAND.args_parser(["--app-plan-label", " "])
    with pytest.raises(
        ValueError,
        match="controller-brain-live-desktop-app-plan-report accepts --json",
    ):
        CONTROLLER_BRAIN_LIVE_DESKTOP_APP_PLAN_CLI_COMMAND.args_parser(["--app-plan-label"])
    with pytest.raises(ValueError, match="framework_target must be"):
        CONTROLLER_BRAIN_LIVE_DESKTOP_APP_PLAN_CLI_COMMAND.args_parser(
            ["--framework-target", "mobile"]
        )

    assert main(["controller-brain-live-desktop-app-plan-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain live desktop app plan" in captured.out
    assert "desktop.file.component.state.global-preview-depth" in captured.out
    assert "desktop-app-plan-passive" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "controller-brain-live-desktop-app-plan-report",
                "--app-plan-label",
                "Warehouse controller desktop",
                "--framework-target",
                "web-desktop",
                "--json",
            ]
        )
        == 0
    )
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_live_desktop_app_plan"]
    assert model["desktop_app_plan_status"] == "desktop-app-plan-passive"
    assert model["app_plan_label"] == "Warehouse controller desktop"
    assert model["framework_target"] == "web-desktop"

    assert main(["controller-brain-live-desktop-app-plan-report", "--arm"]) == 2
    captured_error = capsys.readouterr()
    assert captured_error.out == ""
    assert "accepts --json, --app-plan-label, and --framework-target only" in (captured_error.err)


def test_desktop_app_plan_cli_imports_no_real_midi_modules() -> None:
    forbidden_modules = repr(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main(["controller-brain-live-desktop-app-plan-report", "--json"])
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


def test_desktop_app_plan_help_mentions_disabled_app_plan() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("controller-brain-live-desktop-app-plan-report")

    assert help_text.startswith(
        "RytmRandomizer passive CLI: controller-brain-live-desktop-app-plan-report"
    )
    assert "controller-brain live desktop app plan" in help_text
    assert "app routes" in help_text
    assert "component file hints" in help_text
    assert "state slices" in help_text
    assert "style tokens" in help_text
    assert "acceptance checks" in help_text
    assert "no GUI launch" in help_text
    assert "no app launch" in help_text
    assert "no runtime reducer execution" in help_text
    assert "no WebSocket dispatch" in help_text
    assert "no controller feedback emission" in help_text
    assert "no MIDI sending" in help_text
    assert "no file writing" in help_text


def test_desktop_app_plan_defensive_helpers_keep_contract_stable() -> None:
    from rytm_randomizer.reports import controller_brain_live_desktop_app_plan as app_plan

    assert (
        app_plan._desktop_app_plan_slug("desktop.component.state.global_preview_depth")
        == "desktop-component-state-global-preview-depth"
    )
    assert app_plan._desktop_app_plan_unique_tuple(("a",), ("a", "b")) == ("a", "b")
    assert app_plan._desktop_app_plan_count(("a", "b")) == 2
    assert (
        app_plan._component_file_key_from_component_key(
            "desktop.component.state.global-preview-depth"
        )
        == "desktop.file.component.state.global-preview-depth"
    )
    assert (
        app_plan._state_slice_key_from_component_key("desktop.component.state.global-preview-depth")
        == "desktop.state.state.global-preview-depth"
    )
    assert app_plan._normalize_app_plan_label("  Warehouse  ") == "Warehouse"
    assert app_plan._normalize_desktop_app_plan_framework_target("web-desktop") == "web-desktop"

    route = app_plan.ControllerBrainDesktopAppRoute(
        route_key="desktop.route.custom",
        order=3,
        label="Custom",
        source_region_key="desktop.region.custom",
        layout_area="custom",
        shell_target="operator-dashboard",
        status="disabled-route-ready",
        enabled=False,
        passive=True,
        evidence="custom evidence",
        blocked_action="none",
    )

    assert app_plan._app_route_to_payload(route) == {
        "route_key": "desktop.route.custom",
        "order": 3,
        "label": "Custom",
        "source_region_key": "desktop.region.custom",
        "layout_area": "custom",
        "shell_target": "operator-dashboard",
        "status": "disabled-route-ready",
        "enabled": False,
        "passive": True,
        "evidence": "custom evidence",
        "blocked_action": "none",
    }
