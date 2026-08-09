"""Guarded audio-to-candidate batch export for Analog Four MKII saved kits."""

from __future__ import annotations

import re
import secrets
import sys
import tempfile
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Final

from ...data.analog_four_sysex_calibration import A4_FILTER2_RESONANCE_PARAMETER
from ...devices.analog_four import (
    AnalogFourSavedKitMutation,
    AnalogFourSavedKitRenderResult,
    get_analog_four_saved_kit_capability,
)
from ...observability.errors import BoundaryError
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...observability.tracing import operation as trace_operation
from ...style_analysis.analog_four_patch_genome import (
    ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    ANALOG_FOUR_PATCH_CANDIDATE_MIN,
    ANALOG_FOUR_TRACK_MAX,
    ANALOG_FOUR_TRACK_MIN,
    AnalogFourPatchCandidate,
    AnalogFourPatchCandidatePayload,
    AnalogFourPatchGene,
    AnalogFourPatchGenePayload,
    AnalogFourPatchGenome,
    AnalogFourPatchGenomePayload,
    analog_four_patch_candidate_to_dict,
)
from ...style_analysis.analog_four_patch_inference import (
    AnalogFourPatchAudioFeaturesPayload,
)
from ...style_analysis.analog_four_patch_send_plan import (
    AnalogFourPatchSendPlan,
    AnalogFourPatchSendPlanPayload,
    analog_four_patch_send_plan_to_dict,
)
from ...style_analysis.extractor import StyleAnalysisDependencyError
from ...style_analysis.feature_report import FeatureReport
from .analog_four_export_contracts import (
    AnalogFourExportErrorCode,
    analog_four_export_path_name,
    attach_analog_four_export_error_code,
    require_analog_four_export_path,
)
from .analog_four_kit import (
    AnalogFourSavedKitExportResult,
)
from .analog_four_patch_batch_codec import (
    BATCH_SCHEMA_VERSION,
    CANDIDATE_SCHEMA_VERSION,
    analog_four_patch_batch_payload_sha256,
    analog_four_patch_batch_sha256,
    encode_analog_four_patch_batch_json,
)
from .analog_four_patch_batch_contracts import (
    SYSEX_COVERAGE_STATEMENT,
    AnalogFourAudioPatchBatchExportResult,
)
from .analog_four_patch_batch_contracts import (
    AnalogFourBatchCandidateSidecarPayload as _CandidateSidecarPayload,
)
from .analog_four_patch_batch_contracts import (
    AnalogFourBatchCoverageCountsPayload as _CoverageCountsPayload,
)
from .analog_four_patch_batch_contracts import (
    AnalogFourBatchHardwareAppliedRowPayload as _HardwareAppliedRowPayload,
)
from .analog_four_patch_batch_contracts import (
    AnalogFourBatchManifestCandidatePayload as _ManifestCandidatePayload,
)
from .analog_four_patch_batch_contracts import (
    AnalogFourBatchManifestPayload as _BatchManifestPayload,
)
from .analog_four_patch_batch_contracts import AnalogFourDeferredGenePayload as _DeferredGenePayload
from .analog_four_patch_batch_contracts import (
    AnalogFourPatchCandidateBatchResult,
)
from .analog_four_patch_batch_publication import (
    AnalogFourPatchBatchLockedError,
    AnalogFourPatchBatchPublicationError,
    acquire_batch_lock,
)
from .analog_four_patch_batch_publication import (
    batch_lock_matches_request as _batch_lock_matches_request,
)
from .analog_four_patch_batch_publication import (
    publish_immutable_artifact,
)
from .analog_four_patch_batch_publication import release_batch_lock as _release_batch_lock
from .writer import WriteResult, atomic_write

if TYPE_CHECKING:
    from ...style_analysis.analog_four_patch_inference import AnalogFourAudioPatchGenome

_MIDI_DATA_MAX: Final[int] = 127

FILTER2_RESONANCE_PARAMETER: Final[str] = A4_FILTER2_RESONANCE_PARAMETER
_DEFERRED_REASON: Final[str] = "not hardware-write-validated for saved-kit SysEx"
_SAFE_SEGMENT_RE: Final[re.Pattern[str]] = re.compile(r"[^a-z0-9]+")
_EXPORT_FAILURE_FINGERPRINT: Final[str] = "a4.audio_patch_batch.export_failed"
_LOCK_CLEANUP_FAILURE_FINGERPRINT: Final[str] = "a4.audio_patch_batch.lock_cleanup_failed"
_logger = get_logger(__name__)


class AnalogFourPatchBatchStageError(BoundaryError, RuntimeError):
    """Classified failure while analyzing or staging one A4 patch batch."""

    fingerprint: ClassVar[str] = "a4.audio_patch_batch.stage_failed"

    def __init__(self, message: str, *, error_code: AnalogFourExportErrorCode) -> None:
        super().__init__(message, context={"error_code": error_code})
        self.error_code: AnalogFourExportErrorCode = error_code


@dataclass(frozen=True)
class _AudioInference:
    feature_report: FeatureReport
    genome: AnalogFourPatchGenome
    audio_features_payload: AnalogFourPatchAudioFeaturesPayload
    genome_payload: AnalogFourPatchGenomePayload


@dataclass(frozen=True)
class _PreparedCandidate:
    candidate: AnalogFourPatchCandidate
    resonance_gene: AnalogFourPatchGene
    candidate_payload: AnalogFourPatchCandidatePayload
    deferred_rows: tuple[_DeferredGenePayload, ...]
    send_plan: AnalogFourPatchSendPlan
    send_plan_payload: AnalogFourPatchSendPlanPayload


@dataclass(frozen=True)
class _RenderedCandidate:
    prepared: _PreparedCandidate
    sysex_render: AnalogFourSavedKitRenderResult


