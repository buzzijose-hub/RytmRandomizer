"""Read-only Packet 5A Pad 1 current-engine lane behavior helpers.

This module models deterministic Pad 1 lane intent without prompt loops,
dispatching commands, opening ports, sending MIDI, or touching hardware.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .commands import COMMANDS, PAD1_COMMANDS


PACKET_5A_PAD1_CURRENT_ENGINE_KEYS = ("BR", "BM")
DEFERRED_PACKET_5_PAD1_LANE_KEYS = (
    "FT",
    "FK",
    "FG",
    "FZ",
    "BP",
    "PT",
    "PK",
    "PX",
    "PBH",
    "BI",
    "ST",
    "SK",
    "SC",
    "SBH",
)

_LANE_ACTIONS = {
    "BR": "rotate_profiled_bd_engine",
    "BM": "safe_current_engine_mutation",
}

_DEPTH_DEPENDENCIES = {
    "BR": "",
    "BM": "future_safe_mutation_depth",
}

_REQUIRES_DEPTH_SELECTION = {
    "BR": False,
    "BM": True,
}


@dataclass(frozen=True)
class Pad1LaneBehaviorResult:
    """Immutable read-only result for Packet 5A Pad 1 lane behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "pad1-lane/current-bd-engine"
    accepted: bool = False
    reason: str = "not_evaluated"
    target_pad: int | None = None
    lane: str = ""
    lane_action: str = ""
    engine_dependency: str = ""
    depth_dependency: str = ""
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


def evaluate_pad1_lane_behavior(command_key):
    """Return a passive Packet 5A Pad 1 current-engine lane behavior result."""

    key = str(command_key)

    if key in PACKET_5A_PAD1_CURRENT_ENGINE_KEYS:
        return _accepted_pad1_lane_result(key)

    if key in DEFERRED_PACKET_5_PAD1_LANE_KEYS:
        return Pad1LaneBehaviorResult(
            command_key=key,
            accepted=False,
            reason="deferred_pad1_lane_command",
            metadata=_safe_failure_metadata("PAD1_COMMANDS"),
        )

    if key in COMMANDS:
        return Pad1LaneBehaviorResult(
            command_key=key,
            accepted=False,
            reason="unsupported_pad1_lane_command",
            metadata=_safe_failure_metadata("COMMANDS"),
        )

    return Pad1LaneBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata=_safe_failure_metadata("unknown"),
    )


def _accepted_pad1_lane_result(command_key):
    command_metadata = PAD1_COMMANDS[command_key]
    label = command_metadata["label"]
    target_pad = command_metadata["pad"]
    lane_action = _LANE_ACTIONS[command_key]
    depth_dependency = _DEPTH_DEPENDENCIES[command_key]
    requires_depth_selection = _REQUIRES_DEPTH_SELECTION[command_key]

    display_lines = (
        f"{command_key}: {label}",
        "Read-only Pad 1 current-engine lane intent.",
        f"Target pad: {target_pad}",
        "Lane: Pad 1 BD engine",
        f"Lane action: {lane_action}",
        "Current-engine dependency is recorded only.",
        *_depth_display_lines(depth_dependency),
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )

    return Pad1LaneBehaviorResult(
        command_key=command_key,
        label=label,
        accepted=True,
        reason="supported_pad1_current_engine_lane_intent",
        target_pad=target_pad,
        lane="Pad 1 BD engine",
        lane_action=lane_action,
        engine_dependency="current_pad1_bd_engine_state",
        depth_dependency=depth_dependency,
        display_lines=display_lines,
        metadata={
            "source": "PAD1_COMMANDS",
            "source_command_type": command_metadata["type"],
            "source_command_scope": command_metadata["scope"],
            "source_v134_reference_command": command_metadata[
                "v134_reference_command"
            ],
            "source_scaffold_only": command_metadata["scaffold_only"],
            "target_pad": target_pad,
            "lane": "pad_1_bd_engine",
            "lane_action": lane_action,
            "requires_current_engine_state": True,
            "requires_depth_selection": requires_depth_selection,
            "mock_only": True,
            "sends_real_midi": False,
            "opens_ports": False,
            "hardware_required": False,
            "active_behavior": False,
            "mutates_runtime_state": False,
            "dispatches_command": False,
            "executes_command": False,
        },
    )


def _depth_display_lines(depth_dependency):
    if not depth_dependency:
        return ()

    return ("Future safe mutation depth is recorded only.",)


def _safe_failure_metadata(source):
    return {
        "source": source,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
        "executes_command": False,
    }


__all__ = [
    "DEFERRED_PACKET_5_PAD1_LANE_KEYS",
    "PACKET_5A_PAD1_CURRENT_ENGINE_KEYS",
    "Pad1LaneBehaviorResult",
    "evaluate_pad1_lane_behavior",
]
