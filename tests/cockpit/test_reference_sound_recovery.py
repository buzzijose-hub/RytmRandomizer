"""Fixed recovery actions remain private and bounded at the actual handler boundary."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from threading import Event

import pytest
from cockpit.conftest import make_reference_pcm, make_reference_sound_session

from rytm_randomizer.cockpit.export.reference_sound_errors import (
    REFERENCE_SOUND_FAILURE_MESSAGES,
    ReferenceSoundFailureReason,
    narrow_reference_sound_failure_reason,
    reference_sound_error_context,
    reference_sound_failure_reason,
)
from rytm_randomizer.cockpit.export.reference_sound_session import ReferenceSoundWorkspace
from rytm_randomizer.cockpit.ws import reference_sound_handlers as handlers
from rytm_randomizer.cockpit.ws.result import HandlerResult
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.observability.errors import (
    BoundaryError,
    DataError,
    PersistedStateVersionError,
)
from rytm_randomizer.observability.metrics import get_metrics
from rytm_randomizer.style_analysis.extractor import StyleAnalysisDependencyError

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


@pytest.mark.parametrize("action", ["generate", "refine"])
def test_oversized_numeric_request_is_refused_without_publication_or_lost_ownership(
    action: str,
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    original = workspace.import_reference(make_reference_pcm(), "Numeric refusal fixture")
    frame, device, target, parameters = reference_sound_source
    generated = workspace.commit(
        workspace.generate(
            original["session_id"],
            source_frame=frame,
            device_id=device,
            target=target,
            parameters=parameters,
            locks=(),
            strength=0.1,
            cancel=Event(),
        )
    )
    command = {
        "action": action,
        "session_id": generated["session_id"],
        "candidate_id": generated["selected_candidate_id"],
        "correction_gain": 10**1000,
        "source_record_id": source_id,
        "device_id": device,
        "target": target,
        "parameters": list(parameters),
        "locks": [],
        "strength": 10**1000,
    }
    before = {
        item.name: item.read_bytes()
        for item in workspace.store.directory.iterdir()
        if item.is_file()
    }
    result = asyncio.run(handlers.handle_reference_sound(command, session))
    assert result.ack is not None and result.ack["ok"] is False
    assert result.ack["reason"] == "invalid_identity"
    assert session.sound_cancel is None and session.current_send_plan is None
    assert {
        item.name: item.read_bytes()
        for item in workspace.store.directory.iterdir()
        if item.is_file()
    } == before
    assert workspace.reopen(generated["session_id"]) == generated


@pytest.mark.parametrize(
    "reason",
    ["hardware_active", "operation_busy", "recording_not_in_session", "audio_kind_invalid"],
)
def test_actual_guardrail_refusal_emits_one_fixed_reason_log_and_counter(
    reason: ReferenceSoundFailureReason,
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = reference_sound_workspace
    session, _ = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    original = workspace.import_reference(make_reference_pcm(), "Guardrail fixture")
    command: dict[str, object] = {"action": "list"}
    if reason == "hardware_active":
        session.hardware_intent = True
    elif reason == "operation_busy":
        session.sound_cancel = Event()
    else:
        command = {
            "action": "read_audio",
            "session_id": original["session_id"],
            "offset": 0,
            "audio_kind": "recording" if reason == "recording_not_in_session" else "unsupported",
            "recording_sha256": "f" * 64,
        }
    monkeypatch.setattr(handlers._logger, "handlers", [caplog.handler])
    monkeypatch.setattr(handlers._logger, "propagate", False)
    before = get_metrics().errors_by_kind[f"reference_sound.{reason}"]
    result = asyncio.run(handlers.handle_reference_sound(command, session))
    assert result.ack is not None and result.ack["reason"] == reason
    assert result.ack["message"] == REFERENCE_SOUND_FAILURE_MESSAGES[reason]
    assert get_metrics().errors_by_kind[f"reference_sound.{reason}"] == before + 1
    records = [item for item in caplog.records if item.message == "reference_sound_refused"]
    assert len(records) == 1 and records[0].reason == reason
    assert records[0].fingerprint == f"reference_sound.{reason}"
    assert result.events == []


@pytest.mark.parametrize("reason", tuple(REFERENCE_SOUND_FAILURE_MESSAGES))
def test_each_reason_has_a_fixed_private_wire_message_log_and_metric(
    reason: ReferenceSoundFailureReason,
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    session, _ = make_reference_sound_session(
        tmp_path, reference_sound_workspace, reference_sound_source
    )
    private = "C:/private-client/secret-song.wav bearer-private-value"

    async def fail(cmd: dict[str, object], owner: CockpitSession) -> HandlerResult:
        raise BoundaryError(private, context={"error_code": reason, "path": private})

    monkeypatch.setattr(handlers, "_execute_reference_sound", fail)
    monkeypatch.setattr(handlers._logger, "handlers", [caplog.handler])
    monkeypatch.setattr(handlers._logger, "propagate", False)
    before = get_metrics().errors_by_kind[f"reference_sound.{reason}"]
    result = asyncio.run(handlers.handle_reference_sound({"action": "list"}, session))
    assert result.ack == {
        "ok": False,
        "code": "validation_error",
        "reason": reason,
        "message": REFERENCE_SOUND_FAILURE_MESSAGES[reason],
    }
    assert result.events == []
    assert get_metrics().errors_by_kind[f"reference_sound.{reason}"] == before + 1
    records = [record for record in caplog.records if record.message == "reference_sound_refused"]
    assert records[-1].reason == reason
    assert private not in json.dumps(result.ack) + caplog.text + repr(records[-1].__dict__)
    error = BoundaryError(
        REFERENCE_SOUND_FAILURE_MESSAGES[reason], context=reference_sound_error_context(reason)
    )
    assert isinstance(error, BoundaryError)
    assert error.context["error_code"] == reason
    assert reference_sound_failure_reason(error) == reason


@pytest.mark.parametrize("invalid", [None, [], 1, "private-token", "inference_failed"])
def test_unknown_context_cannot_add_a_metric_label(invalid: object) -> None:
    with pytest.raises(ValueError, match="not supported"):
        narrow_reference_sound_failure_reason(invalid)
    assert reference_sound_failure_reason(
        BoundaryError("private path", context={"error_code": invalid})
    ) == ("worker_failed" if invalid == "inference_failed" else "invalid_identity")


@pytest.mark.parametrize(
    "error,reason",
    [
        (InterruptedError("private"), "interrupted"),
        (StyleAnalysisDependencyError("private"), "dependency_missing"),
        (FileNotFoundError("private"), "artifact_missing"),
        (DataError("private", context={"category": "missing"}), "artifact_missing"),
        (PersistedStateVersionError("private"), "schema_newer"),
        (DataError("private", context={"category": "schema"}), "session_corrupt"),
        (BoundaryError("private", context={"error_code": "audio_read_failed"}), "audio_invalid"),
        (PermissionError("private"), "storage_unavailable"),
        (RuntimeError("private"), "worker_failed"),
        (BoundaryError("private", context={"error_code": "inference_failed"}), "worker_failed"),
        (DataError("private", context={"category": "hash"}), "invalid_identity"),
        (ValueError("private"), "invalid_identity"),
        (TypeError("private"), "invalid_identity"),
        (KeyError("private"), "invalid_identity"),
    ],
)
def test_existing_taxonomy_classifies_without_exception_text(
    error: BaseException, reason: ReferenceSoundFailureReason
) -> None:
    assert reference_sound_failure_reason(error) == reason


def test_invalid_pcm_and_segment_return_fixed_boundary_codes(
    reference_sound_workspace: ReferenceSoundWorkspace,
) -> None:
    from cockpit.conftest import make_reference_pcm

    with pytest.raises(BoundaryError) as refused:
        reference_sound_workspace.import_reference(b"not a private WAV", "Reference")
    assert refused.value.context["error_code"] == "audio_invalid"
    imported = reference_sound_workspace.import_reference(make_reference_pcm(), "Reference")
    with pytest.raises(BoundaryError) as refused:
        reference_sound_workspace.select_segment(imported["session_id"], 0, 1)
    assert refused.value.context["error_code"] == "segment_invalid"
