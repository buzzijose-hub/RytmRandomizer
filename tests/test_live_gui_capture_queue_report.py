"""Tests for passive live GUI capture queue reporting."""

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
        derived_at="2026-05-23T01:15:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def test_live_gui_capture_queue_builds_slots_jobs_and_json_from_description(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_queue import (
        build_style_performance_arc_live_gui_capture_queue_report,
        format_style_performance_arc_live_gui_capture_queue_report,
        to_style_performance_arc_live_gui_capture_queue_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    report = build_style_performance_arc_live_gui_capture_queue_report(
        description="Jeff Mills Oscar Mulero Birmingham Regis Surgeon warehouse pressure",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=2,
        match_limit=3,
        take_count=2,
        queue_label="Warehouse pressure capture",
        capture_prefix="warehouse",
    )

    assert report.queue_version == "live-gui-capture-queue-v1"
    assert len(report.queue_id) == 16
    assert report.queue_status == "queued"
    assert report.queue_label == "Warehouse pressure capture"
    assert report.selected_arc_key == report.rehearsal_session.selected_arc_key
    assert report.scope == report.rehearsal_session.scope
    assert report.capture_mode == "listen-only audio capture"
    assert len(report.capture_slots) == 2
    assert report.capture_slots[0].key == "capture-001"
    assert report.capture_slots[0].capture_label == "warehouse-take-001"
    assert report.capture_slots[0].suggested_filename.endswith("_take_001.wav")
    assert report.capture_slots[0].source_stream == "feature-meters"
    assert report.capture_slots[0].compare_against
    assert len(report.analyzer_jobs) == 2
    assert report.analyzer_jobs[0].input_slot_key == report.capture_slots[0].key
    assert report.analyzer_jobs[0].target_packet_id == (
        report.rehearsal_session.gui_readiness.analyzer_targets.target_packet_id
    )
    assert report.analyzer_jobs[0].comparison_profile == report.selected_arc_key
    assert any("Capture every take as listen-only audio" in item for item in report.checklist)
    assert any("no MIDI sending" in action for action in report.blocked_actions)
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-capture-queue-report"
    )
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-rehearsal-session-report"
    )

    lines = format_style_performance_arc_live_gui_capture_queue_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI capture queue"
    assert "Live GUI capture queue summary:" in lines
    assert "Capture slots:" in lines
    assert "Analyzer job cards:" in lines
    assert "Operator capture checklist:" in lines
    assert "Blocked active actions:" in lines
    assert "GUI/audio analyzer capture queue only" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_capture_queue_json(report)
    queue = payload["live_gui_capture_queue"]
    assert queue["queue_version"] == "live-gui-capture-queue-v1"
    assert queue["queue_id"] == report.queue_id
    assert queue["queue_status"] == "queued"
    assert queue["capture_slots"][0]["key"] == report.capture_slots[0].key
    assert queue["analyzer_jobs"][0]["input_slot_key"] == report.capture_slots[0].key
    assert payload["live_gui_rehearsal_session"]["session_id"] == (
        report.rehearsal_session.session_id
    )
    assert payload["live_gui_analyzer_readiness"]["gui_bundle_id"] == (
        report.rehearsal_session.gui_readiness.gui_bundle_id
    )
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_capture_queue_marks_guarded_rehearsal_sessions(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_queue import (
        build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session,
    )
    from rytm_randomizer.reports.live_gui_rehearsal_session import (
        build_style_performance_arc_live_gui_rehearsal_session_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    session = build_style_performance_arc_live_gui_rehearsal_session_report(
        feature_report=_feature_report(bpm=0.0, energy_arc=(0.5,)),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        lookahead_count=0,
        match_limit=1,
        take_count=3,
    )

    report = build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session(session)

    assert report.queue_status == "guarded"
    assert len(report.capture_slots) == 1
    assert report.capture_slots[0].status == "guarded"
    assert "Tempo is unknown" in report.capture_slots[0].hold_if
    assert report.analyzer_jobs[0].status == "guarded"
    assert "Resolve hold state" in report.analyzer_jobs[0].hold_if


def test_live_gui_capture_queue_preserves_custom_nonready_session_status(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_queue import (
        build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session,
    )
    from rytm_randomizer.reports.live_gui_rehearsal_session import (
        build_style_performance_arc_live_gui_rehearsal_session_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    session = build_style_performance_arc_live_gui_rehearsal_session_report(
        description="Jeff Mills Oscar Mulero focused rehearsal",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        lookahead_count=1,
        match_limit=1,
    )
    staged_session = replace(session, session_status="operator-review")

    report = build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session(
        staged_session
    )

    assert report.queue_status == "operator-review"
    assert {slot.status for slot in report.capture_slots} == {"operator-review"}


def test_live_gui_capture_queue_guards_red_ready_takes_and_custom_timing(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_queue import (
        build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session,
    )
    from rytm_randomizer.reports.live_gui_rehearsal_session import (
        build_style_performance_arc_live_gui_rehearsal_session_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    session = build_style_performance_arc_live_gui_rehearsal_session_report(
        description="Jeff Mills Oscar Mulero focused rehearsal",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        lookahead_count=1,
        match_limit=1,
    )
    altered_take = replace(session.takes[0], status="red", timing="breakdown bridge")
    altered_session = replace(session, takes=(altered_take,), session_status="ready")

    report = build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session(
        altered_session,
        capture_prefix="!!!",
    )

    assert report.queue_status == "queued"
    assert report.capture_slots[0].status == "guarded"
    assert report.capture_slots[0].capture_label.startswith("rehearsal-take")
    assert report.capture_slots[0].capture_window == "capture during breakdown bridge"


def test_live_gui_capture_queue_replays_audio_library_and_feature_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_queue import (
        build_style_performance_arc_live_gui_capture_queue_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)

    def fake_audio_report(path: Path):
        assert path == Path("reference.wav")
        return _feature_report()

    monkeypatch.setattr(
        "rytm_randomizer.style_analysis.extract_from_audio",
        fake_audio_report,
    )

    def fake_library_report(path: Path):
        assert path == Path("library-folder")
        return _feature_report()

    monkeypatch.setattr(
        "rytm_randomizer.style_analysis.analyze_library",
        fake_library_report,
    )

    audio_report = build_style_performance_arc_live_gui_capture_queue_report(
        audio_path=Path("reference.wav"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        capture_prefix="Audio Check",
    )
    assert "--audio reference.wav" in audio_report.replay_commands[0]
    assert audio_report.capture_slots[0].capture_label.startswith("audio-check-take")

    library_report = build_style_performance_arc_live_gui_capture_queue_report(
        library_path=Path("library-folder"),
        rytm_sysex_path=rytm_path,
        match_limit=1,
    )
    assert "--library library-folder" in library_report.replay_commands[0]

    feature_report = build_style_performance_arc_live_gui_capture_queue_report(
        feature_report=_feature_report(),
        rytm_sysex_path=rytm_path,
        match_limit=1,
    )
    assert "--description '<feature report target>'" in feature_report.replay_commands[0]


def test_live_gui_capture_queue_cli_dispatches_json_text_errors_and_help(
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
                "style-performance-arc-live-gui-capture-queue-report",
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
                "--capture-prefix",
                "warehouse",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc live GUI capture queue" in captured.out
    assert "Live GUI capture queue summary:" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-capture-queue-report",
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
    assert payload["live_gui_capture_queue"]["queue_status"] == "queued"
    assert payload["live_gui_capture_queue"]["capture_slots"][0]["key"] == "capture-001"
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-capture-queue-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires saved-kit source paths" in captured.err

    help_text = resolve_help_text("style-performance-arc-live-gui-capture-queue-report")
    assert (
        "RytmRandomizer passive CLI: style-performance-arc-live-gui-capture-queue-report"
    ) in help_text
    assert "GUI/audio analyzer capture queue" in help_text
    assert "no MIDI sending" in help_text


def test_live_gui_capture_queue_parser_validates_sources_counts_and_labels(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_analyzer_readiness import (
        build_style_performance_arc_live_gui_analyzer_readiness_report,
    )
    from rytm_randomizer.reports.live_gui_capture_queue import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_CAPTURE_QUEUE_CLI_COMMAND,
        _parse_cli_args,
        build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session,
        build_style_performance_arc_live_gui_capture_queue_report,
    )
    from rytm_randomizer.reports.live_gui_rehearsal_session import (
        build_style_performance_arc_live_gui_rehearsal_session_from_readiness,
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
            "--capture-prefix",
            "Flight Take",
            "--json",
        ]
    )
    assert args["audio_path"] == Path("track.wav")
    assert args["scope"] == "analog-four-only"
    assert args["match_limit"] == 2
    assert args["take_count"] == 4
    assert args["queue_label"] == "Flight check"
    assert args["capture_prefix"] == "Flight Take"
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
        (["--audio", "track.wav", "--capture-prefix", "   "], "capture_prefix"),
        (["--audio", "track.wav", "--matches", "0"], ">= 1"),
        (["--audio", "track.wav", "--lookahead", "-1"], ">= 0"),
        (["--audio", "track.wav", "--cue", "x"], "must be an integer"),
    )
    for argv, message in bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    with pytest.raises(ValueError, match="requires saved-kit source paths"):
        build_style_performance_arc_live_gui_capture_queue_report(
            feature_report=_feature_report(),
        )
    with pytest.raises(ValueError, match="description must include reference evidence"):
        build_style_performance_arc_live_gui_capture_queue_report(
            description="   ",
            rytm_sysex_path=rytm_path,
        )
    with pytest.raises(ValueError, match="requires exactly one reference source"):
        build_style_performance_arc_live_gui_capture_queue_report(
            description="Jeff Mills",
            audio_path=Path("track.wav"),
            rytm_sysex_path=Path("rytm.syx"),
        )
    with pytest.raises(ValueError, match="take_count must be >= 1"):
        build_style_performance_arc_live_gui_capture_queue_report(
            description="Jeff Mills",
            rytm_sysex_path=rytm_path,
            take_count=0,
        )
    with pytest.raises(ValueError, match="match_limit must be >= 1"):
        build_style_performance_arc_live_gui_capture_queue_report(
            description="Jeff Mills",
            rytm_sysex_path=rytm_path,
            match_limit=0,
        )
    readiness = build_style_performance_arc_live_gui_analyzer_readiness_report(
        description="Jeff Mills",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
    )
    session = build_style_performance_arc_live_gui_rehearsal_session_from_readiness(readiness)
    with pytest.raises(ValueError, match="label must not be blank"):
        build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session(
            session,
            queue_label="   ",
        )
    with pytest.raises(ValueError, match="capture_prefix must not be blank"):
        build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session(
            session,
            capture_prefix="   ",
        )
    empty_session = replace(session, takes=())
    with pytest.raises(ValueError, match="at least one rehearsal take"):
        build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session(empty_session)
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_CAPTURE_QUEUE_CLI_COMMAND.error_formatter(
            ValueError("bad queue")
        )
        == "Error: bad queue"
    )
