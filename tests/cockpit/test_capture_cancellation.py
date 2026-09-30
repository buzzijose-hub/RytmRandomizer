"""Input waits cannot delay DISARM or resurrect revoked session state."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from typing import cast

import pytest
from cockpit.conftest import _make_default_snapshot
from fastapi import WebSocket, WebSocketDisconnect

from conftest import elektron_syx_message, rytm_real_layout_kit_payload
from rytm_randomizer.cockpit.appliance import ApplianceWorkspace
from rytm_randomizer.cockpit.capture import KitCaptureService
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.device.connection import ConnectionState
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import handlers, server
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.observability.errors import StateError
from rytm_randomizer.observability.metrics import MidiMetrics

pytestmark = pytest.mark.fast


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


class DelayedInput:
    def __init__(self, *, cooperative: bool) -> None:
        self.cooperative = cooperative
        self.entered, self.release, self.closed = Event(), Event(), Event()
        self.cancel: Event | None = None

    def list_input_names(self) -> tuple[str, ...]:
        return ("Test input",)

    def capture_sysex_messages(self, _port: str, *, timeout_seconds: float) -> tuple[bytes, ...]:
        self.entered.set()
        try:
            assert timeout_seconds > 0
            assert self.release.wait(2), "test must release its owned input worker"
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
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=history,
        device=MockDeviceAdapter(initial),
        kit_capture_service=KitCaptureService(provider),
    )
    workspace = ApplianceWorkspace(simulation=True)
    workspace.sync(initial, context="current")
    workspace.navigate("anchor")
    workspace.roll(session.profile_registry.list_profiles()[0], 1234)
    assert workspace.candidate is not None
    session.appliance = workspace
    return session


async def next_ack(queue: server.ConnectionQueue, request_id: str) -> dict[str, object]:
    for _ in range(20):
        item = await asyncio.wait_for(queue.get(), timeout=1)
        if item.frame.get("request_id") == request_id:
            return item.frame
    raise AssertionError("ack missing from bounded queue")


def test_disarm_on_same_reader_cancels_input_and_rejects_late_frame(tmp_path: Path) -> None:
    async def exercise() -> None:
        provider = DelayedInput(cooperative=False)
        session = session_with_input(tmp_path, provider)
        original = session.device.capture_snapshot()
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
            inbound.command("disarm", {"type": "disarm"})
            assert (await next_ack(outbound, "disarm"))["ok"] is True
            assert provider.cancel is not None and provider.cancel.is_set()
            assert not provider.closed.is_set()  # DISARM did not wait for the input thread.
            assert session.appliance is not None
            assert session.appliance.candidate is None and session.appliance.anchor is None
            assert session.appliance.sources == {}
            provider.release.set()
            ack = await next_ack(outbound, "capture")
            assert ack["ok"] is False and ack["message"] == "current-kit capture cancelled"
            assert session.device.capture_snapshot() == original
            assert session.kit_captures == {}
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
            handlers.disarm_session_on_teardown(session)
            assert await asyncio.to_thread(provider.closed.wait, 1)
            assert session.device.capture_snapshot() == original and session.kit_captures == {}
            assert session.appliance is not None and session.appliance.sources == {}
        finally:
            provider.release.set()
            for socket in sockets:
                socket.frames.put_nowait(None)
            await asyncio.gather(*readers)

    asyncio.run(exercise())


def test_passive_watchdog_loss_revokes_appliance_and_staged_studio_plan(tmp_path: Path) -> None:
    session = session_with_input(tmp_path, DelayedInput(cooperative=True))
    session.active_profile = session.profile_registry.list_profiles()[0]
    asyncio.run(
        handlers.handle_command({"request_id": "roll", "command": {"type": "regen"}}, session)
    )
    asyncio.run(
        handlers.handle_command(
            {"request_id": "plan", "command": {"type": "prepare_send_plan"}}, session
        )
    )
    assert session.current_send_plan is not None
    events: list[dict[str, object]] = []
    watchdog = handlers.build_armed_watchdog(session, events.append)
    watchdog(
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
    assert session.current_candidate is None and session.current_send_plan is None
    assert session.appliance is not None and session.appliance.context is None
    assert session.appliance.anchor is None and session.appliance.sources == {}
    assert any(event["type"] == "appliance_changed" for event in events)


def test_cancelled_native_capture_never_imports_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    from rytm_randomizer import mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    signal = Event()
    signal.set()
    monkeypatch.setattr(mido_provider, "_import_rtmidi", lambda: pytest.fail("backend imported"))
    with pytest.raises(RealMidiPortError, match="capture_cancelled"):
        mido_provider.MidoMidiPortProvider().capture_sysex_messages_cancellable(
            "Test input", timeout_seconds=120, cancel_event=signal
        )


def test_native_input_poll_cancellation_closes_owned_port(monkeypatch: pytest.MonkeyPatch) -> None:
    from rytm_randomizer import mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    entered = Event()

    class Input:
        closed = 0

        def get_ports(self) -> tuple[str, ...]:
            return ("Test input",)

        def ignore_types(self, *, sysex: bool, timing: bool, active_sense: bool) -> None:
            assert (sysex, timing, active_sense) == (False, True, True)

        def open_port(self, index: int) -> None:
            assert index == 0

        def get_message(self) -> None:
            entered.set()

        def close_port(self) -> None:
            self.closed += 1

    port = Input()
    monkeypatch.setattr(
        mido_provider, "_import_rtmidi", lambda: SimpleNamespace(MidiIn=lambda: port)
    )

    async def exercise() -> None:
        signal = Event()
        capture = asyncio.create_task(
            asyncio.to_thread(
                mido_provider.MidoMidiPortProvider().capture_sysex_messages_cancellable,
                "Test input",
                timeout_seconds=120,
                cancel_event=signal,
            )
        )
        assert await asyncio.to_thread(entered.wait, 1)
        signal.set()
        with pytest.raises(RealMidiPortError, match="capture_cancelled"):
            await asyncio.wait_for(capture, 1)
        assert port.closed == 1

    asyncio.run(exercise())
