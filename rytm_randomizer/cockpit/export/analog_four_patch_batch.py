"""Guarded audio-to-candidate batch export for Analog Four MKII saved kits."""

from __future__ import annotations

import re
import secrets
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final

from ...data.analog_four_sysex_calibration import A4_FILTER2_RESONANCE_PARAMETER
from ...devices.analog_four import (
    AnalogFourSavedKitMutation,
    AnalogFourSavedKitRenderResult,
    get_analog_four_saved_kit_capability,
)
from ...observability.errors import BoundaryError
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
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
    attach_analog_four_export_error_code,
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

FILTER2_RESONANCE_PARAMETER: Final[str] = A4_FILTER2_RESONANCE_PARAMETER
_DEFERRED_REASON: Final[str] = "not hardware-write-validated for saved-kit SysEx"
_SAFE_SEGMENT_RE: Final[re.Pattern[str]] = re.compile(r"[^a-z0-9]+")
_logger = get_logger(__name__)


class AnalogFourPatchBatchStageError(BoundaryError, RuntimeError):
    """Classified failure while analyzing or staging one A4 patch batch."""

    fingerprint = "a4.audio_patch_batch.stage_failed"

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
    sysex_export: AnalogFourSavedKitExportResult


@dataclass(frozen=True)
class _StagedCandidate:
    prepared: _PreparedCandidate
    sysex_path: Path
    sidecar_path: Path
    sysex_export: AnalogFourSavedKitExportResult
    sidecar_bytes: bytes


@dataclass(frozen=True)
class _StagedBatch:
    inference: _AudioInference
    genome_sha256: str
    generation_id: str
    candidates: tuple[_StagedCandidate, ...]
    manifest_path: Path
    manifest_bytes: bytes


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


render_analog_four_saved_kit: Callable[
    [bytes, tuple[AnalogFourSavedKitMutation, ...]],
    AnalogFourSavedKitRenderResult,
] = get_analog_four_saved_kit_capability().render_saved_kit


def _generation_id(
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
        applied_rows: Mapping[str, object] = {"rows": _applied_rows(rendered.sysex_export)}
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
                rendered.sysex_export.render.sha256,
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
        build_analog_four_audio_patch_genome,
    )

    result = build_analog_four_audio_patch_genome(
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


def _validate_request(*, track: int, candidate_count: int, output_dir: Path) -> None:
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
    if str(value) != gene.value.screen_value or not 0 <= value <= 127:
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


def _applied_rows(export: AnalogFourSavedKitExportResult) -> list[_HardwareAppliedRowPayload]:
    return [
        {
            "parameter": row.parameter,
            "track": row.track,
            "screen_value": row.screen_value,
            "unpacked_offset": row.unpacked_offset,
            "source_unpacked_value": row.source_unpacked_value,
            "rendered_unpacked_value": row.rendered_unpacked_value,
        }
        for row in export.render.applied_mutations
    ]


def _sidecar_payload(
    prepared: _PreparedCandidate,
    export: AnalogFourSavedKitExportResult,
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
    applied_rows = _applied_rows(export)
    coverage: _CoverageCountsPayload = {
        "dna_row_count": len(prepared.candidate.genes),
        "sysex_encoded_row_count": len(applied_rows),
        "deferred_row_count": len(prepared.deferred_rows),
        "sendable_row_count": prepared.send_plan.summary.sendable_count,
        "manual_row_count": prepared.send_plan.summary.manual_count,
    }
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
            "sysex_sha256": export.render.sha256,
        },
        "safety": [SYSEX_COVERAGE_STATEMENT, "No MIDI or network operation was performed."],
    }


