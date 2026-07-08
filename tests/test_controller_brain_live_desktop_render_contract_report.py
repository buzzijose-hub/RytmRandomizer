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


def test_desktop_render_contract_composes_view_model_into_disabled_surfaces() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_render_contract import (
        build_controller_brain_live_desktop_render_contract_report,
        format_controller_brain_live_desktop_render_contract_report,
    )

    report = build_controller_brain_live_desktop_render_contract_report(
        session_label="Warehouse arc",
        render_contract_label="Warehouse render contract",
        surface_prefix="warehouse-render",
    )

    assert report.desktop_render_contract_version == (
        "controller-brain-live-desktop-render-contract-v1"
    )
    assert report.desktop_render_contract_status == "desktop-render-contract-passive"
    assert report.session_label == "Warehouse arc"
    assert report.render_contract_label == "Warehouse render contract"
    assert report.surface_prefix == "warehouse-render"
    assert report.source_report == "controller-brain-live-desktop-view-model-report"
    assert report.source_desktop_view_model_version == (
        "controller-brain-live-desktop-view-model-v1"
    )
    assert report.source_desktop_view_model_status == "desktop-view-model-passive"
    assert report.source_component_view_model_count == 27
    assert report.source_state_binding_count == 27
    assert report.source_disabled_action_model_count == 27
    assert report.render_surface_count == 27
    assert report.render_binding_count == 27
    assert report.render_guard_count == 27
    assert report.render_assertion_count == 27
    assert report.acceptance_check_count == 7

    first_surface = report.render_surfaces[0]
    assert first_surface.render_surface_key == "desktop.render.surface.state.global-preview-depth"
    assert first_surface.view_model_key == "desktop.viewmodel.state.global-preview-depth"
    assert first_surface.selector == "rr-controller-state-global-preview-depth"
    assert first_surface.surface_test_id == "warehouse-render-state-global-preview-depth"
    assert first_surface.state_key == "rr-state.state.global-preview-depth"
    assert first_surface.mount_mode == "disabled-passive"
    assert first_surface.enabled is False
    assert first_surface.passive is True

    first_binding = report.render_bindings[0]
    assert first_binding.render_binding_key == "desktop.render.binding.state.global-preview-depth"
    assert first_binding.render_surface_key == first_surface.render_surface_key
    assert first_binding.state_binding_key == "desktop.binding.state.global-preview-depth"
    assert first_binding.binding_mode == "one-way-disabled-state-to-render"
    assert first_binding.fallback_state == "disabled"

    first_guard = report.render_guards[0]
    assert first_guard.render_guard_key == "desktop.render.guard.state.global-preview-depth"
    assert first_guard.action_model_key == "desktop.action.state.global-preview-depth"
    assert first_guard.guard_state == "blocked"
    assert first_guard.blocked_action == "dispatch Cockpit WebSocket commands"

    first_assertion = report.render_assertions[0]
    assert first_assertion.render_contract_assertion_key == (
        "desktop.render.assert.state.global-preview-depth"
    )
    assert first_assertion.source_render_assertion_key == (
        "desktop.assert.state.global-preview-depth"
    )
    assert first_assertion.required_state == "disabled"

    text = "\n".join(format_controller_brain_live_desktop_render_contract_report(report))
    assert "RytmRandomizer passive controller brain live desktop render contract" in text
    assert "Controller brain live desktop render contract:" in text
    assert "- source desktop view model:" in text
    assert "- render surfaces: 27" in text
    assert "- render bindings: 27" in text
    assert "- render guards: 27" in text
    assert "warehouse-render-state-global-preview-depth" in text
    assert "Source: rytm_randomizer.reports.controller_brain_live_desktop_render_contract" in text


