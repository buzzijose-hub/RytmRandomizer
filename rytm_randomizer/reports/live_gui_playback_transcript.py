"""Passive live GUI playback transcript packet for GUI test harnesses."""

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
from .live_gui_controller_state import (
    StylePerformanceArcLiveGuiControllerStateReport,
    build_style_performance_arc_live_gui_controller_state_report,
    parse_style_performance_arc_live_gui_controller_state_cli_args,
    to_style_performance_arc_live_gui_controller_state_json,
)

REPORT_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live GUI playback transcript"
)
SOURCE_MODULE: Final[str] = "reports.live_gui_playback_transcript"
PLAYBACK_TRANSCRIPT_VERSION: Final[str] = "live-gui-playback-transcript-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI playback transcript metadata only",
    "composes live GUI controller state only",
    "playback events are metadata only",
    "GUI playback assertions are metadata only",
    "future GUI test harness only",
    "future audio analyzer comparison only",
    "capture decisions are read-only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
    "no GUI event dispatch",
    "no GUI controller dispatch",
    "no GUI state-store mutation",
    "no file writing",
    "no audio recording",
    "no audio streaming",
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
_DEFAULT_PLAYBACK_LABEL: Final[str] = "Live GUI playback transcript"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-playback-transcript-report usage: "
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
    "[--playback-label <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiPlaybackEvent:
    """One passive ordered GUI playback event."""

    event_key: str
    order: int
    phase: str
    source_key: str
    source_id: str
    action: str
    expected_state: str
    passive: bool
    reason: str
    test_id: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiPlaybackAssertion:
    """One deterministic future-GUI playback assertion."""

    assertion_key: str
    order: int
    target: str
    expected: str
    source: str
    test_id: str
    failure_hint: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiPlaybackAnalyzerCheckpoint:
    """One passive analyzer checkpoint included in the playback transcript."""

    key: str
    order: int
    metric_key: str
    render_node_key: str
    target_value: str
    captured_value: str
    expected_status: str
    display_token: str
    source: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiPlaybackTranscriptReport:
    """Passive playback transcript composed from controller state."""

    controller_state: StylePerformanceArcLiveGuiControllerStateReport
    playback_version: str
    playback_id: str
    playback_label: str
    playback_status: str
    events: tuple[StylePerformanceArcLiveGuiPlaybackEvent, ...]
    assertions: tuple[StylePerformanceArcLiveGuiPlaybackAssertion, ...]
    analyzer_checkpoints: tuple[
        StylePerformanceArcLiveGuiPlaybackAnalyzerCheckpoint,
        ...,
    ]
    blocked_controls: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def controller_id(self) -> str:
        """Return upstream controller-state id."""

        return self.controller_state.controller_id

    @property
    def reducer_id(self) -> str:
        """Return upstream reducer id."""

        return self.controller_state.reducer_id

    @property
    def script_id(self) -> str:
        """Return upstream interaction-script id."""

        return self.controller_state.script_id

    @property
    def frame_id(self) -> str:
        """Return upstream analyzer-frame id."""

        return self.controller_state.frame_id

    @property
    def overlay_id(self) -> str:
        """Return upstream analyzer-overlay id."""

        return self.controller_state.overlay_id

    @property
    def render_tree_id(self) -> str:
        """Return upstream render-tree id."""

        return self.controller_state.render_tree_id

    @property
    def screen_contract_id(self) -> str:
        """Return upstream screen-contract id."""

        return self.controller_state.screen_contract_id

    @property
    def capture_review_id(self) -> str:
        """Return upstream capture-review id."""

        return self.controller_state.capture_review_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.controller_state.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.controller_state.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.controller_state.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _playback_status(
    controller_state: StylePerformanceArcLiveGuiControllerStateReport,
) -> str:
    if controller_state.controller_status == "blocked":
        return "blocked"
    if controller_state.controller_status == "review-needed":
        return "review-needed"
    return "ready"


