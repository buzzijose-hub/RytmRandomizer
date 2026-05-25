"""Tests for passive live analyzer handoff reporting."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _feature_report(
    *,
    bpm: float = 138.0,
    tempo_stability: float = 0.91,
    kick_density: float = 0.82,
    percussion_density: float = 0.74,
    low_end_weight: float = 0.67,
    spectral_brightness: float = 0.42,
    texture_noise: float = 0.58,
    energy_arc: tuple[float, ...] = (0.2, 0.5, 0.9),
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


def test_live_analyzer_handoff_report_builds_gui_analyzer_packet_when_description_reference(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_analyzer_handoff import (
        build_style_performance_arc_live_analyzer_handoff_report,
        format_style_performance_arc_live_analyzer_handoff_report,
        to_style_performance_arc_live_analyzer_handoff_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    report = build_style_performance_arc_live_analyzer_handoff_report(
        description="Jeff Mills Oscar Mulero Birmingham Regis Surgeon warehouse pressure",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=2,
    )

    assert report.analyzer_handoff_version == "live-analyzer-handoff-v1"
    assert report.handoff_status == report.control_surface.surface_status
    assert report.source_kind == "description"
    assert report.source_reference is None
    assert report.selected_arc_key == report.control_surface.selected_arc_key
    assert report.reference_match.selected_match.arc.key == report.selected_arc_key
    assert report.feature_hash == report.reference_match.feature_report.content_hash
    assert len(report.feature_meters) >= 7
    assert {meter.key for meter in report.feature_meters} >= {
        "bpm",
        "low-end",
        "brightness",
        "noise",
        "energy-arc",
    }
    assert len(report.match_cards) >= 3
    assert report.control_sync_cards[0].key == "surface"
    assert any("Analyze reference" in prompt for prompt in report.capture_prompts)
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli style-performance-arc-live-analyzer-handoff-report"
    )

    lines = format_style_performance_arc_live_analyzer_handoff_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live analyzer handoff"
    assert "Live analyzer handoff summary:" in lines
    assert "- Source: description / inline description" in lines
    assert "Measured feature meters:" in lines
    assert "Top influence matches:" in lines
    assert "Control surface sync:" in lines
    assert "Capture prompts:" in lines
    assert "audio analyzer handoff only" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_analyzer_handoff_json(report)
    handoff = payload["live_analyzer_handoff"]
    assert handoff["analyzer_handoff_version"] == "live-analyzer-handoff-v1"
    assert handoff["selected_arc_key"] == report.selected_arc_key
    assert handoff["feature_hash"] == report.feature_hash
    assert handoff["feature_meters"][0]["key"] == report.feature_meters[0].key
    assert payload["live_control_surface"]["surface_id"] == report.control_surface.surface_id
    assert payload["reference_match"]["selected"]["arc"]["key"] == report.selected_arc_key
    assert payload["safety"][0] == "passive/read-only"


def test_live_analyzer_handoff_from_control_surface_covers_status_and_empty_edges(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_analyzer_handoff import (
        build_style_performance_arc_live_analyzer_handoff_from_control_surface,
        format_style_performance_arc_live_analyzer_handoff_report,
    )
    from rytm_randomizer.reports.live_control_surface import (
        build_style_performance_arc_live_control_surface_report,
    )
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_reference_match_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    control_surface = build_style_performance_arc_live_control_surface_report(
        description="Jeff Mills Oscar Mulero tunnel hypnosis",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=0,
    )
    reference_match = build_style_performance_arc_reference_match_report(
        description="Jeff Mills Oscar Mulero tunnel hypnosis",
    )

    report = build_style_performance_arc_live_analyzer_handoff_from_control_surface(
        control_surface=control_surface,
        reference_match=reference_match,
        match_limit=1,
    )

    assert len(report.match_cards) == 1
    assert report.control_sync_cards[0].status == control_surface.surface_status
    assert any(card.key == "now-cue" for card in report.control_sync_cards)
    assert any(card.key == "machines" for card in report.control_sync_cards)
    lines = format_style_performance_arc_live_analyzer_handoff_report(report)
    assert "- No next cue sync cards requested." in lines
    with pytest.raises(ValueError, match="match_limit must be >= 1"):
        build_style_performance_arc_live_analyzer_handoff_from_control_surface(
            control_surface=control_surface,
            reference_match=reference_match,
            match_limit=0,
        )


def test_live_analyzer_handoff_covers_feature_report_audio_and_match_edges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_analyzer_handoff import (
        build_style_performance_arc_live_analyzer_handoff_report,
        format_style_performance_arc_live_analyzer_handoff_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    feature_report = _feature_report()

    feature_handoff = build_style_performance_arc_live_analyzer_handoff_report(
        feature_report=feature_report,
        rytm_sysex_path=rytm_path,
        match_limit=2,
    )

    assert feature_handoff.source_kind == "feature-report"
    assert feature_handoff.replay_commands[0].endswith(
        "--description '<feature report handoff>' --matches 2"
    )
    feature_lines = format_style_performance_arc_live_analyzer_handoff_report(feature_handoff)
    assert "- Source: feature-report / injected FeatureReport" in feature_lines
    assert any("tempo-stability / Tempo stability: 91% | high" in line for line in feature_lines)
    assert any("brightness / Spectral brightness: 42% | medium" in line for line in feature_lines)
    assert any("energy-arc / Energy arc: building | building" in line for line in feature_lines)

    falling_handoff = build_style_performance_arc_live_analyzer_handoff_report(
        feature_report=_feature_report(
            bpm=0.0,
            tempo_stability=0.2,
            kick_density=0.2,
            percussion_density=0.2,
            low_end_weight=0.2,
            spectral_brightness=0.2,
            texture_noise=0.2,
            energy_arc=(0.9, 0.5, 0.2),
        ),
        rytm_sysex_path=rytm_path,
        match_limit=1,
    )
    falling_lines = format_style_performance_arc_live_analyzer_handoff_report(falling_handoff)
    assert any("bpm / Tempo: unknown | needs-audio" in line for line in falling_lines)
    assert any("energy-arc / Energy arc: falling | falling" in line for line in falling_lines)

    unknown_handoff = build_style_performance_arc_live_analyzer_handoff_report(
        feature_report=_feature_report(energy_arc=(0.5,)),
        rytm_sysex_path=rytm_path,
        match_limit=1,
    )
    unknown_lines = format_style_performance_arc_live_analyzer_handoff_report(unknown_handoff)
    assert any("energy-arc / Energy arc: unknown | unknown" in line for line in unknown_lines)

    monkeypatch.setattr(
        "rytm_randomizer.style_analysis.extract_from_audio",
        lambda _path: _feature_report(),
    )
    audio_handoff = build_style_performance_arc_live_analyzer_handoff_report(
        audio_path=Path("track.wav"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
    )
    audio_lines = format_style_performance_arc_live_analyzer_handoff_report(audio_handoff)
    assert "- Source: audio / track.wav" in audio_lines
    assert audio_handoff.replay_commands[0].endswith("--audio track.wav --matches 1")
    assert audio_handoff.capture_prompts[0].startswith("Analyze reference audio")

    weak_handoff = build_style_performance_arc_live_analyzer_handoff_report(
        description="Robert Hood",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=4,
    )
    assert any(card.status == "weak" for card in weak_handoff.match_cards)


def test_live_analyzer_handoff_cli_dispatch_json_and_errors(
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
                "style-performance-arc-live-analyzer-handoff-report",
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
    assert "RytmRandomizer passive style performance arc live analyzer handoff" in captured.out
    assert "Live analyzer handoff summary:" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-analyzer-handoff-report",
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
    assert payload["live_analyzer_handoff"]["handoff_status"] == "rehearsal-ready"
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-analyzer-handoff-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires saved-kit source paths" in captured.err

    help_text = resolve_help_text("style-performance-arc-live-analyzer-handoff-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-live-analyzer-handoff-report" in (
        help_text
    )
    assert "audio analyzer handoff" in help_text
    assert "no MIDI sending" in help_text


def test_live_analyzer_handoff_parser_and_feature_report_edges():
    from rytm_randomizer.reports.live_analyzer_handoff import (
        STYLE_PERFORMANCE_ARC_LIVE_ANALYZER_HANDOFF_CLI_COMMAND,
        _display_source,
        _parse_cli_args,
        build_style_performance_arc_live_analyzer_handoff_report,
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
        build_style_performance_arc_live_analyzer_handoff_report(
            feature_report=_feature_report(),
        )
    with pytest.raises(ValueError, match="requires exactly one reference source"):
        build_style_performance_arc_live_analyzer_handoff_report(
            description="Jeff Mills",
            audio_path=Path("track.wav"),
            rytm_sysex_path=Path("rytm.syx"),
        )
    with pytest.raises(ValueError, match="description must include reference evidence"):
        build_style_performance_arc_live_analyzer_handoff_report(
            description="   ",
            rytm_sysex_path=Path("rytm.syx"),
        )
    with pytest.raises(ValueError, match="match_limit must be >= 1"):
        build_style_performance_arc_live_analyzer_handoff_report(
            description="Jeff Mills",
            rytm_sysex_path=Path("rytm.syx"),
            match_limit=0,
        )
    assert _display_source("unknown", None) == "unknown / none"
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_ANALYZER_HANDOFF_CLI_COMMAND.error_formatter(
            ValueError("bad handoff")
        )
        == "Error: bad handoff"
    )
