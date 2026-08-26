"""Resumable passive studio session for Audio-to-Patch DNA refinement."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, TypedDict, cast

from ...data.analog_four_patch_refinement import (
    ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
)
from .analog_four_patch_refinement import export_analog_four_patch_refinement
from .audio_patch_dna import export_audio_patch_dna_workspace
from .writer import WriteResult, atomic_write_set

AUDIO_PATCH_STUDIO_SESSION_SCHEMA_VERSION: Final[str] = "audio-patch-studio-session-v1"
AUDIO_PATCH_STUDIO_SESSION_JSON_NAME: Final[str] = "studio-session.json"
AUDIO_PATCH_STUDIO_SESSION_MARKDOWN_NAME: Final[str] = "studio-session.md"
AUDIO_PATCH_STUDIO_SESSION_WORKSPACE_DIR_NAME: Final[str] = "workspace"
AUDIO_PATCH_STUDIO_SESSION_REFINEMENT_DIR_NAME: Final[str] = "refinement"
AUDIO_PATCH_STUDIO_SESSION_MANIFEST_CANDIDATE: Final[int] = 1
AUDIO_PATCH_STUDIO_SESSION_SAFETY: Final[tuple[str, ...]] = (
    "passive local audio analysis and offline artifact generation",
    "candidate selection is explicit and hash-bound to this session",
    "session artifacts are hash-verified before refinement",
    "no MIDI ports enumerated or opened",
    "no MIDI or SysEx transmitted",
    "no hardware mutation",
    "no network access",
)

AudioPatchStudioSessionStatus = Literal["waiting_for_render", "accepted", "refined"]


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


class AudioPatchStudioSessionSelectedExportPayload(TypedDict):
    manifest: AudioPatchStudioSessionArtifactPayload
    sysex: AudioPatchStudioSessionArtifactPayload
    sidecar: AudioPatchStudioSessionArtifactPayload


class AudioPatchStudioSessionNextExportPayload(TypedDict):
    manifest: AudioPatchStudioSessionArtifactPayload
    sysex: AudioPatchStudioSessionArtifactPayload
    sidecar: AudioPatchStudioSessionArtifactPayload


class _AudioPatchStudioSessionResultOptionalPayload(TypedDict, total=False):
    next_export: AudioPatchStudioSessionNextExportPayload


class AudioPatchStudioSessionRefinementPayload(_AudioPatchStudioSessionResultOptionalPayload):
    render_audio: AudioPatchStudioSessionFilePayload
    action: Literal["accept", "refine"]
    similarity: int
    json: AudioPatchStudioSessionArtifactPayload
    markdown: AudioPatchStudioSessionArtifactPayload


class _AudioPatchStudioSessionOptionalPayload(TypedDict, total=False):
    refinement: AudioPatchStudioSessionRefinementPayload


class AudioPatchStudioSessionPayload(_AudioPatchStudioSessionOptionalPayload):
    """Durable, deterministic state for one studio feedback cycle."""

    schema_version: str
    session_id: str
    status: AudioPatchStudioSessionStatus
    reference_audio: AudioPatchStudioSessionFilePayload
    source_kit: AudioPatchStudioSessionFilePayload
    selection: AudioPatchStudioSessionSelectionPayload
    workspace: AudioPatchStudioSessionWorkspacePayload
    selected_export: AudioPatchStudioSessionSelectedExportPayload
    safety: list[str]


@dataclass(frozen=True)
class AudioPatchStudioSessionResult:
    """One loaded or newly committed studio-session state."""

    payload: AudioPatchStudioSessionPayload
    json_path: Path
    markdown_path: Path
    json_write: WriteResult | None = None
    markdown_write: WriteResult | None = None


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

    session_root = output_dir.resolve()
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
    dna_result = export_audio_patch_dna_workspace(
        audio_path=reference_audio_path,
        output_dir=session_root / AUDIO_PATCH_STUDIO_SESSION_WORKSPACE_DIR_NAME,
        track=track,
        selection=selection,
        source_kit_path=source_kit_path,
        overwrite=overwrite,
    )
    selected = dna_result.selected_candidate
    selected_export = dna_result.analog_four_export
    if selected is None or selected_export is None:
        raise ValueError("studio session requires one selected Audio-to-Patch DNA export")
    if len(selected_export.candidates) != 1:
        raise ValueError("studio session selected export must contain exactly one candidate")
    exported_candidate = selected_export.candidates[0]
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
            "manifest_candidate": AUDIO_PATCH_STUDIO_SESSION_MANIFEST_CANDIDATE,
            "key": selected.key,
            "label": selected.label,
            "role": selected.role,
            "closeness": selected.closeness,
            "track": track,
            "generation_id": selected_export.generation_id,
        },
        "workspace": {
            "json": _artifact_payload(session_root, dna_result.json_path),
            "markdown": _artifact_payload(session_root, dna_result.markdown_path),
        },
        "selected_export": {
            "manifest": _artifact_payload(session_root, selected_export.manifest_path),
            "sysex": _artifact_payload(session_root, exported_candidate.sysex_path),
            "sidecar": _artifact_payload(session_root, exported_candidate.sidecar_path),
        },
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

    current = load_audio_patch_studio_session(session_path)
    session_root = current.json_path.parent
    payload = current.payload
    _verify_external_file(payload["reference_audio"], reference_audio_path, "reference audio")
    _verify_external_file(payload["source_kit"], source_kit_path, "source kit")
    _verify_committed_artifacts(payload, session_root=session_root)
    render_sha256 = _sha256_file(render_audio_path)
    if payload["status"] != "waiting_for_render":
        refinement = payload.get("refinement")
        if refinement is None or refinement["render_audio"]["sha256"] != render_sha256:
            raise ValueError("studio session is already complete for a different render")
        return current

    manifest_path = _resolve_artifact(
        session_root,
        payload["selected_export"]["manifest"],
    )
    refinement_result = export_analog_four_patch_refinement(
        reference_audio_path=reference_audio_path,
        manifest_path=manifest_path,
        candidate=payload["selection"]["manifest_candidate"],
        render_audio_path=render_audio_path,
        output_dir=session_root / AUDIO_PATCH_STUDIO_SESSION_REFINEMENT_DIR_NAME,
        correction_gain=correction_gain,
        accept_similarity=accept_similarity,
        source_kit_path=source_kit_path,
        overwrite=overwrite,
    )
    refinement_payload: AudioPatchStudioSessionRefinementPayload = {
        "render_audio": _file_payload(render_audio_path, render_sha256),
        "action": refinement_result.plan.action,
        "similarity": refinement_result.plan.similarity,
        "json": _artifact_payload(session_root, refinement_result.json_path),
        "markdown": _artifact_payload(session_root, refinement_result.markdown_path),
    }
    next_export = refinement_result.analog_four_export
    if next_export is not None:
        if len(next_export.candidates) != 1:
            raise ValueError("studio session refinement must contain exactly one candidate")
        next_candidate = next_export.candidates[0]
        refinement_payload["next_export"] = {
            "manifest": _artifact_payload(session_root, next_export.manifest_path),
            "sysex": _artifact_payload(session_root, next_candidate.sysex_path),
            "sidecar": _artifact_payload(session_root, next_candidate.sidecar_path),
        }
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

    resolved_path = session_path.resolve()
    try:
        decoded: object = json.loads(resolved_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("studio session JSON is invalid") from exc
    if not isinstance(decoded, dict):
        raise ValueError("studio session JSON must contain an object")
    payload = cast(dict[str, object], decoded)
    _validate_session_payload(payload)
    typed_payload = cast(AudioPatchStudioSessionPayload, payload)
    return AudioPatchStudioSessionResult(
        payload=typed_payload,
        json_path=resolved_path,
        markdown_path=resolved_path.with_name(AUDIO_PATCH_STUDIO_SESSION_MARKDOWN_NAME),
    )


def _validate_session_payload(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != AUDIO_PATCH_STUDIO_SESSION_SCHEMA_VERSION:
        raise ValueError("unsupported studio session schema version")
    status = payload.get("status")
    if status not in {"waiting_for_render", "accepted", "refined"}:
        raise ValueError("studio session status is invalid")
    required_mappings = (
        "reference_audio",
        "source_kit",
        "selection",
        "workspace",
        "selected_export",
    )
    if not isinstance(payload.get("session_id"), str):
        raise ValueError("studio session id is invalid")
    if any(not isinstance(payload.get(key), dict) for key in required_mappings):
        raise ValueError("studio session is missing required state")
    if not isinstance(payload.get("safety"), list):
        raise ValueError("studio session safety declaration is invalid")
    if status != "waiting_for_render" and not isinstance(payload.get("refinement"), dict):
        raise ValueError("completed studio session is missing refinement state")


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
    json_bytes = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    markdown_bytes = _render_session_markdown(payload).encode("utf-8")
    json_write, markdown_write = atomic_write_set(
        {
            session_root / AUDIO_PATCH_STUDIO_SESSION_JSON_NAME: json_bytes,
            session_root / AUDIO_PATCH_STUDIO_SESSION_MARKDOWN_NAME: markdown_bytes,
        },
        overwrite=overwrite,
    )
    return AudioPatchStudioSessionResult(
        payload=payload,
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
    try:
        relative_path = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("studio session artifact escaped the session root") from exc
    return {"path": relative_path.as_posix(), "sha256": _sha256_file(resolved_path)}


def _resolve_artifact(
    session_root: Path,
    artifact: AudioPatchStudioSessionArtifactPayload,
) -> Path:
    relative_path = Path(artifact["path"])
    if relative_path.is_absolute():
        raise ValueError("studio session artifact path must be relative")
    resolved_root = session_root.resolve()
    resolved_path = (resolved_root / relative_path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("studio session artifact escaped the session root") from exc
    if _sha256_file(resolved_path) != artifact["sha256"]:
        raise ValueError(f"studio session artifact hash mismatch: {relative_path.as_posix()}")
    return resolved_path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.resolve().open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
