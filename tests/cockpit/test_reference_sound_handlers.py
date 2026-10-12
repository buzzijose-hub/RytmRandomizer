"""Actual authenticated reference-sound journey and owned cancellation fence."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from threading import Event

import pytest
from cockpit.conftest import (
    TEST_WS_TOKEN,
    collect_initial_events,
    complete_handshake,
    make_reference_sound_session,
    make_reference_pcm,
    send_cmd,
)
from fastapi.testclient import TestClient

from rytm_randomizer.cockpit.export.reference_sound_session import ReferenceSoundWorkspace
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.reference_sound_handlers import cancel_reference_sound
from rytm_randomizer.cockpit.ws.server import create_app
from rytm_randomizer.style_analysis.extractor import AudioFeatureAnalysis

pytestmark = pytest.mark.fast


_session = make_reference_sound_session


def test_actual_ws_upload_scope_generation_favorite_playback_export_and_restart(
    tmp_path: Path,
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
    offline_hardware_denied: None,
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
