"""Passive stage snapshot-routing report for style performance arcs."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..style_analysis.feature_report import FeatureReport
from .dual_machine_style_kit_selection import (
    StyleKitSelectionMachineChoice,
    normalize_selection_scope,
)
from .dual_machine_style_selection_mock_preview import (
    DualMachineStyleSelectionMockPreviewPlan,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines
from .live_performance_runbook import (
    StylePerformanceArcLiveRunbookReport,
    build_style_performance_arc_live_runbook_report,
    to_style_performance_arc_live_runbook_json,
)
from .style_performance_arcs import (
    StylePerformanceArcReferenceMatchReport,
    StylePerformanceArcStagePacket,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc stage snapshot routing"
SOURCE_MODULE: Final[str] = "reports.live_stage_snapshot_routing"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "stage routing packet only",
    "uses saved-kit snapshots when supplied",
    "Rytm rows are mock CC previews only",
    "Analog Four rows can remain candidate/deferred",
    "no real MIDI rendering",
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
    "style-performance-arc-stage-routing-report usage: "
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
class StylePerformanceArcStageSnapshotRouteCard:
    """One cue-level stage route derived from live cue and snapshot preview data."""

    cue_number: int
    time_window: str
    style_key: str
    machine_focus: str
    readiness: str
    route_status: str
    risk_level: str
    operator_move: str
    listen_for: str
    recovery_action: str
    planned_rytm_pads: tuple[int, ...]
    planned_analog_four_tracks: tuple[int, ...]
    event_row_count: int
    mock_message_count: int
    deferred_row_count: int
    rytm_slot: int | None
    rytm_kit_name: str | None
    rytm_payload_fingerprint: str | None
    rytm_mock_row_count: int
    analog_four_slot: int | None
    analog_four_kit_name: str | None
    analog_four_payload_fingerprint: str | None
    analog_four_mock_row_count: int
    analog_four_deferred_row_count: int
    blocker_summary: str
    event_preview_rows: tuple[str, ...]
    deferred_rows: tuple[str, ...]


@dataclass(frozen=True)
class StylePerformanceArcStageSnapshotRoutingReport:
    """Passive stage routing packet for one live runbook."""

    runbook: StylePerformanceArcLiveRunbookReport
    route_cards: tuple[StylePerformanceArcStageSnapshotRouteCard, ...]
    live_set_card: tuple[str, ...]
    suggested_commands: tuple[str, ...]

    @property
    def selection_source(self) -> str:
        """Return the selected source mode."""

        return self.runbook.selection_source

    @property
    def source_reference(self) -> str | None:
        """Return the selected source reference when available."""

        return self.runbook.source_reference

    @property
    def reference_match(self) -> StylePerformanceArcReferenceMatchReport | None:
        """Return the upstream reference match when the route came from a reference."""

        return self.runbook.reference_match

    @property
    def selected_arc_key(self) -> str:
        """Return the selected arc key."""

        return self.runbook.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return the selected arc name."""

        return self.runbook.selected_arc_name

    @property
    def show_mode(self) -> str:
        """Return the selected show-mode label."""

        return self.runbook.show_mode

    @property
    def scope(self) -> str:
        """Return the selected machine scope."""

        return self.runbook.scope

    @property
    def readiness(self) -> str:
        """Return the stage-packet readiness."""

        return self.runbook.readiness

    @property
    def cue_count(self) -> int:
        """Return cue count."""

        return self.runbook.cue_count

    @property
    def stage_packet(self) -> StylePerformanceArcStagePacket:
        """Return the embedded stage packet."""

        return self.runbook.stage_packet


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


def _choice_fingerprint(choice: StyleKitSelectionMachineChoice | None) -> str | None:
    if choice is None:
        return None
    return choice.payload_fingerprint


def _event_row_count_with_prefix(rows: Sequence[str], prefix: str) -> int:
    return sum(1 for row in rows if row.startswith(prefix))


def _analog_four_deferred_count(rows: Sequence[str]) -> int:
    if rows == ("- none",):
        return 0
    return sum(1 for row in rows if row.startswith("- Analog Four Track"))


