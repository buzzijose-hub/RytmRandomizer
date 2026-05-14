"""Read-only Packet 8 Pad 4 lane behavior helpers.

This module is a thin backward-compatible shim. The Pad 1-4 lane descriptor
data and behavior were collapsed into the single data-driven
``rytm_randomizer.behavior_pad_lane`` registry; this module simply re-exports
the Pad 4 public API so existing imports keep working.

It models deterministic Pad 4 lane intent without prompt loops, dispatching
commands, opening ports, sending MIDI, or touching hardware.
"""

from __future__ import annotations

from .behavior_pad_lane import (
    DEFERRED_PACKET_8_PAD4_LANE_KEYS,
    PACKET_8A_PAD4_LANE_KEYS,
    PACKET_8B_PAD4_LANE_KEYS,
    PACKET_8C_PAD4_LANE_KEYS,
    Pad4LaneBehaviorResult,
    evaluate_pad4_lane_behavior,
)

__all__ = [
    "DEFERRED_PACKET_8_PAD4_LANE_KEYS",
    "PACKET_8A_PAD4_LANE_KEYS",
    "PACKET_8B_PAD4_LANE_KEYS",
    "PACKET_8C_PAD4_LANE_KEYS",
    "Pad4LaneBehaviorResult",
    "evaluate_pad4_lane_behavior",
]
