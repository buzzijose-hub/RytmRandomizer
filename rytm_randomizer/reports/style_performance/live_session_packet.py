"""Passive live-session packet derived from a rehearsal manifest."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..dual_machine_style_performance_set_plan import DualMachineStylePerformanceSetPlan
from ..formatter import passive_report_lines
from ._constants import (
    _DEFAULT_EVENT_LIMIT,
    _LIVE_SESSION_PACKET_HEADER,
    LIVE_SESSION_PACKET_SAFETY_LINES,
)
from ._helpers import _live_session_packet_safety_lines
from .readiness import (
    StylePerformanceArcReadinessEntry,
    _readiness_entry_json,
)
from .rehearsal_manifest import (
    StylePerformanceArcRehearsalManifestReport,
    StylePerformanceArcRehearsalSegment,
    _rehearsal_event_preview_lines,
    build_style_performance_arc_rehearsal_manifest_report,
    to_style_performance_arc_rehearsal_manifest_json,
)


@dataclass(frozen=True)
class StylePerformanceArcLiveSessionSegment:
    """One operator-facing segment card for a live rehearsal session."""

    position: int
    style_key: str
    time_window: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    readiness: str
    listen_for: str
    go_no_go_cue: str
    reset_cue: str
    rytm_preview_summary: str
    analog_four_preview_summary: str
    event_row_count: int
    mock_message_count: int
    deferred_row_count: int


@dataclass(frozen=True)
class StylePerformanceArcLiveSessionPacketReport:
    """Passive live-session packet derived from a rehearsal manifest."""

    rehearsal_manifest: StylePerformanceArcRehearsalManifestReport
    launch_checklist: tuple[str, ...]
    suggested_commands: tuple[str, ...]
    segments: tuple[StylePerformanceArcLiveSessionSegment, ...]

    @property
    def selected_entry(self) -> StylePerformanceArcReadinessEntry:
        """Return the selected reference arc readiness entry."""

        return self.rehearsal_manifest.selected_entry

    @property
    def selected_set_plan(self) -> DualMachineStylePerformanceSetPlan:
        """Return the selected timed set plan."""

        return self.rehearsal_manifest.selected_set_plan

    @property
    def segment_count(self) -> int:
        """Return the selected set-plan segment count."""

        return self.rehearsal_manifest.segment_count

    @property
    def ready_segment_count(self) -> int:
        """Return ready segment count for the selected plan."""

        return self.rehearsal_manifest.ready_segment_count

    @property
    def partial_segment_count(self) -> int:
        """Return partial segment count for the selected plan."""

        return self.rehearsal_manifest.partial_segment_count

    @property
    def blocked_segment_count(self) -> int:
        """Return blocked segment count for the selected plan."""

        return self.rehearsal_manifest.blocked_segment_count


def _live_session_launch_checklist(
    manifest: StylePerformanceArcRehearsalManifestReport,
) -> tuple[str, ...]:
    plan = manifest.selected_set_plan
    return (
        *manifest.preflight_steps,
        "Keep this packet passive until the rehearsal notes are reviewed.",
        "Run each segment as its own audition before trusting the full arc live.",
        f"Use scope {plan.scope} so unchanged machines stay parked.",
        "Reset to a known-good kit before moving from rehearsal into performance.",
    )


def _live_session_machine_path_flags(scope: str) -> str:
    if scope == "analog-four-only":
        return "--analog-four <analog-four-syx-path> --scope analog-four-only"
    if scope == "rytm-only":
        return "--rytm <rytm-syx-path> --scope rytm-only"
    return "--rytm <rytm-syx-path> --analog-four <analog-four-syx-path> --scope dual"


def _live_session_plan_flags(plan: DualMachineStylePerformanceSetPlan) -> str:
    return (
        f"--rank {plan.selection_rank} --total-minutes {plan.total_minutes} "
        f"--discovery-start {plan.discovery_start} --discovery-end {plan.discovery_end}"
    )


def _live_session_suggested_commands(
    manifest: StylePerformanceArcRehearsalManifestReport,
) -> tuple[str, ...]:
    arc_key = manifest.selected_entry.arc.key
    plan = manifest.selected_set_plan
    base_args = (
        f"{arc_key} {_live_session_machine_path_flags(plan.scope)} "
        f"{_live_session_plan_flags(plan)}"
    )
    return (
        (
            "python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report "
            f"{base_args} --events --limit 8"
        ),
        (
            "python -m rytm_randomizer.cli style-performance-arc-rehearsal-manifest-report "
            f"{base_args} --events --limit 8"
        ),
        (
            "python -m rytm_randomizer.cli style-performance-arc-audition-packet-report "
            f"{base_args} --events --limit 8"
        ),
        (
            "python -m rytm_randomizer.cli style-performance-arc-readiness-report "
            f"{base_args} --limit 8"
        ),
        (
            "python -m rytm_randomizer.cli style-performance-arc-set-plan-report "
            f"{base_args} --events --limit 8"
        ),
    )


def _live_session_listen_for(segment: StylePerformanceArcRehearsalSegment) -> str:
    if segment.discovery_amount <= 35:
        return "Subtle variation while the loaded kit identity stays recognizable."
    if segment.discovery_amount >= 75:
        return "Surprise, edge, and whether the machine still supports the live set."
    return "Useful groove movement and tonal pressure without losing the segment role."


def _live_session_go_no_go_cue(segment: StylePerformanceArcRehearsalSegment) -> str:
    if segment.readiness == "ready":
        return "Auditionable: move forward if the segment supports the room."
    if segment.readiness == "partial":
        return "Rehearse carefully: continue only if the weak machine is not exposed."
    return "Planning-only: skip live use until better saved kit material exists."


def _live_session_reset_cue(segment: StylePerformanceArcRehearsalSegment) -> str:
    if segment.readiness == "blocked":
        return "Reset to the previous known-good kit before live use."
    if segment.discovery_amount >= 75:
        return "Reset after audition if the edge overwhelms the groove."
    return "Reset only if the segment pulls focus away from the live arc."


def _live_session_segment_from_rehearsal(
    segment: StylePerformanceArcRehearsalSegment,
) -> StylePerformanceArcLiveSessionSegment:
    return StylePerformanceArcLiveSessionSegment(
        position=segment.position,
        style_key=segment.style_key,
        time_window=segment.time_window,
        discovery_amount=segment.discovery_amount,
        discovery_band=segment.discovery_band,
        mutation_depth=segment.mutation_depth,
        readiness=segment.readiness,
        listen_for=_live_session_listen_for(segment),
        go_no_go_cue=_live_session_go_no_go_cue(segment),
        reset_cue=_live_session_reset_cue(segment),
        rytm_preview_summary=segment.rytm_preview_summary,
        analog_four_preview_summary=segment.analog_four_preview_summary,
        event_row_count=segment.event_row_count,
        mock_message_count=segment.mock_message_count,
        deferred_row_count=segment.deferred_row_count,
    )


def build_style_performance_arc_live_session_packet_report(
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
) -> StylePerformanceArcLiveSessionPacketReport:
    """Return a passive live-session packet for the selected reference arc."""

    manifest = build_style_performance_arc_rehearsal_manifest_report(
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
    return StylePerformanceArcLiveSessionPacketReport(
        rehearsal_manifest=manifest,
        launch_checklist=_live_session_launch_checklist(manifest),
        suggested_commands=_live_session_suggested_commands(manifest),
        segments=tuple(
            _live_session_segment_from_rehearsal(segment) for segment in manifest.segments
        ),
    )


def _live_session_segment_json(
    segment: StylePerformanceArcLiveSessionSegment,
) -> dict[str, object]:
    return {
        "position": segment.position,
        "style_key": segment.style_key,
        "time_window": segment.time_window,
        "discovery_amount": segment.discovery_amount,
        "discovery_band": segment.discovery_band,
        "mutation_depth": segment.mutation_depth,
        "readiness": segment.readiness,
        "listen_for": segment.listen_for,
        "go_no_go_cue": segment.go_no_go_cue,
        "reset_cue": segment.reset_cue,
        "rytm_preview": segment.rytm_preview_summary,
        "analog_four_preview": segment.analog_four_preview_summary,
        "event_row_count": segment.event_row_count,
        "mock_message_count": segment.mock_message_count,
        "deferred_row_count": segment.deferred_row_count,
    }


def format_style_performance_arc_live_session_packet_report(
    report: StylePerformanceArcLiveSessionPacketReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing live-session packet lines."""

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
        "Launch checklist:",
        *[f"- {step}" for step in report.launch_checklist],
        "Suggested passive commands:",
        *[f"- {command}" for command in report.suggested_commands],
        "Segment cards:",
    ]
    for segment in report.segments:
        lines.extend(
            [
                (
                    f"- {segment.position}. {segment.time_window} | {segment.style_key} "
                    f"| discovery {segment.discovery_amount} | {segment.discovery_band} "
                    f"| depth {segment.mutation_depth} | readiness {segment.readiness}"
                ),
                f"  Listen for: {segment.listen_for}",
                f"  Go/no-go cue: {segment.go_no_go_cue}",
                f"  Reset cue: {segment.reset_cue}",
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
    lines.extend(_live_session_packet_safety_lines())
    return passive_report_lines(_LIVE_SESSION_PACKET_HEADER, lines)


def to_style_performance_arc_live_session_packet_json(
    report: StylePerformanceArcLiveSessionPacketReport,
) -> dict[str, object]:
    """Return deterministic JSON data for a live rehearsal session packet."""

    plan = report.selected_set_plan
    return {
        "selected": _readiness_entry_json(report.selected_entry),
        "rehearsal_manifest": to_style_performance_arc_rehearsal_manifest_json(
            report.rehearsal_manifest
        ),
        "session_packet": {
            "scope": plan.scope,
            "total_minutes": plan.total_minutes,
            "selection_rank": plan.selection_rank,
            "discovery_start": plan.discovery_start,
            "discovery_end": plan.discovery_end,
            "launch_checklist": list(report.launch_checklist),
            "suggested_commands": list(report.suggested_commands),
            "totals": {
                "segments": report.segment_count,
                "ready": report.ready_segment_count,
                "partial": report.partial_segment_count,
                "blocked": report.blocked_segment_count,
                "event_rows": plan.total_event_row_count,
                "mock_messages": plan.total_mock_message_count,
                "deferred_rows": plan.total_deferred_row_count,
            },
            "segments": [_live_session_segment_json(segment) for segment in report.segments],
        },
        "safety": list(LIVE_SESSION_PACKET_SAFETY_LINES),
    }
