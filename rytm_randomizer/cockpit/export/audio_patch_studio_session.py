"""Resumable passive studio session for Audio-to-Patch DNA refinement."""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import time
from collections.abc import Callable, Generator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from io import BufferedReader
from pathlib import Path, PurePosixPath
from typing import ClassVar, Final, Literal, TypedDict, TypeVar, cast

from ...data.analog_four_patch_refinement import (
    ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MAX,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MIN,
    ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MAX,
    ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MIN,
)
from ...data.analog_four_sysex_calibration import A4_SYNTH_TRACK_MAX, A4_SYNTH_TRACK_MIN
from ...data.audio_patch_dna import AUDIO_PATCH_DNA_CANDIDATE_COUNT
from ...data.modes import (
    AUDIO_PATCH_STUDIO_SESSION_COMMITTED_TRANSITION,
    AUDIO_PATCH_STUDIO_SESSION_REPLAYED_TRANSITION,
    AudioPatchStudioSessionTransition,
)
from ...observability.errors import BoundaryError
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...observability.tracing import operation as trace_operation
from ...style_analysis.analog_four_patch_genome import (
    ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    ANALOG_FOUR_PATCH_CANDIDATE_MIN,
)
from ...style_analysis.analog_four_patch_refinement import (
    AnalogFourPatchRefinementAction,
)
from .analog_four_export_contracts import (
    AnalogFourExportErrorCode,
    analog_four_export_path_name,
    attach_analog_four_export_error_code,
    classify_analog_four_cli_error,
)
from .analog_four_patch_batch_codec import validate_analog_four_patch_batch_sha256
from .analog_four_patch_batch_contracts import (
    AnalogFourAudioPatchBatchExportResult,
    AnalogFourPatchCandidateBatchResult,
)
from .analog_four_patch_refinement import export_analog_four_patch_refinement
from .audio_patch_dna import export_audio_patch_dna_workspace
from .file_export_contracts import (
    attach_local_file_export_error_context,
    classify_local_file_export_error,
    local_file_export_error_context,
    safe_local_file_export_artifact_name,
)
from .writer import WriteResult, atomic_write_set, guard_atomic_write_tree

AUDIO_PATCH_STUDIO_SESSION_SCHEMA_VERSION: Final[str] = "audio-patch-studio-session-v1"
AUDIO_PATCH_STUDIO_SESSION_JSON_NAME: Final[str] = "studio-session.json"
AUDIO_PATCH_STUDIO_SESSION_MARKDOWN_NAME: Final[str] = "studio-session.md"
AUDIO_PATCH_STUDIO_SESSION_WORKSPACE_DIR_NAME: Final[str] = "workspace"
AUDIO_PATCH_STUDIO_SESSION_REFINEMENT_DIR_NAME: Final[str] = "refinement"
AUDIO_PATCH_STUDIO_SESSION_SAFETY: Final[tuple[str, ...]] = (
    "passive local audio analysis and offline artifact generation",
    "candidate selection is explicit and hash-bound to this session",
    "session artifacts are hash-verified before refinement",
    "no MIDI ports enumerated or opened",
    "no MIDI or SysEx transmitted",
    "no hardware mutation",
    "no network access",
)
_SESSION_FAILURE_FINGERPRINT: Final[str] = "a4.audio_patch_studio_session.failed"
_OUTPUT_GUARD_NAME: Final[str] = ".audio-patch-studio-output.guard"
_REFINEMENT_ACTIONS: Final[tuple[AnalogFourPatchRefinementAction, ...]] = (
    "accept",
    "refine",
)
_logger = get_logger(__name__)
AudioPatchStudioSessionStatus = Literal["waiting_for_render", "accepted", "refined"]
_OutputResult = TypeVar("_OutputResult")


class AudioPatchStudioSessionFilePayload(TypedDict):
    """External input identity without a machine-local absolute path."""

    filename: str
    sha256: str


class AudioPatchStudioSessionArtifactPayload(TypedDict):
    """Hash-bound artifact stored relative to the session root."""

    path: str
    sha256: str


class AudioPatchStudioSessionSelectionPayload(TypedDict):
    """DNA direction and its one-candidate A4 manifest identity."""

    dna_candidate: int
    manifest_candidate: int
    key: str
    label: str
    role: str
    closeness: int
    track: int
    generation_id: str


class AudioPatchStudioSessionWorkspacePayload(TypedDict):
    json: AudioPatchStudioSessionArtifactPayload
    markdown: AudioPatchStudioSessionArtifactPayload


class AudioPatchStudioSessionExportPayload(TypedDict):
    manifest: AudioPatchStudioSessionArtifactPayload
    sysex: AudioPatchStudioSessionArtifactPayload
    sidecar: AudioPatchStudioSessionArtifactPayload


class _AudioPatchStudioSessionResultOptionalPayload(TypedDict, total=False):
    next_export: AudioPatchStudioSessionExportPayload


class AudioPatchStudioSessionRefinementPayload(_AudioPatchStudioSessionResultOptionalPayload):
    render_audio: AudioPatchStudioSessionFilePayload
    action: AnalogFourPatchRefinementAction
    similarity: int
    correction_gain: float
    accept_similarity: int
    json: AudioPatchStudioSessionArtifactPayload
    markdown: AudioPatchStudioSessionArtifactPayload


class _AudioPatchStudioSessionOptionalPayload(TypedDict, total=False):
    refinement: AudioPatchStudioSessionRefinementPayload
    summary_sha256: str


