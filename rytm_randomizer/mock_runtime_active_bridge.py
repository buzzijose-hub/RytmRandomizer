"""Mock-only bridge from runtime intent to active-boundary evaluation.

This module is test-only and inert. It does not import MIDI libraries, open
ports, send real MIDI, expose CLI commands, dispatch runtime behavior, mutate
runtime state, or touch hardware.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .active_boundary import ActiveBoundaryRequest, evaluate_mock_active_boundary
from .mock_midi import MidiMessage, MockMidiSender
from .runtime_plan import RuntimeIntent, validate_runtime_intent_scope


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class RuntimeActiveBridgeRequest:
    """Mock-only request for the first narrow runtime/active bridge."""

    source_kind: str
    source_key: str
    target: str
    armed: bool = False
    dry_run_confirmed: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_key", str(self.source_key))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True)
class RuntimeActiveBridgeResult:
    """Mock-only result for the first narrow runtime/active bridge."""

    accepted: bool
    reason: str
    emitted_messages: tuple[MidiMessage, ...] = ()
    would_execute: bool = False
    mock_only: bool = True
    sends_real_midi: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


def _runtime_intent_from_request(request: RuntimeActiveBridgeRequest) -> RuntimeIntent:
    return RuntimeIntent(
        source_kind=request.source_kind,
        source_key=request.source_key,
        target=request.target,
        armed=request.armed,
        metadata=request.metadata,
    )


def _base_metadata(
    request: RuntimeActiveBridgeRequest,
    *,
    reason: str,
    runtime_supported: bool = False,
    parked: bool = False,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "source_kind": request.source_kind,
        "source_key": request.source_key,
        "target": request.target,
        "armed": request.armed,
        "dry_run_confirmed": request.dry_run_confirmed,
        "runtime_supported": runtime_supported,
        "parked": parked,
        "reason": reason,
        "mock_only": True,
        "sends_real_midi": False,
        "would_execute": False,
    }
    if "operator_intent" in request.metadata:
        metadata["operator_intent"] = request.metadata["operator_intent"]
    return metadata


def _failure(
    request: RuntimeActiveBridgeRequest,
    reason: str,
    *,
    runtime_supported: bool = False,
    parked: bool = False,
) -> RuntimeActiveBridgeResult:
    return RuntimeActiveBridgeResult(
        accepted=False,
        reason=reason,
        emitted_messages=(),
        metadata=_base_metadata(
            request,
            reason=reason,
            runtime_supported=runtime_supported,
            parked=parked,
        ),
    )


def evaluate_mock_runtime_active_bridge(
    request: RuntimeActiveBridgeRequest,
    sender: MockMidiSender,
) -> RuntimeActiveBridgeResult:
    """Evaluate one mock-only runtime intent through the active boundary."""

    if not isinstance(request, RuntimeActiveBridgeRequest):
        raise TypeError("request must be a RuntimeActiveBridgeRequest")
    if not isinstance(sender, MockMidiSender):
        raise TypeError("sender must be a MockMidiSender")

    if not request.armed:
        return _failure(request, "missing_arming")
    if not request.dry_run_confirmed:
        return _failure(request, "missing_dry_run_confirmation")

    runtime_preview = validate_runtime_intent_scope(_runtime_intent_from_request(request))
    runtime_supported = bool(runtime_preview.metadata["supported"])
    parked = bool(runtime_preview.metadata["parked"])

    if request.source_kind != "group_profile":
        return _failure(request, "unsupported_source_kind")
    if parked:
        return _failure(request, "profile_4_parked", parked=True)
    if not runtime_supported:
        return _failure(request, "unsupported_or_unknown_key")

    boundary_result = evaluate_mock_active_boundary(
        ActiveBoundaryRequest(
            source_kind=request.source_kind,
            source_key=request.source_key,
            armed=request.armed,
            dry_run_confirmed=request.dry_run_confirmed,
            target=request.target,
            metadata=request.metadata,
        ),
        sender,
    )

    if not boundary_result.accepted:
        return _failure(
            request,
            "active_boundary_rejected",
            runtime_supported=runtime_supported,
            parked=parked,
        )

    return RuntimeActiveBridgeResult(
        accepted=True,
        reason=boundary_result.reason,
        emitted_messages=boundary_result.emitted_messages,
        metadata=_base_metadata(
            request,
            reason=boundary_result.reason,
            runtime_supported=runtime_supported,
            parked=parked,
        ),
    )
