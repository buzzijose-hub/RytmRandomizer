"""Passive timed performance set planning for dual-machine saved kits."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.style_discovery import (
    DEFAULT_STYLE_DISCOVERY_AMOUNT,
    style_discovery_policy,
)
from .dual_machine_style_kit_selection import normalize_selection_scope
from .dual_machine_style_selection_mock_preview import (
    SAFETY_LINES as SELECTION_MOCK_PREVIEW_SAFETY_LINES,
)
from .dual_machine_style_selection_mock_preview import (
    DualMachineStyleSelectionMockPreviewPlan,
    build_dual_machine_style_selection_mock_preview_report,
    format_dual_machine_style_selection_mock_preview_event_rows,
    to_dual_machine_style_selection_mock_preview_json,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive dual-machine style performance set plan"
SOURCE_MODULE: Final[str] = "reports.dual_machine_style_performance_set_plan"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "performance set plan",
) + tuple(line for line in SELECTION_MOCK_PREVIEW_SAFETY_LINES if line != "passive/read-only")
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_USAGE: Final[str] = (
    "dual-machine-style-performance-set-plan-report usage: "
    "<style-key> [<style-key> ...] --rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]"
)
_DEFAULT_SELECTION_RANK: Final[int] = 1
_DEFAULT_TOTAL_MINUTES: Final[int] = 300
_DEFAULT_EVENT_LIMIT: Final[int] = 24
_CLI_OPTIONS: Final[tuple[str, ...]] = (
    "--rytm",
    "--analog-four",
    "--scope",
    "--rank",
    "--total-minutes",
    "--segment-minutes",
    "--discovery-start",
    "--discovery-end",
    "--events",
    "--limit",
    "--json",
)


@dataclass(frozen=True)
class DualMachineStylePerformanceSetSegment:
    """One timed style segment in a passive live performance set plan."""

    position: int
    style_key: str
    start_minute: int
    end_minute: int
    duration_minutes: int
    time_window: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    selection_readiness: str
    selection_score: int
    operator_action: str
    event_row_count: int
    mock_message_count: int
    deferred_row_count: int
    preview_plan: DualMachineStyleSelectionMockPreviewPlan


@dataclass(frozen=True)
class DualMachineStylePerformanceSetPlan:
    """Passive operator plan for a timed multi-style performance arc."""

    style_keys: tuple[str, ...]
    scope: str
    total_minutes: int
    discovery_start: int
    discovery_end: int
    selection_rank: int
    segment_count: int
    ready_segment_count: int
    partial_segment_count: int
    blocked_segment_count: int
    total_event_row_count: int
    total_mock_message_count: int
    total_deferred_row_count: int
    segments: tuple[DualMachineStylePerformanceSetSegment, ...]


def _normalized_style_keys(style_keys: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(key.strip() for key in style_keys if key.strip())
    if not normalized:
        raise ValueError("performance set plan requires at least one style key")
    return normalized


def _positive_int(value: int, *, name: str) -> int:
    if value < 1:
        raise ValueError(f"{name} must be >= 1")
    return value


def _readiness_count(
    segments: Sequence[DualMachineStylePerformanceSetSegment],
    readiness: str,
) -> int:
    return sum(1 for segment in segments if segment.selection_readiness == readiness)


def _time_window(start_minute: int, end_minute: int) -> str:
    start_hours, start_remainder = divmod(start_minute, 60)
    end_hours, end_remainder = divmod(end_minute, 60)
    return f"{start_hours:02d}:{start_remainder:02d}-{end_hours:02d}:{end_remainder:02d}"


def _duration_for_position(
    *,
    position: int,
    style_count: int,
    total_minutes: int,
) -> int:
    start = round((position - 1) * total_minutes / style_count)
    end = round(position * total_minutes / style_count)
    return end - start


def _segment_durations(
    *,
    style_count: int,
    total_minutes: int,
    segment_minutes: int | None,
) -> tuple[int, ...]:
    if segment_minutes is not None:
        return tuple(segment_minutes for _ in range(style_count))
    return tuple(
        _duration_for_position(
            position=position,
            style_count=style_count,
            total_minutes=total_minutes,
        )
        for position in range(1, style_count + 1)
    )


def _discovery_amounts(
    *,
    style_count: int,
    discovery_start: int,
    discovery_end: int,
) -> tuple[int, ...]:
    if style_count == 1:
        return (style_discovery_policy(discovery_start).amount,)
    return tuple(
        style_discovery_policy(
            round(discovery_start + ((discovery_end - discovery_start) * index / (style_count - 1)))
        ).amount
        for index in range(style_count)
    )


def _segment_from_preview(
    *,
    position: int,
    style_key: str,
    start_minute: int,
    duration_minutes: int,
    discovery_amount: int,
    preview_plan: DualMachineStyleSelectionMockPreviewPlan,
) -> DualMachineStylePerformanceSetSegment:
    end_minute = start_minute + duration_minutes
    policy = style_discovery_policy(discovery_amount)
    return DualMachineStylePerformanceSetSegment(
        position=position,
        style_key=style_key,
        start_minute=start_minute,
        end_minute=end_minute,
        duration_minutes=duration_minutes,
        time_window=_time_window(start_minute, end_minute),
        discovery_amount=policy.amount,
        discovery_band=policy.band,
        mutation_depth=policy.mutation_depth,
        selection_readiness=preview_plan.selection_readiness,
        selection_score=preview_plan.selection_score,
        operator_action=preview_plan.operator_action,
        event_row_count=preview_plan.total_event_row_count,
        mock_message_count=preview_plan.total_mock_message_count,
        deferred_row_count=preview_plan.total_deferred_row_count,
        preview_plan=preview_plan,
    )


def build_dual_machine_style_performance_set_plan_report(
    style_keys: Sequence[str],
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int = _DEFAULT_SELECTION_RANK,
    total_minutes: int = _DEFAULT_TOTAL_MINUTES,
    segment_minutes: int | None = None,
    discovery_start: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
    discovery_end: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> DualMachineStylePerformanceSetPlan:
    """Return a passive timed performance plan from style kit selections."""

    normalized_keys = _normalized_style_keys(style_keys)
    _positive_int(selection_rank, name="selection_rank")
    resolved_segment_minutes = (
        None if segment_minutes is None else _positive_int(segment_minutes, name="segment_minutes")
    )
    resolved_total_minutes = (
        len(normalized_keys) * resolved_segment_minutes
        if resolved_segment_minutes is not None
        else _positive_int(total_minutes, name="total_minutes")
    )
    durations = _segment_durations(
        style_count=len(normalized_keys),
        total_minutes=resolved_total_minutes,
        segment_minutes=resolved_segment_minutes,
    )
    discovery_amounts = _discovery_amounts(
        style_count=len(normalized_keys),
        discovery_start=discovery_start,
        discovery_end=discovery_end,
    )

    start_minute = 0
    segments: list[DualMachineStylePerformanceSetSegment] = []
    for index, (style_key, duration_minutes, discovery_amount) in enumerate(
        zip(normalized_keys, durations, discovery_amounts),
        start=1,
    ):
        preview = build_dual_machine_style_selection_mock_preview_report(
            style_key,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            discovery_amount=discovery_amount,
        )
        segment = _segment_from_preview(
            position=index,
            style_key=style_key,
            start_minute=start_minute,
            duration_minutes=duration_minutes,
            discovery_amount=discovery_amount,
            preview_plan=preview,
        )
        segments.append(segment)
        start_minute = segment.end_minute

    frozen_segments = tuple(segments)
    return DualMachineStylePerformanceSetPlan(
        style_keys=normalized_keys,
        scope=frozen_segments[0].preview_plan.scope,
        total_minutes=resolved_total_minutes,
        discovery_start=style_discovery_policy(discovery_start).amount,
        discovery_end=style_discovery_policy(discovery_end).amount,
        selection_rank=selection_rank,
        segment_count=len(frozen_segments),
        ready_segment_count=_readiness_count(frozen_segments, "ready"),
        partial_segment_count=_readiness_count(frozen_segments, "partial"),
        blocked_segment_count=_readiness_count(frozen_segments, "blocked"),
        total_event_row_count=sum(segment.event_row_count for segment in frozen_segments),
        total_mock_message_count=sum(segment.mock_message_count for segment in frozen_segments),
        total_deferred_row_count=sum(segment.deferred_row_count for segment in frozen_segments),
        segments=frozen_segments,
    )


def _machine_summary_lines(segment: DualMachineStylePerformanceSetSegment) -> list[str]:
    preview = segment.preview_plan
    if preview.rytm_preview is None:
        rytm_line = "  Rytm: unchanged by scope"
    else:
        rytm_line = (
            f"  Rytm: slot {preview.rytm_preview.slot} {preview.rytm_preview.kit_name} "
            f"/ ready {preview.rytm_preview.preview_ready} "
            f"/ mock rows {preview.rytm_preview.mock_message_count}"
        )
    if preview.analog_four_preview is None:
        analog_four_line = "  Analog Four: unchanged by scope"
    else:
        analog_four_line = (
            f"  Analog Four: slot {preview.analog_four_preview.slot} "
            f"{preview.analog_four_preview.kit_name} "
            f"/ ready {preview.analog_four_preview.preview_ready} "
            f"/ deferred rows {preview.analog_four_preview.deferred_row_count}"
        )
    return [rytm_line, analog_four_line]


def _segment_lines(segment: DualMachineStylePerformanceSetSegment) -> list[str]:
    lines = [
        (
            f"- {segment.position}. {segment.time_window} | {segment.style_key} "
            f"| discovery {segment.discovery_amount} | {segment.discovery_band} "
            f"| readiness {segment.selection_readiness} | score {segment.selection_score} "
            f"| events {segment.event_row_count} | mock messages {segment.mock_message_count} "
            f"| deferred {segment.deferred_row_count}"
        ),
        f"  Action: {segment.operator_action}",
    ]
    lines.extend(_machine_summary_lines(segment))
    return lines


def _event_preview_lines(
    segment: DualMachineStylePerformanceSetSegment,
    *,
    event_limit: int,
) -> list[str]:
    rows = format_dual_machine_style_selection_mock_preview_event_rows(segment.preview_plan)
    lines = [f"Event preview for segment {segment.position} / {segment.style_key}:"]
    if not rows:
        lines.append("- No mock rows available because the selected preview is not ready.")
        return lines
    if event_limit == 0 or event_limit >= len(rows):
        selected_rows = rows
        lines.append("- Showing all events")
    else:
        selected_rows = rows[:event_limit]
        lines.append(f"- Showing first {event_limit} of {len(rows)} events")
    lines.extend(selected_rows)
    return lines


def _body_lines(
    plan: DualMachineStylePerformanceSetPlan,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    lines = [
        f"Scope: {plan.scope}",
        f"Total duration minutes: {plan.total_minutes}",
        f"Segment count: {plan.segment_count}",
        f"Selection rank: {plan.selection_rank}",
        f"Discovery ramp: {plan.discovery_start} -> {plan.discovery_end}",
        f"Ready segments: {plan.ready_segment_count}",
        f"Partial segments: {plan.partial_segment_count}",
        f"Blocked segments: {plan.blocked_segment_count}",
        f"Total event rows: {plan.total_event_row_count}",
        f"Total mock messages: {plan.total_mock_message_count}",
        f"Total deferred rows: {plan.total_deferred_row_count}",
        "Performance segments:",
    ]
    for segment in plan.segments:
        lines.extend(_segment_lines(segment))
        if include_events:
            lines.extend(_event_preview_lines(segment, event_limit=event_limit))
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_dual_machine_style_performance_set_plan_report(
    plan: DualMachineStylePerformanceSetPlan,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing performance set plan lines."""

    return passive_report_lines(
        _HEADER,
        _body_lines(plan, include_events=include_events, event_limit=event_limit),
    )


