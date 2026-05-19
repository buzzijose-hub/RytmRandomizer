"""Passive SysEx kit-bank analysis helpers.

This module reads already-available bytes only. It does not import MIDI
libraries, open ports, request dumps, send messages, or write SysEx data.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from ..observability.errors import DataError
from ..snapshot.rytm_decoder import SysexSnapshotDecodeError, decode_rytm_kit_snapshot_record
from ..snapshot.rytm_mutation_planner import (
    SnapshotMutationPlanError,
    build_snapshot_mutation_plan,
)

KIT_NAME_OFFSET = 15
KIT_NAME_LENGTH = 16
SLOT_INDEX_OFFSET = 9
SNAPSHOT_COMPATIBILITY_KEYS = (
    "allowed_on_pad",
    "machine_disabled",
    "unknown_machine",
    "incompatible_with_pad",
)
SNAPSHOT_READINESS_KEYS = (
    "ready",
    "machine_disabled",
    "unknown_machine",
    "incompatible_with_pad",
    "no_mutable_legal_pads",
)


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
    snapshot_decode_status: str
    snapshot_machine_compatibility_counts: tuple[tuple[str, int], ...]
    snapshot_readiness_counts: tuple[tuple[str, int], ...]
    snapshot_pad_machine_labels: tuple[str, ...]


@dataclass(frozen=True)
class SysexPadMachineUsage:
    """Bank-level machine usage counts for one Rytm pad."""

    pad: int
    machine_counts: tuple[tuple[str, int], ...]


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

    @property
    def snapshot_decoded_slot_count(self) -> int:
        return sum(1 for record in self.records if record.snapshot_pad_machine_labels)

    @property
    def snapshot_machine_compatibility_totals(self) -> dict[str, int]:
        return _sum_count_tuples(
            self.records,
            keys=SNAPSHOT_COMPATIBILITY_KEYS,
            field_name="snapshot_machine_compatibility_counts",
        )

    @property
    def snapshot_readiness_totals(self) -> dict[str, int]:
        return _sum_count_tuples(
            self.records,
            keys=SNAPSHOT_READINESS_KEYS,
            field_name="snapshot_readiness_counts",
        )

    @property
    def snapshot_machine_usage_by_pad(self) -> tuple[SysexPadMachineUsage, ...]:
        counters = [Counter() for _ in range(12)]
        for record in self.records:
            for index, machine_label in enumerate(record.snapshot_pad_machine_labels):
                counters[index][machine_label] += 1
        return tuple(
            SysexPadMachineUsage(
                pad=index + 1,
                machine_counts=tuple(counter.most_common()),
            )
            for index, counter in enumerate(counters)
            if counter
        )


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
    ]

    if analysis.snapshot_decoded_slot_count:
        lines.extend(
            [
                f"Snapshot decoded slots: {analysis.snapshot_decoded_slot_count} / {analysis.record_count}",
                _format_snapshot_machine_compatibility(analysis),
                _format_snapshot_readiness(analysis),
                "Snapshot engine usage by pad:",
            ]
        )
        lines.extend(
            _format_snapshot_machine_usage(usage)
            for usage in analysis.snapshot_machine_usage_by_pad
        )

    lines.append("Kit records:")

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
    snapshot_fields = _snapshot_fields_from_message(message)
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
        snapshot_decode_status=snapshot_fields["status"],
        snapshot_machine_compatibility_counts=snapshot_fields["compatibility_counts"],
        snapshot_readiness_counts=snapshot_fields["readiness_counts"],
        snapshot_pad_machine_labels=snapshot_fields["pad_machine_labels"],
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


def _snapshot_fields_from_message(message: bytes) -> dict[str, object]:
    try:
        snapshot = decode_rytm_kit_snapshot_record(message)
        plan = build_snapshot_mutation_plan(snapshot, depth="micro")
    except (SysexSnapshotDecodeError, SnapshotMutationPlanError):
        return {
            "status": "snapshot_decode_unavailable",
            "compatibility_counts": (),
            "readiness_counts": (),
            "pad_machine_labels": (),
        }

    return {
        "status": "decoded_12_pad_snapshot",
        "compatibility_counts": tuple(snapshot.machine_compatibility_counts.items()),
        "readiness_counts": tuple(plan.readiness_counts.items()),
        "pad_machine_labels": tuple(pad.machine_label for pad in snapshot.pads),
    }


def _sum_count_tuples(
    records: tuple[SysexKitRecord, ...],
    *,
    keys: tuple[str, ...],
    field_name: str,
) -> dict[str, int]:
    totals = dict.fromkeys(keys, 0)
    for record in records:
        for key, value in getattr(record, field_name):
            totals[key] = totals.get(key, 0) + value
    return totals


def _format_snapshot_machine_compatibility(analysis: SysexKitBankAnalysis) -> str:
    totals = analysis.snapshot_machine_compatibility_totals
    return (
        "Snapshot machine compatibility: "
        f"allowed {totals['allowed_on_pad']} / "
        f"disabled {totals['machine_disabled']} / "
        f"unknown {totals['unknown_machine']} / "
        f"incompatible {totals['incompatible_with_pad']}"
    )


def _format_snapshot_readiness(analysis: SysexKitBankAnalysis) -> str:
    totals = analysis.snapshot_readiness_totals
    return (
        "Snapshot readiness: "
        f"ready {totals['ready']} / "
        f"disabled {totals['machine_disabled']} / "
        f"unknown {totals['unknown_machine']} / "
        f"incompatible {totals['incompatible_with_pad']} / "
        f"no mutable legal pads {totals['no_mutable_legal_pads']}"
    )


def _format_snapshot_machine_usage(usage: SysexPadMachineUsage) -> str:
    machine_counts = ", ".join(f"{label} {count}" for label, count in usage.machine_counts)
    return f"- Pad {usage.pad}: {machine_counts}"
