"""Passive dual-machine kit-bank readiness summary.

This module reads saved SysEx files only. It does not import MIDI libraries,
open ports, request dumps, receive live SysEx, send messages, or write SysEx.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..analog_four.bank_analyzer import (
    CANDIDATE_STATUS,
    AnalogFourKitBankAnalysis,
    AnalogFourKitBankAnalysisError,
    analyze_analog_four_kit_bank_file,
)
from ..observability.errors import DataError
from ..sysex.bank_analyzer import (
    SNAPSHOT_READINESS_KEYS,
    SysexBankAnalysisError,
    SysexKitBankAnalysis,
    analyze_sysex_kit_bank_file,
)


class DualMachineKitBankReadinessError(DataError, ValueError):
    """Raised when saved dual-machine kit-bank readiness cannot be analyzed."""


@dataclass(frozen=True)
class DualMachineKitBankReadiness:
    """Combined passive readiness for saved Rytm and Analog Four kit banks."""

    rytm_path: str
    analog_four_path: str
    rytm: SysexKitBankAnalysis
    analog_four: AnalogFourKitBankAnalysis

    @property
    def rytm_ready_pad_count(self) -> int:
        return self.rytm.snapshot_readiness_totals["ready"]

    @property
    def rytm_blocked_pad_count(self) -> int:
        totals = self.rytm.snapshot_readiness_totals
        return sum(totals[key] for key in SNAPSHOT_READINESS_KEYS if key != "ready")

    @property
    def rytm_scanned_pad_count(self) -> int:
        return self.rytm.snapshot_decoded_slot_count * 12

    @property
    def analog_four_ready_track_count(self) -> int:
        return self.analog_four.planned_track_count

    @property
    def analog_four_blocked_track_count(self) -> int:
        return self.analog_four.blocked_track_count

    @property
    def combined_ready_lane_count(self) -> int:
        return self.rytm_ready_pad_count + self.analog_four_ready_track_count

    @property
    def combined_blocked_lane_count(self) -> int:
        return self.rytm_blocked_pad_count + self.analog_four_blocked_track_count

    @property
    def combined_scanned_lane_count(self) -> int:
        return self.rytm_scanned_pad_count + self.analog_four.scanned_track_count

    @property
    def rytm_mode_status(self) -> str:
        return _format_mode_status(self.rytm_scanned_pad_count, self.rytm_blocked_pad_count)

    @property
    def analog_four_mode_status(self) -> str:
        return _format_candidate_mode_status(
            self.analog_four.scanned_track_count,
            self.analog_four_blocked_track_count,
        )

    @property
    def both_machine_mode_status(self) -> str:
        return _format_candidate_mode_status(
            self.combined_scanned_lane_count,
            self.combined_blocked_lane_count,
        )

    @property
    def problem_slot_lines(self) -> tuple[str, ...]:
        lines: list[str] = []
        for record in self.rytm.records:
            if not record.snapshot_readiness_counts:
                continue
            ready = _count_tuple_value(record.snapshot_readiness_counts, "ready")
            blocked = sum(
                _count_tuple_value(record.snapshot_readiness_counts, key)
                for key in SNAPSHOT_READINESS_KEYS
                if key != "ready"
            )
            if blocked:
                lines.append(
                    f"- Rytm slot {record.slot_number}: "
                    f"ready pads {ready} / blocked pads {blocked}"
                )
        for record in self.analog_four.records:
            if record.blocked_track_count:
                lines.append(
                    f"- Analog Four slot {record.slot_number}: "
                    f"planned tracks {record.planned_track_count} / "
                    f"blocked tracks {record.blocked_track_count}"
                )
        return tuple(lines) if lines else ("- none",)


def analyze_dual_machine_kit_bank_files(
    rytm_path: str | Path,
    analog_four_path: str | Path,
) -> DualMachineKitBankReadiness:
    """Analyze saved Rytm and Analog Four kit banks without touching hardware."""

    try:
        rytm = analyze_sysex_kit_bank_file(rytm_path)
        analog_four = analyze_analog_four_kit_bank_file(analog_four_path)
    except (SysexBankAnalysisError, AnalogFourKitBankAnalysisError) as exc:
        raise DualMachineKitBankReadinessError(str(exc)) from exc
    return DualMachineKitBankReadiness(
        rytm_path=str(rytm_path),
        analog_four_path=str(analog_four_path),
        rytm=rytm,
        analog_four=analog_four,
    )


def format_dual_machine_kit_bank_readiness_report(
    readiness: DualMachineKitBankReadiness,
) -> list[str]:
    """Format a deterministic passive dual-machine kit-bank readiness report."""

    compatibility = readiness.rytm.snapshot_machine_compatibility_totals
    lines = [
        "RytmRandomizer passive dual-machine kit bank readiness report",
        "Rytm bank:",
        f"- SysEx records: {readiness.rytm.record_count}",
        (
            "- decoded snapshots: "
            f"{readiness.rytm.snapshot_decoded_slot_count} / {readiness.rytm.record_count}"
        ),
        (
            "- snapshot pads: "
            f"ready {readiness.rytm_ready_pad_count} / "
            f"blocked {readiness.rytm_blocked_pad_count} / "
            f"total {readiness.rytm_scanned_pad_count}"
        ),
        (
            "- machine compatibility: "
            f"allowed {compatibility['allowed_on_pad']} / "
            f"disabled {compatibility['machine_disabled']} / "
            f"unknown {compatibility['unknown_machine']} / "
            f"incompatible {compatibility['incompatible_with_pad']}"
        ),
        "Analog Four bank:",
        f"- complete SysEx messages: {readiness.analog_four.complete_sysex_message_count}",
        f"- kit records: {readiness.analog_four.kit_record_count}",
        (
            "- decoded snapshots: "
            f"{readiness.analog_four.decoded_snapshot_count} / "
            f"{readiness.analog_four.kit_record_count}"
        ),
        (
            "- snapshot tracks: "
            f"planned {readiness.analog_four_ready_track_count} / "
            f"blocked {readiness.analog_four_blocked_track_count} / "
            f"total {readiness.analog_four.scanned_track_count}"
        ),
        f"- planned candidate changes: {readiness.analog_four.planned_candidate_change_count}",
        f"- candidate status: {CANDIDATE_STATUS}",
        "Combined live-rig readiness:",
        f"- ready lanes: {readiness.combined_ready_lane_count}",
        f"- blocked lanes: {readiness.combined_blocked_lane_count}",
        f"- scanned lanes: {readiness.combined_scanned_lane_count}",
        f"- Rytm-only snapshot mode: {readiness.rytm_mode_status}",
        f"- Analog Four-only snapshot mode: {readiness.analog_four_mode_status}",
        f"- both-machines snapshot mode: {readiness.both_machine_mode_status}",
        "Policy:",
        "- saved kit-bank files only",
        "- captured-value relative",
        "- Rytm uses pad/machine compatibility gates",
        "- Analog Four saved-offset candidates remain candidate_unverified",
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
    lines[20:20] = (
        "Implementation boundaries:",
        *_format_implementation_boundary_lines(),
        "Problem slots:",
        *readiness.problem_slot_lines,
        "Next validation commands:",
        *_format_next_validation_commands(readiness),
    )
    return lines


def _format_implementation_boundary_lines() -> list[str]:
    return [
        "- Rytm implementation: 12 pad/machine lanes with pad-machine compatibility gates.",
        (
            "- Analog Four implementation: 4 synth tracks with saved-offset "
            "mapping manifest gates."
        ),
        "- Shared layer: target scoping, reporting, orchestration, and guarded validation only.",
    ]


def format_dual_machine_kit_bank_readiness_error(
    rytm_path: str | Path,
    analog_four_path: str | Path,
    message: str,
) -> list[str]:
    """Format deterministic passive dual-machine kit-bank readiness errors."""

    return [
        "RytmRandomizer passive dual-machine kit bank readiness report",
        f"Rytm path: {rytm_path}",
        f"Analog Four path: {analog_four_path}",
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


def _format_mode_status(scanned_count: int, blocked_count: int) -> str:
    if not scanned_count:
        return "unavailable"
    if blocked_count:
        return "blocked"
    return "ready"


def _format_candidate_mode_status(scanned_count: int, blocked_count: int) -> str:
    status = _format_mode_status(scanned_count, blocked_count)
    if status == "ready":
        return "candidate-ready"
    return status


def _format_next_validation_commands(readiness: DualMachineKitBankReadiness) -> list[str]:
    if readiness.combined_blocked_lane_count:
        status_line = (
            "- status: blocked lanes present; resolve Problem slots before "
            "guarded send dry-runs."
        )
    else:
        status_line = (
            "- status: saved-bank preflight passed; choose one target scope "
            "before any armed send."
        )
    return [
        status_line,
        "Rytm-only:",
        "python -m rytm_randomizer.cli dual-machine-lane-validation-guide --target rytm --rytm-pad 1",
        (
            "python -m rytm_randomizer.cli dual-machine-mapping-session-plan-report "
            "--target rytm --slot 1 --limit 8"
        ),
        "Analog Four-only:",
        (
            "python -m rytm_randomizer.cli dual-machine-lane-validation-guide "
            "--target analog-four --analog-four-track 1 "
            "--analog-four-mapping-manifest <analog-four-mapping-manifest-path>"
        ),
        (
            "python -m rytm_randomizer.cli dual-machine-mapping-session-plan-report "
            "--target analog-four --slot 1 --limit 8"
        ),
        (
            "python -m rytm_randomizer.cli analog-four-saved-offset-mapping-manifest-report "
            "<analog-four-mapping-manifest-path>"
        ),
        "Both machines:",
        (
            "python -m rytm_randomizer.cli dual-machine-lane-validation-guide --target both "
            "--rytm-pad 1 --analog-four-track 1 "
            "--analog-four-mapping-manifest <analog-four-mapping-manifest-path>"
        ),
        (
            "python -m rytm_randomizer.cli dual-machine-mapping-session-plan-report "
            "--target both --slot 1 --limit 8"
        ),
    ]


def _count_tuple_value(counts: tuple[tuple[str, int], ...], key: str) -> int:
    return dict(counts).get(key, 0)


__all__ = [
    "DualMachineKitBankReadiness",
    "DualMachineKitBankReadinessError",
    "analyze_dual_machine_kit_bank_files",
    "format_dual_machine_kit_bank_readiness_error",
    "format_dual_machine_kit_bank_readiness_report",
]
