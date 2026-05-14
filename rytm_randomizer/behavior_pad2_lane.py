"""Read-only Packet 6 Pad 2 lane behavior helpers.

This module is a thin backward-compatible shim. The Pad 1-4 lane descriptor
data and behavior were collapsed into the single data-driven
``rytm_randomizer.behavior_pad_lane`` registry; this module simply re-exports
the Pad 2 public API so existing imports keep working.

It models deterministic Pad 2 lane intent without prompt loops, dispatching
commands, opening ports, sending MIDI, or touching hardware.
"""

from __future__ import annotations

from .behavior_pad_lane import (
    DEFERRED_PACKET_6_PAD2_LANE_KEYS,
    PACKET_6A_PAD2_LANE_KEYS,
    PACKET_6B_PAD2_LANE_KEYS,
    PACKET_6C_PAD2_LANE_KEYS,
    PACKET_6D_PAD2_LANE_KEYS,
    PACKET_6E_PAD2_LANE_KEYS,
    PACKET_6F_PAD2_LANE_KEYS,
    PACKET_6G_PAD2_LANE_KEYS,
    PACKET_6H_PAD2_LANE_KEYS,
    PACKET_6I_PAD2_LANE_KEYS,
    PACKET_6J_PAD2_LANE_KEYS,
    Pad2LaneBehaviorResult,
    evaluate_pad2_lane_behavior,
)

__all__ = [
    "DEFERRED_PACKET_6_PAD2_LANE_KEYS",
    "PACKET_6A_PAD2_LANE_KEYS",
    "PACKET_6B_PAD2_LANE_KEYS",
    "PACKET_6C_PAD2_LANE_KEYS",
    "PACKET_6D_PAD2_LANE_KEYS",
    "PACKET_6E_PAD2_LANE_KEYS",
    "PACKET_6F_PAD2_LANE_KEYS",
    "PACKET_6G_PAD2_LANE_KEYS",
    "PACKET_6H_PAD2_LANE_KEYS",
    "PACKET_6I_PAD2_LANE_KEYS",
    "PACKET_6J_PAD2_LANE_KEYS",
    "Pad2LaneBehaviorResult",
    "evaluate_pad2_lane_behavior",
]
