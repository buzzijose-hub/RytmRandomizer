"""Tests for passive live GUI sidecar session reporting."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _feature_report(
    *,
    bpm: float = 141.0,
    confidence=None,
    tempo_stability: float = 0.88,
    kick_density: float = 0.78,
    percussion_density: float = 0.73,
    low_end_weight: float = 0.69,
    spectral_brightness: float = 0.47,
    texture_noise: float = 0.62,
    energy_arc: tuple[float, ...] = (0.24, 0.52, 0.84),
):
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    report_confidence = confidence or Confidence.MEDIUM
    report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=report_confidence,
        bpm=bpm,
        tempo_stability=tempo_stability,
        kick_density=kick_density,
        percussion_density=percussion_density,
        low_end_weight=low_end_weight,
        spectral_brightness=spectral_brightness,
        texture_noise=texture_noise,
        energy_arc=energy_arc,
        content_hash="",
        derived_at="2026-05-23T04:15:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def test_live_gui_sidecar_session_builds_single_gui_contract_from_capture_review(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_review import (
        build_style_performance_arc_live_gui_capture_review_report,
    )
    from rytm_randomizer.reports.live_gui_sidecar_session import (
        build_style_performance_arc_live_gui_sidecar_session_from_capture_review,
        format_style_performance_arc_live_gui_sidecar_session_report,
        to_style_performance_arc_live_gui_sidecar_session_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    capture_review = build_style_performance_arc_live_gui_capture_review_report(
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
        queue_label="Warehouse sidecar capture",
        capture_prefix="warehouse",
        slot_key="capture-001",
    )

    report = build_style_performance_arc_live_gui_sidecar_session_from_capture_review(
        capture_review,
        sidecar_label="Warehouse sidecar",
    )

    assert report.sidecar_version == "live-gui-sidecar-session-v1"
    assert len(report.sidecar_id) == 16
    assert report.sidecar_label == "Warehouse sidecar"
    assert report.sidecar_status == "ready"
    assert report.selected_arc_key == capture_review.selected_arc_key
    assert report.capture_review_id == capture_review.review_id
    assert report.current_cue_label.startswith("Cue")
    assert report.next_operator_action.startswith("Show GO")
    assert {panel.key for panel in report.panels} >= {
        "overview",
        "current-cue",
        "machines",
        "analyzer",
        "capture",
        "safety",
    }
    assert {row.key for row in report.analyzer_rows} >= {
        "bpm",
        "low-end",
        "texture",
        "energy-arc",
    }
    assert report.capture_rows[0].selected is True
    assert report.capture_rows[0].decision == "go"
    assert any(control.key == "arm-hardware" for control in report.disabled_controls)
    assert any("no MIDI sending" in action for action in report.blocked_actions)
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-sidecar-session-report"
    )
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-capture-review-report"
    )

    lines = format_style_performance_arc_live_gui_sidecar_session_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI sidecar session"
    assert "Live GUI sidecar session summary:" in lines
    assert "Sidecar panels:" in lines
    assert "Analyzer comparison rows:" in lines
    assert "Capture decision rows:" in lines
    assert "Disabled active controls:" in lines
    assert "GUI sidecar session packet only" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_sidecar_session_json(report)
    sidecar = payload["live_gui_sidecar_session"]
    assert sidecar["sidecar_version"] == "live-gui-sidecar-session-v1"
    assert sidecar["sidecar_id"] == report.sidecar_id
    assert sidecar["sidecar_status"] == "ready"
    assert sidecar["panels"][0]["key"] == report.panels[0].key
    assert sidecar["capture_rows"][0]["selected"] is True
    assert payload["live_gui_capture_review"]["review_id"] == capture_review.review_id
    assert payload["live_gui_capture_queue"]["queue_id"] == capture_review.capture_queue_id
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_sidecar_session_maps_repeat_and_hold_statuses(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_review import (
        build_style_performance_arc_live_gui_capture_review_report,
    )
    from rytm_randomizer.reports.live_gui_sidecar_session import (
        build_style_performance_arc_live_gui_sidecar_session_from_capture_review,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    repeat_review = build_style_performance_arc_live_gui_capture_review_report(
        feature_report=_feature_report(),
        capture_feature_report=_feature_report(
            bpm=144.4,
            low_end_weight=0.52,
            spectral_brightness=0.63,
            texture_noise=0.78,
        ),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        take_count=1,
    )
    repeat_report = build_style_performance_arc_live_gui_sidecar_session_from_capture_review(
        repeat_review
    )
    assert repeat_report.sidecar_status == "needs-repeat"
    assert repeat_report.next_operator_action.startswith("Repeat")

    hold_review = build_style_performance_arc_live_gui_capture_review_report(
        feature_report=_feature_report(),
        capture_feature_report=_feature_report(bpm=0.0, energy_arc=(0.42,)),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        take_count=1,
    )
    hold_report = build_style_performance_arc_live_gui_sidecar_session_from_capture_review(
        hold_review
    )
    assert hold_report.sidecar_status == "hold"
    assert hold_report.next_operator_action.startswith("Hold")
    assert any(row.status == "blocked" for row in hold_report.capture_rows)


def test_live_gui_sidecar_session_covers_replay_and_fallback_edges(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_review import (
        StylePerformanceArcLiveGuiCaptureMetricReview,
        build_style_performance_arc_live_gui_capture_review_report,
    )
    from rytm_randomizer.reports.live_gui_sidecar_session import (
        build_style_performance_arc_live_gui_sidecar_session_from_capture_review,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    capture_review = build_style_performance_arc_live_gui_capture_review_report(
        feature_report=_feature_report(),
        capture_feature_report=_feature_report(texture_noise=0.66),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        take_count=1,
    )

    handoff = (
        capture_review.capture_queue.rehearsal_session.gui_readiness.analyzer_targets.analyzer_handoff
    )
    targets = capture_review.capture_queue.rehearsal_session.gui_readiness.analyzer_targets
    readiness = capture_review.capture_queue.rehearsal_session.gui_readiness
    session = capture_review.capture_queue.rehearsal_session
    queue = capture_review.capture_queue
    audio_review = replace(
        capture_review,
        capture_queue=replace(
            queue,
            rehearsal_session=replace(
                session,
                gui_readiness=replace(
                    readiness,
                    analyzer_targets=replace(
                        targets,
                        analyzer_handoff=replace(
                            handoff,
                            source_kind="audio",
                            source_reference="reference.wav",
                        ),
                    ),
                ),
            ),
        ),
        captured_source_kind="audio",
        captured_source_reference="capture.wav",
        analog_four_sysex_path=None,
    )
    audio_sidecar = build_style_performance_arc_live_gui_sidecar_session_from_capture_review(
        audio_review
    )
    assert "--audio reference.wav" in audio_sidecar.replay_commands[0]
    assert "--capture-audio capture.wav" in audio_sidecar.replay_commands[0]
    assert "--analog-four" not in audio_sidecar.replay_commands[0]

    library_review = replace(
        audio_review,
        capture_queue=replace(
            audio_review.capture_queue,
            rehearsal_session=replace(
                audio_review.capture_queue.rehearsal_session,
                gui_readiness=replace(
                    audio_review.capture_queue.rehearsal_session.gui_readiness,
                    analyzer_targets=replace(
                        targets,
                        analyzer_handoff=replace(
                            handoff,
                            source_kind="library",
                            source_reference="library",
                        ),
                    ),
                ),
            ),
        ),
        captured_source_kind="library",
        captured_source_reference="captures",
        rytm_sysex_path=None,
        analog_four_sysex_path=a4_path,
    )
    library_sidecar = build_style_performance_arc_live_gui_sidecar_session_from_capture_review(
        library_review
    )
    assert "--library library" in library_sidecar.replay_commands[0]
    assert "--capture-library captures" in library_sidecar.replay_commands[0]
    assert "--rytm" not in library_sidecar.replay_commands[0]

    unknown_review = replace(
        capture_review,
        capture_queue=replace(
            queue,
            rehearsal_session=replace(
                session,
                takes=(),
                gui_readiness=replace(
                    readiness,
                    analyzer_targets=replace(
                        targets,
                        analyzer_handoff=replace(
                            handoff,
                            source_kind="feature-report",
                            source_reference=None,
                        ),
                        cue_checkpoints=(),
                    ),
                ),
            ),
        ),
        captured_slot_key="missing-slot",
        captured_source_kind="feature-report",
        captured_source_reference=None,
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
    )
    unknown_sidecar = build_style_performance_arc_live_gui_sidecar_session_from_capture_review(
        unknown_review
    )
    assert unknown_sidecar.current_cue_label == "Cue 1"
    assert unknown_sidecar.next_cue_labels == ("No lookahead cue queued",)
    assert "--description '<feature report target>'" in unknown_sidecar.replay_commands[0]
    assert "--capture-description '<feature report capture>'" in (
        unknown_sidecar.replay_commands[0]
    )

    checkpoint_only_review = replace(
        capture_review,
        capture_queue=replace(
            queue,
            rehearsal_session=replace(
                session,
                takes=(),
                gui_readiness=replace(
                    readiness,
                    analyzer_targets=replace(
                        targets,
                        target_bands=tuple(
                            band for band in targets.target_bands if band.key != "noise"
                        ),
                    ),
                ),
            ),
        ),
    )
    checkpoint_sidecar = build_style_performance_arc_live_gui_sidecar_session_from_capture_review(
        checkpoint_only_review
    )
    assert checkpoint_sidecar.current_cue_label.startswith("Cue")
    assert "texture" not in {row.key for row in checkpoint_sidecar.analyzer_rows}

    texture_metric = StylePerformanceArcLiveGuiCaptureMetricReview(
        key="noise",
        label="Texture noise",
        target_value="inside 40%-70%",
        captured_value="66%",
        delta="+4%",
        status="pass",
        operator_action="Keep grit present but controlled.",
    )
    texture_review = replace(
        capture_review,
        decisions=(
            replace(
                capture_review.decisions[0],
                metrics=(texture_metric,),
            ),
        ),
    )
    texture_sidecar = build_style_performance_arc_live_gui_sidecar_session_from_capture_review(
        texture_review
    )
    assert [row.key for row in texture_sidecar.analyzer_rows] == ["texture"]

    with pytest.raises(ValueError, match="sidecar_label"):
        build_style_performance_arc_live_gui_sidecar_session_from_capture_review(
            capture_review,
            sidecar_label="   ",
        )


def test_live_gui_sidecar_session_parser_and_builder_edges(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_sidecar_session import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_SIDECAR_SESSION_CLI_COMMAND,
        _parse_cli_args,
        build_style_performance_arc_live_gui_sidecar_session_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = _parse_cli_args(
        [
            "--audio",
            "reference.wav",
            "--capture-audio",
            "capture.wav",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--scope",
            "a4-only",
            "--rank",
            "2",
            "--total-minutes",
            "90",
            "--segment-minutes",
            "15",
            "--discovery-start",
            "10",
            "--discovery-end",
            "80",
            "--cue",
            "2",
            "--lookahead",
            "0",
            "--matches",
            "2",
            "--takes",
            "3",
            "--slot",
            "capture-002",
            "--label",
            "Warehouse queue",
            "--capture-prefix",
            "warehouse",
            "--sidecar-label",
            "Warehouse sidecar",
            "--json",
        ]
    )
    assert parsed["audio_path"] == Path("reference.wav")
    assert parsed["capture_audio_path"] == Path("capture.wav")
    assert parsed["scope"] == "analog-four-only"
    assert parsed["selection_rank"] == 2
    assert parsed["json_output"] is True

    library_parsed = _parse_cli_args(
        [
            "--library",
            "references",
            "--capture-library",
            "captures",
            "--rytm",
            str(rytm_path),
        ]
    )
    assert library_parsed["library_path"] == Path("references")
    assert library_parsed["capture_library_path"] == Path("captures")

    bad_cases = (
        (["--bogus"], "usage"),
        (["--description"], "usage"),
        (["--description", "   ", "--capture-description", "take"], "reference"),
        (["--description", "ref", "--capture-description", "   "], "measured"),
        (["--description", "ref", "--capture-description", "take", "--rank", "0"], ">= 1"),
        (
            ["--description", "ref", "--capture-description", "take", "--lookahead", "-1"],
            ">= 0",
        ),
        (
            ["--description", "ref", "--capture-description", "take", "--matches", "many"],
            "integer",
        ),
        (
            ["--description", "ref", "--capture-description", "take", "--slot", "   "],
            "slot",
        ),
        (
            ["--description", "ref", "--capture-description", "take", "--label", "   "],
            "label",
        ),
        (
            [
                "--description",
                "ref",
                "--capture-description",
                "take",
                "--capture-prefix",
                "   ",
            ],
            "capture_prefix",
        ),
        (
            [
                "--description",
                "ref",
                "--capture-description",
                "take",
                "--sidecar-label",
                "   ",
            ],
            "sidecar_label",
        ),
        (["--description", "ref"], "captured evidence"),
        (["--capture-description", "take"], "usage"),
    )
    for argv, message in bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    with pytest.raises(ValueError, match="reference source"):
        build_style_performance_arc_live_gui_sidecar_session_report(
            capture_feature_report=_feature_report(),
            rytm_sysex_path=rytm_path,
        )
    with pytest.raises(ValueError, match="reference evidence"):
        build_style_performance_arc_live_gui_sidecar_session_report(
            description="   ",
            capture_feature_report=_feature_report(),
            rytm_sysex_path=rytm_path,
        )
    with pytest.raises(ValueError, match="captured evidence"):
        build_style_performance_arc_live_gui_sidecar_session_report(
            feature_report=_feature_report(),
            rytm_sysex_path=rytm_path,
        )

    assert (
        main(
            [
                "style-performance-arc-live-gui-sidecar-session-report",
                "--description",
                "reference",
                "--capture-description",
                "take",
            ]
        )
        == 2
    )
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_SIDECAR_SESSION_CLI_COMMAND.error_formatter(
            ValueError("bad sidecar")
        )
        == "Error: bad sidecar"
    )


def test_live_gui_sidecar_session_cli_dispatches_json_text_errors_and_help(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.cli import main
    from rytm_randomizer.help_text import resolve_help_text

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)

    assert (
        main(
            [
                "style-performance-arc-live-gui-sidecar-session-report",
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
                "1",
                "--takes",
                "2",
                "--capture-prefix",
                "warehouse",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc live GUI sidecar session" in (captured.out)
    assert "Live GUI sidecar session summary:" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-sidecar-session-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
                "--capture-description",
                "captured warehouse take with tight low end and building pressure",
                "--rytm",
                str(rytm_path),
                "--analog-four",
                str(a4_path),
                "--json",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["live_gui_sidecar_session"]["sidecar_status"] in {
        "hold",
        "needs-repeat",
        "ready",
    }
    assert payload["live_gui_sidecar_session"]["disabled_controls"][0]["enabled"] is False
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-sidecar-session-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires exactly one captured evidence source" in captured.err

    help_text = resolve_help_text("style-performance-arc-live-gui-sidecar-session-report")
    assert (
        "RytmRandomizer passive CLI: " "style-performance-arc-live-gui-sidecar-session-report"
    ) in help_text
    assert "single sidecar-ready GUI state" in help_text
    assert "no MIDI sending" in help_text
