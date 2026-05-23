"""Passive live GUI controller-state packet for reducer state."""

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
from .live_gui_action_reducer import (
    StylePerformanceArcLiveGuiActionReducerReport,
    StylePerformanceArcLiveGuiActionTransition,
    build_style_performance_arc_live_gui_action_reducer_report,
    parse_style_performance_arc_live_gui_action_reducer_cli_args,
    to_style_performance_arc_live_gui_action_reducer_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live GUI controller state"
SOURCE_MODULE: Final[str] = "reports.live_gui_controller_state"
CONTROLLER_STATE_VERSION: Final[str] = "live-gui-controller-state-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI controller-state metadata only",
    "composes live GUI action reducer only",
    "control states are metadata only",
    "queued GUI actions are metadata only",
    "future desktop GUI only",
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
_DEFAULT_CONTROLLER_LABEL: Final[str] = "Live GUI controller state"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-controller-state-report usage: "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] [--takes N] "
    "[--slot capture-001] [--label <text>] [--capture-prefix <text>] "
    "[--sidecar-label <text>] [--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiControlState:
    """One passive future-GUI control state row."""

    key: str
    order: int
    control_key: str
    control_type: str
    source_state: str
    current_state: str
    enabled: bool
    reason: str
    reducer_transition_key: str
    test_id: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiQueuedAction:
    """One passive queued GUI action derived from an allowed transition."""

    key: str
    order: int
    control_key: str
    requested_action: str
    target_state: str
    reducer_transition_key: str
    test_id: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiControllerStateReport:
    """Passive controller state composed from an action reducer."""

    action_reducer: StylePerformanceArcLiveGuiActionReducerReport
    controller_version: str
    controller_id: str
    controller_label: str
    controller_status: str
    control_states: tuple[StylePerformanceArcLiveGuiControlState, ...]
    queued_actions: tuple[StylePerformanceArcLiveGuiQueuedAction, ...]
    blocked_controls: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def reducer_id(self) -> str:
        """Return upstream reducer id."""

        return self.action_reducer.reducer_id

    @property
    def script_id(self) -> str:
        """Return upstream interaction-script id."""

        return self.action_reducer.script_id

    @property
    def frame_id(self) -> str:
        """Return upstream analyzer-frame id."""

        return self.action_reducer.frame_id

    @property
    def overlay_id(self) -> str:
        """Return upstream analyzer-overlay id."""

        return self.action_reducer.overlay_id

    @property
    def render_tree_id(self) -> str:
        """Return upstream render-tree id."""

        return self.action_reducer.render_tree_id

    @property
    def screen_contract_id(self) -> str:
        """Return upstream screen-contract id."""

        return self.action_reducer.screen_contract_id

    @property
    def capture_review_id(self) -> str:
        """Return upstream capture-review id."""

        return self.action_reducer.capture_review_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.action_reducer.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.action_reducer.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.action_reducer.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _controller_status(reducer: StylePerformanceArcLiveGuiActionReducerReport) -> str:
    if reducer.reducer_status == "blocked":
        return "blocked"
    if reducer.reducer_status == "review-needed":
        return "review-needed"
    return "ready"


def _controller_id(
    reducer: StylePerformanceArcLiveGuiActionReducerReport,
    *,
    controller_label: str,
    controller_status: str,
) -> str:
    payload = "|".join(
        (
            CONTROLLER_STATE_VERSION,
            reducer.reducer_id,
            reducer.script_id,
            reducer.capture_review_id,
            controller_label,
            controller_status,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _test_id(*parts: str) -> str:
    return "-".join(part.replace(" ", "-").lower() for part in parts if part)


def _control_state_for_transition(
    transition: StylePerformanceArcLiveGuiActionTransition,
    *,
    controller_status: str,
) -> StylePerformanceArcLiveGuiControlState:
    enabled = controller_status != "blocked" and transition.allowed
    current_state = transition.to_state if enabled else "blocked"
    reason = transition.reason
    if controller_status == "blocked":
        reason = "Action reducer is blocked; controller state stays disabled."
    return StylePerformanceArcLiveGuiControlState(
        key=f"control-state-{transition.control_key}",
        order=transition.order,
        control_key=transition.control_key,
        control_type=transition.control_type,
        source_state=transition.from_state,
        current_state=current_state,
        enabled=enabled,
        reason=reason,
        reducer_transition_key=transition.key,
        test_id=_test_id("controller", transition.control_key),
    )


def _control_states(
    reducer: StylePerformanceArcLiveGuiActionReducerReport,
    *,
    controller_status: str,
) -> tuple[StylePerformanceArcLiveGuiControlState, ...]:
    return tuple(
        _control_state_for_transition(
            transition,
            controller_status=controller_status,
        )
        for transition in reducer.transitions
    )


def _queued_actions(
    reducer: StylePerformanceArcLiveGuiActionReducerReport,
    *,
    controller_status: str,
) -> tuple[StylePerformanceArcLiveGuiQueuedAction, ...]:
    if controller_status == "blocked":
        return ()
    return tuple(
        StylePerformanceArcLiveGuiQueuedAction(
            key=f"queued-gui-action-{transition.control_key}",
            order=index,
            control_key=transition.control_key,
            requested_action=transition.requested_action,
            target_state=transition.to_state,
            reducer_transition_key=transition.key,
            test_id=_test_id("queued", transition.control_key),
        )
        for index, transition in enumerate(
            transition for transition in reducer.transitions if transition.allowed
        )
    )


def _blocked_controls(
    control_states: Sequence[StylePerformanceArcLiveGuiControlState],
) -> tuple[str, ...]:
    return tuple(state.control_key for state in control_states if not state.enabled)


def _blocked_actions(controller_status: str) -> tuple[str, ...]:
    actions = [
        "no GUI launch",
        "no GUI event dispatch",
        "no GUI controller dispatch",
        "no GUI state-store mutation",
        "no GUI-triggered MIDI sends",
        "no file writing",
        "no audio recording",
        "no audio streaming",
        "no MIDI sending",
        "no port opening",
        "no hardware mutation",
    ]
    if controller_status == "blocked":
        actions.append("hold controller state before GUI runtime binding")
    return tuple(actions)


def _replace_command(command: str, *, controller_label: str) -> str | None:
    source = "style-performance-arc-live-gui-action-reducer-report"
    target = "style-performance-arc-live-gui-controller-state-report"
    if source not in command:
        return None
    replaced = command.replace(source, target, 1)
    if "--controller-label" not in replaced:
        replaced = f"{replaced} --controller-label {powershell_literal_arg(controller_label)}"
    return replaced


def _replay_commands(
    reducer: StylePerformanceArcLiveGuiActionReducerReport,
    *,
    controller_label: str,
) -> tuple[str, ...]:
    if not reducer.replay_commands:
        return ()
    controller_command = _replace_command(
        reducer.replay_commands[0],
        controller_label=controller_label,
    )
    if controller_command is None:
        return ()
    return (
        controller_command,
        *reducer.replay_commands,
    )


def build_style_performance_arc_live_gui_controller_state_from_action_reducer(
    action_reducer: StylePerformanceArcLiveGuiActionReducerReport,
    *,
    controller_label: str = _DEFAULT_CONTROLLER_LABEL,
) -> StylePerformanceArcLiveGuiControllerStateReport:
    """Build passive controller state from an action reducer."""

    normalized_label = _normalize_nonblank(controller_label, field="controller_label")
    status = _controller_status(action_reducer)
    control_states = _control_states(action_reducer, controller_status=status)
    return StylePerformanceArcLiveGuiControllerStateReport(
        action_reducer=action_reducer,
        controller_version=CONTROLLER_STATE_VERSION,
        controller_id=_controller_id(
            action_reducer,
            controller_label=normalized_label,
            controller_status=status,
        ),
        controller_label=normalized_label,
        controller_status=status,
        control_states=control_states,
        queued_actions=_queued_actions(action_reducer, controller_status=status),
        blocked_controls=_blocked_controls(control_states),
        blocked_actions=_blocked_actions(status),
        replay_commands=_replay_commands(
            action_reducer,
            controller_label=normalized_label,
        ),
    )


def build_style_performance_arc_live_gui_controller_state_report(
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
    controller_label: str = _DEFAULT_CONTROLLER_LABEL,
) -> StylePerformanceArcLiveGuiControllerStateReport:
    """Build passive controller state from source evidence."""

    action_reducer = build_style_performance_arc_live_gui_action_reducer_report(
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
    )
    return build_style_performance_arc_live_gui_controller_state_from_action_reducer(
        action_reducer,
        controller_label=controller_label,
    )


def _control_state_json(
    control_state: StylePerformanceArcLiveGuiControlState,
) -> dict[str, object]:
    return {
        "key": control_state.key,
        "order": control_state.order,
        "control_key": control_state.control_key,
        "control_type": control_state.control_type,
        "source_state": control_state.source_state,
        "current_state": control_state.current_state,
        "enabled": control_state.enabled,
        "reason": control_state.reason,
        "reducer_transition_key": control_state.reducer_transition_key,
        "test_id": control_state.test_id,
    }


def _queued_action_json(
    queued_action: StylePerformanceArcLiveGuiQueuedAction,
) -> dict[str, object]:
    return {
        "key": queued_action.key,
        "order": queued_action.order,
        "control_key": queued_action.control_key,
        "requested_action": queued_action.requested_action,
        "target_state": queued_action.target_state,
        "reducer_transition_key": queued_action.reducer_transition_key,
        "test_id": queued_action.test_id,
    }


def to_style_performance_arc_live_gui_controller_state_json(
    report: StylePerformanceArcLiveGuiControllerStateReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI controller-state payload."""

    reducer_json = to_style_performance_arc_live_gui_action_reducer_json(report.action_reducer)
    return {
        "live_gui_controller_state": {
            "controller_version": report.controller_version,
            "controller_id": report.controller_id,
            "controller_label": report.controller_label,
            "controller_status": report.controller_status,
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
            "control_states": [_control_state_json(row) for row in report.control_states],
            "queued_actions": [_queued_action_json(row) for row in report.queued_actions],
            "blocked_controls": list(report.blocked_controls),
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **reducer_json,
        "safety": list(SAFETY_LINES),
    }


def _control_state_lines(control_state: StylePerformanceArcLiveGuiControlState) -> list[str]:
    enabled = "enabled" if control_state.enabled else "blocked"
    return [
        f"- {control_state.order}. {control_state.key}: "
        f"{control_state.control_key} / {enabled}",
        f"  Control type: {control_state.control_type}",
        f"  Source state: {control_state.source_state}",
        f"  Current state: {control_state.current_state}",
        f"  Reducer transition: {control_state.reducer_transition_key}",
        f"  Test id: {control_state.test_id}",
        f"  Reason: {control_state.reason}",
    ]


def _queued_action_lines(queued_action: StylePerformanceArcLiveGuiQueuedAction) -> list[str]:
    return [
        f"- {queued_action.order}. {queued_action.key}: {queued_action.control_key}",
        f"  Action: {queued_action.requested_action}",
        f"  Target state: {queued_action.target_state}",
        f"  Reducer transition: {queued_action.reducer_transition_key}",
        f"  Test id: {queued_action.test_id}",
    ]


def format_style_performance_arc_live_gui_controller_state_report(
    report: StylePerformanceArcLiveGuiControllerStateReport,
) -> list[str]:
    """Return deterministic passive live GUI controller-state lines."""

    lines = [
        "Live GUI controller state summary:",
        f"- Controller version: {report.controller_version}",
        f"- Controller id: {report.controller_id}",
        f"- Controller label: {report.controller_label}",
        f"- Controller status: {report.controller_status}",
        f"- Action reducer id: {report.reducer_id}",
        f"- Interaction script id: {report.script_id}",
        f"- Frame id: {report.frame_id}",
        f"- Overlay id: {report.overlay_id}",
        f"- Render tree id: {report.render_tree_id}",
        f"- Screen contract id: {report.screen_contract_id}",
        f"- Capture review id: {report.capture_review_id}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        "GUI control states:",
    ]
    for control_state in report.control_states:
        lines.extend(_control_state_lines(control_state))
    lines.append("Queued allowed GUI actions:")
    if report.queued_actions:
        for queued_action in report.queued_actions:
            lines.extend(_queued_action_lines(queued_action))
    else:
        lines.append("- none")
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
    controller_label = _DEFAULT_CONTROLLER_LABEL
    reducer_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--controller-label":
            controller_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="controller_label",
            )
        else:
            reducer_args.append(option)
            if option != "--json":
                reducer_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_action_reducer_cli_args(reducer_args)
    parsed["controller_label"] = controller_label
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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_controller_state_report(
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_controller_state_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_controller_state_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_GUI_CONTROLLER_STATE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-controller-state-report",
    summary="Compose passive action reducer into GUI controller state metadata.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_CONTROLLER_STATE_CLI_COMMAND)

__all__ = [
    "CONTROLLER_STATE_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_CONTROLLER_STATE_CLI_COMMAND",
    "StylePerformanceArcLiveGuiControllerStateReport",
    "StylePerformanceArcLiveGuiControlState",
    "StylePerformanceArcLiveGuiQueuedAction",
    "build_style_performance_arc_live_gui_controller_state_from_action_reducer",
    "build_style_performance_arc_live_gui_controller_state_report",
    "format_style_performance_arc_live_gui_controller_state_report",
    "to_style_performance_arc_live_gui_controller_state_json",
]
