"""Passive live GUI render-tree packet for screen-contract rehearsal state."""

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
from .live_gui_screen_contract import (
    StylePerformanceArcLiveGuiScreenAlert,
    StylePerformanceArcLiveGuiScreenComponent,
    StylePerformanceArcLiveGuiScreenContractReport,
    StylePerformanceArcLiveGuiScreenRegion,
    StylePerformanceArcLiveGuiScreenTableRow,
    build_style_performance_arc_live_gui_screen_contract_report,
    parse_style_performance_arc_live_gui_screen_contract_cli_args,
    to_style_performance_arc_live_gui_screen_contract_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live GUI render tree"
SOURCE_MODULE: Final[str] = "reports.live_gui_render_tree"
RENDER_TREE_VERSION: Final[str] = "live-gui-render-tree-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI render tree only",
    "composes live GUI screen contract only",
    "deterministic GUI node tree only",
    "render nodes are metadata only",
    "bindings are metadata only",
    "future desktop GUI only",
    "future audio analyzer comparison only",
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
_DEFAULT_RENDER_TARGET: Final[str] = "desktop-sidecar"
_DEFAULT_DENSITY: Final[str] = "standard"
_RENDER_TARGETS: Final[tuple[str, ...]] = (
    "desktop-sidecar",
    "test-harness",
    "operator-dashboard",
)
_DENSITIES: Final[tuple[str, ...]] = ("standard", "compact")
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-render-tree-report usage: "
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
    "[--density standard|compact] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiRenderNode:
    """One deterministic GUI render-tree node."""

    key: str
    parent_key: str | None
    node_type: str
    role: str
    label: str
    status: str
    enabled: bool
    source: str
    test_id: str
    style_tokens: tuple[str, ...]
    binding_keys: tuple[str, ...]
    child_keys: tuple[str, ...]
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiRenderBinding:
    """One GUI-facing binding from render node to screen-contract source."""

    key: str
    source: str
    target_node_key: str
    value: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiRenderTreeReport:
    """Passive GUI render tree composed from a screen contract."""

    screen_contract: StylePerformanceArcLiveGuiScreenContractReport
    render_tree_version: str
    render_tree_id: str
    render_target: str
    density: str
    render_status: str
    root_node: StylePerformanceArcLiveGuiRenderNode
    nodes: tuple[StylePerformanceArcLiveGuiRenderNode, ...]
    bindings: tuple[StylePerformanceArcLiveGuiRenderBinding, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def screen_contract_id(self) -> str:
        """Return upstream screen-contract id."""

        return self.screen_contract.screen_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.screen_contract.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.screen_contract.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.screen_contract.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _normalize_render_target(value: str) -> str:
    normalized = _normalize_nonblank(value, field="render_target")
    if normalized not in _RENDER_TARGETS:
        raise ValueError(
            "render target must be desktop-sidecar, test-harness, or operator-dashboard"
        )
    return normalized


def _normalize_density(value: str) -> str:
    normalized = _normalize_nonblank(value, field="density")
    if normalized not in _DENSITIES:
        raise ValueError("density must be standard or compact")
    return normalized


def _render_tree_id(
    screen_contract: StylePerformanceArcLiveGuiScreenContractReport,
    *,
    render_target: str,
    density: str,
) -> str:
    payload = "|".join(
        (
            RENDER_TREE_VERSION,
            screen_contract.screen_id,
            screen_contract.screen_status,
            render_target,
            density,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _test_id(key: str) -> str:
    return f"live-gui-{key.replace('_', '-').replace(' ', '-')}"


def _root_style_tokens(
    screen_contract: StylePerformanceArcLiveGuiScreenContractReport,
    *,
    render_target: str,
    density: str,
) -> tuple[str, ...]:
    return (
        f"target-{render_target}",
        f"density-{density}",
        f"status-{screen_contract.screen_status}",
        f"viewport-{screen_contract.viewport}",
    )


def _node_style_tokens(
    *,
    role: str,
    status: str,
    density: str,
) -> tuple[str, ...]:
    return (f"role-{role}", f"status-{status}", f"density-{density}")


def _region_node(
    region: StylePerformanceArcLiveGuiScreenRegion,
    *,
    status: str,
    density: str,
    child_keys: tuple[str, ...],
) -> StylePerformanceArcLiveGuiRenderNode:
    key = f"region-{region.key}"
    return StylePerformanceArcLiveGuiRenderNode(
        key=key,
        parent_key="root",
        node_type="region",
        role=region.role,
        label=region.label,
        status=status,
        enabled=False,
        source=region.source,
        test_id=_test_id(key),
        style_tokens=_node_style_tokens(role=region.role, status=status, density=density),
        binding_keys=region.component_keys,
        child_keys=child_keys,
        operator_action=f"Render {region.label} region.",
    )


def _component_node(
    component: StylePerformanceArcLiveGuiScreenComponent,
    *,
    density: str,
) -> StylePerformanceArcLiveGuiRenderNode:
    node_type = (
        "disabled-control" if component.component_type == "disabled-control" else "component"
    )
    key = (
        f"control-{component.key}"
        if node_type == "disabled-control"
        else f"component-{component.key}"
    )
    return StylePerformanceArcLiveGuiRenderNode(
        key=key,
        parent_key=f"region-{component.region_key}",
        node_type=node_type,
        role=component.component_type,
        label=component.label,
        status=component.status,
        enabled=component.enabled,
        source=component.source,
        test_id=_test_id(key),
        style_tokens=_node_style_tokens(
            role=component.component_type,
            status=component.status,
            density=density,
        ),
        binding_keys=(component.key,),
        child_keys=(),
        operator_action=component.operator_action,
    )


def _table_row_parent(row: StylePerformanceArcLiveGuiScreenTableRow) -> str:
    if row.key.startswith(("analyzer-", "empty-analyzer")):
        return "region-analyzer-table"
    return "region-capture-table"


def _table_row_node(
    row: StylePerformanceArcLiveGuiScreenTableRow,
    *,
    density: str,
) -> StylePerformanceArcLiveGuiRenderNode:
    key = f"node-{row.key}"
    return StylePerformanceArcLiveGuiRenderNode(
        key=key,
        parent_key=_table_row_parent(row),
        node_type="table-row",
        role=row.row_type,
        label=row.label,
        status=row.status,
        enabled=False,
        source=f"live_gui_screen_contract.{row.row_type}_rows",
        test_id=_test_id(key),
        style_tokens=_node_style_tokens(role=row.row_type, status=row.status, density=density),
        binding_keys=(row.key,),
        child_keys=(),
        operator_action=row.operator_action,
    )


def _alert_node(
    alert: StylePerformanceArcLiveGuiScreenAlert,
    *,
    density: str,
) -> StylePerformanceArcLiveGuiRenderNode:
    key = f"alert-{alert.key}"
    return StylePerformanceArcLiveGuiRenderNode(
        key=key,
        parent_key="region-header",
        node_type="alert",
        role=alert.severity,
        label=alert.label,
        status=alert.severity,
        enabled=False,
        source=alert.source,
        test_id=_test_id(key),
        style_tokens=_node_style_tokens(
            role=alert.severity,
            status=alert.severity,
            density=density,
        ),
        binding_keys=(alert.key,),
        child_keys=(),
        operator_action=alert.message,
    )


def _child_keys_for_region(
    screen_contract: StylePerformanceArcLiveGuiScreenContractReport,
    *,
    region_key: str,
) -> tuple[str, ...]:
    component_keys = tuple(
        (
            f"control-{component.key}"
            if component.component_type == "disabled-control"
            else f"component-{component.key}"
        )
        for component in screen_contract.components
        if component.region_key == region_key and component.component_type not in {"table-row"}
    )
    row_keys = tuple(
        f"node-{row.key}"
        for row in screen_contract.table_rows
        if (region_key == "analyzer-table" and row.key.startswith(("analyzer-", "empty-analyzer")))
        or (
            region_key == "capture-table"
            and not row.key.startswith(("analyzer-", "empty-analyzer"))
        )
    )
    alert_keys = tuple(
        f"alert-{alert.key}" for alert in screen_contract.alerts if region_key == "header"
    )
    return (*component_keys, *row_keys, *alert_keys)


def _root_node(
    screen_contract: StylePerformanceArcLiveGuiScreenContractReport,
    *,
    render_target: str,
    density: str,
) -> StylePerformanceArcLiveGuiRenderNode:
    return StylePerformanceArcLiveGuiRenderNode(
        key="root",
        parent_key=None,
        node_type="root",
        role="application",
        label=screen_contract.screen_label,
        status=screen_contract.screen_status,
        enabled=False,
        source="live_gui_screen_contract",
        test_id="live-gui-root",
        style_tokens=_root_style_tokens(
            screen_contract,
            render_target=render_target,
            density=density,
        ),
        binding_keys=("selected-arc", "sidecar-status", "current-cue", "blocked-actions"),
        child_keys=tuple(f"region-{region.key}" for region in screen_contract.regions),
        operator_action="Render the passive screen contract as a deterministic tree.",
    )


def _nodes(
    screen_contract: StylePerformanceArcLiveGuiScreenContractReport,
    *,
    render_target: str,
    density: str,
) -> tuple[StylePerformanceArcLiveGuiRenderNode, ...]:
    root = _root_node(screen_contract, render_target=render_target, density=density)
    region_nodes = tuple(
        _region_node(
            region,
            status=screen_contract.screen_status,
            density=density,
            child_keys=_child_keys_for_region(screen_contract, region_key=region.key),
        )
        for region in screen_contract.regions
    )
    component_nodes = tuple(
        _component_node(component, density=density)
        for component in screen_contract.components
        if component.component_type not in {"table-row", "disabled-control"}
    )
    table_nodes = tuple(_table_row_node(row, density=density) for row in screen_contract.table_rows)
    control_nodes = tuple(
        _component_node(component, density=density)
        for component in screen_contract.interaction_controls
    )
    alert_nodes = tuple(_alert_node(alert, density=density) for alert in screen_contract.alerts)
    return (*((root,)), *region_nodes, *component_nodes, *table_nodes, *control_nodes, *alert_nodes)


def _binding(
    *,
    key: str,
    source: str,
    target_node_key: str,
    value: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiRenderBinding:
    return StylePerformanceArcLiveGuiRenderBinding(
        key=key,
        source=source,
        target_node_key=target_node_key,
        value=value,
        operator_action=operator_action,
    )


def _bindings(
    screen_contract: StylePerformanceArcLiveGuiScreenContractReport,
) -> tuple[StylePerformanceArcLiveGuiRenderBinding, ...]:
    return (
        _binding(
            key="selected-arc",
            source="live_gui_screen_contract.selected_arc",
            target_node_key="component-selected-arc",
            value=f"{screen_contract.selected_arc_key} / {screen_contract.selected_arc_name}",
            operator_action="Bind selected arc label.",
        ),
        _binding(
            key="sidecar-status",
            source="live_gui_screen_contract.screen_status",
            target_node_key="component-sidecar-status",
            value=screen_contract.screen_status,
            operator_action="Bind screen status badge.",
        ),
        _binding(
            key="current-cue",
            source="live_gui_screen_contract.current_cue_label",
            target_node_key="component-current-cue",
            value=screen_contract.current_cue_label,
            operator_action="Bind current cue label.",
        ),
        _binding(
            key="next-cues",
            source="live_gui_screen_contract.next_cue_labels",
            target_node_key="component-next-cues",
            value=", ".join(screen_contract.next_cue_labels),
            operator_action="Bind lookahead cue labels.",
        ),
        _binding(
            key="primary-action",
            source="live_gui_screen_contract.primary_action",
            target_node_key="component-primary-action",
            value=screen_contract.primary_action.label,
            operator_action="Bind passive primary action label.",
        ),
        _binding(
            key="machine-panels",
            source="live_gui_screen_contract.components.machine_panels",
            target_node_key="region-machine-panels",
            value=str(
                sum(
                    1
                    for component in screen_contract.components
                    if component.region_key == "machine-panels"
                )
            ),
            operator_action="Bind machine-panel component count.",
        ),
        _binding(
            key="analyzer-rows",
            source="live_gui_screen_contract.table_rows.analyzer",
            target_node_key="region-analyzer-table",
            value=str(
                sum(
                    1
                    for row in screen_contract.table_rows
                    if row.key.startswith(("analyzer-", "empty-analyzer"))
                )
            ),
            operator_action="Bind analyzer row count.",
        ),
        _binding(
            key="capture-rows",
            source="live_gui_screen_contract.table_rows.capture",
            target_node_key="region-capture-table",
            value=str(
                sum(
                    1
                    for row in screen_contract.table_rows
                    if not row.key.startswith(("analyzer-", "empty-analyzer"))
                )
            ),
            operator_action="Bind capture row count.",
        ),
        _binding(
            key="alerts",
            source="live_gui_screen_contract.alerts",
            target_node_key="region-header",
            value=str(len(screen_contract.alerts)),
            operator_action="Bind screen alert count.",
        ),
        _binding(
            key="blocked-actions",
            source="live_gui_screen_contract.blocked_actions",
            target_node_key="region-safety-bar",
            value=str(len(screen_contract.blocked_actions)),
            operator_action="Bind blocked active action count.",
        ),
    )


def _blocked_actions(
    screen_contract: StylePerformanceArcLiveGuiScreenContractReport,
) -> tuple[str, ...]:
    actions = (
        *screen_contract.blocked_actions,
        "no GUI render launch",
        "no GUI-triggered MIDI sends",
        "no GUI-triggered port opening",
        "no automatic audio recording",
        "no automatic hardware arming",
        "no automatic kit mutation",
        "no MIDI sending",
        "no port opening",
    )
    return tuple(dict.fromkeys(actions))


def _replay_command(
    screen_contract: StylePerformanceArcLiveGuiScreenContractReport,
    *,
    render_target: str,
    density: str,
) -> str:
    fallback_command = (
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-render-tree-report"
    )
    if screen_contract.replay_commands:
        screen_command = screen_contract.replay_commands[0]
        command = screen_command.replace(
            "style-performance-arc-live-gui-screen-contract-report",
            "style-performance-arc-live-gui-render-tree-report",
            1,
        )
        if command == screen_command:
            command = fallback_command
    else:
        command = fallback_command
    return (
        f"{command} "
        f"--render-target {powershell_literal_arg(render_target)} "
        f"--density {powershell_literal_arg(density)}"
    )


def build_style_performance_arc_live_gui_render_tree_from_screen_contract(
    screen_contract: StylePerformanceArcLiveGuiScreenContractReport,
    *,
    render_target: str = _DEFAULT_RENDER_TARGET,
    density: str = _DEFAULT_DENSITY,
) -> StylePerformanceArcLiveGuiRenderTreeReport:
    """Build one passive GUI render tree from a screen contract."""

    normalized_target = _normalize_render_target(render_target)
    normalized_density = _normalize_density(density)
    nodes = _nodes(
        screen_contract,
        render_target=normalized_target,
        density=normalized_density,
    )
    root = nodes[0]
    return StylePerformanceArcLiveGuiRenderTreeReport(
        screen_contract=screen_contract,
        render_tree_version=RENDER_TREE_VERSION,
        render_tree_id=_render_tree_id(
            screen_contract,
            render_target=normalized_target,
            density=normalized_density,
        ),
        render_target=normalized_target,
        density=normalized_density,
        render_status=screen_contract.screen_status,
        root_node=root,
        nodes=nodes,
        bindings=_bindings(screen_contract),
        blocked_actions=_blocked_actions(screen_contract),
        replay_commands=(
            _replay_command(
                screen_contract,
                render_target=normalized_target,
                density=normalized_density,
            ),
            *screen_contract.replay_commands,
        ),
    )


def build_style_performance_arc_live_gui_render_tree_report(
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
    render_target: str = _DEFAULT_RENDER_TARGET,
    density: str = _DEFAULT_DENSITY,
) -> StylePerformanceArcLiveGuiRenderTreeReport:
    """Build a passive GUI render tree from source evidence."""

    screen_contract = build_style_performance_arc_live_gui_screen_contract_report(
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
    )
    return build_style_performance_arc_live_gui_render_tree_from_screen_contract(
        screen_contract,
        render_target=render_target,
        density=density,
    )


def _node_json(node: StylePerformanceArcLiveGuiRenderNode) -> dict[str, object]:
    return {
        "key": node.key,
        "parent_key": node.parent_key,
        "node_type": node.node_type,
        "role": node.role,
        "label": node.label,
        "status": node.status,
        "enabled": node.enabled,
        "source": node.source,
        "test_id": node.test_id,
        "style_tokens": list(node.style_tokens),
        "binding_keys": list(node.binding_keys),
        "child_keys": list(node.child_keys),
        "operator_action": node.operator_action,
    }


def _binding_json(binding: StylePerformanceArcLiveGuiRenderBinding) -> dict[str, object]:
    return {
        "key": binding.key,
        "source": binding.source,
        "target_node_key": binding.target_node_key,
        "value": binding.value,
        "operator_action": binding.operator_action,
    }


def to_style_performance_arc_live_gui_render_tree_json(
    report: StylePerformanceArcLiveGuiRenderTreeReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI render-tree payload."""

    screen_json = to_style_performance_arc_live_gui_screen_contract_json(report.screen_contract)
    return {
        "live_gui_render_tree": {
            "render_tree_version": report.render_tree_version,
            "render_tree_id": report.render_tree_id,
            "render_target": report.render_target,
            "density": report.density,
            "render_status": report.render_status,
            "screen_contract_id": report.screen_contract_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "root_node": _node_json(report.root_node),
            "nodes": [_node_json(node) for node in report.nodes],
            "bindings": [_binding_json(binding) for binding in report.bindings],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **screen_json,
        "safety": list(SAFETY_LINES),
    }


def _node_lines(node: StylePerformanceArcLiveGuiRenderNode) -> list[str]:
    state = "enabled" if node.enabled else "disabled"
    parent = node.parent_key or "none"
    return [
        f"- {node.key} / {node.label}: {node.node_type} / {node.status} / {state}",
        f"  Parent: {parent}",
        f"  Role: {node.role}",
        f"  Test id: {node.test_id}",
        f"  Style tokens: {', '.join(node.style_tokens) or 'none'}",
        f"  Bindings: {', '.join(node.binding_keys) or 'none'}",
        f"  Children: {', '.join(node.child_keys) or 'none'}",
        f"  Action: {node.operator_action}",
    ]


def _binding_lines(binding: StylePerformanceArcLiveGuiRenderBinding) -> list[str]:
    return [
        f"- {binding.key}: {binding.source} -> {binding.target_node_key}",
        f"  Value: {binding.value}",
        f"  Action: {binding.operator_action}",
    ]


def format_style_performance_arc_live_gui_render_tree_report(
    report: StylePerformanceArcLiveGuiRenderTreeReport,
) -> list[str]:
    """Return deterministic passive live GUI render-tree lines."""

    lines = [
        "Live GUI render tree summary:",
        f"- Render tree version: {report.render_tree_version}",
        f"- Render tree id: {report.render_tree_id}",
        f"- Render target: {report.render_target}",
        f"- Density: {report.density}",
        f"- Render status: {report.render_status}",
        f"- Screen contract id: {report.screen_contract_id}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        "Root node:",
        *_node_lines(report.root_node),
        "Render nodes:",
    ]
    for node in report.nodes:
        lines.extend(_node_lines(node))
    lines.append("Render bindings:")
    for binding in report.bindings:
        lines.extend(_binding_lines(binding))
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
    render_target = _DEFAULT_RENDER_TARGET
    density = _DEFAULT_DENSITY
    screen_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--render-target":
            render_target = _normalize_render_target(_pop_option_value(remaining))
        elif option == "--density":
            density = _normalize_density(_pop_option_value(remaining))
        else:
            screen_args.append(option)
            if option != "--json":
                screen_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_screen_contract_cli_args(screen_args)
    parsed["render_target"] = render_target
    parsed["density"] = density
    return parsed


def parse_style_performance_arc_live_gui_render_tree_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Return parsed CLI args for render-tree-compatible report commands."""

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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_render_tree_report(
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_render_tree_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_render_tree_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_GUI_RENDER_TREE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-render-tree-report",
    summary="Compose passive screen contract into a deterministic GUI render tree.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_RENDER_TREE_CLI_COMMAND)

__all__ = [
    "RENDER_TREE_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_RENDER_TREE_CLI_COMMAND",
    "StylePerformanceArcLiveGuiRenderBinding",
    "StylePerformanceArcLiveGuiRenderNode",
    "StylePerformanceArcLiveGuiRenderTreeReport",
    "build_style_performance_arc_live_gui_render_tree_from_screen_contract",
    "build_style_performance_arc_live_gui_render_tree_report",
    "format_style_performance_arc_live_gui_render_tree_report",
    "parse_style_performance_arc_live_gui_render_tree_cli_args",
    "to_style_performance_arc_live_gui_render_tree_json",
]
