"""Tests for passive live GUI/audio-analyzer readiness reporting."""

from __future__ import annotations

import json
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
        derived_at="2026-05-22T00:00:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def test_live_gui_analyzer_readiness_builds_operator_bundle_when_reference_is_description(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_analyzer_readiness import (
        build_style_performance_arc_live_gui_analyzer_readiness_report,
        format_style_performance_arc_live_gui_analyzer_readiness_report,
        to_style_performance_arc_live_gui_analyzer_readiness_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    report = build_style_performance_arc_live_gui_analyzer_readiness_report(
        description="Jeff Mills Oscar Mulero Birmingham Regis Surgeon warehouse pressure",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=2,
        match_limit=3,
    )

    assert report.gui_bundle_version == "live-gui-analyzer-readiness-v1"
    assert len(report.gui_bundle_id) == 16
    assert report.gui_status == report.analyzer_targets.target_status
    assert report.selected_arc_key == report.analyzer_targets.selected_arc_key
    assert report.selected_arc_name == report.analyzer_targets.selected_arc_name
    assert report.scope == report.analyzer_targets.scope
    assert report.source_kind == "description"
    assert {panel.key for panel in report.panels} >= {
        "overview",
        "transport",
        "cue-strip",
        "machine-cards",
        "analyzer-targets",
        "warning-thresholds",
        "replay-safety",
    }
    assert report.panels[0].status == report.gui_status
    assert any(stream.key == "feature-meters" for stream in report.analyzer_streams)
    target_stream = next(
        stream for stream in report.analyzer_streams if stream.key == "target-bands"
    )
    assert "live_analyzer_targets.target_bands" in target_stream.source_keys
    assert target_stream.consumer == "GUI analyzer meter overlay"
    assert any("listen-only" in step.action for step in report.operator_steps)
    assert any("no MIDI sending" in action for action in report.blocked_actions)
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-analyzer-readiness-report"
    )
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-analyzer-targets-report"
    )

    lines = format_style_performance_arc_live_gui_analyzer_readiness_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI analyzer readiness"
    assert "GUI/audio-analyzer readiness bundle summary:" in lines
    assert "GUI panel manifest:" in lines
    assert "Analyzer stream wiring:" in lines
    assert "Operator workflow:" in lines
    assert "Blocked active actions:" in lines
    assert "GUI/audio-analyzer readiness bundle only" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_analyzer_readiness_json(report)
    readiness = payload["live_gui_analyzer_readiness"]
    assert readiness["gui_bundle_version"] == "live-gui-analyzer-readiness-v1"
    assert readiness["gui_bundle_id"] == report.gui_bundle_id
    assert readiness["selected_arc_key"] == report.selected_arc_key
    assert readiness["panels"][0]["key"] == report.panels[0].key
    assert readiness["analyzer_streams"][0]["key"] == report.analyzer_streams[0].key
    assert readiness["operator_steps"][0]["position"] == 1
    assert payload["live_analyzer_targets"]["target_packet_id"] == (
        report.analyzer_targets.target_packet_id
    )
    assert payload["live_analyzer_handoff"]["handoff_id"] == (
        report.analyzer_targets.analyzer_handoff.handoff_id
    )
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_analyzer_readiness_from_targets_keeps_warning_and_no_lookahead_states(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_analyzer_targets import (
        build_style_performance_arc_live_analyzer_targets_report,
    )
    from rytm_randomizer.reports.live_gui_analyzer_readiness import (
        build_style_performance_arc_live_gui_analyzer_readiness_from_targets,
        format_style_performance_arc_live_gui_analyzer_readiness_report,
        to_style_performance_arc_live_gui_analyzer_readiness_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    targets = build_style_performance_arc_live_analyzer_targets_report(
        feature_report=_feature_report(bpm=0.0, energy_arc=(0.5,)),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        lookahead_count=0,
        match_limit=1,
    )
    report = build_style_performance_arc_live_gui_analyzer_readiness_from_targets(targets)

    warning_panel = next(panel for panel in report.panels if panel.key == "warning-thresholds")
    assert warning_panel.status == "guarded"
    assert "manual tempo" in warning_panel.operator_action
    workflow = "\n".join(step.hold_if for step in report.operator_steps)
    assert "Tempo is unknown" in workflow

    lines = format_style_performance_arc_live_gui_analyzer_readiness_report(report)
    assert "- No next cue checkpoints requested." in lines

    payload = to_style_performance_arc_live_gui_analyzer_readiness_json(report)
    warning_stream = next(
        stream
        for stream in payload["live_gui_analyzer_readiness"]["analyzer_streams"]
        if stream["key"] == "warning-thresholds"
    )
    assert warning_stream["status"] == "guarded"


def test_live_gui_analyzer_readiness_covers_measured_audio_source_and_watch_warnings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_analyzer_readiness import (
        build_style_performance_arc_live_gui_analyzer_readiness_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    monkeypatch.setattr(
        "rytm_randomizer.style_analysis.extract_from_audio",
        lambda _path: _feature_report(),
    )
    report = build_style_performance_arc_live_gui_analyzer_readiness_report(
        audio_path=Path("track.wav"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
    )

    warning_panel = next(panel for panel in report.panels if panel.key == "warning-thresholds")
    warning_stream = next(
        stream for stream in report.analyzer_streams if stream.key == "warning-thresholds"
    )
    assert warning_panel.status == "watch"
    assert (
        warning_panel.operator_action == "Watch warning thresholds before launching the next cue."
    )
    assert warning_stream.status == "watch"
    assert report.replay_commands[0].endswith("--audio track.wav --matches 1")


def test_live_gui_analyzer_readiness_cli_dispatches_json_text_errors_and_help(
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
                "style-performance-arc-live-gui-analyzer-readiness-report",
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
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert (
        "RytmRandomizer passive style performance arc live GUI analyzer readiness" in captured.out
    )
    assert "GUI/audio-analyzer readiness bundle summary:" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-analyzer-readiness-report",
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
    assert payload["live_gui_analyzer_readiness"]["gui_status"] == "rehearsal-ready"
    assert payload["live_gui_analyzer_readiness"]["panels"][0]["key"] == "overview"
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-analyzer-readiness-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires saved-kit source paths" in captured.err

    help_text = resolve_help_text("style-performance-arc-live-gui-analyzer-readiness-report")
    assert (
        "RytmRandomizer passive CLI: " "style-performance-arc-live-gui-analyzer-readiness-report"
    ) in help_text
    assert "GUI/audio-analyzer readiness bundle" in help_text
    assert "no MIDI sending" in help_text


def test_live_gui_analyzer_readiness_parser_validates_sources_and_numeric_options():
    from rytm_randomizer.reports.live_gui_analyzer_readiness import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_READINESS_CLI_COMMAND,
        _parse_cli_args,
        build_style_performance_arc_live_gui_analyzer_readiness_report,
    )

    audio_args = _parse_cli_args(
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
            "--json",
        ]
    )
    assert audio_args["audio_path"] == Path("track.wav")
    assert audio_args["scope"] == "analog-four-only"
    assert audio_args["match_limit"] == 2
    assert audio_args["json_output"] is True
    library_args = _parse_cli_args(["--library", "crate"])
    assert library_args["library_path"] == Path("crate")

    bad_cases = (
        ([], "usage"),
        (["--description"], "usage"),
        (["--bogus"], "usage"),
        (["--description", "   "], "description must include reference evidence"),
        (["--audio", "track.wav", "--rank", "0"], ">= 1"),
        (["--audio", "track.wav", "--lookahead", "-1"], ">= 0"),
        (["--audio", "track.wav", "--matches", "0"], ">= 1"),
        (["--audio", "track.wav", "--cue", "x"], "must be an integer"),
    )
    for argv, message in bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    with pytest.raises(ValueError, match="requires saved-kit source paths"):
        build_style_performance_arc_live_gui_analyzer_readiness_report(
            feature_report=_feature_report(),
        )
    with pytest.raises(ValueError, match="requires exactly one reference source"):
        build_style_performance_arc_live_gui_analyzer_readiness_report(
            description="Jeff Mills",
            audio_path=Path("track.wav"),
            rytm_sysex_path=Path("rytm.syx"),
        )
    with pytest.raises(ValueError, match="description must include reference evidence"):
        build_style_performance_arc_live_gui_analyzer_readiness_report(
            description="   ",
            rytm_sysex_path=Path("rytm.syx"),
        )
    with pytest.raises(ValueError, match="match_limit must be >= 1"):
        build_style_performance_arc_live_gui_analyzer_readiness_report(
            description="Jeff Mills",
            rytm_sysex_path=Path("rytm.syx"),
            match_limit=0,
        )
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_READINESS_CLI_COMMAND.error_formatter(
            ValueError("bad GUI readiness")
        )
        == "Error: bad GUI readiness"
    )
