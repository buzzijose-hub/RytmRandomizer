"""Pure bounded feedback planning for recorded Analog Four patch renders."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Literal, TypedDict

from ..data.analog_four_patch_refinement import (
    ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MAX,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MIN,
    ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MAX,
    ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MIN,
)
from .analog_four_patch_genome import ANALOG_FOUR_TRACK_MAX, ANALOG_FOUR_TRACK_MIN
from .analog_four_patch_inference import (
    AnalogFourAudioPatchGenome,
    AnalogFourAudioPatchGenomePayload,
    analog_four_audio_patch_genome_to_dict,
    build_analog_four_audio_patch_genome_from_analysis,
)
from .analog_four_patch_render_rank import AnalogFourPatchRenderScore
from .extractor import (
    AudioFeatureAnalysis,
    AudioSynthesisFeatures,
    AudioSynthesisFeaturesPayload,
    audio_synthesis_features_to_dict,
)

AnalogFourPatchRefinementAction = Literal["accept", "refine"]


@dataclass(frozen=True)
class AnalogFourPatchRefinementResidual:
    """One measured render error and its bounded corrective target."""

    feature: str
    reference_value: float
    rendered_value: float
    signed_error: float
    weight: float
    weighted_absolute_error: float
    correction: float
    corrected_target: float
    clamped: bool


@dataclass(frozen=True)
class AnalogFourPatchRefinementPlan:
    """A deterministic accept decision or one compensated next candidate."""

    action: AnalogFourPatchRefinementAction
    similarity: int
    candidate: int
    label: str
    selected_track: int
    correction_gain: float
    accept_similarity: int
    residuals: tuple[AnalogFourPatchRefinementResidual, ...]
    corrected_features: AudioSynthesisFeatures
    next_candidate: AnalogFourAudioPatchGenome | None


class AnalogFourPatchRefinementResidualPayload(TypedDict):
    feature: str
    reference_value: float
    rendered_value: float
    signed_error: float
    weight: float
    weighted_absolute_error: float
    correction: float
    corrected_target: float
    clamped: bool


class AnalogFourPatchRefinementPlanPayload(TypedDict):
    action: AnalogFourPatchRefinementAction
    similarity: int
    candidate: int
    label: str
    selected_track: int
    correction_gain: float
    accept_similarity: int
    residuals: list[AnalogFourPatchRefinementResidualPayload]
    corrected_features: AudioSynthesisFeaturesPayload
    next_candidate: AnalogFourAudioPatchGenomePayload | None


def _require_refinement_gain(value: object) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError("correction_gain must be a float")
    gain = float(value)
    if not math.isfinite(gain) or not (
        ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MIN <= gain <= ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MAX
    ):
        raise ValueError("correction_gain must be finite and between 0.0 and 1.0")
    return gain


def _require_accept_similarity(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("accept_similarity must be an integer")
    if not (
        ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MIN
        <= value
        <= ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MAX
    ):
        raise ValueError("accept_similarity must be between 0 and 100")
    return value


def _require_track(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("track must be an integer")
    if not ANALOG_FOUR_TRACK_MIN <= value <= ANALOG_FOUR_TRACK_MAX:
        raise ValueError(
            f"track must be between {ANALOG_FOUR_TRACK_MIN} and " f"{ANALOG_FOUR_TRACK_MAX}"
        )
    return value


def _require_refinement_inputs(
    reference_analysis: object,
    render_score: object,
    render_features: object,
) -> tuple[AudioFeatureAnalysis, AnalogFourPatchRenderScore, AudioSynthesisFeatures]:
    if not isinstance(reference_analysis, AudioFeatureAnalysis):
        raise TypeError("reference_analysis must be an AudioFeatureAnalysis")
    if not isinstance(render_score, AnalogFourPatchRenderScore):
        raise TypeError("render_score must be an AnalogFourPatchRenderScore")
    if not isinstance(render_features, AudioSynthesisFeatures):
        raise TypeError("render_features must be AudioSynthesisFeatures")
    if render_score.render_sha256 != render_features.audio_sha256:
        raise ValueError("render score and measured render hashes must match")
    return reference_analysis, render_score, render_features


def _clamp_normalized(value: float) -> tuple[float, bool]:
    bounded = min(1.0, max(0.0, value))
    return round(bounded, 6), bounded != value


def _build_residuals(
    score: AnalogFourPatchRenderScore,
    *,
    correction_gain: float,
) -> tuple[AnalogFourPatchRefinementResidual, ...]:
    rows: list[AnalogFourPatchRefinementResidual] = []
    for delta in score.feature_deltas:
        signed_error = delta.reference_value - delta.render_value
        correction = signed_error * correction_gain
        corrected_target, clamped = _clamp_normalized(delta.reference_value + correction)
        rows.append(
            AnalogFourPatchRefinementResidual(
                feature=delta.feature,
                reference_value=delta.reference_value,
                rendered_value=delta.render_value,
                signed_error=round(signed_error, 6),
                weight=delta.weight,
                weighted_absolute_error=delta.weighted_delta,
                correction=round(correction, 6),
                corrected_target=corrected_target,
                clamped=clamped,
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (-row.weighted_absolute_error, row.feature),
        )
    )


def _corrected_features(
    reference: AudioSynthesisFeatures,
    residuals: tuple[AnalogFourPatchRefinementResidual, ...],
) -> AudioSynthesisFeatures:
    corrected = {residual.feature: residual.corrected_target for residual in residuals}
    return AudioSynthesisFeatures(
        audio_sha256=reference.audio_sha256,
        duration=reference.duration,
        attack=corrected["attack"],
        decay=corrected["decay"],
        sustain=corrected["sustain"],
        tail=corrected["tail"],
        brightness=corrected["brightness"],
        spectral_flatness=corrected["spectral_flatness"],
        noise=corrected["noise"],
        low_end=corrected["low_end"],
        harmonicity=corrected["harmonicity"],
        transient=corrected["transient"],
        modulation=corrected["modulation"],
    )


def plan_analog_four_patch_refinement(
    reference_analysis: AudioFeatureAnalysis,
    render_score: AnalogFourPatchRenderScore,
    render_features: AudioSynthesisFeatures,
    *,
    track: int,
    correction_gain: float = ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
    accept_similarity: int = ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
) -> AnalogFourPatchRefinementPlan:
    """Compensate measured render error and infer one bounded next candidate."""

    reference_analysis, render_score, render_features = _require_refinement_inputs(
        reference_analysis,
        render_score,
        render_features,
    )
    correction_gain = _require_refinement_gain(correction_gain)
    accept_similarity = _require_accept_similarity(accept_similarity)
    track = _require_track(track)
    residuals = _build_residuals(render_score, correction_gain=correction_gain)
    corrected_features = _corrected_features(
        reference_analysis.synthesis_features,
        residuals,
    )
    action: AnalogFourPatchRefinementAction = (
        "accept" if render_score.similarity >= accept_similarity else "refine"
    )
    next_candidate = None
    if action == "refine":
        corrected_analysis = replace(
            reference_analysis,
            synthesis_features=corrected_features,
        )
        next_candidate = build_analog_four_audio_patch_genome_from_analysis(
            corrected_analysis,
            track=track,
            candidate_count=1,
        )
    return AnalogFourPatchRefinementPlan(
        action=action,
        similarity=render_score.similarity,
        candidate=render_score.candidate,
        label=render_score.label,
        selected_track=track,
        correction_gain=correction_gain,
        accept_similarity=accept_similarity,
        residuals=residuals,
        corrected_features=corrected_features,
        next_candidate=next_candidate,
    )


def analog_four_patch_refinement_plan_to_dict(
    plan: AnalogFourPatchRefinementPlan,
) -> AnalogFourPatchRefinementPlanPayload:
    """Return the stable JSON-ready representation of a refinement plan."""

    return {
        "action": plan.action,
        "similarity": plan.similarity,
        "candidate": plan.candidate,
        "label": plan.label,
        "selected_track": plan.selected_track,
        "correction_gain": plan.correction_gain,
        "accept_similarity": plan.accept_similarity,
        "residuals": [
            AnalogFourPatchRefinementResidualPayload(
                feature=row.feature,
                reference_value=row.reference_value,
                rendered_value=row.rendered_value,
                signed_error=row.signed_error,
                weight=row.weight,
                weighted_absolute_error=row.weighted_absolute_error,
                correction=row.correction,
                corrected_target=row.corrected_target,
                clamped=row.clamped,
            )
            for row in plan.residuals
        ],
        "corrected_features": audio_synthesis_features_to_dict(plan.corrected_features),
        "next_candidate": (
            analog_four_audio_patch_genome_to_dict(plan.next_candidate)
            if plan.next_candidate is not None
            else None
        ),
    }


__all__ = [
    "AnalogFourPatchRefinementAction",
    "AnalogFourPatchRefinementPlan",
    "AnalogFourPatchRefinementPlanPayload",
    "AnalogFourPatchRefinementResidual",
    "AnalogFourPatchRefinementResidualPayload",
    "analog_four_patch_refinement_plan_to_dict",
    "plan_analog_four_patch_refinement",
]