@dataclass(frozen=True)
class _StagedCandidate:
    prepared: _PreparedCandidate
    sysex_path: Path
    sidecar_path: Path
    sysex_render: AnalogFourSavedKitRenderResult
    sidecar_bytes: bytes


@dataclass(frozen=True)
class _StagedBatch:
    inference: _AudioInference
    genome_sha256: str
    generation_id: str
    candidates: tuple[_StagedCandidate, ...]
    manifest_path: Path
    manifest_bytes: bytes


@dataclass(frozen=True)
class _BatchSources:
    audio_bytes: bytes
    source_kit_bytes: bytes
    audio_sha256: str
    source_kit_sha256: str


@dataclass(frozen=True)
class _PublishedBatch:
    candidates: tuple[AnalogFourPatchCandidateBatchResult, ...]
    manifest_write: WriteResult
    lock_cleanup_warning: str | None


def _json_bytes(payload: Mapping[str, object]) -> bytes:
    return encode_analog_four_patch_batch_json(payload)


def _sha256(data: bytes) -> str:
    return analog_four_patch_batch_sha256(data)


def _payload_sha256(payload: Mapping[str, object]) -> str:
    return analog_four_patch_batch_payload_sha256(payload)


def _publish_immutable_artifact(path: Path, data: bytes) -> WriteResult:
    return publish_immutable_artifact(path, data, writer=atomic_write)


def _acquire_batch_lock(
    lock_path: Path,
    *,
    generation_id: str,
    publication_nonce: str,
    audio_sha256: str,
    source_kit_sha256: str,
) -> WriteResult:
    return acquire_batch_lock(
        lock_path,
        generation_id=generation_id,
        publication_nonce=publication_nonce,
        audio_sha256=audio_sha256,
        source_kit_sha256=source_kit_sha256,
        writer=atomic_write,
    )


def _generation_id(  # noqa: PLR0913 - immutable identity includes all source hashes
    *,
    audio_name: str,
    source_kit_name: str,
    audio_sha256: str,
    source_kit_sha256: str,
    genome_sha256: str,
    inference: _AudioInference,
    track: int,
    candidates: tuple[_RenderedCandidate, ...],
) -> str:
    parts = [
        BATCH_SCHEMA_VERSION,
        CANDIDATE_SCHEMA_VERSION,
        SYSEX_COVERAGE_STATEMENT,
        _DEFERRED_REASON,
        FILTER2_RESONANCE_PARAMETER,
        "No MIDI or network operation was performed.",
        str(track),
        audio_name,
        source_kit_name,
        audio_sha256,
        source_kit_sha256,
        inference.feature_report.content_hash,
        _payload_sha256(inference.audio_features_payload),
        genome_sha256,
    ]
    for rendered in candidates:
        prepared = rendered.prepared
        applied_rows: Mapping[str, object] = {"rows": _applied_rows(rendered.sysex_render)}
        deferred_rows: Mapping[str, object] = {"rows": list(prepared.deferred_rows)}
        parts.extend(
            (
                str(prepared.candidate.column),
                _safe_segment(prepared.candidate.label),
                prepared.resonance_gene.value.screen_value,
                _payload_sha256(prepared.candidate_payload),
                _payload_sha256(prepared.send_plan_payload),
                _payload_sha256(applied_rows),
                _payload_sha256(deferred_rows),
                rendered.sysex_render.sha256,
            )
        )
    return _sha256("\0".join(parts).encode("utf-8"))[:32]


def _safe_segment(label: str) -> str:
    segment = _SAFE_SEGMENT_RE.sub("-", label.lower()).strip("-")[:40].rstrip("-")
    return segment or "candidate"


def _build_audio_inference(
    audio_path: Path,
    *,
    track: int,
    candidate_count: int,
) -> _AudioInference:
    from ...style_analysis.analog_four_patch_genome import analog_four_patch_genome_to_dict
    from ...style_analysis.analog_four_patch_inference import (
        analog_four_patch_audio_features_to_dict,
        build_analog_four_audio_patch_genome_isolated,
    )

    result = build_analog_four_audio_patch_genome_isolated(
        audio_path,
        track=track,
        candidate_count=candidate_count,
    )
    return _AudioInference(
        feature_report=result.feature_report,
        genome=result.genome,
        audio_features_payload=analog_four_patch_audio_features_to_dict(result.audio_features),
        genome_payload=analog_four_patch_genome_to_dict(result.genome),
    )


def _build_precomputed_audio_inference(value: object) -> _AudioInference:
    from ...style_analysis.analog_four_patch_genome import analog_four_patch_genome_to_dict
    from ...style_analysis.analog_four_patch_inference import (
        AnalogFourAudioPatchGenome,
        analog_four_patch_audio_features_to_dict,
    )

    if not isinstance(value, AnalogFourAudioPatchGenome):
        raise TypeError("audio_genome must be an AnalogFourAudioPatchGenome")
    candidates = value.genome.candidates
    if len(candidates) != 1 or candidates[0].column != 1:
        raise ValueError("audio_genome must contain exactly one candidate in column 1")
    return _AudioInference(
        feature_report=value.feature_report,
        genome=value.genome,
        audio_features_payload=analog_four_patch_audio_features_to_dict(value.audio_features),
        genome_payload=analog_four_patch_genome_to_dict(value.genome),
    )


def _build_send_plan(
    report: FeatureReport,
    genome: AnalogFourPatchGenome,
    *,
    selected_candidate: int,
) -> AnalogFourPatchSendPlan:
    from ...style_analysis.analog_four_patch_send_plan import (
        build_analog_four_patch_send_plan_from_genome,
    )

    return build_analog_four_patch_send_plan_from_genome(
        report,
        genome,
        selected_candidate=selected_candidate,
    )


def _runtime_int(value: object, *, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} must be an int")
    return value


