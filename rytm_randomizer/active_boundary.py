"""Mock-first active boundary for tests only.

This module does not import MIDI libraries, open ports, send MIDI, expose CLI
commands, dispatch runtime behavior, or touch hardware.

``ActiveBoundaryError`` is also a member of the unified
:mod:`rytm_randomizer.observability.errors` taxonomy: it inherits from both
:class:`~rytm_randomizer.observability.errors.BoundaryError` AND
``ValueError``, so existing ``except ValueError`` callers and new
``except BoundaryError`` callers both work.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .mock_message_mapper import map_group_profile_to_mock_messages
from .mock_midi import MidiMessage, MockMidiSender
from .observability.errors import BoundaryError

SUPPORTED_SOURCE_KIND = "group_profile"
SUPPORTED_SOURCE_KEY = "2"
ACTIVE_BOUNDARY_NAME = "mock_active_boundary"
SUPPORTED_CANDIDATE = f"{SUPPORTED_SOURCE_KIND}:{SUPPORTED_SOURCE_KEY}"

__all__ = [
    "ACTIVE_BOUNDARY_NAME",
    "SUPPORTED_CANDIDATE",
    "SUPPORTED_SOURCE_KEY",
    "SUPPORTED_SOURCE_KIND",
    "ActiveBoundaryError",
    "ActiveBoundaryRequest",
    "ActiveBoundaryResult",
    "evaluate_mock_active_boundary",
]


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class ActiveBoundaryRequest:
    """Mock-only request for the future active boundary."""

    source_kind: str
    source_key: str
    armed: bool = False
    dry_run_confirmed: bool = False
    target: str = "mock"
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_key", str(self.source_key))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True)
class ActiveBoundaryResult:
    """Mock-only active boundary result."""

    accepted: bool
    emitted_messages: tuple[MidiMessage, ...]
    reason: str
    mock_only: bool = True
    sends_real_midi: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


class ActiveBoundaryError(BoundaryError, ValueError):
    """Raised when active boundary inputs are invalid for tests.

    Member of the unified
    :class:`~rytm_randomizer.observability.errors.BoundaryError` taxonomy.
    ``ValueError`` is kept as an additional base for backward-compatibility
    with any ``except ValueError`` caller.
    """


def _result_metadata(
    request: ActiveBoundaryRequest,
    reason: str | None = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "boundary": ACTIVE_BOUNDARY_NAME,
        "source_kind": request.source_kind,
        "source_key": request.source_key,
        "target": request.target,
        "armed": request.armed,
        "dry_run_confirmed": request.dry_run_confirmed,
        "supported_candidate": SUPPORTED_CANDIDATE,
        "mock_only": True,
        "sends_real_midi": False,
    }
    if reason is not None:
        metadata["reason"] = reason
    if "operator_intent" in request.metadata:
        metadata["operator_intent"] = request.metadata["operator_intent"]
    return metadata


def _failure(reason: str, request: ActiveBoundaryRequest) -> ActiveBoundaryResult:
    return ActiveBoundaryResult(
        accepted=False,
        emitted_messages=(),
        reason=reason,
        metadata=_result_metadata(request, reason=reason),
    )


def evaluate_mock_active_boundary(
    request: ActiveBoundaryRequest,
    sender: MockMidiSender,
) -> ActiveBoundaryResult:
    """Evaluate the accepted candidate through the mock-only active boundary."""

    if not isinstance(request, ActiveBoundaryRequest):
        raise TypeError("request must be an ActiveBoundaryRequest")
    if not isinstance(sender, MockMidiSender):
        raise TypeError("sender must be a MockMidiSender")

    if not request.armed:
        return _failure("missing_arming", request)
    if not request.dry_run_confirmed:
        return _failure("missing_dry_run_confirmation", request)
    if request.source_kind != SUPPORTED_SOURCE_KIND:
        return _failure("unsupported_source_kind", request)
    if request.source_key != SUPPORTED_SOURCE_KEY:
        return _failure("unsupported_or_unknown_key", request)

    messages = tuple(map_group_profile_to_mock_messages(SUPPORTED_SOURCE_KEY))
    sender.send_many(messages)
    return ActiveBoundaryResult(
        accepted=True,
        emitted_messages=messages,
        reason="accepted_mock_only",
        metadata=_result_metadata(request),
    )
