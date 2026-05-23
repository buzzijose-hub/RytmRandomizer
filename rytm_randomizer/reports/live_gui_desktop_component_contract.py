"""Passive live GUI desktop component-contract report."""

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
from .live_gui_desktop_app_plan import (
    StylePerformanceArcLiveGuiDesktopAppPlanComponentFile,
    StylePerformanceArcLiveGuiDesktopAppPlanReport,
    build_style_performance_arc_live_gui_desktop_app_plan_report,
    parse_style_performance_arc_live_gui_desktop_app_plan_cli_args,
    to_style_performance_arc_live_gui_desktop_app_plan_json,
)

REPORT_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live GUI desktop component contract"
)
SOURCE_MODULE: Final[str] = "reports.live_gui_desktop_component_contract"
DESKTOP_COMPONENT_CONTRACT_VERSION: Final[str] = "live-gui-desktop-component-contract-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI desktop component-contract metadata only",
    "consumes live GUI desktop app-plan metadata only",
    "component contracts are declarative metadata only",
    "prop contracts are declarative metadata only",
    "action contracts are declarative metadata only",
    "test selectors are declarative metadata only",
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
_DEFAULT_COMPONENT_CONTRACT_LABEL: Final[str] = "Live GUI desktop component contract"
_DEFAULT_SELECTOR_PREFIX: Final[str] = "live-gui"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-desktop-component-contract-report usage: "
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
    "[--component-contract-label <text>] [--selector-prefix <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopComponentContract:
    """One passive future component contract."""

    component_key: str
    order: int
    label: str
    component_type: str
    route_key: str
    widget_key: str
    suggested_path: str
    framework_target: str
    status: str
    enabled: bool
    blocked_reason: str
    test_id: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopComponentPropContract:
    """One passive future component prop contract."""

    prop_key: str
    order: int
    component_key: str
    prop_name: str
    source_packet_key: str
    source_json_key: str
    required: bool
    fallback_value: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopComponentActionContract:
    """One disabled future component action contract."""

    action_key: str
    order: int
    component_key: str
    action_name: str
    allowed: bool
    blocked_reason: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopComponentTestSelector:
    """One passive future component selector contract."""

    selector_key: str
    order: int
    component_key: str
    selector: str
    purpose: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopComponentAcceptanceCheck:
    """One passive component-contract acceptance check."""

    check_key: str
    label: str
    status: str
    severity: str
    source_id: str
    message: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopComponentContractReport:
    """Passive component contract composed from desktop app-plan metadata."""

    desktop_app_plan: StylePerformanceArcLiveGuiDesktopAppPlanReport
    component_contract_version: str
    component_contract_id: str
    component_contract_label: str
    component_contract_status: str
    selector_prefix: str
    framework_target: str
    component_summary: str
    prop_summary: str
    action_summary: str
    selector_summary: str
    component_contracts: tuple[StylePerformanceArcLiveGuiDesktopComponentContract, ...]
    prop_contracts: tuple[
        StylePerformanceArcLiveGuiDesktopComponentPropContract,
        ...,
    ]
    action_contracts: tuple[
        StylePerformanceArcLiveGuiDesktopComponentActionContract,
        ...,
    ]
    test_selectors: tuple[StylePerformanceArcLiveGuiDesktopComponentTestSelector, ...]
    acceptance_checks: tuple[
        StylePerformanceArcLiveGuiDesktopComponentAcceptanceCheck,
        ...,
    ]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def app_plan_id(self) -> str:
        """Return upstream desktop app-plan id."""

        return self.desktop_app_plan.app_plan_id

    @property
    def blueprint_id(self) -> str:
        """Return upstream desktop blueprint id."""

        return self.desktop_app_plan.blueprint_id

    @property
    def bridge_id(self) -> str:
        """Return upstream implementation bridge id."""

        return self.desktop_app_plan.bridge_id

    @property
    def readiness_id(self) -> str:
        """Return upstream readiness id."""

        return self.desktop_app_plan.readiness_id

    @property
    def contract_id(self) -> str:
        """Return upstream test-harness contract id."""

        return self.desktop_app_plan.contract_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected performance arc key."""

        return self.desktop_app_plan.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected performance arc name."""

        return self.desktop_app_plan.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.desktop_app_plan.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _slug(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value.strip()]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug or "selector"


