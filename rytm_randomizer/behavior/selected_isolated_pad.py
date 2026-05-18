"""Read-only Packet 11 selected isolated pad utility behavior helpers.

This module models deterministic selected isolated pad intent without prompt
loops, runtime selected pad state, pad switching execution, anchor return
execution, dispatching commands, opening ports, sending MIDI, or touching
hardware.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ..commands import COMMANDS, ISOLATED_PAD_UTILITY_COMMANDS
from ..state.selected_isolated_pad_validation import (
    build_passive_default_selected_isolated_pad_runtime_state,
)

PACKET_11A_SELECTED_ISOLATED_PAD_KEYS = ("L",)
PACKET_11B_SELECTED_ISOLATED_PAD_KEYS = ("PZ",)
DEFERRED_PACKET_11_SELECTED_ISOLATED_PAD_KEYS = ()
SUPPORTED_SELECTED_ISOLATED_PAD_KEYS = (
    PACKET_11A_SELECTED_ISOLATED_PAD_KEYS + PACKET_11B_SELECTED_ISOLATED_PAD_KEYS
)


@dataclass(frozen=True)
class SelectedIsolatedPadBehaviorResult:
    """Immutable read-only result for Packet 11 selected isolated pad behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "selected-isolated-pad/utility"
    accepted: bool = False
    reason: str = "not_evaluated"
    source_scope: str = ""
    utility_action: str = ""
    intent_kind: str = ""
    default_pad: int | None = None
    target_pad: int | None = None
    selects_isolated_pad: bool = False
    anchor_return_intent: bool = False
    selected_isolated_pad_runtime_state_exists: bool = False
    selected_pad_switch_executed: bool = False
    anchor_return_executed: bool = False
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


def evaluate_selected_isolated_pad_behavior(command_key, runtime_state=None):
    """Return a passive Packet 11 behavior result for selected isolated pad utilities."""

    key = str(command_key)

    if key == "L":
        return _accepted_l_result()

    if key == "PZ":
        return _pz_readiness_result(runtime_state)

    if key in COMMANDS:
        return _unsupported_result(key)

    return SelectedIsolatedPadBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata=_safe_failure_metadata("unknown"),
    )


