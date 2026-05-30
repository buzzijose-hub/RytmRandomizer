"""Passive live GUI/audio-analyzer capture queue for rehearsal workflows."""

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
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value
from .live_gui_rehearsal_session import (
    StylePerformanceArcLiveGuiRehearsalSessionReport,
    StylePerformanceArcLiveGuiRehearsalTake,
    build_style_performance_arc_live_gui_rehearsal_session_report,
    to_style_performance_arc_live_gui_rehearsal_session_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live GUI capture queue"
SOURCE_MODULE: Final[str] = "reports.live_gui_capture_queue"
GUI_CAPTURE_QUEUE_VERSION: Final[str] = "live-gui-capture-queue-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "GUI/audio analyzer capture queue only",
    "composes live GUI rehearsal session only",
    "uses saved-kit snapshots when supplied",
    "operator capture queue workflow only",
    "future desktop GUI only",
    "future audio analyzer comparison only",
    "capture slots are metadata only",
    "analyzer jobs are job-card metadata only",
    "blocked active actions are emitted explicitly",
    "JSON/stdout only",
    "no file writing",
    "no audio recording",
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
_DEFAULT_QUEUE_LABEL: Final[str] = "Live GUI capture queue"
_DEFAULT_CAPTURE_PREFIX: Final[str] = "rehearsal"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-capture-queue-report usage: "
    "(--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--label <text>] [--capture-prefix <text>] [--json]"
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
    "--capture-prefix",
    "--json",
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiCaptureSlot:
    """One GUI-visible listen-only capture slot."""

    slot_number: int
    key: str
    take_number: int
    cue_number: int
    cue_label: str
    status: str
    capture_label: str
    capture_focus: str
    capture_window: str
    suggested_filename: str
    source_stream: str
    compare_against: tuple[str, ...]
    operator_prompt: str
    hold_if: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerJob:
    """One future analyzer comparison job card."""

    position: int
    key: str
    status: str
    input_slot_key: str
    target_packet_id: str
    comparison_profile: str
    operator_action: str
    acceptance_criteria: str
    hold_if: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiCaptureQueueReport:
    """Passive capture queue packet for future GUI/audio-analyzer consumers."""

    rehearsal_session: StylePerformanceArcLiveGuiRehearsalSessionReport
    queue_version: str
    queue_id: str
    queue_label: str
    queue_status: str
    capture_mode: str
    capture_slots: tuple[StylePerformanceArcLiveGuiCaptureSlot, ...]
    analyzer_jobs: tuple[StylePerformanceArcLiveGuiAnalyzerJob, ...]
    checklist: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.rehearsal_session.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.rehearsal_session.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.rehearsal_session.scope

    @property
    def source_kind(self) -> str:
        """Return selected reference source kind."""

        return self.rehearsal_session.source_kind


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


def _queue_id(
    session: StylePerformanceArcLiveGuiRehearsalSessionReport,
    *,
    queue_label: str,
    capture_prefix: str,
) -> str:
    payload = "|".join(
        (
            GUI_CAPTURE_QUEUE_VERSION,
            session.session_id,
            session.gui_readiness.gui_bundle_id,
            queue_label,
            capture_prefix,
            str(len(session.takes)),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _queue_status(session: StylePerformanceArcLiveGuiRehearsalSessionReport) -> str:
    if session.session_status == "ready":
        return "queued"
    if session.session_status == "guarded":
        return "guarded"
    return session.session_status


def _slot_status(
    session: StylePerformanceArcLiveGuiRehearsalSessionReport,
    take: StylePerformanceArcLiveGuiRehearsalTake,
) -> str:
    if session.session_status == "ready" and take.status not in {"red", "hold", "blocked"}:
        return "queued"
    if session.session_status == "ready":
        return "guarded"
    return session.session_status


def _slug(text: str) -> str:
    pieces: list[str] = []
    previous_dash = False
    for char in text.strip().lower():
        if char.isalnum():
            pieces.append(char)
            previous_dash = False
        elif not previous_dash:
            pieces.append("-")
            previous_dash = True
    slug = "".join(pieces).strip("-")
    if slug:
        return slug
    return _DEFAULT_CAPTURE_PREFIX


def _capture_window(take: StylePerformanceArcLiveGuiRehearsalTake) -> str:
    if take.timing == "current cue":
        return "capture 16-32 bars now"
    if take.timing == "next cue":
        return "arm listen-only capture at next cue"
    return f"capture during {take.timing}"


def _slot(
    session: StylePerformanceArcLiveGuiRehearsalSessionReport,
    take: StylePerformanceArcLiveGuiRehearsalTake,
    *,
    capture_prefix: str,
) -> StylePerformanceArcLiveGuiCaptureSlot:
    slot_number = take.take_number
    prefix = _slug(capture_prefix)
    capture_label = f"{prefix}-take-{slot_number:03d}"
    return StylePerformanceArcLiveGuiCaptureSlot(
        slot_number=slot_number,
        key=f"capture-{slot_number:03d}",
        take_number=take.take_number,
        cue_number=take.cue_number,
        cue_label=take.cue_label,
        status=_slot_status(session, take),
        capture_label=capture_label,
        capture_focus=take.capture_focus,
        capture_window=_capture_window(take),
        suggested_filename=f"{capture_label}_cue_{take.cue_number:03d}_take_{slot_number:03d}.wav",
        source_stream="feature-meters",
        compare_against=take.compare_against,
        operator_prompt=take.operator_prompt,
        hold_if=take.hold_if,
    )


def _capture_slots(
    session: StylePerformanceArcLiveGuiRehearsalSessionReport,
    *,
    capture_prefix: str,
) -> tuple[StylePerformanceArcLiveGuiCaptureSlot, ...]:
    return tuple(_slot(session, take, capture_prefix=capture_prefix) for take in session.takes)


def _job_hold_text(slot: StylePerformanceArcLiveGuiCaptureSlot) -> str:
    if slot.status == "queued":
        return "Live meter confidence is low or warning thresholds trip."
    if slot.status == "guarded":
        return "Resolve hold state before comparing this capture."
    return f"Queue status is {slot.status}."


def _analyzer_jobs(
    session: StylePerformanceArcLiveGuiRehearsalSessionReport,
    slots: Sequence[StylePerformanceArcLiveGuiCaptureSlot],
) -> tuple[StylePerformanceArcLiveGuiAnalyzerJob, ...]:
    target_packet_id = session.gui_readiness.analyzer_targets.target_packet_id
    return tuple(
        StylePerformanceArcLiveGuiAnalyzerJob(
            position=slot.slot_number,
            key=f"analyze-{slot.slot_number:03d}",
            status=slot.status,
            input_slot_key=slot.key,
            target_packet_id=target_packet_id,
            comparison_profile=session.selected_arc_key,
            operator_action=(
                "Compare the captured take against the active target bands after recording."
            ),
            acceptance_criteria=(
                "BPM, low-end, brightness, texture, and energy settle inside guidance."
            ),
            hold_if=_job_hold_text(slot),
        )
        for slot in slots
    )


def _checklist() -> tuple[str, ...]:
    return (
        "Capture every take as listen-only audio before judging the style match.",
        "Name each capture with the suggested deterministic label.",
        "Compare the capture only after the GUI/analyzer reports stable meters.",
        "Keep every analyzer job passive until a separate armed workflow exists.",
        "Record go, repeat, or hold for every capture slot.",
    )


def _blocked_actions(
    session: StylePerformanceArcLiveGuiRehearsalSessionReport,
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            (
                *session.blocked_actions,
                "no automatic audio recording",
                "no live input activation",
                "no automatic analyzer job execution",
                "no GUI-triggered MIDI sends",
                "no automatic kit mutation",
            )
        )
    )


def _source_option(session: StylePerformanceArcLiveGuiRehearsalSessionReport) -> str:
    handoff = session.gui_readiness.analyzer_targets.analyzer_handoff
    if handoff.source_kind == "description":
        return f"--description {powershell_literal_arg(handoff.reference_match.description or '')}"
    if handoff.source_kind in {"audio", "library"}:
        return f"--{handoff.source_kind} {powershell_literal_arg(handoff.source_reference or '')}"
    return "--description '<feature report target>'"


def _replay_command(
    session: StylePerformanceArcLiveGuiRehearsalSessionReport,
    *,
    queue_label: str,
    capture_prefix: str,
) -> str:
    targets = session.gui_readiness.analyzer_targets
    return (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-capture-queue-report "
        f"{_source_option(session)} "
        f"--matches {len(targets.analyzer_handoff.match_cards)} "
        f"--takes {len(session.takes)} "
        f"--label {powershell_literal_arg(queue_label)} "
        f"--capture-prefix {powershell_literal_arg(capture_prefix)}"
    )


def build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session(
    session: StylePerformanceArcLiveGuiRehearsalSessionReport,
    *,
    queue_label: str = _DEFAULT_QUEUE_LABEL,
    capture_prefix: str = _DEFAULT_CAPTURE_PREFIX,
) -> StylePerformanceArcLiveGuiCaptureQueueReport:
    """Build a passive capture queue from a GUI rehearsal-session packet."""

    if not queue_label.strip():
        raise ValueError("label must not be blank")
    if not capture_prefix.strip():
        raise ValueError("capture_prefix must not be blank")
    if not session.takes:
        raise ValueError("capture queue requires at least one rehearsal take")
    label = queue_label.strip()
    prefix = capture_prefix.strip()
    slots = _capture_slots(session, capture_prefix=prefix)
    return StylePerformanceArcLiveGuiCaptureQueueReport(
        rehearsal_session=session,
        queue_version=GUI_CAPTURE_QUEUE_VERSION,
        queue_id=_queue_id(session, queue_label=label, capture_prefix=prefix),
        queue_label=label,
        queue_status=_queue_status(session),
        capture_mode="listen-only audio capture",
        capture_slots=slots,
        analyzer_jobs=_analyzer_jobs(session, slots),
        checklist=_checklist(),
        blocked_actions=_blocked_actions(session),
        replay_commands=(
            _replay_command(session, queue_label=label, capture_prefix=prefix),
            *session.replay_commands,
        ),
    )


def build_style_performance_arc_live_gui_capture_queue_report(
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
    queue_label: str = _DEFAULT_QUEUE_LABEL,
    capture_prefix: str = _DEFAULT_CAPTURE_PREFIX,
) -> StylePerformanceArcLiveGuiCaptureQueueReport:
    """Build passive GUI capture-queue readiness from reference evidence."""

    if (
        _source_count(
            description=description,
            feature_report=feature_report,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError("live GUI capture queue report requires exactly one reference source")
    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if rytm_sysex_path is None and analog_four_sysex_path is None:
        raise ValueError("live GUI capture queue report requires saved-kit source paths")
    if match_limit < 1:
        raise ValueError("match_limit must be >= 1")
    if take_count < 1:
        raise ValueError("take_count must be >= 1")

    session = build_style_performance_arc_live_gui_rehearsal_session_report(
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
        take_count=take_count,
        session_label=queue_label,
    )
    return build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session(
        session,
        queue_label=queue_label,
        capture_prefix=capture_prefix,
    )


def _slot_json(slot: StylePerformanceArcLiveGuiCaptureSlot) -> dict[str, object]:
    return {
        "slot_number": slot.slot_number,
        "key": slot.key,
        "take_number": slot.take_number,
        "cue_number": slot.cue_number,
        "cue_label": slot.cue_label,
        "status": slot.status,
        "capture_label": slot.capture_label,
        "capture_focus": slot.capture_focus,
        "capture_window": slot.capture_window,
        "suggested_filename": slot.suggested_filename,
        "source_stream": slot.source_stream,
        "compare_against": list(slot.compare_against),
        "operator_prompt": slot.operator_prompt,
        "hold_if": slot.hold_if,
    }


def _job_json(job: StylePerformanceArcLiveGuiAnalyzerJob) -> dict[str, object]:
    return {
        "position": job.position,
        "key": job.key,
        "status": job.status,
        "input_slot_key": job.input_slot_key,
        "target_packet_id": job.target_packet_id,
        "comparison_profile": job.comparison_profile,
        "operator_action": job.operator_action,
        "acceptance_criteria": job.acceptance_criteria,
        "hold_if": job.hold_if,
    }


def to_style_performance_arc_live_gui_capture_queue_json(
    report: StylePerformanceArcLiveGuiCaptureQueueReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI capture queue payload."""

    session_json = to_style_performance_arc_live_gui_rehearsal_session_json(
        report.rehearsal_session
    )
    return {
        "live_gui_capture_queue": {
            "queue_version": report.queue_version,
            "queue_id": report.queue_id,
            "queue_label": report.queue_label,
            "queue_status": report.queue_status,
            "capture_mode": report.capture_mode,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "source_kind": report.source_kind,
            "session_id": report.rehearsal_session.session_id,
            "gui_bundle_id": report.rehearsal_session.gui_readiness.gui_bundle_id,
            "capture_slots": [_slot_json(slot) for slot in report.capture_slots],
            "analyzer_jobs": [_job_json(job) for job in report.analyzer_jobs],
            "checklist": list(report.checklist),
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "live_gui_rehearsal_session": session_json["live_gui_rehearsal_session"],
        "live_gui_analyzer_readiness": session_json["live_gui_analyzer_readiness"],
        "live_analyzer_targets": session_json["live_analyzer_targets"],
        "live_analyzer_handoff": session_json["live_analyzer_handoff"],
        "live_control_surface": session_json["live_control_surface"],
        "live_readiness": session_json["live_readiness"],
        "live_state_packet": session_json["live_state_packet"],
        "live_command_deck": session_json["live_command_deck"],
        "reference_match": session_json["reference_match"],
        "safety": list(SAFETY_LINES),
    }


def _slot_lines(slot: StylePerformanceArcLiveGuiCaptureSlot) -> list[str]:
    compare_against = ", ".join(slot.compare_against) if slot.compare_against else "none"
    return [
        f"- Slot {slot.slot_number}: {slot.key} / {slot.capture_label}: {slot.status}",
        f"  Cue: {slot.cue_number} / {slot.cue_label}",
        f"  Focus: {slot.capture_focus}",
        f"  Window: {slot.capture_window}",
        f"  Suggested file: {slot.suggested_filename}",
        f"  Source stream: {slot.source_stream}",
        f"  Compare against: {compare_against}",
        f"  Prompt: {slot.operator_prompt}",
        f"  Hold if: {slot.hold_if}",
    ]


def _job_lines(job: StylePerformanceArcLiveGuiAnalyzerJob) -> list[str]:
    return [
        f"- {job.position}. {job.key}: {job.status}",
        f"  Input slot: {job.input_slot_key}",
        f"  Target packet: {job.target_packet_id}",
        f"  Comparison profile: {job.comparison_profile}",
        f"  Action: {job.operator_action}",
        f"  Pass: {job.acceptance_criteria}",
        f"  Hold if: {job.hold_if}",
    ]


def format_style_performance_arc_live_gui_capture_queue_report(
    report: StylePerformanceArcLiveGuiCaptureQueueReport,
) -> list[str]:
    """Return deterministic passive live GUI capture queue lines."""

    lines = [
        "Live GUI capture queue summary:",
        f"- Queue version: {report.queue_version}",
        f"- Queue id: {report.queue_id}",
        f"- Queue label: {report.queue_label}",
        f"- Queue status: {report.queue_status}",
        f"- Capture mode: {report.capture_mode}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        f"- Source kind: {report.source_kind}",
        f"- Session id: {report.rehearsal_session.session_id}",
        f"- GUI bundle id: {report.rehearsal_session.gui_readiness.gui_bundle_id}",
        "Capture slots:",
    ]
    for slot in report.capture_slots:
        lines.extend(_slot_lines(slot))
    lines.append("Analyzer job cards:")
    for job in report.analyzer_jobs:
        lines.extend(_job_lines(job))
    lines.extend(
        [
            "Operator capture checklist:",
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
    queue_label = _DEFAULT_QUEUE_LABEL
    capture_prefix = _DEFAULT_CAPTURE_PREFIX
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
        elif option == "--label":
            if not value.strip():
                raise ValueError("label must not be blank")
            queue_label = value
        else:
            if not value.strip():
                raise ValueError("capture_prefix must not be blank")
            capture_prefix = value

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
        "queue_label": queue_label,
        "capture_prefix": capture_prefix,
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
    queue_label: str,
    capture_prefix: str,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_capture_queue_report(
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
            queue_label=queue_label,
            capture_prefix=capture_prefix,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_capture_queue_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_capture_queue_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


STYLE_PERFORMANCE_ARC_LIVE_GUI_CAPTURE_QUEUE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-capture-queue-report",
    summary="Build passive GUI/audio-analyzer capture queues.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_CAPTURE_QUEUE_CLI_COMMAND)

__all__ = [
    "GUI_CAPTURE_QUEUE_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_CAPTURE_QUEUE_CLI_COMMAND",
    "StylePerformanceArcLiveGuiAnalyzerJob",
    "StylePerformanceArcLiveGuiCaptureQueueReport",
    "StylePerformanceArcLiveGuiCaptureSlot",
    "build_style_performance_arc_live_gui_capture_queue_from_rehearsal_session",
    "build_style_performance_arc_live_gui_capture_queue_report",
    "format_style_performance_arc_live_gui_capture_queue_report",
    "to_style_performance_arc_live_gui_capture_queue_json",
]