def _candidate_result(
    prepared: _PreparedCandidate,
    sysex_path: Path,
    sidecar_path: Path,
    sysex_export: AnalogFourSavedKitExportResult,
    sidecar_bytes: bytes,
    *,
    sysex_write: WriteResult | None = None,
    sidecar_write: WriteResult | None = None,
) -> AnalogFourPatchCandidateBatchResult:
    settled_sysex_write = sysex_write or WriteResult(
        path=sysex_path.resolve(),
        bytes_written=len(sysex_export.render.framed_sysex),
        overwrote_existing=False,
    )
    settled_sidecar_write = sidecar_write or WriteResult(
        path=sidecar_path.resolve(),
        bytes_written=len(sidecar_bytes),
        overwrote_existing=False,
    )
    return AnalogFourPatchCandidateBatchResult(
        column=prepared.candidate.column,
        label=prepared.candidate.label,
        filter2_resonance=prepared.resonance_gene.value.screen_value,
        sysex_export=replace(sysex_export, write=settled_sysex_write),
        sidecar_write=settled_sidecar_write,
        sidecar_sha256=_sha256(sidecar_bytes),
        dna_row_count=len(prepared.candidate.genes),
        sysex_encoded_row_count=len(sysex_export.render.applied_mutations),
        deferred_row_count=len(prepared.deferred_rows),
        sendable_row_count=prepared.send_plan.summary.sendable_count,
        manual_row_count=prepared.send_plan.summary.manual_count,
    )


def _manifest_payload(
    inference: _AudioInference,
    results: tuple[AnalogFourPatchCandidateBatchResult, ...],
    *,
    track: int,
    audio_name: str,
    source_kit_name: str,
    audio_sha256: str,
    source_kit_sha256: str,
    genome_sha256: str,
    generation_id: str,
) -> _BatchManifestPayload:
    candidates: list[_ManifestCandidatePayload] = [
        {
            "column": result.column,
            "label": result.label,
            "filter2_resonance": result.filter2_resonance,
            "sysex_filename": result.sysex_export.write.path.name,
            "sidecar_filename": result.sidecar_write.path.name,
            "sysex_sha256": result.sysex_export.render.sha256,
            "sidecar_sha256": result.sidecar_sha256,
            "coverage_counts": {
                "dna_row_count": result.dna_row_count,
                "sysex_encoded_row_count": result.sysex_encoded_row_count,
                "deferred_row_count": result.deferred_row_count,
                "sendable_row_count": result.sendable_row_count,
                "manual_row_count": result.manual_row_count,
            },
        }
        for result in results
    ]
    coverage: _CoverageCountsPayload = {
        "dna_row_count": sum(result.dna_row_count for result in results),
        "sysex_encoded_row_count": sum(result.sysex_encoded_row_count for result in results),
        "deferred_row_count": sum(result.deferred_row_count for result in results),
        "sendable_row_count": sum(result.sendable_row_count for result in results),
        "manual_row_count": sum(result.manual_row_count for result in results),
    }
    return {
        "schema_version": BATCH_SCHEMA_VERSION,
        "generation_id": generation_id,
        "track": track,
        "candidate_count": len(results),
        "audio_source": {"filename": audio_name, "sha256": audio_sha256},
        "source_kit": {"filename": source_kit_name, "sha256": source_kit_sha256},
        "feature_report_hash": inference.feature_report.content_hash,
        "genome_sha256": genome_sha256,
        "genome": inference.genome_payload,
        "candidates": candidates,
        "coverage_counts": coverage,
        "safety": [SYSEX_COVERAGE_STATEMENT, "No MIDI or network operation was performed."],
    }


