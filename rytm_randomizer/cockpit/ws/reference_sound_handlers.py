"""Authenticated bounded reference-sound adapters, with no hardware imports."""

from __future__ import annotations

import asyncio
import base64
import binascii
import contextvars
import secrets
from collections.abc import Callable
from threading import Event
from typing import Final, TypeVar

from ...guardrails.input_validation import require_sequence
from ...observability.errors import BoundaryError, RytmRandomizerError
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ..data.stage import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID
from ..export.reference_sound_analysis import (
    sound_integer,
    sound_mapping,
    sound_number,
    sound_string_tuple,
    sound_text,
)
from ..export.reference_sound_audio import REFERENCE_AUDIO_MAX_BYTES, REFERENCE_AUDIO_MIN_BYTES
from ..export.reference_sound_candidates import list_reference_sound_controls
from ..export.reference_sound_errors import (
    REFERENCE_SOUND_FAILURE_MESSAGES,
    ReferenceSoundFailureReason,
    reference_sound_failure_reason,
)
from ..export.reference_sound_records import ReferenceSoundSessionPayload
from ..export.reference_sound_session import ReferenceSoundWorkspace
from ..export.reference_sound_store import reference_sound_digest
from .protocol import ERR_VALIDATION, EVENT_SEND_PLAN_CHANGED
from .result import HandlerResult
from .session import CockpitSession

REFERENCE_SOUND_CHUNK_BYTES: Final[int] = 192 * 1024
_Result = TypeVar("_Result")
_logger = get_logger(__name__)


def cancel_reference_sound(session: CockpitSession) -> None:
    """Revoke owned analysis and unfinished uploads without changing retained files."""
    if session.sound_cancel is not None:
        session.sound_cancel.set()
    session.sound_upload = b""
    session.sound_upload_id = None
    session.sound_upload_size = 0


def _sound_workspace(session: CockpitSession) -> ReferenceSoundWorkspace:
    if session.reference_sounds is None:
        session.reference_sounds = ReferenceSoundWorkspace()
    return session.reference_sounds


def _reply(**values: object) -> HandlerResult:
    return HandlerResult(ack={"ok": True, "reference_sound": values})


def _sound_refusal(
    reason: ReferenceSoundFailureReason, *, error_type: str = "GuardrailDecision"
) -> HandlerResult:
    _logger.warning(
        "reference_sound_refused",
        extra={
            "error_type": error_type,
            "fingerprint": f"reference_sound.{reason}",
            "reason": reason,
        },
    )
    get_metrics().record_error(f"reference_sound.{reason}")
    return HandlerResult(
        ack={
            "ok": False,
            "code": ERR_VALIDATION,
            "reason": reason,
            "message": REFERENCE_SOUND_FAILURE_MESSAGES[reason],
        }
    )


def _sound_session_result(
    session: CockpitSession, payload: ReferenceSoundSessionPayload
) -> HandlerResult:
    session.current_send_plan = None
    return HandlerResult(
        ack={"ok": True, "reference_sound": {"session": payload}},
        events=[{"type": EVENT_SEND_PLAN_CHANGED, "send_plan": None}],
    )


async def _owned_operation(session: CockpitSession, execute: Callable[[Event], _Result]) -> _Result:
    if session.sound_cancel is not None:
        raise ValueError("Another audio operation is running; cancel it first.")
    cancel = Event()
    session.sound_cancel = cancel
    try:
        # A private executor future survives loop-wide task cancellation.
        context = contextvars.copy_context()

        def invoke() -> _Result:
            return context.run(execute, cancel)

        task = asyncio.get_running_loop().run_in_executor(None, invoke)
        try:
            result = await asyncio.shield(task)
            if cancel.is_set():
                raise BoundaryError(
                    "Audio operation was cancelled.", context={"error_code": "interrupted"}
                )
            return result
        except asyncio.CancelledError:
            cancel.set()
            # Drain despite repeat cancellation before releasing ownership.
            while True:
                try:
                    await asyncio.shield(task)
                    break
                except asyncio.CancelledError:
                    continue
                except (
                    KeyError,
                    TypeError,
                    ValueError,
                    OSError,
                    RuntimeError,
                    RytmRandomizerError,
                ) as exc:
                    if reference_sound_failure_reason(exc) == "interrupted":
                        _logger.info(
                            "reference_sound_cancel_cleanup_completed",
                            extra={"reason": "interrupted"},
                        )
                    else:
                        _logger.warning(
                            "reference_sound_cancel_cleanup_failed",
                            extra={"error_type": type(exc).__name__},
                        )
                        get_metrics().record_error("reference_sound.cancel_cleanup_failed")
                    break
            raise
    finally:
        if session.sound_cancel is cancel:
            session.sound_cancel = None


