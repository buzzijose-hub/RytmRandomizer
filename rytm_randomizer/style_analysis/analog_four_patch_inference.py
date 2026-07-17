"""Deterministic audio-dependent Analog Four patch candidate inference."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final, TypeAlias, TypedDict, TypeVar, cast

from ..data.analog_four_audio_inference import (
    A4_AUDIO_INFERENCE_BIPOLAR,
    ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER,
    AnalogFourAudioInferenceSpec,
    AnalogFourInferenceFeatureKey,
    AnalogFourInferenceParameter,
)
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
from .extractor import (
    AudioFeatureAnalysis,
    AudioSynthesisFeatures,
    AudioSynthesisFeaturesPayload,
    StyleAnalysisDependencyError,
    analyze_audio,
    audio_synthesis_features_to_dict,
)
from .feature_report import (
    FeatureReport,
    FeatureReportPayload,
    compute_feature_report_hash,
    feature_report_to_dict,
)

_AUDIO_REPORT_DERIVED_AT: Final[str] = "1970-01-01T00:00:00Z"
_INFERENCE_FAILURE_FINGERPRINT: Final[str] = "a4.audio_patch.inference_failed"
_logger = get_logger(__name__)
_InferenceResult = TypeVar("_InferenceResult")


AnalogFourPatchAudioFeatures: TypeAlias = AudioSynthesisFeatures
AnalogFourPatchAudioFeaturesPayload: TypeAlias = AudioSynthesisFeaturesPayload
AnalogFourFeatureReportPayload: TypeAlias = FeatureReportPayload


@dataclass(frozen=True)
class AnalogFourAudioPatchGenome:
    """Measured audio evidence and its inferred Analog Four patch genome."""

    feature_report: FeatureReport
    audio_features: AnalogFourPatchAudioFeatures
    genome: AnalogFourPatchGenome


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
        duration_ms = (time.perf_counter() - started_at) * 1000.0
        metrics.record_a4_patch_inference(duration_ms, error_code=error_code)
        _logger.warning(
            "Analog Four audio patch inference failed",
            extra={
                "operation": "a4_audio_patch_inference",
                "error_code": error_code,
                "fingerprint": getattr(exc, "fingerprint", _INFERENCE_FAILURE_FINGERPRINT),
                "audio_path": str(path),
                "duration_ms": duration_ms,
                "error_type": type(exc).__name__,
                "metrics_summary": metrics.format_summary(),
            },
        )
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics.record_a4_patch_inference(duration_ms)
    _logger.info(
        "Analog Four audio patch inference completed",
        extra={
            "operation": "a4_audio_patch_inference",
            "audio_path": str(path),
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )
    return result


def _analyze_audio_for_a4(path: Path) -> AudioFeatureAnalysis:
    return analyze_audio(path)


def _audio_features_from_analysis(
    analysis: AudioFeatureAnalysis,
) -> AnalogFourPatchAudioFeatures:
    return analysis.synthesis_features


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

    if not isinstance(features, AudioSynthesisFeatures):
        raise TypeError("features must be AnalogFourPatchAudioFeatures")
    return audio_synthesis_features_to_dict(features)


def analog_four_audio_patch_genome_to_dict(
    audio_genome: AnalogFourAudioPatchGenome,
) -> AnalogFourAudioPatchGenomePayload:
    """Return a stable JSON-ready representation of inferred patch DNA."""

    if not isinstance(audio_genome, AnalogFourAudioPatchGenome):
        raise TypeError("audio_genome must be an AnalogFourAudioPatchGenome")
    report = audio_genome.feature_report
    return {
        "feature_report": feature_report_to_dict(report),
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
    feature_values: Mapping[AnalogFourInferenceFeatureKey, float] = {
        "attack": features.attack,
        "decay": features.decay,
        "sustain": features.sustain,
        "duration": features.duration,
        "brightness": brightness,
        "noise": noise,
        "low_end": low_end,
        "animation": animation,
        "tail": tail,
        "harmonicity": features.harmonicity,
        "transient": features.transient,
    }
    if parameter not in ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER:
        return None
    spec = ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER[cast(AnalogFourInferenceParameter, parameter)]
    return _evaluate_inference_spec(spec, feature_values)


def _evaluate_inference_spec(
    spec: AnalogFourAudioInferenceSpec,
    feature_values: Mapping[AnalogFourInferenceFeatureKey, float],
) -> int:
    value = spec.intercept
    for term in spec.terms:
        product = 1.0
        for feature_key in term.feature_keys:
            product *= feature_values[feature_key]
        value += product * term.coefficient
    value *= spec.output_multiplier
    if spec.scale == A4_AUDIO_INFERENCE_BIPOLAR:
        return _bipolar(value)
    return _unipolar(value)


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
