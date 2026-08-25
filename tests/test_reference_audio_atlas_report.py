"""Tests for the passive reference-audio atlas report command."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from conftest import analog_four_reference_feature_report
from rytm_randomizer.reports import reference_audio_atlas as report_module
from rytm_randomizer.style_analysis.reference_audio_atlas import (
    ReferenceAudioAtlas,
    ReferenceAudioAtlasConfig,
    build_reference_audio_atlas,
)

pytestmark = pytest.mark.fast


def _atlas() -> ReferenceAudioAtlas:
    feature_report = analog_four_reference_feature_report(derived_at="2026-08-24T12:00:00Z")
    return build_reference_audio_atlas(
        Path("two-hour-reference.wav"),
        config=ReferenceAudioAtlasConfig(max_windows=1, max_moments=1),
        window_extractor=lambda _path, **_kwargs: feature_report,
        duration_reader=lambda _path: 7_200.0,
    )


def test_report_parser_builds_bounded_config_and_json_mode() -> None:
    parsed = report_module._parse_reference_audio_atlas_args(
        (
            "--audio",
            "mix.wav",
            "--window-seconds",
            "20",
            "--hop-seconds",
            "10",
            "--max-windows",
            "12",
            "--moments",
            "3",
            "--min-novelty",
            "0.2",
            "--track",
            "2",
            "--candidates",
            "3",
            "--json",
        )
    )

    config = parsed["config"]
    assert parsed["audio_path"] == "mix.wav"
    assert parsed["json_output"] is True
    assert isinstance(config, ReferenceAudioAtlasConfig)
    assert config.window_seconds == 20.0
    assert config.hop_seconds == 10.0
    assert config.max_windows == 12
    assert config.max_moments == 3
    assert config.min_novelty == 0.2
    assert config.track == 2
    assert config.candidate_count == 3


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ((), "requires --audio"),
        (("--audio",), "requires a value"),
        (("--unknown", "x"), "unknown argument"),
        (("--audio", "a", "--audio", "b"), "only once"),
        (("--audio", "a", "--moments", "many"), "must be an integer"),
        (("--audio", "a", "--window-seconds", "soon"), "must be numeric"),
        (("--audio", "a", "--min-novelty", "nan"), "must be finite"),
    ],
)
def test_report_parser_rejects_invalid_arguments(
    argv: tuple[str, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        report_module._parse_reference_audio_atlas_args(argv)


def test_text_report_is_chronological_and_states_scope() -> None:
    lines = report_module.format_reference_audio_atlas_report(_atlas())
    text = "\n".join(lines)

    assert report_module.REPORT_TITLE in text
    assert "02:00:00" in text
    assert "Moment 1: 00:00:00 to 00:00:30" in text
    assert "A4 candidate DNA:" in text
    assert "Rytm/A4 blueprint traits:" in text
    assert "not stem separation" in text


@pytest.mark.parametrize(
    "source_path",
    (
        r"C:\Users\Jose Buzzi\private\two-hour-reference.wav",
        "/home/jose/private/two-hour-reference.wav",
    ),
)
def test_text_report_uses_only_the_source_basename(source_path: str) -> None:
    atlas = replace(
        _atlas(),
        source_path=source_path,
    )

    text = "\n".join(report_module.format_reference_audio_atlas_report(atlas))

    assert "- Source: two-hour-reference.wav" in text
    assert "Jose Buzzi" not in text


def test_json_handler_emits_atlas_payload_without_hardware(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    atlas = _atlas()
    monkeypatch.setattr(report_module, "build_reference_audio_atlas", lambda *_a, **_k: atlas)

    result = report_module._handle_reference_audio_atlas_report(
        "mix.wav",
        ReferenceAudioAtlasConfig(),
        json_output=True,
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert result == 0
    assert captured.err == ""
    assert payload["analysis_id"] == atlas.analysis_id
    assert payload["moments"][0]["sequence"] == 1


def test_text_handler_emits_chronological_report_without_hardware(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    atlas = _atlas()
    monkeypatch.setattr(report_module, "build_reference_audio_atlas", lambda *_a, **_k: atlas)

    result = report_module._handle_reference_audio_atlas_report(
        "mix.wav",
        ReferenceAudioAtlasConfig(),
    )

    captured = capsys.readouterr()
    assert result == 0
    assert captured.err == ""
    assert report_module.REPORT_TITLE in captured.out
    assert "Moment 1: 00:00:00 to 00:00:30" in captured.out


def test_handler_reports_a_precise_passive_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(*_args: object, **_kwargs: object) -> ReferenceAudioAtlas:
        raise ValueError("audio is too short")

    monkeypatch.setattr(report_module, "build_reference_audio_atlas", fail)

    result = report_module._handle_reference_audio_atlas_report(
        "mix.wav",
        ReferenceAudioAtlasConfig(),
    )

    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert report_module.USAGE in captured.err
    assert "audio is too short" in captured.err


def test_report_formatter_requires_an_atlas() -> None:
    with pytest.raises(TypeError, match="atlas must be"):
        report_module.format_reference_audio_atlas_report(object())  # type: ignore[arg-type]
