"""Passive Analog Four saved-kit offset candidate analysis.

This module scans existing Analog Four kit records for varying CC-like words in
track blocks. It does not name parameters, import MIDI libraries, open ports,
send messages, receive live SysEx, or write SysEx data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .analog_four_snapshot_decoder import (
    A4_DEVICE_FAMILY,
    KIT_HEADER_LENGTH,
    KIT_OBJECT_TYPE,
    SLOT_INDEX_OFFSET,
    TRACK_BLOCK_LENGTH,
    TRACK_BLOCK_OFFSETS,
    TRACK_NAME_LENGTH,
    _format_manufacturer_id,
    _read_ascii_name,
    _split_complete_sysex_messages,
    _unpack_elektron_7bit,
)
from .observability.errors import DataError

CANDIDATE_STATUS = "candidate_unverified"
VALUE_MIN = 0
VALUE_MAX = 127
DEFAULT_LIMIT = 12


class AnalogFourOffsetCandidateError(DataError, ValueError):
    """Raised when A4 offset candidate analysis cannot run."""


@dataclass(frozen=True)
class AnalogFourOffsetCandidate:
    """One unverified saved-value offset candidate."""

    relative_offset: int
    word_index: int
    sample_count: int
    unique_value_count: int
    min_value: int
    max_value: int
    zero_count: int
    values_preview: tuple[int, ...]
    mapping_status: str


@dataclass(frozen=True)
class AnalogFourOffsetCandidateReport:
    """Passive offset-candidate report for one A4 track across saved kits."""

    source_path: str | None
    track: int
    midi_channel: int
    wire_channel: int
    kit_count: int
    manufacturer_id: str
    candidate_count: int
    candidates: tuple[AnalogFourOffsetCandidate, ...]


@dataclass(frozen=True)
class AnalogFourAllTrackOffsetCandidateReport:
    """Passive offset-candidate report for all four A4 tracks."""

    source_path: str | None
    kit_count: int
    manufacturer_id: str
    track_reports: tuple[AnalogFourOffsetCandidateReport, ...]


def build_analog_four_offset_candidate_report_from_file(
    path: str | Path,
    *,
    track: int,
    limit: int = DEFAULT_LIMIT,
) -> AnalogFourOffsetCandidateReport:
    """Build a passive offset-candidate report from an existing SysEx file."""

    report = build_analog_four_offset_candidate_report_from_bytes(
        Path(path).read_bytes(),
        track=track,
        limit=limit,
    )
    return AnalogFourOffsetCandidateReport(
        source_path=str(path),
        track=report.track,
        midi_channel=report.midi_channel,
        wire_channel=report.wire_channel,
        kit_count=report.kit_count,
        manufacturer_id=report.manufacturer_id,
        candidate_count=report.candidate_count,
        candidates=report.candidates,
    )


def build_analog_four_offset_candidate_report_from_bytes(
    data: bytes,
    *,
    track: int,
    limit: int = DEFAULT_LIMIT,
) -> AnalogFourOffsetCandidateReport:
    """Build a passive offset-candidate report from raw SysEx bytes."""

    if track not in range(1, 5):
        raise AnalogFourOffsetCandidateError("track must be 1-4")
    if limit < 1:
        raise AnalogFourOffsetCandidateError("limit must be at least 1")

    records = _a4_kit_records(data)
    if not records:
        raise AnalogFourOffsetCandidateError("no Analog Four kit records found")

    values_by_offset: dict[int, list[int]] = {}
    for record in records:
        payload = _unpack_elektron_7bit(record[KIT_HEADER_LENGTH:-1])
        block = _track_block(payload, track)
        for relative_offset, value in _cc_like_words(block):
            values_by_offset.setdefault(relative_offset, []).append(value)

    candidates = tuple(
        sorted(
            (
                _candidate_from_values(relative_offset, values)
                for relative_offset, values in values_by_offset.items()
                if len(set(values)) > 1
            ),
            key=lambda candidate: (
                -candidate.unique_value_count,
                -(candidate.max_value - candidate.min_value),
                candidate.relative_offset,
            ),
        )
    )

    first_record = records[0]
    return AnalogFourOffsetCandidateReport(
        source_path=None,
        track=track,
        midi_channel=track,
        wire_channel=track - 1,
        kit_count=len(records),
        manufacturer_id=_format_manufacturer_id(first_record),
        candidate_count=len(candidates),
        candidates=candidates[:limit],
    )


def build_analog_four_all_track_offset_candidate_report_from_file(
    path: str | Path,
    *,
    limit: int = DEFAULT_LIMIT,
) -> AnalogFourAllTrackOffsetCandidateReport:
    """Build a passive all-track offset-candidate report from a SysEx file."""

    report = build_analog_four_all_track_offset_candidate_report_from_bytes(
        Path(path).read_bytes(),
        limit=limit,
    )
    return AnalogFourAllTrackOffsetCandidateReport(
        source_path=str(path),
        kit_count=report.kit_count,
        manufacturer_id=report.manufacturer_id,
        track_reports=report.track_reports,
    )


def build_analog_four_all_track_offset_candidate_report_from_bytes(
    data: bytes,
    *,
    limit: int = DEFAULT_LIMIT,
) -> AnalogFourAllTrackOffsetCandidateReport:
    """Build a passive offset-candidate report for A4 Tracks 1-4."""

    if limit < 1:
        raise AnalogFourOffsetCandidateError("limit must be at least 1")

    track_reports = tuple(
        build_analog_four_offset_candidate_report_from_bytes(
            data,
            track=track,
            limit=limit,
        )
        for track in range(1, 5)
    )
    first_report = track_reports[0]
    return AnalogFourAllTrackOffsetCandidateReport(
        source_path=None,
        kit_count=first_report.kit_count,
        manufacturer_id=first_report.manufacturer_id,
        track_reports=track_reports,
    )


def format_analog_four_offset_candidate_report(
    report: AnalogFourOffsetCandidateReport,
) -> list[str]:
    """Format a deterministic passive A4 offset-candidate report."""

    lines = [
        "RytmRandomizer passive Analog Four offset candidate report",
        f"Source path: {report.source_path or '<bytes>'}",
        f"Track: {report.track}",
        f"MIDI channel: {report.midi_channel}",
        f"Wire channel: {report.wire_channel}",
        f"Kit records scanned: {report.kit_count}",
        f"Manufacturer ID: {report.manufacturer_id}",
        f"Candidates reported: {len(report.candidates)} / {report.candidate_count}",
        "Offset candidates:",
    ]
    if not report.candidates:
        lines.append("- none found")
    for candidate in report.candidates:
        lines.append(_format_candidate_line(candidate))
    lines.extend(_safety_lines())
    return lines


def format_analog_four_all_track_offset_candidate_report(
    report: AnalogFourAllTrackOffsetCandidateReport,
) -> list[str]:
    """Format a deterministic passive all-track A4 offset-candidate report."""

    lines = [
        "RytmRandomizer passive Analog Four all-track offset candidate report",
        f"Source path: {report.source_path or '<bytes>'}",
        "Tracks scanned: 1-4",
        f"Kit records scanned: {report.kit_count}",
        f"Manufacturer ID: {report.manufacturer_id}",
        "Track summaries:",
    ]
    for track_report in report.track_reports:
        lines.append(
            f"Track {track_report.track} / MIDI channel {track_report.midi_channel} "
            f"/ wire channel {track_report.wire_channel}"
        )
        lines.append(
            f"Candidates reported: {len(track_report.candidates)} / "
            f"{track_report.candidate_count}"
        )
        if not track_report.candidates:
            lines.append("- none found")
        for candidate in track_report.candidates:
            lines.append(_format_candidate_line(candidate))
    lines.extend(_safety_lines())
    return lines


def format_analog_four_offset_candidate_error(path: str | Path, message: str) -> list[str]:
    """Format deterministic passive A4 offset-candidate error lines."""

    return [
        "RytmRandomizer passive Analog Four offset candidate report",
        f"Path: {path}",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        *_safety_lines(),
    ]


def _a4_kit_records(data: bytes) -> tuple[bytes, ...]:
    return tuple(
        record
        for record in _split_complete_sysex_messages(data)
        if (
            len(record) > SLOT_INDEX_OFFSET
            and record[4] == A4_DEVICE_FAMILY
            and record[6] == KIT_OBJECT_TYPE
        )
    )


def _track_block(payload: bytes, track: int) -> bytes:
    block_offset = TRACK_BLOCK_OFFSETS[track - 1]
    if len(payload) < block_offset + TRACK_BLOCK_LENGTH:
        raise AnalogFourOffsetCandidateError(
            "Analog Four kit record is too short for four track blocks"
        )
    return payload[block_offset : block_offset + TRACK_BLOCK_LENGTH]


def _cc_like_words(block: bytes) -> tuple[tuple[int, int], ...]:
    words = []
    for relative_offset in range(TRACK_NAME_LENGTH, len(block) - 1, 2):
        value = (block[relative_offset] << 8) | block[relative_offset + 1]
        if VALUE_MIN <= value <= VALUE_MAX:
            words.append((relative_offset, value))
    return tuple(words)


def _candidate_from_values(
    relative_offset: int,
    values: list[int],
) -> AnalogFourOffsetCandidate:
    unique_values = tuple(dict.fromkeys(values))
    return AnalogFourOffsetCandidate(
        relative_offset=relative_offset,
        word_index=relative_offset // 2,
        sample_count=len(values),
        unique_value_count=len(set(values)),
        min_value=min(values),
        max_value=max(values),
        zero_count=sum(1 for value in values if value == 0),
        values_preview=unique_values[:8],
        mapping_status=CANDIDATE_STATUS,
    )


def _format_candidate_line(candidate: AnalogFourOffsetCandidate) -> str:
    preview = ", ".join(str(value) for value in candidate.values_preview)
    return (
        f"- Offset +{candidate.relative_offset} / word {candidate.word_index}: "
        f"samples {candidate.sample_count}, unique {candidate.unique_value_count}, "
        f"range {candidate.min_value}-{candidate.max_value}, zeros {candidate.zero_count}, "
        f"values {preview}, {candidate.mapping_status}"
    )


def _safety_lines() -> list[str]:
    return [
        "Safety:",
        "- passive/read-only",
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
    "AnalogFourAllTrackOffsetCandidateReport",
    "AnalogFourOffsetCandidate",
    "AnalogFourOffsetCandidateError",
    "AnalogFourOffsetCandidateReport",
    "build_analog_four_all_track_offset_candidate_report_from_bytes",
    "build_analog_four_all_track_offset_candidate_report_from_file",
    "build_analog_four_offset_candidate_report_from_bytes",
    "build_analog_four_offset_candidate_report_from_file",
    "format_analog_four_all_track_offset_candidate_report",
    "format_analog_four_offset_candidate_error",
    "format_analog_four_offset_candidate_report",
]
