"""Passive live-performance cue sheet (with stage card / stage packet)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..dual_machine_style_performance_set_plan import DualMachineStylePerformanceSetPlan
from ..formatter import passive_report_lines
from ._constants import (
    _DEFAULT_EVENT_LIMIT,
    _LIVE_CUE_SHEET_HEADER,
    LIVE_CUE_SHEET_SAFETY_LINES,
)
from ._helpers import (
    _live_cue_sheet_safety_lines,
    _number_sequence,
    _readiness_from_counts,
)
from .live_render_bundle import (
    StylePerformanceArcLiveRenderBundleReport,
    StylePerformanceArcLiveRenderSegment,
    _limited_event_rows,
    build_style_performance_arc_live_render_bundle_report,
    to_style_performance_arc_live_render_bundle_json,
)
from .live_session_packet import (
    _live_session_machine_path_flags,
    _live_session_plan_flags,
)
from .readiness import (
    StylePerformanceArcReadinessEntry,
    _readiness_entry_json,
)


@dataclass(frozen=True)
class StylePerformanceArcLiveCue:
    """One operator-facing live cue derived from a render segment."""

    render_segment: StylePerformanceArcLiveRenderSegment
    machine_focus: str
    operator_move: str
    risk_level: str
    recovery_action: str

    @property
    def position(self) -> int:
        """Return the segment position."""

        return self.render_segment.position

    @property
    def style_key(self) -> str:
        """Return the segment style key."""

        return self.render_segment.style_key

    @property
    def time_window(self) -> str:
        """Return the segment time window."""

        return self.render_segment.time_window

    @property
    def readiness(self) -> str:
        """Return the segment readiness."""

        return self.render_segment.readiness

    @property
    def render_row_summary(self) -> str:
        """Return a compact render/deferred row summary."""

        return (
            f"{self.render_segment.event_row_count} event row(s), "
            f"{self.render_segment.deferred_row_count} deferred row(s)"
        )


@dataclass(frozen=True)
class StylePerformanceArcStageCard:
    """Compact show-day handoff card derived from one live cue."""

    cue_number: int
    time_window: str
    style_key: str
    machine_focus: str
    readiness: str
    risk_level: str
    operator_move: str
    listen_for: str
    recovery_action: str
    planned_rytm_pads: tuple[int, ...]
    planned_analog_four_tracks: tuple[int, ...]
    event_row_count: int
    mock_message_count: int
    deferred_row_count: int
    render_row_summary: str


@dataclass(frozen=True)
class StylePerformanceArcStagePacket:
    """Passive stage handoff packet for the selected live cue sheet."""

    selected_arc_key: str
    selected_arc_name: str
    scope: str
    readiness: str
    total_minutes: int
    cue_count: int
    total_event_row_count: int
    total_mock_message_count: int
    total_deferred_row_count: int
    planned_rytm_pads: tuple[int, ...]
    planned_analog_four_tracks: tuple[int, ...]
    operator_action: str
    stage_cards: tuple[StylePerformanceArcStageCard, ...]


@dataclass(frozen=True)
class StylePerformanceArcLiveCueSheetReport:
    """Passive live-performance cue sheet derived from a render bundle."""

    live_render_bundle: StylePerformanceArcLiveRenderBundleReport
    suggested_commands: tuple[str, ...]
    preflight_cues: tuple[str, ...]
    recovery_cues: tuple[str, ...]
    stage_packet: StylePerformanceArcStagePacket
    cues: tuple[StylePerformanceArcLiveCue, ...]

    @property
    def selected_entry(self) -> StylePerformanceArcReadinessEntry:
        """Return the selected reference arc readiness entry."""

        return self.live_render_bundle.selected_entry

    @property
    def selected_set_plan(self) -> DualMachineStylePerformanceSetPlan:
        """Return the selected timed set plan."""

        return self.live_render_bundle.selected_set_plan

    @property
    def segment_count(self) -> int:
        """Return the selected segment count."""

        return self.live_render_bundle.segment_count

    @property
    def cue_count(self) -> int:
        """Return the number of generated cue rows."""

        return len(self.cues)

    @property
    def ready_segment_count(self) -> int:
        """Return ready segment count."""

        return self.live_render_bundle.ready_segment_count

    @property
    def partial_segment_count(self) -> int:
        """Return partial segment count."""

        return self.live_render_bundle.partial_segment_count

    @property
    def blocked_segment_count(self) -> int:
        """Return blocked segment count."""

        return self.live_render_bundle.blocked_segment_count

    @property
    def total_event_row_count(self) -> int:
        """Return total event rows."""

        return self.live_render_bundle.total_event_row_count

    @property
    def total_mock_message_count(self) -> int:
        """Return total mock messages."""

        return self.live_render_bundle.total_mock_message_count

    @property
    def total_deferred_row_count(self) -> int:
        """Return total deferred rows."""

        return self.live_render_bundle.total_deferred_row_count


def _live_cue_sheet_suggested_commands(
    bundle: StylePerformanceArcLiveRenderBundleReport,
) -> tuple[str, ...]:
    arc_key = bundle.selected_entry.arc.key
    plan = bundle.selected_set_plan
    base_args = (
        f"{arc_key} {_live_session_machine_path_flags(plan.scope)} "
        f"{_live_session_plan_flags(plan)}"
    )
    return (
        (
            "python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report "
            f"{base_args} --events --limit 8"
        ),
        *bundle.suggested_commands,
    )


def _live_cue_machine_focus(
    segment: StylePerformanceArcLiveRenderSegment,
    *,
    scope: str,
) -> str:
    if scope == "analog-four-only":
        return "Analog Four only"
    if scope == "rytm-only":
        return "Rytm only"
    if segment.rytm_preview_summary == "unchanged by scope":
        return "Analog Four only"
    if segment.analog_four_preview_summary == "unchanged by scope":
        return "Rytm only"
    return "Rytm + Analog Four"


def _live_cue_operator_move(
    segment: StylePerformanceArcLiveRenderSegment,
    *,
    machine_focus: str,
) -> str:
    if machine_focus == "Analog Four only":
        return (
            "Leave Rytm unchanged; cue Analog Four movement while listening for "
            f"{segment.listen_for}."
        )
    if machine_focus == "Rytm only":
        return (
            "Cue Rytm movement and leave Analog Four unchanged; listen for "
            f"{segment.listen_for}."
        )
    return "Cue both machines from the passive render rows; listen for " f"{segment.listen_for}."


def _live_cue_risk_level(segment: StylePerformanceArcLiveRenderSegment) -> str:
    if segment.readiness == "blocked" or segment.event_row_count == 0:
        return "red"
    if segment.readiness == "partial" or segment.deferred_row_count:
        return "amber"
    return "green"


def _live_cue_recovery_action(
    segment: StylePerformanceArcLiveRenderSegment,
    *,
    risk_level: str,
) -> str:
    if risk_level == "red":
        return f"Skip this cue if uncertain, then recover with: {segment.reset_cue}"
    if risk_level == "amber":
        return f"Keep one hand on recovery and use: {segment.reset_cue}"
    return f"If the room drifts, recover with: {segment.reset_cue}"


def _live_cue_from_segment(
    segment: StylePerformanceArcLiveRenderSegment,
    *,
    scope: str,
) -> StylePerformanceArcLiveCue:
    machine_focus = _live_cue_machine_focus(segment, scope=scope)
    risk_level = _live_cue_risk_level(segment)
    return StylePerformanceArcLiveCue(
        render_segment=segment,
        machine_focus=machine_focus,
        operator_move=_live_cue_operator_move(
            segment,
            machine_focus=machine_focus,
        ),
        risk_level=risk_level,
        recovery_action=_live_cue_recovery_action(
            segment,
            risk_level=risk_level,
        ),
    )


def _live_cue_sheet_preflight_cues(
    bundle: StylePerformanceArcLiveRenderBundleReport,
) -> tuple[str, ...]:
    plan = bundle.selected_set_plan
    return (
        f"Load saved-kit source scope: {plan.scope}.",
        f"Confirm {bundle.segment_count} planned segment cue(s) before launch.",
        f"Keep the live render bundle nearby for mock row detail: {bundle.selected_entry.arc.key}.",
        *bundle.live_session_packet.launch_checklist,
    )


def _live_cue_sheet_recovery_cues(
    cues: Sequence[StylePerformanceArcLiveCue],
) -> tuple[str, ...]:
    recovery_rows: list[str] = []
    seen: set[str] = set()
    for cue in cues:
        if cue.recovery_action in seen:
            continue
        seen.add(cue.recovery_action)
        recovery_rows.append(cue.recovery_action)
    return tuple(recovery_rows)


def _cue_sheet_readiness(cue_sheet: StylePerformanceArcLiveCueSheetReport) -> str:
    return _readiness_from_counts(
        blocked_segment_count=cue_sheet.blocked_segment_count,
        partial_segment_count=cue_sheet.partial_segment_count,
        total_deferred_row_count=cue_sheet.total_deferred_row_count,
        total_event_row_count=cue_sheet.total_event_row_count,
    )


def _stage_card_planned_rytm_pads(
    segment: StylePerformanceArcLiveRenderSegment,
) -> tuple[int, ...]:
    preview = segment.set_plan_segment.preview_plan.rytm_preview
    return tuple(sorted(getattr(preview, "planned_pads", ())))


def _stage_card_planned_analog_four_tracks(
    segment: StylePerformanceArcLiveRenderSegment,
) -> tuple[int, ...]:
    preview = segment.set_plan_segment.preview_plan.analog_four_preview
    tracks = set(getattr(preview, "planned_tracks", ()))
    tracks.update(row.track for row in getattr(preview, "deferred_rows", ()))
    return tuple(sorted(tracks))


def _stage_card_from_live_cue(
    cue: StylePerformanceArcLiveCue,
) -> StylePerformanceArcStageCard:
    segment = cue.render_segment
    return StylePerformanceArcStageCard(
        cue_number=cue.position,
        time_window=cue.time_window,
        style_key=cue.style_key,
        machine_focus=cue.machine_focus,
        readiness=cue.readiness,
        risk_level=cue.risk_level,
        operator_move=cue.operator_move,
        listen_for=segment.listen_for,
        recovery_action=cue.recovery_action,
        planned_rytm_pads=_stage_card_planned_rytm_pads(segment),
        planned_analog_four_tracks=_stage_card_planned_analog_four_tracks(segment),
        event_row_count=segment.event_row_count,
        mock_message_count=segment.mock_message_count,
        deferred_row_count=segment.deferred_row_count,
        render_row_summary=cue.render_row_summary,
    )


def _stage_packet_operator_action(cue_count: int) -> str:
    return (
        "Keep this passive stage packet beside the machines; rehearse "
        f"{cue_count} cue(s) before arming hardware. No MIDI is sent."
    )


def _stage_packet_from_live_cues(
    bundle: StylePerformanceArcLiveRenderBundleReport,
    cues: Sequence[StylePerformanceArcLiveCue],
) -> StylePerformanceArcStagePacket:
    stage_cards = tuple(_stage_card_from_live_cue(cue) for cue in cues)
    planned_rytm_pads = sorted({pad for card in stage_cards for pad in card.planned_rytm_pads})
    planned_analog_four_tracks = sorted(
        {track for card in stage_cards for track in card.planned_analog_four_tracks}
    )
    return StylePerformanceArcStagePacket(
        selected_arc_key=bundle.selected_entry.arc.key,
        selected_arc_name=bundle.selected_entry.arc.name,
        scope=bundle.selected_set_plan.scope,
        readiness=_readiness_from_counts(
            blocked_segment_count=bundle.blocked_segment_count,
            partial_segment_count=bundle.partial_segment_count,
            total_deferred_row_count=bundle.total_deferred_row_count,
            total_event_row_count=bundle.total_event_row_count,
        ),
        total_minutes=bundle.selected_set_plan.total_minutes,
        cue_count=len(stage_cards),
        total_event_row_count=bundle.total_event_row_count,
        total_mock_message_count=bundle.total_mock_message_count,
        total_deferred_row_count=bundle.total_deferred_row_count,
        planned_rytm_pads=tuple(planned_rytm_pads),
        planned_analog_four_tracks=tuple(planned_analog_four_tracks),
        operator_action=_stage_packet_operator_action(len(stage_cards)),
        stage_cards=stage_cards,
    )


def build_style_performance_arc_live_cue_sheet_report(
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
) -> StylePerformanceArcLiveCueSheetReport:
    """Return an operator-facing passive live cue sheet."""

    bundle = build_style_performance_arc_live_render_bundle_report(
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
    cues = tuple(
        _live_cue_from_segment(segment, scope=bundle.selected_set_plan.scope)
        for segment in bundle.segments
    )
    stage_packet = _stage_packet_from_live_cues(bundle, cues)
    return StylePerformanceArcLiveCueSheetReport(
        live_render_bundle=bundle,
        suggested_commands=_live_cue_sheet_suggested_commands(bundle),
        preflight_cues=_live_cue_sheet_preflight_cues(bundle),
        recovery_cues=_live_cue_sheet_recovery_cues(cues),
        stage_packet=stage_packet,
        cues=cues,
    )


def _live_cue_lines(
    cue: StylePerformanceArcLiveCue,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    segment = cue.render_segment
    lines = [
        (
            f"- {cue.position}. {cue.time_window} | {cue.style_key} | "
            f"{cue.machine_focus} | readiness {cue.readiness}"
        ),
        f"  Risk: {cue.risk_level}",
        f"  Hands-on move: {cue.operator_move}",
        f"  Listen for: {segment.listen_for}",
        f"  Go/no-go: {segment.go_no_go_cue}",
        f"  Recovery: {cue.recovery_action}",
        f"  Rytm: {segment.rytm_preview_summary}",
        f"  Analog Four: {segment.analog_four_preview_summary}",
        f"  Render rows: {cue.render_row_summary}",
    ]
    if include_events:
        lines.append("  Mock render row preview:")
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


def _stage_card_lines(card: StylePerformanceArcStageCard) -> list[str]:
    return [
        (
            f"- Cue {card.cue_number}. {card.time_window} | {card.style_key} | "
            f"{card.machine_focus}"
        ),
        f"  Readiness: {card.readiness}",
        f"  Risk: {card.risk_level}",
        f"  Hands-on move: {card.operator_move}",
        f"  Listen for: {card.listen_for}",
        f"  Recovery: {card.recovery_action}",
        f"  Planned Rytm pads: {_number_sequence(card.planned_rytm_pads)}",
        f"  Planned Analog Four tracks: {_number_sequence(card.planned_analog_four_tracks)}",
        f"  Render rows: {card.render_row_summary}",
    ]


def _stage_packet_lines(
    packet: StylePerformanceArcStagePacket,
    *,
    header: str,
) -> list[str]:
    lines = [
        header,
        f"- Selected arc: {packet.selected_arc_key} / {packet.selected_arc_name}",
        f"- Scope: {packet.scope}",
        f"- Readiness: {packet.readiness}",
        f"- Total duration minutes: {packet.total_minutes}",
        f"- Cue count: {packet.cue_count}",
        f"- Total event rows: {packet.total_event_row_count}",
        f"- Total mock messages: {packet.total_mock_message_count}",
        f"- Total deferred rows: {packet.total_deferred_row_count}",
        f"- Planned Rytm pads: {_number_sequence(packet.planned_rytm_pads)}",
        f"- Planned Analog Four tracks: {_number_sequence(packet.planned_analog_four_tracks)}",
        f"- Operator action: {packet.operator_action}",
        "Stage cards:",
    ]
    for card in packet.stage_cards:
        lines.extend(_stage_card_lines(card))
    return lines


def format_style_performance_arc_live_cue_sheet_report(
    report: StylePerformanceArcLiveCueSheetReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic live cue-sheet lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    selected = report.selected_entry
    plan = report.selected_set_plan
    lines = [
        "Cue sheet summary:",
        f"- Scope: {plan.scope}",
        f"- Total duration minutes: {plan.total_minutes}",
        f"- Cue count: {report.cue_count}",
        (
            "- Segment readiness: "
            f"{report.ready_segment_count} ready, "
            f"{report.partial_segment_count} partial, "
            f"{report.blocked_segment_count} blocked"
        ),
        f"- Total event rows: {report.total_event_row_count}",
        f"- Total deferred rows: {report.total_deferred_row_count}",
        "Selected arc:",
        f"- Position: {selected.position}",
        f"- Key: {selected.arc.key}",
        f"- Name: {selected.arc.name}",
        "Replayable passive commands:",
        *[f"- {command}" for command in report.suggested_commands],
        "Preflight cues:",
        *[f"- {cue}" for cue in report.preflight_cues],
        *_stage_packet_lines(report.stage_packet, header="Stage packet:"),
        "Performance cues:",
    ]
    for cue in report.cues:
        lines.extend(
            _live_cue_lines(
                cue,
                include_events=include_events,
                event_limit=event_limit,
            )
        )
    lines.extend(["Recovery cues:", *[f"- {cue}" for cue in report.recovery_cues]])
    lines.extend(_live_cue_sheet_safety_lines())
    return passive_report_lines(_LIVE_CUE_SHEET_HEADER, lines)


def _live_cue_json(cue: StylePerformanceArcLiveCue) -> dict[str, object]:
    segment = cue.render_segment
    return {
        "position": cue.position,
        "time_window": cue.time_window,
        "style_key": cue.style_key,
        "readiness": cue.readiness,
        "machine_focus": cue.machine_focus,
        "operator_move": cue.operator_move,
        "risk_level": cue.risk_level,
        "recovery_action": cue.recovery_action,
        "listen_for": segment.listen_for,
        "go_no_go_cue": segment.go_no_go_cue,
        "reset_cue": segment.reset_cue,
        "rytm_preview": segment.rytm_preview_summary,
        "analog_four_preview": segment.analog_four_preview_summary,
        "event_row_count": segment.event_row_count,
        "mock_message_count": segment.mock_message_count,
        "deferred_row_count": segment.deferred_row_count,
        "render_row_summary": cue.render_row_summary,
    }


def _stage_card_json(card: StylePerformanceArcStageCard) -> dict[str, object]:
    return {
        "cue_number": card.cue_number,
        "time_window": card.time_window,
        "style_key": card.style_key,
        "machine_focus": card.machine_focus,
        "readiness": card.readiness,
        "risk_level": card.risk_level,
        "operator_move": card.operator_move,
        "listen_for": card.listen_for,
        "recovery_action": card.recovery_action,
        "planned_rytm_pads": list(card.planned_rytm_pads),
        "planned_analog_four_tracks": list(card.planned_analog_four_tracks),
        "event_row_count": card.event_row_count,
        "mock_message_count": card.mock_message_count,
        "deferred_row_count": card.deferred_row_count,
        "render_row_summary": card.render_row_summary,
    }


def _stage_packet_json(packet: StylePerformanceArcStagePacket) -> dict[str, object]:
    return {
        "selected_arc_key": packet.selected_arc_key,
        "selected_arc_name": packet.selected_arc_name,
        "scope": packet.scope,
        "readiness": packet.readiness,
        "total_minutes": packet.total_minutes,
        "cue_count": packet.cue_count,
        "total_event_row_count": packet.total_event_row_count,
        "total_mock_message_count": packet.total_mock_message_count,
        "total_deferred_row_count": packet.total_deferred_row_count,
        "planned_rytm_pads": list(packet.planned_rytm_pads),
        "planned_analog_four_tracks": list(packet.planned_analog_four_tracks),
        "operator_action": packet.operator_action,
        "stage_cards": [_stage_card_json(card) for card in packet.stage_cards],
    }


def to_style_performance_arc_live_cue_sheet_json(
    report: StylePerformanceArcLiveCueSheetReport,
) -> dict[str, object]:
    """Return deterministic JSON data for a live cue sheet."""

    plan = report.selected_set_plan
    return {
        "selected": _readiness_entry_json(report.selected_entry),
        "live_render_bundle": to_style_performance_arc_live_render_bundle_json(
            report.live_render_bundle
        ),
        "cue_sheet": {
            "scope": plan.scope,
            "total_minutes": plan.total_minutes,
            "selection_rank": plan.selection_rank,
            "discovery_start": plan.discovery_start,
            "discovery_end": plan.discovery_end,
            "suggested_commands": list(report.suggested_commands),
            "preflight_cues": list(report.preflight_cues),
            "recovery_cues": list(report.recovery_cues),
            "totals": {
                "cues": report.cue_count,
                "segments": report.segment_count,
                "ready": report.ready_segment_count,
                "partial": report.partial_segment_count,
                "blocked": report.blocked_segment_count,
                "event_rows": report.total_event_row_count,
                "mock_messages": report.total_mock_message_count,
                "deferred_rows": report.total_deferred_row_count,
            },
            "stage_packet": _stage_packet_json(report.stage_packet),
            "cues": [_live_cue_json(cue) for cue in report.cues],
        },
        "safety": list(LIVE_CUE_SHEET_SAFETY_LINES),
    }
