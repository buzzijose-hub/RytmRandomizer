"""Read-only Packet 1A menu/status behavior helpers.

This module is intentionally passive. It models deterministic menu/status
behavior results without dispatching commands, opening ports, sending MIDI, or
touching hardware.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .commands import MENU_COMMANDS, UTILITY_COMMANDS


PACKET_1A_MENU_STATUS_KEYS = (
    "BD",
    "FM",
    "PD",
    "SM",
    "P2M",
    "J",
    "GM",
    "SCN",
    "PR",
    "SR",
    "P3M",
    "P4M",
    "H",
    "R",
)

DEFERRED_UTILITY_SESSION_KEYS = ("T", "C", "Q")

_SPECIAL_SCOPES = {
    "J": {
        "scope": "four_pad_group_display",
        "executes_group_mutation": False,
    },
    "SCN": {
        "scope": "scene_menu_display",
        "executes_scene": False,
    },
    "H": {
        "scope": "current_anchor_report",
        "mutates_runtime_state": False,
    },
    "R": {
        "scope": "script_state_report",
        "mutates_runtime_state": False,
    },
}


@dataclass(frozen=True)
class MenuUtilityBehaviorResult:
    """Immutable read-only result for Packet 1A menu/status behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "menu/status"
    display_lines: tuple[str, ...] = ()
    state_dependency_notes: tuple[str, ...] = ()
    accepted: bool = False
    reason: str = "not_evaluated"
    state_changed: bool = False
    prompt_required: bool = False
    sends_real_midi: bool = False
    opens_ports: bool = False
    hardware_required: bool = False
    active_behavior: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "display_lines", tuple(self.display_lines))
        object.__setattr__(
            self,
            "state_dependency_notes",
            tuple(self.state_dependency_notes),
        )
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def evaluate_menu_utility_behavior(command_key):
    """Return a passive Packet 1A behavior result for a command key."""

    key = str(command_key)

    if key in PACKET_1A_MENU_STATUS_KEYS:
        return _accepted_menu_status_result(key)

    if key in DEFERRED_UTILITY_SESSION_KEYS:
        return MenuUtilityBehaviorResult(
            command_key=key,
            label=UTILITY_COMMANDS[key]["label"],
            accepted=False,
            reason="deferred_utility_session_command",
            metadata={
                "source": "UTILITY_COMMANDS",
                "deferred": True,
                "mock_only": True,
                "sends_real_midi": False,
            },
        )

    return MenuUtilityBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata={
            "source": "unknown",
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


def _accepted_menu_status_result(command_key):
    metadata = MENU_COMMANDS[command_key]
    label = metadata["label"]
    result_metadata = {
        "source": "MENU_COMMANDS",
        "command_type": metadata["type"],
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
    }
    result_metadata.update(_SPECIAL_SCOPES.get(command_key, {}))

    return MenuUtilityBehaviorResult(
        command_key=command_key,
        label=label,
        accepted=True,
        reason="supported_menu_status_behavior",
        display_lines=(
            f"{command_key}: {label}",
            "Read-only menu/status behavior.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
        state_dependency_notes=_state_dependency_notes(command_key),
        metadata=result_metadata,
    )


def _state_dependency_notes(command_key):
    if command_key == "H":
        return ("Future current-anchor state may affect displayed details.",)
    if command_key == "R":
        return ("Future script-state model may affect displayed details.",)
    if command_key in {"FM", "PD", "SM", "SR"}:
        return ("Future current-profile status may affect displayed details.",)
    return ()


__all__ = [
    "DEFERRED_UTILITY_SESSION_KEYS",
    "PACKET_1A_MENU_STATUS_KEYS",
    "MenuUtilityBehaviorResult",
    "evaluate_menu_utility_behavior",
]
