"""Input waits cannot delay DISARM or resurrect revoked Studio state."""

from __future__ import annotations

import asyncio
import gc
import json
import logging
import weakref
from datetime import datetime, timezone
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest
from cockpit.conftest import FixedFrameCaptureProvider, _make_default_snapshot
from fastapi import WebSocket, WebSocketDisconnect

from conftest import elektron_syx_message, rytm_real_layout_kit_payload
from rytm_randomizer import mido_provider
from rytm_randomizer.cockpit.capture import KitCaptureResult, KitCaptureService
from rytm_randomizer.cockpit.capture import service as capture_service
from rytm_randomizer.cockpit.data import Snapshot
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.device.connection import ConnectionState
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import handlers, server
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.observability.errors import StateError
from rytm_randomizer.observability.metrics import MidiMetrics
from rytm_randomizer.real_midi_adapter import RealMidiPortError

pytestmark = pytest.mark.fast


class DelayedInput:
    """An owned fake input worker; every test releases or cancels it."""

    def __init__(self, *, cooperative: bool, fail_after_release: bool = False) -> None:
        self.cooperative = cooperative
        self.fail_after_release = fail_after_release
        self.entered, self.release, self.closed = Event(), Event(), Event()
        self.cancel: Event | None = None

    def list_input_names(self) -> tuple[str, ...]:
        return ("Test input",)

    def capture_sysex_messages(self, _port: str, *, timeout_seconds: float) -> tuple[bytes, ...]:
        self.entered.set()
        try:
            assert timeout_seconds > 0
            assert self.release.wait(2), "test must release its owned input worker"
            if self.fail_after_release:
                raise RuntimeError("input failed after owner disconnect")
            return (elektron_syx_message(rytm_real_layout_kit_payload()),)
        finally:
            self.closed.set()

    def capture_sysex_messages_cancellable(
        self, port: str, *, timeout_seconds: float, cancel_event: Event
    ) -> tuple[bytes, ...]:
        self.cancel = cancel_event
        if not self.cooperative:
            return self.capture_sysex_messages(port, timeout_seconds=timeout_seconds)
        self.entered.set()
        try:
            assert cancel_event.wait(2), "test must cancel its owned input worker"
            raise StateError("cancelled")
        finally:
            self.closed.set()


class InboundFrames:
    def __init__(self) -> None:
        self.frames: asyncio.Queue[str | None] = asyncio.Queue()

    async def receive_text(self) -> str:
        value = await self.frames.get()
        if value is None:
            raise WebSocketDisconnect()
        return value

    def command(self, request_id: str, command: dict[str, object]) -> None:
        self.frames.put_nowait(json.dumps({"request_id": request_id, "command": command}))


def session_with_input(tmp_path: Path, provider: DelayedInput) -> CockpitSession:
    initial = _make_default_snapshot()
    history = HistoryStore()
    history.initial(initial)
    return CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=history,
        device=MockDeviceAdapter(initial),
        kit_capture_service=KitCaptureService(provider),
    )


async def next_ack(queue: server.ConnectionQueue, request_id: str) -> dict[str, object]:
    for _ in range(20):
        item = await asyncio.wait_for(queue.get(), timeout=1)
        if item.frame.get("request_id") == request_id:
            return item.frame
    raise AssertionError("ack missing from bounded queue")


async def wait_for_capture_release(session: CockpitSession) -> None:
    async def released() -> None:
        while session.capture_cancel is not None:
            await asyncio.sleep(0)

    await asyncio.wait_for(released(), 1)


