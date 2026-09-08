"""Read-only Packet 9 undo/commit/state behavior helpers.

This module models deterministic state utility intent without prompt loops,
dispatching commands, opening ports, sending MIDI, or touching hardware.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ..commands import COMMANDS, STATE_UTILITY_COMMANDS
from ._result_fields import empty_metadata

PACKET_9A_UNDO_COMMIT_STATE_KEYS = ("B",)
PACKET_9B_UNDO_COMMIT_STATE_KEYS = ("E",)
PACKET_9C_UNDO_COMMIT_STATE_KEYS = ("W",)
PACKET_9D_UNDO_COMMIT_STATE_KEYS = ("U",)
SUPPORTED_UNDO_COMMIT_STATE_KEYS = (
    *PACKET_9A_UNDO_COMMIT_STATE_KEYS,
    *PACKET_9B_UNDO_COMMIT_STATE_KEYS,
    *PACKET_9C_UNDO_COMMIT_STATE_KEYS,
    *PACKET_9D_UNDO_COMMIT_STATE_KEYS,
)
DEFERRED_PACKET_9_UNDO_COMMIT_STATE_KEYS = ()


@dataclass(frozen=True)
class UndoCommitStateBehaviorResult:
    """Immutable read-only result for Packet 9 undo/commit/state behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "undo-commit-state/current-anchor-return"
    accepted: bool = False
    reason: str = "not_evaluated"
    target_scope: str = ""
    state_action: str = ""
    intent_kind: str = ""
    anchor_concept: str = ""
    exploration_concept: str = ""
    history_concept: str = ""
    lifecycle_effect: str = ""
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
    metadata: Mapping[str, object] = field(default_factory=empty_metadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "display_lines", tuple(self.display_lines))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def evaluate_undo_commit_state_behavior(command_key: str) -> UndoCommitStateBehaviorResult:
    """Return a passive Packet 9 behavior result for a state utility key."""

    key = str(command_key)

    if key == "B":
        return _accepted_b_result()

    if key == "E":
        return _accepted_e_result()

    if key == "W":
        return _accepted_w_result()

    if key == "U":
        return _accepted_u_result()

    if key in COMMANDS:
        return _unsupported_result(key)

    return UndoCommitStateBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata={
            "source": "unknown",
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


def _accepted_b_result() -> UndoCommitStateBehaviorResult:
    metadata = STATE_UTILITY_COMMANDS["B"]
    label = str(metadata["label"])
    state_action = "describe_current_anchor_return_intent"
    anchor_concept = "current anchor"

    result_metadata = {
        "source": "STATE_UTILITY_COMMANDS",
        "command_type": metadata["type"],
        "target_scope": metadata["scope"],
        "behavior_family": "undo-commit-state/current-anchor-return",
        "state_action": state_action,
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

    return UndoCommitStateBehaviorResult(
        command_key="B",
        label=label,
        behavior_family="undo-commit-state/current-anchor-return",
        accepted=True,
        reason="supported_current_anchor_return_intent",
        target_scope="current_anchor",
        state_action=state_action,
        intent_kind="anchor_return",
        anchor_concept=anchor_concept,
        display_lines=(
            f"B: {label}",
            "Read-only current-anchor return intent.",
            "Target scope: current_anchor",
            f"State action: {state_action}",
            f"Anchor concept: {anchor_concept}",
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


def _accepted_e_result() -> UndoCommitStateBehaviorResult:
    metadata = STATE_UTILITY_COMMANDS["E"]
    label = str(metadata["label"])
    behavior_family = "undo-commit-state/current-state-anchor-commit"
    target_scope = "current_anchor_state"
    state_action = "describe_current_state_anchor_commit_intent"
    intent_kind = "anchor_commit"
    anchor_concept = "current state as new anchor"
    lifecycle_effect = "described_only"

    result_metadata = {
        "source": "STATE_UTILITY_COMMANDS",
        "command_type": metadata["type"],
        "source_scope": metadata["scope"],
        "target_scope": target_scope,
        "behavior_family": behavior_family,
        "state_action": state_action,
        "intent_kind": intent_kind,
        "anchor_concept": anchor_concept,
        "lifecycle_effect": lifecycle_effect,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
    }

    return UndoCommitStateBehaviorResult(
        command_key="E",
        label=label,
        behavior_family=behavior_family,
        accepted=True,
        reason="supported_current_state_anchor_commit_intent",
        target_scope=target_scope,
        state_action=state_action,
        intent_kind=intent_kind,
        anchor_concept=anchor_concept,
        lifecycle_effect=lifecycle_effect,
        display_lines=(
            f"E: {label}",
            "Read-only current-state anchor commit intent.",
            f"Target scope: {target_scope}",
            f"State action: {state_action}",
            f"Anchor concept: {anchor_concept}",
            f"Lifecycle effect: {lifecycle_effect}",
            "No prompt would run.",
            "No state would change.",
            "No anchor would be committed.",
            "No command would dispatch.",
            "No command would execute.",
            "No runtime state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
        metadata=result_metadata,
    )


def _accepted_w_result() -> UndoCommitStateBehaviorResult:
    metadata = STATE_UTILITY_COMMANDS["W"]
    label = str(metadata["label"])
    behavior_family = "undo-commit-state/waveform-exploration"
    target_scope = "waveform_exploration"
    state_action = "describe_waveform_exploration_intent"
    intent_kind = "waveform_exploration"
    exploration_concept = "waveform exploration only"
    lifecycle_effect = "described_only"

    result_metadata = {
        "source": "STATE_UTILITY_COMMANDS",
        "command_type": metadata["type"],
        "source_scope": metadata["scope"],
        "target_scope": target_scope,
        "behavior_family": behavior_family,
        "state_action": state_action,
        "intent_kind": intent_kind,
        "exploration_concept": exploration_concept,
        "lifecycle_effect": lifecycle_effect,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
    }

    return UndoCommitStateBehaviorResult(
        command_key="W",
        label=label,
        behavior_family=behavior_family,
        accepted=True,
        reason="supported_waveform_exploration_intent",
        target_scope=target_scope,
        state_action=state_action,
        intent_kind=intent_kind,
        exploration_concept=exploration_concept,
        lifecycle_effect=lifecycle_effect,
        display_lines=(
            f"W: {label}",
            "Read-only waveform exploration intent.",
            f"Target scope: {target_scope}",
            f"State action: {state_action}",
            f"Exploration concept: {exploration_concept}",
            f"Lifecycle effect: {lifecycle_effect}",
            "No prompt would run.",
            "No state would change.",
            "No waveform would be selected.",
            "No waveform would be randomized.",
            "No command would dispatch.",
            "No command would execute.",
            "No runtime state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
        metadata=result_metadata,
    )


def _accepted_u_result() -> UndoCommitStateBehaviorResult:
    metadata = STATE_UTILITY_COMMANDS["U"]
    label = str(metadata["label"])
    behavior_family = "undo-commit-state/script-generated-state-undo"
    target_scope = "script_generated_state_history"
    state_action = "describe_previous_script_generated_state_undo_intent"
    intent_kind = "state_history_undo"
    history_concept = "previous script-generated state"
    lifecycle_effect = "described_only"

    result_metadata = {
        "source": "STATE_UTILITY_COMMANDS",
        "command_type": metadata["type"],
        "source_scope": metadata["scope"],
        "target_scope": target_scope,
        "behavior_family": behavior_family,
        "state_action": state_action,
        "intent_kind": intent_kind,
        "history_concept": history_concept,
        "lifecycle_effect": lifecycle_effect,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
    }

    return UndoCommitStateBehaviorResult(
        command_key="U",
        label=label,
        behavior_family=behavior_family,
        accepted=True,
        reason="supported_state_history_undo_intent",
        target_scope=target_scope,
        state_action=state_action,
        intent_kind=intent_kind,
        history_concept=history_concept,
        lifecycle_effect=lifecycle_effect,
        display_lines=(
            f"U: {label}",
            "Read-only previous script-generated state undo intent.",
            f"Target scope: {target_scope}",
            f"State action: {state_action}",
            f"History concept: {history_concept}",
            f"Lifecycle effect: {lifecycle_effect}",
            "No prompt would run.",
            "No state would change.",
            "No undo stack would be inspected.",
            "No undo stack would be mutated.",
            "No undo would execute.",
            "No command would dispatch.",
            "No command would execute.",
            "No runtime state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
        metadata=result_metadata,
    )


def _unsupported_result(command_key: str) -> UndoCommitStateBehaviorResult:
    return UndoCommitStateBehaviorResult(
        command_key=command_key,
        accepted=False,
        reason="unsupported_packet_9_undo_commit_state_key",
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


__all__ = [
    "DEFERRED_PACKET_9_UNDO_COMMIT_STATE_KEYS",
    "PACKET_9A_UNDO_COMMIT_STATE_KEYS",
    "PACKET_9B_UNDO_COMMIT_STATE_KEYS",
    "PACKET_9C_UNDO_COMMIT_STATE_KEYS",
    "PACKET_9D_UNDO_COMMIT_STATE_KEYS",
    "SUPPORTED_UNDO_COMMIT_STATE_KEYS",
    "UndoCommitStateBehaviorResult",
    "evaluate_undo_commit_state_behavior",
]
