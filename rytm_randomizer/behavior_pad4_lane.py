"""Read-only Packet 8 Pad 4 lane behavior helpers.

This module models deterministic Pad 4 lane intent without prompt loops,
dispatching commands, opening ports, sending MIDI, or touching hardware.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .commands import COMMANDS, PAD4_COMMANDS


PACKET_8A_PAD4_LANE_KEYS = ("P4A",)
DEFERRED_PACKET_8_PAD4_LANE_KEYS = ("P4R", "P4X", "P4M")


@dataclass(frozen=True)
class Pad4LaneBehaviorResult:
    """Immutable read-only result for Packet 8 Pad 4 lane behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "pad4-lane/bd-acoustic-body-accent-home-anchor"
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


def evaluate_pad4_lane_behavior(command_key):
    """Return a passive Packet 8 behavior result for a Pad 4 command key."""

    key = str(command_key)

    if key == "P4A":
        return _accepted_p4a_result()

    if key in COMMANDS:
        return _unsupported_result(key)

    return Pad4LaneBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata={
            "source": "unknown",
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


def _accepted_p4a_result():
    metadata = PAD4_COMMANDS["P4A"]
    label = metadata["label"]
    lane_action = "return_pad4_bd_acoustic_body_accent_home_anchor"
    anchor_concept = "Pad 4 BD Acoustic body/accent home anchor"

    result_metadata = {
        "source": "PAD4_COMMANDS",
        "command_type": metadata["type"],
        "target_pad": metadata["pad"],
        "lane": "pad_4_bd_acoustic_lane",
        "behavior_family": "pad4-lane/bd-acoustic-body-accent-home-anchor",
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

    return Pad4LaneBehaviorResult(
        command_key="P4A",
        label=label,
        behavior_family="pad4-lane/bd-acoustic-body-accent-home-anchor",
        accepted=True,
        reason="supported_pad4_bd_acoustic_home_anchor_intent",
        target_pad=4,
        lane="Pad 4 BD Acoustic lane",
        lane_action=lane_action,
        intent_kind="anchor_return",
        anchor_concept=anchor_concept,
        display_lines=(
            f"P4A: {label}",
            "Read-only Pad 4 BD Acoustic body/accent home anchor intent.",
            "Target pad: 4",
            "Lane: Pad 4 BD Acoustic lane",
            f"Lane action: {lane_action}",
            "Pad 4 BD Acoustic body/accent home anchor dependency is recorded only.",
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
    return Pad4LaneBehaviorResult(
        command_key=command_key,
        accepted=False,
        reason="unsupported_packet_8_pad4_lane_key",
        metadata={
            "source": "COMMANDS",
            "mock_only": True,
            "sends_real_midi": False,
            "opens_ports": False,
            "hardware_required": False,
            "active_behavior": False,
            "mutates_runtime_state": False,
            "dispatches_command": False,
        },
    )
