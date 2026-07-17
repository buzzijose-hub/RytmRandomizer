"""Deterministic audio-dependent Analog Four patch candidate inference."""

from __future__ import annotations

import hashlib
import string
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final, Protocol, cast

from ..data.analog_four_display import make_a4_patch_value
from .analog_four_patch_genome import (
    AnalogFourPatchCandidate,
    AnalogFourPatchGene,
    AnalogFourPatchGenome,
    analog_four_patch_genome_to_dict,
    build_analog_four_patch_genome,
)
from .extractor import StyleAnalysisDependencyError, extract_from_audio
from .feature_report import FeatureReport, compute_feature_report_hash

_AUDIO_REPORT_DERIVED_AT: Final[str] = "1970-01-01T00:00:00Z"
_AUDIO_SAMPLE_RATE: Final[int] = 22_050
_AUDIO_FRAME_LENGTH: Final[int] = 2_048
_AUDIO_HOP_LENGTH: Final[int] = 512


class _ArrayResult(Protocol):  # pragma: no cover - typing-only optional dependency API
    def reshape(self, *shape: int) -> _ArrayResult: ...

    def tolist(self) -> object: ...


class _NumpyApi(Protocol):  # pragma: no cover - typing-only optional dependency API
    def abs(self, value: object) -> object: ...

    def asarray(self, value: object) -> _ArrayResult: ...


class _FeatureApi(Protocol):  # pragma: no cover - typing-only optional dependency API
    def rms(
        self,
        *,
        y: object,
        frame_length: int,
        hop_length: int,
    ) -> object: ...

    def spectral_centroid(self, *, y: object, sr: int) -> object: ...

    def spectral_flatness(self, *, y: object) -> object: ...

    def zero_crossing_rate(self, y: object) -> object: ...


class _OnsetApi(Protocol):  # pragma: no cover - typing-only optional dependency API
    def onset_strength(self, *, y: object, sr: int) -> object: ...


class _EffectsApi(Protocol):  # pragma: no cover - typing-only optional dependency API
    def harmonic(self, y: object) -> object: ...


class _LibrosaApi(Protocol):  # pragma: no cover - typing-only optional dependency API
    feature: _FeatureApi
    onset: _OnsetApi
    effects: _EffectsApi

    def load(self, path: str, *, sr: int, mono: bool) -> tuple[object, int]: ...

    def stft(self, y: object, *, n_fft: int, hop_length: int) -> object: ...

    def fft_frequencies(self, *, sr: int, n_fft: int) -> object: ...


@dataclass(frozen=True)
class AnalogFourPatchAudioFeatures:
    """Normalized synthesis evidence measured from one audio file."""

    audio_sha256: str
    duration: float
    attack: float
    decay: float
    sustain: float
    tail: float
    brightness: float
    spectral_flatness: float
    noise: float
    low_end: float
    harmonicity: float
    transient: float
    modulation: float

    def __post_init__(self) -> None:
        if (
            not isinstance(self.audio_sha256, str)
            or len(self.audio_sha256) != 64
            or any(character not in string.hexdigits for character in self.audio_sha256)
        ):
            raise ValueError("audio_sha256 must be a 64-character hexadecimal digest")
        normalized_values = (
            self.duration,
            self.attack,
            self.decay,
            self.sustain,
            self.tail,
            self.brightness,
            self.spectral_flatness,
            self.noise,
            self.low_end,
            self.harmonicity,
            self.transient,
            self.modulation,
        )
        if any(not 0.0 <= value <= 1.0 for value in normalized_values):
            raise ValueError("audio feature values must be normalized to 0.0..1.0")


@dataclass(frozen=True)
class AnalogFourAudioPatchGenome:
    """Measured audio evidence and its inferred Analog Four patch genome."""

    feature_report: FeatureReport
    audio_features: AnalogFourPatchAudioFeatures
    genome: AnalogFourPatchGenome


@dataclass(frozen=True)
class _AnalogFourAudioMeasurements:
    duration: float
    attack: float
    decay: float
    sustain: float
    tail: float
    brightness: float
    spectral_flatness: float
    noise: float
    low_end: float
    harmonicity: float
    transient: float
    modulation: float


def analyze_analog_four_patch_audio(path: Path) -> AnalogFourPatchAudioFeatures:
    """Measure normalized A4 synthesis evidence from ``path``."""

    if not isinstance(path, Path):
        raise TypeError("path must be a pathlib.Path")
    audio_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    measurements = _measure_analog_four_patch_audio(path)
    return AnalogFourPatchAudioFeatures(
        audio_sha256=audio_sha256,
        duration=measurements.duration,
        attack=measurements.attack,
        decay=measurements.decay,
        sustain=measurements.sustain,
        tail=measurements.tail,
        brightness=measurements.brightness,
        spectral_flatness=measurements.spectral_flatness,
        noise=measurements.noise,
        low_end=measurements.low_end,
        harmonicity=measurements.harmonicity,
        transient=measurements.transient,
        modulation=measurements.modulation,
    )