def test_disarm_on_same_reader_cancels_input_and_rejects_late_frame(tmp_path: Path) -> None:
    async def exercise() -> None:
        provider = DelayedInput(cooperative=False)
        session = session_with_input(tmp_path, provider)
        original = session.device.capture_snapshot()
        history = session.history_store.current
        inbound, outbound = InboundFrames(), server.ConnectionQueue()
        reader = asyncio.create_task(
            server._reader_loop(
                cast(WebSocket, inbound),
                session=session,
                queue=outbound,
                emitter=server._QueueEmitter(outbound),
                max_bytes=1024,
            )
        )
        try:
            inbound.command(
                "capture",
                {
                    "type": "capture_current_kit",
                    "device_id": "analog_rytm_mk2",
                    "input_port": "Test input",
                },
            )
            assert await asyncio.to_thread(provider.entered.wait, 1)
            inbound.command("scope", {"type": "set_depth", "depth": 0.7})
            assert (await next_ack(outbound, "scope"))["ok"] is False
            inbound.command("diagnostics", {"type": "diagnostics"})
            assert (await next_ack(outbound, "diagnostics"))["ok"] is True
            inbound.command("disarm", {"type": "disarm"})
            assert (await next_ack(outbound, "disarm"))["ok"] is True
            assert provider.cancel is not None and provider.cancel.is_set()
            assert not provider.closed.is_set()  # DISARM did not wait for the input thread.
            assert (await asyncio.wait_for(outbound.get(), 1)).frame["type"] == "session_status"
            assert (await asyncio.wait_for(outbound.get(), 1)).frame[
                "type"
            ] == "dual_machine_stage_changed"
            provider.release.set()
            ack = await next_ack(outbound, "capture")
            assert ack["ok"] is False and ack["message"] == "current-kit capture cancelled"
            assert session.device.capture_snapshot() == original
            assert session.history_store.current == history
            assert session.kit_captures == {} and session.capture_cancel is None
            assert outbound.size == 0 and session.pending_events == []
        finally:
            provider.release.set()
            inbound.frames.put_nowait(None)
            await asyncio.wait_for(reader, 1)

    asyncio.run(exercise())


def test_completed_captures_enqueue_ack_then_events_before_next_command(tmp_path: Path) -> None:
    async def exercise() -> None:
        provider = DelayedInput(cooperative=False)
        session = session_with_input(tmp_path, provider)
        session.preview_on = True
        session.active_profile = session.profile_registry.list_profiles()[0]
        inbound, outbound = InboundFrames(), server.ConnectionQueue()
        reader = asyncio.create_task(
            server._reader_loop(
                cast(WebSocket, inbound),
                session=session,
                queue=outbound,
                emitter=server._QueueEmitter(outbound),
                max_bytes=1024,
            )
        )
        try:
            for request_id in ("capture-1", "capture-2"):
                inbound.command(
                    request_id,
                    {
                        "type": "capture_current_kit",
                        "device_id": "analog_rytm_mk2",
                        "input_port": "Test input",
                    },
                )
                assert await asyncio.to_thread(provider.entered.wait, 1)
                provider.release.set()
                first = await asyncio.wait_for(outbound.get(), 1)
                assert first.frame["request_id"] == request_id and first.frame["ok"] is True

                # The next command can be read while its predecessor's events
                # are still queued. It must not overwrite or split those events.
                inbound.command("depth", {"type": "set_depth", "depth": 0.7})
                events = [
                    (await asyncio.wait_for(outbound.get(), 1)).frame["type"] for _ in range(5)
                ]
                assert events == [
                    "kit_captures_changed",
                    "snapshot_changed",
                    "history_updated",
                    "mutation_previewed",
                    "dual_machine_stage_changed",
                ]
                depth = await asyncio.wait_for(outbound.get(), 1)
                assert depth.frame["request_id"] == "depth" and depth.frame["ok"] is True
                assert (await asyncio.wait_for(outbound.get(), 1)).frame[
                    "type"
                ] == "mutation_previewed"
                assert (await asyncio.wait_for(outbound.get(), 1)).frame[
                    "type"
                ] == "dual_machine_stage_changed"
                assert outbound.size == 0 and session.pending_events == []
        finally:
            provider.release.set()
            inbound.frames.put_nowait(None)
            await asyncio.wait_for(reader, 1)

    asyncio.run(exercise())


