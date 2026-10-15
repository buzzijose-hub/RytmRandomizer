"""Synthetic DSP, exact segment identity and optional boundary contracts."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import multiprocessing
import pickle
import sys
from pathlib import Path
from threading import Event

import numpy as np
import pytest
import soundfile as sf

from rytm_randomizer.style_analysis import analog_four_patch_inference as inference
from rytm_randomizer.style_analysis import reference_audio_diagnostics as diagnostics
from rytm_randomizer.style_analysis.extractor import AudioFeatureAnalysis, analyze_audio
from rytm_randomizer.style_analysis.reference_audio_diagnostics import (
    ReferenceAudioDiagnostics,
    ReferencePitchComparison,
    analyze_reference_audio_diagnostics,
    compare_reference_audio_diagnostics,
)
from rytm_randomizer.style_analysis.reference_sound_analysis import (
    ReferenceSoundAnalysisPayload,
    sound_analysis_from_dict,
    sound_analysis_to_dict,
)

pytestmark = pytest.mark.fast


def _write(path: Path, samples: np.ndarray, *, rate: int = 16000, subtype: str = "FLOAT") -> Path:
    sf.write(path, samples, rate, subtype=subtype)
    return path


def _tone(frequency: float, *, seconds: float = 0.8, amplitude: float = 0.4) -> np.ndarray:
    time = np.arange(round(seconds * 16000)) / 16000
    return amplitude * np.sin(2 * np.pi * frequency * time)


@pytest.fixture(scope="module")
def measured_tone(tmp_path_factory: pytest.TempPathFactory) -> ReferenceAudioDiagnostics:
    path = tmp_path_factory.mktemp("reference-diagnostics") / "tone.wav"
    return analyze_reference_audio_diagnostics(_write(path, _tone(220)))


def test_tone_has_qualified_f0_separate_peak_and_original_levels(
    measured_tone: ReferenceAudioDiagnostics,
) -> None:
    result = measured_tone
    assert result.pitch_status == "qualified"
    assert result.qualified_pitch_hz == pytest.approx(220, rel=0.01)
    assert result.spectral_peak_hz == pytest.approx(220, abs=4)
    assert result.rms == pytest.approx(0.4 / np.sqrt(2), abs=1e-7)
    assert result.peak == pytest.approx(0.4)
    assert result.clipped_fraction == 0
    assert result.pitch_confidence > 0.7
    assert result.voiced_fraction > 0.6
    assert result.pitch_stability_cents is not None and result.pitch_stability_cents < 35
    assert result.refinement_blockers == ()
    assert result.note_count == 1


@pytest.mark.parametrize("frequency", [5e-324, 31.999, 2000.001])
def test_qualified_pitch_rejects_values_outside_the_supported_dsp_domain(
    measured_tone: ReferenceAudioDiagnostics,
    frequency: float,
) -> None:
    with pytest.raises(ValueError, match="supported analyzer domain"):
        dataclasses.replace(measured_tone, qualified_pitch_hz=frequency)


@pytest.mark.parametrize("onsets", [1, 10**100])
def test_onset_counts_cannot_hide_multiple_note_evidence(
    measured_tone: ReferenceAudioDiagnostics,
    onsets: int,
) -> None:
    payload = measured_tone.to_dict()
    payload["onset_count"] = onsets
    with pytest.raises(ValueError, match="onsets|frame counts"):
        ReferenceAudioDiagnostics.from_dict(payload)


def test_unpitched_multiple_onsets_are_retained_but_cannot_drive_refinement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The DSP note/event estimate is independently policy-checked even for noise.
    monkeypatch.setattr(diagnostics, "_supported_onsets", lambda *_args: 1)
    samples = np.random.default_rng(711).normal(0, 0.12, 12800)
    result = analyze_reference_audio_diagnostics(_write(tmp_path / "noise-events.wav", samples))
    assert result.pitch_status == "unpitched" and result.qualified_pitch_hz is None
    assert result.multiple_pitch and result.note_count == 2
    assert "multiple_notes" in result.refinement_blockers
    assert compare_reference_audio_diagnostics(result, result).support_status == "held"


def test_actual_repeated_noise_hits_are_held_without_voiced_pitch_history(tmp_path: Path) -> None:
    noise = np.random.default_rng(714).normal(0, 0.12, 4800)
    samples = np.concatenate(
        (np.zeros(3200), noise, np.zeros(8000), noise, np.zeros(8000), noise, np.zeros(3200))
    )
    result = analyze_reference_audio_diagnostics(_write(tmp_path / "repeated-noise.wav", samples))
    assert result.pitch_status == "unpitched" and result.qualified_pitch_hz is None
    assert result.onset_count >= 1 and result.multiple_pitch and result.note_count >= 2
    assert "multiple_notes" in result.refinement_blockers
    assert compare_reference_audio_diagnostics(result, result).support_status == "held"


def test_insufficient_stable_pitch_frames_return_uncertainty_not_an_analysis_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import librosa

    frequencies = 440 * 2 ** (np.array([-40, -20, -10, 10, 20, 40]) / 1200)
    monkeypatch.setattr(
        librosa,
        "pyin",
        lambda *_args, **_kwargs: (frequencies, np.ones(6, dtype=bool), np.full(6, 0.9)),
    )
    result = analyze_reference_audio_diagnostics(
        _write(tmp_path / "marginal-pitch.wav", _tone(440, seconds=0.336))
    )
    assert result.pitch_status == "uncertain" and result.qualified_pitch_hz is None
    assert result.stable_pitch_frame_count == 4
    assert "pitch_uncertain" in result.refinement_blockers


def test_uncertain_multi_attack_measurement_is_retained_and_held(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import librosa

    monkeypatch.setattr(
        librosa,
        "pyin",
        lambda *_args, **_kwargs: (np.full(6, np.nan), np.zeros(6, dtype=bool), np.zeros(6)),
    )
    # The actual repeated-noise test covers onset detection; this covers the
    # independent uncertain-pitch policy path with one supported extra event.
    monkeypatch.setattr(diagnostics, "_supported_onsets", lambda *_args: 1)
    result = analyze_reference_audio_diagnostics(
        _write(tmp_path / "uncertain-attacks.wav", _tone(440, seconds=0.336))
    )
    assert result.pitch_status == "uncertain" and result.multiple_pitch
    assert result.onset_count == 1 and result.note_count == 2
    assert set(result.refinement_blockers) >= {"pitch_uncertain", "multiple_notes"}


@pytest.mark.parametrize("status", ["qualified", "unpitched", "uncertain", "bad"])
def test_pitch_literal_parser_is_closed(status: str) -> None:
    if status == "bad":
        with pytest.raises(ValueError, match="unknown"):
            diagnostics.narrow_reference_pitch_status(status)
    else:
        assert diagnostics.narrow_reference_pitch_status(status) == status


@pytest.mark.parametrize("status", ["supported", "unpitched", "held", "bad"])
def test_pitch_support_literal_parser_is_closed(status: str) -> None:
    if status == "bad":
        with pytest.raises(ValueError, match="unknown"):
            diagnostics.narrow_reference_pitch_support_status(status)
    else:
        assert diagnostics.narrow_reference_pitch_support_status(status) == status


@pytest.mark.parametrize("delta", [-1e308, 1e308, 8000.0])
def test_forged_pitch_deltas_are_refused_before_arithmetic(delta: float) -> None:
    with pytest.raises(ValueError, match="supported analyzer domain"):
        ReferencePitchComparison(delta, 0, "held", ("pitch_mismatch",))


def test_strong_second_harmonic_does_not_become_fundamental(tmp_path: Path) -> None:
    samples = _tone(220, amplitude=0.12) + _tone(440, amplitude=0.5) + _tone(660, amplitude=0.15)
    result = analyze_reference_audio_diagnostics(_write(tmp_path / "harmonics.wav", samples))
    assert result.qualified_pitch_hz == pytest.approx(220, rel=0.01)
    assert result.spectral_peak_hz == pytest.approx(440, abs=4)
    assert "spectral_peak_is_harmonic" in result.warnings
    assert not result.octave_ambiguous
    assert result.refinement_blockers == ()


def test_pure_harmonic_only_is_observable_periodicity_not_missing_lower_f0(tmp_path: Path) -> None:
    result = analyze_reference_audio_diagnostics(_write(tmp_path / "pure.wav", _tone(440)))
    assert result.qualified_pitch_hz == pytest.approx(440, rel=0.01)
    assert result.qualified_pitch_hz != pytest.approx(220, rel=0.01)


def test_clean_noise_is_unpitched_and_allows_unpitched_comparison(tmp_path: Path) -> None:
    samples = np.random.default_rng(711).normal(0, 0.12, 12800)
    result = analyze_reference_audio_diagnostics(_write(tmp_path / "noise.wav", samples))
    assert result.pitch_status == "unpitched"
    assert result.qualified_pitch_hz is None
    assert result.refinement_blockers == ()
    comparison = compare_reference_audio_diagnostics(result, result)
    assert comparison.support_status == "unpitched"
    assert comparison.delta_cents is None
    assert comparison.blockers == ()


@pytest.mark.parametrize("kind", ["quiet", "silence", "clipped", "stereo-cancellation"])
def test_original_pcm_quality_is_not_hidden_by_normalization(tmp_path: Path, kind: str) -> None:
    samples = _tone(220)
    if kind == "quiet":
        samples *= 0.0001
    elif kind == "silence":
        samples *= 0
    elif kind == "clipped":
        samples = np.clip(samples * 5, -1, 1)
    else:
        samples = np.column_stack((samples, -samples))
    path = _write(tmp_path / f"{kind}.wav", samples, subtype="PCM_16")
    original, _ = sf.read(path, always_2d=True)
    result = analyze_reference_audio_diagnostics(path)
    assert result.rms == pytest.approx(float(np.sqrt(np.mean(original**2))))
    assert result.peak == pytest.approx(float(np.max(np.abs(original))))
    assert result.refinement_blockers
    assert compare_reference_audio_diagnostics(result, result).support_status == "held"
    if kind == "clipped":
        assert result.clipped_fraction > 0.5
        assert "clipped_audio" in result.refinement_blockers
    elif kind == "stereo-cancellation":
        assert "channel_cancellation" in result.refinement_blockers
    else:
        assert "quiet_audio" in result.refinement_blockers


def test_multiple_octave_notes_are_uncertain_not_one_pitch(tmp_path: Path) -> None:
    samples = np.concatenate((_tone(110), np.zeros(3200), _tone(220), np.zeros(3200), _tone(440)))
    result = analyze_reference_audio_diagnostics(_write(tmp_path / "notes.wav", samples))
    assert result.multiple_pitch and result.octave_ambiguous
    assert result.note_count is not None and result.note_count >= 3
    assert result.qualified_pitch_hz is None
    assert "multiple_notes" in result.refinement_blockers


def test_short_segment_has_valid_quality_but_no_pitch_guess(tmp_path: Path) -> None:
    result = analyze_reference_audio_diagnostics(
        _write(tmp_path / "short.wav", _tone(220, seconds=0.1))
    )
    assert result.pitch_status == "uncertain"
    assert result.qualified_pitch_hz is None
    assert result.spectral_peak_hz == pytest.approx(220, abs=10)
    assert result.rms > 0.1
    assert result.refinement_blockers == ("insufficient_pitch_frames",)


def test_exact_segment_identity_and_endpoint_refusal(tmp_path: Path) -> None:
    path = _write(tmp_path / "long.wav", np.tile(_tone(220, seconds=1), 9))
    original_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="PCM bounds"):
        analyze_reference_audio_diagnostics(path)
    first = analyze_reference_audio_diagnostics(path, sample_count=128000)
    later = analyze_reference_audio_diagnostics(path, start_sample=16000, sample_count=128000)
    assert first.audio_sha256 == later.audio_sha256 == original_hash
    assert first.pcm_sha256 == later.pcm_sha256
    assert first.start_sample == 0 and later.start_sample == 16000
    assert first.sample_count == 128000
    changed = analyze_reference_audio_diagnostics(path, start_sample=1, sample_count=16000)
    assert changed.pcm_sha256 != first.pcm_sha256
    assert hashlib.sha256(path.read_bytes()).hexdigest() == original_hash
    with pytest.raises(ValueError):
        analyze_reference_audio_diagnostics(path, sample_count=128001)
    with pytest.raises(ValueError):
        analyze_reference_audio_diagnostics(path, start_sample=100000, sample_count=50000)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"start_sample": True},
        {"start_sample": -1},
        {"sample_count": 0},
        {"sample_count": 1.2},
        {"sample_count": True},
    ],
)
def test_segment_requires_strict_integer_bounds(tmp_path: Path, kwargs: dict[str, object]) -> None:
    path = _write(tmp_path / "input.wav", _tone(220))
    with pytest.raises(ValueError):
        analyze_reference_audio_diagnostics(path, **kwargs)  # type: ignore[arg-type]


def test_serialization_is_strict_detached_frozen_and_pickle_safe(
    measured_tone: ReferenceAudioDiagnostics,
) -> None:
    payload = measured_tone.to_dict()
    assert (
        ReferenceAudioDiagnostics.from_dict(json.loads(json.dumps(payload, allow_nan=False)))
        == measured_tone
    )
    assert pickle.loads(pickle.dumps(measured_tone)) == measured_tone  # noqa: S301 - own DTO bytes
    payload["warnings"].append("quiet_audio")
    assert measured_tone.warnings == ()
    with pytest.raises(dataclasses.FrozenInstanceError):
        measured_tone.rms = 0  # type: ignore[misc]


@pytest.mark.parametrize(
    "field,value",
    [
        ("audio_sha256", "f" * 63),
        ("pcm_sha256", "G" * 64),
        ("sample_rate", True),
        ("sample_rate", 7999),
        ("channels", 3),
        ("start_sample", -1),
        ("sample_count", 128001),
        ("rms", True),
        ("rms", "0.1"),
        ("rms", float("nan")),
        ("rms", float("inf")),
        ("rms", 2),
        ("peak", -1),
        ("clipped_fraction", 2),
        ("pitch_confidence", -0.1),
        ("voiced_fraction", 2),
        ("qualified_pitch_hz", 0),
        ("spectral_peak_hz", 9000),
        ("pitch_stability_cents", -1),
        ("pitch_status", "guess"),
        ("pitch_status", "unpitched"),
        ("pitch_method", "fft"),
        ("octave_ambiguous", 0),
        ("multiple_pitch", "false"),
        ("frame_count", 502),
        ("stable_pitch_frame_count", 501),
        ("note_count", True),
        ("note_count", 1000),
        ("warnings", ["unknown"]),
        ("warnings", ["quiet_audio"] * 2),
        ("warnings", ()),
        ("refinement_blockers", ["quiet_audio"]),
    ],
)
def test_diagnostic_validator_rejects_invalid_fields(
    measured_tone: ReferenceAudioDiagnostics, field: str, value: object
) -> None:
    payload: dict[str, object] = dict(measured_tone.to_dict())
    payload[field] = value
    with pytest.raises(ValueError):
        ReferenceAudioDiagnostics.from_dict(payload)


def test_validator_rejects_extra_and_missing_keys(measured_tone: ReferenceAudioDiagnostics) -> None:
    payload = dict(measured_tone.to_dict())
    with pytest.raises(ValueError):
        ReferenceAudioDiagnostics.from_dict({**payload, "extra": 1})
    del payload["rms"]
    with pytest.raises(ValueError):
        ReferenceAudioDiagnostics.from_dict(payload)


def test_comparison_delta_octaves_and_missing_support(
    measured_tone: ReferenceAudioDiagnostics,
) -> None:
    higher = dataclasses.replace(measured_tone, qualified_pitch_hz=measured_tone.qualified_pitch_hz * 2)  # type: ignore[operator]
    comparison = compare_reference_audio_diagnostics(measured_tone, higher)
    assert comparison.to_dict() == {
        "delta_cents": 1200.0,
        "octave_difference": 1,
        "support_status": "held",
        "blockers": ["pitch_mismatch"],
    }
    assert compare_reference_audio_diagnostics(higher, measured_tone).octave_difference == -1
    assert (
        compare_reference_audio_diagnostics(measured_tone, measured_tone).support_status
        == "supported"
    )
    assert compare_reference_audio_diagnostics(None, measured_tone).blockers == (
        "diagnostics_missing",
    )
    semitone = dataclasses.replace(measured_tone, qualified_pitch_hz=measured_tone.qualified_pitch_hz * 2 ** (2 / 12))  # type: ignore[operator]
    assert compare_reference_audio_diagnostics(measured_tone, semitone).octave_difference == 0


@pytest.mark.parametrize("cents", [-100.1, -99.9, 99.9, 100.1])
def test_pitch_mismatch_hold_pins_both_sides_of_the_one_semitone_boundary(
    measured_tone: ReferenceAudioDiagnostics, cents: float
) -> None:
    assert measured_tone.qualified_pitch_hz is not None
    recording = dataclasses.replace(
        measured_tone, qualified_pitch_hz=measured_tone.qualified_pitch_hz * 2 ** (cents / 1200)
    )
    comparison = compare_reference_audio_diagnostics(measured_tone, recording)
    held = abs(cents) > 100
    assert comparison.delta_cents == pytest.approx(cents, abs=1e-8)
    assert comparison.octave_difference == 0
    assert comparison.support_status == ("held" if held else "supported")
    assert comparison.blockers == (("pitch_mismatch",) if held else ())


@pytest.mark.parametrize(
    "payload",
    [
        {
            "delta_cents": None,
            "octave_difference": None,
            "support_status": "held",
            "blockers": ["diagnostics_missing"],
        },
        {
            "delta_cents": 1200,
            "octave_difference": 1,
            "support_status": "held",
            "blockers": ["pitch_mismatch"],
        },
        {"delta_cents": 0, "octave_difference": 0, "support_status": "supported", "blockers": []},
        {
            "delta_cents": None,
            "octave_difference": None,
            "support_status": "unpitched",
            "blockers": [],
        },
    ],
)
def test_comparison_payload_validates_without_audio_authority(payload: dict[str, object]) -> None:
    comparison = ReferencePitchComparison.from_dict(payload)
    assert comparison.to_dict() == payload
    assert (
        ReferencePitchComparison.from_dict(json.loads(json.dumps(comparison.to_dict())))
        == comparison
    )


@pytest.mark.parametrize(
    "change",
    [
        {"support_status": "guess"},
        {"support_status": "supported"},
        {"blockers": []},
        {"blockers": ["unknown"]},
        {"blockers": ["quiet_audio", "quiet_audio"]},
        {"blockers": ()},
        {"delta_cents": True},
        {"delta_cents": float("nan")},
        {"delta_cents": 10**1000},
        {"octave_difference": True},
        {"octave_difference": 2},
        {"octave_difference": None},
        {"support_status": "unpitched"},
        {"delta_cents": None},
        {"extra": 1},
    ],
)
def test_comparison_rejects_inconsistent_and_unbounded_payload(change: dict[str, object]) -> None:
    payload = {
        "delta_cents": 1200,
        "octave_difference": 1,
        "support_status": "held",
        "blockers": ["pitch_mismatch"],
    }
    with pytest.raises(ValueError):
        ReferencePitchComparison.from_dict({**payload, **change})


@pytest.mark.parametrize(
    "change",
    [
        {"rms": 0.0001},
        {"clipped_fraction": 0.01},
        {"multiple_pitch": True},
        {"octave_ambiguous": True},
        {"pitch_confidence": 0.2},
        {"voiced_fraction": 0.1},
        {"pitch_stability_cents": None},
        {"pitch_stability_cents": 100},
        {"stable_pitch_frame_count": 1},
        {"note_count": 2},
    ],
)
def test_stats_cannot_forge_empty_refinement_blockers(
    measured_tone: ReferenceAudioDiagnostics, change: dict[str, object]
) -> None:
    with pytest.raises(ValueError):
        ReferenceAudioDiagnostics.from_dict({**measured_tone.to_dict(), **change})


def test_compare_uncertain_and_pitch_support_mismatch(
    measured_tone: ReferenceAudioDiagnostics,
) -> None:
    uncertain = dataclasses.replace(
        measured_tone,
        qualified_pitch_hz=None,
        pitch_status="uncertain",
        warnings=("pitch_uncertain",),
        refinement_blockers=("pitch_uncertain",),
    )
    unpitched = dataclasses.replace(
        measured_tone,
        qualified_pitch_hz=None,
        pitch_status="unpitched",
        pitch_confidence=0.01,
        voiced_fraction=0,
        stable_pitch_frame_count=0,
        pitch_stability_cents=None,
        note_count=0,
    )
    assert compare_reference_audio_diagnostics(uncertain, uncertain).support_status == "held"
    assert compare_reference_audio_diagnostics(measured_tone, unpitched).blockers == (
        "pitch_support_mismatch",
    )
    quiet_noise = dataclasses.replace(
        unpitched, rms=0.0001, warnings=("quiet_audio",), refinement_blockers=("quiet_audio",)
    )
    assert compare_reference_audio_diagnostics(quiet_noise, quiet_noise).support_status == "held"
    with pytest.raises(TypeError):
        compare_reference_audio_diagnostics(measured_tone, object())  # type: ignore[arg-type]


def test_one_attack_and_release_are_not_multiple_notes(tmp_path: Path) -> None:
    samples = _tone(220, seconds=2)
    envelope = np.minimum(np.arange(len(samples)) / 1600, 1) * np.minimum(
        np.arange(len(samples))[::-1] / 1600, 1
    )
    result = analyze_reference_audio_diagnostics(
        _write(tmp_path / "single-note.wav", samples * envelope)
    )
    assert not result.multiple_pitch
    assert "multiple_notes" not in result.refinement_blockers
    assert result.qualified_pitch_hz == pytest.approx(220, rel=0.01)


def test_repeated_same_pitch_has_multiple_attack_evidence(tmp_path: Path) -> None:
    samples = np.concatenate((_tone(220), np.zeros(3200), _tone(220)))
    result = analyze_reference_audio_diagnostics(_write(tmp_path / "retrigger.wav", samples))
    assert result.multiple_pitch
    assert result.note_count is not None and result.note_count > 1
    assert "multiple_notes" in result.refinement_blockers


def test_dc_dominated_segment_keeps_uncertainty(tmp_path: Path) -> None:
    result = analyze_reference_audio_diagnostics(
        _write(tmp_path / "dc-tone.wav", 0.5 + _tone(220, amplitude=0.2))
    )
    assert result.spectral_peak_hz is None
    assert result.qualified_pitch_hz is None
    assert "pitch_uncertain" in result.refinement_blockers


def test_pitch_qualifier_does_not_depend_on_spectral_peak(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(diagnostics, "_spectral_peak", lambda _mono, _rate: None)
    result = analyze_reference_audio_diagnostics(_write(tmp_path / "independent.wav", _tone(220)))
    assert result.spectral_peak_hz is None
    assert result.qualified_pitch_hz == pytest.approx(220, rel=0.01)


def test_constructor_rejects_mutable_codes_and_inconsistent_unpitched_stats(
    measured_tone: ReferenceAudioDiagnostics,
) -> None:
    with pytest.raises(ValueError):
        dataclasses.replace(measured_tone, warnings=[])  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        dataclasses.replace(measured_tone, qualified_pitch_hz=None, pitch_status="unpitched")
    with pytest.raises(ValueError):
        ReferencePitchComparison(0, 0, "unpitched", ())


def test_file_and_decoder_bounds_precede_dsp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    with pytest.raises(TypeError):
        analyze_reference_audio_diagnostics("not-path")  # type: ignore[arg-type]
    empty = tmp_path / "empty.wav"
    empty.touch()
    with pytest.raises(ValueError):
        analyze_reference_audio_diagnostics(empty)
    with (tmp_path / "large.wav").open("wb") as stream:
        stream.truncate(16 * 1024 * 1024 + 1)
    with pytest.raises(ValueError):
        analyze_reference_audio_diagnostics(tmp_path / "large.wav")
    path = _write(tmp_path / "small.wav", _tone(220))
    actual_import = diagnostics.importlib.import_module
    for info in (
        SimpleNamespace(frames=12800, samplerate=1000, channels=1),
        SimpleNamespace(frames=12800, samplerate=16000, channels=3),
    ):
        monkeypatch.setattr(
            diagnostics.importlib,
            "import_module",
            lambda name, info=info: (
                SimpleNamespace(info=lambda _source: info)
                if name == "soundfile"
                else actual_import(name)
            ),
        )
        with pytest.raises(ValueError):
            analyze_reference_audio_diagnostics(path)
    for pcm, rate in (
        (np.full((12800, 1), np.nan), 16000),
        (np.zeros((1, 1)), 16000),
        (np.zeros((12800, 1)), 8000),
    ):
        api = SimpleNamespace(
            info=lambda _source: SimpleNamespace(frames=12800, samplerate=16000, channels=1),
            read=lambda *_args, pcm=pcm, rate=rate, **_kwargs: (pcm, rate),
        )
        monkeypatch.setattr(
            diagnostics.importlib,
            "import_module",
            lambda name, api=api: api if name == "soundfile" else actual_import(name),
        )
        with pytest.raises(ValueError):
            analyze_reference_audio_diagnostics(path)


def test_optional_persistence_keeps_legacy_keys_exact_and_report_identity_unchanged(
    audio_patch_dna_analysis: AudioFeatureAnalysis, measured_tone: ReferenceAudioDiagnostics
) -> None:
    legacy = sound_analysis_to_dict(audio_patch_dna_analysis)
    assert set(legacy) == {"report", "features", "evidence"}
    assert ReferenceSoundAnalysisPayload.__required_keys__ == frozenset(legacy)
    assert ReferenceSoundAnalysisPayload.__optional_keys__ == frozenset({"diagnostics"})
    assert sound_analysis_to_dict(sound_analysis_from_dict(legacy)) == legacy
    matching = dataclasses.replace(
        measured_tone, audio_sha256=audio_patch_dna_analysis.audio_sha256
    )
    enriched = dataclasses.replace(audio_patch_dna_analysis, diagnostics=matching)
    payload = sound_analysis_to_dict(enriched)
    assert sound_analysis_from_dict(payload) == enriched
    assert {key: value for key, value in payload.items() if key != "diagnostics"} == legacy
    assert inference.build_analog_four_audio_patch_genome_from_analysis(enriched) == (
        inference.build_analog_four_audio_patch_genome_from_analysis(audio_patch_dna_analysis)
    )
    payload["diagnostics"]["rms"] = float("nan")
    with pytest.raises(ValueError):
        sound_analysis_from_dict(payload)


def test_legacy_longform_analyzer_remains_optional(tmp_path: Path) -> None:
    path = _write(tmp_path / "long.wav", _tone(220, seconds=8.1))
    analysis = analyze_audio(path)
    assert analysis.diagnostics is None
    assert "diagnostics" not in sound_analysis_to_dict(analysis)


def test_worker_attaches_after_analysis_on_same_path_and_failure_is_categorical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    audio_patch_dna_analysis: AudioFeatureAnalysis,
    measured_tone: ReferenceAudioDiagnostics,
) -> None:
    path = _write(tmp_path / "worker.wav", _tone(220))
    audio_patch_dna_analysis = _identified_analysis(audio_patch_dna_analysis, path)
    measured_tone = dataclasses.replace(
        measured_tone, audio_sha256=audio_patch_dna_analysis.audio_sha256
    )
    calls: list[tuple[str, Path]] = []
    monkeypatch.setattr(inference, "_configure_native_audio_worker", lambda _cache: None)

    def analyze(source: Path) -> AudioFeatureAnalysis:
        calls.append(("analyze", source))
        return audio_patch_dna_analysis

    def measure(source: Path) -> ReferenceAudioDiagnostics:
        calls.append(("diagnostics", source))
        return measured_tone

    monkeypatch.setattr(inference, "analyze_audio_snapshot", analyze)
    monkeypatch.setattr(inference, "analyze_reference_audio_diagnostics", measure)
    receiver, sender = multiprocessing.Pipe(duplex=False)
    inference._native_audio_analysis_worker(str(path), sender)
    result = receiver.recv()
    receiver.close()
    assert calls == [("analyze", path), ("diagnostics", path)]
    assert result.analysis == dataclasses.replace(
        audio_patch_dna_analysis, diagnostics=measured_tone
    )
    assert sender.closed

    def fail(_source: Path) -> ReferenceAudioDiagnostics:
        raise ValueError("private/source/path")

    monkeypatch.setattr(inference, "analyze_reference_audio_diagnostics", fail)
    receiver, sender = multiprocessing.Pipe(duplex=False)
    inference._native_audio_analysis_worker(str(path), sender)
    failure = receiver.recv().failure
    receiver.close()
    assert failure.error_code == "validation"
    assert "private" not in failure.message
    assert sender.closed


def _identified_analysis(analysis: AudioFeatureAnalysis, path: Path) -> AudioFeatureAnalysis:
    return dataclasses.replace(
        analysis,
        synthesis_features=dataclasses.replace(
            analysis.synthesis_features, audio_sha256=hashlib.sha256(path.read_bytes()).hexdigest()
        ),
    )


def test_accepted_long_worker_analysis_never_calls_bounded_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, audio_patch_dna_analysis: AudioFeatureAnalysis
) -> None:
    path = _write(tmp_path / "accepted-long.wav", _tone(220, seconds=9))
    expected = _identified_analysis(audio_patch_dna_analysis, path)
    # Simulate an older/extended caller's already accepted long-form input,
    # independently of this checkout's existing eight-second input perimeter.
    monkeypatch.setattr(inference, "_validate_native_audio_input", lambda _path: None)
    monkeypatch.setattr(inference, "_configure_native_audio_worker", lambda _cache: None)
    monkeypatch.setattr(inference, "analyze_audio_snapshot", lambda _path: expected)

    def never(_path: Path) -> ReferenceAudioDiagnostics:
        pytest.fail("bounded diagnostics ran on a long-form analysis")

    monkeypatch.setattr(inference, "analyze_reference_audio_diagnostics", never)
    receiver, sender = multiprocessing.Pipe(duplex=False)
    inference._native_audio_analysis_worker(str(path), sender)
    message = receiver.recv()
    receiver.close()
    assert message.failure is None and message.analysis == expected
    assert message.analysis.diagnostics is None
    assert sender.closed


@pytest.mark.parametrize("mutation", ["before", "during", "wrong-identity", "oversized"])
def test_worker_refuses_identity_races_without_partial_analysis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    audio_patch_dna_analysis: AudioFeatureAnalysis,
    measured_tone: ReferenceAudioDiagnostics,
    mutation: str,
) -> None:
    path = _write(tmp_path / "raced.wav", _tone(220))
    expected = _identified_analysis(audio_patch_dna_analysis, path)
    matching = dataclasses.replace(measured_tone, audio_sha256=expected.audio_sha256)
    monkeypatch.setattr(inference, "_configure_native_audio_worker", lambda _cache: None)

    def analyze(_path: Path) -> AudioFeatureAnalysis:
        if mutation == "before":
            _write(path, _tone(440))
        if mutation == "oversized":
            with path.open("wb") as stream:
                stream.truncate(16 * 1024 * 1024 + 1)
        return expected

    def measure(_path: Path) -> ReferenceAudioDiagnostics:
        if mutation == "during":
            _write(path, _tone(440))
        return (
            dataclasses.replace(matching, audio_sha256="b" * 64)
            if mutation == "wrong-identity"
            else matching
        )

    monkeypatch.setattr(inference, "analyze_audio_snapshot", analyze)
    monkeypatch.setattr(inference, "analyze_reference_audio_diagnostics", measure)
    receiver, sender = multiprocessing.Pipe(duplex=False)
    inference._native_audio_analysis_worker(str(path), sender)
    message = receiver.recv()
    receiver.close()
    assert message.analysis is None and message.failure.error_code == "validation"
    assert "raced" not in message.failure.message
    assert sender.closed


def test_serialization_rejects_cross_audio_diagnostics_and_malformed_energy_arc(
    audio_patch_dna_analysis: AudioFeatureAnalysis, measured_tone: ReferenceAudioDiagnostics
) -> None:
    wrong = measured_tone
    assert wrong.audio_sha256 != audio_patch_dna_analysis.audio_sha256
    with pytest.raises(ValueError, match="identity"):
        sound_analysis_to_dict(dataclasses.replace(audio_patch_dna_analysis, diagnostics=wrong))
    payload = sound_analysis_to_dict(audio_patch_dna_analysis)
    payload["diagnostics"] = wrong.to_dict()
    with pytest.raises(ValueError, match="identity"):
        sound_analysis_from_dict(payload)
    del payload["diagnostics"]
    for bad_arc in ((), [0] * 33):
        payload["report"]["energy_arc"] = bad_arc  # type: ignore[typeddict-item]
        with pytest.raises(ValueError):
            sound_analysis_from_dict(payload)


def test_one_delayed_initial_onset_is_not_a_second_note(tmp_path: Path) -> None:
    samples = np.concatenate((np.zeros(12800), _tone(220, seconds=2), np.zeros(3200)))
    result = analyze_reference_audio_diagnostics(_write(tmp_path / "delayed.wav", samples))
    assert not result.multiple_pitch
    assert result.note_count == 1
    assert "multiple_notes" not in result.refinement_blockers


def test_precancelled_worker_never_computes_or_publishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from rytm_randomizer.observability.errors import BoundaryError

    cancel = Event()
    cancel.set()

    def never(_source: Path) -> ReferenceAudioDiagnostics:
        pytest.fail("diagnostics computed for cancelled work")

    monkeypatch.setattr(inference, "analyze_reference_audio_diagnostics", never)
    with pytest.raises(BoundaryError) as error:
        inference.analyze_analog_four_patch_audio_analysis_isolated(
            tmp_path / "absent.wav", cancel=cancel
        )
    assert error.value.context["error_code"] == "interrupted"
    assert "mido" not in sys.modules and "rtmidi" not in sys.modules
