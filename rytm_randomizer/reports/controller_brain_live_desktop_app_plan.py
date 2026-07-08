"""Passive desktop app-plan metadata for future controller-brain Cockpit work."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from .controller_brain_live_desktop_blueprint import (
    DESKTOP_BLUEPRINT_STATUS,
    DESKTOP_BLUEPRINT_VERSION,
    ControllerBrainDesktopComponentContract,
    ControllerBrainDesktopRegion,
    build_controller_brain_live_desktop_blueprint_report,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain live desktop app plan"
SOURCE_MODULE: Final[str] = "reports.controller_brain_live_desktop_app_plan"
DESKTOP_APP_PLAN_VERSION: Final[str] = "controller-brain-live-desktop-app-plan-v1"
DESKTOP_APP_PLAN_STATUS: Final[str] = "desktop-app-plan-passive"
SOURCE_DESKTOP_BLUEPRINT_REPORT: Final[str] = "controller-brain-live-desktop-blueprint-report"
_DEFAULT_APP_PLAN_LABEL: Final[str] = "Controller brain desktop app plan"
_DEFAULT_FRAMEWORK_TARGET: Final[str] = "desktop-python"
_FRAMEWORK_TARGETS: Final[tuple[str, ...]] = (
    "desktop-python",
    "web-desktop",
    "test-harness",
)
_ARG_ERROR: Final[str] = (
    "controller-brain-live-desktop-app-plan-report accepts --json, --app-plan-label, "
    "and --framework-target only"
)
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-brain desktop app plan metadata only",
    "composes controller-brain desktop blueprint only",
    "app routes are declarative metadata only",
    "component file hints are advisory metadata only",
    "state slices are declarative metadata only",
    "style tokens are declarative metadata only",
    "acceptance checks are metadata only",
    "JSON/stdout only",
    "no GUI launch",
    "no app launch",
    "no GUI renderer start",
    "no runtime reducer execution",
    "no WebSocket dispatch",
    "no controller feedback emission",
    "no MIDI controller output",
    "no MIDI sending",
    "no port opening",
    "no snapshot mutation",
    "no file writing",
    "no hardware mutation",
    "no hardware required",
)
BASE_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "launch Cockpit GUI runtime",
    "launch desktop app shell",
    "start GUI renderer",
    "mount desktop routes",
    "write component files",
    "execute live state reducer",
    "dispatch Cockpit WebSocket commands",
    "emit controller feedback",
    "open MIDI output",
    "mutate a snapshot",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-live-desktop-app-plan-report",
    "python -m rytm_randomizer.cli controller-brain-live-desktop-app-plan-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-desktop-blueprint-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-implementation-bridge-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainDesktopAppRoute:
    """One disabled future app route derived from a desktop blueprint region."""

    route_key: str
    order: int
    label: str
    source_region_key: str
    layout_area: str
    shell_target: str
    status: str
    enabled: bool
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopComponentFileHint:
    """One advisory future component-file hint that writes no file."""

    component_file_key: str
    order: int
    source_component_key: str
    route_key: str
    suggested_module: str
    component_type: str
    status: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopStateSlice:
    """One disabled future state-slice binding."""

    state_slice_key: str
    order: int
    source_component_key: str
    source_view_model_path: str
    reducer_hint: str
    initial_state: str
    enabled: bool
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopStyleToken:
    """One future style token for a controller-brain desktop shell."""

    token_key: str
    order: int
    label: str
    token_type: str
    value_hint: str
    framework_target: str
    status: str
    passive: bool


@dataclass(frozen=True)
class ControllerBrainDesktopAppAcceptanceCheck:
    """One passive app-plan acceptance check."""

    check_key: str
    order: int
    status: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainLiveDesktopAppPlanReport:
    """Passive desktop app-plan metadata derived from the desktop blueprint."""

    title: str
    desktop_app_plan_version: str
    desktop_app_plan_status: str
    session_label: str
    app_plan_label: str
    framework_target: str
    source_report: str
    source_desktop_blueprint_version: str
    source_desktop_blueprint_status: str
    source_region_count: int
    source_component_contract_count: int
    app_routes: tuple[ControllerBrainDesktopAppRoute, ...]
    component_file_hints: tuple[ControllerBrainDesktopComponentFileHint, ...]
    state_slices: tuple[ControllerBrainDesktopStateSlice, ...]
    style_tokens: tuple[ControllerBrainDesktopStyleToken, ...]
    acceptance_checks: tuple[ControllerBrainDesktopAppAcceptanceCheck, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def route_count(self) -> int:
        """Return future app route count for summaries and JSON."""

        return _desktop_app_plan_count(self.app_routes)

    @property
    def component_file_hint_count(self) -> int:
        """Return component file hint count for summaries and JSON."""

        return _desktop_app_plan_count(self.component_file_hints)

    @property
    def state_slice_count(self) -> int:
        """Return state slice count for summaries and JSON."""

        return _desktop_app_plan_count(self.state_slices)

    @property
    def style_token_count(self) -> int:
        """Return style token count for summaries and JSON."""

        return _desktop_app_plan_count(self.style_tokens)

    @property
    def acceptance_check_count(self) -> int:
        """Return acceptance check count for summaries and JSON."""

        return _desktop_app_plan_count(self.acceptance_checks)


def _desktop_app_plan_unique_tuple(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return tuple(values)


def _desktop_app_plan_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def _desktop_app_plan_count(values: Sequence[object]) -> int:
    return len(values)


def _normalize_app_plan_label(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("app_plan_label must not be blank")
    return normalized


def _normalize_desktop_app_plan_framework_target(value: str) -> str:
    normalized = value.strip()
    if normalized not in _FRAMEWORK_TARGETS:
        raise ValueError("framework_target must be desktop-python, web-desktop, or test-harness")
    return normalized


def _route_key_from_region_key(region_key: str) -> str:
    return f"desktop.route.{region_key.removeprefix('desktop.region.')}"


def _component_file_key_from_component_key(component_key: str) -> str:
    suffix = component_key.removeprefix("desktop.component.")
    return f"desktop.file.component.{suffix}"


def _state_slice_key_from_component_key(component_key: str) -> str:
    suffix = component_key.removeprefix("desktop.component.")
    return f"desktop.state.{suffix}"


def _component_module_from_component_key(component_key: str) -> str:
    suffix = component_key.removeprefix("desktop.component.")
    module_slug = suffix.replace(".", "_").replace("-", "_")
    return f"future_controller_brain/components/{module_slug}.py"


def _reducer_hint_from_component_key(component_key: str) -> str:
    suffix = component_key.removeprefix("desktop.component.")
    return f"reduce-{_desktop_app_plan_slug(suffix)}"


def _app_route_from_region(region: ControllerBrainDesktopRegion) -> ControllerBrainDesktopAppRoute:
    return ControllerBrainDesktopAppRoute(
        route_key=_route_key_from_region_key(region.region_key),
        order=region.order,
        label=region.label,
        source_region_key=region.region_key,
        layout_area=region.layout_area,
        shell_target="operator-dashboard",
        status="disabled-route-ready",
        enabled=False,
        passive=True,
        evidence=f"{region.region_key} is mapped as a disabled future app route",
        blocked_action="mount desktop routes",
    )


def _component_file_hint_from_component(
    component: ControllerBrainDesktopComponentContract,
) -> ControllerBrainDesktopComponentFileHint:
    return ControllerBrainDesktopComponentFileHint(
        component_file_key=_component_file_key_from_component_key(component.component_key),
        order=component.order,
        source_component_key=component.component_key,
        route_key=_route_key_from_region_key(component.region_key),
        suggested_module=_component_module_from_component_key(component.component_key),
        component_type="controller-brain-card",
        status="component-file-hint-ready",
        passive=True,
        evidence=f"{component.component_key} can become a future disabled component file",
        blocked_action="write component files",
    )


def _state_slice_from_component(
    component: ControllerBrainDesktopComponentContract,
) -> ControllerBrainDesktopStateSlice:
    return ControllerBrainDesktopStateSlice(
        state_slice_key=_state_slice_key_from_component_key(component.component_key),
        order=component.order,
        source_component_key=component.component_key,
        source_view_model_path=component.view_model_path,
        reducer_hint=_reducer_hint_from_component_key(component.component_key),
        initial_state="disabled",
        enabled=False,
        passive=True,
        evidence=f"{component.component_key} remains a disabled future state slice",
        blocked_action="execute live state reducer",
    )


def _controller_brain_desktop_app_style_tokens(
    *,
    framework_target: str,
) -> tuple[ControllerBrainDesktopStyleToken, ...]:
    rows = (
        ("controller-brain.color.surface", "Surface", "color", "near-black cockpit base"),
        ("controller-brain.color.panel", "Panel", "color", "low-contrast panel fill"),
        ("controller-brain.color.accent", "Accent", "color", "cyan/green operator accent"),
        ("controller-brain.color.warning", "Warning", "color", "amber blocked-action warning"),
        ("controller-brain.spacing.grid", "Grid", "spacing", "dense 12-pad cockpit grid"),
        ("controller-brain.motion.disabled", "Motion Disabled", "motion", "no runtime animation"),
    )
    return tuple(
        ControllerBrainDesktopStyleToken(
            token_key=token_key,
            order=index + 1,
            label=label,
            token_type=token_type,
            value_hint=value_hint,
            framework_target=framework_target,
            status="style-token-ready",
            passive=True,
        )
        for index, (token_key, label, token_type, value_hint) in enumerate(rows)
    )


def _controller_brain_desktop_app_acceptance_checks() -> (
    tuple[ControllerBrainDesktopAppAcceptanceCheck, ...]
):
    rows = (
        (
            "source-blueprint-ready",
            "source desktop blueprint is available as passive JSON",
            "mount desktop routes",
        ),
        (
            "route-coverage",
            "every desktop region has one disabled future app route",
            "mount desktop routes",
        ),
        (
            "component-file-hint-coverage",
            "every component contract has one advisory component file hint",
            "write component files",
        ),
        (
            "state-slice-coverage",
            "every component contract has one disabled state slice",
            "execute live state reducer",
        ),
        (
            "style-token-coverage",
            "style tokens are declared as metadata only",
            "start GUI renderer",
        ),
        (
            "replay-command",
            "operator replay commands remain copy-ready passive CLI commands",
            "dispatch Cockpit WebSocket commands",
        ),
        (
            "passive-boundary",
            "desktop app plan launches no GUI, writes no files, opens no ports, and sends no MIDI",
            "open MIDI output",
        ),
    )
    return tuple(
        ControllerBrainDesktopAppAcceptanceCheck(
            check_key=key,
            order=index + 1,
            status="ready",
            passive=True,
            evidence=evidence,
            blocked_action=blocked_action,
        )
        for index, (key, evidence, blocked_action) in enumerate(rows)
    )


def build_controller_brain_live_desktop_app_plan_report(
    *,
    session_label: str = "Live Session",
    app_plan_label: str = _DEFAULT_APP_PLAN_LABEL,
    framework_target: str = _DEFAULT_FRAMEWORK_TARGET,
) -> ControllerBrainLiveDesktopAppPlanReport:
    """Build passive future desktop app-plan metadata from the desktop blueprint."""

    normalized_label = _normalize_app_plan_label(app_plan_label)
    normalized_framework = _normalize_desktop_app_plan_framework_target(framework_target)
    blueprint = build_controller_brain_live_desktop_blueprint_report(session_label=session_label)
    return ControllerBrainLiveDesktopAppPlanReport(
        title=REPORT_TITLE,
        desktop_app_plan_version=DESKTOP_APP_PLAN_VERSION,
        desktop_app_plan_status=DESKTOP_APP_PLAN_STATUS,
        session_label=session_label,
        app_plan_label=normalized_label,
        framework_target=normalized_framework,
        source_report=SOURCE_DESKTOP_BLUEPRINT_REPORT,
        source_desktop_blueprint_version=DESKTOP_BLUEPRINT_VERSION,
        source_desktop_blueprint_status=DESKTOP_BLUEPRINT_STATUS,
        source_region_count=blueprint.region_count,
        source_component_contract_count=blueprint.component_contract_count,
        app_routes=tuple(_app_route_from_region(region) for region in blueprint.desktop_regions),
        component_file_hints=tuple(
            _component_file_hint_from_component(component)
            for component in blueprint.component_contracts
        ),
        state_slices=tuple(
            _state_slice_from_component(component) for component in blueprint.component_contracts
        ),
        style_tokens=_controller_brain_desktop_app_style_tokens(
            framework_target=normalized_framework
        ),
        acceptance_checks=_controller_brain_desktop_app_acceptance_checks(),
        blocked_actions=_desktop_app_plan_unique_tuple(
            BASE_BLOCKED_ACTIONS,
            blueprint.blocked_actions,
        ),
        safety_lines=_desktop_app_plan_unique_tuple(
            BASE_SAFETY_LINES,
            blueprint.safety_lines,
        ),
        replay_commands=REPLAY_COMMANDS,
    )


def _app_route_to_payload(route: ControllerBrainDesktopAppRoute) -> dict[str, object]:
    return {
        "route_key": route.route_key,
        "order": route.order,
        "label": route.label,
        "source_region_key": route.source_region_key,
        "layout_area": route.layout_area,
        "shell_target": route.shell_target,
        "status": route.status,
        "enabled": route.enabled,
        "passive": route.passive,
        "evidence": route.evidence,
        "blocked_action": route.blocked_action,
    }


def _component_file_hint_to_payload(
    hint: ControllerBrainDesktopComponentFileHint,
) -> dict[str, object]:
    return {
        "component_file_key": hint.component_file_key,
        "order": hint.order,
        "source_component_key": hint.source_component_key,
        "route_key": hint.route_key,
        "suggested_module": hint.suggested_module,
        "component_type": hint.component_type,
        "status": hint.status,
        "passive": hint.passive,
        "evidence": hint.evidence,
        "blocked_action": hint.blocked_action,
    }


def _state_slice_to_payload(slice_: ControllerBrainDesktopStateSlice) -> dict[str, object]:
    return {
        "state_slice_key": slice_.state_slice_key,
        "order": slice_.order,
        "source_component_key": slice_.source_component_key,
        "source_view_model_path": slice_.source_view_model_path,
        "reducer_hint": slice_.reducer_hint,
        "initial_state": slice_.initial_state,
        "enabled": slice_.enabled,
        "passive": slice_.passive,
        "evidence": slice_.evidence,
        "blocked_action": slice_.blocked_action,
    }


def _style_token_to_payload(token: ControllerBrainDesktopStyleToken) -> dict[str, object]:
    return {
        "token_key": token.token_key,
        "order": token.order,
        "label": token.label,
        "token_type": token.token_type,
        "value_hint": token.value_hint,
        "framework_target": token.framework_target,
        "status": token.status,
        "passive": token.passive,
    }


def _desktop_app_plan_acceptance_check_to_payload(
    check: ControllerBrainDesktopAppAcceptanceCheck,
) -> dict[str, object]:
    return {
        "check_key": check.check_key,
        "order": check.order,
        "status": check.status,
        "passive": check.passive,
        "evidence": check.evidence,
        "blocked_action": check.blocked_action,
    }


def build_controller_brain_live_desktop_app_plan_payload(
    *,
    session_label: str = "Live Session",
    app_plan_label: str = _DEFAULT_APP_PLAN_LABEL,
    framework_target: str = _DEFAULT_FRAMEWORK_TARGET,
) -> dict[str, object]:
    """Return JSON-ready passive desktop app-plan metadata."""

    report = build_controller_brain_live_desktop_app_plan_report(
        session_label=session_label,
        app_plan_label=app_plan_label,
        framework_target=framework_target,
    )
    return {
        "controller_brain_live_desktop_app_plan": {
            "title": report.title,
            "desktop_app_plan_version": report.desktop_app_plan_version,
            "desktop_app_plan_status": report.desktop_app_plan_status,
            "session_label": report.session_label,
            "app_plan_label": report.app_plan_label,
            "framework_target": report.framework_target,
            "source_report": report.source_report,
            "source_desktop_blueprint_version": report.source_desktop_blueprint_version,
            "source_desktop_blueprint_status": report.source_desktop_blueprint_status,
            "source_region_count": report.source_region_count,
            "source_component_contract_count": report.source_component_contract_count,
            "route_count": report.route_count,
            "component_file_hint_count": report.component_file_hint_count,
            "state_slice_count": report.state_slice_count,
            "style_token_count": report.style_token_count,
            "acceptance_check_count": report.acceptance_check_count,
            "app_routes": [_app_route_to_payload(route) for route in report.app_routes],
            "component_file_hints": [
                _component_file_hint_to_payload(hint) for hint in report.component_file_hints
            ],
            "state_slices": [_state_slice_to_payload(slice_) for slice_ in report.state_slices],
            "style_tokens": [_style_token_to_payload(token) for token in report.style_tokens],
            "acceptance_checks": [
                _desktop_app_plan_acceptance_check_to_payload(check)
                for check in report.acceptance_checks
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def _format_desktop_app_plan_body(
    report: ControllerBrainLiveDesktopAppPlanReport,
) -> list[str]:
    lines = [
        "Controller brain live desktop app plan:",
        f"- version: {report.desktop_app_plan_version}",
        f"- status: {report.desktop_app_plan_status}",
        f"- session: {report.session_label}",
        f"- app plan label: {report.app_plan_label}",
        f"- framework target: {report.framework_target}",
        f"- source desktop blueprint: {report.source_report}",
        f"- source desktop blueprint version: {report.source_desktop_blueprint_version}",
        f"- source desktop blueprint status: {report.source_desktop_blueprint_status}",
        f"- source desktop regions: {report.source_region_count}",
        f"- source component contracts: {report.source_component_contract_count}",
        f"- app routes: {report.route_count}",
        f"- component file hints: {report.component_file_hint_count}",
        f"- state slices: {report.state_slice_count}",
        f"- style tokens: {report.style_token_count}",
        f"- acceptance checks: {report.acceptance_check_count}",
        "App routes:",
    ]
    for route in report.app_routes:
        lines.append(f"- {route.route_key}: {route.label}")
        lines.append(f"  source region: {route.source_region_key}")
        lines.append(f"  layout area: {route.layout_area}")
        lines.append(f"  shell target: {route.shell_target}")
        lines.append(f"  enabled: {route.enabled}")
        lines.append(f"  passive: {route.passive}")
        lines.append(f"  blocked: {route.blocked_action}")
    lines.append("Component file hints:")
    for hint in report.component_file_hints:
        lines.append(f"- {hint.component_file_key}: {hint.status}")
        lines.append(f"  source component: {hint.source_component_key}")
        lines.append(f"  route: {hint.route_key}")
        lines.append(f"  suggested module: {hint.suggested_module}")
        lines.append(f"  passive: {hint.passive}")
        lines.append(f"  blocked: {hint.blocked_action}")
    lines.append("State slices:")
    for slice_ in report.state_slices:
        lines.append(f"- {slice_.state_slice_key}: {slice_.initial_state}")
        lines.append(f"  source component: {slice_.source_component_key}")
        lines.append(f"  view model: {slice_.source_view_model_path}")
        lines.append(f"  reducer hint: {slice_.reducer_hint}")
        lines.append(f"  enabled: {slice_.enabled}")
        lines.append(f"  passive: {slice_.passive}")
    lines.append("Style tokens:")
    for token in report.style_tokens:
        lines.append(f"- {token.token_key}: {token.label}")
        lines.append(f"  type: {token.token_type}")
        lines.append(f"  framework target: {token.framework_target}")
        lines.append(f"  passive: {token.passive}")
    lines.append("Acceptance checks:")
    for check in report.acceptance_checks:
        lines.append(f"- {check.check_key}: {check.status}")
        lines.append(f"  passive: {check.passive}")
        lines.append(f"  evidence: {check.evidence}")
        lines.append(f"  blocked: {check.blocked_action}")
    lines.append("Blocked active actions:")
    lines.extend(f"- {action}" for action in report.blocked_actions)
    lines.append("Replay commands:")
    lines.extend(f"- {command}" for command in report.replay_commands)
    lines.append("Safety:")
    lines.extend(f"- {line}" for line in report.safety_lines)
    return lines


def format_controller_brain_live_desktop_app_plan_report(
    report: ControllerBrainLiveDesktopAppPlanReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing desktop app-plan text."""

    source = build_controller_brain_live_desktop_app_plan_report() if report is None else report
    return passive_report_lines(_HEADER, _format_desktop_app_plan_body(source))