def test_owner_disconnect_cancels_capture_even_with_sibling_reader(tmp_path: Path) -> None:
    async def exercise() -> None:
        provider = DelayedInput(cooperative=True)
        session = session_with_input(tmp_path, provider)
        original = session.device.capture_snapshot()
        sockets = [InboundFrames(), InboundFrames()]
        queues = [server.ConnectionQueue(), server.ConnectionQueue()]
        readers = [
            asyncio.create_task(
                server._reader_loop(
                    cast(WebSocket, socket),
                    session=session,
                    queue=queue,
                    emitter=server._QueueEmitter(queue),
                    max_bytes=1024,
                )
            )
            for socket, queue in zip(sockets, queues, strict=True)
        ]
        try:
            sockets[0].command(
                "capture",
                {
                    "type": "capture_current_kit",
                    "device_id": "analog_rytm_mk2",
                    "input_port": "Test input",
                },
            )
            assert await asyncio.to_thread(provider.entered.wait, 1)
            sockets[1].frames.put_nowait(None)
            assert await asyncio.wait_for(readers[1], 1) is False
            assert provider.cancel is not None and not provider.cancel.is_set()
            sockets[0].frames.put_nowait(None)
            assert await asyncio.wait_for(readers[0], 1) is False
            assert await asyncio.to_thread(provider.closed.wait, 1)
            await wait_for_capture_release(session)
            assert session.device.capture_snapshot() == original and session.kit_captures == {}
            assert session.capture_cancel is None
        finally:
            provider.release.set()
            for socket in sockets:
                socket.frames.put_nowait(None)
            await asyncio.gather(*readers)

    asyncio.run(exercise())


def test_noncooperative_owner_disconnect_stays_busy_until_release_then_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def exercise() -> None:
        provider = DelayedInput(cooperative=False)
        session = session_with_input(tmp_path, provider)
        original = session.device.capture_snapshot()
        history = session.history_store.current
        stage = session.stage_coordinator.state
        depth = session.depth
        cancelled_worker_finished = Event()
        capture = session.kit_capture_service.capture

        def receive(device_id: str, port: str, *, cancel_event: Event) -> KitCaptureResult:
            try:
                return capture(device_id, port, cancel_event=cancel_event)
            finally:
                if cancel_event.is_set():
                    cancelled_worker_finished.set()

        monkeypatch.setattr(session.kit_capture_service, "capture", receive)
        sockets = [InboundFrames(), InboundFrames()]
        queues = [server.ConnectionQueue(), server.ConnectionQueue()]
        readers = [
            asyncio.create_task(
                server._reader_loop(
                    cast(WebSocket, socket),
                    session=session,
                    queue=queue,
                    emitter=server._QueueEmitter(queue),
                    max_bytes=1024,
                )
            )
            for socket, queue in zip(sockets, queues, strict=True)
        ]
        command: dict[str, object] = {
            "type": "capture_current_kit",
            "device_id": "analog_rytm_mk2",
            "input_port": "Test input",
        }
        try:
            sockets[0].command("owner", command)
            assert await asyncio.to_thread(provider.entered.wait, 1)
            sockets[0].frames.put_nowait(None)
            assert await asyncio.wait_for(readers[0], 1) is False
            assert provider.cancel is not None and provider.cancel.is_set()
            assert session.capture_cancel is provider.cancel and not provider.closed.is_set()

            sockets[1].command("depth", {"type": "set_depth", "depth": 0.7})
            busy_depth = await next_ack(queues[1], "depth")
            assert busy_depth["ok"] is False and busy_depth["code"] == handlers.ERR_VALIDATION
            assert busy_depth["message"] == "current-kit capture is active; disarm to cancel it"

            sockets[1].command("busy", command)
            busy = await next_ack(queues[1], "busy")
            assert busy["ok"] is False and busy["code"] == handlers.ERR_VALIDATION
            assert busy["message"] == "another current-kit capture is active"
            assert session.capture_cancel is provider.cancel
            assert session.depth == depth
            assert session.device.capture_snapshot() == original and session.kit_captures == {}
            assert session.history_store.current == history
            assert session.stage_coordinator.state == stage
            assert session.pending_events == [] and queues[0].size == queues[1].size == 0
            assert not provider.closed.is_set()

            provider.release.set()
            assert await asyncio.to_thread(cancelled_worker_finished.wait, 1)
            await wait_for_capture_release(session)
            assert provider.closed.is_set()
            assert session.device.capture_snapshot() == original and session.kit_captures == {}
            assert session.history_store.current == history
            assert session.stage_coordinator.state == stage
            assert queues[0].size == queues[1].size == 0

            sockets[1].command("recovered", command)
            assert (await next_ack(queues[1], "recovered"))["ok"] is True
            assert session.kit_captures["analog_rytm_mk2"].frame_bytes > 0
            assert session.stage_coordinator.state.rytm.capture_state == "captured"
            assert session.capture_cancel is None and session.pending_events == []
            assert queues[0].size == 0
        finally:
            provider.release.set()
            for socket in sockets:
                socket.frames.put_nowait(None)
            await asyncio.gather(*readers)

    asyncio.run(exercise())


