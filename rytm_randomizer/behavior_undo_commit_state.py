"""Read-only Packet 9 undo/commit/state behavior helpers.

This module models deterministic state utility intent without prompt loops,
dispatching commands, opening ports, sending MIDI, or touching hardware.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .commands import COMMANDS, STATE_UTILITY_COMMANDS


PACKET_9A_UNDO_COMMIT_STATE_KEYS = ("B",)
DEFERRED_PACKET_9_UNDO_COMMIT_STATE_KEYS = ("E", "W", "U")


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


def evaluate_undo_commit_state_behavior(command_key):
    """Return a passive Packet 9 behavior result for a state utility key."""

    key = str(command_key)

    if key == "B":
        return _accepted_b_result()

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


def _accepted_b_result():
    metadata = STATE_UTILITY_COMMANDS["B"]
    label = metadata["label"]
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


def _unsupported_result(command_key):
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
    "UndoCommitStateBehaviorResult",
    "evaluate_undo_commit_state_behavior",
]
