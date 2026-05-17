"""Passive SysEx whole-project analysis helpers.

This module reads already-available bytes only. It does not import MIDI
libraries, open ports, request dumps, send messages, receive SysEx, or write
SysEx data.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from .observability.errors import DataError

DEVICE_FAMILY_OFFSET = 4
OBJECT_TYPE_OFFSET = 6
SLOT_INDEX_OFFSET = 9

DEVICE_LABELS = {
    0x06: "Analog Four MKII",
    0x07: "Analog Rytm MKII",
}

OBJECT_TYPE_LABELS = {
    0x52: "kits",
    0x53: "sounds",
    0x54: "patterns",
    0x55: "songs_or_project_slots",
    0x56: "project_settings",
    0x57: "global_slots",
}


class SysexProjectAnalysisError(DataError, ValueError):
    """Raised when bytes do not contain complete SysEx project records."""


@dataclass(frozen=True)
class SysexProjectRecord:
    """Metadata for one passive SysEx project record."""

    record_number: int
    offset: int
    length: int
    manufacturer_id: str
    device_family_byte: int | None
    object_type: int | None
    object_label: str
    header_slot_index: int | None
    slot_number: int | None
    starts_with_f0: bool
    ends_with_f7: bool
    sha256_12: str


@dataclass(frozen=True)
class SysexProjectRecordGroup:
    """Summary for project records sharing type and length."""

    object_type: int | None
    label: str
    count: int
    record_length: int
    slot_numbers: tuple[int, ...]
    first_offset: int
    last_offset: int


@dataclass(frozen=True)
class SysexProjectAnalysis:
    """Passive summary for a whole-project SysEx dump."""

    record_count: int
    valid_sysex_boundaries: bool
    complete_stream: bool
    leading_bytes: int
    trailing_bytes: int
    manufacturer_id: str
    device_family_byte: int | None
    device_label: str
    record_groups: tuple[SysexProjectRecordGroup, ...]
    records: tuple[SysexProjectRecord, ...]


def analyze_sysex_project_file(path: str | Path) -> SysexProjectAnalysis:
    """Analyze an existing SysEx file without opening MIDI ports or mutating hardware."""

    return analyze_sysex_project_bytes(Path(path).read_bytes())


def analyze_sysex_project_bytes(data: bytes) -> SysexProjectAnalysis:
    """Return passive project metadata from raw SysEx bytes."""

    messages = _split_complete_sysex_messages(data)
    records = tuple(
        _record_from_message(record_number, offset, message)
        for record_number, offset, message in messages
    )
    first_start = messages[0][1]
    last_end = messages[-1][1] + len(messages[-1][2])
    leading_bytes = first_start
    trailing_bytes = len(data) - last_end
    device_family = _first_present(record.device_family_byte for record in records)

    return SysexProjectAnalysis(
        record_count=len(records),
        valid_sysex_boundaries=all(
            record.starts_with_f0 and record.ends_with_f7 for record in records
        ),
        complete_stream=leading_bytes == 0 and trailing_bytes == 0,
        leading_bytes=leading_bytes,
        trailing_bytes=trailing_bytes,
        manufacturer_id=records[0].manufacturer_id,
        device_family_byte=device_family,
        device_label=_device_label(device_family),
        record_groups=_group_records(records),
        records=records,
    )


def format_sysex_project_report(analysis: SysexProjectAnalysis) -> list[str]:
    """Format a deterministic passive SysEx project report."""

    device_family = (
        f"{analysis.device_family_byte:02X}"
        if analysis.device_family_byte is not None
        else "<unknown>"
    )
    lines = [
        "RytmRandomizer passive SysEx project report",
        f"Device: {analysis.device_label}",
        f"Device family byte: {device_family}",
        f"Manufacturer ID: {analysis.manufacturer_id}",
        f"Complete SysEx records: {analysis.record_count}",
        f"Complete stream: {analysis.complete_stream}",
        f"Valid SysEx boundaries: {analysis.valid_sysex_boundaries}",
        f"Leading bytes before first SysEx: {analysis.leading_bytes}",
        f"Trailing bytes after last SysEx: {analysis.trailing_bytes}",
        "Record groups:",
    ]

    for group in analysis.record_groups:
        lines.append(
            f"- {group.label}: {group.count} record(s), {group.record_length} bytes each, "
            f"slots {_format_slot_ranges(group.slot_numbers)}"
        )

    lines.extend(
        [
            "Live Snapshot relevance:",
            *_snapshot_relevance_lines(analysis.record_groups),
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
    return lines


def _split_complete_sysex_messages(data: bytes) -> tuple[tuple[int, int, bytes], ...]:
    messages: list[tuple[int, int, bytes]] = []
    cursor = 0

    while True:
        start = data.find(bytes([0xF0]), cursor)
        if start == -1:
            break
        end = data.find(bytes([0xF7]), start + 1)
        if end == -1:
            break
        record_number = len(messages) + 1
        messages.append((record_number, start, data[start : end + 1]))
        cursor = end + 1

    if not messages:
        raise SysexProjectAnalysisError("no complete SysEx messages found")

    return tuple(messages)


def _record_from_message(
    record_number: int, offset: int, message: bytes
) -> SysexProjectRecord:
    device_family = (
        message[DEVICE_FAMILY_OFFSET] if len(message) > DEVICE_FAMILY_OFFSET else None
    )
    object_type = message[OBJECT_TYPE_OFFSET] if len(message) > OBJECT_TYPE_OFFSET else None
    header_slot_index = message[SLOT_INDEX_OFFSET] if len(message) > SLOT_INDEX_OFFSET else None
    return SysexProjectRecord(
        record_number=record_number,
        offset=offset,
        length=len(message),
        manufacturer_id=_format_manufacturer_id(message),
        device_family_byte=device_family,
        object_type=object_type,
        object_label=_object_label(object_type),
        header_slot_index=header_slot_index,
        slot_number=header_slot_index + 1 if header_slot_index is not None else None,
        starts_with_f0=bool(message and message[0] == 0xF0),
        ends_with_f7=bool(message and message[-1] == 0xF7),
        sha256_12=sha256(message).hexdigest().upper()[:12],
    )


def _group_records(
    records: tuple[SysexProjectRecord, ...],
) -> tuple[SysexProjectRecordGroup, ...]:
    groups: dict[tuple[int | None, int], list[SysexProjectRecord]] = {}
    for record in records:
        groups.setdefault((record.object_type, record.length), []).append(record)

    result: list[SysexProjectRecordGroup] = []
    for (_object_type, _length), group_records in groups.items():
        first = group_records[0]
        result.append(
            SysexProjectRecordGroup(
                object_type=first.object_type,
                label=first.object_label,
                count=len(group_records),
                record_length=first.length,
                slot_numbers=tuple(
                    record.slot_number
                    for record in group_records
                    if record.slot_number is not None
                ),
                first_offset=first.offset,
                last_offset=group_records[-1].offset,
            )
        )
    return tuple(sorted(result, key=lambda group: group.first_offset))


def _snapshot_relevance_lines(
    record_groups: tuple[SysexProjectRecordGroup, ...],
) -> list[str]:
    labels = {group.label for group in record_groups}
    lines: list[str] = []
    if "kits" in labels:
        lines.append("- contains kit records")
    if "sounds" in labels:
        lines.append("- contains sound records")
    if "patterns" in labels:
        lines.append("- contains pattern records")
    if labels.intersection({"project_settings", "global_slots", "songs_or_project_slots"}):
        lines.append("- contains project/global records")
    lines.append("- suitable raw source for future Live Snapshot decode")
    return lines


def _format_manufacturer_id(message: bytes) -> str:
    if len(message) < 4:
        return "<unknown>"
    return " ".join(f"{byte:02X}" for byte in message[1:4])


def _device_label(device_family: int | None) -> str:
    if device_family is None:
        return "<unknown>"
    return DEVICE_LABELS.get(device_family, f"unknown_0x{device_family:02X}")


def _object_label(object_type: int | None) -> str:
    if object_type is None:
        return "unknown"
    return OBJECT_TYPE_LABELS.get(object_type, f"unknown_0x{object_type:02X}")


def _first_present(values) -> int | None:
    for value in values:
        if value is not None:
            return value
    return None


def _format_slot_ranges(slots: tuple[int, ...]) -> str:
    if not slots:
        return "none"

    ranges: list[str] = []
    start = slots[0]
    previous = slots[0]
    for slot in slots[1:]:
        if slot == previous + 1:
            previous = slot
            continue
        ranges.append(_format_range(start, previous))
        start = previous = slot
    ranges.append(_format_range(start, previous))
    return ", ".join(ranges)


def _format_range(start: int, end: int) -> str:
    return str(start) if start == end else f"{start}-{end}"
