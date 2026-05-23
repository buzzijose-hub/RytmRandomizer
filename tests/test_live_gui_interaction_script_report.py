"""Tests for passive live GUI interaction-script reporting."""

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
    bpm: float = 141.0,
    low_end_weight: float = 0.69,
    spectral_brightness: float = 0.47,
    texture_noise: float = 0.62,
    energy_arc: tuple[float, ...] = (0.24, 0.52, 0.84),
):
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.MEDIUM,
        bpm=bpm,
        tempo_stability=0.88,
        kick_density=0.78,
        percussion_density=0.73,
        low_end_weight=low_end_weight,
        spectral_brightness=spectral_brightness,
        texture_noise=texture_noise,
        energy_arc=energy_arc,
        content_hash="",
        derived_at="2026-05-23T12:15:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _frame(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_analyzer_frame import (
        build_style_performance_arc_live_gui_analyzer_frame_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_analyzer_frame_report(
        feature_report=_feature_report(),
        capture_feature_report=_feature_report(
            bpm=141.5,
            low_end_weight=0.70,
            spectral_brightness=0.48,
            texture_noise=0.60,
            energy_arc=(0.26, 0.54, 0.86),
        ),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=1,
        match_limit=2,
        take_count=2,
        queue_label="Warehouse interaction queue",
        capture_prefix="warehouse",
        slot_key="capture-001",
        sidecar_label="Warehouse sidecar",
        screen_label="Warehouse screen",
        render_target="desktop-sidecar",
        density="standard",
        overlay_label="Warehouse overlay",
        frame_label="Warehouse frame",
    )


def test_live_gui_interaction_script_builds_operator_controls_from_frame(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_gui_interaction_script import (
        build_style_performance_arc_live_gui_interaction_script_from_frame,
        format_style_performance_arc_live_gui_interaction_script_report,
        to_style_performance_arc_live_gui_interaction_script_json,
    )

    frame = _frame(tmp_path)
    report = build_style_performance_arc_live_gui_interaction_script_from_frame(
        frame,
        interaction_label="Warehouse interaction script",
    )

    assert report.script_version == "live-gui-interaction-script-v1"
    assert len(report.script_id) == 16
    assert report.frame_id == frame.frame_id
    assert report.overlay_id == frame.overlay_id
    assert report.render_tree_id == frame.render_tree_id
    assert report.screen_contract_id == frame.screen_contract_id
    assert report.capture_review_id == frame.capture_review_id
    assert report.script_status == "ready"
    assert report.interaction_label == "Warehouse interaction script"
    assert [step.order for step in report.interaction_steps] == list(
        range(len(report.interaction_steps))
    )
    assert report.interaction_steps[0].action_type == "mount-frame"
    assert {step.action_type for step in report.interaction_steps} >= {
        "mount-frame",
        "inspect-meter",
        "inspect-threshold-marker",
        "review-capture-badge",
        "compare-reference",
        "hold-disabled-control",
    }
    assert {binding.control_type for binding in report.control_bindings} >= {
        "primary-action",
        "secondary-action",
        "danger-action",
        "disabled-action",
    }
    hardware_binding = next(
        binding for binding in report.control_bindings if binding.key == "control-arm-hardware"
    )
    assert hardware_binding.enabled is False
    assert hardware_binding.state == "disabled"
    assert "passive report" in hardware_binding.reason
    assert "no GUI event dispatch" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-interaction-script-report"
    )
    assert "style-performance-arc-live-gui-analyzer-frame-report" not in (report.replay_commands[0])
    assert "--frame-label 'Warehouse frame'" in report.replay_commands[0]
    assert "--interaction-label 'Warehouse interaction script'" in report.replay_commands[0]
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-analyzer-frame-report"
    )

    lines = format_style_performance_arc_live_gui_interaction_script_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI interaction script"
    assert "Live GUI interaction script summary:" in lines
    assert "Interaction steps:" in lines
    assert "GUI control bindings:" in lines
    assert "Passive GUI interaction metadata only" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_interaction_script_json(report)
    script = payload["live_gui_interaction_script"]
    assert script["script_version"] == "live-gui-interaction-script-v1"
    assert script["script_id"] == report.script_id
    assert script["frame_id"] == frame.frame_id
    assert script["interaction_steps"][0]["action_type"] == "mount-frame"
    assert script["control_bindings"][-1]["enabled"] is False
    assert payload["live_gui_analyzer_frame"]["frame_id"] == frame.frame_id
    assert payload["live_gui_analyzer_overlay"]["overlay_id"] == frame.overlay_id
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_interaction_script_maps_status_and_replay_fallback_edges(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_gui_interaction_script import (
        build_style_performance_arc_live_gui_interaction_script_from_frame,
    )

    frame = _frame(tmp_path)
    blocked_frame = replace(frame, frame_status="blocked")
    blocked_script = build_style_performance_arc_live_gui_interaction_script_from_frame(
        blocked_frame
    )
    assert blocked_script.script_status == "blocked"
    assert "hold interaction script before GUI binding" in blocked_script.blocked_actions

    review_frame = replace(frame, frame_status="review-needed")
    review_script = build_style_performance_arc_live_gui_interaction_script_from_frame(review_frame)
    assert review_script.script_status == "review-needed"

    empty_frame = replace(frame, frame_events=(), visual_assertions=())
    empty_script = build_style_performance_arc_live_gui_interaction_script_from_frame(empty_frame)
    assert [step.action_type for step in empty_script.interaction_steps] == [
        "mount-frame",
        "compare-reference",
        "hold-disabled-control",
    ]

    fallback_frame = replace(
        frame,
        replay_commands=("python -m rytm_randomizer.cli upstream",),
    )
    fallback_script = build_style_performance_arc_live_gui_interaction_script_from_frame(
        fallback_frame
    )
    assert fallback_script.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-interaction-script-report"
    )

    already_labeled_frame = replace(
        frame,
        replay_commands=(
            "python -m rytm_randomizer.cli "
            "style-performance-arc-live-gui-analyzer-frame-report "
            "--interaction-label 'Existing'",
        ),
    )
    already_labeled_script = build_style_performance_arc_live_gui_interaction_script_from_frame(
        already_labeled_frame
    )
    assert already_labeled_script.replay_commands[0].count("--interaction-label") == 1

    empty_replay_script = build_style_performance_arc_live_gui_interaction_script_from_frame(
        replace(frame, replay_commands=())
    )
    assert empty_replay_script.replay_commands == (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-interaction-script-report "
        "--interaction-label 'Live GUI interaction script'",
    )

    with pytest.raises(ValueError, match="interaction_label"):
        build_style_performance_arc_live_gui_interaction_script_from_frame(
            frame,
            interaction_label=" ",
        )


