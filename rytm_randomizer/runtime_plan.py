"""Mock-only runtime planning primitives.

This module is inert. It does not import MIDI libraries, open ports, send MIDI,
or connect to hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


SUPPORTED_GROUP_PROFILE_KEYS = frozenset({"2", "3"})


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


def create_blocked_runtime_preview(
    intent: RuntimeIntent,
    reason: str,
) -> RuntimePlanPreview:
    return RuntimePlanPreview(
        intent=intent,
        safety=RuntimeSafetyEnvelope(reason=reason),
        status="blocked",
        reason=reason,
        would_execute=False,
    )


def validate_runtime_intent_scope(intent: RuntimeIntent) -> RuntimePlanPreview:
    if intent.source_kind != "group_profile":
        return create_blocked_runtime_preview(intent, "unsupported source kind")
    if intent.source_key == "4":
        return create_blocked_runtime_preview(intent, "profile 4 parked")
    if intent.source_key not in SUPPORTED_GROUP_PROFILE_KEYS:
        return create_blocked_runtime_preview(intent, "unsupported key")
    return create_blocked_runtime_preview(intent, "execution not implemented")