def test_desktop_render_contract_stays_passive_and_blocks_runtime_paths() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_render_contract import (
        build_controller_brain_live_desktop_render_contract_report,
    )

    report = build_controller_brain_live_desktop_render_contract_report()

    assert "passive/read-only" in report.safety_lines
    assert "controller-brain desktop render contract metadata only" in report.safety_lines
    assert "render surfaces are declarative metadata only" in report.safety_lines
    assert "render bindings are declarative metadata only" in report.safety_lines
    assert "render guards are metadata only" in report.safety_lines
    assert "render assertions are metadata only" in report.safety_lines
    assert "no GUI launch" in report.safety_lines
    assert "no app launch" in report.safety_lines
    assert "no component mount" in report.safety_lines
    assert "no GUI renderer start" in report.safety_lines
    assert "no renderer execution" in report.safety_lines
    assert "no WebSocket dispatch" in report.safety_lines
    assert "no MIDI controller output" in report.safety_lines
    assert "no MIDI sending" in report.safety_lines
    assert "no port opening" in report.safety_lines
    assert "no snapshot mutation" in report.safety_lines
    assert "no file writing" in report.safety_lines

    assert "launch Cockpit GUI runtime" in report.blocked_actions
    assert "launch desktop app shell" in report.blocked_actions
    assert "start GUI renderer" in report.blocked_actions
    assert "mount render surfaces" in report.blocked_actions
    assert "execute render bindings" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "open MIDI output" in report.blocked_actions
    assert all(surface.enabled is False for surface in report.render_surfaces)
    assert all(surface.passive for surface in report.render_surfaces)
    assert all(binding.passive for binding in report.render_bindings)
    assert all(guard.passive for guard in report.render_guards)
    assert all(assertion.passive for assertion in report.render_assertions)
    assert all(check.passive for check in report.acceptance_checks)


def test_desktop_render_contract_json_payload_is_deterministic_and_runtime_safe() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_render_contract import (
        build_controller_brain_live_desktop_render_contract_payload,
    )

    first = build_controller_brain_live_desktop_render_contract_payload(
        session_label="Warehouse arc",
        render_contract_label="Warehouse render contract",
        surface_prefix="warehouse-render",
    )
    second = build_controller_brain_live_desktop_render_contract_payload(
        session_label="Warehouse arc",
        render_contract_label="Warehouse render contract",
        surface_prefix="warehouse-render",
    )

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    contract = first["controller_brain_live_desktop_render_contract"]
    assert contract["desktop_render_contract_version"] == (
        "controller-brain-live-desktop-render-contract-v1"
    )
    assert contract["desktop_render_contract_status"] == "desktop-render-contract-passive"
    assert contract["render_contract_label"] == "Warehouse render contract"
    assert contract["surface_prefix"] == "warehouse-render"
    assert contract["render_surface_count"] == 27
    assert contract["render_binding_count"] == 27
    assert contract["render_guard_count"] == 27
    assert contract["render_assertion_count"] == 27
    assert contract["acceptance_check_count"] == 7
    assert contract["render_surfaces"][0]["surface_test_id"] == (
        "warehouse-render-state-global-preview-depth"
    )
    assert contract["render_bindings"][0]["binding_mode"] == ("one-way-disabled-state-to-render")
    assert contract["render_guards"][0]["guard_state"] == "blocked"
    assert contract["render_assertions"][0]["required_state"] == "disabled"
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
        "render_surfaces",
        "render_bindings",
        "render_guards",
        "render_assertions",
        "acceptance_checks",
    ):
        assert all(forbidden_keys.isdisjoint(row) for row in contract[collection_name])


def test_desktop_render_contract_cli_supports_text_json_and_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_live_desktop_render_contract import (
        CONTROLLER_BRAIN_LIVE_DESKTOP_RENDER_CONTRACT_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_LIVE_DESKTOP_RENDER_CONTRACT_CLI_COMMAND.args_parser([]) == {
        "render_contract_label": "Controller brain desktop render contract",
        "surface_prefix": "rr-render",
        "json_output": False,
    }
    assert CONTROLLER_BRAIN_LIVE_DESKTOP_RENDER_CONTRACT_CLI_COMMAND.args_parser(
        [
            "--render-contract-label",
            "Warehouse render contract",
            "--surface-prefix",
            "warehouse-render",
            "--json",
        ]
    ) == {
        "render_contract_label": "Warehouse render contract",
        "surface_prefix": "warehouse-render",
        "json_output": True,
    }
    with pytest.raises(
        ValueError,
        match=(
            "controller-brain-live-desktop-render-contract-report accepts --json, "
            "--render-contract-label, and --surface-prefix only"
        ),
    ):
        CONTROLLER_BRAIN_LIVE_DESKTOP_RENDER_CONTRACT_CLI_COMMAND.args_parser(["--arm"])
    with pytest.raises(ValueError, match="render_contract_label must not be blank"):
        CONTROLLER_BRAIN_LIVE_DESKTOP_RENDER_CONTRACT_CLI_COMMAND.args_parser(
            ["--render-contract-label", " "]
        )
    with pytest.raises(ValueError, match="surface_prefix must not be blank"):
        CONTROLLER_BRAIN_LIVE_DESKTOP_RENDER_CONTRACT_CLI_COMMAND.args_parser(
            ["--surface-prefix", " "]
        )
    with pytest.raises(ValueError, match="surface_prefix must use letters"):
        CONTROLLER_BRAIN_LIVE_DESKTOP_RENDER_CONTRACT_CLI_COMMAND.args_parser(
            ["--surface-prefix", "bad prefix"]
        )
    with pytest.raises(
        ValueError,
        match="controller-brain-live-desktop-render-contract-report accepts --json",
    ):
        CONTROLLER_BRAIN_LIVE_DESKTOP_RENDER_CONTRACT_CLI_COMMAND.args_parser(
            ["--render-contract-label"]
        )
    assert (
        CONTROLLER_BRAIN_LIVE_DESKTOP_RENDER_CONTRACT_CLI_COMMAND.error_formatter(
            ValueError("bad input")
        )
        == "Error: bad input"
    )

    assert main(["controller-brain-live-desktop-render-contract-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain live desktop render contract" in captured.out
    assert "rr-render-state-global-preview-depth" in captured.out
    assert "desktop-render-contract-passive" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "controller-brain-live-desktop-render-contract-report",
                "--render-contract-label",
                "Warehouse render contract",
                "--surface-prefix",
                "warehouse-render",
                "--json",
            ]
        )
        == 0
    )
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    contract = json.loads(captured_json.out)["controller_brain_live_desktop_render_contract"]
    assert contract["desktop_render_contract_status"] == "desktop-render-contract-passive"
    assert contract["surface_prefix"] == "warehouse-render"


