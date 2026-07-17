"""Passive desktop render-contract metadata for future controller-brain Cockpit work."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from .controller_brain_live_desktop_view_model import (
    DESKTOP_VIEW_MODEL_STATUS,
    DESKTOP_VIEW_MODEL_VERSION,
    ControllerBrainDesktopComponentViewModel,
    ControllerBrainDesktopDisabledActionModel,
    ControllerBrainDesktopRenderAssertion,
    ControllerBrainDesktopStateBinding,
    build_controller_brain_live_desktop_view_model_report,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain live desktop render contract"
SOURCE_MODULE: Final[str] = "reports.controller_brain_live_desktop_render_contract"
DESKTOP_RENDER_CONTRACT_VERSION: Final[str] = "controller-brain-live-desktop-render-contract-v1"
DESKTOP_RENDER_CONTRACT_STATUS: Final[str] = "desktop-render-contract-passive"
SOURCE_DESKTOP_VIEW_MODEL_REPORT: Final[str] = "controller-brain-live-desktop-view-model-report"
_DEFAULT_RENDER_CONTRACT_LABEL: Final[str] = "Controller brain desktop render contract"
_DEFAULT_SURFACE_PREFIX: Final[str] = "rr-render"
_ARG_ERROR: Final[str] = (
    "controller-brain-live-desktop-render-contract-report accepts --json, "
    "--render-contract-label, and --surface-prefix only"
)
_SURFACE_PREFIX_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z][a-zA-Z0-9-]*$")
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-brain desktop render contract metadata only",
    "composes controller-brain desktop view model only",
    "render surfaces are declarative metadata only",
    "render bindings are declarative metadata only",
    "render guards are metadata only",
    "render assertions are metadata only",
    "acceptance checks are metadata only",
    "JSON/stdout only",
    "no GUI launch",
    "no app launch",
    "no component mount",
    "no render surface mount",
    "no prop binding execution",
    "no GUI renderer start",
    "no renderer execution",
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
    "mount render surfaces",
    "execute render bindings",
    "dispatch Cockpit WebSocket commands",
    "emit controller feedback",
    "open MIDI output",
    "mutate a snapshot",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-live-desktop-render-contract-report",
    "python -m rytm_randomizer.cli controller-brain-live-desktop-render-contract-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-desktop-view-model-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-desktop-component-contract-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainDesktopRenderSurface:
    """One disabled future render surface."""

    render_surface_key: str
    order: int
    view_model_key: str
    selector: str
    surface_test_id: str
    state_key: str
    component_type: str
    mount_mode: str
    enabled: bool
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopRenderBinding:
    """One passive future render binding."""

    render_binding_key: str
    order: int
    render_surface_key: str
    state_binding_key: str
    view_model_key: str
    prop_name: str
    source_prop_contract_key: str
    fallback_state: str
    binding_mode: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopRenderGuard:
    """One passive future render guard for a disabled action model."""

    render_guard_key: str
    order: int
    render_surface_key: str
    action_model_key: str
    view_model_key: str
    event_name: str
    guard_state: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopRenderContractAssertion:
    """One passive render-contract assertion."""

    render_contract_assertion_key: str
    order: int
    render_surface_key: str
    source_render_assertion_key: str
    view_model_key: str
    test_id: str
    required_state: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopRenderContractAcceptanceCheck:
    """One passive render-contract acceptance check."""

    check_key: str
    order: int
    status: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainLiveDesktopRenderContractReport:
    """Passive render-contract metadata derived from desktop view models."""

    title: str
    desktop_render_contract_version: str
    desktop_render_contract_status: str
    session_label: str
    render_contract_label: str
    surface_prefix: str
    source_report: str
    source_desktop_view_model_version: str
    source_desktop_view_model_status: str
    source_component_view_model_count: int
    source_state_binding_count: int
    source_disabled_action_model_count: int
    render_surfaces: tuple[ControllerBrainDesktopRenderSurface, ...]
    render_bindings: tuple[ControllerBrainDesktopRenderBinding, ...]
    render_guards: tuple[ControllerBrainDesktopRenderGuard, ...]
    render_assertions: tuple[ControllerBrainDesktopRenderContractAssertion, ...]
    acceptance_checks: tuple[ControllerBrainDesktopRenderContractAcceptanceCheck, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def render_surface_count(self) -> int:
        """Return future render surface count for summaries and JSON."""

        return _desktop_render_contract_count(self.render_surfaces)

    @property
    def render_binding_count(self) -> int:
        """Return future render binding count for summaries and JSON."""

        return _desktop_render_contract_count(self.render_bindings)

    @property
    def render_guard_count(self) -> int:
        """Return future render guard count for summaries and JSON."""

        return _desktop_render_contract_count(self.render_guards)

    @property
    def render_assertion_count(self) -> int:
        """Return future render assertion count for summaries and JSON."""

        return _desktop_render_contract_count(self.render_assertions)

    @property
    def acceptance_check_count(self) -> int:
        """Return acceptance check count for summaries and JSON."""

        return _desktop_render_contract_count(self.acceptance_checks)


def _desktop_render_contract_unique_tuple(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return tuple(values)


def _desktop_render_contract_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def _desktop_render_contract_count(values: Sequence[object]) -> int:
    return len(values)


def _normalize_render_contract_label(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("render_contract_label must not be blank")
    return normalized


def _normalize_render_surface_prefix(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("surface_prefix must not be blank")
    if _SURFACE_PREFIX_PATTERN.fullmatch(normalized) is None:
        raise ValueError("surface_prefix must use letters, numbers, and hyphens")
    return normalized


def _render_suffix_from_view_model_key(view_model_key: str) -> str:
    return view_model_key.removeprefix("desktop.viewmodel.")


def _render_surface_key_from_view_model_key(view_model_key: str) -> str:
    suffix = _render_suffix_from_view_model_key(view_model_key)
    return f"desktop.render.surface.{suffix}"


def _render_binding_key_from_view_model_key(view_model_key: str) -> str:
    suffix = _render_suffix_from_view_model_key(view_model_key)
    return f"desktop.render.binding.{suffix}"


def _render_guard_key_from_view_model_key(view_model_key: str) -> str:
    suffix = _render_suffix_from_view_model_key(view_model_key)
    return f"desktop.render.guard.{suffix}"


def _render_assertion_key_from_view_model_key(view_model_key: str) -> str:
    suffix = _render_suffix_from_view_model_key(view_model_key)
    return f"desktop.render.assert.{suffix}"


def _surface_test_id_from_view_model_key(
    view_model_key: str,
    *,
    surface_prefix: str,
) -> str:
    suffix = _desktop_render_contract_slug(_render_suffix_from_view_model_key(view_model_key))
    return f"{surface_prefix}-{suffix}"


def _render_surface_from_view_model(
    view_model: ControllerBrainDesktopComponentViewModel,
    *,
    surface_prefix: str,
) -> ControllerBrainDesktopRenderSurface:
    return ControllerBrainDesktopRenderSurface(
        render_surface_key=_render_surface_key_from_view_model_key(view_model.view_model_key),
        order=view_model.order,
        view_model_key=view_model.view_model_key,
        selector=view_model.selector,
        surface_test_id=_surface_test_id_from_view_model_key(
            view_model.view_model_key,
            surface_prefix=surface_prefix,
        ),
        state_key=view_model.state_key,
        component_type=view_model.component_type,
        mount_mode="disabled-passive",
        enabled=False,
        passive=True,
        evidence=f"{view_model.view_model_key} is mapped to a disabled future render surface",
        blocked_action="mount render surfaces",
    )


def _surface_key_by_view_model(
    render_surfaces: Sequence[ControllerBrainDesktopRenderSurface],
) -> dict[str, str]:
    return {surface.view_model_key: surface.render_surface_key for surface in render_surfaces}


def _render_binding_from_state_binding(
    binding: ControllerBrainDesktopStateBinding,
    *,
    render_surface_key: str,
) -> ControllerBrainDesktopRenderBinding:
    return ControllerBrainDesktopRenderBinding(
        render_binding_key=_render_binding_key_from_view_model_key(binding.view_model_key),
        order=binding.order,
        render_surface_key=render_surface_key,
        state_binding_key=binding.state_binding_key,
        view_model_key=binding.view_model_key,
        prop_name=binding.prop_name,
        source_prop_contract_key=binding.source_prop_contract_key,
        fallback_state=binding.fallback_state,
        binding_mode="one-way-disabled-state-to-render",
        passive=True,
        evidence=f"{binding.state_binding_key} remains a future disabled render binding",
        blocked_action="execute render bindings",
    )


def _render_guard_from_action_model(
    action: ControllerBrainDesktopDisabledActionModel,
    *,
    render_surface_key: str,
) -> ControllerBrainDesktopRenderGuard:
    return ControllerBrainDesktopRenderGuard(
        render_guard_key=_render_guard_key_from_view_model_key(action.view_model_key),
        order=action.order,
        render_surface_key=render_surface_key,
        action_model_key=action.action_model_key,
        view_model_key=action.view_model_key,
        event_name=action.event_name,
        guard_state="blocked",
        passive=True,
        evidence=f"{action.action_model_key} remains guarded before any renderer exists",
        blocked_action=action.blocked_action,
    )


def _render_contract_assertion_from_source(
    assertion: ControllerBrainDesktopRenderAssertion,
    *,
    render_surface_key: str,
) -> ControllerBrainDesktopRenderContractAssertion:
    return ControllerBrainDesktopRenderContractAssertion(
        render_contract_assertion_key=_render_assertion_key_from_view_model_key(
            assertion.view_model_key
        ),
        order=assertion.order,
        render_surface_key=render_surface_key,
        source_render_assertion_key=assertion.render_assertion_key,
        view_model_key=assertion.view_model_key,
        test_id=assertion.test_id,
        required_state=assertion.required_state,
        passive=True,
        evidence=f"{assertion.render_assertion_key} remains a passive renderer assertion",
        blocked_action="start GUI renderer",
    )


def _controller_brain_desktop_render_contract_acceptance_checks() -> (
    tuple[ControllerBrainDesktopRenderContractAcceptanceCheck, ...]
):
    rows = (
        (
            "source-view-model-ready",
            "source desktop view model is available as passive JSON",
            "mount render surfaces",
        ),
        (
            "render-surface-coverage",
            "every component view model has one disabled render surface",
            "mount render surfaces",
        ),
        (
            "render-binding-coverage",
            "every state binding has one disabled render binding",
            "execute render bindings",
        ),
        (
            "render-guard-coverage",
            "every disabled action model has one render guard",
            "dispatch Cockpit WebSocket commands",
        ),
        (
            "render-assertion-coverage",
            "every source render assertion has one render-contract assertion",
            "start GUI renderer",
        ),
        (
            "replay-command",
            "operator replay commands remain copy-ready passive CLI commands",
            "dispatch Cockpit WebSocket commands",
        ),
        (
            "passive-boundary",
            "desktop render contract launches no GUI, writes no files, opens no ports, and sends no MIDI",
            "open MIDI output",
        ),
    )
    return tuple(
        ControllerBrainDesktopRenderContractAcceptanceCheck(
            check_key=key,
            order=index + 1,
            status="ready",
            passive=True,
            evidence=evidence,
            blocked_action=blocked_action,
        )
        for index, (key, evidence, blocked_action) in enumerate(rows)
    )


def build_controller_brain_live_desktop_render_contract_report(
    *,
    session_label: str = "Live Session",
    render_contract_label: str = _DEFAULT_RENDER_CONTRACT_LABEL,
    surface_prefix: str = _DEFAULT_SURFACE_PREFIX,
) -> ControllerBrainLiveDesktopRenderContractReport:
    """Build passive future desktop render-contract metadata from view models."""

    normalized_label = _normalize_render_contract_label(render_contract_label)
    normalized_surface_prefix = _normalize_render_surface_prefix(surface_prefix)
    view_model = build_controller_brain_live_desktop_view_model_report(
        session_label=session_label,
    )
    render_surfaces = tuple(
        _render_surface_from_view_model(
            component_view_model,
            surface_prefix=normalized_surface_prefix,
        )
        for component_view_model in view_model.component_view_models
    )
    surface_key_by_view_model = _surface_key_by_view_model(render_surfaces)
    render_bindings = tuple(
        _render_binding_from_state_binding(
            binding,
            render_surface_key=surface_key_by_view_model[binding.view_model_key],
        )
        for binding in view_model.state_bindings
    )
    render_guards = tuple(
        _render_guard_from_action_model(
            action,
            render_surface_key=surface_key_by_view_model[action.view_model_key],
        )
        for action in view_model.disabled_action_models
    )
    render_assertions = tuple(
        _render_contract_assertion_from_source(
            assertion,
            render_surface_key=surface_key_by_view_model[assertion.view_model_key],
        )
        for assertion in view_model.render_assertions
    )
    return ControllerBrainLiveDesktopRenderContractReport(
        title=REPORT_TITLE,
        desktop_render_contract_version=DESKTOP_RENDER_CONTRACT_VERSION,
        desktop_render_contract_status=DESKTOP_RENDER_CONTRACT_STATUS,
        session_label=session_label,
        render_contract_label=normalized_label,
        surface_prefix=normalized_surface_prefix,
        source_report=SOURCE_DESKTOP_VIEW_MODEL_REPORT,
        source_desktop_view_model_version=DESKTOP_VIEW_MODEL_VERSION,
        source_desktop_view_model_status=DESKTOP_VIEW_MODEL_STATUS,
        source_component_view_model_count=view_model.component_view_model_count,
        source_state_binding_count=view_model.state_binding_count,
        source_disabled_action_model_count=view_model.disabled_action_model_count,
        render_surfaces=render_surfaces,
        render_bindings=render_bindings,
        render_guards=render_guards,
        render_assertions=render_assertions,
        acceptance_checks=_controller_brain_desktop_render_contract_acceptance_checks(),
        blocked_actions=_desktop_render_contract_unique_tuple(
            BASE_BLOCKED_ACTIONS,
            view_model.blocked_actions,
        ),
        safety_lines=_desktop_render_contract_unique_tuple(
            BASE_SAFETY_LINES,
            view_model.safety_lines,
        ),
        replay_commands=REPLAY_COMMANDS,
    )


def _render_surface_to_payload(surface: ControllerBrainDesktopRenderSurface) -> dict[str, object]:
    return {
        "render_surface_key": surface.render_surface_key,
        "order": surface.order,
        "view_model_key": surface.view_model_key,
        "selector": surface.selector,
        "surface_test_id": surface.surface_test_id,
        "state_key": surface.state_key,
        "component_type": surface.component_type,
        "mount_mode": surface.mount_mode,
        "enabled": surface.enabled,
        "passive": surface.passive,
        "evidence": surface.evidence,
        "blocked_action": surface.blocked_action,
    }


def _render_binding_to_payload(binding: ControllerBrainDesktopRenderBinding) -> dict[str, object]:
    return {
        "render_binding_key": binding.render_binding_key,
        "order": binding.order,
        "render_surface_key": binding.render_surface_key,
        "state_binding_key": binding.state_binding_key,
        "view_model_key": binding.view_model_key,
        "prop_name": binding.prop_name,
        "source_prop_contract_key": binding.source_prop_contract_key,
        "fallback_state": binding.fallback_state,
        "binding_mode": binding.binding_mode,
        "passive": binding.passive,
        "evidence": binding.evidence,
        "blocked_action": binding.blocked_action,
    }


def _render_guard_to_payload(guard: ControllerBrainDesktopRenderGuard) -> dict[str, object]:
    return {
        "render_guard_key": guard.render_guard_key,
        "order": guard.order,
        "render_surface_key": guard.render_surface_key,
        "action_model_key": guard.action_model_key,
        "view_model_key": guard.view_model_key,
        "event_name": guard.event_name,
        "guard_state": guard.guard_state,
        "passive": guard.passive,
        "evidence": guard.evidence,
        "blocked_action": guard.blocked_action,
    }


def _render_contract_assertion_to_payload(
    assertion: ControllerBrainDesktopRenderContractAssertion,
) -> dict[str, object]:
    return {
        "render_contract_assertion_key": assertion.render_contract_assertion_key,
        "order": assertion.order,
        "render_surface_key": assertion.render_surface_key,
        "source_render_assertion_key": assertion.source_render_assertion_key,
        "view_model_key": assertion.view_model_key,
        "test_id": assertion.test_id,
        "required_state": assertion.required_state,
        "passive": assertion.passive,
        "evidence": assertion.evidence,
        "blocked_action": assertion.blocked_action,
    }


def _render_contract_acceptance_check_to_payload(
    check: ControllerBrainDesktopRenderContractAcceptanceCheck,
) -> dict[str, object]:
    return {
        "check_key": check.check_key,
        "order": check.order,
        "status": check.status,
        "passive": check.passive,
        "evidence": check.evidence,
        "blocked_action": check.blocked_action,
    }


def build_controller_brain_live_desktop_render_contract_payload(
    *,
    session_label: str = "Live Session",
    render_contract_label: str = _DEFAULT_RENDER_CONTRACT_LABEL,
    surface_prefix: str = _DEFAULT_SURFACE_PREFIX,
) -> dict[str, object]:
    """Return JSON-ready passive desktop render-contract metadata."""

    report = build_controller_brain_live_desktop_render_contract_report(
        session_label=session_label,
        render_contract_label=render_contract_label,
        surface_prefix=surface_prefix,
    )
    return {
        "controller_brain_live_desktop_render_contract": {
            "title": report.title,
            "desktop_render_contract_version": report.desktop_render_contract_version,
            "desktop_render_contract_status": report.desktop_render_contract_status,
            "session_label": report.session_label,
            "render_contract_label": report.render_contract_label,
            "surface_prefix": report.surface_prefix,
            "source_report": report.source_report,
            "source_desktop_view_model_version": (report.source_desktop_view_model_version),
            "source_desktop_view_model_status": report.source_desktop_view_model_status,
            "source_component_view_model_count": (report.source_component_view_model_count),
            "source_state_binding_count": report.source_state_binding_count,
            "source_disabled_action_model_count": (report.source_disabled_action_model_count),
            "render_surface_count": report.render_surface_count,
            "render_binding_count": report.render_binding_count,
            "render_guard_count": report.render_guard_count,
            "render_assertion_count": report.render_assertion_count,
            "acceptance_check_count": report.acceptance_check_count,
            "render_surfaces": [
                _render_surface_to_payload(surface) for surface in report.render_surfaces
            ],
            "render_bindings": [
                _render_binding_to_payload(binding) for binding in report.render_bindings
            ],
            "render_guards": [_render_guard_to_payload(guard) for guard in report.render_guards],
            "render_assertions": [
                _render_contract_assertion_to_payload(assertion)
                for assertion in report.render_assertions
            ],
            "acceptance_checks": [
                _render_contract_acceptance_check_to_payload(check)
                for check in report.acceptance_checks
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def _format_desktop_render_contract_body(
    report: ControllerBrainLiveDesktopRenderContractReport,
) -> list[str]:
    lines = [
        "Controller brain live desktop render contract:",
        f"- version: {report.desktop_render_contract_version}",
        f"- status: {report.desktop_render_contract_status}",
        f"- session: {report.session_label}",
        f"- render contract label: {report.render_contract_label}",
        f"- surface prefix: {report.surface_prefix}",
        f"- source desktop view model: {report.source_report}",
        f"- source desktop view model version: {report.source_desktop_view_model_version}",
        f"- source desktop view model status: {report.source_desktop_view_model_status}",
        f"- source component view models: {report.source_component_view_model_count}",
        f"- source state bindings: {report.source_state_binding_count}",
        f"- source disabled action models: {report.source_disabled_action_model_count}",
        f"- render surfaces: {report.render_surface_count}",
        f"- render bindings: {report.render_binding_count}",
        f"- render guards: {report.render_guard_count}",
        f"- render assertions: {report.render_assertion_count}",
        f"- acceptance checks: {report.acceptance_check_count}",
        "Render surfaces:",
    ]
    for surface in report.render_surfaces:
        lines.append(f"- {surface.render_surface_key}: {surface.mount_mode}")
        lines.append(f"  view model: {surface.view_model_key}")
        lines.append(f"  selector: {surface.selector}")
        lines.append(f"  surface test id: {surface.surface_test_id}")
        lines.append(f"  state key: {surface.state_key}")
        lines.append(f"  enabled: {surface.enabled}")
        lines.append(f"  passive: {surface.passive}")
        lines.append(f"  blocked: {surface.blocked_action}")
    lines.append("Render bindings:")
    for binding in report.render_bindings:
        lines.append(f"- {binding.render_binding_key}: {binding.binding_mode}")
        lines.append(f"  surface: {binding.render_surface_key}")
        lines.append(f"  state binding: {binding.state_binding_key}")
        lines.append(f"  fallback: {binding.fallback_state}")
        lines.append(f"  passive: {binding.passive}")
    lines.append("Render guards:")
    for guard in report.render_guards:
        lines.append(f"- {guard.render_guard_key}: {guard.guard_state}")
        lines.append(f"  surface: {guard.render_surface_key}")
        lines.append(f"  action model: {guard.action_model_key}")
        lines.append(f"  blocked: {guard.blocked_action}")
        lines.append(f"  passive: {guard.passive}")
    lines.append("Render assertions:")
    for assertion in report.render_assertions:
        lines.append(f"- {assertion.render_contract_assertion_key}: {assertion.required_state}")
        lines.append(f"  surface: {assertion.render_surface_key}")
        lines.append(f"  source assertion: {assertion.source_render_assertion_key}")
        lines.append(f"  passive: {assertion.passive}")
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


def format_controller_brain_live_desktop_render_contract_report(
    report: ControllerBrainLiveDesktopRenderContractReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing desktop render-contract text."""

    source = (
        build_controller_brain_live_desktop_render_contract_report() if report is None else report
    )
    return passive_report_lines(_HEADER, _format_desktop_render_contract_body(source))


