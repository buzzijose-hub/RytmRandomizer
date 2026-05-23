from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)


def _feature_report(
    *,
    bpm: float = 142.0,
    low_end_weight: float = 0.71,
    spectral_brightness: float = 0.45,
    texture_noise: float = 0.66,
    energy_arc: tuple[float, ...] = (0.22, 0.55, 0.88),
):
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.MEDIUM,
        bpm=bpm,
        tempo_stability=0.87,
        kick_density=0.80,
        percussion_density=0.74,
        low_end_weight=low_end_weight,
        spectral_brightness=spectral_brightness,
        texture_noise=texture_noise,
        energy_arc=energy_arc,
        content_hash="",
        derived_at="2026-05-23T23:58:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _component_contract(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_desktop_component_contract import (
        build_style_performance_arc_live_gui_desktop_component_contract_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_desktop_component_contract_report(
        feature_report=_feature_report(),
        capture_feature_report=_feature_report(
            bpm=142.5,
            low_end_weight=0.72,
            spectral_brightness=0.46,
            texture_noise=0.63,
            energy_arc=(0.24, 0.57, 0.90),
        ),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=2,
        lookahead_count=2,
        match_limit=2,
        take_count=2,
        queue_label="Warehouse bridge queue",
        capture_prefix="warehouse",
        slot_key="capture-002",
        sidecar_label="Warehouse sidecar",
        screen_label="Warehouse screen",
        render_target="desktop-sidecar",
        density="standard",
        overlay_label="Warehouse overlay",
        frame_label="Warehouse frame",
        interaction_label="Warehouse interactions",
        reducer_label="Warehouse reducer",
        controller_label="Warehouse controller",
        playback_label="Warehouse playback transcript",
        validation_label="Warehouse validation matrix",
        harness_label="Warehouse harness contract",
        readiness_label="Warehouse readiness packet",
        bridge_label="Warehouse implementation bridge",
        blueprint_label="Warehouse desktop blueprint",
        desktop_shell="operator-dashboard",
        app_plan_label="Warehouse desktop app plan",
        framework_target="desktop-python",
        component_contract_label="Warehouse component contract",
        selector_prefix="warehouse-live",
    )