def _stage_batch(
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
) -> _StagedBatch:
    """Build every artifact in private storage and return only in-memory bytes."""

    with tempfile.TemporaryDirectory(prefix="a4-audio-patch-batch-") as temp_name:
        staging_dir = Path(temp_name)
        audio_snapshot = staging_dir / f"audio{audio_path.suffix or '.bin'}"
        source_kit_snapshot = staging_dir / "source-kit.syx"
        atomic_write(audio_snapshot, audio_bytes)
        atomic_write(source_kit_snapshot, source_kit_bytes)
        source_kit_snapshot_bytes = source_kit_snapshot.read_bytes()

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
        genome_sha256 = _payload_sha256(inference.genome_payload)
        prepared = _prepare_candidates(
            inference,
            track=track,
            candidate_count=candidate_count,
        )
        rendered_candidates: list[_RenderedCandidate] = []
        for item in prepared:
            staged_sysex_path = staging_dir / f"candidate-{item.candidate.column:02d}.syx"
            render = render_analog_four_saved_kit(
                source_kit_snapshot_bytes,
                (
                    AnalogFourSavedKitMutation(
                        parameter=FILTER2_RESONANCE_PARAMETER,
                        track=track,
                        screen_value=item.resonance_gene.value.screen_value,
                    ),
                ),
            )
            staged_export = AnalogFourSavedKitExportResult(
                render=render,
                write=WriteResult(
                    path=staged_sysex_path.resolve(),
                    bytes_written=len(render.framed_sysex),
                    overwrote_existing=False,
                ),
            )
            rendered_candidates.append(
                _RenderedCandidate(prepared=item, sysex_export=staged_export)
            )

        settled_rendered = tuple(rendered_candidates)
        generation_id = _generation_id(
            audio_name=audio_path.name,
            source_kit_name=source_kit_path.name,
            audio_sha256=audio_sha256,
            source_kit_sha256=source_kit_sha256,
            genome_sha256=genome_sha256,
            inference=inference,
            track=track,
            candidates=settled_rendered,
        )

        staged_candidates: list[_StagedCandidate] = []
        planned_results: list[AnalogFourPatchCandidateBatchResult] = []
        for rendered in settled_rendered:
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
                    rendered.sysex_export,
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
                    sysex_export=rendered.sysex_export,
                    sidecar_bytes=sidecar_bytes,
                )
            )
            planned_results.append(
                _candidate_result(
                    item,
                    sysex_path,
                    sidecar_path,
                    rendered.sysex_export,
                    sidecar_bytes,
                )
            )

        settled_planned_results = tuple(planned_results)
        manifest_path = output_dir / f"a4-t{track}-audio-patch-batch.json"
        manifest_bytes = _json_bytes(
            _manifest_payload(
                inference,
                settled_planned_results,
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
        staged = _StagedBatch(
            inference=inference,
            genome_sha256=genome_sha256,
            generation_id=generation_id,
            candidates=tuple(staged_candidates),
            manifest_path=manifest_path,
            manifest_bytes=manifest_bytes,
        )
    return staged


def _batch_export_error_code(
    exc: Exception,
    *,
    source_reads_complete: bool,
    output_phase_started: bool,
) -> AnalogFourExportErrorCode:
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
        return "input_not_found"
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


def export_analog_four_audio_patch_batch(
    *,
    audio_path: Path,
    source_kit_path: Path,
    output_dir: Path,
    track: int = 1,
    candidate_count: int = 4,
    overwrite: bool = False,
) -> AnalogFourAudioPatchBatchExportResult:
    """Infer, render, and atomically describe an offline A4 candidate batch."""

    started_at = time.perf_counter()
    metrics = get_metrics()
    source_reads_complete = False
    output_phase_started = False
    try:
        _validate_request(track=track, candidate_count=candidate_count, output_dir=output_dir)
        audio_bytes = audio_path.read_bytes()
        source_kit_bytes = source_kit_path.read_bytes()
        audio_sha256 = _sha256(audio_bytes)
        source_kit_sha256 = _sha256(source_kit_bytes)
        source_reads_complete = True
        manifest_path = output_dir / f"a4-t{track}-audio-patch-batch.json"
        _preflight_destinations((manifest_path,), overwrite=overwrite)
        try:
            staged_batch = _stage_batch(
                audio_path=audio_path,
                source_kit_path=source_kit_path,
                audio_bytes=audio_bytes,
                source_kit_bytes=source_kit_bytes,
                audio_sha256=audio_sha256,
                source_kit_sha256=source_kit_sha256,
                output_dir=output_dir,
                track=track,
                candidate_count=candidate_count,
            )
        except AnalogFourPatchBatchStageError:
            raise
        except OSError as exc:
            raise AnalogFourPatchBatchStageError(
                str(exc),
                error_code="write_failed",
            ) from exc

        output_phase_started = True
        lock_path = output_dir / f".a4-t{track}-audio-patch-batch.lock"
        publication_nonce = secrets.token_hex(16)
        lock_write: WriteResult | None = None
        lock_cleanup_failure: str | None = None
        try:
            lock_write = _acquire_batch_lock(
                lock_path,
                generation_id=staged_batch.generation_id,
                publication_nonce=publication_nonce,
                audio_sha256=audio_sha256,
                source_kit_sha256=source_kit_sha256,
            )
            _preflight_destinations((staged_batch.manifest_path,), overwrite=overwrite)
            candidate_results: list[AnalogFourPatchCandidateBatchResult] = []
            for staged_candidate in staged_batch.candidates:
                item = staged_candidate.prepared
                sysex_write = _publish_immutable_artifact(
                    staged_candidate.sysex_path,
                    staged_candidate.sysex_export.render.framed_sysex,
                )
                sidecar_write = _publish_immutable_artifact(
                    staged_candidate.sidecar_path,
                    staged_candidate.sidecar_bytes,
                )
                candidate_results.append(
                    _candidate_result(
                        item,
                        staged_candidate.sysex_path,
                        staged_candidate.sidecar_path,
                        staged_candidate.sysex_export,
                        staged_candidate.sidecar_bytes,
                        sysex_write=sysex_write,
                        sidecar_write=sidecar_write,
                    )
                )
            settled_results = tuple(candidate_results)
            manifest_write = atomic_write(
                staged_batch.manifest_path,
                staged_batch.manifest_bytes,
                overwrite=overwrite,
            )
        finally:
            active_exception = sys.exception()
            owns_lock = lock_write is not None
            if not owns_lock and isinstance(active_exception, (KeyboardInterrupt, SystemExit)):
                owns_lock = _batch_lock_matches_request(
                    lock_path,
                    generation_id=staged_batch.generation_id,
                    publication_nonce=publication_nonce,
                    audio_sha256=audio_sha256,
                    source_kit_sha256=source_kit_sha256,
                )
            if owns_lock:
                lock_cleanup_failure = _release_batch_lock(lock_path)
            if lock_cleanup_failure is not None:
                if active_exception is not None:
                    active_exception.add_note("batch lock cleanup failure: " + lock_cleanup_failure)
                _logger.error(
                    "Analog Four audio patch batch lock cleanup failed",
                    extra={
                        "operation": "a4_audio_patch_batch_lock_cleanup",
                        "error_code": "lock_cleanup_failed",
                        "detail": lock_cleanup_failure,
                    },
                )

        if lock_cleanup_failure is not None:
            lock_cleanup_warning = (
                "batch committed successfully but publication lock cleanup failed; "
                f"recovery metadata remains at {lock_path}: {lock_cleanup_failure}"
            )
        else:
            lock_cleanup_warning = None

        result = AnalogFourAudioPatchBatchExportResult(
            track=track,
            candidate_count=len(settled_results),
            audio_sha256=audio_sha256,
            source_kit_sha256=source_kit_sha256,
            feature_report_hash=staged_batch.inference.feature_report.content_hash,
            genome_sha256=staged_batch.genome_sha256,
            generation_id=staged_batch.generation_id,
            candidates=settled_results,
            manifest_write=manifest_write,
            manifest_sha256=_sha256(staged_batch.manifest_bytes),
            lock_cleanup_warning=lock_cleanup_warning,
        )
    except (ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        error_code = _batch_export_error_code(
            exc,
            source_reads_complete=source_reads_complete,
            output_phase_started=output_phase_started,
        )
        metrics.record_export((time.perf_counter() - started_at) * 1000.0, error_code=error_code)
        _logger.warning(
            "Analog Four audio patch batch export failed",
            extra={
                "operation": "a4_audio_patch_batch_export",
                "error_code": error_code,
                "audio_path": str(audio_path),
                "source_kit_path": str(source_kit_path),
                "output_dir": str(output_dir),
            },
        )
        attach_analog_four_export_error_code(exc, error_code)
        raise

    metrics.record_export((time.perf_counter() - started_at) * 1000.0)
    _logger.info(
        "Analog Four audio patch batch export completed",
        extra={
            "operation": "a4_audio_patch_batch_export",
            "output_dir": str(output_dir),
            "manifest_sha256": result.manifest_sha256,
            "candidate_count": result.candidate_count,
        },
    )
    return result


__all__ = [
    "AnalogFourAudioPatchBatchExportResult",
    "AnalogFourPatchCandidateBatchResult",
    "BATCH_SCHEMA_VERSION",
    "CANDIDATE_SCHEMA_VERSION",
    "FILTER2_RESONANCE_PARAMETER",
    "SYSEX_COVERAGE_STATEMENT",
    "export_analog_four_audio_patch_batch",
]
