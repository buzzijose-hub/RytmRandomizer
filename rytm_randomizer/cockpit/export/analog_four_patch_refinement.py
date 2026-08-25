"""Passive adaptive refinement for one recorded Analog Four patch candidate."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict

from ...data.analog_four_patch_refinement import (
    ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
    ANALOG_FOUR_PATCH_REFINEMENT_SCHEMA_VERSION,
)
from ...observability.errors import BoundaryError
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...observability.tracing import operation as trace_operation
from ...style_analysis.analog_four_patch_inference import (
    analyze_analog_four_patch_audio_analysis_isolated,
    analyze_analog_four_patch_audio_isolated,
)
from ...style_analysis.analog_four_patch_refinement import (
    AnalogFourPatchRefinementPlan,
    AnalogFourPatchRefinementPlanPayload,
    analog_four_patch_refinement_plan_to_dict,
    plan_analog_four_patch_refinement,
)
from ...style_analysis.analog_four_patch_render_rank import (
    AnalogFourRenderCandidateFeatures,
    rank_analog_four_render_features,
)
from .analog_four_export_contracts import require_analog_four_export_path
from .analog_four_patch_batch import (
    AnalogFourAudioPatchBatchExportResult,
    export_selected_analog_four_audio_patch,
)
from .analog_four_patch_batch_reader import (
    AnalogFourPatchBatchSelection,
    load_analog_four_patch_batch_candidate,
)
from .analog_four_patch_render_rank import (
    AnalogFourPatchRenderRankArtifactError,
    AnalogFourPatchRenderRankReferenceError,
    analog_four_patch_render_rank_error_code,
)
from .writer import WriteResult, atomic_write_set

ANALOG_FOUR_PATCH_REFINEMENT_JSON_NAME: Final[str] = "analog-four-patch-refinement.json"
ANALOG_FOUR_PATCH_REFINEMENT_MARKDOWN_NAME: Final[str] = "analog-four-patch-refinement.md"
ANALOG_FOUR_PATCH_REFINEMENT_A4_DIR_NAME: Final[str] = "refined-a4"
ANALOG_FOUR_PATCH_REFINEMENT_SAFETY: Final[tuple[str, ...]] = (
    "passive local reference and render analysis",
    "batch manifest and candidate sidecar are hash-verified",
    "reference audio must match the committed batch source",
    "bounded feature correction uses the existing verified A4 inference equations",
    "optional SysEx artifact generation is offline only",
    "no MIDI ports enumerated or opened",
    "no MIDI or SysEx transmitted",
    "no hardware mutation",
)
_REFINEMENT_FAILURE_FINGERPRINT: Final[str] = "a4.patch_refinement.failed"
_logger = get_logger(__name__)


class AnalogFourPatchRefinementAudioPayload(TypedDict):
    path: str
    sha256: str


class AnalogFourPatchRefinementSelectionPayload(TypedDict):
    generation_id: str
    manifest_path: str
    candidate: int
    label: str
    track: int


class AnalogFourPatchRefinementExportPayload(TypedDict):
    generation_id: str
    manifest_path: str
    manifest_sha256: str
    sysex_path: str
    sidecar_path: str
    safety: list[str]


class AnalogFourPatchRefinementPayload(TypedDict):
    schema_version: str
    selection: AnalogFourPatchRefinementSelectionPayload
    reference_audio: AnalogFourPatchRefinementAudioPayload
    render_audio: AnalogFourPatchRefinementAudioPayload
    plan: AnalogFourPatchRefinementPlanPayload
    next_export: AnalogFourPatchRefinementExportPayload | None
    safety: list[str]


@dataclass(frozen=True)
class AnalogFourPatchRefinementResult:
    """One measured feedback decision and its optional offline patch artifact."""

    selection: AnalogFourPatchBatchSelection
    reference_path: Path
    render_path: Path
    plan: AnalogFourPatchRefinementPlan
    payload: AnalogFourPatchRefinementPayload
    json_write: WriteResult
    markdown_write: WriteResult
    analog_four_export: AnalogFourAudioPatchBatchExportResult | None

    @property
    def json_path(self) -> Path:
        return self.json_write.path

    @property
    def markdown_path(self) -> Path:
        return self.markdown_write.path


def export_analog_four_patch_refinement(  # noqa: PLR0913 - public request contract
    *,
    reference_audio_path: Path,
    manifest_path: Path,
    candidate: int,
    render_audio_path: Path,
    output_dir: Path,
    correction_gain: float = ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
    accept_similarity: int = ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
    source_kit_path: Path | None = None,
    overwrite: bool = False,
) -> AnalogFourPatchRefinementResult:
    """Measure one render and emit one bounded follow-up candidate when needed."""

    started_at = time.perf_counter()
    metrics = get_metrics()
    operation_id = ""
    try:
        with trace_operation(
            "a4_audio_patch_refinement",
            logger=_logger,
            candidate=candidate,
        ) as operation_id:
            result = _execute_analog_four_patch_refinement(
                reference_audio_path=reference_audio_path,
                manifest_path=manifest_path,
                candidate=candidate,
                render_audio_path=render_audio_path,
                output_dir=output_dir,
                correction_gain=correction_gain,
                accept_similarity=accept_similarity,
                source_kit_path=source_kit_path,
                overwrite=overwrite,
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
            "Analog Four patch refinement failed",
            extra={
                "op_id": operation_id,
                "operation": "a4_audio_patch_refinement",
                "outcome": "failed",
                "error_code": error_code,
                "candidate": candidate,
                "duration_ms": duration_ms,
                "error_type": type(exc).__name__,
                "fingerprint": _refinement_failure_fingerprint(exc),
                "metrics_summary": metrics.format_summary(),
            },
        )
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics.record_a4_patch_render_rank(duration_ms)
    _logger.info(
        "Analog Four patch refinement completed",
        extra={
            "op_id": operation_id,
            "operation": "a4_audio_patch_refinement",
            "outcome": "completed",
            "generation_id": result.selection.generation_id,
            "candidate": candidate,
            "action": result.plan.action,
            "similarity": result.plan.similarity,
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )
    return result


def _refinement_failure_fingerprint(exc: BaseException) -> str:
    fingerprint = getattr(exc, "fingerprint", _REFINEMENT_FAILURE_FINGERPRINT)
    if isinstance(exc, BoundaryError):
        fingerprint = exc.context.get("fingerprint", fingerprint)
    return str(fingerprint)


def _execute_analog_four_patch_refinement(  # noqa: PLR0913 - service boundary
    *,
    reference_audio_path: Path,
    manifest_path: Path,
    candidate: int,
    render_audio_path: Path,
    output_dir: Path,
    correction_gain: float,
    accept_similarity: int,
    source_kit_path: Path | None,
    overwrite: bool,
) -> AnalogFourPatchRefinementResult:
    reference_path = require_analog_four_export_path(
        reference_audio_path,
        field_name="reference_audio_path",
    )
    validated_manifest_path = require_analog_four_export_path(
        manifest_path,
        field_name="manifest_path",
    )
    render_path = require_analog_four_export_path(
        render_audio_path,
        field_name="render_audio_path",
    )
    validated_output_dir = require_analog_four_export_path(
        output_dir,
        field_name="output_dir",
    )
    validated_source_kit = (
        require_analog_four_export_path(
            source_kit_path,
            field_name="source_kit_path",
        )
        if source_kit_path is not None
        else None
    )
    selection = _load_selection(validated_manifest_path, candidate=candidate)
    reference_analysis = analyze_analog_four_patch_audio_analysis_isolated(reference_path)
    if reference_analysis.synthesis_features.audio_sha256 != selection.audio_sha256:
        raise AnalogFourPatchRenderRankReferenceError(
            "reference audio SHA-256 does not match the committed batch source",
            context={
                "actual_sha256": reference_analysis.synthesis_features.audio_sha256,
                "expected_sha256": selection.audio_sha256,
                "candidate": candidate,
            },
        )
    render_features = analyze_analog_four_patch_audio_isolated(render_path)
    render_score = rank_analog_four_render_features(
        reference_analysis.synthesis_features,
        (
            AnalogFourRenderCandidateFeatures(
                candidate=selection.plan.selected_candidate,
                label=selection.plan.selected_label,
                render_path=render_path,
                features=render_features,
            ),
        ),
    )[0]
    plan = plan_analog_four_patch_refinement(
        reference_analysis,
        render_score,
        render_features,
        track=selection.plan.selected_track,
        correction_gain=correction_gain,
        accept_similarity=accept_similarity,
    )
    analog_four_export = _export_next_candidate(
        plan=plan,
        reference_path=reference_path,
        source_kit_path=validated_source_kit,
        output_dir=validated_output_dir,
        overwrite=overwrite,
    )
    payload = _refinement_payload(
        selection=selection,
        reference_path=reference_path,
        render_path=render_path,
        render_sha256=render_features.audio_sha256,
        plan=plan,
        analog_four_export=analog_four_export,
    )
    json_bytes = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    markdown_bytes = _refinement_markdown(payload).encode("utf-8")
    json_write, markdown_write = atomic_write_set(
        {
            validated_output_dir / ANALOG_FOUR_PATCH_REFINEMENT_JSON_NAME: json_bytes,
            validated_output_dir / ANALOG_FOUR_PATCH_REFINEMENT_MARKDOWN_NAME: markdown_bytes,
        },
        overwrite=overwrite,
    )
    return AnalogFourPatchRefinementResult(
        selection=selection,
        reference_path=reference_path,
        render_path=render_path,
        plan=plan,
        payload=payload,
        json_write=json_write,
        markdown_write=markdown_write,
        analog_four_export=analog_four_export,
    )


def _load_selection(
    manifest_path: Path,
    *,
    candidate: int,
) -> AnalogFourPatchBatchSelection:
    try:
        return load_analog_four_patch_batch_candidate(
            manifest_path,
            candidate=candidate,
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise AnalogFourPatchRenderRankArtifactError(
            str(exc),
            context={
                "candidate": candidate,
                "cause_type": type(exc).__name__,
                "manifest_name": manifest_path.name,
            },
        ) from exc


def _export_next_candidate(
    *,
    plan: AnalogFourPatchRefinementPlan,
    reference_path: Path,
    source_kit_path: Path | None,
    output_dir: Path,
    overwrite: bool,
) -> AnalogFourAudioPatchBatchExportResult | None:
    if plan.action == "accept" or source_kit_path is None:
        return None
    if plan.next_candidate is None:
        raise AnalogFourPatchRenderRankArtifactError(
            "refine action is missing its inferred next candidate"
        )
    return export_selected_analog_four_audio_patch(
        audio_path=reference_path,
        source_kit_path=source_kit_path,
        output_dir=output_dir / ANALOG_FOUR_PATCH_REFINEMENT_A4_DIR_NAME,
        audio_genome=plan.next_candidate,
        overwrite=overwrite,
    )


def _refinement_payload(
    *,
    selection: AnalogFourPatchBatchSelection,
    reference_path: Path,
    render_path: Path,
    render_sha256: str,
    plan: AnalogFourPatchRefinementPlan,
    analog_four_export: AnalogFourAudioPatchBatchExportResult | None,
) -> AnalogFourPatchRefinementPayload:
    return {
        "schema_version": ANALOG_FOUR_PATCH_REFINEMENT_SCHEMA_VERSION,
        "selection": {
            "generation_id": selection.generation_id,
            "manifest_path": str(selection.manifest_path),
            "candidate": selection.plan.selected_candidate,
            "label": selection.plan.selected_label,
            "track": selection.plan.selected_track,
        },
        "reference_audio": {
            "path": str(reference_path),
            "sha256": selection.audio_sha256,
        },
        "render_audio": {
            "path": str(render_path),
            "sha256": render_sha256,
        },
        "plan": analog_four_patch_refinement_plan_to_dict(plan),
        "next_export": _next_export_payload(analog_four_export),
        "safety": list(ANALOG_FOUR_PATCH_REFINEMENT_SAFETY),
    }


def _next_export_payload(
    result: AnalogFourAudioPatchBatchExportResult | None,
) -> AnalogFourPatchRefinementExportPayload | None:
    if result is None:
        return None
    candidate = result.candidates[0]
    return {
        "generation_id": result.generation_id,
        "manifest_path": str(result.manifest_path),
        "manifest_sha256": result.manifest_sha256,
        "sysex_path": str(candidate.sysex_path),
        "sidecar_path": str(candidate.sidecar_path),
        "safety": list(result.safety),
    }


def _refinement_markdown(payload: AnalogFourPatchRefinementPayload) -> str:
    selection = payload["selection"]
    plan = payload["plan"]
    lines = [
        "# Analog Four Patch Refinement",
        "",
        f"- Action: `{plan['action']}`",
        f"- Similarity: `{plan['similarity']}`",
        f"- Acceptance threshold: `{plan['accept_similarity']}`",
        f"- Candidate: `{selection['candidate']}` ({selection['label']})",
        f"- Track: `{selection['track']}`",
        f"- Correction gain: `{plan['correction_gain']}`",
        "",
        "## Residuals",
        "",
        "| Feature | Reference | Render | Signed error | Corrected target |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in plan["residuals"]:
        lines.append(
            f"| {row['feature']} | {row['reference_value']:.6f} | "
            f"{row['rendered_value']:.6f} | {row['signed_error']:.6f} | "
            f"{row['corrected_target']:.6f} |"
        )
    lines.extend(("", "## Safety", ""))
    lines.extend(f"- {line}" for line in payload["safety"])
    return "\n".join(lines) + "\n"


__all__ = [
    "ANALOG_FOUR_PATCH_REFINEMENT_A4_DIR_NAME",
    "ANALOG_FOUR_PATCH_REFINEMENT_JSON_NAME",
    "ANALOG_FOUR_PATCH_REFINEMENT_MARKDOWN_NAME",
    "ANALOG_FOUR_PATCH_REFINEMENT_SAFETY",
    "AnalogFourPatchRefinementPayload",
    "AnalogFourPatchRefinementResult",
    "export_analog_four_patch_refinement",
]
