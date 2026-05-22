"""Passive live command deck for style performance arcs."""

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
from .live_transition_timeline import (
    StylePerformanceArcLiveTransitionCard,
    StylePerformanceArcLiveTransitionTimelineReport,
    build_style_performance_arc_live_transition_timeline_report,
    to_style_performance_arc_live_transition_timeline_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live command deck"
SOURCE_MODULE: Final[str] = "reports.live_command_deck"
DECK_VERSION: Final[str] = "live-command-deck-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live command deck only",
    "composes live transition timeline only",
    "uses saved-kit snapshots when supplied",
    "Rytm rows are mock CC previews only",
    "Analog Four rows can remain candidate/deferred",
    "JSON/stdout only",
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
    "style-performance-arc-live-command-deck-report usage: "
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
class StylePerformanceArcLiveCommandDeckCue:
    """One operator-ready command card for the live command deck."""

    source_transition_card: StylePerformanceArcLiveTransitionCard
    source_transition_number: int
    cue_number: int
    cue_label: str
    time_window: str
    style_key: str
    phase: str
    status_light: str
    go_no_go: str
    command_state: str
    operator_prompt: str
    prep_actions: tuple[str, ...]
    launch_sequence: tuple[str, ...]
    hold_action: str
    recovery_action: str
    listen_for: str
    machine_focus: str
    machine_handoff: str
    route_status: str
    blocker_summary: str
    passive_command: str
    event_preview_rows: tuple[str, ...]


@dataclass(frozen=True)
class StylePerformanceArcLiveCommandDeckReport:
    """Passive current-cue command deck composed from a transition timeline."""

    timeline: StylePerformanceArcLiveTransitionTimelineReport
    deck_version: str
    deck_id: str
    current_cue_number: int
    current_cue: StylePerformanceArcLiveCommandDeckCue
    lookahead_cues: tuple[StylePerformanceArcLiveCommandDeckCue, ...]
    stage_state: str
    go_no_go: str
    operator_mode: str
    headline_prompt: str
    launch_sequence: tuple[str, ...]
    machine_handoff: tuple[str, ...]
    recovery_controls: tuple[str, ...]
    suggested_commands: tuple[str, ...]

    @property
    def selection_source(self) -> str:
        """Return the selected source mode."""

        return self.timeline.selection_source

    @property
    def source_reference(self) -> str | None:
        """Return the selected source reference when available."""

        return self.timeline.source_reference

    @property
    def selected_arc_key(self) -> str:
        """Return the selected arc key."""

        return self.timeline.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return the selected arc name."""

        return self.timeline.selected_arc_name

    @property
    def show_mode(self) -> str:
        """Return the selected show-mode label."""

        return self.timeline.show_mode

    @property
    def scope(self) -> str:
        """Return the selected machine scope."""

        return self.timeline.scope

    @property
    def readiness(self) -> str:
        """Return the selected readiness label."""

        return self.timeline.readiness


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


def _to_command_state(go_no_go: str) -> str:
    if go_no_go == "go":
        return "perform"
    if go_no_go == "rehearse":
        return "soundcheck"
    if go_no_go == "do-not-arm":
        return "hold"
    return "review"


def _source_option(timeline: StylePerformanceArcLiveTransitionTimelineReport) -> str:
    if timeline.selection_source in {"arc", "description", "audio", "library"}:
        source_reference = timeline.source_reference or timeline.selected_arc_key
        return f"--{timeline.selection_source} {powershell_literal_arg(source_reference)}"
    return f"--arc {timeline.selected_arc_key}"


def _operator_prompt(card: StylePerformanceArcLiveTransitionCard, command_state: str) -> str:
    if command_state == "perform":
        return f"Cue {card.cue_number} is green: prep, listen, then launch only on purpose."
    if command_state == "soundcheck":
        return f"Cue {card.cue_number} is amber: rehearse the move before any active path."
    if command_state == "hold":
        return f"Cue {card.cue_number} is red: hold current state and recover."
    return f"Cue {card.cue_number} needs review before it becomes a performance move."


def _cue_passive_command(
    timeline: StylePerformanceArcLiveTransitionTimelineReport,
    card: StylePerformanceArcLiveTransitionCard,
    *,
    lookahead_count: int,
) -> str:
    return (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-command-deck-report "
        f"{_source_option(timeline)} --scope {timeline.scope} "
        f"--cue {card.cue_number} --lookahead {lookahead_count} --events --limit 8"
    )


def _deck_cue(
    timeline: StylePerformanceArcLiveTransitionTimelineReport,
    card: StylePerformanceArcLiveTransitionCard,
    *,
    lookahead_count: int,
) -> StylePerformanceArcLiveCommandDeckCue:
    command_state = _to_command_state(card.go_no_go)
    launch_sequence = (
        f"Review {card.cue_label} at {card.time_window}.",
        *card.prep_actions,
        f"Launch: {card.launch_action}",
        f"Hold: {card.hold_action}",
        f"Listen for: {card.listen_for}",
    )
    return StylePerformanceArcLiveCommandDeckCue(
        source_transition_card=card,
        source_transition_number=card.transition_number,
        cue_number=card.cue_number,
        cue_label=card.cue_label,
        time_window=card.time_window,
        style_key=card.style_key,
        phase=card.phase,
        status_light=card.status_light,
        go_no_go=card.go_no_go,
        command_state=command_state,
        operator_prompt=_operator_prompt(card, command_state),
        prep_actions=card.prep_actions,
        launch_sequence=launch_sequence,
        hold_action=card.hold_action,
        recovery_action=card.recover_action,
        listen_for=card.listen_for,
        machine_focus=card.machine_focus,
        machine_handoff=card.machine_handoff,
        route_status=card.route_status,
        blocker_summary=card.blocker_summary,
        passive_command=_cue_passive_command(
            timeline,
            card,
            lookahead_count=lookahead_count,
        ),
        event_preview_rows=card.event_preview_rows,
    )


def _deck_id(
    timeline: StylePerformanceArcLiveTransitionTimelineReport,
    current: StylePerformanceArcLiveCommandDeckCue,
    lookahead: Sequence[StylePerformanceArcLiveCommandDeckCue],
) -> str:
    digest_input = "|".join(
        (
            timeline.timeline_id,
            str(current.cue_number),
            current.command_state,
            ",".join(str(cue.cue_number) for cue in lookahead),
        )
    )
    digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:8]
    return f"{timeline.timeline_id}-cue{current.cue_number:02d}-{digest}"


def _operator_mode(current: StylePerformanceArcLiveCommandDeckCue) -> str:
    return current.command_state


def _headline_prompt(current: StylePerformanceArcLiveCommandDeckCue) -> str:
    return current.operator_prompt


def _machine_handoff_rows(current: StylePerformanceArcLiveCommandDeckCue) -> tuple[str, ...]:
    return (
        f"Focus: {current.machine_focus}",
        f"Handoff: {current.machine_handoff}",
        f"Route: {current.route_status}",
        f"Blockers: {current.blocker_summary}",
    )


def _recovery_controls(current: StylePerformanceArcLiveCommandDeckCue) -> tuple[str, ...]:
    return (
        f"Cue {current.cue_number} recovery: {current.recovery_action}",
        f"Cue {current.cue_number} hold: {current.hold_action}",
        "If any card reads do-not-arm, do not arm it; hold the current machine state.",
    )


def build_style_performance_arc_live_command_deck_from_timeline(
    timeline: StylePerformanceArcLiveTransitionTimelineReport,
    *,
    cue_number: int = _DEFAULT_CUE_NUMBER,
    lookahead_count: int = _DEFAULT_LOOKAHEAD_COUNT,
) -> StylePerformanceArcLiveCommandDeckReport:
    """Build a passive current-cue command deck from an existing transition timeline."""

    if cue_number < 1 or cue_number > len(timeline.transition_cards):
        raise ValueError(f"cue must be between 1 and {len(timeline.transition_cards)}")
    if lookahead_count < 0:
        raise ValueError("lookahead_count must be >= 0")

    current_card = timeline.transition_cards[cue_number - 1]
    current_cue = _deck_cue(
        timeline,
        current_card,
        lookahead_count=lookahead_count,
    )
    lookahead_cards = timeline.transition_cards[cue_number : cue_number + lookahead_count]
    lookahead_cues = tuple(
        _deck_cue(
            timeline,
            card,
            lookahead_count=lookahead_count,
        )
        for card in lookahead_cards
    )
    suggested_command = (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-command-deck-report "
        f"{_source_option(timeline)} --scope {timeline.scope} "
        f"--cue {cue_number} --lookahead {lookahead_count} --events --limit 8"
    )
    return StylePerformanceArcLiveCommandDeckReport(
        timeline=timeline,
        deck_version=DECK_VERSION,
        deck_id=_deck_id(timeline, current_cue, lookahead_cues),
        current_cue_number=cue_number,
        current_cue=current_cue,
        lookahead_cues=lookahead_cues,
        stage_state=timeline.stage_state,
        go_no_go=timeline.go_no_go,
        operator_mode=_operator_mode(current_cue),
        headline_prompt=_headline_prompt(current_cue),
        launch_sequence=(
            f"Confirm current cue {cue_number}: {current_cue.phase} / {current_cue.go_no_go}.",
            *current_cue.launch_sequence,
        ),
        machine_handoff=_machine_handoff_rows(current_cue),
        recovery_controls=_recovery_controls(current_cue),
        suggested_commands=(
            suggested_command,
            current_cue.passive_command,
            *timeline.suggested_commands,
        ),
    )


def build_style_performance_arc_live_command_deck_report(
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
) -> StylePerformanceArcLiveCommandDeckReport:
    """Build a passive live command deck from an arc or reference."""

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
        raise ValueError("live command deck requires exactly one selection source")

    timeline = build_style_performance_arc_live_transition_timeline_report(
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
    return build_style_performance_arc_live_command_deck_from_timeline(
        timeline,
        cue_number=cue_number,
        lookahead_count=lookahead_count,
    )


def _limited_event_rows(rows: Sequence[str], *, event_limit: int) -> tuple[str, ...]:
    if event_limit == 0:
        return tuple(rows)
    return tuple(rows[:event_limit])


def _cue_lines(
    cue: StylePerformanceArcLiveCommandDeckCue,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    lines = [
        f"- {cue.cue_label}. {cue.time_window} | {cue.style_key} | {cue.status_light}",
        f"  Command state: {cue.command_state}",
        f"  Phase: {cue.phase}",
        f"  Go / no-go: {cue.go_no_go}",
        f"  Operator prompt: {cue.operator_prompt}",
        "  Prep actions:",
        *[f"  - {action}" for action in cue.prep_actions],
        "  Launch sequence:",
        *[f"  - {step}" for step in cue.launch_sequence],
        f"  Hold: {cue.hold_action}",
        f"  Listen for: {cue.listen_for}",
        f"  Machine focus: {cue.machine_focus}",
        f"  Machine handoff: {cue.machine_handoff}",
        f"  Route: {cue.route_status}",
        f"  Blockers: {cue.blocker_summary}",
        f"  Recovery: {cue.recovery_action}",
        f"  Passive command: {cue.passive_command}",
    ]
    if include_events:
        lines.append("  Cue event preview:")
        if not cue.event_preview_rows:
            lines.append(
                "  - No mock rows available because the selected cue has no ready preview."
            )
        else:
            rows = _limited_event_rows(cue.event_preview_rows, event_limit=event_limit)
            if len(rows) == len(cue.event_preview_rows):
                lines.append("  - Showing all events")
            else:
                lines.append(f"  - Showing first {event_limit} of {len(cue.event_preview_rows)}")
            lines.extend(f"  {row}" for row in rows)
    return lines


def format_style_performance_arc_live_command_deck_report(
    report: StylePerformanceArcLiveCommandDeckReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic live command deck lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    lines = [
        "Command deck summary:",
        f"- Deck version: {report.deck_version}",
        f"- Deck id: {report.deck_id}",
        f"- Timeline id: {report.timeline.timeline_id}",
        f"- Selection source: {report.selection_source}",
        f"- Source reference: {report.source_reference}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Show mode: {report.show_mode}",
        f"- Scope: {report.scope}",
        f"- Readiness: {report.readiness}",
        f"- Stage state: {report.stage_state}",
        f"- Go / no-go: {report.go_no_go}",
        f"- Operator mode: {report.operator_mode}",
        f"- Current cue: {report.current_cue_number}",
        f"- Lookahead count: {len(report.lookahead_cues)}",
        f"- Headline: {report.headline_prompt}",
        "Now cue:",
        *_cue_lines(
            report.current_cue,
            include_events=include_events,
            event_limit=event_limit,
        ),
        "Lookahead cues:",
    ]
    if not report.lookahead_cues:
        lines.append("- No lookahead cues requested.")
    else:
        for cue in report.lookahead_cues:
            lines.extend(
                _cue_lines(
                    cue,
                    include_events=include_events,
                    event_limit=event_limit,
                )
            )
    lines.extend(
        [
            "Launch sequence:",
            *[f"- {step}" for step in report.launch_sequence],
            "Machine handoff:",
            *[f"- {row}" for row in report.machine_handoff],
            "Recovery controls:",
            *[f"- {row}" for row in report.recovery_controls],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.suggested_commands],
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


def _cue_json(cue: StylePerformanceArcLiveCommandDeckCue) -> dict[str, object]:
    return {
        "source_transition_number": cue.source_transition_number,
        "cue_number": cue.cue_number,
        "cue_label": cue.cue_label,
        "time_window": cue.time_window,
        "style_key": cue.style_key,
        "phase": cue.phase,
        "status_light": cue.status_light,
        "go_no_go": cue.go_no_go,
        "command_state": cue.command_state,
        "operator_prompt": cue.operator_prompt,
        "prep_actions": list(cue.prep_actions),
        "launch_sequence": list(cue.launch_sequence),
        "hold_action": cue.hold_action,
        "recovery_action": cue.recovery_action,
        "listen_for": cue.listen_for,
        "machine_focus": cue.machine_focus,
        "machine_handoff": cue.machine_handoff,
        "route_status": cue.route_status,
        "blocker_summary": cue.blocker_summary,
        "passive_command": cue.passive_command,
        "event_preview_rows": list(cue.event_preview_rows),
    }


def to_style_performance_arc_live_command_deck_json(
    report: StylePerformanceArcLiveCommandDeckReport,
) -> dict[str, object]:
    """Return deterministic JSON data for the live command deck."""

    timeline_json = to_style_performance_arc_live_transition_timeline_json(report.timeline)
    return {
        "live_command_deck": {
            "deck_version": report.deck_version,
            "deck_id": report.deck_id,
            "current_cue_number": report.current_cue_number,
            "selection_source": report.selection_source,
            "source_reference": report.source_reference,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "show_mode": report.show_mode,
            "scope": report.scope,
            "readiness": report.readiness,
            "stage_state": report.stage_state,
            "go_no_go": report.go_no_go,
            "operator_mode": report.operator_mode,
            "headline_prompt": report.headline_prompt,
            "current_cue": _cue_json(report.current_cue),
            "lookahead_cues": [_cue_json(cue) for cue in report.lookahead_cues],
            "launch_sequence": list(report.launch_sequence),
            "machine_handoff": list(report.machine_handoff),
            "recovery_controls": list(report.recovery_controls),
            "suggested_commands": list(report.suggested_commands),
        },
        "live_transition_timeline": timeline_json["live_transition_timeline"],
        "live_show_export": timeline_json["live_show_export"],
        "live_set_cockpit": timeline_json["live_set_cockpit"],
        "stage_rehearsal_state": timeline_json["stage_rehearsal_state"],
        "stage_snapshot_routing": timeline_json["stage_snapshot_routing"],
        "live_runbook": timeline_json["live_runbook"],
        "cue_sheet": timeline_json["cue_sheet"],
        "reference_match": timeline_json["reference_match"],
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
        report = build_style_performance_arc_live_command_deck_report(
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
                    to_style_performance_arc_live_command_deck_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_command_deck_report(
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


STYLE_PERFORMANCE_ARC_LIVE_COMMAND_DECK_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-command-deck-report",
    summary="Build a passive live command deck from an arc or reference.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_COMMAND_DECK_CLI_COMMAND)

__all__ = [
    "DECK_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_COMMAND_DECK_CLI_COMMAND",
    "StylePerformanceArcLiveCommandDeckCue",
    "StylePerformanceArcLiveCommandDeckReport",
    "build_style_performance_arc_live_command_deck_from_timeline",
    "build_style_performance_arc_live_command_deck_report",
    "format_style_performance_arc_live_command_deck_report",
    "to_style_performance_arc_live_command_deck_json",
]
