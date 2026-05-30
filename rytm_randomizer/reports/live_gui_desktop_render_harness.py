"""Passive live GUI desktop render-harness report."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value, replace_replay_command, status_severity
from .live_gui_desktop_render_contract import (
    StylePerformanceArcLiveGuiDesktopRenderContractReport,
    build_style_performance_arc_live_gui_desktop_render_contract_report,
    parse_style_performance_arc_live_gui_desktop_render_contract_cli_args,
    to_style_performance_arc_live_gui_desktop_render_contract_json,
)

REPORT_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live GUI desktop render harness"
)
SOURCE_MODULE: Final[str] = "reports.live_gui_desktop_render_harness"
DESKTOP_RENDER_HARNESS_VERSION: Final[str] = "live-gui-desktop-render-harness-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI desktop render-harness metadata only",
    "consumes live GUI desktop render-contract metadata only",
    "surface harnesses are declarative metadata only",
    "binding harnesses are declarative metadata only",
    "style-token checks are declarative metadata only",
    "harness assertions are passive metadata only",
    "future desktop GUI only",
    "future GUI test harness only",
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
    "no browser automation execution",
    "no screenshot capture",
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
_DEFAULT_RENDER_HARNESS_LABEL: Final[str] = "Live GUI desktop render harness"
_DEFAULT_RUNNER_LABEL: Final[str] = "Live GUI passive desktop runner"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-desktop-render-harness-report usage: "
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
    "[--render-contract-label <text>] "
    "[--render-harness-label <text>] [--runner-label <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopSurfaceHarness:
    """One passive future desktop GUI surface harness."""

    harness_key: str
    order: int
    render_surface_key: str
    component_key: str
    label: str
    selector: str
    test_id: str
    state_key: str
    fixture_key: str
    assertion_key: str
    mount_policy: str
    runner_enabled: bool
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopBindingHarness:
    """One passive future desktop GUI binding harness."""

    binding_key: str
    order: int
    render_binding_key: str
    surface_harness_key: str
    component_key: str
    state_key: str
    prop_name: str
    source_json_key: str
    assertion_key: str
    evaluation_policy: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopStyleTokenCheck:
    """One passive future desktop GUI style-token check."""

    check_key: str
    order: int
    token_key: str
    label: str
    framework_target: str
    target_surface: str
    check_policy: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopHarnessAssertion:
    """One passive desktop render-harness assertion."""

    assertion_key: str
    label: str
    status: str
    severity: str
    source_id: str
    message: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiDesktopRenderHarnessReport:
    """Passive desktop render harness generated from render-contract metadata."""

    render_contract: StylePerformanceArcLiveGuiDesktopRenderContractReport
    render_harness_version: str
    render_harness_id: str
    render_harness_label: str
    runner_label: str
    render_harness_status: str
    framework_target: str
    surface_harness_summary: str
    binding_harness_summary: str
    style_token_check_summary: str
    assertion_summary: str
    surface_harnesses: tuple[StylePerformanceArcLiveGuiDesktopSurfaceHarness, ...]
    binding_harnesses: tuple[StylePerformanceArcLiveGuiDesktopBindingHarness, ...]
    style_token_checks: tuple[StylePerformanceArcLiveGuiDesktopStyleTokenCheck, ...]
    harness_assertions: tuple[StylePerformanceArcLiveGuiDesktopHarnessAssertion, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def render_contract_id(self) -> str:
        """Return upstream desktop render-contract id."""

        return self.render_contract.render_contract_id

    @property
    def view_model_id(self) -> str:
        """Return upstream desktop view-model id."""

        return self.render_contract.view_model_id

    @property
    def component_contract_id(self) -> str:
        """Return upstream desktop component-contract id."""

        return self.render_contract.component_contract_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected performance arc key."""

        return self.render_contract.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected performance arc name."""

        return self.render_contract.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.render_contract.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _coverage_status(count: int) -> str:
    if count <= 0:
        return "blocked"
    return "ready"


def _surface_harnesses(
    render_contract: StylePerformanceArcLiveGuiDesktopRenderContractReport,
) -> tuple[StylePerformanceArcLiveGuiDesktopSurfaceHarness, ...]:
    return tuple(
        StylePerformanceArcLiveGuiDesktopSurfaceHarness(
            harness_key=f"harness-{surface.surface_key}",
            order=surface.order,
            render_surface_key=surface.surface_key,
            component_key=surface.component_key,
            label=surface.label,
            selector=surface.selector,
            test_id=surface.test_id,
            state_key=surface.state_key,
            fixture_key=f"fixture-{surface.surface_key}",
            assertion_key=f"assert-{surface.surface_key}",
            mount_policy="metadata-only-no-mount",
            runner_enabled=False,
            passive=True,
        )
        for surface in render_contract.render_surfaces
    )


def _surface_harness_key_by_surface(
    surface_harnesses: Sequence[StylePerformanceArcLiveGuiDesktopSurfaceHarness],
) -> dict[str, str]:
    return {surface.render_surface_key: surface.harness_key for surface in surface_harnesses}


def _binding_harnesses(
    render_contract: StylePerformanceArcLiveGuiDesktopRenderContractReport,
    surface_harnesses: Sequence[StylePerformanceArcLiveGuiDesktopSurfaceHarness],
) -> tuple[StylePerformanceArcLiveGuiDesktopBindingHarness, ...]:
    surface_harness_key_by_surface = _surface_harness_key_by_surface(surface_harnesses)
    return tuple(
        StylePerformanceArcLiveGuiDesktopBindingHarness(
            binding_key=f"harness-binding-{binding.binding_key}",
            order=binding.order,
            render_binding_key=binding.binding_key,
            surface_harness_key=surface_harness_key_by_surface[binding.surface_key],
            component_key=binding.component_key,
            state_key=binding.state_key,
            prop_name=binding.prop_name,
            source_json_key=binding.source_json_key,
            assertion_key=f"assert-binding-{binding.component_key}-{binding.prop_name}",
            evaluation_policy="metadata-only-no-evaluation",
            passive=True,
        )
        for binding in render_contract.render_bindings
        if binding.surface_key in surface_harness_key_by_surface
    )


def _style_token_checks(
    render_contract: StylePerformanceArcLiveGuiDesktopRenderContractReport,
) -> tuple[StylePerformanceArcLiveGuiDesktopStyleTokenCheck, ...]:
    return tuple(
        StylePerformanceArcLiveGuiDesktopStyleTokenCheck(
            check_key=f"style-check-{binding.token_key}",
            order=order,
            token_key=binding.token_key,
            label=binding.label,
            framework_target=binding.framework_target,
            target_surface=binding.target_surface,
            check_policy="metadata-only-no-style-injection",
            passive=True,
        )
        for order, binding in enumerate(render_contract.style_token_bindings)
    )


def _assertion(
    *,
    assertion_key: str,
    label: str,
    status: str,
    source_id: str,
    message: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiDesktopHarnessAssertion:
    return StylePerformanceArcLiveGuiDesktopHarnessAssertion(
        assertion_key=assertion_key,
        label=label,
        status=status,
        severity=status_severity(status),
        source_id=source_id,
        message=message,
        operator_action=operator_action,
        passive=True,
    )


def _render_contract_status_for_assertion(
    render_contract: StylePerformanceArcLiveGuiDesktopRenderContractReport,
) -> str:
    if render_contract.render_contract_status == "blocked":
        return "blocked"
    if render_contract.render_contract_status == "review-needed":
        return "review-needed"
    return "ready"


def _replay_status(replay_commands: tuple[str, ...]) -> str:
    if not replay_commands:
        return "review-needed"
    if not replay_commands[0].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-desktop-render-harness-report"
    ):
        return "review-needed"
    return "ready"


def _harness_assertions(
    render_contract: StylePerformanceArcLiveGuiDesktopRenderContractReport,
    *,
    surface_harnesses: tuple[StylePerformanceArcLiveGuiDesktopSurfaceHarness, ...],
    binding_harnesses: tuple[StylePerformanceArcLiveGuiDesktopBindingHarness, ...],
    style_token_checks: tuple[StylePerformanceArcLiveGuiDesktopStyleTokenCheck, ...],
    replay_commands: tuple[str, ...],
) -> tuple[StylePerformanceArcLiveGuiDesktopHarnessAssertion, ...]:
    return (
        _assertion(
            assertion_key="assert-render-contract-status",
            label="Desktop render-contract status",
            status=_render_contract_status_for_assertion(render_contract),
            source_id=render_contract.render_contract_id,
            message=(
                f"Desktop render-contract status is " f"{render_contract.render_contract_status}."
            ),
            operator_action="resolve render-contract blockers before GUI harness work",
        ),
        _assertion(
            assertion_key="assert-surface-harness-coverage",
            label="Surface harness coverage",
            status=_coverage_status(len(surface_harnesses)),
            source_id=render_contract.render_contract_id,
            message=f"{len(surface_harnesses)} surface harnesses are available.",
            operator_action="keep surface harnesses declarative until GUI implementation",
        ),
        _assertion(
            assertion_key="assert-binding-harness-coverage",
            label="Binding harness coverage",
            status=_coverage_status(len(binding_harnesses)),
            source_id=render_contract.render_contract_id,
            message=f"{len(binding_harnesses)} binding harnesses are available.",
            operator_action="do not evaluate bindings from the passive CLI",
        ),
        _assertion(
            assertion_key="assert-style-token-check-coverage",
            label="Style-token check coverage",
            status=_coverage_status(len(style_token_checks)),
            source_id=render_contract.render_contract_id,
            message=f"{len(style_token_checks)} style-token checks are available.",
            operator_action="do not inject styles from the passive CLI",
        ),
        _assertion(
            assertion_key="assert-replay-command",
            label="Desktop render-harness replay command",
            status=_replay_status(replay_commands),
            source_id=render_contract.render_contract_id,
            message=(
                "Desktop render-harness replay command is available."
                if replay_commands
                else "Desktop render-harness replay command is missing."
            ),
            operator_action="review command wiring before GUI harness implementation",
        ),
        _assertion(
            assertion_key="assert-no-runner-execution",
            label="No runner execution",
            status="ready",
            source_id=render_contract.render_contract_id,
            message="Desktop render harness remains metadata only.",
            operator_action="do not run GUI, browser, test harness, or screenshot tooling",
        ),
        _assertion(
            assertion_key="assert-passive-boundary",
            label="Passive boundary",
            status="ready",
            source_id=render_contract.render_contract_id,
            message="Desktop render harness emits metadata only.",
            operator_action="do not launch GUI, audio analysis, or MIDI hardware",
        ),
    )


def _render_harness_status(
    render_contract: StylePerformanceArcLiveGuiDesktopRenderContractReport,
    assertions: tuple[StylePerformanceArcLiveGuiDesktopHarnessAssertion, ...],
) -> str:
    if render_contract.render_contract_status == "blocked":
        return "blocked"
    if any(assertion.status == "blocked" for assertion in assertions):
        return "blocked"
    if render_contract.render_contract_status == "review-needed":
        return "review-needed"
    if any(assertion.status == "review-needed" for assertion in assertions):
        return "review-needed"
    return "ready"


def _blocked_actions(
    render_contract: StylePerformanceArcLiveGuiDesktopRenderContractReport,
    render_harness_status: str,
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
        "no browser automation execution",
        "no screenshot capture",
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
    for action in render_contract.blocked_actions:
        if action not in actions:
            actions.append(action)
    if render_harness_status != "ready":
        actions.insert(0, "hold render harness until desktop render contract is clear")
    return tuple(actions)


def _render_harness_id(
    render_contract: StylePerformanceArcLiveGuiDesktopRenderContractReport,
    *,
    render_harness_label: str,
    runner_label: str,
    render_harness_status: str,
) -> str:
    payload = "|".join(
        (
            DESKTOP_RENDER_HARNESS_VERSION,
            render_contract.render_contract_id,
            render_contract.view_model_id,
            render_contract.selected_arc_key,
            render_contract.scope,
            render_contract.framework_target,
            render_harness_label,
            runner_label,
            render_harness_status,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _replace_replay_command(
    command: str,
    *,
    render_harness_label: str,
    runner_label: str,
) -> str | None:
    return replace_replay_command(
        command,
        source_command="style-performance-arc-live-gui-desktop-render-contract-report",
        target_command="style-performance-arc-live-gui-desktop-render-harness-report",
        extra_options=(
            ("--render-harness-label", render_harness_label),
            ("--runner-label", runner_label),
        ),
    )


def _replay_commands(
    render_contract: StylePerformanceArcLiveGuiDesktopRenderContractReport,
    *,
    render_harness_label: str,
    runner_label: str,
) -> tuple[str, ...]:
    if not render_contract.replay_commands:
        return ()
    render_harness_command = _replace_replay_command(
        render_contract.replay_commands[0],
        render_harness_label=render_harness_label,
        runner_label=runner_label,
    )
    if render_harness_command is None:
        return render_contract.replay_commands
    return (render_harness_command, *render_contract.replay_commands)


def build_style_performance_arc_live_gui_desktop_render_harness_from_render_contract(
    render_contract: StylePerformanceArcLiveGuiDesktopRenderContractReport,
    *,
    render_harness_label: str = _DEFAULT_RENDER_HARNESS_LABEL,
    runner_label: str = _DEFAULT_RUNNER_LABEL,
) -> StylePerformanceArcLiveGuiDesktopRenderHarnessReport:
    """Build a passive desktop render harness from render-contract metadata."""

    normalized_harness_label = _normalize_nonblank(
        render_harness_label,
        field="render_harness_label",
    )
    normalized_runner_label = _normalize_nonblank(runner_label, field="runner_label")
    surface_harnesses = _surface_harnesses(render_contract)
    binding_harnesses = _binding_harnesses(render_contract, surface_harnesses)
    style_token_checks = _style_token_checks(render_contract)
    replay_commands = _replay_commands(
        render_contract,
        render_harness_label=normalized_harness_label,
        runner_label=normalized_runner_label,
    )
    harness_assertions = _harness_assertions(
        render_contract,
        surface_harnesses=surface_harnesses,
        binding_harnesses=binding_harnesses,
        style_token_checks=style_token_checks,
        replay_commands=replay_commands,
    )
    render_harness_status = _render_harness_status(render_contract, harness_assertions)
    return StylePerformanceArcLiveGuiDesktopRenderHarnessReport(
        render_contract=render_contract,
        render_harness_version=DESKTOP_RENDER_HARNESS_VERSION,
        render_harness_id=_render_harness_id(
            render_contract,
            render_harness_label=normalized_harness_label,
            runner_label=normalized_runner_label,
            render_harness_status=render_harness_status,
        ),
        render_harness_label=normalized_harness_label,
        runner_label=normalized_runner_label,
        render_harness_status=render_harness_status,
        framework_target=render_contract.framework_target,
        surface_harness_summary=(
            f"{len(surface_harnesses)} surface harnesses for future desktop GUI."
        ),
        binding_harness_summary=(
            f"{len(binding_harnesses)} binding harnesses for future desktop GUI."
        ),
        style_token_check_summary=(
            f"{len(style_token_checks)} style-token checks for future desktop GUI."
        ),
        assertion_summary=f"{len(harness_assertions)} harness assertions for future GUI.",
        surface_harnesses=surface_harnesses,
        binding_harnesses=binding_harnesses,
        style_token_checks=style_token_checks,
        harness_assertions=harness_assertions,
        blocked_actions=_blocked_actions(render_contract, render_harness_status),
        replay_commands=replay_commands,
    )


def build_style_performance_arc_live_gui_desktop_render_harness_report(
    **options: object,
) -> StylePerformanceArcLiveGuiDesktopRenderHarnessReport:
    """Build one passive desktop render-harness report."""

    render_harness_label = str(options.pop("render_harness_label", _DEFAULT_RENDER_HARNESS_LABEL))
    runner_label = str(options.pop("runner_label", _DEFAULT_RUNNER_LABEL))
    render_contract = build_style_performance_arc_live_gui_desktop_render_contract_report(**options)
    return build_style_performance_arc_live_gui_desktop_render_harness_from_render_contract(
        render_contract,
        render_harness_label=render_harness_label,
        runner_label=runner_label,
    )


def _surface_harness_json(
    surface: StylePerformanceArcLiveGuiDesktopSurfaceHarness,
) -> dict[str, object]:
    return {
        "harness_key": surface.harness_key,
        "order": surface.order,
        "render_surface_key": surface.render_surface_key,
        "component_key": surface.component_key,
        "label": surface.label,
        "selector": surface.selector,
        "test_id": surface.test_id,
        "state_key": surface.state_key,
        "fixture_key": surface.fixture_key,
        "assertion_key": surface.assertion_key,
        "mount_policy": surface.mount_policy,
        "runner_enabled": surface.runner_enabled,
        "passive": surface.passive,
    }


def _binding_harness_json(
    binding: StylePerformanceArcLiveGuiDesktopBindingHarness,
) -> dict[str, object]:
    return {
        "binding_key": binding.binding_key,
        "order": binding.order,
        "render_binding_key": binding.render_binding_key,
        "surface_harness_key": binding.surface_harness_key,
        "component_key": binding.component_key,
        "state_key": binding.state_key,
        "prop_name": binding.prop_name,
        "source_json_key": binding.source_json_key,
        "assertion_key": binding.assertion_key,
        "evaluation_policy": binding.evaluation_policy,
        "passive": binding.passive,
    }


def _style_token_check_json(
    check: StylePerformanceArcLiveGuiDesktopStyleTokenCheck,
) -> dict[str, object]:
    return {
        "check_key": check.check_key,
        "order": check.order,
        "token_key": check.token_key,
        "label": check.label,
        "framework_target": check.framework_target,
        "target_surface": check.target_surface,
        "check_policy": check.check_policy,
        "passive": check.passive,
    }


def _assertion_json(
    assertion: StylePerformanceArcLiveGuiDesktopHarnessAssertion,
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


def to_style_performance_arc_live_gui_desktop_render_harness_json(
    report: StylePerformanceArcLiveGuiDesktopRenderHarnessReport,
) -> dict[str, object]:
    """Return deterministic JSON for a passive desktop render harness."""

    render_contract_json = to_style_performance_arc_live_gui_desktop_render_contract_json(
        report.render_contract
    )
    return {
        "live_gui_desktop_render_harness": {
            "render_harness_version": report.render_harness_version,
            "render_harness_id": report.render_harness_id,
            "render_harness_label": report.render_harness_label,
            "runner_label": report.runner_label,
            "render_harness_status": report.render_harness_status,
            "framework_target": report.framework_target,
            "render_contract_id": report.render_contract_id,
            "view_model_id": report.view_model_id,
            "component_contract_id": report.component_contract_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "surface_harness_summary": report.surface_harness_summary,
            "binding_harness_summary": report.binding_harness_summary,
            "style_token_check_summary": report.style_token_check_summary,
            "assertion_summary": report.assertion_summary,
            "surface_harnesses": [
                _surface_harness_json(surface) for surface in report.surface_harnesses
            ],
            "binding_harnesses": [
                _binding_harness_json(binding) for binding in report.binding_harnesses
            ],
            "style_token_checks": [
                _style_token_check_json(check) for check in report.style_token_checks
            ],
            "harness_assertions": [
                _assertion_json(assertion) for assertion in report.harness_assertions
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **render_contract_json,
        "safety": list(SAFETY_LINES),
    }


def _surface_harness_lines(
    surface: StylePerformanceArcLiveGuiDesktopSurfaceHarness,
) -> list[str]:
    return [
        f"- {surface.order}. {surface.harness_key}: {surface.label}",
        f"  Render surface: {surface.render_surface_key}",
        f"  Component: {surface.component_key}",
        f"  Selector: {surface.selector}",
        f"  Test id: {surface.test_id}",
        f"  State key: {surface.state_key}",
        f"  Fixture: {surface.fixture_key}",
        f"  Assertion: {surface.assertion_key}",
        f"  Mount policy: {surface.mount_policy}",
        f"  Runner enabled: {surface.runner_enabled}",
        f"  Passive: {surface.passive}",
    ]


def _binding_harness_lines(
    binding: StylePerformanceArcLiveGuiDesktopBindingHarness,
) -> list[str]:
    return [
        f"- {binding.order}. {binding.binding_key}",
        f"  Render binding: {binding.render_binding_key}",
        f"  Surface harness: {binding.surface_harness_key}",
        f"  Component: {binding.component_key}",
        f"  State key: {binding.state_key}",
        f"  Prop: {binding.prop_name}",
        f"  Source JSON key: {binding.source_json_key}",
        f"  Assertion: {binding.assertion_key}",
        f"  Evaluation policy: {binding.evaluation_policy}",
        f"  Passive: {binding.passive}",
    ]


def _style_token_check_lines(
    check: StylePerformanceArcLiveGuiDesktopStyleTokenCheck,
) -> list[str]:
    return [
        f"- {check.order}. {check.check_key}: {check.label}",
        f"  Token: {check.token_key}",
        f"  Framework target: {check.framework_target}",
        f"  Target surface: {check.target_surface}",
        f"  Check policy: {check.check_policy}",
        f"  Passive: {check.passive}",
    ]


def _assertion_lines(assertion: StylePerformanceArcLiveGuiDesktopHarnessAssertion) -> list[str]:
    return [
        f"- {assertion.assertion_key}: {assertion.label}",
        f"  Status: {assertion.status}",
        f"  Severity: {assertion.severity}",
        f"  Source id: {assertion.source_id}",
        f"  Message: {assertion.message}",
        f"  Operator action: {assertion.operator_action}",
        f"  Passive: {assertion.passive}",
    ]


def format_style_performance_arc_live_gui_desktop_render_harness_report(
    report: StylePerformanceArcLiveGuiDesktopRenderHarnessReport,
) -> list[str]:
    """Format a passive desktop render-harness report."""

    lines = [
        "Live GUI desktop render harness summary:",
        f"- Render harness id: {report.render_harness_id}",
        f"- Render harness label: {report.render_harness_label}",
        f"- Runner label: {report.runner_label}",
        f"- Render harness status: {report.render_harness_status}",
        f"- Framework target: {report.framework_target}",
        f"- Render contract id: {report.render_contract_id}",
        f"- View model id: {report.view_model_id}",
        f"- Component contract id: {report.component_contract_id}",
        f"- Selected arc: {report.selected_arc_name} ({report.selected_arc_key})",
        f"- Scope: {report.scope}",
        f"- Surface harness summary: {report.surface_harness_summary}",
        f"- Binding harness summary: {report.binding_harness_summary}",
        f"- Style-token check summary: {report.style_token_check_summary}",
        f"- Assertion summary: {report.assertion_summary}",
        "Surface harnesses:",
    ]
    for surface in report.surface_harnesses:
        lines.extend(_surface_harness_lines(surface))
    lines.append("Binding harnesses:")
    for binding in report.binding_harnesses:
        lines.extend(_binding_harness_lines(binding))
    lines.append("Style-token checks:")
    for check in report.style_token_checks:
        lines.extend(_style_token_check_lines(check))
    lines.append("Harness assertions:")
    for assertion in report.harness_assertions:
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


def parse_style_performance_arc_live_gui_desktop_render_harness_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Parse desktop render-harness CLI args for passive report composition."""

    render_harness_label = _DEFAULT_RENDER_HARNESS_LABEL
    runner_label = _DEFAULT_RUNNER_LABEL
    render_contract_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--render-harness-label":
            render_harness_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="render_harness_label",
            )
        elif option == "--runner-label":
            runner_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="runner_label",
            )
        else:
            render_contract_args.append(option)
            if option != "--json":
                render_contract_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_desktop_render_contract_cli_args(
        render_contract_args
    )
    parsed["render_harness_label"] = render_harness_label
    parsed["runner_label"] = runner_label
    return parsed


