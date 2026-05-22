"""Passive live stage rehearsal-state report for style performance arcs."""

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
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)
from .live_stage_snapshot_routing import (
    StylePerformanceArcStageSnapshotRouteCard,
    StylePerformanceArcStageSnapshotRoutingReport,
    build_style_performance_arc_stage_snapshot_routing_report,
    to_style_performance_arc_stage_snapshot_routing_json,
)
from .style_performance_arcs import StylePerformanceArcReferenceMatchReport

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc stage rehearsal state"
SOURCE_MODULE: Final[str] = "reports.live_stage_rehearsal_state"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "rehearsal state packet only",
    "transforms stage routing route cards only",
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
    "style-performance-arc-stage-rehearsal-state-report usage: "
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
REHEARSAL_STEPS: Final[tuple[str, ...]] = (
    "Run the passive stage routing report and confirm saved-kit slots before arming.",
    "Practice the listed cue moves with the sequencer running and monitor levels.",
    "Treat rehearse cues as soundcheck-only until deferred/candidate rows are resolved.",
    "Keep S5 -> Z -> Q ready as the recovery sequence.",
)


@dataclass(frozen=True)
class StylePerformanceArcStageRehearsalMachineState:
    """One passive machine state for a cue or report aggregate."""

    machine: str
    label: str
    status: str
    slot: int | None
    kit_name: str | None
    payload_fingerprint: str | None
    planned_units: tuple[int, ...]
    mock_row_count: int
    deferred_row_count: int
    operator_check: str


@dataclass(frozen=True)
class StylePerformanceArcStageRehearsalCueState:
    """One cue-level rehearsal decision derived from a stage route card."""

    cue_number: int
    time_window: str
    style_key: str
    machine_focus: str
    readiness: str
    route_status: str
    risk_level: str
    go_no_go: str
    stage_state: str
    operator_prompt: str
    listen_for: str
    recovery_action: str
    blocker_summary: str
    planned_rytm_pads: tuple[int, ...]
    planned_analog_four_tracks: tuple[int, ...]
    event_row_count: int
    mock_message_count: int
    deferred_row_count: int
    rytm_state: StylePerformanceArcStageRehearsalMachineState
    analog_four_state: StylePerformanceArcStageRehearsalMachineState
    event_preview_rows: tuple[str, ...]
    deferred_rows: tuple[str, ...]
    route_card: StylePerformanceArcStageSnapshotRouteCard


