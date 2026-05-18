"""Test-only anchor state helpers for future runtime planning.

This module records inert anchor state. It does not return anchors, switch
pads, create selected target or selected isolated pad runtime state, dispatch
commands, open ports, send MIDI, or touch hardware.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True)
class AnchorState:
    """Immutable-ish anchor state for tests and planning."""

    anchor_pad: object | None = None
    anchor_state: str = "unknown"
    anchor_source: str = ""
    anchor_identity: str = ""
    command_key: str = ""
    source_scope: str = ""
    source_profile_key: str = ""
    source_profile_name: str = ""
    source_machine_value: int | None = None
    static: bool = False
    software_known: bool = False
    soft_captured: bool = False
    supported: bool = False
    stale: bool = False
    valid: bool = False
    reason: str = "anchor_unknown"
    safe_failure_code: str = "anchor_unknown"
    anchor_return_executed: bool = False
    selected_pad_switch_executed: bool = False
    selected_target_state_exists: bool = False
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


def build_unknown_anchor_state(command_key=""):
    """Return a safe unknown anchor state."""

    return AnchorState(
        command_key=str(command_key),
        metadata=_metadata(
            anchor_pad=None,
            anchor_state="unknown",
            anchor_source="",
            anchor_identity="",
            command_key=str(command_key),
            supported=False,
            stale=False,
            valid=False,
            reason="anchor_unknown",
            safe_failure_code="anchor_unknown",
        ),
    )


def build_unsupported_anchor_state(anchor_pad=None, command_key="", anchor_identity=""):
    """Return a deterministic safe failure for unsupported anchor context."""

    return AnchorState(
        anchor_pad=anchor_pad,
        anchor_state="unsupported",
        anchor_source="unsupported",
        anchor_identity=str(anchor_identity),
        command_key=str(command_key),
        supported=False,
        valid=False,
        reason="unsupported_anchor",
        safe_failure_code="unsupported_anchor",
        metadata=_metadata(
            anchor_pad=anchor_pad,
            anchor_state="unsupported",
            anchor_source="unsupported",
            anchor_identity=str(anchor_identity),
            command_key=str(command_key),
            supported=False,
            valid=False,
            reason="unsupported_anchor",
            safe_failure_code="unsupported_anchor",
        ),
    )


def build_stale_anchor_state(anchor_pad=None, command_key="", anchor_identity=""):
    """Return a deterministic safe failure for stale anchor context."""

    return AnchorState(
        anchor_pad=anchor_pad,
        anchor_state="stale",
        anchor_source="stale",
        anchor_identity=str(anchor_identity),
        command_key=str(command_key),
        supported=False,
        stale=True,
        valid=False,
        reason="stale_anchor",
        safe_failure_code="stale_anchor",
        metadata=_metadata(
            anchor_pad=anchor_pad,
            anchor_state="stale",
            anchor_source="stale",
            anchor_identity=str(anchor_identity),
            command_key=str(command_key),
            supported=False,
            stale=True,
            valid=False,
            reason="stale_anchor",
            safe_failure_code="stale_anchor",
        ),
    )


def build_invalid_anchor_state(anchor_pad=None, reason="invalid_anchor"):
    """Return a deterministic safe failure for invalid anchor context."""

    return AnchorState(
        anchor_pad=anchor_pad,
        anchor_state="invalid",
        anchor_source="invalid",
        supported=False,
        valid=False,
        reason=str(reason),
        safe_failure_code=str(reason),
        metadata=_metadata(
            anchor_pad=anchor_pad,
            anchor_state="invalid",
            anchor_source="invalid",
            anchor_identity="",
            supported=False,
            valid=False,
            reason=str(reason),
            safe_failure_code=str(reason),
        ),
    )


def _metadata(
    *,
    source="anchor_state",
    anchor_pad=None,
    anchor_state,
    anchor_source,
    anchor_identity,
    command_key="",
    source_scope="",
    source_profile_key="",
    source_profile_name="",
    source_machine_value=None,
    static=False,
    software_known=False,
    soft_captured=False,
    supported,
    stale=False,
    valid,
    reason,
    safe_failure_code,
):
    return {
        "source": source,
        "anchor_pad": anchor_pad,
        "anchor_state": anchor_state,
        "anchor_source": anchor_source,
        "anchor_identity": anchor_identity,
        "command_key": command_key,
        "source_scope": source_scope,
        "source_profile_key": source_profile_key,
        "source_profile_name": source_profile_name,
        "source_machine_value": source_machine_value,
        "static": static,
        "software_known": software_known,
        "soft_captured": soft_captured,
        "supported": supported,
        "stale": stale,
        "valid": valid,
        "reason": reason,
        "safe_failure_code": safe_failure_code,
        "anchor_return_executed": False,
        "selected_pad_switch_executed": False,
        "selected_target_state_exists": False,
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
    "AnchorState",
    "build_invalid_anchor_state",
    "build_stale_anchor_state",
    "build_unknown_anchor_state",
    "build_unsupported_anchor_state",
]