def _pop_cli_value(remaining: list[str]) -> str:
    if not remaining:
        raise ValueError(_ARG_ERROR)
    return remaining.pop(0)


def _parse_desktop_app_plan_cli_args(argv: Sequence[str]) -> dict[str, object]:
    app_plan_label = _DEFAULT_APP_PLAN_LABEL
    framework_target = _DEFAULT_FRAMEWORK_TARGET
    json_output = False
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
        elif option == "--app-plan-label":
            app_plan_label = _normalize_app_plan_label(_pop_cli_value(remaining))
        elif option == "--framework-target":
            framework_target = _normalize_desktop_app_plan_framework_target(
                _pop_cli_value(remaining)
            )
        else:
            raise ValueError(_ARG_ERROR)
    return {
        "app_plan_label": app_plan_label,
        "framework_target": framework_target,
        "json_output": json_output,
    }


def _handle_desktop_app_plan_report(
    *,
    app_plan_label: str,
    framework_target: str,
    json_output: bool,
) -> int:
    if json_output:
        sys.stdout.write(
            json.dumps(
                build_controller_brain_live_desktop_app_plan_payload(
                    app_plan_label=app_plan_label,
                    framework_target=framework_target,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0
    report = build_controller_brain_live_desktop_app_plan_report(
        app_plan_label=app_plan_label,
        framework_target=framework_target,
    )
    sys.stdout.write("\n".join(format_controller_brain_live_desktop_app_plan_report(report)))
    sys.stdout.write("\n")
    return 0


def _format_desktop_app_plan_error(exc: Exception) -> str:
    return f"Error: {exc}"


CONTROLLER_BRAIN_LIVE_DESKTOP_APP_PLAN_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="controller-brain-live-desktop-app-plan-report",
    summary="Print passive controller-brain desktop app-plan routes and file hints.",
    args_parser=_parse_desktop_app_plan_cli_args,
    handler=_handle_desktop_app_plan_report,
    error_formatter=_format_desktop_app_plan_error,
)

register(CONTROLLER_BRAIN_LIVE_DESKTOP_APP_PLAN_CLI_COMMAND)

__all__ = (
    "BASE_BLOCKED_ACTIONS",
    "BASE_SAFETY_LINES",
    "CONTROLLER_BRAIN_LIVE_DESKTOP_APP_PLAN_CLI_COMMAND",
    "ControllerBrainDesktopAppAcceptanceCheck",
    "ControllerBrainDesktopAppRoute",
    "ControllerBrainDesktopComponentFileHint",
    "ControllerBrainDesktopStateSlice",
    "ControllerBrainDesktopStyleToken",
    "ControllerBrainLiveDesktopAppPlanReport",
    "DESKTOP_APP_PLAN_STATUS",
    "DESKTOP_APP_PLAN_VERSION",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SOURCE_DESKTOP_BLUEPRINT_REPORT",
    "SOURCE_MODULE",
    "build_controller_brain_live_desktop_app_plan_payload",
    "build_controller_brain_live_desktop_app_plan_report",
    "format_controller_brain_live_desktop_app_plan_report",
)
