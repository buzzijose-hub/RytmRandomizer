"""Tests for passive live GUI desktop app-plan reporting."""

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


def _desktop_blueprint(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_desktop_blueprint import (
        build_style_performance_arc_live_gui_desktop_blueprint_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_desktop_blueprint_report(
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
    )


def test_live_gui_desktop_app_plan_builds_from_blueprint(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_desktop_app_plan import (
        build_style_performance_arc_live_gui_desktop_app_plan_from_blueprint,
        format_style_performance_arc_live_gui_desktop_app_plan_report,
        to_style_performance_arc_live_gui_desktop_app_plan_json,
    )

    blueprint = _desktop_blueprint(tmp_path)
    report = build_style_performance_arc_live_gui_desktop_app_plan_from_blueprint(
        blueprint,
        app_plan_label="Warehouse desktop app plan",
    )

    assert report.app_plan_version == "live-gui-desktop-app-plan-v1"
    assert len(report.app_plan_id) == 16
    assert report.app_plan_label == "Warehouse desktop app plan"
    assert report.app_plan_status == "ready"
    assert report.framework_target == "desktop-python"
    assert report.blueprint_id == blueprint.blueprint_id
    assert report.bridge_id == blueprint.bridge_id
    assert report.readiness_id == blueprint.readiness_id
    assert report.selected_arc_key == blueprint.selected_arc_key
    assert report.scope == blueprint.scope
    assert "routes" in report.route_summary
    assert "component files" in report.component_summary
    assert "state slices" in report.state_summary
    assert "style tokens" in report.style_summary
    assert {route.route_key for route in report.routes} >= {
        "route-current-cue",
        "route-machine-grid",
        "route-analyzer",
        "route-capture-review",
        "route-controls",
        "route-harness",
    }
    assert all(not route.enabled for route in report.routes)
    assert {component.component_key for component in report.component_files} >= {
        "current-cue-panel",
        "machine-panels",
        "analyzer-overlay",
        "capture-review-panel",
        "controller-actions",
        "test-harness-panel",
    }
    assert all(component.passive for component in report.component_files)
    assert {slice_.slice_key for slice_ in report.state_slices} >= {
        "slice-current-cue-panel",
        "slice-machine-panels",
        "slice-analyzer-overlay",
        "slice-capture-review-panel",
        "slice-controller-actions",
        "slice-test-harness-panel",
    }
    assert {token.token_key for token in report.style_tokens} >= {
        "token-surface",
        "token-panel",
        "token-warning",
        "token-disabled",
    }
    assert {check.check_key for check in report.acceptance_checks} >= {
        "accept-blueprint-status",
        "accept-route-coverage",
        "accept-component-file-coverage",
        "accept-state-slice-coverage",
        "accept-style-token-coverage",
        "accept-passive-boundary",
    }
    assert "no GUI launch" in report.blocked_actions
    assert "no dev-server launch" in report.blocked_actions
    assert "no file writing" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-desktop-app-plan-report"
    )
    assert "style-performance-arc-live-gui-desktop-blueprint-report" not in (
        report.replay_commands[0]
    )
    assert "--blueprint-label 'Warehouse desktop blueprint'" in report.replay_commands[0]
    assert "--app-plan-label 'Warehouse desktop app plan'" in report.replay_commands[0]
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-desktop-blueprint-report"
    )

    lines = format_style_performance_arc_live_gui_desktop_app_plan_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI desktop app plan"
    assert "Live GUI desktop app plan summary:" in lines
    assert "App routes:" in lines
    assert "Component file hints:" in lines
    assert "State slices:" in lines
    assert "Style tokens:" in lines
    assert "Acceptance checks:" in lines
    assert "Passive GUI desktop app-plan metadata only" in text
    assert "- no GUI launch" in lines
    assert "- no dev-server launch" in lines
    assert "- no MIDI sending" in lines

    payload = to_style_performance_arc_live_gui_desktop_app_plan_json(report)
    app_plan = payload["live_gui_desktop_app_plan"]
    assert app_plan["app_plan_version"] == "live-gui-desktop-app-plan-v1"
    assert app_plan["app_plan_id"] == report.app_plan_id
    assert app_plan["blueprint_id"] == blueprint.blueprint_id
    assert app_plan["routes"][0]["route_key"] == "route-current-cue"
    assert app_plan["component_files"][0]["component_key"] == "current-cue-panel"
    assert app_plan["state_slices"][0]["slice_key"] == "slice-current-cue-panel"
    assert app_plan["style_tokens"][0]["token_key"] == "token-surface"
    assert app_plan["acceptance_checks"][0]["check_key"] == "accept-blueprint-status"
    assert "live_gui_desktop_blueprint" in payload
    assert "live_gui_implementation_bridge" in payload
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_desktop_app_plan_status_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_desktop_app_plan import (
        _acceptance_checks,
        _app_plan_status,
        _component_files,
        _component_key_from_widget,
        _routes,
        _state_slices,
        _style_tokens,
        build_style_performance_arc_live_gui_desktop_app_plan_from_blueprint,
    )

    blueprint = _desktop_blueprint(tmp_path)

    blocked_report = build_style_performance_arc_live_gui_desktop_app_plan_from_blueprint(
        replace(blueprint, blueprint_status="blocked")
    )
    assert blocked_report.app_plan_status == "blocked"
    assert "hold desktop app plan until desktop blueprint is clear" in (
        blocked_report.blocked_actions
    )
    assert any(
        check.check_key == "accept-blueprint-status" and check.status == "blocked"
        for check in blocked_report.acceptance_checks
    )

    review_report = build_style_performance_arc_live_gui_desktop_app_plan_from_blueprint(
        replace(blueprint, blueprint_status="review-needed")
    )
    assert review_report.app_plan_status == "review-needed"
    assert any(check.status == "review-needed" for check in review_report.acceptance_checks)

    no_replay_report = build_style_performance_arc_live_gui_desktop_app_plan_from_blueprint(
        replace(blueprint, replay_commands=())
    )
    assert no_replay_report.app_plan_status == "review-needed"
    assert no_replay_report.replay_commands == ()
    assert any(
        check.check_key == "accept-replay-command" and check.status == "review-needed"
        for check in no_replay_report.acceptance_checks
    )

    malformed_replay_report = build_style_performance_arc_live_gui_desktop_app_plan_from_blueprint(
        replace(blueprint, replay_commands=("python -m rytm_randomizer.cli other-report",))
    )
    assert malformed_replay_report.app_plan_status == "review-needed"
    assert malformed_replay_report.replay_commands == (
        "python -m rytm_randomizer.cli other-report",
    )

    checks_with_empty_routes = _acceptance_checks(
        blueprint,
        routes=(),
        component_files=_component_files(()),
        state_slices=_state_slices(()),
        style_tokens=_style_tokens(framework_target="desktop-python"),
        replay_commands=malformed_replay_report.replay_commands,
    )
    assert _app_plan_status(blueprint, checks_with_empty_routes) == "blocked"
    assert any(
        check.check_key == "accept-route-coverage" and check.status == "blocked"
        for check in checks_with_empty_routes
    )

    assert _routes(()) == ()
    assert _component_key_from_widget("custom-panel") == "custom-panel"


def test_live_gui_desktop_app_plan_rejects_blank_label(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_desktop_app_plan import (
        build_style_performance_arc_live_gui_desktop_app_plan_from_blueprint,
        parse_style_performance_arc_live_gui_desktop_app_plan_cli_args,
    )

    with pytest.raises(ValueError, match="app_plan_label must not be blank"):
        build_style_performance_arc_live_gui_desktop_app_plan_from_blueprint(
            _desktop_blueprint(tmp_path),
            app_plan_label=" ",
        )

    with pytest.raises(ValueError, match="usage"):
        parse_style_performance_arc_live_gui_desktop_app_plan_cli_args(["--description"])

    with pytest.raises(ValueError, match="app_plan_label must not be blank"):
        parse_style_performance_arc_live_gui_desktop_app_plan_cli_args(
            [
                "--description",
                "Jeff Mills pressure",
                "--capture-description",
                "captured warehouse pressure",
                "--app-plan-label",
                " ",
            ]
        )


def test_live_gui_desktop_app_plan_wrapper_and_parser_support_custom_labels(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_desktop_app_plan import (
        build_style_performance_arc_live_gui_desktop_app_plan_report,
        parse_style_performance_arc_live_gui_desktop_app_plan_cli_args,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    report = build_style_performance_arc_live_gui_desktop_app_plan_report(
        feature_report=_feature_report(),
        capture_feature_report=_feature_report(
            bpm=141.8,
            low_end_weight=0.70,
            spectral_brightness=0.43,
            texture_noise=0.61,
            energy_arc=(0.20, 0.54, 0.86),
        ),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=3,
        lookahead_count=1,
        match_limit=1,
        take_count=1,
        slot_key="capture-001",
        bridge_label="Direct wrapper bridge",
        blueprint_label="Direct wrapper blueprint",
        app_plan_label="Direct wrapper app plan",
        framework_target="web-desktop",
    )
    assert report.app_plan_status == "ready"
    assert report.app_plan_label == "Direct wrapper app plan"
    assert report.framework_target == "web-desktop"
    assert report.replay_commands[0].endswith("--app-plan-label 'Direct wrapper app plan'")

    parsed = parse_style_performance_arc_live_gui_desktop_app_plan_cli_args(
        [
            "--description",
            "Jeff Mills and Oscar Mulero pressure",
            "--capture-description",
            "captured warehouse take",
            "--blueprint-label",
            "Parsed blueprint",
            "--app-plan-label",
            "Parsed app plan",
            "--framework-target",
            "test-harness",
            "--json",
        ]
    )
    assert parsed["description"] == "Jeff Mills and Oscar Mulero pressure"
    assert parsed["capture_description"] == "captured warehouse take"
    assert parsed["blueprint_label"] == "Parsed blueprint"
    assert parsed["app_plan_label"] == "Parsed app plan"
    assert parsed["framework_target"] == "test-harness"
    assert parsed["json_output"] is True

    with pytest.raises(ValueError, match="framework_target must be"):
        parse_style_performance_arc_live_gui_desktop_app_plan_cli_args(
            [
                "--description",
                "Jeff Mills and Oscar Mulero pressure",
                "--capture-description",
                "captured warehouse take",
                "--framework-target",
                "mobile",
            ]
        )


def test_live_gui_desktop_app_plan_handler_outputs_text_json_and_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_desktop_app_plan import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_APP_PLAN_CLI_COMMAND,
        _format_cli_error,
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
        "match_limit": 1,
        "take_count": 1,
        "slot_key": "capture-001",
        "queue_label": "Live GUI capture queue",
        "capture_prefix": "live-capture",
        "sidecar_label": "Live performance sidecar",
        "screen_label": "Live GUI screen contract",
        "layout_key": "operator-default",
        "viewport": "desktop",
        "render_target": "desktop-sidecar",
        "density": "standard",
        "overlay_label": "Live GUI overlay",
        "frame_label": "Live GUI frame",
        "interaction_label": "Live GUI interaction script",
        "reducer_label": "Live GUI action reducer",
        "controller_label": "Live GUI controller state",
        "playback_label": "Live GUI playback transcript",
        "validation_label": "Live GUI playback validation matrix",
        "harness_label": "Live GUI test-harness contract",
        "readiness_label": "Live GUI test-harness readiness",
        "bridge_label": "Handler bridge",
        "blueprint_label": "Handler blueprint",
        "desktop_shell": "operator-dashboard",
        "app_plan_label": "Handler app plan",
        "framework_target": "desktop-python",
    }

    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_APP_PLAN_CLI_COMMAND.handler(
            **base_kwargs,
            json_output=False,
        )
        == 0
    )
    text_output = capsys.readouterr()
    assert "Live GUI desktop app plan summary:" in text_output.out
    assert text_output.err == ""

    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_APP_PLAN_CLI_COMMAND.handler(
            **base_kwargs,
            json_output=True,
        )
        == 0
    )
    json_output = capsys.readouterr()
    assert json.loads(json_output.out)["live_gui_desktop_app_plan"]["app_plan_label"] == (
        "Handler app plan"
    )
    assert json_output.err == ""

    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_APP_PLAN_CLI_COMMAND.handler(
            **{**base_kwargs, "app_plan_label": " "},
            json_output=True,
        )
        == 2
    )
    error_output = capsys.readouterr()
    assert "app_plan_label must not be blank" in error_output.err

    assert _format_cli_error(ValueError("boom")) == "Error: boom"


