"""Per-domain runtime state objects for the Analog Rytm randomizer.

This sub-package extracts the mutable module-level globals that the
``rytm_hybrid_randomizer_v134`` monolith historically threaded implicitly
through nearly every function. Each module here owns one domain and exposes a
frozen dataclass plus explicit transition functions: a transition returns a
NEW state object rather than mutating in place.

The monolith keeps plain mutable globals as its live state (so its existing
``global`` / mutation statements stay byte-identical), but initializes those
globals from the default-builders here so this package owns the canonical
default values. Nothing in this package opens ports, sends MIDI, or touches
hardware.
"""

from __future__ import annotations

from . import (
    a4_soft_capture,
    anchor,
    anchor_validation,
    group,
    pad_mode,
    rytm_cc_observe,
    scene,
    selected_isolated_pad_validation,
    selected_target_validation,
    selection,
)

__all__ = [
    "a4_soft_capture",
    "anchor",
    "anchor_validation",
    "group",
    "pad_mode",
    "rytm_cc_observe",
    "scene",
    "selected_isolated_pad_validation",
    "selected_target_validation",
    "selection",
]
