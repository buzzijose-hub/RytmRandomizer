"""Passive Analog Rytm 12-pad machine matrix report."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES,
    RYTM_PAD_CAPABILITIES,
    RytmMachineProfile,
    allowed_machine_profiles_for_pad,
)
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive Rytm 12-pad machine matrix"
SOURCE_MODULE: Final[str] = "reports.rytm_machine_matrix"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "no MIDI sending",
    "no port opening",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class RytmMachineMatrixPadReport:
    """Formatted machine eligibility for one 1-based Rytm pad."""

    pad: int
    track_code: str
    label: str
    machines: tuple[str, ...]


@dataclass(frozen=True)
class RytmMachineMatrixReport:
    """Passive report data for the Rytm 12-pad machine matrix."""

    pad_count: int
    machine_profile_count: int
    allowed_slot_count: int
    pads_by_pad: Mapping[int, RytmMachineMatrixPadReport]


def _machine_label(profile: RytmMachineProfile) -> str:
    return f"{profile.label} (CC15 {profile.machine_value})"


def build_rytm_machine_matrix_report() -> RytmMachineMatrixReport:
    """Return passive report data for the Rytm 12-pad machine matrix."""

    pads_by_pad: dict[int, RytmMachineMatrixPadReport] = {}
    allowed_slot_count = 0

    for capability in RYTM_PAD_CAPABILITIES:
        profiles = allowed_machine_profiles_for_pad(capability.pad)
        machines = tuple(_machine_label(profile) for profile in profiles)
        allowed_slot_count += len(machines)
        pads_by_pad[capability.pad] = RytmMachineMatrixPadReport(
            pad=capability.pad,
            track_code=capability.track_code,
            label=capability.label,
            machines=machines,
        )

    return RytmMachineMatrixReport(
        pad_count=len(RYTM_PAD_CAPABILITIES),
        machine_profile_count=len(RYTM_MACHINE_PROFILES),
        allowed_slot_count=allowed_slot_count,
        pads_by_pad=MappingProxyType(pads_by_pad),
    )


def _body_lines(report: RytmMachineMatrixReport) -> list[str]:
    lines = [
        "Summary:",
        f"- Pads: {report.pad_count}",
        f"- Machine profiles: {report.machine_profile_count}",
        f"- Allowed pad-machine slots: {report.allowed_slot_count}",
        "Pads:",
    ]

    for pad in sorted(report.pads_by_pad):
        pad_report = report.pads_by_pad[pad]
        lines.append(f"Pad {pad} / {pad_report.track_code} / {pad_report.label}:")
        lines.extend(f"  - {machine}" for machine in pad_report.machines)

    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_rytm_machine_matrix_report(
    report: RytmMachineMatrixReport | None = None,
) -> list[str]:
    """Return deterministic report lines for the Rytm 12-pad machine matrix."""

    source_report = build_rytm_machine_matrix_report() if report is None else report
    return passive_report_lines(_HEADER, _body_lines(source_report))


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if argv:
        raise ValueError("rytm-12-pad-machine-matrix-report takes no arguments")
    return {}


def _handle_cli_report() -> int:
    sys.stdout.write("\n".join(format_rytm_machine_matrix_report()))
    sys.stdout.write("\n")
    return 0


RYTM_MACHINE_MATRIX_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="rytm-12-pad-machine-matrix-report",
    summary="Print the passive Rytm 12-pad machine matrix report.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
)

register(RYTM_MACHINE_MATRIX_CLI_COMMAND)


__all__ = [
    "REPORT_TITLE",
    "RYTM_MACHINE_MATRIX_CLI_COMMAND",
    "RytmMachineMatrixPadReport",
    "RytmMachineMatrixReport",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_rytm_machine_matrix_report",
    "format_rytm_machine_matrix_report",
]