def build_analog_four_audio_patch_genome(
    path: Path,
    *,
    track: int = 1,
    candidate_count: int = 4,
) -> AnalogFourAudioPatchGenome:
    """Infer deterministic audio-dependent A4 candidates from ``path``."""

    audio_features = analyze_analog_four_patch_audio(path)
    feature_report = _stable_audio_feature_report(extract_from_audio(path))
    static_genome = build_analog_four_patch_genome(
        feature_report,
        track=track,
        candidate_count=candidate_count,
    )
    genome = replace(
        static_genome,
        source_hash=audio_features.audio_sha256,
        candidates=tuple(
            _infer_candidate(candidate, audio_features) for candidate in static_genome.candidates
        ),
    )
    return AnalogFourAudioPatchGenome(
        feature_report=feature_report,
        audio_features=audio_features,
        genome=genome,
    )


def analog_four_patch_audio_features_to_dict(
    features: AnalogFourPatchAudioFeatures,
) -> dict[str, object]:
    """Return a stable JSON-ready representation of audio evidence."""

    if not isinstance(features, AnalogFourPatchAudioFeatures):
        raise TypeError("features must be AnalogFourPatchAudioFeatures")
    return {
        "audio_sha256": features.audio_sha256,
        "duration": features.duration,
        "attack": features.attack,
        "decay": features.decay,
        "sustain": features.sustain,
        "tail": features.tail,
        "brightness": features.brightness,
        "spectral_flatness": features.spectral_flatness,
        "noise": features.noise,
        "low_end": features.low_end,
        "harmonicity": features.harmonicity,
        "transient": features.transient,
        "modulation": features.modulation,
    }


def analog_four_audio_patch_genome_to_dict(
    audio_genome: AnalogFourAudioPatchGenome,
) -> dict[str, object]:
    """Return a stable JSON-ready representation of inferred patch DNA."""

    if not isinstance(audio_genome, AnalogFourAudioPatchGenome):
        raise TypeError("audio_genome must be an AnalogFourAudioPatchGenome")
    report = audio_genome.feature_report
    return {
        "feature_report": {
            "source_type": report.source_type.value,
            "confidence": report.confidence.value,
            "bpm": report.bpm,
            "tempo_stability": report.tempo_stability,
            "kick_density": report.kick_density,
            "percussion_density": report.percussion_density,
            "low_end_weight": report.low_end_weight,
            "spectral_brightness": report.spectral_brightness,
            "texture_noise": report.texture_noise,
            "energy_arc": list(report.energy_arc),
            "content_hash": report.content_hash,
            "derived_at": report.derived_at,
        },
        "audio_features": analog_four_patch_audio_features_to_dict(audio_genome.audio_features),
        "genome": analog_four_patch_genome_to_dict(audio_genome.genome),
    }


def _require_audio_stack() -> tuple[_LibrosaApi, _NumpyApi]:  # pragma: no cover
    try:
        import librosa  # type: ignore[import-not-found]
        import numpy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise StyleAnalysisDependencyError(
            "Analog Four audio inference requires the 'style' optional extra. "
            'Install it with: pip install -e ".[style,dev]"'
        ) from exc
    return cast(_LibrosaApi, librosa), cast(_NumpyApi, numpy)


