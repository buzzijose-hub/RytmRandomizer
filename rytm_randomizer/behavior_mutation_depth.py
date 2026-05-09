"""Read-only Packet 3 mutation-depth and guarded-input behavior helpers.

This module models deterministic mutation-depth intent without prompt loops,
dispatching commands, opening ports, sending MIDI, or touching hardware.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .commands import (
    COMMANDS,
    CURRENT_PROFILE_PAGE_MUTATION_COMMANDS,
    LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS,
    MAIN_PROMPT_DEPTH_GUARDRAIL,
)
from .constants import GUARDED_MAIN_PROMPT_DEPTH_COMMANDS


PACKET_3A_GUARDED_DEPTH_KEYS = GUARDED_MAIN_PROMPT_DEPTH_COMMANDS
PACKET_3B_LEGACY_SINGLE_PROFILE_MUTATION_KEYS = tuple(
    LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS
)
PACKET_3C_CURRENT_PROFILE_PAGE_MUTATION_KEYS = tuple(
    CURRENT_PROFILE_PAGE_MUTATION_COMMANDS
)
DEFERRED_PACKET_3_MUTATION_DEPTH_KEYS = (
    "PM",
    "PS",
    "PF",
    "PA",
    "PL",
    "PO",
    "PB",
    "PG",
)


@dataclass(frozen=True)
class MutationDepthBehaviorResult:
    """Immutable read-only result for Packet 3 mutation-depth behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "mutation-depth/guarded-input"
    accepted: bool = False
    reason: str = "not_evaluated"
    depth_value: int | None = None
    mutation_area: str = ""
    mutation_depth: str = ""
    scope: str = ""
    uses_selected_profile: bool = False
    guarded_input: bool = False
    requires_depth_prompt_context: bool = False
    prompt_available: bool = False
    display_lines: tuple[str, ...] = ()
    state_changed: bool = False
    prompt_required: bool = False
    dispatches_command: bool = False
    executes_command: bool = False
    sends_real_midi: bool = False
    opens_ports: bool = False
    hardware_required: bool = False
    active_behavior: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "display_lines", tuple(self.display_lines))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def evaluate_mutation_depth_behavior(command_key):
    """Return a passive Packet 3 mutation-depth behavior result."""

    key = str(command_key)

    if key in PACKET_3A_GUARDED_DEPTH_KEYS:
        return _accepted_guarded_depth_result(key)

    if key in PACKET_3B_LEGACY_SINGLE_PROFILE_MUTATION_KEYS:
        return _accepted_legacy_single_profile_mutation_result(key)

    if key in PACKET_3C_CURRENT_PROFILE_PAGE_MUTATION_KEYS:
        return _accepted_current_profile_page_mutation_result(key)

    if key in DEFERRED_PACKET_3_MUTATION_DEPTH_KEYS:
        return MutationDepthBehaviorResult(
            command_key=key,
            accepted=False,
            reason="deferred_mutation_depth_command",
            metadata=_safe_failure_metadata("COMMANDS"),
        )

    if key in COMMANDS:
        return MutationDepthBehaviorResult(
            command_key=key,
            accepted=False,
            reason="unsupported_mutation_depth_command",
            metadata=_safe_failure_metadata("COMMANDS"),
        )

    return MutationDepthBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata=_safe_failure_metadata("unknown"),
    )


def _accepted_guarded_depth_result(command_key):
    command_metadata = COMMANDS[command_key]
    label = command_metadata["label"]
    depth_value = int(command_key)

    return MutationDepthBehaviorResult(
        command_key=command_key,
        label=label,
        accepted=True,
        reason="supported_guarded_depth_input",
        depth_value=depth_value,
        guarded_input=True,
        requires_depth_prompt_context=True,
        prompt_available=False,
        display_lines=(
            f"{command_key}: {label}",
            "Read-only guarded numeric input intent.",
            f"Depth value: {depth_value}",
            "Bare main-prompt use remains guarded.",
            "Valid only inside a future depth prompt context.",
            "No active depth prompt exists now.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No MIDI would be sent.",
            "No ports would be opened.",
        ),
        metadata={
            "source": "MAIN_PROMPT_DEPTH_GUARDRAIL",
            "source_command_type": command_metadata["type"],
            "depth_prompt_context": MAIN_PROMPT_DEPTH_GUARDRAIL[
                "depth_prompt_context"
            ],
            "mock_only": True,
            "sends_real_midi": False,
            "opens_ports": False,
            "hardware_required": False,
            "active_behavior": False,
            "mutates_runtime_state": False,
        },
    )