def test_desktop_render_contract_cli_imports_no_real_midi_modules() -> None:
    code = (
        "import sys\n"
        "from rytm_randomizer.cli import main\n"
        "raise SystemExit(main(['controller-brain-live-desktop-render-contract-report']))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "RytmRandomizer passive controller brain live desktop render contract" in (
        completed.stdout
    )

    probe = (
        "import sys\n"
        "from rytm_randomizer.cli import main\n"
        "main(['controller-brain-live-desktop-render-contract-report'])\n"
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


def test_desktop_render_contract_help_text_documents_passive_contract() -> None:
    from rytm_randomizer.help_text import HELP_TEXT

    help_text = HELP_TEXT["controller-brain-live-desktop-render-contract-report"]()

    assert "future render surfaces" in help_text
    assert "--render-contract-label" in help_text
    assert "--surface-prefix" in help_text
    assert "render bindings" in help_text
    assert "render guards" in help_text
    assert "render assertions" in help_text
    assert "no GUI launch" in help_text
    assert "no renderer execution" in help_text
    assert "no WebSocket dispatch" in help_text
    assert "no MIDI sending" in help_text
    assert "no file writing" in help_text


def test_desktop_render_contract_helper_edges_are_deterministic() -> None:
    from rytm_randomizer.reports.controller_brain_live_desktop_render_contract import (
        ControllerBrainDesktopRenderSurface,
        _desktop_render_contract_count,
        _desktop_render_contract_slug,
        _desktop_render_contract_unique_tuple,
        _normalize_render_contract_label,
        _normalize_render_surface_prefix,
        _render_surface_key_from_view_model_key,
        _surface_test_id_from_view_model_key,
    )

    assert _desktop_render_contract_slug("desktop.viewmodel.state.global_preview_depth") == (
        "desktop-viewmodel-state-global-preview-depth"
    )
    assert _desktop_render_contract_unique_tuple(("a",), ("a", "b")) == ("a", "b")
    assert _desktop_render_contract_count(("a", "b")) == 2
    assert (
        _render_surface_key_from_view_model_key("desktop.viewmodel.state.global-preview-depth")
        == "desktop.render.surface.state.global-preview-depth"
    )
    assert (
        _surface_test_id_from_view_model_key(
            "desktop.viewmodel.state.global-preview-depth",
            surface_prefix="rr-render",
        )
        == "rr-render-state-global-preview-depth"
    )
    assert _normalize_render_contract_label("  Warehouse  ") == "Warehouse"
    assert _normalize_render_surface_prefix(" rr-render ") == "rr-render"
    assert (
        ControllerBrainDesktopRenderSurface(
            render_surface_key="desktop.render.surface.state.global-preview-depth",
            order=1,
            view_model_key="desktop.viewmodel.state.global-preview-depth",
            selector="rr-controller-state-global-preview-depth",
            surface_test_id="rr-render-state-global-preview-depth",
            state_key="rr-state.state.global-preview-depth",
            component_type="slider",
            mount_mode="disabled-passive",
            enabled=False,
            passive=True,
            evidence="metadata only",
            blocked_action="mount render surfaces",
        ).render_surface_key
        == "desktop.render.surface.state.global-preview-depth"
    )
