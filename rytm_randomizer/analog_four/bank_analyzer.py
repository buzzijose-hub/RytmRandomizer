"""Passive Analog Four kit-bank readiness analysis.

This module reads already-available bytes only. It does not import MIDI
libraries, open ports, request dumps, receive live SysEx, send messages, or
write SysEx data.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from ..observability.errors import DataError
from .offset_candidates import CANDIDATE_STATUS
from .snapshot_decoder import (
    AnalogFourSnapshotDecodeError,
    decode_analog_four_kit_snapshot_bytes,
)
from .snapshot_mutation_planner import (
    AnalogFourSnapshotMutationPlanError,
    build_analog_four_snapshot_mutation_plan_from_bytes,
)

A4_DEVICE_FAMILY = 0x06
KIT_OBJECT_TYPE = 0x52
SLOT_INDEX_OFFSET = 9
TRACK_COUNT = 4
MAX_TRACK_NAME_USAGE_ITEMS = 12


class AnalogFourKitBankAnalysisError(DataError, ValueError):
    """Raised when bytes cannot be analyzed as an Analog Four kit bank."""


@dataclass(frozen=True)
class AnalogFourKitBankRecord:
    """Passive bank metadata for one decoded Analog Four kit record."""

    slot_number: int
    header_slot_index: int
    offset: int
    length: int
    kit_name: str
    track_names: tuple[str, ...]
    planned_track_count: int
    blocked_track_count: int
    planned_candidate_change_count: int
    sha256_12: str


@dataclass(frozen=True)
class AnalogFourTrackNameUsage:
    """Bank-level track-name usage counts for one A4 track."""

    track: int
    name_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class AnalogFourKitBankAnalysis:
    """Passive summary for Analog Four kit snapshots inside a SysEx file."""

    complete_sysex_message_count: int
    kit_record_count: int
    records: tuple[AnalogFourKitBankRecord, ...]

    @property
    def decoded_snapshot_count(self) -> int:
        return len(self.records)

    @property
    def planned_track_count(self) -> int:
        return sum(record.planned_track_count for record in self.records)

    @property
    def blocked_track_count(self) -> int:
        return sum(record.blocked_track_count for record in self.records)

    @property
    def scanned_track_count(self) -> int:
        return self.decoded_snapshot_count * TRACK_COUNT

    @property
    def planned_candidate_change_count(self) -> int:
        return sum(record.planned_candidate_change_count for record in self.records)

    @property
    def track_name_usage(self) -> tuple[AnalogFourTrackNameUsage, ...]:
        counters = [Counter() for _ in range(TRACK_COUNT)]
        for record in self.records:
            for index, name in enumerate(record.track_names):
                counters[index][name or "<blank>"] += 1
        return tuple(
            AnalogFourTrackNameUsage(
                track=index + 1,
                name_counts=tuple(counter.most_common()),
            )
            for index, counter in enumerate(counters)
            if counter
        )


def analyze_analog_four_kit_bank_file(path: str | Path) -> AnalogFourKitBankAnalysis:
    """Analyze an existing Analog Four SysEx file without touching hardware."""

    return analyze_analog_four_kit_bank_bytes(Path(path).read_bytes())


def analyze_analog_four_kit_bank_bytes(data: bytes) -> AnalogFourKitBankAnalysis:
    """Return passive bank-level readiness from raw Analog Four SysEx bytes."""

    messages = _split_complete_sysex_messages(data)
    kit_records = tuple(
        _record_from_message(offset, message)
        for offset, message in messages
        if _is_a4_kit_record(message)
    )
    if not kit_records:
        raise AnalogFourKitBankAnalysisError("no Analog Four kit records found")
    return AnalogFourKitBankAnalysis(
        complete_sysex_message_count=len(messages),
        kit_record_count=len(kit_records),
        records=kit_records,
    )


def format_analog_four_kit_bank_report(analysis: AnalogFourKitBankAnalysis) -> list[str]:
    """Format a deterministic passive Analog Four kit-bank report."""

    lines = [
        "RytmRandomizer passive Analog Four kit bank report",
        f"Complete SysEx messages: {analysis.complete_sysex_message_count}",
        f"Analog Four kit records: {analysis.kit_record_count}",
        f"Decoded kit snapshots: {analysis.decoded_snapshot_count} / {analysis.kit_record_count}",
        (
            "Snapshot tracks: "
            f"planned {analysis.planned_track_count} / "
            f"blocked {analysis.blocked_track_count} / "
            f"total {analysis.scanned_track_count}"
        ),
        f"Planned candidate changes: {analysis.planned_candidate_change_count}",
        f"Candidate status: {CANDIDATE_STATUS}",
        "Track name usage:",
    ]
    lines.extend(_format_track_name_usage(usage) for usage in analysis.track_name_usage)
    lines.append("Kit records:")
    for record in analysis.records:
        lines.append(
            f"- Slot {record.slot_number}: {record.kit_name or '<blank>'} / "
            f"tracks {', '.join(record.track_names)} / "
            f"planned tracks {record.planned_track_count} / "
            f"candidate changes {record.planned_candidate_change_count} / "
            f"bytes {record.length}"
        )
    lines.extend(_policy_and_safety_lines())
    return lines


def format_analog_four_kit_bank_error(path: str | Path, message: str) -> list[str]:
    """Format deterministic passive Analog Four kit-bank errors."""

    return [
        "RytmRandomizer passive Analog Four kit bank report",
        f"Path: {path}",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
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


def _record_from_message(offset: int, message: bytes) -> AnalogFourKitBankRecord:
    header_slot_index = message[SLOT_INDEX_OFFSET]
    slot_number = header_slot_index + 1
    try:
        snapshot = decode_analog_four_kit_snapshot_bytes(message, slot=slot_number)
        plan = build_analog_four_snapshot_mutation_plan_from_bytes(
            message,
            slot=slot_number,
            depth="micro",
        )
    except (AnalogFourSnapshotDecodeError, AnalogFourSnapshotMutationPlanError) as exc:
        raise AnalogFourKitBankAnalysisError(str(exc)) from exc

    return AnalogFourKitBankRecord(
        slot_number=slot_number,
        header_slot_index=header_slot_index,
        offset=offset,
        length=len(message),
        kit_name=snapshot.kit_name,
        track_names=tuple(track.name or "<blank>" for track in snapshot.tracks),
        planned_track_count=plan.planned_track_count,
        blocked_track_count=plan.blocked_track_count,
        planned_candidate_change_count=plan.planned_change_count,
        sha256_12=sha256(message).hexdigest().upper()[:12],
    )


def _split_complete_sysex_messages(data: bytes) -> tuple[tuple[int, bytes], ...]:
    messages: list[tuple[int, bytes]] = []
    cursor = 0
    while True:
        start = data.find(bytes([0xF0]), cursor)
        if start == -1:
            break
        end = data.find(bytes([0xF7]), start + 1)
        if end == -1:
            break
        messages.append((start, data[start : end + 1]))
        cursor = end + 1
    if not messages:
        raise AnalogFourKitBankAnalysisError("no complete SysEx messages found")
    return tuple(messages)


def _is_a4_kit_record(message: bytes) -> bool:
    return (
        len(message) > SLOT_INDEX_OFFSET
        and message[0] == 0xF0
        and message[-1] == 0xF7
        and message[1:4] == bytes([0x00, 0x20, 0x3C])
        and message[4] == A4_DEVICE_FAMILY
        and message[6] == KIT_OBJECT_TYPE
    )


def _format_track_name_usage(usage: AnalogFourTrackNameUsage) -> str:
    shown = usage.name_counts[:MAX_TRACK_NAME_USAGE_ITEMS]
    name_counts = ", ".join(f"{name} {count}" for name, count in shown)
    hidden_count = len(usage.name_counts) - len(shown)
    if hidden_count:
        name_counts = f"{name_counts}, ... {hidden_count} more"
    return f"- Track {usage.track}: {name_counts}"


def _policy_and_safety_lines() -> list[str]:
    return [
        "Mutation policy:",
        "- captured-value relative",
        "- bounded deterministic deltas",
        "- candidate offsets only",
        "- no parameter names claimed",
        "- no CC mapping claimed",
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
    "AnalogFourKitBankAnalysis",
    "AnalogFourKitBankAnalysisError",
    "AnalogFourKitBankRecord",
    "AnalogFourTrackNameUsage",
    "analyze_analog_four_kit_bank_bytes",
    "analyze_analog_four_kit_bank_file",
    "format_analog_four_kit_bank_error",
    "format_analog_four_kit_bank_report",
]