def _blocker_summary(
    *,
    preview_plan: DualMachineStyleSelectionMockPreviewPlan,
    event_row_count: int,
    deferred_rows: Sequence[str],
) -> str:
    analog_four_preview = preview_plan.analog_four_preview
    if analog_four_preview is not None and analog_four_preview.deferred_rows:
        reasons = tuple(sorted({row.reason for row in analog_four_preview.deferred_rows}))
        return (
            "Analog Four deferred/candidate rows block live rendering until promoted: "
            f"{_string_sequence(reasons)}."
        )
    if deferred_rows and deferred_rows != ("- none",):
        return "Deferred rows are present; rehearse this cue before armed live use."
    if event_row_count == 0:
        return "No mock rows are available because the selected preview is not ready."
    return "No route blockers detected in the passive mock preview."


def _route_status(
    *,
    readiness: str,
    event_row_count: int,
    deferred_row_count: int,
) -> str:
    if readiness in {"ready", "partial", "blocked", "empty"}:
        return readiness
    if deferred_row_count:
        return "partial"
    if event_row_count:
        return "ready"
    return "empty"


def _route_card_from_runbook_index(
    runbook: StylePerformanceArcLiveRunbookReport,
    index: int,
) -> StylePerformanceArcStageSnapshotRouteCard:
    cue = runbook.live_cue_sheet.cues[index]
    timeline = runbook.timeline_cards[index]
    segment = cue.render_segment
    preview_plan = segment.set_plan_segment.preview_plan
    rytm_choice = preview_plan.selection.rytm_choice
    analog_four_choice = preview_plan.selection.analog_four_choice
    rytm_mock_row_count = _event_row_count_with_prefix(
        segment.event_preview_rows,
        "- Rytm Pad",
    )
    analog_four_mock_row_count = _event_row_count_with_prefix(
        segment.event_preview_rows,
        "- Analog Four Track",
    )
    analog_four_deferred_row_count = _analog_four_deferred_count(segment.deferred_rows)
    route_status = _route_status(
        readiness=timeline.readiness,
        event_row_count=timeline.event_row_count,
        deferred_row_count=timeline.deferred_row_count,
    )
    return StylePerformanceArcStageSnapshotRouteCard(
        cue_number=timeline.cue_number,
        time_window=timeline.time_window,
        style_key=timeline.style_key,
        machine_focus=timeline.machine_focus,
        readiness=timeline.readiness,
        route_status=route_status,
        risk_level=timeline.risk_level,
        operator_move=timeline.operator_move,
        listen_for=timeline.listen_for,
        recovery_action=timeline.recovery_action,
        planned_rytm_pads=timeline.planned_rytm_pads,
        planned_analog_four_tracks=timeline.planned_analog_four_tracks,
        event_row_count=timeline.event_row_count,
        mock_message_count=timeline.mock_message_count,
        deferred_row_count=timeline.deferred_row_count,
        rytm_slot=None if rytm_choice is None else rytm_choice.slot,
        rytm_kit_name=None if rytm_choice is None else rytm_choice.kit_name,
        rytm_payload_fingerprint=_choice_fingerprint(rytm_choice),
        rytm_mock_row_count=rytm_mock_row_count,
        analog_four_slot=None if analog_four_choice is None else analog_four_choice.slot,
        analog_four_kit_name=None if analog_four_choice is None else analog_four_choice.kit_name,
        analog_four_payload_fingerprint=_choice_fingerprint(analog_four_choice),
        analog_four_mock_row_count=analog_four_mock_row_count,
        analog_four_deferred_row_count=analog_four_deferred_row_count,
        blocker_summary=_blocker_summary(
            preview_plan=preview_plan,
            event_row_count=timeline.event_row_count,
            deferred_rows=segment.deferred_rows,
        ),
        event_preview_rows=segment.event_preview_rows,
        deferred_rows=segment.deferred_rows,
    )


def _route_cards_from_runbook(
    runbook: StylePerformanceArcLiveRunbookReport,
) -> tuple[StylePerformanceArcStageSnapshotRouteCard, ...]:
    if len(runbook.timeline_cards) != len(runbook.live_cue_sheet.cues):
        raise ValueError("stage snapshot routing requires matching runbook cue counts")
    return tuple(
        _route_card_from_runbook_index(runbook, index)
        for index in range(len(runbook.timeline_cards))
    )


def _live_set_card(report: StylePerformanceArcLiveRunbookReport) -> tuple[str, ...]:
    return (
        "Preflight: run passive reports first; keep the machine volume moderate.",
        (
            "Armed path: rytm-randomizer --arm -> choose the Rytm output -> "
            "target Pad 1 -> profile 1."
        ),
        "Performance flow: SCN -> GM -> S1A -> S3A -> S3B -> S4B -> S5 -> Z -> Q.",
        "Rescue sequence: S5 -> Z -> Q.",
        (
            "S3B and S4B are loud/high-energy checkpoints; rehearse before pushing "
            f"{report.selected_arc_name} live."
        ),
    )