def _source(cmd: dict[str, object], session: CockpitSession) -> tuple[bytes, str, int]:
    if session.library_store is None:
        raise ValueError("Import a backed-up KIT into the source library first.")
    record_id = sound_text(cmd["source_record_id"])
    record = session.library_store.get(record_id, strict_original_source=True)
    device_id = sound_text(cmd["device_id"])
    target = sound_integer(cmd["target"])
    if record is None or record.device_id != device_id:
        raise ValueError("Selected KIT belongs to a different device or is missing.")
    frame = session.library_store.read_source_frame(record_id)
    return frame, device_id, target


def _upload_bytes(cmd: dict[str, object], session: CockpitSession) -> bytes:
    if session.sound_upload_id is None or cmd.get("upload_id") != session.sound_upload_id:
        raise ValueError("Upload is stale; choose the audio file again.")
    if len(session.sound_upload) != session.sound_upload_size:
        raise ValueError("Audio upload is incomplete; finish its chunks first.")
    return session.sound_upload


def _operator_context(session: CockpitSession) -> tuple[object, ...]:
    return (
        frozenset(session.pad_locks),
        frozenset(session.a4_track_locks),
        frozenset(session.rytm_pad_targets),
        frozenset(session.a4_track_targets),
        session.rytm_parameters,
        session.a4_parameters,
        session.hardware_intent,
        session.armed_apply,
        session.capture_generation,
    )


