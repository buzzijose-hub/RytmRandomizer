"""Generic CC/NRPN event-plan sender."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Final, Protocol

from ..midi_io import Sender, send_cc, send_nrpn

MIDI_EVENT_KIND_CC: Final[str] = "cc"
MIDI_EVENT_KIND_NRPN: Final[str] = "nrpn"


class CcNrpnSendEvent(Protocol):
    """Minimum event shape required by the generic CC/NRPN sender."""

    message_kind: str
    cc_msb: int | None
    nrpn_address: tuple[int, int] | None
    midi_value: int
    channel: int


SleepCallable = Callable[[float], object]


def send_cc_nrpn_event_plan(
    events: Sequence[CcNrpnSendEvent],
    out: Sender,
    *,
    sleep: SleepCallable,
) -> int:
    """Send CC/NRPN events through ``out`` and return transport-message count."""

    message_count = 0
    for event in events:
        if event.message_kind == MIDI_EVENT_KIND_CC:
            if event.cc_msb is None:
                raise ValueError("CC event is missing a CC MSB")
            send_cc(
                out,
                event.cc_msb,
                event.midi_value,
                channel=event.channel,
                sleep=sleep,
            )
            message_count += 1
            continue
        if event.message_kind == MIDI_EVENT_KIND_NRPN:
            if event.nrpn_address is None:
                raise ValueError("NRPN event is missing an NRPN address")
            send_nrpn(
                out,
                event.nrpn_address[0],
                event.nrpn_address[1],
                event.midi_value,
                channel=event.channel,
                sleep=sleep,
            )
            message_count += 3
            continue
        raise ValueError(f"unsupported MIDI event kind: {event.message_kind}")
    return message_count


__all__ = [
    "CcNrpnSendEvent",
    "MIDI_EVENT_KIND_CC",
    "MIDI_EVENT_KIND_NRPN",
    "send_cc_nrpn_event_plan",
]