class AudioPatchStudioSessionPayload(_AudioPatchStudioSessionOptionalPayload):
    """Durable, deterministic state for one studio feedback cycle."""

    schema_version: str
    session_id: str
    status: AudioPatchStudioSessionStatus
    reference_audio: AudioPatchStudioSessionFilePayload
    source_kit: AudioPatchStudioSessionFilePayload
    selection: AudioPatchStudioSessionSelectionPayload
    workspace: AudioPatchStudioSessionWorkspacePayload
    selected_export: AudioPatchStudioSessionExportPayload
    safety: list[str]


@dataclass(frozen=True)
class AudioPatchStudioSessionResult:
    """One loaded or newly committed studio-session state."""

    payload: AudioPatchStudioSessionPayload
    json_path: Path
    markdown_path: Path
    json_write: WriteResult | None = None
    markdown_write: WriteResult | None = None

    @property
    def transition(self) -> AudioPatchStudioSessionTransition:
        """Report whether this invocation committed state or replayed it."""

        if self.json_write is None:
            return AUDIO_PATCH_STUDIO_SESSION_REPLAYED_TRANSITION
        return AUDIO_PATCH_STUDIO_SESSION_COMMITTED_TRANSITION


class AudioPatchStudioSessionAccessError(BoundaryError, PermissionError):
    """The session output tree could not be inspected safely."""

    fingerprint: ClassVar[str] = "a4.audio_patch_studio_session.access_denied"


class AudioPatchStudioSessionLockedError(BoundaryError, FileExistsError):
    """A concurrent process already owns one session publication tree."""

    fingerprint: ClassVar[str] = "a4.audio_patch_studio_session.publication_locked"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        attach_analog_four_export_error_code(self, "publication_locked")


