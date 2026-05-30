"""Cockpit device adapter subpackage — mock + real-MIDI wiring (WS-F).

The cockpit talks to a ``DeviceAdapter`` Protocol so the UI never knows
whether it is driving an in-memory mock or a real Analog Rytm MK2 over MIDI.
Two adapters are shipped:

* :class:`MockDeviceAdapter` — in-memory state, always-on for development.
* :class:`RealMidiDeviceAdapter` — wraps the project's existing
  :mod:`rytm_randomizer.mido_provider` + :mod:`rytm_randomizer.real_midi_adapter`
  boundary; only constructed when the operator passes ``--arm``. ``mido`` is
  imported lazily inside methods, never at module top — see
  ``.claude/rules/architecture.md`` rule 9.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Device Adapter" for the authoritative shape and
``docs/superpowers/plans/2026-05-23-cockpit-and-profile-model.md`` §3 WS-F
for the workstream contract.
"""

from __future__ import annotations

from .adapter import DeviceAdapter
from .mock import MockDeviceAdapter
from .real import RealMidiDeviceAdapter

__all__ = [
    "DeviceAdapter",
    "MockDeviceAdapter",
    "RealMidiDeviceAdapter",
]
