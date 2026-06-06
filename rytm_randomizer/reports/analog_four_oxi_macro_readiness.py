"""Passive Analog Four OXI macro hardware-readiness report."""

from __future__ import annotations

import json
import shlex
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

from ..cli_registry import CliCommand, register
from ..data.analog_four_oxi_macros import DEFAULT_ANALOG_FOUR_OXI_MACRO
from .analog_four_oxi_macro_report import (
    AnalogFourOxiMacroEvent,
    build_analog_four_oxi_macro_report,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

ReadinessStatus = Literal["cc-ready", "nrpn-required", "manual-review", "blocked"]
ReportReadiness = Literal["review-ready", "needs-review", "blocked"]

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four OXI macro readiness"
SOURCE_MODULE: Final[str] = "reports.analog_four_oxi_macro_readiness"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "manual-backed Analog Four CC metadata only",
    "operator-present validation commands only",
    "no MIDI sending",
    "no port opening",
    "no unattended hardware behavior",
    "A4 full macro SEND remains unimplemented",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_DEFAULT_EVENT_LIMIT: Final[int] = 24
_USAGE: Final[str] = (
    "analog-four-oxi-macro-readiness-report usage: "
    "[<macro-name>] [--seed N] [--intensity N] [--limit N] [--json]"
)


@dataclass(frozen=True)
class AnalogFourOxiMacroReadinessEvent:
    """One passive A4 macro row with an operator-present validation command."""

    track: int
    role: str
    lane: str
    parameter: str
    channel: int
    control: int
    value: int
    status: ReadinessStatus
    validation_command: str
    reason: str


@dataclass(frozen=True)
class AnalogFourOxiMacroReadinessReport:
    """Passive hardware-readiness summary for one deterministic A4 OXI macro."""

    title: str
    macro_name: str
    seed: int
    intensity: int
    readiness: ReportReadiness
    event_count: int
    ready_count: int
    review_count: int
    blocked_count: int
    events: tuple[AnalogFourOxiMacroReadinessEvent, ...]
    opens_ports: bool
    sends_midi: bool
    hardware_required: bool
    operator_present_required: bool


def _validate_event_limit(event_limit: int) -> None:
    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")


def _visible_events(
    events: Sequence[AnalogFourOxiMacroReadinessEvent],
    *,
    event_limit: int,
) -> tuple[AnalogFourOxiMacroReadinessEvent, ...]:
    _validate_event_limit(event_limit)
    if event_limit == 0 or event_limit >= len(events):
        return tuple(events)
    return tuple(events[:event_limit])


def _validation_command(event: AnalogFourOxiMacroEvent) -> str:
    return (
        "python -m rytm_randomizer.app --arm --a4-send-param "
        f"--track {event.track} "
        f"--parameter {shlex.quote(event.parameter)} "
        f"--value {event.value}"
    )


def _readiness_event(event: AnalogFourOxiMacroEvent) -> AnalogFourOxiMacroReadinessEvent:
    return AnalogFourOxiMacroReadinessEvent(
        track=event.track,
        role=event.role,
        lane=event.lane,
        parameter=event.parameter,
        channel=event.channel,
        control=event.control,
        value=event.value,
        status="cc-ready",
        validation_command=_validation_command(event),
        reason="manual-backed CC MSB row is available through --a4-send-param",
    )


def _report_readiness(
    events: Sequence[AnalogFourOxiMacroReadinessEvent],
) -> ReportReadiness:
    if any(event.status == "blocked" for event in events):
        return "blocked"
    if any(event.status != "cc-ready" for event in events):
        return "needs-review"
    return "review-ready"


def build_analog_four_oxi_macro_readiness_report(
    macro_name: str = DEFAULT_ANALOG_FOUR_OXI_MACRO,
    *,
    seed: int = 0,
    intensity: int = 4,
) -> AnalogFourOxiMacroReadinessReport:
    """Return passive A4 OXI macro readiness without opening MIDI ports."""

    macro_report = build_analog_four_oxi_macro_report(
        macro_name,
        seed=seed,
        intensity=intensity,
    )
    events = tuple(_readiness_event(event) for event in macro_report.events)
    ready_count = sum(1 for event in events if event.status == "cc-ready")
    blocked_count = sum(1 for event in events if event.status == "blocked")
    review_count = len(events) - ready_count - blocked_count
    return AnalogFourOxiMacroReadinessReport(
        title=REPORT_TITLE,
        macro_name=macro_report.macro_name,
        seed=macro_report.seed,
        intensity=macro_report.intensity,
        readiness=_report_readiness(events),
        event_count=len(events),
        ready_count=ready_count,
        review_count=review_count,
        blocked_count=blocked_count,
        events=events,
        opens_ports=False,
        sends_midi=False,
        hardware_required=False,
        operator_present_required=True,
    )


def _event_line(event: AnalogFourOxiMacroReadinessEvent) -> str:
    return (
        f"- Track {event.track} | {event.role} | {event.lane} | "
        f"{event.parameter} | ch {event.channel} | CC{event.control} -> {event.value} | "
        f"{event.status} | {event.reason}"
    )


def _a4_macro_readiness_body_lines(
    report: AnalogFourOxiMacroReadinessReport,
    *,
    event_limit: int,
) -> list[str]:
    visible_events = _visible_events(report.events, event_limit=event_limit)
    lines = [
        f"Macro: {report.macro_name}",
        f"Seed: {report.seed}",
        f"Intensity: {report.intensity}",
        f"Readiness: {report.readiness}",
        f"Event count: {report.event_count}",
        f"Ready events: {report.ready_count}",
        f"Review events: {report.review_count}",
        f"Blocked events: {report.blocked_count}",
        f"Shown events: {len(visible_events)}",
        f"Truncated events: {report.event_count - len(visible_events)}",
        "Safety flags:",
        f"- opens_ports: {report.opens_ports}",
        f"- sends_midi: {report.sends_midi}",
        f"- hardware_required: {report.hardware_required}",
        f"- operator_present_required: {report.operator_present_required}",
        "Readiness events:",
    ]
    lines.extend(_event_line(event) for event in visible_events)
    lines.append("Validation commands:")
    lines.extend(f"- {event.validation_command}" for event in visible_events)
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_analog_four_oxi_macro_readiness_report(
    report: AnalogFourOxiMacroReadinessReport | None = None,
    *,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing A4 macro readiness lines."""

    resolved_report = (
        report if report is not None else build_analog_four_oxi_macro_readiness_report()
    )
    _validate_event_limit(event_limit)
    return passive_report_lines(
        _HEADER,
        _a4_macro_readiness_body_lines(resolved_report, event_limit=event_limit),
    )


def _a4_macro_readiness_event_json(
    event: AnalogFourOxiMacroReadinessEvent,
) -> dict[str, object]:
    return {
        "track": event.track,
        "role": event.role,
        "lane": event.lane,
        "parameter": event.parameter,
        "channel": event.channel,
        "control": event.control,
        "value": event.value,
        "status": event.status,
        "validation_command": event.validation_command,
        "reason": event.reason,
    }


def build_analog_four_oxi_macro_readiness_payload(
    report: AnalogFourOxiMacroReadinessReport,
    *,
    event_limit: int = 0,
) -> dict[str, object]:
    """Return machine-readable passive A4 macro readiness metadata."""

    visible_events = _visible_events(report.events, event_limit=event_limit)
    return {
        "title": report.title,
        "macro_name": report.macro_name,
        "seed": report.seed,
        "intensity": report.intensity,
        "readiness": report.readiness,
        "event_count": report.event_count,
        "ready_count": report.ready_count,
        "review_count": report.review_count,
        "blocked_count": report.blocked_count,
        "shown_count": len(visible_events),
        "truncated_count": report.event_count - len(visible_events),
        "opens_ports": report.opens_ports,
        "sends_midi": report.sends_midi,
        "hardware_required": report.hardware_required,
        "operator_present_required": report.operator_present_required,
        "events": [_a4_macro_readiness_event_json(event) for event in visible_events],
        "safety": list(SAFETY_LINES),
    }


def _parse_a4_macro_readiness_int(value: str, *, option: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc


def _parse_a4_macro_readiness_nonnegative_int(value: str, *, option: str) -> int:
    parsed = _parse_a4_macro_readiness_int(value, option=option)
    if parsed < 0:
        raise ValueError(f"{option} must be >= 0")
    return parsed


def _parse_a4_macro_readiness_intensity(value: str, *, option: str) -> int:
    parsed = _parse_a4_macro_readiness_int(value, option=option)
    if parsed < 0 or parsed > 7:
        raise ValueError("intensity must be between 0 and 7")
    return parsed


def _pop_required_value(remaining: list[str], *, option: str) -> str:
    if not remaining:
        raise ValueError(f"{option} requires a value")
    return remaining.pop(0)


def _parse_a4_macro_readiness_args(argv: Sequence[str]) -> dict[str, object]:
    macro_name = DEFAULT_ANALOG_FOUR_OXI_MACRO
    seed = 0
    intensity = 4
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    macro_seen = False
    remaining = list(argv)
    while remaining:
        argument = remaining.pop(0)
        if argument == "--json":
            json_output = True
            continue
        if argument in {"--seed", "--intensity", "--limit"}:
            value = _pop_required_value(remaining, option=argument)
            if argument == "--seed":
                seed = _parse_a4_macro_readiness_int(value, option=argument)
            elif argument == "--intensity":
                intensity = _parse_a4_macro_readiness_intensity(value, option=argument)
            else:
                event_limit = _parse_a4_macro_readiness_nonnegative_int(
                    value,
                    option=argument,
                )
            continue
        if argument.startswith("--"):
            raise ValueError(f"unknown argument: {argument}")
        if macro_seen:
            raise ValueError("macro name can only be provided once")
        macro_name = argument
        macro_seen = True
    return {
        "macro_name": macro_name,
        "seed": seed,
        "intensity": intensity,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _handle_a4_macro_readiness_report(
    *,
    macro_name: str,
    seed: int,
    intensity: int,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        report = build_analog_four_oxi_macro_readiness_report(
            macro_name,
            seed=seed,
            intensity=intensity,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    build_analog_four_oxi_macro_readiness_payload(
                        report,
                        event_limit=event_limit,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_analog_four_oxi_macro_readiness_report(
            report,
            event_limit=event_limit,
        )
    except (ValueError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_a4_macro_readiness_error(exc: Exception) -> str:
    return f"Error: {exc}\n{_USAGE}"


ANALOG_FOUR_OXI_MACRO_READINESS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-oxi-macro-readiness-report",
    summary="Print passive Analog Four OXI macro hardware-readiness metadata.",
    args_parser=_parse_a4_macro_readiness_args,
    handler=_handle_a4_macro_readiness_report,
    error_formatter=_format_a4_macro_readiness_error,
)

register(ANALOG_FOUR_OXI_MACRO_READINESS_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_OXI_MACRO_READINESS_CLI_COMMAND",
    "AnalogFourOxiMacroReadinessEvent",
    "AnalogFourOxiMacroReadinessReport",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_analog_four_oxi_macro_readiness_payload",
    "build_analog_four_oxi_macro_readiness_report",
    "format_analog_four_oxi_macro_readiness_report",
]