def _status_severity(status: str) -> str:
    if status == "blocked":
        return "critical"
    if status == "review-needed":
        return "warning"
    return "info"


def _coverage_status(count: int) -> str:
    if count <= 0:
        return "blocked"
    return "ready"


def _app_plan_status_for_check(app_plan: StylePerformanceArcLiveGuiDesktopAppPlanReport) -> str:
    if app_plan.app_plan_status == "blocked":
        return "blocked"
    if app_plan.app_plan_status == "review-needed":
        return "review-needed"
    return "ready"


def _component_contract_id(
    app_plan: StylePerformanceArcLiveGuiDesktopAppPlanReport,
    *,
    component_contract_label: str,
    component_contract_status: str,
    selector_prefix: str,
) -> str:
    payload = "|".join(
        (
            DESKTOP_COMPONENT_CONTRACT_VERSION,
            app_plan.app_plan_id,
            app_plan.blueprint_id,
            app_plan.selected_arc_key,
            app_plan.scope,
            app_plan.framework_target,
            component_contract_label,
            component_contract_status,
            selector_prefix,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _component_contract(
    component_file: StylePerformanceArcLiveGuiDesktopAppPlanComponentFile,
    *,
    framework_target: str,
) -> StylePerformanceArcLiveGuiDesktopComponentContract:
    return StylePerformanceArcLiveGuiDesktopComponentContract(
        component_key=component_file.component_key,
        order=component_file.order,
        label=component_file.component_key.replace("-", " ").title(),
        component_type=component_file.component_type,
        route_key=component_file.route_key,
        widget_key=component_file.widget_key,
        suggested_path=component_file.suggested_path,
        framework_target=framework_target,
        status="ready",
        enabled=False,
        blocked_reason="future component contract only; no component is mounted",
        test_id=component_file.test_id,
        passive=True,
    )


def _component_contracts(
    component_files: Sequence[StylePerformanceArcLiveGuiDesktopAppPlanComponentFile],
    *,
    framework_target: str,
) -> tuple[StylePerformanceArcLiveGuiDesktopComponentContract, ...]:
    return tuple(
        _component_contract(component_file, framework_target=framework_target)
        for component_file in component_files
    )


def _prop_contracts(
    component_contracts: Sequence[StylePerformanceArcLiveGuiDesktopComponentContract],
) -> tuple[StylePerformanceArcLiveGuiDesktopComponentPropContract, ...]:
    props: list[StylePerformanceArcLiveGuiDesktopComponentPropContract] = []
    order = 1
    for component in component_contracts:
        props.append(
            StylePerformanceArcLiveGuiDesktopComponentPropContract(
                prop_key=f"prop-{component.component_key}-source-data",
                order=order,
                component_key=component.component_key,
                prop_name="sourceData",
                source_packet_key=component.widget_key,
                source_json_key=f"$.live_gui_desktop_app_plan.component_files[{component.order - 1}]",
                required=True,
                fallback_value="disabled-empty-state",
                passive=True,
            )
        )
        order += 1
        props.append(
            StylePerformanceArcLiveGuiDesktopComponentPropContract(
                prop_key=f"prop-{component.component_key}-status",
                order=order,
                component_key=component.component_key,
                prop_name="status",
                source_packet_key=component.widget_key,
                source_json_key=f"$.live_gui_desktop_app_plan.component_files[{component.order - 1}]",
                required=True,
                fallback_value="blocked",
                passive=True,
            )
        )
        order += 1
    return tuple(props)


def _action_contracts(
    component_contracts: Sequence[StylePerformanceArcLiveGuiDesktopComponentContract],
) -> tuple[StylePerformanceArcLiveGuiDesktopComponentActionContract, ...]:
    return tuple(
        StylePerformanceArcLiveGuiDesktopComponentActionContract(
            action_key=f"action-{component.component_key}-activate",
            order=component.order,
            component_key=component.component_key,
            action_name="activate",
            allowed=False,
            blocked_reason="future GUI action only; no event dispatch in passive CLI",
            operator_action="keep active component actions disabled until the GUI implementation PR",
            passive=True,
        )
        for component in component_contracts
    )


def _test_selectors(
    component_contracts: Sequence[StylePerformanceArcLiveGuiDesktopComponentContract],
    *,
    selector_prefix: str,
) -> tuple[StylePerformanceArcLiveGuiDesktopComponentTestSelector, ...]:
    normalized_prefix = _slug(selector_prefix)
    return tuple(
        StylePerformanceArcLiveGuiDesktopComponentTestSelector(
            selector_key=f"selector-{component.component_key}",
            order=component.order,
            component_key=component.component_key,
            selector=f"data-testid={normalized_prefix}-{component.component_key}",
            purpose="future GUI test harness selector",
            passive=True,
        )
        for component in component_contracts
    )


def _check(
    *,
    check_key: str,
    label: str,
    status: str,
    source_id: str,
    message: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiDesktopComponentAcceptanceCheck:
    return StylePerformanceArcLiveGuiDesktopComponentAcceptanceCheck(
        check_key=check_key,
        label=label,
        status=status,
        severity=_status_severity(status),
        source_id=source_id,
        message=message,
        operator_action=operator_action,
        passive=True,
    )


def _replay_status(replay_commands: tuple[str, ...]) -> str:
    if not replay_commands:
        return "review-needed"
    if not replay_commands[0].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-desktop-component-contract-report"
    ):
        return "review-needed"
    return "ready"


def _acceptance_checks(
    app_plan: StylePerformanceArcLiveGuiDesktopAppPlanReport,
    *,
    component_contracts: tuple[StylePerformanceArcLiveGuiDesktopComponentContract, ...],
    prop_contracts: tuple[StylePerformanceArcLiveGuiDesktopComponentPropContract, ...],
    action_contracts: tuple[StylePerformanceArcLiveGuiDesktopComponentActionContract, ...],
    test_selectors: tuple[StylePerformanceArcLiveGuiDesktopComponentTestSelector, ...],
    replay_commands: tuple[str, ...],
) -> tuple[StylePerformanceArcLiveGuiDesktopComponentAcceptanceCheck, ...]:
    return (
        _check(
            check_key="accept-app-plan-status",
            label="Desktop app-plan status",
            status=_app_plan_status_for_check(app_plan),
            source_id=app_plan.app_plan_id,
            message=f"Desktop app-plan status is {app_plan.app_plan_status}.",
            operator_action="resolve desktop app-plan blockers before component contracts",
        ),
        _check(
            check_key="accept-component-coverage",
            label="Component coverage",
            status=_coverage_status(len(component_contracts)),
            source_id=app_plan.app_plan_id,
            message=f"{len(component_contracts)} component contracts are available.",
            operator_action="keep component contracts declarative until a GUI implementation PR",
        ),
        _check(
            check_key="accept-prop-coverage",
            label="Prop coverage",
            status=_coverage_status(len(prop_contracts)),
            source_id=app_plan.app_plan_id,
            message=f"{len(prop_contracts)} prop contracts are available.",
            operator_action="keep props declarative until a GUI implementation PR",
        ),
        _check(
            check_key="accept-action-coverage",
            label="Action coverage",
            status=_coverage_status(len(action_contracts)),
            source_id=app_plan.app_plan_id,
            message=f"{len(action_contracts)} disabled action contracts are available.",
            operator_action="do not dispatch GUI actions from the passive CLI",
        ),
        _check(
            check_key="accept-selector-coverage",
            label="Selector coverage",
            status=_coverage_status(len(test_selectors)),
            source_id=app_plan.app_plan_id,
            message=f"{len(test_selectors)} test selectors are available.",
            operator_action="do not create GUI test files in the passive report",
        ),
        _check(
            check_key="accept-replay-command",
            label="Desktop component-contract replay command",
            status=_replay_status(replay_commands),
            source_id=app_plan.app_plan_id,
            message=(
                "Desktop component-contract replay command is available."
                if replay_commands
                else "Desktop component-contract replay command is missing."
            ),
            operator_action="review command wiring before opening a GUI implementation PR",
        ),
        _check(
            check_key="accept-passive-boundary",
            label="Passive boundary",
            status="ready",
            source_id=app_plan.app_plan_id,
            message="Desktop component contract emits metadata only.",
            operator_action="do not launch GUI, dev server, audio analysis, or MIDI hardware",
        ),
    )


def _component_contract_status(
    app_plan: StylePerformanceArcLiveGuiDesktopAppPlanReport,
    checks: tuple[StylePerformanceArcLiveGuiDesktopComponentAcceptanceCheck, ...],
) -> str:
    if app_plan.app_plan_status == "blocked":
        return "blocked"
    if any(check.status == "blocked" for check in checks):
        return "blocked"
    if app_plan.app_plan_status == "review-needed":
        return "review-needed"
    if any(check.status == "review-needed" for check in checks):
        return "review-needed"
    return "ready"


def _blocked_actions(component_contract_status: str) -> tuple[str, ...]:
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
    if component_contract_status != "ready":
        actions.insert(0, "hold component contracts until desktop app plan is clear")
    return tuple(actions)


def _replace_replay_command(
    command: str,
    *,
    component_contract_label: str,
    selector_prefix: str,
) -> str | None:
    source = "style-performance-arc-live-gui-desktop-app-plan-report"
    target = "style-performance-arc-live-gui-desktop-component-contract-report"
    if source not in command:
        return None
    return (
        command.replace(source, target, 1)
        + " --component-contract-label "
        + powershell_literal_arg(component_contract_label)
        + f" --selector-prefix {powershell_literal_arg(selector_prefix)}"
    )


def _replay_commands(
    app_plan: StylePerformanceArcLiveGuiDesktopAppPlanReport,
    *,
    component_contract_label: str,
    selector_prefix: str,
) -> tuple[str, ...]:
    if not app_plan.replay_commands:
        return ()
    component_contract_command = _replace_replay_command(
        app_plan.replay_commands[0],
        component_contract_label=component_contract_label,
        selector_prefix=selector_prefix,
    )
    if component_contract_command is None:
        return app_plan.replay_commands
    return (component_contract_command, *app_plan.replay_commands)


def build_style_performance_arc_live_gui_desktop_component_contract_from_app_plan(
    app_plan: StylePerformanceArcLiveGuiDesktopAppPlanReport,
    *,
    component_contract_label: str = _DEFAULT_COMPONENT_CONTRACT_LABEL,
    selector_prefix: str = _DEFAULT_SELECTOR_PREFIX,
) -> StylePerformanceArcLiveGuiDesktopComponentContractReport:
    """Build one passive component contract from desktop app-plan metadata."""

    normalized_label = _normalize_nonblank(
        component_contract_label,
        field="component_contract_label",
    )
    normalized_selector_prefix = _normalize_nonblank(
        selector_prefix,
        field="selector_prefix",
    )
    component_contracts = _component_contracts(
        app_plan.component_files,
        framework_target=app_plan.framework_target,
    )
    prop_contracts = _prop_contracts(component_contracts)
    action_contracts = _action_contracts(component_contracts)
    test_selectors = _test_selectors(
        component_contracts,
        selector_prefix=normalized_selector_prefix,
    )
    replay_commands = _replay_commands(
        app_plan,
        component_contract_label=normalized_label,
        selector_prefix=normalized_selector_prefix,
    )
    checks = _acceptance_checks(
        app_plan,
        component_contracts=component_contracts,
        prop_contracts=prop_contracts,
        action_contracts=action_contracts,
        test_selectors=test_selectors,
        replay_commands=replay_commands,
    )
    component_contract_status = _component_contract_status(app_plan, checks)
    return StylePerformanceArcLiveGuiDesktopComponentContractReport(
        desktop_app_plan=app_plan,
        component_contract_version=DESKTOP_COMPONENT_CONTRACT_VERSION,
        component_contract_id=_component_contract_id(
            app_plan,
            component_contract_label=normalized_label,
            component_contract_status=component_contract_status,
            selector_prefix=normalized_selector_prefix,
        ),
        component_contract_label=normalized_label,
        component_contract_status=component_contract_status,
        selector_prefix=normalized_selector_prefix,
        framework_target=app_plan.framework_target,
        component_summary=f"{len(component_contracts)} component contracts for future GUI.",
        prop_summary=f"{len(prop_contracts)} prop contracts for future GUI components.",
        action_summary=f"{len(action_contracts)} disabled action contracts for future GUI.",
        selector_summary=f"{len(test_selectors)} test selectors for future GUI harness.",
        component_contracts=component_contracts,
        prop_contracts=prop_contracts,
        action_contracts=action_contracts,
        test_selectors=test_selectors,
        acceptance_checks=checks,
        blocked_actions=_blocked_actions(component_contract_status),
        replay_commands=replay_commands,
    )


def build_style_performance_arc_live_gui_desktop_component_contract_report(
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
    component_contract_label: str = _DEFAULT_COMPONENT_CONTRACT_LABEL,
    selector_prefix: str = _DEFAULT_SELECTOR_PREFIX,
) -> StylePerformanceArcLiveGuiDesktopComponentContractReport:
    """Build one passive desktop component-contract report."""

    app_plan = build_style_performance_arc_live_gui_desktop_app_plan_report(
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
    )
    return build_style_performance_arc_live_gui_desktop_component_contract_from_app_plan(
        app_plan,
        component_contract_label=component_contract_label,
        selector_prefix=selector_prefix,
    )


def _component_json(
    component: StylePerformanceArcLiveGuiDesktopComponentContract,
) -> dict[str, object]:
    return {
        "component_key": component.component_key,
        "order": component.order,
        "label": component.label,
        "component_type": component.component_type,
        "route_key": component.route_key,
        "widget_key": component.widget_key,
        "suggested_path": component.suggested_path,
        "framework_target": component.framework_target,
        "status": component.status,
        "enabled": component.enabled,
        "blocked_reason": component.blocked_reason,
        "test_id": component.test_id,
        "passive": component.passive,
    }


def _prop_json(
    prop: StylePerformanceArcLiveGuiDesktopComponentPropContract,
) -> dict[str, object]:
    return {
        "prop_key": prop.prop_key,
        "order": prop.order,
        "component_key": prop.component_key,
        "prop_name": prop.prop_name,
        "source_packet_key": prop.source_packet_key,
        "source_json_key": prop.source_json_key,
        "required": prop.required,
        "fallback_value": prop.fallback_value,
        "passive": prop.passive,
    }


def _action_json(
    action: StylePerformanceArcLiveGuiDesktopComponentActionContract,
) -> dict[str, object]:
    return {
        "action_key": action.action_key,
        "order": action.order,
        "component_key": action.component_key,
        "action_name": action.action_name,
        "allowed": action.allowed,
        "blocked_reason": action.blocked_reason,
        "operator_action": action.operator_action,
        "passive": action.passive,
    }


def _selector_json(
    selector: StylePerformanceArcLiveGuiDesktopComponentTestSelector,
) -> dict[str, object]:
    return {
        "selector_key": selector.selector_key,
        "order": selector.order,
        "component_key": selector.component_key,
        "selector": selector.selector,
        "purpose": selector.purpose,
        "passive": selector.passive,
    }


def _check_json(
    check: StylePerformanceArcLiveGuiDesktopComponentAcceptanceCheck,
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


def to_style_performance_arc_live_gui_desktop_component_contract_json(
    report: StylePerformanceArcLiveGuiDesktopComponentContractReport,
) -> dict[str, object]:
    """Return deterministic JSON for a passive desktop component contract."""

    app_plan_json = to_style_performance_arc_live_gui_desktop_app_plan_json(report.desktop_app_plan)
    return {
        "live_gui_desktop_component_contract": {
            "component_contract_version": report.component_contract_version,
            "component_contract_id": report.component_contract_id,
            "component_contract_label": report.component_contract_label,
            "component_contract_status": report.component_contract_status,
            "selector_prefix": report.selector_prefix,
            "framework_target": report.framework_target,
            "app_plan_id": report.app_plan_id,
            "blueprint_id": report.blueprint_id,
            "bridge_id": report.bridge_id,
            "readiness_id": report.readiness_id,
            "contract_id": report.contract_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "component_summary": report.component_summary,
            "prop_summary": report.prop_summary,
            "action_summary": report.action_summary,
            "selector_summary": report.selector_summary,
            "component_contracts": [
                _component_json(component) for component in report.component_contracts
            ],
            "prop_contracts": [_prop_json(prop) for prop in report.prop_contracts],
            "action_contracts": [_action_json(action) for action in report.action_contracts],
            "test_selectors": [_selector_json(selector) for selector in report.test_selectors],
            "acceptance_checks": [_check_json(check) for check in report.acceptance_checks],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **app_plan_json,
        "safety": list(SAFETY_LINES),
    }


def _component_lines(
    component: StylePerformanceArcLiveGuiDesktopComponentContract,
) -> list[str]:
    return [
        f"- {component.order}. {component.component_key}: {component.label}",
        f"  Type: {component.component_type}",
        f"  Route: {component.route_key}",
        f"  Widget: {component.widget_key}",
        f"  Suggested path: {component.suggested_path}",
        f"  Framework target: {component.framework_target}",
        f"  Status: {component.status}",
        f"  Enabled: {component.enabled}",
        f"  Blocked reason: {component.blocked_reason}",
        f"  Test id: {component.test_id}",
        f"  Passive: {component.passive}",
    ]


def _prop_lines(prop: StylePerformanceArcLiveGuiDesktopComponentPropContract) -> list[str]:
    return [
        f"- {prop.order}. {prop.prop_key}",
        f"  Component: {prop.component_key}",
        f"  Prop: {prop.prop_name}",
        f"  Source packet: {prop.source_packet_key}",
        f"  Source JSON key: {prop.source_json_key}",
        f"  Required: {prop.required}",
        f"  Fallback: {prop.fallback_value}",
        f"  Passive: {prop.passive}",
    ]


def _action_lines(
    action: StylePerformanceArcLiveGuiDesktopComponentActionContract,
) -> list[str]:
    return [
        f"- {action.order}. {action.action_key}",
        f"  Component: {action.component_key}",
        f"  Action: {action.action_name}",
        f"  Allowed: {action.allowed}",
        f"  Blocked reason: {action.blocked_reason}",
        f"  Operator action: {action.operator_action}",
        f"  Passive: {action.passive}",
    ]


def _selector_lines(
    selector: StylePerformanceArcLiveGuiDesktopComponentTestSelector,
) -> list[str]:
    return [
        f"- {selector.order}. {selector.selector_key}",
        f"  Component: {selector.component_key}",
        f"  Selector: {selector.selector}",
        f"  Purpose: {selector.purpose}",
        f"  Passive: {selector.passive}",
    ]


def _check_lines(
    check: StylePerformanceArcLiveGuiDesktopComponentAcceptanceCheck,
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


def format_style_performance_arc_live_gui_desktop_component_contract_report(
    report: StylePerformanceArcLiveGuiDesktopComponentContractReport,
) -> list[str]:
    """Format a passive desktop component-contract report."""

    lines = [
        "Live GUI desktop component contract summary:",
        f"- Component contract id: {report.component_contract_id}",
        f"- Component contract label: {report.component_contract_label}",
        f"- Component contract status: {report.component_contract_status}",
        f"- Selector prefix: {report.selector_prefix}",
        f"- Framework target: {report.framework_target}",
        f"- App plan id: {report.app_plan_id}",
        f"- Blueprint id: {report.blueprint_id}",
        f"- Bridge id: {report.bridge_id}",
        f"- Readiness id: {report.readiness_id}",
        f"- Contract id: {report.contract_id}",
        f"- Selected arc: {report.selected_arc_name} ({report.selected_arc_key})",
        f"- Scope: {report.scope}",
        f"- Component summary: {report.component_summary}",
        f"- Prop summary: {report.prop_summary}",
        f"- Action summary: {report.action_summary}",
        f"- Selector summary: {report.selector_summary}",
        "Component contracts:",
    ]
    for component in report.component_contracts:
        lines.extend(_component_lines(component))
    lines.append("Prop contracts:")
    for prop in report.prop_contracts:
        lines.extend(_prop_lines(prop))
    lines.append("Action contracts:")
    for action in report.action_contracts:
        lines.extend(_action_lines(action))
    lines.append("Test selectors:")
    for selector in report.test_selectors:
        lines.extend(_selector_lines(selector))
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
    if not remaining:
        raise ValueError(_USAGE)
    return remaining.pop(0)


def parse_style_performance_arc_live_gui_desktop_component_contract_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Parse desktop component-contract CLI args for passive report composition."""

    component_contract_label = _DEFAULT_COMPONENT_CONTRACT_LABEL
    selector_prefix = _DEFAULT_SELECTOR_PREFIX
    app_plan_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--component-contract-label":
            component_contract_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="component_contract_label",
            )
        elif option == "--selector-prefix":
            selector_prefix = _normalize_nonblank(
                _pop_option_value(remaining),
                field="selector_prefix",
            )
        else:
            app_plan_args.append(option)
            if option != "--json":
                app_plan_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_desktop_app_plan_cli_args(app_plan_args)
    parsed["component_contract_label"] = component_contract_label
    parsed["selector_prefix"] = selector_prefix
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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_desktop_component_contract_report(
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_desktop_component_contract_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_desktop_component_contract_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND: Final[CliCommand] = (
    CliCommand(
        name="style-performance-arc-live-gui-desktop-component-contract-report",
        summary="Compose passive GUI desktop app plan metadata into future component contracts.",
        args_parser=parse_style_performance_arc_live_gui_desktop_component_contract_cli_args,
        handler=_handle_cli_report,
        error_formatter=_format_cli_error,
    )
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND)

__all__ = [
    "DESKTOP_COMPONENT_CONTRACT_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND",
    "StylePerformanceArcLiveGuiDesktopComponentAcceptanceCheck",
    "StylePerformanceArcLiveGuiDesktopComponentActionContract",
    "StylePerformanceArcLiveGuiDesktopComponentContract",
    "StylePerformanceArcLiveGuiDesktopComponentContractReport",
    "StylePerformanceArcLiveGuiDesktopComponentPropContract",
    "StylePerformanceArcLiveGuiDesktopComponentTestSelector",
    "build_style_performance_arc_live_gui_desktop_component_contract_from_app_plan",
    "build_style_performance_arc_live_gui_desktop_component_contract_report",
    "format_style_performance_arc_live_gui_desktop_component_contract_report",
    "parse_style_performance_arc_live_gui_desktop_component_contract_cli_args",
    "to_style_performance_arc_live_gui_desktop_component_contract_json",
]
