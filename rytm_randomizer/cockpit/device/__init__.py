"""Cockpit device adapter subpackage — mock + real-MIDI wiring (WS-F).

The cockpit talks to a ``DeviceAdapter`` Protocol so the UI never knows
whether it is driving an in-memory mock or a real Analog Rytm MK2 over MIDI.
One adapter is shipped:

* :class:`MockDeviceAdapter` — in-memory state, always-on for development.

There is deliberately **no** real-MIDI adapter. A cockpit session models
its snapshot/history state through the mock adapter whether or not it is
armed; outbound transmit is the exclusive job of the ArmedApply seam
(:mod:`rytm_randomizer.senders.armed_apply`), which owns the single real
output port. An adapter that opened its own port alongside the seam is
precisely the two-handles defect the seam exists to prevent — see
``.claude/rules/live-but-passive-midi.md``.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Device Adapter" for the authoritative shape and
``docs/superpowers/plans/2026-05-23-cockpit-and-profile-model.md`` §3 WS-F
for the workstream contract.
"""

from __future__ import annotations

from .adapter import DeviceAdapter
from .mock import MockDeviceAdapter

__all__ = [
    "DeviceAdapter",
    "MockDeviceAdapter",
]
