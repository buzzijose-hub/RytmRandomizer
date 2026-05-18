"""Generic ``MockRuntime`` Protocol + ``BaseMockRuntime`` ABC (WS-S6).

A mock runtime renders a mutation plan into a list of inert messages and
delivers them to a :class:`~rytm_randomizer.devices.base.MidiOutbox`
(typically the :class:`rytm_randomizer.mock_midi.MockMidiSender` test
recorder). It is the seam test code uses to capture "what would have been
sent" without touching real MIDI hardware.

Per Gate 6 (PLAN_REQUIREMENTS) the boundary is a ``@runtime_checkable``
``Protocol``; the default :class:`BaseMockRuntime` ABC supplies a
``capture_messages`` that delegates to the device's own
``to_mock_messages`` renderer so most device wrappers only need to
specify which :class:`Device` they target, not re-implement capture
plumbing.
"""

from __future__ import annotations

from abc import ABC
from typing import Any, Protocol, runtime_checkable

from ..devices.base import Device, MidiOutbox


@runtime_checkable
class MockRuntime(Protocol):
    """Capture the message sequence a mutation plan would emit.

    Implementations return a ``list`` of inert messages (typically
    :class:`rytm_randomizer.mock_midi.MidiMessage` instances) that the
    test path can compare byte-identically against a parity fixture.

    Implementations also typically forward each captured message to a
    :class:`~rytm_randomizer.devices.base.MidiOutbox` so the
    :class:`~rytm_randomizer.mock_midi.MockMidiSender` recorder picks
    them up in the order they would be sent on the wire.
    """

    def capture_messages(self, plan: Any) -> list[Any]: ...


class BaseMockRuntime(ABC):  # noqa: B024 - intentional ABC; subclasses override capture_messages
    """Default ``MockRuntime`` that delegates to ``device.to_mock_messages``.

    Subclass and pass the target :class:`Device` to ``__init__``; the
    base class's :meth:`capture_messages` will call
    ``device.to_mock_messages(plan)`` and forward each emitted message
    to the outbox.

    Most device wrappers do not need to subclass this -- the
    :class:`Device` Protocol itself already exposes ``to_mock_messages``
    and the test harness can call it directly. This ABC exists for the
    common case where a device wants a unified "capture + forward"
    helper instead of repeating ``for m in device.to_mock_messages(plan):
    outbox.send(m)`` at every call site.
    """

    def __init__(self, outbox: MidiOutbox) -> None:
        """Store the outbox each captured message will be forwarded to.

        ``outbox`` must satisfy the
        :class:`~rytm_randomizer.devices.base.MidiOutbox` Protocol
        (anything with a ``.send(message)`` method).
        """

        self._outbox: MidiOutbox = outbox

    @property
    def outbox(self) -> MidiOutbox:
        """The :class:`MidiOutbox` captured messages are forwarded to."""

        return self._outbox

    def capture_messages(self, plan: Any, *, device: Device) -> list[Any]:
        """Render ``plan`` through ``device`` and forward to the outbox.

        Returns the list of inert messages (the same value
        ``device.to_mock_messages(plan)`` returned) so the caller can
        also assert against it directly without going through the
        outbox.
        """

        messages = device.to_mock_messages(plan)
        for message in messages:
            self._outbox.send(message)
        return messages
