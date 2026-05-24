"""Inert cockpit SEND plan dataclasses.

``CockpitSendPlan`` is the deterministic preflight object between a
``MutationCandidate`` and the actual SEND command. It is safe to inspect,
serialize, and hand to the desktop UI because it contains only planned CC
packets and readiness metadata; it does not open MIDI ports or touch hardware.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Literal, Self

from .types import STATUS_VALUES, Status

_PAD_ID_MIN: Final[int] = 1
_PAD_ID_MAX: Final[int] = 12
_MIDI_VALUE_MIN: Final[int] = 0
_MIDI_VALUE_MAX: Final[int] = 127
_MIDI_CHANNEL_MIN: Final[int] = 0
_MIDI_CHANNEL_MAX: Final[int] = 15

ReadinessReason = Literal[
    "ready",
    "candidate_high_risk",
    "profile_mismatch",
    "source_snapshot_mismatch",
    "no_sendable_changes",
]
READINESS_REASON_VALUES: Final[tuple[ReadinessReason, ...]] = (
    "ready",
    "candidate_high_risk",
    "profile_mismatch",
    "source_snapshot_mismatch",
    "no_sendable_changes",
)


def synthetic_parameter_cc(parameter: str) -> int:
    """Return the deterministic Phase-1 synthetic CC for ``parameter``.

    This mirrors the Phase-1 cockpit real adapter mapping but is exposed in
    the neutral data layer so SEND can follow an already prepared plan instead
    of recalculating CC numbers at the hardware boundary.
    """

    digest = hashlib.sha1(parameter.encode("utf-8"), usedforsecurity=False).digest()
    return 33 + (digest[0] % 95)


@dataclass(frozen=True)
class SendPlanPacket:
    """One inert CC packet in a prepared SEND plan."""

    pad_id: int
    parameter: str
    channel: int
    control: int
    value: int

    def __post_init__(self) -> None:
        if not (_PAD_ID_MIN <= self.pad_id <= _PAD_ID_MAX):
            raise ValueError(f"pad_id must be in [{_PAD_ID_MIN}, {_PAD_ID_MAX}]; got {self.pad_id}")
        if not self.parameter:
            raise ValueError("parameter must be a non-empty string")
        if not (_MIDI_CHANNEL_MIN <= self.channel <= _MIDI_CHANNEL_MAX):
            raise ValueError(
                f"channel must be in [{_MIDI_CHANNEL_MIN}, {_MIDI_CHANNEL_MAX}]; got {self.channel}"
            )
        if not (_MIDI_VALUE_MIN <= self.control <= _MIDI_VALUE_MAX):
            raise ValueError(
                f"control must be in [{_MIDI_VALUE_MIN}, {_MIDI_VALUE_MAX}]; got {self.control}"
            )
        if not (_MIDI_VALUE_MIN <= self.value <= _MIDI_VALUE_MAX):
            raise ValueError(
                f"value must be in [{_MIDI_VALUE_MIN}, {_MIDI_VALUE_MAX}]; got {self.value}"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "pad_id": self.pad_id,
            "parameter": self.parameter,
            "channel": self.channel,
            "control": self.control,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        return cls(
            pad_id=int(data["pad_id"]),
            parameter=str(data["parameter"]),
            channel=int(data["channel"]),
            control=int(data["control"]),
            value=int(data["value"]),
        )


@dataclass(frozen=True)
class CockpitSendPlan:
    """Deterministic preflight state required before SEND can apply."""

    plan_id: str
    candidate_id: str
    source_snapshot_id: str
    profile_id: str
    ready: bool
    readiness_reason: ReadinessReason
    safety_status: Status
    packets: tuple[SendPlanPacket, ...]
    locked_pad_ids: frozenset[int]
    blocked_reasons: tuple[ReadinessReason, ...]

    def __post_init__(self) -> None:
        for field_name, value in (
            ("plan_id", self.plan_id),
            ("candidate_id", self.candidate_id),
            ("source_snapshot_id", self.source_snapshot_id),
            ("profile_id", self.profile_id),
        ):
            if not value:
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.readiness_reason not in READINESS_REASON_VALUES:
            raise ValueError(
                f"readiness_reason must be one of {READINESS_REASON_VALUES}; "
                f"got {self.readiness_reason!r}"
            )
        if self.safety_status not in STATUS_VALUES:
            raise ValueError(
                f"safety_status must be one of {STATUS_VALUES}; got {self.safety_status!r}"
            )
        unknown_reasons = set(self.blocked_reasons) - set(READINESS_REASON_VALUES)
        if unknown_reasons:
            raise ValueError(f"blocked_reasons contains unknown values: {sorted(unknown_reasons)}")
        if self.ready:
            if self.readiness_reason != "ready":
                raise ValueError("ready plans must use readiness_reason='ready'")
            if self.blocked_reasons:
                raise ValueError("ready plans must not carry blocked_reasons")
            if not self.packets:
                raise ValueError("ready plans must contain at least one packet")
        else:
            if not self.blocked_reasons:
                raise ValueError("blocked plans must carry blocked_reasons")
            if self.readiness_reason == "ready":
                raise ValueError("blocked plans must not use readiness_reason='ready'")

    def to_dict(self) -> dict[str, object]:
        packet_pad_ids = {packet.pad_id for packet in self.packets}
        return {
            "plan_id": self.plan_id,
            "candidate_id": self.candidate_id,
            "source_snapshot_id": self.source_snapshot_id,
            "profile_id": self.profile_id,
            "ready": self.ready,
            "readiness_reason": self.readiness_reason,
            "safety_status": self.safety_status,
            "estimated_midi_msgs": len(self.packets),
            "pad_count": len(packet_pad_ids),
            "locked_pad_ids": sorted(self.locked_pad_ids),
            "blocked_reasons": list(self.blocked_reasons),
            "packets": [packet.to_dict() for packet in self.packets],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        packets_obj = data["packets"]
        locked_obj = data["locked_pad_ids"]
        blocked_obj = data["blocked_reasons"]
        if not isinstance(packets_obj, (list, tuple)):
            raise TypeError(f"packets must be a list/tuple; got {type(packets_obj).__name__}")
        if not isinstance(locked_obj, (list, tuple, frozenset, set)):
            raise TypeError(f"locked_pad_ids must be an iterable; got {type(locked_obj).__name__}")
        if not isinstance(blocked_obj, (list, tuple)):
            raise TypeError(
                f"blocked_reasons must be a list/tuple; got {type(blocked_obj).__name__}"
            )
        return cls(
            plan_id=str(data["plan_id"]),
            candidate_id=str(data["candidate_id"]),
            source_snapshot_id=str(data["source_snapshot_id"]),
            profile_id=str(data["profile_id"]),
            ready=bool(data["ready"]),
            readiness_reason=str(data["readiness_reason"]),  # type: ignore[arg-type]
            safety_status=str(data["safety_status"]),  # type: ignore[arg-type]
            packets=tuple(SendPlanPacket.from_dict(packet) for packet in packets_obj),
            locked_pad_ids=frozenset(int(pad_id) for pad_id in locked_obj),
            blocked_reasons=tuple(str(reason) for reason in blocked_obj),  # type: ignore[arg-type]
        )


__all__ = [
    "CockpitSendPlan",
    "READINESS_REASON_VALUES",
    "ReadinessReason",
    "SendPlanPacket",
    "synthetic_parameter_cc",
]
