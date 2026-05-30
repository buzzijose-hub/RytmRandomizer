"""Passive live transition timeline for style performance arcs."""

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
from .live_show_export import (
    StylePerformanceArcLiveShowCueStep,
    StylePerformanceArcLiveShowExportReport,
    build_style_performance_arc_live_show_export_report,
    to_style_performance_arc_live_show_export_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live transition timeline"
SOURCE_MODULE: Final[str] = "reports.live_transition_timeline"
TIMELINE_VERSION: Final[str] = "live-transition-timeline-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live transition timeline only",
    "composes live show export only",
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
_DEFAULT_EVENT_LIMIT: Final[int] = 24
_USAGE: Final[str] = (
    "style-performance-arc-live-transition-timeline-report usage: "
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
class StylePerformanceArcLiveTransitionCard:
    """One cue-to-cue transition card for the passive timeline."""

    transition_number: int
    cue_number: int
    cue_label: str
    time_window: str
    style_key: str
    phase: str
    status_light: str
    go_no_go: str
    prep_window: str
    prep_actions: tuple[str, ...]
    launch_action: str
    hold_action: str
    recover_action: str
    listen_for: str
    machine_focus: str
    machine_handoff: str
    route_status: str
    blocker_summary: str
    passive_command: str
    event_preview_rows: tuple[str, ...]


@dataclass(frozen=True)
class StylePerformanceArcLiveTransitionTimelineReport:
    """Passive transition timeline composed from a live show export packet."""

    live_show_export: StylePerformanceArcLiveShowExportReport
    timeline_version: str
    timeline_id: str
    show_title: str
    stage_state: str
    go_no_go: str
    transition_cards: tuple[StylePerformanceArcLiveTransitionCard, ...]
    operator_timeline: tuple[str, ...]
    rehearsal_loop: tuple[str, ...]
    recovery_timeline: tuple[str, ...]
    suggested_commands: tuple[str, ...]

    @property
    def selection_source(self) -> str:
        """Return the selected source mode."""

        return self.live_show_export.selection_source

    @property
    def source_reference(self) -> str | None:
        """Return the selected source reference when available."""

        return self.live_show_export.source_reference

    @property
    def selected_arc_key(self) -> str:
        """Return the selected arc key."""

        return self.live_show_export.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return the selected arc name."""

        return self.live_show_export.selected_arc_name

    @property
    def show_mode(self) -> str:
        """Return the selected show-mode label."""

        return self.live_show_export.show_mode

    @property
    def scope(self) -> str:
        """Return the selected machine scope."""

        return self.live_show_export.scope

    @property
    def readiness(self) -> str:
        """Return the selected readiness label."""

        return self.live_show_export.readiness


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


def _transition_phase(go_no_go: str) -> str:
    if go_no_go == "go":
        return "launch"
    if go_no_go == "rehearse":
        return "soundcheck"
    if go_no_go == "do-not-arm":
        return "rescue"
    return "review"


def _source_option(export: StylePerformanceArcLiveShowExportReport) -> str:
    if export.selection_source in {"arc", "description", "audio", "library"}:
        source_reference = export.source_reference or export.selected_arc_key
        return f"--{export.selection_source} {powershell_literal_arg(source_reference)}"
    return f"--arc {export.selected_arc_key}"


def _machine_handoff(export: StylePerformanceArcLiveShowExportReport) -> str:
    if not export.machine_exports:
        return "none"
    return "; ".join(
        f"{machine.label}: {machine.status_action}/{machine.arm_state}"
        for machine in export.machine_exports
    )


def _prep_window(
    cue: StylePerformanceArcLiveShowCueStep,
    previous: StylePerformanceArcLiveShowCueStep | None,
) -> str:
    if previous is None:
        return "before show"
    return f"after cue {previous.cue_number}"


def _prep_actions(
    export: StylePerformanceArcLiveShowExportReport,
    cue: StylePerformanceArcLiveShowCueStep,
) -> tuple[str, ...]:
    actions = [
        cue.preflight_check,
        f"Verify route status: {cue.route_status}.",
        f"Confirm machine handoff: {_machine_handoff(export)}.",
    ]
    if cue.blocker_summary != "none":
        actions.append(f"Resolve blockers before launch: {cue.blocker_summary}.")
    return tuple(actions)


def _hold_action(cue: StylePerformanceArcLiveShowCueStep) -> str:
    if cue.go_no_go == "go":
        return "Hold the groove until the launch line feels stable, then move."
    if cue.go_no_go == "rehearse":
        return f"Hold current machines through {cue.time_window} until soundcheck confirms launch."
    if cue.go_no_go == "do-not-arm":
        return "Hold current machine state; skip this cue and follow recovery."
    return f"Hold and review go/no-go state {cue.go_no_go}."


def _passive_command(
    export: StylePerformanceArcLiveShowExportReport,
    cue: StylePerformanceArcLiveShowCueStep,
) -> str:
    return (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-transition-timeline-report "
        f"{_source_option(export)} --scope {export.scope} --events --limit 8 "
        f"# cue {cue.cue_number}"
    )


def _transition_card(
    export: StylePerformanceArcLiveShowExportReport,
    cue: StylePerformanceArcLiveShowCueStep,
    previous: StylePerformanceArcLiveShowCueStep | None,
) -> StylePerformanceArcLiveTransitionCard:
    return StylePerformanceArcLiveTransitionCard(
        transition_number=cue.cue_number,
        cue_number=cue.cue_number,
        cue_label=f"Cue {cue.cue_number}",
        time_window=cue.time_window,
        style_key=cue.style_key,
        phase=_transition_phase(cue.go_no_go),
        status_light=cue.status_light,
        go_no_go=cue.go_no_go,
        prep_window=_prep_window(cue, previous),
        prep_actions=_prep_actions(export, cue),
        launch_action=cue.launch_line,
        hold_action=_hold_action(cue),
        recover_action=cue.recovery_line,
        listen_for=cue.listen_for,
        machine_focus=cue.machine_focus,
        machine_handoff=_machine_handoff(export),
        route_status=cue.route_status,
        blocker_summary=cue.blocker_summary,
        passive_command=_passive_command(export, cue),
        event_preview_rows=cue.event_preview_rows,
    )


def _operator_timeline(
    cards: Sequence[StylePerformanceArcLiveTransitionCard],
) -> tuple[str, ...]:
    return tuple(
        (
            f"Transition {card.transition_number}: {card.prep_window} -> "
            f"{card.launch_action} [{card.phase}]"
        )
        for card in cards
    )


def _rehearsal_loop(
    cards: Sequence[StylePerformanceArcLiveTransitionCard],
) -> tuple[str, ...]:
    return tuple(
        (
            f"Rehearse cue {card.cue_number}: prep, launch, listen for "
            f"{card.listen_for}, then recover if needed."
        )
        for card in cards
    )


def _timeline_id(
    export: StylePerformanceArcLiveShowExportReport,
    cards: Sequence[StylePerformanceArcLiveTransitionCard],
) -> str:
    digest_input = "|".join(
        f"{card.cue_number}:{card.phase}:{card.go_no_go}:{card.route_status}" for card in cards
    )
    digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:8]
    return f"{export.export_id}-{digest}"


def build_style_performance_arc_live_transition_timeline_from_export(
    live_show_export: StylePerformanceArcLiveShowExportReport,
) -> StylePerformanceArcLiveTransitionTimelineReport:
    """Build a passive transition timeline from an existing show export."""

    cards = tuple(
        _transition_card(
            live_show_export,
            cue,
            live_show_export.cue_steps[index - 1] if index > 0 else None,
        )
        for index, cue in enumerate(live_show_export.cue_steps)
    )
    suggested_command = (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-transition-timeline-report "
        f"{_source_option(live_show_export)} --scope {live_show_export.scope} "
        "--events --limit 8"
    )
    return StylePerformanceArcLiveTransitionTimelineReport(
        live_show_export=live_show_export,
        timeline_version=TIMELINE_VERSION,
        timeline_id=_timeline_id(live_show_export, cards),
        show_title=f"{live_show_export.selected_arc_name} live transition timeline",
        stage_state=live_show_export.stage_state,
        go_no_go=live_show_export.go_no_go,
        transition_cards=cards,
        operator_timeline=_operator_timeline(cards),
        rehearsal_loop=_rehearsal_loop(cards),
        recovery_timeline=live_show_export.recovery_script,
        suggested_commands=(suggested_command, *live_show_export.suggested_commands),
    )


def build_style_performance_arc_live_transition_timeline_report(
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
) -> StylePerformanceArcLiveTransitionTimelineReport:
    """Build a passive transition timeline from an arc or reference."""

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
        raise ValueError("live transition timeline requires exactly one selection source")

    live_show_export = build_style_performance_arc_live_show_export_report(
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
    return build_style_performance_arc_live_transition_timeline_from_export(live_show_export)


def _limited_event_rows(rows: Sequence[str], *, event_limit: int) -> tuple[str, ...]:
    if event_limit == 0:
        return tuple(rows)
    return tuple(rows[:event_limit])


def _transition_card_lines(
    card: StylePerformanceArcLiveTransitionCard,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    lines = [
        f"- {card.cue_label}. {card.time_window} | {card.style_key} | {card.status_light}",
        f"  Phase: {card.phase}",
        f"  Go / no-go: {card.go_no_go}",
        f"  Prep window: {card.prep_window}",
        "  Prep actions:",
        *[f"  - {action}" for action in card.prep_actions],
        f"  Launch: {card.launch_action}",
        f"  Hold: {card.hold_action}",
        f"  Listen for: {card.listen_for}",
        f"  Machine focus: {card.machine_focus}",
        f"  Machine handoff: {card.machine_handoff}",
        f"  Route: {card.route_status}",
        f"  Blockers: {card.blocker_summary}",
        f"  Recovery: {card.recover_action}",
        f"  Passive command: {card.passive_command}",
    ]
    if include_events:
        lines.append("  Transition event preview:")
        if not card.event_preview_rows:
            lines.append(
                "  - No mock rows available because the selected transition has no ready preview."
            )
        else:
            rows = _limited_event_rows(card.event_preview_rows, event_limit=event_limit)
            if len(rows) == len(card.event_preview_rows):
                lines.append("  - Showing all events")
            else:
                lines.append(f"  - Showing first {event_limit} of {len(card.event_preview_rows)}")
            lines.extend(f"  {row}" for row in rows)
    return lines


def format_style_performance_arc_live_transition_timeline_report(
    report: StylePerformanceArcLiveTransitionTimelineReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic live transition timeline lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    lines = [
        "Transition timeline summary:",
        f"- Timeline version: {report.timeline_version}",
        f"- Timeline id: {report.timeline_id}",
        f"- Show title: {report.show_title}",
        f"- Selection source: {report.selection_source}",
        f"- Source reference: {report.source_reference}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Show mode: {report.show_mode}",
        f"- Scope: {report.scope}",
        f"- Readiness: {report.readiness}",
        f"- Stage state: {report.stage_state}",
        f"- Go / no-go: {report.go_no_go}",
        f"- Transition count: {len(report.transition_cards)}",
        "Operator timeline:",
        *[f"- {line}" for line in report.operator_timeline],
        "Transition cards:",
    ]
    for card in report.transition_cards:
        lines.extend(
            _transition_card_lines(
                card,
                include_events=include_events,
                event_limit=event_limit,
            )
        )
    lines.extend(
        [
            "Rehearsal loop:",
            *[f"- {line}" for line in report.rehearsal_loop],
            "Recovery timeline:",
            *[f"- {line}" for line in report.recovery_timeline],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.suggested_commands],
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


def _transition_card_json(card: StylePerformanceArcLiveTransitionCard) -> dict[str, object]:
    return {
        "transition_number": card.transition_number,
        "cue_number": card.cue_number,
        "cue_label": card.cue_label,
        "time_window": card.time_window,
        "style_key": card.style_key,
        "phase": card.phase,
        "status_light": card.status_light,
        "go_no_go": card.go_no_go,
        "prep_window": card.prep_window,
        "prep_actions": list(card.prep_actions),
        "launch_action": card.launch_action,
        "hold_action": card.hold_action,
        "recover_action": card.recover_action,
        "listen_for": card.listen_for,
        "machine_focus": card.machine_focus,
        "machine_handoff": card.machine_handoff,
        "route_status": card.route_status,
        "blocker_summary": card.blocker_summary,
        "passive_command": card.passive_command,
        "event_preview_rows": list(card.event_preview_rows),
    }


def to_style_performance_arc_live_transition_timeline_json(
    report: StylePerformanceArcLiveTransitionTimelineReport,
) -> dict[str, object]:
    """Return deterministic JSON data for the transition timeline."""

    export_json = to_style_performance_arc_live_show_export_json(report.live_show_export)
    return {
        "live_transition_timeline": {
            "timeline_version": report.timeline_version,
            "timeline_id": report.timeline_id,
            "show_title": report.show_title,
            "selection_source": report.selection_source,
            "source_reference": report.source_reference,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "show_mode": report.show_mode,
            "scope": report.scope,
            "readiness": report.readiness,
            "stage_state": report.stage_state,
            "go_no_go": report.go_no_go,
            "transition_cards": [_transition_card_json(card) for card in report.transition_cards],
            "operator_timeline": list(report.operator_timeline),
            "rehearsal_loop": list(report.rehearsal_loop),
            "recovery_timeline": list(report.recovery_timeline),
            "suggested_commands": list(report.suggested_commands),
        },
        "live_show_export": export_json["live_show_export"],
        "live_set_cockpit": export_json["live_set_cockpit"],
        "stage_rehearsal_state": export_json["stage_rehearsal_state"],
        "stage_snapshot_routing": export_json["stage_snapshot_routing"],
        "live_runbook": export_json["live_runbook"],
        "cue_sheet": export_json["cue_sheet"],
        "reference_match": export_json["reference_match"],
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
        report = build_style_performance_arc_live_transition_timeline_report(
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
                    to_style_performance_arc_live_transition_timeline_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_transition_timeline_report(
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


STYLE_PERFORMANCE_ARC_LIVE_TRANSITION_TIMELINE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-transition-timeline-report",
    summary="Build a passive live transition timeline from an arc or reference.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_TRANSITION_TIMELINE_CLI_COMMAND)

__all__ = [
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_TRANSITION_TIMELINE_CLI_COMMAND",
    "TIMELINE_VERSION",
    "StylePerformanceArcLiveTransitionCard",
    "StylePerformanceArcLiveTransitionTimelineReport",
    "build_style_performance_arc_live_transition_timeline_from_export",
    "build_style_performance_arc_live_transition_timeline_report",
    "format_style_performance_arc_live_transition_timeline_report",
    "to_style_performance_arc_live_transition_timeline_json",
]
