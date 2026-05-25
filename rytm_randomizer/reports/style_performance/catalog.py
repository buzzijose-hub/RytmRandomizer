"""Catalog, list, inspect, search, and set-plan reports for the passive
style performance arc catalog.

This is the bottom of the dependency stack for the
``style_performance`` subpackage: readiness, audition packet, rehearsal
manifest, live session packet, live render bundle, live cue sheet, and
reference match all build on top of :func:`build_style_performance_arc_set_plan_report`
defined here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ...data.style_performance_arcs import STYLE_PERFORMANCE_ARCS, StylePerformanceArc
from ..dual_machine_style_kit_selection import normalize_selection_scope
from ..dual_machine_style_performance_set_plan import (
    DualMachineStylePerformanceSetPlan,
    build_dual_machine_style_performance_set_plan_report,
    format_dual_machine_style_performance_set_plan_report,
    to_dual_machine_style_performance_set_plan_json,
)
from ..formatter import SAFETY_SECTION_HEADER, passive_report_lines
from ._constants import (
    _DEFAULT_EVENT_LIMIT,
    _HEADER,
    _INSPECT_HEADER,
    _LIST_HEADER,
    _SEARCH_HEADER,
    _SET_PLAN_HEADER,
    SAFETY_LINES,
)
from ._helpers import (
    _arc_or_raise,
    _arcs_by_key,
    _join,
    _normalized_arc_key,
    _safety_lines,
    _search_text,
    _sequence,
)


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
