"""Passive live GUI rehearsal-session packet for analyzer workflows."""

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
from .live_analyzer_targets import StylePerformanceArcLiveAnalyzerCueCheckpoint
from .live_gui_analyzer_readiness import (
    StylePerformanceArcLiveGuiAnalyzerReadinessReport,
    build_style_performance_arc_live_gui_analyzer_readiness_report,
    to_style_performance_arc_live_gui_analyzer_readiness_json,
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live GUI rehearsal session"
SOURCE_MODULE: Final[str] = "reports.live_gui_rehearsal_session"
GUI_REHEARSAL_SESSION_VERSION: Final[str] = "live-gui-rehearsal-session-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "GUI rehearsal session packet only",
    "composes live GUI analyzer readiness only",
    "uses saved-kit snapshots when supplied",
    "operator rehearsal workflow only",
    "future desktop GUI only",
    "future audio analyzer comparison only",
    "session tasks are checklist metadata only",
    "rehearsal takes are listen-only capture guidance",
    "blocked active actions are emitted explicitly",
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
_DEFAULT_MATCH_LIMIT: Final[int] = 3
_DEFAULT_TAKE_COUNT: Final[int] = 2
_DEFAULT_SESSION_LABEL: Final[str] = "Live GUI rehearsal"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-rehearsal-session-report usage: "
    "(--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--label <text>] [--json]"
)
_CLI_OPTIONS: Final[tuple[str, ...]] = (
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
    "--matches",
    "--takes",
    "--label",
    "--json",
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiRehearsalTask:
    """One GUI-visible rehearsal task card."""

    position: int
    key: str
    label: str
    status: str
    panel_key: str
    stream_key: str
    operator_action: str
    pass_condition: str
    hold_if: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiRehearsalTake:
    """One listen-only rehearsal take card."""

    take_number: int
    cue_number: int
    cue_label: str
    timing: str
    status: str
    capture_focus: str
    compare_against: tuple[str, ...]
    operator_prompt: str
    hold_if: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiRehearsalSessionReport:
    """Passive session packet for a future live GUI rehearsal surface."""

    gui_readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport
    session_version: str
    session_id: str
    session_label: str
    session_status: str
    session_mode: str
    tasks: tuple[StylePerformanceArcLiveGuiRehearsalTask, ...]
    takes: tuple[StylePerformanceArcLiveGuiRehearsalTake, ...]
    checklist: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.gui_readiness.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.gui_readiness.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.gui_readiness.scope

    @property
    def source_kind(self) -> str:
        """Return selected reference source kind."""

        return self.gui_readiness.source_kind


def _source_count(
    *,
    description: str | None,
    feature_report: FeatureReport | None,
    audio_path: Path | None,
    library_path: Path | None,
) -> int:
    return sum(
        (
            description is not None,
            feature_report is not None,
            audio_path is not None,
            library_path is not None,
        )
    )


def _session_id(
    readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport,
    *,
    session_label: str,
    take_count: int,
) -> str:
    payload = "|".join(
        (
            GUI_REHEARSAL_SESSION_VERSION,
            readiness.gui_bundle_id,
            readiness.analyzer_targets.target_packet_id,
            session_label,
            str(take_count),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _has_manual_tempo(readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport) -> bool:
    return any(
        threshold.key == "manual-tempo"
        for threshold in readiness.analyzer_targets.warning_thresholds
    )


def _has_hold_warning(readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport) -> bool:
    return any(
        threshold.severity == "hold" for threshold in readiness.analyzer_targets.warning_thresholds
    )


def _has_blocking_hold_warning(
    readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport,
) -> bool:
    if readiness.source_kind == "description":
        return False
    return _has_hold_warning(readiness)


def _session_status(readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport) -> str:
    if _has_blocking_hold_warning(readiness):
        return "guarded"
    if readiness.gui_status == "rehearsal-ready":
        return "ready"
    return readiness.gui_status


def _warning_hold_text(readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport) -> str:
    if _has_manual_tempo(readiness):
        return "manual tempo is unresolved."
    if _has_hold_warning(readiness):
        return "a hold-level analyzer threshold is active."
    return "two or more warning thresholds trip at once."


def _task(
    position: int,
    key: str,
    label: str,
    status: str,
    panel_key: str,
    stream_key: str,
    operator_action: str,
    pass_condition: str,
    hold_if: str,
) -> StylePerformanceArcLiveGuiRehearsalTask:
    return StylePerformanceArcLiveGuiRehearsalTask(
        position=position,
        key=key,
        label=label,
        status=status,
        panel_key=panel_key,
        stream_key=stream_key,
        operator_action=operator_action,
        pass_condition=pass_condition,
        hold_if=hold_if,
    )


def _tasks(
    readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport,
) -> tuple[StylePerformanceArcLiveGuiRehearsalTask, ...]:
    warning_status = "guarded" if _has_blocking_hold_warning(readiness) else "watch"
    return (
        _task(
            1,
            "source-confirmation",
            "Source confirmation",
            readiness.gui_status,
            "overview",
            "target-bands",
            "Confirm the selected arc, source kind, and machine scope.",
            "The selected arc, source, and scope match the intended rehearsal.",
            "The selected arc or machine scope is wrong.",
        ),
        _task(
            2,
            "listen-only-capture",
            "Listen-only capture",
            "ready",
            "transport",
            "feature-meters",
            "Capture the current cue while the GUI/analyzer remains listen-only.",
            "Meters move and no MIDI ports open.",
            "Any active MIDI send, port-open, or command-execution path appears.",
        ),
        _task(
            3,
            "target-compare",
            "Target compare",
            readiness.analyzer_targets.target_status,
            "analyzer-targets",
            "target-bands",
            "Compare live meter values against target windows for the active cue.",
            "Tempo, low-end, brightness, texture, and energy stay inside guidance.",
            "The live cue drifts outside the target bands for the selected arc.",
        ),
        _task(
            4,
            "warning-review",
            "Warning review",
            warning_status,
            "warning-thresholds",
            "warning-thresholds",
            "Review warning thresholds before moving to the next rehearsal take.",
            "No hold-level warnings remain active.",
            _warning_hold_text(readiness),
        ),
        _task(
            5,
            "operator-notes",
            "Operator notes",
            "ready",
            "replay-safety",
            "cue-checkpoints",
            "Write a short decision note: go, repeat, or hold.",
            "The next action is explainable without guessing.",
            "The operator cannot explain why the cue should move forward.",
        ),
    )


def _take_hold_text(
    readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport,
    checkpoint: StylePerformanceArcLiveAnalyzerCueCheckpoint,
) -> str:
    if _has_manual_tempo(readiness):
        return "Tempo is unknown; enter BPM or run audio extraction before compare."
    if checkpoint.status in {"red", "hold", "blocked"}:
        return "Cue status is red/hold/blocked."
    return "Capture confidence is low or warning thresholds trip."


def _takes(
    readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport,
    *,
    take_count: int,
) -> tuple[StylePerformanceArcLiveGuiRehearsalTake, ...]:
    checkpoints = readiness.analyzer_targets.cue_checkpoints[:take_count]
    return tuple(
        StylePerformanceArcLiveGuiRehearsalTake(
            take_number=position,
            cue_number=checkpoint.cue_number,
            cue_label=checkpoint.cue_label,
            timing=checkpoint.timing,
            status=checkpoint.status,
            capture_focus=checkpoint.expected_focus,
            compare_against=checkpoint.target_keys,
            operator_prompt=checkpoint.operator_prompt,
            hold_if=_take_hold_text(readiness, checkpoint),
        )
        for position, checkpoint in enumerate(checkpoints, start=1)
    )


def _checklist() -> tuple[str, ...]:
    return (
        "Keep the GUI/analyzer in listen-only mode for the full rehearsal session.",
        "Confirm the selected saved-kit snapshots before interpreting machine cards.",
        "Capture at least 16 bars before judging target-band drift.",
        "Record go, repeat, or hold after every rehearsal take.",
        "Treat every replay command as passive CLI output only.",
    )


def _blocked_actions(
    readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport,
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            (
                *readiness.blocked_actions,
                "no automatic rehearsal recording",
                "no live analyzer input activation",
                "no GUI-triggered MIDI sends",
                "no automatic kit mutation",
            )
        )
    )


def _source_option(readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport) -> str:
    handoff = readiness.analyzer_targets.analyzer_handoff
    if handoff.source_kind == "description":
        return f"--description {powershell_literal_arg(handoff.reference_match.description or '')}"
    if handoff.source_kind in {"audio", "library"}:
        return f"--{handoff.source_kind} {powershell_literal_arg(handoff.source_reference or '')}"
    return "--description '<feature report target>'"


def _replay_command(
    readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport,
    *,
    take_count: int,
    session_label: str,
) -> str:
    return (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-rehearsal-session-report "
        f"{_source_option(readiness)} "
        f"--matches {len(readiness.analyzer_targets.analyzer_handoff.match_cards)} "
        f"--takes {take_count} --label {powershell_literal_arg(session_label)}"
    )


def build_style_performance_arc_live_gui_rehearsal_session_from_readiness(
    readiness: StylePerformanceArcLiveGuiAnalyzerReadinessReport,
    *,
    take_count: int = _DEFAULT_TAKE_COUNT,
    session_label: str = _DEFAULT_SESSION_LABEL,
) -> StylePerformanceArcLiveGuiRehearsalSessionReport:
    """Build a passive GUI rehearsal-session packet from GUI/analyzer readiness."""

    if take_count < 1:
        raise ValueError("take_count must be >= 1")
    if not session_label.strip():
        raise ValueError("label must not be blank")
    label = session_label.strip()
    return StylePerformanceArcLiveGuiRehearsalSessionReport(
        gui_readiness=readiness,
        session_version=GUI_REHEARSAL_SESSION_VERSION,
        session_id=_session_id(readiness, session_label=label, take_count=take_count),
        session_label=label,
        session_status=_session_status(readiness),
        session_mode="listen-only rehearsal",
        tasks=_tasks(readiness),
        takes=_takes(readiness, take_count=take_count),
        checklist=_checklist(),
        blocked_actions=_blocked_actions(readiness),
        replay_commands=(
            _replay_command(readiness, take_count=take_count, session_label=label),
            *readiness.replay_commands,
        ),
    )


def build_style_performance_arc_live_gui_rehearsal_session_report(
    *,
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
    match_limit: int = _DEFAULT_MATCH_LIMIT,
    take_count: int = _DEFAULT_TAKE_COUNT,
    session_label: str = _DEFAULT_SESSION_LABEL,
) -> StylePerformanceArcLiveGuiRehearsalSessionReport:
    """Build passive GUI rehearsal-session readiness from reference evidence."""

    if (
        _source_count(
            description=description,
            feature_report=feature_report,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError("live GUI rehearsal session report requires exactly one reference source")
    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if rytm_sysex_path is None and analog_four_sysex_path is None:
        raise ValueError("live GUI rehearsal session report requires saved-kit source paths")
    if match_limit < 1:
        raise ValueError("match_limit must be >= 1")
    if take_count < 1:
        raise ValueError("take_count must be >= 1")

    readiness = build_style_performance_arc_live_gui_analyzer_readiness_report(
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
        match_limit=match_limit,
    )
    return build_style_performance_arc_live_gui_rehearsal_session_from_readiness(
        readiness,
        take_count=take_count,
        session_label=session_label,
    )


def _task_json(task: StylePerformanceArcLiveGuiRehearsalTask) -> dict[str, object]:
    return {
        "position": task.position,
        "key": task.key,
        "label": task.label,
        "status": task.status,
        "panel_key": task.panel_key,
        "stream_key": task.stream_key,
        "operator_action": task.operator_action,
        "pass_condition": task.pass_condition,
        "hold_if": task.hold_if,
    }


def _take_json(take: StylePerformanceArcLiveGuiRehearsalTake) -> dict[str, object]:
    return {
        "take_number": take.take_number,
        "cue_number": take.cue_number,
        "cue_label": take.cue_label,
        "timing": take.timing,
        "status": take.status,
        "capture_focus": take.capture_focus,
        "compare_against": list(take.compare_against),
        "operator_prompt": take.operator_prompt,
        "hold_if": take.hold_if,
    }


def to_style_performance_arc_live_gui_rehearsal_session_json(
    report: StylePerformanceArcLiveGuiRehearsalSessionReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI rehearsal-session payload."""

    readiness_json = to_style_performance_arc_live_gui_analyzer_readiness_json(report.gui_readiness)
    return {
        "live_gui_rehearsal_session": {
            "session_version": report.session_version,
            "session_id": report.session_id,
            "session_label": report.session_label,
            "session_status": report.session_status,
            "session_mode": report.session_mode,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "source_kind": report.source_kind,
            "gui_bundle_id": report.gui_readiness.gui_bundle_id,
            "tasks": [_task_json(task) for task in report.tasks],
            "takes": [_take_json(take) for take in report.takes],
            "checklist": list(report.checklist),
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "live_gui_analyzer_readiness": readiness_json["live_gui_analyzer_readiness"],
        "live_analyzer_targets": readiness_json["live_analyzer_targets"],
        "live_analyzer_handoff": readiness_json["live_analyzer_handoff"],
        "live_control_surface": readiness_json["live_control_surface"],
        "live_readiness": readiness_json["live_readiness"],
        "live_state_packet": readiness_json["live_state_packet"],
        "live_command_deck": readiness_json["live_command_deck"],
        "reference_match": readiness_json["reference_match"],
        "safety": list(SAFETY_LINES),
    }


def _task_lines(task: StylePerformanceArcLiveGuiRehearsalTask) -> list[str]:
    return [
        f"- {task.position}. {task.key} / {task.label}: {task.status}",
        f"  Panel: {task.panel_key}",
        f"  Stream: {task.stream_key}",
        f"  Action: {task.operator_action}",
        f"  Pass: {task.pass_condition}",
        f"  Hold if: {task.hold_if}",
    ]


def _take_lines(take: StylePerformanceArcLiveGuiRehearsalTake) -> list[str]:
    compare_against = ", ".join(take.compare_against) if take.compare_against else "none"
    return [
        f"- Take {take.take_number}: cue {take.cue_number} / {take.cue_label}",
        f"  Timing: {take.timing}",
        f"  Status: {take.status}",
        f"  Capture focus: {take.capture_focus}",
        f"  Compare against: {compare_against}",
        f"  Prompt: {take.operator_prompt}",
        f"  Hold if: {take.hold_if}",
    ]


def format_style_performance_arc_live_gui_rehearsal_session_report(
    report: StylePerformanceArcLiveGuiRehearsalSessionReport,
) -> list[str]:
    """Return deterministic passive live GUI rehearsal-session lines."""

    lines = [
        "Live GUI rehearsal session summary:",
        f"- Session version: {report.session_version}",
        f"- Session id: {report.session_id}",
        f"- Session label: {report.session_label}",
        f"- Session status: {report.session_status}",
        f"- Session mode: {report.session_mode}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        f"- Source kind: {report.source_kind}",
        f"- GUI bundle id: {report.gui_readiness.gui_bundle_id}",
        "Session task cards:",
    ]
    for task in report.tasks:
        lines.extend(_task_lines(task))
    lines.append("Rehearsal take cards:")
    for take in report.takes:
        lines.extend(_take_lines(take))
    lines.extend(
        [
            "Operator checklist:",
            *[f"- {item}" for item in report.checklist],
            "Blocked active actions:",
            *[f"- {action}" for action in report.blocked_actions],
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
    return pop_option_value(remaining, usage=_USAGE)


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
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
    match_limit = _DEFAULT_MATCH_LIMIT
    take_count = _DEFAULT_TAKE_COUNT
    session_label = _DEFAULT_SESSION_LABEL
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
        if option == "--description":
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
        elif option == "--matches":
            match_limit = _parse_positive_int(value, option=option)
        elif option == "--takes":
            take_count = _parse_positive_int(value, option=option)
        else:
            if not value.strip():
                raise ValueError("label must not be blank")
            session_label = value

    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if (
        _source_count(
            description=description,
            feature_report=None,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError(_USAGE)

    return {
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
        "match_limit": match_limit,
        "take_count": take_count,
        "session_label": session_label,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
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
    match_limit: int,
    take_count: int,
    session_label: str,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_rehearsal_session_report(
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
            match_limit=match_limit,
            take_count=take_count,
            session_label=session_label,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_rehearsal_session_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_rehearsal_session_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


STYLE_PERFORMANCE_ARC_LIVE_GUI_REHEARSAL_SESSION_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-rehearsal-session-report",
    summary="Build passive GUI rehearsal session packets.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_REHEARSAL_SESSION_CLI_COMMAND)

__all__ = [
    "GUI_REHEARSAL_SESSION_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_REHEARSAL_SESSION_CLI_COMMAND",
    "StylePerformanceArcLiveGuiRehearsalSessionReport",
    "StylePerformanceArcLiveGuiRehearsalTake",
    "StylePerformanceArcLiveGuiRehearsalTask",
    "build_style_performance_arc_live_gui_rehearsal_session_from_readiness",
    "build_style_performance_arc_live_gui_rehearsal_session_report",
    "format_style_performance_arc_live_gui_rehearsal_session_report",
    "to_style_performance_arc_live_gui_rehearsal_session_json",
]