@pytest.mark.parametrize("replace_owner", [False, True])
def test_detached_failed_capture_consumes_exception_and_only_releases_its_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, replace_owner: bool
) -> None:
    async def exercise() -> None:
        provider = DelayedInput(cooperative=False, fail_after_release=True)
        session = session_with_input(tmp_path, provider)
        original = session.device.capture_snapshot()
        stage = session.stage_coordinator.state
        newer_owner = Event()
        loop = asyncio.get_running_loop()
        loop_errors: list[dict[str, object]] = []
        previous_handler = loop.get_exception_handler()
        loop.set_exception_handler(lambda _loop, context: loop_errors.append(context))
        shield = asyncio.shield
        owned_tasks: list[weakref.ReferenceType[asyncio.Task[KitCaptureResult]]] = []

        def track_input(task: asyncio.Task[KitCaptureResult]) -> asyncio.Future[KitCaptureResult]:
            owned_tasks.append(weakref.ref(task))
            return shield(task)

        monkeypatch.setattr(handlers.asyncio, "shield", track_input)
        capture = asyncio.create_task(
            handlers.handle_command(
                {
                    "request_id": "cancelled",
                    "command": {
                        "type": "capture_current_kit",
                        "device_id": "analog_rytm_mk2",
                        "input_port": "Test input",
                    },
                },
                session,
            )
        )
        try:
            assert await asyncio.to_thread(provider.entered.wait, 1)
            capture.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(capture, 1)
            assert provider.cancel is not None and provider.cancel.is_set()
            assert session.capture_cancel is provider.cancel and not provider.closed.is_set()
            if replace_owner:
                session.capture_cancel = newer_owner
            provider.release.set()
            assert await asyncio.to_thread(provider.closed.wait, 1)

            async def collected() -> None:
                while owned_tasks[0]() is not None:
                    await asyncio.sleep(0)
                    gc.collect()

            await asyncio.wait_for(collected(), 1)
            assert loop_errors == []
            assert session.capture_cancel is (newer_owner if replace_owner else None)
            assert not newer_owner.is_set()
            assert session.device.capture_snapshot() == original and session.kit_captures == {}
            assert session.stage_coordinator.state == stage and session.pending_events == []
        finally:
            provider.release.set()
            await asyncio.gather(capture, return_exceptions=True)
            loop.set_exception_handler(previous_handler)

    asyncio.run(exercise())


def test_size_rejection_on_capture_owner_cancels_input(tmp_path: Path) -> None:
    async def exercise() -> None:
        provider = DelayedInput(cooperative=True)
        session = session_with_input(tmp_path, provider)
        inbound, outbound = InboundFrames(), server.ConnectionQueue()
        reader = asyncio.create_task(
            server._reader_loop(
                cast(WebSocket, inbound),
                session=session,
                queue=outbound,
                emitter=server._QueueEmitter(outbound),
                max_bytes=1024,
            )
        )
        try:
            inbound.command(
                "capture",
                {
                    "type": "capture_current_kit",
                    "device_id": "analog_rytm_mk2",
                    "input_port": "Test input",
                },
            )
            assert await asyncio.to_thread(provider.entered.wait, 1)
            inbound.frames.put_nowait("x" * 1025)
            assert await asyncio.wait_for(reader, 1) is True
            item = await asyncio.wait_for(outbound.get(), 1)
            assert item.frame == {"ok": False, "code": server.MESSAGE_TOO_LARGE_CODE}
            assert item.close_code == server.CLOSE_CODE_MESSAGE_TOO_BIG
            assert await asyncio.to_thread(provider.closed.wait, 1)
            await wait_for_capture_release(session)
            assert session.kit_captures == {} and session.capture_cancel is None
        finally:
            provider.release.set()
            inbound.frames.put_nowait(None)
            await asyncio.gather(reader)

    asyncio.run(exercise())


