"""Read-only Packet 5 Pad 1 lane behavior helpers.

This module models deterministic Pad 1 lane intent without prompt loops,
dispatching commands, opening ports, sending MIDI, or touching hardware.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .commands import COMMANDS, PAD1_COMMANDS


PACKET_5A_PAD1_CURRENT_ENGINE_KEYS = ("BR", "BM")
PACKET_5B_PAD1_BD_FM_KEYS = ("FT", "FK", "FG", "FZ")
PACKET_5C_PAD1_BD_PLASTIC_KEYS = ("BP", "PT", "PK", "PX", "PBH")
DEFERRED_PACKET_5_PAD1_LANE_KEYS = (
    "BI",
    "ST",
    "SK",
    "SC",
    "SBH",
)

_LANE_ACTIONS = {
    "BR": "rotate_profiled_bd_engine",
    "BM": "safe_current_engine_mutation",
    "FT": "bd_fm_tone_fm_discovery",
    "FK": "bd_fm_kick_body_discovery",
    "FG": "bd_fm_grit_discovery",
    "FZ": "return_bd_fm_to_anchor",
    "BP": "load_bd_plastic_profiled_anchor",
    "PT": "bd_plastic_tone_modulation_discovery",
    "PK": "bd_plastic_kick_body_discovery",
    "PX": "bd_plastic_rubber_experimental_discovery",
    "PBH": "return_bd_plastic_to_anchor",
}

_DEPTH_DEPENDENCIES = {
    "BR": "",
    "BM": "future_safe_mutation_depth",
    "FT": "future_bd_fm_discovery_depth",
    "FK": "future_bd_fm_discovery_depth",
    "FG": "future_bd_fm_discovery_depth",
    "FZ": "",
    "BP": "",
    "PT": "future_bd_plastic_discovery_depth",
    "PK": "future_bd_plastic_discovery_depth",
    "PX": "future_bd_plastic_discovery_depth",
    "PBH": "",
}

_REQUIRES_DEPTH_SELECTION = {
    "BR": False,
    "BM": True,
    "FT": True,
    "FK": True,
    "FG": True,
    "FZ": False,
    "BP": False,
    "PT": True,
    "PK": True,
    "PX": True,
    "PBH": False,
}

_BEHAVIOR_FAMILIES = {
    "BR": "pad1-lane/current-bd-engine",
    "BM": "pad1-lane/current-bd-engine",
    "FT": "pad1-lane/bd-fm-discovery",
    "FK": "pad1-lane/bd-fm-discovery",
    "FG": "pad1-lane/bd-fm-discovery",
    "FZ": "pad1-lane/bd-fm-anchor-return",
    "BP": "pad1-lane/bd-plastic-anchor-load",
    "PT": "pad1-lane/bd-plastic-discovery",
    "PK": "pad1-lane/bd-plastic-discovery",
    "PX": "pad1-lane/bd-plastic-discovery",
    "PBH": "pad1-lane/bd-plastic-anchor-return",
}

_REASONS = {
    "BR": "supported_pad1_current_engine_lane_intent",
    "BM": "supported_pad1_current_engine_lane_intent",
    "FT": "supported_pad1_bd_fm_discovery_intent",
    "FK": "supported_pad1_bd_fm_discovery_intent",
    "FG": "supported_pad1_bd_fm_discovery_intent",
    "FZ": "supported_pad1_bd_fm_anchor_return_intent",
    "BP": "supported_pad1_bd_plastic_anchor_load_intent",
    "PT": "supported_pad1_bd_plastic_discovery_intent",
    "PK": "supported_pad1_bd_plastic_discovery_intent",
    "PX": "supported_pad1_bd_plastic_discovery_intent",
    "PBH": "supported_pad1_bd_plastic_anchor_return_intent",
}

_LANES = {
    "BR": "Pad 1 BD engine",
    "BM": "Pad 1 BD engine",
    "FT": "Pad 1 BD FM",
    "FK": "Pad 1 BD FM",
    "FG": "Pad 1 BD FM",
    "FZ": "Pad 1 BD FM",
    "BP": "Pad 1 BD Plastic",
    "PT": "Pad 1 BD Plastic",
    "PK": "Pad 1 BD Plastic",
    "PX": "Pad 1 BD Plastic",
    "PBH": "Pad 1 BD Plastic",
}

_LANE_METADATA = {
    "BR": "pad_1_bd_engine",
    "BM": "pad_1_bd_engine",
    "FT": "pad_1_bd_fm",
    "FK": "pad_1_bd_fm",
    "FG": "pad_1_bd_fm",
    "FZ": "pad_1_bd_fm",
    "BP": "pad_1_bd_plastic",
    "PT": "pad_1_bd_plastic",
    "PK": "pad_1_bd_plastic",
    "PX": "pad_1_bd_plastic",
    "PBH": "pad_1_bd_plastic",
}

_ENGINE_DEPENDENCIES = {
    "BR": "current_pad1_bd_engine_state",
    "BM": "current_pad1_bd_engine_state",
    "FT": "pad1_bd_fm_engine_profile",
    "FK": "pad1_bd_fm_engine_profile",
    "FG": "pad1_bd_fm_engine_profile",
    "FZ": "pad1_bd_fm_anchor_state",
    "BP": "pad1_bd_plastic_profiled_anchor",
    "PT": "pad1_bd_plastic_engine_profile",
    "PK": "pad1_bd_plastic_engine_profile",
    "PX": "pad1_bd_plastic_engine_profile",
    "PBH": "pad1_bd_plastic_anchor_state",
}

_INTENT_LINES = {
    "BR": "Read-only Pad 1 current-engine lane intent.",
    "BM": "Read-only Pad 1 current-engine lane intent.",
    "FT": "Read-only Pad 1 BD FM discovery intent.",
    "FK": "Read-only Pad 1 BD FM discovery intent.",
    "FG": "Read-only Pad 1 BD FM discovery intent.",
    "FZ": "Read-only Pad 1 BD FM anchor-return intent.",
    "BP": "Read-only Pad 1 BD Plastic lane intent.",
    "PT": "Read-only Pad 1 BD Plastic lane intent.",
    "PK": "Read-only Pad 1 BD Plastic lane intent.",
    "PX": "Read-only Pad 1 BD Plastic lane intent.",
    "PBH": "Read-only Pad 1 BD Plastic lane intent.",
}

_DEPENDENCY_LINES = {
    "BR": "Current-engine dependency is recorded only.",
    "BM": "Current-engine dependency is recorded only.",
    "FT": "BD FM engine/profile dependency is recorded only.",
    "FK": "BD FM engine/profile dependency is recorded only.",
    "FG": "BD FM engine/profile dependency is recorded only.",
    "FZ": "BD FM anchor dependency is recorded only.",
    "BP": "BD Plastic anchor/profile dependency is recorded only.",
    "PT": "BD Plastic engine/profile dependency is recorded only.",
    "PK": "BD Plastic engine/profile dependency is recorded only.",
    "PX": "BD Plastic engine/profile dependency is recorded only.",
    "PBH": "BD Plastic anchor dependency is recorded only.",
}


@dataclass(frozen=True)
class Pad1LaneBehaviorResult:
    """Immutable read-only result for Packet 5 Pad 1 lane behavior."""

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
    """Return a passive Packet 5 Pad 1 lane behavior result."""

    key = str(command_key)

    if key in (
        *PACKET_5A_PAD1_CURRENT_ENGINE_KEYS,
        *PACKET_5B_PAD1_BD_FM_KEYS,
        *PACKET_5C_PAD1_BD_PLASTIC_KEYS,
    ):
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
    lane = _LANES[command_key]
    engine_dependency = _ENGINE_DEPENDENCIES[command_key]

    display_lines = (
        f"{command_key}: {label}",
        _INTENT_LINES[command_key],
        f"Target pad: {target_pad}",
        f"Lane: {lane}",
        f"Lane action: {lane_action}",
        _DEPENDENCY_LINES[command_key],
        *_depth_display_lines(command_key, depth_dependency),
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
        behavior_family=_BEHAVIOR_FAMILIES[command_key],
        reason=_REASONS[command_key],
        target_pad=target_pad,
        lane=lane,
        lane_action=lane_action,
        engine_dependency=engine_dependency,
        depth_dependency=depth_dependency,
        display_lines=display_lines,
        metadata=_accepted_metadata(
            command_key,
            command_metadata,
            target_pad,
            lane_action,
            requires_depth_selection,
        ),
    )


def _accepted_metadata(
    command_key,
    command_metadata,
    target_pad,
    lane_action,
    requires_depth_selection,
):
    metadata = {
        "source": "PAD1_COMMANDS",
        "source_command_type": command_metadata["type"],
        "source_command_scope": command_metadata["scope"],
        "source_v134_reference_command": command_metadata[
            "v134_reference_command"
        ],
        "source_scaffold_only": command_metadata["scaffold_only"],
        "target_pad": target_pad,
        "lane": _LANE_METADATA[command_key],
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
    }

    if command_key in PACKET_5B_PAD1_BD_FM_KEYS:
        metadata.update(
            {
                "requires_current_engine_state": False,
                "requires_bd_fm_engine_profile": command_key in ("FT", "FK", "FG"),
                "requires_bd_fm_anchor": command_key == "FZ",
            }
        )

    if command_key in PACKET_5C_PAD1_BD_PLASTIC_KEYS:
        metadata.update(
            {
                "requires_current_engine_state": False,
                "requires_bd_plastic_engine_profile": command_key
                in ("PT", "PK", "PX"),
                "requires_bd_plastic_anchor": command_key in ("BP", "PBH"),
            }
        )

    return metadata


def _depth_display_lines(command_key, depth_dependency):
    if not depth_dependency:
        return ()

    if command_key in PACKET_5B_PAD1_BD_FM_KEYS:
        return ("Future BD FM discovery depth is recorded only.",)

    if command_key in PACKET_5C_PAD1_BD_PLASTIC_KEYS:
        return ("Future BD Plastic discovery depth is recorded only.",)

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
    "PACKET_5B_PAD1_BD_FM_KEYS",
    "PACKET_5C_PAD1_BD_PLASTIC_KEYS",
    "Pad1LaneBehaviorResult",
    "evaluate_pad1_lane_behavior",
]