def test_live_gui_desktop_view_model_builds_from_component_contract(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_desktop_view_model import (
        build_style_performance_arc_live_gui_desktop_view_model_from_component_contract,
        format_style_performance_arc_live_gui_desktop_view_model_report,
        to_style_performance_arc_live_gui_desktop_view_model_json,
    )

    component_contract = _component_contract(tmp_path)
    report = build_style_performance_arc_live_gui_desktop_view_model_from_component_contract(
        component_contract,
        view_model_label="Warehouse desktop view model",
        state_prefix="warehouse-state",
    )

    assert report.view_model_version == "live-gui-desktop-view-model-v1"
    assert len(report.view_model_id) == 16
    assert report.view_model_label == "Warehouse desktop view model"
    assert report.view_model_status == "ready"
    assert report.state_prefix == "warehouse-state"
    assert report.component_contract_id == component_contract.component_contract_id
    assert report.app_plan_id == component_contract.app_plan_id
    assert report.selected_arc_key == component_contract.selected_arc_key
    assert report.scope == component_contract.scope
    assert "component view models" in report.component_summary
    assert "state bindings" in report.binding_summary
    assert "style tokens" in report.style_summary
    assert {component.component_key for component in report.component_view_models} >= {
        "current-cue-panel",
        "machine-panels",
        "analyzer-overlay",
        "capture-review-panel",
    }
    current_cue = next(
        component
        for component in report.component_view_models
        if component.component_key == "current-cue-panel"
    )
    assert current_cue.region_key == "region-current-cue"
    assert current_cue.state_key == "warehouse-state.current-cue-panel"
    assert current_cue.selector == "data-testid=warehouse-live-current-cue-panel"
    assert current_cue.enabled is False
    assert current_cue.passive is True
    source_prop = next(
        prop
        for prop in component_contract.prop_contracts
        if prop.component_key == "current-cue-panel" and prop.prop_name == "sourceData"
    )
    source_binding = next(
        binding
        for binding in report.state_bindings
        if binding.binding_key == "binding-current-cue-panel-sourceData"
    )
    assert source_binding.source_packet_key == source_prop.source_packet_key
    assert source_binding.source_json_key == source_prop.source_json_key
    assert source_binding.fallback_value == source_prop.fallback_value
    assert source_binding.required == source_prop.required
    app_style_token = next(
        token
        for token in component_contract.desktop_app_plan.style_tokens
        if token.token_key == "token-surface"
    )
    view_style_token = next(
        token for token in report.style_tokens if token.token_key == "token-surface"
    )
    assert view_style_token.framework_target == app_style_token.framework_target
    assert view_style_token.status == app_style_token.status
    assert all(not action.allowed for action in report.action_view_models)
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-desktop-view-model-report"
    )
    assert "--view-model-label 'Warehouse desktop view model'" in report.replay_commands[0]
    assert "--state-prefix warehouse-state" in report.replay_commands[0]
    assert report.replay_commands[1] == component_contract.replay_commands[0]
    assert "no GUI launch" in report.blocked_actions
    assert "no renderer execution" in report.blocked_actions

    lines = format_style_performance_arc_live_gui_desktop_view_model_report(report)
    assert "Live GUI desktop view model summary:" in lines
    assert "Component view models:" in lines
    assert "State bindings:" in lines
    assert "Action view models:" in lines
    assert "Style tokens:" in lines
    assert "- no MIDI sending" in lines

    payload = to_style_performance_arc_live_gui_desktop_view_model_json(report)
    view_model_payload = payload["live_gui_desktop_view_model"]
    assert view_model_payload["view_model_version"] == "live-gui-desktop-view-model-v1"
    assert view_model_payload["view_model_id"] == report.view_model_id
    assert view_model_payload["component_contract_id"] == component_contract.component_contract_id
    assert view_model_payload["component_view_models"][0]["component_key"] == (
        report.component_view_models[0].component_key
    )
    assert view_model_payload["state_bindings"][0]["source_json_key"] == (
        component_contract.prop_contracts[0].source_json_key
    )
    assert view_model_payload["style_tokens"][0]["framework_target"] == (
        component_contract.desktop_app_plan.style_tokens[0].framework_target
    )
    assert view_model_payload["style_tokens"][0]["status"] == (
        component_contract.desktop_app_plan.style_tokens[0].status
    )
    assert "live_gui_desktop_component_contract" in payload
    assert "live_gui_desktop_app_plan" in payload
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_desktop_view_model_status_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_desktop_view_model import (
        _acceptance_checks,
        _selector_text,
        _state_bindings,
        _view_model_status,
        build_style_performance_arc_live_gui_desktop_view_model_from_component_contract,
    )

    component_contract = _component_contract(tmp_path)

    blocked_report = (
        build_style_performance_arc_live_gui_desktop_view_model_from_component_contract(
            replace(component_contract, component_contract_status="blocked")
        )
    )
    assert blocked_report.view_model_status == "blocked"
    assert "hold view model until component contract is clear" in blocked_report.blocked_actions
    assert any(
        check.check_key == "accept-component-contract-status" and check.status == "blocked"
        for check in blocked_report.acceptance_checks
    )

    review_report = build_style_performance_arc_live_gui_desktop_view_model_from_component_contract(
        replace(component_contract, component_contract_status="review-needed")
    )
    assert review_report.view_model_status == "review-needed"
    assert any(check.status == "review-needed" for check in review_report.acceptance_checks)

    no_replay_report = (
        build_style_performance_arc_live_gui_desktop_view_model_from_component_contract(
            replace(component_contract, replay_commands=())
        )
    )
    assert no_replay_report.view_model_status == "review-needed"
    assert no_replay_report.replay_commands == ()

    malformed_replay = ("python -m rytm_randomizer.cli unrelated-report",)
    malformed_replay_report = (
        build_style_performance_arc_live_gui_desktop_view_model_from_component_contract(
            replace(component_contract, replay_commands=malformed_replay)
        )
    )
    assert malformed_replay_report.view_model_status == "review-needed"
    assert malformed_replay_report.replay_commands == malformed_replay

    checks_with_empty_components = _acceptance_checks(
        component_contract,
        component_view_models=(),
        state_bindings=_state_bindings(component_contract, ()),
        action_view_models=(),
        style_tokens=(),
        replay_commands=no_replay_report.replay_commands,
    )
    assert _view_model_status(component_contract, checks_with_empty_components) == "blocked"
    assert any(
        check.check_key == "accept-view-model-coverage" and check.status == "blocked"
        for check in checks_with_empty_components
    )
    assert _selector_text("warehouse-live-current-cue-panel") == (
        "data-testid=warehouse-live-current-cue-panel"
    )
    assert _selector_text("data-testid=warehouse-live-current-cue-panel") == (
        "data-testid=warehouse-live-current-cue-panel"
    )


