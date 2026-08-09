"""Passive Audio-to-Patch DNA comparison and selected A4 export service."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict

from ...data import AUDIO_PATCH_DNA_CANDIDATE_COUNT
from ...observability.errors import BoundaryError
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...observability.tracing import operation as trace_operation
from ...style_analysis.analog_four_patch_inference import (
    analyze_analog_four_patch_audio_analysis_isolated,
)
from ...style_analysis.audio_patch_dna import (
    AudioPatchDnaCandidate,
    AudioPatchDnaWorkspace,
    AudioPatchDnaWorkspacePayload,
    audio_patch_dna_workspace_to_dict,
    build_audio_patch_dna_workspace,
    render_audio_patch_dna_markdown,
    select_audio_patch_dna_candidate,
)
from .analog_four_export_contracts import (
    AnalogFourExportErrorCode,
    analog_four_export_path_name,
    attach_analog_four_export_error_code,
    classify_analog_four_cli_error,
    require_analog_four_export_path,
)
from .analog_four_patch_batch import (
    AnalogFourAudioPatchBatchExportResult,
    export_selected_analog_four_audio_patch,
)
from .writer import WriteResult, atomic_write_set

AUDIO_PATCH_DNA_JSON_NAME: Final[str] = "audio-patch-dna.json"
AUDIO_PATCH_DNA_MARKDOWN_NAME: Final[str] = "audio-patch-dna.md"
AUDIO_PATCH_DNA_SELECTED_A4_DIR_NAME: Final[str] = "selected-a4"
_EXPORT_FAILURE_FINGERPRINT: Final[str] = "a4.audio_patch_dna.export_failed"
_logger = get_logger(__name__)


class AudioPatchDnaSelectedCandidatePayload(TypedDict):
    """Stable summary of the explicitly selected direction."""

    column: int
    key: str
    label: str
    role: str
    closeness: int


class AudioPatchDnaSelectedA4Payload(TypedDict):
    """Stable summary of the existing A4 exporter result."""

    generation_id: str
    manifest_path: str
    manifest_sha256: str
    sysex_path: str
    sidecar_path: str
    safety: list[str]


class _AudioPatchDnaExportOptionalPayload(TypedDict, total=False):
    selected_candidate: AudioPatchDnaSelectedCandidatePayload
    selected_a4: AudioPatchDnaSelectedA4Payload


class AudioPatchDnaExportPayload(_AudioPatchDnaExportOptionalPayload):
    """JSON document written for one complete DNA workspace."""

    workspace: AudioPatchDnaWorkspacePayload


@dataclass(frozen=True)
class AudioPatchDnaExportResult:
    """Written comparison artifacts and optional selected A4 export."""

    workspace: AudioPatchDnaWorkspace
    json_write: WriteResult
    markdown_write: WriteResult
    selected_candidate: AudioPatchDnaCandidate | None
    analog_four_export: AnalogFourAudioPatchBatchExportResult | None

    @property
    def json_path(self) -> Path:
        return self.json_write.path

    @property
    def markdown_path(self) -> Path:
        return self.markdown_write.path


def export_audio_patch_dna_workspace(
    *,
    audio_path: Path,
    output_dir: Path,
    track: int = 1,
    selection: int | None = None,
    source_kit_path: Path | None = None,
    overwrite: bool = False,
) -> AudioPatchDnaExportResult:
    """Analyze once, write eight directions, and optionally export one A4 patch."""

    with trace_operation(
        "a4_audio_patch_dna_export",
        logger=_logger,
        audio_name=analog_four_export_path_name(audio_path),
        source_kit_name=analog_four_export_path_name(source_kit_path),
        output_dir_name=analog_four_export_path_name(output_dir),
        track=track,
        selection=selection,
    ):
        return _execute_audio_patch_dna_workspace(
            audio_path=audio_path,
            output_dir=output_dir,
            track=track,
            selection=selection,
            source_kit_path=source_kit_path,
            overwrite=overwrite,
        )


def _execute_audio_patch_dna_workspace(  # noqa: PLR0913 - mirrors the service request
    *,
    audio_path: Path,
    output_dir: Path,
    track: int,
    selection: int | None,
    source_kit_path: Path | None,
    overwrite: bool,
) -> AudioPatchDnaExportResult:
    started_at = time.perf_counter()
    try:
        validated_audio_path = require_analog_four_export_path(
            audio_path,
            field_name="audio_path",
        )
        validated_output_dir = require_analog_four_export_path(
            output_dir,
            field_name="output_dir",
        )
        validated_source_kit = _validate_selection_inputs(
            selection=selection,
            source_kit_path=source_kit_path,
        )

        analysis = analyze_analog_four_patch_audio_analysis_isolated(validated_audio_path)
        workspace = build_audio_patch_dna_workspace(analysis, track=track)
        selected_candidate = workspace.candidates[selection - 1] if selection is not None else None
        analog_four_export = _export_selected_candidate(
            workspace=workspace,
            selected_candidate=selected_candidate,
            audio_path=validated_audio_path,
            source_kit_path=validated_source_kit,
            output_dir=validated_output_dir,
            overwrite=overwrite,
        )
        payload = _audio_patch_dna_export_payload(
            workspace,
            selected_candidate=selected_candidate,
            analog_four_export=analog_four_export,
        )
        markdown = _audio_patch_dna_export_markdown(
            workspace,
            selected_candidate=selected_candidate,
            analog_four_export=analog_four_export,
        )
        json_bytes = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
        markdown_bytes = markdown.encode("utf-8")
        json_write, markdown_write = atomic_write_set(
            {
                validated_output_dir / AUDIO_PATCH_DNA_JSON_NAME: json_bytes,
                validated_output_dir / AUDIO_PATCH_DNA_MARKDOWN_NAME: markdown_bytes,
            },
            overwrite=overwrite,
        )
        result = AudioPatchDnaExportResult(
            workspace=workspace,
            json_write=json_write,
            markdown_write=markdown_write,
            selected_candidate=selected_candidate,
            analog_four_export=analog_four_export,
        )
    except (KeyboardInterrupt, SystemExit) as exc:
        _record_audio_patch_dna_failure(
            exc,
            audio_path=audio_path,
            output_dir=output_dir,
            selection=selection,
            started_at=started_at,
        )
        raise
    except (
        BoundaryError,
        ImportError,
        KeyError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as exc:
        _record_audio_patch_dna_failure(
            exc,
            audio_path=audio_path,
            output_dir=output_dir,
            selection=selection,
            started_at=started_at,
        )
        raise
    _record_audio_patch_dna_success(result, output_dir=output_dir, started_at=started_at)
    return result


def _record_audio_patch_dna_failure(
    exc: Exception | KeyboardInterrupt | SystemExit,
    *,
    audio_path: object,
    output_dir: object,
    selection: int | None,
    started_at: float,
) -> None:
    if isinstance(exc, (KeyboardInterrupt, SystemExit)):
        error_code: AnalogFourExportErrorCode = "interrupted"
    else:
        error_code = classify_analog_four_cli_error(
            exc,
            default_error_code="invalid_input",
        )
        attach_analog_four_export_error_code(exc, error_code)
    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics = get_metrics()
    metrics.record_export(duration_ms, error_code=error_code)
    _logger.warning(
        "Audio-to-Patch DNA export failed",
        extra={
            "operation": "a4_audio_patch_dna_export",
            "outcome": "failed",
            "error_code": error_code,
            "fingerprint": getattr(exc, "fingerprint", _EXPORT_FAILURE_FINGERPRINT),
            "error_type": type(exc).__name__,
            "audio_name": analog_four_export_path_name(audio_path),
            "output_dir_name": analog_four_export_path_name(output_dir),
            "selection": selection,
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )


def _record_audio_patch_dna_success(
    result: AudioPatchDnaExportResult,
    *,
    output_dir: object,
    started_at: float,
) -> None:
    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics = get_metrics()
    metrics.record_export(duration_ms)
    _logger.info(
        "Audio-to-Patch DNA export completed",
        extra={
            "operation": "a4_audio_patch_dna_export",
            "outcome": "completed",
            "output_dir_name": analog_four_export_path_name(output_dir),
            "candidate_count": len(result.workspace.candidates),
            "selected": result.selected_candidate is not None,
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )


def _strict_integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} must be an integer")
    return value


def _validate_selection_inputs(
    *,
    selection: int | None,
    source_kit_path: Path | None,
) -> Path | None:
    if selection is None:
        if source_kit_path is not None:
            raise ValueError("source_kit_path requires a candidate selection")
        return None
    validated_selection = _strict_integer(selection, "selection")
    if not 1 <= validated_selection <= AUDIO_PATCH_DNA_CANDIDATE_COUNT:
        raise ValueError(f"selection must be in 1..{AUDIO_PATCH_DNA_CANDIDATE_COUNT}")
    if source_kit_path is None:
        raise ValueError("source_kit_path is required for a candidate selection")
    return require_analog_four_export_path(
        source_kit_path,
        field_name="source_kit_path",
    )


def _export_selected_candidate(
    *,
    workspace: AudioPatchDnaWorkspace,
    selected_candidate: AudioPatchDnaCandidate | None,
    audio_path: Path,
    source_kit_path: Path | None,
    output_dir: Path,
    overwrite: bool,
) -> AnalogFourAudioPatchBatchExportResult | None:
    if selected_candidate is None:
        return None
    if source_kit_path is None:  # Defensive; validated at the public boundary.
        raise ValueError("source_kit_path is required for a candidate selection")
    audio_genome = select_audio_patch_dna_candidate(
        workspace,
        selected_candidate.column,
    )
    return export_selected_analog_four_audio_patch(
        audio_path=audio_path,
        source_kit_path=source_kit_path,
        output_dir=output_dir / AUDIO_PATCH_DNA_SELECTED_A4_DIR_NAME,
        audio_genome=audio_genome,
        overwrite=overwrite,
    )


def _audio_patch_dna_export_payload(
    workspace: AudioPatchDnaWorkspace,
    *,
    selected_candidate: AudioPatchDnaCandidate | None,
    analog_four_export: AnalogFourAudioPatchBatchExportResult | None,
) -> AudioPatchDnaExportPayload:
    payload: AudioPatchDnaExportPayload = {
        "workspace": audio_patch_dna_workspace_to_dict(workspace),
    }
    if selected_candidate is not None:
        payload["selected_candidate"] = _selected_candidate_payload(selected_candidate)
    if analog_four_export is not None:
        candidate = analog_four_export.candidates[0]
        payload["selected_a4"] = {
            "generation_id": analog_four_export.generation_id,
            "manifest_path": str(analog_four_export.manifest_path),
            "manifest_sha256": analog_four_export.manifest_sha256,
            "sysex_path": str(candidate.sysex_path),
            "sidecar_path": str(candidate.sidecar_path),
            "safety": list(analog_four_export.safety),
        }
    return payload


def _selected_candidate_payload(
    candidate: AudioPatchDnaCandidate,
) -> AudioPatchDnaSelectedCandidatePayload:
    return {
        "column": candidate.column,
        "key": candidate.key,
        "label": candidate.label,
        "role": candidate.role,
        "closeness": candidate.closeness,
    }


def _audio_patch_dna_export_markdown(
    workspace: AudioPatchDnaWorkspace,
    *,
    selected_candidate: AudioPatchDnaCandidate | None,
    analog_four_export: AnalogFourAudioPatchBatchExportResult | None,
) -> str:
    markdown = render_audio_patch_dna_markdown(workspace).rstrip()
    if selected_candidate is None:
        return markdown + "\n"
    lines = [
        markdown,
        "",
        "## Selected Direction",
        "",
        f"- Candidate: {selected_candidate.column}. {selected_candidate.label}",
        f"- Role: {selected_candidate.role}",
    ]
    if analog_four_export is not None:
        candidate = analog_four_export.candidates[0]
        lines.extend(
            (
                f"- A4 manifest: {analog_four_export.manifest_path}",
                f"- A4 SysEx: {candidate.sysex_path}",
                f"- A4 sidecar: {candidate.sidecar_path}",
            )
        )
    return "\n".join(lines) + "\n"


__all__ = [
    "AUDIO_PATCH_DNA_JSON_NAME",
    "AUDIO_PATCH_DNA_MARKDOWN_NAME",
    "AUDIO_PATCH_DNA_SELECTED_A4_DIR_NAME",
    "AudioPatchDnaExportPayload",
    "AudioPatchDnaExportResult",
    "AudioPatchDnaSelectedA4Payload",
    "AudioPatchDnaSelectedCandidatePayload",
    "export_audio_patch_dna_workspace",
]
