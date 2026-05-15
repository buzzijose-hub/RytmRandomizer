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
"""

from __future__ import annotations

import time
from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .data import MACHINE_CC
from .observability.logging import get_logger

__all__ = [
    "ApplyStateResult",
    "apply_state",
    "clamp",
    "send_cc",
    "send_machine",
    "send_param",
]


# Module logger for MIDI I/O diagnostic output. Records sit alongside the
# V1.34-parity stdout UI (e.g. "  X: CC42 -> 64"). The log is the
# troubleshooter's grep target -- structured, level-filterable, and JSON-
# shippable -- while stdout remains the operator UI. See
# docs/OBSERVABILITY.md for the structured format and the --debug flag.
_logger = get_logger(__name__)

# A MIDI sender duck-types ``mido.ports.BaseOutput``: anything with ``send``.
Sender = Any
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

    import mido  # noqa: PLC0415 - intentional lazy import for import-safety

    msg = mido.Message(
        "control_change",
        channel=channel,
        control=cc,
        value=value,
    )
    _logger.debug(
        "midi_send cc",
        extra={
            "channel": channel,
            "control": cc,
            "value": value,
            "kind": "midi_send",
        },
    )
    out.send(msg)
    sleep(0.02)


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
