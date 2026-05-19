"""Device protocol + registry for cross-machine support.

The ``devices`` subpackage is the cross-machine abstraction layer added by
WS-S5 (per docs/SIMPLIFICATION_PLAN.md). It declares a single ``Device``
``Protocol`` and an in-memory registry so adding support for a new Elektron
device (e.g. PR #21's Analog Four) is "one new module that registers a
``Device`` instance", not "33 new top-level files that hand-roll the same
contract per device".

The existing Rytm-specific code under ``rytm_randomizer/engines``,
``rytm_randomizer/randomization``, etc. is unchanged. ``AnalogRytmDevice``
is a thin wrapper that re-exposes the existing Rytm operations through the
new Protocol so the registry is non-empty out of the box.
"""

from __future__ import annotations

# Importing concrete device modules triggers their import-time
# ``register_device`` calls so ``get_device("<device_id>")`` resolves out
# of the box. Side-effect import is the documented registry pattern.
from . import analog_four  # noqa: F401 - import for side effect (registration)
from . import analog_rytm  # noqa: F401 - import for side effect (registration)
from .base import Device, MessageRenderer, MidiOutbox, MutationPlanner, SnapshotDecoder
from .registry import all_devices, get_device, register_device

__all__ = [
    "Device",
    "MessageRenderer",
    "MidiOutbox",
    "MutationPlanner",
    "SnapshotDecoder",
    "all_devices",
    "get_device",
    "register_device",
]
