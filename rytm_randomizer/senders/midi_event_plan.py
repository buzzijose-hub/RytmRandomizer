"""Generic CC/NRPN event-plan sender."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Final, Protocol

from ..midi_io import Sender, send_cc, send_nrpn
from ..observability.errors import MidiEventPlanSendError

MIDI_EVENT_KIND_CC: Final[str] = "cc"
MIDI_EVENT_KIND_NRPN: Final[str] = "nrpn"


class CcNrpnSendEvent(Protocol):
    """Minimum event shape required by the generic CC/NRPN sender."""

    @property
    def message_kind(self) -> str: ...  # pragma: no cover - typing protocol

    @property
    def cc_msb(self) -> int | None: ...  # pragma: no cover - typing protocol

    @property
    def nrpn_address(
        self,
    ) -> tuple[int, int] | None: ...  # pragma: no cover - typing protocol

    @property
    def midi_value(self) -> int: ...  # pragma: no cover - typing protocol

    @property
    def channel(self) -> int: ...  # pragma: no cover - typing protocol


SleepCallable = Callable[[float], object]


def _midi_byte(name: str, value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 127:
        raise ValueError(f"{name} must be an integer in 0..127")
    return value


def validate_cc_nrpn_event_plan(events: Sequence[CcNrpnSendEvent]) -> int:
    """Validate every event before any MIDI write and return message count."""

    message_count = 0
    for event in events:
        _midi_byte("event channel", event.channel)
        if event.channel > 15:
            raise ValueError("event channel must be an integer in 0..15")
        _midi_byte("event MIDI value", event.midi_value)
        if event.message_kind == MIDI_EVENT_KIND_CC:
            if event.cc_msb is None:
                raise ValueError("CC event is missing a CC MSB")
            _midi_byte("CC MSB", event.cc_msb)
            message_count += 1
            continue
        if event.message_kind == MIDI_EVENT_KIND_NRPN:
            nrpn_address = event.nrpn_address
            if nrpn_address is None:
                raise ValueError("NRPN event is missing an NRPN address")
            if not isinstance(nrpn_address, tuple) or len(nrpn_address) != 2:
                raise ValueError("NRPN address must contain exactly two MIDI bytes")
            _midi_byte("NRPN MSB", nrpn_address[0])
            _midi_byte("NRPN LSB", nrpn_address[1])
            message_count += 3
            continue
        raise ValueError(f"unsupported MIDI event kind: {event.message_kind}")
    return message_count


def send_cc_nrpn_event_plan(
    events: Sequence[CcNrpnSendEvent],
    out: Sender,
    *,
    sleep: SleepCallable,
) -> int:
    """Send CC/NRPN events through ``out`` and return transport-message count."""

    expected_message_count = validate_cc_nrpn_event_plan(events)
    sent_message_count = 0

    def record_message_sent() -> None:
        nonlocal sent_message_count
        sent_message_count += 1

    try:
        for event in events:
            if event.message_kind == MIDI_EVENT_KIND_CC:
                send_cc(
                    out,
                    _midi_byte("CC MSB", event.cc_msb),
                    event.midi_value,
                    channel=event.channel,
                    sleep=sleep,
                    on_message_sent=record_message_sent,
                )
                continue
            nrpn_address = event.nrpn_address
            if nrpn_address is None:  # pragma: no cover - validated above
                raise AssertionError("validated NRPN event lost its address")
            send_nrpn(
                out,
                nrpn_address[0],
                nrpn_address[1],
                event.midi_value,
                channel=event.channel,
                sleep=sleep,
                on_message_sent=record_message_sent,
            )
    except KeyboardInterrupt as exc:
        raise MidiEventPlanSendError(
            "MIDI event-plan delivery was interrupted after "
            f"{sent_message_count} of {expected_message_count} messages",
            sent_message_count=sent_message_count,
            expected_message_count=expected_message_count,
            interrupted=True,
        ) from exc
    except (AttributeError, ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
        raise MidiEventPlanSendError(
            "MIDI event-plan delivery failed after "
            f"{sent_message_count} of {expected_message_count} messages",
            sent_message_count=sent_message_count,
            expected_message_count=expected_message_count,
        ) from exc
    return sent_message_count


__all__ = [
    "CcNrpnSendEvent",
    "MIDI_EVENT_KIND_CC",
    "MIDI_EVENT_KIND_NRPN",
    "MidiEventPlanSendError",
    "send_cc_nrpn_event_plan",
    "validate_cc_nrpn_event_plan",
]
