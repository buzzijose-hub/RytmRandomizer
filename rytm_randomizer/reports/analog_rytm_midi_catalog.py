"""Passive Analog Rytm MKII OS 1.72 MIDI CC/NRPN catalog report."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.analog_rytm_midi import get_analog_rytm_catalog_summary
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Rytm MIDI catalog"
SOURCE_MODULE: Final[str] = "reports.analog_rytm_midi_catalog"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "manual-backed catalog only",
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
class AnalogRytmMidiCatalogReport:
    """Passive coverage summary for the manual-backed Analog Rytm MIDI catalog."""

    general_cc_count: int
    machine_src_cc_count: int
    total_cc_count: int
    validated_runtime_count: int
    locked_default_count: int
    documented_only_count: int
    machine_profile_count: int
    machine_profiles_with_src_count: int
    note_trigger_count: int
    pad_count: int


def build_analog_rytm_midi_catalog_report() -> AnalogRytmMidiCatalogReport:
    """Return passive coverage data for the Analog Rytm OS 1.72 MIDI catalog."""

    summary = get_analog_rytm_catalog_summary()
    return AnalogRytmMidiCatalogReport(
        general_cc_count=summary.general_cc_count,
        machine_src_cc_count=summary.machine_src_cc_count,
        total_cc_count=summary.total_cc_count,
        validated_runtime_count=summary.validated_runtime_count,
        locked_default_count=summary.locked_default_count,
        documented_only_count=summary.documented_only_count,
        machine_profile_count=summary.machine_profile_count,
        machine_profiles_with_src_count=summary.machine_profiles_with_src_count,
        note_trigger_count=summary.note_trigger_count,
        pad_count=summary.pad_count,
    )


def _body_lines(report: AnalogRytmMidiCatalogReport) -> list[str]:
    lines = [
        "Summary:",
        f"- General CC/NRPN rows: {report.general_cc_count}",
        f"- Machine SRC rows: {report.machine_src_cc_count}",
        f"- Total CC/NRPN rows: {report.total_cc_count}",
        f"- Validated runtime rows: {report.validated_runtime_count}",
        f"- Locked-default rows: {report.locked_default_count}",
        f"- Documented-only rows: {report.documented_only_count}",
        (
            "- Machine profiles with SRC rows: "
            f"{report.machine_profiles_with_src_count} / {report.machine_profile_count}"
        ),
        f"- MIDI note trigger rows: {report.note_trigger_count}",
        f"- Pads: {report.pad_count}",
        "Promotion boundary:",
        "- Validated runtime rows stay limited to the existing V1.34 mutation maps.",
        (
            "- Documented-only rows require separate approval and hardware validation "
            "before mutation."
        ),
        SAFETY_SECTION_HEADER,
    ]
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_analog_rytm_midi_catalog_report(
    report: AnalogRytmMidiCatalogReport | None = None,
) -> list[str]:
    """Return deterministic report lines for the passive Rytm MIDI catalog."""

    source_report = build_analog_rytm_midi_catalog_report() if report is None else report
    return passive_report_lines(_HEADER, _body_lines(source_report))


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if argv:
        raise ValueError("analog-rytm-midi-catalog-report takes no arguments")
    return {}


def _handle_cli_report() -> int:
    sys.stdout.write("\n".join(format_analog_rytm_midi_catalog_report()))
    sys.stdout.write("\n")
    return 0


ANALOG_RYTM_MIDI_CATALOG_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-rytm-midi-catalog-report",
    summary="Print the passive Analog Rytm MIDI catalog report.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
)

register(ANALOG_RYTM_MIDI_CATALOG_CLI_COMMAND)


__all__ = [
    "ANALOG_RYTM_MIDI_CATALOG_CLI_COMMAND",
    "AnalogRytmMidiCatalogReport",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_analog_rytm_midi_catalog_report",
    "format_analog_rytm_midi_catalog_report",
]
