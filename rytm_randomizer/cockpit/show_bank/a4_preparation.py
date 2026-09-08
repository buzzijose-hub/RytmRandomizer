"""Pure preparation of blocked A4 audition reviews from canonical KIT bytes.

There are no transport collaborators here. Even a completely verified local
candidate remains an offline review: neither a saved-KIT field calibration
nor a manual source-reload statement grants a live MIDI mapping or a restore
contract. Imported records and reports never grant output authority.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Final

from ...data.analog_four_sysex_calibration import (
    A4_FILTER1_FREQUENCY_PARAMETER,
    analog_four_sysex_calibration_for,
)
from ...devices import (
    AnalogFourFilter1FrequencyCandidateMutation,
    get_analog_four_filter1_frequency_candidate_capability,
    resolve_saved_kit_capture_capability,
)
from ...guardrails.input_validation import require_boolean, require_text
from ...snapshot.mutation_scope import MutationScope, registered_mutation_ids
from ..capture import KitCaptureResult
from ..data.a4_preparation import (
    A4PreparationBlocker,
    A4PreparationChange,
    A4PreparationReport,
)
from ..data.show_bank import ShowBankEntry, ShowKitCandidate, ShowKitCapture
from ..data.stage import ANALOG_FOUR_DEVICE_ID, is_analog_four_stage_slot

_MAX_OUTPUT_NAME: Final[int] = 256
_ASCII_SPACE: Final[int] = 32
_ASCII_DELETE: Final[int] = 127


def _require_aware_time(value: datetime, label: str) -> None:
    if value.utcoffset() is None:
        raise ValueError(f"{label} must have a timezone")


@dataclass(frozen=True)
class A4PreparationContext:
    """Current-session observations supplied by the workspace, never imported.

    ``capture_after`` is the latest relevant session/cue/source cutoff. A
    current capture must follow it and not postdate ``checked_at``.
    ``source_reloaded`` records an explicit operator statement; a capture
    alone cannot prove working-RAM restoration. Defaults provide no such
    statement or local provenance, and this context cannot authorize output.
    ``output_port_name`` is exact operator intent, not an enumerated/open port.
    """

    scope: MutationScope
    capture_after: datetime
    checked_at: datetime
    current_capture: KitCaptureResult | None = None
    active_candidate_id: str | None = None
    session_connected: bool = False
    candidate_is_local: bool = False
    source_reloaded: bool = False
    output_port_name: str | None = None

    def __post_init__(self) -> None:
        for name in ("session_connected", "candidate_is_local", "source_reloaded"):
            require_boolean(getattr(self, name), name, ValueError)
        _require_aware_time(self.capture_after, "capture_after")
        _require_aware_time(self.checked_at, "checked_at")
        if self.capture_after > self.checked_at:
            raise ValueError("capture_after must not follow checked_at")
        if self.output_port_name is not None:
            name = require_text(self.output_port_name, "output_port_name", ValueError)
            if len(name) > _MAX_OUTPUT_NAME or any(
                ord(character) < _ASCII_SPACE or ord(character) == _ASCII_DELETE
                for character in name
            ):
                raise ValueError("output_port_name must be bounded plain text or null")


def _frame_fingerprint(frame: bytes) -> str:
    """Revalidate a saved-KIT frame through the registered capture capability."""

    capability = resolve_saved_kit_capture_capability(ANALOG_FOUR_DEVICE_ID).capability
    decoded = capability.decode_saved_kit_capture(frame)
    if capability.encode_saved_kit_capture(decoded) != frame:
        raise ValueError("A4 frame does not round-trip exactly")
    return hashlib.sha256(decoded.unpacked).hexdigest()[:16]


def _source_matches(source: ShowKitCapture, frame: bytes) -> bool:
    return (
        is_analog_four_stage_slot(source.device_id)
        and source.round_trip_verified is True
        and source.sysex.frame_bytes == len(frame)
        and source.sysex.frame_sha256 == hashlib.sha256(frame).hexdigest()
        and source.fingerprint == _frame_fingerprint(frame)
    )


def _candidate_changes(
    candidate: ShowKitCandidate,
    source: ShowKitCapture,
    source_frame: bytes,
    candidate_frame: bytes,
) -> tuple[A4PreparationChange, ...]:
    """Derive change rows from canonical rendering, never claimed offsets."""

    a4 = candidate.analog_four_candidate
    if (
        candidate.source_a4_fingerprint != source.fingerprint
        or a4.source_fingerprint != source.fingerprint
        or a4.sysex.frame_sha256 != hashlib.sha256(candidate_frame).hexdigest()
        or a4.sysex.frame_bytes != len(candidate_frame)
    ):
        raise ValueError("A4 candidate does not match its source and artifact identities")
    capability = get_analog_four_filter1_frequency_candidate_capability()
    rendered = capability.render_filter1_frequency_candidate(
        source_frame,
        tuple(
            AnalogFourFilter1FrequencyCandidateMutation(
                track=value.track_id, screen_value=value.screen_value
            )
            for value in a4.values
        ),
    )
    if (
        rendered.framed_sysex != candidate_frame
        or not rendered.roundtrip_redecoded
        or not rendered.native_byte_isolation_validated
        or rendered.hardware_send_validated is not False
    ):
        raise ValueError("A4 artifact differs from its canonically isolated offline candidate")
    changes: list[A4PreparationChange] = []
    calibration = analog_four_sysex_calibration_for(A4_FILTER1_FREQUENCY_PARAMETER)
    for claimed, applied in zip(a4.values, rendered.applied_mutations, strict=True):
        if (
            claimed.parameter != A4_FILTER1_FREQUENCY_PARAMETER
            or claimed.unpacked_offset != applied.intended_unpacked_offsets[0]
            or claimed.encoded_unsigned_8_8 != applied.redecoded_raw_q8_8
        ):
            raise ValueError("A4 candidate field claims differ from canonical calibration")
        before = int.from_bytes(applied.source_unpacked_bytes, "big")
        changes.append(
            A4PreparationChange(
                track_id=applied.track,
                parameter=A4_FILTER1_FREQUENCY_PARAMETER,
                before_raw_q8_8=before,
                after_raw_q8_8=applied.redecoded_raw_q8_8,
                before_screen_value=calibration.format_native_screen_value(before),
                after_screen_value=applied.redecoded_screen_value,
                unpacked_offsets=applied.intended_unpacked_offsets,
            )
        )
    return tuple(changes)


def _review_current_capture(
    source: ShowKitCapture,
    context: A4PreparationContext,
    blockers: list[A4PreparationBlocker],
) -> bool:
    capture = context.current_capture
    if capture is None:
        blockers.append("current_capture_required")
        return False
    try:
        _require_aware_time(capture.captured_at, "current capture")
        if (
            not is_analog_four_stage_slot(capture.device_id)
            or capture.round_trip_verified is not True
            or capture.input_only is not True
            or capture.sent_midi is not False
            or capture.frame_bytes != len(capture.frame)
            or capture.fingerprint != _frame_fingerprint(capture.frame)
        ):
            raise ValueError("current A4 capture is not verified input-only evidence")
    except (TypeError, ValueError):
        blockers.append("current_capture_invalid")
        return False
    after = max(context.capture_after, source.captured_at)
    if not after < capture.captured_at <= context.checked_at:
        blockers.append("current_capture_stale")
        return False
    if (
        capture.fingerprint != source.fingerprint
        or hashlib.sha256(capture.frame).hexdigest() != source.sysex.frame_sha256
    ):
        blockers.append("current_source_mismatch")
        return False
    return True


def _review_candidate(
    entry: ShowBankEntry,
    source_frame: bytes | None,
    candidate_frame: bytes | None,
    context: A4PreparationContext,
    blockers: list[A4PreparationBlocker],
) -> tuple[ShowKitCandidate | None, tuple[A4PreparationChange, ...], bool]:
    candidate = next(
        (item for item in entry.candidates if item.candidate_id == entry.selected_candidate_id),
        None,
    )
    if candidate is None or context.active_candidate_id != candidate.candidate_id:
        blockers.append("candidate_not_selected")
    if not context.candidate_is_local:
        blockers.append("candidate_not_local")
    if source_frame is None:
        blockers.append("source_bytes_unavailable")
        return candidate, (), False
    try:
        if not _source_matches(entry.analog_four_source, source_frame):
            raise ValueError("retained A4 source does not match the immutable anchor")
    except (TypeError, ValueError):
        blockers.append("source_bytes_invalid")
        return candidate, (), False
    if candidate is None:
        return None, (), False
    if candidate_frame is None:
        blockers.append("candidate_bytes_unavailable")
        return candidate, (), False
    recipe_scope = candidate.recipe.analog_four_scope
    if context.scope.target_ids != frozenset(
        recipe_scope.target_ids
    ) or context.scope.locked_ids != frozenset(recipe_scope.locked_ids):
        blockers.append("scope_changed")
    try:
        changes = _candidate_changes(
            candidate, entry.analog_four_source, source_frame, candidate_frame
        )
        changed_tracks = frozenset(change.track_id for change in changes)
        if changed_tracks != frozenset(recipe_scope.effective_ids):
            raise ValueError("A4 candidate values do not match its recipe scope")
    except (TypeError, ValueError):
        blockers.append("candidate_bytes_invalid")
        return candidate, (), False
    if not any(change.before_raw_q8_8 != change.after_raw_q8_8 for change in changes):
        blockers.append("no_a4_changes")
    return candidate, changes, True


def prepare_a4_audition(
    *,
    entry: ShowBankEntry,
    source_frame: bytes | None,
    candidate_frame: bytes | None,
    context: A4PreparationContext,
) -> A4PreparationReport:
    """Review exact local bytes and current observations without making a plan sendable.

    Missing or contradictory evidence appears as closed blocker codes. Scope
    ids and context fields are validated as caller input. Neither output-port
    discovery nor any hardware-side validation takes place.
    """

    effective = context.scope.validated_effective_ids(
        registered_mutation_ids(ANALOG_FOUR_DEVICE_ID), item_label="A4 track"
    )
    blockers: list[A4PreparationBlocker] = []
    if not context.session_connected:
        blockers.append("session_unavailable")
    candidate, changes, verified = _review_candidate(
        entry, source_frame, candidate_frame, context, blockers
    )
    if not context.source_reloaded:
        blockers.append("source_reload_required")
    current_verified = _review_current_capture(entry.analog_four_source, context, blockers)
    if context.output_port_name is None or not context.output_port_name.strip():
        blockers.append("output_port_intent_required")
    if entry.analog_four_source.hardware_slot is None:
        blockers.append("recovery_slot_required")
    capture = context.current_capture
    return A4PreparationReport(
        entry_id=entry.entry_id,
        candidate_id=None if candidate is None else candidate.candidate_id,
        source_capture_id=entry.analog_four_source.capture_id,
        source_fingerprint=entry.analog_four_source.fingerprint,
        source_frame_sha256=entry.analog_four_source.sysex.frame_sha256,
        candidate_frame_sha256=(
            None if candidate is None else candidate.analog_four_candidate.sysex.frame_sha256
        ),
        current_capture_fingerprint=None if capture is None else capture.fingerprint,
        current_capture_at=None if capture is None else capture.captured_at,
        capture_after=context.capture_after,
        checked_at=context.checked_at,
        target_ids=tuple(sorted(context.scope.target_ids)),
        locked_ids=tuple(sorted(context.scope.locked_ids)),
        effective_ids=tuple(sorted(effective)),
        output_port_name=context.output_port_name,
        recovery_slot=entry.analog_four_source.hardware_slot,
        source_reloaded=context.source_reloaded,
        candidate_is_local=context.candidate_is_local,
        candidate_bytes_verified=verified,
        current_source_verified=current_verified,
        changes=changes,
        blocked_reasons=tuple(blockers),
    )


__all__ = ["A4PreparationContext", "prepare_a4_audition"]
