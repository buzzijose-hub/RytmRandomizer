"""Read-only Packet 4 scene/group intent behavior helpers.

This module models deterministic scene and group mutation intent without
dispatching commands, executing scenes, opening ports, sending MIDI, or
touching hardware.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from ..commands import GROUP_COMMANDS
from ..scenes import SCENE_COMMANDS
from ._result_fields import empty_metadata

PACKET_4A_SCENE_INTENT_KEYS = tuple(SCENE_COMMANDS)
PACKET_4B_GROUP_MUTATION_INTENT_KEYS = ("X", "D", "I", "4")
PACKET_4C_LANE_AWARE_GROUP_MUTATION_INTENT_KEYS = ("Y", "V", "N")
PACKET_4D_GROUP_ANCHOR_INTENT_KEYS = ("O", "Z")
# Deferral lists, deliberately drained: every key that once sat here has
# graduated to a supported packet above. They are annotated (rather than
# deleted) so a future deferral has an obvious home, and typed so the
# guard branches below read as reachable-when-populated instead of as a
# str-vs-empty-tuple comparison the type checker flags as always False.
DEFERRED_GROUP_MUTATION_KEYS: Final[tuple[str, ...]] = ()
DEFERRED_LANE_AWARE_GROUP_MUTATION_KEYS: Final[tuple[str, ...]] = ()

_FORBIDDEN_EARLY_HARDWARE_ACTIONS = {
    "harder",
    "wild_controlled",
    "wild_maximum",
}
_FORBIDDEN_EARLY_HARDWARE_GROUP_MUTATION_KEYS = {"4"}
_GROUP_MUTATION_INTENT_DETAILS = {
    "X": {
        "mode": "balanced_four_lane",
        "intensity": "balanced",
    },
    "D": {
        "mode": "deeper_four_lane",
        "intensity": "deeper",
    },
    "I": {
        "mode": "intense_controlled_chaos",
        "intensity": "intense",
    },
    "4": {
        "mode": "harder_wild_four_lane",
        "intensity": "wild",
    },
}
_LANE_AWARE_GROUP_MUTATION_INTENT_DETAILS = {
    "Y": {
        "page": "src_morph",
        "mode": "lane_aware_src_morph",
    },
    "V": {
        "page": "filter",
        "mode": "lane_aware_filter",
    },
    "N": {
        "page": "grit",
        "mode": "lane_aware_grit",
    },
}
_GROUP_ANCHOR_INTENT_DETAILS = {
    "O": {
        "anchor_action": "load_group_anchors",
        "reason": "supported_group_anchor_load_intent",
    },
    "Z": {
        "anchor_action": "return_group_anchors",
        "reason": "supported_group_anchor_return_intent",
    },
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
    metadata: Mapping[str, object] = field(default_factory=empty_metadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "display_lines", tuple(self.display_lines))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def evaluate_scene_group_behavior(command_key: str) -> SceneGroupBehaviorResult:
    """Return a passive Packet 4 scene/group behavior result."""

    key = str(command_key)

    if key in PACKET_4A_SCENE_INTENT_KEYS:
        return _accepted_scene_intent_result(key)

    if key in PACKET_4B_GROUP_MUTATION_INTENT_KEYS:
        return _accepted_group_mutation_intent_result(key)

    if key in PACKET_4C_LANE_AWARE_GROUP_MUTATION_INTENT_KEYS:
        return _accepted_lane_aware_group_mutation_intent_result(key)

    if key in PACKET_4D_GROUP_ANCHOR_INTENT_KEYS:
        return _accepted_group_anchor_intent_result(key)

    if (
        key in DEFERRED_GROUP_MUTATION_KEYS
    ):  # pyright: ignore[reportUnnecessaryContains]  # drained deferral list; branch kept as the contract for a future deferral
        return SceneGroupBehaviorResult(
            command_key=key,
            accepted=False,
            reason="deferred_group_mutation_command",
            metadata=_safe_failure_metadata("GROUP_COMMANDS"),
        )

    if (
        key in DEFERRED_LANE_AWARE_GROUP_MUTATION_KEYS
    ):  # pyright: ignore[reportUnnecessaryContains]  # drained deferral list; branch kept as the contract for a future deferral
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


def _accepted_scene_intent_result(command_key: str) -> SceneGroupBehaviorResult:
    scene_metadata = SCENE_COMMANDS[command_key]
    scene_name = str(scene_metadata["name"])
    scene_description = str(scene_metadata["description"])
    scene_action = str(scene_metadata["action"])
    scene_scope = str(scene_metadata["scope"])
    forbidden_early_hardware_scope = scene_action in _FORBIDDEN_EARLY_HARDWARE_ACTIONS

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
            "source_v134_reference_command": scene_metadata["v134_reference_command"],
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


def _accepted_group_mutation_intent_result(command_key: str) -> SceneGroupBehaviorResult:
    group_metadata = GROUP_COMMANDS[command_key]
    label = str(group_metadata["label"])
    command_type = str(group_metadata["type"])
    scope = str(group_metadata["scope"])
    intent_details = _GROUP_MUTATION_INTENT_DETAILS[command_key]
    group_mutation_mode = str(intent_details["mode"])
    mutation_intensity = str(intent_details["intensity"])
    forbidden_early_hardware_scope = command_key in _FORBIDDEN_EARLY_HARDWARE_GROUP_MUTATION_KEYS

    return SceneGroupBehaviorResult(
        command_key=command_key,
        scene_scope=scope,
        behavior_family="scene-group/group-mutation-intent",
        accepted=True,
        reason="supported_group_mutation_intent",
        display_lines=_group_mutation_display_lines(
            command_key,
            label,
            group_mutation_mode,
            scope,
            forbidden_early_hardware_scope,
        ),
        metadata={
            "source": "GROUP_COMMANDS",
            "source_group_command_label": label,
            "source_group_command_type": command_type,
            "source_group_command_scope": scope,
            "source_group_command_executable": group_metadata["executable"],
            "source_v134_reference_command": group_metadata["v134_reference_command"],
            "source_scaffold_only": group_metadata["scaffold_only"],
            "group_mutation_mode": group_mutation_mode,
            "mutation_intensity": mutation_intensity,
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


def _accepted_lane_aware_group_mutation_intent_result(command_key: str) -> SceneGroupBehaviorResult:
    group_metadata = GROUP_COMMANDS[command_key]
    label = str(group_metadata["label"])
    command_type = str(group_metadata["type"])
    scope = str(group_metadata["scope"])
    command_family = group_metadata["command_family"]
    intent_details = _LANE_AWARE_GROUP_MUTATION_INTENT_DETAILS[command_key]
    lane_aware_page = str(intent_details["page"])
    lane_aware_mutation_mode = intent_details["mode"]

    return SceneGroupBehaviorResult(
        command_key=command_key,
        scene_scope=scope,
        behavior_family="scene-group/lane-aware-group-mutation-intent",
        accepted=True,
        reason="supported_lane_aware_group_mutation_intent",
        display_lines=_lane_aware_group_mutation_display_lines(
            command_key,
            label,
            lane_aware_page,
            scope,
        ),
        metadata={
            "source": "GROUP_COMMANDS",
            "source_group_command_label": label,
            "source_group_command_type": command_type,
            "source_group_command_scope": scope,
            "source_group_command_family": command_family,
            "source_group_command_executable": group_metadata["executable"],
            "source_v134_reference_command": group_metadata["v134_reference_command"],
            "source_scaffold_only": group_metadata["scaffold_only"],
            "lane_aware_page": lane_aware_page,
            "lane_aware_mutation_mode": lane_aware_mutation_mode,
            "loads_anchors": False,
            "executes_scene": False,
            "executes_group_mutation": False,
            "dispatches_command": False,
            "mock_only": True,
            "sends_real_midi": False,
            "opens_ports": False,
            "hardware_required": False,
            "active_behavior": False,
            "mutates_runtime_state": False,
        },
    )


def _accepted_group_anchor_intent_result(command_key: str) -> SceneGroupBehaviorResult:
    group_metadata = GROUP_COMMANDS[command_key]
    label = str(group_metadata["label"])
    command_type = str(group_metadata["type"])
    scope = str(group_metadata["scope"])
    intent_details = _GROUP_ANCHOR_INTENT_DETAILS[command_key]
    anchor_action = intent_details["anchor_action"]

    return SceneGroupBehaviorResult(
        command_key=command_key,
        scene_scope=scope,
        behavior_family="scene-group/group-anchor-intent",
        accepted=True,
        reason=intent_details["reason"],
        display_lines=_group_anchor_display_lines(
            command_key,
            label,
            anchor_action,
            scope,
        ),
        metadata={
            "source": "GROUP_COMMANDS",
            "source_group_command_label": label,
            "source_group_command_type": command_type,
            "source_group_command_scope": scope,
            "source_group_command_executable": group_metadata["executable"],
            "source_v134_reference_command": group_metadata["v134_reference_command"],
            "source_scaffold_only": group_metadata["scaffold_only"],
            "anchor_action": anchor_action,
            "loads_anchors": False,
            "executes_scene": False,
            "executes_group_anchor": False,
            "executes_group_mutation": False,
            "dispatches_command": False,
            "mock_only": True,
            "sends_real_midi": False,
            "opens_ports": False,
            "hardware_required": False,
            "active_behavior": False,
            "mutates_runtime_state": False,
        },
    )


def _scene_display_lines(
    command_key: str,
    scene_name: str,
    scene_action: str,
    scene_scope: str,
    forbidden_early_hardware_scope: bool,
) -> tuple[str, ...]:
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


def _group_mutation_display_lines(
    command_key: str,
    label: str,
    group_mutation_mode: str,
    scope: str,
    forbidden_early_hardware_scope: bool,
) -> tuple[str, ...]:
    lines = (
        f"{command_key}: {label}",
        "Read-only group mutation intent.",
        f"Group mutation mode: {group_mutation_mode}",
        f"Group scope: {scope}",
        "No group mutation would execute.",
        "No scene would execute.",
        "No state would change.",
        "No command would dispatch.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )

    if forbidden_early_hardware_scope:
        return (*lines, "Early hardware scope: forbidden.")

    return lines


def _lane_aware_group_mutation_display_lines(
    command_key: str,
    label: str,
    lane_aware_page: str,
    scope: str,
) -> tuple[str, ...]:
    return (
        f"{command_key}: {label}",
        "Read-only lane-aware group mutation intent.",
        f"Lane-aware page: {lane_aware_page}",
        f"Group scope: {scope}",
        "No lane-aware group mutation would execute.",
        "No group mutation would execute.",
        "No scene would execute.",
        "No state would change.",
        "No command would dispatch.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )


def _group_anchor_display_lines(
    command_key: str,
    label: str,
    anchor_action: str,
    scope: str,
) -> tuple[str, ...]:
    return (
        f"{command_key}: {label}",
        "Read-only group anchor intent.",
        f"Group anchor action: {anchor_action}",
        f"Group scope: {scope}",
        "No group anchor load or return would execute.",
        "No group mutation would execute.",
        "No scene would execute.",
        "No state would change.",
        "No command would dispatch.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )


def _safe_failure_metadata(source: str) -> dict[str, object]:
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
    "PACKET_4B_GROUP_MUTATION_INTENT_KEYS",
    "PACKET_4C_LANE_AWARE_GROUP_MUTATION_INTENT_KEYS",
    "PACKET_4D_GROUP_ANCHOR_INTENT_KEYS",
    "SceneGroupBehaviorResult",
    "evaluate_scene_group_behavior",
]
