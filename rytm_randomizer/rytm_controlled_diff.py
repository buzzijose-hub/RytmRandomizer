"""Passive Analog Rytm controlled saved-kit diff analysis.

This module compares existing before/after SysEx files only. It does not import
MIDI libraries, open ports, request dumps, receive live SysEx, send messages, or
write SysEx data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .observability.errors import DataError
from .sysex_snapshot_decoder import (
    PAD_COUNT,
    RytmKitSnapshot,
    RytmSnapshotPad,
    SysexSnapshotDecodeError,
    _is_rytm_kit_record,
    _split_complete_sysex_messages,
    decode_rytm_kit_snapshot_record,
)

DEFAULT_LIMIT = 16


class RytmControlledDiffError(DataError, ValueError):
    """Raised when Rytm controlled diff analysis cannot run."""


@dataclass(frozen=True)
class RytmControlledParameterChange:
    """One before/after saved-parameter change for a Rytm pad."""

    name: str
    cc: int
    block_offset: int
    before_value: int
    after_value: int
    delta: int
    mapping_status: str


@dataclass(frozen=True)
class RytmControlledDiffReport:
    """Passive controlled diff report for one Rytm slot and pad."""

    before_path: str | None
    after_path: str | None
    slot: int
    pad: int
    midi_channel: int
    before_kit_name: str
    after_kit_name: str
    before_sound_name: str
    after_sound_name: str
    before_machine_label: str
    after_machine_label: str
    changed_parameter_count: int
    changes: tuple[RytmControlledParameterChange, ...]


def build_rytm_controlled_diff_report_from_file(
    before_path: str | Path,
    after_path: str | Path,
    *,
    slot: int,
    pad: int,
    limit: int = DEFAULT_LIMIT,
) -> RytmControlledDiffReport:
    """Build a passive controlled diff report from existing SysEx files."""

    report = build_rytm_controlled_diff_report_from_bytes(
        Path(before_path).read_bytes(),
        Path(after_path).read_bytes(),
        slot=slot,
        pad=pad,
        limit=limit,
    )
    return RytmControlledDiffReport(
        before_path=str(before_path),
        after_path=str(after_path),
        slot=report.slot,
        pad=report.pad,
        midi_channel=report.midi_channel,
        before_kit_name=report.before_kit_name,
        after_kit_name=report.after_kit_name,
        before_sound_name=report.before_sound_name,
        after_sound_name=report.after_sound_name,
        before_machine_label=report.before_machine_label,
        after_machine_label=report.after_machine_label,
        changed_parameter_count=report.changed_parameter_count,
        changes=report.changes,
    )


def build_rytm_controlled_diff_report_from_bytes(
    before_data: bytes,
    after_data: bytes,
    *,
    slot: int,
    pad: int,
    limit: int = DEFAULT_LIMIT,
) -> RytmControlledDiffReport:
    """Build a passive controlled diff report from raw SysEx bytes."""

    if slot not in range(1, 129):
        raise RytmControlledDiffError("slot must be 1-128")
    if pad not in range(1, PAD_COUNT + 1):
        raise RytmControlledDiffError("pad must be 1-12")
    if limit < 1:
        raise RytmControlledDiffError("limit must be at least 1")

    before_snapshot = _decode_snapshot_from_bytes(before_data, slot=slot)
    after_snapshot = _decode_snapshot_from_bytes(after_data, slot=slot)
    before_pad = before_snapshot.pads[pad - 1]
    after_pad = after_snapshot.pads[pad - 1]
    changes = tuple(
        sorted(
            _changed_parameters(before_pad, after_pad),
            key=lambda change: (-abs(change.delta), change.cc, change.block_offset),
        )
    )

    return RytmControlledDiffReport(
        before_path=None,
        after_path=None,
        slot=slot,
        pad=pad,
        midi_channel=before_pad.midi_channel,
        before_kit_name=before_snapshot.kit_name,
        after_kit_name=after_snapshot.kit_name,
        before_sound_name=before_pad.sound_name,
        after_sound_name=after_pad.sound_name,
        before_machine_label=before_pad.machine_label,
        after_machine_label=after_pad.machine_label,
        changed_parameter_count=len(changes),
        changes=changes[:limit],
    )


def format_rytm_controlled_diff_report(report: RytmControlledDiffReport) -> list[str]:
    """Format a deterministic passive Rytm controlled diff report."""

    lines = [
        "RytmRandomizer passive Rytm controlled diff report",
        f"Before path: {report.before_path or '<bytes>'}",
        f"After path: {report.after_path or '<bytes>'}",
        f"Slot: {report.slot}",
        f"Pad: {report.pad}",
        f"MIDI channel: {report.midi_channel}",
        f"Before kit: {report.before_kit_name or '<blank>'}",
        f"After kit: {report.after_kit_name or '<blank>'}",
        f"Before sound: {report.before_sound_name or '<blank>'}",
        f"After sound: {report.after_sound_name or '<blank>'}",
        f"Before machine: {report.before_machine_label}",
        f"After machine: {report.after_machine_label}",
        f"Changed parameters reported: {len(report.changes)} / {report.changed_parameter_count}",
        "Changed mapped parameters:",
    ]
    if not report.changes:
        lines.append("- none found")
    for change in report.changes:
        lines.append(_format_change_line(change))
    lines.extend(_safety_lines())
    return lines


def format_rytm_controlled_diff_error(message: str) -> list[str]:
    """Format deterministic passive Rytm controlled diff error lines."""

    return [
        "RytmRandomizer passive Rytm controlled diff report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        *_safety_lines(),
    ]


def _decode_snapshot_from_bytes(data: bytes, *, slot: int) -> RytmKitSnapshot:
    try:
        for message in _split_complete_sysex_messages(data):
            if _is_rytm_kit_record(message) and message[9] == slot - 1:
                return decode_rytm_kit_snapshot_record(message)
    except SysexSnapshotDecodeError as exc:
        raise RytmControlledDiffError(str(exc)) from exc
    raise RytmControlledDiffError(f"Rytm kit slot {slot} not found")


def _changed_parameters(
    before_pad: RytmSnapshotPad,
    after_pad: RytmSnapshotPad,
) -> tuple[RytmControlledParameterChange, ...]:
    after_parameters = {
        (parameter.cc, parameter.block_offset): parameter
        for parameter in after_pad.parameters
    }
    changes = []
    for before_parameter in before_pad.parameters:
        key = (before_parameter.cc, before_parameter.block_offset)
        after_parameter = after_parameters.get(key)
        if after_parameter is None or before_parameter.value == after_parameter.value:
            continue
        changes.append(
            RytmControlledParameterChange(
                name=before_parameter.name,
                cc=before_parameter.cc,
                block_offset=before_parameter.block_offset,
                before_value=before_parameter.value,
                after_value=after_parameter.value,
                delta=after_parameter.value - before_parameter.value,
                mapping_status=_mapping_status(before_pad, after_pad),
            )
        )
    return tuple(changes)


def _mapping_status(before_pad: RytmSnapshotPad, after_pad: RytmSnapshotPad) -> str:
    if before_pad.parameter_map_status == after_pad.parameter_map_status:
        return before_pad.parameter_map_status
    return f"{before_pad.parameter_map_status}->{after_pad.parameter_map_status}"


def _format_change_line(change: RytmControlledParameterChange) -> str:
    return (
        f"- {change.name} / CC{change.cc} @0x{change.block_offset:04X}: "
        f"{change.before_value} -> {change.after_value} "
        f"(delta {change.delta:+d}), {change.mapping_status}"
    )


def _safety_lines() -> list[str]:
    return [
        "Safety:",
        "- passive/read-only",
        "- controlled comparison only",
        "- mapped saved parameters only",
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
    "RytmControlledDiffError",
    "RytmControlledDiffReport",
    "RytmControlledParameterChange",
    "build_rytm_controlled_diff_report_from_bytes",
    "build_rytm_controlled_diff_report_from_file",
    "format_rytm_controlled_diff_error",
    "format_rytm_controlled_diff_report",
]
