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
* **Per-family decoding.** Rows are decoded by a
  :class:`MonitorDecoder` chosen from the ``devices`` registry for the
  connected family — never by an unconditional Rytm assumption. The Rytm
  decoder labels CCs from
  :data:`~rytm_randomizer.data.ANALOG_RYTM_MANUAL_CC` and reports a
  ``pad`` (channel + 1, 12 pads); the Analog Four decoder labels from
  :data:`~rytm_randomizer.data.ANALOG_FOUR_MANUAL_CC` and reports a
  ``track`` (4 tracks). An unrecognised device gets the neutral
  :data:`UNKNOWN_DEVICE_DECODER`: no labels invented, no pad/track
  claimed, and ``device_id`` reported as :data:`UNKNOWN_DEVICE_ID` so the
  UI can say "unknown device" instead of silently mislabelling A4 traffic
  as Rytm pads.

Why per-family and not "Rytm plus a note": CC 16 on a Rytm is a pad
parameter and on an Analog Four is a different control entirely, and
``channel + 1`` is a *pad* number only on the 12-pad Rytm grid. Applying
the Rytm reading to an A4 connection produced confidently wrong operator
labels — the defect this seam fixes.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections import OrderedDict, deque
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Protocol, cast, runtime_checkable

from ...observability.logging import get_logger
from ...state.rytm_cc_observe import RytmCcLabel, build_rytm_cc_label_lookup
from ..ws.protocol import EVENT_MIDI_ACTIVITY
from .connection import ConnectionState

