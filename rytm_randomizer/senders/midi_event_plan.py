"""Generic CC/NRPN event-plan sender."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from ..behavior.midi_event_plan import (
    CcNrpnEvent,
)
from ..behavior.midi_event_plan import validate_cc_nrpn_event_plan as _validate_cc_nrpn_event_plan
from ..data.midi_event_kinds import (
    MIDI_EVENT_KIND_CC,
    MIDI_EVENT_KIND_NRPN,
    MidiEventKind,
)
from ..midi_io import Sender, send_cc, send_nrpn
from ..observability.errors import MidiEventPlanSendError

SleepCallable = Callable[[float], object]


def send_cc_nrpn_event_plan(
    events: Sequence[CcNrpnEvent],
    out: Sender,
    *,
    sleep: SleepCallable,
) -> int:
    """Send CC/NRPN events through ``out`` and return transport-message count."""

    expected_message_count = _validate_cc_nrpn_event_plan(events)
    sent_message_count = 0

    def record_message_sent() -> None:
        nonlocal sent_message_count
        sent_message_count += 1

    try:
        for event in events:
            if event.message_kind == MIDI_EVENT_KIND_CC:
                cc_msb = event.cc_msb
                if cc_msb is None:
                    raise AssertionError("validated CC event lost its address")
                send_cc(
                    out,
                    cc_msb,
                    event.midi_value,
                    channel=event.channel,
                    sleep=sleep,
                    on_message_sent=record_message_sent,
                )
                continue
            nrpn_address = event.nrpn_address
            if nrpn_address is None:
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
    except (KeyboardInterrupt, SystemExit) as exc:
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
    "CcNrpnEvent",
    "MIDI_EVENT_KIND_CC",
    "MIDI_EVENT_KIND_NRPN",
    "MidiEventKind",
    "MidiEventPlanSendError",
    "send_cc_nrpn_event_plan",
]
