"""Guarded audio-to-candidate batch export for Analog Four MKII saved kits."""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from ...devices.strategies.analog_four_saved_kit_writer import (
    AnalogFourSavedKitMutation,
)
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...style_analysis.analog_four_patch_genome import (
    ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    ANALOG_FOUR_PATCH_CANDIDATE_MIN,
    ANALOG_FOUR_TRACK_MAX,
    ANALOG_FOUR_TRACK_MIN,
    AnalogFourPatchCandidate,
    AnalogFourPatchGene,
    AnalogFourPatchGenome,
    analog_four_patch_candidate_to_dict,
)
from ...style_analysis.analog_four_patch_send_plan import (
    AnalogFourPatchSendPlan,
    analog_four_patch_send_plan_to_dict,
)
from ...style_analysis.feature_report import FeatureReport
from .analog_four_kit import (
    AnalogFourSavedKitExportResult,
    export_analog_four_saved_kit,
)
from .writer import WriteResult, atomic_write

FILTER2_RESONANCE_PARAMETER: Final[str] = "Filter2 Resonance"
BATCH_SCHEMA_VERSION: Final[str] = "analog-four-audio-patch-batch-v1"
CANDIDATE_SCHEMA_VERSION: Final[str] = "analog-four-audio-patch-candidate-v1"
SYSEX_COVERAGE_STATEMENT: Final[str] = (
    "Only Filter2 Resonance is encoded in the saved-kit SysEx; all remaining "
    "candidate DNA stays in this sidecar and its live-dial send plan."
)
_DEFERRED_REASON: Final[str] = "not hardware-write-validated for saved-kit SysEx"
_SAFE_SEGMENT_RE: Final[re.Pattern[str]] = re.compile(r"[^a-z0-9]+")
_logger = get_logger(__name__)


@dataclass(frozen=True)
class AnalogFourPatchCandidateBatchResult:
    """Written artifacts and coverage for one generated patch candidate."""

    column: int
    label: str
    filter2_resonance: str
    sysex_export: AnalogFourSavedKitExportResult
    sidecar_write: WriteResult
    sidecar_sha256: str
    dna_row_count: int
    sysex_encoded_row_count: int
    deferred_row_count: int
    sendable_row_count: int
    manual_row_count: int

    @property
    def candidate(self) -> int:
        return self.column

    @property
    def sysex_path(self) -> Path:
        return self.sysex_export.write.path

    @property
    def sidecar_path(self) -> Path:
        return self.sidecar_write.path

    @property
    def sysex_applied_count(self) -> int:
        return self.sysex_encoded_row_count

    @property
    def live_sendable_count(self) -> int:
        return self.sendable_row_count

    @property
    def manual_count(self) -> int:
        return self.manual_row_count

    @property
    def deferred_count(self) -> int:
        return self.deferred_row_count


@dataclass(frozen=True)
class AnalogFourAudioPatchBatchExportResult:
    """Complete, manifest-backed result for one audio candidate batch."""

    track: int
    candidate_count: int
    audio_sha256: str
    source_kit_sha256: str
    feature_report_hash: str
    genome_sha256: str
    candidates: tuple[AnalogFourPatchCandidateBatchResult, ...]
    manifest_write: WriteResult
    manifest_sha256: str

    @property
    def source_hash(self) -> str:
        return self.audio_sha256

    @property
    def selected_track(self) -> int:
        return self.track

    @property
    def candidate_outputs(self) -> tuple[AnalogFourPatchCandidateBatchResult, ...]:
        return self.candidates

    @property
    def safety(self) -> tuple[str, ...]:
        return (SYSEX_COVERAGE_STATEMENT, "No MIDI or network operation was performed.")


@dataclass(frozen=True)
class _AudioInference:
    feature_report: FeatureReport
    genome: AnalogFourPatchGenome
    audio_features_payload: dict[str, object]
    genome_payload: dict[str, object]


@dataclass(frozen=True)
class _PreparedCandidate:
    candidate: AnalogFourPatchCandidate
    resonance_gene: AnalogFourPatchGene
    candidate_payload: dict[str, object]
    deferred_rows: tuple[dict[str, object], ...]
    send_plan: AnalogFourPatchSendPlan
    send_plan_payload: dict[str, object]
    sysex_path: Path
    sidecar_path: Path


