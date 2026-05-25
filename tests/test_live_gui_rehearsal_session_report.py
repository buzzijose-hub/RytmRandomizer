"""Tests for passive live GUI rehearsal-session reporting."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _feature_report(
    *,
    bpm: float = 141.0,
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

    report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.MEDIUM,
        bpm=bpm,
        tempo_stability=tempo_stability,
        kick_density=kick_density,
        percussion_density=percussion_density,
        low_end_weight=low_end_weight,
        spectral_brightness=spectral_brightness,
        texture_noise=texture_noise,
        energy_arc=energy_arc,
        content_hash="",
        derived_at="2026-05-23T00:00:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def test_live_gui_rehearsal_session_builds_task_and_take_packet_from_description(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_rehearsal_session import (
        build_style_performance_arc_live_gui_rehearsal_session_report,
        format_style_performance_arc_live_gui_rehearsal_session_report,
        to_style_performance_arc_live_gui_rehearsal_session_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    report = build_style_performance_arc_live_gui_rehearsal_session_report(
        description="Jeff Mills Oscar Mulero Birmingham Regis Surgeon warehouse pressure",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=2,
        match_limit=3,
        take_count=2,
        session_label="Warehouse pressure rehearsal",
    )

    assert report.session_version == "live-gui-rehearsal-session-v1"
    assert len(report.session_id) == 16
    assert report.session_status == "ready"
    assert report.session_label == "Warehouse pressure rehearsal"
    assert report.selected_arc_key == report.gui_readiness.selected_arc_key
    assert report.scope == report.gui_readiness.scope
    assert {task.key for task in report.tasks} >= {
        "source-confirmation",
        "listen-only-capture",
        "target-compare",
        "warning-review",
        "operator-notes",
    }
    assert report.tasks[0].panel_key == "overview"
    assert report.tasks[1].stream_key == "feature-meters"
    assert len(report.takes) == 2
    assert report.takes[0].take_number == 1
    assert report.takes[0].cue_number == 1
    assert report.takes[0].compare_against
    assert any("no MIDI sending" in action for action in report.blocked_actions)
    assert any("listen-only" in item for item in report.checklist)
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-rehearsal-session-report"
    )
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-analyzer-readiness-report"
    )

    lines = format_style_performance_arc_live_gui_rehearsal_session_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI rehearsal session"
    assert "Live GUI rehearsal session summary:" in lines
    assert "Session task cards:" in lines
    assert "Rehearsal take cards:" in lines
    assert "Operator checklist:" in lines
    assert "Blocked active actions:" in lines
    assert "GUI rehearsal session packet only" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_rehearsal_session_json(report)
    session = payload["live_gui_rehearsal_session"]
    assert session["session_version"] == "live-gui-rehearsal-session-v1"
    assert session["session_id"] == report.session_id
    assert session["session_status"] == "ready"
    assert session["selected_arc_key"] == report.selected_arc_key
    assert session["tasks"][0]["key"] == report.tasks[0].key
    assert session["takes"][0]["take_number"] == 1
    assert payload["live_gui_analyzer_readiness"]["gui_bundle_id"] == (
        report.gui_readiness.gui_bundle_id
    )
    assert payload["live_analyzer_targets"]["target_packet_id"] == (
        report.gui_readiness.analyzer_targets.target_packet_id
    )
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_rehearsal_session_marks_warning_review_guarded_for_manual_tempo(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_analyzer_readiness import (
        build_style_performance_arc_live_gui_analyzer_readiness_report,
    )
    from rytm_randomizer.reports.live_gui_rehearsal_session import (
        build_style_performance_arc_live_gui_rehearsal_session_from_readiness,
        to_style_performance_arc_live_gui_rehearsal_session_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    readiness = build_style_performance_arc_live_gui_analyzer_readiness_report(
        feature_report=_feature_report(bpm=0.0, energy_arc=(0.5,)),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        lookahead_count=0,
        match_limit=1,
    )
    report = build_style_performance_arc_live_gui_rehearsal_session_from_readiness(
        readiness,
        take_count=3,
    )

    warning_task = next(task for task in report.tasks if task.key == "warning-review")
    assert report.session_status == "guarded"
    assert warning_task.status == "guarded"
    assert "manual tempo" in warning_task.hold_if
    assert len(report.takes) == 1
    assert "Tempo is unknown" in report.takes[0].hold_if

    payload = to_style_performance_arc_live_gui_rehearsal_session_json(report)
    warning_json = next(
        task
        for task in payload["live_gui_rehearsal_session"]["tasks"]
        if task["key"] == "warning-review"
    )
    assert warning_json["status"] == "guarded"


def test_live_gui_rehearsal_session_tracks_guarded_thresholds_and_red_cues(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_analyzer_targets import (
        StylePerformanceArcLiveAnalyzerWarningThreshold,
    )
    from rytm_randomizer.reports.live_gui_analyzer_readiness import (
        build_style_performance_arc_live_gui_analyzer_readiness_report,
    )
    from rytm_randomizer.reports.live_gui_rehearsal_session import (
        build_style_performance_arc_live_gui_rehearsal_session_from_readiness,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    readiness = build_style_performance_arc_live_gui_analyzer_readiness_report(
        feature_report=_feature_report(),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        lookahead_count=1,
        match_limit=1,
    )
    warning_threshold = StylePerformanceArcLiveAnalyzerWarningThreshold(
        key="meter-confidence",
        label="Meter confidence",
        threshold="< 60%",
        severity="hold",
        operator_action="Pause active comparison until the analyzer locks.",
    )
    red_checkpoint = replace(readiness.analyzer_targets.cue_checkpoints[0], status="red")
    guarded_targets = replace(
        readiness.analyzer_targets,
        cue_checkpoints=(red_checkpoint,),
        warning_thresholds=(warning_threshold,),
    )
    guarded_readiness = replace(readiness, analyzer_targets=guarded_targets)

    report = build_style_performance_arc_live_gui_rehearsal_session_from_readiness(
        guarded_readiness
    )

    assert report.session_status == "guarded"
    warning_task = next(task for task in report.tasks if task.key == "warning-review")
    assert warning_task.hold_if == "a hold-level analyzer threshold is active."
    assert report.takes[0].hold_if == "Cue status is red/hold/blocked."


def test_live_gui_rehearsal_session_preserves_upstream_nonready_gui_status(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_analyzer_readiness import (
        build_style_performance_arc_live_gui_analyzer_readiness_report,
    )
    from rytm_randomizer.reports.live_gui_rehearsal_session import (
        build_style_performance_arc_live_gui_rehearsal_session_from_readiness,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    readiness = build_style_performance_arc_live_gui_analyzer_readiness_report(
        description="Jeff Mills Oscar Mulero focused rehearsal",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        lookahead_count=1,
        match_limit=1,
    )
    staged_readiness = replace(readiness, gui_status="staged-for-review")

    report = build_style_performance_arc_live_gui_rehearsal_session_from_readiness(staged_readiness)

    assert report.session_status == "staged-for-review"


def test_live_gui_rehearsal_session_replays_audio_and_feature_report_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_rehearsal_session import (
        build_style_performance_arc_live_gui_rehearsal_session_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)

    def fake_audio_report(path: Path):
        assert path == Path("reference.wav")
        return _feature_report()

    monkeypatch.setattr(
        "rytm_randomizer.style_analysis.extract_from_audio",
        fake_audio_report,
    )

    audio_report = build_style_performance_arc_live_gui_rehearsal_session_report(
        audio_path=Path("reference.wav"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
    )
    assert "--audio reference.wav" in audio_report.replay_commands[0]

    feature_report = build_style_performance_arc_live_gui_rehearsal_session_report(
        feature_report=_feature_report(),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
    )
    assert "--description '<feature report target>'" in feature_report.replay_commands[0]


def test_live_gui_rehearsal_session_cli_dispatches_json_text_errors_and_help(
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
                "style-performance-arc-live-gui-rehearsal-session-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
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
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc live GUI rehearsal session" in captured.out
    assert "Live GUI rehearsal session summary:" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-rehearsal-session-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
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
    assert payload["live_gui_rehearsal_session"]["session_status"] == "ready"
    assert payload["live_gui_rehearsal_session"]["tasks"][0]["key"] == "source-confirmation"
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-rehearsal-session-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires saved-kit source paths" in captured.err

    help_text = resolve_help_text("style-performance-arc-live-gui-rehearsal-session-report")
    assert (
        "RytmRandomizer passive CLI: " "style-performance-arc-live-gui-rehearsal-session-report"
    ) in help_text
    assert "GUI rehearsal session packet" in help_text
    assert "no MIDI sending" in help_text


def test_live_gui_rehearsal_session_parser_validates_sources_takes_and_label(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_rehearsal_session import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_REHEARSAL_SESSION_CLI_COMMAND,
        _parse_cli_args,
        build_style_performance_arc_live_gui_rehearsal_session_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    args = _parse_cli_args(
        [
            "--audio",
            "track.wav",
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
            "--label",
            "Flight check",
            "--json",
        ]
    )
    assert args["audio_path"] == Path("track.wav")
    assert args["scope"] == "analog-four-only"
    assert args["match_limit"] == 2
    assert args["take_count"] == 4
    assert args["session_label"] == "Flight check"
    assert args["json_output"] is True
    library_args = _parse_cli_args(["--library", "folder"])
    assert library_args["library_path"] == Path("folder")

    bad_cases = (
        ([], "usage"),
        (["--description"], "usage"),
        (["--bogus"], "usage"),
        (["--description", "   "], "description must include reference evidence"),
        (["--audio", "track.wav", "--takes", "0"], ">= 1"),
        (["--audio", "track.wav", "--label", "   "], "label must not be blank"),
        (["--audio", "track.wav", "--matches", "0"], ">= 1"),
        (["--audio", "track.wav", "--lookahead", "-1"], ">= 0"),
        (["--audio", "track.wav", "--cue", "x"], "must be an integer"),
    )
    for argv, message in bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    with pytest.raises(ValueError, match="requires saved-kit source paths"):
        build_style_performance_arc_live_gui_rehearsal_session_report(
            feature_report=_feature_report(),
        )
    with pytest.raises(ValueError, match="description must include reference evidence"):
        build_style_performance_arc_live_gui_rehearsal_session_report(
            description="   ",
            rytm_sysex_path=rytm_path,
        )
    with pytest.raises(ValueError, match="requires exactly one reference source"):
        build_style_performance_arc_live_gui_rehearsal_session_report(
            description="Jeff Mills",
            audio_path=Path("track.wav"),
            rytm_sysex_path=Path("rytm.syx"),
        )
    with pytest.raises(ValueError, match="take_count must be >= 1"):
        build_style_performance_arc_live_gui_rehearsal_session_report(
            description="Jeff Mills",
            rytm_sysex_path=rytm_path,
            take_count=0,
        )
    with pytest.raises(ValueError, match="match_limit must be >= 1"):
        build_style_performance_arc_live_gui_rehearsal_session_report(
            description="Jeff Mills",
            rytm_sysex_path=rytm_path,
            match_limit=0,
        )
    with pytest.raises(ValueError, match="label must not be blank"):
        from rytm_randomizer.reports.live_gui_analyzer_readiness import (
            build_style_performance_arc_live_gui_analyzer_readiness_report,
        )
        from rytm_randomizer.reports.live_gui_rehearsal_session import (
            build_style_performance_arc_live_gui_rehearsal_session_from_readiness,
        )

        readiness = build_style_performance_arc_live_gui_analyzer_readiness_report(
            description="Jeff Mills",
            rytm_sysex_path=rytm_path,
            analog_four_sysex_path=a4_path,
            match_limit=1,
        )
        build_style_performance_arc_live_gui_rehearsal_session_from_readiness(
            readiness,
            session_label="   ",
        )
    with pytest.raises(ValueError, match="take_count must be >= 1"):
        from rytm_randomizer.reports.live_gui_analyzer_readiness import (
            build_style_performance_arc_live_gui_analyzer_readiness_report,
        )
        from rytm_randomizer.reports.live_gui_rehearsal_session import (
            build_style_performance_arc_live_gui_rehearsal_session_from_readiness,
        )

        readiness = build_style_performance_arc_live_gui_analyzer_readiness_report(
            description="Jeff Mills",
            rytm_sysex_path=rytm_path,
            analog_four_sysex_path=a4_path,
            match_limit=1,
        )
        build_style_performance_arc_live_gui_rehearsal_session_from_readiness(
            readiness,
            take_count=0,
        )
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_REHEARSAL_SESSION_CLI_COMMAND.error_formatter(
            ValueError("bad session")
        )
        == "Error: bad session"
    )
