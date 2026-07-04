"""Tests for the passive Analog Four patch capture-corpus report."""

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


def _write_corpus_file(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "entry_id": "studio-capture-001",
                        "label": "Jose A4 take 001",
                        "source_kind": "captured-hardware",
                        "track": 2,
                        "selected_candidate": 1,
                        "capture_notes": ["manual front-panel dialed from patch genome"],
                        "feature_report": {
                            "source_type": "SINGLE_TRACK",
                            "confidence": "HIGH",
                            "bpm": 134.0,
                            "tempo_stability": 0.9,
                            "kick_density": 0.4,
                            "percussion_density": 0.7,
                            "low_end_weight": 0.35,
                            "spectral_brightness": 0.62,
                            "texture_noise": 0.3,
                            "energy_arc": [0.1, 0.2, 0.4, 0.6, 0.7, 0.6, 0.4, 0.2],
                            "derived_at": "2026-07-03T12:00:00Z",
                        },
                    }
                ]
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _valid_feature_payload() -> dict[str, object]:
    return {
        "source_type": "SINGLE_TRACK",
        "confidence": "HIGH",
        "bpm": 134.0,
        "tempo_stability": 0.9,
        "kick_density": 0.4,
        "percussion_density": 0.7,
        "low_end_weight": 0.35,
        "spectral_brightness": 0.62,
        "texture_noise": 0.3,
        "energy_arc": [0.1, 0.2, 0.4, 0.6, 0.7, 0.6, 0.4, 0.2],
        "derived_at": "2026-07-03T12:00:00Z",
    }


def test_importing_patch_corpus_report_prints_nothing() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rytm_randomizer.reports.analog_four_patch_corpus",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_patch_corpus_report_text_shows_nearest_matches_and_calibration_gaps() -> None:
    from rytm_randomizer.reports.analog_four_patch_corpus import (
        build_analog_four_patch_corpus_report_from_source,
        format_analog_four_patch_corpus_report,
    )

    report = build_analog_four_patch_corpus_report_from_source(
        "--description",
        "hypnotic metallic techno with bright sync stab and compact envelope",
        track=1,
        limit=3,
        corpus_file=None,
    )
    text = "\n".join(format_analog_four_patch_corpus_report(report))

    assert text.startswith("RytmRandomizer passive Analog Four patch capture corpus\n")
    assert "Corpus readiness: synthetic-starter-only" in text
    assert "Recommended candidate: 1 / Closest reference" in text
    assert "Nearest corpus matches:" in text
    assert "a4-template-closest-reference" in text
    assert "Calibration gaps:" in text
    assert "capture real A4 audio for candidate 1" in text
    assert "- no MIDI port opened" in text
    assert "- no MIDI sent" in text


def test_patch_corpus_report_loads_captured_corpus_file(tmp_path: Path) -> None:
    from rytm_randomizer.reports.analog_four_patch_corpus import (
        build_analog_four_patch_corpus_report,
    )

    corpus_file = tmp_path / "a4-corpus.json"
    _write_corpus_file(corpus_file)

    report = build_analog_four_patch_corpus_report(
        _feature_report(),
        source_label="description",
        source_value="manual feature report",
        track=2,
        limit=4,
        corpus_file=corpus_file,
    )

    assert report.corpus_file == corpus_file
    assert report.packet.match_summary.total_entries == 1
    assert report.packet.match_summary.captured_count == 1
    assert report.packet.matches[0].entry_id == "studio-capture-001"
    assert report.packet.matches[0].similarity == 100


