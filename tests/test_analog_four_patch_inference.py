"""Tests for deterministic Analog Four audio-to-patch inference."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis import FeatureReport

pytestmark = pytest.mark.fast


def _reference_report(*, derived_at: str = "2026-07-16T12:00:00Z") -> FeatureReport:
    return FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=128.0,
        tempo_stability=0.94,
        kick_density=0.18,
        percussion_density=0.41,
        low_end_weight=0.48,
        spectral_brightness=0.52,
        texture_noise=0.21,
        energy_arc=(0.12, 0.82, 0.64, 0.48, 0.35, 0.24, 0.16, 0.08),
        content_hash="time-dependent-placeholder",
        derived_at=derived_at,
    )


def _features(
    *,
    audio_sha256: str = "a" * 64,
    duration: float = 0.38,
    attack: float = 0.05,
    decay: float = 0.32,
    sustain: float = 0.18,
    tail: float = 0.24,
    brightness: float = 0.58,
    spectral_flatness: float = 0.12,
    noise: float = 0.16,
    low_end: float = 0.44,
    harmonicity: float = 0.76,
    transient: float = 0.82,
    modulation: float = 0.22,
):
    from rytm_randomizer.style_analysis.analog_four_patch_inference import (
        AnalogFourPatchAudioFeatures,
    )

    return AnalogFourPatchAudioFeatures(
        audio_sha256=audio_sha256,
        duration=duration,
        attack=attack,
        decay=decay,
        sustain=sustain,
        tail=tail,
        brightness=brightness,
        spectral_flatness=spectral_flatness,
        noise=noise,
        low_end=low_end,
        harmonicity=harmonicity,
        transient=transient,
        modulation=modulation,
    )


def _gene(candidate, parameter: str):
    matches = [gene for gene in candidate.genes if gene.value.parameter == parameter]
    assert matches, f"Missing parameter {parameter}"
    return matches[0]


def _candidate_dna(audio_genome) -> tuple[tuple[tuple[str, int | None], ...], ...]:
    return tuple(
        tuple((gene.value.parameter, gene.value.midi_value) for gene in candidate.genes)
        for candidate in audio_genome.genome.candidates
    )


def test_audio_feature_analysis_hashes_exact_input_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    audio_path = tmp_path / "reference.wav"
    audio_bytes = b"RIFF-deterministic-audio-bytes"
    audio_path.write_bytes(audio_bytes)
    measured = inference._AnalogFourAudioMeasurements(
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
        transient=1.0,
        modulation=0.0,
    )
    monkeypatch.setattr(inference, "_measure_analog_four_patch_audio", lambda _path: measured)

    features = inference.analyze_analog_four_patch_audio(audio_path)

    assert features.audio_sha256 == hashlib.sha256(audio_bytes).hexdigest()
    assert features.duration == 0.5
    assert inference.analog_four_patch_audio_features_to_dict(features)["noise"] == 0.7


def test_audio_features_are_frozen_normalized_and_type_checked() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_inference import (
        AnalogFourPatchAudioFeatures,
        analog_four_audio_patch_genome_to_dict,
        analog_four_patch_audio_features_to_dict,
        analyze_analog_four_patch_audio,
    )

    features = _features()
    with pytest.raises(dataclasses.FrozenInstanceError):
        features.noise = 0.5  # type: ignore[misc]
    with pytest.raises(ValueError, match="64-character hexadecimal"):
        _features(audio_sha256="not-a-digest")
    with pytest.raises(ValueError, match="64-character hexadecimal"):
        _features(audio_sha256="z" * 64)
    with pytest.raises(ValueError, match="normalized"):
        _features(modulation=1.01)
    with pytest.raises(TypeError, match="path must be"):
        analyze_analog_four_patch_audio("sound.wav")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="features must be"):
        analog_four_patch_audio_features_to_dict(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="audio_genome must be"):
        analog_four_audio_patch_genome_to_dict(object())  # type: ignore[arg-type]
    assert isinstance(features, AnalogFourPatchAudioFeatures)


def test_audio_genome_is_stable_and_preserves_enum_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    timestamps = iter(("2026-07-16T12:00:00Z", "2026-07-16T12:00:01Z"))
    monkeypatch.setattr(inference, "analyze_analog_four_patch_audio", lambda _path: _features())
    monkeypatch.setattr(
        inference,
        "extract_from_audio",
        lambda _path: _reference_report(derived_at=next(timestamps)),
    )

    first = inference.build_analog_four_audio_patch_genome(Path("reference.wav"), track=2)
    second = inference.build_analog_four_audio_patch_genome(Path("reference.wav"), track=2)
    first_payload = inference.analog_four_audio_patch_genome_to_dict(first)
    second_payload = inference.analog_four_audio_patch_genome_to_dict(second)

    assert first_payload == second_payload
    assert first.feature_report.derived_at == "1970-01-01T00:00:00Z"
    assert first.genome.source_hash == "a" * 64
    assert first.genome.selected_track == 2
    assert [candidate.label for candidate in first.genome.candidates] == [
        "Closest reference",
        "Brighter sync",
        "Noisy texture",
        "Rounder bass",
    ]
    assert _gene(first.genome.candidates[0], "Filter2 Type").value.screen_value == "HP2"
    assert _gene(first.genome.candidates[0], "EnvA Env Shape").value.screen_value == ("triangle")
    assert _gene(first.genome.candidates[1], "Filter1 Frequency").value.midi_value > (
        _gene(first.genome.candidates[0], "Filter1 Frequency").value.midi_value
    )
    assert _gene(first.genome.candidates[2], "Noise Level").value.midi_value > 40
    assert _gene(first.genome.candidates[2], "LFO1 Depth A").value.midi_value > (
        _gene(first.genome.candidates[0], "LFO1 Depth A").value.midi_value
    )
    assert _gene(first.genome.candidates[3], "Filter1 Frequency").value.midi_value < (
        _gene(first.genome.candidates[0], "Filter1 Frequency").value.midi_value
    )
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )


def test_different_audio_profiles_produce_different_clamped_candidate_dna(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    profiles = iter(
        (
            _features(
                audio_sha256="1" * 64,
                brightness=0.08,
                noise=0.03,
                low_end=0.92,
                harmonicity=0.94,
                transient=0.12,
                modulation=0.04,
            ),
            _features(
                audio_sha256="2" * 64,
                attack=1.0,
                decay=1.0,
                sustain=1.0,
                tail=1.0,
                brightness=1.0,
                spectral_flatness=1.0,
                noise=1.0,
                low_end=0.0,
                harmonicity=0.0,
                transient=1.0,
                modulation=1.0,
            ),
        )
    )
    monkeypatch.setattr(
        inference,
        "analyze_analog_four_patch_audio",
        lambda _path: next(profiles),
    )
    monkeypatch.setattr(inference, "extract_from_audio", lambda _path: _reference_report())

    dark = inference.build_analog_four_audio_patch_genome(Path("dark.wav"))
    bright = inference.build_analog_four_audio_patch_genome(Path("bright.wav"))

    assert _candidate_dna(dark) != _candidate_dna(bright)
    assert dark.genome.source_hash != bright.genome.source_hash
    for candidate in bright.genome.candidates:
        for gene in candidate.genes:
            if gene.value.midi_value is not None:
                assert 0 <= gene.value.midi_value <= 127


def test_candidate_count_and_numeric_helpers_cover_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    monkeypatch.setattr(inference, "analyze_analog_four_patch_audio", lambda _path: _features())
    monkeypatch.setattr(inference, "extract_from_audio", lambda _path: _reference_report())

    result = inference.build_analog_four_audio_patch_genome(
        Path("two-columns.wav"),
        candidate_count=2,
    )

    assert result.genome.candidate_count == 2
    assert inference._unipolar(-1.0) == 0
    assert inference._unipolar(200.0) == 127
    assert inference._bipolar(-100.0) == -64
    assert inference._bipolar(100.0) == 63
    assert inference._clamp_audio_feature_unit(-1.0) == 0.0
    assert inference._clamp_audio_feature_unit(2.0) == 1.0
    assert inference._safe_ratio(1.0, 0.0) == 0.0
    assert inference._safe_ratio(1.0, 2.0) == 0.5
    assert inference._mean([]) == 0.0
    assert inference._mean([1.0, 3.0]) == 2.0
    assert inference._standard_deviation([], 0.0) == 0.0
    assert inference._standard_deviation([1.0, 3.0], 2.0) == 1.0
    assert inference._decay_frames([1.0, 0.2], 0, 1.0) == 1
    assert inference._decay_frames([1.0, 0.9], 0, 1.0) == 1
    assert inference._window_level([], 0.0, 0.4, 0.8) == 0.0
    assert inference._window_level([1.0, 0.5], 1.0, 0.4, 1.0) == 0.75