@dataclass(frozen=True)
class StylePerformanceArcStageRehearsalStateReport:
    """Passive stage rehearsal-state packet for one selected live arc."""

    stage_routing: StylePerformanceArcStageSnapshotRoutingReport
    cue_states: tuple[StylePerformanceArcStageRehearsalCueState, ...]
    machine_states: tuple[StylePerformanceArcStageRehearsalMachineState, ...]
    rehearsal_steps: tuple[str, ...]
    suggested_commands: tuple[str, ...]
    overall_go_no_go: str
    stage_state: str

    @property
    def selection_source(self) -> str:
        """Return the selected source mode."""

        return self.stage_routing.selection_source

    @property
    def source_reference(self) -> str | None:
        """Return the selected source reference when available."""

        return self.stage_routing.source_reference

    @property
    def reference_match(self) -> StylePerformanceArcReferenceMatchReport | None:
        """Return the upstream reference match when the route came from a reference."""

        return self.stage_routing.reference_match

    @property
    def selected_arc_key(self) -> str:
        """Return the selected arc key."""

        return self.stage_routing.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return the selected arc name."""

        return self.stage_routing.selected_arc_name

    @property
    def show_mode(self) -> str:
        """Return the selected show-mode label."""

        return self.stage_routing.show_mode

    @property
    def scope(self) -> str:
        """Return the selected machine scope."""

        return self.stage_routing.scope

    @property
    def readiness(self) -> str:
        """Return the stage-packet readiness."""

        return self.stage_routing.readiness

    @property
    def cue_count(self) -> int:
        """Return cue count."""

        return self.stage_routing.cue_count


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


def _machine_status(card: StylePerformanceArcStageSnapshotRouteCard, *, machine: str) -> str:
    if machine == "rytm":
        if card.rytm_slot is None:
            return "unchanged-by-scope"
        if card.route_status in {"blocked", "empty"} or card.rytm_mock_row_count == 0:
            return "blocked"
        return "loaded"
    if card.analog_four_slot is None:
        return "unchanged-by-scope"
    if card.analog_four_deferred_row_count > 0:
        return "candidate-deferred"
    if card.route_status in {"blocked", "empty"} or card.analog_four_mock_row_count == 0:
        return "blocked"
    return "loaded"


def _machine_state_for_card(
    card: StylePerformanceArcStageSnapshotRouteCard,
    *,
    machine: str,
) -> StylePerformanceArcStageRehearsalMachineState:
    if machine == "rytm":
        status = _machine_status(card, machine=machine)
        if status == "unchanged-by-scope":
            operator_check = "Leave Rytm unchanged for this scoped cue."
        elif status == "blocked":
            operator_check = "Do not arm Rytm for this cue until mock rows are available."
        else:
            operator_check = (
                f"Confirm Rytm kit slot {card.rytm_slot} and pads "
                f"{_number_sequence(card.planned_rytm_pads)}."
            )
        return StylePerformanceArcStageRehearsalMachineState(
            machine="rytm",
            label="Rytm",
            status=status,
            slot=card.rytm_slot,
            kit_name=card.rytm_kit_name,
            payload_fingerprint=card.rytm_payload_fingerprint,
            planned_units=card.planned_rytm_pads,
            mock_row_count=card.rytm_mock_row_count,
            deferred_row_count=0,
            operator_check=operator_check,
        )
    status = _machine_status(card, machine=machine)
    if status == "unchanged-by-scope":
        operator_check = "Leave Analog Four unchanged for this scoped cue."
    elif status == "candidate-deferred":
        operator_check = "Rehearse A4 candidate/deferred rows before armed use."
    elif status == "blocked":
        operator_check = "Do not arm Analog Four for this cue until rows are promoted."
    else:
        operator_check = (
            f"Confirm Analog Four kit slot {card.analog_four_slot} and tracks "
            f"{_number_sequence(card.planned_analog_four_tracks)}."
        )
    return StylePerformanceArcStageRehearsalMachineState(
        machine="analog-four",
        label="Analog Four",
        status=status,
        slot=card.analog_four_slot,
        kit_name=card.analog_four_kit_name,
        payload_fingerprint=card.analog_four_payload_fingerprint,
        planned_units=card.planned_analog_four_tracks,
        mock_row_count=card.analog_four_mock_row_count,
        deferred_row_count=card.analog_four_deferred_row_count,
        operator_check=operator_check,
    )


def _cue_go_no_go(
    card: StylePerformanceArcStageSnapshotRouteCard,
    *,
    rytm_state: StylePerformanceArcStageRehearsalMachineState,
    analog_four_state: StylePerformanceArcStageRehearsalMachineState,
) -> str:
    if card.route_status in {"blocked", "empty"}:
        return "do-not-arm"
    if rytm_state.status == "blocked" or analog_four_state.status == "blocked":
        return "do-not-arm"
    if card.deferred_row_count > 0 or analog_four_state.status == "candidate-deferred":
        return "rehearse"
    if card.route_status == "partial":
        return "rehearse"
    return "go"


def _stage_state(go_no_go: str) -> str:
    if go_no_go == "go":
        return "ready"
    if go_no_go == "rehearse":
        return "rehearsal-required"
    return "blocked"


def _operator_prompt(
    card: StylePerformanceArcStageSnapshotRouteCard,
    *,
    go_no_go: str,
) -> str:
    if go_no_go == "go":
        return f"Go cue {card.cue_number}: {card.operator_move}"
    if go_no_go == "rehearse":
        return (
            f"Rehearse cue {card.cue_number}: {card.operator_move}; "
            "resolve deferred/candidate rows before arming."
        )
    return f"Do not arm cue {card.cue_number}: {card.blocker_summary}"


def _cue_state_from_route_card(
    card: StylePerformanceArcStageSnapshotRouteCard,
) -> StylePerformanceArcStageRehearsalCueState:
    rytm_state = _machine_state_for_card(card, machine="rytm")
    analog_four_state = _machine_state_for_card(card, machine="analog-four")
    go_no_go = _cue_go_no_go(
        card,
        rytm_state=rytm_state,
        analog_four_state=analog_four_state,
    )
    return StylePerformanceArcStageRehearsalCueState(
        cue_number=card.cue_number,
        time_window=card.time_window,
        style_key=card.style_key,
        machine_focus=card.machine_focus,
        readiness=card.readiness,
        route_status=card.route_status,
        risk_level=card.risk_level,
        go_no_go=go_no_go,
        stage_state=_stage_state(go_no_go),
        operator_prompt=_operator_prompt(card, go_no_go=go_no_go),
        listen_for=card.listen_for,
        recovery_action=card.recovery_action,
        blocker_summary=card.blocker_summary,
        planned_rytm_pads=card.planned_rytm_pads,
        planned_analog_four_tracks=card.planned_analog_four_tracks,
        event_row_count=card.event_row_count,
        mock_message_count=card.mock_message_count,
        deferred_row_count=card.deferred_row_count,
        rytm_state=rytm_state,
        analog_four_state=analog_four_state,
        event_preview_rows=card.event_preview_rows,
        deferred_rows=card.deferred_rows,
        route_card=card,
    )


def _aggregate_status(states: Sequence[StylePerformanceArcStageRehearsalMachineState]) -> str:
    statuses = tuple(state.status for state in states)
    if not statuses:
        return "empty"
    if all(status == "unchanged-by-scope" for status in statuses):
        return "unchanged-by-scope"
    if "blocked" in statuses:
        return "blocked"
    if "candidate-deferred" in statuses:
        return "candidate-deferred"
    if "loaded" in statuses:
        return "loaded"
    return statuses[0]


def _unique_numbers(
    states: Sequence[StylePerformanceArcStageRehearsalMachineState],
) -> tuple[int, ...]:
    return tuple(sorted({unit for state in states for unit in state.planned_units}))


def _unique_strings(values: Sequence[str | None]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))


def _aggregate_machine_state(
    states: Sequence[StylePerformanceArcStageRehearsalMachineState],
    *,
    machine: str,
    label: str,
) -> StylePerformanceArcStageRehearsalMachineState:
    status = _aggregate_status(states)
    kit_names = _unique_strings(tuple(state.kit_name for state in states))
    fingerprints = _unique_strings(tuple(state.payload_fingerprint for state in states))
    if status == "unchanged-by-scope":
        operator_check = f"Leave {label} unchanged for the selected scope."
    elif status == "candidate-deferred":
        operator_check = f"Rehearse and promote {label} candidate/deferred rows before arming."
    elif status == "blocked":
        operator_check = f"Resolve {label} blocked cues before live use."
    else:
        operator_check = f"Confirm {label} saved-kit slots and planned units before arming."
    return StylePerformanceArcStageRehearsalMachineState(
        machine=machine,
        label=label,
        status=status,
        slot=None,
        kit_name=_string_sequence(kit_names),
        payload_fingerprint=_string_sequence(fingerprints),
        planned_units=_unique_numbers(states),
        mock_row_count=sum(state.mock_row_count for state in states),
        deferred_row_count=sum(state.deferred_row_count for state in states),
        operator_check=operator_check,
    )


def _machine_states_from_cues(
    cue_states: Sequence[StylePerformanceArcStageRehearsalCueState],
) -> tuple[StylePerformanceArcStageRehearsalMachineState, ...]:
    return (
        _aggregate_machine_state(
            tuple(cue.rytm_state for cue in cue_states),
            machine="rytm",
            label="Rytm",
        ),
        _aggregate_machine_state(
            tuple(cue.analog_four_state for cue in cue_states),
            machine="analog-four",
            label="Analog Four",
        ),
    )


def _overall_go_no_go(
    cue_states: Sequence[StylePerformanceArcStageRehearsalCueState],
) -> str:
    cue_statuses = tuple(cue.go_no_go for cue in cue_states)
    if not cue_statuses or "do-not-arm" in cue_statuses:
        return "do-not-arm"
    if "rehearse" in cue_statuses:
        return "rehearse"
    return "go"


def _rehearsal_command(report: StylePerformanceArcStageSnapshotRoutingReport) -> str:
    source = report.source_reference or report.selected_arc_key
    if report.selection_source == "arc":
        selector = f"--arc {powershell_literal_arg(source)}"
    elif report.selection_source == "description":
        selector = f"--description {powershell_literal_arg(source)}"
    elif report.selection_source == "feature-report":
        selector = f"--description {powershell_literal_arg(report.selected_arc_name)}"
    elif report.selection_source == "audio":
        selector = f"--audio {powershell_literal_arg(source)}"
    else:
        selector = f"--library {powershell_literal_arg(source)}"
    return (
        "python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report "
        f"{selector} --scope {report.scope} --events --limit 8"
    )


def build_style_performance_arc_stage_rehearsal_state_from_stage_routing(
    stage_routing: StylePerformanceArcStageSnapshotRoutingReport,
) -> StylePerformanceArcStageRehearsalStateReport:
    """Return a rehearsal-state report from an existing stage-routing report."""

    cue_states = tuple(_cue_state_from_route_card(card) for card in stage_routing.route_cards)
    overall_go_no_go = _overall_go_no_go(cue_states)
    return StylePerformanceArcStageRehearsalStateReport(
        stage_routing=stage_routing,
        cue_states=cue_states,
        machine_states=_machine_states_from_cues(cue_states),
        rehearsal_steps=REHEARSAL_STEPS,
        suggested_commands=(
            _rehearsal_command(stage_routing),
            *stage_routing.suggested_commands,
        ),
        overall_go_no_go=overall_go_no_go,
        stage_state=_stage_state(overall_go_no_go),
    )


def build_style_performance_arc_stage_rehearsal_state_report(
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
) -> StylePerformanceArcStageRehearsalStateReport:
    """Return a passive stage rehearsal-state packet from a runbook source."""

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
        raise ValueError("stage rehearsal state requires exactly one selection source")

    stage_routing = build_style_performance_arc_stage_snapshot_routing_report(
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
    return build_style_performance_arc_stage_rehearsal_state_from_stage_routing(stage_routing)


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


def _machine_state_lines(
    state: StylePerformanceArcStageRehearsalMachineState,
    *,
    indent: str = "",
) -> list[str]:
    kit_name = state.kit_name or "none"
    fingerprint = state.payload_fingerprint or "none"
    return [
        (
            f"{indent}- {state.label}: {state.status} | units "
            f"{_number_sequence(state.planned_units)} | rows {state.mock_row_count} | "
            f"deferred {state.deferred_row_count}"
        ),
        f"{indent}  Kit(s): {kit_name}",
        f"{indent}  Fingerprint(s): {fingerprint}",
        f"{indent}  Check: {state.operator_check}",
    ]


def _cue_state_lines(
    cue: StylePerformanceArcStageRehearsalCueState,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    lines = [
        (f"- Cue {cue.cue_number}. {cue.time_window} | {cue.style_key} | " f"{cue.machine_focus}"),
        f"  Go / no-go: {cue.go_no_go}",
        f"  Stage state: {cue.stage_state}",
        f"  Readiness: {cue.readiness}",
        f"  Route status: {cue.route_status}",
        f"  Risk: {cue.risk_level}",
        f"  Operator prompt: {cue.operator_prompt}",
        f"  Listen for: {cue.listen_for}",
        f"  Recovery: {cue.recovery_action}",
        f"  Blockers: {cue.blocker_summary}",
        f"  Planned Rytm pads: {_number_sequence(cue.planned_rytm_pads)}",
        f"  Planned Analog Four tracks: {_number_sequence(cue.planned_analog_four_tracks)}",
        (
            "  Render rows: "
            f"{cue.event_row_count} event row(s), "
            f"{cue.mock_message_count} mock message(s), "
            f"{cue.deferred_row_count} deferred row(s)"
        ),
        "  Machine cue states:",
        *_machine_state_lines(cue.rytm_state, indent="  "),
        *_machine_state_lines(cue.analog_four_state, indent="  "),
        "  A4 deferred/candidate rows:",
        *[f"  {row}" for row in cue.deferred_rows],
        "  Rescue sequence: S5 -> Z -> Q",
    ]
    if include_events:
        lines.append("  Cue event preview:")
        if not cue.event_preview_rows:
            lines.append("  - No mock rows available because the selected preview is not ready.")
        else:
            selected_rows = _limited_event_rows(
                cue.event_preview_rows,
                event_limit=event_limit,
            )
            if len(selected_rows) == len(cue.event_preview_rows):
                lines.append("  - Showing all events")
            else:
                lines.append(
                    f"  - Showing first {event_limit} of {len(cue.event_preview_rows)} events"
                )
            lines.extend(f"  {row}" for row in selected_rows)
    return lines


def format_style_performance_arc_stage_rehearsal_state_report(
    report: StylePerformanceArcStageRehearsalStateReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic stage rehearsal-state lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    lines = [
        "Stage rehearsal summary:",
        f"- Selection source: {report.selection_source}",
        f"- Source reference: {report.source_reference}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Show mode: {report.show_mode}",
        f"- Scope: {report.scope}",
        f"- Readiness: {report.readiness}",
        f"- Cue count: {report.cue_count}",
        f"- Stage state: {report.stage_state}",
        f"- Go / no-go: {report.overall_go_no_go}",
        f"- Total event rows: {report.stage_routing.stage_packet.total_event_row_count}",
        f"- Total mock messages: {report.stage_routing.stage_packet.total_mock_message_count}",
        f"- Total deferred rows: {report.stage_routing.stage_packet.total_deferred_row_count}",
        *_reference_match_lines(report.reference_match),
        "Machine states:",
    ]
    for state in report.machine_states:
        lines.extend(_machine_state_lines(state))
    lines.extend(
        [
            "Rehearsal steps:",
            *[f"- {step}" for step in report.rehearsal_steps],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.suggested_commands],
            "Cue states:",
        ]
    )
    for cue in report.cue_states:
        lines.extend(
            _cue_state_lines(
                cue,
                include_events=include_events,
                event_limit=event_limit,
            )
        )
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return passive_report_lines(_HEADER, lines)


def _machine_state_json(
    state: StylePerformanceArcStageRehearsalMachineState,
) -> dict[str, object]:
    return {
        "machine": state.machine,
        "label": state.label,
        "status": state.status,
        "slot": state.slot,
        "kit_name": state.kit_name,
        "payload_fingerprint": state.payload_fingerprint,
        "planned_units": list(state.planned_units),
        "mock_row_count": state.mock_row_count,
        "deferred_row_count": state.deferred_row_count,
        "operator_check": state.operator_check,
    }


def _cue_state_json(cue: StylePerformanceArcStageRehearsalCueState) -> dict[str, object]:
    return {
        "cue_number": cue.cue_number,
        "time_window": cue.time_window,
        "style_key": cue.style_key,
        "machine_focus": cue.machine_focus,
        "readiness": cue.readiness,
        "route_status": cue.route_status,
        "risk_level": cue.risk_level,
        "go_no_go": cue.go_no_go,
        "stage_state": cue.stage_state,
        "operator_prompt": cue.operator_prompt,
        "listen_for": cue.listen_for,
        "recovery_action": cue.recovery_action,
        "blocker_summary": cue.blocker_summary,
        "planned_rytm_pads": list(cue.planned_rytm_pads),
        "planned_analog_four_tracks": list(cue.planned_analog_four_tracks),
        "event_row_count": cue.event_row_count,
        "mock_message_count": cue.mock_message_count,
        "deferred_row_count": cue.deferred_row_count,
        "rytm": _machine_state_json(cue.rytm_state),
        "analog_four": _machine_state_json(cue.analog_four_state),
        "event_preview_rows": list(cue.event_preview_rows),
        "deferred_rows": list(cue.deferred_rows),
    }


def to_style_performance_arc_stage_rehearsal_state_json(
    report: StylePerformanceArcStageRehearsalStateReport,
) -> dict[str, object]:
    """Return deterministic JSON data for stage rehearsal state."""

    routing_json = to_style_performance_arc_stage_snapshot_routing_json(report.stage_routing)
    return {
        "stage_rehearsal_state": {
            "selection_source": report.selection_source,
            "source_reference": report.source_reference,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "show_mode": report.show_mode,
            "scope": report.scope,
            "readiness": report.readiness,
            "cue_count": report.cue_count,
            "stage_state": report.stage_state,
            "overall_go_no_go": report.overall_go_no_go,
            "rehearsal_steps": list(report.rehearsal_steps),
            "suggested_commands": list(report.suggested_commands),
            "machine_states": [_machine_state_json(state) for state in report.machine_states],
            "cue_states": [_cue_state_json(cue) for cue in report.cue_states],
        },
        "stage_snapshot_routing": routing_json["stage_snapshot_routing"],
        "live_runbook": routing_json["live_runbook"],
        "cue_sheet": routing_json["cue_sheet"],
        "reference_match": routing_json["reference_match"],
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
        report = build_style_performance_arc_stage_rehearsal_state_report(
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
                    to_style_performance_arc_stage_rehearsal_state_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_stage_rehearsal_state_report(
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


STYLE_PERFORMANCE_ARC_STAGE_REHEARSAL_STATE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-stage-rehearsal-state-report",
    summary="Build passive stage rehearsal state from an arc or reference.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_STAGE_REHEARSAL_STATE_CLI_COMMAND)

__all__ = [
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_STAGE_REHEARSAL_STATE_CLI_COMMAND",
    "StylePerformanceArcStageRehearsalCueState",
    "StylePerformanceArcStageRehearsalMachineState",
    "StylePerformanceArcStageRehearsalStateReport",
    "build_style_performance_arc_stage_rehearsal_state_from_stage_routing",
    "build_style_performance_arc_stage_rehearsal_state_report",
    "format_style_performance_arc_stage_rehearsal_state_report",
    "to_style_performance_arc_stage_rehearsal_state_json",
]
