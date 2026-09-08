"""Immutable, inert A4 audition review records; never hardware authority."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Final, Literal, TypedDict

from ...guardrails.input_validation import canonical_json_bytes
from .stage import ANALOG_FOUR_DEVICE_ID, StageDeviceId

A4PreparationBlocker = Literal[
    "session_unavailable",
    "candidate_not_selected",
    "candidate_not_local",
    "source_bytes_unavailable",
    "source_bytes_invalid",
    "candidate_bytes_unavailable",
    "candidate_bytes_invalid",
    "scope_changed",
    "no_a4_changes",
    "source_reload_required",
    "current_capture_required",
    "current_capture_invalid",
    "current_capture_stale",
    "current_source_mismatch",
    "output_port_intent_required",
    "recovery_slot_required",
    "a4_hardware_audition_validation_pending",
    "a4_live_transport_mapping_unverified",
    "persistent_kit_write_prohibited",
]

A4_PREPARATION_PERMANENT_BLOCKERS: Final[tuple[A4PreparationBlocker, ...]] = (
    "a4_hardware_audition_validation_pending",
    "a4_live_transport_mapping_unverified",
    "persistent_kit_write_prohibited",
)


class A4PreparationChangeDict(TypedDict):
    track_id: int
    parameter: str
    before_raw_q8_8: int
    after_raw_q8_8: int
    before_screen_value: str
    after_screen_value: str
    unpacked_offsets: list[int]


@dataclass(frozen=True)
class A4PreparationChange:
    """A canonically re-rendered saved-KIT field, not a MIDI packet."""

    track_id: int
    parameter: str
    before_raw_q8_8: int
    after_raw_q8_8: int
    before_screen_value: str
    after_screen_value: str
    unpacked_offsets: tuple[int, ...]

    def to_dict(self) -> A4PreparationChangeDict:
        return {
            "track_id": self.track_id,
            "parameter": self.parameter,
            "before_raw_q8_8": self.before_raw_q8_8,
            "after_raw_q8_8": self.after_raw_q8_8,
            "before_screen_value": self.before_screen_value,
            "after_screen_value": self.after_screen_value,
            "unpacked_offsets": list(self.unpacked_offsets),
        }


class A4PreparationReportDict(TypedDict):
    schema_version: Literal["a4-preparation-v1"]
    preparation_id: str
    entry_id: str
    candidate_id: str | None
    device_id: StageDeviceId
    source_capture_id: str
    source_fingerprint: str
    source_frame_sha256: str
    candidate_frame_sha256: str | None
    current_capture_fingerprint: str | None
    current_capture_at: str | None
    capture_after: str
    checked_at: str
    target_ids: list[int]
    locked_ids: list[int]
    effective_ids: list[int]
    output_port_name: str | None
    recovery_slot: int | None
    source_reloaded: bool
    candidate_is_local: bool
    candidate_bytes_verified: bool
    current_source_verified: bool
    changes: list[A4PreparationChangeDict]
    blocked_reasons: list[A4PreparationBlocker]
    ready: Literal[False]
    hardware_send_validated: Literal[False]
    output_authority: Literal["offline-review-only"]


@dataclass(frozen=True)
class A4PreparationReport:
    """Candidate-bound review evidence with unconditionally blocked output.

    This DTO has no inbound authority parser. Exporting or reconstructing it
    cannot authorize a send. Timestamps and output names describe the reviewed
    context, never an armed port or proof that working RAM was restored.
    """

    entry_id: str
    candidate_id: str | None
    source_capture_id: str
    source_fingerprint: str
    source_frame_sha256: str
    candidate_frame_sha256: str | None
    current_capture_fingerprint: str | None
    current_capture_at: datetime | None
    capture_after: datetime
    checked_at: datetime
    target_ids: tuple[int, ...]
    locked_ids: tuple[int, ...]
    effective_ids: tuple[int, ...]
    output_port_name: str | None
    recovery_slot: int | None
    source_reloaded: bool
    candidate_is_local: bool
    candidate_bytes_verified: bool
    current_source_verified: bool
    changes: tuple[A4PreparationChange, ...]
    blocked_reasons: tuple[A4PreparationBlocker, ...]
    preparation_id: str = field(default="", init=False)
    ready: Literal[False] = field(default=False, init=False)
    hardware_send_validated: Literal[False] = field(default=False, init=False)
    output_authority: Literal["offline-review-only"] = field(
        default="offline-review-only", init=False
    )

    def __post_init__(self) -> None:
        # The permanent refusal survives direct construction and dataclass
        # replacement as well as the normal pure builder path.
        reasons = tuple(dict.fromkeys((*self.blocked_reasons, *A4_PREPARATION_PERMANENT_BLOCKERS)))
        object.__setattr__(self, "blocked_reasons", reasons)
        payload = self.to_dict()
        encoded = canonical_json_bytes(payload)
        object.__setattr__(
            self, "preparation_id", f"a4-preparation-{hashlib.sha256(encoded).hexdigest()}"
        )

    def to_dict(self) -> A4PreparationReportDict:
        return {
            "schema_version": "a4-preparation-v1",
            "preparation_id": self.preparation_id,
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "device_id": ANALOG_FOUR_DEVICE_ID,
            "source_capture_id": self.source_capture_id,
            "source_fingerprint": self.source_fingerprint,
            "source_frame_sha256": self.source_frame_sha256,
            "candidate_frame_sha256": self.candidate_frame_sha256,
            "current_capture_fingerprint": self.current_capture_fingerprint,
            "current_capture_at": (
                None if self.current_capture_at is None else self.current_capture_at.isoformat()
            ),
            "capture_after": self.capture_after.isoformat(),
            "checked_at": self.checked_at.isoformat(),
            "target_ids": list(self.target_ids),
            "locked_ids": list(self.locked_ids),
            "effective_ids": list(self.effective_ids),
            "output_port_name": self.output_port_name,
            "recovery_slot": self.recovery_slot,
            "source_reloaded": self.source_reloaded,
            "candidate_is_local": self.candidate_is_local,
            "candidate_bytes_verified": self.candidate_bytes_verified,
            "current_source_verified": self.current_source_verified,
            "changes": [change.to_dict() for change in self.changes],
            "blocked_reasons": list(self.blocked_reasons),
            "ready": self.ready,
            "hardware_send_validated": self.hardware_send_validated,
            "output_authority": self.output_authority,
        }


__all__ = [
    "A4_PREPARATION_PERMANENT_BLOCKERS",
    "A4PreparationBlocker",
    "A4PreparationChange",
    "A4PreparationChangeDict",
    "A4PreparationReport",
    "A4PreparationReportDict",
]
