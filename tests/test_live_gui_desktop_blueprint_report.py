"""Tests for passive live GUI desktop blueprint reporting."""

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
        derived_at="2026-05-23T23:45:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _implementation_bridge(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_implementation_bridge import (
        build_style_performance_arc_live_gui_implementation_bridge_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_implementation_bridge_report(
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
    )


def test_live_gui_desktop_blueprint_builds_from_bridge(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_desktop_blueprint import (
        build_style_performance_arc_live_gui_desktop_blueprint_from_bridge,
        format_style_performance_arc_live_gui_desktop_blueprint_report,
        to_style_performance_arc_live_gui_desktop_blueprint_json,
    )

    bridge = _implementation_bridge(tmp_path)
    report = build_style_performance_arc_live_gui_desktop_blueprint_from_bridge(
        bridge,
        blueprint_label="Warehouse desktop blueprint",
    )

    assert report.blueprint_version == "live-gui-desktop-blueprint-v1"
    assert len(report.blueprint_id) == 16
    assert report.blueprint_label == "Warehouse desktop blueprint"
    assert report.blueprint_status == "ready"
    assert report.bridge_id == bridge.bridge_id
    assert report.readiness_id == bridge.readiness_id
    assert report.selected_arc_key == bridge.selected_arc_key
    assert report.scope == bridge.scope
    assert "blueprint sections" in report.section_summary
    assert "implementation tasks" in report.task_summary
    assert "fixture file hints" in report.fixture_summary
    assert {section.section_key for section in report.sections} >= {
        "section-sidecar-session",
        "section-screen-contract",
        "section-render-tree",
        "section-controller-state",
        "section-test-harness-readiness",
    }
    assert all(section.passive for section in report.sections)
    assert {task.task_key for task in report.implementation_tasks} >= {
        "task-current-cue-panel",
        "task-machine-panels",
        "task-analyzer-overlay",
        "task-capture-review-panel",
        "task-controller-actions",
        "task-test-harness-panel",
    }
    assert all(not task.enabled for task in report.implementation_tasks)
    assert {fixture.fixture_key for fixture in report.fixture_file_hints} >= {
        "file-fixture-sidecar-session-json",
        "file-fixture-render-tree-json",
        "file-fixture-controller-state-json",
        "file-fixture-test-harness-readiness-json",
    }
    assert all(fixture.passive for fixture in report.fixture_file_hints)
    assert {check.check_key for check in report.acceptance_checks} >= {
        "accept-readiness-status",
        "accept-view-model-coverage",
        "accept-component-mount-coverage",
        "accept-fixture-bundle-coverage",
        "accept-passive-boundary",
    }
    assert "no GUI launch" in report.blocked_actions
    assert "no renderer execution" in report.blocked_actions
    assert "no file writing" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-desktop-blueprint-report"
    )
    assert "style-performance-arc-live-gui-implementation-bridge-report" not in (
        report.replay_commands[0]
    )
    assert "--bridge-label 'Warehouse implementation bridge'" in report.replay_commands[0]
    assert "--blueprint-label 'Warehouse desktop blueprint'" in report.replay_commands[0]
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-implementation-bridge-report"
    )

    lines = format_style_performance_arc_live_gui_desktop_blueprint_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI desktop blueprint"
    assert "Live GUI desktop blueprint summary:" in lines
    assert "Blueprint sections:" in lines
    assert "Implementation tasks:" in lines
    assert "Fixture file hints:" in lines
    assert "Acceptance checks:" in lines
    assert "Passive GUI desktop blueprint metadata only" in text
    assert "- no GUI launch" in lines
    assert "- no renderer execution" in lines
    assert "- no MIDI sending" in lines

    payload = to_style_performance_arc_live_gui_desktop_blueprint_json(report)
    blueprint = payload["live_gui_desktop_blueprint"]
    assert blueprint["blueprint_version"] == "live-gui-desktop-blueprint-v1"
    assert blueprint["blueprint_id"] == report.blueprint_id
    assert blueprint["bridge_id"] == bridge.bridge_id
    assert blueprint["sections"][0]["section_key"] == "section-sidecar-session"
    assert blueprint["implementation_tasks"][0]["task_key"] == "task-current-cue-panel"
    assert blueprint["fixture_file_hints"][0]["fixture_key"] == (
        "file-fixture-sidecar-session-json"
    )
    assert blueprint["acceptance_checks"][0]["check_key"] == "accept-bridge-status"
    assert "live_gui_implementation_bridge" in payload
    assert "live_gui_test_harness_readiness" in payload
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_desktop_blueprint_status_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_desktop_blueprint import (
        _acceptance_checks,
        _blueprint_status,
        _blueprint_tasks,
        build_style_performance_arc_live_gui_desktop_blueprint_from_bridge,
    )

    bridge = _implementation_bridge(tmp_path)

    blocked_report = build_style_performance_arc_live_gui_desktop_blueprint_from_bridge(
        replace(bridge, bridge_status="blocked")
    )
    assert blocked_report.blueprint_status == "blocked"
    assert "hold GUI desktop blueprint until implementation bridge is clear" in (
        blocked_report.blocked_actions
    )
    assert any(
        check.check_key == "accept-bridge-status" and check.status == "blocked"
        for check in blocked_report.acceptance_checks
    )

    review_report = build_style_performance_arc_live_gui_desktop_blueprint_from_bridge(
        replace(bridge, bridge_status="review-needed")
    )
    assert review_report.blueprint_status == "review-needed"
    assert any(check.status == "review-needed" for check in review_report.acceptance_checks)

    no_replay_report = build_style_performance_arc_live_gui_desktop_blueprint_from_bridge(
        replace(bridge, replay_commands=())
    )
    assert no_replay_report.blueprint_status == "review-needed"
    assert no_replay_report.replay_commands == ()
    assert any(
        check.check_key == "accept-replay-command" and check.status == "review-needed"
        for check in no_replay_report.acceptance_checks
    )

    malformed_replay_report = build_style_performance_arc_live_gui_desktop_blueprint_from_bridge(
        replace(bridge, replay_commands=("python -m rytm_randomizer.cli other-report",))
    )
    assert malformed_replay_report.blueprint_status == "review-needed"
    assert malformed_replay_report.replay_commands == (
        "python -m rytm_randomizer.cli other-report",
    )

    checks_with_empty_tasks = _acceptance_checks(
        bridge,
        sections=(),
        tasks=_blueprint_tasks((), blueprint_label="empty"),
        fixtures=(),
        replay_commands=malformed_replay_report.replay_commands,
    )
    assert _blueprint_status(bridge, checks_with_empty_tasks) == "blocked"
    assert any(
        check.check_key == "accept-section-coverage" and check.status == "blocked"
        for check in checks_with_empty_tasks
    )


