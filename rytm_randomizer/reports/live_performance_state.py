"""Passive live performance state packet for style performance arcs."""

from __future__ import annotations

import hashlib
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
from .live_command_deck import (
    StylePerformanceArcLiveCommandDeckCue,
    StylePerformanceArcLiveCommandDeckReport,
    build_style_performance_arc_live_command_deck_report,
    to_style_performance_arc_live_command_deck_json,
)
from .live_show_export import StylePerformanceArcLiveShowMachineExport

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live state packet"
SOURCE_MODULE: Final[str] = "reports.live_performance_state"
STATE_PACKET_VERSION: Final[str] = "live-performance-state-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live state packet only",
    "composes live command deck only",
    "uses saved-kit snapshots when supplied",
    "Rytm rows are mock CC previews only",
    "Analog Four rows can remain candidate/deferred",
    "GUI-ready JSON/stdout only",
    "no file writing",
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
_DEFAULT_CUE_NUMBER: Final[int] = 1
_DEFAULT_LOOKAHEAD_COUNT: Final[int] = 1
_DEFAULT_EVENT_LIMIT: Final[int] = 24
_USAGE: Final[str] = (
    "style-performance-arc-live-state-report usage: "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--events] [--limit N] [--json]"
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
    "--cue",
    "--lookahead",
    "--events",
    "--limit",
    "--json",
)


@dataclass(frozen=True)
class StylePerformanceArcLiveStateCue:
    """One GUI-ready cue state for the passive live state packet."""

    cue_number: int
    cue_label: str
    time_window: str
    style_key: str
    phase: str
    status_light: str
    go_no_go: str
    screen_state: str
    operator_prompt: str
    primary_action: str
    secondary_action: str
    recovery_action: str
    listen_for: str
    machine_focus: str
    route_status: str
    blocker_summary: str
    warning_text: str
    passive_command: str
    event_preview_rows: tuple[str, ...]


@dataclass(frozen=True)
class StylePerformanceArcLiveStateMachine:
    """One machine panel state for future GUI/live routing."""

    machine: str
    label: str
    status: str
    status_light: str
    arm_state: str
    ui_badge: str
    handoff_label: str
    slot_summary: str
    kit_summary: str
    fingerprint_summary: str
    planned_units: tuple[int, ...]
    row_summary: str
    mock_row_count: int
    deferred_row_count: int
    operator_check: str


