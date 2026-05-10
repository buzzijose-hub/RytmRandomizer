"""Read-only Packet 6 Pad 2 lane behavior helpers.

This module models deterministic Pad 2 lane intent without prompt loops,
dispatching commands, opening ports, sending MIDI, or touching hardware.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .commands import COMMANDS, PAD2_COMMANDS


PACKET_6A_PAD2_LANE_KEYS = ("P2B",)
PACKET_6B_PAD2_LANE_KEYS = ("P2H",)
PACKET_6C_PAD2_LANE_KEYS = ("P2C",)
DEFERRED_PACKET_6_PAD2_LANE_KEYS = (
    "P2M",
    "P2F",
    "P2T",
    "P2P",
    "P2G",
    "P2R",
    "P2X",
    "P2Z",
)


@dataclass(frozen=True)
class Pad2LaneBehaviorResult:
    """Immutable read-only result for Packet 6 Pad 2 lane behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "pad2-lane/bd-classic-home-anchor"
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


def evaluate_pad2_lane_behavior(command_key):
    """Return a passive Packet 6 behavior result for a Pad 2 command key."""

    key = str(command_key)

    if key == "P2B":
        return _accepted_p2b_result()
    if key == "P2H":
        return _accepted_p2h_result()
    if key == "P2C":
        return _accepted_p2c_result()

    if key in COMMANDS:
        return _unsupported_result(key)

    return Pad2LaneBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata={
            "source": "unknown",
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


def _accepted_p2b_result():
    metadata = PAD2_COMMANDS["P2B"]
    label = metadata["label"]
    lane_action = "load_pad2_bd_classic_home_anchor"
    anchor_concept = "Pad 2 BD Classic home anchor"

    result_metadata = {
        "source": "PAD2_COMMANDS",
        "command_type": metadata["type"],
        "target_pad": metadata["pad"],
        "lane": "pad_2_secondary_lane",
        "behavior_family": "pad2-lane/bd-classic-home-anchor",
        "lane_action": lane_action,
        "intent_kind": "anchor_load",
        "anchor_concept": anchor_concept,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
    }

    return Pad2LaneBehaviorResult(
        command_key="P2B",
        label=label,
        behavior_family="pad2-lane/bd-classic-home-anchor",
        accepted=True,
        reason="supported_pad2_bd_classic_home_anchor_intent",
        target_pad=2,
        lane="Pad 2 secondary lane",
        lane_action=lane_action,
        intent_kind="anchor_load",
        anchor_concept=anchor_concept,
        display_lines=(
            f"P2B: {label}",
            "Read-only Pad 2 BD Classic home anchor intent.",
            "Target pad: 2",
            "Lane: Pad 2 secondary lane",
            f"Lane action: {lane_action}",
            "Pad 2 BD Classic home anchor dependency is recorded only.",
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


def _accepted_p2h_result():
    metadata = PAD2_COMMANDS["P2H"]
    label = metadata["label"]
    lane_action = "load_pad2_sd_hard_anchor"
    anchor_concept = "Pad 2 SD Hard anchor"

    result_metadata = {
        "source": "PAD2_COMMANDS",
        "command_type": metadata["type"],
        "target_pad": metadata["pad"],
        "lane": "pad_2_secondary_lane",
        "behavior_family": "pad2-lane/sd-hard-anchor",
        "lane_action": lane_action,
        "intent_kind": "anchor_load",
        "anchor_concept": anchor_concept,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
    }

    return Pad2LaneBehaviorResult(
        command_key="P2H",
        label=label,
        behavior_family="pad2-lane/sd-hard-anchor",
        accepted=True,
        reason="supported_pad2_sd_hard_anchor_intent",
        target_pad=2,
        lane="Pad 2 secondary lane",
        lane_action=lane_action,
        intent_kind="anchor_load",
        anchor_concept=anchor_concept,
        display_lines=(
            f"P2H: {label}",
            "Read-only Pad 2 SD Hard anchor intent.",
            "Target pad: 2",
            "Lane: Pad 2 secondary lane",
            f"Lane action: {lane_action}",
            "Pad 2 SD Hard anchor dependency is recorded only.",
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


def _accepted_p2c_result():
    metadata = PAD2_COMMANDS["P2C"]
    label = metadata["label"]
    lane_action = "load_pad2_sd_classic_anchor"
    anchor_concept = "Pad 2 SD Classic anchor"

    result_metadata = {
        "source": "PAD2_COMMANDS",
        "command_type": metadata["type"],
        "target_pad": metadata["pad"],
        "lane": "pad_2_secondary_lane",
        "behavior_family": "pad2-lane/sd-classic-anchor",
        "lane_action": lane_action,
        "intent_kind": "anchor_load",
        "anchor_concept": anchor_concept,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
    }

    return Pad2LaneBehaviorResult(
        command_key="P2C",
        label=label,
        behavior_family="pad2-lane/sd-classic-anchor",
        accepted=True,
        reason="supported_pad2_sd_classic_anchor_intent",
        target_pad=2,
        lane="Pad 2 secondary lane",
        lane_action=lane_action,
        intent_kind="anchor_load",
        anchor_concept=anchor_concept,
        display_lines=(
            f"P2C: {label}",
            "Read-only Pad 2 SD Classic anchor intent.",
            "Target pad: 2",
            "Lane: Pad 2 secondary lane",
            f"Lane action: {lane_action}",
            "Pad 2 SD Classic anchor dependency is recorded only.",
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
    return Pad2LaneBehaviorResult(
        command_key=command_key,
        accepted=False,
        reason="unsupported_pad2_lane_command",
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
    "DEFERRED_PACKET_6_PAD2_LANE_KEYS",
    "PACKET_6A_PAD2_LANE_KEYS",
    "PACKET_6B_PAD2_LANE_KEYS",
    "PACKET_6C_PAD2_LANE_KEYS",
    "Pad2LaneBehaviorResult",
    "evaluate_pad2_lane_behavior",
]
