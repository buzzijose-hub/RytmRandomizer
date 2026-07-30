"""Canonical bounded vocabulary for compiled MIDI event plans."""

from __future__ import annotations

from typing import Final, Literal, TypeAlias

MidiEventKind: TypeAlias = Literal["cc", "nrpn"]
MidiEventSkipCode: TypeAlias = Literal["not-transport-ready", "paired-cc-unverified"]

MIDI_EVENT_KIND_CC: Final[MidiEventKind] = "cc"
MIDI_EVENT_KIND_NRPN: Final[MidiEventKind] = "nrpn"
MIDI_EVENT_SKIP_NOT_READY: Final[MidiEventSkipCode] = "not-transport-ready"
MIDI_EVENT_SKIP_PAIRED_CC_UNVERIFIED: Final[MidiEventSkipCode] = "paired-cc-unverified"

__all__ = [
    "MIDI_EVENT_KIND_CC",
    "MIDI_EVENT_KIND_NRPN",
    "MIDI_EVENT_SKIP_NOT_READY",
    "MIDI_EVENT_SKIP_PAIRED_CC_UNVERIFIED",
    "MidiEventKind",
    "MidiEventSkipCode",
]
