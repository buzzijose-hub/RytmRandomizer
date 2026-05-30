"""Passive live GUI desktop render-contract report."""

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
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value, replace_replay_command, status_severity
from .live_gui_desktop_view_model import (
    StylePerformanceArcLiveGuiDesktopViewModelReport,
    build_style_performance_arc_live_gui_desktop_view_model_report,
    parse_style_performance_arc_live_gui_desktop_view_model_cli_args,
    to_style_performance_arc_live_gui_desktop_view_model_json,
)

REPORT_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live GUI desktop render contract"
)
SOURCE_MODULE: Final[str] = "reports.live_gui_desktop_render_contract"
DESKTOP_RENDER_CONTRACT_VERSION: Final[str] = "live-gui-desktop-render-contract-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI desktop render-contract metadata only",
    "consumes live GUI desktop view-model metadata only",
    "render surfaces are declarative metadata only",
    "render bindings are declarative metadata only",
    "style-token bindings are declarative metadata only",
    "render assertions are passive metadata only",
    "future desktop GUI only",
    "future audio analyzer comparison only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
    "no app launch",
    "no component mount",
    "no render surface mount",
    "no prop binding execution",
    "no style injection",
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
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_DEFAULT_RENDER_CONTRACT_LABEL: Final[str] = "Live GUI desktop render contract"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-desktop-render-contract-report usage: "
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
    "[--app-plan-label <text>] "
    "[--framework-target desktop-python|web-desktop|test-harness] "
    "[--component-contract-label <text>] [--selector-prefix <text>] "
    "[--view-model-label <text>] [--state-prefix <text>] "
    "[--render-contract-label <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopRenderSurface:
    """One passive future GUI render surface."""

    surface_key: str
    order: int
    component_key: str
    view_model_key: str
    label: str
    component_type: str
    region_key: str
    route_key: str
    widget_key: str
    test_id: str
    selector: str
    state_key: str
    status: str
    mount_mode: str
    enabled: bool
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopRenderBinding:
    """One passive future GUI render binding."""

    binding_key: str
    order: int
    surface_key: str
    component_key: str
    state_key: str
    prop_name: str
    source_packet_key: str
    source_json_key: str
    fallback_value: str
    required: bool
    binding_mode: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopStyleTokenBinding:
    """One passive future GUI style-token binding."""

    binding_key: str
    token_key: str
    label: str
    token_type: str
    value_hint: str
    framework_target: str
    status: str
    target_surface: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopRenderAssertion:
    """One passive desktop render-contract assertion."""

    assertion_key: str
    label: str
    status: str
    severity: str
    source_id: str
    message: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopRenderContractReport:
    """Passive render contract generated from desktop view-model metadata."""

    view_model: StylePerformanceArcLiveGuiDesktopViewModelReport
    render_contract_version: str
    render_contract_id: str
    render_contract_label: str
    render_contract_status: str
    framework_target: str
    surface_summary: str
    binding_summary: str
    assertion_summary: str
    style_summary: str
    render_surfaces: tuple[StylePerformanceArcLiveGuiDesktopRenderSurface, ...]
    render_bindings: tuple[StylePerformanceArcLiveGuiDesktopRenderBinding, ...]
    style_token_bindings: tuple[StylePerformanceArcLiveGuiDesktopStyleTokenBinding, ...]
    render_assertions: tuple[StylePerformanceArcLiveGuiDesktopRenderAssertion, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def view_model_id(self) -> str:
        """Return upstream desktop view-model id."""

        return self.view_model.view_model_id

    @property
    def component_contract_id(self) -> str:
        """Return upstream component-contract id."""

        return self.view_model.component_contract_id

    @property
    def app_plan_id(self) -> str:
        """Return upstream desktop app-plan id."""

        return self.view_model.app_plan_id

    @property
    def blueprint_id(self) -> str:
        """Return upstream desktop blueprint id."""

        return self.view_model.blueprint_id

    @property
    def bridge_id(self) -> str:
        """Return upstream implementation bridge id."""

        return self.view_model.bridge_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected performance arc key."""

        return self.view_model.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected performance arc name."""

        return self.view_model.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.view_model.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _coverage_status(count: int) -> str:
    if count <= 0:
        return "blocked"
    return "ready"


def _render_surfaces(
    view_model: StylePerformanceArcLiveGuiDesktopViewModelReport,
) -> tuple[StylePerformanceArcLiveGuiDesktopRenderSurface, ...]:
    return tuple(
        StylePerformanceArcLiveGuiDesktopRenderSurface(
            surface_key=f"surface-{component.component_key}",
            order=component.order,
            component_key=component.component_key,
            view_model_key=component.view_model_key,
            label=component.label,
            component_type=component.component_type,
            region_key=component.region_key,
            route_key=component.route_key,
            widget_key=component.widget_key,
            test_id=component.test_id,
            selector=component.selector,
            state_key=component.state_key,
            status=component.status,
            mount_mode="declarative-passive",
            enabled=False,
            passive=True,
        )
        for component in view_model.component_view_models
    )


def _surface_key_by_component(
    render_surfaces: Sequence[StylePerformanceArcLiveGuiDesktopRenderSurface],
) -> dict[str, str]:
    return {surface.component_key: surface.surface_key for surface in render_surfaces}


def _render_bindings(
    view_model: StylePerformanceArcLiveGuiDesktopViewModelReport,
    render_surfaces: Sequence[StylePerformanceArcLiveGuiDesktopRenderSurface],
) -> tuple[StylePerformanceArcLiveGuiDesktopRenderBinding, ...]:
    surface_key_by_component = _surface_key_by_component(render_surfaces)
    return tuple(
        StylePerformanceArcLiveGuiDesktopRenderBinding(
            binding_key=f"render-binding-{binding.component_key}-{binding.prop_name}",
            order=binding.order,
            surface_key=surface_key_by_component[binding.component_key],
            component_key=binding.component_key,
            state_key=binding.state_key,
            prop_name=binding.prop_name,
            source_packet_key=binding.source_packet_key,
            source_json_key=binding.source_json_key,
            fallback_value=binding.fallback_value,
            required=binding.required,
            binding_mode="one-way-state-to-prop",
            passive=binding.passive,
        )
        for binding in view_model.state_bindings
        if binding.component_key in surface_key_by_component
    )


def _style_token_bindings(
    view_model: StylePerformanceArcLiveGuiDesktopViewModelReport,
) -> tuple[StylePerformanceArcLiveGuiDesktopStyleTokenBinding, ...]:
    return tuple(
        StylePerformanceArcLiveGuiDesktopStyleTokenBinding(
            binding_key=f"style-token-binding-{token.token_key}",
            token_key=token.token_key,
            label=token.label,
            token_type=token.token_type,
            value_hint=token.value_hint,
            framework_target=token.framework_target,
            status=token.status,
            target_surface="desktop-shell",
            passive=token.passive,
        )
        for token in view_model.style_tokens
    )


def _assertion(
    *,
    assertion_key: str,
    label: str,
    status: str,
    source_id: str,
    message: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiDesktopRenderAssertion:
    return StylePerformanceArcLiveGuiDesktopRenderAssertion(
        assertion_key=assertion_key,
        label=label,
        status=status,
        severity=status_severity(status),
        source_id=source_id,
        message=message,
        operator_action=operator_action,
        passive=True,
    )


def _view_model_status_for_assertion(
    view_model: StylePerformanceArcLiveGuiDesktopViewModelReport,
) -> str:
    if view_model.view_model_status == "blocked":
        return "blocked"
    if view_model.view_model_status == "review-needed":
        return "review-needed"
    return "ready"


def _disabled_action_status(
    view_model: StylePerformanceArcLiveGuiDesktopViewModelReport,
) -> str:
    if any(action.allowed for action in view_model.action_view_models):
        return "blocked"
    return "ready"


def _replay_status(replay_commands: tuple[str, ...]) -> str:
    if not replay_commands:
        return "review-needed"
    if not replay_commands[0].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-desktop-render-contract-report"
    ):
        return "review-needed"
    return "ready"


def _render_assertions(
    view_model: StylePerformanceArcLiveGuiDesktopViewModelReport,
    *,
    render_surfaces: tuple[StylePerformanceArcLiveGuiDesktopRenderSurface, ...],
    render_bindings: tuple[StylePerformanceArcLiveGuiDesktopRenderBinding, ...],
    style_token_bindings: tuple[StylePerformanceArcLiveGuiDesktopStyleTokenBinding, ...],
    replay_commands: tuple[str, ...],
) -> tuple[StylePerformanceArcLiveGuiDesktopRenderAssertion, ...]:
    return (
        _assertion(
            assertion_key="assert-view-model-status",
            label="Desktop view-model status",
            status=_view_model_status_for_assertion(view_model),
            source_id=view_model.view_model_id,
            message=f"Desktop view-model status is {view_model.view_model_status}.",
            operator_action="resolve view-model blockers before renderer implementation",
        ),
        _assertion(
            assertion_key="assert-render-surface-coverage",
            label="Render surface coverage",
            status=_coverage_status(len(render_surfaces)),
            source_id=view_model.view_model_id,
            message=f"{len(render_surfaces)} render surfaces are available.",
            operator_action="keep render surfaces declarative until GUI implementation",
        ),
        _assertion(
            assertion_key="assert-render-binding-coverage",
            label="Render binding coverage",
            status=_coverage_status(len(render_bindings)),
            source_id=view_model.view_model_id,
            message=f"{len(render_bindings)} render bindings are available.",
            operator_action="do not execute prop or state bindings from the passive CLI",
        ),
        _assertion(
            assertion_key="assert-style-token-binding-coverage",
            label="Style-token binding coverage",
            status=_coverage_status(len(style_token_bindings)),
            source_id=view_model.app_plan_id,
            message=f"{len(style_token_bindings)} style-token bindings are available.",
            operator_action="do not inject styles from the passive CLI",
        ),
        _assertion(
            assertion_key="assert-disabled-action-lock",
            label="Disabled action lock",
            status=_disabled_action_status(view_model),
            source_id=view_model.view_model_id,
            message="All desktop view-model actions remain disabled.",
            operator_action="keep active GUI dispatch outside passive report commands",
        ),
        _assertion(
            assertion_key="assert-replay-command",
            label="Desktop render-contract replay command",
            status=_replay_status(replay_commands),
            source_id=view_model.view_model_id,
            message=(
                "Desktop render-contract replay command is available."
                if replay_commands
                else "Desktop render-contract replay command is missing."
            ),
            operator_action="review command wiring before opening a GUI implementation PR",
        ),
        _assertion(
            assertion_key="assert-passive-boundary",
            label="Passive boundary",
            status="ready",
            source_id=view_model.view_model_id,
            message="Desktop render contract emits metadata only.",
            operator_action="do not launch GUI, dev server, audio analysis, or MIDI hardware",
        ),
    )


def _render_contract_status(
    view_model: StylePerformanceArcLiveGuiDesktopViewModelReport,
    assertions: tuple[StylePerformanceArcLiveGuiDesktopRenderAssertion, ...],
) -> str:
    if view_model.view_model_status == "blocked":
        return "blocked"
    if any(assertion.status == "blocked" for assertion in assertions):
        return "blocked"
    if view_model.view_model_status == "review-needed":
        return "review-needed"
    if any(assertion.status == "review-needed" for assertion in assertions):
        return "review-needed"
    return "ready"


def _blocked_actions(
    view_model: StylePerformanceArcLiveGuiDesktopViewModelReport,
    render_contract_status: str,
) -> tuple[str, ...]:
    actions: list[str] = [
        "no GUI launch",
        "no app launch",
        "no component mount",
        "no render surface mount",
        "no prop binding execution",
        "no style injection",
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
    for action in view_model.blocked_actions:
        if action not in actions:
            actions.append(action)
    if render_contract_status != "ready":
        actions.insert(0, "hold render contract until desktop view model is clear")
    return tuple(actions)


def _render_contract_id(
    view_model: StylePerformanceArcLiveGuiDesktopViewModelReport,
    *,
    render_contract_label: str,
    render_contract_status: str,
) -> str:
    payload = "|".join(
        (
            DESKTOP_RENDER_CONTRACT_VERSION,
            view_model.view_model_id,
            view_model.component_contract_id,
            view_model.app_plan_id,
            view_model.selected_arc_key,
            view_model.scope,
            view_model.framework_target,
            render_contract_label,
            render_contract_status,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _replace_replay_command(
    command: str,
    *,
    render_contract_label: str,
) -> str | None:
    return replace_replay_command(
        command,
        source_command="style-performance-arc-live-gui-desktop-view-model-report",
        target_command="style-performance-arc-live-gui-desktop-render-contract-report",
        extra_options=(("--render-contract-label", render_contract_label),),
    )


def _replay_commands(
    view_model: StylePerformanceArcLiveGuiDesktopViewModelReport,
    *,
    render_contract_label: str,
) -> tuple[str, ...]:
    if not view_model.replay_commands:
        return ()
    render_contract_command = _replace_replay_command(
        view_model.replay_commands[0],
        render_contract_label=render_contract_label,
    )
    if render_contract_command is None:
        return view_model.replay_commands
    return (render_contract_command, *view_model.replay_commands)


def build_style_performance_arc_live_gui_desktop_render_contract_from_view_model(
    view_model: StylePerformanceArcLiveGuiDesktopViewModelReport,
    *,
    render_contract_label: str = _DEFAULT_RENDER_CONTRACT_LABEL,
) -> StylePerformanceArcLiveGuiDesktopRenderContractReport:
    """Build one passive desktop render contract from view-model metadata."""

    normalized_label = _normalize_nonblank(
        render_contract_label,
        field="render_contract_label",
    )
    render_surfaces = _render_surfaces(view_model)
    render_bindings = _render_bindings(view_model, render_surfaces)
    style_token_bindings = _style_token_bindings(view_model)
    replay_commands = _replay_commands(
        view_model,
        render_contract_label=normalized_label,
    )
    render_assertions = _render_assertions(
        view_model,
        render_surfaces=render_surfaces,
        render_bindings=render_bindings,
        style_token_bindings=style_token_bindings,
        replay_commands=replay_commands,
    )
    render_contract_status = _render_contract_status(view_model, render_assertions)
    return StylePerformanceArcLiveGuiDesktopRenderContractReport(
        view_model=view_model,
        render_contract_version=DESKTOP_RENDER_CONTRACT_VERSION,
        render_contract_id=_render_contract_id(
            view_model,
            render_contract_label=normalized_label,
            render_contract_status=render_contract_status,
        ),
        render_contract_label=normalized_label,
        render_contract_status=render_contract_status,
        framework_target=view_model.framework_target,
        surface_summary=f"{len(render_surfaces)} render surfaces for future GUI.",
        binding_summary=f"{len(render_bindings)} render bindings for future GUI.",
        assertion_summary=f"{len(render_assertions)} render assertions for future GUI.",
        style_summary=f"{len(style_token_bindings)} style-token bindings for future GUI.",
        render_surfaces=render_surfaces,
        render_bindings=render_bindings,
        style_token_bindings=style_token_bindings,
        render_assertions=render_assertions,
        blocked_actions=_blocked_actions(view_model, render_contract_status),
        replay_commands=replay_commands,
    )


def build_style_performance_arc_live_gui_desktop_render_contract_report(
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
    app_plan_label: str = "Live GUI desktop app plan",
    framework_target: str = "desktop-python",
    component_contract_label: str = "Live GUI desktop component contract",
    selector_prefix: str = "live-gui",
    view_model_label: str = "Live GUI desktop view model",
    state_prefix: str = "live-gui-state",
    render_contract_label: str = _DEFAULT_RENDER_CONTRACT_LABEL,
) -> StylePerformanceArcLiveGuiDesktopRenderContractReport:
    """Build one passive desktop render-contract report."""

    view_model = build_style_performance_arc_live_gui_desktop_view_model_report(
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
        app_plan_label=app_plan_label,
        framework_target=framework_target,
        component_contract_label=component_contract_label,
        selector_prefix=selector_prefix,
        view_model_label=view_model_label,
        state_prefix=state_prefix,
    )
    return build_style_performance_arc_live_gui_desktop_render_contract_from_view_model(
        view_model,
        render_contract_label=render_contract_label,
    )


def _render_surface_json(
    surface: StylePerformanceArcLiveGuiDesktopRenderSurface,
) -> dict[str, object]:
    return {
        "surface_key": surface.surface_key,
        "order": surface.order,
        "component_key": surface.component_key,
        "view_model_key": surface.view_model_key,
        "label": surface.label,
        "component_type": surface.component_type,
        "region_key": surface.region_key,
        "route_key": surface.route_key,
        "widget_key": surface.widget_key,
        "test_id": surface.test_id,
        "selector": surface.selector,
        "state_key": surface.state_key,
        "status": surface.status,
        "mount_mode": surface.mount_mode,
        "enabled": surface.enabled,
        "passive": surface.passive,
    }


def _render_binding_json(
    binding: StylePerformanceArcLiveGuiDesktopRenderBinding,
) -> dict[str, object]:
    return {
        "binding_key": binding.binding_key,
        "order": binding.order,
        "surface_key": binding.surface_key,
        "component_key": binding.component_key,
        "state_key": binding.state_key,
        "prop_name": binding.prop_name,
        "source_packet_key": binding.source_packet_key,
        "source_json_key": binding.source_json_key,
        "fallback_value": binding.fallback_value,
        "required": binding.required,
        "binding_mode": binding.binding_mode,
        "passive": binding.passive,
    }


def _style_token_binding_json(
    binding: StylePerformanceArcLiveGuiDesktopStyleTokenBinding,
) -> dict[str, object]:
    return {
        "binding_key": binding.binding_key,
        "token_key": binding.token_key,
        "label": binding.label,
        "token_type": binding.token_type,
        "value_hint": binding.value_hint,
        "framework_target": binding.framework_target,
        "status": binding.status,
        "target_surface": binding.target_surface,
        "passive": binding.passive,
    }


def _assertion_json(
    assertion: StylePerformanceArcLiveGuiDesktopRenderAssertion,
) -> dict[str, object]:
    return {
        "assertion_key": assertion.assertion_key,
        "label": assertion.label,
        "status": assertion.status,
        "severity": assertion.severity,
        "source_id": assertion.source_id,
        "message": assertion.message,
        "operator_action": assertion.operator_action,
        "passive": assertion.passive,
    }


def to_style_performance_arc_live_gui_desktop_render_contract_json(
    report: StylePerformanceArcLiveGuiDesktopRenderContractReport,
) -> dict[str, object]:
    """Return deterministic JSON for a passive desktop render contract."""

    view_model_json = to_style_performance_arc_live_gui_desktop_view_model_json(report.view_model)
    return {
        "live_gui_desktop_render_contract": {
            "render_contract_version": report.render_contract_version,
            "render_contract_id": report.render_contract_id,
            "render_contract_label": report.render_contract_label,
            "render_contract_status": report.render_contract_status,
            "framework_target": report.framework_target,
            "view_model_id": report.view_model_id,
            "component_contract_id": report.component_contract_id,
            "app_plan_id": report.app_plan_id,
            "blueprint_id": report.blueprint_id,
            "bridge_id": report.bridge_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "surface_summary": report.surface_summary,
            "binding_summary": report.binding_summary,
            "assertion_summary": report.assertion_summary,
            "style_summary": report.style_summary,
            "render_surfaces": [
                _render_surface_json(surface) for surface in report.render_surfaces
            ],
            "render_bindings": [
                _render_binding_json(binding) for binding in report.render_bindings
            ],
            "style_token_bindings": [
                _style_token_binding_json(binding) for binding in report.style_token_bindings
            ],
            "render_assertions": [
                _assertion_json(assertion) for assertion in report.render_assertions
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **view_model_json,
        "safety": list(SAFETY_LINES),
    }


def _render_surface_lines(
    surface: StylePerformanceArcLiveGuiDesktopRenderSurface,
) -> list[str]:
    return [
        f"- {surface.order}. {surface.surface_key}: {surface.label}",
        f"  Component: {surface.component_key}",
        f"  View model: {surface.view_model_key}",
        f"  Type: {surface.component_type}",
        f"  Region: {surface.region_key}",
        f"  Route: {surface.route_key}",
        f"  Widget: {surface.widget_key}",
        f"  Test id: {surface.test_id}",
        f"  Selector: {surface.selector}",
        f"  State key: {surface.state_key}",
        f"  Status: {surface.status}",
        f"  Mount mode: {surface.mount_mode}",
        f"  Enabled: {surface.enabled}",
        f"  Passive: {surface.passive}",
    ]


def _render_binding_lines(
    binding: StylePerformanceArcLiveGuiDesktopRenderBinding,
) -> list[str]:
    return [
        f"- {binding.order}. {binding.binding_key}",
        f"  Surface: {binding.surface_key}",
        f"  Component: {binding.component_key}",
        f"  State key: {binding.state_key}",
        f"  Prop: {binding.prop_name}",
        f"  Source packet: {binding.source_packet_key}",
        f"  Source JSON key: {binding.source_json_key}",
        f"  Fallback: {binding.fallback_value}",
        f"  Required: {binding.required}",
        f"  Binding mode: {binding.binding_mode}",
        f"  Passive: {binding.passive}",
    ]


def _style_token_binding_lines(
    binding: StylePerformanceArcLiveGuiDesktopStyleTokenBinding,
) -> list[str]:
    return [
        f"- {binding.binding_key}: {binding.label}",
        f"  Token: {binding.token_key}",
        f"  Type: {binding.token_type}",
        f"  Value hint: {binding.value_hint}",
        f"  Framework target: {binding.framework_target}",
        f"  Status: {binding.status}",
        f"  Target surface: {binding.target_surface}",
        f"  Passive: {binding.passive}",
    ]


def _assertion_lines(assertion: StylePerformanceArcLiveGuiDesktopRenderAssertion) -> list[str]:
    return [
        f"- {assertion.assertion_key}: {assertion.label}",
        f"  Status: {assertion.status}",
        f"  Severity: {assertion.severity}",
        f"  Source id: {assertion.source_id}",
        f"  Message: {assertion.message}",
        f"  Operator action: {assertion.operator_action}",
        f"  Passive: {assertion.passive}",
    ]


def format_style_performance_arc_live_gui_desktop_render_contract_report(
    report: StylePerformanceArcLiveGuiDesktopRenderContractReport,
) -> list[str]:
    """Format a passive desktop render-contract report."""

    lines = [
        "Live GUI desktop render contract summary:",
        f"- Render contract id: {report.render_contract_id}",
        f"- Render contract label: {report.render_contract_label}",
        f"- Render contract status: {report.render_contract_status}",
        f"- Framework target: {report.framework_target}",
        f"- View model id: {report.view_model_id}",
        f"- Component contract id: {report.component_contract_id}",
        f"- App plan id: {report.app_plan_id}",
        f"- Blueprint id: {report.blueprint_id}",
        f"- Bridge id: {report.bridge_id}",
        f"- Selected arc: {report.selected_arc_name} ({report.selected_arc_key})",
        f"- Scope: {report.scope}",
        f"- Surface summary: {report.surface_summary}",
        f"- Binding summary: {report.binding_summary}",
        f"- Assertion summary: {report.assertion_summary}",
        f"- Style summary: {report.style_summary}",
        "Render surfaces:",
    ]
    for surface in report.render_surfaces:
        lines.extend(_render_surface_lines(surface))
    lines.append("Render bindings:")
    for binding in report.render_bindings:
        lines.extend(_render_binding_lines(binding))
    lines.append("Style-token bindings:")
    for binding in report.style_token_bindings:
        lines.extend(_style_token_binding_lines(binding))
    lines.append("Render assertions:")
    for assertion in report.render_assertions:
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
    return pop_option_value(remaining, usage=_USAGE)


def parse_style_performance_arc_live_gui_desktop_render_contract_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Parse desktop render-contract CLI args for passive report composition."""

    render_contract_label = _DEFAULT_RENDER_CONTRACT_LABEL
    view_model_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--render-contract-label":
            render_contract_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="render_contract_label",
            )
        else:
            view_model_args.append(option)
            if option != "--json":
                view_model_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_desktop_view_model_cli_args(view_model_args)
    parsed["render_contract_label"] = render_contract_label
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
    component_contract_label: str,
    selector_prefix: str,
    view_model_label: str,
    state_prefix: str,
    render_contract_label: str,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_desktop_render_contract_report(
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
            component_contract_label=component_contract_label,
            selector_prefix=selector_prefix,
            view_model_label=view_model_label,
            state_prefix=state_prefix,
            render_contract_label=render_contract_label,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_desktop_render_contract_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_desktop_render_contract_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_RENDER_CONTRACT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-desktop-render-contract-report",
    summary="Compose passive GUI desktop view models into render contracts.",
    args_parser=parse_style_performance_arc_live_gui_desktop_render_contract_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_RENDER_CONTRACT_CLI_COMMAND)

__all__ = [
    "DESKTOP_RENDER_CONTRACT_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_RENDER_CONTRACT_CLI_COMMAND",
    "StylePerformanceArcLiveGuiDesktopRenderAssertion",
    "StylePerformanceArcLiveGuiDesktopRenderBinding",
    "StylePerformanceArcLiveGuiDesktopRenderContractReport",
    "StylePerformanceArcLiveGuiDesktopRenderSurface",
    "StylePerformanceArcLiveGuiDesktopStyleTokenBinding",
    "build_style_performance_arc_live_gui_desktop_render_contract_from_view_model",
    "build_style_performance_arc_live_gui_desktop_render_contract_report",
    "format_style_performance_arc_live_gui_desktop_render_contract_report",
    "parse_style_performance_arc_live_gui_desktop_render_contract_cli_args",
    "to_style_performance_arc_live_gui_desktop_render_contract_json",
]
