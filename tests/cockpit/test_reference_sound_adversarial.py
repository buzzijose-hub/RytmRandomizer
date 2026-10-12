"""Adversarial offline evidence tests; synthetic measurements prove no physical match."""

from __future__ import annotations

import asyncio
import base64
import copy
import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from threading import Event
from typing import TypeAlias

import pytest
from cockpit.conftest import make_reference_pcm, make_reference_sound_session

from rytm_randomizer.cockpit.export import reference_sound_session as sound_service
from rytm_randomizer.cockpit.export import writer
from rytm_randomizer.cockpit.export.reference_sound_session import (
    PreparedReferenceSound,
    ReferenceSoundWorkspace,
)
from rytm_randomizer.cockpit.export.reference_sound_store import (
    REFERENCE_SOUND_SCHEMA,
    reference_sound_digest,
    reference_sound_json,
    sound_artifact_name,
)
from rytm_randomizer.cockpit.ws import reference_sound_handlers as sound_handlers
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.devices import SavedKitCaptureFrame
from rytm_randomizer.observability.errors import BoundaryError, DataError
from rytm_randomizer.snapshot.elektron_native_object import ElektronNativeObjectMessage
from rytm_randomizer.style_analysis.extractor import (
    AudioFeatureAnalysis,
    StyleAnalysisDependencyError,
)

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]
Source: TypeAlias = tuple[bytes, str, int, tuple[str, ...]]


def _files(directory: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


def _generated(workspace: ReferenceSoundWorkspace, source: Source) -> dict:
    base = workspace.import_reference(make_reference_pcm(frames=1600), "Synthetic reference")
    frame, device, target, parameters = source
    prepared = workspace.generate(
        base["session_id"],
        source_frame=frame,
        device_id=device,
        target=target,
        parameters=parameters,
        locks=(),
        strength=1.0,
        cancel=Event(),
    )
    return workspace.commit(prepared)


def _recorded(workspace: ReferenceSoundWorkspace, payload: dict) -> dict:
    analyze = workspace.analyzer

    def measured(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        analysis = analyze(path, cancel)
        return replace(
            analysis, synthesis_features=replace(analysis.synthesis_features, brightness=0.25)
        )

    workspace.analyzer = measured
    candidate = workspace.candidate(payload["session_id"], payload["selected_candidate_id"])
    return workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate.candidate_id,
            candidate_sha256=reference_sound_digest(candidate.frame),
            recording=make_reference_pcm(frames=801),
            cancel=Event(),
        )
    )


async def _command(session: CockpitSession, action: str, **body: object) -> dict:
    result = await sound_handlers.handle_reference_sound({"action": action, **body}, session)
    assert result.ack is not None
    return result.ack


def _call(session: CockpitSession, action: str, **body: object) -> dict:
    return asyncio.run(_command(session, action, **body))


