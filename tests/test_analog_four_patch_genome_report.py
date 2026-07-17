"""Tests for the passive Analog Four patch genome report."""

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


def test_importing_patch_genome_report_prints_nothing() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rytm_randomizer.reports.analog_four_patch_genome",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_patch_genome_report_text_shows_candidate_dna_and_front_panel_targets() -> None:
    from rytm_randomizer.reports.analog_four_patch_genome import (
        build_analog_four_patch_genome_report_from_source,
        format_analog_four_patch_genome_report,
    )

    report = build_analog_four_patch_genome_report_from_source(
        "--description",
        "hypnotic metallic techno with bright sync stab and compact envelope",
        track=1,
        selected_candidate=1,
    )
    text = "\n".join(format_analog_four_patch_genome_report(report))

    assert text.startswith("RytmRandomizer passive Analog Four patch genome\n")
    assert "Selected candidate: 1 / Closest reference" in text
    assert "Patch DNA:" in text
    assert "FILTERS C Filter Overdrive | screen +10 | MIDI CC86 -> 74 | NRPN 1:42" in text
    assert "FILTERS H Filter2 Type | screen HP2 | NRPN 1:47" in text
    assert "ENVF D EnvF Release Time | screen 12 | MIDI CC111 -> 12 | NRPN 1:63" in text
    assert "LFO1 G LFO1 Destination A | screen Filter1 Frequency | NRPN 1:86" in text
    assert "- no MIDI port opened" in text
    assert "- no MIDI sent" in text


def test_patch_genome_report_audio_source_uses_inferred_audio_genome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.reports import analog_four_patch_genome as report_module
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        build_analog_four_patch_genome,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_inference import (
        AnalogFourAudioPatchGenome,
        AnalogFourPatchAudioFeatures,
    )

    observed_paths: list[Path] = []

    def _fake_build_audio_genome(
        path: Path,
        *,
        track: int,
    ) -> AnalogFourAudioPatchGenome:
        observed_paths.append(path)
        feature_report = _feature_report()
        return AnalogFourAudioPatchGenome(
            feature_report=feature_report,
            audio_features=AnalogFourPatchAudioFeatures(
                audio_sha256="a" * 64,
                duration=0.5,
                attack=0.1,
                decay=0.2,
                sustain=0.3,
                tail=0.4,
                brightness=0.5,
                spectral_flatness=0.6,
                noise=0.7,
                low_end=0.8,
                harmonicity=0.9,
                transient=0.4,
                modulation=0.2,
            ),
            genome=build_analog_four_patch_genome(feature_report, track=track),
        )

    monkeypatch.setattr(
        report_module,
        "build_analog_four_audio_patch_genome",
        _fake_build_audio_genome,
    )

    report = report_module.build_analog_four_patch_genome_report_from_source(
        "--audio",
        "reference.wav",
        track=4,
        selected_candidate=3,
    )

    assert observed_paths == [Path("reference.wav")]
    assert report.source_label == "audio"
    assert report.genome.selected_track == 4
    assert report.selected.label == "Noisy texture"


def test_patch_genome_report_rejects_unknown_source_and_candidate() -> None:
    from rytm_randomizer.reports.analog_four_patch_genome import (
        build_analog_four_patch_genome_report,
        build_analog_four_patch_genome_report_from_source,
    )

    with pytest.raises(ValueError, match="source_flag must be"):
        build_analog_four_patch_genome_report_from_source(
            "--library",
            "reference-folder",
            track=1,
            selected_candidate=1,
        )
    with pytest.raises(ValueError, match="candidate must be in"):
        build_analog_four_patch_genome_report(
            _feature_report(),
            source_label="description",
            source_value="x",
            track=1,
            selected_candidate=5,
        )


def test_patch_genome_report_transport_phrase_front_panel_only() -> None:
    from rytm_randomizer.data.analog_four_display import AnalogFourPatchValue
    from rytm_randomizer.reports.analog_four_patch_genome import _transport_phrase

    value = AnalogFourPatchValue(
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

    assert _transport_phrase(value) == "front-panel only"


def test_patch_genome_report_json_includes_all_candidates() -> None:
    from rytm_randomizer.reports.analog_four_patch_genome import (
        build_analog_four_patch_genome_payload,
        build_analog_four_patch_genome_report_from_source,
    )

    report = build_analog_four_patch_genome_report_from_source(
        "--description",
        "low end pressure with noisy metallic percussion",
        track=3,
        selected_candidate=2,
    )
    payload = build_analog_four_patch_genome_payload(report)

    assert payload["selected_candidate"] == 2
    assert payload["selected_track"] == 3
    assert len(payload["genome"]["candidates"]) == 4
    assert payload["selected"]["label"] == "Brighter sync"
    assert payload["selected"]["genes"][0]["track"] == 3
    assert payload["safety"][0] == "passive read-only patch genome"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        build_analog_four_patch_genome_payload(report),
        sort_keys=True,
    )


def test_patch_genome_cli_description_json_mode(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(
        [
            "analog-four-patch-genome-report",
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
    assert payload["selected"]["genes"][0]["track"] == 2
    assert payload["genome"]["candidate_count"] == 4
    assert captured.err == ""


def test_patch_genome_cli_description_text_mode(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(
        [
            "analog-four-patch-genome-report",
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
    assert "Patch DNA:" in captured.out
    assert "Selected track: 2" in captured.out
    assert captured.err == ""


def test_patch_genome_cli_rejects_bad_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["analog-four-patch-genome-report", "--track", "5"])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "requires exactly one source" in captured.err
    assert captured.out == ""


def test_patch_genome_cli_handler_formats_builder_errors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.analog_four_patch_genome import (
        _handle_analog_four_patch_genome_report,
    )

    exit_code = _handle_analog_four_patch_genome_report(
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
def test_patch_genome_cli_rejects_specific_bad_arguments(
    args: list[str],
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["analog-four-patch-genome-report", *args])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert expected in captured.err
    assert captured.out == ""
