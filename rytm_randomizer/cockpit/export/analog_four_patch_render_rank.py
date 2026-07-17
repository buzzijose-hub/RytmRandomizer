"""Passive acoustic ranking for rendered Analog Four patch candidates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict

from ...style_analysis.analog_four_patch_inference import analyze_analog_four_patch_audio
from ...style_analysis.analog_four_patch_render_rank import (
    AnalogFourPatchRenderScore,
    AnalogFourRenderCandidateFeatures,
    AnalogFourRenderFeatureDelta,
    rank_analog_four_render_features,
)
from .analog_four_patch_batch_reader import load_analog_four_patch_batch_candidate

ANALOG_FOUR_RENDER_RANK_VERSION: Final[str] = "analog-four-render-rank-v1"
ANALOG_FOUR_RENDER_RANK_SAFETY: Final[tuple[str, ...]] = (
    "passive local audio comparison",
    "batch candidate sidecars are hash-verified before ranking",
    "reference audio must match the batch source hash",
    "no MIDI port opened",
    "no MIDI sent",
    "no SysEx written",
    "no hardware mutation",
)


@dataclass(frozen=True)
class AnalogFourPatchRenderRankPacket:
    """Ranked hardware-render feedback for one committed patch generation."""

    version: str
    generation_id: str
    selected_track: int
    reference_path: Path
    reference_sha256: str
    render_count: int
    recommended_candidate: int
    recommended_label: str
    scores: tuple[AnalogFourPatchRenderScore, ...]
    safety: tuple[str, ...]


class AnalogFourRenderFeatureDeltaPayload(TypedDict):
    feature: str
    reference_value: float
    render_value: float
    absolute_delta: float
    weight: float
    weighted_delta: float


class AnalogFourPatchRenderScorePayload(TypedDict):
    rank: int
    candidate: int
    label: str
    render_path: str
    render_sha256: str
    similarity: int
    distance: float
    feature_deltas: list[AnalogFourRenderFeatureDeltaPayload]


class AnalogFourPatchRenderRankPayload(TypedDict):
    version: str
    generation_id: str
    selected_track: int
    reference_path: str
    reference_sha256: str
    render_count: int
    recommended_candidate: int
    recommended_label: str
    scores: list[AnalogFourPatchRenderScorePayload]
    safety: list[str]


class AnalogFourPatchRenderRankArtifactError(ValueError):
    """A batch manifest or candidate sidecar failed integrity validation."""


class AnalogFourPatchRenderRankReferenceError(ValueError):
    """The supplied reference audio does not match the committed batch."""


def rank_analog_four_patch_renders(
    *,
    reference_audio_path: Path,
    manifest_path: Path,
    render_paths: Mapping[int, Path],
) -> AnalogFourPatchRenderRankPacket:
    """Rank A4 recordings against the exact audio that generated their batch."""

    if not isinstance(reference_audio_path, Path):
        raise TypeError("reference_audio_path must be a Path")
    if not isinstance(manifest_path, Path):
        raise TypeError("manifest_path must be a Path")
    if not isinstance(render_paths, Mapping):
        raise TypeError("render_paths must be a mapping")
    if not render_paths:
        raise ValueError("at least one candidate render is required")
    if any(
        not isinstance(candidate, int)
        or isinstance(candidate, bool)
        or candidate < 1
        or candidate > 4
        or not isinstance(path, Path)
        for candidate, path in render_paths.items()
    ):
        raise ValueError("render_paths must map candidate integers 1..4 to Path values")

    reference = analyze_analog_four_patch_audio(reference_audio_path)
    measured_candidates: list[AnalogFourRenderCandidateFeatures] = []
    generation_id = ""
    selected_track = 0
    for candidate, render_path in sorted(render_paths.items()):
        try:
            selection = load_analog_four_patch_batch_candidate(
                manifest_path,
                candidate=candidate,
            )
        except (KeyError, OSError, TypeError, ValueError) as exc:
            raise AnalogFourPatchRenderRankArtifactError(str(exc)) from exc
        if reference.audio_sha256 != selection.audio_sha256:
            raise AnalogFourPatchRenderRankReferenceError(
                "reference audio SHA-256 does not match the committed batch source"
            )
        if generation_id and selection.generation_id != generation_id:
            raise AnalogFourPatchRenderRankArtifactError(
                "render candidates do not share one committed batch generation"
            )
        generation_id = selection.generation_id
        selected_track = selection.plan.selected_track
        measured_candidates.append(
            AnalogFourRenderCandidateFeatures(
                candidate=candidate,
                label=selection.plan.selected_label,
                render_path=render_path,
                features=analyze_analog_four_patch_audio(render_path),
            )
        )

    ranked = rank_analog_four_render_features(reference, tuple(measured_candidates))
    recommended = ranked[0]
    return AnalogFourPatchRenderRankPacket(
        version=ANALOG_FOUR_RENDER_RANK_VERSION,
        generation_id=generation_id,
        selected_track=selected_track,
        reference_path=reference_audio_path.resolve(),
        reference_sha256=reference.audio_sha256,
        render_count=len(ranked),
        recommended_candidate=recommended.candidate,
        recommended_label=recommended.label,
        scores=ranked,
        safety=ANALOG_FOUR_RENDER_RANK_SAFETY,
    )


def analog_four_patch_render_rank_to_dict(
    packet: AnalogFourPatchRenderRankPacket,
) -> AnalogFourPatchRenderRankPayload:
    """Return a stable JSON-ready render-ranking payload."""

    if not isinstance(packet, AnalogFourPatchRenderRankPacket):
        raise TypeError("packet must be an AnalogFourPatchRenderRankPacket")
    return {
        "version": packet.version,
        "generation_id": packet.generation_id,
        "selected_track": packet.selected_track,
        "reference_path": str(packet.reference_path),
        "reference_sha256": packet.reference_sha256,
        "render_count": packet.render_count,
        "recommended_candidate": packet.recommended_candidate,
        "recommended_label": packet.recommended_label,
        "scores": [_score_payload(score) for score in packet.scores],
        "safety": list(packet.safety),
    }


def _score_payload(score: AnalogFourPatchRenderScore) -> AnalogFourPatchRenderScorePayload:
    return {
        "rank": score.rank,
        "candidate": score.candidate,
        "label": score.label,
        "render_path": str(score.render_path),
        "render_sha256": score.render_sha256,
        "similarity": score.similarity,
        "distance": score.distance,
        "feature_deltas": [
            {
                "feature": delta.feature,
                "reference_value": delta.reference_value,
                "render_value": delta.render_value,
                "absolute_delta": delta.absolute_delta,
                "weight": delta.weight,
                "weighted_delta": delta.weighted_delta,
            }
            for delta in score.feature_deltas
        ],
    }


__all__ = [
    "ANALOG_FOUR_RENDER_RANK_SAFETY",
    "ANALOG_FOUR_RENDER_RANK_VERSION",
    "AnalogFourPatchRenderRankPacket",
    "AnalogFourPatchRenderRankArtifactError",
    "AnalogFourPatchRenderRankReferenceError",
    "AnalogFourPatchRenderScore",
    "AnalogFourRenderFeatureDelta",
    "analog_four_patch_render_rank_to_dict",
    "rank_analog_four_patch_renders",
]
