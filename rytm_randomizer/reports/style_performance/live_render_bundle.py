"""Passive segment-level mock-render bundle for live rehearsal."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..dual_machine_style_performance_set_plan import (
    DualMachineStylePerformanceSetPlan,
    DualMachineStylePerformanceSetSegment,
)
from ..dual_machine_style_selection_mock_preview import (
    format_dual_machine_style_selection_mock_preview_event_rows,
    to_dual_machine_style_selection_mock_preview_json,
)
from ..formatter import passive_report_lines
from ._constants import (
    _DEFAULT_EVENT_LIMIT,
    _LIVE_RENDER_BUNDLE_HEADER,
    LIVE_RENDER_BUNDLE_SAFETY_LINES,
)
from ._helpers import _live_render_bundle_safety_lines
from .live_session_packet import (
    StylePerformanceArcLiveSessionPacketReport,
    StylePerformanceArcLiveSessionSegment,
    _live_session_machine_path_flags,
    _live_session_plan_flags,
    to_style_performance_arc_live_session_packet_json,
)
from .readiness import (
    StylePerformanceArcReadinessEntry,
    _readiness_entry_json,
)


@dataclass(frozen=True)
class StylePerformanceArcLiveRenderSegment:
    """One segment-level passive mock-render bundle for live rehearsal."""

    live_segment: StylePerformanceArcLiveSessionSegment
    set_plan_segment: DualMachineStylePerformanceSetSegment
    event_preview_rows: tuple[str, ...]
    deferred_rows: tuple[str, ...]

    @property
    def position(self) -> int:
        """Return the segment position in the selected performance arc."""

        return self.live_segment.position

    @property
    def style_key(self) -> str:
        """Return the segment style key."""

        return self.live_segment.style_key

    @property
    def time_window(self) -> str:
        """Return the segment time window."""

        return self.live_segment.time_window

    @property
    def discovery_amount(self) -> int:
        """Return the segment discovery amount."""

        return self.live_segment.discovery_amount

    @property
    def discovery_band(self) -> str:
        """Return the segment discovery band."""

        return self.live_segment.discovery_band

    @property
    def mutation_depth(self) -> str:
        """Return the segment mutation depth."""

        return self.live_segment.mutation_depth

    @property
    def readiness(self) -> str:
        """Return the segment readiness."""

        return self.live_segment.readiness

    @property
    def listen_for(self) -> str:
        """Return the segment listening cue."""

        return self.live_segment.listen_for

    @property
    def go_no_go_cue(self) -> str:
        """Return the segment go/no-go cue."""

        return self.live_segment.go_no_go_cue

    @property
    def reset_cue(self) -> str:
        """Return the segment reset cue."""

        return self.live_segment.reset_cue

    @property
    def rytm_preview_summary(self) -> str:
        """Return the Rytm preview summary."""

        return self.live_segment.rytm_preview_summary

    @property
    def analog_four_preview_summary(self) -> str:
        """Return the Analog Four preview summary."""

        return self.live_segment.analog_four_preview_summary

    @property
    def event_row_count(self) -> int:
        """Return the segment event row count."""

        return self.live_segment.event_row_count

    @property
    def mock_message_count(self) -> int:
        """Return the segment mock message count."""

        return self.live_segment.mock_message_count

    @property
    def deferred_row_count(self) -> int:
        """Return the segment deferred row count."""

        return self.live_segment.deferred_row_count

    @property
    def preview_json(self) -> dict[str, object]:
        """Return the full existing dual-machine mock preview JSON."""

        return to_dual_machine_style_selection_mock_preview_json(self.set_plan_segment.preview_plan)


@dataclass(frozen=True)
class StylePerformanceArcLiveRenderBundleReport:
    """Passive live render bundle derived from a live-session packet."""

    live_session_packet: StylePerformanceArcLiveSessionPacketReport
    suggested_commands: tuple[str, ...]
    segments: tuple[StylePerformanceArcLiveRenderSegment, ...]

    @property
    def selected_entry(self) -> StylePerformanceArcReadinessEntry:
        """Return the selected reference arc readiness entry."""

        return self.live_session_packet.selected_entry

    @property
    def selected_set_plan(self) -> DualMachineStylePerformanceSetPlan:
        """Return the selected timed set plan."""

        return self.live_session_packet.selected_set_plan

    @property
    def segment_count(self) -> int:
        """Return the selected set-plan segment count."""

        return self.live_session_packet.segment_count

    @property
    def ready_segment_count(self) -> int:
        """Return ready segment count for the selected plan."""

        return self.live_session_packet.ready_segment_count

    @property
    def partial_segment_count(self) -> int:
        """Return partial segment count for the selected plan."""

        return self.live_session_packet.partial_segment_count

    @property
    def blocked_segment_count(self) -> int:
        """Return blocked segment count for the selected plan."""

        return self.live_session_packet.blocked_segment_count

    @property
    def total_event_row_count(self) -> int:
        """Return total segment event rows."""

        return self.selected_set_plan.total_event_row_count

    @property
    def total_mock_message_count(self) -> int:
        """Return total segment mock messages."""

        return self.selected_set_plan.total_mock_message_count

    @property
    def total_deferred_row_count(self) -> int:
        """Return total deferred rows."""

        return self.selected_set_plan.total_deferred_row_count


def _live_render_bundle_suggested_commands(
    packet: StylePerformanceArcLiveSessionPacketReport,
) -> tuple[str, ...]:
    arc_key = packet.selected_entry.arc.key
    plan = packet.selected_set_plan
    base_args = (
        f"{arc_key} {_live_session_machine_path_flags(plan.scope)} "
        f"{_live_session_plan_flags(plan)}"
    )
    return (
        (
            "python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report "
            f"{base_args} --events --limit 8"
        ),
        *packet.suggested_commands,
    )


def _live_render_bundle_event_rows(
    segment: DualMachineStylePerformanceSetSegment,
) -> tuple[str, ...]:
    return format_dual_machine_style_selection_mock_preview_event_rows(segment.preview_plan)


def _live_render_bundle_deferred_rows(
    segment: DualMachineStylePerformanceSetSegment,
) -> tuple[str, ...]:
    analog_four_preview = segment.preview_plan.analog_four_preview
    if analog_four_preview is None or not analog_four_preview.deferred_rows:
        return ("- none",)
    return tuple(
        (
            f"- Analog Four Track {row.track} | {row.role_key} | {row.zone} | "
            f"{row.reason} | bias {row.target_bias} | depth {row.mutation_depth} | "
            f"direction {row.target_direction}"
        )
        for row in analog_four_preview.deferred_rows
    )


def _live_render_segment(
    *,
    live_segment: StylePerformanceArcLiveSessionSegment,
    set_plan_segment: DualMachineStylePerformanceSetSegment,
) -> StylePerformanceArcLiveRenderSegment:
    return StylePerformanceArcLiveRenderSegment(
        live_segment=live_segment,
        set_plan_segment=set_plan_segment,
        event_preview_rows=_live_render_bundle_event_rows(set_plan_segment),
        deferred_rows=_live_render_bundle_deferred_rows(set_plan_segment),
    )


def build_style_performance_arc_live_render_bundle_report(
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
) -> StylePerformanceArcLiveRenderBundleReport:
    """Return a passive segment-level mock-render bundle for live rehearsal."""

    # Late-binding lookup via the public facade so tests that monkeypatch
    # ``rytm_randomizer.reports.style_performance_arcs.build_style_performance_arc_live_session_packet_report``
    # still substitute the call site below. This preserves the test
    # contract from the pre-split monolith.
    from .. import style_performance_arcs as _facade

    packet = _facade.build_style_performance_arc_live_session_packet_report(
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
    live_segments = packet.segments
    set_plan_segments = packet.selected_set_plan.segments
    if len(live_segments) != len(set_plan_segments):
        raise ValueError(
            "live render bundle requires matching live-session and set-plan segment counts"
        )
    segments = tuple(
        _live_render_segment(
            live_segment=live_segment,
            set_plan_segment=set_plan_segment,
        )
        for live_segment, set_plan_segment in zip(
            live_segments,
            set_plan_segments,
            strict=True,
        )
    )
    return StylePerformanceArcLiveRenderBundleReport(
        live_session_packet=packet,
        suggested_commands=_live_render_bundle_suggested_commands(packet),
        segments=segments,
    )


def _limited_event_rows(
    rows: Sequence[str],
    *,
    event_limit: int,
) -> tuple[str, ...]:
    if event_limit == 0 or event_limit >= len(rows):
        return tuple(rows)
    return tuple(rows[:event_limit])


def _live_render_segment_lines(
    segment: StylePerformanceArcLiveRenderSegment,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    lines = [
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
        "  Deferred rows:",
        *[f"  {row}" for row in segment.deferred_rows],
    ]
    if include_events:
        lines.append(f"  Mock render preview: Event preview for segment {segment.position}")
        if not segment.event_preview_rows:
            lines.append("  - No mock rows available because the selected preview is not ready.")
        else:
            selected_rows = _limited_event_rows(
                segment.event_preview_rows,
                event_limit=event_limit,
            )
            if len(selected_rows) == len(segment.event_preview_rows):
                lines.append("  - Showing all events")
            else:
                lines.append(
                    f"  - Showing first {event_limit} of {len(segment.event_preview_rows)} events"
                )
            lines.extend(f"  {row}" for row in selected_rows)
    return lines


def format_style_performance_arc_live_render_bundle_report(
    report: StylePerformanceArcLiveRenderBundleReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic live render bundle lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    selected = report.selected_entry
    plan = report.selected_set_plan
    lines = [
        "Render bundle summary:",
        f"- Scope: {plan.scope}",
        f"- Total duration minutes: {plan.total_minutes}",
        f"- Selection rank: {plan.selection_rank}",
        f"- Segment count: {report.segment_count}",
        (
            "- Segment readiness: "
            f"{report.ready_segment_count} ready, "
            f"{report.partial_segment_count} partial, "
            f"{report.blocked_segment_count} blocked"
        ),
        f"- Total event rows: {report.total_event_row_count}",
        f"- Total mock messages: {report.total_mock_message_count}",
        f"- Total deferred rows: {report.total_deferred_row_count}",
        "Selected arc:",
        f"- Position: {selected.position}",
        f"- Key: {selected.arc.key}",
        f"- Name: {selected.arc.name}",
        f"- Readiness: {selected.readiness}",
        f"- Operator action: {selected.operator_action}",
        "Replayable passive commands:",
        *[f"- {command}" for command in report.suggested_commands],
        "Segment render bundles:",
    ]
    for segment in report.segments:
        lines.extend(
            _live_render_segment_lines(
                segment,
                include_events=include_events,
                event_limit=event_limit,
            )
        )
    lines.extend(_live_render_bundle_safety_lines())
    return passive_report_lines(_LIVE_RENDER_BUNDLE_HEADER, lines)


def _live_render_segment_json(
    segment: StylePerformanceArcLiveRenderSegment,
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
        "event_preview_rows": list(segment.event_preview_rows),
        "deferred_rows": list(segment.deferred_rows),
        "preview": segment.preview_json,
    }


def to_style_performance_arc_live_render_bundle_json(
    report: StylePerformanceArcLiveRenderBundleReport,
) -> dict[str, object]:
    """Return deterministic JSON data for a live render bundle."""

    plan = report.selected_set_plan
    return {
        "selected": _readiness_entry_json(report.selected_entry),
        "live_session_packet": to_style_performance_arc_live_session_packet_json(
            report.live_session_packet
        ),
        "render_bundle": {
            "scope": plan.scope,
            "total_minutes": plan.total_minutes,
            "selection_rank": plan.selection_rank,
            "discovery_start": plan.discovery_start,
            "discovery_end": plan.discovery_end,
            "suggested_commands": list(report.suggested_commands),
            "totals": {
                "segments": report.segment_count,
                "ready": report.ready_segment_count,
                "partial": report.partial_segment_count,
                "blocked": report.blocked_segment_count,
                "event_rows": report.total_event_row_count,
                "mock_messages": report.total_mock_message_count,
                "deferred_rows": report.total_deferred_row_count,
            },
            "segments": [_live_render_segment_json(segment) for segment in report.segments],
        },
        "safety": list(LIVE_RENDER_BUNDLE_SAFETY_LINES),
    }
