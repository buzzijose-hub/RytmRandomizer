"""Passive Analog Four snapshot mutation planning.

This module plans bounded changes from saved Analog Four kit values only. The
current Analog Four parameter map is not validated, so changes are reported as
unverified saved offset candidates. It does not import MIDI libraries, open
ports, send messages, request SysEx, receive live SysEx, write SysEx, or mutate
hardware.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from ..observability.errors import DataError
from .offset_candidates import CANDIDATE_STATUS, VALUE_MAX, VALUE_MIN
from .saved_offset_mappings import (
    VERIFIED_CHANGE_SOURCE,
    VERIFIED_MAPPING_STATUS,
    AnalogFourVerifiedSavedOffsetMapping,
    find_verified_saved_offset_mapping,
    normalize_verified_saved_offset_mappings,
)
from .snapshot_decoder import (
    KIT_HEADER_LENGTH,
    KIT_NAME_LENGTH,
    KIT_NAME_OFFSET,
    TRACK_BLOCK_LENGTH,
    TRACK_BLOCK_OFFSETS,
    TRACK_NAME_LENGTH,
    AnalogFourSnapshotDecodeError,
    _find_kit_record,
    _format_manufacturer_id,
    _read_ascii_name,
    _unpack_elektron_7bit,
    _validate_a4_kit_record,
)

TRACK_COUNT = 4
MAX_CHANGES_PER_TRACK = 6
DEPTH_DELTAS = {
    "micro": 3,
    "groove": 8,
    "strong": 14,
}
CHANGE_SOURCE = "saved_parameter_offset_candidate_unverified"


class AnalogFourSnapshotMutationPlanError(DataError, ValueError):
    """Raised when passive A4 snapshot mutation planning cannot run."""


@dataclass(frozen=True)
class AnalogFourSnapshotPlannedOffsetChange:
    """One captured-value-relative unverified A4 saved-offset change."""

    track: int
    midi_channel: int
    wire_channel: int
    relative_offset: int
    word_index: int
    baseline_value: int
    planned_value: int
    delta: int
    mapping_status: str
    source: str
    parameter_name: str | None = None
    cc: int | None = None


@dataclass(frozen=True)
class AnalogFourTrackMutationPlan:
    """Passive mutation plan for one Analog Four track block."""

    track: int
    midi_channel: int
    wire_channel: int
    name: str
    block_offset: int
    mapping_status: str
    plan_status: str
    changes: tuple[AnalogFourSnapshotPlannedOffsetChange, ...]


@dataclass(frozen=True)
class AnalogFourSnapshotMutationPlan:
    """Passive mutation plan for one saved Analog Four kit snapshot."""

    source_path: str | None
    slot_number: int
    kit_name: str
    depth: str
    manufacturer_id: str
    tracks: tuple[AnalogFourTrackMutationPlan, ...]

    @property
    def planned_track_count(self) -> int:
        return sum(1 for track in self.tracks if track.changes)

    @property
    def blocked_track_count(self) -> int:
        return sum(1 for track in self.tracks if not track.changes)

    @property
    def planned_change_count(self) -> int:
        return sum(len(track.changes) for track in self.tracks)

    @property
    def scanned_track_count(self) -> int:
        return len(self.tracks)


def build_analog_four_snapshot_mutation_plan_from_file(
    path: str | Path,
    *,
    slot: int,
    depth: str,
    verified_mappings: Iterable[AnalogFourVerifiedSavedOffsetMapping] | None = None,
) -> AnalogFourSnapshotMutationPlan:
    """Build a passive A4 snapshot mutation plan from an existing SysEx file."""

    plan = build_analog_four_snapshot_mutation_plan_from_bytes(
        Path(path).read_bytes(),
        slot=slot,
        depth=depth,
        verified_mappings=verified_mappings,
    )
    return AnalogFourSnapshotMutationPlan(
        source_path=str(path),
        slot_number=plan.slot_number,
        kit_name=plan.kit_name,
        depth=plan.depth,
        manufacturer_id=plan.manufacturer_id,
        tracks=plan.tracks,
    )


def build_analog_four_snapshot_mutation_plan_from_bytes(
    data: bytes,
    *,
    slot: int,
    depth: str,
    verified_mappings: Iterable[AnalogFourVerifiedSavedOffsetMapping] | None = None,
) -> AnalogFourSnapshotMutationPlan:
    """Build a passive A4 snapshot mutation plan from raw SysEx bytes."""

    if depth not in DEPTH_DELTAS:
        raise AnalogFourSnapshotMutationPlanError("depth must be micro, groove, or strong")

    try:
        record = _find_kit_record(data, slot=slot)
        _validate_a4_kit_record(record)
    except AnalogFourSnapshotDecodeError as exc:
        raise AnalogFourSnapshotMutationPlanError(str(exc)) from exc

    payload = _unpack_elektron_7bit(record[KIT_HEADER_LENGTH:-1])
    _require_track_blocks(payload)
    normalized_mappings = normalize_verified_saved_offset_mappings(verified_mappings)
    return AnalogFourSnapshotMutationPlan(
        source_path=None,
        slot_number=slot,
        kit_name=_read_ascii_name(payload, KIT_NAME_OFFSET, KIT_NAME_LENGTH),
        depth=depth,
        manufacturer_id=_format_manufacturer_id(record),
        tracks=tuple(
            _build_track_plan(payload, track, depth, normalized_mappings) for track in range(1, 5)
        ),
    )


def filter_analog_four_snapshot_mutation_plan_to_track(
    plan: AnalogFourSnapshotMutationPlan,
    *,
    track: int,
) -> AnalogFourSnapshotMutationPlan:
    """Return a copy of an Analog Four snapshot mutation plan for one track."""

    if not isinstance(plan, AnalogFourSnapshotMutationPlan):
        raise TypeError("plan must be an AnalogFourSnapshotMutationPlan")
    if track not in range(1, 5):
        raise AnalogFourSnapshotMutationPlanError(
            "Analog Four snapshot track must be 1, 2, 3, or 4"
        )

    selected_tracks = tuple(track_plan for track_plan in plan.tracks if track_plan.track == track)
    if not selected_tracks:
        raise AnalogFourSnapshotMutationPlanError(
            "Analog Four snapshot track must be 1, 2, 3, or 4"
        )

    return AnalogFourSnapshotMutationPlan(
        source_path=plan.source_path,
        slot_number=plan.slot_number,
        kit_name=plan.kit_name,
        depth=plan.depth,
        manufacturer_id=plan.manufacturer_id,
        tracks=selected_tracks,
    )


def format_analog_four_snapshot_mutation_plan_report(
    plan: AnalogFourSnapshotMutationPlan,
) -> list[str]:
    """Format a deterministic passive A4 snapshot mutation plan report."""

    lines = [
        "RytmRandomizer passive Analog Four Snapshot Mutation Plan Report",
        f"Source path: {plan.source_path or '<bytes>'}",
        f"Source slot: {plan.slot_number}",
        f"Kit: {plan.kit_name or '<blank>'}",
        f"Depth: {plan.depth}",
        f"Manufacturer ID: {plan.manufacturer_id}",
        f"Tracks scanned: {_format_scanned_tracks(plan)}",
        f"Planned tracks: {plan.planned_track_count} / {plan.scanned_track_count}",
        f"Blocked tracks: {plan.blocked_track_count} / {plan.scanned_track_count}",
        f"Planned changes: {plan.planned_change_count}",
        "Track plans:",
    ]
    for track in plan.tracks:
        lines.append(
            f"- Track {track.track} / MIDI channel {track.midi_channel}: "
            f"{track.name or '<blank>'} / {track.mapping_status} / "
            f"{len(track.changes)} change(s)"
        )
    if plan.planned_change_count:
        lines.append("Planned saved-offset changes:")
        for track in plan.tracks:
            lines.extend(_format_change_line(track, change) for change in track.changes)
    lines.extend(_policy_and_safety_lines(has_verified_mappings=_has_verified_mappings(plan)))
    return lines


def format_analog_four_snapshot_mutation_plan_error(
    path: str | Path,
    message: str,
) -> list[str]:
    """Format deterministic passive A4 snapshot mutation-plan errors."""

    return [
        "RytmRandomizer passive Analog Four Snapshot Mutation Plan Report",
        f"Path: {path}",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        *_policy_and_safety_lines(has_verified_mappings=False),
    ]


def _build_track_plan(
    payload: bytes,
    track: int,
    depth: str,
    verified_mappings: tuple[AnalogFourVerifiedSavedOffsetMapping, ...],
) -> AnalogFourTrackMutationPlan:
    block_offset = TRACK_BLOCK_OFFSETS[track - 1]
    block = payload[block_offset : block_offset + TRACK_BLOCK_LENGTH]
    changes = tuple(
        _planned_change(track, relative_offset, value, depth, verified_mappings)
        for relative_offset, value in _selected_cc_like_words(block)
    )
    changes = tuple(change for change in changes if change.delta)
    return AnalogFourTrackMutationPlan(
        track=track,
        midi_channel=track,
        wire_channel=track - 1,
        name=_read_ascii_name(payload, block_offset, TRACK_NAME_LENGTH),
        block_offset=block_offset,
        mapping_status=_mapping_status_for_changes(changes),
        plan_status=_plan_status_for_changes(changes),
        changes=changes,
    )


def _selected_cc_like_words(block: bytes) -> tuple[tuple[int, int], ...]:
    words = []
    for relative_offset in range(TRACK_NAME_LENGTH, len(block) - 1, 2):
        value = (block[relative_offset] << 8) | block[relative_offset + 1]
        if VALUE_MIN < value <= VALUE_MAX:
            words.append((relative_offset, value))
        if len(words) == MAX_CHANGES_PER_TRACK:
            break
    return tuple(words)


def _planned_change(
    track: int,
    relative_offset: int,
    baseline_value: int,
    depth: str,
    verified_mappings: tuple[AnalogFourVerifiedSavedOffsetMapping, ...],
) -> AnalogFourSnapshotPlannedOffsetChange:
    planned_value = _clamp_midi_value(baseline_value + DEPTH_DELTAS[depth])
    mapping = find_verified_saved_offset_mapping(
        track=track,
        relative_offset=relative_offset,
        mappings=verified_mappings,
    )
    mapping_status = mapping.mapping_status if mapping is not None else CANDIDATE_STATUS
    source = VERIFIED_CHANGE_SOURCE if mapping is not None else CHANGE_SOURCE
    return AnalogFourSnapshotPlannedOffsetChange(
        track=track,
        midi_channel=track,
        wire_channel=track - 1,
        relative_offset=relative_offset,
        word_index=relative_offset // 2,
        baseline_value=baseline_value,
        planned_value=planned_value,
        delta=planned_value - baseline_value,
        mapping_status=mapping_status,
        source=source,
        parameter_name=mapping.parameter_name if mapping is not None else None,
        cc=mapping.cc if mapping is not None else None,
    )


def _require_track_blocks(payload: bytes) -> None:
    if len(payload) < TRACK_BLOCK_OFFSETS[-1] + TRACK_BLOCK_LENGTH:
        raise AnalogFourSnapshotMutationPlanError(
            "Analog Four kit record is too short for four track blocks"
        )


def _clamp_midi_value(value: int) -> int:
    return max(VALUE_MIN, min(VALUE_MAX, value))


def _format_change_line(
    track: AnalogFourTrackMutationPlan,
    change: AnalogFourSnapshotPlannedOffsetChange,
) -> str:
    mapping_label = change.mapping_status
    if change.parameter_name is not None and change.cc is not None:
        mapping_label = f"{change.parameter_name} CC{change.cc}, {change.mapping_status}"
    return (
        f"- Track {track.track} {track.name or '<blank>'} / "
        f"Offset +{change.relative_offset} / word {change.word_index}: "
        f"{change.baseline_value} -> {change.planned_value} "
        f"(delta {change.delta:+d}), {mapping_label}"
    )


def _format_scanned_tracks(plan: AnalogFourSnapshotMutationPlan) -> str:
    tracks = tuple(track.track for track in plan.tracks)
    if tracks == tuple(range(1, TRACK_COUNT + 1)):
        return "1-4"
    return ", ".join(str(track) for track in tracks) if tracks else "none"


def _mapping_status_for_changes(
    changes: tuple[AnalogFourSnapshotPlannedOffsetChange, ...],
) -> str:
    statuses = {change.mapping_status for change in changes}
    if not statuses:
        return CANDIDATE_STATUS
    if statuses == {VERIFIED_MAPPING_STATUS}:
        return VERIFIED_MAPPING_STATUS
    if VERIFIED_MAPPING_STATUS in statuses:
        return "mixed_verified_and_candidate"
    return CANDIDATE_STATUS


def _plan_status_for_changes(
    changes: tuple[AnalogFourSnapshotPlannedOffsetChange, ...],
) -> str:
    if not changes:
        return "blocked_no_candidate_offsets"
    mapping_status = _mapping_status_for_changes(changes)
    if mapping_status == VERIFIED_MAPPING_STATUS:
        return "planned_verified_cc_mappings"
    if mapping_status == "mixed_verified_and_candidate":
        return "planned_mixed_saved_offsets"
    return "planned_candidate_offsets"


def _has_verified_mappings(plan: AnalogFourSnapshotMutationPlan) -> bool:
    return any(change.cc is not None for track in plan.tracks for change in track.changes)


def _policy_and_safety_lines(*, has_verified_mappings: bool) -> list[str]:
    mutation_policy = [
        "Mutation policy:",
        "- captured-value relative",
        "- bounded deterministic deltas",
    ]
    if has_verified_mappings:
        mutation_policy.extend(
            [
                "- verified saved offsets may become named CC mock events",
                "- unverified saved offsets remain candidate offsets",
            ]
        )
    else:
        mutation_policy.extend(
            [
                "- candidate offsets only",
                "- no parameter names claimed",
                "- no CC mapping claimed",
            ]
        )
    return [
        *mutation_policy,
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


__all__ = [
    "AnalogFourSnapshotMutationPlan",
    "AnalogFourSnapshotMutationPlanError",
    "AnalogFourSnapshotPlannedOffsetChange",
    "AnalogFourTrackMutationPlan",
    "build_analog_four_snapshot_mutation_plan_from_bytes",
    "build_analog_four_snapshot_mutation_plan_from_file",
    "filter_analog_four_snapshot_mutation_plan_to_track",
    "format_analog_four_snapshot_mutation_plan_error",
    "format_analog_four_snapshot_mutation_plan_report",
]