@dataclass(frozen=True)
class StylePerformanceArcLiveStateReport:
    """Passive GUI-ready state packet composed from a live command deck."""

    command_deck: StylePerformanceArcLiveCommandDeckReport
    state_version: str
    state_id: str
    screen_title: str
    screen_mode: str
    live_state: str
    current_cue: StylePerformanceArcLiveStateCue
    next_cues: tuple[StylePerformanceArcLiveStateCue, ...]
    machine_states: tuple[StylePerformanceArcLiveStateMachine, ...]
    action_bar: tuple[str, ...]
    warning_stack: tuple[str, ...]
    recovery_stack: tuple[str, ...]
    replay_commands: tuple[str, ...]
    suggested_commands: tuple[str, ...]

    @property
    def selection_source(self) -> str:
        """Return the selected source mode."""

        return self.command_deck.selection_source

    @property
    def source_reference(self) -> str | None:
        """Return the selected source reference when available."""

        return self.command_deck.source_reference

    @property
    def selected_arc_key(self) -> str:
        """Return the selected arc key."""

        return self.command_deck.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return the selected arc name."""

        return self.command_deck.selected_arc_name

    @property
    def show_mode(self) -> str:
        """Return the selected show-mode label."""

        return self.command_deck.show_mode

    @property
    def scope(self) -> str:
        """Return the selected machine scope."""

        return self.command_deck.scope

    @property
    def readiness(self) -> str:
        """Return the selected readiness label."""

        return self.command_deck.readiness

    @property
    def stage_state(self) -> str:
        """Return the upstream stage state."""

        return self.command_deck.stage_state

    @property
    def go_no_go(self) -> str:
        """Return the upstream aggregate go/no-go."""

        return self.command_deck.go_no_go


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


def _live_state(screen_mode: str) -> str:
    if screen_mode == "perform":
        return "ready"
    if screen_mode == "soundcheck":
        return "rehearsal"
    if screen_mode == "hold":
        return "blocked"
    return "review"


def _source_option(command_deck: StylePerformanceArcLiveCommandDeckReport) -> str:
    if command_deck.selection_source in {"arc", "description", "audio", "library"}:
        source_reference = command_deck.source_reference or command_deck.selected_arc_key
        return f"--{command_deck.selection_source} {powershell_literal_arg(source_reference)}"
    return f"--arc {command_deck.selected_arc_key}"


def _state_passive_command(
    command_deck: StylePerformanceArcLiveCommandDeckReport,
    cue: StylePerformanceArcLiveCommandDeckCue,
    *,
    lookahead_count: int,
) -> str:
    return (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-state-report "
        f"{_source_option(command_deck)} --scope {command_deck.scope} "
        f"--cue {cue.cue_number} --lookahead {lookahead_count} --events --limit 8"
    )


def _first_prefixed(values: Sequence[str], prefix: str, fallback: str) -> str:
    for value in values:
        if value.startswith(prefix):
            return value
    return fallback


def _warning_text(cue: StylePerformanceArcLiveCommandDeckCue) -> str:
    if cue.command_state == "perform":
        return "Green cue: arm only after human confirmation and moderate monitoring."
    if cue.command_state == "soundcheck":
        return "Amber cue: rehearse this state before considering any armed path."
    if cue.command_state == "hold":
        return "Red cue: do not arm; hold the current machine state and recover."
    return "Review cue: confirm blockers and machine states before performance use."


def _cue_state(
    command_deck: StylePerformanceArcLiveCommandDeckReport,
    cue: StylePerformanceArcLiveCommandDeckCue,
    *,
    lookahead_count: int,
) -> StylePerformanceArcLiveStateCue:
    primary_action = _first_prefixed(
        cue.launch_sequence,
        "Launch:",
        f"Launch: {cue.operator_prompt}",
    )
    secondary_action = _first_prefixed(
        cue.launch_sequence,
        "Hold:",
        f"Hold: {cue.hold_action}",
    )
    return StylePerformanceArcLiveStateCue(
        cue_number=cue.cue_number,
        cue_label=cue.cue_label,
        time_window=cue.time_window,
        style_key=cue.style_key,
        phase=cue.phase,
        status_light=cue.status_light,
        go_no_go=cue.go_no_go,
        screen_state=cue.command_state,
        operator_prompt=cue.operator_prompt,
        primary_action=primary_action,
        secondary_action=secondary_action,
        recovery_action=cue.recovery_action,
        listen_for=cue.listen_for,
        machine_focus=cue.machine_focus,
        route_status=cue.route_status,
        blocker_summary=cue.blocker_summary,
        warning_text=_warning_text(cue),
        passive_command=_state_passive_command(
            command_deck,
            cue,
            lookahead_count=lookahead_count,
        ),
        event_preview_rows=cue.event_preview_rows,
    )


def _machine_state(
    machine: StylePerformanceArcLiveShowMachineExport,
) -> StylePerformanceArcLiveStateMachine:
    return StylePerformanceArcLiveStateMachine(
        machine=machine.machine,
        label=machine.label,
        status=machine.status,
        status_light=machine.status_light,
        arm_state=machine.arm_state,
        ui_badge=f"{machine.status_light}:{machine.status_action}",
        handoff_label=f"{machine.label}: {machine.status_action}/{machine.arm_state}",
        slot_summary=machine.slot_summary,
        kit_summary=machine.kit_summary,
        fingerprint_summary=machine.fingerprint_summary,
        planned_units=machine.planned_units,
        row_summary=f"mock {machine.mock_row_count} | deferred {machine.deferred_row_count}",
        mock_row_count=machine.mock_row_count,
        deferred_row_count=machine.deferred_row_count,
        operator_check=machine.operator_check,
    )


def _state_id(
    command_deck: StylePerformanceArcLiveCommandDeckReport,
    current: StylePerformanceArcLiveStateCue,
    machines: Sequence[StylePerformanceArcLiveStateMachine],
) -> str:
    digest_input = "|".join(
        (
            command_deck.deck_id,
            current.screen_state,
            current.status_light,
            ",".join(f"{machine.machine}:{machine.ui_badge}" for machine in machines),
        )
    )
    digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:8]
    return f"{command_deck.deck_id}-state-{digest}"


def _action_bar(current: StylePerformanceArcLiveStateCue) -> tuple[str, ...]:
    return (
        f"Now: {current.primary_action}",
        f"Machine: {current.machine_focus}",
        f"Listen: {current.listen_for}",
        f"Recovery: {current.recovery_action}",
    )


def _warning_stack(
    current: StylePerformanceArcLiveStateCue,
    machines: Sequence[StylePerformanceArcLiveStateMachine],
) -> tuple[str, ...]:
    warnings = [current.warning_text]
    if current.blocker_summary and current.blocker_summary.lower() != "none":
        warnings.append(f"Blockers: {current.blocker_summary}")
    warnings.extend(
        f"{machine.label}: {machine.operator_check}"
        for machine in machines
        if machine.arm_state in {"do-not-arm", "rehearse"}
    )
    return tuple(warnings)


def _recovery_stack(current: StylePerformanceArcLiveStateCue) -> tuple[str, ...]:
    return (
        f"Recovery: {current.recovery_action}",
        f"Hold: {current.secondary_action}",
        "If anything feels wrong, keep the current machine state parked and use the rescue path.",
    )


def build_style_performance_arc_live_state_from_command_deck(
    command_deck: StylePerformanceArcLiveCommandDeckReport,
) -> StylePerformanceArcLiveStateReport:
    """Build a passive GUI-ready state packet from a live command deck."""

    lookahead_count = len(command_deck.lookahead_cues)
    current = _cue_state(
        command_deck,
        command_deck.current_cue,
        lookahead_count=lookahead_count,
    )
    next_cues = tuple(
        _cue_state(
            command_deck,
            cue,
            lookahead_count=lookahead_count,
        )
        for cue in command_deck.lookahead_cues
    )
    machines = tuple(
        _machine_state(machine)
        for machine in command_deck.timeline.live_show_export.machine_exports
    )
    state_command = (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-state-report "
        f"{_source_option(command_deck)} --scope {command_deck.scope} "
        f"--cue {command_deck.current_cue_number} "
        f"--lookahead {lookahead_count} --events --limit 8"
    )
    return StylePerformanceArcLiveStateReport(
        command_deck=command_deck,
        state_version=STATE_PACKET_VERSION,
        state_id=_state_id(command_deck, current, machines),
        screen_title=f"Cue {command_deck.current_cue_number} live state",
        screen_mode=current.screen_state,
        live_state=_live_state(current.screen_state),
        current_cue=current,
        next_cues=next_cues,
        machine_states=machines,
        action_bar=_action_bar(current),
        warning_stack=_warning_stack(current, machines),
        recovery_stack=_recovery_stack(current),
        replay_commands=(
            state_command,
            current.passive_command,
            command_deck.current_cue.passive_command,
        ),
        suggested_commands=(
            state_command,
            *command_deck.suggested_commands,
        ),
    )


def build_style_performance_arc_live_state_report(
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
    cue_number: int = _DEFAULT_CUE_NUMBER,
    lookahead_count: int = _DEFAULT_LOOKAHEAD_COUNT,
) -> StylePerformanceArcLiveStateReport:
    """Build a passive live state packet from an arc or reference."""

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
        raise ValueError("live state packet requires exactly one selection source")

    command_deck = build_style_performance_arc_live_command_deck_report(
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
        cue_number=cue_number,
        lookahead_count=lookahead_count,
    )
    return build_style_performance_arc_live_state_from_command_deck(command_deck)


def _limited_event_rows(rows: Sequence[str], *, event_limit: int) -> tuple[str, ...]:
    if event_limit == 0:
        return tuple(rows)
    return tuple(rows[:event_limit])


def _number_sequence(values: Sequence[int]) -> str:
    if not values:
        return "none"
    return ", ".join(str(value) for value in values)


def _cue_lines(
    cue: StylePerformanceArcLiveStateCue,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    lines = [
        f"- {cue.cue_label}. {cue.time_window} | {cue.style_key} | {cue.status_light}",
        f"  Screen state: {cue.screen_state}",
        f"  Phase: {cue.phase}",
        f"  Go / no-go: {cue.go_no_go}",
        f"  Prompt: {cue.operator_prompt}",
        f"  Primary: {cue.primary_action}",
        f"  Secondary: {cue.secondary_action}",
        f"  Listen for: {cue.listen_for}",
        f"  Machine focus: {cue.machine_focus}",
        f"  Route: {cue.route_status}",
        f"  Blockers: {cue.blocker_summary}",
        f"  Warning: {cue.warning_text}",
        f"  Recovery: {cue.recovery_action}",
        f"  Passive command: {cue.passive_command}",
    ]
    if include_events:
        lines.append("  Cue event preview:")
        if not cue.event_preview_rows:
            lines.append("  - No mock rows available because the selected preview is not ready.")
        else:
            rows = _limited_event_rows(cue.event_preview_rows, event_limit=event_limit)
            if len(rows) == len(cue.event_preview_rows):
                lines.append("  - Showing all events")
            else:
                lines.append(f"  - Showing first {event_limit} of {len(cue.event_preview_rows)}")
            lines.extend(f"  {row}" for row in rows)
    return lines


def _machine_lines(machine: StylePerformanceArcLiveStateMachine) -> list[str]:
    return [
        f"- {machine.label}: {machine.ui_badge} | {machine.status} | {machine.arm_state}",
        f"  Handoff: {machine.handoff_label}",
        f"  Slot(s): {machine.slot_summary}",
        f"  Kit(s): {machine.kit_summary}",
        f"  Fingerprint(s): {machine.fingerprint_summary}",
        f"  Planned units: {_number_sequence(machine.planned_units)}",
        f"  Rows: {machine.row_summary}",
        f"  Check: {machine.operator_check}",
    ]


def format_style_performance_arc_live_state_report(
    report: StylePerformanceArcLiveStateReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic live state packet lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    lines = [
        "Live state summary:",
        f"- State version: {report.state_version}",
        f"- State id: {report.state_id}",
        f"- Command deck id: {report.command_deck.deck_id}",
        f"- Timeline id: {report.command_deck.timeline.timeline_id}",
        f"- Selection source: {report.selection_source}",
        f"- Source reference: {report.source_reference}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Show mode: {report.show_mode}",
        f"- Scope: {report.scope}",
        f"- Readiness: {report.readiness}",
        f"- Stage state: {report.stage_state}",
        f"- Go / no-go: {report.go_no_go}",
        f"- Screen title: {report.screen_title}",
        f"- Screen mode: {report.screen_mode}",
        f"- Live state: {report.live_state}",
        f"- Current cue: {report.current_cue.cue_number}",
        f"- Next cue count: {len(report.next_cues)}",
        "Current GUI state:",
        *_cue_lines(
            report.current_cue,
            include_events=include_events,
            event_limit=event_limit,
        ),
        "Next cue strip:",
    ]
    if not report.next_cues:
        lines.append("- No next cues requested.")
    else:
        for cue in report.next_cues:
            lines.extend(
                _cue_lines(
                    cue,
                    include_events=include_events,
                    event_limit=event_limit,
                )
            )
    lines.append("Machine state panels:")
    if not report.machine_states:
        lines.append("- No machine states available.")
    else:
        for machine in report.machine_states:
            lines.extend(_machine_lines(machine))
    lines.extend(
        [
            "Action bar:",
            *[f"- {action}" for action in report.action_bar],
            "Warning stack:",
            *[f"- {warning}" for warning in report.warning_stack],
            "Recovery stack:",
            *[f"- {recovery}" for recovery in report.recovery_stack],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.replay_commands],
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


def _cue_json(cue: StylePerformanceArcLiveStateCue) -> dict[str, object]:
    return {
        "cue_number": cue.cue_number,
        "cue_label": cue.cue_label,
        "time_window": cue.time_window,
        "style_key": cue.style_key,
        "phase": cue.phase,
        "status_light": cue.status_light,
        "go_no_go": cue.go_no_go,
        "screen_state": cue.screen_state,
        "operator_prompt": cue.operator_prompt,
        "primary_action": cue.primary_action,
        "secondary_action": cue.secondary_action,
        "recovery_action": cue.recovery_action,
        "listen_for": cue.listen_for,
        "machine_focus": cue.machine_focus,
        "route_status": cue.route_status,
        "blocker_summary": cue.blocker_summary,
        "warning_text": cue.warning_text,
        "passive_command": cue.passive_command,
        "event_preview_rows": list(cue.event_preview_rows),
    }


def _machine_json(machine: StylePerformanceArcLiveStateMachine) -> dict[str, object]:
    return {
        "machine": machine.machine,
        "label": machine.label,
        "status": machine.status,
        "status_light": machine.status_light,
        "arm_state": machine.arm_state,
        "ui_badge": machine.ui_badge,
        "handoff_label": machine.handoff_label,
        "slot_summary": machine.slot_summary,
        "kit_summary": machine.kit_summary,
        "fingerprint_summary": machine.fingerprint_summary,
        "planned_units": list(machine.planned_units),
        "row_summary": machine.row_summary,
        "mock_row_count": machine.mock_row_count,
        "deferred_row_count": machine.deferred_row_count,
        "operator_check": machine.operator_check,
    }


def to_style_performance_arc_live_state_json(
    report: StylePerformanceArcLiveStateReport,
) -> dict[str, object]:
    """Return deterministic JSON data for the live performance state packet."""

    deck_json = to_style_performance_arc_live_command_deck_json(report.command_deck)
    return {
        "live_state_packet": {
            "state_version": report.state_version,
            "state_id": report.state_id,
            "screen_title": report.screen_title,
            "screen_mode": report.screen_mode,
            "live_state": report.live_state,
            "selection_source": report.selection_source,
            "source_reference": report.source_reference,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "show_mode": report.show_mode,
            "scope": report.scope,
            "readiness": report.readiness,
            "stage_state": report.stage_state,
            "go_no_go": report.go_no_go,
            "current_cue": _cue_json(report.current_cue),
            "next_cues": [_cue_json(cue) for cue in report.next_cues],
            "machine_states": [_machine_json(machine) for machine in report.machine_states],
            "action_bar": list(report.action_bar),
            "warning_stack": list(report.warning_stack),
            "recovery_stack": list(report.recovery_stack),
            "replay_commands": list(report.replay_commands),
            "suggested_commands": list(report.suggested_commands),
        },
        "live_command_deck": deck_json["live_command_deck"],
        "live_transition_timeline": deck_json["live_transition_timeline"],
        "live_show_export": deck_json["live_show_export"],
        "live_set_cockpit": deck_json["live_set_cockpit"],
        "stage_rehearsal_state": deck_json["stage_rehearsal_state"],
        "stage_snapshot_routing": deck_json["stage_snapshot_routing"],
        "live_runbook": deck_json["live_runbook"],
        "cue_sheet": deck_json["cue_sheet"],
        "reference_match": deck_json["reference_match"],
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
    cue_number = _DEFAULT_CUE_NUMBER
    lookahead_count = _DEFAULT_LOOKAHEAD_COUNT
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
        elif option == "--cue":
            cue_number = _parse_positive_int(value, option=option)
        elif option == "--lookahead":
            lookahead_count = _parse_nonnegative_int(value, option=option)
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
        "cue_number": cue_number,
        "lookahead_count": lookahead_count,
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
    cue_number: int,
    lookahead_count: int,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_state_report(
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
            cue_number=cue_number,
            lookahead_count=lookahead_count,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_state_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_state_report(
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


STYLE_PERFORMANCE_ARC_LIVE_STATE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-state-report",
    summary="Build a passive live performance state packet from an arc or reference.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_STATE_CLI_COMMAND)

__all__ = [
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STATE_PACKET_VERSION",
    "STYLE_PERFORMANCE_ARC_LIVE_STATE_CLI_COMMAND",
    "StylePerformanceArcLiveStateCue",
    "StylePerformanceArcLiveStateMachine",
    "StylePerformanceArcLiveStateReport",
    "build_style_performance_arc_live_state_from_command_deck",
    "build_style_performance_arc_live_state_report",
    "format_style_performance_arc_live_state_report",
    "to_style_performance_arc_live_state_json",
]
