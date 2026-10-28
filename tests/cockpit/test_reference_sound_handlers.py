"""Actual authenticated reference-sound journey and owned cancellation fence."""

from __future__ import annotations

import asyncio
import base64
import os
from pathlib import Path
from threading import Event

import pytest
from cockpit.conftest import (
    TEST_WS_TOKEN,
    collect_initial_events,
    complete_handshake,
    make_reference_pcm,
    make_reference_sound_session,
    send_cmd,
)
from fastapi.testclient import TestClient

from rytm_randomizer.cockpit.data import CockpitSendPlan, SendPlanPacket
from rytm_randomizer.cockpit.export.reference_sound_session import ReferenceSoundWorkspace
from rytm_randomizer.cockpit.ws import reference_sound_handlers as sound_handlers
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.reference_sound_handlers import (
    _owned_operation,
    cancel_reference_sound,
)
from rytm_randomizer.cockpit.ws.server import create_app
from rytm_randomizer.observability.metrics import get_metrics
from rytm_randomizer.style_analysis.extractor import AudioFeatureAnalysis

pytestmark = pytest.mark.fast


_session = make_reference_sound_session


@pytest.mark.parametrize("action", ("controls", "reopen"))
@pytest.mark.parametrize(
    "identity",
    (
        "../PRIVATE_PATH",
        "/PRIVATE_PATH",
        "C:\\PRIVATE_PATH",
        "valid_id/../PRIVATE_PATH",
        "valid_id\\PRIVATE_PATH",
        "sound-" + "a" * 32 + "\n",
        None,
    ),
)
@pytest.mark.usefixtures("offline_hardware_denied")
def test_reference_sound_commands_refuse_path_ids_before_io_and_preserve_state(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    identity: object,
) -> None:
    session, _ = _session(tmp_path, reference_sound_workspace, reference_sound_source)
    retained = reference_sound_workspace.import_reference(make_reference_pcm(), "Saved reference")
    _, device, target, _ = reference_sound_source
    plan = CockpitSendPlan(
        plan_id="sendplan-abcdef0123456789",
        candidate_id="candidate-1",
        source_snapshot_id="snapshot-1",
        profile_id="profile-1",
        ready=True,
        readiness_reason="ready",
        safety_status="safe",
        packets=(SendPlanPacket(2, "flt", 1, 74, 64),),
        locked_pad_ids=frozenset(),
        blocked_reasons=(),
    )
    session.current_send_plan = plan
    assert session.library_store is not None
    roots = (session.library_store.library_dir, reference_sound_workspace.store.directory)
    before = {path: path.read_bytes() for root in roots for path in root.iterdir()}
    command: dict[str, object] = {"type": "reference_sound", "action": action}
    if action == "controls":
        command.update(source_record_id=identity, device_id=device, target=target)
    else:
        command["session_id"] = identity

    def forbidden_access(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("untrusted command identity reached the filesystem")

    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "stat", forbidden_access)
        scoped.setattr(Path, "iterdir", forbidden_access)
        scoped.setattr(Path, "mkdir", forbidden_access)
        scoped.setattr(os, "open", forbidden_access)
        scoped.setattr(os.path, "lexists", forbidden_access)
        ack = asyncio.run(
            handle_command({"request_id": "path-refusal", "command": command}, session)
        )
    assert ack["ok"] is False
    assert "PRIVATE_PATH" not in str(ack)
    assert session.current_send_plan is plan
    assert session.armed_apply is None and session.sound_cancel is None
    assert {path: path.read_bytes() for root in roots for path in root.iterdir()} == before
    assert reference_sound_workspace.reopen(str(retained["session_id"])) == retained


