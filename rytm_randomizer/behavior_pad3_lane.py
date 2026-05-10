"""Read-only Packet 7 Pad 3 lane behavior helpers.

This module models deterministic Pad 3 lane intent without prompt loops,
dispatching commands, opening ports, sending MIDI, or touching hardware.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .commands import COMMANDS, PAD3_COMMANDS


PACKET_7A_PAD3_LANE_KEYS = ("P3A",)
DEFERRED_PACKET_7_PAD3_LANE_KEYS = (
    "P3M",
    "SW",
    "SL",
    "SB",
    "SX",
    "SA",
    "P3R",
    "P3X",
)


@dataclass(frozen=True)
class Pad3LaneBehaviorResult:
    """Immutable read-only result for Packet 7 Pad 3 lane behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "pad3-lane/sy-raw-mid-bass-home-anchor"
    accepted: bool = False
    reason: str = "not_evaluated"
    target_pad: int | None = None
    lane: str = ""
    lane_action: str = ""
    intent_kind: str = ""
    anchor_concept: str = ""
    display_lines: tuple[str, ...] = ()
    state_changed: bool = False
    prompt_required: bool = False
    dispatches_command: bool = False
    executes_command: bool = False
    mutates_lane_state: bool = False
    sends_real_midi: bool = False
    opens_ports: bool = False
    hardware_required: bool = False
    active_behavior: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "display_lines", tuple(self.display_lines))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def evaluate_pad3_lane_behavior(command_key):
    """Return a passive Packet 7 behavior result for a Pad 3 command key."""

    key = str(command_key)

    if key == "P3A":
        return _accepted_p3a_result()

    if key in COMMANDS:
        return _unsupported_result(key)

    return Pad3LaneBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata={
            "source": "unknown",
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


def _accepted_p3a_result():
    metadata = PAD3_COMMANDS["P3A"]
    label = metadata["label"]
    lane_action = "return_pad3_sy_raw_mid_bass_home_anchor"
    anchor_concept = "Pad 3 SY Raw Mid Bass home anchor"

    result_metadata = {
        "source": "PAD3_COMMANDS",
        "command_type": metadata["type"],
        "target_pad": metadata["pad"],
        "lane": "pad_3_sy_raw_lane",
        "behavior_family": "pad3-lane/sy-raw-mid-bass-home-anchor",
        "lane_action": lane_action,
        "intent_kind": "anchor_return",
        "anchor_concept": anchor_concept,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
    }

    return Pad3LaneBehaviorResult(
        command_key="P3A",
        label=label,
        behavior_family="pad3-lane/sy-raw-mid-bass-home-anchor",
        accepted=True,
        reason="supported_pad3_sy_raw_mid_bass_home_anchor_intent",
        target_pad=3,
        lane="Pad 3 SY Raw lane",
        lane_action=lane_action,
        intent_kind="anchor_return",
        anchor_concept=anchor_concept,
        display_lines=(
            f"P3A: {label}",
            "Read-only Pad 3 SY Raw Mid Bass home anchor intent.",
            "Target pad: 3",
            "Lane: Pad 3 SY Raw lane",
            f"Lane action: {lane_action}",
            "Pad 3 SY Raw Mid Bass home anchor dependency is recorded only.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No lane state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
        metadata=result_metadata,
    )


def _unsupported_result(command_key):
    return Pad3LaneBehaviorResult(
        command_key=command_key,
        accepted=False,
        reason="unsupported_packet_7_pad3_lane_key",
        metadata={
            "source": "COMMANDS",
            "mock_only": True,
            "sends_real_midi": False,
            "opens_ports": False,
            "hardware_required": False,
            "active_behavior": False,
        },
    )


__all__ = [
    "DEFERRED_PACKET_7_PAD3_LANE_KEYS",
    "PACKET_7A_PAD3_LANE_KEYS",
    "Pad3LaneBehaviorResult",
    "evaluate_pad3_lane_behavior",
]
