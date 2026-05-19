"""Passive proof report for Rytm controlled saved-parameter mappings.

This module wraps the existing Rytm controlled-diff analyzer with a stricter
single-parameter proof gate. It reads existing before/after SysEx data only and
does not import MIDI libraries, open ports, send MIDI, receive live SysEx, write
SysEx, execute commands, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .controlled_diff import (
    RytmControlledDiffReport,
    RytmControlledParameterChange,
    build_rytm_controlled_diff_report_from_bytes,
    build_rytm_controlled_diff_report_from_file,
)


@dataclass(frozen=True)
class RytmControlledMappingProofEntry:
    """One reviewable Rytm mapping proof from a clean controlled diff."""

    pad: int
    midi_channel: int
    machine_label: str
    parameter_name: str
    cc: int
    block_offset: int
    mapping_status: str


@dataclass(frozen=True)
class RytmControlledMappingProof:
    """Result of checking one Rytm controlled diff against one intended target."""

    before_path: str | None
    after_path: str | None
    requested_parameter: str
    parameter_key: str
    ready: bool
    reason: str
    diff_report: RytmControlledDiffReport
    entry: RytmControlledMappingProofEntry | None

    @property
    def slot(self) -> int:
        return self.diff_report.slot

    @property
    def pad(self) -> int:
        return self.diff_report.pad

    @property
    def changed_parameter_count(self) -> int:
        return self.diff_report.changed_parameter_count


def build_rytm_controlled_mapping_proof_from_file(
    before_path: str | Path,
    after_path: str | Path,
    *,
    slot: int,
    pad: int,
    parameter: str,
    limit: int,
) -> RytmControlledMappingProof:
    """Build a passive mapping proof from existing before/after SysEx files."""

    parameter_key = _normalize_parameter(parameter)
    diff_report = build_rytm_controlled_diff_report_from_file(
        before_path,
        after_path,
        slot=slot,
        pad=pad,
        limit=limit,
    )
    proof = _proof_from_diff_report(
        diff_report,
        requested_parameter=str(parameter),
        parameter_key=parameter_key,
    )
    return RytmControlledMappingProof(
        before_path=str(before_path),
        after_path=str(after_path),
        requested_parameter=proof.requested_parameter,
        parameter_key=proof.parameter_key,
        ready=proof.ready,
        reason=proof.reason,
        diff_report=proof.diff_report,
        entry=proof.entry,
    )


def build_rytm_controlled_mapping_proof_from_bytes(
    before_data: bytes,
    after_data: bytes,
    *,
    slot: int,
    pad: int,
    parameter: str,
    limit: int,
) -> RytmControlledMappingProof:
    """Build a passive mapping proof from raw before/after SysEx bytes."""

    parameter_key = _normalize_parameter(parameter)
    diff_report = build_rytm_controlled_diff_report_from_bytes(
        before_data,
        after_data,
        slot=slot,
        pad=pad,
        limit=limit,
    )
    return _proof_from_diff_report(
        diff_report,
        requested_parameter=str(parameter),
        parameter_key=parameter_key,
    )


def format_rytm_controlled_mapping_proof_report(
    proof: RytmControlledMappingProof,
) -> list[str]:
    """Format a deterministic passive Rytm controlled mapping proof report."""

    lines = [
        "RytmRandomizer passive Rytm Controlled Mapping Proof Report",
        f"Before path: {proof.before_path or '<bytes>'}",
        f"After path: {proof.after_path or '<bytes>'}",
        f"Slot: {proof.slot}",
        f"Pad: {proof.pad}",
        f"MIDI channel: {proof.diff_report.midi_channel}",
        f"Before kit: {proof.diff_report.before_kit_name or '<blank>'}",
        f"After kit: {proof.diff_report.after_kit_name or '<blank>'}",
        f"Before sound: {proof.diff_report.before_sound_name or '<blank>'}",
        f"After sound: {proof.diff_report.after_sound_name or '<blank>'}",
        f"Before machine: {proof.diff_report.before_machine_label}",
        f"After machine: {proof.diff_report.after_machine_label}",
        f"Requested parameter: {proof.requested_parameter}",
        f"Parameter key: {proof.parameter_key}",
        f"Ready: {proof.ready}",
        f"Reason: {proof.reason}",
        f"Changed mapped parameters: {proof.changed_parameter_count}",
        "Changed parameter details:",
    ]
    if proof.diff_report.changes:
        lines.extend(_format_change_line(change) for change in proof.diff_report.changes)
    else:
        lines.append("- none found")

    lines.append("Proof entry:")
    if proof.entry is None:
        lines.append("- not ready; repeat a cleaner controlled diff before trusting this proof")
    else:
        lines.extend(_format_entry(proof.entry))

    lines.extend(
        [
            "Proof policy:",
            "- one selected pad only",
            "- one intended parameter only",
            "- single changed mapped parameter required",
            "- changed parameter must match the requested parameter name or CC",
            "- operator review still required before treating the proof as canonical",
            "Safety:",
            "- passive/read-only",
            "- controlled comparison only",
            "- no MIDI sending",
            "- no MIDI receive",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
    return lines


def format_rytm_controlled_mapping_proof_error(message: str) -> list[str]:
    """Format deterministic passive proof-report errors."""

    return [
        "RytmRandomizer passive Rytm Controlled Mapping Proof Report",
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


def _proof_from_diff_report(
    diff_report: RytmControlledDiffReport,
    *,
    requested_parameter: str,
    parameter_key: str,
) -> RytmControlledMappingProof:
    reason = _reason_for_diff(diff_report, parameter_key)
    entry = None
    if reason == "single_changed_parameter_ready_for_review":
        change = diff_report.changes[0]
        entry = RytmControlledMappingProofEntry(
            pad=diff_report.pad,
            midi_channel=diff_report.midi_channel,
            machine_label=diff_report.after_machine_label,
            parameter_name=change.name,
            cc=change.cc,
            block_offset=change.block_offset,
            mapping_status=change.mapping_status,
        )
    return RytmControlledMappingProof(
        before_path=diff_report.before_path,
        after_path=diff_report.after_path,
        requested_parameter=requested_parameter,
        parameter_key=parameter_key,
        ready=entry is not None,
        reason=reason,
        diff_report=diff_report,
        entry=entry,
    )


def _reason_for_diff(diff_report: RytmControlledDiffReport, parameter_key: str) -> str:
    if diff_report.changed_parameter_count == 0:
        return "blocked_no_changed_parameters"
    if diff_report.changed_parameter_count > 1:
        return "blocked_multiple_changed_parameters"
    if len(diff_report.changes) != 1:
        return "blocked_changed_parameter_not_reported"
    if not _change_matches_parameter(diff_report.changes[0], parameter_key):
        return "blocked_parameter_mismatch"
    return "single_changed_parameter_ready_for_review"


def _change_matches_parameter(
    change: RytmControlledParameterChange,
    parameter_key: str,
) -> bool:
    return parameter_key in {
        _normalize_parameter(change.name),
        f"cc{change.cc}",
        str(change.cc),
    }


def _normalize_parameter(parameter: str) -> str:
    key = "".join(character for character in str(parameter).lower() if character.isalnum())
    if not key:
        raise ValueError("parameter must not be blank")
    return key


def _format_change_line(change: RytmControlledParameterChange) -> str:
    return (
        f"- {change.name} / CC{change.cc} @0x{change.block_offset:04X}: "
        f"{change.before_value} -> {change.after_value} "
        f"(delta {change.delta:+d}), {change.mapping_status}"
    )


def _format_entry(entry: RytmControlledMappingProofEntry) -> list[str]:
    return [
        "RytmControlledMappingProofEntry(",
        f"    pad={entry.pad},",
        f"    midi_channel={entry.midi_channel},",
        f'    machine_label="{entry.machine_label}",',
        f'    parameter_name="{entry.parameter_name}",',
        f"    cc={entry.cc},",
        f"    block_offset=0x{entry.block_offset:04X},",
        f'    mapping_status="{entry.mapping_status}",',
        ")",
    ]


__all__ = [
    "RytmControlledMappingProof",
    "RytmControlledMappingProofEntry",
    "build_rytm_controlled_mapping_proof_from_bytes",
    "build_rytm_controlled_mapping_proof_from_file",
    "format_rytm_controlled_mapping_proof_error",
    "format_rytm_controlled_mapping_proof_report",
]