def _sound_upload(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    action = sound_text(cmd["action"])
    if action == "upload_begin":
        if session.sound_upload_id is not None:
            raise ValueError("Cancel the unfinished upload before choosing another file.")
        size = sound_integer(cmd["size"])
        if not REFERENCE_AUDIO_MIN_BYTES <= size <= REFERENCE_AUDIO_MAX_BYTES:
            raise ValueError("Choose an uncompressed PCM WAV up to 16 MiB.")
        session.sound_upload_id = secrets.token_hex(16)
        session.sound_upload_size = size
        session.sound_upload = b""
        return _reply(upload_id=session.sound_upload_id, received=0)
    if action == "upload_chunk":
        if session.sound_upload_id is None or cmd.get("upload_id") != session.sound_upload_id:
            raise ValueError("Upload is stale; choose the audio file again.")
        encoded = cmd["chunk"]
        if (
            not isinstance(encoded, str)
            or not 1 <= len(encoded) <= REFERENCE_SOUND_CHUNK_BYTES * 4 // 3 + 4
        ):
            raise ValueError("Audio upload chunk exceeds its supported bound.")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("Audio upload chunk is not valid base64.") from exc
        offset = sound_integer(cmd["offset"])
        if (
            offset != len(session.sound_upload)
            or not 1 <= len(data) <= REFERENCE_SOUND_CHUNK_BYTES
            or offset + len(data) > session.sound_upload_size
        ):
            raise ValueError("Audio upload chunk is out of order or exceeds the declared size.")
        session.sound_upload += data
        return _reply(upload_id=session.sound_upload_id, received=len(session.sound_upload))
    if action == "upload_finish":
        audio = _upload_bytes(cmd, session)
        result = _sound_workspace(session).import_reference(audio, sound_text(cmd["title"]))
        cancel_reference_sound(session)
        return _reply(session=result)
    raise ValueError("Reference-sound upload action is not supported.")


def _sound_inputs(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    action = sound_text(cmd["action"])
    if action in ("upload_begin", "upload_chunk", "upload_finish"):
        return _sound_upload(cmd, session)
    if action == "list":
        summaries: list[dict[str, object]] = []
        for item in _sound_workspace(session).store.catalog():
            summary = {
                key: item[key] for key in ("session_id", "title", "segment", "context", "favorites")
            }
            summary["candidate_count"] = len(
                require_sequence(item["candidates"], "retained candidates", ValueError)
            )
            summary["recording_count"] = len(
                require_sequence(item["recordings"], "retained recordings", ValueError)
            )
            summaries.append(summary)
        return _reply(sessions=summaries)
    if action == "controls":
        frame, device, target = _source(cmd, session)
        return _reply(
            controls=[
                item.to_dict() for item in list_reference_sound_controls(frame, device, target)
            ]
        )
    raise ValueError("Reference-sound input action is not supported.")


async def _sound_analysis_operation(
    cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
    action = sound_text(cmd["action"])
    workspace = _sound_workspace(session)
    session_id = sound_text(cmd["session_id"])
    if action == "generate":
        source, device, target = _source(cmd, session)
        parameters = sound_string_tuple(cmd["parameters"])
        locks = sound_string_tuple(cmd["locks"])
        lock_sets = {
            ANALOG_RYTM_DEVICE_ID: session.pad_locks,
            ANALOG_FOUR_DEVICE_ID: session.a4_track_locks,
        }
        if target in lock_sets.get(device, set()):
            raise BoundaryError(
                "The selected pad/track is locked. Unlock it explicitly before generation.",
                context={"error_code": "target_locked"},
            )
        owner_context = _operator_context(session)
        result = await _owned_operation(
            session,
            lambda cancel: workspace.generate(
                session_id,
                source_frame=source,
                device_id=device,
                target=target,
                parameters=parameters,
                locks=locks,
                strength=sound_number(cmd["strength"]),
                cancel=cancel,
            ),
        )
        if owner_context != _operator_context(session) or _source(cmd, session)[0] != source:
            raise BoundaryError(
                "Source, locks or scope changed during analysis. No candidate was published; prepare again.",
                context={"error_code": "stale_generation_context"},
            )
        payload = workspace.commit(result)
        return _sound_session_result(session, payload)
    if action == "record":
        audio = _upload_bytes(cmd, session)
        result = await _owned_operation(
            session,
            lambda cancel: workspace.compare(
                session_id,
                sound_text(cmd["candidate_id"]),
                candidate_sha256=sound_text(cmd["candidate_sha256"]),
                recording=audio,
                cancel=cancel,
            ),
        )
        payload = workspace.commit(result)
        cancel_reference_sound(session)
        return _reply(session=payload)
    if action == "refine":
        payload = workspace.reopen(session_id)
        context = sound_mapping(payload["context"])
        device = sound_text(context["device_id"])
        target = sound_integer(context["target"])
        lock_sets = {
            ANALOG_RYTM_DEVICE_ID: session.pad_locks,
            ANALOG_FOUR_DEVICE_ID: session.a4_track_locks,
        }
        if target in lock_sets.get(device, set()):
            raise BoundaryError(
                "The selected pad/track is locked. Unlock it explicitly before refinement.",
                context={"error_code": "target_locked"},
            )
        owner_context = _operator_context(session)
        result = await _owned_operation(
            session,
            lambda cancel: workspace.refine(
                session_id,
                sound_text(cmd["candidate_id"]),
                correction_gain=sound_number(cmd["correction_gain"]),
                cancel=cancel,
            ),
        )
        if owner_context != _operator_context(session):
            raise BoundaryError(
                "Locks or scope changed during refinement. No candidate was published; prepare again.",
                context={"error_code": "stale_refinement_context"},
            )
        payload = workspace.commit(result)
        return _sound_session_result(session, payload)
    raise ValueError("Reference-sound analysis action is not supported.")


def _sound_retention(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    action = sound_text(cmd["action"])
    workspace = _sound_workspace(session)
    session_id = sound_text(cmd["session_id"])
    if action == "reopen":
        return _sound_session_result(session, workspace.reopen(session_id))
    if action == "segment":
        return _sound_session_result(
            session,
            workspace.select_segment(
                session_id, sound_integer(cmd["start_frame"]), sound_integer(cmd["frame_count"])
            ),
        )
    if action in ("select", "favorite"):
        favorite = cmd.get("favorite") if action == "favorite" else None
        if favorite is not None and not isinstance(favorite, bool):
            raise ValueError("Favorite must be a boolean.")
        return _sound_session_result(
            session,
            workspace.select(session_id, sound_text(cmd["candidate_id"]), favorite=favorite),
        )
    raise ValueError("Reference-sound retention action is not supported.")


def _sound_outputs(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    action = sound_text(cmd["action"])
    workspace = _sound_workspace(session)
    session_id = sound_text(cmd["session_id"])
    if action == "read_audio":
        payload = workspace.reopen(session_id)
        segment = sound_mapping(payload["segment"])
        digest = sound_text(segment["sha256"])
        kind = cmd.get("audio_kind", "segment")
        if kind == "original":
            digest = sound_text(sound_mapping(segment["original"])["sha256"])
        elif kind == "recording":
            requested = sound_text(cmd["recording_sha256"])
            records = require_sequence(payload["recordings"], "retained recordings", ValueError)
            if not any(sound_mapping(item)["audio_sha256"] == requested for item in records):
                return _sound_refusal("recording_not_in_session")
            digest = requested
        elif kind != "segment":
            return _sound_refusal("audio_kind_invalid")
        audio = workspace.store.read_artifact(digest, "wav")
        offset = sound_integer(cmd["offset"])
        if not 0 <= offset < len(audio):
            raise ValueError("Audio playback offset is outside the retained segment.")
        return _reply(
            audio_chunk=base64.b64encode(
                audio[offset : offset + REFERENCE_SOUND_CHUNK_BYTES]
            ).decode("ascii"),
            offset=offset,
            size=len(audio),
            sha256=digest,
        )
    if action == "export":
        candidate = workspace.candidate(session_id, sound_text(cmd["candidate_id"]))
        destination = sound_integer(cmd["destination_slot"])
        exported = workspace.export_patch(session_id, candidate.candidate_id, destination)
        return _reply(
            sysex_base64=base64.b64encode(exported).decode("ascii"),
            sha256=reference_sound_digest(exported),
            candidate_id=candidate.candidate_id,
            destination_slot=destination,
        )
    raise ValueError("Reference-sound action is not supported.")


async def _execute_reference_sound(
    cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
    action = sound_text(cmd["action"])
    if action == "cancel":
        cancel_reference_sound(session)
        return _reply(cancelled=True)
    if session.sound_cancel is not None:
        return _sound_refusal("operation_busy")
    if action in ("list", "controls", "upload_begin", "upload_chunk", "upload_finish"):
        return _sound_inputs(cmd, session)
    if action in ("generate", "record", "refine"):
        return await _sound_analysis_operation(cmd, session)
    if action in ("reopen", "segment", "select", "favorite"):
        return _sound_retention(cmd, session)
    return _sound_outputs(cmd, session)


async def handle_reference_sound(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    """Keep all failures actionable without exposing audio, paths or decoder details."""
    if (
        session.hardware_intent
        or session.armed_apply is not None
        or session.capture_cancel is not None
    ):
        return _sound_refusal("hardware_active")
    try:
        return await _execute_reference_sound(cmd, session)
    except asyncio.CancelledError:
        raise
    except (KeyError, TypeError, ValueError, OSError, RuntimeError, RytmRandomizerError) as exc:
        reason = reference_sound_failure_reason(exc)
        return _sound_refusal(reason, error_type=type(exc).__name__)