def _pop_desktop_render_contract_cli_value(remaining: list[str]) -> str:
    if not remaining:
        raise ValueError(_ARG_ERROR)
    return remaining.pop(0)


def _parse_desktop_render_contract_cli_args(argv: Sequence[str]) -> dict[str, object]:
    render_contract_label = _DEFAULT_RENDER_CONTRACT_LABEL
    surface_prefix = _DEFAULT_SURFACE_PREFIX
    json_output = False
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
        elif option == "--render-contract-label":
            render_contract_label = _normalize_render_contract_label(
                _pop_desktop_render_contract_cli_value(remaining)
            )
        elif option == "--surface-prefix":
            surface_prefix = _normalize_render_surface_prefix(
                _pop_desktop_render_contract_cli_value(remaining)
            )
        else:
            raise ValueError(_ARG_ERROR)
    return {
        "render_contract_label": render_contract_label,
        "surface_prefix": surface_prefix,
        "json_output": json_output,
    }


def _handle_desktop_render_contract_report(
    *,
    render_contract_label: str,
    surface_prefix: str,
    json_output: bool,
) -> int:
    if json_output:
        sys.stdout.write(
            json.dumps(
                build_controller_brain_live_desktop_render_contract_payload(
                    render_contract_label=render_contract_label,
                    surface_prefix=surface_prefix,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0
    report = build_controller_brain_live_desktop_render_contract_report(
        render_contract_label=render_contract_label,
        surface_prefix=surface_prefix,
    )
    sys.stdout.write("\n".join(format_controller_brain_live_desktop_render_contract_report(report)))
    sys.stdout.write("\n")
    return 0


def _format_desktop_render_contract_error(exc: Exception) -> str:
    return f"Error: {exc}"


CONTROLLER_BRAIN_LIVE_DESKTOP_RENDER_CONTRACT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="controller-brain-live-desktop-render-contract-report",
    summary="Print passive controller-brain desktop render surfaces and bindings.",
    args_parser=_parse_desktop_render_contract_cli_args,
    handler=_handle_desktop_render_contract_report,
    error_formatter=_format_desktop_render_contract_error,
)

register(CONTROLLER_BRAIN_LIVE_DESKTOP_RENDER_CONTRACT_CLI_COMMAND)

__all__ = (
    "BASE_BLOCKED_ACTIONS",
    "BASE_SAFETY_LINES",
    "CONTROLLER_BRAIN_LIVE_DESKTOP_RENDER_CONTRACT_CLI_COMMAND",
    "ControllerBrainDesktopRenderBinding",
    "ControllerBrainDesktopRenderContractAcceptanceCheck",
    "ControllerBrainDesktopRenderContractAssertion",
    "ControllerBrainDesktopRenderGuard",
    "ControllerBrainDesktopRenderSurface",
    "ControllerBrainLiveDesktopRenderContractReport",
    "DESKTOP_RENDER_CONTRACT_STATUS",
    "DESKTOP_RENDER_CONTRACT_VERSION",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SOURCE_DESKTOP_VIEW_MODEL_REPORT",
    "SOURCE_MODULE",
    "_desktop_render_contract_count",
    "_desktop_render_contract_slug",
    "_desktop_render_contract_unique_tuple",
    "_normalize_render_contract_label",
    "_normalize_render_surface_prefix",
    "_render_surface_key_from_view_model_key",
    "_surface_test_id_from_view_model_key",
    "build_controller_brain_live_desktop_render_contract_payload",
    "build_controller_brain_live_desktop_render_contract_report",
    "format_controller_brain_live_desktop_render_contract_report",
)
