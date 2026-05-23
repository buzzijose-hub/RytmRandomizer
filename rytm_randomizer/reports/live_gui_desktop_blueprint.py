"""Passive live GUI desktop blueprint for future operator surfaces."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.live_gui_contracts import (
    LIVE_GUI_DESKTOP_MOUNT_REGION_SPECS,
    LIVE_GUI_DESKTOP_REGION_SPECS,
    LIVE_GUI_DESKTOP_VIEWPORT_SPECS,
)
from ..style_analysis.feature_report import FeatureReport
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value, replace_replay_command, status_severity
from .live_gui_implementation_bridge import (
    StylePerformanceArcLiveGuiImplementationBridgeReport,
    build_style_performance_arc_live_gui_implementation_bridge_report,
    parse_style_performance_arc_live_gui_implementation_bridge_cli_args,
    to_style_performance_arc_live_gui_implementation_bridge_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live GUI desktop blueprint"
SOURCE_MODULE: Final[str] = "reports.live_gui_desktop_blueprint"
DESKTOP_BLUEPRINT_VERSION: Final[str] = "live-gui-desktop-blueprint-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI desktop blueprint metadata only",
    "consumes live GUI implementation bridge metadata only",
    "desktop shell metadata only",
    "viewports are declarative metadata only",
    "regions are declarative metadata only",
    "widgets are declarative metadata only",
    "bindings are declarative metadata only",
    "implementation tasks are advisory metadata only",
    "fixture file hints are advisory metadata only",
    "acceptance checks are advisory metadata only",
    "future desktop GUI only",
    "future audio analyzer comparison only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
    "no GUI renderer start",
    "no renderer execution",
    "no GUI event dispatch",
    "no GUI controller dispatch",
    "no GUI state-store mutation",
    "no GUI test runner execution",
    "no bundler or dev-server launch",
    "no command execution",
    "no file writing",
    "no audio recording",
    "no audio streaming",
    "no audio read/compare execution",
    "no real MIDI rendering",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_DEFAULT_BLUEPRINT_LABEL: Final[str] = "Live GUI desktop blueprint"
_DEFAULT_DESKTOP_SHELL: Final[str] = "operator-dashboard"
_DEFAULT_LAYOUT_KEY: Final[str] = "operator-cockpit"
_DEFAULT_DENSITY: Final[str] = "standard"
_DESKTOP_SHELLS: Final[tuple[str, ...]] = (
    "operator-dashboard",
    "desktop-sidecar",
    "test-harness",
)
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-desktop-blueprint-report usage: "
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
    "[--playback-label <text>] [--validation-label <text>] "
    "[--harness-label <text>] [--readiness-label <text>] "
    "[--bridge-label <text>] [--blueprint-label <text>] "
    "[--desktop-shell operator-dashboard|desktop-sidecar|test-harness] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopBlueprintViewport:
    """One future desktop viewport target."""

    viewport_key: str
    width_px: int
    height_px: int
    density: str
    layout_key: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopBlueprintRegion:
    """One future desktop layout region."""

    region_key: str
    order: int
    label: str
    role: str
    source_component_key: str
    grid_area: str
    min_width_px: int
    min_height_px: int
    enabled: bool
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopBlueprintWidget:
    """One future widget binding target."""

    widget_key: str
    order: int
    region_key: str
    widget_type: str
    source_packet_key: str
    source_json_key: str
    test_id: str
    state: str
    bind_enabled: bool
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopBlueprintBinding:
    """One declarative view-model binding."""

    binding_key: str
    order: int
    source_packet_key: str
    source_json_path: str
    target_widget_key: str
    target_prop: str
    fallback_value: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopBlueprintSection:
    """One implementation blueprint section."""

    section_key: str
    order: int
    title: str
    source_packet_key: str
    source_json_key: str
    objective: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopBlueprintTask:
    """One disabled future desktop implementation task."""

    task_key: str
    order: int
    region_key: str
    widget_key: str
    source_component_key: str
    title: str
    enabled: bool
    blocked_reason: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopBlueprintFixtureHint:
    """One future fixture-file hint that does not write a file."""

    fixture_key: str
    order: int
    source_fixture_key: str
    source_packet_key: str
    suggested_path: str
    purpose: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopBlueprintAcceptanceCheck:
    """One future desktop blueprint acceptance check."""

    check_key: str
    label: str
    status: str
    severity: str
    source_id: str
    message: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopBlueprintReport:
    """Passive desktop blueprint composed from implementation bridge metadata."""

    implementation_bridge: StylePerformanceArcLiveGuiImplementationBridgeReport
    blueprint_version: str
    blueprint_id: str
    blueprint_label: str
    blueprint_status: str
    desktop_shell: str
    section_summary: str
    task_summary: str
    fixture_summary: str
    viewport_summary: str
    binding_summary: str
    viewports: tuple[StylePerformanceArcLiveGuiDesktopBlueprintViewport, ...]
    regions: tuple[StylePerformanceArcLiveGuiDesktopBlueprintRegion, ...]
    widgets: tuple[StylePerformanceArcLiveGuiDesktopBlueprintWidget, ...]
    bindings: tuple[StylePerformanceArcLiveGuiDesktopBlueprintBinding, ...]
    sections: tuple[StylePerformanceArcLiveGuiDesktopBlueprintSection, ...]
    implementation_tasks: tuple[StylePerformanceArcLiveGuiDesktopBlueprintTask, ...]
    fixture_file_hints: tuple[StylePerformanceArcLiveGuiDesktopBlueprintFixtureHint, ...]
    acceptance_checks: tuple[StylePerformanceArcLiveGuiDesktopBlueprintAcceptanceCheck, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def bridge_id(self) -> str:
        """Return upstream implementation bridge id."""

        return self.implementation_bridge.bridge_id

    @property
    def readiness_id(self) -> str:
        """Return upstream readiness id."""

        return self.implementation_bridge.readiness_id

    @property
    def contract_id(self) -> str:
        """Return upstream contract id."""

        return self.implementation_bridge.contract_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected performance arc key."""

        return self.implementation_bridge.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected performance arc name."""

        return self.implementation_bridge.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.implementation_bridge.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _normalize_desktop_shell(value: str) -> str:
    normalized = _normalize_nonblank(value, field="desktop_shell")
    if normalized not in _DESKTOP_SHELLS:
        raise ValueError(
            "desktop_shell must be operator-dashboard, desktop-sidecar, or test-harness"
        )
    return normalized


def _coverage_status(count: int) -> str:
    if count <= 0:
        return "blocked"
    return "ready"


def _blueprint_id(
    bridge: StylePerformanceArcLiveGuiImplementationBridgeReport,
    *,
    blueprint_label: str,
    blueprint_status: str,
    desktop_shell: str,
) -> str:
    payload = "|".join(
        (
            DESKTOP_BLUEPRINT_VERSION,
            bridge.bridge_id,
            bridge.readiness_id,
            bridge.selected_arc_key,
            bridge.scope,
            desktop_shell,
            blueprint_label,
            blueprint_status,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _viewports(
    *,
    density: str,
    layout_key: str,
) -> tuple[StylePerformanceArcLiveGuiDesktopBlueprintViewport, ...]:
    return tuple(
        StylePerformanceArcLiveGuiDesktopBlueprintViewport(
            viewport_key=spec.viewport_key,
            width_px=spec.width_px,
            height_px=spec.height_px,
            density=density if spec.density_mode == "requested" else spec.density_mode,
            layout_key=layout_key,
            passive=True,
        )
        for spec in LIVE_GUI_DESKTOP_VIEWPORT_SPECS
    )


def _region(
    *,
    region_key: str,
    order: int,
    label: str,
    role: str,
    source_component_key: str,
    grid_area: str,
    min_width_px: int,
    min_height_px: int,
) -> StylePerformanceArcLiveGuiDesktopBlueprintRegion:
    return StylePerformanceArcLiveGuiDesktopBlueprintRegion(
        region_key=region_key,
        order=order,
        label=label,
        role=role,
        source_component_key=source_component_key,
        grid_area=grid_area,
        min_width_px=min_width_px,
        min_height_px=min_height_px,
        enabled=False,
        passive=True,
    )


def _regions() -> tuple[StylePerformanceArcLiveGuiDesktopBlueprintRegion, ...]:
    return tuple(
        _region(
            region_key=spec.region_key,
            order=spec.order,
            label=spec.label,
            role=spec.role,
            source_component_key=spec.source_component_key,
            grid_area=spec.grid_area,
            min_width_px=spec.min_width_px,
            min_height_px=spec.min_height_px,
        )
        for spec in LIVE_GUI_DESKTOP_REGION_SPECS
    )


def _widget(
    *,
    widget_key: str,
    order: int,
    region_key: str,
    widget_type: str,
    source_packet_key: str,
    source_json_key: str,
    test_id: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiDesktopBlueprintWidget:
    return StylePerformanceArcLiveGuiDesktopBlueprintWidget(
        widget_key=widget_key,
        order=order,
        region_key=region_key,
        widget_type=widget_type,
        source_packet_key=source_packet_key,
        source_json_key=source_json_key,
        test_id=test_id,
        state="disabled",
        bind_enabled=False,
        operator_action=operator_action,
        passive=True,
    )


def _widgets(
    bridge: StylePerformanceArcLiveGuiImplementationBridgeReport,
) -> tuple[StylePerformanceArcLiveGuiDesktopBlueprintWidget, ...]:
    mounts = bridge.component_mounts
    region_by_mount = {
        spec.component_key: spec.region_key for spec in LIVE_GUI_DESKTOP_MOUNT_REGION_SPECS
    }
    return tuple(
        _widget(
            widget_key=f"widget-{mount.component_key}",
            order=mount.order,
            region_key=region_by_mount.get(
                mount.component_key,
                f"region-{mount.region_key.replace('_', '-')}",
            ),
            widget_type=mount.component_type,
            source_packet_key=mount.source_packet_key,
            source_json_key=mount.source_packet_key.replace("-", "_"),
            test_id=mount.test_id,
            operator_action=mount.operator_action,
        )
        for mount in mounts
    )


def _binding(
    *,
    binding_key: str,
    order: int,
    source_packet_key: str,
    source_json_path: str,
    target_widget_key: str,
    target_prop: str,
    fallback_value: str,
) -> StylePerformanceArcLiveGuiDesktopBlueprintBinding:
    return StylePerformanceArcLiveGuiDesktopBlueprintBinding(
        binding_key=binding_key,
        order=order,
        source_packet_key=source_packet_key,
        source_json_path=source_json_path,
        target_widget_key=target_widget_key,
        target_prop=target_prop,
        fallback_value=fallback_value,
        passive=True,
    )


def _bindings(
    widgets: tuple[StylePerformanceArcLiveGuiDesktopBlueprintWidget, ...],
) -> tuple[StylePerformanceArcLiveGuiDesktopBlueprintBinding, ...]:
    return tuple(
        _binding(
            binding_key=f"binding-{widget.widget_key}",
            order=widget.order,
            source_packet_key=widget.source_packet_key,
            source_json_path=f"$.live_gui_implementation_bridge.view_model_packets[{widget.order - 1}]",
            target_widget_key=widget.widget_key,
            target_prop="viewModel",
            fallback_value="disabled",
        )
        for widget in widgets
    )


def _sections(
    bridge: StylePerformanceArcLiveGuiImplementationBridgeReport,
) -> tuple[StylePerformanceArcLiveGuiDesktopBlueprintSection, ...]:
    return tuple(
        StylePerformanceArcLiveGuiDesktopBlueprintSection(
            section_key=f"section-{packet.packet_key}",
            order=packet.order,
            title=packet.component_hint.title(),
            source_packet_key=packet.packet_key,
            source_json_key=packet.json_key,
            objective=f"Define the future GUI section for {packet.component_hint}.",
            passive=packet.passive,
        )
        for packet in bridge.view_model_packets
    )


def _task_title(component_key: str) -> str:
    return component_key.replace("-", " ").title()


def _blueprint_tasks(
    sections: tuple[StylePerformanceArcLiveGuiDesktopBlueprintSection, ...],
    *,
    blueprint_label: str,
) -> tuple[StylePerformanceArcLiveGuiDesktopBlueprintTask, ...]:
    section_keys = {section.source_packet_key for section in sections}
    component_rows = (
        (
            "current-cue-panel",
            "primary",
            "widget-current-cue-panel",
            "screen-contract",
            "bind current cue, primary action, and alert rows",
        ),
        (
            "machine-panels",
            "machine-grid",
            "widget-machine-panels",
            "sidecar-session",
            "bind Rytm/A4 machine status panels from sidecar rows",
        ),
        (
            "analyzer-overlay",
            "analyzer",
            "widget-analyzer-overlay",
            "analyzer-frame",
            "bind analyzer meters and warning thresholds",
        ),
        (
            "capture-review-panel",
            "capture",
            "widget-capture-review-panel",
            "sidecar-session",
            "bind selected take and go/repeat/hold decisions",
        ),
        (
            "controller-actions",
            "controls",
            "widget-controller-actions",
            "controller-state",
            "bind disabled controls and safe action copy",
        ),
        (
            "test-harness-panel",
            "validation",
            "widget-test-harness-panel",
            "test-harness-readiness",
            "bind readiness gates, checks, and rehearsal steps",
        ),
    )
    tasks: list[StylePerformanceArcLiveGuiDesktopBlueprintTask] = []
    for order, (component_key, region_key, widget_key, source_packet_key, action) in enumerate(
        component_rows,
        start=1,
    ):
        if source_packet_key not in section_keys:
            continue
        tasks.append(
            StylePerformanceArcLiveGuiDesktopBlueprintTask(
                task_key=f"task-{component_key}",
                order=order,
                region_key=f"region-{region_key}",
                widget_key=widget_key,
                source_component_key=component_key,
                title=f"{_task_title(component_key)} for {blueprint_label}",
                enabled=False,
                blocked_reason="future GUI implementation only; no renderer or bundler is launched",
                operator_action=action,
                passive=True,
            )
        )
    return tuple(tasks)


def _fixture_hints(
    bridge: StylePerformanceArcLiveGuiImplementationBridgeReport,
) -> tuple[StylePerformanceArcLiveGuiDesktopBlueprintFixtureHint, ...]:
    return tuple(
        StylePerformanceArcLiveGuiDesktopBlueprintFixtureHint(
            fixture_key=f"file-{bundle.bundle_key}",
            order=bundle.order,
            source_fixture_key=bundle.bundle_key,
            source_packet_key=bundle.source_packet_key,
            suggested_path=f"tests/fixtures/live_gui/{bundle.bundle_key}.json",
            purpose=f"Future fixture for {bundle.target_scope}.",
            passive=bundle.passive,
        )
        for bundle in bridge.fixture_bundles
    )


def _replay_status(replay_commands: tuple[str, ...]) -> str:
    if replay_commands and replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-desktop-blueprint-report"
    ):
        return "ready"
    return "review-needed"


def _check(
    *,
    check_key: str,
    label: str,
    status: str,
    source_id: str,
    message: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiDesktopBlueprintAcceptanceCheck:
    return StylePerformanceArcLiveGuiDesktopBlueprintAcceptanceCheck(
        check_key=check_key,
        label=label,
        status=status,
        severity=status_severity(status),
        source_id=source_id,
        message=message,
        operator_action=operator_action,
        passive=True,
    )


def _acceptance_checks(
    bridge: StylePerformanceArcLiveGuiImplementationBridgeReport,
    *,
    sections: tuple[StylePerformanceArcLiveGuiDesktopBlueprintSection, ...],
    tasks: tuple[StylePerformanceArcLiveGuiDesktopBlueprintTask, ...],
    fixtures: tuple[StylePerformanceArcLiveGuiDesktopBlueprintFixtureHint, ...],
    replay_commands: tuple[str, ...],
) -> tuple[StylePerformanceArcLiveGuiDesktopBlueprintAcceptanceCheck, ...]:
    bridge_status = bridge.bridge_status
    return (
        _check(
            check_key="accept-bridge-status",
            label="Implementation bridge status",
            status=bridge_status,
            source_id=bridge.bridge_id,
            message=f"Upstream implementation bridge is {bridge_status}.",
            operator_action="hold desktop GUI implementation if bridge is blocked",
        ),
        _check(
            check_key="accept-readiness-status",
            label="Test-harness readiness status",
            status=bridge.test_harness_readiness.readiness_status,
            source_id=bridge.readiness_id,
            message=("Readiness packet remains the source of truth for GUI promotion."),
            operator_action="re-run readiness before enabling a desktop shell",
        ),
        _check(
            check_key="accept-view-model-coverage",
            label="View-model packet coverage",
            status=_coverage_status(len(bridge.view_model_packets)),
            source_id=bridge.bridge_id,
            message=f"{len(bridge.view_model_packets)} bridge packets are available.",
            operator_action="bind each packet to one future desktop blueprint section",
        ),
        _check(
            check_key="accept-component-mount-coverage",
            label="Component mount coverage",
            status=_coverage_status(len(bridge.component_mounts)),
            source_id=bridge.bridge_id,
            message=f"{len(bridge.component_mounts)} bridge component mounts are available.",
            operator_action="keep component mounts disabled until the GUI runner exists",
        ),
        _check(
            check_key="accept-fixture-bundle-coverage",
            label="Fixture bundle coverage",
            status=_coverage_status(len(bridge.fixture_bundles)),
            source_id=bridge.bridge_id,
            message=f"{len(bridge.fixture_bundles)} bridge fixture bundles are available.",
            operator_action="treat fixture paths as hints only; do not write files",
        ),
        _check(
            check_key="accept-section-coverage",
            label="Blueprint section coverage",
            status=_coverage_status(len(sections)),
            source_id=bridge.bridge_id,
            message=f"{len(sections)} blueprint sections are available.",
            operator_action="create desktop sections only after coverage is present",
        ),
        _check(
            check_key="accept-task-coverage",
            label="Implementation task coverage",
            status=_coverage_status(len(tasks)),
            source_id=bridge.bridge_id,
            message=f"{len(tasks)} desktop implementation tasks are available.",
            operator_action="keep tasks advisory and disabled",
        ),
        _check(
            check_key="accept-fixture-file-coverage",
            label="Fixture file hint coverage",
            status=_coverage_status(len(fixtures)),
            source_id=bridge.bridge_id,
            message=f"{len(fixtures)} fixture file hints are available.",
            operator_action="do not write fixture files in the passive report",
        ),
        _check(
            check_key="accept-replay-command",
            label="Desktop blueprint replay command",
            status=_replay_status(replay_commands),
            source_id=bridge.bridge_id,
            message=(
                "Desktop blueprint replay command is available."
                if replay_commands
                else "Desktop blueprint replay command is missing."
            ),
            operator_action="review command wiring before opening a GUI implementation PR",
        ),
        _check(
            check_key="accept-passive-boundary",
            label="Passive boundary",
            status="ready",
            source_id=bridge.bridge_id,
            message="Desktop blueprint emits metadata only.",
            operator_action="do not launch GUI, renderer, bundler, audio analysis, or MIDI hardware",
        ),
    )


def _blueprint_status(
    bridge: StylePerformanceArcLiveGuiImplementationBridgeReport,
    checks: tuple[StylePerformanceArcLiveGuiDesktopBlueprintAcceptanceCheck, ...],
) -> str:
    if bridge.bridge_status == "blocked":
        return "blocked"
    if any(check.status == "blocked" for check in checks):
        return "blocked"
    if bridge.bridge_status == "review-needed":
        return "review-needed"
    if any(check.status == "review-needed" for check in checks):
        return "review-needed"
    return "ready"


def _blocked_actions(blueprint_status: str) -> tuple[str, ...]:
    actions: list[str] = [
        "no GUI launch",
        "no GUI renderer start",
        "no renderer execution",
        "no GUI event dispatch",
        "no GUI controller dispatch",
        "no GUI state-store mutation",
        "no GUI test runner execution",
        "no bundler or dev-server launch",
        "no command execution",
        "no file writing",
        "no fixture file writing",
        "no audio recording",
        "no audio streaming",
        "no audio read/compare execution",
        "no real MIDI rendering",
        "no MIDI sending",
        "no port opening",
        "no hardware mutation",
    ]
    if blueprint_status != "ready":
        actions.insert(0, "hold GUI desktop blueprint until implementation bridge is clear")
    return tuple(actions)


def _replace_replay_command(
    command: str,
    *,
    blueprint_label: str,
    desktop_shell: str,
) -> str | None:
    return replace_replay_command(
        command,
        source_command="style-performance-arc-live-gui-implementation-bridge-report",
        target_command="style-performance-arc-live-gui-desktop-blueprint-report",
        extra_options=(
            ("--desktop-shell", desktop_shell),
            ("--blueprint-label", blueprint_label),
        ),
    )


def _replay_commands(
    bridge: StylePerformanceArcLiveGuiImplementationBridgeReport,
    *,
    blueprint_label: str,
    desktop_shell: str,
) -> tuple[str, ...]:
    if not bridge.replay_commands:
        return ()
    blueprint_command = _replace_replay_command(
        bridge.replay_commands[0],
        blueprint_label=blueprint_label,
        desktop_shell=desktop_shell,
    )
    if blueprint_command is None:
        return bridge.replay_commands
    return (blueprint_command, *bridge.replay_commands)


def build_style_performance_arc_live_gui_desktop_blueprint_from_bridge(
    bridge: StylePerformanceArcLiveGuiImplementationBridgeReport,
    *,
    blueprint_label: str = _DEFAULT_BLUEPRINT_LABEL,
    desktop_shell: str = _DEFAULT_DESKTOP_SHELL,
) -> StylePerformanceArcLiveGuiDesktopBlueprintReport:
    """Build one passive desktop blueprint from implementation bridge metadata."""

    normalized_label = _normalize_nonblank(blueprint_label, field="blueprint_label")
    normalized_shell = _normalize_desktop_shell(desktop_shell)
    density = _DEFAULT_DENSITY
    layout_key = _DEFAULT_LAYOUT_KEY
    viewports = _viewports(density=density, layout_key=layout_key)
    regions = _regions()
    widgets = _widgets(bridge)
    bindings = _bindings(widgets)
    sections = _sections(bridge)
    tasks = _blueprint_tasks(sections, blueprint_label=normalized_label)
    fixtures = _fixture_hints(bridge)
    replay_commands = _replay_commands(
        bridge,
        blueprint_label=normalized_label,
        desktop_shell=normalized_shell,
    )
    checks = _acceptance_checks(
        bridge,
        sections=sections,
        tasks=tasks,
        fixtures=fixtures,
        replay_commands=replay_commands,
    )
    blueprint_status = _blueprint_status(bridge, checks)
    return StylePerformanceArcLiveGuiDesktopBlueprintReport(
        implementation_bridge=bridge,
        blueprint_version=DESKTOP_BLUEPRINT_VERSION,
        blueprint_id=_blueprint_id(
            bridge,
            blueprint_label=normalized_label,
            blueprint_status=blueprint_status,
            desktop_shell=normalized_shell,
        ),
        blueprint_label=normalized_label,
        blueprint_status=blueprint_status,
        desktop_shell=normalized_shell,
        section_summary=f"{len(sections)} blueprint sections ready for future GUI implementation",
        task_summary=f"{len(tasks)} implementation tasks held disabled",
        fixture_summary=f"{len(fixtures)} fixture file hints held read-only",
        viewport_summary=f"{len(viewports)} viewport targets described",
        binding_summary=f"{len(bindings)} widget bindings described",
        viewports=viewports,
        regions=regions,
        widgets=widgets,
        bindings=bindings,
        sections=sections,
        implementation_tasks=tasks,
        fixture_file_hints=fixtures,
        acceptance_checks=checks,
        blocked_actions=_blocked_actions(blueprint_status),
        replay_commands=replay_commands,
    )


def build_style_performance_arc_live_gui_desktop_blueprint_report(
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
    lookahead_count: int = 2,
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
    validation_label: str = "Live GUI playback validation matrix",
    harness_label: str = "Live GUI test-harness contract",
    readiness_label: str = "Live GUI test-harness readiness",
    bridge_label: str = "Live GUI implementation bridge",
    blueprint_label: str = _DEFAULT_BLUEPRINT_LABEL,
    desktop_shell: str = _DEFAULT_DESKTOP_SHELL,
) -> StylePerformanceArcLiveGuiDesktopBlueprintReport:
    """Build a passive desktop blueprint from normal report inputs."""

    bridge = build_style_performance_arc_live_gui_implementation_bridge_report(
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
        validation_label=validation_label,
        harness_label=harness_label,
        readiness_label=readiness_label,
        bridge_label=bridge_label,
    )
    return build_style_performance_arc_live_gui_desktop_blueprint_from_bridge(
        bridge,
        blueprint_label=blueprint_label,
        desktop_shell=desktop_shell,
    )


def _viewport_json(
    viewport: StylePerformanceArcLiveGuiDesktopBlueprintViewport,
) -> dict[str, object]:
    return {
        "viewport_key": viewport.viewport_key,
        "width_px": viewport.width_px,
        "height_px": viewport.height_px,
        "density": viewport.density,
        "layout_key": viewport.layout_key,
        "passive": viewport.passive,
    }


def _region_json(region: StylePerformanceArcLiveGuiDesktopBlueprintRegion) -> dict[str, object]:
    return {
        "region_key": region.region_key,
        "order": region.order,
        "label": region.label,
        "role": region.role,
        "source_component_key": region.source_component_key,
        "grid_area": region.grid_area,
        "min_width_px": region.min_width_px,
        "min_height_px": region.min_height_px,
        "enabled": region.enabled,
        "passive": region.passive,
    }


def _widget_json(widget: StylePerformanceArcLiveGuiDesktopBlueprintWidget) -> dict[str, object]:
    return {
        "widget_key": widget.widget_key,
        "order": widget.order,
        "region_key": widget.region_key,
        "widget_type": widget.widget_type,
        "source_packet_key": widget.source_packet_key,
        "source_json_key": widget.source_json_key,
        "test_id": widget.test_id,
        "state": widget.state,
        "bind_enabled": widget.bind_enabled,
        "operator_action": widget.operator_action,
        "passive": widget.passive,
    }


def _binding_json(
    binding: StylePerformanceArcLiveGuiDesktopBlueprintBinding,
) -> dict[str, object]:
    return {
        "binding_key": binding.binding_key,
        "order": binding.order,
        "source_packet_key": binding.source_packet_key,
        "source_json_path": binding.source_json_path,
        "target_widget_key": binding.target_widget_key,
        "target_prop": binding.target_prop,
        "fallback_value": binding.fallback_value,
        "passive": binding.passive,
    }


def _section_json(
    section: StylePerformanceArcLiveGuiDesktopBlueprintSection,
) -> dict[str, object]:
    return {
        "section_key": section.section_key,
        "order": section.order,
        "title": section.title,
        "source_packet_key": section.source_packet_key,
        "source_json_key": section.source_json_key,
        "objective": section.objective,
        "passive": section.passive,
    }


def _task_json(task: StylePerformanceArcLiveGuiDesktopBlueprintTask) -> dict[str, object]:
    return {
        "task_key": task.task_key,
        "order": task.order,
        "region_key": task.region_key,
        "widget_key": task.widget_key,
        "source_component_key": task.source_component_key,
        "title": task.title,
        "enabled": task.enabled,
        "blocked_reason": task.blocked_reason,
        "operator_action": task.operator_action,
        "passive": task.passive,
    }


def _fixture_json(
    fixture: StylePerformanceArcLiveGuiDesktopBlueprintFixtureHint,
) -> dict[str, object]:
    return {
        "fixture_key": fixture.fixture_key,
        "order": fixture.order,
        "source_fixture_key": fixture.source_fixture_key,
        "source_packet_key": fixture.source_packet_key,
        "suggested_path": fixture.suggested_path,
        "purpose": fixture.purpose,
        "passive": fixture.passive,
    }


def _check_json(
    check: StylePerformanceArcLiveGuiDesktopBlueprintAcceptanceCheck,
) -> dict[str, object]:
    return {
        "check_key": check.check_key,
        "label": check.label,
        "status": check.status,
        "severity": check.severity,
        "source_id": check.source_id,
        "message": check.message,
        "operator_action": check.operator_action,
        "passive": check.passive,
    }


def to_style_performance_arc_live_gui_desktop_blueprint_json(
    report: StylePerformanceArcLiveGuiDesktopBlueprintReport,
) -> dict[str, object]:
    """Return deterministic JSON for a passive desktop blueprint."""

    bridge_json = to_style_performance_arc_live_gui_implementation_bridge_json(
        report.implementation_bridge
    )
    return {
        "live_gui_desktop_blueprint": {
            "blueprint_version": report.blueprint_version,
            "blueprint_id": report.blueprint_id,
            "blueprint_label": report.blueprint_label,
            "blueprint_status": report.blueprint_status,
            "desktop_shell": report.desktop_shell,
            "bridge_id": report.bridge_id,
            "readiness_id": report.readiness_id,
            "contract_id": report.contract_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "section_summary": report.section_summary,
            "task_summary": report.task_summary,
            "fixture_summary": report.fixture_summary,
            "viewport_summary": report.viewport_summary,
            "binding_summary": report.binding_summary,
            "viewports": [_viewport_json(viewport) for viewport in report.viewports],
            "regions": [_region_json(region) for region in report.regions],
            "widgets": [_widget_json(widget) for widget in report.widgets],
            "bindings": [_binding_json(binding) for binding in report.bindings],
            "sections": [_section_json(section) for section in report.sections],
            "implementation_tasks": [_task_json(task) for task in report.implementation_tasks],
            "fixture_file_hints": [_fixture_json(fixture) for fixture in report.fixture_file_hints],
            "acceptance_checks": [_check_json(check) for check in report.acceptance_checks],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **bridge_json,
        "safety": list(SAFETY_LINES),
    }


def _viewport_lines(viewport: StylePerformanceArcLiveGuiDesktopBlueprintViewport) -> list[str]:
    return [
        f"- {viewport.viewport_key}: {viewport.width_px}x{viewport.height_px}",
        f"  Density: {viewport.density}",
        f"  Layout: {viewport.layout_key}",
        f"  Passive: {viewport.passive}",
    ]


def _region_lines(region: StylePerformanceArcLiveGuiDesktopBlueprintRegion) -> list[str]:
    return [
        f"- {region.order}. {region.region_key}: {region.label}",
        f"  Role: {region.role}",
        f"  Source component: {region.source_component_key}",
        f"  Grid area: {region.grid_area}",
        f"  Min size: {region.min_width_px}x{region.min_height_px}",
        f"  Enabled: {region.enabled}",
        f"  Passive: {region.passive}",
    ]


def _widget_lines(widget: StylePerformanceArcLiveGuiDesktopBlueprintWidget) -> list[str]:
    return [
        f"- {widget.order}. {widget.widget_key} ({widget.widget_type})",
        f"  Region: {widget.region_key}",
        f"  Source packet: {widget.source_packet_key}",
        f"  JSON key: {widget.source_json_key}",
        f"  Test id: {widget.test_id}",
        f"  State: {widget.state}",
        f"  Bind enabled: {widget.bind_enabled}",
        f"  Operator action: {widget.operator_action}",
        f"  Passive: {widget.passive}",
    ]


def _binding_lines(
    binding: StylePerformanceArcLiveGuiDesktopBlueprintBinding,
) -> list[str]:
    return [
        f"- {binding.order}. {binding.binding_key}",
        f"  Source packet: {binding.source_packet_key}",
        f"  Source JSON path: {binding.source_json_path}",
        f"  Target widget: {binding.target_widget_key}",
        f"  Target prop: {binding.target_prop}",
        f"  Fallback value: {binding.fallback_value}",
        f"  Passive: {binding.passive}",
    ]


def _section_lines(
    section: StylePerformanceArcLiveGuiDesktopBlueprintSection,
) -> list[str]:
    return [
        f"- {section.order}. {section.section_key}: {section.title}",
        f"  Source packet: {section.source_packet_key}",
        f"  JSON key: {section.source_json_key}",
        f"  Objective: {section.objective}",
        f"  Passive: {section.passive}",
    ]


def _task_lines(task: StylePerformanceArcLiveGuiDesktopBlueprintTask) -> list[str]:
    return [
        f"- {task.order}. {task.task_key}: {task.title}",
        f"  Region: {task.region_key}",
        f"  Widget: {task.widget_key}",
        f"  Source component: {task.source_component_key}",
        f"  Enabled: {task.enabled}",
        f"  Blocked reason: {task.blocked_reason}",
        f"  Operator action: {task.operator_action}",
        f"  Passive: {task.passive}",
    ]


def _fixture_lines(fixture: StylePerformanceArcLiveGuiDesktopBlueprintFixtureHint) -> list[str]:
    return [
        f"- {fixture.order}. {fixture.fixture_key}",
        f"  Source fixture: {fixture.source_fixture_key}",
        f"  Source packet: {fixture.source_packet_key}",
        f"  Suggested path: {fixture.suggested_path}",
        f"  Purpose: {fixture.purpose}",
        f"  Passive: {fixture.passive}",
    ]


def _check_lines(
    check: StylePerformanceArcLiveGuiDesktopBlueprintAcceptanceCheck,
) -> list[str]:
    return [
        f"- {check.check_key}: {check.label}",
        f"  Status: {check.status}",
        f"  Severity: {check.severity}",
        f"  Source id: {check.source_id}",
        f"  Message: {check.message}",
        f"  Operator action: {check.operator_action}",
        f"  Passive: {check.passive}",
    ]


def format_style_performance_arc_live_gui_desktop_blueprint_report(
    report: StylePerformanceArcLiveGuiDesktopBlueprintReport,
) -> list[str]:
    """Format a passive desktop blueprint report."""

    lines = [
        "Live GUI desktop blueprint summary:",
        f"- Blueprint id: {report.blueprint_id}",
        f"- Blueprint label: {report.blueprint_label}",
        f"- Blueprint status: {report.blueprint_status}",
        f"- Desktop shell: {report.desktop_shell}",
        f"- Bridge id: {report.bridge_id}",
        f"- Readiness id: {report.readiness_id}",
        f"- Contract id: {report.contract_id}",
        f"- Selected arc: {report.selected_arc_name} ({report.selected_arc_key})",
        f"- Scope: {report.scope}",
        f"- Section summary: {report.section_summary}",
        f"- Task summary: {report.task_summary}",
        f"- Fixture summary: {report.fixture_summary}",
        f"- Viewport summary: {report.viewport_summary}",
        f"- Binding summary: {report.binding_summary}",
        "Desktop shell:",
        f"- {report.desktop_shell}",
        "Blueprint viewports:",
    ]
    for viewport in report.viewports:
        lines.extend(_viewport_lines(viewport))
    lines.append("Blueprint regions:")
    for region in report.regions:
        lines.extend(_region_lines(region))
    lines.append("Blueprint widgets:")
    for widget in report.widgets:
        lines.extend(_widget_lines(widget))
    lines.append("Blueprint bindings:")
    for binding in report.bindings:
        lines.extend(_binding_lines(binding))
    lines.append("Blueprint sections:")
    for section in report.sections:
        lines.extend(_section_lines(section))
    lines.append("Implementation tasks:")
    for task in report.implementation_tasks:
        lines.extend(_task_lines(task))
    lines.append("Fixture file hints:")
    for fixture in report.fixture_file_hints:
        lines.extend(_fixture_lines(fixture))
    lines.append("Acceptance checks:")
    for check in report.acceptance_checks:
        lines.extend(_check_lines(check))
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


def parse_style_performance_arc_live_gui_desktop_blueprint_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Parse desktop blueprint CLI args for passive report composition."""

    blueprint_label = _DEFAULT_BLUEPRINT_LABEL
    desktop_shell = _DEFAULT_DESKTOP_SHELL
    bridge_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--blueprint-label":
            blueprint_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="blueprint_label",
            )
        elif option == "--desktop-shell":
            desktop_shell = _normalize_desktop_shell(_pop_option_value(remaining))
        else:
            bridge_args.append(option)
            if option != "--json":
                bridge_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_implementation_bridge_cli_args(bridge_args)
    parsed["blueprint_label"] = blueprint_label
    parsed["desktop_shell"] = desktop_shell
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
    harness_label: str,
    readiness_label: str,
    bridge_label: str,
    blueprint_label: str,
    json_output: bool,
    desktop_shell: str = _DEFAULT_DESKTOP_SHELL,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_desktop_blueprint_report(
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
            harness_label=harness_label,
            readiness_label=readiness_label,
            bridge_label=bridge_label,
            blueprint_label=blueprint_label,
            desktop_shell=desktop_shell,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_desktop_blueprint_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_desktop_blueprint_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_BLUEPRINT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-desktop-blueprint-report",
    summary="Compose passive GUI implementation metadata into a future desktop blueprint.",
    args_parser=parse_style_performance_arc_live_gui_desktop_blueprint_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_BLUEPRINT_CLI_COMMAND)

__all__ = [
    "DESKTOP_BLUEPRINT_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_BLUEPRINT_CLI_COMMAND",
    "StylePerformanceArcLiveGuiDesktopBlueprintAcceptanceCheck",
    "StylePerformanceArcLiveGuiDesktopBlueprintBinding",
    "StylePerformanceArcLiveGuiDesktopBlueprintFixtureHint",
    "StylePerformanceArcLiveGuiDesktopBlueprintRegion",
    "StylePerformanceArcLiveGuiDesktopBlueprintReport",
    "StylePerformanceArcLiveGuiDesktopBlueprintSection",
    "StylePerformanceArcLiveGuiDesktopBlueprintTask",
    "StylePerformanceArcLiveGuiDesktopBlueprintViewport",
    "StylePerformanceArcLiveGuiDesktopBlueprintWidget",
    "build_style_performance_arc_live_gui_desktop_blueprint_from_bridge",
    "build_style_performance_arc_live_gui_desktop_blueprint_report",
    "format_style_performance_arc_live_gui_desktop_blueprint_report",
    "parse_style_performance_arc_live_gui_desktop_blueprint_cli_args",
    "to_style_performance_arc_live_gui_desktop_blueprint_json",
]