def test_refinement_respects_current_target_lock_and_late_lock_changes(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = reference_sound_workspace
    payload = _recorded(workspace, _generated(workspace, reference_sound_source))
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    target = reference_sound_source[2]
    locks = (
        session.pad_locks
        if reference_sound_source[1] == "analog_rytm_mk2"
        else session.a4_track_locks
    )
    before = _files(workspace.store.directory)
    locks.add(target)
    refused = _call(
        session,
        "refine",
        session_id=payload["session_id"],
        candidate_id=payload["selected_candidate_id"],
        correction_gain=0.5,
    )
    assert not refused["ok"] and "locked" in refused["message"]
    assert _files(workspace.store.directory) == before
    locks.clear()
    renderer = sound_service.render_refined_reference_sound_candidate

    def late_lock(*args, **kwargs):
        result = renderer(*args, **kwargs)
        locks.add(target)
        return result

    monkeypatch.setattr(sound_service, "render_refined_reference_sound_candidate", late_lock)
    refused = _call(
        session,
        "refine",
        session_id=payload["session_id"],
        candidate_id=payload["selected_candidate_id"],
        correction_gain=0.5,
    )
    assert not refused["ok"] and "changed during refinement" in refused["message"]
    assert _files(workspace.store.directory) == before
    _assert_passive(session, source_id, reference_sound_source)


def test_original_saved_slot_is_protected_before_transferable_export(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    source = ElektronNativeObjectMessage.from_bytes(reference_sound_source[0])
    before = _files(workspace.store.directory)
    with pytest.raises(ValueError, match="source slot is protected"):
        workspace.export_patch(payload["session_id"], payload["selected_candidate_id"], source.slot)
    assert _files(workspace.store.directory) == before
    safe = workspace.export_patch(
        payload["session_id"], payload["selected_candidate_id"], (source.slot + 1) % 128
    )
    candidate = workspace.candidate(payload["session_id"], payload["selected_candidate_id"])
    assert (
        ElektronNativeObjectMessage.from_bytes(safe).payload
        == ElektronNativeObjectMessage.from_bytes(candidate.frame).payload
    )


def _generation_request(base: dict, source_id: str, source: Source) -> dict:
    return {
        "session_id": base["session_id"],
        "source_record_id": source_id,
        "device_id": source[1],
        "target": source[2],
        "parameters": list(source[3]),
        "locks": [],
        "strength": 1.0,
    }


def _assert_passive(session: CockpitSession, source_id: str, source: Source) -> None:
    assert session.hardware_intent is False
    assert session.armed_apply is None
    assert session.sound_cancel is None
    assert session.library_store.read_source_frame(source_id) == source[0]


@pytest.mark.parametrize(
    "case",
    [
        "segment-start",
        "segment-metadata",
        "context-segment",
        "context-source",
        "context-strength",
        "analysis-digest",
        "candidate-value",
        "selected",
        "favorite",
        "record-parent",
        "record-patch",
        "record-physical",
        "record-digest",
        "record-metric",
        "record-score",
        "record-distance",
        "record-deltas",
        "records-shape",
        "records-limit",
        "refinement-parent",
        "refinement-recording",
        "refinement-features",
        "refinement-limit",
    ],
    ids=str,
)
def test_rehashed_manifest_drift_is_refused_without_repair_or_partial_writes(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    case: str,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    if case.startswith(("record", "refinement")):
        payload = _recorded(workspace, payload)
    if case.startswith("refinement"):
        payload = workspace.commit(
            workspace.refine(
                payload["session_id"],
                payload["selected_candidate_id"],
                correction_gain=0.5,
                cancel=Event(),
            )
        )
    forged = copy.deepcopy(payload)
    mutations: dict[str, Callable[[], None]] = {
        "segment-start": lambda: forged["segment"].__setitem__("start_frame", 1),
        "segment-metadata": lambda: forged["segment"].__setitem__("seconds", 7.5),
        "context-segment": lambda: forged["context"].__setitem__("segment_sha256", "0" * 64),
        "context-source": lambda: forged["context"].__setitem__("source_sha256", "0" * 64),
        "context-strength": lambda: forged["context"].__setitem__("strength", 0.25),
        "analysis-digest": lambda: forged["analysis"]["features"].__setitem__(
            "audio_sha256", "0" * 64
        ),
        "candidate-value": lambda: forged["candidates"][0].__setitem__("label", "Forged value"),
        "selected": lambda: forged.__setitem__("selected_candidate_id", "missing"),
        "favorite": lambda: forged.__setitem__("favorites", ["missing"]),
        "records-shape": lambda: forged.__setitem__("recordings", {}),
        "records-limit": lambda: forged.__setitem__("recordings", forged["recordings"] * 17),
        "record-digest": lambda: forged["recordings"][0]["features"]["features"].__setitem__(
            "audio_sha256", "0" * 64
        ),
        "refinement-parent": lambda: forged["refinements"][0].__setitem__("parent_id", "missing"),
        "refinement-recording": lambda: forged["refinements"][0].__setitem__(
            "recording_sha256", "0" * 64
        ),
        "refinement-features": lambda: forged["refinements"][0]["features"].__setitem__(
            "brightness", 0.01
        ),
        "refinement-limit": lambda: forged.__setitem__("refinements", forged["refinements"] * 4),
    }
    record_fields = {
        "record-parent": ("candidate_id", "missing"),
        "record-patch": ("candidate_sha256", "0" * 64),
        "record-physical": ("physical_validation", True),
        "record-metric": ("metric", "physical match probability"),
        "record-score": ("score", -1),
        "record-distance": ("distance", 0.99),
        "record-deltas": ("feature_deltas", []),
    }
    if case in record_fields:
        field, value = record_fields[case]
        forged["recordings"][0][field] = value
    else:
        mutations[case]()
    # A valid outer hash is not a substitute for canonical source/feedback replay.
    workspace.store.publish(forged, {})
    before = _files(workspace.store.directory)
    with pytest.raises((ValueError, DataError)):
        workspace.reopen(payload["session_id"])
    assert _files(workspace.store.directory) == before
    assert (
        workspace.store.read_artifact(reference_sound_digest(reference_sound_source[0]), "syx")
        == reference_sound_source[0]
    )


@pytest.mark.parametrize("artifact", ["original", "source", "candidate", "recording"])
def test_missing_original_or_derived_artifacts_preserve_manifests_and_favorites(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    artifact: str,
) -> None:
    workspace = reference_sound_workspace
    payload = _recorded(workspace, _generated(workspace, reference_sound_source))
    payload = workspace.select(
        payload["session_id"], payload["selected_candidate_id"], favorite=True
    )
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    identities = {
        "original": (payload["segment"]["original"]["sha256"], "wav"),
        "source": (payload["context"]["source_sha256"], "syx"),
        "candidate": (payload["candidates"][0]["frame_sha256"], "syx"),
        "recording": (payload["recordings"][0]["audio_sha256"], "wav"),
    }
    digest, extension = identities[artifact]
    (workspace.store.directory / sound_artifact_name(digest, extension)).unlink()
    before = _files(workspace.store.directory)
    result = _call(session, "reopen", session_id=payload["session_id"])
    assert result["ok"] is False and "missing" in result["message"]
    assert _files(workspace.store.directory) == before
    assert workspace.store.load(payload["session_id"])["favorites"] == payload["favorites"]
    _assert_passive(session, source_id, reference_sound_source)


@pytest.mark.parametrize(
    "schema", [True, "1", None, REFERENCE_SOUND_SCHEMA + 1], ids=["bool", "text", "null", "future"]
)
def test_invalid_and_future_schema_are_never_reset_by_handler(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    schema: object,
) -> None:
    workspace = reference_sound_workspace
    payload = workspace.import_reference(make_reference_pcm(), "Keep this reference")
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    forged = {**payload, "schema_version": schema}
    document = {**forged, "content_sha256": reference_sound_digest(reference_sound_json(forged))}
    (workspace.store.directory / f"{payload['session_id']}.sound.json").write_bytes(
        reference_sound_json(document)
    )
    before = _files(workspace.store.directory)
    result = _call(session, "reopen", session_id=payload["session_id"])
    assert result["ok"] is False
    assert _files(workspace.store.directory) == before
    _assert_passive(session, source_id, reference_sound_source)


@pytest.mark.parametrize(
    "favorite", [None, True, False, 1, "true"], ids=["omitted", "add", "remove", "integer", "text"]
)
def test_optional_favorite_is_strictly_boolean_and_rejections_preserve_selection(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    favorite: object,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    old_id, new_id = (item["candidate_id"] for item in payload["candidates"][:2])
    workspace.select(payload["session_id"], old_id, favorite=True)
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    before = _files(workspace.store.directory)
    result = _call(
        session,
        "favorite",
        session_id=payload["session_id"],
        candidate_id=new_id,
        favorite=favorite,
    )
    if favorite is None or isinstance(favorite, bool):
        assert result["ok"] is True
        saved = workspace.reopen(payload["session_id"])
        assert saved["selected_candidate_id"] == new_id
        assert set(saved["favorites"]) == ({old_id, new_id} if favorite is True else {old_id})
    else:
        assert result["ok"] is False
        assert _files(workspace.store.directory) == before
        with pytest.raises(ValueError, match="true or false"):
            workspace.select(payload["session_id"], new_id, favorite=favorite)
        assert _files(workspace.store.directory) == before
    _assert_passive(session, source_id, reference_sound_source)


@pytest.mark.parametrize(
    "slot",
    [None, True, -1, 128, 1.5, "19", 0, 127],
    ids=["missing", "bool", "negative", "overflow", "fraction", "text", "first", "last"],
)
def test_export_requires_explicit_bounded_destination_and_preserves_exact_payload(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    slot: object,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    before = _files(workspace.store.directory)
    request = {
        "session_id": payload["session_id"],
        "candidate_id": payload["selected_candidate_id"],
    }
    if slot is not None:
        request["destination_slot"] = slot
    result = _call(session, "export", **request)
    if type(slot) is int and 0 <= slot <= 127:
        assert result["ok"] is True
        frame = base64.b64decode(result["reference_sound"]["sysex_base64"], validate=True)
        exported = ElektronNativeObjectMessage.from_bytes(frame)
        candidate = workspace.candidate(payload["session_id"], payload["selected_candidate_id"])
        assert exported.payload == ElektronNativeObjectMessage.from_bytes(candidate.frame).payload
        assert result["reference_sound"]["destination_slot"] == slot
        assert result["reference_sound"]["sha256"] == reference_sound_digest(frame)
    else:
        assert result["ok"] is False
    assert _files(workspace.store.directory) == before
    _assert_passive(session, source_id, reference_sound_source)


@pytest.mark.parametrize(
    "case", ["locks", "targets", "parameters", "capture", "source-removed", "source-replaced"]
)
def test_generation_rechecks_operator_context_and_source_before_publication(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    case: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = reference_sound_workspace
    base = workspace.import_reference(make_reference_pcm(), "Keep previous reference")
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    before = _files(workspace.store.directory)
    analyze = workspace.analyzer
    replacement = (
        ElektronNativeObjectMessage.from_bytes(reference_sound_source[0]).with_slot(12).to_bytes()
    )

    def drift(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        if case == "locks":
            session.pad_locks.add(reference_sound_source[2])
        elif case == "targets":
            session.a4_track_targets.add(1)
        elif case == "parameters":
            session.rytm_parameters = frozenset()
        elif case == "capture":
            session.capture_generation += 1
        elif case == "source-removed":
            assert session.library_store.delete(source_id)
        else:
            monkeypatch.setattr(
                session.library_store, "read_source_frame", lambda record_id: replacement
            )
        return analyze(path, cancel)

    workspace.analyzer = drift
    result = _call(
        session, "generate", **_generation_request(base, source_id, reference_sound_source)
    )
    assert result["ok"] is False
    assert _files(workspace.store.directory) == before
    assert session.armed_apply is None and session.hardware_intent is False
    assert session.sound_cancel is None


def test_cancelled_owner_propagates_cancellation_and_waits_for_worker_cleanup(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
) -> None:
    workspace = reference_sound_workspace
    base = workspace.import_reference(make_reference_pcm(), "Keep reference")
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    before = _files(workspace.store.directory)
    entered, exited = Event(), Event()
    analyze = workspace.analyzer

    def cooperative(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        entered.set()
        assert cancel.wait(2), "owner must cancel its bounded worker"
        try:
            return analyze(path, cancel)
        finally:
            exited.set()

    workspace.analyzer = cooperative

    async def exercise() -> None:
        task = asyncio.create_task(
            _command(
                session, "generate", **_generation_request(base, source_id, reference_sound_source)
            )
        )
        assert await asyncio.to_thread(entered.wait, 2)
        try:
            for action in ("list", "upload_begin", "segment"):
                refusal = await _command(
                    session,
                    action,
                    session_id=base["session_id"],
                    size=44,
                    start_frame=0,
                    frame_count=1,
                )
                assert refusal["ok"] is False and "running" in refusal["message"]
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        finally:
            sound_handlers.cancel_reference_sound(session)
            await asyncio.gather(task, return_exceptions=True)
            assert exited.is_set()
            assert _files(workspace.store.directory) == before
            _assert_passive(session, source_id, reference_sound_source)

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "case",
    ["stale", "offset", "overrun", "empty", "oversize", "encoded-size", "wrong-type", "base64"],
    ids=str,
)
def test_bad_upload_chunk_preserves_ordered_prefix_and_can_be_cancelled(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    case: str,
) -> None:
    session, source_id = make_reference_sound_session(
        tmp_path, reference_sound_workspace, reference_sound_source
    )
    audio = make_reference_pcm()
    started = _call(session, "upload_begin", size=len(audio))["reference_sound"]
    upload_id = started["upload_id"]
    assert _call(
        session,
        "upload_chunk",
        upload_id=upload_id,
        offset=0,
        chunk=base64.b64encode(audio[:44]).decode(),
    )["ok"]
    request = {"upload_id": upload_id, "offset": 44, "chunk": base64.b64encode(audio[44:]).decode()}
    bad = {
        "stale": ("upload_id", "other"),
        "offset": ("offset", 0),
        "overrun": ("chunk", base64.b64encode(audio).decode()),
        "empty": ("chunk", "===="),
        "oversize": (
            "chunk",
            base64.b64encode(b"x" * (sound_handlers.REFERENCE_SOUND_CHUNK_BYTES + 1)).decode(),
        ),
        "encoded-size": ("chunk", "A" * (sound_handlers.REFERENCE_SOUND_CHUNK_BYTES * 4 // 3 + 5)),
        "wrong-type": ("chunk", 7),
        "base64": ("chunk", "!bad!"),
    }
    field, value = bad[case]
    request[field] = value
    refused = _call(session, "upload_chunk", **request)
    assert refused["ok"] is False
    assert session.sound_upload == audio[:44] and session.sound_upload_id == upload_id
    assert _call(session, "upload_finish", upload_id=upload_id, title="Incomplete")["ok"] is False
    assert _call(session, "upload_begin", size=len(audio))["ok"] is False
    assert _call(session, "cancel")["ok"] is True
    assert (
        session.sound_upload == b""
        and session.sound_upload_id is None
        and session.sound_upload_size == 0
    )
    assert not reference_sound_workspace.store.directory.exists()
    _assert_passive(session, source_id, reference_sound_source)


@pytest.mark.parametrize(
    "size", [43, 16 * 1024 * 1024 + 1, True, "44"], ids=["short", "large", "bool", "text"]
)
def test_upload_size_refusal_never_allocates_or_changes_prior_state(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    size: object,
) -> None:
    session, source_id = make_reference_sound_session(
        tmp_path, reference_sound_workspace, reference_sound_source
    )
    assert _call(session, "upload_begin", size=size)["ok"] is False
    assert (
        session.sound_upload_id is None
        and session.sound_upload_size == 0
        and session.sound_upload == b""
    )
    assert not reference_sound_workspace.store.directory.exists()
    _assert_passive(session, source_id, reference_sound_source)


def test_record_refine_original_and_recording_playback_use_retained_real_store(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    payload = workspace.select_segment(payload["session_id"], 800, 800)
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    generated = _call(
        session, "generate", **_generation_request(payload, source_id, reference_sound_source)
    )
    assert generated["ok"] is True
    payload = generated["reference_sound"]["session"]
    analyze = workspace.analyzer

    def measured(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        analysis = analyze(path, cancel)
        return replace(
            analysis, synthesis_features=replace(analysis.synthesis_features, brightness=0.25)
        )

    workspace.analyzer = measured
    recording = make_reference_pcm(frames=801)
    upload = _call(session, "upload_begin", size=len(recording))["reference_sound"]
    assert _call(
        session,
        "upload_chunk",
        upload_id=upload["upload_id"],
        offset=0,
        chunk=base64.b64encode(recording).decode(),
    )["ok"]
    candidate = workspace.candidate(payload["session_id"], payload["selected_candidate_id"])
    recorded = _call(
        session,
        "record",
        session_id=payload["session_id"],
        candidate_id=candidate.candidate_id,
        candidate_sha256=reference_sound_digest(candidate.frame),
        upload_id=upload["upload_id"],
    )
    assert recorded["ok"] is True
    payload = recorded["reference_sound"]["session"]
    assert payload["recordings"][0]["physical_validation"] is False
    assert session.sound_upload_id is None
    original = _call(
        session, "read_audio", session_id=payload["session_id"], audio_kind="original", offset=0
    )
    assert base64.b64decode(original["reference_sound"]["audio_chunk"]) == make_reference_pcm(
        frames=1600
    )
    heard = _call(
        session,
        "read_audio",
        session_id=payload["session_id"],
        audio_kind="recording",
        recording_sha256=reference_sound_digest(recording),
        offset=44,
    )
    assert base64.b64decode(heard["reference_sound"]["audio_chunk"]) == recording[44:]
    for kind, digest, offset in (
        ("recording", "0" * 64, 0),
        ("unknown", "0" * 64, 0),
        ("original", "0" * 64, -1),
        ("original", "0" * 64, 3244),
    ):
        before = _files(workspace.store.directory)
        assert (
            _call(
                session,
                "read_audio",
                session_id=payload["session_id"],
                audio_kind=kind,
                recording_sha256=digest,
                offset=offset,
            )["ok"]
            is False
        )
        assert _files(workspace.store.directory) == before
    refined = _call(
        session,
        "refine",
        session_id=payload["session_id"],
        candidate_id=candidate.candidate_id,
        correction_gain=0.5,
    )
    assert refined["ok"] is True
    assert len(refined["reference_sound"]["session"]["refinements"]) == 1
    assert workspace.reopen(payload["session_id"]) == refined["reference_sound"]["session"]
    catalog = _call(session, "list")
    assert catalog["ok"] is True
    summaries = catalog["reference_sound"]["sessions"]
    summary = next(item for item in summaries if item["session_id"] == payload["session_id"])
    assert summary["candidate_count"] == 9 and summary["recording_count"] == 1
    assert set(summary) == {
        "session_id",
        "title",
        "segment",
        "context",
        "favorites",
        "candidate_count",
        "recording_count",
    }
    _assert_passive(session, source_id, reference_sound_source)


@pytest.mark.parametrize(
    "failure",
    [
        "dependency",
        "dependency-code",
        "crash",
        "timeout",
        "cancelled",
        "interrupted",
        "missing",
        "missing-code",
        "disk",
        "corrupt",
        "bad-type",
        "bad-key",
    ],
    ids=str,
)
def test_worker_failures_have_specific_private_path_free_errors_and_no_publication(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    failure: str,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    workspace = reference_sound_workspace
    base = workspace.import_reference(make_reference_pcm(), "Private recording")
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    before = _files(workspace.store.directory)
    private = str(tmp_path / "private-client" / "secret-song.wav")
    errors = {
        "dependency": StyleAnalysisDependencyError(private),
        "dependency-code": BoundaryError(private, context={"error_code": "dependency_missing"}),
        "crash": RuntimeError(private),
        "timeout": BoundaryError(private, context={"error_code": "inference_failed"}),
        "cancelled": BoundaryError(private, context={"error_code": "interrupted"}),
        "interrupted": InterruptedError(private),
        "missing": FileNotFoundError(private),
        "missing-code": DataError(private, context={"category": "missing"}),
        "disk": PermissionError(private),
        "corrupt": DataError(private, context={"category": "hash"}),
        "bad-type": TypeError(private),
        "bad-key": KeyError(private),
    }

    def failing(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        raise errors[failure]

    workspace.analyzer = failing
    monkeypatch.setattr(sound_handlers._logger, "handlers", [caplog.handler])
    result = _call(
        session, "generate", **_generation_request(base, source_id, reference_sound_source)
    )
    fragments = {
        "dependency": "runtime is missing",
        "dependency-code": "runtime is missing",
        "crash": "failed or timed out",
        "timeout": "failed or timed out",
        "cancelled": "cancelled",
        "interrupted": "cancelled",
        "missing": "artifact is missing",
        "missing-code": "artifact is missing",
        "disk": "disk space and permissions",
        "corrupt": "identity is invalid",
        "bad-type": "identity is invalid",
        "bad-key": "identity is invalid",
    }
    assert result["ok"] is False and fragments[failure] in result["message"]
    visible = json.dumps(result) + caplog.text
    assert (
        private not in visible and "secret-song" not in visible and "private-client" not in visible
    )
    assert _files(workspace.store.directory) == before
    _assert_passive(session, source_id, reference_sound_source)


def test_atomic_publication_failure_rolls_back_new_candidates_and_manifest(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = reference_sound_workspace
    base = workspace.import_reference(make_reference_pcm(), "Retained reference")
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    before = _files(workspace.store.directory)
    real_replace = writer.os.replace
    published = []

    def fail_manifest(src: str | Path, dest: str | Path) -> None:
        if Path(src).suffix == ".stage" and Path(dest).name.endswith(".sound.json"):
            assert published, "fault must happen after candidate bytes reached publication"
            raise PermissionError("private path must not escape publication")
        real_replace(src, dest)
        if Path(src).suffix == ".stage" and Path(dest).suffix == ".syx":
            published.append(Path(dest))

    monkeypatch.setattr(writer.os, "replace", fail_manifest)
    result = _call(
        session, "generate", **_generation_request(base, source_id, reference_sound_source)
    )
    assert result["ok"] is False and "disk space" in result["message"]
    assert published
    assert _files(workspace.store.directory) == before
    assert workspace.reopen(base["session_id"]) == base
    _assert_passive(session, source_id, reference_sound_source)
    monkeypatch.setattr(writer.os, "replace", real_replace)
    generated = _call(
        session, "generate", **_generation_request(base, source_id, reference_sound_source)
    )["reference_sound"]["session"]
    candidate = workspace.candidate(generated["session_id"], generated["selected_candidate_id"])
    compared = workspace.compare(
        generated["session_id"],
        candidate.candidate_id,
        candidate_sha256=reference_sound_digest(candidate.frame),
        recording=make_reference_pcm(frames=801),
        cancel=Event(),
    )
    before = _files(workspace.store.directory)
    monkeypatch.setattr(writer.os, "replace", fail_manifest)
    with pytest.raises(writer.WriteSetError):
        workspace.commit(compared)
    assert _files(workspace.store.directory) == before
    assert workspace.reopen(generated["session_id"]) == generated


def test_recording_and_refinement_limits_and_duplicate_refinement_preserve_retained_work(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
) -> None:
    workspace = reference_sound_workspace
    payload = _recorded(workspace, _generated(workspace, reference_sound_source))
    session_id, candidate_id = payload["session_id"], payload["selected_candidate_id"]
    candidate = workspace.candidate(session_id, candidate_id)
    refined = workspace.commit(
        workspace.refine(session_id, candidate_id, correction_gain=0.25, cancel=Event())
    )
    before = _files(workspace.store.directory)
    duplicate = workspace.refine(session_id, candidate_id, correction_gain=0.25, cancel=Event())
    assert duplicate.payload == refined and not duplicate.artifacts
    assert _files(workspace.store.directory) == before
    for gain in (0.5, 0.75):
        refined = workspace.commit(
            workspace.refine(session_id, candidate_id, correction_gain=gain, cancel=Event())
        )
    assert len(refined["refinements"]) == 3
    before = _files(workspace.store.directory)
    with pytest.raises(ValueError, match="Three refinement"):
        workspace.refine(session_id, candidate_id, correction_gain=1.0, cancel=Event())
    assert _files(workspace.store.directory) == before
    for frames in range(802, 817):
        payload = workspace.commit(
            workspace.compare(
                session_id,
                candidate_id,
                candidate_sha256=reference_sound_digest(candidate.frame),
                recording=make_reference_pcm(frames=frames),
                cancel=Event(),
            )
        )
    assert len(payload["recordings"]) == 16
    before = _files(workspace.store.directory)
    with pytest.raises(ValueError, match="Recording limit"):
        workspace.compare(
            session_id,
            candidate_id,
            candidate_sha256=reference_sound_digest(candidate.frame),
            recording=make_reference_pcm(frames=900),
            cancel=Event(),
        )
    assert _files(workspace.store.directory) == before


def test_zero_distance_feedback_is_noop_and_long_recording_is_refused(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    candidate = workspace.candidate(payload["session_id"], payload["selected_candidate_id"])
    before = _files(workspace.store.directory)
    with pytest.raises(ValueError, match="eight seconds"):
        workspace.compare(
            payload["session_id"],
            candidate.candidate_id,
            candidate_sha256=reference_sound_digest(candidate.frame),
            recording=make_reference_pcm(frames=64001),
            cancel=Event(),
        )
    assert _files(workspace.store.directory) == before
    measured = workspace.commit(
        workspace.compare(
            payload["session_id"],
            candidate.candidate_id,
            candidate_sha256=reference_sound_digest(candidate.frame),
            recording=make_reference_pcm(),
            cancel=Event(),
        )
    )
    assert measured["recordings"][0]["distance"] == 0
    before = _files(workspace.store.directory)
    refined = workspace.refine(
        payload["session_id"], candidate.candidate_id, correction_gain=0.5, cancel=Event()
    )
    assert refined.payload == measured and not refined.artifacts
    assert _files(workspace.store.directory) == before


def test_handler_validation_and_lazy_workspace_never_touch_hardware_or_private_storage(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session, source_id = make_reference_sound_session(
        tmp_path, reference_sound_workspace, reference_sound_source
    )
    session.reference_sounds = None
    monkeypatch.setattr(
        sound_handlers, "ReferenceSoundWorkspace", lambda: reference_sound_workspace
    )
    assert _call(session, "list")["reference_sound"]["sessions"] == []
    assert session.reference_sounds is reference_sound_workspace
    assert _call(session, "upload_finish", upload_id="stale", title="x")["ok"] is False
    assert _call(session, "not-a-command", session_id="sound-" + "0" * 32)["ok"] is False
    library = session.library_store
    session.library_store = None
    assert (
        _call(
            session,
            "controls",
            source_record_id=source_id,
            device_id=reference_sound_source[1],
            target=reference_sound_source[2],
        )["ok"]
        is False
    )
    session.library_store = library
    session.armed_apply = object()
    assert _call(session, "list")["ok"] is False
    session.armed_apply = None
    _assert_passive(session, source_id, reference_sound_source)


def test_retained_overlong_recording_is_refused_even_with_valid_hash_and_manifest(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
) -> None:
    workspace = reference_sound_workspace
    payload = _recorded(workspace, _generated(workspace, reference_sound_source))
    audio = make_reference_pcm(frames=64001)
    digest = reference_sound_digest(audio)
    payload["recordings"][0]["audio_sha256"] = digest
    payload["recordings"][0]["features"]["features"]["audio_sha256"] = digest
    workspace.store.publish(payload, {sound_artifact_name(digest, "wav"): audio})
    before = _files(workspace.store.directory)
    with pytest.raises(ValueError, match="bounded comparison"):
        workspace.reopen(payload["session_id"])
    assert _files(workspace.store.directory) == before


def test_workspace_rejects_storage_boundary_returning_another_canonical_candidate(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    candidate = workspace.candidate(payload["session_id"], payload["selected_candidate_id"])
    digest = reference_sound_digest(candidate.frame)
    real_read = workspace.store.read_artifact

    def stale_read(identity: str, extension: str) -> bytes:
        if identity == digest and extension == "syx":
            return reference_sound_source[0]
        return real_read(identity, extension)

    monkeypatch.setattr(workspace.store, "read_artifact", stale_read)
    before = _files(workspace.store.directory)
    with pytest.raises(ValueError, match="differs from canonical"):
        workspace.reopen(payload["session_id"])
    assert _files(workspace.store.directory) == before


@pytest.mark.parametrize("fault", ["payload", "destination", "roundtrip"])
def test_export_proves_codec_payload_destination_and_exact_roundtrip_before_returning_bytes(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    canonical = sound_service.resolve_saved_kit_capture_capability(reference_sound_source[1])

    class FaultyCodec:
        def decode_saved_kit_capture(self, frame: bytes) -> SavedKitCaptureFrame:
            decoded = canonical.capability.decode_saved_kit_capture(frame)
            return (
                replace(decoded, unpacked=decoded.unpacked + b"\0")
                if fault == "payload"
                else decoded
            )

        def encode_saved_kit_capture(self, decoded: SavedKitCaptureFrame) -> bytes:
            frame = canonical.capability.encode_saved_kit_capture(decoded)
            return ElektronNativeObjectMessage.from_bytes(frame).with_slot(21).to_bytes()

    monkeypatch.setattr(
        sound_service,
        "resolve_saved_kit_capture_capability",
        lambda device_id: replace(canonical, capability=FaultyCodec()),
    )
    if fault == "destination":
        encode = ElektronNativeObjectMessage.to_bytes

        def wrong_slot(message: ElektronNativeObjectMessage) -> bytes:
            return encode(message.with_slot(21) if message.slot == 20 else message)

        monkeypatch.setattr(ElektronNativeObjectMessage, "to_bytes", wrong_slot)
    before = _files(workspace.store.directory)
    with pytest.raises(ValueError, match="scratch-slot and payload"):
        workspace.export_patch(payload["session_id"], payload["selected_candidate_id"], 20)
    assert _files(workspace.store.directory) == before


def test_owned_operation_refuses_busy_owner_and_cancelled_late_result_without_publication(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    before = _files(workspace.store.directory)
    replacement = Event()

    def late(cancel: Event) -> dict:
        cancel.set()
        # An older completion must never clear a newer owner's cancellation fence.
        session.sound_cancel = replacement
        return payload

    async def exercise() -> None:
        session.sound_cancel = Event()
        with pytest.raises(ValueError, match="Another audio operation"):
            await sound_handlers._owned_operation(session, late)
        session.sound_cancel = None
        with pytest.raises(BoundaryError) as failure:
            await sound_handlers._owned_operation(session, late)
        assert failure.value.context["error_code"] == "interrupted"
        assert session.sound_cancel is replacement
        session.sound_cancel = None

    asyncio.run(exercise())
    assert _files(workspace.store.directory) == before
    _assert_passive(session, source_id, reference_sound_source)


def test_owned_cancel_waits_for_noncooperative_worker_and_propagates_cancellation(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    entered, released = Event(), Event()
    before = _files(workspace.store.directory)

    def late(session_id: str, *, cancel: Event, **arguments: object) -> PreparedReferenceSound:
        entered.set()
        assert released.wait(2), "test must release the noncooperative worker"
        assert cancel.is_set()
        return PreparedReferenceSound(payload, {})

    monkeypatch.setattr(workspace, "generate", late)

    async def exercise() -> None:
        task = asyncio.create_task(
            _command(
                session,
                "generate",
                **_generation_request(payload, source_id, reference_sound_source),
            )
        )
        assert await asyncio.to_thread(entered.wait, 2)
        task.cancel()
        assert session.sound_cancel is not None
        assert await asyncio.to_thread(session.sound_cancel.wait, 2)
        released.set()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(exercise())
    assert _files(workspace.store.directory) == before
    _assert_passive(session, source_id, reference_sound_source)


def test_default_analyzer_passes_exact_path_and_cancellation_to_isolated_runtime(
    reference_sound_workspace: ReferenceSoundWorkspace,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "synthetic.wav"
    path.write_bytes(make_reference_pcm())
    cancel = Event()
    expected = reference_sound_workspace.analyzer(path, cancel)
    seen = []

    def isolated(audio_path: Path, *, cancel: Event) -> AudioFeatureAnalysis:
        seen.append((audio_path, cancel))
        return expected

    monkeypatch.setattr(
        sound_service, "analyze_analog_four_patch_audio_analysis_isolated", isolated
    )
    assert sound_service.analyze_reference_sound(path, cancel) == expected
    assert seen == [(path, cancel)]


def test_complete_but_corrupt_audio_upload_preserves_prefix_and_existing_work(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
) -> None:
    workspace = reference_sound_workspace
    payload = workspace.import_reference(make_reference_pcm(), "Keep reference")
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    before = _files(workspace.store.directory)
    upload = _call(session, "upload_begin", size=44)["reference_sound"]
    corrupt = b"not a wave".ljust(44, b"\0")
    assert _call(
        session,
        "upload_chunk",
        upload_id=upload["upload_id"],
        offset=0,
        chunk=base64.b64encode(corrupt).decode(),
    )["ok"]
    assert (
        _call(session, "upload_finish", upload_id=upload["upload_id"], title="Bad WAV")["ok"]
        is False
    )
    assert session.sound_upload == corrupt and session.sound_upload_id == upload["upload_id"]
    assert _files(workspace.store.directory) == before
    assert workspace.reopen(payload["session_id"]) == payload
    _assert_passive(session, source_id, reference_sound_source)


@pytest.mark.parametrize("action", ["record", "refine"])
def test_worker_cannot_overwrite_newer_retained_favorite_before_publication(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    if action == "refine":
        payload = _recorded(workspace, payload)
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    candidate = workspace.candidate(payload["session_id"], payload["selected_candidate_id"])
    snapshots = []

    def concurrent_favorite() -> None:
        workspace.select(payload["session_id"], candidate.candidate_id, favorite=True)
        snapshots.append(_files(workspace.store.directory))

    if action == "record":
        analyze = workspace.analyzer

        def measured(path: Path, cancel: Event) -> AudioFeatureAnalysis:
            concurrent_favorite()
            return analyze(path, cancel)

        workspace.analyzer = measured
        audio = make_reference_pcm(frames=802)
        upload = _call(session, "upload_begin", size=len(audio))["reference_sound"]
        assert _call(
            session,
            "upload_chunk",
            upload_id=upload["upload_id"],
            offset=0,
            chunk=base64.b64encode(audio).decode(),
        )["ok"]
        arguments = {
            "upload_id": upload["upload_id"],
            "candidate_sha256": reference_sound_digest(candidate.frame),
        }
    else:
        render = sound_service.render_refined_reference_sound_candidate

        def rendered(*args, **kwargs):
            result = render(*args, **kwargs)
            concurrent_favorite()
            return result

        monkeypatch.setattr(sound_service, "render_refined_reference_sound_candidate", rendered)
        arguments = {"correction_gain": 0.5}
    result = _call(
        session,
        action,
        session_id=payload["session_id"],
        candidate_id=candidate.candidate_id,
        **arguments,
    )
    _assert_passive(session, source_id, reference_sound_source)
    assert snapshots
    checks = {
        "stale_result_refused": result["ok"] is False,
        "newer_manifest_preserved": _files(workspace.store.directory) == snapshots[-1],
        "newer_favorite_preserved": workspace.store.load(payload["session_id"])["favorites"]
        == [candidate.candidate_id],
    }
    assert all(checks.values()), checks


def test_refinement_rechecks_feedback_patch_when_candidate_lookup_drifts(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = reference_sound_workspace
    payload = _recorded(workspace, _generated(workspace, reference_sound_source))
    candidate_id = payload["selected_candidate_id"]
    alternative = workspace.candidate(
        payload["session_id"], payload["candidates"][-1]["candidate_id"]
    )
    assert reference_sound_digest(alternative.frame) != payload["recordings"][0]["candidate_sha256"]
    # A stale resolver still returns codec-valid bytes, but not this recording's patch.
    monkeypatch.setattr(workspace, "candidate", lambda session_id, requested_id: alternative)
    before = _files(workspace.store.directory)
    with pytest.raises(ValueError, match="different patch"):
        workspace.refine(payload["session_id"], candidate_id, correction_gain=0.5, cancel=Event())
    assert _files(workspace.store.directory) == before


def test_locked_selected_target_is_refused_before_analysis_or_publication(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
) -> None:
    workspace = reference_sound_workspace
    base = workspace.import_reference(make_reference_pcm(), "Keep reference")
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    session.pad_locks.add(reference_sound_source[2])
    session.a4_track_locks.add(reference_sound_source[2])
    before = _files(workspace.store.directory)
    result = _call(
        session, "generate", **_generation_request(base, source_id, reference_sound_source)
    )
    assert result["ok"] is False and "locked" in result["message"]
    assert _files(workspace.store.directory) == before
    _assert_passive(session, source_id, reference_sound_source)


def test_handler_segment_selection_revokes_derived_work_without_destroying_previous_favorite(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: Source,
    tmp_path: Path,
) -> None:
    workspace = reference_sound_workspace
    payload = _generated(workspace, reference_sound_source)
    saved = workspace.select(payload["session_id"], payload["selected_candidate_id"], favorite=True)
    session, source_id = make_reference_sound_session(tmp_path, workspace, reference_sound_source)
    result = _call(
        session, "segment", session_id=payload["session_id"], start_frame=800, frame_count=800
    )
    assert result["ok"] is True
    segment = result["reference_sound"]["session"]
    assert segment["session_id"] != payload["session_id"]
    assert segment["analysis"] is None and segment["context"] is None
    assert segment["candidates"] == segment["recordings"] == segment["refinements"] == []
    assert segment["favorites"] == [] and segment["selected_candidate_id"] is None
    assert workspace.reopen(payload["session_id"]) == saved
    before = _files(workspace.store.directory)
    refusal = _call(
        session, "segment", session_id=segment["session_id"], start_frame=True, frame_count=800
    )
    assert refusal["ok"] is False
    assert _files(workspace.store.directory) == before
    assert session.current_send_plan is None
    _assert_passive(session, source_id, reference_sound_source)
