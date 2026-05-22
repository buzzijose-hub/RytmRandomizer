"""Passive live-performance readiness report for GUI/audio-analyzer routing."""

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
from .live_performance_state import (
    StylePerformanceArcLiveStateMachine,
    StylePerformanceArcLiveStateReport,
    build_style_performance_arc_live_state_report,
    to_style_performance_arc_live_state_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live readiness"
SOURCE_MODULE: Final[str] = "reports.live_performance_readiness"
READINESS_VERSION: Final[str] = "live-performance-readiness-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live readiness report only",
    "composes live state packet only",
    "uses saved-kit snapshots when supplied",
    "GUI/audio-analyzer readiness only",
    "audio analyzer preview only",
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
_USAGE: Final[str] = (
    "style-performance-arc-live-readiness-report usage: "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--json]"
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
    "--json",
)


@dataclass(frozen=True)
class StylePerformanceArcLiveReadinessGate:
    """One passive readiness gate for future GUI/audio-analyzer routing."""

    key: str
    label: str
    status: str
    severity: str
    message: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveReadinessReport:
    """Passive readiness view composed from a live state packet."""

    live_state: StylePerformanceArcLiveStateReport
    readiness_version: str
    readiness_id: str
    overall_status: str
    launch_mode: str
    current_cue_summary: str
    machine_summary: str
    gates: tuple[StylePerformanceArcLiveReadinessGate, ...]
    machine_panel_rows: tuple[str, ...]
    audio_analyzer_handoff: tuple[str, ...]
    operator_next_actions: tuple[str, ...]
    rehearsal_commands: tuple[str, ...]

    @property
    def selected_arc_key(self) -> str:
        """Return the selected arc key."""

        return self.live_state.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return the selected arc name."""

        return self.live_state.selected_arc_name

    @property
    def scope(self) -> str:
        """Return the selected machine scope."""

        return self.live_state.scope

    @property
    def go_no_go(self) -> str:
        """Return the upstream aggregate go/no-go value."""

        return self.live_state.go_no_go


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


def _source_option(live_state: StylePerformanceArcLiveStateReport) -> str:
    if live_state.selection_source in {"arc", "description", "audio", "library"}:
        source_reference = live_state.source_reference or live_state.selected_arc_key
        return f"--{live_state.selection_source} {powershell_literal_arg(source_reference)}"
    return f"--arc {live_state.selected_arc_key}"


def _status_from_cue(live_state: StylePerformanceArcLiveStateReport) -> str:
    cue = live_state.current_cue
    if live_state.live_state == "blocked" or cue.go_no_go == "do-not-arm":
        return "blocked"
    if cue.screen_state == "perform":
        return "ready"
    if cue.screen_state == "soundcheck":
        return "rehearse"
    return "review"


def _machine_summary(machines: Sequence[StylePerformanceArcLiveStateMachine]) -> str:
    armed_count = sum(machine.arm_state == "armed-preview" for machine in machines)
    rehearse_count = sum(machine.arm_state == "rehearse" for machine in machines)
    blocked_count = sum(machine.arm_state == "do-not-arm" for machine in machines)
    return f"{armed_count} armed-preview | {rehearse_count} rehearse | {blocked_count} blocked"


def _machine_gate_status(machines: Sequence[StylePerformanceArcLiveStateMachine]) -> str:
    if any(machine.arm_state == "do-not-arm" for machine in machines):
        return "blocked"
    if any(machine.arm_state == "rehearse" for machine in machines):
        return "partial"
    if machines:
        return "ready"
    return "blocked"


def _overall_status(
    live_state: StylePerformanceArcLiveStateReport,
    machines: Sequence[StylePerformanceArcLiveStateMachine],
) -> str:
    if live_state.live_state == "blocked" or _machine_gate_status(machines) == "blocked":
        return "blocked"
    if live_state.live_state == "ready" and _machine_gate_status(machines) == "ready":
        return "performance-ready"
    return "rehearsal-ready"


def _gate_severity(status: str) -> str:
    if status in {"ready", "disabled"}:
        return "info"
    if status in {"rehearse", "partial", "preview", "review"}:
        return "warning"
    return "critical"


def _gate(
    key: str,
    label: str,
    status: str,
    message: str,
    operator_action: str,
) -> StylePerformanceArcLiveReadinessGate:
    return StylePerformanceArcLiveReadinessGate(
        key=key,
        label=label,
        status=status,
        severity=_gate_severity(status),
        message=message,
        operator_action=operator_action,
    )


def _gates(live_state: StylePerformanceArcLiveStateReport) -> tuple[
    StylePerformanceArcLiveReadinessGate,
    ...,
]:
    cue_status = _status_from_cue(live_state)
    machine_status = _machine_gate_status(live_state.machine_states)
    return (
        _gate(
            "live-state-packet",
            "Live state packet",
            "ready",
            f"State packet {live_state.state_id} is built from the command deck.",
            "Use this packet as the GUI state source.",
        ),
        _gate(
            "current-cue",
            "Current cue",
            cue_status,
            f"{live_state.current_cue.cue_label}: {live_state.current_cue.warning_text}",
            (
                live_state.current_cue.recovery_action
                if cue_status == "blocked"
                else live_state.current_cue.primary_action
            ),
        ),
        _gate(
            "machine-panels",
            "Machine panels",
            machine_status,
            _machine_summary(live_state.machine_states),
            (
                "Rehearse and promote candidate/deferred rows before arming."
                if machine_status != "ready"
                else "Machine panels are ready for passive preview."
            ),
        ),
        _gate(
            "gui-command-surface",
            "GUI command surface",
            "ready",
            "Action bar, warning stack, recovery stack, and replay commands are present.",
            "Render now/next cues, machine panels, and recovery controls.",
        ),
        _gate(
            "audio-analyzer-reference",
            "Audio analyzer reference",
            "preview",
            f"Use {live_state.selected_arc_name} and cue listen target as passive reference.",
            "Analyze current audio only as influence matching; do not clone source material.",
        ),
        _gate(
            "hardware-send",
            "Hardware send",
            "disabled",
            "This CLI remains passive and cannot open MIDI ports.",
            "Keep hardware sends disabled here; only the armed app path may touch ports.",
        ),
    )


def _machine_panel_rows(
    machines: Sequence[StylePerformanceArcLiveStateMachine],
) -> tuple[str, ...]:
    return tuple(
        (
            f"{machine.label}: {machine.ui_badge} | {machine.arm_state} | "
            f"{machine.row_summary} | {machine.operator_check}"
        )
        for machine in machines
    )


def _current_cue_summary(live_state: StylePerformanceArcLiveStateReport) -> str:
    cue = live_state.current_cue
    return f"Cue {cue.cue_number} / {cue.phase} / {cue.go_no_go} / {cue.status_light}"


def _audio_analyzer_handoff(
    live_state: StylePerformanceArcLiveStateReport,
) -> tuple[str, ...]:
    cue = live_state.current_cue
    return (
        f"Reference arc: {live_state.selected_arc_key} / {live_state.selected_arc_name}",
        f"Reference source: {live_state.selection_source} / {live_state.source_reference}",
        f"Current style: {cue.style_key}",
        f"Listen target: {cue.listen_for}",
        f"Machine focus: {cue.machine_focus}",
        "Analyzer mode: influence-not-replica; compare energy, density, grit, and motion only.",
    )


def _operator_next_actions(
    live_state: StylePerformanceArcLiveStateReport,
    overall_status: str,
) -> tuple[str, ...]:
    cue = live_state.current_cue
    if overall_status == "blocked":
        return (
            "Hold the current machine state.",
            f"Recover with: {cue.recovery_action}",
            "Keep hardware sends disabled until every red gate clears.",
        )
    if overall_status == "performance-ready":
        return (
            f"Confirm cue {cue.cue_number}, then launch deliberately.",
            f"Listen for: {cue.listen_for}",
            "Analyze current audio only as a passive influence reference.",
        )
    return (
        f"Rehearse cue {cue.cue_number} before arming.",
        "Promote or replace any candidate/deferred Analog Four rows.",
        f"Analyze current audio against: {cue.listen_for}",
    )


def _readiness_id(
    live_state: StylePerformanceArcLiveStateReport,
    gates: Sequence[StylePerformanceArcLiveReadinessGate],
) -> str:
    digest_input = "|".join(
        (
            live_state.state_id,
            ",".join(f"{gate.key}:{gate.status}" for gate in gates),
        )
    )
    digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:8]
    return f"{live_state.state_id}-ready-{digest}"


def _readiness_command(live_state: StylePerformanceArcLiveStateReport) -> str:
    return (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-readiness-report "
        f"{_source_option(live_state)} --scope {live_state.scope} "
        f"--cue {live_state.current_cue.cue_number} --lookahead {len(live_state.next_cues)}"
    )


def build_style_performance_arc_live_readiness_from_state(
    live_state: StylePerformanceArcLiveStateReport,
) -> StylePerformanceArcLiveReadinessReport:
    """Build a passive GUI/audio-analyzer readiness report from live state."""

    gates = _gates(live_state)
    overall_status = _overall_status(live_state, live_state.machine_states)
    return StylePerformanceArcLiveReadinessReport(
        live_state=live_state,
        readiness_version=READINESS_VERSION,
        readiness_id=_readiness_id(live_state, gates),
        overall_status=overall_status,
        launch_mode=live_state.screen_mode,
        current_cue_summary=_current_cue_summary(live_state),
        machine_summary=_machine_summary(live_state.machine_states),
        gates=gates,
        machine_panel_rows=_machine_panel_rows(live_state.machine_states),
        audio_analyzer_handoff=_audio_analyzer_handoff(live_state),
        operator_next_actions=_operator_next_actions(live_state, overall_status),
        rehearsal_commands=(
            _readiness_command(live_state),
            *live_state.replay_commands,
        ),
    )


def build_style_performance_arc_live_readiness_report(
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
) -> StylePerformanceArcLiveReadinessReport:
    """Build passive live-performance readiness from an arc or reference."""

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
        raise ValueError("live readiness requires exactly one selection source")

    live_state = build_style_performance_arc_live_state_report(
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
    return build_style_performance_arc_live_readiness_from_state(live_state)


def format_style_performance_arc_live_readiness_report(
    report: StylePerformanceArcLiveReadinessReport,
) -> list[str]:
    """Return deterministic passive live-readiness report lines."""

    blockers = tuple(warning for warning in report.live_state.warning_stack if warning)
    lines = [
        "Readiness summary:",
        f"- Readiness version: {report.readiness_version}",
        f"- Readiness id: {report.readiness_id}",
        f"- Live state id: {report.live_state.state_id}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        f"- Overall status: {report.overall_status}",
        f"- Launch mode: {report.launch_mode}",
        f"- Go / no-go: {report.go_no_go}",
        f"- Current cue: {report.current_cue_summary}",
        f"- Machine summary: {report.machine_summary}",
        f"- Blockers: {'; '.join(blockers) if blockers else 'none'}",
        "Gate stack:",
    ]
    for gate in report.gates:
        lines.extend(
            (
                f"- {gate.key} / {gate.label}: {gate.status} | {gate.severity}",
                f"  Message: {gate.message}",
                f"  Action: {gate.operator_action}",
            )
        )
    lines.extend(
        [
            "Machine panels:",
            *[f"- {row}" for row in report.machine_panel_rows],
            "Audio analyzer handoff:",
            *[f"- {row}" for row in report.audio_analyzer_handoff],
            "Operator next actions:",
            *[f"- {action}" for action in report.operator_next_actions],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.rehearsal_commands],
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


def _gate_json(gate: StylePerformanceArcLiveReadinessGate) -> dict[str, object]:
    return {
        "key": gate.key,
        "label": gate.label,
        "status": gate.status,
        "severity": gate.severity,
        "message": gate.message,
        "operator_action": gate.operator_action,
    }


def to_style_performance_arc_live_readiness_json(
    report: StylePerformanceArcLiveReadinessReport,
) -> dict[str, object]:
    """Return deterministic JSON data for passive live readiness."""

    state_json = to_style_performance_arc_live_state_json(report.live_state)
    return {
        "live_readiness": {
            "readiness_version": report.readiness_version,
            "readiness_id": report.readiness_id,
            "overall_status": report.overall_status,
            "launch_mode": report.launch_mode,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "go_no_go": report.go_no_go,
            "current_cue_summary": report.current_cue_summary,
            "machine_summary": report.machine_summary,
            "gates": [_gate_json(gate) for gate in report.gates],
            "machine_panel_rows": list(report.machine_panel_rows),
            "audio_analyzer_handoff": list(report.audio_analyzer_handoff),
            "operator_next_actions": list(report.operator_next_actions),
            "rehearsal_commands": list(report.rehearsal_commands),
        },
        "live_state_packet": state_json["live_state_packet"],
        "live_command_deck": state_json["live_command_deck"],
        "live_transition_timeline": state_json["live_transition_timeline"],
        "live_show_export": state_json["live_show_export"],
        "live_set_cockpit": state_json["live_set_cockpit"],
        "stage_rehearsal_state": state_json["stage_rehearsal_state"],
        "stage_snapshot_routing": state_json["stage_snapshot_routing"],
        "live_runbook": state_json["live_runbook"],
        "cue_sheet": state_json["cue_sheet"],
        "reference_match": state_json["reference_match"],
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
    json_output = False
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
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
        else:
            lookahead_count = _parse_nonnegative_int(value, option=option)

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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_readiness_report(
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
                    to_style_performance_arc_live_readiness_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_readiness_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_READINESS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-readiness-report",
    summary="Build passive GUI/audio-analyzer readiness from live state.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_READINESS_CLI_COMMAND)

__all__ = [
    "READINESS_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_READINESS_CLI_COMMAND",
    "StylePerformanceArcLiveReadinessGate",
    "StylePerformanceArcLiveReadinessReport",
    "build_style_performance_arc_live_readiness_from_state",
    "build_style_performance_arc_live_readiness_report",
    "format_style_performance_arc_live_readiness_report",
    "to_style_performance_arc_live_readiness_json",
]
