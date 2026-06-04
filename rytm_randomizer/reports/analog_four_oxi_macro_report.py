"""Passive Analog Four OXI-style macro report."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.analog_four_midi import ANALOG_FOUR_SYNTH_TRACK_CC
from ..data.analog_four_oxi_macros import (
    ANALOG_FOUR_OXI_MACROS,
    DEFAULT_ANALOG_FOUR_OXI_MACRO,
    AnalogFourOxiMacroEventSpec,
    AnalogFourOxiMacroSpec,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four OXI macro report"
SOURCE_MODULE: Final[str] = "reports.analog_four_oxi_macro_report"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "mock-only Analog Four OXI-style macro preview",
    "manual-backed Analog Four CC metadata only",
    "no real MIDI rendering",
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
_DEFAULT_EVENT_LIMIT: Final[int] = 24
_USAGE: Final[str] = (
    "analog-four-oxi-macro-report usage: "
    "[<macro-name>] [--seed N] [--intensity N] [--events] [--limit N] [--json]"
)


@dataclass(frozen=True)
class AnalogFourOxiMacroEvent:
    """One deterministic passive event row in an A4 OXI-style macro preview."""

    track: int
    role: str
    lane: str
    parameter: str
    section: str
    encoder: str
    channel: int
    control: int
    value: int
    value_min: int
    value_max: int
    intent: str


@dataclass(frozen=True)
class AnalogFourOxiMacroReport:
    """Passive in-memory preview of an Analog Four OXI-style macro."""

    macro_name: str
    macro_label: str
    summary: str
    seed: int
    intensity: int
    energy: int
    track_count: int
    event_count: int
    events: tuple[AnalogFourOxiMacroEvent, ...]
    mock_only: bool
    hardware_required: bool
    opens_ports: bool
    sends_midi: bool
    active_behavior: bool


def _stable_int(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big")


def _validate_intensity(intensity: int) -> None:
    if intensity < 0 or intensity > 7:
        raise ValueError("intensity must be between 0 and 7")


def _resolve_macro(macro_name: str) -> AnalogFourOxiMacroSpec:
    try:
        return ANALOG_FOUR_OXI_MACROS[macro_name]
    except KeyError as exc:
        available = ", ".join(ANALOG_FOUR_OXI_MACROS)
        raise ValueError(
            f"unknown Analog Four OXI macro {macro_name!r}; available: {available}"
        ) from exc


def _scaled_range(event: AnalogFourOxiMacroEventSpec, *, intensity: int) -> tuple[int, int]:
    _validate_intensity(intensity)
    if intensity == 7:
        return event.value_min, event.value_max
    midpoint = (event.value_min + event.value_max) // 2
    half_span = (event.value_max - event.value_min) / 2
    radius = round(half_span * intensity / 7)
    return (
        max(event.value_min, midpoint - radius),
        min(event.value_max, midpoint + radius),
    )


def _event_value(
    event: AnalogFourOxiMacroEventSpec,
    *,
    macro_name: str,
    seed: int,
    intensity: int,
    event_index: int,
) -> int:
    low, high = _scaled_range(event, intensity=intensity)
    if low == high:
        return low
    stable_value = _stable_int(macro_name, seed, intensity, event_index, event.parameter)
    return low + stable_value % (high - low + 1)


def _build_event(
    event: AnalogFourOxiMacroEventSpec,
    *,
    macro_name: str,
    seed: int,
    intensity: int,
    event_index: int,
) -> AnalogFourOxiMacroEvent:
    mapping = ANALOG_FOUR_SYNTH_TRACK_CC[event.parameter]
    if mapping.cc_msb is None:
        raise ValueError(f"Analog Four OXI macro parameter {event.parameter!r} has no CC MSB")
    return AnalogFourOxiMacroEvent(
        track=event.track,
        role=event.role,
        lane=event.lane,
        parameter=event.parameter,
        section=mapping.section,
        encoder=mapping.encoder,
        channel=event.track - 1,
        control=mapping.cc_msb,
        value=_event_value(
            event,
            macro_name=macro_name,
            seed=seed,
            intensity=intensity,
            event_index=event_index,
        ),
        value_min=event.value_min,
        value_max=event.value_max,
        intent=event.intent,
    )


def build_analog_four_oxi_macro_report(
    macro_name: str = DEFAULT_ANALOG_FOUR_OXI_MACRO,
    *,
    seed: int = 0,
    intensity: int = 4,
) -> AnalogFourOxiMacroReport:
    """Return a deterministic passive A4 OXI-style macro preview report."""

    _validate_intensity(intensity)
    macro = _resolve_macro(macro_name)
    events = tuple(
        _build_event(
            event,
            macro_name=macro.name,
            seed=seed,
            intensity=intensity,
            event_index=index,
        )
        for index, event in enumerate(macro.events)
    )
    return AnalogFourOxiMacroReport(
        macro_name=macro.name,
        macro_label=macro.label,
        summary=macro.summary,
        seed=seed,
        intensity=intensity,
        energy=macro.energy,
        track_count=macro.track_count,
        event_count=len(events),
        events=events,
        mock_only=True,
        hardware_required=False,
        opens_ports=False,
        sends_midi=False,
        active_behavior=False,
    )


def _oxi_macro_visible_events(
    events: Sequence[AnalogFourOxiMacroEvent],
    *,
    event_limit: int,
) -> tuple[AnalogFourOxiMacroEvent, ...]:
    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")
    if event_limit == 0 or event_limit >= len(events):
        return tuple(events)
    return tuple(events[:event_limit])


def _oxi_macro_event_line(event: AnalogFourOxiMacroEvent) -> str:
    return (
        f"- Track {event.track} | {event.role} | {event.lane} | "
        f"{event.parameter} ({event.section}/{event.encoder}) | "
        f"ch {event.channel} | CC{event.control} -> {event.value} | "
        f"range {event.value_min}-{event.value_max} | {event.intent}"
    )


def _oxi_macro_body_lines(
    report: AnalogFourOxiMacroReport,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    visible_events = _oxi_macro_visible_events(report.events, event_limit=event_limit)
    lines = [
        f"Macro: {report.macro_name} / {report.macro_label}",
        f"Summary: {report.summary}",
        f"Seed: {report.seed}",
        f"Intensity: {report.intensity}",
        f"Energy: {report.energy}",
        f"Tracks: {report.track_count}",
        f"Event count: {report.event_count}",
        f"Shown events: {len(visible_events) if include_events else 0}",
        f"Truncated events: {report.event_count - len(visible_events) if include_events else 0}",
        "Safety flags:",
        f"- mock_only: {report.mock_only}",
        f"- hardware_required: {report.hardware_required}",
        f"- opens_ports: {report.opens_ports}",
        f"- sends_midi: {report.sends_midi}",
        f"- active_behavior: {report.active_behavior}",
        "Events:",
    ]
    if include_events:
        lines.extend(_oxi_macro_event_line(event) for event in visible_events)
    else:
        lines.append("- hidden; pass --events to show deterministic mock rows")
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_analog_four_oxi_macro_report(
    report: AnalogFourOxiMacroReport | None = None,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing A4 OXI macro report lines."""

    resolved_report = report if report is not None else build_analog_four_oxi_macro_report()
    return passive_report_lines(
        _HEADER,
        _oxi_macro_body_lines(
            resolved_report,
            include_events=include_events,
            event_limit=event_limit,
        ),
    )


