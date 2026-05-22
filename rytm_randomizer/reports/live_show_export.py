"""Passive live show export packet for style performance arcs."""

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
from .live_set_cockpit import (
    StylePerformanceArcLiveSetCockpitCueCard,
    StylePerformanceArcLiveSetCockpitReport,
    StylePerformanceArcLiveSetMachinePanel,
    build_style_performance_arc_live_set_cockpit_report,
    to_style_performance_arc_live_set_cockpit_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live show export"
SOURCE_MODULE: Final[str] = "reports.live_show_export"
PACKET_VERSION: Final[str] = "live-show-export-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live show export packet only",
    "composes live set cockpit only",
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
    "style-performance-arc-live-show-export-report usage: "
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
class StylePerformanceArcLiveShowMachineExport:
    """One machine handoff row for a passive live show packet."""

    machine: str
    label: str
    status: str
    status_light: str
    status_action: str
    arm_state: str
    slot_summary: str
    kit_summary: str
    fingerprint_summary: str
    planned_units: tuple[int, ...]
    mock_row_count: int
    deferred_row_count: int
    operator_check: str
    export_note: str


@dataclass(frozen=True)
class StylePerformanceArcLiveShowCueStep:
    """One operator cue step for the passive live show packet."""

    cue_number: int
    time_window: str
    style_key: str
    status_light: str
    go_no_go: str
    status_action: str
    launch_line: str
    preflight_check: str
    listen_for: str
    machine_focus: str
    recovery_line: str
    route_status: str
    blocker_summary: str
    passive_command: str
    event_preview_rows: tuple[str, ...]


@dataclass(frozen=True)
class StylePerformanceArcLiveShowExportReport:
    """Passive live-show export packet composed from a cockpit report."""

    cockpit: StylePerformanceArcLiveSetCockpitReport
    packet_version: str
    export_id: str
    show_title: str
    show_summary: str
    stage_state: str
    go_no_go: str
    machine_exports: tuple[StylePerformanceArcLiveShowMachineExport, ...]
    cue_steps: tuple[StylePerformanceArcLiveShowCueStep, ...]
    operator_script: tuple[str, ...]
    recovery_script: tuple[str, ...]
    suggested_commands: tuple[str, ...]

    @property
    def selection_source(self) -> str:
        """Return the selected source mode."""

        return self.cockpit.selection_source

    @property
    def source_reference(self) -> str | None:
        """Return the selected source reference when available."""

        return self.cockpit.source_reference

    @property
    def selected_arc_key(self) -> str:
        """Return the selected arc key."""

        return self.cockpit.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return the selected arc name."""

        return self.cockpit.selected_arc_name

    @property
    def show_mode(self) -> str:
        """Return the selected show-mode label."""

        return self.cockpit.show_mode

    @property
    def scope(self) -> str:
        """Return the selected machine scope."""

        return self.cockpit.scope

    @property
    def readiness(self) -> str:
        """Return the selected readiness label."""

        return self.cockpit.readiness


def _string_sequence(values: Sequence[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def _number_sequence(values: Sequence[int]) -> str:
    if not values:
        return "none"
    return ", ".join(str(value) for value in values)


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


def _status_action(go_no_go: str) -> str:
    if go_no_go == "go":
        return "launch-ready"
    if go_no_go == "rehearse":
        return "rehearse-before-arm"
    if go_no_go == "do-not-arm":
        return "skip-and-recover"
    return "review"


def _step_status_light(go_no_go: str) -> str:
    if go_no_go == "go":
        return "GREEN"
    if go_no_go == "rehearse":
        return "AMBER"
    if go_no_go == "do-not-arm":
        return "RED"
    return "WHITE"


def _machine_status_action(status: str) -> str:
    if status == "loaded":
        return "export-ready"
    if status == "blocked":
        return "do-not-arm"
    return "rehearse-or-park"


def _machine_export(
    panel: StylePerformanceArcLiveSetMachinePanel,
) -> StylePerformanceArcLiveShowMachineExport:
    status_action = _machine_status_action(panel.status)
    return StylePerformanceArcLiveShowMachineExport(
        machine=panel.machine,
        label=panel.label,
        status=panel.status,
        status_light=panel.status_light,
        status_action=status_action,
        arm_state=panel.arm_state,
        slot_summary=panel.slot_summary,
        kit_summary=panel.kit_summary,
        fingerprint_summary=panel.fingerprint_summary,
        planned_units=panel.planned_units,
        mock_row_count=panel.mock_row_count,
        deferred_row_count=panel.deferred_row_count,
        operator_check=panel.operator_check,
        export_note=f"{panel.label}: {status_action}; {panel.operator_check}",
    )


def _source_option(cockpit: StylePerformanceArcLiveSetCockpitReport) -> str:
    if cockpit.selection_source in {"arc", "description", "audio", "library"}:
        source_reference = cockpit.source_reference or cockpit.selected_arc_key
        return f"--{cockpit.selection_source} {powershell_literal_arg(source_reference)}"
    return f"--arc {cockpit.selected_arc_key}"


def _cue_passive_command(
    cockpit: StylePerformanceArcLiveSetCockpitReport,
    cue: StylePerformanceArcLiveSetCockpitCueCard,
) -> str:
    return (
        "python -m rytm_randomizer.cli style-performance-arc-live-show-export-report "
        f"{_source_option(cockpit)} --scope {cockpit.scope} --events --limit 8 "
        f"# cue {cue.cue_number}"
    )


def _cue_step(
    cockpit: StylePerformanceArcLiveSetCockpitReport,
    cue: StylePerformanceArcLiveSetCockpitCueCard,
) -> StylePerformanceArcLiveShowCueStep:
    status_action = _status_action(cue.go_no_go)
    launch_line = f"Cue {cue.cue_number}: {cue.time_window} / {cue.style_key} / " f"{status_action}"
    return StylePerformanceArcLiveShowCueStep(
        cue_number=cue.cue_number,
        time_window=cue.time_window,
        style_key=cue.style_key,
        status_light=_step_status_light(cue.go_no_go),
        go_no_go=cue.go_no_go,
        status_action=status_action,
        launch_line=launch_line,
        preflight_check=f"Confirm machine focus: {cue.machine_focus}; {cue.machine_arm_summary}.",
        listen_for=cue.listen_for,
        machine_focus=f"{cue.machine_focus}; {cue.machine_arm_summary}",
        recovery_line=f"If unsafe: {cue.recovery_action}",
        route_status=cue.route_status,
        blocker_summary=cue.blocker_summary,
        passive_command=_cue_passive_command(cockpit, cue),
        event_preview_rows=cue.event_preview_rows,
    )


def _operator_script(
    cockpit: StylePerformanceArcLiveSetCockpitReport,
    cue_steps: Sequence[StylePerformanceArcLiveShowCueStep],
) -> tuple[str, ...]:
    return (
        f"Load show export {cockpit.selected_arc_key} and verify scope {cockpit.scope}.",
        f"Confirm cockpit state {cockpit.stage_state} / {cockpit.overall_go_no_go}.",
        "Check each machine handoff row before any future active send path.",
        *[step.launch_line for step in cue_steps],
    )


def _recovery_script(cockpit: StylePerformanceArcLiveSetCockpitReport) -> tuple[str, ...]:
    return (
        *cockpit.recovery_controls,
        "If any cue reads do-not-arm, do not arm it; hold the current machine state.",
        "This packet is export-only; recover with the hardware and passive reports.",
    )


def _deterministic_export_id(cockpit: StylePerformanceArcLiveSetCockpitReport) -> str:
    cockpit_json = to_style_performance_arc_live_set_cockpit_json(cockpit)
    encoded = json.dumps(cockpit_json, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def build_style_performance_arc_live_show_export_from_cockpit(
    cockpit: StylePerformanceArcLiveSetCockpitReport,
) -> StylePerformanceArcLiveShowExportReport:
    """Build a passive show export packet from an existing cockpit report."""

    cue_steps = tuple(_cue_step(cockpit, cue) for cue in cockpit.cue_cards)
    machine_exports = tuple(_machine_export(panel) for panel in cockpit.machine_panels)
    suggested_command = (
        "python -m rytm_randomizer.cli style-performance-arc-live-show-export-report "
        f"{_source_option(cockpit)} --scope {cockpit.scope} --events --limit 8"
    )
    return StylePerformanceArcLiveShowExportReport(
        cockpit=cockpit,
        packet_version=PACKET_VERSION,
        export_id=_deterministic_export_id(cockpit),
        show_title=f"{cockpit.selected_arc_name} live show export",
        show_summary=(
            f"{cockpit.selected_arc_key} / {cockpit.selected_arc_name} / "
            f"{cockpit.scope} / {cockpit.cue_count} cues"
        ),
        stage_state=cockpit.stage_state,
        go_no_go=cockpit.overall_go_no_go,
        machine_exports=machine_exports,
        cue_steps=cue_steps,
        operator_script=_operator_script(cockpit, cue_steps),
        recovery_script=_recovery_script(cockpit),
        suggested_commands=(suggested_command, *cockpit.suggested_commands),
    )


def build_style_performance_arc_live_show_export_report(
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
) -> StylePerformanceArcLiveShowExportReport:
    """Build a passive live show export from an arc or reference."""

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
        raise ValueError("live show export requires exactly one selection source")

    cockpit = build_style_performance_arc_live_set_cockpit_report(
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
    return build_style_performance_arc_live_show_export_from_cockpit(cockpit)


def _limited_event_rows(rows: Sequence[str], *, event_limit: int) -> tuple[str, ...]:
    if event_limit == 0:
        return tuple(rows)
    return tuple(rows[:event_limit])


def _machine_export_lines(machine_export: StylePerformanceArcLiveShowMachineExport) -> list[str]:
    return [
        (
            f"- {machine_export.label}: {machine_export.status_light} | "
            f"{machine_export.status} | {machine_export.status_action}"
        ),
        f"  Arm state: {machine_export.arm_state}",
        f"  Slot(s): {machine_export.slot_summary}",
        f"  Kit(s): {machine_export.kit_summary}",
        f"  Fingerprint(s): {machine_export.fingerprint_summary}",
        f"  Planned units: {_number_sequence(machine_export.planned_units)}",
        (
            "  Rows: "
            f"mock {machine_export.mock_row_count} | deferred {machine_export.deferred_row_count}"
        ),
        f"  Export note: {machine_export.export_note}",
    ]


def _cue_step_lines(
    cue_step: StylePerformanceArcLiveShowCueStep,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    lines = [
        f"- {cue_step.launch_line} | {cue_step.status_light}",
        f"  Go / no-go: {cue_step.go_no_go}",
        f"  Preflight: {cue_step.preflight_check}",
        f"  Listen for: {cue_step.listen_for}",
        f"  Machine focus: {cue_step.machine_focus}",
        f"  Route: {cue_step.route_status}",
        f"  Blockers: {cue_step.blocker_summary}",
        f"  Recovery: {cue_step.recovery_line}",
        f"  Passive command: {cue_step.passive_command}",
    ]
    if include_events:
        lines.append("  Cue event preview:")
        if not cue_step.event_preview_rows:
            lines.append(
                "  - No mock rows available because the selected cue has no ready mock preview."
            )
        else:
            rows = _limited_event_rows(cue_step.event_preview_rows, event_limit=event_limit)
            if len(rows) == len(cue_step.event_preview_rows):
                lines.append("  - Showing all events")
            else:
                lines.append(
                    f"  - Showing first {event_limit} of {len(cue_step.event_preview_rows)}"
                )
            lines.extend(f"  {row}" for row in rows)
    return lines


def format_style_performance_arc_live_show_export_report(
    report: StylePerformanceArcLiveShowExportReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic live show export lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    lines = [
        "Show export summary:",
        f"- Packet version: {report.packet_version}",
        f"- Export id: {report.export_id}",
        f"- Show title: {report.show_title}",
        f"- Selection source: {report.selection_source}",
        f"- Source reference: {report.source_reference}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Show mode: {report.show_mode}",
        f"- Scope: {report.scope}",
        f"- Readiness: {report.readiness}",
        f"- Stage state: {report.stage_state}",
        f"- Go / no-go: {report.go_no_go}",
        f"- Cue count: {len(report.cue_steps)}",
        "Machine handoff manifest:",
    ]
    for machine_export in report.machine_exports:
        lines.extend(_machine_export_lines(machine_export))
    lines.extend(
        [
            "Operator launch script:",
            *[f"- {step}" for step in report.operator_script],
            "Cue launch script:",
        ]
    )
    for cue_step in report.cue_steps:
        lines.extend(
            _cue_step_lines(
                cue_step,
                include_events=include_events,
                event_limit=event_limit,
            )
        )
    lines.extend(
        [
            "Recovery script:",
            *[f"- {step}" for step in report.recovery_script],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.suggested_commands],
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


def _machine_export_json(
    machine_export: StylePerformanceArcLiveShowMachineExport,
) -> dict[str, object]:
    return {
        "machine": machine_export.machine,
        "label": machine_export.label,
        "status": machine_export.status,
        "status_light": machine_export.status_light,
        "status_action": machine_export.status_action,
        "arm_state": machine_export.arm_state,
        "slot_summary": machine_export.slot_summary,
        "kit_summary": machine_export.kit_summary,
        "fingerprint_summary": machine_export.fingerprint_summary,
        "planned_units": list(machine_export.planned_units),
        "mock_row_count": machine_export.mock_row_count,
        "deferred_row_count": machine_export.deferred_row_count,
        "operator_check": machine_export.operator_check,
        "export_note": machine_export.export_note,
    }


def _cue_step_json(cue_step: StylePerformanceArcLiveShowCueStep) -> dict[str, object]:
    return {
        "cue_number": cue_step.cue_number,
        "time_window": cue_step.time_window,
        "style_key": cue_step.style_key,
        "status_light": cue_step.status_light,
        "go_no_go": cue_step.go_no_go,
        "status_action": cue_step.status_action,
        "launch_line": cue_step.launch_line,
        "preflight_check": cue_step.preflight_check,
        "listen_for": cue_step.listen_for,
        "machine_focus": cue_step.machine_focus,
        "recovery_line": cue_step.recovery_line,
        "route_status": cue_step.route_status,
        "blocker_summary": cue_step.blocker_summary,
        "passive_command": cue_step.passive_command,
        "event_preview_rows": list(cue_step.event_preview_rows),
    }


def to_style_performance_arc_live_show_export_json(
    report: StylePerformanceArcLiveShowExportReport,
) -> dict[str, object]:
    """Return deterministic JSON data for the live show export."""

    cockpit_json = to_style_performance_arc_live_set_cockpit_json(report.cockpit)
    return {
        "live_show_export": {
            "packet_version": report.packet_version,
            "export_id": report.export_id,
            "show_title": report.show_title,
            "show_summary": report.show_summary,
            "selection_source": report.selection_source,
            "source_reference": report.source_reference,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "show_mode": report.show_mode,
            "scope": report.scope,
            "readiness": report.readiness,
            "stage_state": report.stage_state,
            "go_no_go": report.go_no_go,
            "machine_exports": [
                _machine_export_json(machine_export) for machine_export in report.machine_exports
            ],
            "cue_steps": [_cue_step_json(cue_step) for cue_step in report.cue_steps],
            "operator_script": list(report.operator_script),
            "recovery_script": list(report.recovery_script),
            "suggested_commands": list(report.suggested_commands),
        },
        "live_set_cockpit": cockpit_json["live_set_cockpit"],
        "stage_rehearsal_state": cockpit_json["stage_rehearsal_state"],
        "stage_snapshot_routing": cockpit_json["stage_snapshot_routing"],
        "live_runbook": cockpit_json["live_runbook"],
        "cue_sheet": cockpit_json["cue_sheet"],
        "reference_match": cockpit_json["reference_match"],
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
        report = build_style_performance_arc_live_show_export_report(
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
                    to_style_performance_arc_live_show_export_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_show_export_report(
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


STYLE_PERFORMANCE_ARC_LIVE_SHOW_EXPORT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-show-export-report",
    summary="Build a passive live show export packet from an arc or reference.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_SHOW_EXPORT_CLI_COMMAND)

__all__ = [
    "PACKET_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_SHOW_EXPORT_CLI_COMMAND",
    "StylePerformanceArcLiveShowCueStep",
    "StylePerformanceArcLiveShowExportReport",
    "StylePerformanceArcLiveShowMachineExport",
    "build_style_performance_arc_live_show_export_from_cockpit",
    "build_style_performance_arc_live_show_export_report",
    "format_style_performance_arc_live_show_export_report",
    "to_style_performance_arc_live_show_export_json",
]
