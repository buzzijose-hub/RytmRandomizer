"""AnalogRytmDevice -- the existing Rytm code surfaced as a Device (WS-S5).

This module is a thin wrapper that exposes the existing
``rytm_randomizer/engines/*`` + ``randomization.py`` + ``data/*`` code
through the :class:`rytm_randomizer.devices.base.Device` protocol. It
serves three purposes:

1. The device registry is non-empty out of the box -- ``get_device("analog_rytm_mk2")``
   resolves to something real, not a stub.
2. The Protocol's surface is exercised against the live Rytm code, so the
   shape is proven before PR #21's ``AnalogFourDevice`` arrives.
3. Future cross-device code (a dual-machine bridge, a CLI that lists
   available devices) has a reference implementation to lean on.

The snapshot decoder / mutation planner / message renderers are
**deliberately minimal** -- they return shape-correct stubs so the Protocol
is satisfied at runtime, but the actual decode + plan + render bodies will
be filled in when PR #21's snapshot work lands and the Rytm side needs
them. Today the live Rytm path goes through ``engines/pad{1-4}.py`` not
through ``Device``; the wrapper is the *forward-compat seam*, not a
replacement for the engine path.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Final

from . import registry
from .base import Device


@dataclass(frozen=True)
class _RytmSnapshot:
    """Stub snapshot type -- placeholder until PR #21's snapshot work lands."""

    raw: bytes
    slot: int


@dataclass(frozen=True)
class _RytmMutationPlan:
    """Stub mutation plan -- placeholder until the snapshot path is wired."""

    snapshot: _RytmSnapshot
    depth: int


# Elektron's 3-byte SysEx manufacturer ID. Documented in the Analog Rytm
# MKII MIDI spec and reused across every Elektron device. NOT secret.
_ELEKTRON_MFR_ID: Final[bytes] = bytes([0x00, 0x20, 0x3C])


class AnalogRytmDevice:
    """``Device`` wrapping the live Rytm code path.

    See module docstring for what's wired today vs. deferred. Protocol
    conformance is what matters; the decode / plan / render bodies
    expand as the snapshot pipeline matures.
    """

    device_id: Final[str] = "analog_rytm_mk2"
    display_name: Final[str] = "Elektron Analog Rytm MKII"
    default_midi_channel: Final[int] = 0
    track_count: Final[int] = 12  # Pads 1-12 (V1.34 currently uses 1-4)
    sysex_manufacturer_id: Final[bytes] = _ELEKTRON_MFR_ID

    def decode_snapshot(self, raw: bytes, slot: int) -> _RytmSnapshot:
        """Decode a SysEx kit dump into the internal snapshot shape.

        Stub: returns the raw + slot wrapped. The real Elektron envelope
        unpacking (7-bit unstuffing, manufacturer-id check, kit-record
        location) will land alongside PR #21's snapshot path.
        """
        return _RytmSnapshot(raw=raw, slot=slot)

    def plan_mutation(self, snapshot: Any, depth: int) -> _RytmMutationPlan:
        """Plan a depth-bounded mutation against the snapshot.

        Stub: returns the snapshot + depth wrapped. The Rytm engines'
        existing mutation logic (in ``engines/pad{1-4}.py`` +
        ``randomization.py``) will be reached for here when the snapshot
        path is wired.
        """
        if not isinstance(snapshot, _RytmSnapshot):
            raise TypeError(
                f"AnalogRytmDevice.plan_mutation expected _RytmSnapshot, got {type(snapshot).__name__}"
            )
        return _RytmMutationPlan(snapshot=snapshot, depth=depth)

    def to_mock_messages(self, plan: Any) -> list[Any]:
        """Render the plan into inert ``MidiMessage`` instances.

        Not yet implemented. The renderer lands when the snapshot path is
        wired; today the live Rytm path captures into a ``MockMidiSender``
        via the engine code (``engines/pad{1-4}.py``), not via this surface.

        Codex review P1: this previously returned ``[]``, which let a caller
        successfully ``plan -> render`` and silently emit zero messages -- a
        false positive (tests could pass while the machine would not move).
        Raising ``NotImplementedError`` makes the unfinished state loud so
        the caller can route to the engines for now, or wait for the wiring.
        """
        if not isinstance(plan, _RytmMutationPlan):
            raise TypeError(
                f"AnalogRytmDevice.to_mock_messages expected _RytmMutationPlan, got {type(plan).__name__}"
            )
        raise NotImplementedError(
            "AnalogRytmDevice.to_mock_messages: snapshot-to-mock rendering is "
            "not yet wired. The live mutation path goes through engines/pad*.py "
            "and captures via MockMidiSender directly; use that surface, or "
            "wait until the snapshot-decoder lands to populate this renderer."
        )

    def to_cc_messages(self, plan: Any) -> Iterable[tuple[int, int, int]]:
        """Render the plan into ``(channel, control, value)`` triples.

        Not yet implemented. The renderer lands when the snapshot path is
        wired; today the live Rytm path sends CCs via ``midi_io.send_cc``
        directly from the engines.

        Codex review P1: previously returned ``()``; see ``to_mock_messages``
        above for the same rationale on why a silent empty return masks an
        unfinished implementation. Raising surfaces the gap.
        """
        if not isinstance(plan, _RytmMutationPlan):
            raise TypeError(
                f"AnalogRytmDevice.to_cc_messages expected _RytmMutationPlan, got {type(plan).__name__}"
            )
        raise NotImplementedError(
            "AnalogRytmDevice.to_cc_messages: snapshot-to-CC rendering is "
            "not yet wired. The live mutation path emits CCs via "
            "midi_io.send_cc from engines/pad*.py; use that surface, or "
            "wait until the snapshot-decoder lands to populate this renderer."
        )


# Register at import time so consumers see a non-empty registry.
registry.register_device(AnalogRytmDevice())


def _assert_protocol_conformance() -> None:
    """Compile-time-ish sanity check: AnalogRytmDevice satisfies Device.

    Called once at module import (it's free) so a structural mismatch is
    caught at import rather than at first ``isinstance(device, Device)``
    call from a consumer.
    """
    if not isinstance(registry.get_device("analog_rytm_mk2"), Device):
        raise AssertionError(  # noqa: S101 - structural-typing invariant
            "AnalogRytmDevice does not conform to Device protocol -- check "
            "the attribute / method surface in rytm_randomizer/devices/base.py."
        )


_assert_protocol_conformance()
