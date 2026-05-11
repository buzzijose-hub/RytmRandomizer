"""Test-only selected target state helpers for future runtime planning.

This module records inert selected isolated pad target state. It does not
switch pads, create selected isolated pad runtime state, dispatch commands,
open ports, send MIDI, or touch hardware.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .commands import ISOLATED_PAD_UTILITY_COMMANDS


SELECTED_TARGET_DEFAULT_COMMAND_KEY = "L"
DEFAULT_SELECTED_TARGET_PAD = int(
    ISOLATED_PAD_UTILITY_COMMANDS[SELECTED_TARGET_DEFAULT_COMMAND_KEY]["default_pad"]
)


@dataclass(frozen=True)
class SelectedTargetState:
    """Immutable-ish selected target state for tests and planning."""

    target_pad: object | None = None
    target_state: str = "unset"
    target_source: str = ""
    command_key: str = ""
    source_scope: str = ""
    defaulted: bool = False
    explicit: bool = False
    supported: bool = False
    stale: bool = False
    valid: bool = False
    reason: str = "selected_target_unset"
    safe_failure_code: str = "selected_target_unset"
    selected_pad_switch_executed: bool = False
    selected_isolated_pad_runtime_state_exists: bool = False
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


def build_unset_selected_target_state():
    """Return a safe unset selected target state."""

    return SelectedTargetState(
        metadata=_metadata(
            target_pad=None,
            target_state="unset",
            target_source="",
            command_key="",
            source_scope="",
            supported=False,
            stale=False,
            valid=False,
            reason="selected_target_unset",
            safe_failure_code="selected_target_unset",
        ),
    )


def build_default_selected_target_state():
    """Return the passive default Pad 3 selected target state."""

    command_metadata = ISOLATED_PAD_UTILITY_COMMANDS[SELECTED_TARGET_DEFAULT_COMMAND_KEY]
    source_scope = str(command_metadata["scope"])

    return SelectedTargetState(
        target_pad=DEFAULT_SELECTED_TARGET_PAD,
        target_state="defaulted",
        target_source="passive_default",
        command_key=SELECTED_TARGET_DEFAULT_COMMAND_KEY,
        source_scope=source_scope,
        defaulted=True,
        supported=True,
        valid=True,
        reason="defaulted_selected_isolated_pad_target",
        safe_failure_code="",
        metadata=_metadata(
            source="ISOLATED_PAD_UTILITY_COMMANDS",
            target_pad=DEFAULT_SELECTED_TARGET_PAD,
            target_state="defaulted",
            target_source="passive_default",
            command_key=SELECTED_TARGET_DEFAULT_COMMAND_KEY,
            source_scope=source_scope,
            defaulted=True,
            explicit=False,
            supported=True,
            stale=False,
            valid=True,
            reason="defaulted_selected_isolated_pad_target",
            safe_failure_code="",
        ),
    )


def build_unsupported_selected_target_state(target_pad, command_key=""):
    """Return a deterministic safe failure for unsupported selected targets."""

    return SelectedTargetState(
        target_pad=target_pad,
        target_state="unsupported",
        target_source="unsupported",
        command_key=str(command_key),
        supported=False,
        valid=False,
        reason="unsupported_selected_target",
        safe_failure_code="unsupported_selected_target",
        metadata=_metadata(
            target_pad=target_pad,
            target_state="unsupported",
            target_source="unsupported",
            command_key=str(command_key),
            supported=False,
            valid=False,
            reason="unsupported_selected_target",
            safe_failure_code="unsupported_selected_target",
        ),
    )


def build_stale_selected_target_state(target_pad, command_key=""):
    """Return a deterministic safe failure for stale selected target context."""

    return SelectedTargetState(
        target_pad=target_pad,
        target_state="stale",
        target_source="stale",
        command_key=str(command_key),
        supported=False,
        stale=True,
        valid=False,
        reason="stale_selected_target",
        safe_failure_code="stale_selected_target",
        metadata=_metadata(
            target_pad=target_pad,
            target_state="stale",
            target_source="stale",
            command_key=str(command_key),
            supported=False,
            stale=True,
            valid=False,
            reason="stale_selected_target",
            safe_failure_code="stale_selected_target",
        ),
    )


def build_invalid_selected_target_state(target_pad=None, reason="invalid_selected_target"):
    """Return a deterministic safe failure for invalid selected target context."""

    return SelectedTargetState(
        target_pad=target_pad,
        target_state="invalid",
        target_source="invalid",
        supported=False,
        valid=False,
        reason=str(reason),
        safe_failure_code=str(reason),
        metadata=_metadata(
            target_pad=target_pad,
            target_state="invalid",
            target_source="invalid",
            supported=False,
            valid=False,
            reason=str(reason),
            safe_failure_code=str(reason),
        ),
    )


def _metadata(
    *,
    source="selected_target_state",
    target_pad=None,
    target_state,
    target_source,
    command_key="",
    source_scope="",
    defaulted=False,
    explicit=False,
    supported,
    stale=False,
    valid,
    reason,
    safe_failure_code,
):
    return {
        "source": source,
        "target_pad": target_pad,
        "target_state": target_state,
        "target_source": target_source,
        "command_key": command_key,
        "source_scope": source_scope,
        "defaulted": defaulted,
        "explicit": explicit,
        "supported": supported,
        "stale": stale,
        "valid": valid,
        "reason": reason,
        "safe_failure_code": safe_failure_code,
        "selected_pad_switch_executed": False,
        "selected_isolated_pad_runtime_state_exists": False,
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


__all__ = [
    "DEFAULT_SELECTED_TARGET_PAD",
    "SELECTED_TARGET_DEFAULT_COMMAND_KEY",
    "SelectedTargetState",
    "build_default_selected_target_state",
    "build_invalid_selected_target_state",
    "build_stale_selected_target_state",
    "build_unsupported_selected_target_state",
    "build_unset_selected_target_state",
]
