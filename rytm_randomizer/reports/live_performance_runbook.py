"""Passive live-performance runbook report for style performance arcs."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..style_analysis.feature_report import FeatureReport
from .dual_machine_style_kit_selection import normalize_selection_scope
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines
from .style_performance_arcs import (
    StylePerformanceArcLiveCue,
    StylePerformanceArcLiveCueSheetReport,
    StylePerformanceArcReferenceMatchReport,
    StylePerformanceArcStageCard,
    StylePerformanceArcStagePacket,
    build_style_performance_arc_live_cue_sheet_report,
    build_style_performance_arc_reference_match_report,
    to_style_performance_arc_live_cue_sheet_json,
    to_style_performance_arc_reference_match_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live runbook"
SOURCE_MODULE: Final[str] = "reports.live_performance_runbook"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "operator runbook only",
    "uses saved-kit snapshots when supplied",
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
_DEFAULT_EVENT_LIMIT: Final[int] = 24
_USAGE: Final[str] = (
    "style-performance-arc-live-runbook-report usage: "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]"
)
_CLI_OPTIONS: Final[tuple[str, ...]] = (
    "--arc",
    "--description",
    "--audio",
    "--library",
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
class StylePerformanceArcLiveRunbookTimelineCard:
    """One live runbook timeline card derived from a stage card and cue row."""

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
    event_preview_rows: tuple[str, ...]


@dataclass(frozen=True)
class StylePerformanceArcLiveRunbookReport:
    """Passive show-facing runbook for one selected performance arc."""

    selection_source: str
    source_reference: str | None
    live_cue_sheet: StylePerformanceArcLiveCueSheetReport
    reference_match: StylePerformanceArcReferenceMatchReport | None
    launch_brief: tuple[str, ...]
    timeline_cards: tuple[StylePerformanceArcLiveRunbookTimelineCard, ...]
    recovery_cues: tuple[str, ...]
    suggested_commands: tuple[str, ...]

    @property
    def selected_arc_key(self) -> str:
        """Return the selected performance arc key."""

        return self.stage_packet.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return the selected performance arc display name."""

        return self.stage_packet.selected_arc_name

    @property
    def scope(self) -> str:
        """Return the selected performance scope."""

        return self.stage_packet.scope

    @property
    def show_mode(self) -> str:
        """Return a human-facing show mode label."""

        if self.scope == "dual":
            return "dual-machine"
        if self.scope == "rytm-only":
            return "Rytm only"
        if self.scope == "analog-four-only":
            return "Analog Four only"
        return self.scope

    @property
    def stage_packet(self) -> StylePerformanceArcStagePacket:
        """Return the compact stage packet for the runbook."""

        return self.live_cue_sheet.stage_packet

    @property
    def readiness(self) -> str:
        """Return the selected stage-packet readiness."""

        return self.stage_packet.readiness

    @property
    def total_minutes(self) -> int:
        """Return planned set duration in minutes."""

        return self.stage_packet.total_minutes

    @property
    def cue_count(self) -> int:
        """Return runbook cue count."""

        return self.stage_packet.cue_count


def _number_sequence(values: Sequence[int]) -> str:
    if not values:
        return "none"
    return ", ".join(str(value) for value in values)