def test_executor_submission_failure_releases_the_fence_and_allows_fresh_work(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session, _ = _session(tmp_path, reference_sound_workspace, reference_sound_source)

    def failed_submit(*_args: object) -> asyncio.Future[int]:
        raise RuntimeError("test-owned executor is unavailable")

    async def exercise() -> None:
        loop = asyncio.get_running_loop()
        with monkeypatch.context() as patch:
            patch.setattr(loop, "run_in_executor", failed_submit)
            with pytest.raises(RuntimeError, match="executor is unavailable"):
                await _owned_operation(session, lambda _cancel: 1)
        assert session.sound_cancel is None
        assert await _owned_operation(session, lambda _cancel: 2) == 2

    asyncio.run(exercise())


def test_action_group_boundaries_refuse_foreign_actions_without_touching_retained_state(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    session, _ = _session(tmp_path, reference_sound_workspace, reference_sound_source)
    base = reference_sound_workspace.import_reference(make_reference_pcm(), "Action group fixture")
    command = {"action": "foreign", "session_id": base["session_id"]}
    before = {
        item.name: item.read_bytes()
        for item in reference_sound_workspace.store.directory.iterdir()
        if item.is_file()
    }
    for handler in (
        sound_handlers._sound_upload,
        sound_handlers._sound_inputs,
        sound_handlers._sound_retention,
    ):
        with pytest.raises(ValueError, match="action is not supported"):
            handler(command, session)
    with pytest.raises(ValueError, match="analysis action is not supported"):
        asyncio.run(sound_handlers._sound_analysis_operation(command, session))
    assert {
        item.name: item.read_bytes()
        for item in reference_sound_workspace.store.directory.iterdir()
        if item.is_file()
    } == before


def test_actual_websocket_disconnect_cancels_and_drains_the_owned_audio_worker(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    from rytm_randomizer.observability.errors import BoundaryError

    session, source_id = _session(tmp_path, reference_sound_workspace, reference_sound_source)
    base = reference_sound_workspace.import_reference(make_reference_pcm(), "Disconnect fixture")
    entered, finished = Event(), Event()

    def delayed(_path: Path, cancel: Event) -> AudioFeatureAnalysis:
        entered.set()
        try:
            assert cancel.wait(3), "Disconnect must cancel this worker"
            raise BoundaryError("test-owned child stopped", context={"error_code": "interrupted"})
        finally:
            finished.set()

    reference_sound_workspace.analyzer = delayed
    cleanup_errors = get_metrics().errors_by_kind["reference_sound.cancel_cleanup_failed"]
    _, device, target, parameters = reference_sound_source
    before = {
        item.name: item.read_bytes()
        for item in reference_sound_workspace.store.directory.iterdir()
        if item.is_file()
    }
    with TestClient(create_app(session, token=TEST_WS_TOKEN)) as client:
        with client.websocket_connect("/ws", subprotocols=["rytm-rand-cockpit-v1"]) as ws:
            complete_handshake(ws)
            collect_initial_events(ws)
            ws.send_json(
                {
                    "request_id": "disconnect-analysis",
                    "command": {
                        "type": "reference_sound",
                        "action": "generate",
                        "session_id": base["session_id"],
                        "source_record_id": source_id,
                        "device_id": device,
                        "target": target,
                        "parameters": list(parameters),
                        "locks": [],
                        "strength": 0.1,
                    },
                }
            )
            assert entered.wait(2)
            assert session.sound_cancel is not None
        assert finished.wait(2)
    assert session.sound_cancel is None
    assert get_metrics().errors_by_kind["reference_sound.cancel_cleanup_failed"] == cleanup_errors
    assert {
        item.name: item.read_bytes()
        for item in reference_sound_workspace.store.directory.iterdir()
        if item.is_file()
    } == before


@pytest.mark.parametrize("worker_fails", [False, True])
def test_repeated_task_cancellation_keeps_worker_fence_until_terminal_result(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    worker_fails: bool,
) -> None:
    session, _ = _session(tmp_path, reference_sound_workspace, reference_sound_source)
    entered, release = Event(), Event()

    def delayed(cancel: Event) -> int:
        entered.set()
        assert release.wait(5)
        assert cancel.is_set()
        if worker_fails:
            raise RuntimeError("test-owned worker cleanup failed")
        return 1

    async def exercise() -> None:
        pending = asyncio.create_task(_owned_operation(session, delayed))
        assert await asyncio.to_thread(entered.wait, 2)
        cancel = session.sound_cancel
        pending.cancel()
        await asyncio.sleep(0)
        pending.cancel()
        await asyncio.sleep(0)
        assert session.sound_cancel is cancel and cancel is not None and cancel.is_set()
        assert not pending.done()
        with pytest.raises(ValueError, match="Another audio operation"):
            await _owned_operation(session, lambda _cancel: 2)
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await pending
        assert session.sound_cancel is None
        assert await _owned_operation(session, lambda _cancel: 2) == 2

    try:
        asyncio.run(exercise())
    finally:
        release.set()


@pytest.mark.parametrize("child_signal", ["KeyboardInterrupt", "SystemExit"])
def test_child_interrupt_is_categorical_and_parent_can_continue(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    child_signal: str,
) -> None:
    from rytm_randomizer.observability.errors import BoundaryError
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    session, _ = _session(tmp_path, reference_sound_workspace, reference_sound_source)

    def interrupted(_cancel: Event) -> int:
        inference._raise_native_analysis_failure(
            inference._NativeAnalysisFailure(
                error_code="interrupted",
                error_type=child_signal,
                message="private worker context",
                fingerprint="a4.audio_patch.worker_interrupted",
            )
        )
        raise AssertionError("Child interruption must refuse the operation")

    async def exercise() -> None:
        with pytest.raises(BoundaryError) as failure:
            await _owned_operation(session, interrupted)
        assert failure.value.context["error_code"] == "interrupted"
        assert session.sound_cancel is None
        assert await _owned_operation(session, lambda _cancel: 42) == 42

    asyncio.run(exercise())


@pytest.mark.parametrize("action", ["reopen", "segment", "select"])
def test_failed_reference_change_preserves_existing_plan_and_success_clears_ui_confirmation(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    action: str,
) -> None:
    session, _ = _session(tmp_path, reference_sound_workspace, reference_sound_source)
    plan = CockpitSendPlan(
        plan_id="sendplan-abcdef0123456789",
        candidate_id="candidate-1",
        source_snapshot_id="snapshot-1",
        profile_id="profile-1",
        ready=True,
        readiness_reason="ready",
        safety_status="safe",
        packets=(SendPlanPacket(2, "filter_freq", 1, 74, 64),),
        locked_pad_ids=frozenset(),
        blocked_reasons=(),
    )
    session.current_send_plan = plan
    request = {
        "request_id": "invalid",
        "command": {
            "type": "reference_sound",
            "action": action,
            "session_id": "sound-" + "f" * 32,
            "start_frame": 0,
            "frame_count": 800,
            "candidate_id": "missing",
        },
    }
    result = asyncio.run(handle_command(request, session))
    assert not result["ok"] and session.current_send_plan is plan
    imported = reference_sound_workspace.import_reference(make_reference_pcm(), "Reference")
    result = asyncio.run(
        handle_command(
            {
                "request_id": "valid",
                "command": {
                    "type": "reference_sound",
                    "action": "reopen",
                    "session_id": imported["session_id"],
                },
            },
            session,
        )
    )
    assert result["ok"] and session.current_send_plan is None
    assert session.pending_events == [{"type": "send_plan_changed", "send_plan": None}]


@pytest.mark.usefixtures("offline_hardware_denied")
def test_actual_ws_upload_scope_generation_favorite_playback_export_and_restart(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    session, source_id = _session(tmp_path, reference_sound_workspace, reference_sound_source)
    _, device, target, parameters = reference_sound_source
    app = create_app(session, token=TEST_WS_TOKEN)
    audio = make_reference_pcm()
    with (
        TestClient(app) as client,
        client.websocket_connect("/ws", subprotocols=["rytm-rand-cockpit-v1"]) as ws,
    ):
        complete_handshake(ws, TEST_WS_TOKEN)
        collect_initial_events(ws)

        def command(action: str, **body: object) -> dict:
            ack = send_cmd(ws, "reference_sound", action=action, **body)
            assert ack["ok"], ack
            return ack["reference_sound"]

        upload = command("upload_begin", size=len(audio))
        command(
            "upload_chunk",
            upload_id=upload["upload_id"],
            offset=0,
            chunk=base64.b64encode(audio).decode(),
        )
        imported = command(
            "upload_finish", upload_id=upload["upload_id"], title="Fixture reference"
        )["session"]
        controls = command("controls", source_record_id=source_id, device_id=device, target=target)[
            "controls"
        ]
        assert any(item["parameter"] == parameters[0] and item["mutable"] for item in controls)
        generated = command(
            "generate",
            session_id=imported["session_id"],
            source_record_id=source_id,
            device_id=device,
            target=target,
            parameters=list(parameters),
            locks=[parameters[0]],
            strength=0.1,
        )["session"]
        selected = generated["candidates"][0]
        assert parameters[0] not in {item["parameter"] for item in selected["changes"]}
        retained = command(
            "favorite",
            session_id=generated["session_id"],
            candidate_id=selected["candidate_id"],
            favorite=True,
        )["session"]
        assert retained["favorites"] == [selected["candidate_id"]]
        playback = command("read_audio", session_id=generated["session_id"], offset=0)
        assert base64.b64decode(playback["audio_chunk"]) == audio
        exported = command(
            "export",
            session_id=generated["session_id"],
            candidate_id=selected["candidate_id"],
            destination_slot=19,
        )
        assert base64.b64decode(exported["sysex_base64"]) == reference_sound_workspace.export_patch(
            generated["session_id"], selected["candidate_id"], 19
        )
        assert exported["destination_slot"] == 19
        assert session.armed_apply is None and session.current_send_plan is None
    restarted, _ = _session(
        tmp_path / "restart",
        ReferenceSoundWorkspace(
            reference_sound_workspace.store, analyzer=reference_sound_workspace.analyzer
        ),
        reference_sound_source,
    )
    ack = asyncio.run(
        handle_command(
            {
                "request_id": "restart",
                "command": {
                    "type": "reference_sound",
                    "action": "reopen",
                    "session_id": generated["session_id"],
                },
            },
            restarted,
        )
    )
    assert ack["ok"]
    assert ack["reference_sound"]["session"] == retained
    assert restarted.armed_apply is None and restarted.current_send_plan is None


def test_owned_analysis_cancellation_cannot_publish_late_result(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    session, source_id = _session(tmp_path, reference_sound_workspace, reference_sound_source)
    base = reference_sound_workspace.import_reference(make_reference_pcm(), "Reference")
    entered = Event()
    original = reference_sound_workspace.analyzer

    def delayed(path: Path, cancel: Event) -> AudioFeatureAnalysis:
        entered.set()
        assert cancel.wait(2), "test must cancel its owned worker"
        return original(path, cancel)

    reference_sound_workspace.analyzer = delayed
    before = {
        path.name: path.read_bytes() for path in reference_sound_workspace.store.directory.iterdir()
    }
    _, device, target, parameters = reference_sound_source

    async def exercise() -> None:
        pending = asyncio.create_task(
            handle_command(
                {
                    "request_id": "generation",
                    "command": {
                        "type": "reference_sound",
                        "action": "generate",
                        "session_id": base["session_id"],
                        "source_record_id": source_id,
                        "device_id": device,
                        "target": target,
                        "parameters": list(parameters),
                        "locks": [],
                        "strength": 0.1,
                    },
                },
                session,
            )
        )
        assert await asyncio.to_thread(entered.wait, 2)
        cancellation = await handle_command(
            {"request_id": "cancel", "command": {"type": "reference_sound", "action": "cancel"}},
            session,
        )
        assert cancellation["ok"]
        result = await pending
        assert not result["ok"] and "cancelled" in result["message"]

    asyncio.run(exercise())
    assert session.sound_cancel is None
    assert {
        path.name: path.read_bytes() for path in reference_sound_workspace.store.directory.iterdir()
    } == before


@pytest.mark.parametrize(
    "case", ["hardware-intent", "capture-active", "pad-locked", "foreign-source", "bad-base64"]
)
def test_refusals_are_server_enforced_and_do_not_create_candidates(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    case: str,
) -> None:
    session, source_id = _session(tmp_path, reference_sound_workspace, reference_sound_source)
    base = reference_sound_workspace.import_reference(make_reference_pcm(), "Reference")
    _, device, target, parameters = reference_sound_source
    command: dict[str, object] = {
        "type": "reference_sound",
        "action": "generate",
        "session_id": base["session_id"],
        "source_record_id": source_id,
        "device_id": device,
        "target": target,
        "parameters": list(parameters),
        "locks": [],
        "strength": 0.1,
    }
    if case == "hardware-intent":
        session.hardware_intent = True
    elif case == "capture-active":
        session.capture_cancel = Event()
    elif case == "pad-locked":
        session.pad_locks.add(target)
        session.a4_track_locks.add(target)
    elif case == "foreign-source":
        command["device_id"] = "not-the-selected-device"
    else:
        session.sound_upload_id = "test-upload"
        command = {
            "type": "reference_sound",
            "action": "upload_chunk",
            "upload_id": "test-upload",
            "offset": 0,
            "chunk": "not base64",
        }
    result = asyncio.run(handle_command({"request_id": "refuse", "command": command}, session))
    assert not result["ok"]
    assert len(reference_sound_workspace.store.catalog()) == 1
    assert reference_sound_workspace.store.load(str(base["session_id"]))["candidates"] == []
    cancel_reference_sound(session)
