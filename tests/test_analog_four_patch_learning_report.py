"""Tests for the passive Analog Four patch learning report."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis import FeatureReport

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _feature_report() -> FeatureReport:
    return FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=134.0,
        tempo_stability=0.9,
        kick_density=0.4,
        percussion_density=0.7,
        low_end_weight=0.35,
        spectral_brightness=0.62,
        texture_noise=0.3,
        energy_arc=(0.1, 0.2, 0.4, 0.6, 0.7, 0.6, 0.4, 0.2),
        content_hash="",
        derived_at="2026-07-03T12:00:00Z",
    )


def test_importing_patch_learning_report_prints_nothing() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rytm_randomizer.reports.analog_four_patch_learning",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_patch_learning_report_text_shows_learning_routes_capture_and_dial_readiness() -> None:
    from rytm_randomizer.reports.analog_four_patch_learning import (
        build_analog_four_patch_learning_report_from_source,
        format_analog_four_patch_learning_report,
    )

    report = build_analog_four_patch_learning_report_from_source(
        "--description",
        "hypnotic metallic techno with bright sync stab and compact envelope",
        track=1,
        selected_candidate=1,
    )
    text = "\n".join(format_analog_four_patch_learning_report(report))

    assert text.startswith("RytmRandomizer passive Analog Four patch learning\n")
    assert "Selected candidate: 1 / Closest reference" in text
    assert "Candidate ranking:" in text
    assert "- 1. Column 1 / Closest reference" in text
    assert "Knowledge acquisition routes:" in text
    assert "Metallic pressure -> Sync Amount" in text
    assert "Capture matrix:" in text
    assert "a4-root-short | C2 | velocity 96" in text
    assert "Live dial-in readiness:" in text
    assert "screen-only-nrpn" in text
    assert "Selected patch DNA:" in text
    assert "FILTERS C Filter Overdrive | screen +10 | MIDI CC86 -> 74" in text
    assert "- no MIDI port opened" in text
    assert "- no MIDI sent" in text


def test_patch_learning_report_audio_source_uses_audio_extractor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.reports import analog_four_patch_learning as report_module

    observed_paths: list[Path] = []

    def _fake_extract_from_audio(path: Path) -> FeatureReport:
        observed_paths.append(path)
        return _feature_report()

    monkeypatch.setattr(report_module, "extract_from_audio", _fake_extract_from_audio)

    report = report_module.build_analog_four_patch_learning_report_from_source(
        "--audio",
        "reference.wav",
        track=4,
        selected_candidate=3,
    )

    assert observed_paths == [Path("reference.wav")]
    assert report.source_label == "audio"
    assert report.packet.selected_track == 4
    assert report.packet.selected_label == "Noisy texture"


def test_patch_learning_report_rejects_unknown_source() -> None:
    from rytm_randomizer.reports.analog_four_patch_learning import (
        build_analog_four_patch_learning_report_from_source,
    )

    with pytest.raises(ValueError, match="source_flag must be"):
        build_analog_four_patch_learning_report_from_source(
            "--library",
            "reference-folder",
            track=1,
            selected_candidate=1,
        )


def test_patch_learning_report_private_transport_helpers_cover_manual_rows() -> None:
    from rytm_randomizer.data.analog_four_display import AnalogFourPatchValue
    from rytm_randomizer.reports.analog_four_patch_learning import (
        _learning_join_or_none,
        _learning_transport_phrase,
    )

    front_panel_value = AnalogFourPatchValue(
        parameter="Manual-only",
        section="TEST",
        encoder="-",
        screen_value="manual",
        midi_value=None,
        cc_msb=None,
        cc_lsb=None,
        nrpn_address=None,
        transport_status="screen-only",
        dial_direction="set manually",
    )
    nrpn_value = AnalogFourPatchValue(
        parameter="NRPN-only",
        section="TEST",
        encoder="-",
        screen_value="12",
        midi_value=12,
        cc_msb=None,
        cc_lsb=None,
        nrpn_address=(1, 99),
        transport_status="nrpn-ready",
        dial_direction="set to 12",
    )

    assert _learning_join_or_none(()) == "none"
    assert _learning_transport_phrase(front_panel_value) == "front-panel only"
    assert _learning_transport_phrase(nrpn_value) == "NRPN 1:99 -> 12"


def test_patch_learning_report_json_includes_packet_genome_and_selected_patch() -> None:
    from rytm_randomizer.reports.analog_four_patch_learning import (
        build_analog_four_patch_learning_payload,
        build_analog_four_patch_learning_report_from_source,
    )

    report = build_analog_four_patch_learning_report_from_source(
        "--description",
        "low end pressure with noisy metallic percussion",
        track=3,
        selected_candidate=2,
    )
    payload = build_analog_four_patch_learning_payload(report)

    assert payload["selected_candidate"] == 2
    assert payload["selected_track"] == 3
    assert payload["learning_packet"]["selected_patch"]["label"] == "Brighter sync"
    assert payload["learning_packet"]["candidate_scores"][0]["column"] == 1
    assert payload["learning_packet"]["live_dial_readiness"]["cc_ready_count"] > 0
    assert payload["safety"][0] == "passive read-only patch learning"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        build_analog_four_patch_learning_payload(report),
        sort_keys=True,
    )


def test_patch_learning_cli_description_json_mode(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(
        [
            "analog-four-patch-learning-report",
            "--description",
            "dark rolling techno with narrow pulse and HP2 filter",
            "--track",
            "2",
            "--candidate",
            "1",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["selected_track"] == 2
    assert payload["selected_candidate"] == 1
    assert payload["learning_packet"]["selected_patch"]["genes"][0]["track"] == 2
    assert payload["learning_packet"]["capture_steps"][0]["step_id"] == "a4-root-short"
    assert captured.err == ""


def test_patch_learning_cli_description_text_mode(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(
        [
            "analog-four-patch-learning-report",
            "--description",
            "dark rolling techno with narrow pulse and HP2 filter",
            "--track",
            "2",
            "--candidate",
            "1",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Knowledge acquisition routes:" in captured.out
    assert "Selected track: 2" in captured.out
    assert captured.err == ""


def test_patch_learning_cli_rejects_bad_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["analog-four-patch-learning-report", "--track", "5"])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "requires exactly one source" in captured.err
    assert captured.out == ""


def test_patch_learning_cli_handler_formats_builder_errors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.analog_four_patch_learning import (
        _handle_analog_four_patch_learning_report,
    )

    exit_code = _handle_analog_four_patch_learning_report(
        "--library",
        "reference-folder",
        track=1,
        selected_candidate=1,
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "source_flag must be --description or --audio" in captured.err
    assert captured.out == ""


@pytest.mark.parametrize(
    "args, expected",
    [
        (["--description"], "--description requires a value"),
        (["--description", "x", "--track"], "--track requires a value"),
        (["--description", "x", "--candidate"], "--candidate requires a value"),
        (["--description", "x", "--candidate", "NaN"], "--candidate must be an integer"),
        (["--description", "x", "--track", "5"], "--track must be in 1..4"),
        (["--description", "x", "--unknown"], "unknown argument: --unknown"),
    ],
)
def test_patch_learning_cli_rejects_specific_bad_arguments(
    args: list[str],
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["analog-four-patch-learning-report", *args])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert expected in captured.err
    assert captured.out == ""
