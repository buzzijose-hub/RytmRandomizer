"""Passive rehearsal manifest derived from the selected audition packet."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..dual_machine_style_performance_set_plan import (
    DualMachineStylePerformanceSetPlan,
    DualMachineStylePerformanceSetSegment,
    format_dual_machine_style_performance_set_plan_report,
)
from ..formatter import SAFETY_SECTION_HEADER, passive_report_lines
from ._constants import (
    _DEFAULT_EVENT_LIMIT,
    _REHEARSAL_MANIFEST_HEADER,
    REHEARSAL_MANIFEST_SAFETY_LINES,
)
from ._helpers import _rehearsal_manifest_safety_lines
from .audition_packet import (
    StylePerformanceArcAuditionPacketReport,
    build_style_performance_arc_audition_packet_report,
    to_style_performance_arc_audition_packet_json,
)
from .readiness import (
    StylePerformanceArcReadinessEntry,
    _readiness_entry_json,
)


@dataclass(frozen=True)
class StylePerformanceArcRehearsalSegment:
    """One operator-facing segment row for a selected reference arc rehearsal."""

    position: int
    style_key: str
    time_window: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    readiness: str
    selection_score: int
    operator_action: str
    rytm_preview_summary: str
    analog_four_preview_summary: str
    event_row_count: int
    mock_message_count: int
    deferred_row_count: int


@dataclass(frozen=True)
class StylePerformanceArcRehearsalManifestReport:
    """Passive rehearsal runbook derived from the selected audition packet."""

    audition_packet: StylePerformanceArcAuditionPacketReport
    preflight_steps: tuple[str, ...]
    segments: tuple[StylePerformanceArcRehearsalSegment, ...]

    @property
    def selected_entry(self) -> StylePerformanceArcReadinessEntry:
        """Return the selected reference arc readiness entry."""

        return self.audition_packet.selected_entry

    @property
    def selected_set_plan(self) -> DualMachineStylePerformanceSetPlan:
        """Return the timed set plan used by the rehearsal manifest."""

        return self.audition_packet.selected_set_plan

    @property
    def segment_count(self) -> int:
        """Return the selected set-plan segment count."""

        return self.selected_set_plan.segment_count

    @property
    def ready_segment_count(self) -> int:
        """Return ready segment count for the selected plan."""

        return self.selected_set_plan.ready_segment_count

    @property
    def partial_segment_count(self) -> int:
        """Return partial segment count for the selected plan."""

        return self.selected_set_plan.partial_segment_count

    @property
    def blocked_segment_count(self) -> int:
        """Return blocked segment count for the selected plan."""

        return self.selected_set_plan.blocked_segment_count


def _rytm_preview_summary(segment: DualMachineStylePerformanceSetSegment) -> str:
    preview = segment.preview_plan.rytm_preview
    if preview is None:
        return "unchanged by scope"
    return (
        f"slot {preview.slot} {preview.kit_name} "
        f"/ ready {preview.preview_ready} "
        f"/ mock rows {preview.mock_message_count}"
    )


def _analog_four_preview_summary(segment: DualMachineStylePerformanceSetSegment) -> str:
    preview = segment.preview_plan.analog_four_preview
    if preview is None:
        return "unchanged by scope"
    return (
        f"slot {preview.slot} {preview.kit_name} "
        f"/ ready {preview.preview_ready} "
        f"/ deferred rows {preview.deferred_row_count}"
    )


def _rehearsal_segment_from_set_segment(
    segment: DualMachineStylePerformanceSetSegment,
) -> StylePerformanceArcRehearsalSegment:
    return StylePerformanceArcRehearsalSegment(
        position=segment.position,
        style_key=segment.style_key,
        time_window=segment.time_window,
        discovery_amount=segment.discovery_amount,
        discovery_band=segment.discovery_band,
        mutation_depth=segment.mutation_depth,
        readiness=segment.selection_readiness,
        selection_score=segment.selection_score,
        operator_action=segment.operator_action,
        rytm_preview_summary=_rytm_preview_summary(segment),
        analog_four_preview_summary=_analog_four_preview_summary(segment),
        event_row_count=segment.event_row_count,
        mock_message_count=segment.mock_message_count,
        deferred_row_count=segment.deferred_row_count,
    )


def _rehearsal_preflight_steps(plan: DualMachineStylePerformanceSetPlan) -> tuple[str, ...]:
    steps = []
    if plan.scope in {"dual", "rytm-only"}:
        steps.append("Confirm the saved Rytm kit bank before rehearsal.")
    else:
        steps.append("Rytm is unchanged by this scope; leave its current kit alone.")
    if plan.scope in {"dual", "analog-four-only"}:
        steps.append("Confirm the saved Analog Four kit bank before rehearsal.")
    else:
        steps.append("Analog Four is unchanged by this scope; leave its current kit alone.")
    steps.extend(
        [
            "Keep this command passive; it is a rehearsal manifest, not an armed send.",
            "Audition one segment at a time before trusting the full arc live.",
        ]
    )
    return tuple(steps)


def build_style_performance_arc_rehearsal_manifest_report(
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
) -> StylePerformanceArcRehearsalManifestReport:
    """Return a passive rehearsal manifest for the selected reference arc."""

    audition_packet = build_style_performance_arc_audition_packet_report(
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
    plan = audition_packet.selected_set_plan
    return StylePerformanceArcRehearsalManifestReport(
        audition_packet=audition_packet,
        preflight_steps=_rehearsal_preflight_steps(plan),
        segments=tuple(_rehearsal_segment_from_set_segment(segment) for segment in plan.segments),
    )


def _rehearsal_event_preview_lines(
    plan: DualMachineStylePerformanceSetPlan,
    *,
    event_limit: int,
) -> list[str]:
    set_plan_lines = format_dual_machine_style_performance_set_plan_report(
        plan,
        include_events=True,
        event_limit=event_limit,
    )
    selected_lines: list[str] = []
    capture = False
    for line in set_plan_lines:
        if line == SAFETY_SECTION_HEADER:
            capture = False
        elif line.startswith("Event preview for segment"):
            capture = True
        if capture:
            selected_lines.append(line)
    return selected_lines


def _rehearsal_segment_json(
    segment: StylePerformanceArcRehearsalSegment,
) -> dict[str, object]:
    return {
        "position": segment.position,
        "style_key": segment.style_key,
        "time_window": segment.time_window,
        "discovery_amount": segment.discovery_amount,
        "discovery_band": segment.discovery_band,
        "mutation_depth": segment.mutation_depth,
        "readiness": segment.readiness,
        "selection_score": segment.selection_score,
        "operator_action": segment.operator_action,
        "rytm_preview": segment.rytm_preview_summary,
        "analog_four_preview": segment.analog_four_preview_summary,
        "event_row_count": segment.event_row_count,
        "mock_message_count": segment.mock_message_count,
        "deferred_row_count": segment.deferred_row_count,
    }


def format_style_performance_arc_rehearsal_manifest_report(
    report: StylePerformanceArcRehearsalManifestReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing rehearsal manifest lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    selected = report.selected_entry
    plan = report.selected_set_plan
    lines = [
        "Summary:",
        f"- Scope: {plan.scope}",
        f"- Total duration minutes: {plan.total_minutes}",
        f"- Segment count: {report.segment_count}",
        (
            "- Segment readiness: "
            f"{report.ready_segment_count} ready, "
            f"{report.partial_segment_count} partial, "
            f"{report.blocked_segment_count} blocked"
        ),
        "Selected arc:",
        f"- Position: {selected.position}",
        f"- Key: {selected.arc.key}",
        f"- Name: {selected.arc.name}",
        f"- Readiness: {selected.readiness}",
        f"- Operator action: {selected.operator_action}",
        "Preflight checklist:",
        *[f"- {step}" for step in report.preflight_steps],
        "Segment runbook:",
    ]
    for segment in report.segments:
        lines.extend(
            [
                (
                    f"- {segment.position}. {segment.time_window} | {segment.style_key} "
                    f"| discovery {segment.discovery_amount} | {segment.discovery_band} "
                    f"| depth {segment.mutation_depth} | readiness {segment.readiness} "
                    f"| score {segment.selection_score}"
                ),
                f"  Action: {segment.operator_action}",
                f"  Rytm preview: {segment.rytm_preview_summary}",
                f"  Analog Four preview: {segment.analog_four_preview_summary}",
                (
                    f"  Counts: events {segment.event_row_count}, "
                    f"mock messages {segment.mock_message_count}, "
                    f"deferred {segment.deferred_row_count}"
                ),
            ]
        )
    if include_events:
        lines.append("Event previews:")
        lines.extend(
            _rehearsal_event_preview_lines(
                plan,
                event_limit=event_limit,
            )
        )
    lines.extend(_rehearsal_manifest_safety_lines())
    return passive_report_lines(_REHEARSAL_MANIFEST_HEADER, lines)


def to_style_performance_arc_rehearsal_manifest_json(
    report: StylePerformanceArcRehearsalManifestReport,
) -> dict[str, object]:
    """Return deterministic JSON data for a reference arc rehearsal manifest."""

    plan = report.selected_set_plan
    return {
        "selected": _readiness_entry_json(report.selected_entry),
        "audition_packet": to_style_performance_arc_audition_packet_json(report.audition_packet),
        "manifest": {
            "scope": plan.scope,
            "total_minutes": plan.total_minutes,
            "selection_rank": plan.selection_rank,
            "discovery_start": plan.discovery_start,
            "discovery_end": plan.discovery_end,
            "preflight": list(report.preflight_steps),
            "totals": {
                "segments": report.segment_count,
                "ready": report.ready_segment_count,
                "partial": report.partial_segment_count,
                "blocked": report.blocked_segment_count,
                "event_rows": plan.total_event_row_count,
                "mock_messages": plan.total_mock_message_count,
                "deferred_rows": plan.total_deferred_row_count,
            },
            "segments": [_rehearsal_segment_json(segment) for segment in report.segments],
        },
        "safety": list(REHEARSAL_MANIFEST_SAFETY_LINES),
    }
