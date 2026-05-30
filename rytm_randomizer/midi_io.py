"""Leaf-level MIDI I/O primitives extracted from the V1.34 monolith.

This module holds the small, low-level functions that build and send MIDI
control-change messages and apply parameter states to a profile. They were
previously module-level functions in ``rytm_hybrid_randomizer_v134.py`` that
reached for module globals (``out``, ``channel``, ``active_profile`` and the
mutable ``anchor_state`` / ``current_state`` / ``previous_state``).

Here the dependencies are *injected* instead of global:

* the MIDI ``out`` sender is always a parameter -- never a global,
* the MIDI ``channel`` defaults to ``0`` but can be overridden,
* the ``sleep`` callable is injectable so tests need not really wait,
* the active ``profile`` dict is passed in,
* mutable state (anchor / current / previous) is passed in and the new state
  is *returned* via :class:`ApplyStateResult` rather than mutated in place.

Import-safety: ``mido`` is imported lazily inside :func:`send_cc` only, so
``import rytm_randomizer.midi_io`` opens no ports and pulls in no MIDI library.
The NRPN helper delegates to :func:`send_cc`, preserving that same lazy
boundary.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any, Callable, Protocol, runtime_checkable

from .data import MACHINE_CC
from .observability.logging import get_logger

__all__ = [
    "ApplyStateResult",
    "MidiSender",
    "Sender",
    "apply_state",
    "clamp",
    "send_cc",
    "send_machine",
    "send_nrpn",
    "send_param",
]


# Module logger for MIDI I/O diagnostic output. Records sit alongside the
# V1.34-parity stdout UI (e.g. "  X: CC42 -> 64"). The log is the
# troubleshooter's grep target -- structured, level-filterable, and JSON-
# shippable -- while stdout remains the operator UI. See
# docs/OBSERVABILITY.md for the structured format and the --debug flag.
_logger = get_logger(__name__)


@runtime_checkable
class MidiSender(Protocol):
    """The minimum sender contract: anything with ``send(message)`` works.

    Satisfied structurally by:

    * :class:`mido.ports.BaseOutput` (hardware path via the lazy ``import mido``),
    * :class:`rytm_randomizer.mock_midi.MockMidiSender` (in-process tests).

    NOT satisfied (by design):

    * :class:`rytm_randomizer.real_midi_adapter.RealMidiSender` — exposes
      ``send_messages(Sequence[MidiMessage])`` instead of bare ``send(message)``.
      RealMidiSender is the parity-API wrapper documented in
      ``docs/ARCHITECTURE.md`` §8; it lives at a different layer (it consumes
      a port provider, not a raw out-port) and is not in the engine ->
      ``midi_io.send_cc(out, ...)`` -> ``out.send`` critical path.

    Runtime-checkable because :func:`send_cc` switches on
    ``isinstance(out, MockMidiSender)`` to record an inert
    :class:`~rytm_randomizer.mock_midi.MidiMessage` instead of constructing a
    real ``mido.Message``. A ``Protocol`` (not an ABC) is the right shape here
    because the V1.34 codebase never owned the ``mido.ports.BaseOutput`` class
    definition; structural typing is the only way to admit all three
    implementations without monkey-patching.

    The Protocol's surface is deliberately the minimum that callers need
    (``send(message)``). The actual validation of the message shape happens
    inside :meth:`rytm_randomizer.real_midi_adapter.RealMidiSender.send_messages`
    via :class:`RealMidiSendError`; the runtime-checkable nature here only
    decides which of the two branches in :func:`send_cc` to take.
    """

    def send(self, message: object) -> None: ...


# Canonical re-export. Every consumer (engines/, group_runner, shell,
# randomization) imports `Sender` from this module. Prior to WS-S1 each
# consumer had its own `Sender = Any` line; that escape hatch is gone.
Sender = MidiSender
# A sleep callable: takes a duration in seconds, returns nothing.
SleepFunc = Callable[[float], Any]
# A profile is the canonical V1.34 profile dict from ``rytm_randomizer.data``.
Profile = Mapping[str, Any]


def clamp(value: int, low: int, high: int) -> int:
    """Clamp ``value`` into the inclusive ``[low, high]`` range."""

    return max(low, min(high, value))


def send_cc(
    out: Sender,
    cc: int,
    value: int,
    *,
    channel: int = 0,
    sleep: SleepFunc = time.sleep,
) -> None:
    """Build a control-change message and send it through ``out``.

    Mirrors the monolith's ``send_cc``: a real ``mido`` message is constructed
    and sent, followed by a short settle delay. ``mido`` is imported lazily so
    importing this module stays inert.

    Every CC is also logged at ``DEBUG`` level under the structured field
    set ``channel`` / ``control`` / ``value`` so a troubleshooter running
    ``python -m rytm_randomizer.app --arm --debug`` can ``grep midi_send``
    their stderr log and reconstruct the exact wire-level stream the
    operator just produced. The mock-sender path already records the
    messages on the ``MockMidiSender``; the real path now leaves the same
    breadcrumb in the log.
    """

    _logger.debug(
        "midi_send cc",
        extra={
            "channel": channel,
            "control": cc,
            "value": value,
            "kind": "midi_send",
        },
    )

    from .observability.metrics import (  # noqa: PLC0415 - lazy import — keep midi_io/engines import-surface clean
        get_metrics,
    )

    get_metrics().record_cc_sent(channel)

    from .mock_midi import (  # noqa: PLC0415 - lazy import keeps midi_io import-safe; mock_midi has no mido dependency.
        MidiMessage,
        MockMidiSender,
    )

    if isinstance(out, MockMidiSender):
        out.send(
            MidiMessage(
                message_type="control_change",
                channel=channel,
                control=cc,
                value=value,
            )
        )
        sleep(0.02)
        return

    import mido  # noqa: PLC0415 - intentional lazy import for import-safety

    msg = mido.Message(
        "control_change",
        channel=channel,
        control=cc,
        value=value,
    )
    out.send(msg)
    sleep(0.02)


def send_nrpn(
    out: Sender,
    nrpn_msb: int,
    nrpn_lsb: int,
    value_msb: int,
    *,
    value_lsb: int | None = None,
    channel: int = 0,
    sleep: SleepFunc = time.sleep,
) -> None:
    """Send one NRPN parameter update as control-change messages.

    The standard NRPN address sequence is CC99 (parameter MSB), CC98
    (parameter LSB), then CC6 (Data Entry MSB). When a fine value is supplied,
    CC38 (Data Entry LSB) follows as the optional 14-bit data component.
    """

    send_cc(out, 99, nrpn_msb, channel=channel, sleep=sleep)
    send_cc(out, 98, nrpn_lsb, channel=channel, sleep=sleep)
    send_cc(out, 6, value_msb, channel=channel, sleep=sleep)
    if value_lsb is not None:
        send_cc(out, 38, value_lsb, channel=channel, sleep=sleep)


def send_machine(
    out: Sender,
    profile: Profile,
    *,
    channel: int = 0,
    sleep: SleepFunc = time.sleep,
) -> None:
    """Switch the Rytm machine to ``profile``'s machine value via CC15."""

    value = profile["machine_value"]
    name = profile["name"]

    print(f"\nSwitching Rytm machine to {name}:")
    send_cc(out, MACHINE_CC, value, channel=channel, sleep=sleep)
    print(f"  Machine CC15 -> {value}")
    sleep(0.40)


