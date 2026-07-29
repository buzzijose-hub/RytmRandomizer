"""Tests for the passive live MIDI input monitor (WS-4).

Pins: injected-opener-only port access, non-blocking drain, bounded
drop-oldest ring with counted drops, coalesced same-CC batches on the
60 ms cadence, decoded labels from the shared Rytm CC lookup, and the
supervisor's follow-the-selected-input lifecycle.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import pytest

from rytm_randomizer.cockpit.device.connection import ConnectionState
from rytm_randomizer.cockpit.device.midi_monitor import (
    DEFAULT_BATCH_INTERVAL_SECONDS,
    DEFAULT_RING_CAPACITY,
    MidiInputMonitor,
    MidiMonitorSupervisor,
    default_rytm_cc_lookup,
)
from rytm_randomizer.cockpit.ws.protocol import EVENT_MIDI_ACTIVITY

pytestmark = pytest.mark.fast

_PORT = "Elektron Analog Rytm MK2 In"


@dataclass
class _Msg:
    type: str = "control_change"
    channel: int = 0
    control: int = 16
    value: int = 64


@dataclass
class _FakeInputPort:
    pending: list[object] = field(default_factory=list)
    raises: bool = False
    closed: int = 0

    def iter_pending(self) -> list[object]:
        if self.raises:
            raise OSError("backend read failed")
        drained = list(self.pending)
        self.pending.clear()
        return drained

    def close(self) -> None:
        self.closed += 1


@dataclass
class _FakeOpener:
    port: _FakeInputPort = field(default_factory=_FakeInputPort)
    raises: bool = False
    opened: list[str] = field(default_factory=list)

    def open_input(self, port_name: str) -> _FakeInputPort:
        self.opened.append(port_name)
        if self.raises:
            raise RuntimeError("no input backend")
        return self.port


def _make_monitor(
    opener: _FakeOpener | None = None,
    *,
    ring_capacity: int = 8,
) -> tuple[MidiInputMonitor, _FakeOpener, list[dict]]:
    opener = opener if opener is not None else _FakeOpener()
    events: list[dict] = []
    ticks = iter(float(n) for n in range(1, 10_000))
    monitor = MidiInputMonitor(
        opener,
        port_name=_PORT,
        broadcast=events.append,
        ring_capacity=ring_capacity,
        clock=lambda: next(ticks),
    )
    return monitor, opener, events


def test_defaults_match_spec() -> None:
    assert pytest.approx(0.06) == DEFAULT_BATCH_INTERVAL_SECONDS
    assert DEFAULT_RING_CAPACITY == 256
    monitor = MidiInputMonitor(_FakeOpener(), port_name=_PORT, broadcast=lambda _e: None)
    assert monitor.batch_interval == pytest.approx(0.06)
    assert monitor.port_name == _PORT


def test_open_goes_through_injected_opener_only_and_is_idempotent() -> None:
    monitor, opener, _ = _make_monitor()
    assert monitor.is_open is False
    monitor.open()
    monitor.open()
    assert monitor.is_open is True
    assert opener.opened == [_PORT]


def test_poll_before_open_is_a_noop() -> None:
    monitor, _, events = _make_monitor()
    assert monitor.poll_once() is None
    assert events == []


def test_poll_broadcasts_one_coalesced_batch() -> None:
    monitor, opener, events = _make_monitor()
    monitor.open()
    opener.port.pending = [
        _Msg(channel=0, control=16, value=10),
        _Msg(channel=0, control=16, value=20),
        _Msg(channel=1, control=17, value=30),
    ]
    event = monitor.poll_once()
    assert event is not None
    assert events == [event]
    assert event["type"] == EVENT_MIDI_ACTIVITY
    activity = event["midi_activity"]
    assert activity["port"] == _PORT
    assert activity["dropped"] == 0
    batch = activity["batch"]
    assert len(batch) == 2
    first, second = batch
    # Repeated same-(channel, control) coalesced: latest value wins.
    assert first["channel"] == 0
    assert first["pad"] == 1
    assert first["control"] == 16
    assert first["value"] == 20
    assert first["repeat_count"] == 2
    assert second["channel"] == 1
    assert second["pad"] == 2
    assert second["value"] == 30
    assert second["repeat_count"] == 1


def test_quiet_poll_emits_no_event() -> None:
    monitor, _, events = _make_monitor()
    monitor.open()
    assert monitor.poll_once() is None
    assert events == []


def test_ring_overflow_drops_oldest_and_counts() -> None:
    monitor, opener, _ = _make_monitor(ring_capacity=2)
    monitor.open()
    opener.port.pending = [
        _Msg(control=10, value=1),
        _Msg(control=11, value=2),
        _Msg(control=12, value=3),
    ]
    event = monitor.poll_once()
    assert event is not None
    assert monitor.dropped_count == 1
    controls = [row["control"] for row in event["midi_activity"]["batch"]]
    assert controls == [11, 12]  # oldest (control 10) dropped
    assert event["midi_activity"]["dropped"] == 1


def test_read_errors_never_raise_and_are_counted() -> None:
    monitor, opener, events = _make_monitor()
    monitor.open()
    opener.port.raises = True
    assert monitor.poll_once() is None  # no crash, nothing buffered
    opener.port.raises = False
    opener.port.pending = [_Msg()]
    event = monitor.poll_once()
    assert event is not None
    assert event["midi_activity"]["read_errors"] == 1
    assert len(events) == 1


def test_non_cc_and_malformed_messages_are_ignored_and_counted() -> None:
    monitor, opener, _ = _make_monitor()
    monitor.open()

    @dataclass
    class _Sysex:
        type: str = "sysex"

    @dataclass
    class _BadCc:
        type: str = "control_change"
        channel: object = "x"
        control: int = 16
        value: int = 1

    opener.port.pending = [_Sysex(), _BadCc(), _Msg(control=18, value=5)]
    event = monitor.poll_once()
    assert event is not None
    assert event["midi_activity"]["ignored"] == 2
    assert len(event["midi_activity"]["batch"]) == 1


def test_bool_values_are_rejected_as_malformed() -> None:
    monitor, opener, _ = _make_monitor()
    monitor.open()
    opener.port.pending = [_Msg(value=True)]  # type: ignore[arg-type]
    assert monitor.poll_once() is None


def test_labels_come_from_the_shared_rytm_cc_lookup() -> None:
    lookup = default_rytm_cc_lookup()
    labelled_control = next(iter(lookup))
    expected = [label.display_name for label in lookup[labelled_control]]
    opener = _FakeOpener()
    events: list[dict] = []
    monitor = MidiInputMonitor(opener, port_name=_PORT, broadcast=events.append)
    monitor.open()
    opener.port.pending = [_Msg(control=labelled_control)]
    event = monitor.poll_once()
    assert event is not None
    assert event["midi_activity"]["batch"][0]["labels"] == expected


def test_unknown_control_gets_empty_labels() -> None:
    lookup = default_rytm_cc_lookup()
    unlabelled = next(cc for cc in range(128) if cc not in lookup)
    monitor, opener, _ = _make_monitor()
    monitor.open()
    opener.port.pending = [_Msg(control=unlabelled, value=9)]
    event = monitor.poll_once()
    assert event is not None
    assert event["midi_activity"]["batch"][0]["labels"] == []


def test_observed_at_uses_injected_clock() -> None:
    monitor, opener, _ = _make_monitor()
    monitor.open()
    opener.port.pending = [_Msg(control=20), _Msg(control=20)]
    event = monitor.poll_once()
    assert event is not None
    row = event["midi_activity"]["batch"][0]
    assert row["observed_at"] == 2.0  # latest observation's clock tick


def test_close_is_idempotent_and_best_effort() -> None:
    monitor, opener, _ = _make_monitor()
    monitor.open()
    monitor.close()
    monitor.close()
    assert opener.port.closed == 1
    assert monitor.is_open is False


def test_close_handles_port_without_close() -> None:
    @dataclass
    class _NoClosePort:
        def iter_pending(self) -> list[object]:
            return []

    @dataclass
    class _NoCloseOpener:
        def open_input(self, _name: str) -> _NoClosePort:
            return _NoClosePort()

    monitor = MidiInputMonitor(_NoCloseOpener(), port_name=_PORT, broadcast=lambda _e: None)
    monitor.open()
    monitor.close()
    assert monitor.is_open is False


def test_close_swallows_backend_close_errors() -> None:
    @dataclass
    class _BadClosePort:
        def iter_pending(self) -> list[object]:
            return []

        def close(self) -> None:
            raise RuntimeError("close failed")

    @dataclass
    class _BadCloseOpener:
        def open_input(self, _name: str) -> _BadClosePort:
            return _BadClosePort()

    monitor = MidiInputMonitor(_BadCloseOpener(), port_name=_PORT, broadcast=lambda _e: None)
    monitor.open()
    monitor.close()
    assert monitor.is_open is False


def test_run_loop_polls_on_cadence_and_start_stop_are_idempotent() -> None:
    async def _scenario() -> None:
        opener = _FakeOpener()
        events: list[dict] = []
        monitor = MidiInputMonitor(
            opener,
            port_name=_PORT,
            broadcast=events.append,
            batch_interval=0.001,
            clock=time.monotonic,
        )
        monitor.open()
        opener.port.pending = [_Msg()]
        await monitor.start()
        await monitor.start()  # idempotent
        deadline = time.monotonic() + 1.0
        while not events and time.monotonic() < deadline:
            await asyncio.sleep(0.002)
        await monitor.stop()
        await monitor.stop()  # idempotent
        assert events, "run loop never flushed a batch"
        assert monitor.is_open is False

    asyncio.run(_scenario())


# ---------------------------------------------------------------------------
# MidiMonitorSupervisor — follow the passive selected input.
# ---------------------------------------------------------------------------


def _state(selected_input: str | None, *, phase: str = "listening") -> ConnectionState:
    return ConnectionState(
        phase=phase,  # type: ignore[arg-type]
        available_inputs=() if selected_input is None else (selected_input,),
        available_outputs=(),
        selected_input=selected_input,
        selected_output=None,
        last_error_fingerprint=None,
        changed_at=1.0,
    )


def test_supervisor_opens_monitor_when_input_selected() -> None:
    opener = _FakeOpener()
    supervisor = MidiMonitorSupervisor(opener, broadcast=lambda _e: None)
    assert supervisor.active_port is None
    supervisor.notify(_state(_PORT))
    assert supervisor.active_port == _PORT
    assert opener.opened == [_PORT]


def test_supervisor_is_noop_when_selection_unchanged() -> None:
    opener = _FakeOpener()
    supervisor = MidiMonitorSupervisor(opener, broadcast=lambda _e: None)
    supervisor.notify(_state(_PORT))
    supervisor.notify(_state(_PORT))
    assert opener.opened == [_PORT]  # opened exactly once


def test_supervisor_stops_monitor_when_input_disappears() -> None:
    opener = _FakeOpener()
    supervisor = MidiMonitorSupervisor(opener, broadcast=lambda _e: None)
    supervisor.notify(_state(_PORT))
    supervisor.notify(_state(None, phase="searching"))
    assert supervisor.active_port is None
    assert opener.port.closed == 1


def test_supervisor_switches_monitor_when_input_changes() -> None:
    opener = _FakeOpener()
    supervisor = MidiMonitorSupervisor(opener, broadcast=lambda _e: None)
    supervisor.notify(_state(_PORT))
    supervisor.notify(_state("Another Elektron In"))
    assert supervisor.active_port == "Another Elektron In"
    assert opener.opened == [_PORT, "Another Elektron In"]


def test_supervisor_swallows_open_failures() -> None:
    opener = _FakeOpener(raises=True)
    supervisor = MidiMonitorSupervisor(opener, broadcast=lambda _e: None)
    supervisor.notify(_state(_PORT))  # must not raise
    assert supervisor.active_port is None
    assert supervisor.monitor is None


def test_supervisor_monitor_broadcasts_through_injected_sink() -> None:
    opener = _FakeOpener()
    events: list[dict] = []
    supervisor = MidiMonitorSupervisor(opener, broadcast=events.append)
    supervisor.notify(_state(_PORT))
    monitor = supervisor.monitor
    assert monitor is not None
    opener.port.pending = [_Msg()]
    monitor.poll_once()
    assert len(events) == 1
    assert events[0]["type"] == EVENT_MIDI_ACTIVITY


def test_supervisor_spawns_and_cancels_task_on_running_loop() -> None:
    async def _scenario() -> None:
        opener = _FakeOpener()
        events: list[dict] = []
        supervisor = MidiMonitorSupervisor(opener, broadcast=events.append, batch_interval=0.001)
        supervisor.notify(_state(_PORT))
        opener.port.pending = [_Msg()]
        deadline = time.monotonic() + 1.0
        while not events and time.monotonic() < deadline:
            await asyncio.sleep(0.002)
        assert events, "supervised monitor never flushed"
        # Switch while a poll task is live: the running task is cancelled
        # synchronously and the old port is released.
        second_port = _FakeInputPort()
        opener.port = second_port
        supervisor.notify(_state("Another Elektron In"))
        assert supervisor.active_port == "Another Elektron In"
        await supervisor.aclose()
        await supervisor.aclose()  # idempotent
        assert supervisor.monitor is None
        assert second_port.closed == 1

    asyncio.run(_scenario())


def test_supervisor_aclose_without_monitor_is_noop() -> None:
    async def _scenario() -> None:
        supervisor = MidiMonitorSupervisor(_FakeOpener(), broadcast=lambda _e: None)
        await supervisor.aclose()

    asyncio.run(_scenario())