def _totals_json(plan: DualMachineStylePerformanceSetPlan) -> dict[str, object]:
    return {
        "segments": plan.segment_count,
        "ready": plan.ready_segment_count,
        "partial": plan.partial_segment_count,
        "blocked": plan.blocked_segment_count,
        "event_rows": plan.total_event_row_count,
        "mock_messages": plan.total_mock_message_count,
        "deferred_rows": plan.total_deferred_row_count,
    }


def _segment_json(segment: DualMachineStylePerformanceSetSegment) -> dict[str, object]:
    return {
        "position": segment.position,
        "style_key": segment.style_key,
        "start_minute": segment.start_minute,
        "end_minute": segment.end_minute,
        "duration_minutes": segment.duration_minutes,
        "time_window": segment.time_window,
        "discovery_amount": segment.discovery_amount,
        "discovery_band": segment.discovery_band,
        "mutation_depth": segment.mutation_depth,
        "selection_readiness": segment.selection_readiness,
        "selection_score": segment.selection_score,
        "operator_action": segment.operator_action,
        "event_row_count": segment.event_row_count,
        "mock_message_count": segment.mock_message_count,
        "deferred_row_count": segment.deferred_row_count,
        "preview": to_dual_machine_style_selection_mock_preview_json(segment.preview_plan),
    }