def test_patch_corpus_cli_corpus_file_text_mode_labels_file_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    corpus_file = tmp_path / "a4-corpus.json"
    _write_corpus_file(corpus_file)

    exit_code = main(
        [
            "analog-four-patch-corpus-report",
            "--description",
            "dark rolling techno with narrow pulse and HP2 filter",
            "--track",
            "2",
            "--corpus-file",
            str(corpus_file),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Corpus file: {corpus_file}" in captured.out
    assert "studio-capture-001" in captured.out
    assert captured.err == ""


def test_patch_corpus_report_audio_source_uses_audio_extractor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.reports import analog_four_patch_corpus as report_module

    observed_paths: list[Path] = []

    def _fake_extract_from_audio(path: Path) -> FeatureReport:
        observed_paths.append(path)
        return _feature_report()

    monkeypatch.setattr(report_module, "extract_from_audio", _fake_extract_from_audio)

    report = report_module.build_analog_four_patch_corpus_report_from_source(
        "--audio",
        "reference.wav",
        track=4,
        limit=2,
        corpus_file=None,
    )

    assert observed_paths == [Path("reference.wav")]
    assert report.source_label == "audio"
    assert report.packet.selected_track == 4


def test_patch_corpus_report_json_includes_match_packet() -> None:
    from rytm_randomizer.reports.analog_four_patch_corpus import (
        build_analog_four_patch_corpus_payload,
        build_analog_four_patch_corpus_report_from_source,
    )

    report = build_analog_four_patch_corpus_report_from_source(
        "--description",
        "low end pressure with noisy metallic percussion",
        track=3,
        limit=2,
        corpus_file=None,
    )
    payload = build_analog_four_patch_corpus_payload(report)

    assert payload["selected_track"] == 3
    assert payload["corpus_file"] is None
    assert payload["match_packet"]["recommended_candidate"] == 1
    assert payload["match_packet"]["match_summary"]["synthetic_count"] == 4
    assert payload["safety"][0] == "passive read-only patch capture corpus"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        build_analog_four_patch_corpus_payload(report),
        sort_keys=True,
    )


def test_patch_corpus_cli_description_json_mode(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(
        [
            "analog-four-patch-corpus-report",
            "--description",
            "dark rolling techno with narrow pulse and HP2 filter",
            "--track",
            "2",
            "--limit",
            "2",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["selected_track"] == 2
    assert payload["match_packet"]["match_count"] == 2
    assert payload["match_packet"]["matches"][0]["selected_candidate"] == 1
    assert captured.err == ""


def test_patch_corpus_cli_description_text_mode(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(
        [
            "analog-four-patch-corpus-report",
            "--description",
            "dark rolling techno with narrow pulse and HP2 filter",
            "--track",
            "2",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Nearest corpus matches:" in captured.out
    assert "Selected track: 2" in captured.out
    assert captured.err == ""


def test_patch_corpus_cli_handler_formats_builder_errors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.analog_four_patch_corpus import (
        _handle_analog_four_patch_corpus_report,
    )

    exit_code = _handle_analog_four_patch_corpus_report(
        "--library",
        "reference-folder",
        track=1,
        limit=4,
        corpus_file=None,
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "source_flag must be --description or --audio" in captured.err
    assert captured.out == ""


def test_patch_corpus_report_rejects_corpus_file_without_entries_list(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.reports.analog_four_patch_corpus import (
        build_analog_four_patch_corpus_report,
    )

    corpus_file = tmp_path / "bad-corpus.json"
    corpus_file.write_text(json.dumps({"entries": {}}), encoding="utf-8")

    with pytest.raises(ValueError, match="entries list"):
        build_analog_four_patch_corpus_report(
            _feature_report(),
            source_label="description",
            source_value="manual feature report",
            track=1,
            limit=4,
            corpus_file=corpus_file,
        )


@pytest.mark.parametrize(
    "payload, expected",
    [
        ([], "corpus entry must be an object"),
        ({"feature_report": []}, "feature_report must be an object"),
        (
            {
                "entry_id": 1,
                "label": "Bad",
                "source_kind": "captured-hardware",
                "selected_candidate": 1,
                "feature_report": {},
            },
            "entry_id must be a string",
        ),
        (
            {
                "entry_id": "bad",
                "label": "Bad",
                "source_kind": "captured-hardware",
                "selected_candidate": "1",
                "feature_report": _valid_feature_payload(),
            },
            "selected_candidate must be an integer",
        ),
        (
            {
                "entry_id": "bad",
                "label": "Bad",
                "source_kind": "captured-hardware",
                "track": "1",
                "selected_candidate": 1,
                "feature_report": _valid_feature_payload(),
            },
            "track must be an integer",
        ),
        (
            {
                "entry_id": "bad",
                "label": "Bad",
                "source_kind": "captured-hardware",
                "selected_candidate": 1,
                "capture_notes": "not-list",
                "feature_report": _valid_feature_payload(),
            },
            "capture_notes must be a list",
        ),
        (
            {
                "entry_id": "bad",
                "label": "Bad",
                "source_kind": "captured-hardware",
                "selected_candidate": 1,
                "capture_notes": [1],
                "feature_report": _valid_feature_payload(),
            },
            "capture_notes entries must be strings",
        ),
    ],
)
def test_patch_corpus_report_rejects_malformed_entry_payloads(
    payload: object,
    expected: str,
) -> None:
    from rytm_randomizer.reports.analog_four_patch_corpus import (
        _corpus_entry_from_payload,
        _expect_mapping,
    )

    with pytest.raises(ValueError, match=expected):
        _corpus_entry_from_payload(_expect_mapping(payload, "corpus entry"), default_track=1)


@pytest.mark.parametrize(
    "override, expected",
    [
        ({"bpm": "fast"}, "bpm must be numeric"),
        ({"energy_arc": "flat"}, "energy_arc must be a list"),
        ({"energy_arc": ["loud"]}, "energy_arc entries must be numeric"),
        ({"content_hash": 123}, "content_hash must be a string"),
    ],
)
def test_patch_corpus_report_rejects_malformed_feature_payloads(
    override: dict[str, object],
    expected: str,
) -> None:
    from rytm_randomizer.reports.analog_four_patch_corpus import _feature_report_from_payload

    payload = _valid_feature_payload()
    payload.update(override)

    with pytest.raises(ValueError, match=expected):
        _feature_report_from_payload(payload)


@pytest.mark.parametrize(
    "args, expected",
    [
        ([], "requires exactly one source"),
        (["--description"], "--description requires a value"),
        (["--description", "x", "--track"], "--track requires a value"),
        (["--description", "x", "--limit"], "--limit requires a value"),
        (["--description", "x", "--corpus-file"], "--corpus-file requires a value"),
        (["--description", "x", "--limit", "NaN"], "--limit must be an integer"),
        (["--description", "x", "--track", "5"], "--track must be in 1..4"),
        (["--description", "x", "--unknown"], "unknown argument: --unknown"),
    ],
)
def test_patch_corpus_cli_rejects_specific_bad_arguments(
    args: list[str],
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["analog-four-patch-corpus-report", *args])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert expected in captured.err
    assert captured.out == ""