def _validate_request(*, track: int, candidate_count: int, output_dir: Path) -> None:
    track = _runtime_int(track, label="track")
    candidate_count = _runtime_int(candidate_count, label="candidate_count")
    if track < ANALOG_FOUR_TRACK_MIN or track > ANALOG_FOUR_TRACK_MAX:
        raise ValueError(f"track must be in {ANALOG_FOUR_TRACK_MIN}..{ANALOG_FOUR_TRACK_MAX}")
    if (
        candidate_count < ANALOG_FOUR_PATCH_CANDIDATE_MIN
        or candidate_count > ANALOG_FOUR_PATCH_CANDIDATE_MAX
    ):
        raise ValueError(
            "candidate_count must be in "
            f"{ANALOG_FOUR_PATCH_CANDIDATE_MIN}..{ANALOG_FOUR_PATCH_CANDIDATE_MAX}"
        )
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError(f"output_dir is not a directory: {output_dir}")


def _filter2_resonance_gene(
    candidate: AnalogFourPatchCandidate,
    *,
    track: int,
) -> AnalogFourPatchGene:
    matches = tuple(
        gene for gene in candidate.genes if gene.value.parameter == FILTER2_RESONANCE_PARAMETER
    )
    if len(matches) != 1:
        raise ValueError(
            f"candidate {candidate.column} must contain exactly one {FILTER2_RESONANCE_PARAMETER} gene"
        )
    gene = matches[0]
    if gene.track != track:
        raise ValueError(
            f"candidate {candidate.column} Filter2 Resonance targets track {gene.track}, expected {track}"
        )
    try:
        value = int(gene.value.screen_value)
    except ValueError as exc:
        raise ValueError("Filter2 Resonance screen value must be a decimal integer") from exc
    if str(value) != gene.value.screen_value or not 0 <= value <= _MIDI_DATA_MAX:
        raise ValueError("Filter2 Resonance screen value must be in 0..127")
    return gene


def _deferred_gene_payload(row: AnalogFourPatchGenePayload) -> _DeferredGenePayload:
    return {
        "track": row["track"],
        "family": row["family"],
        "rationale": row["rationale"],
        "confidence": row["confidence"],
        "value": row["value"],
        "deferred_reason": _DEFERRED_REASON,
    }


def _candidate_paths(
    output_dir: Path,
    candidate: AnalogFourPatchCandidate,
    track: int,
    generation_id: str,
) -> tuple[Path, Path]:
    stem = (
        f"a4-t{track}-g{generation_id}-c{candidate.column:02d}-" f"{_safe_segment(candidate.label)}"
    )
    return output_dir / f"{stem}.syx", output_dir / f"{stem}.json"


def _prepare_candidates(
    inference: _AudioInference,
    *,
    track: int,
    candidate_count: int,
) -> tuple[_PreparedCandidate, ...]:
    candidates = tuple(sorted(inference.genome.candidates, key=lambda item: item.column))
    expected_columns = tuple(range(1, candidate_count + 1))
    if (
        len(candidates) != candidate_count
        or tuple(item.column for item in candidates) != expected_columns
    ):
        raise ValueError("inference genome must contain contiguous candidate columns for the batch")

    prepared: list[_PreparedCandidate] = []
    for candidate in candidates:
        resonance_gene = _filter2_resonance_gene(candidate, track=track)
        candidate_payload = analog_four_patch_candidate_to_dict(candidate)
        rows = tuple(candidate_payload["genes"])
        deferred_rows = tuple(
            _deferred_gene_payload(row)
            for gene, row in zip(candidate.genes, rows, strict=True)
            if gene.value.parameter != FILTER2_RESONANCE_PARAMETER
        )
        send_plan = _build_send_plan(
            inference.feature_report,
            inference.genome,
            selected_candidate=candidate.column,
        )
        prepared.append(
            _PreparedCandidate(
                candidate=candidate,
                resonance_gene=resonance_gene,
                candidate_payload=candidate_payload,
                deferred_rows=deferred_rows,
                send_plan=send_plan,
                send_plan_payload=analog_four_patch_send_plan_to_dict(send_plan),
            )
        )
    return tuple(prepared)


def _preflight_destinations(paths: tuple[Path, ...], *, overwrite: bool) -> None:
    _validate_unique_destinations(paths)
    if not overwrite:
        for path in paths:
            if path.exists():
                raise FileExistsError(
                    f"refusing to overwrite existing file: {path} (pass overwrite=True to allow)"
                )


def _validate_unique_destinations(paths: tuple[Path, ...]) -> None:
    if len(paths) != len(set(paths)):
        raise ValueError("generated batch destinations are not unique")


def _applied_rows(render: AnalogFourSavedKitRenderResult) -> list[_HardwareAppliedRowPayload]:
    return [
        {
            "parameter": row.parameter,
            "track": row.track,
            "screen_value": row.screen_value,
            "unpacked_offset": row.unpacked_offset,
            "source_unpacked_value": row.source_unpacked_value,
            "rendered_unpacked_value": row.rendered_unpacked_value,
        }
        for row in render.applied_mutations
    ]


def _coverage_counts(
    prepared: _PreparedCandidate,
    render: AnalogFourSavedKitRenderResult,
) -> _CoverageCountsPayload:
    return {
        "dna_row_count": len(prepared.candidate.genes),
        "sysex_encoded_row_count": len(render.applied_mutations),
        "deferred_row_count": len(prepared.deferred_rows),
        "sendable_row_count": prepared.send_plan.summary.sendable_count,
        "manual_row_count": prepared.send_plan.summary.manual_count,
    }


