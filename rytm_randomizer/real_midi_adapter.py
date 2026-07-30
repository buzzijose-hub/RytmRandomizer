"""Import-safe real MIDI adapter boundary.

This module defines a future real MIDI boundary without importing real MIDI
libraries at module import time. Unit tests must use fake providers only.

The three error classes below are also members of the unified
:mod:`rytm_randomizer.observability.errors` taxonomy: they inherit from both
:class:`~rytm_randomizer.observability.errors.MidiError` AND ``RuntimeError``.
The multi-inheritance preserves every existing ``except RuntimeError``
behaviour AND lets new code ``except MidiError`` to catch the whole MIDI
boundary in one clause. Class identity is unchanged -- ``isinstance`` checks
in existing tests and ``from rytm_randomizer.real_midi_adapter import ...``
imports keep working.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import ClassVar, Protocol, runtime_checkable

from .mock_midi import MidiMessage
from .observability.errors import MidiError


class RealMidiDependencyError(MidiError, RuntimeError):
    """Raised when a real MIDI provider is required but absent.

    Member of the unified :class:`~rytm_randomizer.observability.errors.MidiError`
    taxonomy. ``RuntimeError`` is kept as an additional base for
    backward-compatibility with any ``except RuntimeError`` caller.
    """

    fingerprint: ClassVar[str] = "midi.port.dependency_missing"


class RealMidiPortError(MidiError, RuntimeError):
    """Raised when MIDI port selection fails safely.

    Member of the unified :class:`~rytm_randomizer.observability.errors.MidiError`
    taxonomy. ``RuntimeError`` is kept as an additional base for
    backward-compatibility with any ``except RuntimeError`` caller.
    """

    fingerprint: ClassVar[str] = "midi.port.open_failed"


class RealMidiSendError(MidiError, RuntimeError):
    """Raised when a send request cannot be translated safely.

    Member of the unified :class:`~rytm_randomizer.observability.errors.MidiError`
    taxonomy. ``RuntimeError`` is kept as an additional base for
    backward-compatibility with any ``except RuntimeError`` caller.
    """

    fingerprint: ClassVar[str] = "midi.send.failed"


@runtime_checkable
class RealMidiOutputPort(Protocol):
    """Armed output-port contract with mandatory deterministic cleanup."""

    def send(self, message: object) -> None:
        """Transmit one already-validated MIDI message."""
        ...

    def close(self) -> None:
        """Close the physical or fake output port."""
        ...


@runtime_checkable
class RealMidiOutputProvider(Protocol):
    """Neutral output-provider boundary for fake and armed implementations."""

    def list_output_names(self) -> Sequence[str]:
        """Return the currently available output names."""
        ...

    def open_output(self, port_name: str) -> RealMidiOutputPort:
        """Open exactly one named output port."""
        ...


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


def _require_fake_provider(value: object) -> RealMidiPortProvider:
    if not isinstance(value, RealMidiPortProvider):
        raise TypeError("provider must be a fake-only RealMidiPortProvider")
    return value


def _require_real_midi_port_name(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise RealMidiPortError("midi_output_port_required")
    return value


@dataclass(frozen=True)
class RealMidiSendResult:
    """Result for adapter sends through an injected provider."""

    port_name: str
    message_count: int
    sent_real_midi: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


class RealMidiPortProvider:
    """Explicit output-port provider for fake-provider tests.

    This provider does not discover hardware. It only exposes the names and
    fake ports injected by tests or a future explicitly-approved backend.
    """

    def __init__(
        self,
        output_names: Sequence[str] = (),
        ports: Mapping[str, RealMidiOutputPort] | None = None,
    ) -> None:
        self._output_names = tuple(output_names)
        self._ports = dict(ports or {})

    def list_output_names(self) -> tuple[str, ...]:
        return self._output_names

    def open_output(self, port_name: str) -> RealMidiOutputPort:
        if port_name not in self._output_names:
            raise RealMidiPortError(f"unknown_midi_output_port: {port_name}")
        try:
            port = self._ports[port_name]
        except KeyError as exc:
            raise RealMidiPortError(f"unavailable_midi_output_port: {port_name}") from exc
        if not callable(getattr(port, "send", None)) or not callable(getattr(port, "close", None)):
            raise RealMidiPortError(f"invalid_midi_output_port: {port_name}")
        return port


class RealMidiSender:
    """Sender boundary that can be tested with fake output ports only."""

    def __init__(self, provider: RealMidiPortProvider, port_name: str) -> None:
        checked_provider = _require_fake_provider(provider)
        checked_port_name = _require_real_midi_port_name(port_name)
        self._port_name = checked_port_name
        self._port = checked_provider.open_output(checked_port_name)

    @property
    def port_name(self) -> str:
        return self._port_name

    def send_messages(self, messages: Sequence[MidiMessage]) -> RealMidiSendResult:
        translated_messages = [_translate_message(message) for message in messages]
        for translated_message in translated_messages:
            self._port.send(translated_message)
        return RealMidiSendResult(
            port_name=self._port_name,
            message_count=len(translated_messages),
            sent_real_midi=False,
            metadata={"fake_provider_only": True},
        )

    def close(self) -> None:
        """Close the injected output port deterministically."""

        self._port.close()


def _translate_message(message: object) -> Mapping[str, object]:
    if not isinstance(message, MidiMessage):
        raise TypeError("message must be a MidiMessage")
    if message.message_type != "cc":
        raise RealMidiSendError(f"unsupported_midi_message_type: {message.message_type}")
    return {
        "message_type": message.message_type,
        "channel": message.channel,
        "control": message.control,
        "value": message.value,
        "metadata": dict(message.metadata),
    }


def build_real_midi_sender(
    provider: RealMidiPortProvider | None,
    port_name: str,
) -> RealMidiSender:
    """Build a sender only from an explicit provider and port name."""

    if provider is None:
        raise RealMidiDependencyError("real_midi_provider_required")
    return RealMidiSender(provider=provider, port_name=port_name)


__all__ = [
    "RealMidiDependencyError",
    "RealMidiOutputPort",
    "RealMidiOutputProvider",
    "RealMidiPortError",
    "RealMidiPortProvider",
    "RealMidiSendError",
    "RealMidiSendResult",
    "RealMidiSender",
    "build_real_midi_sender",
]
