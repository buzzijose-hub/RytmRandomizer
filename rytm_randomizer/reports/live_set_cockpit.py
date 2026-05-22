"""Passive live set cockpit report for style performance arcs."""

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
from .live_stage_rehearsal_state import (
    StylePerformanceArcStageRehearsalCueState,
    StylePerformanceArcStageRehearsalMachineState,
    StylePerformanceArcStageRehearsalStateReport,
    build_style_performance_arc_stage_rehearsal_state_report,
    to_style_performance_arc_stage_rehearsal_state_json,
)
from .style_performance_arcs import StylePerformanceArcReferenceMatchReport

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live set cockpit"
SOURCE_MODULE: Final[str] = "reports.live_set_cockpit"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live set cockpit packet only",
    "composes stage rehearsal state only",
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
    "style-performance-arc-live-set-cockpit-report usage: "
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
RECOVERY_CONTROLS: Final[tuple[str, ...]] = (
    "Keep S5 -> Z -> Q ready as the live rescue sequence.",
    "If a cue turns red, skip the cue and keep the current kit/snapshot parked.",
    "Return to clean anchors before changing references mid-set.",
    "Exit the script with Q if anything feels wrong.",
)


@dataclass(frozen=True)
class StylePerformanceArcLiveSetMachinePanel:
    """One machine panel for the passive cockpit dashboard."""

    machine: str
    label: str
    status: str
    status_light: str
    arm_state: str
    slot_summary: str
    kit_summary: str
    fingerprint_summary: str
    planned_units: tuple[int, ...]
    mock_row_count: int
    deferred_row_count: int
    operator_check: str


@dataclass(frozen=True)
class StylePerformanceArcLiveSetCockpitCueCard:
    """One now/next cue card for the passive cockpit dashboard."""

    cue_number: int
    deck_label: str
    time_window: str
    style_key: str
    status_light: str
    go_no_go: str
    stage_state: str
    operator_mode: str
    machine_focus: str
    machine_arm_summary: str
    operator_prompt: str
    listen_for: str
    recovery_action: str
    risk_level: str
    route_status: str
    blocker_summary: str
    planned_rytm_pads: tuple[int, ...]
    planned_analog_four_tracks: tuple[int, ...]
    event_preview_rows: tuple[str, ...]
    deferred_rows: tuple[str, ...]