def _sidecar_payload(  # noqa: PLR0913 - schema builder mirrors artifact fields
    prepared: _PreparedCandidate,
    render: AnalogFourSavedKitRenderResult,
    inference: _AudioInference,
    *,
    sysex_path: Path,
    audio_name: str,
    source_kit_name: str,
    audio_sha256: str,
    source_kit_sha256: str,
    genome_sha256: str,
    generation_id: str,
) -> _CandidateSidecarPayload:
    applied_rows = _applied_rows(render)
    coverage = _coverage_counts(prepared, render)
    return {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "generation_id": generation_id,
        "audio_source": {"filename": audio_name},
        "source_kit": {"filename": source_kit_name},
        "candidate_dna": prepared.candidate_payload,
        "audio_features": inference.audio_features_payload,
        "dynamic_send_plan": prepared.send_plan_payload,
        "hardware_applied_rows": applied_rows,
        "deferred_rows": list(prepared.deferred_rows),
        "coverage_counts": coverage,
        "hardware_export": {
            "sysex_filename": sysex_path.name,
            "encoded_parameters": [FILTER2_RESONANCE_PARAMETER],
            "coverage_statement": SYSEX_COVERAGE_STATEMENT,
        },
        "hashes": {
            "audio_sha256": audio_sha256,
            "source_kit_sha256": source_kit_sha256,
            "genome_sha256": genome_sha256,
            "candidate_dna_sha256": _payload_sha256(prepared.candidate_payload),
            "send_plan_sha256": _payload_sha256(prepared.send_plan_payload),
            "sysex_sha256": render.sha256,
        },
        "safety": [SYSEX_COVERAGE_STATEMENT, "No MIDI or network operation was performed."],
    }


def _candidate_result(
    prepared: _PreparedCandidate,
    sysex_render: AnalogFourSavedKitRenderResult,
    sidecar_bytes: bytes,
    *,
    sysex_write: WriteResult,
    sidecar_write: WriteResult,
) -> AnalogFourPatchCandidateBatchResult:
    coverage = _coverage_counts(prepared, sysex_render)
    return AnalogFourPatchCandidateBatchResult(
        column=prepared.candidate.column,
        label=prepared.candidate.label,
        filter2_resonance=prepared.resonance_gene.value.screen_value,
        sysex_export=AnalogFourSavedKitExportResult(render=sysex_render, write=sysex_write),
        sidecar_write=sidecar_write,
        sidecar_sha256=_sha256(sidecar_bytes),
        dna_row_count=coverage["dna_row_count"],
        sysex_encoded_row_count=coverage["sysex_encoded_row_count"],
        deferred_row_count=coverage["deferred_row_count"],
        sendable_row_count=coverage["sendable_row_count"],
        manual_row_count=coverage["manual_row_count"],
    )


def _manifest_payload(  # noqa: PLR0913 - schema builder mirrors manifest fields
    inference: _AudioInference,
    staged_candidates: tuple[_StagedCandidate, ...],
    *,
    track: int,
    audio_name: str,
    source_kit_name: str,
    audio_sha256: str,
    source_kit_sha256: str,
    genome_sha256: str,
    generation_id: str,
) -> _BatchManifestPayload:
    candidate_coverage = tuple(
        _coverage_counts(item.prepared, item.sysex_render) for item in staged_candidates
    )
    candidates: list[_ManifestCandidatePayload] = [
        {
            "column": item.prepared.candidate.column,
            "label": item.prepared.candidate.label,
            "filter2_resonance": item.prepared.resonance_gene.value.screen_value,
            "sysex_filename": item.sysex_path.name,
            "sidecar_filename": item.sidecar_path.name,
            "sysex_sha256": item.sysex_render.sha256,
            "sidecar_sha256": _sha256(item.sidecar_bytes),
            "coverage_counts": item_coverage,
        }
        for item, item_coverage in zip(staged_candidates, candidate_coverage, strict=True)
    ]
    coverage: _CoverageCountsPayload = {
        "dna_row_count": sum(item["dna_row_count"] for item in candidate_coverage),
        "sysex_encoded_row_count": sum(
            item["sysex_encoded_row_count"] for item in candidate_coverage
        ),
        "deferred_row_count": sum(item["deferred_row_count"] for item in candidate_coverage),
        "sendable_row_count": sum(item["sendable_row_count"] for item in candidate_coverage),
        "manual_row_count": sum(item["manual_row_count"] for item in candidate_coverage),
    }
    return {
        "schema_version": BATCH_SCHEMA_VERSION,
        "generation_id": generation_id,
        "track": track,
        "candidate_count": len(staged_candidates),
        "audio_source": {"filename": audio_name, "sha256": audio_sha256},
        "source_kit": {"filename": source_kit_name, "sha256": source_kit_sha256},
        "feature_report_hash": inference.feature_report.content_hash,
        "genome_sha256": genome_sha256,
        "genome": inference.genome_payload,
        "candidates": candidates,
        "coverage_counts": coverage,
        "safety": [SYSEX_COVERAGE_STATEMENT, "No MIDI or network operation was performed."],
    }


def _stage_input_snapshots(
    *,
    audio_path: Path,
    audio_bytes: bytes,
    source_kit_bytes: bytes,
    staging_dir: Path,
) -> tuple[Path, bytes]:
    audio_snapshot = staging_dir / f"audio{audio_path.suffix or '.bin'}"
    source_kit_snapshot = staging_dir / "source-kit.syx"
    atomic_write(audio_snapshot, audio_bytes)
    atomic_write(source_kit_snapshot, source_kit_bytes)
    return audio_snapshot, source_kit_snapshot.read_bytes()


def _render_inferred_candidates(
    inference: _AudioInference,
    source_kit_snapshot_bytes: bytes,
    *,
    track: int,
    candidate_count: int,
) -> tuple[_RenderedCandidate, ...]:
    prepared = _prepare_candidates(
        inference,
        track=track,
        candidate_count=candidate_count,
    )
    saved_kit_capability = get_analog_four_saved_kit_capability()
    return tuple(
        _RenderedCandidate(
            prepared=item,
            sysex_render=saved_kit_capability.render_saved_kit(
                source_kit_snapshot_bytes,
                (
                    AnalogFourSavedKitMutation(
                        parameter=FILTER2_RESONANCE_PARAMETER,
                        track=track,
                        screen_value=item.resonance_gene.value.screen_value,
                    ),
                ),
            ),
        )
        for item in prepared
    )


