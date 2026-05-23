"""Tests for passive live GUI capture review reporting."""

from __future__ import annotations

import json
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
    include_hash: bool = True,
    content_hash: str | None = None,
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
        derived_at="2026-05-23T02:15:00Z",
    )
    if content_hash is not None:
        return FeatureReport(
            **{
                **report.__dict__,
                "content_hash": content_hash,
            }
        )
    if not include_hash:
        return report
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def test_live_gui_capture_review_builds_go_decision_json_and_text(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_queue import (
        build_style_performance_arc_live_gui_capture_queue_report,
    )
    from rytm_randomizer.reports.live_gui_capture_review import (
        build_style_performance_arc_live_gui_capture_review_from_capture_queue,
        format_style_performance_arc_live_gui_capture_review_report,
        to_style_performance_arc_live_gui_capture_review_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    queue = build_style_performance_arc_live_gui_capture_queue_report(
        feature_report=_feature_report(),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=1,
        match_limit=2,
        take_count=2,
        queue_label="Warehouse capture",
        capture_prefix="warehouse",
    )

    report = build_style_performance_arc_live_gui_capture_review_from_capture_queue(
        queue,
        captured_feature_report=_feature_report(
            bpm=141.6,
            low_end_weight=0.70,
            spectral_brightness=0.48,
            texture_noise=0.60,
            energy_arc=(0.26, 0.54, 0.86),
        ),
        slot_key="capture-001",
        captured_source_kind="feature-report",
        captured_source_reference="captured take",
    )

    assert report.review_version == "live-gui-capture-review-v1"
    assert report.review_status == "operator-ready"
    assert report.review_label == "Warehouse capture review"
    assert report.capture_queue_id == queue.queue_id
    assert report.captured_slot_key == "capture-001"
    assert len(report.decisions) == 2
    assert report.decisions[0].decision == "go"
    assert report.decisions[0].status == "operator-ready"
    assert report.decisions[0].analyzer_job_key == queue.analyzer_jobs[0].key
    assert report.decisions[0].captured_feature_hash == report.captured_feature_hash
    assert {metric.status for metric in report.decisions[0].metrics} == {"pass"}
    target_bands = {
        band.key: band
        for band in queue.rehearsal_session.gui_readiness.analyzer_targets.target_bands
    }
    low_end_metric = next(
        metric for metric in report.decisions[0].metrics if metric.key == "low-end"
    )
    assert low_end_metric.label == target_bands["low-end"].label
    assert low_end_metric.target_value == target_bands["low-end"].target_window
    assert low_end_metric.operator_action == target_bands["low-end"].cue_action
    assert "operator-only" in report.decisions[0].operator_action
    assert report.decisions[1].decision == "hold"
    assert "No captured FeatureReport" in report.decisions[1].hold_reasons[0]
    assert any("go does not arm hardware" in item for item in report.checklist)
    assert any("no MIDI sending" in item for item in report.blocked_actions)

    lines = format_style_performance_arc_live_gui_capture_review_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI capture review"
    assert "Live GUI capture review summary:" in lines
    assert "Capture review decisions:" in lines
    assert "- Slot capture-001 / analyze-001: go / operator-ready" in lines
    assert "Metric review:" in text
    assert "Safety:" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_capture_review_json(report)
    review = payload["live_gui_capture_review"]
    assert review["review_id"] == report.review_id
    assert review["review_status"] == "operator-ready"
    assert review["decisions"][0]["decision"] == "go"
    assert review["decisions"][0]["metrics"][0]["status"] == "pass"
    assert payload["live_gui_capture_queue"]["queue_id"] == queue.queue_id
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_capture_review_repeats_when_metrics_are_near_misses(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_queue import (
        build_style_performance_arc_live_gui_capture_queue_report,
    )
    from rytm_randomizer.reports.live_gui_capture_review import (
        build_style_performance_arc_live_gui_capture_review_from_capture_queue,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    queue = build_style_performance_arc_live_gui_capture_queue_report(
        feature_report=_feature_report(),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        take_count=1,
    )

    report = build_style_performance_arc_live_gui_capture_review_from_capture_queue(
        queue,
        captured_feature_report=_feature_report(
            bpm=144.4,
            low_end_weight=0.52,
            spectral_brightness=0.63,
            texture_noise=0.78,
        ),
        slot_key="capture-001",
    )

    decision = report.decisions[0]
    assert report.review_status == "review-needed"
    assert decision.decision == "repeat"
    assert decision.status == "review-needed"
    assert any(metric.status == "warn" for metric in decision.metrics)
    assert not decision.hold_reasons
    assert "Repeat" in decision.operator_action


def test_live_gui_capture_review_holds_when_capture_evidence_is_not_trustworthy(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_queue import (
        build_style_performance_arc_live_gui_capture_queue_report,
    )
    from rytm_randomizer.reports.live_gui_capture_review import (
        build_style_performance_arc_live_gui_capture_review_from_capture_queue,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    queue = build_style_performance_arc_live_gui_capture_queue_report(
        feature_report=_feature_report(),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        take_count=1,
    )

    report = build_style_performance_arc_live_gui_capture_review_from_capture_queue(
        queue,
        captured_feature_report=_feature_report(bpm=0.0, energy_arc=(0.42,)),
        slot_key="capture-001",
    )

    decision = report.decisions[0]
    assert report.review_status == "blocked"
    assert decision.decision == "hold"
    assert decision.status == "blocked"
    assert any("tempo" in reason.lower() for reason in decision.hold_reasons)
    assert any("energy arc" in reason.lower() for reason in decision.hold_reasons)


def test_live_gui_capture_review_holds_low_confidence_capture(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.guardrails.schema import Confidence
    from rytm_randomizer.reports.live_gui_capture_queue import (
        build_style_performance_arc_live_gui_capture_queue_report,
    )
    from rytm_randomizer.reports.live_gui_capture_review import (
        build_style_performance_arc_live_gui_capture_review_from_capture_queue,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    queue = build_style_performance_arc_live_gui_capture_queue_report(
        feature_report=_feature_report(),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        take_count=1,
    )

    report = build_style_performance_arc_live_gui_capture_review_from_capture_queue(
        queue,
        captured_feature_report=_feature_report(confidence=Confidence.LOW),
        slot_key="capture-001",
    )

    decision = report.decisions[0]
    assert decision.decision == "hold"
    assert any("confidence is low" in reason for reason in decision.hold_reasons)


def test_live_gui_capture_review_holds_unqueued_slots_and_missing_jobs(tmp_path: Path):
    from dataclasses import replace

    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_queue import (
        build_style_performance_arc_live_gui_capture_queue_report,
    )
    from rytm_randomizer.reports.live_gui_capture_review import (
        build_style_performance_arc_live_gui_capture_review_from_capture_queue,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    queue = build_style_performance_arc_live_gui_capture_queue_report(
        feature_report=_feature_report(),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        take_count=2,
    )

    held_slot = replace(queue.capture_slots[0], status="held")
    held_queue = replace(queue, capture_slots=(held_slot, *queue.capture_slots[1:]))
    held_report = build_style_performance_arc_live_gui_capture_review_from_capture_queue(
        held_queue,
        captured_feature_report=_feature_report(),
        slot_key=held_slot.key,
    )
    assert held_report.decisions[0].decision == "hold"
    assert "Capture slot is held" in held_report.decisions[0].summary

    no_job_queue = replace(queue, analyzer_jobs=())
    no_job_report = build_style_performance_arc_live_gui_capture_review_from_capture_queue(
        no_job_queue,
        captured_feature_report=_feature_report(),
        slot_key="capture-001",
    )
    assert no_job_report.decisions[0].decision == "hold"
    assert no_job_report.decisions[0].analyzer_job_key == "missing-analyzer-job"
    assert "No analyzer job card" in no_job_report.decisions[0].summary


def test_live_gui_capture_review_handles_hash_and_metric_edge_cases(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_queue import (
        build_style_performance_arc_live_gui_capture_queue_report,
    )
    from rytm_randomizer.reports.live_gui_capture_review import (
        build_style_performance_arc_live_gui_capture_review_from_capture_queue,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    queue = build_style_performance_arc_live_gui_capture_queue_report(
        feature_report=_feature_report(),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        take_count=1,
    )

    report_with_computed_hash = (
        build_style_performance_arc_live_gui_capture_review_from_capture_queue(
            queue,
            captured_feature_report=_feature_report(include_hash=False),
            slot_key="capture-001",
        )
    )
    assert len(report_with_computed_hash.captured_feature_hash) == 64

    invalid_report = build_style_performance_arc_live_gui_capture_review_from_capture_queue(
        queue,
        captured_feature_report=_feature_report(
            bpm=147.5,
            low_end_weight=1.25,
            energy_arc=(0.86, 0.54, 0.24),
            content_hash="bad-hash",
        ),
        slot_key="capture-001",
    )
    decision = invalid_report.decisions[0]
    assert decision.decision == "hold"
    assert any("content hash" in reason for reason in decision.hold_reasons)
    assert any("Low-end weight" in reason for reason in decision.hold_reasons)
    assert any(
        metric.key == "energy-arc" and metric.status == "warn" for metric in decision.metrics
    )


def test_live_gui_capture_review_metric_helpers_cover_defensive_edges(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports import live_gui_capture_review as review
    from rytm_randomizer.reports.live_gui_capture_queue import (
        build_style_performance_arc_live_gui_capture_queue_report,
    )

    target = _feature_report()
    captured = _feature_report(
        tempo_stability=0.62,
        percussion_density=0.96,
        spectral_brightness=1.25,
        texture_noise=0.18,
        energy_arc=(float("nan"), 0.5),
    )
    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    queue = build_style_performance_arc_live_gui_capture_queue_report(
        feature_report=target,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        take_count=1,
    )
    target_bands = {
        band.key: band
        for band in queue.rehearsal_session.gui_readiness.analyzer_targets.target_bands
    }

    assert review._shape((float("nan"), 0.5)) == "unknown"
    assert (
        review._numeric_metric_review(
            target_band=target_bands["tempo-stability"],
            target_report=target,
            captured_report=captured,
            key="tempo-stability",
        ).status
        == "hold"
    )
    assert (
        review._numeric_metric_review(
            target_band=target_bands["percussion-density"],
            target_report=target,
            captured_report=captured,
            key="percussion-density",
        ).status
        == "hold"
    )
    assert (
        review._numeric_metric_review(
            target_band=target_bands["brightness"],
            target_report=target,
            captured_report=captured,
            key="brightness",
        ).status
        == "hold"
    )
    assert (
        review._numeric_metric_review(
            target_band=target_bands["noise"],
            target_report=target,
            captured_report=captured,
            key="noise",
        ).status
        == "hold"
    )
    with pytest.raises(ValueError, match="unsupported metric"):
        review._feature_value(target, "unknown")
    assert (
        review._metric_reviews(
            targets=queue.rehearsal_session.gui_readiness.analyzer_targets,
            captured_report=captured,
            metric_keys=("unknown",),
        )
        == ()
    )
    assert review._review_status(()) == "operator-ready"

    with pytest.raises(ValueError, match="slot must not be blank"):
        review.build_style_performance_arc_live_gui_capture_review_from_capture_queue(
            queue,
            captured_feature_report=captured,
            slot_key="   ",
        )


def test_live_gui_capture_review_builds_from_sources_and_validates_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_review import (
        build_style_performance_arc_live_gui_capture_review_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)

    def fake_capture_audio(path: Path):
        assert path == Path("capture.wav")
        return _feature_report()

    monkeypatch.setattr("rytm_randomizer.style_analysis.extract_from_audio", fake_capture_audio)

    report = build_style_performance_arc_live_gui_capture_review_report(
        feature_report=_feature_report(),
        capture_audio_path=Path("capture.wav"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        take_count=1,
    )
    assert report.captured_source_kind == "audio"
    assert report.decisions[0].decision == "go"

    def fake_library(path: Path):
        assert path in {Path("reference-library"), Path("capture-library")}
        return _feature_report()

    monkeypatch.setattr("rytm_randomizer.style_analysis.analyze_library", fake_library)

    library_report = build_style_performance_arc_live_gui_capture_review_report(
        library_path=Path("reference-library"),
        capture_library_path=Path("capture-library"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        take_count=1,
    )
    assert library_report.captured_source_kind == "library"
    assert "--library reference-library" in library_report.replay_commands[0]
    assert "--capture-library capture-library" in library_report.replay_commands[0]
    assert "--rytm" in library_report.replay_commands[0]
    assert str(rytm_path) in library_report.replay_commands[0]
    assert "--analog-four" in library_report.replay_commands[0]
    assert str(a4_path) in library_report.replay_commands[0]
    assert library_report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-capture-review-report "
    )
    cli_args = [
        "style-performance-arc-live-gui-capture-review-report",
        "--library",
        "reference-library",
        "--capture-library",
        "capture-library",
        "--rytm",
        str(rytm_path),
        "--analog-four",
        str(a4_path),
        "--matches",
        "1",
        "--takes",
        "1",
        "--slot",
        library_report.captured_slot_key,
        "--label",
        library_report.capture_queue.queue_label,
    ]
    from rytm_randomizer.cli import main

    assert main(cli_args) == 0

    with pytest.raises(ValueError, match="exactly one captured evidence source"):
        build_style_performance_arc_live_gui_capture_review_report(
            feature_report=_feature_report(),
            capture_description="one",
            capture_audio_path=Path("capture.wav"),
            rytm_sysex_path=rytm_path,
        )
    with pytest.raises(ValueError, match="exactly one captured evidence source"):
        build_style_performance_arc_live_gui_capture_review_report(
            feature_report=_feature_report(),
            rytm_sysex_path=rytm_path,
        )
    with pytest.raises(ValueError, match="capture description"):
        build_style_performance_arc_live_gui_capture_review_report(
            feature_report=_feature_report(),
            capture_description="   ",
            rytm_sysex_path=rytm_path,
        )
    with pytest.raises(ValueError, match="requires saved-kit source paths"):
        build_style_performance_arc_live_gui_capture_review_report(
            feature_report=_feature_report(),
            capture_feature_report=_feature_report(),
        )
    with pytest.raises(ValueError, match="unknown capture slot"):
        build_style_performance_arc_live_gui_capture_review_report(
            feature_report=_feature_report(),
            capture_feature_report=_feature_report(),
            rytm_sysex_path=rytm_path,
            slot_key="missing",
        )
    with pytest.raises(ValueError, match="exactly one reference source"):
        build_style_performance_arc_live_gui_capture_review_report(
            description="target",
            feature_report=_feature_report(),
            capture_feature_report=_feature_report(),
            rytm_sysex_path=rytm_path,
        )
    with pytest.raises(ValueError, match="description must include"):
        build_style_performance_arc_live_gui_capture_review_report(
            description="   ",
            capture_feature_report=_feature_report(),
            rytm_sysex_path=rytm_path,
        )
    with pytest.raises(ValueError, match="match_limit"):
        build_style_performance_arc_live_gui_capture_review_report(
            feature_report=_feature_report(),
            capture_feature_report=_feature_report(),
            rytm_sysex_path=rytm_path,
            match_limit=0,
        )
    with pytest.raises(ValueError, match="take_count"):
        build_style_performance_arc_live_gui_capture_review_report(
            feature_report=_feature_report(),
            capture_feature_report=_feature_report(),
            rytm_sysex_path=rytm_path,
            take_count=0,
        )


def test_live_gui_capture_review_cli_dispatches_json_text_errors_and_help(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.cli import main
    from rytm_randomizer.help_text import resolve_help_text

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    command = "style-performance-arc-live-gui-capture-review-report"

    assert (
        main(
            [
                command,
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
                "--capture-description",
                "Jeff Mills Oscar Mulero Birmingham pressure captured take",
                "--rytm",
                str(rytm_path),
                "--analog-four",
                str(a4_path),
                "--takes",
                "2",
                "--slot",
                "capture-001",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc live GUI capture review" in captured.out
    assert "Live GUI capture review summary:" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                command,
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
                "--capture-description",
                "Jeff Mills Oscar Mulero Birmingham pressure captured take",
                "--rytm",
                str(rytm_path),
                "--json",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["live_gui_capture_review"]["captured_slot_key"] == "capture-001"
    assert payload["live_gui_capture_queue"]["capture_slots"][0]["key"] == "capture-001"
    assert captured.err == ""

    assert (
        main(
            [
                command,
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
                "--rytm",
                str(rytm_path),
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires exactly one captured evidence source" in captured.err

    assert (
        main(
            [
                command,
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
                "--capture-description",
                "captured take",
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires saved-kit source paths" in captured.err

    help_text = resolve_help_text(command)
    assert "RytmRandomizer passive CLI: style-performance-arc-live-gui-capture-review-report" in (
        help_text
    )
    assert "go/repeat/hold" in help_text
    assert "no MIDI sending" in help_text


def test_live_gui_capture_review_parser_validates_options():
    from rytm_randomizer.reports.live_gui_capture_review import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_CAPTURE_REVIEW_CLI_COMMAND,
        _parse_cli_args,
    )

    args = _parse_cli_args(
        [
            "--audio",
            "reference.wav",
            "--capture-library",
            "capture-library",
            "--scope",
            "a4-only",
            "--rank",
            "2",
            "--total-minutes",
            "300",
            "--segment-minutes",
            "25",
            "--discovery-start",
            "5",
            "--discovery-end",
            "80",
            "--cue",
            "2",
            "--lookahead",
            "3",
            "--matches",
            "2",
            "--takes",
            "4",
            "--slot",
            "capture-004",
            "--label",
            "Flight review",
            "--capture-prefix",
            "Flight Take",
            "--json",
        ]
    )
    assert args["audio_path"] == Path("reference.wav")
    assert args["capture_library_path"] == Path("capture-library")
    assert args["scope"] == "analog-four-only"
    assert args["slot_key"] == "capture-004"
    assert args["json_output"] is True

    library_args = _parse_cli_args(
        [
            "--library",
            "reference-library",
            "--capture-audio",
            "capture.wav",
        ]
    )
    assert library_args["library_path"] == Path("reference-library")
    assert library_args["capture_audio_path"] == Path("capture.wav")

    bad_cases = (
        ([], "usage"),
        (["--description"], "usage"),
        (["--bogus"], "usage"),
        (["--description", "   ", "--capture-description", "take"], "description"),
        (["--description", "target", "--capture-description", "   "], "capture description"),
        (["--description", "target"], "captured evidence source"),
        (["--description", "target", "--capture-description", "take", "--slot", "   "], "slot"),
        (["--audio", "track.wav", "--capture-description", "take", "--takes", "0"], ">= 1"),
        (["--audio", "track.wav", "--capture-description", "take", "--matches", "0"], ">= 1"),
        (["--audio", "track.wav", "--capture-description", "take", "--lookahead", "-1"], ">= 0"),
        (
            ["--audio", "track.wav", "--capture-description", "take", "--lookahead", "later"],
            "integer",
        ),
        (["--audio", "track.wav", "--capture-description", "take", "--label", "   "], "label"),
        (
            [
                "--audio",
                "track.wav",
                "--capture-description",
                "take",
                "--capture-prefix",
                "   ",
            ],
            "capture_prefix",
        ),
    )
    for argv, message in bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_CAPTURE_REVIEW_CLI_COMMAND.error_formatter(
            ValueError("bad review")
        )
        == "Error: bad review"
    )
