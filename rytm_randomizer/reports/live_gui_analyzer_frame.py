"""Passive live GUI analyzer-frame packet for overlay rehearsal state."""

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
from .live_gui_analyzer_overlay import (
    StylePerformanceArcLiveGuiAnalyzerOverlayReport,
    build_style_performance_arc_live_gui_analyzer_overlay_report,
    parse_style_performance_arc_live_gui_analyzer_overlay_cli_args,
    to_style_performance_arc_live_gui_analyzer_overlay_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live GUI analyzer frame"
SOURCE_MODULE: Final[str] = "reports.live_gui_analyzer_frame"
ANALYZER_FRAME_VERSION: Final[str] = "live-gui-analyzer-frame-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive analyzer frame only",
    "composes live GUI analyzer overlay only",
    "frame events are metadata only",
    "visual assertions are metadata only",
    "future desktop GUI only",
    "future GUI test harness only",
    "future audio analyzer comparison only",
    "capture decisions are read-only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
    "no GUI frame rendering",
    "no window creation",
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
_DEFAULT_FRAME_LABEL: Final[str] = "Live GUI analyzer frame"
_DISABLED_CONTROL_STATE: Final[str] = "disabled"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-analyzer-frame-report usage: "
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
    "[--frame-label <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerFrameEvent:
    """One ordered passive GUI/analyzer frame event."""

    key: str
    order: int
    event_type: str
    target_key: str
    label: str
    status: str
    source: str
    test_id: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerVisualAssertion:
    """One deterministic GUI test-harness assertion."""

    key: str
    assertion_type: str
    target_key: str
    expected_status: str
    expected_token: str
    source: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerFrameReport:
    """Passive analyzer frame contract composed from an analyzer overlay."""

    overlay: StylePerformanceArcLiveGuiAnalyzerOverlayReport
    frame_version: str
    frame_id: str
    frame_label: str
    frame_status: str
    frame_events: tuple[StylePerformanceArcLiveGuiAnalyzerFrameEvent, ...]
    visual_assertions: tuple[StylePerformanceArcLiveGuiAnalyzerVisualAssertion, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def overlay_id(self) -> str:
        """Return upstream analyzer-overlay id."""

        return self.overlay.overlay_id

    @property
    def render_tree_id(self) -> str:
        """Return upstream render-tree id."""

        return self.overlay.render_tree_id

    @property
    def screen_contract_id(self) -> str:
        """Return upstream screen-contract id."""

        return self.overlay.screen_contract_id

    @property
    def capture_review_id(self) -> str:
        """Return upstream capture-review id."""

        return self.overlay.capture_review_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.overlay.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.overlay.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.overlay.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _frame_status(overlay: StylePerformanceArcLiveGuiAnalyzerOverlayReport) -> str:
    if overlay.overlay_status == "blocked":
        return "blocked"
    if overlay.overlay_status == "review-needed":
        return "review-needed"
    return "ready"


def _frame_id(
    overlay: StylePerformanceArcLiveGuiAnalyzerOverlayReport,
    *,
    frame_label: str,
    frame_status: str,
) -> str:
    payload = "|".join(
        (
            ANALYZER_FRAME_VERSION,
            overlay.overlay_id,
            overlay.render_tree_id,
            overlay.capture_review_id,
            frame_label,
            frame_status,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _test_id(*parts: str) -> str:
    return "-".join(part.replace(" ", "-").lower() for part in parts if part)


def _frame_events(
    overlay: StylePerformanceArcLiveGuiAnalyzerOverlayReport,
) -> tuple[StylePerformanceArcLiveGuiAnalyzerFrameEvent, ...]:
    events: list[StylePerformanceArcLiveGuiAnalyzerFrameEvent] = [
        StylePerformanceArcLiveGuiAnalyzerFrameEvent(
            key="frame-event-mount-overlay",
            order=0,
            event_type="mount-overlay",
            target_key=overlay.overlay_id,
            label=overlay.overlay_label,
            status=overlay.overlay_status,
            source="live_gui_analyzer_overlay",
            test_id=_test_id("overlay", overlay.overlay_id),
            operator_action="Mount the passive analyzer overlay packet.",
        )
    ]
    for meter in overlay.meter_widgets:
        events.append(
            StylePerformanceArcLiveGuiAnalyzerFrameEvent(
                key=f"frame-event-{meter.key}",
                order=len(events),
                event_type="paint-meter",
                target_key=meter.key,
                label=meter.label,
                status=meter.status,
                source=meter.render_node_key,
                test_id=_test_id("meter", meter.key),
                operator_action=f"Paint analyzer meter {meter.label}.",
            )
        )
    for marker in overlay.threshold_markers:
        events.append(
            StylePerformanceArcLiveGuiAnalyzerFrameEvent(
                key=f"frame-event-{marker.key}",
                order=len(events),
                event_type="paint-threshold-marker",
                target_key=marker.key,
                label=marker.label,
                status=marker.status,
                source=marker.source,
                test_id=_test_id("threshold", marker.key),
                operator_action=f"Paint {marker.band} threshold marker.",
            )
        )
    badge = overlay.selected_capture_badge
    events.append(
        StylePerformanceArcLiveGuiAnalyzerFrameEvent(
            key=f"frame-event-capture-badge-{badge.slot_key}",
            order=len(events),
            event_type="paint-capture-badge",
            target_key=badge.slot_key,
            label=f"{badge.slot_key} {badge.decision}",
            status=badge.status,
            source="live_gui_analyzer_overlay.selected_capture_badge",
            test_id=_test_id("capture-badge", badge.slot_key),
            operator_action=badge.operator_action,
        )
    )
    for annotation in overlay.node_annotations:
        if annotation.annotation_type != "disabled-control":
            continue
        events.append(
            StylePerformanceArcLiveGuiAnalyzerFrameEvent(
                key=f"frame-event-lock-{annotation.render_node_key}",
                order=len(events),
                event_type="lock-disabled-control",
                target_key=annotation.render_node_key,
                label=annotation.label,
                status=annotation.status,
                source=annotation.source,
                test_id=_test_id("disabled", annotation.render_node_key),
                operator_action=annotation.operator_action,
            )
        )
    return tuple(events)


def _visual_assertions(
    overlay: StylePerformanceArcLiveGuiAnalyzerOverlayReport,
) -> tuple[StylePerformanceArcLiveGuiAnalyzerVisualAssertion, ...]:
    assertions: list[StylePerformanceArcLiveGuiAnalyzerVisualAssertion] = []
    for meter in overlay.meter_widgets:
        assertions.append(
            StylePerformanceArcLiveGuiAnalyzerVisualAssertion(
                key=f"assertion-{meter.key}",
                assertion_type="meter-status",
                target_key=meter.key,
                expected_status=meter.status,
                expected_token=meter.display_token,
                source=meter.render_node_key,
                operator_action=f"Assert analyzer meter {meter.label} is {meter.status}.",
            )
        )
    for marker in overlay.threshold_markers:
        assertions.append(
            StylePerformanceArcLiveGuiAnalyzerVisualAssertion(
                key=f"assertion-{marker.key}",
                assertion_type="threshold-marker-state",
                target_key=marker.key,
                expected_status=marker.status,
                expected_token=marker.band,
                source=marker.source,
                operator_action=f"Assert {marker.band} marker for {marker.meter_key}.",
            )
        )
    badge = overlay.selected_capture_badge
    assertions.append(
        StylePerformanceArcLiveGuiAnalyzerVisualAssertion(
            key=f"assertion-capture-badge-{badge.slot_key}",
            assertion_type="capture-badge-state",
            target_key=badge.slot_key,
            expected_status=badge.status,
            expected_token=badge.decision,
            source="live_gui_analyzer_overlay.selected_capture_badge",
            operator_action=f"Assert selected capture badge {badge.slot_key}.",
        )
    )
    for annotation in overlay.node_annotations:
        if annotation.annotation_type != "disabled-control":
            continue
        assertions.append(
            StylePerformanceArcLiveGuiAnalyzerVisualAssertion(
                key=f"assertion-disabled-{annotation.render_node_key}",
                assertion_type="disabled-control-lock",
                target_key=annotation.render_node_key,
                expected_status=annotation.status,
                expected_token=_DISABLED_CONTROL_STATE,
                source=annotation.source,
                operator_action=f"Assert disabled control lock for {annotation.label}.",
            )
        )
    return tuple(assertions)


def _blocked_actions(
    overlay: StylePerformanceArcLiveGuiAnalyzerOverlayReport,
    *,
    frame_status: str,
) -> tuple[str, ...]:
    actions = (
        *overlay.blocked_actions,
        "no GUI frame rendering",
        "no GUI mount",
        "no GUI test harness launch",
        "no GUI-triggered MIDI sends",
        "no GUI-triggered port opening",
        "no automatic audio recording",
        "no automatic audio streaming",
        "no automatic hardware arming",
        "no automatic kit mutation",
        "hold overlay before frame render" if frame_status == "blocked" else "",
        "no MIDI sending",
        "no port opening",
    )
    return tuple(dict.fromkeys(action for action in actions if action))


def _replay_command(
    overlay: StylePerformanceArcLiveGuiAnalyzerOverlayReport,
    *,
    frame_label: str,
) -> str:
    fallback_command = (
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-analyzer-frame-report"
    )
    if overlay.replay_commands:
        overlay_command = overlay.replay_commands[0]
        command = overlay_command.replace(
            "style-performance-arc-live-gui-analyzer-overlay-report",
            "style-performance-arc-live-gui-analyzer-frame-report",
            1,
        )
        if command == overlay_command:
            command = fallback_command
    else:
        command = fallback_command
    return f"{command} --frame-label {powershell_literal_arg(frame_label)}"


def build_style_performance_arc_live_gui_analyzer_frame_from_overlay(
    overlay: StylePerformanceArcLiveGuiAnalyzerOverlayReport,
    *,
    frame_label: str = _DEFAULT_FRAME_LABEL,
) -> StylePerformanceArcLiveGuiAnalyzerFrameReport:
    """Build one passive analyzer frame from an analyzer overlay."""

    normalized_label = _normalize_nonblank(frame_label, field="frame_label")
    status = _frame_status(overlay)
    return StylePerformanceArcLiveGuiAnalyzerFrameReport(
        overlay=overlay,
        frame_version=ANALYZER_FRAME_VERSION,
        frame_id=_frame_id(overlay, frame_label=normalized_label, frame_status=status),
        frame_label=normalized_label,
        frame_status=status,
        frame_events=_frame_events(overlay),
        visual_assertions=_visual_assertions(overlay),
        blocked_actions=_blocked_actions(overlay, frame_status=status),
        replay_commands=(
            _replay_command(overlay, frame_label=normalized_label),
            *overlay.replay_commands,
        ),
    )


def build_style_performance_arc_live_gui_analyzer_frame_report(
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
    frame_label: str = _DEFAULT_FRAME_LABEL,
) -> StylePerformanceArcLiveGuiAnalyzerFrameReport:
    """Build a passive analyzer frame from source evidence."""

    overlay = build_style_performance_arc_live_gui_analyzer_overlay_report(
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
    )
    return build_style_performance_arc_live_gui_analyzer_frame_from_overlay(
        overlay,
        frame_label=frame_label,
    )


def _event_json(event: StylePerformanceArcLiveGuiAnalyzerFrameEvent) -> dict[str, object]:
    return {
        "key": event.key,
        "order": event.order,
        "event_type": event.event_type,
        "target_key": event.target_key,
        "label": event.label,
        "status": event.status,
        "source": event.source,
        "test_id": event.test_id,
        "operator_action": event.operator_action,
    }


def _assertion_json(
    assertion: StylePerformanceArcLiveGuiAnalyzerVisualAssertion,
) -> dict[str, object]:
    return {
        "key": assertion.key,
        "assertion_type": assertion.assertion_type,
        "target_key": assertion.target_key,
        "expected_status": assertion.expected_status,
        "expected_token": assertion.expected_token,
        "source": assertion.source,
        "operator_action": assertion.operator_action,
    }


def to_style_performance_arc_live_gui_analyzer_frame_json(
    report: StylePerformanceArcLiveGuiAnalyzerFrameReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI analyzer-frame payload."""

    overlay_json = to_style_performance_arc_live_gui_analyzer_overlay_json(report.overlay)
    return {
        "live_gui_analyzer_frame": {
            "frame_version": report.frame_version,
            "frame_id": report.frame_id,
            "frame_label": report.frame_label,
            "frame_status": report.frame_status,
            "overlay_id": report.overlay_id,
            "render_tree_id": report.render_tree_id,
            "screen_contract_id": report.screen_contract_id,
            "capture_review_id": report.capture_review_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "frame_events": [_event_json(event) for event in report.frame_events],
            "visual_assertions": [
                _assertion_json(assertion) for assertion in report.visual_assertions
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **overlay_json,
        "safety": list(SAFETY_LINES),
    }


def _event_lines(event: StylePerformanceArcLiveGuiAnalyzerFrameEvent) -> list[str]:
    return [
        f"- {event.order}. {event.key}: {event.event_type} / {event.status}",
        f"  Target: {event.target_key}",
        f"  Test id: {event.test_id}",
        f"  Source: {event.source}",
        f"  Action: {event.operator_action}",
    ]


def _assertion_lines(
    assertion: StylePerformanceArcLiveGuiAnalyzerVisualAssertion,
) -> list[str]:
    return [
        f"- {assertion.key}: {assertion.assertion_type} / {assertion.expected_status}",
        f"  Target: {assertion.target_key}",
        f"  Token: {assertion.expected_token}",
        f"  Source: {assertion.source}",
        f"  Action: {assertion.operator_action}",
    ]


def format_style_performance_arc_live_gui_analyzer_frame_report(
    report: StylePerformanceArcLiveGuiAnalyzerFrameReport,
) -> list[str]:
    """Return deterministic passive live GUI analyzer-frame lines."""

    lines = [
        "Live GUI analyzer frame summary:",
        f"- Frame version: {report.frame_version}",
        f"- Frame id: {report.frame_id}",
        f"- Frame label: {report.frame_label}",
        f"- Frame status: {report.frame_status}",
        f"- Overlay id: {report.overlay_id}",
        f"- Render tree id: {report.render_tree_id}",
        f"- Screen contract id: {report.screen_contract_id}",
        f"- Capture review id: {report.capture_review_id}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        "Frame events:",
    ]
    for event in report.frame_events:
        lines.extend(_event_lines(event))
    lines.append("Visual assertions:")
    for assertion in report.visual_assertions:
        lines.extend(_assertion_lines(assertion))
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
    frame_label = _DEFAULT_FRAME_LABEL
    overlay_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--frame-label":
            frame_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="frame_label",
            )
        else:
            overlay_args.append(option)
            if option != "--json":
                overlay_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_analyzer_overlay_cli_args(overlay_args)
    parsed["frame_label"] = frame_label
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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_analyzer_frame_report(
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_analyzer_frame_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_analyzer_frame_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_FRAME_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-analyzer-frame-report",
    summary="Compose passive analyzer overlay into GUI frame metadata.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_FRAME_CLI_COMMAND)

__all__ = [
    "ANALYZER_FRAME_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_FRAME_CLI_COMMAND",
    "StylePerformanceArcLiveGuiAnalyzerFrameEvent",
    "StylePerformanceArcLiveGuiAnalyzerFrameReport",
    "StylePerformanceArcLiveGuiAnalyzerVisualAssertion",
    "build_style_performance_arc_live_gui_analyzer_frame_from_overlay",
    "build_style_performance_arc_live_gui_analyzer_frame_report",
    "format_style_performance_arc_live_gui_analyzer_frame_report",
    "to_style_performance_arc_live_gui_analyzer_frame_json",
]