def _stage_candidate_artifacts(  # noqa: PLR0913 - staged pipeline passes immutable context
    inference: _AudioInference,
    rendered_candidates: tuple[_RenderedCandidate, ...],
    *,
    audio_path: Path,
    source_kit_path: Path,
    audio_sha256: str,
    source_kit_sha256: str,
    genome_sha256: str,
    generation_id: str,
    output_dir: Path,
    track: int,
) -> tuple[_StagedCandidate, ...]:
    staged_candidates: list[_StagedCandidate] = []
    for rendered in rendered_candidates:
        item = rendered.prepared
        sysex_path, sidecar_path = _candidate_paths(
            output_dir,
            item.candidate,
            track,
            generation_id,
        )
        sidecar_bytes = _json_bytes(
            _sidecar_payload(
                item,
                rendered.sysex_render,
                inference,
                sysex_path=sysex_path,
                audio_name=audio_path.name,
                source_kit_name=source_kit_path.name,
                audio_sha256=audio_sha256,
                source_kit_sha256=source_kit_sha256,
                genome_sha256=genome_sha256,
                generation_id=generation_id,
            )
        )
        staged_candidates.append(
            _StagedCandidate(
                prepared=item,
                sysex_path=sysex_path,
                sidecar_path=sidecar_path,
                sysex_render=rendered.sysex_render,
                sidecar_bytes=sidecar_bytes,
            )
        )
    return tuple(staged_candidates)


def _assemble_staged_batch(  # noqa: PLR0913 - staged pipeline passes immutable context
    inference: _AudioInference,
    staged_candidates: tuple[_StagedCandidate, ...],
    *,
    audio_path: Path,
    source_kit_path: Path,
    audio_sha256: str,
    source_kit_sha256: str,
    genome_sha256: str,
    generation_id: str,
    output_dir: Path,
    track: int,
) -> _StagedBatch:
    manifest_path = output_dir / f"a4-t{track}-audio-patch-batch.json"
    manifest_bytes = _json_bytes(
        _manifest_payload(
            inference,
            staged_candidates,
            track=track,
            audio_name=audio_path.name,
            source_kit_name=source_kit_path.name,
            audio_sha256=audio_sha256,
            source_kit_sha256=source_kit_sha256,
            genome_sha256=genome_sha256,
            generation_id=generation_id,
        )
    )
    destinations = tuple(
        path for item in staged_candidates for path in (item.sysex_path, item.sidecar_path)
    ) + (manifest_path,)
    _validate_unique_destinations(destinations)
    return _StagedBatch(
        inference=inference,
        genome_sha256=genome_sha256,
        generation_id=generation_id,
        candidates=staged_candidates,
        manifest_path=manifest_path,
        manifest_bytes=manifest_bytes,
    )


def _infer_parent_owned_audio_snapshot(
    audio_snapshot: Path,
    *,
    audio_sha256: str,
    track: int,
    candidate_count: int,
) -> tuple[_AudioInference, str]:
    try:
        inference = _build_audio_inference(
            audio_snapshot,
            track=track,
            candidate_count=candidate_count,
        )
    except StyleAnalysisDependencyError as exc:
        raise AnalogFourPatchBatchStageError(
            str(exc),
            error_code="dependency_missing",
        ) from exc
    except BoundaryError as exc:
        boundary_code = exc.context.get("error_code")
        error_code: AnalogFourExportErrorCode = (
            "audio_read_failed" if boundary_code == "audio_read_failed" else "inference_failed"
        )
        raise AnalogFourPatchBatchStageError(
            str(exc),
            error_code=error_code,
        ) from exc
    except OSError as exc:
        raise AnalogFourPatchBatchStageError(
            str(exc),
            error_code="audio_read_failed",
        ) from exc
    except RuntimeError as exc:
        raise AnalogFourPatchBatchStageError(
            str(exc),
            error_code="inference_failed",
        ) from exc
    if inference.audio_features_payload["audio_sha256"] != audio_sha256:
        raise ValueError("audio snapshot hash does not match patch inference provenance")
    return inference, _payload_sha256(inference.genome_payload)


def _validate_precomputed_audio_inference(
    inference: _AudioInference,
    *,
    audio_sha256: str,
) -> tuple[_AudioInference, str]:
    if inference.audio_features_payload["audio_sha256"] != audio_sha256:
        raise ValueError("audio snapshot hash does not match patch inference provenance")
    return inference, _payload_sha256(inference.genome_payload)


def _render_and_identify_batch(  # noqa: PLR0913 - render boundary needs source identity
    inference: _AudioInference,
    source_kit_snapshot_bytes: bytes,
    *,
    audio_path: Path,
    source_kit_path: Path,
    audio_sha256: str,
    source_kit_sha256: str,
    genome_sha256: str,
    track: int,
    candidate_count: int,
) -> tuple[tuple[_RenderedCandidate, ...], str]:
    rendered_candidates = _render_inferred_candidates(
        inference,
        source_kit_snapshot_bytes,
        track=track,
        candidate_count=candidate_count,
    )
    generation_id = _generation_id(
        audio_name=audio_path.name,
        source_kit_name=source_kit_path.name,
        audio_sha256=audio_sha256,
        source_kit_sha256=source_kit_sha256,
        genome_sha256=genome_sha256,
        inference=inference,
        track=track,
        candidates=rendered_candidates,
    )
    return rendered_candidates, generation_id