def _json_bytes(payload: dict[str, object]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _payload_sha256(payload: dict[str, object]) -> str:
    return _sha256(_json_bytes(payload))


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
        raise NotADirectoryError(f"output_dir is not a directory: {output_dir}")


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


def _serialized_gene_rows(
    candidate: AnalogFourPatchCandidate,
    candidate_payload: dict[str, object],
) -> tuple[dict[str, object], ...]:
    raw_rows = candidate_payload.get("genes")
    if not isinstance(raw_rows, list) or len(raw_rows) != len(candidate.genes):
        raise ValueError("serialized candidate DNA does not match its gene rows")
    rows: list[dict[str, object]] = []
    for raw_row in raw_rows:
        if not isinstance(raw_row, dict) or not all(isinstance(key, str) for key in raw_row):
            raise ValueError("serialized candidate DNA contains an invalid gene row")
        rows.append(dict(cast(dict[str, object], raw_row)))
    return tuple(rows)


def _candidate_paths(
    output_dir: Path, candidate: AnalogFourPatchCandidate, track: int
) -> tuple[Path, Path]:
    stem = f"a4-t{track}-c{candidate.column:02d}-{_safe_segment(candidate.label)}"
    return output_dir / f"{stem}.syx", output_dir / f"{stem}.json"


def _prepare_candidates(
    inference: _AudioInference,
    *,
    output_dir: Path,
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
        rows = _serialized_gene_rows(candidate, candidate_payload)
        deferred_rows = tuple(
            {**row, "deferred_reason": _DEFERRED_REASON}
            for gene, row in zip(candidate.genes, rows, strict=True)
            if gene.value.parameter != FILTER2_RESONANCE_PARAMETER
        )
        send_plan = _build_send_plan(
            inference.feature_report,
            inference.genome,
            selected_candidate=candidate.column,
        )
        sysex_path, sidecar_path = _candidate_paths(output_dir, candidate, track)
        prepared.append(
            _PreparedCandidate(
                candidate=candidate,
                resonance_gene=resonance_gene,
                candidate_payload=candidate_payload,
                deferred_rows=deferred_rows,
                send_plan=send_plan,
                send_plan_payload=analog_four_patch_send_plan_to_dict(send_plan),
                sysex_path=sysex_path,
                sidecar_path=sidecar_path,
            )
        )
    return tuple(prepared)


def _preflight_destinations(paths: tuple[Path, ...], *, overwrite: bool) -> None:
    if len(paths) != len(set(paths)):
        raise ValueError("generated batch destinations are not unique")
    if not overwrite:
        for path in paths:
            if path.exists():
                raise FileExistsError(
                    f"refusing to overwrite existing file: {path} (pass overwrite=True to allow)"
                )


def _applied_rows(export: AnalogFourSavedKitExportResult) -> list[dict[str, object]]:
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
    audio_name: str,
    source_kit_name: str,
    audio_sha256: str,
    source_kit_sha256: str,
    genome_sha256: str,
) -> dict[str, object]:
    applied_rows = _applied_rows(export)
    coverage = {
        "dna_row_count": len(prepared.candidate.genes),
        "sysex_encoded_row_count": len(applied_rows),
        "deferred_row_count": len(prepared.deferred_rows),
        "sendable_row_count": prepared.send_plan.summary.sendable_count,
        "manual_row_count": prepared.send_plan.summary.manual_count,
    }
    return {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "audio_source": {"filename": audio_name},
        "source_kit": {"filename": source_kit_name},
        "candidate_dna": prepared.candidate_payload,
        "audio_features": inference.audio_features_payload,
        "dynamic_send_plan": prepared.send_plan_payload,
        "hardware_applied_rows": applied_rows,
        "deferred_rows": list(prepared.deferred_rows),
        "coverage_counts": coverage,
        "hardware_export": {
            "sysex_filename": prepared.sysex_path.name,
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
) -> dict[str, object]:
    return {
        "schema_version": BATCH_SCHEMA_VERSION,
        "track": track,
        "candidate_count": len(results),
        "audio_source": {"filename": audio_name, "sha256": audio_sha256},
        "source_kit": {"filename": source_kit_name, "sha256": source_kit_sha256},
        "feature_report_hash": inference.genome.source_hash,
        "genome_sha256": genome_sha256,
        "genome": inference.genome_payload,
        "candidates": [
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
        ],
        "coverage_counts": {
            "dna_row_count": sum(result.dna_row_count for result in results),
            "sysex_encoded_row_count": sum(result.sysex_encoded_row_count for result in results),
            "deferred_row_count": sum(result.deferred_row_count for result in results),
            "sendable_row_count": sum(result.sendable_row_count for result in results),
            "manual_row_count": sum(result.manual_row_count for result in results),
        },
        "safety": [SYSEX_COVERAGE_STATEMENT, "No MIDI or network operation was performed."],
    }


def _error_code(exc: Exception, *, source_reads_complete: bool) -> str:
    if isinstance(exc, FileExistsError):
        return "overwrite_refused"
    if isinstance(exc, OSError):
        return "write_failed" if source_reads_complete else "source_read_failed"
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
    try:
        _validate_request(track=track, candidate_count=candidate_count, output_dir=output_dir)
        audio_sha256 = _sha256(audio_path.read_bytes())
        source_kit_sha256 = _sha256(source_kit_path.read_bytes())
        source_reads_complete = True
        inference = _build_audio_inference(
            audio_path,
            track=track,
            candidate_count=candidate_count,
        )
        genome_sha256 = _payload_sha256(inference.genome_payload)
        prepared = _prepare_candidates(
            inference,
            output_dir=output_dir,
            track=track,
            candidate_count=candidate_count,
        )
        manifest_path = output_dir / f"a4-t{track}-audio-patch-batch.json"
        destinations = tuple(
            path for item in prepared for path in (item.sysex_path, item.sidecar_path)
        ) + (manifest_path,)
        _preflight_destinations(destinations, overwrite=overwrite)

        candidate_results: list[AnalogFourPatchCandidateBatchResult] = []
        for item in prepared:
            sysex_export = export_analog_four_saved_kit(
                source_path=source_kit_path,
                output_path=item.sysex_path,
                mutations=(
                    AnalogFourSavedKitMutation(
                        parameter=FILTER2_RESONANCE_PARAMETER,
                        track=track,
                        screen_value=item.resonance_gene.value.screen_value,
                    ),
                ),
                overwrite=overwrite,
            )
            sidecar_payload = _sidecar_payload(
                item,
                sysex_export,
                inference,
                audio_name=audio_path.name,
                source_kit_name=source_kit_path.name,
                audio_sha256=audio_sha256,
                source_kit_sha256=source_kit_sha256,
                genome_sha256=genome_sha256,
            )
            sidecar_bytes = _json_bytes(sidecar_payload)
            sidecar_write = atomic_write(item.sidecar_path, sidecar_bytes, overwrite=overwrite)
            candidate_results.append(
                AnalogFourPatchCandidateBatchResult(
                    column=item.candidate.column,
                    label=item.candidate.label,
                    filter2_resonance=item.resonance_gene.value.screen_value,
                    sysex_export=sysex_export,
                    sidecar_write=sidecar_write,
                    sidecar_sha256=_sha256(sidecar_bytes),
                    dna_row_count=len(item.candidate.genes),
                    sysex_encoded_row_count=len(sysex_export.render.applied_mutations),
                    deferred_row_count=len(item.deferred_rows),
                    sendable_row_count=item.send_plan.summary.sendable_count,
                    manual_row_count=item.send_plan.summary.manual_count,
                )
            )

        settled_results = tuple(candidate_results)
        manifest_payload = _manifest_payload(
            inference,
            settled_results,
            track=track,
            audio_name=audio_path.name,
            source_kit_name=source_kit_path.name,
            audio_sha256=audio_sha256,
            source_kit_sha256=source_kit_sha256,
            genome_sha256=genome_sha256,
        )
        manifest_bytes = _json_bytes(manifest_payload)
        manifest_write = atomic_write(manifest_path, manifest_bytes, overwrite=overwrite)
        result = AnalogFourAudioPatchBatchExportResult(
            track=track,
            candidate_count=len(settled_results),
            audio_sha256=audio_sha256,
            source_kit_sha256=source_kit_sha256,
            feature_report_hash=inference.genome.source_hash,
            genome_sha256=genome_sha256,
            candidates=settled_results,
            manifest_write=manifest_write,
            manifest_sha256=_sha256(manifest_bytes),
        )
    except Exception as exc:
        error_code = _error_code(exc, source_reads_complete=source_reads_complete)
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
