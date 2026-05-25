"""Passive reference arc readiness matrix.

Ranks reference arcs against saved kit banks and scope. Built on top of
:func:`build_style_performance_arc_set_plan_report` from
:mod:`.catalog`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ...data.style_performance_arcs import StylePerformanceArc
from ..dual_machine_style_performance_set_plan import (
    DualMachineStylePerformanceSetPlan,
    to_dual_machine_style_performance_set_plan_json,
)
from ..formatter import SAFETY_SECTION_HEADER, passive_report_lines
from ._constants import (
    _DEFAULT_EVENT_LIMIT,
    _READINESS_HEADER,
    _READINESS_SORT_ORDER,
    SAFETY_LINES,
)
from ._helpers import _selected_arc_keys, _sequence
from .catalog import (
    build_style_performance_arc_set_plan_report,
    to_style_performance_arc_json,
)


@dataclass(frozen=True)
class StylePerformanceArcReadinessEntry:
    """One ranked arc readiness row derived from an expanded set plan."""

    position: int
    arc: StylePerformanceArc
    readiness: str
    average_selection_score: int
    operator_action: str
    plan: DualMachineStylePerformanceSetPlan


@dataclass(frozen=True)
class StylePerformanceArcReadinessReport:
    """Passive readiness matrix across reference arcs and saved kit banks."""

    scope: str
    arc_count: int
    ready_arc_count: int
    partial_arc_count: int
    blocked_arc_count: int
    total_segment_count: int
    total_event_row_count: int
    total_mock_message_count: int
    total_deferred_row_count: int
    entries: tuple[StylePerformanceArcReadinessEntry, ...]


def _readiness_for_plan(plan: DualMachineStylePerformanceSetPlan) -> str:
    if plan.blocked_segment_count:
        return "blocked"
    if plan.partial_segment_count:
        return "partial"
    return "ready"


def _average_selection_score(plan: DualMachineStylePerformanceSetPlan) -> int:
    if not plan.segments:
        return 0
    return round(sum(segment.selection_score for segment in plan.segments) / len(plan.segments))


def _readiness_operator_action(
    *,
    readiness: str,
    plan: DualMachineStylePerformanceSetPlan,
) -> str:
    if readiness == "ready":
        return "Ready for live audition with all segments route-ready."
    if readiness == "partial":
        return (
            "Live-audition candidate with caveats: review partial segments, "
            f"{plan.total_deferred_row_count} deferred rows, and keep hardware unchanged "
            "until the mock preview is acceptable."
        )
    return (
        "Blocked for this kit-bank/scope combination: choose another arc, change scope, "
        "or load a different saved-kit bank before audition."
    )


def _readiness_entry_from_set_plan(
    *,
    arc: StylePerformanceArc,
    plan: DualMachineStylePerformanceSetPlan,
) -> StylePerformanceArcReadinessEntry:
    readiness = _readiness_for_plan(plan)
    return StylePerformanceArcReadinessEntry(
        position=0,
        arc=arc,
        readiness=readiness,
        average_selection_score=_average_selection_score(plan),
        operator_action=_readiness_operator_action(readiness=readiness, plan=plan),
        plan=plan,
    )


def _ranked_readiness_entry(
    *,
    position: int,
    entry: StylePerformanceArcReadinessEntry,
) -> StylePerformanceArcReadinessEntry:
    return StylePerformanceArcReadinessEntry(
        position=position,
        arc=entry.arc,
        readiness=entry.readiness,
        average_selection_score=entry.average_selection_score,
        operator_action=entry.operator_action,
        plan=entry.plan,
    )


def _readiness_sort_key(
    entry: StylePerformanceArcReadinessEntry,
) -> tuple[int, int, str]:
    return (
        _READINESS_SORT_ORDER[entry.readiness],
        -entry.average_selection_score,
        entry.arc.key,
    )


def _readiness_count(
    entries: Sequence[StylePerformanceArcReadinessEntry],
    readiness: str,
) -> int:
    return sum(1 for entry in entries if entry.readiness == readiness)


def build_style_performance_arc_readiness_report(
    arc_keys: Sequence[str] | None = None,
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
) -> StylePerformanceArcReadinessReport:
    """Rank passive reference arcs against saved kit banks and scope."""

    raw_entries = []
    for arc_key in _selected_arc_keys(arc_keys):
        set_plan = build_style_performance_arc_set_plan_report(
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
        raw_entries.append(
            _readiness_entry_from_set_plan(
                arc=set_plan.arc,
                plan=set_plan.plan,
            )
        )
    sorted_entries = tuple(sorted(raw_entries, key=_readiness_sort_key))
    entries = tuple(
        _ranked_readiness_entry(position=index + 1, entry=entry)
        for index, entry in enumerate(sorted_entries)
    )
    return StylePerformanceArcReadinessReport(
        scope=entries[0].plan.scope,
        arc_count=len(entries),
        ready_arc_count=_readiness_count(entries, "ready"),
        partial_arc_count=_readiness_count(entries, "partial"),
        blocked_arc_count=_readiness_count(entries, "blocked"),
        total_segment_count=sum(entry.plan.segment_count for entry in entries),
        total_event_row_count=sum(entry.plan.total_event_row_count for entry in entries),
        total_mock_message_count=sum(entry.plan.total_mock_message_count for entry in entries),
        total_deferred_row_count=sum(entry.plan.total_deferred_row_count for entry in entries),
        entries=entries,
    )


def _readiness_entry_lines(entry: StylePerformanceArcReadinessEntry) -> list[str]:
    plan = entry.plan
    arc = entry.arc
    return [
        f"- {entry.position}. {arc.key} | {arc.name} | {entry.readiness}",
        f"  Average selection score: {entry.average_selection_score}",
        (
            f"  Segments: {plan.segment_count} total / {plan.ready_segment_count} ready / "
            f"{plan.partial_segment_count} partial / {plan.blocked_segment_count} blocked"
        ),
        (
            f"  Rows: {plan.total_event_row_count} events / "
            f"{plan.total_mock_message_count} mock messages / "
            f"{plan.total_deferred_row_count} deferred"
        ),
        (
            f"  Defaults: {arc.default_total_minutes} min / "
            f"discovery {arc.default_discovery_start}->{arc.default_discovery_end}"
        ),
        f"  Style sequence: {_sequence(arc.style_keys)}",
        f"  Action: {entry.operator_action}",
    ]


def _limited_readiness_entries(
    report: StylePerformanceArcReadinessReport,
    *,
    entry_limit: int,
) -> tuple[StylePerformanceArcReadinessEntry, ...]:
    if entry_limit < 0:
        raise ValueError("entry_limit must be >= 0")
    if entry_limit == 0 or entry_limit >= len(report.entries):
        return report.entries
    return report.entries[:entry_limit]


def format_style_performance_arc_readiness_report(
    report: StylePerformanceArcReadinessReport,
    *,
    entry_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing reference arc readiness lines."""

    selected_entries = _limited_readiness_entries(report, entry_limit=entry_limit)
    lines = [
        f"Scope: {report.scope}",
        f"Arc count: {report.arc_count}",
        f"Ready arcs: {report.ready_arc_count}",
        f"Partial arcs: {report.partial_arc_count}",
        f"Blocked arcs: {report.blocked_arc_count}",
        f"Total segments: {report.total_segment_count}",
        f"Total event rows: {report.total_event_row_count}",
        f"Total mock messages: {report.total_mock_message_count}",
        f"Total deferred rows: {report.total_deferred_row_count}",
        "Arc readiness matrix:",
    ]
    if len(selected_entries) == len(report.entries):
        lines.append("- Showing all arcs")
    else:
        lines.append(f"- Showing first {entry_limit} of {len(report.entries)} arcs")
    for entry in selected_entries:
        lines.extend(_readiness_entry_lines(entry))
    lines.append(SAFETY_SECTION_HEADER)
    lines.append("- reference arc readiness matrix")
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return passive_report_lines(_READINESS_HEADER, lines)


def _readiness_totals_json(report: StylePerformanceArcReadinessReport) -> dict[str, object]:
    return {
        "arcs": report.arc_count,
        "ready": report.ready_arc_count,
        "partial": report.partial_arc_count,
        "blocked": report.blocked_arc_count,
        "segments": report.total_segment_count,
        "event_rows": report.total_event_row_count,
        "mock_messages": report.total_mock_message_count,
        "deferred_rows": report.total_deferred_row_count,
    }


def _readiness_entry_json(entry: StylePerformanceArcReadinessEntry) -> dict[str, object]:
    return {
        "position": entry.position,
        "arc": to_style_performance_arc_json(entry.arc),
        "readiness": entry.readiness,
        "average_selection_score": entry.average_selection_score,
        "operator_action": entry.operator_action,
        "performance_plan": to_dual_machine_style_performance_set_plan_json(entry.plan),
    }


def to_style_performance_arc_readiness_json(
    report: StylePerformanceArcReadinessReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready reference arc readiness metadata."""

    return {
        "scope": report.scope,
        "totals": _readiness_totals_json(report),
        "entries": [_readiness_entry_json(entry) for entry in report.entries],
        "safety": list(SAFETY_LINES),
    }
