"""Tests for passive live analyzer target reporting."""

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


def test_live_analyzer_targets_report_builds_rehearsal_target_packet(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_analyzer_targets import (
        build_style_performance_arc_live_analyzer_targets_report,
        format_style_performance_arc_live_analyzer_targets_report,
        to_style_performance_arc_live_analyzer_targets_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    report = build_style_performance_arc_live_analyzer_targets_report(
        description="Jeff Mills Oscar Mulero Birmingham Regis Surgeon warehouse pressure",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=2,
        match_limit=3,
    )

    assert report.target_packet_version == "live-analyzer-targets-v1"
    assert len(report.target_packet_id) == 16
    assert report.target_status == report.analyzer_handoff.handoff_status
    assert report.selected_arc_key == report.analyzer_handoff.selected_arc_key
    assert report.source_kind == "description"
    assert {band.key for band in report.target_bands} >= {
        "bpm",
        "tempo-stability",
        "kick-density",
        "percussion-density",
        "low-end",
        "brightness",
        "noise",
        "energy-arc",
    }
    assert report.target_bands[0].key == "bpm"
    assert report.target_bands[0].target_window
    assert any("current cue" in checkpoint.timing for checkpoint in report.cue_checkpoints)
    assert any("next cue" in checkpoint.timing for checkpoint in report.cue_checkpoints)
    assert any("listen-only" in step.action for step in report.calibration_steps)
    assert any(threshold.key == "tempo-drift" for threshold in report.warning_thresholds)
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report"
    )

    lines = format_style_performance_arc_live_analyzer_targets_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live analyzer targets"
    assert "Live analyzer target packet summary:" in lines
    assert "Target bands:" in lines
    assert "Cue checkpoints:" in lines
    assert "Calibration steps:" in lines
    assert "Warning thresholds:" in lines
    assert "future live analyzer comparison only" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_analyzer_targets_json(report)
    targets = payload["live_analyzer_targets"]
    assert targets["target_packet_version"] == "live-analyzer-targets-v1"
    assert targets["target_packet_id"] == report.target_packet_id
    assert targets["selected_arc_key"] == report.selected_arc_key
    assert targets["target_bands"][0]["key"] == report.target_bands[0].key
    assert payload["live_analyzer_handoff"]["handoff_id"] == report.analyzer_handoff.handoff_id
    assert payload["safety"][0] == "passive/read-only"


def test_live_analyzer_targets_from_handoff_covers_unknown_feature_edges(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_analyzer_handoff import (
        build_style_performance_arc_live_analyzer_handoff_report,
    )
    from rytm_randomizer.reports.live_analyzer_targets import (
        build_style_performance_arc_live_analyzer_targets_from_handoff,
        format_style_performance_arc_live_analyzer_targets_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    handoff = build_style_performance_arc_live_analyzer_handoff_report(
        feature_report=_feature_report(bpm=0.0, energy_arc=(0.5,)),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        lookahead_count=0,
    )
    report = build_style_performance_arc_live_analyzer_targets_from_handoff(handoff)

    bpm_band = next(band for band in report.target_bands if band.key == "bpm")
    energy_band = next(band for band in report.target_bands if band.key == "energy-arc")
    assert bpm_band.status == "needs-audio"
    assert bpm_band.target_window == "manual tempo target required"
    assert energy_band.status == "unknown"
    assert energy_band.target_window == "capture longer reference"
    assert any(threshold.key == "manual-tempo" for threshold in report.warning_thresholds)

    lines = format_style_performance_arc_live_analyzer_targets_report(report)
    assert "- No next cue checkpoints requested." in lines


def test_live_analyzer_targets_cover_measured_audio_and_energy_shapes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_analyzer_targets import (
        build_style_performance_arc_live_analyzer_targets_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)

    measured = build_style_performance_arc_live_analyzer_targets_report(
        feature_report=_feature_report(),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
    )
    bpm_band = next(band for band in measured.target_bands if band.key == "bpm")
    energy_band = next(band for band in measured.target_bands if band.key == "energy-arc")
    assert bpm_band.target_window.endswith("BPM")
    assert energy_band.status == "building"
    assert measured.replay_commands[0].endswith(
        "--description '<feature report target>' --matches 1"
    )

    falling = build_style_performance_arc_live_analyzer_targets_report(
        feature_report=_feature_report(energy_arc=(0.92, 0.51, 0.2)),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
    )
    falling_band = next(band for band in falling.target_bands if band.key == "energy-arc")
    assert falling_band.status == "falling"

    flat = build_style_performance_arc_live_analyzer_targets_report(
        feature_report=_feature_report(energy_arc=(0.5, 0.55)),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
    )
    flat_band = next(band for band in flat.target_bands if band.key == "energy-arc")
    assert flat_band.status == "flat"

    monkeypatch.setattr(
        "rytm_randomizer.style_analysis.extract_from_audio",
        lambda _path: _feature_report(),
    )
    audio = build_style_performance_arc_live_analyzer_targets_report(
        audio_path=Path("track.wav"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
    )
    assert audio.replay_commands[0].endswith("--audio track.wav --matches 1")


def test_live_analyzer_targets_cli_dispatch_json_and_errors(
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
                "style-performance-arc-live-analyzer-targets-report",
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
    assert "RytmRandomizer passive style performance arc live analyzer targets" in captured.out
    assert "Live analyzer target packet summary:" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-analyzer-targets-report",
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
    assert payload["live_analyzer_targets"]["target_status"] == "rehearsal-ready"
    assert payload["live_analyzer_targets"]["target_bands"][0]["key"] == "bpm"
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-analyzer-targets-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires saved-kit source paths" in captured.err

    help_text = resolve_help_text("style-performance-arc-live-analyzer-targets-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-live-analyzer-targets-report" in (
        help_text
    )
    assert "future live analyzer comparison" in help_text
    assert "no MIDI sending" in help_text


def test_live_analyzer_targets_parser_edges():
    from rytm_randomizer.reports.live_analyzer_targets import (
        STYLE_PERFORMANCE_ARC_LIVE_ANALYZER_TARGETS_CLI_COMMAND,
        _parse_cli_args,
        build_style_performance_arc_live_analyzer_targets_report,
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
        build_style_performance_arc_live_analyzer_targets_report(
            feature_report=_feature_report(),
        )
    with pytest.raises(ValueError, match="requires exactly one reference source"):
        build_style_performance_arc_live_analyzer_targets_report(
            description="Jeff Mills",
            audio_path=Path("track.wav"),
            rytm_sysex_path=Path("rytm.syx"),
        )
    with pytest.raises(ValueError, match="description must include reference evidence"):
        build_style_performance_arc_live_analyzer_targets_report(
            description="   ",
            rytm_sysex_path=Path("rytm.syx"),
        )
    with pytest.raises(ValueError, match="match_limit must be >= 1"):
        build_style_performance_arc_live_analyzer_targets_report(
            description="Jeff Mills",
            rytm_sysex_path=Path("rytm.syx"),
            match_limit=0,
        )
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_ANALYZER_TARGETS_CLI_COMMAND.error_formatter(
            ValueError("bad targets")
        )
        == "Error: bad targets"
    )
