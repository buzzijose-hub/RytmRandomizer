"""Passive live MIDI input monitor — read-only listening (WS-4).

The Live-but-Passive model's *input* half: the cockpit may open MIDI
**inputs** freely (never interrupts the device's sound output) and stream
what it hears to every connected client as ``midi_activity`` events.

Design constraints, all test-pinned:

* **Injected opener only.** The monitor talks to a
  :class:`MidiInputOpener` Protocol (``open_input`` + nothing else); it
  never imports ``mido`` — the repo-wide perimeter and the import matrix
  both enforce that. Production injects the
  :class:`~rytm_randomizer.mido_provider.MidoMidiPortProvider` surface,
  tests inject fakes.
* **Never blocks the reader.** The port is drained with the non-blocking
  ``iter_pending`` surface on a fixed cadence; a backend read error is
  counted, never raised out of the poll loop.
* **Bounded drop-oldest ring.** Between flushes, observations land in a
  bounded ring; overflow drops the oldest observation and counts the
  drop, so a burst can never pin unbounded memory.
* **Coalesced batches.** Every flush (default 60 ms cadence) coalesces
  repeated same-``(channel, control)`` observations into one row carrying
  the latest value and a ``repeat_count``, then pushes ONE
  ``midi_activity`` event through the injected broadcast callable
  (production: :meth:`ConnectionRegistry.broadcast_event`).
* **Decoded labels.** Rows carry the operator-facing control labels from
  the existing passive Rytm CC lookup
  (:func:`~rytm_randomizer.state.rytm_cc_observe.build_rytm_cc_label_lookup`
  over :data:`~rytm_randomizer.data.ANALOG_RYTM_MANUAL_CC`).
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections import OrderedDict, deque
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Final, Protocol, cast, runtime_checkable

from ...observability.logging import get_logger
from ...state.rytm_cc_observe import RytmCcLabel, build_rytm_cc_label_lookup
from ..ws.protocol import EVENT_MIDI_ACTIVITY
from .connection import ConnectionState

__all__ = [
    "DEFAULT_BATCH_INTERVAL_SECONDS",
    "DEFAULT_RING_CAPACITY",
    "MidiInputMonitor",
    "MidiInputOpener",
    "MidiInputPortLike",
    "MidiMonitorSupervisor",
    "ObservedInputMessage",
    "default_rytm_cc_lookup",
]

_logger = get_logger(__name__)
"""Module logger for the passive input monitor (open failures, lifecycle)."""

DEFAULT_BATCH_INTERVAL_SECONDS: Final[float] = 0.06
"""Default coalescing cadence — one ``midi_activity`` batch per 60 ms."""

DEFAULT_RING_CAPACITY: Final[int] = 256
"""Bound on buffered observations between flushes (drop-oldest overflow)."""

_CONTROL_CHANGE_TYPE: Final[str] = "control_change"
"""The only message type the monitor decodes; everything else is counted."""

_READ_ERRORS: Final[tuple[type[BaseException], ...]] = (OSError, RuntimeError, ValueError)
"""Backend families a hostile/absent MIDI input can raise mid-drain."""


@runtime_checkable
class MidiInputPortLike(Protocol):
    """Minimal non-blocking input surface the monitor drains."""

    def iter_pending(self) -> Iterable[object]:
        """Return an iterable of backend-specific pending input messages."""
        ...


@runtime_checkable
class MidiInputOpener(Protocol):
    """The passive open-input seam — ``open_input`` and nothing else.

    Structurally satisfied by
    :class:`~rytm_randomizer.mido_provider.MidoMidiPortProvider`; the
    Protocol deliberately omits every output method so nothing reachable
    from the monitor can transmit.
    """

    def open_input(self, port_name: str) -> MidiInputPortLike:
        """Open a hardware MIDI input port by name (read-only)."""
        ...


def default_rytm_cc_lookup() -> Mapping[int, tuple[RytmCcLabel, ...]]:
    """Build the default Rytm CC label lookup from the shared fact table."""

    from ...data import ANALOG_RYTM_MANUAL_CC  # noqa: PLC0415 - lazy fact-table pull

    return build_rytm_cc_label_lookup(ANALOG_RYTM_MANUAL_CC.values())


@dataclass(frozen=True)
class ObservedInputMessage:
    """One decoded control-change observation buffered for the next flush."""

    channel: int
    control: int
    value: int
    observed_at: float


def _coerce_int(candidate: object) -> int | None:
    """Return ``candidate`` as an int when it is int-like, else ``None``."""

    if isinstance(candidate, bool):
        return None
    if isinstance(candidate, int):
        return candidate
    return None


class MidiInputMonitor:
    """Poll-driven passive input monitor with coalesced broadcast batches.

    Args:
        opener: The :class:`MidiInputOpener` seam (production: the mido
            provider; tests: a fake). The port opens in :meth:`open`,
            never at construction.
        port_name: The input port to listen on.
        broadcast: Non-blocking event sink — production wires
            :meth:`ConnectionRegistry.broadcast_event`.
        cc_lookup: ``control -> labels`` mapping; ``None`` uses
            :func:`default_rytm_cc_lookup`.
        batch_interval: Seconds between coalesced flushes.
        ring_capacity: Bound on buffered observations between flushes.
        clock: Timestamp source for ``observed_at`` (injectable).
    """

    def __init__(
        self,
        opener: MidiInputOpener,
        *,
        port_name: str,
        broadcast: Callable[[dict[str, object]], object],
        cc_lookup: Mapping[int, tuple[RytmCcLabel, ...]] | None = None,
        batch_interval: float = DEFAULT_BATCH_INTERVAL_SECONDS,
        ring_capacity: int = DEFAULT_RING_CAPACITY,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._opener = opener
        self._port_name = port_name
        self._broadcast = broadcast
        self._cc_lookup = default_rytm_cc_lookup() if cc_lookup is None else cc_lookup
        self._batch_interval = float(batch_interval)
        self._ring: deque[ObservedInputMessage] = deque()
        self._ring_capacity = int(ring_capacity)
        self._clock = clock
        self._port: MidiInputPortLike | None = None
        self._task: asyncio.Task[None] | None = None
        self._dropped_total = 0
        self._ignored_total = 0
        self._read_error_total = 0

    @property
    def port_name(self) -> str:
        """The input port name this monitor listens on."""

        return self._port_name

    @property
    def is_open(self) -> bool:
        """True once :meth:`open` succeeded and the port is held."""

        return self._port is not None

    @property
    def dropped_count(self) -> int:
        """Total observations dropped to the ring bound so far."""

        return self._dropped_total

    @property
    def batch_interval(self) -> float:
        """Seconds between coalesced flushes (fixed at construction)."""

        return self._batch_interval

    def open(self) -> None:
        """Open the input port through the injected opener (idempotent).

        Passive by the safety model — opening an input needs no arming
        and no confirmation. Opener errors propagate to the caller so a
        supervisor can surface them; the monitor stays closed.
        """

        if self._port is not None:
            return
        self._port = self._opener.open_input(self._port_name)

    def close(self) -> None:
        """Release the port (idempotent, best-effort backend close)."""

        port = self._port
        self._port = None
        if port is None:
            return
        close = getattr(port, "close", None)
        if not callable(close):
            return
        try:
            close()
        except _READ_ERRORS:
            return

    def poll_once(self) -> dict[str, object] | None:
        """Drain pending input into the ring, then flush one batch.

        Never raises for backend read failures — the reader must never
        block or crash the loop; failures are counted in
        ``read_errors`` on the next emitted batch instead.
        """

        port = self._port
        if port is None:
            return None
        try:
            pending = tuple(port.iter_pending())
        except _READ_ERRORS:
            self._read_error_total += 1
            pending = ()
        for message in pending:
            self._buffer_message(message)
        return self.flush()

    def flush(self) -> dict[str, object] | None:
        """Coalesce the ring into one ``midi_activity`` event and push it.

        Returns the broadcast event, or ``None`` when the ring is empty
        (no event is emitted for silence — unwired/quiet sessions stay
        byte-identical on the wire).
        """

        if not self._ring:
            return None
        coalesced: OrderedDict[tuple[int, int], dict[str, object]] = OrderedDict()
        for item in self._ring:
            key = (item.channel, item.control)
            row = coalesced.get(key)
            if row is None:
                coalesced[key] = {
                    "channel": item.channel,
                    "pad": item.channel + 1,
                    "control": item.control,
                    "value": item.value,
                    "repeat_count": 1,
                    "observed_at": item.observed_at,
                    "labels": self._label_names(item.control),
                }
            else:
                row["value"] = item.value
                row["repeat_count"] = cast("int", row["repeat_count"]) + 1
                row["observed_at"] = item.observed_at
        self._ring.clear()
        event: dict[str, object] = {
            "type": EVENT_MIDI_ACTIVITY,
            "midi_activity": {
                "port": self._port_name,
                "batch": list(coalesced.values()),
                "dropped": self._dropped_total,
                "ignored": self._ignored_total,
                "read_errors": self._read_error_total,
            },
        }
        self._broadcast(event)
        return event

    async def run(self) -> None:
        """Poll + flush forever at ``batch_interval`` until cancelled."""

        while True:
            self.poll_once()
            await asyncio.sleep(self._batch_interval)

    async def start(self) -> None:
        """Spawn :meth:`run` as a background task (idempotent)."""

        if self._task is not None:
            return
        self._task = asyncio.get_running_loop().create_task(self.run())

    async def stop(self) -> None:
        """Cancel + await the poll task, then release the port (idempotent)."""

        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self.close()

    def _buffer_message(self, message: object) -> None:
        """Decode one backend message into the ring (drop-oldest on overflow)."""

        if getattr(message, "type", None) != _CONTROL_CHANGE_TYPE:
            self._ignored_total += 1
            return
        channel = _coerce_int(getattr(message, "channel", None))
        control = _coerce_int(getattr(message, "control", None))
        value = _coerce_int(getattr(message, "value", None))
        if channel is None or control is None or value is None:
            self._ignored_total += 1
            return
        if len(self._ring) >= self._ring_capacity:
            self._ring.popleft()
            self._dropped_total += 1
        self._ring.append(
            ObservedInputMessage(
                channel=channel,
                control=control,
                value=value,
                observed_at=self._clock(),
            )
        )

    def _label_names(self, control: int) -> list[str]:
        """Operator-facing label names for one CC number (may be empty)."""

        return [label.display_name for label in self._cc_lookup.get(control, ())]


class MidiMonitorSupervisor:
    """Follow the passive connection state: one monitor per selected input.

    Registered as a ConnectionManager notify hook by ``__main__``. When a
    poll diff selects an Elektron input, the supervisor opens ONE
    :class:`MidiInputMonitor` on it (passive — no arming involved) and
    spawns its poll loop on the serving event loop; when the input
    disappears or changes, the current monitor is stopped and closed.
    Open failures are logged and swallowed — a broken input backend must
    never take the cockpit down.
    """

    def __init__(
        self,
        opener: MidiInputOpener,
        *,
        broadcast: Callable[[dict[str, object]], object],
        cc_lookup: Mapping[int, tuple[RytmCcLabel, ...]] | None = None,
        batch_interval: float = DEFAULT_BATCH_INTERVAL_SECONDS,
    ) -> None:
        self._opener = opener
        self._broadcast = broadcast
        self._cc_lookup = default_rytm_cc_lookup() if cc_lookup is None else cc_lookup
        self._batch_interval = float(batch_interval)
        self._monitor: MidiInputMonitor | None = None
        self._task: asyncio.Task[None] | None = None

    @property
    def active_port(self) -> str | None:
        """The input port the current monitor listens on, or ``None``."""

        if self._monitor is None:
            return None
        return self._monitor.port_name

    @property
    def monitor(self) -> MidiInputMonitor | None:
        """The currently running monitor (``None`` when idle)."""

        return self._monitor

    def notify(self, state: ConnectionState) -> None:
        """React to one passive connection diff (ConnectionManager hook)."""

        selected = state.selected_input
        if selected == self.active_port:
            return
        self._stop_current()
        if selected is None:
            return
        monitor = MidiInputMonitor(
            self._opener,
            port_name=selected,
            broadcast=self._broadcast,
            cc_lookup=self._cc_lookup,
            batch_interval=self._batch_interval,
        )
        try:
            monitor.open()
        except _READ_ERRORS as exc:
            _logger.warning(
                "midi_monitor_open_failed",
                extra={
                    "port_name": selected,
                    "exception_type": type(exc).__name__,
                    "exception_repr": repr(exc),
                },
            )
            return
        self._monitor = monitor
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No serving loop (synchronous test harness): the monitor is
            # open and pollable via poll_once(); no background task runs.
            return
        self._task = loop.create_task(monitor.run())

    async def aclose(self) -> None:
        """Stop + close the current monitor (FastAPI shutdown handler)."""

        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        monitor = self._monitor
        self._monitor = None
        if monitor is not None:
            monitor.close()

    def _stop_current(self) -> None:
        """Synchronously cancel the poll task and release the port."""

        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
        monitor = self._monitor
        self._monitor = None
        if monitor is not None:
            monitor.close()
