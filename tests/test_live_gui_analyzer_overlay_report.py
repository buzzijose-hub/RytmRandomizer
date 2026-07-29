"""Tests for passive live GUI analyzer-overlay reporting."""

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
        derived_at="2026-05-23T06:30:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _render_tree(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_analyzer_overlay import (
        build_style_performance_arc_live_gui_render_tree_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_render_tree_report(
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
        queue_label="Warehouse overlay queue",
        capture_prefix="warehouse",
        slot_key="capture-001",
        sidecar_label="Warehouse sidecar",
        screen_label="Warehouse screen",
        render_target="desktop-sidecar",
        density="standard",
    )


def test_live_gui_analyzer_overlay_builds_meter_contract_from_render_tree(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_gui_analyzer_overlay import (
        build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree,
        format_style_performance_arc_live_gui_analyzer_overlay_report,
        to_style_performance_arc_live_gui_analyzer_overlay_json,
    )

    render_tree = _render_tree(tmp_path)
    report = build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree(
        render_tree,
        overlay_label="Warehouse analyzer overlay",
    )

    assert report.overlay_version == "live-gui-analyzer-overlay-v1"
    assert len(report.overlay_id) == 16
    assert report.render_tree_id == render_tree.render_tree_id
    assert report.screen_contract_id == render_tree.screen_contract_id
    assert report.capture_review_id == render_tree.screen_contract.sidecar_session.capture_review_id
    assert report.overlay_status == "ready"
    assert report.overlay_label == "Warehouse analyzer overlay"
    assert report.selected_capture_badge.slot_key == "capture-001"
    assert report.selected_capture_badge.decision == "go"
    assert {meter.key for meter in report.meter_widgets} >= {
        "meter-bpm",
        "meter-low-end",
        "meter-energy-arc",
    }
    assert all(meter.render_node_key.startswith("node-analyzer-") for meter in report.meter_widgets)
    assert all(marker.band in {"pass", "warn", "hold"} for marker in report.threshold_markers)
    assert len(report.threshold_markers) == len(report.meter_widgets) * 3
    assert {annotation.annotation_type for annotation in report.node_annotations} >= {
        "meter",
        "capture-badge",
        "disabled-control",
    }
    assert "no GUI-triggered MIDI sends" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-analyzer-overlay-report"
    )
    assert "style-performance-arc-live-gui-render-tree-report" not in report.replay_commands[0]
    assert "--render-target desktop-sidecar" in report.replay_commands[0]
    assert "--density standard" in report.replay_commands[0]
    assert "--overlay-label 'Warehouse analyzer overlay'" in report.replay_commands[0]
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-render-tree-report"
    )

    lines = format_style_performance_arc_live_gui_analyzer_overlay_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI analyzer overlay"
    assert "Live GUI analyzer overlay summary:" in lines
    assert "Meter widgets:" in lines
    assert "Threshold markers:" in lines
    assert "Node annotations:" in lines
    assert "Passive analyzer overlay only" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_analyzer_overlay_json(report)
    overlay = payload["live_gui_analyzer_overlay"]
    assert overlay["overlay_version"] == "live-gui-analyzer-overlay-v1"
    assert overlay["overlay_id"] == report.overlay_id
    assert overlay["render_tree_id"] == render_tree.render_tree_id
    assert overlay["meter_widgets"][0]["key"].startswith("meter-")
    assert overlay["selected_capture_badge"]["decision"] == "go"
    assert payload["live_gui_render_tree"]["render_tree_id"] == render_tree.render_tree_id
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_analyzer_overlay_maps_review_and_fallback_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_analyzer_overlay import (
        build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree,
    )
    from rytm_randomizer.reports.live_gui_capture_review import (
        StylePerformanceArcLiveGuiCaptureMetricReview,
    )

    render_tree = _render_tree(tmp_path)
    held_tree = replace(render_tree, render_status="hold")
    held_report = build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree(held_tree)
    assert held_report.overlay_status == "blocked"
    assert any("hold" in action for action in held_report.blocked_actions)

    fallback_tree = replace(
        render_tree, replay_commands=("python -m rytm_randomizer.cli upstream",)
    )
    fallback_report = build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree(
        fallback_tree
    )
    assert fallback_report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-analyzer-overlay-report"
    )

    empty_replay_report = build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree(
        replace(render_tree, replay_commands=())
    )
    assert empty_replay_report.replay_commands == (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-analyzer-overlay-report "
        "--overlay-label 'Live GUI analyzer overlay'",
    )

    capture_review = render_tree.screen_contract.sidecar_session.capture_review
    first_decision = capture_review.decisions[0]
    repeat_decision = replace(
        first_decision,
        decision="repeat",
        status="review-needed",
    )
    noise_metric = replace(
        first_decision.metrics[0],
        key="noise",
        label="Texture noise",
    )
    unknown_metric = StylePerformanceArcLiveGuiCaptureMetricReview(
        key="unknown",
        label="Unknown metric",
        target_value="target",
        captured_value="captured",
        delta="unknown",
        status="warn",
        operator_action="Show unknown metric fallback.",
    )
    noisy_decision = replace(
        repeat_decision,
        metrics=(noise_metric, unknown_metric),
    )
    noisy_review = replace(capture_review, decisions=(noisy_decision,))
    noisy_sidecar = replace(
        render_tree.screen_contract.sidecar_session,
        capture_review=noisy_review,
    )
    noisy_screen = replace(render_tree.screen_contract, sidecar_session=noisy_sidecar)
    noisy_tree = replace(render_tree, screen_contract=noisy_screen)
    noisy_report = build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree(
        noisy_tree
    )
    meter_by_key = {meter.key: meter for meter in noisy_report.meter_widgets}
    assert noisy_report.overlay_status == "review-needed"
    assert meter_by_key["meter-texture"].metric_key == "noise"
    assert meter_by_key["meter-unknown"].render_node_key == "region-analyzer-table"

    fallback_review = replace(capture_review, captured_slot_key="missing-slot")
    fallback_sidecar = replace(
        render_tree.screen_contract.sidecar_session,
        capture_review=fallback_review,
    )
    fallback_screen = replace(render_tree.screen_contract, sidecar_session=fallback_sidecar)
    selected_fallback_report = (
        build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree(
            replace(render_tree, screen_contract=fallback_screen)
        )
    )
    assert selected_fallback_report.selected_capture_badge.slot_key == first_decision.slot_key

    missing_slot_decision = replace(first_decision, slot_key="missing-slot")
    missing_slot_review = replace(
        capture_review,
        captured_slot_key="missing-slot",
        decisions=(missing_slot_decision,),
    )
    missing_slot_sidecar = replace(
        render_tree.screen_contract.sidecar_session,
        capture_review=missing_slot_review,
    )
    missing_slot_screen = replace(
        render_tree.screen_contract,
        sidecar_session=missing_slot_sidecar,
    )
    missing_slot_report = build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree(
        replace(render_tree, screen_contract=missing_slot_screen)
    )
    capture_annotation = next(
        annotation
        for annotation in missing_slot_report.node_annotations
        if annotation.annotation_type == "capture-badge"
    )
    assert capture_annotation.render_node_key == "region-capture-table"

    with pytest.raises(ValueError, match="overlay_label"):
        build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree(
            render_tree,
            overlay_label=" ",
        )