def to_dual_machine_style_performance_set_plan_json(
    plan: DualMachineStylePerformanceSetPlan,
) -> dict[str, object]:
    """Return deterministic set-plan metadata for GUI/analyzer consumers."""

    return {
        "style_keys": list(plan.style_keys),
        "scope": plan.scope,
        "total_minutes": plan.total_minutes,
        "selection_rank": plan.selection_rank,
        "discovery_ramp": {
            "start": plan.discovery_start,
            "end": plan.discovery_end,
        },
        "totals": _totals_json(plan),
        "segments": [_segment_json(segment) for segment in plan.segments],
        "safety": list(SAFETY_LINES),
    }


def _parse_nonnegative_int(value: str, *, option: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{option} must be >= 0")
    return parsed


def _parse_positive_int(value: str, *, option: str) -> int:
    parsed = _parse_nonnegative_int(value, option=option)
    if parsed < 1:
        raise ValueError(f"{option} must be >= 1")
    return parsed


def _parse_discovery_amount(value: str, *, option: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc
    style_discovery_policy(parsed)
    return parsed


def _pop_option_value(remaining: list[str]) -> str:
    if not remaining:
        raise ValueError(_USAGE)
    return remaining.pop(0)


def _auto_scope(
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
) -> str:
    if rytm_sysex_path is not None and analog_four_sysex_path is not None:
        return "dual"
    if rytm_sysex_path is not None:
        return "rytm-only"
    if analog_four_sysex_path is not None:
        return "analog-four-only"
    raise ValueError("performance set plan requires at least one of --rytm or --analog-four")


def _parse_style_keys(remaining: list[str]) -> tuple[str, ...]:
    style_keys: list[str] = []
    while remaining and not remaining[0].startswith("--"):
        style_keys.append(remaining.pop(0))
    if not style_keys:
        raise ValueError(_USAGE)
    return _normalized_style_keys(style_keys)


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if not argv:
        raise ValueError(_USAGE)
    remaining = list(argv)
    style_keys = _parse_style_keys(remaining)
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank = _DEFAULT_SELECTION_RANK
    total_minutes = _DEFAULT_TOTAL_MINUTES
    segment_minutes: int | None = None
    discovery_start = DEFAULT_STYLE_DISCOVERY_AMOUNT
    discovery_end = DEFAULT_STYLE_DISCOVERY_AMOUNT
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    while remaining:
        option = remaining.pop(0)
        if option == "--events":
            include_events = True
            continue
        if option == "--json":
            json_output = True
            continue
        if option not in _CLI_OPTIONS:
            raise ValueError(_USAGE)
        value = _pop_option_value(remaining)
        if option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--rank":
            selection_rank = _parse_positive_int(value, option=option)
        elif option == "--total-minutes":
            total_minutes = _parse_positive_int(value, option=option)
        elif option == "--segment-minutes":
            segment_minutes = _parse_positive_int(value, option=option)
        elif option == "--discovery-start":
            discovery_start = _parse_discovery_amount(value, option=option)
        elif option == "--discovery-end":
            discovery_end = _parse_discovery_amount(value, option=option)
        else:
            event_limit = _parse_nonnegative_int(value, option=option)
    normalized_scope = (
        _auto_scope(rytm_sysex_path, analog_four_sysex_path) if scope is None else scope
    )
    return {
        "style_keys": style_keys,
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": normalized_scope,
        "selection_rank": selection_rank,
        "total_minutes": total_minutes,
        "segment_minutes": segment_minutes,
        "discovery_start": discovery_start,
        "discovery_end": discovery_end,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
    style_keys: Sequence[str],
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str,
    selection_rank: int,
    total_minutes: int,
    segment_minutes: int | None,
    discovery_start: int,
    discovery_end: int,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        plan = build_dual_machine_style_performance_set_plan_report(
            style_keys,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_dual_machine_style_performance_set_plan_json(plan),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_dual_machine_style_performance_set_plan_report(
            plan,
            include_events=include_events,
            event_limit=event_limit,
        )
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


DUAL_MACHINE_STYLE_PERFORMANCE_SET_PLAN_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="dual-machine-style-performance-set-plan-report",
    summary="Print passive timed performance set plans from style selections.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(DUAL_MACHINE_STYLE_PERFORMANCE_SET_PLAN_CLI_COMMAND)

__all__ = [
    "DUAL_MACHINE_STYLE_PERFORMANCE_SET_PLAN_CLI_COMMAND",
    "DualMachineStylePerformanceSetPlan",
    "DualMachineStylePerformanceSetSegment",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_dual_machine_style_performance_set_plan_report",
    "format_dual_machine_style_performance_set_plan_report",
    "to_dual_machine_style_performance_set_plan_json",
]