def _accepted_l_result():
    metadata = ISOLATED_PAD_UTILITY_COMMANDS["L"]
    label = metadata["label"]
    behavior_family = "selected-isolated-pad/target-selection"
    source_scope = metadata["scope"]
    utility_action = "describe_selected_isolated_pad_target_intent"
    intent_kind = "selected_isolated_pad_target_selection"
    default_pad = int(metadata["default_pad"])

    result_metadata = {
        "source": "ISOLATED_PAD_UTILITY_COMMANDS",
        "command_type": metadata["type"],
        "source_scope": source_scope,
        "behavior_family": behavior_family,
        "utility_action": utility_action,
        "intent_kind": intent_kind,
        "default_pad": default_pad,
        "target_pad": default_pad,
        "selects_isolated_pad": True,
        "anchor_return_intent": False,
        "selected_isolated_pad_runtime_state_exists": False,
        "selected_pad_switch_executed": False,
        "anchor_return_executed": False,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
    }

    return SelectedIsolatedPadBehaviorResult(
        command_key="L",
        label=label,
        behavior_family=behavior_family,
        accepted=True,
        reason="supported_selected_isolated_pad_target_intent",
        source_scope=source_scope,
        utility_action=utility_action,
        intent_kind=intent_kind,
        default_pad=default_pad,
        target_pad=default_pad,
        selects_isolated_pad=True,
        display_lines=(
            f"L: {label}",
            "Read-only selected isolated pad target intent.",
            f"Source scope: {source_scope}",
            f"Utility action: {utility_action}",
            f"Intent kind: {intent_kind}",
            f"Default target pad: {default_pad}",
            "Selected isolated pad target is described only.",
            "No selected isolated pad state would be created.",
            "No selected pad switch would execute.",
            "No anchor would return.",
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


def _pz_readiness_result(runtime_state=None):
    metadata = ISOLATED_PAD_UTILITY_COMMANDS["PZ"]
    behavior_family = "selected-isolated-pad/anchor-return-readiness"
    utility_action = "describe_selected_isolated_pad_anchor_return_readiness"
    intent_kind = "selected_isolated_pad_anchor_return_readiness"
    selected_runtime_state = runtime_state

    if selected_runtime_state is None:
        selected_runtime_state = build_passive_default_selected_isolated_pad_runtime_state()

    pz_ready = bool(getattr(selected_runtime_state, "pz_ready", False))
    reason = str(getattr(selected_runtime_state, "reason", "missing_runtime_state"))
    safe_failure_code = str(
        getattr(selected_runtime_state, "safe_failure_code", "missing_runtime_state")
    )
    target_pad = getattr(selected_runtime_state, "target_pad", None)
    runtime_state_value = str(getattr(selected_runtime_state, "runtime_state", ""))
    target_anchor_status = str(getattr(selected_runtime_state, "target_anchor_status", ""))
    anchor_state = str(getattr(selected_runtime_state, "anchor_state", ""))

    return SelectedIsolatedPadBehaviorResult(
        command_key="PZ",
        label=metadata["label"],
        behavior_family=behavior_family,
        accepted=pz_ready,
        reason=reason,
        source_scope=metadata["scope"],
        utility_action=utility_action,
        intent_kind=intent_kind,
        target_pad=target_pad,
        anchor_return_intent=True,
        selected_isolated_pad_runtime_state_exists=True,
        display_lines=(
            f"PZ: {metadata['label']}",
            "Read-only selected isolated pad anchor return readiness.",
            f"Source scope: {metadata['scope']}",
            f"Utility action: {utility_action}",
            f"Intent kind: {intent_kind}",
            f"Runtime state: {runtime_state_value}",
            f"Target pad: {target_pad}",
            f"Target-anchor status: {target_anchor_status}",
            f"Anchor state: {anchor_state}",
            f"PZ ready: {pz_ready}",
            f"Safe failure code: {safe_failure_code}",
            "Anchor return is described only.",
            "No selected pad switch would execute.",
            "No anchor would return.",
            "No runtime state would mutate.",
            "No command would dispatch.",
            "No command would execute.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
        metadata={
            **_safe_failure_metadata("ISOLATED_PAD_UTILITY_COMMANDS"),
            "command_type": metadata["type"],
            "source_scope": metadata["scope"],
            "behavior_family": behavior_family,
            "utility_action": utility_action,
            "intent_kind": intent_kind,
            "runtime_state_source": "selected_isolated_pad_runtime_state",
            "runtime_state": runtime_state_value,
            "target_pad": target_pad,
            "target_state": str(getattr(selected_runtime_state, "target_state", "")),
            "target_source": str(getattr(selected_runtime_state, "target_source", "")),
            "target_command_key": str(getattr(selected_runtime_state, "target_command_key", "")),
            "target_anchor_status": target_anchor_status,
            "anchor_pad": getattr(selected_runtime_state, "anchor_pad", None),
            "anchor_state": anchor_state,
            "anchor_source": str(getattr(selected_runtime_state, "anchor_source", "")),
            "anchor_identity": str(getattr(selected_runtime_state, "anchor_identity", "")),
            "operation_kind": str(getattr(selected_runtime_state, "operation_kind", "")),
            "supported": bool(getattr(selected_runtime_state, "supported", False)),
            "stale": bool(getattr(selected_runtime_state, "stale", False)),
            "valid": bool(getattr(selected_runtime_state, "valid", False)),
            "reason": reason,
            "safe_failure_code": safe_failure_code,
            "pz_ready": pz_ready,
            "pz_executed": bool(getattr(selected_runtime_state, "pz_executed", False)),
            "selected_isolated_pad_runtime_state_exists": True,
            "anchor_return_intent": True,
            "anchor_return_executed": False,
        },
    )


def _unsupported_result(command_key):
    return SelectedIsolatedPadBehaviorResult(
        command_key=command_key,
        accepted=False,
        reason="unsupported_packet_11_selected_isolated_pad_key",
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
        "selected_isolated_pad_runtime_state_exists": False,
        "selected_pad_switch_executed": False,
        "anchor_return_intent": False,
        "anchor_return_executed": False,
    }


__all__ = [
    "DEFERRED_PACKET_11_SELECTED_ISOLATED_PAD_KEYS",
    "PACKET_11A_SELECTED_ISOLATED_PAD_KEYS",
    "PACKET_11B_SELECTED_ISOLATED_PAD_KEYS",
    "SUPPORTED_SELECTED_ISOLATED_PAD_KEYS",
    "SelectedIsolatedPadBehaviorResult",
    "evaluate_selected_isolated_pad_behavior",
]