def test_live_gui_desktop_blueprint_rejects_blank_label(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_desktop_blueprint import (
        build_style_performance_arc_live_gui_desktop_blueprint_from_bridge,
        parse_style_performance_arc_live_gui_desktop_blueprint_cli_args,
    )

    with pytest.raises(ValueError, match="blueprint_label must not be blank"):
        build_style_performance_arc_live_gui_desktop_blueprint_from_bridge(
            _implementation_bridge(tmp_path),
            blueprint_label=" ",
        )

    with pytest.raises(ValueError, match="usage"):
        parse_style_performance_arc_live_gui_desktop_blueprint_cli_args(["--description"])

    with pytest.raises(ValueError, match="blueprint_label must not be blank"):
        parse_style_performance_arc_live_gui_desktop_blueprint_cli_args(
            [
                "--description",
                "Jeff Mills pressure",
                "--capture-description",
                "captured warehouse pressure",
                "--blueprint-label",
                " ",
            ]
        )


def test_live_gui_desktop_blueprint_wrapper_and_parser_support_custom_labels(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_desktop_blueprint import (
        build_style_performance_arc_live_gui_desktop_blueprint_report,
        parse_style_performance_arc_live_gui_desktop_blueprint_cli_args,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    report = build_style_performance_arc_live_gui_desktop_blueprint_report(
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
    )
    assert report.blueprint_status == "ready"
    assert report.blueprint_label == "Direct wrapper blueprint"
    assert report.replay_commands[0].endswith("--blueprint-label 'Direct wrapper blueprint'")

    parsed = parse_style_performance_arc_live_gui_desktop_blueprint_cli_args(
        [
            "--description",
            "Jeff Mills and Oscar Mulero pressure",
            "--capture-description",
            "captured warehouse take",
            "--bridge-label",
            "Parsed bridge",
            "--blueprint-label",
            "Parsed blueprint",
            "--desktop-shell",
            "desktop-sidecar",
            "--json",
        ]
    )
    assert parsed["description"] == "Jeff Mills and Oscar Mulero pressure"
    assert parsed["capture_description"] == "captured warehouse take"
    assert parsed["bridge_label"] == "Parsed bridge"
    assert parsed["blueprint_label"] == "Parsed blueprint"
    assert parsed["desktop_shell"] == "desktop-sidecar"
    assert parsed["json_output"] is True

    with pytest.raises(ValueError, match="desktop_shell must be"):
        parse_style_performance_arc_live_gui_desktop_blueprint_cli_args(
            [
                "--description",
                "Jeff Mills and Oscar Mulero pressure",
                "--capture-description",
                "captured warehouse take",
                "--desktop-shell",
                "browser",
            ]
        )


def test_live_gui_desktop_blueprint_handler_outputs_text_json_and_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_desktop_blueprint import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_BLUEPRINT_CLI_COMMAND,
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
    }

    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_BLUEPRINT_CLI_COMMAND.handler(
            **base_kwargs,
            json_output=False,
        )
        == 0
    )
    text_output = capsys.readouterr()
    assert "Live GUI desktop blueprint summary:" in text_output.out
    assert text_output.err == ""

    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_BLUEPRINT_CLI_COMMAND.handler(
            **base_kwargs,
            json_output=True,
        )
        == 0
    )
    json_output = capsys.readouterr()
    assert (
        json.loads(json_output.out)["live_gui_desktop_blueprint"]["blueprint_label"]
        == "Handler blueprint"
    )
    assert json_output.err == ""

    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_BLUEPRINT_CLI_COMMAND.handler(
            **{**base_kwargs, "blueprint_label": " "},
            json_output=True,
        )
        == 2
    )
    error_output = capsys.readouterr()
    assert "blueprint_label must not be blank" in error_output.err

    assert _format_cli_error(ValueError("boom")) == "Error: boom"


def test_live_gui_desktop_blueprint_cli_json_is_passive(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    command = [
        sys.executable,
        "-m",
        "rytm_randomizer.cli",
        "style-performance-arc-live-gui-desktop-blueprint-report",
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
    assert payload["live_gui_desktop_blueprint"]["blueprint_status"] == "blocked"
    assert payload["live_gui_desktop_blueprint"]["blueprint_label"] == (
        "Warehouse desktop blueprint"
    )
    assert (
        "hold GUI desktop blueprint until implementation bridge is clear"
        in payload["live_gui_desktop_blueprint"]["blocked_actions"]
    )
    assert "live_gui_implementation_bridge" in payload

    module_snapshot_command = [
        sys.executable,
        "-c",
        (
            "import sys; "
            "import rytm_randomizer.reports.live_gui_desktop_blueprint; "
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
