"""Passive live GUI playback validation matrix for GUI test harnesses."""

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
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)
from .live_gui_playback_transcript import (
    StylePerformanceArcLiveGuiPlaybackTranscriptReport,
    build_style_performance_arc_live_gui_playback_transcript_report,
    parse_style_performance_arc_live_gui_playback_transcript_cli_args,
    to_style_performance_arc_live_gui_playback_transcript_json,
)

REPORT_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live GUI playback validation matrix"
)
SOURCE_MODULE: Final[str] = "reports.live_gui_playback_validation"
VALIDATION_VERSION: Final[str] = "live-gui-playback-validation-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI playback validation metadata only",
    "consumes live GUI playback transcript metadata only",
    "validation cases are declarative metadata only",
    "future GUI test harness only",
    "future audio analyzer comparison only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
    "no GUI event dispatch",
    "no GUI controller dispatch",
    "no GUI state-store mutation",
    "no GUI test runner dispatch",
    "no file writing",
    "no audio recording",
    "no audio streaming",
    "no audio comparison execution",
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
_DEFAULT_VALIDATION_LABEL: Final[str] = "Live GUI playback validation matrix"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-playback-validation-report usage: "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] [--takes N] "
    "[--slot capture-001] [--label <text>] [--capture-prefix <text>] "
    "[--sidecar-label <text>] [--screen-label <text>] "
    "[--layout <key>] [--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiPlaybackValidationStep:
    """One passive validation harness step."""

    step_key: str
    order: int
    phase: str
    source_id: str
    action: str
    expected_state: str
    passive: bool
    reason: str
    test_id: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiPlaybackValidationCase:
    """One deterministic validation case for a future GUI harness."""

    case_key: str
    order: int
    category: str
    source_key: str
    source_id: str
    source_test_id: str
    target: str
    assertion: str
    expected: str
    actual_source: str
    passive: bool
    failure_hint: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiPlaybackValidationReport:
    """Passive validation matrix composed from a playback transcript."""

    playback_transcript: StylePerformanceArcLiveGuiPlaybackTranscriptReport
    validation_version: str
    validation_id: str
    validation_label: str
    validation_status: str
    harness_steps: tuple[StylePerformanceArcLiveGuiPlaybackValidationStep, ...]
    validation_cases: tuple[StylePerformanceArcLiveGuiPlaybackValidationCase, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def playback_id(self) -> str:
        """Return upstream playback transcript id."""

        return self.playback_transcript.playback_id

    @property
    def controller_id(self) -> str:
        """Return upstream controller state id."""

        return self.playback_transcript.controller_id

    @property
    def reducer_id(self) -> str:
        """Return upstream reducer id."""

        return self.playback_transcript.reducer_id

    @property
    def script_id(self) -> str:
        """Return upstream interaction script id."""

        return self.playback_transcript.script_id

    @property
    def frame_id(self) -> str:
        """Return upstream analyzer frame id."""

        return self.playback_transcript.frame_id

    @property
    def overlay_id(self) -> str:
        """Return upstream analyzer overlay id."""

        return self.playback_transcript.overlay_id

    @property
    def render_tree_id(self) -> str:
        """Return upstream render tree id."""

        return self.playback_transcript.render_tree_id

    @property
    def screen_contract_id(self) -> str:
        """Return upstream screen contract id."""

        return self.playback_transcript.screen_contract_id

    @property
    def capture_review_id(self) -> str:
        """Return upstream capture review id."""

        return self.playback_transcript.capture_review_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected performance arc key."""

        return self.playback_transcript.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected performance arc name."""

        return self.playback_transcript.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.playback_transcript.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _validation_status(
    playback_transcript: StylePerformanceArcLiveGuiPlaybackTranscriptReport,
) -> str:
    if playback_transcript.playback_status == "blocked":
        return "blocked"
    if playback_transcript.playback_status == "review-needed":
        return "review-needed"
    return "ready"


def _validation_id(
    playback_transcript: StylePerformanceArcLiveGuiPlaybackTranscriptReport,
    *,
    validation_label: str,
    validation_status: str,
) -> str:
    payload = "|".join(
        (
            VALIDATION_VERSION,
            playback_transcript.playback_id,
            playback_transcript.controller_id,
            playback_transcript.reducer_id,
            validation_label,
            validation_status,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _test_id(*parts: str) -> str:
    return "-".join(part.replace(" ", "-").lower() for part in parts if part)


def _step(
    *,
    order: int,
    phase: str,
    source_id: str,
    action: str,
    expected_state: str,
    reason: str,
) -> StylePerformanceArcLiveGuiPlaybackValidationStep:
    return StylePerformanceArcLiveGuiPlaybackValidationStep(
        step_key=f"validation-step-{phase}",
        order=order,
        phase=phase,
        source_id=source_id,
        action=action,
        expected_state=expected_state,
        passive=True,
        reason=reason,
        test_id=_test_id("validation", phase),
    )


def _harness_steps(
    playback_transcript: StylePerformanceArcLiveGuiPlaybackTranscriptReport,
) -> tuple[StylePerformanceArcLiveGuiPlaybackValidationStep, ...]:
    return (
        _step(
            order=0,
            phase="load-playback-transcript",
            source_id=playback_transcript.playback_id,
            action="load playback transcript metadata",
            expected_state="loaded",
            reason="Future GUI harness can consume the transcript without launching UI.",
        ),
        _step(
            order=1,
            phase="load-controller-state",
            source_id=playback_transcript.controller_id,
            action="load controller-state metadata",
            expected_state="loaded",
            reason="Future GUI harness can hydrate controls from passive metadata.",
        ),
        _step(
            order=2,
            phase="evaluate-validation-cases",
            source_id=playback_transcript.playback_id,
            action="evaluate validation case metadata",
            expected_state="metadata-ready",
            reason="Validation matrix is declarative and does not execute tests.",
        ),
        _step(
            order=3,
            phase="assert-passive-boundary",
            source_id=playback_transcript.playback_id,
            action="assert passive boundary",
            expected_state="no active side effects",
            reason="Validation matrix remains stdout/JSON metadata only.",
        ),
    )


def _timeline_case(
    *,
    order: int,
    source_key: str,
    source_id: str,
    source_test_id: str,
    target: str,
    assertion: str,
    expected: str,
    actual_source: str,
    failure_hint: str,
) -> StylePerformanceArcLiveGuiPlaybackValidationCase:
    return StylePerformanceArcLiveGuiPlaybackValidationCase(
        case_key=f"validation-case-{order:03d}-{source_key}",
        order=order,
        category="timeline",
        source_key=source_key,
        source_id=source_id,
        source_test_id=source_test_id,
        target=target,
        assertion=assertion,
        expected=expected,
        actual_source=actual_source,
        passive=True,
        failure_hint=failure_hint,
    )


def _validation_cases(
    playback_transcript: StylePerformanceArcLiveGuiPlaybackTranscriptReport,
) -> tuple[StylePerformanceArcLiveGuiPlaybackValidationCase, ...]:
    cases: list[StylePerformanceArcLiveGuiPlaybackValidationCase] = []
    order = 0
    for event in playback_transcript.events:
        cases.append(
            _timeline_case(
                order=order,
                source_key=event.event_key,
                source_id=event.source_id,
                source_test_id=event.test_id,
                target=event.phase,
                assertion=f"{event.phase} event expects {event.expected_state}",
                expected=event.expected_state,
                actual_source="live_gui_playback_transcript.events",
                failure_hint=f"Expected playback event {event.event_key} to be present.",
            )
        )
        order += 1
    for assertion in playback_transcript.assertions:
        cases.append(
            StylePerformanceArcLiveGuiPlaybackValidationCase(
                case_key=f"validation-case-{order:03d}-{assertion.assertion_key}",
                order=order,
                category="assertion",
                source_key=assertion.assertion_key,
                source_id=assertion.source,
                source_test_id=assertion.test_id,
                target=assertion.target,
                assertion=f"{assertion.target} equals {assertion.expected}",
                expected=assertion.expected,
                actual_source="live_gui_playback_transcript.assertions",
                passive=True,
                failure_hint=assertion.failure_hint,
            )
        )
        order += 1
    for checkpoint in playback_transcript.analyzer_checkpoints:
        cases.append(
            StylePerformanceArcLiveGuiPlaybackValidationCase(
                case_key=f"validation-case-{order:03d}-{checkpoint.key}",
                order=order,
                category="analyzer",
                source_key=checkpoint.key,
                source_id=checkpoint.render_node_key,
                source_test_id=_test_id("analyzer", checkpoint.key),
                target=checkpoint.metric_key,
                assertion="meter widget target/capture status remains deterministic",
                expected=checkpoint.expected_status,
                actual_source="live_gui_playback_transcript.analyzer_checkpoints",
                passive=True,
                failure_hint=f"Expected analyzer checkpoint {checkpoint.key} status.",
            )
        )
        order += 1
    for safety_line in SAFETY_LINES:
        cases.append(
            StylePerformanceArcLiveGuiPlaybackValidationCase(
                case_key=f"validation-case-{order:03d}-safety-{_test_id(safety_line)}",
                order=order,
                category="safety",
                source_key=f"safety-{_test_id(safety_line)}",
                source_id=SOURCE_MODULE,
                source_test_id=_test_id("safety", safety_line),
                target="safety",
                assertion=f"passive safety includes {safety_line}",
                expected=safety_line,
                actual_source="live_gui_playback_validation.safety",
                passive=True,
                failure_hint=f"Missing passive safety statement: {safety_line}.",
            )
        )
        order += 1
    return tuple(cases)


def _blocked_actions(validation_status: str) -> tuple[str, ...]:
    actions = [
        "no GUI launch",
        "no GUI event dispatch",
        "no GUI controller dispatch",
        "no GUI state-store mutation",
        "no GUI test runner dispatch",
        "no file writing",
        "no audio recording",
        "no audio streaming",
        "no audio comparison execution",
        "no MIDI sending",
        "no port opening",
        "no command execution",
        "no hardware mutation",
    ]
    if validation_status == "blocked":
        actions.append("hold playback validation matrix before GUI test harness binding")
    return tuple(actions)


def _replace_command(command: str, *, validation_label: str) -> str | None:
    source = "style-performance-arc-live-gui-playback-transcript-report"
    target = "style-performance-arc-live-gui-playback-validation-report"
    prefix = "python -m rytm_randomizer.cli "
    if not command.startswith(prefix):
        return None
    arguments = command[len(prefix) :]
    if arguments != source and not arguments.startswith(f"{source} "):
        return None
    replaced = f"{prefix}{target}{arguments[len(source):]}"
    return f"{replaced} --validation-label {powershell_literal_arg(validation_label)}"


def _replay_commands(
    playback_transcript: StylePerformanceArcLiveGuiPlaybackTranscriptReport,
    *,
    validation_label: str,
) -> tuple[str, ...]:
    if not playback_transcript.replay_commands:
        return ()
    validation_command = _replace_command(
        playback_transcript.replay_commands[0],
        validation_label=validation_label,
    )
    if validation_command is None:
        return ()
    return (
        validation_command,
        *playback_transcript.replay_commands,
    )


def build_style_performance_arc_live_gui_playback_validation_from_transcript(
    playback_transcript: StylePerformanceArcLiveGuiPlaybackTranscriptReport,
    *,
    validation_label: str = _DEFAULT_VALIDATION_LABEL,
) -> StylePerformanceArcLiveGuiPlaybackValidationReport:
    """Build passive GUI playback validation matrix from transcript metadata."""

    normalized_label = _normalize_nonblank(validation_label, field="validation_label")
    status = _validation_status(playback_transcript)
    return StylePerformanceArcLiveGuiPlaybackValidationReport(
        playback_transcript=playback_transcript,
        validation_version=VALIDATION_VERSION,
        validation_id=_validation_id(
            playback_transcript,
            validation_label=normalized_label,
            validation_status=status,
        ),
        validation_label=normalized_label,
        validation_status=status,
        harness_steps=_harness_steps(playback_transcript),
        validation_cases=_validation_cases(playback_transcript),
        blocked_actions=_blocked_actions(status),
        replay_commands=_replay_commands(
            playback_transcript,
            validation_label=normalized_label,
        ),
    )


def build_style_performance_arc_live_gui_playback_validation_report(
    *,
    description: str | None = None,
    feature_report: FeatureReport | None = None,
    audio_path: Path | None = None,
    library_path: Path | None = None,
    capture_description: str | None = None,
    capture_feature_report: FeatureReport | None = None,
    capture_audio_path: Path | None = None,
    capture_library_path: Path | None = None,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
    cue_number: int = 1,
    lookahead_count: int = 1,
    match_limit: int = 3,
    take_count: int = 2,
    slot_key: str = "capture-001",
    queue_label: str = "Live GUI capture queue",
    capture_prefix: str = "rehearsal",
    sidecar_label: str = "Live GUI sidecar session",
    screen_label: str = "Live GUI screen contract",
    layout_key: str = "operator-cockpit",
    viewport: str = "desktop",
    render_target: str = "desktop-sidecar",
    density: str = "standard",
    overlay_label: str = "Live GUI analyzer overlay",
    frame_label: str = "Live GUI analyzer frame",
    interaction_label: str = "Live GUI interaction script",
    reducer_label: str = "Live GUI action reducer",
    controller_label: str = "Live GUI controller state",
    playback_label: str = "Live GUI playback transcript",
    validation_label: str = _DEFAULT_VALIDATION_LABEL,
) -> StylePerformanceArcLiveGuiPlaybackValidationReport:
    """Build passive GUI playback validation matrix from source evidence."""

    playback_transcript = build_style_performance_arc_live_gui_playback_transcript_report(
        description=description,
        feature_report=feature_report,
        audio_path=audio_path,
        library_path=library_path,
        capture_description=capture_description,
        capture_feature_report=capture_feature_report,
        capture_audio_path=capture_audio_path,
        capture_library_path=capture_library_path,
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
        slot_key=slot_key,
        queue_label=queue_label,
        capture_prefix=capture_prefix,
        sidecar_label=sidecar_label,
        screen_label=screen_label,
        layout_key=layout_key,
        viewport=viewport,
        render_target=render_target,
        density=density,
        overlay_label=overlay_label,
        frame_label=frame_label,
        interaction_label=interaction_label,
        reducer_label=reducer_label,
        controller_label=controller_label,
        playback_label=playback_label,
    )
    return build_style_performance_arc_live_gui_playback_validation_from_transcript(
        playback_transcript,
        validation_label=validation_label,
    )


def _step_json(step: StylePerformanceArcLiveGuiPlaybackValidationStep) -> dict[str, object]:
    return {
        "step_key": step.step_key,
        "order": step.order,
        "phase": step.phase,
        "source_id": step.source_id,
        "action": step.action,
        "expected_state": step.expected_state,
        "passive": step.passive,
        "reason": step.reason,
        "test_id": step.test_id,
    }


def _case_json(case: StylePerformanceArcLiveGuiPlaybackValidationCase) -> dict[str, object]:
    return {
        "case_key": case.case_key,
        "order": case.order,
        "category": case.category,
        "source_key": case.source_key,
        "source_id": case.source_id,
        "source_test_id": case.source_test_id,
        "target": case.target,
        "assertion": case.assertion,
        "expected": case.expected,
        "actual_source": case.actual_source,
        "passive": case.passive,
        "failure_hint": case.failure_hint,
    }


def to_style_performance_arc_live_gui_playback_validation_json(
    report: StylePerformanceArcLiveGuiPlaybackValidationReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI playback validation payload."""

    playback_json = to_style_performance_arc_live_gui_playback_transcript_json(
        report.playback_transcript
    )
    return {
        "live_gui_playback_validation": {
            "validation_version": report.validation_version,
            "validation_id": report.validation_id,
            "validation_label": report.validation_label,
            "validation_status": report.validation_status,
            "playback_id": report.playback_id,
            "controller_id": report.controller_id,
            "reducer_id": report.reducer_id,
            "script_id": report.script_id,
            "frame_id": report.frame_id,
            "overlay_id": report.overlay_id,
            "render_tree_id": report.render_tree_id,
            "screen_contract_id": report.screen_contract_id,
            "capture_review_id": report.capture_review_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "harness_steps": [_step_json(row) for row in report.harness_steps],
            "validation_cases": [_case_json(row) for row in report.validation_cases],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **playback_json,
        "safety": list(SAFETY_LINES),
    }


def _step_lines(step: StylePerformanceArcLiveGuiPlaybackValidationStep) -> list[str]:
    return [
        f"- {step.order}. {step.step_key}: {step.phase}",
        f"  Action: {step.action}",
        f"  Expected state: {step.expected_state}",
        f"  Source id: {step.source_id}",
        f"  Test id: {step.test_id}",
        f"  Reason: {step.reason}",
    ]


def _case_lines(case: StylePerformanceArcLiveGuiPlaybackValidationCase) -> list[str]:
    return [
        f"- {case.order}. {case.case_key}: {case.category} / {case.source_key}",
        f"  Target: {case.target}",
        f"  Assertion: {case.assertion}",
        f"  Expected: {case.expected}",
        f"  Actual source: {case.actual_source}",
        f"  Source test id: {case.source_test_id}",
        f"  Failure hint: {case.failure_hint}",
    ]


def format_style_performance_arc_live_gui_playback_validation_report(
    report: StylePerformanceArcLiveGuiPlaybackValidationReport,
) -> list[str]:
    """Return deterministic passive live GUI playback validation lines."""

    lines = [
        "Live GUI playback validation summary:",
        f"- Validation version: {report.validation_version}",
        f"- Validation id: {report.validation_id}",
        f"- Validation label: {report.validation_label}",
        f"- Validation status: {report.validation_status}",
        f"- Playback transcript id: {report.playback_id}",
        f"- Controller state id: {report.controller_id}",
        f"- Action reducer id: {report.reducer_id}",
        f"- Interaction script id: {report.script_id}",
        f"- Frame id: {report.frame_id}",
        f"- Overlay id: {report.overlay_id}",
        f"- Render tree id: {report.render_tree_id}",
        f"- Screen contract id: {report.screen_contract_id}",
        f"- Capture review id: {report.capture_review_id}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        "Validation harness steps:",
    ]
    for step in report.harness_steps:
        lines.extend(_step_lines(step))
    lines.append("Validation cases:")
    for case in report.validation_cases:
        lines.extend(_case_lines(case))
    lines.extend(
        [
            "Blocked active actions:",
            *[f"- {action}" for action in report.blocked_actions],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.replay_commands],
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


def _pop_option_value(remaining: list[str]) -> str:
    if not remaining:
        raise ValueError(_USAGE)
    return remaining.pop(0)


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    validation_label = _DEFAULT_VALIDATION_LABEL
    playback_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--validation-label":
            validation_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="validation_label",
            )
        else:
            playback_args.append(option)
            if option != "--json":
                playback_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_playback_transcript_cli_args(playback_args)
    parsed["validation_label"] = validation_label
    return parsed


def _handle_cli_report(
    *,
    description: str | None,
    audio_path: Path | None,
    library_path: Path | None,
    capture_description: str | None,
    capture_audio_path: Path | None,
    capture_library_path: Path | None,
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
    slot_key: str,
    queue_label: str,
    capture_prefix: str,
    sidecar_label: str,
    screen_label: str,
    layout_key: str,
    viewport: str,
    render_target: str,
    density: str,
    overlay_label: str,
    frame_label: str,
    interaction_label: str,
    reducer_label: str,
    controller_label: str,
    playback_label: str,
    validation_label: str,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_playback_validation_report(
            description=description,
            audio_path=audio_path,
            library_path=library_path,
            capture_description=capture_description,
            capture_audio_path=capture_audio_path,
            capture_library_path=capture_library_path,
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
            slot_key=slot_key,
            queue_label=queue_label,
            capture_prefix=capture_prefix,
            sidecar_label=sidecar_label,
            screen_label=screen_label,
            layout_key=layout_key,
            viewport=viewport,
            render_target=render_target,
            density=density,
            overlay_label=overlay_label,
            frame_label=frame_label,
            interaction_label=interaction_label,
            reducer_label=reducer_label,
            controller_label=controller_label,
            playback_label=playback_label,
            validation_label=validation_label,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_playback_validation_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_playback_validation_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_GUI_PLAYBACK_VALIDATION_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-playback-validation-report",
    summary="Compose passive playback transcript into GUI validation matrix metadata.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_PLAYBACK_VALIDATION_CLI_COMMAND)

__all__ = [
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_PLAYBACK_VALIDATION_CLI_COMMAND",
    "VALIDATION_VERSION",
    "StylePerformanceArcLiveGuiPlaybackValidationCase",
    "StylePerformanceArcLiveGuiPlaybackValidationReport",
    "StylePerformanceArcLiveGuiPlaybackValidationStep",
    "build_style_performance_arc_live_gui_playback_validation_from_transcript",
    "build_style_performance_arc_live_gui_playback_validation_report",
    "format_style_performance_arc_live_gui_playback_validation_report",
    "to_style_performance_arc_live_gui_playback_validation_json",
]
