"""Passive live GUI desktop app plan for future operator surfaces."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.live_gui_contracts import LIVE_GUI_DESKTOP_APP_STYLE_TOKEN_SPECS
from ..style_analysis.feature_report import FeatureReport
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value, replace_replay_command, status_severity
from .live_gui_desktop_blueprint import (
    StylePerformanceArcLiveGuiDesktopBlueprintRegion,
    StylePerformanceArcLiveGuiDesktopBlueprintReport,
    StylePerformanceArcLiveGuiDesktopBlueprintWidget,
    build_style_performance_arc_live_gui_desktop_blueprint_report,
    parse_style_performance_arc_live_gui_desktop_blueprint_cli_args,
    to_style_performance_arc_live_gui_desktop_blueprint_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live GUI desktop app plan"
SOURCE_MODULE: Final[str] = "reports.live_gui_desktop_app_plan"
DESKTOP_APP_PLAN_VERSION: Final[str] = "live-gui-desktop-app-plan-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI desktop app-plan metadata only",
    "consumes live GUI desktop blueprint metadata only",
    "app shell metadata only",
    "routes are declarative metadata only",
    "component file hints are advisory metadata only",
    "state slices are declarative metadata only",
    "style tokens are declarative metadata only",
    "acceptance checks are advisory metadata only",
    "future desktop GUI only",
    "future audio analyzer comparison only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
    "no app launch",
    "no Electron launch",
    "no Tauri launch",
    "no webview launch",
    "no GUI renderer start",
    "no renderer execution",
    "no GUI event dispatch",
    "no GUI controller dispatch",
    "no GUI state-store mutation",
    "no GUI test runner execution",
    "no bundler launch",
    "no dev-server launch",
    "no command execution",
    "no build execution",
    "no file writing",
    "no fixture file writing",
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
_DEFAULT_APP_PLAN_LABEL: Final[str] = "Live GUI desktop app plan"
_DEFAULT_FRAMEWORK_TARGET: Final[str] = "desktop-python"
_FRAMEWORK_TARGETS: Final[tuple[str, ...]] = (
    "desktop-python",
    "web-desktop",
    "test-harness",
)
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-desktop-app-plan-report usage: "
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
    "[--desktop-shell operator-dashboard|desktop-sidecar|test-harness] "
    "[--app-plan-label <text>] [--framework-target desktop-python|web-desktop|test-harness] "
    "[--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopAppPlanRoute:
    """One disabled future application route."""

    route_key: str
    order: int
    label: str
    desktop_shell: str
    viewport_key: str
    region_key: str
    grid_area: str
    component_key: str
    enabled: bool
    blocked_reason: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopAppPlanComponentFile:
    """One future component file hint that does not write a file."""

    component_key: str
    order: int
    route_key: str
    widget_key: str
    component_type: str
    suggested_path: str
    source_packet_key: str
    source_json_key: str
    test_id: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopAppPlanStateSlice:
    """One future GUI state-slice binding."""

    slice_key: str
    order: int
    component_key: str
    source_packet_key: str
    source_json_path: str
    reducer_hint: str
    initial_state: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopAppPlanStyleToken:
    """One future desktop style token."""

    token_key: str
    label: str
    token_type: str
    value_hint: str
    framework_target: str
    status: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopAppPlanAcceptanceCheck:
    """One future desktop app-plan acceptance check."""

    check_key: str
    label: str
    status: str
    severity: str
    source_id: str
    message: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopAppPlanReport:
    """Passive desktop app plan composed from desktop blueprint metadata."""

    desktop_blueprint: StylePerformanceArcLiveGuiDesktopBlueprintReport
    app_plan_version: str
    app_plan_id: str
    app_plan_label: str
    app_plan_status: str
    framework_target: str
    route_summary: str
    component_summary: str
    state_summary: str
    style_summary: str
    routes: tuple[StylePerformanceArcLiveGuiDesktopAppPlanRoute, ...]
    component_files: tuple[StylePerformanceArcLiveGuiDesktopAppPlanComponentFile, ...]
    state_slices: tuple[StylePerformanceArcLiveGuiDesktopAppPlanStateSlice, ...]
    style_tokens: tuple[StylePerformanceArcLiveGuiDesktopAppPlanStyleToken, ...]
    acceptance_checks: tuple[StylePerformanceArcLiveGuiDesktopAppPlanAcceptanceCheck, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def blueprint_id(self) -> str:
        """Return upstream desktop blueprint id."""

        return self.desktop_blueprint.blueprint_id

    @property
    def bridge_id(self) -> str:
        """Return upstream implementation bridge id."""

        return self.desktop_blueprint.bridge_id

    @property
    def readiness_id(self) -> str:
        """Return upstream readiness id."""

        return self.desktop_blueprint.readiness_id

    @property
    def contract_id(self) -> str:
        """Return upstream contract id."""

        return self.desktop_blueprint.contract_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected performance arc key."""

        return self.desktop_blueprint.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected performance arc name."""

        return self.desktop_blueprint.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.desktop_blueprint.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _normalize_framework_target(value: str) -> str:
    normalized = _normalize_nonblank(value, field="framework_target")
    if normalized not in _FRAMEWORK_TARGETS:
        raise ValueError("framework_target must be desktop-python, web-desktop, or test-harness")
    return normalized


def _coverage_status(count: int) -> str:
    if count <= 0:
        return "blocked"
    return "ready"


def _component_key_from_widget(widget_key: str) -> str:
    if widget_key.startswith("widget-"):
        return widget_key.removeprefix("widget-")
    return widget_key


def _route_key_from_region(region_key: str) -> str:
    return region_key.removeprefix("region-")


def _app_plan_id(
    blueprint: StylePerformanceArcLiveGuiDesktopBlueprintReport,
    *,
    app_plan_label: str,
    app_plan_status: str,
    framework_target: str,
) -> str:
    payload = "|".join(
        (
            DESKTOP_APP_PLAN_VERSION,
            blueprint.blueprint_id,
            blueprint.bridge_id,
            blueprint.readiness_id,
            blueprint.selected_arc_key,
            blueprint.scope,
            framework_target,
            app_plan_label,
            app_plan_status,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _route(
    *,
    region: StylePerformanceArcLiveGuiDesktopBlueprintRegion,
    desktop_shell: str,
) -> StylePerformanceArcLiveGuiDesktopAppPlanRoute:
    route_base = _route_key_from_region(region.region_key)
    return StylePerformanceArcLiveGuiDesktopAppPlanRoute(
        route_key=f"route-{route_base}",
        order=region.order,
        label=region.label,
        desktop_shell=desktop_shell,
        viewport_key="desktop",
        region_key=region.region_key,
        grid_area=region.grid_area,
        component_key=region.source_component_key,
        enabled=False,
        blocked_reason="future desktop app route only; no app shell is launched",
        passive=True,
    )


def _routes(
    regions: Sequence[StylePerformanceArcLiveGuiDesktopBlueprintRegion],
) -> tuple[StylePerformanceArcLiveGuiDesktopAppPlanRoute, ...]:
    return tuple(_route(region=region, desktop_shell="operator-dashboard") for region in regions)


def _component_file(
    widget: StylePerformanceArcLiveGuiDesktopBlueprintWidget,
) -> StylePerformanceArcLiveGuiDesktopAppPlanComponentFile:
    component_key = _component_key_from_widget(widget.widget_key)
    route_key = f"route-{widget.region_key.removeprefix('region-')}"
    component_name = "".join(part.title() for part in component_key.split("-"))
    return StylePerformanceArcLiveGuiDesktopAppPlanComponentFile(
        component_key=component_key,
        order=widget.order,
        route_key=route_key,
        widget_key=widget.widget_key,
        component_type=widget.widget_type,
        suggested_path=f"future_gui/components/{component_name}.py",
        source_packet_key=widget.source_packet_key,
        source_json_key=widget.source_json_key,
        test_id=widget.test_id,
        passive=True,
    )


def _component_files(
    widgets: Sequence[StylePerformanceArcLiveGuiDesktopBlueprintWidget],
) -> tuple[StylePerformanceArcLiveGuiDesktopAppPlanComponentFile, ...]:
    return tuple(_component_file(widget) for widget in widgets)


def _state_slice(
    component: StylePerformanceArcLiveGuiDesktopAppPlanComponentFile,
) -> StylePerformanceArcLiveGuiDesktopAppPlanStateSlice:
    return StylePerformanceArcLiveGuiDesktopAppPlanStateSlice(
        slice_key=f"slice-{component.component_key}",
        order=component.order,
        component_key=component.component_key,
        source_packet_key=component.source_packet_key,
        source_json_path=f"$.live_gui_desktop_blueprint.widgets[{component.order - 1}]",
        reducer_hint=f"reduce-{component.component_key}",
        initial_state="disabled",
        passive=True,
    )


def _state_slices(
    component_files: Sequence[StylePerformanceArcLiveGuiDesktopAppPlanComponentFile],
) -> tuple[StylePerformanceArcLiveGuiDesktopAppPlanStateSlice, ...]:
    return tuple(_state_slice(component) for component in component_files)


def _style_tokens(
    *,
    framework_target: str,
) -> tuple[StylePerformanceArcLiveGuiDesktopAppPlanStyleToken, ...]:
    return tuple(
        StylePerformanceArcLiveGuiDesktopAppPlanStyleToken(
            token_key=spec.token_key,
            label=spec.label,
            token_type=spec.token_type,
            value_hint=spec.value_hint,
            framework_target=framework_target,
            status="ready",
            passive=True,
        )
        for spec in LIVE_GUI_DESKTOP_APP_STYLE_TOKEN_SPECS
    )


def _check(
    *,
    check_key: str,
    label: str,
    status: str,
    source_id: str,
    message: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiDesktopAppPlanAcceptanceCheck:
    return StylePerformanceArcLiveGuiDesktopAppPlanAcceptanceCheck(
        check_key=check_key,
        label=label,
        status=status,
        severity=status_severity(status),
        source_id=source_id,
        message=message,
        operator_action=operator_action,
        passive=True,
    )


def _blueprint_status_for_check(
    blueprint: StylePerformanceArcLiveGuiDesktopBlueprintReport,
) -> str:
    if blueprint.blueprint_status == "blocked":
        return "blocked"
    if blueprint.blueprint_status == "review-needed":
        return "review-needed"
    return "ready"


def _replay_status(replay_commands: tuple[str, ...]) -> str:
    if not replay_commands:
        return "review-needed"
    if not replay_commands[0].startswith(
        "python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-app-plan-report"
    ):
        return "review-needed"
    return "ready"


def _acceptance_checks(
    blueprint: StylePerformanceArcLiveGuiDesktopBlueprintReport,
    *,
    routes: tuple[StylePerformanceArcLiveGuiDesktopAppPlanRoute, ...],
    component_files: tuple[StylePerformanceArcLiveGuiDesktopAppPlanComponentFile, ...],
    state_slices: tuple[StylePerformanceArcLiveGuiDesktopAppPlanStateSlice, ...],
    style_tokens: tuple[StylePerformanceArcLiveGuiDesktopAppPlanStyleToken, ...],
    replay_commands: tuple[str, ...],
) -> tuple[StylePerformanceArcLiveGuiDesktopAppPlanAcceptanceCheck, ...]:
    return (
        _check(
            check_key="accept-blueprint-status",
            label="Desktop blueprint status",
            status=_blueprint_status_for_check(blueprint),
            source_id=blueprint.blueprint_id,
            message=f"Desktop blueprint status is {blueprint.blueprint_status}.",
            operator_action="resolve desktop blueprint blockers before implementing the app plan",
        ),
        _check(
            check_key="accept-route-coverage",
            label="Route coverage",
            status=_coverage_status(len(routes)),
            source_id=blueprint.blueprint_id,
            message=f"{len(routes)} future desktop routes are available.",
            operator_action="keep route metadata disabled until a GUI implementation PR",
        ),
        _check(
            check_key="accept-component-file-coverage",
            label="Component file coverage",
            status=_coverage_status(len(component_files)),
            source_id=blueprint.blueprint_id,
            message=f"{len(component_files)} component file hints are available.",
            operator_action="do not write component files in the passive report",
        ),
        _check(
            check_key="accept-state-slice-coverage",
            label="State-slice coverage",
            status=_coverage_status(len(state_slices)),
            source_id=blueprint.blueprint_id,
            message=f"{len(state_slices)} state slices are available.",
            operator_action="keep state slices declarative until a GUI implementation PR",
        ),
        _check(
            check_key="accept-style-token-coverage",
            label="Style token coverage",
            status=_coverage_status(len(style_tokens)),
            source_id=blueprint.blueprint_id,
            message=f"{len(style_tokens)} style tokens are available.",
            operator_action="treat style tokens as metadata only",
        ),
        _check(
            check_key="accept-replay-command",
            label="Desktop app-plan replay command",
            status=_replay_status(replay_commands),
            source_id=blueprint.blueprint_id,
            message=(
                "Desktop app-plan replay command is available."
                if replay_commands
                else "Desktop app-plan replay command is missing."
            ),
            operator_action="review command wiring before opening a GUI implementation PR",
        ),
        _check(
            check_key="accept-passive-boundary",
            label="Passive boundary",
            status="ready",
            source_id=blueprint.blueprint_id,
            message="Desktop app plan emits metadata only.",
            operator_action="do not launch GUI, dev server, audio analysis, or MIDI hardware",
        ),
    )


def _app_plan_status(
    blueprint: StylePerformanceArcLiveGuiDesktopBlueprintReport,
    checks: tuple[StylePerformanceArcLiveGuiDesktopAppPlanAcceptanceCheck, ...],
) -> str:
    if blueprint.blueprint_status == "blocked":
        return "blocked"
    if any(check.status == "blocked" for check in checks):
        return "blocked"
    if blueprint.blueprint_status == "review-needed":
        return "review-needed"
    if any(check.status == "review-needed" for check in checks):
        return "review-needed"
    return "ready"


def _blocked_actions(app_plan_status: str) -> tuple[str, ...]:
    actions: list[str] = [
        "no GUI launch",
        "no app launch",
        "no Electron launch",
        "no Tauri launch",
        "no webview launch",
        "no GUI renderer start",
        "no renderer execution",
        "no GUI event dispatch",
        "no GUI controller dispatch",
        "no GUI state-store mutation",
        "no GUI test runner execution",
        "no bundler launch",
        "no dev-server launch",
        "no command execution",
        "no build execution",
        "no file writing",
        "no fixture file writing",
        "no component file writing",
        "no audio recording",
        "no audio streaming",
        "no audio read/compare execution",
        "no real MIDI rendering",
        "no MIDI sending",
        "no port opening",
        "no hardware mutation",
    ]
    if app_plan_status != "ready":
        actions.insert(0, "hold desktop app plan until desktop blueprint is clear")
    return tuple(actions)


def _replace_replay_command(
    command: str,
    *,
    app_plan_label: str,
    framework_target: str,
) -> str | None:
    return replace_replay_command(
        command,
        source_command="style-performance-arc-live-gui-desktop-blueprint-report",
        target_command="style-performance-arc-live-gui-desktop-app-plan-report",
        extra_options=(
            ("--framework-target", framework_target),
            ("--app-plan-label", app_plan_label),
        ),
    )


def _replay_commands(
    blueprint: StylePerformanceArcLiveGuiDesktopBlueprintReport,
    *,
    app_plan_label: str,
    framework_target: str,
) -> tuple[str, ...]:
    if not blueprint.replay_commands:
        return ()
    app_plan_command = _replace_replay_command(
        blueprint.replay_commands[0],
        app_plan_label=app_plan_label,
        framework_target=framework_target,
    )
    if app_plan_command is None:
        return blueprint.replay_commands
    return (app_plan_command, *blueprint.replay_commands)


def build_style_performance_arc_live_gui_desktop_app_plan_from_blueprint(
    blueprint: StylePerformanceArcLiveGuiDesktopBlueprintReport,
    *,
    app_plan_label: str = _DEFAULT_APP_PLAN_LABEL,
    framework_target: str = _DEFAULT_FRAMEWORK_TARGET,
) -> StylePerformanceArcLiveGuiDesktopAppPlanReport:
    """Build one passive desktop app plan from desktop blueprint metadata."""

    normalized_label = _normalize_nonblank(app_plan_label, field="app_plan_label")
    normalized_framework = _normalize_framework_target(framework_target)
    routes = _routes(blueprint.regions)
    component_files = _component_files(blueprint.widgets)
    state_slices = _state_slices(component_files)
    style_tokens = _style_tokens(framework_target=normalized_framework)
    replay_commands = _replay_commands(
        blueprint,
        app_plan_label=normalized_label,
        framework_target=normalized_framework,
    )
    checks = _acceptance_checks(
        blueprint,
        routes=routes,
        component_files=component_files,
        state_slices=state_slices,
        style_tokens=style_tokens,
        replay_commands=replay_commands,
    )
    app_plan_status = _app_plan_status(blueprint, checks)
    return StylePerformanceArcLiveGuiDesktopAppPlanReport(
        desktop_blueprint=blueprint,
        app_plan_version=DESKTOP_APP_PLAN_VERSION,
        app_plan_id=_app_plan_id(
            blueprint,
            app_plan_label=normalized_label,
            app_plan_status=app_plan_status,
            framework_target=normalized_framework,
        ),
        app_plan_label=normalized_label,
        app_plan_status=app_plan_status,
        framework_target=normalized_framework,
        route_summary=f"{len(routes)} routes for future desktop app shell.",
        component_summary=f"{len(component_files)} component files for future GUI implementation.",
        state_summary=f"{len(state_slices)} state slices for future view-model wiring.",
        style_summary=f"{len(style_tokens)} style tokens for {normalized_framework}.",
        routes=routes,
        component_files=component_files,
        state_slices=state_slices,
        style_tokens=style_tokens,
        acceptance_checks=checks,
        blocked_actions=_blocked_actions(app_plan_status),
        replay_commands=replay_commands,
    )


def build_style_performance_arc_live_gui_desktop_app_plan_report(
    *,
    description: str | None = None,
    audio_path: Path | None = None,
    library_path: Path | None = None,
    capture_description: str | None = None,
    capture_audio_path: Path | None = None,
    capture_library_path: Path | None = None,
    feature_report: FeatureReport | None = None,
    capture_feature_report: FeatureReport | None = None,
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
    take_count: int = 1,
    slot_key: str = "capture-001",
    queue_label: str = "Live GUI capture queue",
    capture_prefix: str = "live-capture",
    sidecar_label: str = "Live performance sidecar",
    screen_label: str = "Live GUI screen contract",
    layout_key: str = "operator-default",
    viewport: str = "desktop",
    render_target: str = "desktop-sidecar",
    density: str = "standard",
    overlay_label: str = "Live GUI overlay",
    frame_label: str = "Live GUI frame",
    interaction_label: str = "Live GUI interaction script",
    reducer_label: str = "Live GUI action reducer",
    controller_label: str = "Live GUI controller state",
    playback_label: str = "Live GUI playback transcript",
    validation_label: str = "Live GUI playback validation matrix",
    harness_label: str = "Live GUI test-harness contract",
    readiness_label: str = "Live GUI test-harness readiness",
    bridge_label: str = "Live GUI implementation bridge",
    blueprint_label: str = "Live GUI desktop blueprint",
    desktop_shell: str = "operator-dashboard",
    app_plan_label: str = _DEFAULT_APP_PLAN_LABEL,
    framework_target: str = _DEFAULT_FRAMEWORK_TARGET,
) -> StylePerformanceArcLiveGuiDesktopAppPlanReport:
    """Build one passive desktop app-plan report from style/capture inputs."""

    blueprint = build_style_performance_arc_live_gui_desktop_blueprint_report(
        description=description,
        audio_path=audio_path,
        library_path=library_path,
        capture_description=capture_description,
        capture_audio_path=capture_audio_path,
        capture_library_path=capture_library_path,
        feature_report=feature_report,
        capture_feature_report=capture_feature_report,
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
    return build_style_performance_arc_live_gui_desktop_app_plan_from_blueprint(
        blueprint,
        app_plan_label=app_plan_label,
        framework_target=framework_target,
    )


def _route_json(route: StylePerformanceArcLiveGuiDesktopAppPlanRoute) -> dict[str, object]:
    return {
        "route_key": route.route_key,
        "order": route.order,
        "label": route.label,
        "desktop_shell": route.desktop_shell,
        "viewport_key": route.viewport_key,
        "region_key": route.region_key,
        "grid_area": route.grid_area,
        "component_key": route.component_key,
        "enabled": route.enabled,
        "blocked_reason": route.blocked_reason,
        "passive": route.passive,
    }


def _component_file_json(
    component: StylePerformanceArcLiveGuiDesktopAppPlanComponentFile,
) -> dict[str, object]:
    return {
        "component_key": component.component_key,
        "order": component.order,
        "route_key": component.route_key,
        "widget_key": component.widget_key,
        "component_type": component.component_type,
        "suggested_path": component.suggested_path,
        "source_packet_key": component.source_packet_key,
        "source_json_key": component.source_json_key,
        "test_id": component.test_id,
        "passive": component.passive,
    }


def _state_slice_json(
    state_slice: StylePerformanceArcLiveGuiDesktopAppPlanStateSlice,
) -> dict[str, object]:
    return {
        "slice_key": state_slice.slice_key,
        "order": state_slice.order,
        "component_key": state_slice.component_key,
        "source_packet_key": state_slice.source_packet_key,
        "source_json_path": state_slice.source_json_path,
        "reducer_hint": state_slice.reducer_hint,
        "initial_state": state_slice.initial_state,
        "passive": state_slice.passive,
    }


def _style_token_json(
    token: StylePerformanceArcLiveGuiDesktopAppPlanStyleToken,
) -> dict[str, object]:
    return {
        "token_key": token.token_key,
        "label": token.label,
        "token_type": token.token_type,
        "value_hint": token.value_hint,
        "framework_target": token.framework_target,
        "status": token.status,
        "passive": token.passive,
    }


def _check_json(
    check: StylePerformanceArcLiveGuiDesktopAppPlanAcceptanceCheck,
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


def to_style_performance_arc_live_gui_desktop_app_plan_json(
    report: StylePerformanceArcLiveGuiDesktopAppPlanReport,
) -> dict[str, object]:
    """Return deterministic JSON for a passive desktop app plan."""

    blueprint_json = to_style_performance_arc_live_gui_desktop_blueprint_json(
        report.desktop_blueprint
    )
    return {
        "live_gui_desktop_app_plan": {
            "app_plan_version": report.app_plan_version,
            "app_plan_id": report.app_plan_id,
            "app_plan_label": report.app_plan_label,
            "app_plan_status": report.app_plan_status,
            "framework_target": report.framework_target,
            "blueprint_id": report.blueprint_id,
            "bridge_id": report.bridge_id,
            "readiness_id": report.readiness_id,
            "contract_id": report.contract_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "route_summary": report.route_summary,
            "component_summary": report.component_summary,
            "state_summary": report.state_summary,
            "style_summary": report.style_summary,
            "routes": [_route_json(route) for route in report.routes],
            "component_files": [
                _component_file_json(component) for component in report.component_files
            ],
            "state_slices": [_state_slice_json(slice_) for slice_ in report.state_slices],
            "style_tokens": [_style_token_json(token) for token in report.style_tokens],
            "acceptance_checks": [_check_json(check) for check in report.acceptance_checks],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **blueprint_json,
        "safety": list(SAFETY_LINES),
    }


def _route_lines(route: StylePerformanceArcLiveGuiDesktopAppPlanRoute) -> list[str]:
    return [
        f"- {route.order}. {route.route_key}: {route.label}",
        f"  Desktop shell: {route.desktop_shell}",
        f"  Viewport: {route.viewport_key}",
        f"  Region: {route.region_key}",
        f"  Grid area: {route.grid_area}",
        f"  Component: {route.component_key}",
        f"  Enabled: {route.enabled}",
        f"  Blocked reason: {route.blocked_reason}",
        f"  Passive: {route.passive}",
    ]


def _component_file_lines(
    component: StylePerformanceArcLiveGuiDesktopAppPlanComponentFile,
) -> list[str]:
    return [
        f"- {component.order}. {component.component_key}",
        f"  Route: {component.route_key}",
        f"  Widget: {component.widget_key}",
        f"  Component type: {component.component_type}",
        f"  Suggested path: {component.suggested_path}",
        f"  Source packet: {component.source_packet_key}",
        f"  JSON key: {component.source_json_key}",
        f"  Test id: {component.test_id}",
        f"  Passive: {component.passive}",
    ]


def _state_slice_lines(
    state_slice: StylePerformanceArcLiveGuiDesktopAppPlanStateSlice,
) -> list[str]:
    return [
        f"- {state_slice.order}. {state_slice.slice_key}",
        f"  Component: {state_slice.component_key}",
        f"  Source packet: {state_slice.source_packet_key}",
        f"  Source JSON path: {state_slice.source_json_path}",
        f"  Reducer hint: {state_slice.reducer_hint}",
        f"  Initial state: {state_slice.initial_state}",
        f"  Passive: {state_slice.passive}",
    ]


def _style_token_lines(token: StylePerformanceArcLiveGuiDesktopAppPlanStyleToken) -> list[str]:
    return [
        f"- {token.token_key}: {token.label}",
        f"  Type: {token.token_type}",
        f"  Value hint: {token.value_hint}",
        f"  Framework target: {token.framework_target}",
        f"  Status: {token.status}",
        f"  Passive: {token.passive}",
    ]


def _check_lines(
    check: StylePerformanceArcLiveGuiDesktopAppPlanAcceptanceCheck,
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


def format_style_performance_arc_live_gui_desktop_app_plan_report(
    report: StylePerformanceArcLiveGuiDesktopAppPlanReport,
) -> list[str]:
    """Format a passive desktop app-plan report."""

    lines = [
        "Live GUI desktop app plan summary:",
        f"- App plan id: {report.app_plan_id}",
        f"- App plan label: {report.app_plan_label}",
        f"- App plan status: {report.app_plan_status}",
        f"- Framework target: {report.framework_target}",
        f"- Blueprint id: {report.blueprint_id}",
        f"- Bridge id: {report.bridge_id}",
        f"- Readiness id: {report.readiness_id}",
        f"- Contract id: {report.contract_id}",
        f"- Selected arc: {report.selected_arc_name} ({report.selected_arc_key})",
        f"- Scope: {report.scope}",
        f"- Route summary: {report.route_summary}",
        f"- Component summary: {report.component_summary}",
        f"- State summary: {report.state_summary}",
        f"- Style summary: {report.style_summary}",
        "App routes:",
    ]
    for route in report.routes:
        lines.extend(_route_lines(route))
    lines.append("Component file hints:")
    for component in report.component_files:
        lines.extend(_component_file_lines(component))
    lines.append("State slices:")
    for state_slice in report.state_slices:
        lines.extend(_state_slice_lines(state_slice))
    lines.append("Style tokens:")
    for token in report.style_tokens:
        lines.extend(_style_token_lines(token))
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


def parse_style_performance_arc_live_gui_desktop_app_plan_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Parse desktop app-plan CLI args for passive report composition."""

    app_plan_label = _DEFAULT_APP_PLAN_LABEL
    framework_target = _DEFAULT_FRAMEWORK_TARGET
    blueprint_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--app-plan-label":
            app_plan_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="app_plan_label",
            )
        elif option == "--framework-target":
            framework_target = _normalize_framework_target(_pop_option_value(remaining))
        else:
            blueprint_args.append(option)
            if option != "--json":
                blueprint_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_desktop_blueprint_cli_args(blueprint_args)
    parsed["app_plan_label"] = app_plan_label
    parsed["framework_target"] = framework_target
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
    desktop_shell: str,
    app_plan_label: str,
    framework_target: str,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_desktop_app_plan_report(
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
            app_plan_label=app_plan_label,
            framework_target=framework_target,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_desktop_app_plan_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_desktop_app_plan_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_APP_PLAN_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-desktop-app-plan-report",
    summary="Compose passive GUI desktop blueprint metadata into a future desktop app plan.",
    args_parser=parse_style_performance_arc_live_gui_desktop_app_plan_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_APP_PLAN_CLI_COMMAND)

__all__ = [
    "DESKTOP_APP_PLAN_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_APP_PLAN_CLI_COMMAND",
    "StylePerformanceArcLiveGuiDesktopAppPlanAcceptanceCheck",
    "StylePerformanceArcLiveGuiDesktopAppPlanComponentFile",
    "StylePerformanceArcLiveGuiDesktopAppPlanReport",
    "StylePerformanceArcLiveGuiDesktopAppPlanRoute",
    "StylePerformanceArcLiveGuiDesktopAppPlanStateSlice",
    "StylePerformanceArcLiveGuiDesktopAppPlanStyleToken",
    "build_style_performance_arc_live_gui_desktop_app_plan_from_blueprint",
    "build_style_performance_arc_live_gui_desktop_app_plan_report",
    "format_style_performance_arc_live_gui_desktop_app_plan_report",
    "parse_style_performance_arc_live_gui_desktop_app_plan_cli_args",
    "to_style_performance_arc_live_gui_desktop_app_plan_json",
]
