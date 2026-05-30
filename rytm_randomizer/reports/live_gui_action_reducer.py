"""Passive live GUI action-reducer packet for interaction-script state."""

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
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value
from .live_gui_interaction_script import (
    StylePerformanceArcLiveGuiControlBinding,
    StylePerformanceArcLiveGuiInteractionScriptReport,
    build_style_performance_arc_live_gui_interaction_script_report,
    parse_style_performance_arc_live_gui_interaction_script_cli_args,
    to_style_performance_arc_live_gui_interaction_script_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live GUI action reducer"
SOURCE_MODULE: Final[str] = "reports.live_gui_action_reducer"
ACTION_REDUCER_VERSION: Final[str] = "live-gui-action-reducer-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI reducer metadata only",
    "composes live GUI interaction script only",
    "control transitions are metadata only",
    "future desktop GUI only",
    "future GUI test harness only",
    "future audio analyzer comparison only",
    "capture decisions are read-only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
    "no GUI event dispatch",
    "no GUI reducer dispatch",
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
_DEFAULT_REDUCER_LABEL: Final[str] = "Live GUI action reducer"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-action-reducer-report usage: "
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
    "[--reducer-label <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiActionTransition:
    """One passive future-GUI action transition decision."""

    key: str
    order: int
    control_key: str
    control_type: str
    requested_action: str
    from_state: str
    to_state: str
    allowed: bool
    reason: str
    source: str
    test_id: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiActionReducerReport:
    """Passive reducer composed from an interaction script."""

    interaction_script: StylePerformanceArcLiveGuiInteractionScriptReport
    reducer_version: str
    reducer_id: str
    reducer_label: str
    reducer_status: str
    transitions: tuple[StylePerformanceArcLiveGuiActionTransition, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def script_id(self) -> str:
        """Return upstream interaction-script id."""

        return self.interaction_script.script_id

    @property
    def frame_id(self) -> str:
        """Return upstream analyzer-frame id."""

        return self.interaction_script.frame_id

    @property
    def overlay_id(self) -> str:
        """Return upstream analyzer-overlay id."""

        return self.interaction_script.overlay_id

    @property
    def render_tree_id(self) -> str:
        """Return upstream render-tree id."""

        return self.interaction_script.render_tree_id

    @property
    def screen_contract_id(self) -> str:
        """Return upstream screen-contract id."""

        return self.interaction_script.screen_contract_id

    @property
    def capture_review_id(self) -> str:
        """Return upstream capture-review id."""

        return self.interaction_script.capture_review_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.interaction_script.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.interaction_script.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.interaction_script.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _reducer_status(script: StylePerformanceArcLiveGuiInteractionScriptReport) -> str:
    if script.script_status == "blocked":
        return "blocked"
    if script.script_status == "review-needed":
        return "review-needed"
    return "ready"


def _reducer_id(
    script: StylePerformanceArcLiveGuiInteractionScriptReport,
    *,
    reducer_label: str,
    reducer_status: str,
) -> str:
    payload = "|".join(
        (
            ACTION_REDUCER_VERSION,
            script.script_id,
            script.frame_id,
            script.capture_review_id,
            reducer_label,
            reducer_status,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _test_id(*parts: str) -> str:
    return "-".join(part.replace(" ", "-").lower() for part in parts if part)


def _next_state_for_control(binding: StylePerformanceArcLiveGuiControlBinding) -> str:
    next_states: Final[dict[str, str]] = {
        "control-review-capture": "capture-review-open",
        "control-compare-reference": "reference-comparison-open",
        "control-repeat-take": "repeat-take-queued",
        "control-accept-capture": "capture-accepted",
    }
    return next_states.get(binding.key, "metadata-updated")


def _transition_reason(
    binding: StylePerformanceArcLiveGuiControlBinding,
    *,
    reducer_status: str,
    allowed: bool,
) -> str:
    if reducer_status == "blocked":
        return "Interaction script is blocked; reducer transition stays disabled."
    if allowed:
        return f"{binding.reason} Reducer may expose this as a passive GUI state change."
    return binding.reason


def _transition_for_binding(
    binding: StylePerformanceArcLiveGuiControlBinding,
    *,
    order: int,
    reducer_status: str,
) -> StylePerformanceArcLiveGuiActionTransition:
    allowed = reducer_status != "blocked" and binding.enabled
    return StylePerformanceArcLiveGuiActionTransition(
        key=f"action-transition-{binding.key}",
        order=order,
        control_key=binding.key,
        control_type=binding.control_type,
        requested_action=binding.operator_action,
        from_state=binding.state,
        to_state=_next_state_for_control(binding) if allowed else "blocked",
        allowed=allowed,
        reason=_transition_reason(
            binding,
            reducer_status=reducer_status,
            allowed=allowed,
        ),
        source=binding.source,
        test_id=_test_id("action", binding.key),
    )


def _transitions(
    script: StylePerformanceArcLiveGuiInteractionScriptReport,
    *,
    reducer_status: str,
) -> tuple[StylePerformanceArcLiveGuiActionTransition, ...]:
    return tuple(
        _transition_for_binding(
            binding,
            order=order,
            reducer_status=reducer_status,
        )
        for order, binding in enumerate(script.control_bindings)
    )


def _blocked_actions(reducer_status: str) -> tuple[str, ...]:
    actions = [
        "no GUI launch",
        "no GUI event dispatch",
        "no GUI reducer dispatch",
        "no GUI-triggered MIDI sends",
        "no file writing",
        "no audio recording",
        "no audio streaming",
        "no MIDI sending",
        "no port opening",
        "no hardware mutation",
    ]
    if reducer_status == "blocked":
        actions.append("hold action reducer before GUI controller binding")
    return tuple(actions)


def _replace_command(command: str, *, reducer_label: str) -> str:
    source = "style-performance-arc-live-gui-interaction-script-report"
    target = "style-performance-arc-live-gui-action-reducer-report"
    if source not in command:
        return (
            "python -m rytm_randomizer.cli "
            f"{target} --reducer-label {powershell_literal_arg(reducer_label)}"
        )
    replaced = command.replace(source, target, 1)
    if "--reducer-label" not in replaced:
        replaced = f"{replaced} --reducer-label {powershell_literal_arg(reducer_label)}"
    return replaced


def _replay_commands(
    script: StylePerformanceArcLiveGuiInteractionScriptReport,
    *,
    reducer_label: str,
) -> tuple[str, ...]:
    if not script.replay_commands:
        return (
            "python -m rytm_randomizer.cli "
            "style-performance-arc-live-gui-action-reducer-report "
            f"--reducer-label {powershell_literal_arg(reducer_label)}",
        )
    return (
        _replace_command(script.replay_commands[0], reducer_label=reducer_label),
        *script.replay_commands,
    )


def build_style_performance_arc_live_gui_action_reducer_from_interaction_script(
    interaction_script: StylePerformanceArcLiveGuiInteractionScriptReport,
    *,
    reducer_label: str = _DEFAULT_REDUCER_LABEL,
) -> StylePerformanceArcLiveGuiActionReducerReport:
    """Build a passive action reducer from an interaction script."""

    normalized_label = _normalize_nonblank(reducer_label, field="reducer_label")
    status = _reducer_status(interaction_script)
    return StylePerformanceArcLiveGuiActionReducerReport(
        interaction_script=interaction_script,
        reducer_version=ACTION_REDUCER_VERSION,
        reducer_id=_reducer_id(
            interaction_script,
            reducer_label=normalized_label,
            reducer_status=status,
        ),
        reducer_label=normalized_label,
        reducer_status=status,
        transitions=_transitions(interaction_script, reducer_status=status),
        blocked_actions=_blocked_actions(status),
        replay_commands=_replay_commands(interaction_script, reducer_label=normalized_label),
    )


def build_style_performance_arc_live_gui_action_reducer_report(
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
    reducer_label: str = _DEFAULT_REDUCER_LABEL,
) -> StylePerformanceArcLiveGuiActionReducerReport:
    """Build a passive action reducer from source evidence."""

    interaction_script = build_style_performance_arc_live_gui_interaction_script_report(
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
    )
    return build_style_performance_arc_live_gui_action_reducer_from_interaction_script(
        interaction_script,
        reducer_label=reducer_label,
    )


def _transition_json(
    transition: StylePerformanceArcLiveGuiActionTransition,
) -> dict[str, object]:
    return {
        "key": transition.key,
        "order": transition.order,
        "control_key": transition.control_key,
        "control_type": transition.control_type,
        "requested_action": transition.requested_action,
        "from_state": transition.from_state,
        "to_state": transition.to_state,
        "allowed": transition.allowed,
        "reason": transition.reason,
        "source": transition.source,
        "test_id": transition.test_id,
    }


def to_style_performance_arc_live_gui_action_reducer_json(
    report: StylePerformanceArcLiveGuiActionReducerReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI action-reducer payload."""

    script_json = to_style_performance_arc_live_gui_interaction_script_json(
        report.interaction_script
    )
    return {
        "live_gui_action_reducer": {
            "reducer_version": report.reducer_version,
            "reducer_id": report.reducer_id,
            "reducer_label": report.reducer_label,
            "reducer_status": report.reducer_status,
            "script_id": report.script_id,
            "frame_id": report.frame_id,
            "overlay_id": report.overlay_id,
            "render_tree_id": report.render_tree_id,
            "screen_contract_id": report.screen_contract_id,
            "capture_review_id": report.capture_review_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "transitions": [_transition_json(row) for row in report.transitions],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **script_json,
        "safety": list(SAFETY_LINES),
    }


def _transition_lines(transition: StylePerformanceArcLiveGuiActionTransition) -> list[str]:
    allowed = "allowed" if transition.allowed else "blocked"
    return [
        f"- {transition.order}. {transition.key}: {transition.control_key} / {allowed}",
        f"  Control type: {transition.control_type}",
        f"  From: {transition.from_state}",
        f"  To: {transition.to_state}",
        f"  Test id: {transition.test_id}",
        f"  Source: {transition.source}",
        f"  Action: {transition.requested_action}",
        f"  Reason: {transition.reason}",
    ]


def format_style_performance_arc_live_gui_action_reducer_report(
    report: StylePerformanceArcLiveGuiActionReducerReport,
) -> list[str]:
    """Return deterministic passive live GUI action-reducer lines."""

    lines = [
        "Live GUI action reducer summary:",
        f"- Reducer version: {report.reducer_version}",
        f"- Reducer id: {report.reducer_id}",
        f"- Reducer label: {report.reducer_label}",
        f"- Reducer status: {report.reducer_status}",
        f"- Interaction script id: {report.script_id}",
        f"- Frame id: {report.frame_id}",
        f"- Overlay id: {report.overlay_id}",
        f"- Render tree id: {report.render_tree_id}",
        f"- Screen contract id: {report.screen_contract_id}",
        f"- Capture review id: {report.capture_review_id}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        "GUI action transitions:",
    ]
    for transition in report.transitions:
        lines.extend(_transition_lines(transition))
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
    return pop_option_value(remaining, usage=_USAGE)


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    reducer_label = _DEFAULT_REDUCER_LABEL
    script_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--reducer-label":
            reducer_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="reducer_label",
            )
        else:
            script_args.append(option)
            if option != "--json":
                script_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_interaction_script_cli_args(script_args)
    parsed["reducer_label"] = reducer_label
    return parsed


def parse_style_performance_arc_live_gui_action_reducer_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Return parsed CLI args for action-reducer-compatible report commands."""

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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_action_reducer_report(
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_action_reducer_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_action_reducer_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


STYLE_PERFORMANCE_ARC_LIVE_GUI_ACTION_REDUCER_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-action-reducer-report",
    summary="Compose passive interaction script into GUI action reducer metadata.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_ACTION_REDUCER_CLI_COMMAND)

__all__ = [
    "ACTION_REDUCER_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_ACTION_REDUCER_CLI_COMMAND",
    "StylePerformanceArcLiveGuiActionReducerReport",
    "StylePerformanceArcLiveGuiActionTransition",
    "build_style_performance_arc_live_gui_action_reducer_from_interaction_script",
    "build_style_performance_arc_live_gui_action_reducer_report",
    "format_style_performance_arc_live_gui_action_reducer_report",
    "parse_style_performance_arc_live_gui_action_reducer_cli_args",
    "to_style_performance_arc_live_gui_action_reducer_json",
]
