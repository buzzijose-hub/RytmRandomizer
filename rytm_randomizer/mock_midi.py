"""Test-only mock MIDI boundary.

This module contains inert, in-memory helpers for future tests that need to
represent intended MIDI-like messages. It does not import MIDI libraries, open
ports, send MIDI, or touch hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Iterable, Mapping


def _validate_integer(name: str, value: int) -> None:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class MidiMessage:
    """Immutable intended MIDI-like message for tests only."""

    message_type: str
    channel: int
    control: int
    value: int
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.message_type, str):
            raise TypeError("message_type must be a string")
        _validate_integer("channel", self.channel)
        _validate_integer("control", self.control)
        _validate_integer("value", self.value)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def type(self) -> str:
        """Mido-compatible message type alias for runtime dry-run capture."""

        return self.message_type


def build_cc_message(
    channel: int,
    control: int,
    value: int,
    metadata: Mapping[str, object] | None = None,
) -> MidiMessage:
    """Build an inert CC-style message representation for tests."""

    return MidiMessage(
        message_type="cc",
        channel=channel,
        control=control,
        value=value,
        metadata=_freeze_metadata(metadata),
    )


class MockMidiSender:
    """In-memory sender for tests; never opens ports or talks to hardware."""

    def __init__(self) -> None:
        self._messages: list[MidiMessage] = []

    @property
    def sent_messages(self) -> tuple[MidiMessage, ...]:
        return tuple(self._messages)

    @property
    def messages(self) -> tuple[MidiMessage, ...]:
        return self.sent_messages

    def send(self, message: MidiMessage) -> None:
        if not isinstance(message, MidiMessage):
            raise TypeError("message must be a MidiMessage")
        self._messages.append(message)

    def send_many(self, messages: Iterable[MidiMessage]) -> None:
        for message in messages:
            self.send(message)

    def clear(self) -> None:
        self._messages.clear()
