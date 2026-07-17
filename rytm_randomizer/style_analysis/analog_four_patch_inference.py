"""Deterministic audio-dependent Analog Four patch candidate inference."""

from __future__ import annotations

import string
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final, TypedDict, TypeVar

from ..data.analog_four_display import make_a4_patch_value
from ..data.analog_four_patch_templates import ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES
from ..observability.logging import get_logger
from ..observability.metrics import AnalogFourPatchInferenceErrorCode, get_metrics
from .analog_four_patch_genome import (
    AnalogFourPatchCandidate,
    AnalogFourPatchGene,
    AnalogFourPatchGenome,
    AnalogFourPatchGenomePayload,
    analog_four_patch_genome_to_dict,
    build_analog_four_patch_genome,
)
from .extractor import AudioFeatureAnalysis, StyleAnalysisDependencyError, analyze_audio
from .feature_report import FeatureReport, compute_feature_report_hash

_AUDIO_REPORT_DERIVED_AT: Final[str] = "1970-01-01T00:00:00Z"
_logger = get_logger(__name__)
_InferenceResult = TypeVar("_InferenceResult")


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


class AnalogFourPatchAudioFeaturesPayload(TypedDict):
    """Stable JSON-ready schema for measured audio evidence."""

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


class AnalogFourFeatureReportPayload(TypedDict):
    source_type: str
    confidence: str
    bpm: float
    tempo_stability: float
    kick_density: float
    percussion_density: float
    low_end_weight: float
    spectral_brightness: float
    texture_noise: float
    energy_arc: list[float]
    content_hash: str
    derived_at: str


class AnalogFourAudioPatchGenomePayload(TypedDict):
    feature_report: AnalogFourFeatureReportPayload
    audio_features: AnalogFourPatchAudioFeaturesPayload
    genome: AnalogFourPatchGenomePayload


def analyze_analog_four_patch_audio(path: Path) -> AnalogFourPatchAudioFeatures:
    """Measure normalized A4 synthesis evidence from ``path``."""

    return _recorded_a4_inference(
        path,
        lambda: _audio_features_from_analysis(_analyze_audio_for_a4(path)),
    )


def _a4_inference_error_code(exc: Exception) -> AnalogFourPatchInferenceErrorCode:
    if isinstance(exc, StyleAnalysisDependencyError):
        return "dependency_missing"
    if isinstance(exc, OSError):
        return "audio_read_failed"
    if isinstance(exc, (TypeError, ValueError)):
        return "validation"
    return "inference_failed"


def _recorded_a4_inference(
    path: Path,
    operation: Callable[[], _InferenceResult],
) -> _InferenceResult:
    started_at = time.perf_counter()
    metrics = get_metrics()
    try:
        result = operation()
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        error_code = _a4_inference_error_code(exc)
        metrics.record_a4_patch_inference(
            (time.perf_counter() - started_at) * 1000.0,
            error_code=error_code,
        )
        _logger.warning(
            "Analog Four audio patch inference failed",
            extra={
                "operation": "a4_audio_patch_inference",
                "error_code": error_code,
                "audio_path": str(path),
            },
        )
        raise

    metrics.record_a4_patch_inference((time.perf_counter() - started_at) * 1000.0)
    _logger.info(
        "Analog Four audio patch inference completed",
        extra={
            "operation": "a4_audio_patch_inference",
            "audio_path": str(path),
        },
    )
    return result


def _analyze_audio_for_a4(path: Path) -> AudioFeatureAnalysis:
    return analyze_audio(path)


def _audio_features_from_analysis(
    analysis: AudioFeatureAnalysis,
) -> AnalogFourPatchAudioFeatures:
    return AnalogFourPatchAudioFeatures(
        audio_sha256=analysis.audio_sha256,
        duration=analysis.duration,
        attack=analysis.attack,
        decay=analysis.decay,
        sustain=analysis.sustain,
        tail=analysis.tail,
        brightness=analysis.brightness,
        spectral_flatness=analysis.spectral_flatness,
        noise=analysis.noise,
        low_end=analysis.low_end,
        harmonicity=analysis.harmonicity,
        transient=analysis.transient,
        modulation=analysis.modulation,
    )


def build_analog_four_audio_patch_genome(
    path: Path,
    *,
    track: int = 1,
    candidate_count: int = 4,
) -> AnalogFourAudioPatchGenome:
    """Infer deterministic audio-dependent A4 candidates from ``path``."""

    return _recorded_a4_inference(
        path,
        lambda: _build_analog_four_audio_patch_genome(
            path,
            track=track,
            candidate_count=candidate_count,
        ),
    )


def _build_analog_four_audio_patch_genome(
    path: Path,
    *,
    track: int,
    candidate_count: int,
) -> AnalogFourAudioPatchGenome:
    """Build one genome inside the complete-operation metrics boundary."""

    analysis = _analyze_audio_for_a4(path)
    audio_features = _audio_features_from_analysis(analysis)
    feature_report = _stable_audio_feature_report(analysis.feature_report)
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
) -> AnalogFourPatchAudioFeaturesPayload:
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
) -> AnalogFourAudioPatchGenomePayload:
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
    try:
        template = ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES[column - 1]
    except IndexError as exc:
        raise ValueError(
            f"candidate column must be in 1..{len(ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES)}"
        ) from exc
    if template.column != column:
        raise ValueError("candidate template columns must be contiguous and one-based")
    return (
        _clamp_audio_feature_unit(features.brightness + template.brightness_offset),
        _clamp_audio_feature_unit(features.noise + template.noise_offset),
        _clamp_audio_feature_unit(features.low_end + template.low_end_offset),
        _clamp_audio_feature_unit(features.modulation + template.animation_offset),
        _clamp_audio_feature_unit(features.tail + template.tail_offset),
    )


def _unipolar(value: float) -> int:
    return max(0, min(127, int(round(value))))


def _bipolar(value: float) -> int:
    return max(-64, min(63, int(round(value))))


def _clamp_audio_feature_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


__all__ = [
    "AnalogFourAudioPatchGenome",
    "AnalogFourAudioPatchGenomePayload",
    "AnalogFourFeatureReportPayload",
    "AnalogFourPatchAudioFeatures",
    "AnalogFourPatchAudioFeaturesPayload",
    "analog_four_audio_patch_genome_to_dict",
    "analog_four_patch_audio_features_to_dict",
    "analyze_analog_four_patch_audio",
    "build_analog_four_audio_patch_genome",
]