def _run_session_operation(
    *,
    operation_name: str,
    source_path: object,
    output_path: object,
    execute: Callable[[], AudioPatchStudioSessionResult],
) -> AudioPatchStudioSessionResult:
    started_at = time.perf_counter()
    try:
        result = execute()
    except (KeyboardInterrupt, SystemExit) as exc:
        _record_session_failure(
            exc,
            operation_name=operation_name,
            source_path=source_path,
            output_path=output_path,
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
        _record_session_failure(
            exc,
            operation_name=operation_name,
            source_path=source_path,
            output_path=output_path,
            started_at=started_at,
        )
        raise
    _record_session_success(
        result,
        operation_name=operation_name,
        output_path=output_path,
        started_at=started_at,
    )
    return result


def _record_session_failure(
    exc: Exception | KeyboardInterrupt | SystemExit,
    *,
    operation_name: str,
    source_path: object,
    output_path: object,
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
    local_context = local_file_export_error_context(exc)
    source_name = (
        local_context.artifact_name
        if local_context is not None
        else analog_four_export_path_name(source_path)
    )
    fingerprint = getattr(exc, "fingerprint", _SESSION_FAILURE_FINGERPRINT)
    if isinstance(exc, BoundaryError):
        contextual_fingerprint = exc.context.get("fingerprint")
        if isinstance(contextual_fingerprint, str) and contextual_fingerprint:
            fingerprint = contextual_fingerprint
    _logger.warning(
        "Audio-to-Patch studio session failed",
        extra={
            "operation": operation_name,
            "outcome": "failed",
            "error_code": error_code,
            "fingerprint": fingerprint,
            "error_type": type(exc).__name__,
            "source_name": source_name,
            "output_name": analog_four_export_path_name(output_path),
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )


def _record_session_success(
    result: AudioPatchStudioSessionResult,
    *,
    operation_name: str,
    output_path: object,
    started_at: float,
) -> None:
    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics = get_metrics()
    metrics.record_export(duration_ms)
    _logger.info(
        "Audio-to-Patch studio session completed",
        extra={
            "operation": operation_name,
            "outcome": "completed",
            "output_name": analog_four_export_path_name(output_path),
            "session_id": result.payload["session_id"],
            "status": result.payload["status"],
            "transition": result.transition,
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )


def start_audio_patch_studio_session(
    *,
    reference_audio_path: Path,
    source_kit_path: Path,
    selection: int,
    output_dir: Path,
    track: int = 1,
    overwrite: bool = False,
) -> AudioPatchStudioSessionResult:
    """Create or idempotently reopen a selected DNA studio session."""

    with trace_operation(
        "a4_audio_patch_studio_session_start",
        logger=_logger,
        reference_name=analog_four_export_path_name(reference_audio_path),
        source_kit_name=analog_four_export_path_name(source_kit_path),
        output_dir_name=analog_four_export_path_name(output_dir),
        selection=selection,
        track=track,
    ):
        return _run_session_operation(
            operation_name="a4_audio_patch_studio_session_start",
            source_path=reference_audio_path,
            output_path=output_dir,
            execute=lambda: _execute_start_audio_patch_studio_session(
                reference_audio_path=reference_audio_path,
                source_kit_path=source_kit_path,
                selection=selection,
                output_dir=output_dir,
                track=track,
                overwrite=overwrite,
            ),
        )


def _execute_start_audio_patch_studio_session(
    *,
    reference_audio_path: Path,
    source_kit_path: Path,
    selection: int,
    output_dir: Path,
    track: int,
    overwrite: bool,
) -> AudioPatchStudioSessionResult:
    """Execute a validated session start inside the recorded service boundary."""

    session_root = output_dir.resolve()
    _validate_inputs_outside_output_tree(
        output_dir=session_root,
        inputs={
            "reference audio": reference_audio_path,
            "source kit": source_kit_path,
        },
    )
    json_path = session_root / AUDIO_PATCH_STUDIO_SESSION_JSON_NAME
    if json_path.exists():
        result = load_audio_patch_studio_session(json_path)
        _verify_start_request(
            result.payload,
            reference_audio_path=reference_audio_path,
            source_kit_path=source_kit_path,
            selection=selection,
            track=track,
        )
        _verify_committed_artifacts(result.payload, session_root=session_root)
        return result

    reference_sha256 = _sha256_file(reference_audio_path)
    source_kit_sha256 = _sha256_file(source_kit_path)
    workspace_dir = session_root / AUDIO_PATCH_STUDIO_SESSION_WORKSPACE_DIR_NAME
    dna_result = _run_in_guarded_output_tree(
        session_root,
        workspace_dir,
        execute=lambda: export_audio_patch_dna_workspace(
            audio_path=reference_audio_path,
            output_dir=workspace_dir,
            track=track,
            selection=selection,
            source_kit_path=source_kit_path,
            overwrite=overwrite,
        ),
    )
    selected = dna_result.selected_candidate
    selected_export = dna_result.analog_four_export
    if selected is None or selected_export is None:
        raise ValueError("studio session requires one selected Audio-to-Patch DNA export")
    if len(selected_export.candidates) != 1:
        raise ValueError("studio session selected export must contain exactly one candidate")
    exported_candidate = selected_export.candidates[0]
    _require_hash_match(
        selected_export.audio_sha256,
        reference_sha256,
        "selected export reference audio",
    )
    _require_hash_match(
        selected_export.source_kit_sha256,
        source_kit_sha256,
        "selected export source kit",
    )
    workspace_payload: AudioPatchStudioSessionWorkspacePayload = {
        "json": _artifact_payload(session_root, dna_result.json_path),
        "markdown": _artifact_payload(session_root, dna_result.markdown_path),
    }
    selected_export_payload = _verified_export_payload(
        session_root=session_root,
        export_result=selected_export,
        exported_candidate=exported_candidate,
        expected_track=track,
        label="selected export",
    )
    _require_file_unchanged(reference_audio_path, reference_sha256, "reference audio")
    _require_file_unchanged(source_kit_path, source_kit_sha256, "source kit")
    session_id = _studio_session_id(
        reference_sha256=reference_sha256,
        source_kit_sha256=source_kit_sha256,
        selection=selection,
        track=track,
    )
    payload: AudioPatchStudioSessionPayload = {
        "schema_version": AUDIO_PATCH_STUDIO_SESSION_SCHEMA_VERSION,
        "session_id": session_id,
        "status": "waiting_for_render",
        "reference_audio": _file_payload(reference_audio_path, reference_sha256),
        "source_kit": _file_payload(source_kit_path, source_kit_sha256),
        "selection": {
            "dna_candidate": selected.column,
            "manifest_candidate": exported_candidate.candidate,
            "key": selected.key,
            "label": selected.label,
            "role": selected.role,
            "closeness": selected.closeness,
            "track": track,
            "generation_id": selected_export.generation_id,
        },
        "workspace": workspace_payload,
        "selected_export": selected_export_payload,
        "safety": list(AUDIO_PATCH_STUDIO_SESSION_SAFETY),
    }
    return _write_session(payload, session_root=session_root, overwrite=overwrite)


def resume_audio_patch_studio_session(  # noqa: PLR0913 - explicit resume contract
    *,
    session_path: Path,
    reference_audio_path: Path,
    source_kit_path: Path,
    render_audio_path: Path,
    correction_gain: float = ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
    accept_similarity: int = ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
    overwrite: bool = False,
) -> AudioPatchStudioSessionResult:
    """Measure one render and commit the terminal accepted/refined state."""

    with trace_operation(
        "a4_audio_patch_studio_session_resume",
        logger=_logger,
        session_name=analog_four_export_path_name(session_path),
        reference_name=analog_four_export_path_name(reference_audio_path),
        source_kit_name=analog_four_export_path_name(source_kit_path),
        render_name=analog_four_export_path_name(render_audio_path),
        correction_gain=correction_gain,
        accept_similarity=accept_similarity,
    ):
        return _run_session_operation(
            operation_name="a4_audio_patch_studio_session_resume",
            source_path=render_audio_path,
            output_path=session_path,
            execute=lambda: _execute_resume_audio_patch_studio_session(
                session_path=session_path,
                reference_audio_path=reference_audio_path,
                source_kit_path=source_kit_path,
                render_audio_path=render_audio_path,
                correction_gain=correction_gain,
                accept_similarity=accept_similarity,
                overwrite=overwrite,
            ),
        )


def _execute_resume_audio_patch_studio_session(  # noqa: PLR0913
    *,
    session_path: Path,
    reference_audio_path: Path,
    source_kit_path: Path,
    render_audio_path: Path,
    correction_gain: float,
    accept_similarity: int,
    overwrite: bool,
) -> AudioPatchStudioSessionResult:
    """Execute a validated session resume inside the recorded service boundary."""

    current = load_audio_patch_studio_session(session_path)
    session_root = current.json_path.parent
    payload = current.payload
    _validate_inputs_outside_output_tree(
        output_dir=session_root,
        inputs={
            "reference audio": reference_audio_path,
            "source kit": source_kit_path,
            "render audio": render_audio_path,
        },
    )
    _verify_external_file(payload["reference_audio"], reference_audio_path, "reference audio")
    _verify_external_file(payload["source_kit"], source_kit_path, "source kit")
    _verify_committed_artifacts(payload, session_root=session_root)
    render_sha256 = _sha256_file(render_audio_path)
    if payload["status"] != "waiting_for_render":
        refinement = payload.get("refinement")
        if (
            refinement is not None
            and refinement["render_audio"]["sha256"] == render_sha256
            and refinement["correction_gain"] == correction_gain
            and refinement["accept_similarity"] == accept_similarity
        ):
            return current
        raise ValueError(
            "studio session is already complete for a different render or refinement policy"
        )

    manifest_path = _resolve_artifact(
        session_root,
        payload["selected_export"]["manifest"],
    )
    refinement_dir = session_root / AUDIO_PATCH_STUDIO_SESSION_REFINEMENT_DIR_NAME
    refinement_result = _run_in_guarded_output_tree(
        session_root,
        refinement_dir,
        execute=lambda: export_analog_four_patch_refinement(
            reference_audio_path=reference_audio_path,
            manifest_path=manifest_path,
            candidate=payload["selection"]["manifest_candidate"],
            render_audio_path=render_audio_path,
            output_dir=refinement_dir,
            correction_gain=correction_gain,
            accept_similarity=accept_similarity,
            source_kit_path=source_kit_path,
            overwrite=overwrite,
        ),
    )
    result_payload = refinement_result.payload
    _require_hash_match(
        result_payload["reference_audio"]["sha256"],
        payload["reference_audio"]["sha256"],
        "refinement reference audio",
    )
    _require_hash_match(
        result_payload["render_audio"]["sha256"],
        render_sha256,
        "refinement render audio",
    )
    result_selection = result_payload["selection"]
    if (
        result_selection["generation_id"] != payload["selection"]["generation_id"]
        or result_selection["candidate"] != payload["selection"]["manifest_candidate"]
        or result_selection["track"] != payload["selection"]["track"]
    ):
        raise ValueError("refinement selection does not match the studio session")
    result_plan = result_payload["plan"]
    if (
        result_plan["candidate"] != payload["selection"]["manifest_candidate"]
        or result_plan["selected_track"] != payload["selection"]["track"]
        or result_plan["correction_gain"] != correction_gain
        or result_plan["accept_similarity"] != accept_similarity
        or result_plan["action"] != refinement_result.plan.action
        or result_plan["similarity"] != refinement_result.plan.similarity
    ):
        raise ValueError("refinement plan does not match the requested studio policy")
    refinement_payload: AudioPatchStudioSessionRefinementPayload = {
        "render_audio": _file_payload(render_audio_path, render_sha256),
        "action": refinement_result.plan.action,
        "similarity": refinement_result.plan.similarity,
        "correction_gain": correction_gain,
        "accept_similarity": accept_similarity,
        "json": _artifact_payload(session_root, refinement_result.json_path),
        "markdown": _artifact_payload(session_root, refinement_result.markdown_path),
    }
    next_export = refinement_result.analog_four_export
    if next_export is not None:
        if len(next_export.candidates) != 1:
            raise ValueError("studio session refinement must contain exactly one candidate")
        next_candidate = next_export.candidates[0]
        next_payload = result_payload["next_export"]
        if next_payload is None:
            raise ValueError("refinement result omitted next-export provenance")
        _require_hash_match(
            next_export.audio_sha256,
            payload["reference_audio"]["sha256"],
            "refinement export reference audio",
        )
        _require_hash_match(
            next_export.source_kit_sha256,
            payload["source_kit"]["sha256"],
            "refinement export source kit",
        )
        _require_hash_match(
            next_payload["manifest_sha256"],
            next_export.manifest_sha256,
            "refinement manifest provenance",
        )
        refinement_payload["next_export"] = _verified_export_payload(
            session_root=session_root,
            export_result=next_export,
            exported_candidate=next_candidate,
            expected_track=payload["selection"]["track"],
            label="refinement export",
        )
    elif result_payload["next_export"] is not None:
        raise ValueError("refinement payload reported an unexpected next export")
    _require_file_unchanged(
        reference_audio_path,
        payload["reference_audio"]["sha256"],
        "reference audio",
    )
    _require_file_unchanged(
        source_kit_path,
        payload["source_kit"]["sha256"],
        "source kit",
    )
    _require_file_unchanged(render_audio_path, render_sha256, "render audio")
    status: AudioPatchStudioSessionStatus = (
        "accepted" if refinement_result.plan.action == "accept" else "refined"
    )
    completed_payload: AudioPatchStudioSessionPayload = {
        **payload,
        "status": status,
        "refinement": refinement_payload,
    }
    return _write_session(completed_payload, session_root=session_root, overwrite=True)


def load_audio_patch_studio_session(session_path: Path) -> AudioPatchStudioSessionResult:
    """Load and structurally validate one committed session document."""

    if session_path.name != AUDIO_PATCH_STUDIO_SESSION_JSON_NAME:
        raise ValueError(f"studio session filename must be {AUDIO_PATCH_STUDIO_SESSION_JSON_NAME}")
    absolute_path = session_path.absolute()
    try:
        decoded: object = json.loads(_read_text(absolute_path))
    except json.JSONDecodeError as exc:
        raise ValueError("studio session JSON is invalid") from exc
    if not isinstance(decoded, dict):
        raise ValueError("studio session JSON must contain an object")
    payload = cast(dict[str, object], decoded)
    _validate_session_payload(payload)
    typed_payload = cast(AudioPatchStudioSessionPayload, payload)
    resolved_path = absolute_path.resolve()
    markdown_path = absolute_path.with_name(AUDIO_PATCH_STUDIO_SESSION_MARKDOWN_NAME)
    if _sha256_file(markdown_path) != cast(str, payload["summary_sha256"]):
        raise ValueError("studio session Markdown does not match the committed JSON state")
    return AudioPatchStudioSessionResult(
        payload=typed_payload,
        json_path=resolved_path,
        markdown_path=markdown_path,
    )


def _validate_session_payload(payload: dict[str, object]) -> None:
    _require_payload_keys(
        payload,
        {
            "schema_version",
            "session_id",
            "status",
            "reference_audio",
            "source_kit",
            "selection",
            "workspace",
            "selected_export",
            "safety",
            "summary_sha256",
        },
        {"refinement"},
        "studio session",
    )
    if payload.get("schema_version") != AUDIO_PATCH_STUDIO_SESSION_SCHEMA_VERSION:
        raise ValueError("unsupported studio session schema version")
    status = payload.get("status")
    if status not in {"waiting_for_render", "accepted", "refined"}:
        raise ValueError("studio session status is invalid")
    if not isinstance(payload.get("session_id"), str) or not payload["session_id"]:
        raise ValueError("studio session id is invalid")
    reference_audio = _require_mapping(payload.get("reference_audio"), "reference audio")
    source_kit = _require_mapping(payload.get("source_kit"), "source kit")
    selection = _require_mapping(payload.get("selection"), "selection")
    workspace = _require_mapping(payload.get("workspace"), "workspace")
    selected_export = _require_mapping(payload.get("selected_export"), "selected export")
    _validate_file_payload(reference_audio, "reference audio")
    _validate_file_payload(source_kit, "source kit")
    _validate_selection_payload(selection)
    _validate_workspace_payload(workspace)
    _validate_export_payload(selected_export, "selected export")
    _validate_sha256(payload.get("summary_sha256"), "studio session Markdown digest")
    safety = payload.get("safety")
    if safety != list(AUDIO_PATCH_STUDIO_SESSION_SAFETY):
        raise ValueError("studio session safety declaration is invalid")
    expected_session_id = _studio_session_id(
        reference_sha256=cast(str, reference_audio["sha256"]),
        source_kit_sha256=cast(str, source_kit["sha256"]),
        selection=cast(int, selection["dna_candidate"]),
        track=cast(int, selection["track"]),
    )
    if payload["session_id"] != expected_session_id:
        raise ValueError("studio session id does not match its request identity")
    refinement_value = payload.get("refinement")
    if status == "waiting_for_render":
        if refinement_value is not None:
            raise ValueError("waiting studio session must not contain refinement state")
        return
    refinement = _require_mapping(refinement_value, "refinement")
    _validate_refinement_payload(refinement, status=cast(AudioPatchStudioSessionStatus, status))


def _require_payload_keys(
    payload: dict[str, object],
    required: set[str],
    optional: set[str],
    label: str,
) -> None:
    actual = set(payload)
    missing = tuple(sorted(required - actual))
    unexpected = tuple(sorted(actual - required - optional))
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if unexpected:
            details.append(f"unexpected={','.join(unexpected)}")
        raise ValueError(f"{label} keys are invalid: {'; '.join(details)}")


def _require_mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    mapping = cast(dict[object, object], value)
    if any(not isinstance(key, str) for key in mapping):
        raise ValueError(f"{label} must be an object")
    return cast(dict[str, object], value)


def _require_nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _require_integer(value: object, label: str, *, lower: int, upper: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    if not lower <= value <= upper:
        raise ValueError(f"{label} must be in {lower}..{upper}")
    return value


def _require_number(value: object, label: str, *, lower: float, upper: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be a number")
    number = float(value)
    if not math.isfinite(number) or not lower <= number <= upper:
        raise ValueError(f"{label} must be finite and in {lower}..{upper}")
    return number


def _validate_sha256(value: object, label: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    validate_analog_four_patch_batch_sha256(value, label=label)


def _validate_filename(value: object, label: str) -> None:
    filename = _require_nonempty_string(value, label)
    if (
        filename in {".", ".."}
        or "/" in filename
        or "\\" in filename
        or ":" in filename
        or any(ord(character) < 32 for character in filename)
    ):
        raise ValueError(f"{label} must be a filename without directories")


def _validate_artifact_path(value: object, label: str) -> None:
    path_value = _require_nonempty_string(value, label)
    path = PurePosixPath(path_value)
    if (
        path.is_absolute()
        or path_value != path.as_posix()
        or path == PurePosixPath(".")
        or any(part in {"", ".", ".."} for part in path.parts)
        or "\\" in path_value
    ):
        raise ValueError(f"{label} must be a canonical relative POSIX path")


def _validate_file_payload(payload: dict[str, object], label: str) -> None:
    _require_payload_keys(payload, {"filename", "sha256"}, set(), label)
    _validate_filename(payload["filename"], f"{label} filename")
    _validate_sha256(payload["sha256"], f"{label} sha256")


def _validate_artifact_payload(payload: dict[str, object], label: str) -> None:
    _require_payload_keys(payload, {"path", "sha256"}, set(), label)
    _validate_artifact_path(payload["path"], f"{label} path")
    _validate_sha256(payload["sha256"], f"{label} sha256")


def _validate_selection_payload(payload: dict[str, object]) -> None:
    _require_payload_keys(
        payload,
        {
            "dna_candidate",
            "manifest_candidate",
            "key",
            "label",
            "role",
            "closeness",
            "track",
            "generation_id",
        },
        set(),
        "selection",
    )
    _require_integer(
        payload["dna_candidate"],
        "selection dna candidate",
        lower=1,
        upper=AUDIO_PATCH_DNA_CANDIDATE_COUNT,
    )
    _require_integer(
        payload["manifest_candidate"],
        "selection manifest candidate",
        lower=ANALOG_FOUR_PATCH_CANDIDATE_MIN,
        upper=ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    )
    _require_nonempty_string(payload["key"], "selection key")
    _require_nonempty_string(payload["label"], "selection label")
    _require_nonempty_string(payload["role"], "selection role")
    _require_integer(payload["closeness"], "selection closeness", lower=0, upper=100)
    _require_integer(
        payload["track"],
        "selection track",
        lower=A4_SYNTH_TRACK_MIN,
        upper=A4_SYNTH_TRACK_MAX,
    )
    _require_nonempty_string(payload["generation_id"], "selection generation id")


def _validate_workspace_payload(payload: dict[str, object]) -> None:
    _require_payload_keys(payload, {"json", "markdown"}, set(), "workspace")
    _validate_artifact_payload(
        _require_mapping(payload["json"], "workspace json"), "workspace json"
    )
    _validate_artifact_payload(
        _require_mapping(payload["markdown"], "workspace markdown"),
        "workspace markdown",
    )


def _validate_export_payload(payload: dict[str, object], label: str) -> None:
    _require_payload_keys(payload, {"manifest", "sysex", "sidecar"}, set(), label)
    for artifact_name in ("manifest", "sysex", "sidecar"):
        _validate_artifact_payload(
            _require_mapping(payload[artifact_name], f"{label} {artifact_name}"),
            f"{label} {artifact_name}",
        )


def _validate_refinement_payload(
    payload: dict[str, object],
    *,
    status: AudioPatchStudioSessionStatus,
) -> None:
    _require_payload_keys(
        payload,
        {
            "render_audio",
            "action",
            "similarity",
            "correction_gain",
            "accept_similarity",
            "json",
            "markdown",
        },
        {"next_export"},
        "refinement",
    )
    _validate_file_payload(
        _require_mapping(payload["render_audio"], "refinement render audio"),
        "refinement render audio",
    )
    action_value = payload["action"]
    if action_value not in _REFINEMENT_ACTIONS:
        raise ValueError("refinement action is invalid")
    action = action_value
    similarity = _require_integer(
        payload["similarity"],
        "refinement similarity",
        lower=ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MIN,
        upper=ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MAX,
    )
    _require_number(
        payload["correction_gain"],
        "refinement correction gain",
        lower=ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MIN,
        upper=ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MAX,
    )
    accept_similarity = _require_integer(
        payload["accept_similarity"],
        "refinement acceptance threshold",
        lower=ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MIN,
        upper=ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MAX,
    )
    expected_action: AnalogFourPatchRefinementAction = (
        "accept" if similarity >= accept_similarity else "refine"
    )
    if action != expected_action:
        raise ValueError("refinement action does not match its similarity threshold")
    _validate_artifact_payload(
        _require_mapping(payload["json"], "refinement json"),
        "refinement json",
    )
    _validate_artifact_payload(
        _require_mapping(payload["markdown"], "refinement markdown"),
        "refinement markdown",
    )
    next_export_value = payload.get("next_export")
    if status == "accepted":
        if action != "accept" or next_export_value is not None:
            raise ValueError("accepted studio session has inconsistent refinement state")
        return
    if status != "refined" or action != "refine" or next_export_value is None:
        raise ValueError("refined studio session has inconsistent refinement state")
    _validate_export_payload(
        _require_mapping(next_export_value, "refinement next export"),
        "refinement next export",
    )


def _verify_start_request(
    payload: AudioPatchStudioSessionPayload,
    *,
    reference_audio_path: Path,
    source_kit_path: Path,
    selection: int,
    track: int,
) -> None:
    _verify_external_file(payload["reference_audio"], reference_audio_path, "reference audio")
    _verify_external_file(payload["source_kit"], source_kit_path, "source kit")
    stored = payload["selection"]
    if stored["dna_candidate"] != selection or stored["track"] != track:
        raise ValueError("existing studio session does not match the requested selection")


def _verify_external_file(
    expected: AudioPatchStudioSessionFilePayload,
    path: Path,
    label: str,
) -> None:
    if _sha256_file(path) != expected["sha256"]:
        raise ValueError(f"{label} does not match the studio session")


def _verify_committed_artifacts(
    payload: AudioPatchStudioSessionPayload,
    *,
    session_root: Path,
) -> None:
    artifacts = (
        payload["workspace"]["json"],
        payload["workspace"]["markdown"],
        payload["selected_export"]["manifest"],
        payload["selected_export"]["sysex"],
        payload["selected_export"]["sidecar"],
    )
    for artifact in artifacts:
        _resolve_artifact(session_root, artifact)
    refinement = payload.get("refinement")
    if refinement is not None:
        _resolve_artifact(session_root, refinement["json"])
        _resolve_artifact(session_root, refinement["markdown"])
        next_export = refinement.get("next_export")
        if next_export is not None:
            for artifact in (
                next_export["manifest"],
                next_export["sysex"],
                next_export["sidecar"],
            ):
                _resolve_artifact(session_root, artifact)


def _write_session(
    payload: AudioPatchStudioSessionPayload,
    *,
    session_root: Path,
    overwrite: bool,
) -> AudioPatchStudioSessionResult:
    markdown_bytes = _render_session_markdown(payload).encode("utf-8")
    committed_payload = cast(
        AudioPatchStudioSessionPayload,
        {
            **payload,
            "summary_sha256": hashlib.sha256(markdown_bytes).hexdigest(),
        },
    )
    _validate_session_payload(cast(dict[str, object], committed_payload))
    json_bytes = (json.dumps(committed_payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    json_write, markdown_write = atomic_write_set(
        {
            session_root / AUDIO_PATCH_STUDIO_SESSION_JSON_NAME: json_bytes,
            session_root / AUDIO_PATCH_STUDIO_SESSION_MARKDOWN_NAME: markdown_bytes,
        },
        overwrite=overwrite,
    )
    return AudioPatchStudioSessionResult(
        payload=committed_payload,
        json_path=json_write.path,
        markdown_path=markdown_write.path,
        json_write=json_write,
        markdown_write=markdown_write,
    )


def _render_session_markdown(payload: AudioPatchStudioSessionPayload) -> str:
    selection = payload["selection"]
    lines = [
        "# Audio-to-Patch Studio Session",
        "",
        f"- Session ID: `{payload['session_id']}`",
        f"- Status: `{payload['status']}`",
        f"- DNA direction: {selection['dna_candidate']} — {selection['label']}",
        f"- Manifest candidate: {selection['manifest_candidate']}",
        f"- Track: {selection['track']}",
        f"- Closeness: {selection['closeness']}",
        "",
        "## Studio Step",
        "",
    ]
    if payload["status"] == "waiting_for_render":
        lines.extend(
            (
                "Load or audition the selected offline A4 artifact, record one clean render,",
                "then resume this session with that render. The session does not access hardware.",
            )
        )
    else:
        refinement = payload.get("refinement")
        if refinement is None:
            raise ValueError("completed studio session is missing refinement state")
        lines.extend(
            (
                f"- Decision: `{refinement['action']}`",
                f"- Similarity: {refinement['similarity']}",
                f"- Correction gain: {refinement['correction_gain']}",
                f"- Acceptance threshold: {refinement['accept_similarity']}",
            )
        )
    lines.extend(("", "## Safety", "", *(f"- {item}" for item in payload["safety"])))
    return "\n".join(lines) + "\n"


def _studio_session_id(
    *,
    reference_sha256: str,
    source_kit_sha256: str,
    selection: int,
    track: int,
) -> str:
    request = {
        "reference_sha256": reference_sha256,
        "schema_version": AUDIO_PATCH_STUDIO_SESSION_SCHEMA_VERSION,
        "selection": selection,
        "source_kit_sha256": source_kit_sha256,
        "track": track,
    }
    digest = hashlib.sha256(
        json.dumps(request, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"studio-{digest[:16]}"


def _file_payload(path: Path, sha256: str) -> AudioPatchStudioSessionFilePayload:
    return {"filename": path.name, "sha256": sha256}


def _artifact_payload(
    session_root: Path,
    path: Path,
) -> AudioPatchStudioSessionArtifactPayload:
    resolved_root = session_root.resolve()
    resolved_path = path.resolve()
    relative_path = _require_path_within_root(
        resolved_root,
        resolved_path,
        "studio session artifact",
    )
    return {"path": relative_path.as_posix(), "sha256": _sha256_file(resolved_path)}


def _verified_export_payload(
    *,
    session_root: Path,
    export_result: AnalogFourAudioPatchBatchExportResult,
    exported_candidate: AnalogFourPatchCandidateBatchResult,
    expected_track: int,
    label: str,
) -> AudioPatchStudioSessionExportPayload:
    if export_result.track != expected_track:
        raise ValueError(f"{label} track does not match the studio session")
    if (
        export_result.candidate_count != len(export_result.candidates)
        or export_result.candidate_count != 1
        or export_result.candidates[0] != exported_candidate
    ):
        raise ValueError(f"{label} candidate count does not match the studio session")
    manifest = _artifact_payload(session_root, export_result.manifest_path)
    sysex = _artifact_payload(session_root, exported_candidate.sysex_path)
    sidecar = _artifact_payload(session_root, exported_candidate.sidecar_path)
    _require_hash_match(manifest["sha256"], export_result.manifest_sha256, f"{label} manifest")
    _require_hash_match(
        sysex["sha256"],
        exported_candidate.sysex_export.render.sha256,
        f"{label} SysEx",
    )
    _require_hash_match(
        sidecar["sha256"],
        exported_candidate.sidecar_sha256,
        f"{label} sidecar",
    )
    return {"manifest": manifest, "sysex": sysex, "sidecar": sidecar}


def _require_hash_match(actual: str, expected: str, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label} hash does not match its reported provenance")


def _require_file_unchanged(path: Path, expected_sha256: str, label: str) -> None:
    _require_hash_match(_sha256_file(path), expected_sha256, label)


def _validate_output_tree(session_root: Path, output_dir: Path) -> None:
    lexical_root = session_root.absolute()
    lexical_output = output_dir.absolute()
    try:
        relative_output = lexical_output.relative_to(lexical_root)
    except ValueError as exc:
        raise ValueError("studio session output escaped the session root") from exc

    resolved_root = lexical_root.resolve()
    current = lexical_root
    _require_path_within_root(resolved_root, current.resolve(), "studio session root")
    for part in relative_output.parts:
        current /= part
        if current.exists() or current.is_symlink():
            _require_path_within_root(
                resolved_root,
                current.resolve(),
                "studio session output",
            )

    if not lexical_output.exists():
        return
    for directory, child_directories, filenames in os.walk(
        lexical_output,
        followlinks=False,
        onerror=_raise_walk_error,
    ):
        directory_path = Path(directory)
        _require_path_within_root(
            resolved_root,
            directory_path.resolve(),
            "studio session output",
        )
        for child_name in (*child_directories, *filenames):
            child_path = directory_path / child_name
            _require_path_within_root(
                resolved_root,
                child_path.resolve(),
                "studio session output",
            )


def _raise_walk_error(exc: OSError) -> None:
    raise AudioPatchStudioSessionAccessError(str(exc)) from exc


def _directory_identity(path: Path) -> tuple[int, int]:
    metadata = path.stat(follow_symlinks=False)
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("studio session output must remain a directory")
    return metadata.st_dev, metadata.st_ino


def _run_in_guarded_output_tree(
    session_root: Path,
    output_dir: Path,
    *,
    execute: Callable[[], _OutputResult],
) -> _OutputResult:
    """Pin one validated output directory while a child exporter publishes files."""

    _validate_output_tree(session_root, output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _validate_output_tree(session_root, output_dir)
    output_identity = _directory_identity(output_dir)
    guard_path = output_dir / _OUTPUT_GUARD_NAME
    active_exception: Exception | KeyboardInterrupt | SystemExit | None = None
    try:
        try:
            guard = guard_path.open("x+b")
        except FileExistsError as exc:
            raise AudioPatchStudioSessionLockedError(
                f"studio session publication already in progress: {_OUTPUT_GUARD_NAME}"
            ) from exc
        with guard, guard_atomic_write_tree(output_dir, output_identity):
            guard.write(b"audio-patch-studio-output\n")
            guard.flush()
            result = execute()
            if _directory_identity(output_dir) != output_identity:
                raise ValueError("studio session output identity changed during publication")
            _validate_output_tree(session_root, output_dir)
            return result
    except (Exception, KeyboardInterrupt, SystemExit) as exc:
        active_exception = exc
        raise
    finally:
        try:
            identity_unchanged = (
                output_dir.exists() and _directory_identity(output_dir) == output_identity
            )
        except (OSError, ValueError):
            identity_unchanged = False
        if identity_unchanged:
            try:
                guard_path.unlink(missing_ok=True)
            except OSError:
                if active_exception is None:
                    raise
                active_exception.add_note(
                    "studio session output guard cleanup failed after the primary error"
                )


def _require_path_within_root(root: Path, path: Path, label: str) -> Path:
    try:
        return path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escaped the session root") from exc


def _resolve_artifact(
    session_root: Path,
    artifact: AudioPatchStudioSessionArtifactPayload,
) -> Path:
    relative_path = Path(artifact["path"])
    if relative_path.is_absolute():
        raise ValueError("studio session artifact path must be relative")
    resolved_root = session_root.resolve()
    candidate_path = resolved_root / relative_path
    resolved_path = candidate_path.resolve()
    _require_path_within_root(resolved_root, resolved_path, "studio session artifact")
    if _sha256_file(candidate_path) != artifact["sha256"]:
        raise ValueError(f"studio session artifact hash mismatch: {relative_path.as_posix()}")
    return resolved_path


def _read_text(path: Path) -> str:
    with _open_regular_binary(path) as handle:
        return handle.read().decode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with _open_regular_binary(path) as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def _open_regular_binary(path: Path) -> Generator[BufferedReader, None, None]:
    """Open one unchanged regular file without following a pre-existing link."""

    artifact_name = safe_local_file_export_artifact_name(
        path,
        fallback="<invalid>",
    )
    descriptor = -1
    try:
        try:
            before = path.stat(follow_symlinks=False)
            if not stat.S_ISREG(before.st_mode):
                raise ValueError("studio session source must be a regular file")
            flags = (
                os.O_RDONLY
                | getattr(os, "O_BINARY", 0)
                | getattr(os, "O_NOINHERIT", 0)
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0)
            )
            descriptor = os.open(path, flags)
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or (
                opened.st_dev,
                opened.st_ino,
            ) != (before.st_dev, before.st_ino):
                raise ValueError("studio session source changed during open")
        except (OSError, ValueError) as exc:
            error_code = classify_local_file_export_error(exc, phase="source_read")
            attach_local_file_export_error_context(
                exc,
                error_code=error_code,
                phase="source_read",
                artifact_name=artifact_name,
            )
            attach_analog_four_export_error_code(exc, error_code)
            raise
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            yield handle
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _validate_inputs_outside_output_tree(
    *,
    output_dir: Path,
    inputs: Mapping[str, Path],
) -> None:
    """Reject input/output aliases before any child exporter can overwrite data."""

    resolved_output = output_dir.resolve(strict=False)
    for label, input_path in inputs.items():
        resolved_input = input_path.resolve(strict=False)
        try:
            resolved_input.relative_to(resolved_output)
        except ValueError:
            continue
        raise ValueError(f"{label} must not be inside the generated output tree")


__all__ = [
    "AUDIO_PATCH_STUDIO_SESSION_JSON_NAME",
    "AUDIO_PATCH_STUDIO_SESSION_MARKDOWN_NAME",
    "AUDIO_PATCH_STUDIO_SESSION_SAFETY",
    "AUDIO_PATCH_STUDIO_SESSION_SCHEMA_VERSION",
    "AudioPatchStudioSessionPayload",
    "AudioPatchStudioSessionResult",
    "load_audio_patch_studio_session",
    "resume_audio_patch_studio_session",
    "start_audio_patch_studio_session",
]