@pytest.mark.parametrize("command", [{"type": "set_depth", "depth": 0.7}, {"type": ["private"]}])
def test_capture_busy_refusals_record_bounded_command_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command: dict[str, object]
) -> None:
    session = session_with_input(tmp_path, DelayedInput(cooperative=True))
    session.capture_cancel = Event()
    metrics = MidiMetrics()
    monkeypatch.setattr(handlers, "get_metrics", lambda: metrics)
    result = asyncio.run(
        handlers.handle_command({"request_id": "busy-request", "command": command}, session)
    )
    assert result["ok"] is False and result["code"] == handlers.ERR_VALIDATION
    label = "set_depth" if command["type"] == "set_depth" else "<unknown>"
    assert metrics.ws_command_count == {label: 1}
    assert metrics.ws_command_errors_by_code == {handlers.ERR_VALIDATION: 1}
    assert set(metrics.ws_command_duration_ms_total) == {label}


def test_second_capture_keeps_existing_owner_and_never_calls_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ws_handler_caplog: pytest.LogCaptureFixture
) -> None:
    ws_handler_caplog.set_level(logging.INFO, logger="rytm_randomizer.cockpit.ws.handlers")
    session = session_with_input(tmp_path, DelayedInput(cooperative=True))
    owner = Event()
    session.capture_cancel = owner
    receive = Mock(side_effect=AssertionError("duplicate input capture started"))
    monkeypatch.setattr(session.kit_capture_service, "capture", receive)
    ack = asyncio.run(
        handlers.handle_command(
            {
                "request_id": "duplicate",
                "command": {
                    "type": "capture_current_kit",
                    "device_id": "analog_rytm_mk2",
                    "input_port": "Test input",
                },
            },
            session,
        )
    )
    assert ack["ok"] is False and ack["message"] == "another current-kit capture is active"
    assert session.capture_cancel is owner and not owner.is_set()
    receive.assert_not_called()
    refused = next(
        record
        for record in ws_handler_caplog.records
        if record.msg == "cockpit_kit_capture_refused"
    )
    assert refused.device_id == "analog_rytm_mk2" and refused.reason == "capture_busy"
    assert refused.sent_midi is False and "Test input" not in repr(refused.__dict__)


@pytest.mark.parametrize("context_change", ["generation", "owner", "both"])
def test_completed_capture_cannot_publish_across_a_changed_generation_or_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, context_change: str
) -> None:
    session = session_with_input(tmp_path, DelayedInput(cooperative=False))
    session.kit_capture_service = KitCaptureService(
        FixedFrameCaptureProvider(elektron_syx_message(rytm_real_layout_kit_payload()))
    )
    original = session.device.capture_snapshot()
    stage = session.stage_coordinator.state
    receive = session.kit_capture_service.capture
    newer_owner = Event()

    def changed_context(device_id: str, port: str, *, cancel_event: Event) -> KitCaptureResult:
        result = receive(device_id, port, cancel_event=cancel_event)
        if context_change != "owner":
            session.capture_generation += 1
        if context_change != "generation":
            session.capture_cancel = newer_owner
        return result

    monkeypatch.setattr(session.kit_capture_service, "capture", changed_context)
    ack = asyncio.run(
        handlers.handle_command(
            {
                "request_id": "late-result",
                "command": {
                    "type": "capture_current_kit",
                    "device_id": "analog_rytm_mk2",
                    "input_port": "Mock input",
                },
            },
            session,
        )
    )
    assert ack["ok"] is False and ack["message"] == "current-kit capture cancelled"
    assert session.device.capture_snapshot() == original and session.kit_captures == {}
    assert session.stage_coordinator.state == stage and session.pending_events == []
    assert session.capture_cancel is (None if context_change == "generation" else newer_owner)
    assert not newer_owner.is_set()


