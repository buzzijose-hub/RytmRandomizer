"""Passive Analog Four patch send-plan report."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from ..style_analysis import StyleAnalysisDependencyError
from ..style_analysis.analog_four_patch_send_plan import (
    ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    ANALOG_FOUR_PATCH_CANDIDATE_MIN,
    ANALOG_FOUR_PATCH_SEND_KIND_CC,
    ANALOG_FOUR_PATCH_SEND_PLAN_SAFETY,
    ANALOG_FOUR_TRACK_MAX,
    ANALOG_FOUR_TRACK_MIN,
    AnalogFourPatchManualEvent,
    AnalogFourPatchSendEvent,
    AnalogFourPatchSendPlan,
    analog_four_patch_send_plan_to_dict,
    build_analog_four_patch_send_plan,
    build_analog_four_patch_send_plan_from_source,
)
from ..style_analysis.feature_report import FeatureReport
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four patch send plan"
SOURCE_MODULE: Final[str] = "reports.analog_four_patch_send_plan"
SAFETY_LINES: Final[tuple[str, ...]] = ANALOG_FOUR_PATCH_SEND_PLAN_SAFETY
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli analog-four-patch-send-plan-report "
    "(--description <text>|--audio <path>) [--track N] [--candidate N] [--json]"
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class AnalogFourPatchSendPlanReport:
    """Operator-facing report wrapper for passive A4 patch send plans."""

    source_label: str
    source_value: str
    plan: AnalogFourPatchSendPlan


def build_analog_four_patch_send_plan_report(
    feature_report: FeatureReport,
    *,
    source_label: str,
    source_value: str,
    track: int,
    selected_candidate: int,
) -> AnalogFourPatchSendPlanReport:
    """Build a passive A4 patch send-plan report from a feature report."""

    plan = build_analog_four_patch_send_plan(
        feature_report,
        track=track,
        selected_candidate=selected_candidate,
    )
    return AnalogFourPatchSendPlanReport(
        source_label=source_label,
        source_value=source_value,
        plan=plan,
    )


def build_analog_four_patch_send_plan_report_from_source(
    source_flag: str,
    source_value: str,
    *,
    track: int,
    selected_candidate: int,
) -> AnalogFourPatchSendPlanReport:
    """Build a passive send-plan report from a description or audio source."""

    source = build_analog_four_patch_send_plan_from_source(
        source_flag,
        source_value,
        track=track,
        selected_candidate=selected_candidate,
    )
    return AnalogFourPatchSendPlanReport(
        source_label=source.source_label,
        source_value=source.source_value,
        plan=source.plan,
    )


def format_analog_four_patch_send_plan_report(
    report: AnalogFourPatchSendPlanReport,
) -> list[str]:
    """Return deterministic operator-facing patch send-plan lines."""

    plan = report.plan
    summary = plan.summary
    lines: list[str] = [
        "Summary:",
        f"- Source: {report.source_label}",
        f"- Source confidence: {plan.source_confidence}",
        f"- Source hash: {plan.source_hash}",
        f"- Send-plan mode: {plan.mode}",
        f"- Selected track: {plan.selected_track}",
        f"- Selected candidate: {plan.selected_candidate} / {plan.selected_label}",
        f"- Live dial path: {summary.live_dial_path}",
        f"- Sendable events: {summary.sendable_count} / {summary.total_rows} "
        f"({summary.ready_percentage}%)",
        f"- Transport messages: {summary.transport_message_count}",
        f"- Transport counts: cc {summary.cc_event_count}, nrpn {summary.nrpn_event_count}",
        f"- Manual rows skipped: {summary.manual_count}",
        f"- Blocker: {summary.blocking_reason}",
        "Sendable MIDI events:",
    ]
    lines.extend(_send_event_line(event) for event in plan.send_events)
    lines.append("Manual/front-panel rows:")
    lines.extend(_manual_event_line(event) for event in plan.manual_events)
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in plan.safety)
    return passive_report_lines(_HEADER, lines)


def build_analog_four_patch_send_plan_payload(
    report: AnalogFourPatchSendPlanReport,
) -> dict[str, object]:
    """Return deterministic machine-readable report payload."""

    return {
        "source": {
            "type": report.source_label,
            "value": report.source_value,
        },
        "selected_candidate": report.plan.selected_candidate,
        "selected_track": report.plan.selected_track,
        "send_plan": analog_four_patch_send_plan_to_dict(report.plan),
        "safety": list(report.plan.safety),
    }


def _send_event_line(event: AnalogFourPatchSendEvent) -> str:
    return (
        f"- {event.sequence:02d} T{event.track} ch{event.channel} "
        f"{_transport_label(event)} {event.parameter} -> {event.midi_value} | "
        f"screen {event.screen_value} | {event.section} {event.encoder} | "
        f"{event.dial_direction} | {event.rationale}"
    )


def _transport_label(event: AnalogFourPatchSendEvent) -> str:
    if event.message_kind == ANALOG_FOUR_PATCH_SEND_KIND_CC:
        return f"CC{event.cc_msb}"
    if event.nrpn_address is None:
        return "NRPN pending"
    return f"NRPN {event.nrpn_address[0]}:{event.nrpn_address[1]}"


def _manual_event_line(event: AnalogFourPatchManualEvent) -> str:
    return (
        f"- {event.sequence:02d} T{event.track} {event.parameter} | "
        f"screen {event.screen_value} | skipped | {event.skip_reason} | "
        f"{event.dial_direction} | {event.rationale}"
    )


def _parse_patch_send_plan_int(value: str, *, option: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc


def _validate_patch_send_plan_range(
    value: int,
    *,
    option: str,
    minimum: int,
    maximum: int,
) -> None:
    if value < minimum or value > maximum:
        raise ValueError(f"{option} must be in {minimum}..{maximum}")


def _parse_analog_four_patch_send_plan_args(argv: Sequence[str]) -> dict[str, object]:
    json_output = False
    track = 1
    selected_candidate = 1
    sources: list[tuple[str, str]] = []
    index = 0
    while index < len(argv):
        option = argv[index]
        if option == "--json":
            json_output = True
            index += 1
            continue
        if option in ("--description", "--audio"):
            if index + 1 >= len(argv):
                raise ValueError(f"{option} requires a value")
            sources.append((option, argv[index + 1]))
            index += 2
            continue
        if option == "--track":
            if index + 1 >= len(argv):
                raise ValueError("--track requires a value")
            track = _parse_patch_send_plan_int(argv[index + 1], option=option)
            index += 2
            continue
        if option == "--candidate":
            if index + 1 >= len(argv):
                raise ValueError("--candidate requires a value")
            selected_candidate = _parse_patch_send_plan_int(argv[index + 1], option=option)
            index += 2
            continue
        raise ValueError(f"unknown argument: {option}")

    if len(sources) != 1:
        raise ValueError(
            "analog-four-patch-send-plan-report requires exactly one source: "
            "--description or --audio"
        )
    _validate_patch_send_plan_range(
        track,
        option="--track",
        minimum=ANALOG_FOUR_TRACK_MIN,
        maximum=ANALOG_FOUR_TRACK_MAX,
    )
    _validate_patch_send_plan_range(
        selected_candidate,
        option="--candidate",
        minimum=ANALOG_FOUR_PATCH_CANDIDATE_MIN,
        maximum=ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    )
    source_flag, source_value = sources[0]
    return {
        "source_flag": source_flag,
        "source_value": source_value,
        "track": track,
        "selected_candidate": selected_candidate,
        "json_output": json_output,
    }


def _format_patch_send_plan_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


def _handle_analog_four_patch_send_plan_report(
    source_flag: str,
    source_value: str,
    track: int,
    selected_candidate: int,
    json_output: bool = False,
) -> int:
    try:
        report = build_analog_four_patch_send_plan_report_from_source(
            source_flag,
            source_value,
            track=track,
            selected_candidate=selected_candidate,
        )
    except (StyleAnalysisDependencyError, ValueError, TypeError, KeyError) as exc:
        sys.stderr.write(f"{_format_patch_send_plan_error(exc)}\n")
        return 2

    if json_output:
        sys.stdout.write(
            json.dumps(
                build_analog_four_patch_send_plan_payload(report),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0

    sys.stdout.write("\n".join(format_analog_four_patch_send_plan_report(report)))
    sys.stdout.write("\n")
    return 0


ANALOG_FOUR_PATCH_SEND_PLAN_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-patch-send-plan-report",
    summary=(
        "Preview the CC/NRPN send plan for a generated Analog Four patch " "without opening MIDI."
    ),
    args_parser=_parse_analog_four_patch_send_plan_args,
    handler=_handle_analog_four_patch_send_plan_report,
    error_formatter=_format_patch_send_plan_error,
)

register(ANALOG_FOUR_PATCH_SEND_PLAN_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_PATCH_SEND_PLAN_CLI_COMMAND",
    "AnalogFourPatchSendPlanReport",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "USAGE",
    "build_analog_four_patch_send_plan_payload",
    "build_analog_four_patch_send_plan_report",
    "build_analog_four_patch_send_plan_report_from_source",
    "format_analog_four_patch_send_plan_report",
]
