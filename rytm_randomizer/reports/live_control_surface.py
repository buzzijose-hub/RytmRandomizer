"""Passive live control surface for GUI/audio-analyzer routing."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol

from ..cli_registry import CliCommand, register
from ..style_analysis.feature_report import FeatureReport
from .dual_machine_style_kit_selection import normalize_selection_scope
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)
from .live_performance_readiness import (
    StylePerformanceArcLiveReadinessGate,
    StylePerformanceArcLiveReadinessReport,
    build_style_performance_arc_live_readiness_report,
    to_style_performance_arc_live_readiness_json,
)
from .live_performance_state import (
    StylePerformanceArcLiveStateCue,
    StylePerformanceArcLiveStateMachine,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live control surface"
SOURCE_MODULE: Final[str] = "reports.live_control_surface"
CONTROL_SURFACE_VERSION: Final[str] = "live-control-surface-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live control surface report only",
    "composes live readiness report only",
    "uses saved-kit snapshots when supplied",
    "GUI/audio-analyzer control surface only",
    "audio analyzer preview only",
    "influence matching only",
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
    "style-performance-arc-live-control-surface-report usage: "
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


class _SelectionSource(Protocol):
    """Small protocol for reports that can be replayed from a selection source."""

    selection_source: str
    source_reference: str | None
    selected_arc_key: str


@dataclass(frozen=True)
class StylePerformanceArcLiveControlSurfaceTile:
    """One compact header tile for the passive live control surface."""

    key: str
    label: str
    value: str
    status: str


@dataclass(frozen=True)
class StylePerformanceArcLiveControlSurfaceCueCard:
    """One now/next cue card for the passive live control surface."""

    cue_number: int
    cue_label: str
    status_light: str
    warning_level: str
    go_no_go: str
    phase: str
    style_key: str
    screen_state: str
    prompt: str
    primary_action: str
    listen_for: str
    machine_focus: str
    route_status: str
    blocker_summary: str
    recovery_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveControlSurfaceMachineCard:
    """One machine card for the passive live control surface."""

    machine: str
    label: str
    status_light: str
    arm_state: str
    ui_badge: str
    handoff_label: str
    slot_summary: str
    kit_summary: str
    fingerprint_summary: str
    planned_units: tuple[int, ...]
    row_summary: str
    operator_check: str


@dataclass(frozen=True)
class StylePerformanceArcLiveControlSurfaceAnalyzerCard:
    """One audio-analyzer handoff card for influence matching."""

    key: str
    label: str
    status: str
    source: str
    prompt: str


@dataclass(frozen=True)
class StylePerformanceArcLiveControlSurfaceDecision:
    """One decision strip item copied from readiness gates."""

    key: str
    label: str
    status: str
    severity: str
    action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveControlSurfaceReport:
    """Passive GUI/audio-analyzer control-surface packet."""

    readiness_report: StylePerformanceArcLiveReadinessReport
    control_surface_version: str
    surface_id: str
    surface_title: str
    surface_status: str
    surface_mode: str
    header_tiles: tuple[StylePerformanceArcLiveControlSurfaceTile, ...]
    transport_controls: tuple[str, ...]
    now_cue: StylePerformanceArcLiveControlSurfaceCueCard
    next_cues: tuple[StylePerformanceArcLiveControlSurfaceCueCard, ...]
    machine_cards: tuple[StylePerformanceArcLiveControlSurfaceMachineCard, ...]
    analyzer_cards: tuple[StylePerformanceArcLiveControlSurfaceAnalyzerCard, ...]
    decision_strip: tuple[StylePerformanceArcLiveControlSurfaceDecision, ...]
    recovery_controls: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.readiness_report.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.readiness_report.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.readiness_report.scope


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


def _source_option(source: _SelectionSource) -> str:
    if source.selection_source in {"arc", "description", "audio", "library"}:
        source_reference = source.source_reference or source.selected_arc_key
        return f"--{source.selection_source} {powershell_literal_arg(source_reference)}"
    return f"--arc {source.selected_arc_key}"


def _number_sequence(values: Sequence[int]) -> str:
    if not values:
        return "none"
    return ", ".join(str(value) for value in values)


def _warning_level(cue: StylePerformanceArcLiveStateCue) -> str:
    if cue.go_no_go == "do-not-arm" or cue.status_light == "RED":
        return "critical"
    if cue.go_no_go == "go" and cue.status_light == "GREEN":
        return "info"
    return "warning"


def _cue_card(
    cue: StylePerformanceArcLiveStateCue,
) -> StylePerformanceArcLiveControlSurfaceCueCard:
    return StylePerformanceArcLiveControlSurfaceCueCard(
        cue_number=cue.cue_number,
        cue_label=cue.cue_label,
        status_light=cue.status_light,
        warning_level=_warning_level(cue),
        go_no_go=cue.go_no_go,
        phase=cue.phase,
        style_key=cue.style_key,
        screen_state=cue.screen_state,
        prompt=cue.operator_prompt,
        primary_action=cue.primary_action,
        listen_for=cue.listen_for,
        machine_focus=cue.machine_focus,
        route_status=cue.route_status,
        blocker_summary=cue.blocker_summary,
        recovery_action=cue.recovery_action,
    )


def _machine_card(
    machine: StylePerformanceArcLiveStateMachine,
) -> StylePerformanceArcLiveControlSurfaceMachineCard:
    return StylePerformanceArcLiveControlSurfaceMachineCard(
        machine=machine.machine,
        label=machine.label,
        status_light=machine.status_light,
        arm_state=machine.arm_state,
        ui_badge=machine.ui_badge,
        handoff_label=machine.handoff_label,
        slot_summary=machine.slot_summary,
        kit_summary=machine.kit_summary,
        fingerprint_summary=machine.fingerprint_summary,
        planned_units=machine.planned_units,
        row_summary=machine.row_summary,
        operator_check=machine.operator_check,
    )


def _decision(
    gate: StylePerformanceArcLiveReadinessGate,
) -> StylePerformanceArcLiveControlSurfaceDecision:
    return StylePerformanceArcLiveControlSurfaceDecision(
        key=gate.key,
        label=gate.label,
        status=gate.status,
        severity=gate.severity,
        action=gate.operator_action,
    )


def _header_tiles(
    readiness: StylePerformanceArcLiveReadinessReport,
) -> tuple[StylePerformanceArcLiveControlSurfaceTile, ...]:
    live_state = readiness.live_state
    return (
        StylePerformanceArcLiveControlSurfaceTile(
            "arc",
            "Arc",
            f"{readiness.selected_arc_key} / {readiness.selected_arc_name}",
            "ready",
        ),
        StylePerformanceArcLiveControlSurfaceTile(
            "status",
            "Status",
            readiness.overall_status,
            readiness.overall_status,
        ),
        StylePerformanceArcLiveControlSurfaceTile(
            "scope",
            "Scope",
            readiness.scope,
            "ready",
        ),
        StylePerformanceArcLiveControlSurfaceTile(
            "cue",
            "Cue",
            f"{live_state.current_cue.cue_number} of {len(live_state.command_deck.timeline.transition_cards)}",
            live_state.current_cue.go_no_go,
        ),
        StylePerformanceArcLiveControlSurfaceTile(
            "machine-summary",
            "Machines",
            readiness.machine_summary,
            "ready" if readiness.overall_status == "performance-ready" else "review",
        ),
    )


def _transport_controls(
    readiness: StylePerformanceArcLiveReadinessReport,
) -> tuple[str, ...]:
    cue = readiness.live_state.current_cue
    if readiness.overall_status == "blocked":
        return (
            "Hold current machine state.",
            f"Recover: {cue.recovery_action}",
            "Keep hardware sends disabled.",
            "Re-run readiness before any armed path.",
        )
    if readiness.overall_status == "performance-ready":
        return (
            f"Confirm cue {cue.cue_number}.",
            "Analyze current audio as influence only.",
            "Preview machine panels.",
            "Keep hardware sends disabled in this passive CLI.",
        )
    return (
        f"Rehearse cue {cue.cue_number}.",
        "Analyze current audio as influence only.",
        "Resolve amber machine cards before arming.",
        "Keep hardware sends disabled in this passive CLI.",
    )


def _analyzer_cards(
    readiness: StylePerformanceArcLiveReadinessReport,
) -> tuple[StylePerformanceArcLiveControlSurfaceAnalyzerCard, ...]:
    cue = readiness.live_state.current_cue
    return (
        StylePerformanceArcLiveControlSurfaceAnalyzerCard(
            "reference",
            "Reference arc",
            "preview",
            readiness.selected_arc_key,
            f"Use {readiness.selected_arc_name} as the influence reference.",
        ),
        StylePerformanceArcLiveControlSurfaceAnalyzerCard(
            "listen-target",
            "Listen target",
            "preview",
            cue.style_key,
            cue.listen_for,
        ),
        StylePerformanceArcLiveControlSurfaceAnalyzerCard(
            "machine-focus",
            "Machine focus",
            "preview",
            cue.machine_focus,
            "Compare current machine energy against this cue focus.",
        ),
        StylePerformanceArcLiveControlSurfaceAnalyzerCard(
            "comparison-rules",
            "Comparison rules",
            "guarded",
            "energy/density/grit/motion",
            "Influence-not-replica: never clone source material or automate hardware sends.",
        ),
    )


def _recovery_controls(
    readiness: StylePerformanceArcLiveReadinessReport,
) -> tuple[str, ...]:
    return (
        *readiness.operator_next_actions,
        *readiness.live_state.recovery_stack,
        "Keep hardware sends disabled in this passive CLI.",
    )


def _surface_id(
    readiness: StylePerformanceArcLiveReadinessReport,
    decisions: Sequence[StylePerformanceArcLiveControlSurfaceDecision],
) -> str:
    digest_input = "|".join(
        (
            readiness.readiness_id,
            readiness.overall_status,
            ",".join(f"{decision.key}:{decision.status}" for decision in decisions),
        )
    )
    digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:8]
    return f"{readiness.readiness_id}-surface-{digest}"


def _surface_command(readiness: StylePerformanceArcLiveReadinessReport) -> str:
    live_state = readiness.live_state
    return (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-control-surface-report "
        f"{_source_option(live_state)} --scope {live_state.scope} "
        f"--cue {live_state.current_cue.cue_number} --lookahead {len(live_state.next_cues)}"
    )


def build_style_performance_arc_live_control_surface_from_readiness(
    readiness_report: StylePerformanceArcLiveReadinessReport,
) -> StylePerformanceArcLiveControlSurfaceReport:
    """Build a passive GUI/audio-analyzer control surface from readiness."""

    decisions = tuple(_decision(gate) for gate in readiness_report.gates)
    return StylePerformanceArcLiveControlSurfaceReport(
        readiness_report=readiness_report,
        control_surface_version=CONTROL_SURFACE_VERSION,
        surface_id=_surface_id(readiness_report, decisions),
        surface_title=f"Cue {readiness_report.live_state.current_cue.cue_number} control surface",
        surface_status=readiness_report.overall_status,
        surface_mode=readiness_report.launch_mode,
        header_tiles=_header_tiles(readiness_report),
        transport_controls=_transport_controls(readiness_report),
        now_cue=_cue_card(readiness_report.live_state.current_cue),
        next_cues=tuple(_cue_card(cue) for cue in readiness_report.live_state.next_cues),
        machine_cards=tuple(
            _machine_card(machine) for machine in readiness_report.live_state.machine_states
        ),
        analyzer_cards=_analyzer_cards(readiness_report),
        decision_strip=decisions,
        recovery_controls=_recovery_controls(readiness_report),
        replay_commands=(
            _surface_command(readiness_report),
            *readiness_report.rehearsal_commands,
        ),
    )


def build_style_performance_arc_live_control_surface_report(
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
) -> StylePerformanceArcLiveControlSurfaceReport:
    """Build a passive live control surface from an arc or reference."""

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
        raise ValueError("live control surface requires exactly one selection source")

    readiness = build_style_performance_arc_live_readiness_report(
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
    return build_style_performance_arc_live_control_surface_from_readiness(readiness)


def _tile_json(tile: StylePerformanceArcLiveControlSurfaceTile) -> dict[str, object]:
    return {
        "key": tile.key,
        "label": tile.label,
        "value": tile.value,
        "status": tile.status,
    }


def _cue_json(card: StylePerformanceArcLiveControlSurfaceCueCard) -> dict[str, object]:
    return {
        "cue_number": card.cue_number,
        "cue_label": card.cue_label,
        "status_light": card.status_light,
        "warning_level": card.warning_level,
        "go_no_go": card.go_no_go,
        "phase": card.phase,
        "style_key": card.style_key,
        "screen_state": card.screen_state,
        "prompt": card.prompt,
        "primary_action": card.primary_action,
        "listen_for": card.listen_for,
        "machine_focus": card.machine_focus,
        "route_status": card.route_status,
        "blocker_summary": card.blocker_summary,
        "recovery_action": card.recovery_action,
    }


def _machine_json(
    card: StylePerformanceArcLiveControlSurfaceMachineCard,
) -> dict[str, object]:
    return {
        "machine": card.machine,
        "label": card.label,
        "status_light": card.status_light,
        "arm_state": card.arm_state,
        "ui_badge": card.ui_badge,
        "handoff_label": card.handoff_label,
        "slot_summary": card.slot_summary,
        "kit_summary": card.kit_summary,
        "fingerprint_summary": card.fingerprint_summary,
        "planned_units": list(card.planned_units),
        "row_summary": card.row_summary,
        "operator_check": card.operator_check,
    }


def _analyzer_json(
    card: StylePerformanceArcLiveControlSurfaceAnalyzerCard,
) -> dict[str, object]:
    return {
        "key": card.key,
        "label": card.label,
        "status": card.status,
        "source": card.source,
        "prompt": card.prompt,
    }


def _decision_json(
    decision: StylePerformanceArcLiveControlSurfaceDecision,
) -> dict[str, object]:
    return {
        "key": decision.key,
        "label": decision.label,
        "status": decision.status,
        "severity": decision.severity,
        "action": decision.action,
    }


def to_style_performance_arc_live_control_surface_json(
    report: StylePerformanceArcLiveControlSurfaceReport,
) -> dict[str, object]:
    """Return deterministic JSON data for the passive live control surface."""

    readiness_json = to_style_performance_arc_live_readiness_json(report.readiness_report)
    return {
        "live_control_surface": {
            "control_surface_version": report.control_surface_version,
            "surface_id": report.surface_id,
            "surface_title": report.surface_title,
            "surface_status": report.surface_status,
            "surface_mode": report.surface_mode,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "header_tiles": [_tile_json(tile) for tile in report.header_tiles],
            "transport_controls": list(report.transport_controls),
            "now_cue": _cue_json(report.now_cue),
            "next_cues": [_cue_json(card) for card in report.next_cues],
            "machine_cards": [_machine_json(card) for card in report.machine_cards],
            "analyzer_cards": [_analyzer_json(card) for card in report.analyzer_cards],
            "decision_strip": [_decision_json(decision) for decision in report.decision_strip],
            "recovery_controls": list(report.recovery_controls),
            "replay_commands": list(report.replay_commands),
        },
        "live_readiness": readiness_json["live_readiness"],
        "live_state_packet": readiness_json["live_state_packet"],
        "live_command_deck": readiness_json["live_command_deck"],
        "live_transition_timeline": readiness_json["live_transition_timeline"],
        "live_show_export": readiness_json["live_show_export"],
        "live_set_cockpit": readiness_json["live_set_cockpit"],
        "stage_rehearsal_state": readiness_json["stage_rehearsal_state"],
        "stage_snapshot_routing": readiness_json["stage_snapshot_routing"],
        "live_runbook": readiness_json["live_runbook"],
        "cue_sheet": readiness_json["cue_sheet"],
        "reference_match": readiness_json["reference_match"],
        "safety": list(SAFETY_LINES),
    }


def _tile_lines(tile: StylePerformanceArcLiveControlSurfaceTile) -> list[str]:
    return [f"- {tile.key} / {tile.label}: {tile.value} | {tile.status}"]


def _cue_lines(
    card: StylePerformanceArcLiveControlSurfaceCueCard,
    *,
    prefix: str,
) -> list[str]:
    return [
        f"- {prefix} {card.cue_number}. {card.cue_label} | {card.status_light} | {card.warning_level}",
        f"  Go / no-go: {card.go_no_go}",
        f"  Phase: {card.phase}",
        f"  Style: {card.style_key}",
        f"  Screen state: {card.screen_state}",
        f"  Prompt: {card.prompt}",
        f"  Primary: {card.primary_action}",
        f"  Listen for: {card.listen_for}",
        f"  Machine focus: {card.machine_focus}",
        f"  Route: {card.route_status}",
        f"  Blockers: {card.blocker_summary}",
        f"  Recovery: {card.recovery_action}",
    ]


def _machine_lines(card: StylePerformanceArcLiveControlSurfaceMachineCard) -> list[str]:
    return [
        f"- {card.label}: {card.status_light} | {card.arm_state} | {card.ui_badge}",
        f"  Handoff: {card.handoff_label}",
        f"  Slot(s): {card.slot_summary}",
        f"  Kit(s): {card.kit_summary}",
        f"  Fingerprint(s): {card.fingerprint_summary}",
        f"  Planned units: {_number_sequence(card.planned_units)}",
        f"  Rows: {card.row_summary}",
        f"  Check: {card.operator_check}",
    ]


def _analyzer_lines(card: StylePerformanceArcLiveControlSurfaceAnalyzerCard) -> list[str]:
    return [
        f"- {card.key} / {card.label}: {card.status}",
        f"  Source: {card.source}",
        f"  Prompt: {card.prompt}",
    ]


def _decision_lines(
    decision: StylePerformanceArcLiveControlSurfaceDecision,
) -> list[str]:
    return [
        f"- {decision.key} / {decision.label}: {decision.status} | {decision.severity}",
        f"  Action: {decision.action}",
    ]


def format_style_performance_arc_live_control_surface_report(
    report: StylePerformanceArcLiveControlSurfaceReport,
) -> list[str]:
    """Return deterministic passive live control surface lines."""

    lines = [
        "Control surface summary:",
        f"- Control surface version: {report.control_surface_version}",
        f"- Surface id: {report.surface_id}",
        f"- Surface title: {report.surface_title}",
        f"- Surface status: {report.surface_status}",
        f"- Surface mode: {report.surface_mode}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        f"- Readiness id: {report.readiness_report.readiness_id}",
        f"- Live state id: {report.readiness_report.live_state.state_id}",
        "Header tiles:",
    ]
    for tile in report.header_tiles:
        lines.extend(_tile_lines(tile))
    lines.extend(
        [
            "Transport controls:",
            *[f"- {control}" for control in report.transport_controls],
            "Now cue:",
            *_cue_lines(report.now_cue, prefix="Now"),
            "Next cue strip:",
        ]
    )
    if not report.next_cues:
        lines.append("- No next cues requested.")
    else:
        for cue in report.next_cues:
            lines.extend(_cue_lines(cue, prefix="Next"))
    lines.append("Machine cards:")
    if not report.machine_cards:
        lines.append("- No machine cards available.")
    else:
        for card in report.machine_cards:
            lines.extend(_machine_lines(card))
    lines.append("Audio analyzer cards:")
    for card in report.analyzer_cards:
        lines.extend(_analyzer_lines(card))
    lines.append("Decision strip:")
    for decision in report.decision_strip:
        lines.extend(_decision_lines(decision))
    lines.extend(
        [
            "Recovery controls:",
            *[f"- {control}" for control in report.recovery_controls],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.replay_commands],
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


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
        report = build_style_performance_arc_live_control_surface_report(
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
                    to_style_performance_arc_live_control_surface_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_control_surface_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_CONTROL_SURFACE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-control-surface-report",
    summary="Build a passive GUI/audio-analyzer control surface from live readiness.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_CONTROL_SURFACE_CLI_COMMAND)

__all__ = [
    "CONTROL_SURFACE_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_CONTROL_SURFACE_CLI_COMMAND",
    "StylePerformanceArcLiveControlSurfaceAnalyzerCard",
    "StylePerformanceArcLiveControlSurfaceCueCard",
    "StylePerformanceArcLiveControlSurfaceDecision",
    "StylePerformanceArcLiveControlSurfaceMachineCard",
    "StylePerformanceArcLiveControlSurfaceReport",
    "StylePerformanceArcLiveControlSurfaceTile",
    "build_style_performance_arc_live_control_surface_from_readiness",
    "build_style_performance_arc_live_control_surface_report",
    "format_style_performance_arc_live_control_surface_report",
    "to_style_performance_arc_live_control_surface_json",
]