def _stage_batch(  # noqa: PLR0913 - private staging boundary is intentionally explicit
    *,
    audio_path: Path,
    source_kit_path: Path,
    audio_bytes: bytes,
    source_kit_bytes: bytes,
    audio_sha256: str,
    source_kit_sha256: str,
    output_dir: Path,
    track: int,
    candidate_count: int,
    inference_override: _AudioInference | None,
) -> _StagedBatch:
    """Build every artifact in parent-owned private storage."""

    with tempfile.TemporaryDirectory(prefix="a4-audio-patch-batch-") as temp_name:
        audio_snapshot, source_kit_snapshot_bytes = _stage_input_snapshots(
            audio_path=audio_path,
            audio_bytes=audio_bytes,
            source_kit_bytes=source_kit_bytes,
            staging_dir=Path(temp_name),
        )
        if inference_override is None:
            inference, genome_sha256 = _infer_parent_owned_audio_snapshot(
                audio_snapshot,
                audio_sha256=audio_sha256,
                track=track,
                candidate_count=candidate_count,
            )
        else:
            inference, genome_sha256 = _validate_precomputed_audio_inference(
                inference_override,
                audio_sha256=audio_sha256,
            )
        rendered_candidates, generation_id = _render_and_identify_batch(
            inference,
            source_kit_snapshot_bytes,
            audio_path=audio_path,
            source_kit_path=source_kit_path,
            audio_sha256=audio_sha256,
            source_kit_sha256=source_kit_sha256,
            genome_sha256=genome_sha256,
            track=track,
            candidate_count=candidate_count,
        )
        staged_candidates = _stage_candidate_artifacts(
            inference,
            rendered_candidates,
            audio_path=audio_path,
            source_kit_path=source_kit_path,
            audio_sha256=audio_sha256,
            source_kit_sha256=source_kit_sha256,
            genome_sha256=genome_sha256,
            generation_id=generation_id,
            output_dir=output_dir,
            track=track,
        )
        return _assemble_staged_batch(
            inference,
            staged_candidates,
            audio_path=audio_path,
            source_kit_path=source_kit_path,
            audio_sha256=audio_sha256,
            source_kit_sha256=source_kit_sha256,
            genome_sha256=genome_sha256,
            generation_id=generation_id,
            output_dir=output_dir,
            track=track,
        )


def _batch_export_error_code(  # noqa: PLR0911 - ordered fail-closed classifier
    exc: BaseException,
    *,
    source_reads_complete: bool,
    output_phase_started: bool,
) -> AnalogFourExportErrorCode:
    if isinstance(exc, (KeyboardInterrupt, SystemExit)):
        return "interrupted"
    if isinstance(
        exc,
        (
            AnalogFourPatchBatchStageError,
            AnalogFourPatchBatchPublicationError,
            AnalogFourPatchBatchLockedError,
        ),
    ):
        return exc.error_code
    if isinstance(exc, FileNotFoundError):
        if not source_reads_complete:
            return "input_not_found"
        return "write_failed" if output_phase_started else "inference_failed"
    if isinstance(exc, PermissionError):
        return "permission_denied"
    if isinstance(exc, ImportError):
        return "service_unavailable"
    if isinstance(exc, FileExistsError):
        return "overwrite_refused"
    if isinstance(exc, OSError):
        if not source_reads_complete:
            return "source_read_failed"
        return "write_failed" if output_phase_started else "inference_failed"
    if isinstance(exc, (KeyError, TypeError, ValueError)):
        return "validation"
    return "inference_failed"


def _read_batch_sources(  # noqa: PLR0913 - source snapshot boundary is explicit
    *,
    audio_path: Path,
    source_kit_path: Path,
    output_dir: Path,
    track: int,
    candidate_count: int,
    overwrite: bool,
) -> _BatchSources:
    _validate_request(track=track, candidate_count=candidate_count, output_dir=output_dir)
    audio_bytes = audio_path.read_bytes()
    source_kit_bytes = source_kit_path.read_bytes()
    manifest_path = output_dir / f"a4-t{track}-audio-patch-batch.json"
    _preflight_destinations((manifest_path,), overwrite=overwrite)
    return _BatchSources(
        audio_bytes=audio_bytes,
        source_kit_bytes=source_kit_bytes,
        audio_sha256=_sha256(audio_bytes),
        source_kit_sha256=_sha256(source_kit_bytes),
    )


def _stage_batch_request(  # noqa: PLR0913 - request fields remain typed and explicit
    *,
    audio_path: Path,
    source_kit_path: Path,
    output_dir: Path,
    sources: _BatchSources,
    track: int,
    candidate_count: int,
    inference_override: _AudioInference | None,
) -> _StagedBatch:
    try:
        return _stage_batch(
            audio_path=audio_path,
            source_kit_path=source_kit_path,
            audio_bytes=sources.audio_bytes,
            source_kit_bytes=sources.source_kit_bytes,
            audio_sha256=sources.audio_sha256,
            source_kit_sha256=sources.source_kit_sha256,
            output_dir=output_dir,
            track=track,
            candidate_count=candidate_count,
            inference_override=inference_override,
        )
    except AnalogFourPatchBatchStageError:
        raise
    except OSError as exc:
        raise AnalogFourPatchBatchStageError(
            str(exc),
            error_code="write_failed",
        ) from exc


def _publish_candidate_artifacts(
    staged_batch: _StagedBatch,
) -> tuple[AnalogFourPatchCandidateBatchResult, ...]:
    results: list[AnalogFourPatchCandidateBatchResult] = []
    for staged_candidate in staged_batch.candidates:
        sysex_write = _publish_immutable_artifact(
            staged_candidate.sysex_path,
            staged_candidate.sysex_render.framed_sysex,
        )
        sidecar_write = _publish_immutable_artifact(
            staged_candidate.sidecar_path,
            staged_candidate.sidecar_bytes,
        )
        results.append(
            _candidate_result(
                staged_candidate.prepared,
                staged_candidate.sysex_render,
                staged_candidate.sidecar_bytes,
                sysex_write=sysex_write,
                sidecar_write=sidecar_write,
            )
        )
    return tuple(results)


