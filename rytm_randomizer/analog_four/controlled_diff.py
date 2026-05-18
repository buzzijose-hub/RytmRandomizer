"""Passive Analog Four controlled saved-kit diff analysis.

This module compares existing before/after SysEx files only. It does not import
MIDI libraries, open ports, request dumps, receive live SysEx, send messages, or
write SysEx data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..observability.errors import DataError
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

CANDIDATE_STATUS = "candidate_unverified"
VALUE_MIN = 0
VALUE_MAX = 127
DEFAULT_LIMIT = 16


class AnalogFourControlledDiffError(DataError, ValueError):
    """Raised when A4 controlled diff analysis cannot run."""


@dataclass(frozen=True)
class AnalogFourControlledOffsetChange:
    """One unverified before/after saved-value change."""

    relative_offset: int
    word_index: int
    before_value: int
    after_value: int
    delta: int
    mapping_status: str


@dataclass(frozen=True)
class AnalogFourControlledDiffReport:
    """Passive controlled diff report for one A4 slot and track."""

    before_path: str | None
    after_path: str | None
    slot: int
    track: int
    midi_channel: int
    wire_channel: int
    before_kit_name: str
    after_kit_name: str
    manufacturer_id: str
    changed_candidate_count: int
    changes: tuple[AnalogFourControlledOffsetChange, ...]


def build_analog_four_controlled_diff_report_from_file(
    before_path: str | Path,
    after_path: str | Path,
    *,
    slot: int,
    track: int,
    limit: int = DEFAULT_LIMIT,
) -> AnalogFourControlledDiffReport:
    """Build a passive controlled diff report from existing SysEx files."""

    report = build_analog_four_controlled_diff_report_from_bytes(
        Path(before_path).read_bytes(),
        Path(after_path).read_bytes(),
        slot=slot,
        track=track,
        limit=limit,
    )
    return AnalogFourControlledDiffReport(
        before_path=str(before_path),
        after_path=str(after_path),
        slot=report.slot,
        track=report.track,
        midi_channel=report.midi_channel,
        wire_channel=report.wire_channel,
        before_kit_name=report.before_kit_name,
        after_kit_name=report.after_kit_name,
        manufacturer_id=report.manufacturer_id,
        changed_candidate_count=report.changed_candidate_count,
        changes=report.changes,
    )


def build_analog_four_controlled_diff_report_from_bytes(
    before_data: bytes,
    after_data: bytes,
    *,
    slot: int,
    track: int,
    limit: int = DEFAULT_LIMIT,
) -> AnalogFourControlledDiffReport:
    """Build a passive controlled diff report from raw SysEx bytes."""

    if slot not in range(1, 129):
        raise AnalogFourControlledDiffError("slot must be 1-128")
    if track not in range(1, 5):
        raise AnalogFourControlledDiffError("track must be 1-4")
    if limit < 1:
        raise AnalogFourControlledDiffError("limit must be at least 1")

    before_record, before_payload = _kit_record_and_payload(before_data, slot=slot)
    after_record, after_payload = _kit_record_and_payload(after_data, slot=slot)
    before_block = _track_block(before_payload, track)
    after_block = _track_block(after_payload, track)

    changes = tuple(
        sorted(
            _changed_words(before_block, after_block),
            key=lambda change: (-abs(change.delta), change.relative_offset),
        )
    )

    return AnalogFourControlledDiffReport(
        before_path=None,
        after_path=None,
        slot=slot,
        track=track,
        midi_channel=track,
        wire_channel=track - 1,
        before_kit_name=_read_ascii_name(before_payload, KIT_NAME_OFFSET, KIT_NAME_LENGTH),
        after_kit_name=_read_ascii_name(after_payload, KIT_NAME_OFFSET, KIT_NAME_LENGTH),
        manufacturer_id=_format_manufacturer_id(before_record),
        changed_candidate_count=len(changes),
        changes=changes[:limit],
    )


def format_analog_four_controlled_diff_report(
    report: AnalogFourControlledDiffReport,
) -> list[str]:
    """Format a deterministic passive A4 controlled diff report."""

    lines = [
        "RytmRandomizer passive Analog Four controlled diff report",
        f"Before path: {report.before_path or '<bytes>'}",
        f"After path: {report.after_path or '<bytes>'}",
        f"Slot: {report.slot}",
        f"Track: {report.track}",
        f"MIDI channel: {report.midi_channel}",
        f"Wire channel: {report.wire_channel}",
        f"Before kit: {report.before_kit_name or '<blank>'}",
        f"After kit: {report.after_kit_name or '<blank>'}",
        f"Manufacturer ID: {report.manufacturer_id}",
        f"Changed candidates reported: {len(report.changes)} / {report.changed_candidate_count}",
        "Changed offset candidates:",
    ]
    if not report.changes:
        lines.append("- none found")
    for change in report.changes:
        lines.append(_format_change_line(change))
    lines.extend(_safety_lines())
    return lines


def format_analog_four_controlled_diff_error(message: str) -> list[str]:
    """Format deterministic passive A4 controlled diff error lines."""

    return [
        "RytmRandomizer passive Analog Four controlled diff report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        *_safety_lines(),
    ]


def _kit_record_and_payload(data: bytes, *, slot: int) -> tuple[bytes, bytes]:
    try:
        record = _find_kit_record(data, slot=slot)
        _validate_a4_kit_record(record)
    except AnalogFourSnapshotDecodeError as exc:
        raise AnalogFourControlledDiffError(str(exc)) from exc
    return record, _unpack_elektron_7bit(record[KIT_HEADER_LENGTH:-1])


def _track_block(payload: bytes, track: int) -> bytes:
    block_offset = TRACK_BLOCK_OFFSETS[track - 1]
    if len(payload) < block_offset + TRACK_BLOCK_LENGTH:
        raise AnalogFourControlledDiffError(
            "Analog Four kit record is too short for four track blocks"
        )
    return payload[block_offset : block_offset + TRACK_BLOCK_LENGTH]


def _changed_words(
    before_block: bytes,
    after_block: bytes,
) -> tuple[AnalogFourControlledOffsetChange, ...]:
    changes = []
    max_length = min(len(before_block), len(after_block))
    for relative_offset in range(TRACK_NAME_LENGTH, max_length - 1, 2):
        before_value = (before_block[relative_offset] << 8) | before_block[relative_offset + 1]
        after_value = (after_block[relative_offset] << 8) | after_block[relative_offset + 1]
        if before_value == after_value:
            continue
        if not (VALUE_MIN <= before_value <= VALUE_MAX and VALUE_MIN <= after_value <= VALUE_MAX):
            continue
        changes.append(
            AnalogFourControlledOffsetChange(
                relative_offset=relative_offset,
                word_index=relative_offset // 2,
                before_value=before_value,
                after_value=after_value,
                delta=after_value - before_value,
                mapping_status=CANDIDATE_STATUS,
            )
        )
    return tuple(changes)


def _format_change_line(change: AnalogFourControlledOffsetChange) -> str:
    return (
        f"- Offset +{change.relative_offset} / word {change.word_index}: "
        f"{change.before_value} -> {change.after_value} "
        f"(delta {change.delta:+d}), {change.mapping_status}"
    )


def _safety_lines() -> list[str]:
    return [
        "Safety:",
        "- passive/read-only",
        "- controlled comparison only",
        "- candidate offsets only",
        "- no parameter names claimed",
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
    "AnalogFourControlledDiffError",
    "AnalogFourControlledDiffReport",
    "AnalogFourControlledOffsetChange",
    "build_analog_four_controlled_diff_report_from_bytes",
    "build_analog_four_controlled_diff_report_from_file",
    "format_analog_four_controlled_diff_error",
    "format_analog_four_controlled_diff_report",
]