__all__ = [
    "ANALOG_FOUR_DEVICE_ID",
    "ANALOG_RYTM_DEVICE_ID",
    "DEFAULT_BATCH_INTERVAL_SECONDS",
    "DEFAULT_RING_CAPACITY",
    "UNKNOWN_DEVICE_DECODER",
    "UNKNOWN_DEVICE_ID",
    "MidiInputMonitor",
    "MidiInputOpener",
    "MidiInputPortLike",
    "MidiMonitorSupervisor",
    "MonitorDecoder",
    "ObservedInputMessage",
    "AnalogFourCcRow",
    "analog_four_cc_lookup",
    "build_analog_four_cc_label_lookup",
    "default_rytm_cc_lookup",
    "decoder_for_port_name",
    "decoder_for_device_id",
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


ANALOG_RYTM_DEVICE_ID: Final[str] = "analog_rytm_mk2"
"""Registry ``device_id`` of the Analog Rytm MKII (12 pads)."""

ANALOG_FOUR_DEVICE_ID: Final[str] = "analog_four_mk2"
"""Registry ``device_id`` of the Analog Four MKII (4 synth tracks)."""

UNKNOWN_DEVICE_ID: Final[str] = "unknown"
"""``device_id`` reported when no registered family matches the port."""

_RYTM_VOICE_KEY: Final[str] = "pad"
"""Per-voice key the Rytm decoder emits (pads, 1-based)."""

_A4_VOICE_KEY: Final[str] = "track"
"""Per-voice key the Analog Four decoder emits (tracks, 1-based)."""


def default_rytm_cc_lookup() -> Mapping[int, tuple[RytmCcLabel, ...]]:
    """Build the Analog Rytm CC label lookup from the shared fact table."""

    from ...data import ANALOG_RYTM_MANUAL_CC  # noqa: PLC0415 - lazy fact-table pull

    return build_rytm_cc_label_lookup(ANALOG_RYTM_MANUAL_CC.values())


class AnalogFourCcRow(Protocol):
    """The A4 fact-table fields the monitor's label adapter reads.

    Structural, so :class:`~rytm_randomizer.data.AnalogFourCcMapping`
    satisfies it without the data layer importing the cockpit.
    """

    @property
    def section(self) -> str: ...  # pragma: no cover - protocol declaration

    @property
    def parameter(self) -> str: ...  # pragma: no cover - protocol declaration

    @property
    def cc_msb(self) -> int | None: ...  # pragma: no cover - protocol declaration

    @property
    def nrpn_msb(self) -> int | None: ...  # pragma: no cover - protocol declaration

    @property
    def nrpn_lsb(self) -> int | None: ...  # pragma: no cover - protocol declaration


def build_analog_four_cc_label_lookup(
    rows: Iterable[AnalogFourCcRow],
) -> Mapping[int, tuple[RytmCcLabel, ...]]:
    """Adapt A4 CC fact rows into the shared ``control -> labels`` shape.

    ``AnalogFourCcMapping`` rows carry no ``scope`` / ``machine_key`` (the
    A4 has no machine-per-track concept), so they are adapted into the
    shared :class:`RytmCcLabel` shape here rather than by widening the
    fact table — the label vocabulary is display-only.

    Rows with no ``cc_msb`` (NRPN-only parameters) are skipped: there is
    no CC number to key a control-change observation by, and bucketing
    them under a placeholder would fabricate a label for real traffic.
    """

    grouped: dict[int, list[RytmCcLabel]] = {}
    for row in rows:
        control = row.cc_msb
        if control is None:
            continue
        grouped.setdefault(control, []).append(
            RytmCcLabel(
                section=row.section,
                parameter=row.parameter,
                scope="track",
                nrpn_msb=row.nrpn_msb,
                nrpn_lsb=row.nrpn_lsb,
            )
        )
    return {
        control: tuple(sorted(labels, key=lambda label: (label.section, label.parameter)))
        for control, labels in sorted(grouped.items())
    }


def analog_four_cc_lookup() -> Mapping[int, tuple[RytmCcLabel, ...]]:
    """Build the Analog Four CC label lookup from the shared fact table."""

    from ...data import ANALOG_FOUR_MANUAL_CC  # noqa: PLC0415 - lazy fact-table pull

    return build_analog_four_cc_label_lookup(ANALOG_FOUR_MANUAL_CC.values())


def _no_cc_lookup() -> Mapping[int, tuple[RytmCcLabel, ...]]:
    """Empty lookup — the neutral decoder invents no labels."""

    return {}


@dataclass(frozen=True)
class MonitorDecoder:
    """How one device family's control-change traffic is read.

    Selected from the ``devices`` registry per connection; never assumed.

    Attributes:
        device_id: Registry id, or :data:`UNKNOWN_DEVICE_ID`.
        display_name: Operator-facing family name.
        voice_key: Row key for the per-voice number (``"pad"`` on the
            Rytm, ``"track"`` on the Analog Four), or ``None`` when the
            family's voice layout is unknown — in which case no voice
            number is emitted at all rather than a guessed one.
        voice_count: Number of addressable voices, or ``None`` when
            unknown.
        build_lookup: Zero-arg factory for the ``control -> labels``
            mapping. A factory (not the mapping) so the fact tables stay
            lazily imported.
    """

    device_id: str
    display_name: str
    voice_key: str | None
    voice_count: int | None
    build_lookup: Callable[[], Mapping[int, tuple[RytmCcLabel, ...]]]

    def voice_for_channel(self, channel: int) -> int | None:
        """Return the 1-based voice number for ``channel``, or ``None``.

        ``None`` whenever the family's voice layout is unknown, or the
        channel falls outside it — an out-of-range channel is real
        traffic the operator should see undecorated, not forced onto a
        pad number the hardware never used.
        """

        if self.voice_key is None or self.voice_count is None:
            return None
        if not 0 <= channel < self.voice_count:
            return None
        return channel + 1


UNKNOWN_DEVICE_DECODER: Final[MonitorDecoder] = MonitorDecoder(
    device_id=UNKNOWN_DEVICE_ID,
    display_name="Unknown MIDI device",
    voice_key=None,
    voice_count=None,
    build_lookup=_no_cc_lookup,
)
"""Neutral decoder: labels nothing, claims no pad/track, says so plainly.

Deliberately NOT a Rytm fallback. Mislabelling unknown traffic with Rytm
parameter names is worse than no label — the operator cannot tell a real
decode from a coincidence.
"""

_DECODERS_BY_DEVICE_ID: Final[Mapping[str, MonitorDecoder]] = MappingProxyType(
    {
        ANALOG_RYTM_DEVICE_ID: MonitorDecoder(
            device_id=ANALOG_RYTM_DEVICE_ID,
            display_name="Elektron Analog Rytm MKII",
            voice_key=_RYTM_VOICE_KEY,
            voice_count=12,
            build_lookup=default_rytm_cc_lookup,
        ),
        ANALOG_FOUR_DEVICE_ID: MonitorDecoder(
            device_id=ANALOG_FOUR_DEVICE_ID,
            display_name="Elektron Analog Four MKII",
            voice_key=_A4_VOICE_KEY,
            voice_count=4,
            build_lookup=analog_four_cc_lookup,
        ),
    }
)

# Port-name stems that identify a family, longest-specific first. The
# generic ``elektron`` stem is deliberately absent: "Elektron <something>"
# alone does not say which machine, and guessing is the defect.
_PORT_NAME_DEVICE_STEMS: Final[tuple[tuple[str, str], ...]] = (
    ("analog rytm", ANALOG_RYTM_DEVICE_ID),
    ("analog four", ANALOG_FOUR_DEVICE_ID),
)


def decoder_for_device_id(device_id: str | None) -> MonitorDecoder:
    """Return the decoder for a registered ``device_id``.

    Falls back to :data:`UNKNOWN_DEVICE_DECODER` for ``None`` and for any
    id with no decoder — including a device that IS in the registry but
    has no monitor decoding yet. A registered-but-undecodable family must
    read as unknown, not as Rytm.
    """

    if device_id is None:
        return UNKNOWN_DEVICE_DECODER
    return _DECODERS_BY_DEVICE_ID.get(device_id, UNKNOWN_DEVICE_DECODER)


def decoder_for_port_name(port_name: str | None) -> MonitorDecoder:
    """Resolve a decoder from an OS MIDI port name.

    The port name is the only family signal available on a passive
    connection (no SysEx identity request is sent — that would be an
    outbound byte). A matched stem is confirmed against the ``devices``
    registry so this cannot decode a family the app does not support.
    """

    if port_name is None:
        return UNKNOWN_DEVICE_DECODER
    from ...devices import all_devices  # noqa: PLC0415 - lazy registry pull

    registered = all_devices()
    lowered = port_name.lower()
    for stem, device_id in _PORT_NAME_DEVICE_STEMS:
        if stem in lowered and device_id in registered:
            return decoder_for_device_id(device_id)
    return UNKNOWN_DEVICE_DECODER


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
        decoder: The :class:`MonitorDecoder` for the connected family;
            ``None`` resolves one from ``port_name`` via the ``devices``
            registry (:func:`decoder_for_port_name`), which yields
            :data:`UNKNOWN_DEVICE_DECODER` when the family is unknown.
        cc_lookup: Explicit ``control -> labels`` override; ``None`` uses
            the decoder's own lookup. Provided for tests and for a future
            operator-chosen label set — it never changes which family the
            monitor *reports*.
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
        decoder: MonitorDecoder | None = None,
        cc_lookup: Mapping[int, tuple[RytmCcLabel, ...]] | None = None,
        batch_interval: float = DEFAULT_BATCH_INTERVAL_SECONDS,
        ring_capacity: int = DEFAULT_RING_CAPACITY,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._opener = opener
        self._port_name = port_name
        self._broadcast = broadcast
        self._decoder = decoder_for_port_name(port_name) if decoder is None else decoder
        self._cc_lookup = self._decoder.build_lookup() if cc_lookup is None else cc_lookup
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
    def decoder(self) -> MonitorDecoder:
        """The per-family decoder this monitor labels traffic with."""

        return self._decoder

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
                voice = self._decoder.voice_for_channel(item.channel)
                new_row: dict[str, object] = {
                    "channel": item.channel,
                    # ``pad`` stays in the row shape (the wire contract the
                    # web client types against) but is now the DECODER's
                    # answer, not an unconditional ``channel + 1``: it is
                    # ``None`` for an Analog Four, an unknown device, or an
                    # out-of-range channel. A null pad renders as "no pad";
                    # a wrong pad number reads as fact.
                    "pad": voice if self._decoder.voice_key == _RYTM_VOICE_KEY else None,
                    "control": item.control,
                    "value": item.value,
                    "repeat_count": 1,
                    "observed_at": item.observed_at,
                    "labels": self._label_names(item.control),
                }
                # The family's own voice key alongside it (``track`` on an
                # A4), so a client can render the right noun. Omitted when
                # the family has no voice layout — nothing is invented.
                # (On a Rytm the key IS ``pad``, so this re-states the value
                # already set above rather than adding a second field.)
                if self._decoder.voice_key is not None and voice is not None:
                    new_row[self._decoder.voice_key] = voice
                coalesced[key] = new_row
            else:
                row["value"] = item.value
                row["repeat_count"] = cast("int", row["repeat_count"]) + 1
                row["observed_at"] = item.observed_at
        self._ring.clear()
        event: dict[str, object] = {
            "type": EVENT_MIDI_ACTIVITY,
            "midi_activity": {
                "port": self._port_name,
                # Which family these rows were decoded AS. Explicit so the
                # UI can label "unknown device" rather than implying Rytm.
                "device_id": self._decoder.device_id,
                "device_name": self._decoder.display_name,
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
    :class:`MidiInputMonitor` on it — which resolves its own
    :class:`MonitorDecoder` for that port's family, so switching from a
    Rytm to an Analog Four re-decodes rather than reusing Rytm labels —
    (passive: no arming involved) and
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
        # ``None`` (the production default) means "decode per family": each
        # monitor resolves its own decoder from the selected port name. An
        # explicit override pins one label set across every connection and
        # exists only for tests.
        self._cc_lookup = cc_lookup
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
