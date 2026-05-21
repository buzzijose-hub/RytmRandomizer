"""Passive reference performance arc reports for long-form techno planning."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.style_performance_arcs import STYLE_PERFORMANCE_ARCS, StylePerformanceArc
from .dual_machine_style_kit_selection import normalize_selection_scope
from .dual_machine_style_performance_set_plan import (
    DualMachineStylePerformanceSetPlan,
    build_dual_machine_style_performance_set_plan_report,
    format_dual_machine_style_performance_set_plan_report,
    to_dual_machine_style_performance_set_plan_json,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc report"
LIST_TITLE: Final[str] = "RytmRandomizer passive style performance arc list"
INSPECT_TITLE: Final[str] = "RytmRandomizer passive style performance arc inspection"
SEARCH_TITLE: Final[str] = "RytmRandomizer passive style performance arc search"
SET_PLAN_TITLE: Final[str] = "RytmRandomizer passive style performance arc set plan"
SOURCE_MODULE: Final[str] = "reports.style_performance_arcs"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "metadata and plan expansion only",
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
_LIST_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=LIST_TITLE,
    source_module=SOURCE_MODULE,
)
_INSPECT_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=INSPECT_TITLE,
    source_module=SOURCE_MODULE,
)
_SEARCH_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=SEARCH_TITLE,
    source_module=SOURCE_MODULE,
)
_SET_PLAN_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=SET_PLAN_TITLE,
    source_module=SOURCE_MODULE,
)
_SET_PLAN_USAGE: Final[str] = (
    "style-performance-arc-set-plan-report usage: "
    "<arc-key> --rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]"
)
_SET_PLAN_OPTIONS: Final[tuple[str, ...]] = (
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
_DEFAULT_EVENT_LIMIT: Final[int] = 24


@dataclass(frozen=True)
class StylePerformanceArcCatalogReport:
    """Passive catalog report for reference performance arcs."""

    arc_count: int
    arcs_by_key: Mapping[str, StylePerformanceArc]


@dataclass(frozen=True)
class StylePerformanceArcSetPlanReport:
    """Passive reference arc expansion into the dual-machine set planner."""

    arc: StylePerformanceArc
    plan: DualMachineStylePerformanceSetPlan


def _join(values: Sequence[str]) -> str:
    return ", ".join(values)


def _sequence(values: Sequence[str]) -> str:
    return " -> ".join(values)


def _safety_lines() -> list[str]:
    return [SAFETY_SECTION_HEADER, *[f"- {line}" for line in SAFETY_LINES]]


def _arcs_by_key() -> Mapping[str, StylePerformanceArc]:
    return MappingProxyType(dict(STYLE_PERFORMANCE_ARCS))


def _normalized_arc_key(key: str) -> str:
    return str(key).lower()


def _arc_or_raise(key: str) -> StylePerformanceArc:
    normalized_key = _normalized_arc_key(key)
    arc = STYLE_PERFORMANCE_ARCS.get(normalized_key)
    if arc is None:
        raise KeyError(f"unknown style performance arc: {normalized_key}")
    return arc


def _search_text(arc: StylePerformanceArc) -> str:
    values = [
        arc.key,
        arc.name,
        arc.summary,
        *arc.references,
        *arc.tags,
        *arc.style_keys,
        *arc.operator_notes,
    ]
    return "\n".join(values).lower()


def build_style_performance_arc_catalog_report() -> StylePerformanceArcCatalogReport:
    """Return passive catalog data for all reference performance arcs."""

    arcs_by_key = _arcs_by_key()
    return StylePerformanceArcCatalogReport(
        arc_count=len(arcs_by_key),
        arcs_by_key=arcs_by_key,
    )


def _default_plan_text(arc: StylePerformanceArc) -> str:
    return (
        f"scope={arc.default_scope}, minutes={arc.default_total_minutes}, "
        f"rank={arc.default_selection_rank}, "
        f"discovery={arc.default_discovery_start}->{arc.default_discovery_end}"
    )


def _arc_summary_lines(arc: StylePerformanceArc) -> list[str]:
    return [
        f"Key: {arc.key}",
        f"Name: {arc.name}",
        f"Summary: {arc.summary}",
        f"Primary references: {_join(arc.references[:2])}",
        "References:",
        *[f"- {reference}" for reference in arc.references],
        f"Tags: {_join(arc.tags)}",
        f"Style sequence: {_sequence(arc.style_keys)}",
        f"Default plan: {_default_plan_text(arc)}",
        "Operator notes:",
        *[f"- {note}" for note in arc.operator_notes],
    ]


def format_style_performance_arc_report(
    report: StylePerformanceArcCatalogReport | None = None,
) -> list[str]:
    """Return deterministic catalog lines for all reference performance arcs."""

    source_report = build_style_performance_arc_catalog_report() if report is None else report
    lines = [
        "Summary:",
        f"- Arcs: {source_report.arc_count}",
        "- Purpose: passive reference arcs for long-form live set planning",
        "Arcs:",
    ]
    for key in sorted(source_report.arcs_by_key):
        arc = source_report.arcs_by_key[key]
        lines.extend(
            [
                f"{arc.key}: {arc.name}",
                f"  Primary references: {_join(arc.references[:2])}",
                f"  Default plan: {_default_plan_text(arc)}",
                f"  Style sequence: {_sequence(arc.style_keys)}",
                f"  Summary: {arc.summary}",
            ]
        )
    lines.extend(_safety_lines())
    return passive_report_lines(_HEADER, lines)


def format_style_performance_arc_list() -> list[str]:
    """Return deterministic list lines for all reference arcs."""

    lines = [
        f"Count: {len(STYLE_PERFORMANCE_ARCS)}",
        "Items:",
    ]
    for key in sorted(STYLE_PERFORMANCE_ARCS):
        arc = STYLE_PERFORMANCE_ARCS[key]
        lines.append(f"- {arc.key}: {arc.name} ({_join(arc.tags)})")
    lines.extend(_safety_lines())
    return passive_report_lines(_LIST_HEADER, lines)


def format_style_performance_arc_inspection(key: str) -> list[str]:
    """Return deterministic detail lines for one reference arc."""

    normalized_key = _normalized_arc_key(key)
    arc = STYLE_PERFORMANCE_ARCS.get(normalized_key)
    if arc is None:
        lines = [
            f"Key: {normalized_key}",
            "Found: False",
            "Message: Style performance arc not found. No MIDI was sent. No command executed.",
        ]
        lines.extend(_safety_lines())
        return passive_report_lines(_INSPECT_HEADER, lines)

    lines = [
        f"Key: {arc.key}",
        "Found: True",
        *_arc_summary_lines(arc)[1:],
    ]
    lines.extend(_safety_lines())
    return passive_report_lines(_INSPECT_HEADER, lines)


def format_style_performance_arc_search(query: str) -> list[str]:
    """Return deterministic search lines for reference arc metadata."""

    normalized_query = str(query)
    search_query = normalized_query.lower()
    matches = [
        arc
        for key, arc in sorted(STYLE_PERFORMANCE_ARCS.items())
        if search_query in _search_text(arc)
    ]
    lines = [
        f"Query: {normalized_query}",
        f"Match count: {len(matches)}",
        "Matches:",
    ]
    if not matches:
        lines.append("- no matches found. No MIDI was sent. No command executed.")
    else:
        for arc in matches:
            lines.append(f"- {arc.key}: {arc.name}")
    lines.extend(_safety_lines())
    return passive_report_lines(_SEARCH_HEADER, lines)


def _default_plan_json(arc: StylePerformanceArc) -> dict[str, object]:
    return {
        "scope": arc.default_scope,
        "total_minutes": arc.default_total_minutes,
        "selection_rank": arc.default_selection_rank,
        "discovery_start": arc.default_discovery_start,
        "discovery_end": arc.default_discovery_end,
    }


def to_style_performance_arc_json(arc: StylePerformanceArc) -> dict[str, object]:
    """Return deterministic JSON-ready metadata for one reference arc."""

    return {
        "key": arc.key,
        "name": arc.name,
        "summary": arc.summary,
        "references": list(arc.references),
        "tags": list(arc.tags),
        "style_keys": list(arc.style_keys),
        "default_plan": _default_plan_json(arc),
        "operator_notes": list(arc.operator_notes),
    }


def _scope_from_paths_or_default(
    *,
    arc: StylePerformanceArc,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
) -> str:
    if (
        arc.default_scope == "dual"
        and rytm_sysex_path is not None
        and analog_four_sysex_path is None
    ):
        return "rytm-only"
    if (
        arc.default_scope == "dual"
        and rytm_sysex_path is None
        and analog_four_sysex_path is not None
    ):
        return "analog-four-only"
    return arc.default_scope


def build_style_performance_arc_set_plan_report(
    arc_key: str,
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
) -> StylePerformanceArcSetPlanReport:
    """Expand one passive reference arc into the timed dual-machine set planner."""

    arc = _arc_or_raise(arc_key)
    resolved_scope = (
        _scope_from_paths_or_default(
            arc=arc,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
        )
        if scope is None
        else normalize_selection_scope(scope)
    )
    plan = build_dual_machine_style_performance_set_plan_report(
        arc.style_keys,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        scope=resolved_scope,
        selection_rank=arc.default_selection_rank if selection_rank is None else selection_rank,
        total_minutes=arc.default_total_minutes if total_minutes is None else total_minutes,
        segment_minutes=segment_minutes,
        discovery_start=(
            arc.default_discovery_start if discovery_start is None else discovery_start
        ),
        discovery_end=arc.default_discovery_end if discovery_end is None else discovery_end,
    )
    return StylePerformanceArcSetPlanReport(arc=arc, plan=plan)


def _set_plan_intro_lines(report: StylePerformanceArcSetPlanReport) -> list[str]:
    arc = report.arc
    return [
        f"Arc: {arc.name}",
        f"Key: {arc.key}",
        f"Summary: {arc.summary}",
        f"References: {_join(arc.references)}",
        f"Tags: {_join(arc.tags)}",
        f"Default plan: {_default_plan_text(arc)}",
        "Operator notes:",
        *[f"- {note}" for note in arc.operator_notes],
        "Embedded performance set plan:",
    ]


def format_style_performance_arc_set_plan_report(
    report: StylePerformanceArcSetPlanReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing arc-expanded set plan lines."""

    lines = _set_plan_intro_lines(report)
    lines.extend(
        format_dual_machine_style_performance_set_plan_report(
            report.plan,
            include_events=include_events,
            event_limit=event_limit,
        )
    )
    lines.append(SAFETY_SECTION_HEADER)
    lines.append("- reference performance arc")
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return passive_report_lines(_SET_PLAN_HEADER, lines)