def _stage_routing_command(report: StylePerformanceArcLiveRunbookReport) -> str:
    source = report.source_reference or report.selected_arc_key
    if report.selection_source == "arc":
        selector = f"--arc {source}"
    elif report.selection_source == "description":
        selector = f"--description {source}"
    elif report.selection_source == "feature-report":
        selector = f"--description {report.selected_arc_name}"
    elif report.selection_source == "audio":
        selector = f"--audio {source}"
    else:
        selector = f"--library {source}"
    return (
        "python -m rytm_randomizer.cli style-performance-arc-stage-routing-report "
        f"{selector} --scope {report.scope} --events --limit 8"
    )


def build_style_performance_arc_stage_snapshot_routing_report(
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
) -> StylePerformanceArcStageSnapshotRoutingReport:
    """Return a passive stage snapshot-routing packet from a runbook source."""

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
        raise ValueError("stage snapshot routing requires exactly one selection source")

    runbook = build_style_performance_arc_live_runbook_report(
        arc_key=arc_key,
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
    )
    return StylePerformanceArcStageSnapshotRoutingReport(
        runbook=runbook,
        route_cards=_route_cards_from_runbook(runbook),
        live_set_card=_live_set_card(runbook),
        suggested_commands=(
            _stage_routing_command(runbook),
            *runbook.suggested_commands,
        ),
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


def _limited_event_rows(
    rows: Sequence[str],
    *,
    event_limit: int,
) -> tuple[str, ...]:
    if event_limit == 0 or event_limit >= len(rows):
        return tuple(rows)
    return tuple(rows[:event_limit])


def _route_card_lines(
    card: StylePerformanceArcStageSnapshotRouteCard,
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
        f"  Route status: {card.route_status}",
        f"  Risk: {card.risk_level}",
        f"  Operator move: {card.operator_move}",
        f"  Listen for: {card.listen_for}",
        f"  Recovery: {card.recovery_action}",
        f"  Planned Rytm pads: {_number_sequence(card.planned_rytm_pads)}",
        f"  Planned Analog Four tracks: {_number_sequence(card.planned_analog_four_tracks)}",
        (
            "  Render rows: "
            f"{card.event_row_count} event row(s), "
            f"{card.mock_message_count} mock message(s), "
            f"{card.deferred_row_count} deferred row(s)"
        ),
    ]
    if card.rytm_slot is None:
        lines.append("  Rytm snapshot: unchanged by scope")
    else:
        lines.extend(
            [
                (
                    f"  Rytm snapshot: slot {card.rytm_slot} {card.rytm_kit_name} "
                    f"/ fingerprint {card.rytm_payload_fingerprint}"
                ),
                f"  Rytm mock rows: {card.rytm_mock_row_count}",
            ]
        )
    if card.analog_four_slot is None:
        lines.append("  Analog Four snapshot: unchanged by scope")
    else:
        lines.extend(
            [
                (
                    "  Analog Four snapshot: "
                    f"slot {card.analog_four_slot} {card.analog_four_kit_name} "
                    f"/ fingerprint {card.analog_four_payload_fingerprint}"
                ),
                f"  Analog Four mock rows: {card.analog_four_mock_row_count}",
                f"  Analog Four deferred rows: {card.analog_four_deferred_row_count}",
            ]
        )
    lines.extend(
        [
            f"  Blockers: {card.blocker_summary}",
            "  A4 deferred/candidate rows:",
            *[f"  {row}" for row in card.deferred_rows],
            "  Rescue sequence: S5 -> Z -> Q",
        ]
    )
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


def format_style_performance_arc_stage_snapshot_routing_report(
    report: StylePerformanceArcStageSnapshotRoutingReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic stage snapshot-routing lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    lines = [
        "Stage snapshot routing summary:",
        f"- Selection source: {report.selection_source}",
        f"- Source reference: {report.source_reference}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Show mode: {report.show_mode}",
        f"- Scope: {report.scope}",
        f"- Readiness: {report.readiness}",
        f"- Cue count: {report.cue_count}",
        f"- Total event rows: {report.stage_packet.total_event_row_count}",
        f"- Total mock messages: {report.stage_packet.total_mock_message_count}",
        f"- Total deferred rows: {report.stage_packet.total_deferred_row_count}",
        *_reference_match_lines(report.reference_match),
        "Live set card:",
        *[f"- {line}" for line in report.live_set_card],
        "Replayable passive commands:",
        *[f"- {command}" for command in report.suggested_commands],
        "Route cards:",
    ]
    for card in report.route_cards:
        lines.extend(
            _route_card_lines(
                card,
                include_events=include_events,
                event_limit=event_limit,
            )
        )
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return passive_report_lines(_HEADER, lines)


def _route_machine_json(
    *,
    slot: int | None,
    kit_name: str | None,
    payload_fingerprint: str | None,
    planned_numbers: Sequence[int],
    mock_row_count: int,
    deferred_row_count: int = 0,
) -> dict[str, object]:
    return {
        "slot": slot,
        "kit_name": kit_name,
        "payload_fingerprint": payload_fingerprint,
        "planned": list(planned_numbers),
        "mock_row_count": mock_row_count,
        "deferred_row_count": deferred_row_count,
    }


def _route_card_json(
    card: StylePerformanceArcStageSnapshotRouteCard,
) -> dict[str, object]:
    return {
        "cue_number": card.cue_number,
        "time_window": card.time_window,
        "style_key": card.style_key,
        "machine_focus": card.machine_focus,
        "readiness": card.readiness,
        "route_status": card.route_status,
        "risk_level": card.risk_level,
        "operator_move": card.operator_move,
        "listen_for": card.listen_for,
        "recovery_action": card.recovery_action,
        "event_row_count": card.event_row_count,
        "mock_message_count": card.mock_message_count,
        "deferred_row_count": card.deferred_row_count,
        "blocker_summary": card.blocker_summary,
        "rytm": _route_machine_json(
            slot=card.rytm_slot,
            kit_name=card.rytm_kit_name,
            payload_fingerprint=card.rytm_payload_fingerprint,
            planned_numbers=card.planned_rytm_pads,
            mock_row_count=card.rytm_mock_row_count,
        ),
        "analog_four": _route_machine_json(
            slot=card.analog_four_slot,
            kit_name=card.analog_four_kit_name,
            payload_fingerprint=card.analog_four_payload_fingerprint,
            planned_numbers=card.planned_analog_four_tracks,
            mock_row_count=card.analog_four_mock_row_count,
            deferred_row_count=card.analog_four_deferred_row_count,
        ),
        "event_preview_rows": list(card.event_preview_rows),
        "deferred_rows": list(card.deferred_rows),
    }


def to_style_performance_arc_stage_snapshot_routing_json(
    report: StylePerformanceArcStageSnapshotRoutingReport,
) -> dict[str, object]:
    """Return deterministic JSON data for stage snapshot routing."""

    runbook_json = to_style_performance_arc_live_runbook_json(report.runbook)
    return {
        "stage_snapshot_routing": {
            "selection_source": report.selection_source,
            "source_reference": report.source_reference,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "show_mode": report.show_mode,
            "scope": report.scope,
            "readiness": report.readiness,
            "cue_count": report.cue_count,
            "live_set_card": list(report.live_set_card),
            "suggested_commands": list(report.suggested_commands),
            "stage_packet": runbook_json["live_runbook"]["stage_packet"],
            "route_cards": [_route_card_json(card) for card in report.route_cards],
        },
        "live_runbook": runbook_json["live_runbook"],
        "cue_sheet": runbook_json["cue_sheet"],
        "reference_match": runbook_json["reference_match"],
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
        report = build_style_performance_arc_stage_snapshot_routing_report(
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
                    to_style_performance_arc_stage_snapshot_routing_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_stage_snapshot_routing_report(
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


STYLE_PERFORMANCE_ARC_STAGE_ROUTING_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-stage-routing-report",
    summary="Build passive stage snapshot routing from an arc or reference.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_STAGE_ROUTING_CLI_COMMAND)

__all__ = [
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_STAGE_ROUTING_CLI_COMMAND",
    "StylePerformanceArcStageSnapshotRouteCard",
    "StylePerformanceArcStageSnapshotRoutingReport",
    "build_style_performance_arc_stage_snapshot_routing_report",
    "format_style_performance_arc_stage_snapshot_routing_report",
    "to_style_performance_arc_stage_snapshot_routing_json",
]
