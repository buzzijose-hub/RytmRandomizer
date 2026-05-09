"""Read-only Packet 2 anchor/profile behavior helpers.

This module models deterministic anchor/profile intent without dispatching
commands, opening ports, sending MIDI, or touching hardware.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .commands import COMMANDS, PAD1_COMMANDS
from .profile_lookup import describe_group_profile


PACKET_2A_ANCHOR_PROFILE_KEYS = ("BH", "BC")
PACKET_2B_ANCHOR_PROFILE_KEYS = ("BS",)
PACKET_2C_ANCHOR_PROFILE_KEYS = ("BF",)
SUPPORTED_ANCHOR_PROFILE_KEYS = (
    *PACKET_2A_ANCHOR_PROFILE_KEYS,
    *PACKET_2B_ANCHOR_PROFILE_KEYS,
    *PACKET_2C_ANCHOR_PROFILE_KEYS,
)

_COMMAND_PROFILE_KEYS = {
    "BH": "2",
    "BC": "3",
    "BS": "",
    "BF": "",
}

_COMMAND_ANCHOR_NAMES = {
    "BH": "BD Hard",
    "BC": "BD Classic",
    "BS": "BD Sharp",
    "BF": "BD FM",
}


@dataclass(frozen=True)
class AnchorProfileBehaviorResult:
    """Immutable read-only result for Packet 2 anchor/profile behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "anchor/profile"
    accepted: bool = False
    reason: str = "not_evaluated"
    target_pad: int | None = None
    anchor_name: str = ""
    profile_key: str = ""
    machine_value: int | None = None
    display_lines: tuple[str, ...] = ()
    state_changed: bool = False
    prompt_required: bool = False
    sends_real_midi: bool = False
    opens_ports: bool = False
    hardware_required: bool = False
    active_behavior: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "display_lines", tuple(self.display_lines))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def evaluate_anchor_profile_behavior(command_key):
    """Return a passive Packet 2 anchor/profile behavior result."""

    key = str(command_key)

    if key in SUPPORTED_ANCHOR_PROFILE_KEYS:
        return _accepted_anchor_profile_result(key)

    if key in COMMANDS:
        return AnchorProfileBehaviorResult(
            command_key=key,
            accepted=False,
            reason="unsupported_anchor_profile_command",
            metadata=_safe_failure_metadata("COMMANDS"),
        )

    return AnchorProfileBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata=_safe_failure_metadata("unknown"),
    )


def _accepted_anchor_profile_result(command_key):
    command_metadata = PAD1_COMMANDS[command_key]
    profile_key = _COMMAND_PROFILE_KEYS[command_key]
    profile = describe_group_profile(profile_key) if profile_key else None
    anchor_name = _COMMAND_ANCHOR_NAMES[command_key]
    target_pad = command_metadata["pad"]
    label = command_metadata["label"]
    machine_value = profile["machine_value"] if profile else None

    return AnchorProfileBehaviorResult(
        command_key=command_key,
        label=label,
        accepted=True,
        reason="supported_anchor_profile_intent",
        target_pad=target_pad,
        anchor_name=anchor_name,
        profile_key=profile_key,
        machine_value=machine_value,
        display_lines=(
            f"{command_key}: {label}",
            "Read-only anchor/profile intent.",
            f"Target pad: {target_pad}",
            f"Anchor: {anchor_name}",
            _profile_display_line(profile_key),
            "No prompt would run.",
            "No state would change.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
        metadata={
            "source": "PAD1_COMMANDS",
            "source_command_type": command_metadata["type"],
            "source_profile_key": profile_key,
            "source_profile_name": profile["name"] if profile else "",
            "source_profile_group_pad": profile["group_pad"] if profile else None,
            "group_profile_metadata_exists": bool(profile),
            "target": f"Pad {target_pad} / {anchor_name}",
            "machine_value": machine_value,
            "mock_only": True,
            "sends_real_midi": False,
            "opens_ports": False,
            "hardware_required": False,
            "active_behavior": False,
            "mutates_runtime_state": False,
        },
    )


def _profile_display_line(profile_key):
    if profile_key:
        return f"Profile key: {profile_key}"
    return "Profile metadata: absent"


def _safe_failure_metadata(source):
    return {
        "source": source,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
    }


__all__ = [
    "PACKET_2A_ANCHOR_PROFILE_KEYS",
    "PACKET_2B_ANCHOR_PROFILE_KEYS",
    "PACKET_2C_ANCHOR_PROFILE_KEYS",
    "SUPPORTED_ANCHOR_PROFILE_KEYS",
    "AnchorProfileBehaviorResult",
    "evaluate_anchor_profile_behavior",
]