def test_live_gui_desktop_view_model_rejects_blank_inputs(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_desktop_view_model import (
        build_style_performance_arc_live_gui_desktop_view_model_from_component_contract,
        parse_style_performance_arc_live_gui_desktop_view_model_cli_args,
    )

    with pytest.raises(ValueError, match="view_model_label"):
        build_style_performance_arc_live_gui_desktop_view_model_from_component_contract(
            _component_contract(tmp_path),
            view_model_label="  ",
        )
    with pytest.raises(ValueError, match="state_prefix"):
        build_style_performance_arc_live_gui_desktop_view_model_from_component_contract(
            _component_contract(tmp_path),
            state_prefix="  ",
        )
    with pytest.raises(ValueError, match="view-model-report usage"):
        parse_style_performance_arc_live_gui_desktop_view_model_cli_args(["--description"])


def test_live_gui_desktop_view_model_wrapper_and_parser_support_custom_labels(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_desktop_view_model import (
        build_style_performance_arc_live_gui_desktop_view_model_report,
        parse_style_performance_arc_live_gui_desktop_view_model_cli_args,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    report = build_style_performance_arc_live_gui_desktop_view_model_report(
        feature_report=_feature_report(),
        capture_feature_report=_feature_report(
            bpm=143.0,
            low_end_weight=0.73,
            spectral_brightness=0.47,
            texture_noise=0.64,
        ),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=3,
        lookahead_count=1,
        match_limit=2,
        take_count=2,
        component_contract_label="Custom component contract",
        selector_prefix="custom-live",
        view_model_label="Custom desktop view model",
        state_prefix="custom-state",
    )
    assert report.view_model_label == "Custom desktop view model"
    assert report.state_prefix == "custom-state"
    assert report.component_contract.component_contract_label == "Custom component contract"

    parsed = parse_style_performance_arc_live_gui_desktop_view_model_cli_args(
        [
            "--description",
            "Jeff Mills",
            "--capture-description",
            "warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--component-contract-label",
            "Custom component contract",
            "--selector-prefix",
            "custom-live",
            "--view-model-label",
            "Custom desktop view model",
            "--state-prefix",
            "custom-state",
            "--json",
        ]
    )
    assert parsed["component_contract_label"] == "Custom component contract"
    assert parsed["selector_prefix"] == "custom-live"
    assert parsed["view_model_label"] == "Custom desktop view model"
    assert parsed["state_prefix"] == "custom-state"
    assert parsed["json_output"] is True


def test_live_gui_desktop_view_model_handler_outputs_text_json_and_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_desktop_view_model import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_VIEW_MODEL_CLI_COMMAND,
        _handle_cli_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    base_kwargs = {
        "description": "Jeff Mills Birmingham pressure",
        "audio_path": None,
        "library_path": None,
        "capture_description": "captured warehouse take",
        "capture_audio_path": None,
        "capture_library_path": None,
        "rytm_sysex_path": rytm_path,
        "analog_four_sysex_path": a4_path,
        "scope": None,
        "selection_rank": None,
        "total_minutes": None,
        "segment_minutes": None,
        "discovery_start": None,
        "discovery_end": None,
        "cue_number": 1,
        "lookahead_count": 1,
        "match_limit": 2,
        "take_count": 1,
        "slot_key": "capture-001",
        "queue_label": "Queue",
        "capture_prefix": "warehouse",
        "sidecar_label": "Sidecar",
        "screen_label": "Screen",
        "layout_key": "operator-default",
        "viewport": "desktop",
        "render_target": "desktop-sidecar",
        "density": "standard",
        "overlay_label": "Overlay",
        "frame_label": "Frame",
        "interaction_label": "Interaction",
        "reducer_label": "Reducer",
        "controller_label": "Controller",
        "playback_label": "Playback",
        "validation_label": "Validation",
        "harness_label": "Harness",
        "readiness_label": "Readiness",
        "bridge_label": "Bridge",
        "blueprint_label": "Blueprint",
        "desktop_shell": "operator-dashboard",
        "app_plan_label": "App plan",
        "framework_target": "desktop-python",
        "component_contract_label": "Component contract",
        "selector_prefix": "live",
        "view_model_label": "View model",
        "state_prefix": "live-state",
    }

    text_rc = _handle_cli_report(
        **base_kwargs,
        json_output=False,
    )
    text_output = capsys.readouterr()
    assert text_rc == 0
    assert "Live GUI desktop view model summary:" in text_output.out
    assert text_output.err == ""

    json_rc = _handle_cli_report(
        **base_kwargs,
        json_output=True,
    )
    json_output = capsys.readouterr()
    assert json_rc == 0
    assert (
        json.loads(json_output.out)["live_gui_desktop_view_model"]["view_model_label"]
        == "View model"
    )
    assert json_output.err == ""

    error_rc = _handle_cli_report(
        **{
            **base_kwargs,
            "view_model_label": " ",
        },
        json_output=False,
    )
    error_output = capsys.readouterr()
    assert error_rc == 2
    assert "Error:" in error_output.err

    assert STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_VIEW_MODEL_CLI_COMMAND.name == (
        "style-performance-arc-live-gui-desktop-view-model-report"
    )
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_VIEW_MODEL_CLI_COMMAND.error_formatter(
            ValueError("boom")
        )
        == "Error: boom"
    )


def test_live_gui_desktop_view_model_cli_json_is_passive(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    command = [
        sys.executable,
        "-m",
        "rytm_randomizer.cli",
        "style-performance-arc-live-gui-desktop-view-model-report",
        "--description",
        "Jeff Mills Oscar Mulero Birmingham pressure",
        "--capture-description",
        "captured warehouse take with tight low end and building pressure",
        "--rytm",
        str(rytm_path),
        "--analog-four",
        str(a4_path),
        "--cue",
        "1",
        "--lookahead",
        "2",
        "--matches",
        "2",
        "--takes",
        "2",
        "--slot",
        "capture-001",
        "--capture-prefix",
        "warehouse",
        "--sidecar-label",
        "Warehouse sidecar",
        "--screen-label",
        "Warehouse screen",
        "--render-target",
        "desktop-sidecar",
        "--density",
        "standard",
        "--overlay-label",
        "Warehouse overlay",
        "--frame-label",
        "Warehouse frame",
        "--interaction-label",
        "Warehouse interactions",
        "--reducer-label",
        "Warehouse reducer",
        "--controller-label",
        "Warehouse controller",
        "--playback-label",
        "Warehouse playback",
        "--validation-label",
        "Warehouse validation",
        "--harness-label",
        "Warehouse harness",
        "--readiness-label",
        "Warehouse readiness",
        "--bridge-label",
        "Warehouse implementation bridge",
        "--blueprint-label",
        "Warehouse desktop blueprint",
        "--desktop-shell",
        "operator-dashboard",
        "--app-plan-label",
        "Warehouse desktop app plan",
        "--framework-target",
        "desktop-python",
        "--component-contract-label",
        "Warehouse component contract",
        "--selector-prefix",
        "warehouse-live",
        "--view-model-label",
        "Warehouse desktop view model",
        "--state-prefix",
        "warehouse-state",
        "--json",
    ]
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["live_gui_desktop_view_model"]["view_model_status"] in {
        "ready",
        "review-needed",
        "blocked",
    }
    assert payload["live_gui_desktop_view_model"]["state_prefix"] == "warehouse-state"
    assert "live_gui_desktop_view_model" in payload
    assert completed.stderr == ""

    module_snapshot = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.reports.live_gui_desktop_view_model; "
                "print('\\n'.join(sorted(sys.modules)))"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert module_snapshot.returncode == 0, module_snapshot.stderr
    imported_modules = set(module_snapshot.stdout.splitlines())
    assert not imported_modules.intersection(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