def _oxi_macro_event_json(event: AnalogFourOxiMacroEvent) -> dict[str, object]:
    return {
        "track": event.track,
        "role": event.role,
        "lane": event.lane,
        "parameter": event.parameter,
        "section": event.section,
        "encoder": event.encoder,
        "channel": event.channel,
        "control": event.control,
        "value": event.value,
        "value_min": event.value_min,
        "value_max": event.value_max,
        "intent": event.intent,
    }


def to_analog_four_oxi_macro_json(
    report: AnalogFourOxiMacroReport,
    *,
    event_limit: int = 0,
) -> dict[str, object]:
    """Return deterministic machine-readable A4 OXI macro metadata."""

    visible_events = _oxi_macro_visible_events(report.events, event_limit=event_limit)
    return {
        "macro_name": report.macro_name,
        "macro_label": report.macro_label,
        "summary": report.summary,
        "seed": report.seed,
        "intensity": report.intensity,
        "energy": report.energy,
        "track_count": report.track_count,
        "event_count": report.event_count,
        "shown_count": len(visible_events),
        "truncated_count": report.event_count - len(visible_events),
        "mock_only": report.mock_only,
        "hardware_required": report.hardware_required,
        "opens_ports": report.opens_ports,
        "sends_midi": report.sends_midi,
        "active_behavior": report.active_behavior,
        "events": [_oxi_macro_event_json(event) for event in visible_events],
        "safety": list(SAFETY_LINES),
    }


def _parse_int(value: str, *, option: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc


def _parse_oxi_macro_nonnegative_int(value: str, *, option: str) -> int:
    parsed = _parse_int(value, option=option)
    if parsed < 0:
        raise ValueError(f"{option} must be >= 0")
    return parsed


def _parse_intensity(value: str, *, option: str) -> int:
    parsed = _parse_int(value, option=option)
    _validate_intensity(parsed)
    return parsed


def _parse_oxi_macro_cli_args(argv: Sequence[str]) -> dict[str, object]:
    macro_name = DEFAULT_ANALOG_FOUR_OXI_MACRO
    seed = 0
    intensity = 4
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    macro_seen = False
    remaining = list(argv)
    while remaining:
        argument = remaining.pop(0)
        if argument == "--events":
            include_events = True
            continue
        if argument == "--json":
            json_output = True
            continue
        if argument in {"--seed", "--intensity", "--limit"}:
            if not remaining:
                raise ValueError(_USAGE)
            value = remaining.pop(0)
            if argument == "--seed":
                seed = _parse_int(value, option=argument)
            elif argument == "--intensity":
                intensity = _parse_intensity(value, option=argument)
            else:
                event_limit = _parse_oxi_macro_nonnegative_int(value, option=argument)
            continue
        if argument.startswith("--") or macro_seen:
            raise ValueError(_USAGE)
        macro_name = argument
        macro_seen = True
    return {
        "macro_name": macro_name,
        "seed": seed,
        "intensity": intensity,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _handle_oxi_macro_cli_report(
    *,
    macro_name: str,
    seed: int,
    intensity: int,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        report = build_analog_four_oxi_macro_report(
            macro_name,
            seed=seed,
            intensity=intensity,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_analog_four_oxi_macro_json(report, event_limit=event_limit),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_analog_four_oxi_macro_report(
            report,
            include_events=include_events,
            event_limit=event_limit,
        )
    except (ValueError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_oxi_macro_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


ANALOG_FOUR_OXI_MACRO_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-oxi-macro-report",
    summary="Print passive Analog Four OXI-style macro preview metadata.",
    args_parser=_parse_oxi_macro_cli_args,
    handler=_handle_oxi_macro_cli_report,
    error_formatter=_format_oxi_macro_cli_error,
)

register(ANALOG_FOUR_OXI_MACRO_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_OXI_MACRO_CLI_COMMAND",
    "AnalogFourOxiMacroEvent",
    "AnalogFourOxiMacroReport",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_analog_four_oxi_macro_report",
    "format_analog_four_oxi_macro_report",
    "to_analog_four_oxi_macro_json",
]
