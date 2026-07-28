"""Passive acoustic ranking for rendered Analog Four patch candidates."""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Final, TypedDict, cast

from ...observability.errors import BoundaryError, DataError
from ...observability.logging import get_logger
from ...observability.metrics import AnalogFourPatchRenderRankErrorCode, get_metrics
from ...observability.tracing import operation
from ...style_analysis.analog_four_patch_genome import (
    ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    ANALOG_FOUR_PATCH_CANDIDATE_MIN,
)
from ...style_analysis.analog_four_patch_inference import (
    analyze_analog_four_patch_audio_isolated,
)
from ...style_analysis.analog_four_patch_render_rank import (
    AnalogFourPatchRenderScore,
    AnalogFourRenderCandidateFeatures,
    AnalogFourRenderFeatureDelta,
    rank_analog_four_render_features,
)
from ...style_analysis.extractor import StyleAnalysisDependencyError
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
_RENDER_RANK_FAILURE_FINGERPRINT: Final[str] = "a4.render_rank.failed"
_logger = get_logger(__name__)


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


class AnalogFourPatchRenderRankArtifactError(DataError, ValueError):
    """A batch manifest or candidate sidecar failed integrity validation."""

    fingerprint: ClassVar[str] = "a4.render_rank.artifact_invalid"


class AnalogFourPatchRenderRankReferenceError(DataError, ValueError):
    """The supplied reference audio does not match the committed batch."""

    fingerprint: ClassVar[str] = "a4.render_rank.reference_mismatch"


def analog_four_patch_render_rank_error_code(
    exc: BaseException,
) -> AnalogFourPatchRenderRankErrorCode:
    """Classify a ranking failure for metrics and presentation."""

    if isinstance(exc, (KeyboardInterrupt, SystemExit)):
        return "interrupted"
    if isinstance(exc, AnalogFourPatchRenderRankArtifactError):
        return "artifact_validation"
    if isinstance(exc, AnalogFourPatchRenderRankReferenceError):
        return "reference_mismatch"
    if isinstance(exc, BoundaryError):
        if exc.context.get("error_code") == "audio_read_failed":
            return "input_read_failed"
        if exc.context.get("error_code") == "interrupted":
            return "interrupted"
        return "rank_failed"
    if isinstance(exc, StyleAnalysisDependencyError):
        return "dependency_missing"
    if isinstance(exc, OSError):
        return "input_read_failed"
    if isinstance(exc, (TypeError, ValueError)):
        return "validation"
    return "rank_failed"


def _render_rank_failure_fingerprint(exc: BaseException) -> str:
    fingerprint = getattr(exc, "fingerprint", _RENDER_RANK_FAILURE_FINGERPRINT)
    if isinstance(exc, BoundaryError):
        fingerprint = exc.context.get("fingerprint", fingerprint)
    return str(fingerprint)