@dataclass(frozen=True)
class StylePerformanceArcLiveSetCockpitReport:
    """Passive cockpit packet composed from stage rehearsal state."""

    stage_rehearsal_state: StylePerformanceArcStageRehearsalStateReport
    cockpit_status: str
    operator_mode: str
    next_best_action: str
    launch_controls: tuple[str, ...]
    machine_panels: tuple[StylePerformanceArcLiveSetMachinePanel, ...]
    cue_cards: tuple[StylePerformanceArcLiveSetCockpitCueCard, ...]
    recovery_controls: tuple[str, ...]
    suggested_commands: tuple[str, ...]

    @property
    def selection_source(self) -> str:
        """Return the selected source mode."""

        return self.stage_rehearsal_state.selection_source

    @property
    def source_reference(self) -> str | None:
        """Return the selected source reference when available."""

        return self.stage_rehearsal_state.source_reference

    @property
    def reference_match(self) -> StylePerformanceArcReferenceMatchReport | None:
        """Return the upstream reference match when present."""

        return self.stage_rehearsal_state.reference_match

    @property
    def selected_arc_key(self) -> str:
        """Return the selected arc key."""

        return self.stage_rehearsal_state.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return the selected arc name."""

        return self.stage_rehearsal_state.selected_arc_name

    @property
    def show_mode(self) -> str:
        """Return the selected show-mode label."""

        return self.stage_rehearsal_state.show_mode

    @property
    def scope(self) -> str:
        """Return the selected machine scope."""

        return self.stage_rehearsal_state.scope

    @property
    def readiness(self) -> str:
        """Return the selected stage-packet readiness."""

        return self.stage_rehearsal_state.readiness

    @property
    def stage_state(self) -> str:
        """Return the stage state used by the cockpit."""

        return self.cockpit_status

    @property
    def overall_go_no_go(self) -> str:
        """Return the aggregate go/no-go value."""

        return self.stage_rehearsal_state.overall_go_no_go

    @property
    def cue_count(self) -> int:
        """Return cue count."""

        return self.stage_rehearsal_state.cue_count


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


def _status_light(go_no_go: str) -> str:
    if go_no_go == "go":
        return "GREEN"
    if go_no_go == "rehearse":
        return "AMBER"
    if go_no_go == "do-not-arm":
        return "RED"
    return "WHITE"


def _machine_status_light(status: str) -> str:
    if status == "loaded":
        return "GREEN"
    if status in {"candidate-deferred", "parked", "unchanged-by-scope"}:
        return "AMBER"
    if status == "blocked":
        return "RED"
    return "WHITE"


def _operator_mode(stage_state: str) -> str:
    if stage_state == "ready":
        return "performance-ready"
    if stage_state == "rehearsal-required":
        return "soundcheck"
    if stage_state == "blocked":
        return "blocked"
    return "review"


def _next_best_action(stage_state: str, go_no_go: str) -> str:
    if go_no_go == "go":
        return "Run one passive cockpit pass, then arm only after human confirmation."
    if go_no_go == "rehearse":
        return "Rehearse the amber cue cards with the sequencer running before arming."
    if go_no_go == "do-not-arm":
        return "Resolve red blockers before any live send path is considered."
    return f"Review cockpit state {stage_state} before proceeding."


def _launch_controls(
    stage_rehearsal_state: StylePerformanceArcStageRehearsalStateReport,
) -> tuple[str, ...]:
    runbook = stage_rehearsal_state.stage_routing.runbook
    return (
        *runbook.launch_brief,
        *stage_rehearsal_state.stage_routing.live_set_card,
    )


def _suggested_source_option(
    stage_rehearsal_state: StylePerformanceArcStageRehearsalStateReport,
) -> str:
    if stage_rehearsal_state.selection_source in {"arc", "description", "audio", "library"}:
        source_reference = (
            stage_rehearsal_state.source_reference or stage_rehearsal_state.selected_arc_key
        )
        return f"--{stage_rehearsal_state.selection_source} {source_reference}"
    return f"--arc {stage_rehearsal_state.selected_arc_key}"


def _slot_summary(state: StylePerformanceArcStageRehearsalMachineState) -> str:
    return "none" if state.slot is None else str(state.slot)


def _kit_summary(state: StylePerformanceArcStageRehearsalMachineState) -> str:
    return state.kit_name or "none"


def _fingerprint_summary(state: StylePerformanceArcStageRehearsalMachineState) -> str:
    return state.payload_fingerprint or "none"


def _machine_panel(
    state: StylePerformanceArcStageRehearsalMachineState,
) -> StylePerformanceArcLiveSetMachinePanel:
    if state.status == "loaded":
        arm_state = "armed-preview"
    elif state.status == "blocked":
        arm_state = "do-not-arm"
    else:
        arm_state = "rehearse"
    return StylePerformanceArcLiveSetMachinePanel(
        machine=state.machine,
        label=state.label,
        status=state.status,
        status_light=_machine_status_light(state.status),
        arm_state=arm_state,
        slot_summary=_slot_summary(state),
        kit_summary=_kit_summary(state),
        fingerprint_summary=_fingerprint_summary(state),
        planned_units=state.planned_units,
        mock_row_count=state.mock_row_count,
        deferred_row_count=state.deferred_row_count,
        operator_check=state.operator_check,
    )


def _machine_arm_summary(cue: StylePerformanceArcStageRehearsalCueState) -> str:
    return f"Rytm {cue.rytm_state.status}; Analog Four {cue.analog_four_state.status}"


def _cue_card(
    cue: StylePerformanceArcStageRehearsalCueState,
) -> StylePerformanceArcLiveSetCockpitCueCard:
    return StylePerformanceArcLiveSetCockpitCueCard(
        cue_number=cue.cue_number,
        deck_label=f"Cue {cue.cue_number}",
        time_window=cue.time_window,
        style_key=cue.style_key,
        status_light=_status_light(cue.go_no_go),
        go_no_go=cue.go_no_go,
        stage_state=cue.stage_state,
        operator_mode=_operator_mode(cue.stage_state),
        machine_focus=cue.machine_focus,
        machine_arm_summary=_machine_arm_summary(cue),
        operator_prompt=cue.operator_prompt,
        listen_for=cue.listen_for,
        recovery_action=cue.recovery_action,
        risk_level=cue.risk_level,
        route_status=cue.route_status,
        blocker_summary=cue.blocker_summary,
        planned_rytm_pads=cue.planned_rytm_pads,
        planned_analog_four_tracks=cue.planned_analog_four_tracks,
        event_preview_rows=cue.event_preview_rows,
        deferred_rows=cue.deferred_rows,
    )


def build_style_performance_arc_live_set_cockpit_from_rehearsal_state(
    stage_rehearsal_state: StylePerformanceArcStageRehearsalStateReport,
) -> StylePerformanceArcLiveSetCockpitReport:
    """Build a cockpit packet from an existing stage rehearsal state."""

    operator_mode = _operator_mode(stage_rehearsal_state.stage_state)
    return StylePerformanceArcLiveSetCockpitReport(
        stage_rehearsal_state=stage_rehearsal_state,
        cockpit_status=stage_rehearsal_state.stage_state,
        operator_mode=operator_mode,
        next_best_action=_next_best_action(
            stage_rehearsal_state.stage_state,
            stage_rehearsal_state.overall_go_no_go,
        ),
        launch_controls=_launch_controls(stage_rehearsal_state),
        machine_panels=tuple(
            _machine_panel(state) for state in stage_rehearsal_state.machine_states
        ),
        cue_cards=tuple(_cue_card(cue) for cue in stage_rehearsal_state.cue_states),
        recovery_controls=RECOVERY_CONTROLS,
        suggested_commands=(
            "python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report "
            f"{_suggested_source_option(stage_rehearsal_state)} "
            f"--scope {stage_rehearsal_state.scope} --events --limit 8",
            *stage_rehearsal_state.suggested_commands,
        ),
    )


def build_style_performance_arc_live_set_cockpit_report(
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
) -> StylePerformanceArcLiveSetCockpitReport:
    """Build a passive live set cockpit from an arc or reference."""

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
        raise ValueError("live set cockpit requires exactly one selection source")

    stage_rehearsal_state = build_style_performance_arc_stage_rehearsal_state_report(
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
    return build_style_performance_arc_live_set_cockpit_from_rehearsal_state(stage_rehearsal_state)


def _reference_match_lines(
    reference_match: StylePerformanceArcReferenceMatchReport | None,
) -> list[str]:
    if reference_match is None:
        return []
    selected = reference_match.selected_match
    return [
        "Reference match:",
        f"- Source kind: {reference_match.source_kind}",
        f"- Selected arc: {selected.arc.key} / {selected.arc.name}",
        f"- Selected score: {selected.score}",
        f"- Matched terms: {_string_sequence(selected.matched_terms)}",
    ]


def _limited_event_rows(rows: Sequence[str], *, event_limit: int) -> tuple[str, ...]:
    if event_limit == 0:
        return tuple(rows)
    return tuple(rows[:event_limit])


def _machine_panel_lines(panel: StylePerformanceArcLiveSetMachinePanel) -> list[str]:
    return [
        f"- {panel.label}: {panel.status_light} | {panel.status} | {panel.arm_state}",
        f"  Slot(s): {panel.slot_summary}",
        f"  Kit(s): {panel.kit_summary}",
        f"  Fingerprint(s): {panel.fingerprint_summary}",
        f"  Planned units: {_number_sequence(panel.planned_units)}",
        f"  Rows: mock {panel.mock_row_count} | deferred {panel.deferred_row_count}",
        f"  Check: {panel.operator_check}",
    ]


def _cue_card_lines(
    card: StylePerformanceArcLiveSetCockpitCueCard,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    lines = [
        f"- {card.deck_label}. {card.time_window} | {card.style_key} | {card.status_light}",
        f"  Go / no-go: {card.go_no_go}",
        f"  Stage state: {card.stage_state}",
        f"  Operator mode: {card.operator_mode}",
        f"  Focus: {card.machine_focus}",
        f"  Machine arm: {card.machine_arm_summary}",
        f"  Prompt: {card.operator_prompt}",
        f"  Listen for: {card.listen_for}",
        f"  Risk: {card.risk_level}",
        f"  Route: {card.route_status}",
        f"  Rytm pads: {_number_sequence(card.planned_rytm_pads)}",
        f"  Analog Four tracks: {_number_sequence(card.planned_analog_four_tracks)}",
        f"  Blockers: {card.blocker_summary}",
        f"  Recovery: {card.recovery_action}",
    ]
    if include_events:
        lines.append("  Cue event preview:")
        if not card.event_preview_rows:
            lines.append("  - No mock rows available because the selected preview is not ready.")
        else:
            rows = _limited_event_rows(card.event_preview_rows, event_limit=event_limit)
            if len(rows) == len(card.event_preview_rows):
                lines.append("  - Showing all events")
            else:
                lines.append(f"  - Showing first {event_limit} of {len(card.event_preview_rows)}")
            lines.extend(f"  {row}" for row in rows)
    return lines


def format_style_performance_arc_live_set_cockpit_report(
    report: StylePerformanceArcLiveSetCockpitReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic live set cockpit lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    stage = report.stage_rehearsal_state
    lines = [
        "Cockpit summary:",
        f"- Selection source: {report.selection_source}",
        f"- Source reference: {report.source_reference}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Show mode: {report.show_mode}",
        f"- Scope: {report.scope}",
        f"- Readiness: {report.readiness}",
        f"- Cue count: {report.cue_count}",
        f"- Cockpit status: {report.cockpit_status}",
        f"- Operator mode: {report.operator_mode}",
        f"- Go / no-go: {report.overall_go_no_go}",
        f"- Next best action: {report.next_best_action}",
        f"- Total event rows: {stage.stage_routing.stage_packet.total_event_row_count}",
        f"- Total mock messages: {stage.stage_routing.stage_packet.total_mock_message_count}",
        f"- Total deferred rows: {stage.stage_routing.stage_packet.total_deferred_row_count}",
        *_reference_match_lines(report.reference_match),
        "Launch controls:",
        *[f"- {line}" for line in report.launch_controls],
        "Machine panels:",
    ]
    for panel in report.machine_panels:
        lines.extend(_machine_panel_lines(panel))
    lines.extend(
        [
            "Cue cockpit cards:",
        ]
    )
    for card in report.cue_cards:
        lines.extend(
            _cue_card_lines(
                card,
                include_events=include_events,
                event_limit=event_limit,
            )
        )
    lines.extend(
        [
            "Recovery controls:",
            *[f"- {control}" for control in report.recovery_controls],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.suggested_commands],
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


def _machine_panel_json(panel: StylePerformanceArcLiveSetMachinePanel) -> dict[str, object]:
    return {
        "machine": panel.machine,
        "label": panel.label,
        "status": panel.status,
        "status_light": panel.status_light,
        "arm_state": panel.arm_state,
        "slot_summary": panel.slot_summary,
        "kit_summary": panel.kit_summary,
        "fingerprint_summary": panel.fingerprint_summary,
        "planned_units": list(panel.planned_units),
        "mock_row_count": panel.mock_row_count,
        "deferred_row_count": panel.deferred_row_count,
        "operator_check": panel.operator_check,
    }


def _cue_card_json(card: StylePerformanceArcLiveSetCockpitCueCard) -> dict[str, object]:
    return {
        "cue_number": card.cue_number,
        "deck_label": card.deck_label,
        "time_window": card.time_window,
        "style_key": card.style_key,
        "status_light": card.status_light,
        "go_no_go": card.go_no_go,
        "stage_state": card.stage_state,
        "operator_mode": card.operator_mode,
        "machine_focus": card.machine_focus,
        "machine_arm_summary": card.machine_arm_summary,
        "operator_prompt": card.operator_prompt,
        "listen_for": card.listen_for,
        "recovery_action": card.recovery_action,
        "risk_level": card.risk_level,
        "route_status": card.route_status,
        "blocker_summary": card.blocker_summary,
        "planned_rytm_pads": list(card.planned_rytm_pads),
        "planned_analog_four_tracks": list(card.planned_analog_four_tracks),
        "event_preview_rows": list(card.event_preview_rows),
        "deferred_rows": list(card.deferred_rows),
    }


def to_style_performance_arc_live_set_cockpit_json(
    report: StylePerformanceArcLiveSetCockpitReport,
) -> dict[str, object]:
    """Return deterministic JSON data for the live set cockpit."""

    rehearsal_json = to_style_performance_arc_stage_rehearsal_state_json(
        report.stage_rehearsal_state
    )
    return {
        "live_set_cockpit": {
            "selection_source": report.selection_source,
            "source_reference": report.source_reference,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "show_mode": report.show_mode,
            "scope": report.scope,
            "readiness": report.readiness,
            "cue_count": report.cue_count,
            "cockpit_status": report.cockpit_status,
            "stage_state": report.stage_state,
            "operator_mode": report.operator_mode,
            "overall_go_no_go": report.overall_go_no_go,
            "next_best_action": report.next_best_action,
            "launch_controls": list(report.launch_controls),
            "machine_panels": [_machine_panel_json(panel) for panel in report.machine_panels],
            "cue_cards": [_cue_card_json(card) for card in report.cue_cards],
            "recovery_controls": list(report.recovery_controls),
            "suggested_commands": list(report.suggested_commands),
        },
        "stage_rehearsal_state": rehearsal_json["stage_rehearsal_state"],
        "stage_snapshot_routing": rehearsal_json["stage_snapshot_routing"],
        "live_runbook": rehearsal_json["live_runbook"],
        "cue_sheet": rehearsal_json["cue_sheet"],
        "reference_match": rehearsal_json["reference_match"],
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
        report = build_style_performance_arc_live_set_cockpit_report(
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
                    to_style_performance_arc_live_set_cockpit_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_set_cockpit_report(
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


STYLE_PERFORMANCE_ARC_LIVE_SET_COCKPIT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-set-cockpit-report",
    summary="Build a passive live set cockpit from an arc or reference.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_SET_COCKPIT_CLI_COMMAND)

__all__ = [
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_SET_COCKPIT_CLI_COMMAND",
    "StylePerformanceArcLiveSetCockpitCueCard",
    "StylePerformanceArcLiveSetCockpitReport",
    "StylePerformanceArcLiveSetMachinePanel",
    "build_style_performance_arc_live_set_cockpit_from_rehearsal_state",
    "build_style_performance_arc_live_set_cockpit_report",
    "format_style_performance_arc_live_set_cockpit_report",
    "to_style_performance_arc_live_set_cockpit_json",
]
