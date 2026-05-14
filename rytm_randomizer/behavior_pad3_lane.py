"""Read-only Packet 7 Pad 3 lane behavior helpers.

This module is a thin backward-compatible shim. The Pad 1-4 lane descriptor
data and behavior were collapsed into the single data-driven
``rytm_randomizer.behavior_pad_lane`` registry; this module simply re-exports
the Pad 3 public API so existing imports keep working.

It models deterministic Pad 3 lane intent without prompt loops, dispatching
commands, opening ports, sending MIDI, or touching hardware.
"""

from __future__ import annotations

from .behavior_pad_lane import (
    DEFERRED_PACKET_7_PAD3_LANE_KEYS,
    PACKET_7A_PAD3_LANE_KEYS,
    PACKET_7B_PAD3_LANE_KEYS,
    PACKET_7C_PAD3_LANE_KEYS,
    PACKET_7D_PAD3_LANE_KEYS,
    PACKET_7E_PAD3_LANE_KEYS,
    PACKET_7F_PAD3_LANE_KEYS,
    PACKET_7G_PAD3_LANE_KEYS,
    PACKET_7H_PAD3_LANE_KEYS,
    Pad3LaneBehaviorResult,
    evaluate_pad3_lane_behavior,
)

__all__ = [
    "DEFERRED_PACKET_7_PAD3_LANE_KEYS",
    "PACKET_7A_PAD3_LANE_KEYS",
    "PACKET_7B_PAD3_LANE_KEYS",
    "PACKET_7C_PAD3_LANE_KEYS",
    "PACKET_7D_PAD3_LANE_KEYS",
    "PACKET_7E_PAD3_LANE_KEYS",
    "PACKET_7F_PAD3_LANE_KEYS",
    "PACKET_7G_PAD3_LANE_KEYS",
    "PACKET_7H_PAD3_LANE_KEYS",
    "Pad3LaneBehaviorResult",
    "evaluate_pad3_lane_behavior",
]