def _accepted_legacy_single_profile_mutation_result(command_key):
    command_metadata = LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS[command_key]
    label = command_metadata["label"]
    mutation_area = command_metadata["mutation_area"]
    mutation_depth = command_metadata["mutation_depth"]
    scope = command_metadata["scope"]
    uses_selected_profile = command_metadata["uses_selected_profile"]

    return MutationDepthBehaviorResult(
        command_key=command_key,
        label=label,
        behavior_family="mutation-depth/legacy-single-profile",
        accepted=True,
        reason="supported_legacy_single_profile_mutation_intent",
        mutation_area=mutation_area,
        mutation_depth=mutation_depth,
        scope=scope,
        uses_selected_profile=uses_selected_profile,
        prompt_available=False,
        display_lines=(
            f"{command_key}: {label}",
            "Read-only legacy single-profile mutation intent.",
            f"Mutation area: {mutation_area}",
            f"Mutation depth: {mutation_depth}",
            "Selected-profile dependency is recorded only.",
            "No selected-profile state exists in this helper.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No MIDI would be sent.",
            "No ports would be opened.",
        ),
        metadata={
            "source": "LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS",
            "source_command_type": command_metadata["type"],
            "command_family": command_metadata["command_family"],
            "mutation_area": mutation_area,
            "mutation_depth": mutation_depth,
            "scope": scope,
            "uses_selected_profile": uses_selected_profile,
            "mock_only": True,
            "sends_real_midi": False,
            "opens_ports": False,
            "hardware_required": False,
            "active_behavior": False,
            "mutates_runtime_state": False,
        },
    )


def _accepted_current_profile_page_mutation_result(command_key):
    command_metadata = CURRENT_PROFILE_PAGE_MUTATION_COMMANDS[command_key]
    label = command_metadata["label"]
    mutation_area = command_metadata["mutation_area"]
    scope = command_metadata["scope"]
    requires_depth_selection = command_metadata["requires_depth_selection"]

    return MutationDepthBehaviorResult(
        command_key=command_key,
        label=label,
        behavior_family="mutation-depth/current-profile-page",
        accepted=True,
        reason="supported_current_profile_page_mutation_intent",
        mutation_area=mutation_area,
        scope=scope,
        requires_depth_prompt_context=requires_depth_selection,
        prompt_available=False,
        prompt_required=requires_depth_selection,
        display_lines=(
            f"{command_key}: {label}",
            "Read-only current-profile page mutation intent.",
            f"Mutation area: {mutation_area}",
            "Current-profile dependency is recorded only.",
            "Future depth selection is required.",
            "No active depth prompt exists now.",
            "No current-profile state exists in this helper.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No MIDI would be sent.",
            "No ports would be opened.",
        ),
        metadata={
            "source": "CURRENT_PROFILE_PAGE_MUTATION_COMMANDS",
            "source_command_type": command_metadata["type"],
            "command_family": command_metadata["command_family"],
            "mutation_area": mutation_area,
            "requires_depth_selection": requires_depth_selection,
            "scope": scope,
            "mock_only": True,
            "sends_real_midi": False,
            "opens_ports": False,
            "hardware_required": False,
            "active_behavior": False,
            "mutates_runtime_state": False,
        },
    )


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
    "DEFERRED_PACKET_3_MUTATION_DEPTH_KEYS",
    "PACKET_3A_GUARDED_DEPTH_KEYS",
    "PACKET_3B_LEGACY_SINGLE_PROFILE_MUTATION_KEYS",
    "PACKET_3C_CURRENT_PROFILE_PAGE_MUTATION_KEYS",
    "MutationDepthBehaviorResult",
    "evaluate_mutation_depth_behavior",
]