def _playback_id(
    controller_state: StylePerformanceArcLiveGuiControllerStateReport,
    *,
    playback_label: str,
    playback_status: str,
) -> str:
    payload = "|".join(
        (
            PLAYBACK_TRANSCRIPT_VERSION,
            controller_state.controller_id,
            controller_state.reducer_id,
            controller_state.script_id,
            playback_label,
            playback_status,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _test_id(*parts: str) -> str:
    return "-".join(part.replace(" ", "-").lower() for part in parts if part)


def _event(
    *,
    order: int,
    phase: str,
    source_key: str,
    source_id: str,
    action: str,
    expected_state: str,
    reason: str,
) -> StylePerformanceArcLiveGuiPlaybackEvent:
    return StylePerformanceArcLiveGuiPlaybackEvent(
        event_key=f"playback-event-{phase}-{source_key}",
        order=order,
        phase=phase,
        source_key=source_key,
        source_id=source_id,
        action=action,
        expected_state=expected_state,
        passive=True,
        reason=reason,
        test_id=_test_id("playback", phase, source_key),
    )


def _bootstrap_events(
    controller_state: StylePerformanceArcLiveGuiControllerStateReport,
) -> list[StylePerformanceArcLiveGuiPlaybackEvent]:
    return [
        _event(
            order=0,
            phase="bootstrap",
            source_key="screen-contract",
            source_id=controller_state.screen_contract_id,
            action="load screen contract metadata",
            expected_state="loaded",
            reason="Future GUI harness can identify the screen contract without launching UI.",
        ),
        _event(
            order=1,
            phase="bootstrap",
            source_key="render-tree",
            source_id=controller_state.render_tree_id,
            action="load render tree metadata",
            expected_state="loaded",
            reason="Future GUI harness can identify render nodes without rendering UI.",
        ),
        _event(
            order=2,
            phase="bootstrap",
            source_key="analyzer-frame",
            source_id=controller_state.frame_id,
            action="load analyzer frame metadata",
            expected_state="loaded",
            reason="Future analyzer comparison can bind deterministic frame metadata.",
        ),
    ]


def _playback_events(
    controller_state: StylePerformanceArcLiveGuiControllerStateReport,
    *,
    playback_status: str,
) -> tuple[StylePerformanceArcLiveGuiPlaybackEvent, ...]:
    events = _bootstrap_events(controller_state)
    next_order = len(events)
    for state in controller_state.control_states:
        events.append(
            _event(
                order=next_order,
                phase="hydrate",
                source_key=state.control_key,
                source_id=state.key,
                action="hydrate GUI control state",
                expected_state=state.current_state,
                reason=state.reason,
            )
        )
        next_order += 1
    if playback_status != "blocked":
        for action in controller_state.queued_actions:
            events.append(
                _event(
                    order=next_order,
                    phase="queue-gui-action",
                    source_key=action.control_key,
                    source_id=action.key,
                    action=action.requested_action,
                    expected_state=action.target_state,
                    reason=f"Replay metadata for {action.reducer_transition_key}.",
                )
            )
            next_order += 1
    for blocked_control in controller_state.blocked_controls:
        events.append(
            _event(
                order=next_order,
                phase="assert",
                source_key=blocked_control,
                source_id=f"blocked-control-{blocked_control}",
                action="assert GUI control remains blocked",
                expected_state="blocked",
                reason="Passive transcript preserves blocked-control guardrails.",
            )
        )
        next_order += 1
    events.append(
        _event(
            order=next_order,
            phase="safety",
            source_key="passive-boundary",
            source_id=controller_state.controller_id,
            action="assert passive boundary",
            expected_state="no active side effects",
            reason="Playback transcript is metadata only.",
        )
    )
    return tuple(events)


def _assertions(
    controller_state: StylePerformanceArcLiveGuiControllerStateReport,
) -> tuple[StylePerformanceArcLiveGuiPlaybackAssertion, ...]:
    rows: list[StylePerformanceArcLiveGuiPlaybackAssertion] = []
    order = 0
    for state in controller_state.control_states:
        rows.append(
            StylePerformanceArcLiveGuiPlaybackAssertion(
                assertion_key=f"playback-assertion-{state.control_key}",
                order=order,
                target=state.test_id,
                expected=state.current_state,
                source="live_gui_controller_state.control_states",
                test_id=_test_id("assertion", state.control_key),
                failure_hint=f"Expected {state.control_key} to be {state.current_state}.",
            )
        )
        order += 1
    for action in controller_state.blocked_actions:
        rows.append(
            StylePerformanceArcLiveGuiPlaybackAssertion(
                assertion_key=f"playback-assertion-blocked-action-{order}",
                order=order,
                target="blocked_actions",
                expected=action,
                source="live_gui_controller_state.blocked_actions",
                test_id=_test_id("assertion", "blocked-actions", str(order)),
                failure_hint=f"Missing passive guardrail: {action}.",
            )
        )
        order += 1
    return tuple(rows)


def _analyzer_checkpoints(
    controller_state: StylePerformanceArcLiveGuiControllerStateReport,
) -> tuple[StylePerformanceArcLiveGuiPlaybackAnalyzerCheckpoint, ...]:
    overlay = controller_state.action_reducer.interaction_script.frame.overlay
    return tuple(
        StylePerformanceArcLiveGuiPlaybackAnalyzerCheckpoint(
            key=f"playback-checkpoint-{meter.key}",
            order=index,
            metric_key=meter.metric_key,
            render_node_key=meter.render_node_key,
            target_value=meter.target_value,
            captured_value=meter.captured_value,
            expected_status=meter.status,
            display_token=meter.display_token,
            source="live_gui_analyzer_overlay.meter_widgets",
        )
        for index, meter in enumerate(overlay.meter_widgets)
    )


def _blocked_actions(playback_status: str) -> tuple[str, ...]:
    actions = [
        "no GUI launch",
        "no GUI event dispatch",
        "no GUI controller dispatch",
        "no GUI state-store mutation",
        "no GUI test runner dispatch",
        "no file writing",
        "no audio recording",
        "no audio streaming",
        "no MIDI sending",
        "no port opening",
        "no command execution",
        "no hardware mutation",
    ]
    if playback_status == "blocked":
        actions.append("hold playback transcript before GUI runtime binding")
    return tuple(actions)


def _replace_command(command: str, *, playback_label: str) -> str | None:
    source = "style-performance-arc-live-gui-controller-state-report"
    target = "style-performance-arc-live-gui-playback-transcript-report"
    prefix = "python -m rytm_randomizer.cli "
    if not command.startswith(prefix):
        return None
    arguments = command[len(prefix) :]
    if arguments != source and not arguments.startswith(f"{source} "):
        return None
    replaced = f"{prefix}{target}{arguments[len(source):]}"
    if "--playback-label" not in replaced:
        replaced = f"{replaced} --playback-label {powershell_literal_arg(playback_label)}"
    return replaced


def _replay_commands(
    controller_state: StylePerformanceArcLiveGuiControllerStateReport,
    *,
    playback_label: str,
) -> tuple[str, ...]:
    if not controller_state.replay_commands:
        return ()
    playback_command = _replace_command(
        controller_state.replay_commands[0],
        playback_label=playback_label,
    )
    if playback_command is None:
        return ()
    return (
        playback_command,
        *controller_state.replay_commands,
    )


def build_style_performance_arc_live_gui_playback_transcript_from_controller_state(
    controller_state: StylePerformanceArcLiveGuiControllerStateReport,
    *,
    playback_label: str = _DEFAULT_PLAYBACK_LABEL,
) -> StylePerformanceArcLiveGuiPlaybackTranscriptReport:
    """Build passive GUI playback transcript from controller state."""

    normalized_label = _normalize_nonblank(playback_label, field="playback_label")
    status = _playback_status(controller_state)
    return StylePerformanceArcLiveGuiPlaybackTranscriptReport(
        controller_state=controller_state,
        playback_version=PLAYBACK_TRANSCRIPT_VERSION,
        playback_id=_playback_id(
            controller_state,
            playback_label=normalized_label,
            playback_status=status,
        ),
        playback_label=normalized_label,
        playback_status=status,
        events=_playback_events(controller_state, playback_status=status),
        assertions=_assertions(controller_state),
        analyzer_checkpoints=_analyzer_checkpoints(controller_state),
        blocked_controls=controller_state.blocked_controls,
        blocked_actions=_blocked_actions(status),
        replay_commands=_replay_commands(
            controller_state,
            playback_label=normalized_label,
        ),
    )


def build_style_performance_arc_live_gui_playback_transcript_report(
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
    playback_label: str = _DEFAULT_PLAYBACK_LABEL,
) -> StylePerformanceArcLiveGuiPlaybackTranscriptReport:
    """Build passive GUI playback transcript from source evidence."""

    controller_state = build_style_performance_arc_live_gui_controller_state_report(
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
    )
    return build_style_performance_arc_live_gui_playback_transcript_from_controller_state(
        controller_state,
        playback_label=playback_label,
    )


def _event_json(event: StylePerformanceArcLiveGuiPlaybackEvent) -> dict[str, object]:
    return {
        "event_key": event.event_key,
        "order": event.order,
        "phase": event.phase,
        "source_key": event.source_key,
        "source_id": event.source_id,
        "action": event.action,
        "expected_state": event.expected_state,
        "passive": event.passive,
        "reason": event.reason,
        "test_id": event.test_id,
    }


def _assertion_json(
    assertion: StylePerformanceArcLiveGuiPlaybackAssertion,
) -> dict[str, object]:
    return {
        "assertion_key": assertion.assertion_key,
        "order": assertion.order,
        "target": assertion.target,
        "expected": assertion.expected,
        "source": assertion.source,
        "test_id": assertion.test_id,
        "failure_hint": assertion.failure_hint,
    }


def _checkpoint_json(
    checkpoint: StylePerformanceArcLiveGuiPlaybackAnalyzerCheckpoint,
) -> dict[str, object]:
    return {
        "key": checkpoint.key,
        "order": checkpoint.order,
        "metric_key": checkpoint.metric_key,
        "render_node_key": checkpoint.render_node_key,
        "target_value": checkpoint.target_value,
        "captured_value": checkpoint.captured_value,
        "expected_status": checkpoint.expected_status,
        "display_token": checkpoint.display_token,
        "source": checkpoint.source,
    }


def to_style_performance_arc_live_gui_playback_transcript_json(
    report: StylePerformanceArcLiveGuiPlaybackTranscriptReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI playback transcript payload."""

    controller_json = to_style_performance_arc_live_gui_controller_state_json(
        report.controller_state
    )
    return {
        "live_gui_playback_transcript": {
            "playback_version": report.playback_version,
            "playback_id": report.playback_id,
            "playback_label": report.playback_label,
            "playback_status": report.playback_status,
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
            "events": [_event_json(row) for row in report.events],
            "assertions": [_assertion_json(row) for row in report.assertions],
            "analyzer_checkpoints": [_checkpoint_json(row) for row in report.analyzer_checkpoints],
            "blocked_controls": list(report.blocked_controls),
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **controller_json,
        "safety": list(SAFETY_LINES),
    }


def _event_lines(event: StylePerformanceArcLiveGuiPlaybackEvent) -> list[str]:
    return [
        f"- {event.order}. {event.event_key}: {event.phase} / {event.source_key}",
        f"  Action: {event.action}",
        f"  Expected state: {event.expected_state}",
        f"  Source id: {event.source_id}",
        f"  Test id: {event.test_id}",
        f"  Reason: {event.reason}",
    ]


def _assertion_lines(
    assertion: StylePerformanceArcLiveGuiPlaybackAssertion,
) -> list[str]:
    return [
        f"- {assertion.order}. {assertion.assertion_key}: {assertion.target}",
        f"  Expected: {assertion.expected}",
        f"  Source: {assertion.source}",
        f"  Test id: {assertion.test_id}",
        f"  Failure hint: {assertion.failure_hint}",
    ]


def _checkpoint_lines(
    checkpoint: StylePerformanceArcLiveGuiPlaybackAnalyzerCheckpoint,
) -> list[str]:
    return [
        f"- {checkpoint.order}. {checkpoint.key}: {checkpoint.metric_key}",
        f"  Node: {checkpoint.render_node_key}",
        f"  Target -> captured: {checkpoint.target_value} -> {checkpoint.captured_value}",
        f"  Expected status: {checkpoint.expected_status}",
        f"  Display token: {checkpoint.display_token}",
        f"  Source: {checkpoint.source}",
    ]


def format_style_performance_arc_live_gui_playback_transcript_report(
    report: StylePerformanceArcLiveGuiPlaybackTranscriptReport,
) -> list[str]:
    """Return deterministic passive live GUI playback transcript lines."""

    lines = [
        "Live GUI playback transcript summary:",
        f"- Playback version: {report.playback_version}",
        f"- Playback id: {report.playback_id}",
        f"- Playback label: {report.playback_label}",
        f"- Playback status: {report.playback_status}",
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
        "Playback timeline:",
    ]
    for event in report.events:
        lines.extend(_event_lines(event))
    lines.append("GUI playback assertions:")
    for assertion in report.assertions:
        lines.extend(_assertion_lines(assertion))
    lines.append("Analyzer checkpoints:")
    for checkpoint in report.analyzer_checkpoints:
        lines.extend(_checkpoint_lines(checkpoint))
    lines.extend(
        [
            "Blocked GUI controls:",
            *[f"- {control}" for control in report.blocked_controls],
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
    playback_label = _DEFAULT_PLAYBACK_LABEL
    controller_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--playback-label":
            playback_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="playback_label",
            )
        else:
            controller_args.append(option)
            if option != "--json":
                controller_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_controller_state_cli_args(controller_args)
    parsed["playback_label"] = playback_label
    return parsed


def parse_style_performance_arc_live_gui_playback_transcript_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Return parsed CLI args for playback-transcript-compatible report commands."""

    return _parse_cli_args(argv)


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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_playback_transcript_report(
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_playback_transcript_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_playback_transcript_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_GUI_PLAYBACK_TRANSCRIPT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-playback-transcript-report",
    summary="Compose passive controller state into GUI playback transcript metadata.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_PLAYBACK_TRANSCRIPT_CLI_COMMAND)

__all__ = [
    "PLAYBACK_TRANSCRIPT_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_PLAYBACK_TRANSCRIPT_CLI_COMMAND",
    "StylePerformanceArcLiveGuiPlaybackAnalyzerCheckpoint",
    "StylePerformanceArcLiveGuiPlaybackAssertion",
    "StylePerformanceArcLiveGuiPlaybackEvent",
    "StylePerformanceArcLiveGuiPlaybackTranscriptReport",
    "build_style_performance_arc_live_gui_playback_transcript_from_controller_state",
    "build_style_performance_arc_live_gui_playback_transcript_report",
    "format_style_performance_arc_live_gui_playback_transcript_report",
    "parse_style_performance_arc_live_gui_playback_transcript_cli_args",
    "to_style_performance_arc_live_gui_playback_transcript_json",
]