def _handle_cli_report(**options: object) -> int:
    json_output = options.pop("json_output", False)
    try:
        report = build_style_performance_arc_live_gui_desktop_render_harness_report(**options)
        if json_output is True:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_desktop_render_harness_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_desktop_render_harness_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_RENDER_HARNESS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-desktop-render-harness-report",
    summary="Compose passive GUI desktop render contracts into render-harness metadata.",
    args_parser=parse_style_performance_arc_live_gui_desktop_render_harness_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_RENDER_HARNESS_CLI_COMMAND)

__all__ = [
    "DESKTOP_RENDER_HARNESS_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_RENDER_HARNESS_CLI_COMMAND",
    "StylePerformanceArcLiveGuiDesktopBindingHarness",
    "StylePerformanceArcLiveGuiDesktopHarnessAssertion",
    "StylePerformanceArcLiveGuiDesktopRenderHarnessReport",
    "StylePerformanceArcLiveGuiDesktopStyleTokenCheck",
    "StylePerformanceArcLiveGuiDesktopSurfaceHarness",
    "build_style_performance_arc_live_gui_desktop_render_harness_from_render_contract",
    "build_style_performance_arc_live_gui_desktop_render_harness_report",
    "format_style_performance_arc_live_gui_desktop_render_harness_report",
    "parse_style_performance_arc_live_gui_desktop_render_harness_cli_args",
    "to_style_performance_arc_live_gui_desktop_render_harness_json",
]
