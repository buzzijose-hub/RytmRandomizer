"""Cancellation races refuse late input without consuming another action's state."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from cockpit.conftest import TEST_WS_TOKEN, FixedFrameCaptureProvider, _make_default_snapshot

from conftest import elektron_syx_message, rytm_real_layout_kit_payload
from rytm_randomizer import mido_provider
from rytm_randomizer.cockpit import __main__ as cockpit_main
from rytm_randomizer.cockpit.appliance import ApplianceWorkspace
from rytm_randomizer.cockpit.capture import KitCaptureResult, KitCaptureService
from rytm_randomizer.cockpit.capture import service as capture_service
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.device.connection import ConnectionState
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.observability.errors import StateError
from rytm_randomizer.real_midi_adapter import RealMidiPortError
from rytm_randomizer.senders.armed_apply import ArmedApplySession, ExactPortOpener, OutputPortLike

pytestmark = pytest.mark.fast


@pytest.fixture
def capture_edge_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CockpitSession:
    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path / "profiles")
    frame = elektron_syx_message(rytm_real_layout_kit_payload())
    session = cockpit_main.build_session(
        KitCaptureService(FixedFrameCaptureProvider(frame)),
        device=MockDeviceAdapter(_make_default_snapshot()),
    )
    session.appliance = ApplianceWorkspace(simulation=True)
    session.appliance.sync(session.device.capture_snapshot(), context="known-source")
    session.appliance.navigate("anchor")
    return session


@pytest.mark.parametrize(
    "cancel_at", ["before_input", "receive_error", "after_receive", "after_decode"]
)
def test_service_cancellation_at_each_handoff_refuses_frame_and_releases_lock(
    monkeypatch: pytest.MonkeyPatch, cancel_at: str
) -> None:
    signal = Event()
    frame = elektron_syx_message(rytm_real_layout_kit_payload())
    provider = FixedFrameCaptureProvider(frame)
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

    # An interrupted receive never retains the service's exclusive capture lock.
    monkeypatch.setattr(provider, "capture_sysex_messages", original_receive)
    monkeypatch.setattr(capture_service, "_decode_capture_result", original_decode)
    signal.clear()
    assert service.capture("analog_rytm_mk2", "Mock input", cancel_event=signal).frame_bytes > 0


def test_native_frame_arriving_during_cancellation_is_discarded_and_input_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signal = Event()
    port = Mock(spec=("get_ports", "ignore_types", "open_port", "get_message", "close_port"))
    port.get_ports.return_value = ("Mock input",)

    def arrive() -> tuple[list[int], float]:
        signal.set()
        return ([0xF0, 0x01, 0xF7], 0.0)

    port.get_message.side_effect = arrive
    factory = Mock(return_value=port)
    monkeypatch.setattr(mido_provider, "_import_rtmidi", lambda: SimpleNamespace(MidiIn=factory))
    with pytest.raises(RealMidiPortError, match="capture_cancelled"):
        mido_provider.MidoMidiPortProvider().capture_sysex_messages_cancellable(
            "Mock input", timeout_seconds=1, cancel_event=signal
        )
    factory.assert_called_once_with()
    port.open_port.assert_called_once_with(0)
    port.get_message.assert_called_once_with()
    port.close_port.assert_called_once_with()


def test_second_capture_keeps_existing_owner_and_never_calls_provider(
    capture_edge_session: CockpitSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = capture_edge_session
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
                    "input_port": "Mock input",
                },
            },
            session,
        )
    )
    assert ack["ok"] is False and ack["message"] == "another current-kit capture is active"
    assert session.capture_cancel is owner and not owner.is_set()
    receive.assert_not_called()


@pytest.mark.parametrize("replace_owner", [False, True])
def test_completed_capture_cannot_publish_across_a_changed_generation(
    capture_edge_session: CockpitSession,
    monkeypatch: pytest.MonkeyPatch,
    replace_owner: bool,
) -> None:
    session = capture_edge_session
    original = session.device.capture_snapshot()
    receive = session.kit_capture_service.capture
    newer_owner = Event()

    def changed_context(device_id: str, port: str, *, cancel_event: Event) -> KitCaptureResult:
        result = receive(device_id, port, cancel_event=cancel_event)
        session.capture_generation += 1
        if replace_owner:
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
    assert session.capture_cancel is (newer_owner if replace_owner else None)
    assert not newer_owner.is_set()


@pytest.mark.parametrize("broadcast", [False, True])
def test_armed_watchdog_revokes_appliance_even_without_a_connected_browser(
    capture_edge_session: CockpitSession, broadcast: bool
) -> None:
    session = capture_edge_session
    port = Mock(spec=OutputPortLike)
    opener = Mock(spec=ExactPortOpener)
    opener.open_exact.return_value = port
    armed = ArmedApplySession(opener=opener, port_name="Mock output", arm_token=TEST_WS_TOKEN)
    armed.arm(TEST_WS_TOKEN)
    session.armed_apply = armed
    session.capture_cancel = Event()
    cancellation = session.capture_cancel
    events: list[dict[str, object]] = []
    watchdog = handlers.build_armed_watchdog(session, events.append if broadcast else None)
    lost = ConnectionState(
        phase="disconnected",
        available_inputs=(),
        available_outputs=(),
        selected_input=None,
        selected_output=None,
        last_error_fingerprint=None,
        changed_at=datetime.now(timezone.utc),
    )
    watchdog(lost)
    assert cancellation.is_set() and session.armed_apply is None
    assert session.appliance is not None and session.appliance.context is None
    assert session.appliance.anchor is None and session.appliance.sources == {}
    port.close.assert_called_once_with()
    port.send.assert_not_called()
    if broadcast:
        event = next(item for item in events if item["type"] == "appliance_changed")
        assert event["state"]["armed"] is False
        assert event["state"]["candidate"] is None
    else:
        assert events == []
    prior = list(events)
    watchdog(lost)
    assert events == prior
    port.close.assert_called_once_with()
