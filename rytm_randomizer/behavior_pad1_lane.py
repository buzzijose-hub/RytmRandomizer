"""Read-only Packet 5 Pad 1 lane behavior helpers.

This module is a thin backward-compatible shim. The Pad 1-4 lane descriptor
data and behavior were collapsed into the single data-driven
``rytm_randomizer.behavior_pad_lane`` registry; this module simply re-exports
the Pad 1 public API so existing imports keep working.

It models deterministic Pad 1 lane intent without prompt loops, dispatching
commands, opening ports, sending MIDI, or touching hardware.
"""

from __future__ import annotations

from .behavior_pad_lane import (
    DEFERRED_PACKET_5_PAD1_LANE_KEYS,
    PACKET_5A_PAD1_CURRENT_ENGINE_KEYS,
    PACKET_5B_PAD1_BD_FM_KEYS,
    PACKET_5C_PAD1_BD_PLASTIC_KEYS,
    PACKET_5D_PAD1_BD_SILKY_KEYS,
    PACKET_5E_PAD1_BD_ACOUSTIC_KEYS,
    Pad1LaneBehaviorResult,
    Pad1LaneStateDescriptor,
    describe_pad1_lane_state,
    evaluate_pad1_lane_behavior,
)

__all__ = [
    "DEFERRED_PACKET_5_PAD1_LANE_KEYS",
    "PACKET_5A_PAD1_CURRENT_ENGINE_KEYS",
    "PACKET_5B_PAD1_BD_FM_KEYS",
    "PACKET_5C_PAD1_BD_PLASTIC_KEYS",
    "PACKET_5D_PAD1_BD_SILKY_KEYS",
    "PACKET_5E_PAD1_BD_ACOUSTIC_KEYS",
    "Pad1LaneBehaviorResult",
    "Pad1LaneStateDescriptor",
    "describe_pad1_lane_state",
    "evaluate_pad1_lane_behavior",
]