def send_param(
    out: Sender,
    profile: Profile,
    name: str,
    value: int,
    *,
    channel: int = 0,
    sleep: SleepFunc = time.sleep,
) -> None:
    """Send a named parameter for ``profile`` by resolving its CC number."""

    cc = profile["params"][name]
    send_cc(out, cc, value, channel=channel, sleep=sleep)
    print(f"  {name}: CC{cc} -> {value}")


@dataclass(frozen=True)
class ApplyStateResult:
    """Outcome of :func:`apply_state`.

    ``applied`` is ``False`` when no profile was active (the monolith's
    ``require_profile`` guard failed). The three state mappings are the
    post-call values the caller should write back to its own state holders.
    """

    applied: bool
    anchor_state: Mapping[str, int]
    current_state: Mapping[str, int]
    previous_state: Mapping[str, int] | None


def apply_state(
    out: Sender,
    profile: Profile | None,
    state: Mapping[str, int],
    label: str,
    *,
    anchor_state: Mapping[str, int],
    current_state: Mapping[str, int],
    previous_state: Mapping[str, int] | None,
    set_anchor: bool = False,
    switch_machine_first: bool = False,
    channel: int = 0,
    sleep: SleepFunc = time.sleep,
) -> ApplyStateResult:
    """Send every in-range parameter of ``state`` in the profile's order.

    State is taken as input and the updated state is returned via
    :class:`ApplyStateResult`; nothing global is mutated. When ``set_anchor``
    is set, ``profile["anchor"]`` is updated in place to match the monolith.
    """

    if profile is None:
        print("\nSelect a profile first with P.")
        return ApplyStateResult(False, anchor_state, current_state, previous_state)

    if switch_machine_first:
        send_machine(out, profile, channel=channel, sleep=sleep)

    print(f"\n{label}:")

    new_previous = previous_state
    if current_state:
        new_previous = dict(current_state)

    for name in profile["order"]:
        if name in state:
            send_param(out, profile, name, state[name], channel=channel, sleep=sleep)

    new_current = dict(state)
    new_anchor: Mapping[str, int] = anchor_state

    if set_anchor:
        new_anchor = dict(state)
        # Match the monolith: the active profile's anchor is updated in place.
        if isinstance(profile, MutableMapping):
            profile["anchor"] = dict(state)
        print("  Anchor updated.")

    return ApplyStateResult(True, new_anchor, new_current, new_previous)
