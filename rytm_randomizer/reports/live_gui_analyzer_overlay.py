"""Passive live GUI analyzer-overlay packet for render-tree rehearsal state."""

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
from .live_gui_capture_review import (
    StylePerformanceArcLiveGuiCaptureDecision,
    StylePerformanceArcLiveGuiCaptureMetricReview,
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value

# The render-tree/screen-contract builder machinery was relocated verbatim
# to reports/live_gui_overlay/ when the standalone paper-spec report
# commands were retired (2026-07-28; see
# docs/superpowers/plans/2026-07-20-live-gui-retirement-evidence.md).
from .live_gui_overlay.render_tree import (
    StylePerformanceArcLiveGuiRenderNode,
    StylePerformanceArcLiveGuiRenderTreeReport,
    build_style_performance_arc_live_gui_render_tree_report,
    parse_style_performance_arc_live_gui_render_tree_cli_args,
    to_style_performance_arc_live_gui_render_tree_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live GUI analyzer overlay"
SOURCE_MODULE: Final[str] = "reports.live_gui_analyzer_overlay"
ANALYZER_OVERLAY_VERSION: Final[str] = "live-gui-analyzer-overlay-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive analyzer overlay only",
    "composes live GUI render tree only",
    "meter widgets are metadata only",
    "threshold markers are metadata only",
    "node annotations are metadata only",
    "future desktop GUI only",
    "future audio analyzer comparison only",
    "capture decisions are read-only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
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
_DEFAULT_OVERLAY_LABEL: Final[str] = "Live GUI analyzer overlay"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-analyzer-overlay-report usage: "
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
    "[--density standard|compact] [--overlay-label <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerMeterWidget:
    """One passive analyzer meter widget projected onto a render-tree node."""

    key: str
    metric_key: str
    label: str
    render_node_key: str
    target_value: str
    captured_value: str
    delta: str
    status: str
    display_token: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerThresholdMarker:
    """One passive visual threshold marker for a meter widget."""

    key: str
    meter_key: str
    band: str
    label: str
    status: str
    source: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerSelectedCaptureBadge:
    """One selected capture badge for the analyzer overlay."""

    slot_key: str
    decision: str
    status: str
    summary: str
    hold_reasons: tuple[str, ...]
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerNodeAnnotation:
    """One render-tree node annotation for future GUI overlay consumers."""

    key: str
    render_node_key: str
    annotation_type: str
    label: str
    status: str
    source: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiAnalyzerOverlayReport:
    """Passive analyzer overlay composed from a live GUI render tree."""

    render_tree: StylePerformanceArcLiveGuiRenderTreeReport
    overlay_version: str
    overlay_id: str
    overlay_label: str
    overlay_status: str
    selected_capture_badge: StylePerformanceArcLiveGuiAnalyzerSelectedCaptureBadge
    meter_widgets: tuple[StylePerformanceArcLiveGuiAnalyzerMeterWidget, ...]
    threshold_markers: tuple[StylePerformanceArcLiveGuiAnalyzerThresholdMarker, ...]
    node_annotations: tuple[StylePerformanceArcLiveGuiAnalyzerNodeAnnotation, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def render_tree_id(self) -> str:
        """Return upstream render-tree id."""

        return self.render_tree.render_tree_id

    @property
    def screen_contract_id(self) -> str:
        """Return upstream screen-contract id."""

        return self.render_tree.screen_contract_id

    @property
    def capture_review_id(self) -> str:
        """Return upstream capture-review id."""

        return self.render_tree.screen_contract.sidecar_session.capture_review_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.render_tree.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.render_tree.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.render_tree.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _selected_decision(
    render_tree: StylePerformanceArcLiveGuiRenderTreeReport,
) -> StylePerformanceArcLiveGuiCaptureDecision:
    capture_review = render_tree.screen_contract.sidecar_session.capture_review
    for decision in capture_review.decisions:
        if decision.slot_key == capture_review.captured_slot_key:
            return decision
    return capture_review.decisions[0]


def _overlay_status(
    render_tree: StylePerformanceArcLiveGuiRenderTreeReport,
    decision: StylePerformanceArcLiveGuiCaptureDecision,
) -> str:
    if render_tree.render_status == "hold" or decision.decision == "hold":
        return "blocked"
    if decision.decision == "repeat":
        return "review-needed"
    return "ready"


def _overlay_id(
    render_tree: StylePerformanceArcLiveGuiRenderTreeReport,
    *,
    overlay_label: str,
    decision: StylePerformanceArcLiveGuiCaptureDecision,
) -> str:
    payload = "|".join(
        (
            ANALYZER_OVERLAY_VERSION,
            render_tree.render_tree_id,
            render_tree.screen_contract_id,
            render_tree.screen_contract.sidecar_session.capture_review_id,
            decision.slot_key,
            decision.decision,
            overlay_label,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _node_keys(nodes: Sequence[StylePerformanceArcLiveGuiRenderNode]) -> frozenset[str]:
    return frozenset(node.key for node in nodes)


def _display_metric_key(metric: StylePerformanceArcLiveGuiCaptureMetricReview) -> str:
    if metric.key == "noise":
        return "texture"
    return metric.key


def _render_node_key(
    metric: StylePerformanceArcLiveGuiCaptureMetricReview,
    *,
    render_tree: StylePerformanceArcLiveGuiRenderTreeReport,
) -> str:
    keys = _node_keys(render_tree.nodes)
    display_key = _display_metric_key(metric)
    for candidate in (
        f"node-analyzer-{display_key}",
        f"node-analyzer-{metric.key}",
    ):
        if candidate in keys:
            return candidate
    return "region-analyzer-table"


def _meter_widgets(
    render_tree: StylePerformanceArcLiveGuiRenderTreeReport,
    *,
    decision: StylePerformanceArcLiveGuiCaptureDecision,
) -> tuple[StylePerformanceArcLiveGuiAnalyzerMeterWidget, ...]:
    return tuple(
        StylePerformanceArcLiveGuiAnalyzerMeterWidget(
            key=f"meter-{_display_metric_key(metric)}",
            metric_key=metric.key,
            label=metric.label,
            render_node_key=_render_node_key(metric, render_tree=render_tree),
            target_value=metric.target_value,
            captured_value=metric.captured_value,
            delta=metric.delta,
            status=metric.status,
            display_token=f"meter-{metric.status}",
            operator_action=metric.operator_action,
        )
        for metric in decision.metrics
    )


def _threshold_markers(
    meters: Sequence[StylePerformanceArcLiveGuiAnalyzerMeterWidget],
) -> tuple[StylePerformanceArcLiveGuiAnalyzerThresholdMarker, ...]:
    markers: list[StylePerformanceArcLiveGuiAnalyzerThresholdMarker] = []
    for meter in meters:
        for band, label in (
            ("pass", "pass band"),
            ("warn", "warning band"),
            ("hold", "hold band"),
        ):
            markers.append(
                StylePerformanceArcLiveGuiAnalyzerThresholdMarker(
                    key=f"{meter.key}-{band}",
                    meter_key=meter.key,
                    band=band,
                    label=f"{meter.label} {label}",
                    status="active" if meter.status == band else "inactive",
                    source="live_gui_capture_review.metrics",
                    operator_action=f"Paint {band} threshold marker for {meter.label}.",
                )
            )
    return tuple(markers)


def _selected_capture_badge(
    decision: StylePerformanceArcLiveGuiCaptureDecision,
) -> StylePerformanceArcLiveGuiAnalyzerSelectedCaptureBadge:
    return StylePerformanceArcLiveGuiAnalyzerSelectedCaptureBadge(
        slot_key=decision.slot_key,
        decision=decision.decision,
        status=decision.status,
        summary=decision.summary,
        hold_reasons=decision.hold_reasons,
        operator_action=decision.operator_action,
    )


def _capture_node_key(
    render_tree: StylePerformanceArcLiveGuiRenderTreeReport,
    *,
    slot_key: str,
) -> str:
    key = f"node-capture-{slot_key}"
    if key in _node_keys(render_tree.nodes):
        return key
    return "region-capture-table"


def _node_annotations(
    render_tree: StylePerformanceArcLiveGuiRenderTreeReport,
    *,
    meters: Sequence[StylePerformanceArcLiveGuiAnalyzerMeterWidget],
    decision: StylePerformanceArcLiveGuiCaptureDecision,
) -> tuple[StylePerformanceArcLiveGuiAnalyzerNodeAnnotation, ...]:
    annotations: list[StylePerformanceArcLiveGuiAnalyzerNodeAnnotation] = [
        StylePerformanceArcLiveGuiAnalyzerNodeAnnotation(
            key=f"annotation-{meter.key}",
            render_node_key=meter.render_node_key,
            annotation_type="meter",
            label=meter.label,
            status=meter.status,
            source="live_gui_capture_review.metrics",
            operator_action=f"Overlay analyzer meter {meter.label}.",
        )
        for meter in meters
    ]
    annotations.append(
        StylePerformanceArcLiveGuiAnalyzerNodeAnnotation(
            key=f"annotation-capture-{decision.slot_key}",
            render_node_key=_capture_node_key(render_tree, slot_key=decision.slot_key),
            annotation_type="capture-badge",
            label=f"{decision.slot_key} {decision.decision}",
            status=decision.status,
            source="live_gui_capture_review.decisions",
            operator_action=decision.operator_action,
        )
    )
    for node in render_tree.nodes:
        if node.node_type != "disabled-control":
            continue
        annotations.append(
            StylePerformanceArcLiveGuiAnalyzerNodeAnnotation(
                key=f"annotation-{node.key}",
                render_node_key=node.key,
                annotation_type="disabled-control",
                label=node.label,
                status=node.status,
                source=node.source,
                operator_action=node.operator_action,
            )
        )
    return tuple(annotations)


def _blocked_actions(
    render_tree: StylePerformanceArcLiveGuiRenderTreeReport,
    *,
    overlay_status: str,
) -> tuple[str, ...]:
    actions = (
        *render_tree.blocked_actions,
        "no GUI analyzer launch",
        "no GUI-triggered MIDI sends",
        "no GUI-triggered port opening",
        "no automatic audio recording",
        "no automatic capture recording",
        "no automatic hardware arming",
        "no automatic kit mutation",
        "hold render tree before overlay launch" if overlay_status == "blocked" else "",
        "no MIDI sending",
        "no port opening",
    )
    return tuple(dict.fromkeys(action for action in actions if action))


def _replay_command(
    render_tree: StylePerformanceArcLiveGuiRenderTreeReport,
    *,
    overlay_label: str,
) -> str:
    fallback_command = (
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-analyzer-overlay-report"
    )
    if render_tree.replay_commands:
        render_command = render_tree.replay_commands[0]
        command = render_command.replace(
            "style-performance-arc-live-gui-render-tree-report",
            "style-performance-arc-live-gui-analyzer-overlay-report",
            1,
        )
        if command == render_command:
            command = fallback_command
    else:
        command = fallback_command
    return f"{command} --overlay-label {powershell_literal_arg(overlay_label)}"


def build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree(
    render_tree: StylePerformanceArcLiveGuiRenderTreeReport,
    *,
    overlay_label: str = _DEFAULT_OVERLAY_LABEL,
) -> StylePerformanceArcLiveGuiAnalyzerOverlayReport:
    """Build one passive analyzer overlay from a render tree."""

    normalized_label = _normalize_nonblank(overlay_label, field="overlay_label")
    decision = _selected_decision(render_tree)
    status = _overlay_status(render_tree, decision)
    meters = _meter_widgets(render_tree, decision=decision)
    return StylePerformanceArcLiveGuiAnalyzerOverlayReport(
        render_tree=render_tree,
        overlay_version=ANALYZER_OVERLAY_VERSION,
        overlay_id=_overlay_id(render_tree, overlay_label=normalized_label, decision=decision),
        overlay_label=normalized_label,
        overlay_status=status,
        selected_capture_badge=_selected_capture_badge(decision),
        meter_widgets=meters,
        threshold_markers=_threshold_markers(meters),
        node_annotations=_node_annotations(render_tree, meters=meters, decision=decision),
        blocked_actions=_blocked_actions(render_tree, overlay_status=status),
        replay_commands=(
            _replay_command(render_tree, overlay_label=normalized_label),
            *render_tree.replay_commands,
        ),
    )


def build_style_performance_arc_live_gui_analyzer_overlay_report(
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
    overlay_label: str = _DEFAULT_OVERLAY_LABEL,
) -> StylePerformanceArcLiveGuiAnalyzerOverlayReport:
    """Build a passive analyzer overlay from source evidence."""

    render_tree = build_style_performance_arc_live_gui_render_tree_report(
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
    )
    return build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree(
        render_tree,
        overlay_label=overlay_label,
    )


def _meter_json(meter: StylePerformanceArcLiveGuiAnalyzerMeterWidget) -> dict[str, object]:
    return {
        "key": meter.key,
        "metric_key": meter.metric_key,
        "label": meter.label,
        "render_node_key": meter.render_node_key,
        "target_value": meter.target_value,
        "captured_value": meter.captured_value,
        "delta": meter.delta,
        "status": meter.status,
        "display_token": meter.display_token,
        "operator_action": meter.operator_action,
    }


def _marker_json(
    marker: StylePerformanceArcLiveGuiAnalyzerThresholdMarker,
) -> dict[str, object]:
    return {
        "key": marker.key,
        "meter_key": marker.meter_key,
        "band": marker.band,
        "label": marker.label,
        "status": marker.status,
        "source": marker.source,
        "operator_action": marker.operator_action,
    }


def _badge_json(
    badge: StylePerformanceArcLiveGuiAnalyzerSelectedCaptureBadge,
) -> dict[str, object]:
    return {
        "slot_key": badge.slot_key,
        "decision": badge.decision,
        "status": badge.status,
        "summary": badge.summary,
        "hold_reasons": list(badge.hold_reasons),
        "operator_action": badge.operator_action,
    }


def _annotation_json(
    annotation: StylePerformanceArcLiveGuiAnalyzerNodeAnnotation,
) -> dict[str, object]:
    return {
        "key": annotation.key,
        "render_node_key": annotation.render_node_key,
        "annotation_type": annotation.annotation_type,
        "label": annotation.label,
        "status": annotation.status,
        "source": annotation.source,
        "operator_action": annotation.operator_action,
    }


def to_style_performance_arc_live_gui_analyzer_overlay_json(
    report: StylePerformanceArcLiveGuiAnalyzerOverlayReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI analyzer-overlay payload."""

    render_tree_json = to_style_performance_arc_live_gui_render_tree_json(report.render_tree)
    return {
        "live_gui_analyzer_overlay": {
            "overlay_version": report.overlay_version,
            "overlay_id": report.overlay_id,
            "overlay_label": report.overlay_label,
            "overlay_status": report.overlay_status,
            "render_tree_id": report.render_tree_id,
            "screen_contract_id": report.screen_contract_id,
            "capture_review_id": report.capture_review_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "selected_capture_badge": _badge_json(report.selected_capture_badge),
            "meter_widgets": [_meter_json(meter) for meter in report.meter_widgets],
            "threshold_markers": [_marker_json(marker) for marker in report.threshold_markers],
            "node_annotations": [
                _annotation_json(annotation) for annotation in report.node_annotations
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **render_tree_json,
        "safety": list(SAFETY_LINES),
    }


def _meter_lines(meter: StylePerformanceArcLiveGuiAnalyzerMeterWidget) -> list[str]:
    return [
        f"- {meter.key} / {meter.label}: {meter.status} / {meter.delta}",
        f"  Node: {meter.render_node_key}",
        f"  Target -> captured: {meter.target_value} -> {meter.captured_value}",
        f"  Token: {meter.display_token}",
        f"  Action: {meter.operator_action}",
    ]


def _marker_lines(
    marker: StylePerformanceArcLiveGuiAnalyzerThresholdMarker,
) -> list[str]:
    return [
        f"- {marker.key}: {marker.band} / {marker.status}",
        f"  Meter: {marker.meter_key}",
        f"  Source: {marker.source}",
        f"  Action: {marker.operator_action}",
    ]


def _annotation_lines(
    annotation: StylePerformanceArcLiveGuiAnalyzerNodeAnnotation,
) -> list[str]:
    return [
        f"- {annotation.key}: {annotation.annotation_type} / {annotation.status}",
        f"  Node: {annotation.render_node_key}",
        f"  Source: {annotation.source}",
        f"  Action: {annotation.operator_action}",
    ]


def format_style_performance_arc_live_gui_analyzer_overlay_report(
    report: StylePerformanceArcLiveGuiAnalyzerOverlayReport,
) -> list[str]:
    """Return deterministic passive live GUI analyzer-overlay lines."""

    badge = report.selected_capture_badge
    lines = [
        "Live GUI analyzer overlay summary:",
        f"- Overlay version: {report.overlay_version}",
        f"- Overlay id: {report.overlay_id}",
        f"- Overlay label: {report.overlay_label}",
        f"- Overlay status: {report.overlay_status}",
        f"- Render tree id: {report.render_tree_id}",
        f"- Screen contract id: {report.screen_contract_id}",
        f"- Capture review id: {report.capture_review_id}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        "Selected capture badge:",
        f"- {badge.slot_key}: {badge.decision} / {badge.status}",
        f"  Summary: {badge.summary}",
        f"  Action: {badge.operator_action}",
    ]
    if badge.hold_reasons:
        lines.append("  Hold reasons:")
        lines.extend(f"  - {reason}" for reason in badge.hold_reasons)
    lines.append("Meter widgets:")
    for meter in report.meter_widgets:
        lines.extend(_meter_lines(meter))
    lines.append("Threshold markers:")
    for marker in report.threshold_markers:
        lines.extend(_marker_lines(marker))
    lines.append("Node annotations:")
    for annotation in report.node_annotations:
        lines.extend(_annotation_lines(annotation))
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
    overlay_label = _DEFAULT_OVERLAY_LABEL
    render_tree_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--overlay-label":
            overlay_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="overlay_label",
            )
        else:
            render_tree_args.append(option)
            if option != "--json":
                render_tree_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_render_tree_cli_args(render_tree_args)
    parsed["overlay_label"] = overlay_label
    return parsed


def parse_style_performance_arc_live_gui_analyzer_overlay_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Return parsed CLI args for analyzer-overlay-compatible report commands."""

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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_analyzer_overlay_report(
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_analyzer_overlay_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_analyzer_overlay_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_OVERLAY_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-analyzer-overlay-report",
    summary="Compose passive render tree into GUI analyzer overlay metadata.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_OVERLAY_CLI_COMMAND)

__all__ = [
    "ANALYZER_OVERLAY_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_ANALYZER_OVERLAY_CLI_COMMAND",
    "StylePerformanceArcLiveGuiAnalyzerMeterWidget",
    "StylePerformanceArcLiveGuiAnalyzerNodeAnnotation",
    "StylePerformanceArcLiveGuiAnalyzerOverlayReport",
    "StylePerformanceArcLiveGuiAnalyzerSelectedCaptureBadge",
    "StylePerformanceArcLiveGuiAnalyzerThresholdMarker",
    "build_style_performance_arc_live_gui_analyzer_overlay_from_render_tree",
    "build_style_performance_arc_live_gui_analyzer_overlay_report",
    "format_style_performance_arc_live_gui_analyzer_overlay_report",
    "parse_style_performance_arc_live_gui_analyzer_overlay_cli_args",
    "to_style_performance_arc_live_gui_analyzer_overlay_json",
]
