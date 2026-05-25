"""Tests for passive live GUI analyzer-frame reporting."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


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
        derived_at="2026-05-23T10:15:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _overlay(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_analyzer_overlay import (
        build_style_performance_arc_live_gui_analyzer_overlay_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_analyzer_overlay_report(
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
        queue_label="Warehouse frame queue",
        capture_prefix="warehouse",
        slot_key="capture-001",
        sidecar_label="Warehouse sidecar",
        screen_label="Warehouse screen",
        render_target="desktop-sidecar",
        density="standard",
        overlay_label="Warehouse overlay",
    )


def test_live_gui_analyzer_frame_builds_ordered_frame_contract_from_overlay(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_gui_analyzer_frame import (
        build_style_performance_arc_live_gui_analyzer_frame_from_overlay,
        format_style_performance_arc_live_gui_analyzer_frame_report,
        to_style_performance_arc_live_gui_analyzer_frame_json,
    )

    overlay = _overlay(tmp_path)
    report = build_style_performance_arc_live_gui_analyzer_frame_from_overlay(
        overlay,
        frame_label="Warehouse analyzer frame",
    )

    assert report.frame_version == "live-gui-analyzer-frame-v1"
    assert len(report.frame_id) == 16
    assert report.overlay_id == overlay.overlay_id
    assert report.render_tree_id == overlay.render_tree_id
    assert report.screen_contract_id == overlay.screen_contract_id
    assert report.capture_review_id == overlay.capture_review_id
    assert report.frame_status == "ready"
    assert report.frame_label == "Warehouse analyzer frame"
    assert [event.order for event in report.frame_events] == list(range(len(report.frame_events)))
    assert report.frame_events[0].event_type == "mount-overlay"
    assert report.frame_events[0].target_key == overlay.overlay_id
    assert {event.event_type for event in report.frame_events} >= {
        "mount-overlay",
        "paint-meter",
        "paint-threshold-marker",
        "paint-capture-badge",
        "lock-disabled-control",
    }
    assert {assertion.assertion_type for assertion in report.visual_assertions} >= {
        "meter-status",
        "threshold-marker-state",
        "capture-badge-state",
        "disabled-control-lock",
    }
    assert "no GUI frame rendering" in report.blocked_actions
    assert "no GUI-triggered MIDI sends" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-analyzer-frame-report"
    )
    assert "style-performance-arc-live-gui-analyzer-overlay-report" not in (
        report.replay_commands[0]
    )
    assert "--overlay-label 'Warehouse overlay'" in report.replay_commands[0]
    assert "--frame-label 'Warehouse analyzer frame'" in report.replay_commands[0]
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-analyzer-overlay-report"
    )

    lines = format_style_performance_arc_live_gui_analyzer_frame_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI analyzer frame"
    assert "Live GUI analyzer frame summary:" in lines
    assert "Frame events:" in lines
    assert "Visual assertions:" in lines
    assert "Passive analyzer frame only" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_analyzer_frame_json(report)
    frame = payload["live_gui_analyzer_frame"]
    assert frame["frame_version"] == "live-gui-analyzer-frame-v1"
    assert frame["frame_id"] == report.frame_id
    assert frame["overlay_id"] == overlay.overlay_id
    assert frame["frame_events"][0]["event_type"] == "mount-overlay"
    assert frame["visual_assertions"][0]["assertion_type"]
    assert payload["live_gui_analyzer_overlay"]["overlay_id"] == overlay.overlay_id
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_analyzer_frame_maps_status_and_replay_fallback_edges(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_gui_analyzer_frame import (
        build_style_performance_arc_live_gui_analyzer_frame_from_overlay,
    )

    overlay = _overlay(tmp_path)
    blocked_overlay = replace(overlay, overlay_status="blocked")
    blocked_frame = build_style_performance_arc_live_gui_analyzer_frame_from_overlay(
        blocked_overlay
    )
    assert blocked_frame.frame_status == "blocked"
    assert "hold overlay before frame render" in blocked_frame.blocked_actions

    review_overlay = replace(overlay, overlay_status="review-needed")
    review_frame = build_style_performance_arc_live_gui_analyzer_frame_from_overlay(review_overlay)
    assert review_frame.frame_status == "review-needed"

    fallback_overlay = replace(
        overlay,
        replay_commands=("python -m rytm_randomizer.cli upstream",),
    )
    fallback_frame = build_style_performance_arc_live_gui_analyzer_frame_from_overlay(
        fallback_overlay
    )
    assert fallback_frame.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-analyzer-frame-report"
    )

    empty_replay_frame = build_style_performance_arc_live_gui_analyzer_frame_from_overlay(
        replace(overlay, replay_commands=())
    )
    assert empty_replay_frame.replay_commands == (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-analyzer-frame-report "
        "--frame-label 'Live GUI analyzer frame'",
    )

    with pytest.raises(ValueError, match="frame_label"):
        build_style_performance_arc_live_gui_analyzer_frame_from_overlay(
            overlay,
            frame_label=" ",
        )


def test_live_gui_analyzer_frame_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_analyzer_frame import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_FRAME_CLI_COMMAND,
        build_style_performance_arc_live_gui_analyzer_frame_report,
        to_style_performance_arc_live_gui_analyzer_frame_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_FRAME_CLI_COMMAND.args_parser(
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
            "1",
            "--lookahead",
            "1",
            "--matches",
            "2",
            "--takes",
            "1",
            "--slot",
            "capture-001",
            "--label",
            "Warehouse queue",
            "--capture-prefix",
            "warehouse",
            "--sidecar-label",
            "Warehouse sidecar",
            "--screen-label",
            "Warehouse screen",
            "--layout",
            "operator-cockpit",
            "--viewport",
            "desktop",
            "--render-target",
            "desktop-sidecar",
            "--density",
            "standard",
            "--overlay-label",
            "Warehouse overlay",
            "--frame-label",
            "Warehouse frame",
            "--json",
        ]
    )
    assert parsed["frame_label"] == "Warehouse frame"
    assert parsed["overlay_label"] == "Warehouse overlay"
    assert parsed["json_output"] is True

    report = build_style_performance_arc_live_gui_analyzer_frame_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        capture_description="captured warehouse take",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=1,
        match_limit=2,
        take_count=1,
        slot_key="capture-001",
        queue_label="Warehouse queue",
        capture_prefix="warehouse",
        sidecar_label="Warehouse sidecar",
        screen_label="Warehouse screen",
        layout_key="operator-cockpit",
        viewport="desktop",
        render_target="desktop-sidecar",
        density="standard",
        overlay_label="Warehouse overlay",
        frame_label="Warehouse frame",
    )
    payload = to_style_performance_arc_live_gui_analyzer_frame_json(report)
    assert payload["live_gui_analyzer_frame"]["frame_status"] in {
        "ready",
        "review-needed",
        "blocked",
    }

    with pytest.raises(ValueError, match="frame_label"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_FRAME_CLI_COMMAND.args_parser(
            [
                "--description",
                "x",
                "--capture-description",
                "y",
                "--frame-label",
                " ",
            ]
        )
    with pytest.raises(ValueError, match="usage"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_FRAME_CLI_COMMAND.args_parser(["--frame-label"])
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_FRAME_CLI_COMMAND.error_formatter(ValueError("x"))
        == "Error: x"
    )
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_FRAME_CLI_COMMAND.handler(
            **{**parsed, "frame_label": " "}
        )
        == 2
    )
    captured = capsys.readouterr()
    assert "Error: frame_label must not be blank" in captured.err

    assert (
        main(
            [
                "style-performance-arc-live-gui-analyzer-frame-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
                "--capture-description",
                "captured warehouse take",
                "--rytm",
                str(rytm_path),
                "--analog-four",
                str(a4_path),
                "--overlay-label",
                "Warehouse overlay",
                "--frame-label",
                "Warehouse frame",
                "--json",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["live_gui_analyzer_frame"]["frame_label"] == "Warehouse frame"
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-analyzer-frame-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
                "--capture-description",
                "captured warehouse take",
                "--rytm",
                str(rytm_path),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc live GUI analyzer frame" in captured.out
    assert "Live GUI analyzer frame summary:" in captured.out
    assert captured.err == ""


def test_live_gui_analyzer_frame_help_mentions_passive_contract():
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("style-performance-arc-live-gui-analyzer-frame-report")
    assert (
        "RytmRandomizer passive CLI: " "style-performance-arc-live-gui-analyzer-frame-report"
    ) in help_text
    assert "analyzer frame" in help_text
    assert "no MIDI sending" in help_text
