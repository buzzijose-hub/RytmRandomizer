"""Read-only Packet 10 selected-profile workflow behavior helpers.

This module models deterministic selected-profile intent without prompt loops,
runtime profile state, machine changes, anchor loading, dispatching commands,
opening ports, sending MIDI, or touching hardware.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .commands import COMMANDS, PROFILE_WORKFLOW_COMMANDS


PACKET_10A_SELECTED_PROFILE_KEYS = ("P",)
PACKET_10B_SELECTED_PROFILE_KEYS = ("M",)
DEFERRED_PACKET_10_SELECTED_PROFILE_KEYS = ()
SUPPORTED_SELECTED_PROFILE_KEYS = (
    *PACKET_10A_SELECTED_PROFILE_KEYS,
    *PACKET_10B_SELECTED_PROFILE_KEYS,
)


@dataclass(frozen=True)
class SelectedProfileBehaviorResult:
    """Immutable read-only result for Packet 10 selected-profile behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "selected-profile-workflow/profile-selection"
    accepted: bool = False
    reason: str = "not_evaluated"
    source_scope: str = ""
    workflow_action: str = ""
    intent_kind: str = ""
    selects_profile: bool = False
    machine_change_intent: bool = False
    uses_selected_profile: bool = False
    selected_profile_dependency: str = ""
    anchor_load_intent: bool = False
    selected_profile_runtime_state_exists: bool = False
    machine_change_executed: bool = False
    anchor_load_executed: bool = False
    display_lines: tuple[str, ...] = ()
    state_changed: bool = False
    prompt_required: bool = False
    dispatches_command: bool = False
    executes_command: bool = False
    mutates_runtime_state: bool = False
    sends_real_midi: bool = False
    opens_ports: bool = False
    hardware_required: bool = False
    active_behavior: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "display_lines", tuple(self.display_lines))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def evaluate_selected_profile_behavior(command_key):
    """Return a passive Packet 10 behavior result for selected-profile workflow."""

    key = str(command_key)

    if key == "P":
        return _accepted_p_result()

    if key == "M":
        return _accepted_m_result()

    if key in COMMANDS:
        return _unsupported_result(key)

    return SelectedProfileBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata=_safe_failure_metadata("unknown"),
    )


def _accepted_p_result():
    metadata = PROFILE_WORKFLOW_COMMANDS["P"]
    label = metadata["label"]
    behavior_family = "selected-profile-workflow/profile-selection"
    source_scope = metadata["scope"]
    workflow_action = "describe_profile_selection_machine_change_intent"
    intent_kind = "profile_machine_selection"

    result_metadata = {
        "source": "PROFILE_WORKFLOW_COMMANDS",
        "command_type": metadata["type"],
        "source_scope": source_scope,
        "behavior_family": behavior_family,
        "workflow_action": workflow_action,
        "intent_kind": intent_kind,
        "selects_profile": bool(metadata["selects_profile"]),
        "machine_change_intent": bool(metadata["machine_change_intent"]),
        "uses_selected_profile": False,
        "selected_profile_runtime_state_exists": False,
        "machine_change_executed": False,
        "anchor_load_executed": False,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
    }

    return SelectedProfileBehaviorResult(
        command_key="P",
        label=label,
        behavior_family=behavior_family,
        accepted=True,
        reason="supported_profile_selection_machine_change_intent",
        source_scope=source_scope,
        workflow_action=workflow_action,
        intent_kind=intent_kind,
        selects_profile=True,
        machine_change_intent=True,
        display_lines=(
            f"P: {label}",
            "Read-only selected-profile workflow intent.",
            f"Source scope: {source_scope}",
            f"Workflow action: {workflow_action}",
            f"Intent kind: {intent_kind}",
            "Profile selection is described only.",
            "Machine change is described only.",
            "No selected-profile state would be created.",
            "No machine would change.",
            "No anchor would load.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No runtime state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
        metadata=result_metadata,
    )


def _accepted_m_result():
    metadata = PROFILE_WORKFLOW_COMMANDS["M"]
    label = metadata["label"]
    behavior_family = "selected-profile-workflow/selected-profile-anchor-load"
    source_scope = metadata["scope"]
    workflow_action = "describe_selected_profile_anchor_load_intent"
    intent_kind = "selected_profile_anchor_load"
    selected_profile_dependency = "current_selected_profile_state"

    result_metadata = {
        "source": "PROFILE_WORKFLOW_COMMANDS",
        "command_type": metadata["type"],
        "source_scope": source_scope,
        "behavior_family": behavior_family,
        "workflow_action": workflow_action,
        "intent_kind": intent_kind,
        "selects_profile": False,
        "machine_change_intent": False,
        "uses_selected_profile": bool(metadata["uses_selected_profile"]),
        "selected_profile_dependency": selected_profile_dependency,
        "anchor_load_intent": bool(metadata["anchor_load_intent"]),
        "selected_profile_runtime_state_exists": False,
        "machine_change_executed": False,
        "anchor_load_executed": False,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
    }

    return SelectedProfileBehaviorResult(
        command_key="M",
        label=label,
        behavior_family=behavior_family,
        accepted=True,
        reason="supported_selected_profile_anchor_load_intent",
        source_scope=source_scope,
        workflow_action=workflow_action,
        intent_kind=intent_kind,
        uses_selected_profile=True,
        selected_profile_dependency=selected_profile_dependency,
        anchor_load_intent=True,
        display_lines=(
            f"M: {label}",
            "Read-only selected-profile anchor-load intent.",
            f"Source scope: {source_scope}",
            f"Workflow action: {workflow_action}",
            f"Intent kind: {intent_kind}",
            f"Selected-profile dependency: {selected_profile_dependency}",
            "Selected-profile anchor load is described only.",
            "No selected-profile state would be read.",
            "No selected-profile state would be created.",
            "No anchor would load.",
            "No machine would change.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No runtime state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
        metadata=result_metadata,
    )


def _unsupported_result(command_key):
    return SelectedProfileBehaviorResult(
        command_key=command_key,
        accepted=False,
        reason="unsupported_packet_10_selected_profile_key",
        metadata=_safe_failure_metadata("COMMANDS"),
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
        "dispatches_command": False,
        "selected_profile_dependency": "",
        "anchor_load_intent": False,
        "selected_profile_runtime_state_exists": False,
        "machine_change_executed": False,
        "anchor_load_executed": False,
    }


__all__ = [
    "DEFERRED_PACKET_10_SELECTED_PROFILE_KEYS",
    "PACKET_10A_SELECTED_PROFILE_KEYS",
    "PACKET_10B_SELECTED_PROFILE_KEYS",
    "SUPPORTED_SELECTED_PROFILE_KEYS",
    "SelectedProfileBehaviorResult",
    "evaluate_selected_profile_behavior",
]