def _string_sequence(values: Sequence[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def _selection_source_count(
    *,
    arc_key: str | None,
    description: str | None,
    feature_report: FeatureReport | None,
    audio_path: Path | None,
    library_path: Path | None,
) -> int:
    return sum(
        (
            bool(arc_key),
            bool(description and description.strip()),
            feature_report is not None,
            audio_path is not None,
            library_path is not None,
        )
    )


def _source_reference(
    *,
    arc_key: str | None,
    description: str | None,
    feature_report: FeatureReport | None,
    audio_path: Path | None,
    library_path: Path | None,
) -> tuple[str, str | None]:
    if arc_key is not None and arc_key.strip():
        return "arc", arc_key.strip()
    if description is not None and description.strip():
        return "description", description.strip()
    if feature_report is not None:
        return "feature-report", feature_report.content_hash
    if audio_path is not None:
        return "audio", str(audio_path)
    if library_path is not None:
        return "library", str(library_path)
    raise ValueError("live runbook requires exactly one selection source")


def _launch_brief(
    cue_sheet: StylePerformanceArcLiveCueSheetReport,
    *,
    selection_source: str,
) -> tuple[str, ...]:
    packet = cue_sheet.stage_packet
    return (
        (
            f"Selected {packet.selected_arc_key} / {packet.selected_arc_name} "
            f"from {selection_source}."
        ),
        (
            f"Run {packet.cue_count} cue(s) across {packet.total_minutes} minute(s) "
            f"in {packet.scope} scope."
        ),
        (
            f"Readiness is {packet.readiness}; review red/amber timeline cards before "
            "arming hardware."
        ),
        "Use this report as a passive stage checklist; it opens no ports and sends no MIDI.",
    )


def _timeline_card_from_stage_card(
    card: StylePerformanceArcStageCard,
    cue: StylePerformanceArcLiveCue,
) -> StylePerformanceArcLiveRunbookTimelineCard:
    return StylePerformanceArcLiveRunbookTimelineCard(
        cue_number=card.cue_number,
        time_window=card.time_window,
        style_key=card.style_key,
        machine_focus=card.machine_focus,
        readiness=card.readiness,
        risk_level=card.risk_level,
        operator_move=card.operator_move,
        listen_for=card.listen_for,
        recovery_action=card.recovery_action,
        planned_rytm_pads=card.planned_rytm_pads,
        planned_analog_four_tracks=card.planned_analog_four_tracks,
        event_row_count=card.event_row_count,
        mock_message_count=card.mock_message_count,
        deferred_row_count=card.deferred_row_count,
        render_row_summary=card.render_row_summary,
        event_preview_rows=cue.render_segment.event_preview_rows,
    )


def _timeline_cards_from_cue_sheet(
    cue_sheet: StylePerformanceArcLiveCueSheetReport,
) -> tuple[StylePerformanceArcLiveRunbookTimelineCard, ...]:
    return tuple(
        _timeline_card_from_stage_card(card, cue)
        for card, cue in zip(
            cue_sheet.stage_packet.stage_cards,
            cue_sheet.cues,
            strict=True,
        )
    )


def _limited_event_rows(
    rows: Sequence[str],
    *,
    event_limit: int,
) -> tuple[str, ...]:
    if event_limit == 0 or event_limit >= len(rows):
        return tuple(rows)
    return tuple(rows[:event_limit])


def build_style_performance_arc_live_runbook_report(
    *,
    arc_key: str | None = None,
    description: str | None = None,
    feature_report: FeatureReport | None = None,
    audio_path: Path | None = None,
    library_path: Path | None = None,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
) -> StylePerformanceArcLiveRunbookReport:
    """Return a passive live runbook from a direct arc or reference source."""

    if (
        _selection_source_count(
            arc_key=arc_key,
            description=description,
            feature_report=feature_report,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError("live runbook requires exactly one selection source")

    selection_source, source_reference = _source_reference(
        arc_key=arc_key,
        description=description,
        feature_report=feature_report,
        audio_path=audio_path,
        library_path=library_path,
    )
    reference_match = None
    if selection_source == "arc":
        cue_sheet = build_style_performance_arc_live_cue_sheet_report(
            (source_reference,),
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
        )
    else:
        reference_match = build_style_performance_arc_reference_match_report(
            description=description,
            feature_report=feature_report,
            audio_path=audio_path,
            library_path=library_path,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
            include_live_cue_sheet=True,
        )
        if reference_match.live_cue_sheet is None:
            raise ValueError(
                "live runbook requires saved-kit source paths before a cue sheet "
                "and stage packet can be embedded"
            )
        cue_sheet = reference_match.live_cue_sheet

    return StylePerformanceArcLiveRunbookReport(
        selection_source=selection_source,
        source_reference=source_reference,
        live_cue_sheet=cue_sheet,
        reference_match=reference_match,
        launch_brief=_launch_brief(cue_sheet, selection_source=selection_source),
        timeline_cards=_timeline_cards_from_cue_sheet(cue_sheet),
        recovery_cues=cue_sheet.recovery_cues,
        suggested_commands=cue_sheet.suggested_commands,
    )


def _reference_match_lines(
    reference_match: StylePerformanceArcReferenceMatchReport | None,
) -> list[str]:
    if reference_match is None:
        return []
    selected = reference_match.selected_match
    lines = [
        "Reference match:",
        f"- Source kind: {reference_match.source_kind}",
        f"- Selected arc: {selected.arc.key} / {selected.arc.name}",
        f"- Selected score: {selected.score}",
        f"- Matched terms: {_string_sequence(selected.matched_terms)}",
    ]
    if reference_match.source_reference is not None:
        lines.insert(2, f"- Source reference: {reference_match.source_reference}")
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


def _stage_packet_lines(packet: StylePerformanceArcStagePacket) -> list[str]:
    lines = [
        "Stage packet:",
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


def _timeline_card_lines(
    card: StylePerformanceArcLiveRunbookTimelineCard,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    lines = [
        (
            f"- Cue {card.cue_number}. {card.time_window} | {card.style_key} | "
            f"{card.machine_focus}"
        ),
        f"  Readiness: {card.readiness}",
        f"  Risk: {card.risk_level}",
        f"  Operator move: {card.operator_move}",
        f"  Listen for: {card.listen_for}",
        f"  Recovery: {card.recovery_action}",
        f"  Planned Rytm pads: {_number_sequence(card.planned_rytm_pads)}",
        f"  Planned Analog Four tracks: {_number_sequence(card.planned_analog_four_tracks)}",
        (
            "  Render rows: "
            f"{card.event_row_count} event row(s), "
            f"{card.deferred_row_count} deferred row(s)"
        ),
    ]
    if include_events:
        lines.append("  Cue event preview:")
        if not card.event_preview_rows:
            lines.append("  - No mock rows available because the selected preview is not ready.")
        else:
            selected_rows = _limited_event_rows(
                card.event_preview_rows,
                event_limit=event_limit,
            )
            if len(selected_rows) == len(card.event_preview_rows):
                lines.append("  - Showing all events")
            else:
                lines.append(
                    f"  - Showing first {event_limit} of {len(card.event_preview_rows)} events"
                )
            lines.extend(f"  {row}" for row in selected_rows)
    return lines


def format_style_performance_arc_live_runbook_report(
    report: StylePerformanceArcLiveRunbookReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing live runbook lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    lines = [
        "Runbook summary:",
        f"- Selection source: {report.selection_source}",
        f"- Source reference: {report.source_reference}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Show mode: {report.show_mode}",
        f"- Scope: {report.scope}",
        f"- Readiness: {report.readiness}",
        f"- Total duration minutes: {report.total_minutes}",
        f"- Cue count: {report.cue_count}",
        f"- Total event rows: {report.stage_packet.total_event_row_count}",
        f"- Total mock messages: {report.stage_packet.total_mock_message_count}",
        f"- Total deferred rows: {report.stage_packet.total_deferred_row_count}",
        *_reference_match_lines(report.reference_match),
        "Launch brief:",
        *[f"- {line}" for line in report.launch_brief],
        "Replayable passive commands:",
        *[f"- {command}" for command in report.suggested_commands],
        *_stage_packet_lines(report.stage_packet),
        "Timeline cards:",
    ]
    for card in report.timeline_cards:
        lines.extend(
            _timeline_card_lines(
                card,
                include_events=include_events,
                event_limit=event_limit,
            )
        )
    lines.extend(["Recovery cues:", *[f"- {cue}" for cue in report.recovery_cues]])
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return passive_report_lines(_HEADER, lines)


def _timeline_card_json(card: StylePerformanceArcLiveRunbookTimelineCard) -> dict[str, object]:
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
        "event_preview_rows": list(card.event_preview_rows),
    }


def to_style_performance_arc_live_runbook_json(
    report: StylePerformanceArcLiveRunbookReport,
) -> dict[str, object]:
    """Return deterministic JSON data for a live runbook."""

    cue_sheet_json = to_style_performance_arc_live_cue_sheet_json(report.live_cue_sheet)
    return {
        "live_runbook": {
            "selection_source": report.selection_source,
            "source_reference": report.source_reference,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "show_mode": report.show_mode,
            "scope": report.scope,
            "readiness": report.readiness,
            "total_minutes": report.total_minutes,
            "cue_count": report.cue_count,
            "launch_brief": list(report.launch_brief),
            "suggested_commands": list(report.suggested_commands),
            "recovery_cues": list(report.recovery_cues),
            "stage_packet": cue_sheet_json["cue_sheet"]["stage_packet"],
            "timeline_cards": [_timeline_card_json(card) for card in report.timeline_cards],
        },
        "cue_sheet": cue_sheet_json,
        "reference_match": (
            None
            if report.reference_match is None
            else to_style_performance_arc_reference_match_json(report.reference_match)
        ),
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


def _pop_option_value(remaining: list[str]) -> str:
    if not remaining:
        raise ValueError(_USAGE)
    return remaining.pop(0)


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    arc_key: str | None = None
    description: str | None = None
    audio_path: Path | None = None
    library_path: Path | None = None
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
    remaining = list(argv)
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
        if option == "--arc":
            arc_key = value
        elif option == "--description":
            description = value
        elif option == "--audio":
            audio_path = Path(value)
        elif option == "--library":
            library_path = Path(value)
        elif option == "--rytm":
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

    if (
        _selection_source_count(
            arc_key=arc_key,
            description=description,
            feature_report=None,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError(_USAGE)

    return {
        "arc_key": arc_key,
        "description": description,
        "audio_path": audio_path,
        "library_path": library_path,
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


def _handle_cli_report(
    *,
    arc_key: str | None,
    description: str | None,
    audio_path: Path | None,
    library_path: Path | None,
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
        report = build_style_performance_arc_live_runbook_report(
            arc_key=arc_key,
            description=description,
            audio_path=audio_path,
            library_path=library_path,
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
                    to_style_performance_arc_live_runbook_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_runbook_report(
            report,
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


STYLE_PERFORMANCE_ARC_LIVE_RUNBOOK_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-runbook-report",
    summary="Build a passive live performance runbook from an arc or reference.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_RUNBOOK_CLI_COMMAND)

__all__ = [
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_RUNBOOK_CLI_COMMAND",
    "StylePerformanceArcLiveRunbookReport",
    "StylePerformanceArcLiveRunbookTimelineCard",
    "build_style_performance_arc_live_runbook_report",
    "format_style_performance_arc_live_runbook_report",
    "to_style_performance_arc_live_runbook_json",
]