def _cleanup_publication_lock(  # noqa: PLR0913 - cleanup requires complete owner identity
    *,
    lock_path: Path,
    lock_write: WriteResult | None,
    staged_batch: _StagedBatch,
    publication_nonce: str,
    sources: _BatchSources,
    manifest_committed: bool,
) -> str | None:
    active_exception = sys.exception()
    owns_lock = lock_write is not None
    if not owns_lock and isinstance(active_exception, (KeyboardInterrupt, SystemExit)):
        owns_lock = _batch_lock_matches_request(
            lock_path,
            generation_id=staged_batch.generation_id,
            publication_nonce=publication_nonce,
            audio_sha256=sources.audio_sha256,
            source_kit_sha256=sources.source_kit_sha256,
        )
    if not owns_lock:
        return None
    owner = {
        "generation_id": staged_batch.generation_id,
        "publication_nonce": publication_nonce,
        "audio_sha256": sources.audio_sha256,
        "source_kit_sha256": sources.source_kit_sha256,
    }
    try:
        cleanup_failure = _release_batch_lock(lock_path, **owner)
    except (KeyboardInterrupt, SystemExit) as exc:
        cleanup_failure = f"{lock_path.name}: {type(exc).__name__}; " + (
            "lock cleanup interrupted after manifest commit"
            if manifest_committed
            else "lock cleanup interrupted while publication failed"
        )
        try:
            retry_failure = _release_batch_lock(lock_path, **owner)
        except (KeyboardInterrupt, SystemExit) as retry_exc:
            retry_failure = (
                f"{lock_path.name}: {type(retry_exc).__name__}; "
                "best-effort cleanup retry interrupted"
            )
        if retry_failure is None:
            cleanup_failure += "; best-effort cleanup retry completed"
        else:
            cleanup_failure += "; retry result: " + retry_failure
    if cleanup_failure is None:
        return None
    metrics = get_metrics()
    metrics.record_error("a4_audio_patch_batch_lock_cleanup")
    if active_exception is not None:
        active_exception.add_note("batch lock cleanup failure: " + cleanup_failure)
    _logger.error(
        "Analog Four audio patch batch lock cleanup failed",
        extra={
            "operation": "a4_audio_patch_batch_lock_cleanup",
            "error_code": "lock_cleanup_failed",
            "fingerprint": _LOCK_CLEANUP_FAILURE_FINGERPRINT,
            "detail": cleanup_failure,
            "metrics_summary": metrics.format_summary(),
        },
    )
    return cleanup_failure


def _publish_staged_batch(
    staged_batch: _StagedBatch,
    *,
    output_dir: Path,
    sources: _BatchSources,
    track: int,
    overwrite: bool,
) -> _PublishedBatch:
    lock_path = output_dir / f".a4-t{track}-audio-patch-batch.lock"
    publication_nonce = secrets.token_hex(16)
    lock_write: WriteResult | None = None
    manifest_committed = False
    try:
        lock_write = _acquire_batch_lock(
            lock_path,
            generation_id=staged_batch.generation_id,
            publication_nonce=publication_nonce,
            audio_sha256=sources.audio_sha256,
            source_kit_sha256=sources.source_kit_sha256,
        )
        _preflight_destinations((staged_batch.manifest_path,), overwrite=overwrite)
        candidates = _publish_candidate_artifacts(staged_batch)
        manifest_write = atomic_write(
            staged_batch.manifest_path,
            staged_batch.manifest_bytes,
            overwrite=overwrite,
        )
        manifest_committed = True
    finally:
        cleanup_failure = _cleanup_publication_lock(
            lock_path=lock_path,
            lock_write=lock_write,
            staged_batch=staged_batch,
            publication_nonce=publication_nonce,
            sources=sources,
            manifest_committed=manifest_committed,
        )
    warning = None
    if cleanup_failure is not None:
        warning = (
            "batch committed successfully but publication lock cleanup failed; "
            f"recovery metadata remains at {lock_path.name}: {cleanup_failure}"
        )
    return _PublishedBatch(
        candidates=candidates,
        manifest_write=manifest_write,
        lock_cleanup_warning=warning,
    )


def _batch_export_result(
    staged_batch: _StagedBatch,
    published_batch: _PublishedBatch,
    *,
    sources: _BatchSources,
    track: int,
) -> AnalogFourAudioPatchBatchExportResult:
    return AnalogFourAudioPatchBatchExportResult(
        track=track,
        candidate_count=len(published_batch.candidates),
        audio_sha256=sources.audio_sha256,
        source_kit_sha256=sources.source_kit_sha256,
        feature_report_hash=staged_batch.inference.feature_report.content_hash,
        genome_sha256=staged_batch.genome_sha256,
        generation_id=staged_batch.generation_id,
        candidates=published_batch.candidates,
        manifest_write=published_batch.manifest_write,
        manifest_sha256=_sha256(staged_batch.manifest_bytes),
        lock_cleanup_warning=published_batch.lock_cleanup_warning,
    )


