"""Passive live GUI desktop view-model report."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.live_gui_contracts import LIVE_GUI_DESKTOP_MOUNT_REGION_SPECS
from ..style_analysis.feature_report import FeatureReport
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value, replace_replay_command, status_severity
from .live_gui_desktop_component_contract import (
    StylePerformanceArcLiveGuiDesktopComponentContractReport,
    build_style_performance_arc_live_gui_desktop_component_contract_report,
    parse_style_performance_arc_live_gui_desktop_component_contract_cli_args,
    to_style_performance_arc_live_gui_desktop_component_contract_json,
)

REPORT_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live GUI desktop view model"
)
SOURCE_MODULE: Final[str] = "reports.live_gui_desktop_view_model"
DESKTOP_VIEW_MODEL_VERSION: Final[str] = "live-gui-desktop-view-model-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI desktop view-model metadata only",
    "consumes live GUI desktop component-contract metadata only",
    "component view models are declarative metadata only",
    "state bindings are declarative metadata only",
    "action view models are disabled metadata only",
    "style tokens are declarative metadata only",
    "future desktop GUI only",
    "future audio analyzer comparison only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
    "no app launch",
    "no component mount",
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
_DEFAULT_VIEW_MODEL_LABEL: Final[str] = "Live GUI desktop view model"
_DEFAULT_STATE_PREFIX: Final[str] = "live-gui-state"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-desktop-view-model-report usage: "
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
    "[--view-model-label <text>] [--state-prefix <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopComponentViewModel:
    """One passive future component view model."""

    view_model_key: str
    order: int
    component_key: str
    label: str
    component_type: str
    region_key: str
    route_key: str
    widget_key: str
    test_id: str
    selector: str
    state_key: str
    status: str
    enabled: bool
    blocked_reason: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopStateBinding:
    """One passive future GUI state binding."""

    binding_key: str
    order: int
    component_key: str
    state_key: str
    prop_name: str
    source_packet_key: str
    source_json_key: str
    fallback_value: str
    required: bool
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopActionViewModel:
    """One disabled future action view model."""

    action_model_key: str
    order: int
    component_key: str
    action_name: str
    control_state: str
    allowed: bool
    blocked_reason: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopStyleToken:
    """One passive future desktop style-token view model."""

    token_key: str
    label: str
    token_type: str
    value_hint: str
    framework_target: str
    status: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopViewModelAcceptanceCheck:
    """One passive desktop view-model acceptance check."""

    check_key: str
    label: str
    status: str
    severity: str
    source_id: str
    message: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopViewModelReport:
    """Passive desktop view-model packet from component-contract metadata."""

    component_contract: StylePerformanceArcLiveGuiDesktopComponentContractReport
    view_model_version: str
    view_model_id: str
    view_model_label: str
    view_model_status: str
    state_prefix: str
    framework_target: str
    component_summary: str
    binding_summary: str
    action_summary: str
    style_summary: str
    component_view_models: tuple[
        StylePerformanceArcLiveGuiDesktopComponentViewModel,
        ...,
    ]
    state_bindings: tuple[StylePerformanceArcLiveGuiDesktopStateBinding, ...]
    action_view_models: tuple[StylePerformanceArcLiveGuiDesktopActionViewModel, ...]
    style_tokens: tuple[StylePerformanceArcLiveGuiDesktopStyleToken, ...]
    acceptance_checks: tuple[StylePerformanceArcLiveGuiDesktopViewModelAcceptanceCheck, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def component_contract_id(self) -> str:
        """Return upstream component-contract id."""

        return self.component_contract.component_contract_id

    @property
    def app_plan_id(self) -> str:
        """Return upstream desktop app-plan id."""

        return self.component_contract.app_plan_id

    @property
    def blueprint_id(self) -> str:
        """Return upstream desktop blueprint id."""

        return self.component_contract.blueprint_id

    @property
    def bridge_id(self) -> str:
        """Return upstream implementation bridge id."""

        return self.component_contract.bridge_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected performance arc key."""

        return self.component_contract.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected performance arc name."""

        return self.component_contract.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.component_contract.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _coverage_status(count: int) -> str:
    if count <= 0:
        return "blocked"
    return "ready"


def _selector_text(selector: str) -> str:
    prefix = "data-testid="
    if selector.startswith(prefix):
        return selector
    return f"{prefix}{selector}"


def _region_by_component() -> dict[str, str]:
    return {mount.component_key: mount.region_key for mount in LIVE_GUI_DESKTOP_MOUNT_REGION_SPECS}


def _selector_by_component(
    component_contract: StylePerformanceArcLiveGuiDesktopComponentContractReport,
) -> dict[str, str]:
    return {
        selector.component_key: _selector_text(selector.selector)
        for selector in component_contract.test_selectors
    }


def _component_view_models(
    component_contract: StylePerformanceArcLiveGuiDesktopComponentContractReport,
    *,
    state_prefix: str,
) -> tuple[StylePerformanceArcLiveGuiDesktopComponentViewModel, ...]:
    region_by_component = _region_by_component()
    selector_by_component = _selector_by_component(component_contract)
    return tuple(
        StylePerformanceArcLiveGuiDesktopComponentViewModel(
            view_model_key=f"view-model-{component.component_key}",
            order=component.order,
            component_key=component.component_key,
            label=component.label,
            component_type=component.component_type,
            region_key=region_by_component.get(component.component_key, "region-unassigned"),
            route_key=component.route_key,
            widget_key=component.widget_key,
            test_id=component.test_id,
            selector=selector_by_component.get(component.component_key, ""),
            state_key=f"{state_prefix}.{component.component_key}",
            status=component.status,
            enabled=False,
            blocked_reason="future desktop view model only; no component is mounted",
            passive=True,
        )
        for component in component_contract.component_contracts
    )


def _state_key_by_component(
    component_view_models: Sequence[StylePerformanceArcLiveGuiDesktopComponentViewModel],
) -> dict[str, str]:
    return {component.component_key: component.state_key for component in component_view_models}


def _state_bindings(
    component_contract: StylePerformanceArcLiveGuiDesktopComponentContractReport,
    component_view_models: Sequence[StylePerformanceArcLiveGuiDesktopComponentViewModel],
) -> tuple[StylePerformanceArcLiveGuiDesktopStateBinding, ...]:
    state_key_by_component = _state_key_by_component(component_view_models)
    return tuple(
        StylePerformanceArcLiveGuiDesktopStateBinding(
            binding_key=f"binding-{prop.component_key}-{prop.prop_name}",
            order=prop.order,
            component_key=prop.component_key,
            state_key=state_key_by_component[prop.component_key],
            prop_name=prop.prop_name,
            source_packet_key=prop.source_packet_key,
            source_json_key=prop.source_json_key,
            fallback_value=prop.fallback_value,
            required=prop.required,
            passive=prop.passive,
        )
        for prop in component_contract.prop_contracts
        if prop.component_key in state_key_by_component
    )


def _action_view_models(
    component_contract: StylePerformanceArcLiveGuiDesktopComponentContractReport,
) -> tuple[StylePerformanceArcLiveGuiDesktopActionViewModel, ...]:
    return tuple(
        StylePerformanceArcLiveGuiDesktopActionViewModel(
            action_model_key=f"action-view-model-{action.component_key}-{action.action_name}",
            order=action.order,
            component_key=action.component_key,
            action_name=action.action_name,
            control_state="disabled",
            allowed=False,
            blocked_reason=action.blocked_reason,
            operator_action=action.operator_action,
            passive=True,
        )
        for action in component_contract.action_contracts
    )


def _style_tokens(
    component_contract: StylePerformanceArcLiveGuiDesktopComponentContractReport,
) -> tuple[StylePerformanceArcLiveGuiDesktopStyleToken, ...]:
    return tuple(
        StylePerformanceArcLiveGuiDesktopStyleToken(
            token_key=token.token_key,
            label=token.label,
            token_type=token.token_type,
            value_hint=token.value_hint,
            framework_target=token.framework_target,
            status=token.status,
            passive=token.passive,
        )
        for token in component_contract.desktop_app_plan.style_tokens
    )


def _check(
    *,
    check_key: str,
    label: str,
    status: str,
    source_id: str,
    message: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiDesktopViewModelAcceptanceCheck:
    return StylePerformanceArcLiveGuiDesktopViewModelAcceptanceCheck(
        check_key=check_key,
        label=label,
        status=status,
        severity=status_severity(status),
        source_id=source_id,
        message=message,
        operator_action=operator_action,
        passive=True,
    )


def _component_contract_status_for_check(
    component_contract: StylePerformanceArcLiveGuiDesktopComponentContractReport,
) -> str:
    if component_contract.component_contract_status == "blocked":
        return "blocked"
    if component_contract.component_contract_status == "review-needed":
        return "review-needed"
    return "ready"


def _replay_status(replay_commands: tuple[str, ...]) -> str:
    if not replay_commands:
        return "review-needed"
    if not replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-desktop-view-model-report"
    ):
        return "review-needed"
    return "ready"


def _acceptance_checks(
    component_contract: StylePerformanceArcLiveGuiDesktopComponentContractReport,
    *,
    component_view_models: tuple[StylePerformanceArcLiveGuiDesktopComponentViewModel, ...],
    state_bindings: tuple[StylePerformanceArcLiveGuiDesktopStateBinding, ...],
    action_view_models: tuple[StylePerformanceArcLiveGuiDesktopActionViewModel, ...],
    style_tokens: tuple[StylePerformanceArcLiveGuiDesktopStyleToken, ...],
    replay_commands: tuple[str, ...],
) -> tuple[StylePerformanceArcLiveGuiDesktopViewModelAcceptanceCheck, ...]:
    return (
        _check(
            check_key="accept-component-contract-status",
            label="Desktop component-contract status",
            status=_component_contract_status_for_check(component_contract),
            source_id=component_contract.component_contract_id,
            message=f"Desktop component-contract status is {component_contract.component_contract_status}.",
            operator_action="resolve component-contract blockers before view-model wiring",
        ),
        _check(
            check_key="accept-view-model-coverage",
            label="Component view-model coverage",
            status=_coverage_status(len(component_view_models)),
            source_id=component_contract.component_contract_id,
            message=f"{len(component_view_models)} component view models are available.",
            operator_action="keep component view models declarative until the GUI implementation PR",
        ),
        _check(
            check_key="accept-state-binding-coverage",
            label="State binding coverage",
            status=_coverage_status(len(state_bindings)),
            source_id=component_contract.component_contract_id,
            message=f"{len(state_bindings)} state bindings are available.",
            operator_action="do not mutate GUI state from the passive CLI",
        ),
        _check(
            check_key="accept-action-model-coverage",
            label="Action view-model coverage",
            status=_coverage_status(len(action_view_models)),
            source_id=component_contract.component_contract_id,
            message=f"{len(action_view_models)} disabled action view models are available.",
            operator_action="do not dispatch GUI actions from the passive CLI",
        ),
        _check(
            check_key="accept-style-token-coverage",
            label="Style token coverage",
            status=_coverage_status(len(style_tokens)),
            source_id=component_contract.component_contract_id,
            message=f"{len(style_tokens)} style tokens are available.",
            operator_action="keep style tokens declarative until GUI rendering lands",
        ),
        _check(
            check_key="accept-replay-command",
            label="Desktop view-model replay command",
            status=_replay_status(replay_commands),
            source_id=component_contract.component_contract_id,
            message=(
                "Desktop view-model replay command is available."
                if replay_commands
                else "Desktop view-model replay command is missing."
            ),
            operator_action="review command wiring before opening a GUI implementation PR",
        ),
        _check(
            check_key="accept-passive-boundary",
            label="Passive boundary",
            status="ready",
            source_id=component_contract.component_contract_id,
            message="Desktop view model emits metadata only.",
            operator_action="do not launch GUI, dev server, audio analysis, or MIDI hardware",
        ),
    )


def _view_model_status(
    component_contract: StylePerformanceArcLiveGuiDesktopComponentContractReport,
    checks: tuple[StylePerformanceArcLiveGuiDesktopViewModelAcceptanceCheck, ...],
) -> str:
    if component_contract.component_contract_status == "blocked":
        return "blocked"
    if any(check.status == "blocked" for check in checks):
        return "blocked"
    if component_contract.component_contract_status == "review-needed":
        return "review-needed"
    if any(check.status == "review-needed" for check in checks):
        return "review-needed"
    return "ready"


def _blocked_actions(view_model_status: str) -> tuple[str, ...]:
    actions: list[str] = [
        "no GUI launch",
        "no app launch",
        "no component mount",
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
    if view_model_status != "ready":
        actions.insert(0, "hold view model until component contract is clear")
    return tuple(actions)


def _view_model_id(
    component_contract: StylePerformanceArcLiveGuiDesktopComponentContractReport,
    *,
    view_model_label: str,
    view_model_status: str,
    state_prefix: str,
) -> str:
    payload = "|".join(
        (
            DESKTOP_VIEW_MODEL_VERSION,
            component_contract.component_contract_id,
            component_contract.app_plan_id,
            component_contract.selected_arc_key,
            component_contract.scope,
            component_contract.framework_target,
            view_model_label,
            view_model_status,
            state_prefix,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _replace_replay_command(
    command: str,
    *,
    view_model_label: str,
    state_prefix: str,
) -> str | None:
    return replace_replay_command(
        command,
        source_command="style-performance-arc-live-gui-desktop-component-contract-report",
        target_command="style-performance-arc-live-gui-desktop-view-model-report",
        extra_options=(
            ("--view-model-label", view_model_label),
            ("--state-prefix", state_prefix),
        ),
    )


def _replay_commands(
    component_contract: StylePerformanceArcLiveGuiDesktopComponentContractReport,
    *,
    view_model_label: str,
    state_prefix: str,
) -> tuple[str, ...]:
    if not component_contract.replay_commands:
        return ()
    view_model_command = _replace_replay_command(
        component_contract.replay_commands[0],
        view_model_label=view_model_label,
        state_prefix=state_prefix,
    )
    if view_model_command is None:
        return component_contract.replay_commands
    return (view_model_command, *component_contract.replay_commands)


def build_style_performance_arc_live_gui_desktop_view_model_from_component_contract(
    component_contract: StylePerformanceArcLiveGuiDesktopComponentContractReport,
    *,
    view_model_label: str = _DEFAULT_VIEW_MODEL_LABEL,
    state_prefix: str = _DEFAULT_STATE_PREFIX,
) -> StylePerformanceArcLiveGuiDesktopViewModelReport:
    """Build one passive view-model packet from component-contract metadata."""

    normalized_label = _normalize_nonblank(view_model_label, field="view_model_label")
    normalized_state_prefix = _normalize_nonblank(state_prefix, field="state_prefix")
    component_view_models = _component_view_models(
        component_contract,
        state_prefix=normalized_state_prefix,
    )
    state_bindings = _state_bindings(component_contract, component_view_models)
    action_view_models = _action_view_models(component_contract)
    style_tokens = _style_tokens(component_contract)
    replay_commands = _replay_commands(
        component_contract,
        view_model_label=normalized_label,
        state_prefix=normalized_state_prefix,
    )
    checks = _acceptance_checks(
        component_contract,
        component_view_models=component_view_models,
        state_bindings=state_bindings,
        action_view_models=action_view_models,
        style_tokens=style_tokens,
        replay_commands=replay_commands,
    )
    view_model_status = _view_model_status(component_contract, checks)
    return StylePerformanceArcLiveGuiDesktopViewModelReport(
        component_contract=component_contract,
        view_model_version=DESKTOP_VIEW_MODEL_VERSION,
        view_model_id=_view_model_id(
            component_contract,
            view_model_label=normalized_label,
            view_model_status=view_model_status,
            state_prefix=normalized_state_prefix,
        ),
        view_model_label=normalized_label,
        view_model_status=view_model_status,
        state_prefix=normalized_state_prefix,
        framework_target=component_contract.framework_target,
        component_summary=f"{len(component_view_models)} component view models for future GUI.",
        binding_summary=f"{len(state_bindings)} state bindings for future GUI.",
        action_summary=f"{len(action_view_models)} disabled action view models for future GUI.",
        style_summary=f"{len(style_tokens)} style tokens for future GUI.",
        component_view_models=component_view_models,
        state_bindings=state_bindings,
        action_view_models=action_view_models,
        style_tokens=style_tokens,
        acceptance_checks=checks,
        blocked_actions=_blocked_actions(view_model_status),
        replay_commands=replay_commands,
    )


def build_style_performance_arc_live_gui_desktop_view_model_report(
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
    view_model_label: str = _DEFAULT_VIEW_MODEL_LABEL,
    state_prefix: str = _DEFAULT_STATE_PREFIX,
) -> StylePerformanceArcLiveGuiDesktopViewModelReport:
    """Build one passive desktop view-model report."""

    component_contract = build_style_performance_arc_live_gui_desktop_component_contract_report(
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
    )
    return build_style_performance_arc_live_gui_desktop_view_model_from_component_contract(
        component_contract,
        view_model_label=view_model_label,
        state_prefix=state_prefix,
    )


def _component_view_model_json(
    component: StylePerformanceArcLiveGuiDesktopComponentViewModel,
) -> dict[str, object]:
    return {
        "view_model_key": component.view_model_key,
        "order": component.order,
        "component_key": component.component_key,
        "label": component.label,
        "component_type": component.component_type,
        "region_key": component.region_key,
        "route_key": component.route_key,
        "widget_key": component.widget_key,
        "test_id": component.test_id,
        "selector": component.selector,
        "state_key": component.state_key,
        "status": component.status,
        "enabled": component.enabled,
        "blocked_reason": component.blocked_reason,
        "passive": component.passive,
    }


def _state_binding_json(
    binding: StylePerformanceArcLiveGuiDesktopStateBinding,
) -> dict[str, object]:
    return {
        "binding_key": binding.binding_key,
        "order": binding.order,
        "component_key": binding.component_key,
        "state_key": binding.state_key,
        "prop_name": binding.prop_name,
        "source_packet_key": binding.source_packet_key,
        "source_json_key": binding.source_json_key,
        "fallback_value": binding.fallback_value,
        "required": binding.required,
        "passive": binding.passive,
    }


def _action_view_model_json(
    action: StylePerformanceArcLiveGuiDesktopActionViewModel,
) -> dict[str, object]:
    return {
        "action_model_key": action.action_model_key,
        "order": action.order,
        "component_key": action.component_key,
        "action_name": action.action_name,
        "control_state": action.control_state,
        "allowed": action.allowed,
        "blocked_reason": action.blocked_reason,
        "operator_action": action.operator_action,
        "passive": action.passive,
    }


def _style_token_json(token: StylePerformanceArcLiveGuiDesktopStyleToken) -> dict[str, object]:
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
    check: StylePerformanceArcLiveGuiDesktopViewModelAcceptanceCheck,
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


def to_style_performance_arc_live_gui_desktop_view_model_json(
    report: StylePerformanceArcLiveGuiDesktopViewModelReport,
) -> dict[str, object]:
    """Return deterministic JSON for a passive desktop view model."""

    component_contract_json = to_style_performance_arc_live_gui_desktop_component_contract_json(
        report.component_contract
    )
    return {
        "live_gui_desktop_view_model": {
            "view_model_version": report.view_model_version,
            "view_model_id": report.view_model_id,
            "view_model_label": report.view_model_label,
            "view_model_status": report.view_model_status,
            "state_prefix": report.state_prefix,
            "framework_target": report.framework_target,
            "component_contract_id": report.component_contract_id,
            "app_plan_id": report.app_plan_id,
            "blueprint_id": report.blueprint_id,
            "bridge_id": report.bridge_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "component_summary": report.component_summary,
            "binding_summary": report.binding_summary,
            "action_summary": report.action_summary,
            "style_summary": report.style_summary,
            "component_view_models": [
                _component_view_model_json(component) for component in report.component_view_models
            ],
            "state_bindings": [_state_binding_json(binding) for binding in report.state_bindings],
            "action_view_models": [
                _action_view_model_json(action) for action in report.action_view_models
            ],
            "style_tokens": [_style_token_json(token) for token in report.style_tokens],
            "acceptance_checks": [_check_json(check) for check in report.acceptance_checks],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **component_contract_json,
        "safety": list(SAFETY_LINES),
    }


def _component_view_model_lines(
    component: StylePerformanceArcLiveGuiDesktopComponentViewModel,
) -> list[str]:
    return [
        f"- {component.order}. {component.component_key}: {component.label}",
        f"  View model key: {component.view_model_key}",
        f"  Type: {component.component_type}",
        f"  Region: {component.region_key}",
        f"  Route: {component.route_key}",
        f"  Widget: {component.widget_key}",
        f"  Test id: {component.test_id}",
        f"  Selector: {component.selector}",
        f"  State key: {component.state_key}",
        f"  Status: {component.status}",
        f"  Enabled: {component.enabled}",
        f"  Blocked reason: {component.blocked_reason}",
        f"  Passive: {component.passive}",
    ]


def _state_binding_lines(binding: StylePerformanceArcLiveGuiDesktopStateBinding) -> list[str]:
    return [
        f"- {binding.order}. {binding.binding_key}",
        f"  Component: {binding.component_key}",
        f"  State key: {binding.state_key}",
        f"  Prop: {binding.prop_name}",
        f"  Source packet: {binding.source_packet_key}",
        f"  Source JSON key: {binding.source_json_key}",
        f"  Fallback: {binding.fallback_value}",
        f"  Required: {binding.required}",
        f"  Passive: {binding.passive}",
    ]


def _action_view_model_lines(
    action: StylePerformanceArcLiveGuiDesktopActionViewModel,
) -> list[str]:
    return [
        f"- {action.order}. {action.action_model_key}",
        f"  Component: {action.component_key}",
        f"  Action: {action.action_name}",
        f"  Control state: {action.control_state}",
        f"  Allowed: {action.allowed}",
        f"  Blocked reason: {action.blocked_reason}",
        f"  Operator action: {action.operator_action}",
        f"  Passive: {action.passive}",
    ]


def _style_token_lines(token: StylePerformanceArcLiveGuiDesktopStyleToken) -> list[str]:
    return [
        f"- {token.token_key}: {token.label}",
        f"  Type: {token.token_type}",
        f"  Value hint: {token.value_hint}",
        f"  Framework target: {token.framework_target}",
        f"  Status: {token.status}",
        f"  Passive: {token.passive}",
    ]


def _check_lines(check: StylePerformanceArcLiveGuiDesktopViewModelAcceptanceCheck) -> list[str]:
    return [
        f"- {check.check_key}: {check.label}",
        f"  Status: {check.status}",
        f"  Severity: {check.severity}",
        f"  Source id: {check.source_id}",
        f"  Message: {check.message}",
        f"  Operator action: {check.operator_action}",
        f"  Passive: {check.passive}",
    ]


def format_style_performance_arc_live_gui_desktop_view_model_report(
    report: StylePerformanceArcLiveGuiDesktopViewModelReport,
) -> list[str]:
    """Format a passive desktop view-model report."""

    lines = [
        "Live GUI desktop view model summary:",
        f"- View model id: {report.view_model_id}",
        f"- View model label: {report.view_model_label}",
        f"- View model status: {report.view_model_status}",
        f"- State prefix: {report.state_prefix}",
        f"- Framework target: {report.framework_target}",
        f"- Component contract id: {report.component_contract_id}",
        f"- App plan id: {report.app_plan_id}",
        f"- Blueprint id: {report.blueprint_id}",
        f"- Bridge id: {report.bridge_id}",
        f"- Selected arc: {report.selected_arc_name} ({report.selected_arc_key})",
        f"- Scope: {report.scope}",
        f"- Component summary: {report.component_summary}",
        f"- Binding summary: {report.binding_summary}",
        f"- Action summary: {report.action_summary}",
        f"- Style summary: {report.style_summary}",
        "Component view models:",
    ]
    for component in report.component_view_models:
        lines.extend(_component_view_model_lines(component))
    lines.append("State bindings:")
    for binding in report.state_bindings:
        lines.extend(_state_binding_lines(binding))
    lines.append("Action view models:")
    for action in report.action_view_models:
        lines.extend(_action_view_model_lines(action))
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


def parse_style_performance_arc_live_gui_desktop_view_model_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Parse desktop view-model CLI args for passive report composition."""

    view_model_label = _DEFAULT_VIEW_MODEL_LABEL
    state_prefix = _DEFAULT_STATE_PREFIX
    component_contract_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--view-model-label":
            view_model_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="view_model_label",
            )
        elif option == "--state-prefix":
            state_prefix = _normalize_nonblank(
                _pop_option_value(remaining),
                field="state_prefix",
            )
        else:
            component_contract_args.append(option)
            if option != "--json":
                component_contract_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_desktop_component_contract_cli_args(
        component_contract_args
    )
    parsed["view_model_label"] = view_model_label
    parsed["state_prefix"] = state_prefix
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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_desktop_view_model_report(
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_desktop_view_model_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_desktop_view_model_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_VIEW_MODEL_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-desktop-view-model-report",
    summary="Compose passive GUI desktop component contracts into future view models.",
    args_parser=parse_style_performance_arc_live_gui_desktop_view_model_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_VIEW_MODEL_CLI_COMMAND)

__all__ = [
    "DESKTOP_VIEW_MODEL_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_VIEW_MODEL_CLI_COMMAND",
    "StylePerformanceArcLiveGuiDesktopActionViewModel",
    "StylePerformanceArcLiveGuiDesktopComponentViewModel",
    "StylePerformanceArcLiveGuiDesktopStateBinding",
    "StylePerformanceArcLiveGuiDesktopStyleToken",
    "StylePerformanceArcLiveGuiDesktopViewModelAcceptanceCheck",
    "StylePerformanceArcLiveGuiDesktopViewModelReport",
    "build_style_performance_arc_live_gui_desktop_view_model_from_component_contract",
    "build_style_performance_arc_live_gui_desktop_view_model_report",
    "format_style_performance_arc_live_gui_desktop_view_model_report",
    "parse_style_performance_arc_live_gui_desktop_view_model_cli_args",
    "to_style_performance_arc_live_gui_desktop_view_model_json",
]