def test_live_gui_interaction_script_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_interaction_script import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_INTERACTION_SCRIPT_CLI_COMMAND,
        build_style_performance_arc_live_gui_interaction_script_report,
        to_style_performance_arc_live_gui_interaction_script_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = STYLE_PERFORMANCE_ARC_LIVE_GUI_INTERACTION_SCRIPT_CLI_COMMAND.args_parser(
        [
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
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
            "compact",
            "--overlay-label",
            "Warehouse overlay",
            "--frame-label",
            "Warehouse frame",
            "--interaction-label",
            "Warehouse interactions",
            "--json",
        ]
    )
    assert parsed["interaction_label"] == "Warehouse interactions"
    assert parsed["frame_label"] == "Warehouse frame"
    assert parsed["json_output"] is True

    with pytest.raises(ValueError, match="usage"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_INTERACTION_SCRIPT_CLI_COMMAND.args_parser(
            ["--interaction-label"]
        )

    report = build_style_performance_arc_live_gui_interaction_script_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        capture_description="captured warehouse take",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        frame_label="Warehouse frame",
        interaction_label="Warehouse interactions",
    )
    payload = to_style_performance_arc_live_gui_interaction_script_json(report)
    assert payload["live_gui_interaction_script"]["interaction_label"] == ("Warehouse interactions")

    rc = main(
        [
            "style-performance-arc-live-gui-interaction-script-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--interaction-label",
            "Warehouse interactions",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    cli_payload = json.loads(captured.out)
    assert cli_payload["live_gui_interaction_script"]["interaction_label"] == (
        "Warehouse interactions"
    )
    assert captured.err == ""

    rc = main(
        [
            "style-performance-arc-live-gui-interaction-script-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--interaction-label",
            "Warehouse interactions",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "Live GUI interaction script summary:" in captured.out
    assert "GUI control bindings:" in captured.out
    assert captured.err == ""

    rc = main(
        [
            "style-performance-arc-live-gui-interaction-script-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--interaction-label",
            " ",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "interaction_label" in captured.err

    rc = main(
        [
            "style-performance-arc-live-gui-interaction-script-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "Error:" in captured.err

    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main({[
        "style-performance-arc-live-gui-interaction-script-report",
        "--description",
        "Jeff Mills Oscar Mulero Birmingham pressure",
        "--capture-description",
        "captured warehouse take",
        "--rytm",
        str(rytm_path),
        "--analog-four",
        str(a4_path),
        "--interaction-label",
        "Warehouse interactions",
        "--json",
    ]!r})
assert exit_code == 0, exit_code
for module_name in {FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES!r}:
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


def test_live_gui_interaction_script_help_mentions_passive_contract():
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("style-performance-arc-live-gui-interaction-script-report")

    assert help_text.startswith(
        "RytmRandomizer passive CLI: " "style-performance-arc-live-gui-interaction-script-report"
    )
    assert "GUI interaction script" in help_text
    assert "no GUI launch" in help_text
    assert "no MIDI sending" in help_text