def test_successful_capture_keeps_reservation_through_snapshot_adoption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = session_with_input(tmp_path, DelayedInput(cooperative=False))
    session.kit_capture_service = KitCaptureService(
        FixedFrameCaptureProvider(elektron_syx_message(rytm_real_layout_kit_payload()))
    )
    adopt = session.device.adopt_snapshot
    owners: list[Event] = []

    def adopt_owned(snapshot: Snapshot) -> None:
        owner = session.capture_cancel
        assert owner is not None and not owner.is_set()
        owners.append(owner)
        adopt(snapshot)

    monkeypatch.setattr(session.device, "adopt_snapshot", adopt_owned)
    ack = asyncio.run(
        handlers.handle_command(
            {
                "request_id": "adopt",
                "command": {
                    "type": "capture_current_kit",
                    "device_id": "analog_rytm_mk2",
                    "input_port": "Mock input",
                },
            },
            session,
        )
    )
    assert ack["ok"] is True and len(owners) == 1
    assert session.capture_cancel is None


def test_cancelled_input_task_cleanup_does_not_raise_in_completion_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ws_handler_caplog: pytest.LogCaptureFixture
) -> None:
    ws_handler_caplog.set_level(logging.INFO, logger="rytm_randomizer.cockpit.ws.handlers")
    metrics = MidiMetrics()
    monkeypatch.setattr(handlers, "get_metrics", lambda: metrics)

    async def exercise() -> None:
        session = session_with_input(tmp_path, DelayedInput(cooperative=False))
        loop = asyncio.get_running_loop()
        loop_errors: list[dict[str, object]] = []
        previous_handler = loop.get_exception_handler()
        loop.set_exception_handler(lambda _loop, context: loop_errors.append(context))

        async def cancelled_input(*_args: object, **_kwargs: object) -> KitCaptureResult:
            raise asyncio.CancelledError

        monkeypatch.setattr(handlers.asyncio, "to_thread", cancelled_input)
        try:
            with pytest.raises(asyncio.CancelledError):
                await handlers.handle_command(
                    {
                        "request_id": "cancelled-input",
                        "command": {
                            "type": "capture_current_kit",
                            "device_id": "analog_rytm_mk2",
                            "input_port": "Test input",
                        },
                    },
                    session,
                )
            await asyncio.sleep(0)
            assert session.capture_cancel is None and session.kit_captures == {}
            assert session.pending_events == [] and loop_errors == []
        finally:
            loop.set_exception_handler(previous_handler)

    asyncio.run(exercise())
    assert metrics.ws_command_count == {"capture_current_kit": 1}
    assert metrics.ws_command_errors_by_code == {handlers.ERR_VALIDATION: 1}
    assert set(metrics.ws_command_duration_ms_total) == {"capture_current_kit"}
    assert metrics.errors_by_kind == {"cockpit.capture.cancelled": 1}
    cancelled = next(
        record
        for record in ws_handler_caplog.records
        if record.msg == "cockpit_kit_capture_cancelled"
    )
    assert cancelled.device_id == "analog_rytm_mk2" and cancelled.sent_midi is False
    assert "Test input" not in repr(cancelled.__dict__)


