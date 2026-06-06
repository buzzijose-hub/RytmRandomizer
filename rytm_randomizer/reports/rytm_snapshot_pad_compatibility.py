"""Passive Analog Rytm snapshot-pad compatibility report."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from ..data.rytm_machine_catalog import (
    MACHINE_SELECTABLE,
    MUTABLE_V134,
    RYTM_PAD_CAPABILITIES,
    RytmMachineProfile,
    allowed_machine_profiles_for_pad,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Rytm snapshot pad compatibility"
SOURCE_MODULE: Final[str] = "reports.rytm_snapshot_pad_compatibility"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class RytmSnapshotPadCompatibilityPadReport:
    """Snapshot-readiness summary for one 1-based Rytm pad."""

    pad: int
    track_code: str
    label: str
    allowed_machine_count: int
    mutable_machine_count: int
    machine_selectable_count: int
    snapshot_ready: bool
    readiness_reason: str
    machine_labels: tuple[str, ...]


@dataclass(frozen=True)
class RytmSnapshotPadCompatibilityReport:
    """Passive snapshot-pad compatibility report for the 12-pad Rytm surface."""

    pad_count: int
    snapshot_ready_pad_count: int
    blocked_pad_count: int
    allowed_slot_count: int
    pads_by_pad: Mapping[int, RytmSnapshotPadCompatibilityPadReport]


def _machine_label(profile: RytmMachineProfile) -> str:
    return f"{profile.label} (CC15 {profile.machine_value}, {profile.support_status})"


def _readiness_reason(mutable_count: int, selectable_count: int) -> str:
    if mutable_count:
        return (
            f"Snapshot-ready: {mutable_count} V1.34-backed legal machine(s); "
            f"{selectable_count} legal machine(s) are selectable only."
        )
    return "Blocked: legal machines are selectable on this pad, but none are snapshot-mutable yet."


def _pad_report(pad: int, track_code: str, label: str) -> RytmSnapshotPadCompatibilityPadReport:
    profiles = allowed_machine_profiles_for_pad(pad)
    mutable_count = sum(1 for profile in profiles if profile.support_status == MUTABLE_V134)
    selectable_count = sum(
        1 for profile in profiles if profile.support_status == MACHINE_SELECTABLE
    )
    return RytmSnapshotPadCompatibilityPadReport(
        pad=pad,
        track_code=track_code,
        label=label,
        allowed_machine_count=len(profiles),
        mutable_machine_count=mutable_count,
        machine_selectable_count=selectable_count,
        snapshot_ready=mutable_count > 0,
        readiness_reason=_readiness_reason(mutable_count, selectable_count),
        machine_labels=tuple(_machine_label(profile) for profile in profiles),
    )


def build_rytm_snapshot_pad_compatibility_report() -> RytmSnapshotPadCompatibilityReport:
    """Return passive snapshot-readiness data for all 12 Rytm pads."""

    pads_by_pad: dict[int, RytmSnapshotPadCompatibilityPadReport] = {}
    allowed_slot_count = 0
    ready_count = 0

    for capability in RYTM_PAD_CAPABILITIES:
        pad_report = _pad_report(capability.pad, capability.track_code, capability.label)
        pads_by_pad[capability.pad] = pad_report
        allowed_slot_count += pad_report.allowed_machine_count
        if pad_report.snapshot_ready:
            ready_count += 1

    return RytmSnapshotPadCompatibilityReport(
        pad_count=len(RYTM_PAD_CAPABILITIES),
        snapshot_ready_pad_count=ready_count,
        blocked_pad_count=len(RYTM_PAD_CAPABILITIES) - ready_count,
        allowed_slot_count=allowed_slot_count,
        pads_by_pad=MappingProxyType(pads_by_pad),
    )


def _body_lines(report: RytmSnapshotPadCompatibilityReport) -> list[str]:
    lines = [
        "Summary:",
        f"- Pads: {report.pad_count}",
        f"- Snapshot-ready pads: {report.snapshot_ready_pad_count}",
        f"- Blocked pads: {report.blocked_pad_count}",
        f"- Allowed pad-machine slots: {report.allowed_slot_count}",
        "Pads:",
    ]

    for pad in sorted(report.pads_by_pad):
        pad_report = report.pads_by_pad[pad]
        lines.extend(
            [
                f"Pad {pad} / {pad_report.track_code} / {pad_report.label}:",
                f"  Snapshot ready: {pad_report.snapshot_ready}",
                f"  Allowed machines: {pad_report.allowed_machine_count}",
                f"  Snapshot-mutable machines: {pad_report.mutable_machine_count}",
                f"  Selectable-only machines: {pad_report.machine_selectable_count}",
                f"  Reason: {pad_report.readiness_reason}",
                "  Machines:",
            ]
        )
        lines.extend(f"    - {machine}" for machine in pad_report.machine_labels)

    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_rytm_snapshot_pad_compatibility_report(
    report: RytmSnapshotPadCompatibilityReport | None = None,
) -> list[str]:
    """Return deterministic report lines for Rytm snapshot-pad compatibility."""

    source_report = build_rytm_snapshot_pad_compatibility_report() if report is None else report
    return passive_report_lines(_HEADER, _body_lines(source_report))


RYTM_SNAPSHOT_PAD_COMPATIBILITY_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "rytm-snapshot-pad-compatibility-report",
    "Print the passive Rytm snapshot-pad compatibility report.",
    format_lines=format_rytm_snapshot_pad_compatibility_report,
    json_flag=False,
    error_formatter=None,
)

register(RYTM_SNAPSHOT_PAD_COMPATIBILITY_CLI_COMMAND)


__all__ = [
    "REPORT_TITLE",
    "RYTM_SNAPSHOT_PAD_COMPATIBILITY_CLI_COMMAND",
    "RytmSnapshotPadCompatibilityPadReport",
    "RytmSnapshotPadCompatibilityReport",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_rytm_snapshot_pad_compatibility_report",
    "format_rytm_snapshot_pad_compatibility_report",
]
