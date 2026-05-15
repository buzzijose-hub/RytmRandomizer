"""Test-only selected isolated pad runtime-state validation helpers.

This module combines inert selected target state and anchor state data into
deterministic validation results. It does not execute PZ, return anchors,
switch pads, mutate runtime state, dispatch commands, open ports, send MIDI,
or touch hardware.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .anchor_state import build_unknown_anchor_state
from .selected_target_state import build_default_selected_target_state

DEFAULT_OPERATION_KIND = "selected_isolated_pad_runtime_validation"


@dataclass(frozen=True)
class SelectedIsolatedPadRuntimeState:
    """Immutable-ish selected isolated pad runtime-state validation result."""

    runtime_state: str = "uninitialized"
    target_pad: object | None = None
    target_state: str = ""
    target_source: str = ""
    target_command_key: str = ""
    anchor_pad: object | None = None
    anchor_state: str = ""
    anchor_source: str = ""
    anchor_identity: str = ""
    operation_kind: str = DEFAULT_OPERATION_KIND
    target_anchor_status: str = "unavailable"
    supported: bool = False
    stale: bool = False
    valid: bool = False
    reason: str = "selected_isolated_pad_runtime_uninitialized"
    safe_failure_code: str = "selected_isolated_pad_runtime_uninitialized"
    pz_ready: bool = False
    pz_executed: bool = False
    selected_pad_switch_executed: bool = False
    anchor_return_executed: bool = False
    state_changed: bool = False
    dispatches_command: bool = False
    executes_command: bool = False
    mutates_runtime_state: bool = False
    sends_real_midi: bool = False
    opens_ports: bool = False
    hardware_required: bool = False
    active_behavior: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def build_uninitialized_selected_isolated_pad_runtime_state():
    """Return a safe uninitialized selected isolated pad runtime state."""

    return _runtime_state(
        runtime_state="uninitialized",
        target_anchor_status="unavailable",
        reason="selected_isolated_pad_runtime_uninitialized",
        safe_failure_code="selected_isolated_pad_runtime_uninitialized",
    )


def build_passive_default_selected_isolated_pad_runtime_state():
    """Return passive default target context with safely unavailable anchor."""

    return build_selected_isolated_pad_runtime_state(
        selected_target_state=build_default_selected_target_state(),
        anchor_state=build_unknown_anchor_state(),
    )


def build_missing_selected_target_runtime_state(anchor_state=None):
    """Return a deterministic safe failure for missing selected target state."""

    return build_selected_isolated_pad_runtime_state(
        selected_target_state=None,
        anchor_state=anchor_state,
    )


def build_missing_anchor_runtime_state(selected_target_state=None):
    """Return a deterministic safe failure for missing anchor state."""

    return build_selected_isolated_pad_runtime_state(
        selected_target_state=selected_target_state,
        anchor_state=None,
    )


def build_selected_isolated_pad_runtime_state(
    *,
    selected_target_state=None,
    anchor_state=None,
    operation_kind=DEFAULT_OPERATION_KIND,
):
    """Combine selected target and anchor state into an inert validation result."""

    if selected_target_state is None:
        return _runtime_state(
            anchor_state_obj=anchor_state,
            operation_kind=operation_kind,
            runtime_state="invalid",
            target_anchor_status="target-missing",
            reason="missing_selected_target_state",
            safe_failure_code="missing_selected_target_state",
        )

    if anchor_state is None:
        return _runtime_state(
            selected_target_state=selected_target_state,
            operation_kind=operation_kind,
            runtime_state="invalid",
            target_anchor_status="anchor-missing",
            reason="missing_anchor_state",
            safe_failure_code="missing_anchor_state",
        )

    target_state = str(selected_target_state.target_state)
    anchor_state_value = str(anchor_state.anchor_state)

    if target_state == "invalid":
        return _runtime_state(
            selected_target_state=selected_target_state,
            anchor_state_obj=anchor_state,
            operation_kind=operation_kind,
            runtime_state="invalid",
            target_anchor_status="target-invalid",
            reason=str(selected_target_state.reason),
            safe_failure_code=str(selected_target_state.safe_failure_code),
        )

    if anchor_state_value == "invalid":
        return _runtime_state(
            selected_target_state=selected_target_state,
            anchor_state_obj=anchor_state,
            operation_kind=operation_kind,
            runtime_state="invalid",
            target_anchor_status="anchor-invalid",
            reason=str(anchor_state.reason),
            safe_failure_code=str(anchor_state.safe_failure_code),
        )

    if selected_target_state.stale or target_state == "stale":
        return _runtime_state(
            selected_target_state=selected_target_state,
            anchor_state_obj=anchor_state,
            operation_kind=operation_kind,
            runtime_state="stale",
            target_anchor_status="target-stale",
            stale=True,
            reason=str(selected_target_state.reason),
            safe_failure_code=str(selected_target_state.safe_failure_code),
        )

    if anchor_state.stale or anchor_state_value == "stale":
        return _runtime_state(
            selected_target_state=selected_target_state,
            anchor_state_obj=anchor_state,
            operation_kind=operation_kind,
            runtime_state="stale",
            target_anchor_status="anchor-stale",
            stale=True,
            reason=str(anchor_state.reason),
            safe_failure_code=str(anchor_state.safe_failure_code),
        )

    if target_state == "unsupported":
        return _runtime_state(
            selected_target_state=selected_target_state,
            anchor_state_obj=anchor_state,
            operation_kind=operation_kind,
            runtime_state="unsupported",
            target_anchor_status="target-unsupported",
            reason=str(selected_target_state.reason),
            safe_failure_code=str(selected_target_state.safe_failure_code),
        )

    if anchor_state_value == "unsupported":
        return _runtime_state(
            selected_target_state=selected_target_state,
            anchor_state_obj=anchor_state,
            operation_kind=operation_kind,
            runtime_state="unsupported",
            target_anchor_status="anchor-unsupported",
            reason=str(anchor_state.reason),
            safe_failure_code=str(anchor_state.safe_failure_code),
        )

    if target_state == "defaulted" and anchor_state_value == "unknown":
        return _runtime_state(
            selected_target_state=selected_target_state,
            anchor_state_obj=anchor_state,
            operation_kind=operation_kind,
            runtime_state="passive-default",
            target_anchor_status="anchor-unavailable",
            reason="anchor_unavailable_for_selected_target",
            safe_failure_code="anchor_unavailable_for_selected_target",
        )

    return _runtime_state(
        selected_target_state=selected_target_state,
        anchor_state_obj=anchor_state,
        operation_kind=operation_kind,
        runtime_state="unsupported",
        target_anchor_status="runtime-state-unsupported",
        reason="unsupported_selected_isolated_pad_runtime_state",
        safe_failure_code="unsupported_selected_isolated_pad_runtime_state",
    )


def _runtime_state(
    *,
    selected_target_state=None,
    anchor_state_obj=None,
    operation_kind=DEFAULT_OPERATION_KIND,
    runtime_state,
    target_anchor_status,
    supported=False,
    stale=False,
    valid=False,
    reason,
    safe_failure_code,
):
    target_pad = getattr(selected_target_state, "target_pad", None)
    target_state = str(getattr(selected_target_state, "target_state", ""))
    target_source = str(getattr(selected_target_state, "target_source", ""))
    target_command_key = str(getattr(selected_target_state, "command_key", ""))
    anchor_pad = getattr(anchor_state_obj, "anchor_pad", None)
    anchor_state = str(getattr(anchor_state_obj, "anchor_state", ""))
    anchor_source = str(getattr(anchor_state_obj, "anchor_source", ""))
    anchor_identity = str(getattr(anchor_state_obj, "anchor_identity", ""))

    metadata = {
        "source": "selected_isolated_pad_runtime_state",
        "runtime_state": runtime_state,
        "target_pad": target_pad,
        "target_state": target_state,
        "target_source": target_source,
        "target_command_key": target_command_key,
        "anchor_pad": anchor_pad,
        "anchor_state": anchor_state,
        "anchor_source": anchor_source,
        "anchor_identity": anchor_identity,
        "operation_kind": operation_kind,
        "target_anchor_status": target_anchor_status,
        "supported": supported,
        "stale": stale,
        "valid": valid,
        "reason": reason,
        "safe_failure_code": safe_failure_code,
        "pz_ready": False,
        "pz_executed": False,
        "selected_pad_switch_executed": False,
        "anchor_return_executed": False,
        "state_changed": False,
        "dispatches_command": False,
        "executes_command": False,
        "mutates_runtime_state": False,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
    }

    return SelectedIsolatedPadRuntimeState(
        runtime_state=runtime_state,
        target_pad=target_pad,
        target_state=target_state,
        target_source=target_source,
        target_command_key=target_command_key,
        anchor_pad=anchor_pad,
        anchor_state=anchor_state,
        anchor_source=anchor_source,
        anchor_identity=anchor_identity,
        operation_kind=operation_kind,
        target_anchor_status=target_anchor_status,
        supported=supported,
        stale=stale,
        valid=valid,
        reason=reason,
        safe_failure_code=safe_failure_code,
        metadata=metadata,
    )


__all__ = [
    "DEFAULT_OPERATION_KIND",
    "SelectedIsolatedPadRuntimeState",
    "build_missing_anchor_runtime_state",
    "build_missing_selected_target_runtime_state",
    "build_passive_default_selected_isolated_pad_runtime_state",
    "build_selected_isolated_pad_runtime_state",
    "build_uninitialized_selected_isolated_pad_runtime_state",
]