def test_passive_watchdog_cancels_capture_without_replacing_snapshot(tmp_path: Path) -> None:
    async def exercise() -> None:
        provider = DelayedInput(cooperative=False)
        session = session_with_input(tmp_path, provider)
        original = session.device.capture_snapshot()
        stage = session.stage_coordinator.state
        capture = asyncio.create_task(
            handlers.handle_command(
                {
                    "request_id": "capture",
                    "command": {
                        "type": "capture_current_kit",
                        "device_id": "analog_rytm_mk2",
                        "input_port": "Test input",
                    },
                },
                session,
            )
        )
        try:
            assert await asyncio.to_thread(provider.entered.wait, 1)
            handlers.build_armed_watchdog(session)(
                ConnectionState(
                    phase="disconnected",
                    available_inputs=(),
                    available_outputs=(),
                    selected_input=None,
                    selected_output=None,
                    last_error_fingerprint=None,
                    changed_at=datetime.now(timezone.utc),
                )
            )
            provider.release.set()
            ack = await asyncio.wait_for(capture, 1)
            assert ack["ok"] is False and ack["message"] == "current-kit capture cancelled"
            assert session.device.capture_snapshot() == original and session.kit_captures == {}
            assert session.stage_coordinator.state == stage and session.pending_events == []
        finally:
            provider.release.set()
            await asyncio.gather(capture)

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "cancel_at", ["before_input", "receive_error", "after_receive", "after_decode"]
)
def test_service_cancellation_at_each_handoff_refuses_frame_and_releases_lock(
    monkeypatch: pytest.MonkeyPatch, cancel_at: str
) -> None:
    signal = Event()
    provider = FixedFrameCaptureProvider(elektron_syx_message(rytm_real_layout_kit_payload()))
    service = KitCaptureService(provider)
    original_receive = provider.capture_sysex_messages
    original_decode = capture_service._decode_capture_result

    def receive(port: str, *, timeout_seconds: float) -> tuple[bytes, ...]:
        frames = original_receive(port, timeout_seconds=timeout_seconds)
        if cancel_at == "receive_error":
            signal.set()
            raise RuntimeError("input closed during cancellation")
        if cancel_at == "after_receive":
            signal.set()
        return frames

    def decode(*args: object) -> KitCaptureResult:
        result = original_decode(*args)
        if cancel_at == "after_decode":
            signal.set()
        return result

    receive_spy, decode_spy = Mock(side_effect=receive), Mock(side_effect=decode)
    monkeypatch.setattr(provider, "capture_sysex_messages", receive_spy)
    monkeypatch.setattr(capture_service, "_decode_capture_result", decode_spy)
    if cancel_at == "before_input":
        signal.set()
    with pytest.raises(StateError, match="current-kit capture cancelled"):
        service.capture("analog_rytm_mk2", "Mock input", cancel_event=signal)
    assert receive_spy.call_count == (0 if cancel_at == "before_input" else 1)
    assert decode_spy.call_count == (1 if cancel_at == "after_decode" else 0)

    monkeypatch.setattr(provider, "capture_sysex_messages", original_receive)
    monkeypatch.setattr(capture_service, "_decode_capture_result", original_decode)
    signal.clear()
    assert service.capture("analog_rytm_mk2", "Mock input", cancel_event=signal).frame_bytes > 0


def test_cancellable_service_accepts_a_current_uncancelled_frame(tmp_path: Path) -> None:
    provider = DelayedInput(cooperative=False)
    provider.release.set()
    session = session_with_input(tmp_path, provider)
    signal = Event()

    result = session.kit_capture_service.capture(
        "analog_rytm_mk2", "Test input", cancel_event=signal
    )

    assert result.frame_bytes > 0 and provider.cancel is signal
    assert provider.closed.is_set() and not signal.is_set()


def test_cancelled_native_capture_never_imports_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    signal = Event()
    signal.set()
    monkeypatch.setattr(mido_provider, "_import_rtmidi", lambda: pytest.fail("backend imported"))
    with pytest.raises(RealMidiPortError, match="capture_cancelled"):
        mido_provider.MidoMidiPortProvider().capture_sysex_messages_cancellable(
            "Test input", timeout_seconds=120, cancel_event=signal
        )


@pytest.mark.parametrize("late_frame", [False, True])
def test_native_cancellation_discards_frame_and_closes_owned_input(
    monkeypatch: pytest.MonkeyPatch, late_frame: bool
) -> None:
    signal, entered = Event(), Event()
    port = Mock(spec=("get_ports", "ignore_types", "open_port", "get_message", "close_port"))
    port.get_ports.return_value = ("Test input",)

    def arrive() -> tuple[list[int], float] | None:
        entered.set()
        if late_frame:
            signal.set()
            return ([0xF0, 0x01, 0xF7], 0.0)
        return None

    port.get_message.side_effect = arrive
    factory = Mock(return_value=port)
    monkeypatch.setattr(mido_provider, "_import_rtmidi", lambda: SimpleNamespace(MidiIn=factory))

    async def exercise() -> None:
        capture = asyncio.create_task(
            asyncio.to_thread(
                mido_provider.MidoMidiPortProvider().capture_sysex_messages_cancellable,
                "Test input",
                timeout_seconds=120,
                cancel_event=signal,
            )
        )
        try:
            assert await asyncio.to_thread(entered.wait, 1)
        finally:
            signal.set()
        with pytest.raises(RealMidiPortError, match="capture_cancelled"):
            await asyncio.wait_for(capture, 1)
        factory.assert_called_once_with()
        port.open_port.assert_called_once_with(0)
        port.close_port.assert_called_once_with()

    asyncio.run(exercise())