def test_live_gui_analyzer_overlay_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_analyzer_overlay import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_OVERLAY_CLI_COMMAND,
        build_style_performance_arc_live_gui_analyzer_overlay_report,
        to_style_performance_arc_live_gui_analyzer_overlay_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_OVERLAY_CLI_COMMAND.args_parser(
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
            "--json",
        ]
    )
    assert parsed["overlay_label"] == "Warehouse overlay"
    assert parsed["json_output"] is True

    report = build_style_performance_arc_live_gui_analyzer_overlay_report(
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
    )
    payload = to_style_performance_arc_live_gui_analyzer_overlay_json(report)
    assert payload["live_gui_analyzer_overlay"]["overlay_status"] in {
        "ready",
        "review-needed",
        "blocked",
    }

    with pytest.raises(ValueError, match="overlay_label"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_OVERLAY_CLI_COMMAND.args_parser(
            [
                "--description",
                "x",
                "--capture-description",
                "y",
                "--overlay-label",
                " ",
            ]
        )
    with pytest.raises(ValueError, match="usage"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_OVERLAY_CLI_COMMAND.args_parser(["--overlay-label"])
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_OVERLAY_CLI_COMMAND.error_formatter(ValueError("x"))
        == "Error: x"
    )
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_OVERLAY_CLI_COMMAND.handler(
            **{**parsed, "overlay_label": " "}
        )
        == 2
    )
    captured = capsys.readouterr()
    assert "Error: overlay_label must not be blank" in captured.err

    assert (
        main(
            [
                "style-performance-arc-live-gui-analyzer-overlay-report",
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
                "--json",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["live_gui_analyzer_overlay"]["overlay_label"] == "Warehouse overlay"
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-analyzer-overlay-report",
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
    assert "RytmRandomizer passive style performance arc live GUI analyzer overlay" in captured.out
    assert "Live GUI analyzer overlay summary:" in captured.out
    assert captured.err == ""


def test_live_gui_analyzer_overlay_help_mentions_passive_contract():
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("style-performance-arc-live-gui-analyzer-overlay-report")
    assert (
        "RytmRandomizer passive CLI: " "style-performance-arc-live-gui-analyzer-overlay-report"
    ) in help_text
    assert "analyzer overlay" in help_text
    assert "no MIDI sending" in help_text
