"""Mock-only runtime planning primitives.

This module is inert. It does not import MIDI libraries, open ports, send MIDI,
or connect to hardware.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

SUPPORTED_GROUP_PROFILE_KEYS = frozenset({"2", "3"})

REASON_EXECUTION_NOT_IMPLEMENTED = "execution_not_implemented"
REASON_UNSUPPORTED_KEY = "unsupported_key"
REASON_UNSUPPORTED_SOURCE_KIND = "unsupported_source_kind"
REASON_PROFILE_4_PARKED = "profile_4_parked"
REASON_MISSING_ARMING = "missing_arming"

__all__ = [
    "MockRuntimeProvider",
    "REASON_EXECUTION_NOT_IMPLEMENTED",
    "REASON_MISSING_ARMING",
    "REASON_PROFILE_4_PARKED",
    "REASON_UNSUPPORTED_KEY",
    "REASON_UNSUPPORTED_SOURCE_KIND",
    "RuntimeIntent",
    "RuntimePlanPreview",
    "RuntimeSafetyEnvelope",
    "SUPPORTED_GROUP_PROFILE_KEYS",
    "create_blocked_runtime_preview",
    "validate_runtime_intent_scope",
]

_REASON_CODE_BY_REASON = {
    "execution not implemented": REASON_EXECUTION_NOT_IMPLEMENTED,
    "unsupported key": REASON_UNSUPPORTED_KEY,
    "unsupported source kind": REASON_UNSUPPORTED_SOURCE_KIND,
    "profile 4 parked": REASON_PROFILE_4_PARKED,
    "missing arming": REASON_MISSING_ARMING,
}


@dataclass(frozen=True)
class RuntimeIntent:
    """Inert description of a future runtime-facing operator intent."""

    source_kind: str
    source_key: str
    target: str
    armed: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class RuntimeSafetyEnvelope:
    """Safety flags for a mock-only runtime planning preview."""

    mock_only: bool = True
    sends_real_midi: bool = False
    ports_allowed: bool = False
    hardware_required: bool = False
    reason: str = "mock-only runtime planning"


@dataclass(frozen=True)
class RuntimePlanPreview:
    """Blocked runtime preview that never executes."""

    intent: RuntimeIntent
    safety: RuntimeSafetyEnvelope
    status: str
    reason: str
    would_execute: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class MockRuntimeProvider:
    """In-memory fake provider for future runtime planning tests only."""

    def __init__(self) -> None:
        self._records: list[RuntimePlanPreview] = []

    @property
    def records(self) -> tuple[RuntimePlanPreview, ...]:
        return tuple(self._records)

    def record(self, preview: RuntimePlanPreview) -> RuntimePlanPreview:
        self._records.append(preview)
        return preview

    def clear(self) -> None:
        self._records.clear()


def _reason_code_for(reason: str) -> str:
    return _REASON_CODE_BY_REASON.get(reason, reason.replace(" ", "_").replace("-", "_"))


def _build_blocked_preview_metadata(
    intent: RuntimeIntent,
    reason: str,
    *,
    supported: bool = False,
    parked: bool = False,
) -> dict[str, object]:
    return {
        "source_kind": intent.source_kind,
        "source_key": intent.source_key,
        "target": intent.target,
        "source_label": f"{intent.source_kind}:{intent.source_key}",
        "request_kind": "runtime_plan_preview",
        "supported": supported,
        "parked": parked,
        "arming_required": True,
        "armed": intent.armed,
        "reason_code": _reason_code_for(reason),
        "mock_only": True,
        "sends_real_midi": False,
        "ports_allowed": False,
        "hardware_required": False,
        "would_execute": False,
    }


def create_blocked_runtime_preview(
    intent: RuntimeIntent,
    reason: str,
    *,
    supported: bool = False,
    parked: bool = False,
) -> RuntimePlanPreview:
    return RuntimePlanPreview(
        intent=intent,
        safety=RuntimeSafetyEnvelope(reason=reason),
        status="blocked",
        reason=reason,
        would_execute=False,
        metadata=_build_blocked_preview_metadata(
            intent,
            reason,
            supported=supported,
            parked=parked,
        ),
    )


def validate_runtime_intent_scope(intent: RuntimeIntent) -> RuntimePlanPreview:
    if intent.source_kind != "group_profile":
        return create_blocked_runtime_preview(intent, "unsupported source kind")
    if intent.source_key == "4":
        return create_blocked_runtime_preview(intent, "profile 4 parked", parked=True)
    if intent.source_key not in SUPPORTED_GROUP_PROFILE_KEYS:
        return create_blocked_runtime_preview(intent, "unsupported key")
    return create_blocked_runtime_preview(
        intent,
        "execution not implemented",
        supported=True,
    )