def _measure_analog_four_patch_audio(
    path: Path,
) -> _AnalogFourAudioMeasurements:  # pragma: no cover - optional librosa path
    librosa, numpy = _require_audio_stack()
    y, sample_rate = librosa.load(str(path), sr=_AUDIO_SAMPLE_RATE, mono=True)
    samples = _flat_float_values(numpy, y)
    if not samples or sample_rate <= 0:
        return _AnalogFourAudioMeasurements(*(0.0 for _ in range(12)))

    duration_seconds = len(samples) / float(sample_rate)
    rms = _flat_float_values(
        numpy,
        librosa.feature.rms(
            y=y,
            frame_length=_AUDIO_FRAME_LENGTH,
            hop_length=_AUDIO_HOP_LENGTH,
        ),
    )
    peak_rms = max(rms, default=0.0)
    peak_index = rms.index(peak_rms) if peak_rms > 0.0 else 0
    attack_seconds = peak_index * _AUDIO_HOP_LENGTH / float(sample_rate)
    decay_frames = _decay_frames(rms, peak_index, peak_rms)
    decay_seconds = decay_frames * _AUDIO_HOP_LENGTH / float(sample_rate)
    sustain = _window_level(rms, peak_rms, 0.40, 0.75)
    tail = _window_level(rms, peak_rms, 0.80, 1.00)

    centroid = _flat_float_values(
        numpy,
        librosa.feature.spectral_centroid(y=y, sr=sample_rate),
    )
    brightness = _clamp_audio_feature_unit(_mean(centroid) / (sample_rate / 2.0))
    flatness_values = _flat_float_values(
        numpy,
        librosa.feature.spectral_flatness(y=y),
    )
    spectral_flatness = _clamp_audio_feature_unit(_mean(flatness_values))
    zero_crossings = _flat_float_values(
        numpy,
        librosa.feature.zero_crossing_rate(y),
    )
    noise = _clamp_audio_feature_unit(spectral_flatness * 0.75 + _mean(zero_crossings) * 0.25)

    magnitude = _matrix_float_values(
        numpy,
        numpy.abs(
            librosa.stft(
                y,
                n_fft=_AUDIO_FRAME_LENGTH,
                hop_length=_AUDIO_HOP_LENGTH,
            )
        ),
    )
    frequencies = _flat_float_values(
        numpy,
        librosa.fft_frequencies(sr=sample_rate, n_fft=_AUDIO_FRAME_LENGTH),
    )
    total_spectral_energy = sum(sum(row) for row in magnitude)
    low_spectral_energy = sum(
        sum(row)
        for frequency, row in zip(frequencies, magnitude, strict=False)
        if frequency < 250.0
    )
    low_end = _safe_ratio(low_spectral_energy, total_spectral_energy)

    harmonic = _flat_float_values(numpy, librosa.effects.harmonic(y))
    harmonic_energy = sum(sample * sample for sample in harmonic)
    total_sample_energy = sum(sample * sample for sample in samples)
    harmonicity = _safe_ratio(harmonic_energy, total_sample_energy)

    onset_strength = _flat_float_values(
        numpy,
        librosa.onset.onset_strength(y=y, sr=sample_rate),
    )
    transient = _safe_ratio(_mean(onset_strength), max(onset_strength, default=0.0))
    rms_mean = _mean(rms)
    modulation = _clamp_audio_feature_unit(
        _standard_deviation(rms, rms_mean) / max(rms_mean, 1e-12) / 2.0
    )
    return _AnalogFourAudioMeasurements(
        duration=_clamp_audio_feature_unit(duration_seconds / 8.0),
        attack=_clamp_audio_feature_unit(attack_seconds / 2.0),
        decay=_clamp_audio_feature_unit(decay_seconds / 4.0),
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


def _flat_float_values(  # pragma: no cover - optional librosa path
    numpy: _NumpyApi, value: object
) -> list[float]:
    raw = cast(list[float], numpy.asarray(value).reshape(-1).tolist())
    return [float(item) for item in raw]


def _matrix_float_values(  # pragma: no cover - optional librosa path
    numpy: _NumpyApi, value: object
) -> list[list[float]]:
    raw = cast(list[list[float]], numpy.asarray(value).tolist())
    return [[float(item) for item in row] for row in raw]


def _decay_frames(rms: list[float], peak_index: int, peak_rms: float) -> int:
    threshold = peak_rms * 0.37
    for index in range(peak_index, len(rms)):
        if rms[index] <= threshold:
            return index - peak_index
    return max(0, len(rms) - peak_index - 1)


def _window_level(
    rms: list[float],
    peak_rms: float,
    start_fraction: float,
    end_fraction: float,
) -> float:
    if not rms or peak_rms <= 0.0:
        return 0.0
    start = min(len(rms) - 1, int(len(rms) * start_fraction))
    end = max(start + 1, min(len(rms), int(len(rms) * end_fraction)))
    return _clamp_audio_feature_unit(_mean(rms[start:end]) / peak_rms)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _standard_deviation(values: list[float], mean: float) -> float:
    if not values:
        return 0.0
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return variance**0.5


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0.0:
        return 0.0
    return _clamp_audio_feature_unit(numerator / denominator)


def _stable_audio_feature_report(report: FeatureReport) -> FeatureReport:
    stable = replace(report, content_hash="", derived_at=_AUDIO_REPORT_DERIVED_AT)
    return replace(stable, content_hash=compute_feature_report_hash(stable))


def _infer_candidate(
    candidate: AnalogFourPatchCandidate,
    features: AnalogFourPatchAudioFeatures,
) -> AnalogFourPatchCandidate:
    return replace(
        candidate,
        genes=tuple(_infer_gene(gene, candidate.column, features) for gene in candidate.genes),
    )


def _infer_gene(
    gene: AnalogFourPatchGene,
    column: int,
    features: AnalogFourPatchAudioFeatures,
) -> AnalogFourPatchGene:
    screen_target = _inferred_screen_target(gene.value.parameter, column, features)
    if screen_target is None:
        return gene
    return replace(
        gene,
        value=make_a4_patch_value(gene.value.parameter, screen_target=screen_target),
        rationale=f"{gene.rationale}; adjusted from measured audio evidence",
    )


def _inferred_screen_target(
    parameter: str,
    column: int,
    features: AnalogFourPatchAudioFeatures,
) -> int | None:
    brightness, noise, low_end, animation, tail = _candidate_character(features, column)
    harmonicity = features.harmonicity
    transient = features.transient
    if parameter == "OSC1 Level":
        return _unipolar(70 + harmonicity * 38 + low_end * 18 - noise * 12)
    if parameter == "OSC2 Level":
        return _unipolar(22 + brightness * 54 + harmonicity * 22 - low_end * 8)
    if parameter == "Noise Level":
        return _unipolar(8 + noise * 106)
    if parameter == "Noise Fade":
        return _unipolar(10 + tail * 96)
    if parameter in {"OSC1 Pulsewidth", "OSC2 Pulsewidth"}:
        return _bipolar(-(brightness * 28 + harmonicity * 12 - low_end * 8))
    if parameter == "Sync Amount":
        return _unipolar(brightness * 82 + harmonicity * 34)
    if parameter in {"EnvA Attack Time", "EnvF Attack Time"}:
        return _unipolar(features.attack * 112)
    if parameter == "EnvA Decay Time":
        return _unipolar(features.decay * 82 + features.duration * 30 + 8)
    if parameter == "EnvF Decay Time":
        return _unipolar(features.decay * 72 + transient * 34 + 10)
    if parameter == "EnvA Sustain Level":
        return _unipolar(features.sustain * 112)
    if parameter == "EnvF Sustain Level":
        return _unipolar(features.sustain * 92)
    if parameter == "EnvA Release Time":
        return _unipolar(tail * 100 + features.duration * 18)
    if parameter == "EnvF Release Time":
        return _unipolar(tail * 92 + features.decay * 22)
    if parameter == "LFO1 Speed":
        return _bipolar(animation * 48 + transient * 8)
    if parameter == "LFO1 Depth A":
        return _bipolar(animation * 24 + noise * 8)
    if parameter == "LFO1 Depth B":
        return _bipolar(animation * noise * 18)
    if parameter == "Filter1 Frequency":
        return _unipolar(24 + brightness * 92 - low_end * 18)
    if parameter == "Filter2 Frequency":
        return _unipolar(46 + brightness * 76 - low_end * 12)
    if parameter == "Filter1 Resonance":
        return _unipolar(8 + harmonicity * 38 + transient * 22)
    if parameter == "Filter2 Resonance":
        return _unipolar(6 + harmonicity * 30 + brightness * 20)
    if parameter == "Filter Overdrive":
        return _bipolar((harmonicity * 0.35 + noise * 0.35 + low_end * 0.30) * 34)
    if parameter == "Filter1 Envelope Amount":
        return _bipolar(transient * 46 + features.decay * 10 - features.sustain * 6)
    if parameter == "Filter2 Envelope Amount":
        return _bipolar(transient * 34 + animation * 10 - features.sustain * 5)
    if parameter == "Delay Send Level":
        return _unipolar(animation * 42 + tail * 35)
    if parameter == "Reverb Send Level":
        return _unipolar(tail * 58 + features.sustain * 28 + noise * 20)
    if parameter == "Volume":
        return _unipolar(88 + harmonicity * 16 - noise * 8)
    return None


def _candidate_character(
    features: AnalogFourPatchAudioFeatures,
    column: int,
) -> tuple[float, float, float, float, float]:
    brightness_offset = (0.0, 0.18, 0.04, -0.18)[column - 1]
    noise_offset = (0.0, 0.04, 0.30, -0.12)[column - 1]
    low_end_offset = (0.0, -0.08, -0.04, 0.20)[column - 1]
    animation_offset = (0.0, 0.08, 0.28, -0.10)[column - 1]
    tail_offset = (0.0, -0.05, 0.12, 0.10)[column - 1]
    return (
        _clamp_audio_feature_unit(features.brightness + brightness_offset),
        _clamp_audio_feature_unit(features.noise + noise_offset),
        _clamp_audio_feature_unit(features.low_end + low_end_offset),
        _clamp_audio_feature_unit(features.modulation + animation_offset),
        _clamp_audio_feature_unit(features.tail + tail_offset),
    )


def _unipolar(value: float) -> int:
    return max(0, min(127, int(round(value))))


def _bipolar(value: float) -> int:
    return max(-64, min(63, int(round(value))))


def _clamp_audio_feature_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


__all__ = [
    "AnalogFourAudioPatchGenome",
    "AnalogFourPatchAudioFeatures",
    "analog_four_audio_patch_genome_to_dict",
    "analog_four_patch_audio_features_to_dict",
    "analyze_analog_four_patch_audio",
    "build_analog_four_audio_patch_genome",
]