def test_live_gui_desktop_app_plan_cli_json_is_passive(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    command = [
        sys.executable,
        "-m",
        "rytm_randomizer.cli",
        "style-performance-arc-live-gui-desktop-app-plan-report",
        "--description",
        "Jeff Mills Oscar Mulero Birmingham pressure",
        "--capture-description",
        "captured warehouse take with tight low end and building pressure",
        "--rytm",
        str(rytm_path),
        "--analog-four",
        str(a4_path),
        "--cue",
        "2",
        "--lookahead",
        "2",
        "--matches",
        "2",
        "--takes",
        "2",
        "--slot",
        "capture-002",
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
        "--harness-label",
        "Warehouse harness contract",
        "--readiness-label",
        "Warehouse readiness packet",
        "--bridge-label",
        "Warehouse implementation bridge",
        "--blueprint-label",
        "Warehouse desktop blueprint",
        "--app-plan-label",
        "Warehouse desktop app plan",
        "--json",
    ]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["live_gui_desktop_app_plan"]["app_plan_status"] == "blocked"
    assert payload["live_gui_desktop_app_plan"]["app_plan_label"] == ("Warehouse desktop app plan")
    assert (
        "hold desktop app plan until desktop blueprint is clear"
        in payload["live_gui_desktop_app_plan"]["blocked_actions"]
    )
    assert "live_gui_desktop_blueprint" in payload

    module_snapshot_command = [
        sys.executable,
        "-c",
        (
            "import sys; "
            "import rytm_randomizer.reports.live_gui_desktop_app_plan; "
            "print('\\n'.join(sorted(sys.modules)))"
        ),
    ]
    module_snapshot = subprocess.run(
        module_snapshot_command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert module_snapshot.returncode == 0, module_snapshot.stderr
    imported_modules = set(module_snapshot.stdout.splitlines())
    assert not imported_modules.intersection(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
