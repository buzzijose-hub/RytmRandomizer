"""Pure acoustic scoring for recorded Analog Four patch candidates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from ..data.analog_four_render_rank import ANALOG_FOUR_RENDER_RANK_FEATURE_WEIGHTS
from .extractor import AudioSynthesisFeatures


@dataclass(frozen=True)
class AnalogFourRenderCandidateFeatures:
    candidate: int
    label: str
    render_path: Path
    features: AudioSynthesisFeatures


@dataclass(frozen=True)
class AnalogFourRenderFeatureDelta:
    """One normalized reference-to-render feature difference."""

    feature: str
    reference_value: float
    render_value: float
    absolute_delta: float
    weight: float
    weighted_delta: float


@dataclass(frozen=True)
class AnalogFourPatchRenderScore:
    """Acoustic match score for one rendered A4 batch candidate."""

    rank: int
    candidate: int
    label: str
    render_path: Path
    render_sha256: str
    similarity: int
    distance: float
    feature_deltas: tuple[AnalogFourRenderFeatureDelta, ...]


def _require_audio_synthesis_features(value: object) -> AudioSynthesisFeatures:
    if not isinstance(value, AudioSynthesisFeatures):
        raise TypeError("reference must be AudioSynthesisFeatures")
    return value


def rank_analog_four_render_features(
    reference: AudioSynthesisFeatures,
    candidates: tuple[AnalogFourRenderCandidateFeatures, ...],
) -> tuple[AnalogFourPatchRenderScore, ...]:
    """Rank already-measured A4 renders without file or manifest I/O."""

    reference = _require_audio_synthesis_features(reference)
    if not candidates:
        raise ValueError("at least one measured render candidate is required")

    scores = tuple(_score_candidate(reference, candidate) for candidate in candidates)
    return tuple(
        replace(score, rank=rank)
        for rank, score in enumerate(
            sorted(scores, key=lambda score: (score.distance, score.candidate)),
            start=1,
        )
    )


def _score_candidate(
    reference: AudioSynthesisFeatures,
    candidate: AnalogFourRenderCandidateFeatures,
) -> AnalogFourPatchRenderScore:
    deltas = _feature_deltas(reference, candidate.features)
    distance = min(1.0, sum(delta.weighted_delta for delta in deltas))
    return AnalogFourPatchRenderScore(
        rank=0,
        candidate=candidate.candidate,
        label=candidate.label,
        render_path=candidate.render_path.resolve(),
        render_sha256=candidate.features.audio_sha256,
        similarity=max(0, min(100, int(round((1.0 - distance) * 100.0)))),
        distance=round(distance, 6),
        feature_deltas=deltas,
    )


def _feature_deltas(
    reference: AudioSynthesisFeatures,
    rendered: AudioSynthesisFeatures,
) -> tuple[AnalogFourRenderFeatureDelta, ...]:
    rows: list[AnalogFourRenderFeatureDelta] = []
    for feature, weight in ANALOG_FOUR_RENDER_RANK_FEATURE_WEIGHTS:
        reference_value = float(getattr(reference, feature))
        render_value = float(getattr(rendered, feature))
        absolute_delta = abs(reference_value - render_value)
        rows.append(
            AnalogFourRenderFeatureDelta(
                feature=feature,
                reference_value=round(reference_value, 6),
                render_value=round(render_value, 6),
                absolute_delta=round(absolute_delta, 6),
                weight=weight,
                weighted_delta=round(absolute_delta * weight, 6),
            )
        )
    return tuple(rows)


__all__ = [
    "AnalogFourPatchRenderScore",
    "AnalogFourRenderCandidateFeatures",
    "AnalogFourRenderFeatureDelta",
    "rank_analog_four_render_features",
]