def _record_batch_export_failure(  # noqa: PLR0913 - telemetry retains bounded context
    exc: BaseException,
    *,
    audio_path: Path,
    source_kit_path: Path,
    output_dir: Path,
    started_at: float,
    source_reads_complete: bool,
    output_phase_started: bool,
) -> None:
    if isinstance(exc, (KeyboardInterrupt, SystemExit)):
        error_code: AnalogFourExportErrorCode = "interrupted"
    elif isinstance(exc, Exception):
        error_code = _batch_export_error_code(
            exc,
            source_reads_complete=source_reads_complete,
            output_phase_started=output_phase_started,
        )
    else:
        error_code = "write_failed" if output_phase_started else "inference_failed"
    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics = get_metrics()
    metrics.record_export(duration_ms, error_code=error_code)
    _logger.warning(
        "Analog Four audio patch batch export failed",
        extra={
            "operation": "a4_audio_patch_batch_export",
            "outcome": "failed",
            "error_code": error_code,
            "fingerprint": getattr(exc, "fingerprint", _EXPORT_FAILURE_FINGERPRINT),
            "error_type": type(exc).__name__,
            "audio_name": analog_four_export_path_name(audio_path),
            "source_kit_name": analog_four_export_path_name(source_kit_path),
            "output_dir_name": analog_four_export_path_name(output_dir),
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )
    if isinstance(exc, Exception):
        attach_analog_four_export_error_code(exc, error_code)


def _record_batch_export_success(
    result: AnalogFourAudioPatchBatchExportResult,
    *,
    output_dir: Path,
    started_at: float,
) -> None:
    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics = get_metrics()
    metrics.record_export(duration_ms)
    _logger.info(
        "Analog Four audio patch batch export completed",
        extra={
            "operation": "a4_audio_patch_batch_export",
            "outcome": "completed",
            "output_dir_name": output_dir.name,
            "manifest_sha256": result.manifest_sha256,
            "candidate_count": result.candidate_count,
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )


def _execute_analog_four_audio_patch_batch(  # noqa: PLR0913 - service boundary mirrors request
    *,
    audio_path: Path,
    source_kit_path: Path,
    output_dir: Path,
    track: int,
    candidate_count: int,
    overwrite: bool,
    inference_override: _AudioInference | None = None,
) -> AnalogFourAudioPatchBatchExportResult:
    started_at = time.perf_counter()
    source_reads_complete = False
    output_phase_started = False
    try:
        audio_path = require_analog_four_export_path(audio_path, field_name="audio_path")
        source_kit_path = require_analog_four_export_path(
            source_kit_path,
            field_name="source_kit_path",
        )
        output_dir = require_analog_four_export_path(output_dir, field_name="output_dir")
        sources = _read_batch_sources(
            audio_path=audio_path,
            source_kit_path=source_kit_path,
            output_dir=output_dir,
            track=track,
            candidate_count=candidate_count,
            overwrite=overwrite,
        )
        source_reads_complete = True
        staged_batch = _stage_batch_request(
            audio_path=audio_path,
            source_kit_path=source_kit_path,
            output_dir=output_dir,
            sources=sources,
            track=track,
            candidate_count=candidate_count,
            inference_override=inference_override,
        )
        output_phase_started = True
        published_batch = _publish_staged_batch(
            staged_batch,
            output_dir=output_dir,
            sources=sources,
            track=track,
            overwrite=overwrite,
        )
        result = _batch_export_result(
            staged_batch,
            published_batch,
            sources=sources,
            track=track,
        )
    except (KeyboardInterrupt, SystemExit) as exc:
        _record_batch_export_failure(
            exc,
            audio_path=audio_path,
            source_kit_path=source_kit_path,
            output_dir=output_dir,
            started_at=started_at,
            source_reads_complete=source_reads_complete,
            output_phase_started=output_phase_started,
        )
        raise
    except (ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        _record_batch_export_failure(
            exc,
            audio_path=audio_path,
            source_kit_path=source_kit_path,
            output_dir=output_dir,
            started_at=started_at,
            source_reads_complete=source_reads_complete,
            output_phase_started=output_phase_started,
        )
        raise
    _record_batch_export_success(result, output_dir=output_dir, started_at=started_at)
    return result


def export_selected_analog_four_audio_patch(
    *,
    audio_path: Path,
    source_kit_path: Path,
    output_dir: Path,
    audio_genome: AnalogFourAudioPatchGenome,
    overwrite: bool = False,
) -> AnalogFourAudioPatchBatchExportResult:
    """Render one preselected, audio-provenanced A4 candidate offline."""

    inference = _build_precomputed_audio_inference(audio_genome)
    track = inference.genome.selected_track
    with trace_operation(
        "a4_audio_patch_selected_export",
        logger=_logger,
        audio_name=analog_four_export_path_name(audio_path),
        source_kit_name=analog_four_export_path_name(source_kit_path),
        output_dir_name=analog_four_export_path_name(output_dir),
        track=track,
        candidate_count=1,
    ):
        return _execute_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=source_kit_path,
            output_dir=output_dir,
            track=track,
            candidate_count=1,
            overwrite=overwrite,
            inference_override=inference,
        )


def export_analog_four_audio_patch_batch(  # noqa: PLR0913 - public API mirrors request
    *,
    audio_path: Path,
    source_kit_path: Path,
    output_dir: Path,
    track: int = 1,
    candidate_count: int = ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    overwrite: bool = False,
) -> AnalogFourAudioPatchBatchExportResult:
    """Infer, render, and atomically describe an offline A4 candidate batch."""

    with trace_operation(
        "a4_audio_patch_batch_export",
        logger=_logger,
        audio_name=analog_four_export_path_name(audio_path),
        source_kit_name=analog_four_export_path_name(source_kit_path),
        output_dir_name=analog_four_export_path_name(output_dir),
        track=track,
        candidate_count=candidate_count,
    ):
        return _execute_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=source_kit_path,
            output_dir=output_dir,
            track=track,
            candidate_count=candidate_count,
            overwrite=overwrite,
            inference_override=None,
        )


__all__ = [
    "AnalogFourAudioPatchBatchExportResult",
    "AnalogFourPatchCandidateBatchResult",
    "BATCH_SCHEMA_VERSION",
    "CANDIDATE_SCHEMA_VERSION",
    "FILTER2_RESONANCE_PARAMETER",
    "SYSEX_COVERAGE_STATEMENT",
    "export_analog_four_audio_patch_batch",
    "export_selected_analog_four_audio_patch",
]