def rank_analog_four_patch_renders(
    *,
    reference_audio_path: Path,
    manifest_path: Path,
    render_paths: Mapping[int, Path],
) -> AnalogFourPatchRenderRankPacket:
    """Rank A4 recordings against the exact audio that generated their batch."""

    started_at = time.perf_counter()
    metrics = get_metrics()
    requested_render_count = _requested_render_count(render_paths)
    operation_id = ""
    try:
        with operation(
            "a4_patch_render_rank",
            logger=_logger,
            render_count=requested_render_count,
        ) as operation_id:
            packet = _rank_analog_four_patch_renders(
                reference_audio_path=reference_audio_path,
                manifest_path=manifest_path,
                render_paths=render_paths,
            )
    except (
        ImportError,
        BoundaryError,
        KeyError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        KeyboardInterrupt,
        SystemExit,
    ) as exc:
        error_code = analog_four_patch_render_rank_error_code(exc)
        duration_ms = (time.perf_counter() - started_at) * 1000.0
        metrics.record_a4_patch_render_rank(duration_ms, error_code=error_code)
        _logger.warning(
            "Analog Four patch render ranking failed",
            extra={
                "op_id": operation_id,
                "operation": "a4_patch_render_rank",
                "outcome": "failed",
                "error_code": error_code,
                "render_count": requested_render_count,
                "duration_ms": duration_ms,
                "error_type": type(exc).__name__,
                "fingerprint": _render_rank_failure_fingerprint(exc),
                "metrics_summary": metrics.format_summary(),
            },
        )
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics.record_a4_patch_render_rank(duration_ms)
    _logger.info(
        "Analog Four patch render ranking completed",
        extra={
            "op_id": operation_id,
            "operation": "a4_patch_render_rank",
            "outcome": "completed",
            "generation_id": packet.generation_id,
            "recommended_candidate": packet.recommended_candidate,
            "render_count": packet.render_count,
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )
    return packet


def _rank_analog_four_patch_renders(
    *,
    reference_audio_path: object,
    manifest_path: object,
    render_paths: object,
) -> AnalogFourPatchRenderRankPacket:
    validated_reference_path = _render_rank_path(
        reference_audio_path,
        label="reference_audio_path",
    )
    validated_manifest_path = _render_rank_path(
        manifest_path,
        label="manifest_path",
    )
    validated_render_paths = _render_rank_paths(render_paths)
    if not validated_render_paths:
        raise ValueError("at least one candidate render is required")

    reference = analyze_analog_four_patch_audio_isolated(validated_reference_path)
    measured_candidates: list[AnalogFourRenderCandidateFeatures] = []
    generation_id = ""
    selected_track = 0
    for candidate, render_path in sorted(validated_render_paths.items()):
        try:
            selection = load_analog_four_patch_batch_candidate(
                validated_manifest_path,
                candidate=candidate,
            )
        except (KeyError, OSError, TypeError, ValueError) as exc:
            raise AnalogFourPatchRenderRankArtifactError(
                str(exc),
                context={
                    "candidate": candidate,
                    "cause_type": type(exc).__name__,
                    "manifest_name": validated_manifest_path.name,
                },
            ) from exc
        if reference.audio_sha256 != selection.audio_sha256:
            raise AnalogFourPatchRenderRankReferenceError(
                "reference audio SHA-256 does not match the committed batch source",
                context={
                    "actual_sha256": reference.audio_sha256,
                    "expected_sha256": selection.audio_sha256,
                    "candidate": candidate,
                },
            )
        if generation_id and selection.generation_id != generation_id:
            raise AnalogFourPatchRenderRankArtifactError(
                "render candidates do not share one committed batch generation",
                context={
                    "candidate": candidate,
                    "actual_generation_id": selection.generation_id,
                    "expected_generation_id": generation_id,
                },
            )
        generation_id = selection.generation_id
        selected_track = selection.plan.selected_track
        measured_candidates.append(
            AnalogFourRenderCandidateFeatures(
                candidate=candidate,
                label=selection.plan.selected_label,
                render_path=render_path,
                features=analyze_analog_four_patch_audio_isolated(render_path),
            )
        )

    ranked = rank_analog_four_render_features(reference, tuple(measured_candidates))
    recommended = ranked[0]
    return AnalogFourPatchRenderRankPacket(
        version=ANALOG_FOUR_RENDER_RANK_VERSION,
        generation_id=generation_id,
        selected_track=selected_track,
        reference_path=validated_reference_path.resolve(),
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

    packet = _render_rank_packet(packet)
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


def _requested_render_count(render_paths: object) -> int:
    if not isinstance(render_paths, Mapping):
        return 0
    return len(cast(Mapping[object, object], render_paths))


def _render_rank_path(value: object, *, label: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{label} must be a Path")
    return value


def _render_rank_paths(value: object) -> dict[int, Path]:
    if not isinstance(value, Mapping):
        raise TypeError("render_paths must be a mapping")
    paths: dict[int, Path] = {}
    for candidate, path in cast(Mapping[object, object], value).items():
        if (
            not isinstance(candidate, int)
            or isinstance(candidate, bool)
            or candidate < ANALOG_FOUR_PATCH_CANDIDATE_MIN
            or candidate > ANALOG_FOUR_PATCH_CANDIDATE_MAX
            or not isinstance(path, Path)
        ):
            raise ValueError(
                "render_paths must map candidate integers "
                f"{ANALOG_FOUR_PATCH_CANDIDATE_MIN}.."
                f"{ANALOG_FOUR_PATCH_CANDIDATE_MAX} to Path values"
            )
        paths[candidate] = path
    return paths


def _render_rank_packet(value: object) -> AnalogFourPatchRenderRankPacket:
    if not isinstance(value, AnalogFourPatchRenderRankPacket):
        raise TypeError("packet must be an AnalogFourPatchRenderRankPacket")
    return value


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
    "analog_four_patch_render_rank_error_code",
    "analog_four_patch_render_rank_to_dict",
    "rank_analog_four_patch_renders",
]
