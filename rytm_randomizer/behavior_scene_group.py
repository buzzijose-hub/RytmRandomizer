"""Read-only Packet 4A scene/group intent behavior helpers.

This module models deterministic scene intent without dispatching commands,
executing scenes, opening ports, sending MIDI, or touching hardware.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .commands import GROUP_COMMANDS
from .scenes import SCENE_COMMANDS


PACKET_4A_SCENE_INTENT_KEYS = tuple(SCENE_COMMANDS)
DEFERRED_GROUP_MUTATION_KEYS = ("X", "D", "I", "4")
DEFERRED_LANE_AWARE_GROUP_MUTATION_KEYS = ("Y", "V", "N")

_FORBIDDEN_EARLY_HARDWARE_ACTIONS = {
    "harder",
    "wild_controlled",
    "wild_maximum",
}


@dataclass(frozen=True)
class SceneGroupBehaviorResult:
    """Immutable read-only result for Packet 4 scene/group intent behavior."""

    command_key: str
    scene_name: str = ""
    scene_description: str = ""
    scene_action: str = ""
    scene_scope: str = ""
    behavior_family: str = "scene-group/scene-intent"
    accepted: bool = False
    reason: str = "not_evaluated"
    loads_anchors: bool = False
    display_lines: tuple[str, ...] = ()
    state_changed: bool = False
    prompt_required: bool = False
    dispatches_command: bool = False
    executes_scene: bool = False
    executes_group_mutation: bool = False
    sends_real_midi: bool = False
    opens_ports: bool = False
    hardware_required: bool = False
    active_behavior: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "display_lines", tuple(self.display_lines))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def evaluate_scene_group_behavior(command_key):
    """Return a passive Packet 4 scene/group behavior result."""

    key = str(command_key)

    if key in PACKET_4A_SCENE_INTENT_KEYS:
        return _accepted_scene_intent_result(key)

    if key in DEFERRED_GROUP_MUTATION_KEYS:
        return SceneGroupBehaviorResult(
            command_key=key,
            accepted=False,
            reason="deferred_group_mutation_command",
            metadata=_safe_failure_metadata("GROUP_COMMANDS"),
        )

    if key in DEFERRED_LANE_AWARE_GROUP_MUTATION_KEYS:
        return SceneGroupBehaviorResult(
            command_key=key,
            accepted=False,
            reason="deferred_lane_aware_group_mutation_command",
            metadata=_safe_failure_metadata("GROUP_COMMANDS"),
        )

    if key in GROUP_COMMANDS:
        return SceneGroupBehaviorResult(
            command_key=key,
            accepted=False,
            reason="unsupported_scene_group_command",
            metadata=_safe_failure_metadata("GROUP_COMMANDS"),
        )

    return SceneGroupBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata=_safe_failure_metadata("unknown"),
    )


def _accepted_scene_intent_result(command_key):
    scene_metadata = SCENE_COMMANDS[command_key]
    scene_name = scene_metadata["name"]
    scene_description = scene_metadata["description"]
    scene_action = scene_metadata["action"]
    scene_scope = scene_metadata["scope"]
    forbidden_early_hardware_scope = (
        scene_action in _FORBIDDEN_EARLY_HARDWARE_ACTIONS
    )

    return SceneGroupBehaviorResult(
        command_key=command_key,
        scene_name=scene_name,
        scene_description=scene_description,
        scene_action=scene_action,
        scene_scope=scene_scope,
        accepted=True,
        reason="supported_scene_intent",
        display_lines=_scene_display_lines(
            command_key,
            scene_name,
            scene_action,
            scene_scope,
            forbidden_early_hardware_scope,
        ),
        metadata={
            "source": "SCENE_COMMANDS",
            "source_scene_name": scene_name,
            "source_scene_description": scene_description,
            "source_scene_action": scene_action,
            "source_scene_scope": scene_scope,
            "source_scene_executable": scene_metadata["executable"],
            "source_v134_reference_command": scene_metadata[
                "v134_reference_command"
            ],
            "source_scaffold_only": scene_metadata["scaffold_only"],
            "loads_anchors": False,
            "executes_scene": False,
            "executes_group_mutation": False,
            "dispatches_command": False,
            "forbidden_early_hardware_scope": forbidden_early_hardware_scope,
            "mock_only": True,
            "sends_real_midi": False,
            "opens_ports": False,
            "hardware_required": False,
            "active_behavior": False,
            "mutates_runtime_state": False,
        },
    )


def _scene_display_lines(
    command_key,
    scene_name,
    scene_action,
    scene_scope,
    forbidden_early_hardware_scope,
):
    lines = (
        f"{command_key}: {scene_name}",
        "Read-only scene intent.",
        f"Scene action: {scene_action}",
        f"Scene scope: {scene_scope}",
        "No scene would execute.",
        "No anchors would load.",
        "No state would change.",
        "No command would dispatch.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )

    if forbidden_early_hardware_scope:
        return (*lines, "Early hardware scope: forbidden.")

    return lines


def _safe_failure_metadata(source):
    return {
        "source": source,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "executes_scene": False,
        "executes_group_mutation": False,
        "dispatches_command": False,
    }


__all__ = [
    "DEFERRED_GROUP_MUTATION_KEYS",
    "DEFERRED_LANE_AWARE_GROUP_MUTATION_KEYS",
    "PACKET_4A_SCENE_INTENT_KEYS",
    "SceneGroupBehaviorResult",
    "evaluate_scene_group_behavior",
]
