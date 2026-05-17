"""Passive SysEx kit-bank analysis helpers.

This module reads already-available bytes only. It does not import MIDI
libraries, open ports, request dumps, send messages, or write SysEx data.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from .observability.errors import DataError

KIT_NAME_OFFSET = 15
KIT_NAME_LENGTH = 16
SLOT_INDEX_OFFSET = 9


class SysexBankAnalysisError(DataError, ValueError):
    """Raised when bytes do not contain a complete SysEx kit-bank message."""


@dataclass(frozen=True)
class SysexKitRecord:
    """Metadata for one passive SysEx kit record."""

    slot_number: int
    header_slot_index: int | None
    offset: int
    length: int
    name: str
    starts_with_f0: bool
    ends_with_f7: bool
    sha256_12: str
    normalized_sha256_12: str
    payload_nonzero_count: int


@dataclass(frozen=True)
class SysexKitBankAnalysis:
    """Passive summary for a SysEx kit bank."""

    record_count: int
    record_length: int | None
    fixed_length_records: bool
    valid_sysex_boundaries: bool
    manufacturer_id: str
    records: tuple[SysexKitRecord, ...]
    nonblank_slots: tuple[int, ...]
    blank_candidate_slots: tuple[int, ...]
    largest_duplicate_group_slots: tuple[int, ...]


def analyze_sysex_kit_bank_file(path: str | Path) -> SysexKitBankAnalysis:
    """Analyze an existing SysEx file without opening MIDI ports or mutating hardware."""

    return analyze_sysex_kit_bank_bytes(Path(path).read_bytes())


def analyze_sysex_kit_bank_bytes(data: bytes) -> SysexKitBankAnalysis:
    """Return passive kit-bank metadata from raw SysEx bytes."""

    messages = _split_complete_sysex_messages(data)
    records = tuple(
        _record_from_message(slot, offset, message) for slot, offset, message in messages
    )
    lengths = {record.length for record in records}
    fixed_length = len(lengths) == 1
    record_length = records[0].length if fixed_length else None
    valid_boundaries = all(record.starts_with_f0 and record.ends_with_f7 for record in records)
    manufacturer_id = _format_manufacturer_id(messages[0][2])
    largest_duplicate_group = _largest_normalized_duplicate_group(records)
    blank_candidates = _blank_candidate_slots(records, largest_duplicate_group)
    blank_set = set(blank_candidates)

    return SysexKitBankAnalysis(
        record_count=len(records),
        record_length=record_length,
        fixed_length_records=fixed_length,
        valid_sysex_boundaries=valid_boundaries,
        manufacturer_id=manufacturer_id,
        records=records,
        nonblank_slots=tuple(
            record.slot_number for record in records if record.slot_number not in blank_set
        ),
        blank_candidate_slots=blank_candidates,
        largest_duplicate_group_slots=largest_duplicate_group,
    )


def format_sysex_kit_bank_report(analysis: SysexKitBankAnalysis) -> list[str]:
    """Format a deterministic passive SysEx kit-bank report."""

    lines = [
        "RytmRandomizer passive SysEx kit bank report",
        f"Record count: {analysis.record_count}",
        f"Record length: {_format_optional_int(analysis.record_length)}",
        f"Fixed-length records: {analysis.fixed_length_records}",
        f"Valid SysEx boundaries: {analysis.valid_sysex_boundaries}",
        f"Manufacturer ID: {analysis.manufacturer_id}",
        f"Nonblank kit slots: {_format_slot_ranges(analysis.nonblank_slots)}",
        f"Blank/default candidate slots: {_format_slot_ranges(analysis.blank_candidate_slots)}",
        (
            "Largest duplicate normalized group: "
            f"{_format_slot_ranges(analysis.largest_duplicate_group_slots)}"
        ),
        "Kit records:",
    ]

    for record in analysis.records:
        name = record.name or "<blank>"
        header_index = (
            str(record.header_slot_index) if record.header_slot_index is not None else "<missing>"
        )
        lines.append(
            f"- Slot {record.slot_number}: {name} / header index {header_index} / "
            f"offset {record.offset} / bytes {record.length}"
        )

    lines.extend(
        [
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
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
        slot_number = len(messages) + 1
        messages.append((slot_number, start, data[start : end + 1]))
        cursor = end + 1

    if not messages:
        raise SysexBankAnalysisError("no complete SysEx messages found")

    return tuple(messages)


def _record_from_message(slot_number: int, offset: int, message: bytes) -> SysexKitRecord:
    normalized = bytearray(message)
    header_slot_index = message[SLOT_INDEX_OFFSET] if len(message) > SLOT_INDEX_OFFSET else None
    if len(normalized) > SLOT_INDEX_OFFSET:
        normalized[SLOT_INDEX_OFFSET] = 0

    payload = message[32:-1] if len(message) > 33 else b""
    return SysexKitRecord(
        slot_number=slot_number,
        header_slot_index=header_slot_index,
        offset=offset,
        length=len(message),
        name=_decode_name(message),
        starts_with_f0=bool(message and message[0] == 0xF0),
        ends_with_f7=bool(message and message[-1] == 0xF7),
        sha256_12=sha256(message).hexdigest().upper()[:12],
        normalized_sha256_12=sha256(bytes(normalized)).hexdigest().upper()[:12],
        payload_nonzero_count=sum(1 for byte in payload if byte != 0),
    )


def _decode_name(message: bytes) -> str:
    field = message[KIT_NAME_OFFSET : KIT_NAME_OFFSET + KIT_NAME_LENGTH]
    printable = bytes(byte for byte in field if 32 <= byte <= 126)
    return printable.decode("ascii").strip()


def _format_manufacturer_id(message: bytes) -> str:
    if len(message) < 4:
        return "<unknown>"
    return " ".join(f"{byte:02X}" for byte in message[1:4])


def _largest_normalized_duplicate_group(
    records: tuple[SysexKitRecord, ...],
) -> tuple[int, ...]:
    groups: dict[str, list[int]] = {}
    for record in records:
        groups.setdefault(record.normalized_sha256_12, []).append(record.slot_number)

    duplicate_groups = [tuple(slots) for slots in groups.values() if len(slots) > 1]
    if not duplicate_groups:
        return ()
    return max(duplicate_groups, key=lambda slots: (len(slots), -slots[0]))


def _blank_candidate_slots(
    records: tuple[SysexKitRecord, ...],
    largest_duplicate_group: tuple[int, ...],
) -> tuple[int, ...]:
    if not largest_duplicate_group:
        return ()
    record_by_slot = {record.slot_number: record for record in records}
    if all(record_by_slot[slot].name == "" for slot in largest_duplicate_group):
        return largest_duplicate_group
    return ()


def _format_optional_int(value: int | None) -> str:
    return str(value) if value is not None else "<mixed>"


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