def to_style_performance_arc_set_plan_json(
    report: StylePerformanceArcSetPlanReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready metadata for an arc-expanded set plan."""

    return {
        "arc": to_style_performance_arc_json(report.arc),
        "performance_plan": to_dual_machine_style_performance_set_plan_json(report.plan),
        "safety": list(SAFETY_LINES),
    }


def _parse_no_args(argv: Sequence[str]) -> dict[str, object]:
    if argv:
        raise ValueError("command takes no arguments")
    return {}


def _parse_arc_key(argv: Sequence[str]) -> dict[str, object]:
    if len(argv) != 1:
        raise ValueError("command requires exactly one arc key")
    return {"key": argv[0]}


def _parse_query(argv: Sequence[str]) -> dict[str, object]:
    if len(argv) != 1:
        raise ValueError("command requires exactly one query")
    return {"query": argv[0]}


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


def _pop_option_value(remaining: list[str]) -> str:
    if not remaining:
        raise ValueError(_SET_PLAN_USAGE)
    return remaining.pop(0)


def _parse_arc_set_plan_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if not argv:
        raise ValueError(_SET_PLAN_USAGE)
    arc_key = argv[0]
    if arc_key.startswith("--"):
        raise ValueError(_SET_PLAN_USAGE)
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank: int | None = None
    total_minutes: int | None = None
    segment_minutes: int | None = None
    discovery_start: int | None = None
    discovery_end: int | None = None
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    remaining = list(argv[1:])
    while remaining:
        option = remaining.pop(0)
        if option == "--events":
            include_events = True
            continue
        if option == "--json":
            json_output = True
            continue
        if option not in _SET_PLAN_OPTIONS:
            raise ValueError(_SET_PLAN_USAGE)
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
            discovery_start = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery-end":
            discovery_end = _parse_nonnegative_int(value, option=option)
        else:
            event_limit = _parse_nonnegative_int(value, option=option)
    return {
        "arc_key": arc_key,
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": scope,
        "selection_rank": selection_rank,
        "total_minutes": total_minutes,
        "segment_minutes": segment_minutes,
        "discovery_start": discovery_start,
        "discovery_end": discovery_end,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _write_lines(lines: Sequence[str]) -> int:
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _handle_style_performance_arc_report() -> int:
    return _write_lines(format_style_performance_arc_report())


def _handle_style_performance_arc_list() -> int:
    return _write_lines(format_style_performance_arc_list())


def _handle_style_performance_arc_inspection(key: str) -> int:
    lines = format_style_performance_arc_inspection(key)
    output = "\n".join(lines)
    if "Found: True" in lines:
        sys.stdout.write(f"{output}\n")
        return 0
    sys.stderr.write(f"{output}\n")
    return 1


def _handle_style_performance_arc_search(query: str) -> int:
    return _write_lines(format_style_performance_arc_search(query))


def _handle_style_performance_arc_set_plan_report(
    *,
    arc_key: str,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str | None,
    selection_rank: int | None,
    total_minutes: int | None,
    segment_minutes: int | None,
    discovery_start: int | None,
    discovery_end: int | None,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_set_plan_report(
            arc_key,
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
                    to_style_performance_arc_set_plan_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_set_plan_report(
            report,
            include_events=include_events,
            event_limit=event_limit,
        )
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    return _write_lines(lines)


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_REPORT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-report",
    summary="Print the passive style performance arc report.",
    args_parser=_parse_no_args,
    handler=_handle_style_performance_arc_report,
)
LIST_STYLE_PERFORMANCE_ARCS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="list-style-performance-arcs",
    summary="List passive style performance arc keys and names.",
    args_parser=_parse_no_args,
    handler=_handle_style_performance_arc_list,
)
INSPECT_STYLE_PERFORMANCE_ARC_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="inspect-style-performance-arc",
    summary="Inspect passive style performance arc metadata by key.",
    args_parser=_parse_arc_key,
    handler=_handle_style_performance_arc_inspection,
)
SEARCH_STYLE_PERFORMANCE_ARCS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="search-style-performance-arcs",
    summary="Search passive style performance arc metadata.",
    args_parser=_parse_query,
    handler=_handle_style_performance_arc_search,
)
STYLE_PERFORMANCE_ARC_SET_PLAN_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-set-plan-report",
    summary="Print passive timed performance set plans from a reference arc.",
    args_parser=_parse_arc_set_plan_cli_args,
    handler=_handle_style_performance_arc_set_plan_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_REPORT_CLI_COMMAND)
register(LIST_STYLE_PERFORMANCE_ARCS_CLI_COMMAND)
register(INSPECT_STYLE_PERFORMANCE_ARC_CLI_COMMAND)
register(SEARCH_STYLE_PERFORMANCE_ARCS_CLI_COMMAND)
register(STYLE_PERFORMANCE_ARC_SET_PLAN_CLI_COMMAND)

__all__ = [
    "INSPECT_STYLE_PERFORMANCE_ARC_CLI_COMMAND",
    "LIST_STYLE_PERFORMANCE_ARCS_CLI_COMMAND",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SEARCH_STYLE_PERFORMANCE_ARCS_CLI_COMMAND",
    "SET_PLAN_TITLE",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_REPORT_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_SET_PLAN_CLI_COMMAND",
    "StylePerformanceArcCatalogReport",
    "StylePerformanceArcSetPlanReport",
    "build_style_performance_arc_catalog_report",
    "build_style_performance_arc_set_plan_report",
    "format_style_performance_arc_inspection",
    "format_style_performance_arc_list",
    "format_style_performance_arc_report",
    "format_style_performance_arc_search",
    "format_style_performance_arc_set_plan_report",
    "to_style_performance_arc_json",
    "to_style_performance_arc_set_plan_json",
]
