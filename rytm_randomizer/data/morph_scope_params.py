"""Discrete-vs-continuous parameter classification for morph/scope planning.

These are layout facts, not behavior: on the Analog Rytm MK2 most synthesis
parameters are *continuous* (a 0..127 knob whose intermediate values are
musically meaningful), but a handful are *discrete* selectors — a waveform
index, an LFO destination, a machine/filter *type* — where an interpolated
value like 1.5 has no meaning. Morphing and scoped randomization treat the two
classes differently:

* continuous params → linear interpolation / symmetric anchor-relative spread,
* discrete params   → threshold at the midpoint (the nearest endpoint wins).

The set below is the closed roster of discrete selectors observed across the
V1.34 profile registry (``data/profiles.py``). It is name-keyed because the
same selector (e.g. ``"SRC Waveform"``) appears under several machine profiles
and always behaves as a selector regardless of which profile carries it.

This module is leaf-passive: importing it opens no ports, sends no MIDI, and
holds only immutable ``Final`` constants.
"""

from __future__ import annotations

from typing import Final

#: Parameter names whose value is a *selector index*, not a continuous knob.
#: Interpolation across these thresholds at the midpoint instead of blending.
DISCRETE_PARAM_NAMES: Final[frozenset[str]] = frozenset(
    {
        "FLT Type",
        "LFO Destination",
        "LFO Multiplier",
        "LFO Trig Mode",
        "LFO Waveform",
        "SRC Mod Type",
        "SRC Osc 1 Wave",
        "SRC Osc 2 Wave",
        "SRC Waveform",
    }
)


def is_discrete_param(name: str) -> bool:
    """Return True when ``name`` is a discrete selector (threshold-interpolated).

    Every other parameter is treated as continuous (linear-interpolated /
    symmetric anchor spread).
    """

    return name in DISCRETE_PARAM_NAMES


__all__ = [
    "DISCRETE_PARAM_NAMES",
    "is_discrete_param",
]
