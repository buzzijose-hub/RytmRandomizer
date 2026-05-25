"""Passive best-arc audition packet derived from a readiness matrix."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..dual_machine_style_performance_set_plan import DualMachineStylePerformanceSetPlan
from ..formatter import passive_report_lines
from ._constants import (
    _AUDITION_PACKET_HEADER,
    _DEFAULT_EVENT_LIMIT,
    AUDITION_PACKET_SAFETY_LINES,
)
from ._helpers import _audition_packet_safety_lines
from .catalog import (
    StylePerformanceArcSetPlanReport,
    format_style_performance_arc_set_plan_report,
    to_style_performance_arc_set_plan_json,
)
from .readiness import (
    StylePerformanceArcReadinessEntry,
    StylePerformanceArcReadinessReport,
    _readiness_entry_json,
    to_style_performance_arc_readiness_json,
)


@dataclass(frozen=True)
class StylePerformanceArcAuditionPacketReport:
    """Passive best-arc audition packet derived from a readiness matrix."""

    readiness_report: StylePerformanceArcReadinessReport
    selected_entry: StylePerformanceArcReadinessEntry

    @property
    def selected_set_plan(self) -> DualMachineStylePerformanceSetPlan:
        """Return the selected timed set plan for operator preview."""

        return self.selected_entry.plan


def build_style_performance_arc_audition_packet_report(
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
) -> StylePerformanceArcAuditionPacketReport:
    """Return the highest-ranked passive reference arc audition packet."""

    # Late-binding lookup via the public facade so tests that monkeypatch
    # ``rytm_randomizer.reports.style_performance_arcs.build_style_performance_arc_readiness_report``
    # still substitute the call site below. This preserves the test
    # contract from the pre-split monolith where audition packet and
    # readiness lived in the same module.
    from .. import style_performance_arcs as _facade

    readiness_report = _facade.build_style_performance_arc_readiness_report(
        arc_keys,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        scope=scope,
        selection_rank=selection_rank,
        total_minutes=total_minutes,
        segment_minutes=segment_minutes,
        discovery_start=discovery_start,
        discovery_end=discovery_end,
    )
    if not readiness_report.entries:
        raise ValueError("audition packet requires at least one readiness entry")
    return StylePerformanceArcAuditionPacketReport(
        readiness_report=readiness_report,
        selected_entry=readiness_report.entries[0],
    )


def _selected_set_plan_report(
    report: StylePerformanceArcAuditionPacketReport,
) -> StylePerformanceArcSetPlanReport:
    return StylePerformanceArcSetPlanReport(
        arc=report.selected_entry.arc,
        plan=report.selected_entry.plan,
    )


def format_style_performance_arc_audition_packet_report(
    report: StylePerformanceArcAuditionPacketReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing best-arc audition packet lines."""

    selected = report.selected_entry
    readiness = report.readiness_report
    set_plan_lines = format_style_performance_arc_set_plan_report(
        _selected_set_plan_report(report),
        include_events=include_events,
        event_limit=event_limit,
    )
    lines = [
        "Summary:",
        f"- Scope: {readiness.scope}",
        f"- Evaluated arcs: {readiness.arc_count}",
        (
            "- Readiness totals: "
            f"{readiness.ready_arc_count} ready, "
            f"{readiness.partial_arc_count} partial, "
            f"{readiness.blocked_arc_count} blocked"
        ),
        "Selected arc:",
        f"- Position: {selected.position}",
        f"- Key: {selected.arc.key}",
        f"- Name: {selected.arc.name}",
        f"- Readiness: {selected.readiness}",
        f"- Average selection score: {selected.average_selection_score}",
        f"- Operator action: {selected.operator_action}",
        "Readiness matrix:",
        *[
            (
                f"- #{entry.position}: {entry.arc.key} | {entry.readiness} | "
                f"score {entry.average_selection_score}"
            )
            for entry in readiness.entries
        ],
        "Selected set plan:",
        *[f"  {line}" for line in set_plan_lines],
        *_audition_packet_safety_lines(),
    ]
    return passive_report_lines(_AUDITION_PACKET_HEADER, lines)


def to_style_performance_arc_audition_packet_json(
    report: StylePerformanceArcAuditionPacketReport,
) -> dict[str, object]:
    """Return deterministic JSON data for the selected reference arc packet."""

    return {
        "selected": _readiness_entry_json(report.selected_entry),
        "readiness_matrix": to_style_performance_arc_readiness_json(report.readiness_report),
        "selected_set_plan": to_style_performance_arc_set_plan_json(
            _selected_set_plan_report(report)
        ),
        "safety": list(AUDITION_PACKET_SAFETY_LINES),
    }
