"""Passive validation contract for tagged CC/NRPN event plans."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from typing import Protocol, cast

from ..data.midi_event_kinds import (
    MIDI_EVENT_KIND_CC,
    MIDI_EVENT_KIND_NRPN,
    MidiEventKind,
)


class CcNrpnEvent(Protocol):
    """Minimum read-only shape shared by compilers, readers, and senders."""

    @property
    @abstractmethod
    def message_kind(self) -> MidiEventKind: ...

    @property
    @abstractmethod
    def cc_msb(self) -> int | None: ...

    @property
    @abstractmethod
    def cc_lsb(self) -> int | None: ...

    @property
    @abstractmethod
    def nrpn_address(self) -> tuple[int, int] | None: ...

    @property
    @abstractmethod
    def midi_value(self) -> int: ...

    @property
    @abstractmethod
    def channel(self) -> int: ...


def _midi_byte(name: str, value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 127:
        raise ValueError(f"{name} must be an integer in 0..127")
    return value


def _validated_event_nrpn_address(value: object) -> tuple[int, int]:
    if not isinstance(value, tuple):
        raise ValueError("NRPN address must contain exactly two MIDI bytes")
    address = cast(tuple[object, ...], value)
    if len(address) != 2:
        raise ValueError("NRPN address must contain exactly two MIDI bytes")
    msb = _midi_byte("NRPN MSB", address[0])
    lsb = _midi_byte("NRPN LSB", address[1])
    return (msb, lsb)


def midi_event_kind_for_addresses(
    *,
    cc_msb: int | None,
    cc_lsb: int | None,
    nrpn_address: tuple[int, int] | None,
) -> MidiEventKind:
    """Choose a transport kind from canonical source mapping addresses.

    A parameter may expose both a verified direct CC and an NRPN alternative.
    The compiled event prefers the direct CC and retains only that selected
    address. A paired CC still fails closed until its 14-bit value domain is
    verified.
    """

    if cc_msb is not None:
        if cc_lsb is not None:
            raise ValueError("paired-CC events require a verified CC14 transport")
        return MIDI_EVENT_KIND_CC
    if cc_lsb is not None:
        raise ValueError("CC LSB requires a CC MSB")
    if nrpn_address is not None:
        return MIDI_EVENT_KIND_NRPN
    raise ValueError("MIDI event has no CC or NRPN address")


def validate_cc_nrpn_event(event: CcNrpnEvent) -> int:
    """Validate one tagged event and return its transport-message count."""

    cc_lsb = getattr(event, "cc_lsb", None)
    _midi_byte("event channel", event.channel)
    if event.channel > 15:
        raise ValueError("event channel must be an integer in 0..15")
    _midi_byte("event MIDI value", event.midi_value)
    if event.message_kind == MIDI_EVENT_KIND_CC:
        if event.cc_msb is None:
            raise ValueError("CC event is missing a CC MSB")
        if cc_lsb is not None:
            raise ValueError("paired-CC events require a verified CC14 transport")
        if event.nrpn_address is not None:
            raise ValueError("CC event must not include an NRPN address")
        _midi_byte("CC MSB", event.cc_msb)
        return 1
    if event.message_kind == MIDI_EVENT_KIND_NRPN:
        if event.cc_msb is not None or cc_lsb is not None:
            raise ValueError("NRPN event must not include a CC address")
        nrpn_address = event.nrpn_address
        if nrpn_address is None:
            raise ValueError("NRPN event is missing an NRPN address")
        _validated_event_nrpn_address(nrpn_address)
        return 3
    raise ValueError(f"unsupported MIDI event kind: {event.message_kind}")


def validate_cc_nrpn_event_plan(events: Sequence[CcNrpnEvent]) -> int:
    """Validate all events before delivery and return total message count."""

    return sum(validate_cc_nrpn_event(event) for event in events)


__all__ = [
    "CcNrpnEvent",
    "midi_event_kind_for_addresses",
    "validate_cc_nrpn_event",
    "validate_cc_nrpn_event_plan",
]
