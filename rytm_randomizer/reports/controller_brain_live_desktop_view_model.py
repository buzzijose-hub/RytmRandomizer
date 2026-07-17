"""Passive desktop view-model metadata for future controller-brain Cockpit work."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from .controller_brain_live_desktop_component_contract import (
    DESKTOP_COMPONENT_CONTRACT_STATUS,
    DESKTOP_COMPONENT_CONTRACT_VERSION,
    ControllerBrainDesktopComponentContractBinding,
    ControllerBrainDesktopComponentEventContract,
    ControllerBrainDesktopComponentPropContract,
    build_controller_brain_live_desktop_component_contract_report,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain live desktop view model"
SOURCE_MODULE: Final[str] = "reports.controller_brain_live_desktop_view_model"
DESKTOP_VIEW_MODEL_VERSION: Final[str] = "controller-brain-live-desktop-view-model-v1"
DESKTOP_VIEW_MODEL_STATUS: Final[str] = "desktop-view-model-passive"
SOURCE_DESKTOP_COMPONENT_CONTRACT_REPORT: Final[str] = (
    "controller-brain-live-desktop-component-contract-report"
)
_DEFAULT_VIEW_MODEL_LABEL: Final[str] = "Controller brain desktop view model"
_DEFAULT_STATE_PREFIX: Final[str] = "rr-state"
_ARG_ERROR: Final[str] = (
    "controller-brain-live-desktop-view-model-report accepts --json, "
    "--view-model-label, and --state-prefix only"
)
_STATE_PREFIX_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z][a-zA-Z0-9-]*$")
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-brain desktop view model metadata only",
    "composes controller-brain desktop component contract only",
    "component view models are declarative metadata only",
    "state bindings are declarative metadata only",
    "disabled action models are metadata only",
    "render assertions are metadata only",
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
    "mount component view models",
    "execute live state reducer",
    "dispatch Cockpit WebSocket commands",
    "emit controller feedback",
    "open MIDI output",
    "mutate a snapshot",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-live-desktop-view-model-report",
    "python -m rytm_randomizer.cli controller-brain-live-desktop-view-model-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-desktop-component-contract-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-desktop-app-plan-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainDesktopComponentViewModel:
    """One disabled future component view model."""

    view_model_key: str
    order: int
    component_contract_key: str
    selector: str
    state_key: str
    component_type: str
    status: str
    enabled: bool
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopStateBinding:
    """One passive future GUI state binding."""

    state_binding_key: str
    order: int
    view_model_key: str
    prop_name: str
    source_prop_contract_key: str
    source_state_slice_key: str
    source_view_model_path: str
    fallback_state: str
    required: bool
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopDisabledActionModel:
    """One disabled future action model."""

    action_model_key: str
    order: int
    view_model_key: str
    event_name: str
    control_state: str
    enabled: bool
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopRenderAssertion:
    """One passive future render assertion."""

    render_assertion_key: str
    order: int
    view_model_key: str
    test_id: str
    required_state: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopViewModelAcceptanceCheck:
    """One passive view-model acceptance check."""

    check_key: str
    order: int
    status: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainLiveDesktopViewModelReport:
    """Passive view-model metadata derived from component contracts."""

    title: str
    desktop_view_model_version: str
    desktop_view_model_status: str
    session_label: str
    view_model_label: str
    state_prefix: str
    source_report: str
    source_desktop_component_contract_version: str
    source_desktop_component_contract_status: str
    source_component_contract_count: int
    source_prop_contract_count: int
    source_event_contract_count: int
    component_view_models: tuple[ControllerBrainDesktopComponentViewModel, ...]
    state_bindings: tuple[ControllerBrainDesktopStateBinding, ...]
    disabled_action_models: tuple[ControllerBrainDesktopDisabledActionModel, ...]
    render_assertions: tuple[ControllerBrainDesktopRenderAssertion, ...]
    acceptance_checks: tuple[ControllerBrainDesktopViewModelAcceptanceCheck, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def component_view_model_count(self) -> int:
        """Return future component view-model count for summaries and JSON."""

        return _desktop_view_model_count(self.component_view_models)

    @property
    def state_binding_count(self) -> int:
        """Return future state binding count for summaries and JSON."""

        return _desktop_view_model_count(self.state_bindings)

    @property
    def disabled_action_model_count(self) -> int:
        """Return future disabled action model count for summaries and JSON."""

        return _desktop_view_model_count(self.disabled_action_models)

    @property
    def render_assertion_count(self) -> int:
        """Return future render assertion count for summaries and JSON."""

        return _desktop_view_model_count(self.render_assertions)

    @property
    def acceptance_check_count(self) -> int:
        """Return acceptance check count for summaries and JSON."""

        return _desktop_view_model_count(self.acceptance_checks)


def _desktop_view_model_unique_tuple(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return tuple(values)


def _desktop_view_model_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def _desktop_view_model_count(values: Sequence[object]) -> int:
    return len(values)


def _normalize_view_model_label(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("view_model_label must not be blank")
    return normalized


def _normalize_desktop_state_prefix(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("state_prefix must not be blank")
    if _STATE_PREFIX_PATTERN.fullmatch(normalized) is None:
        raise ValueError("state_prefix must use letters, numbers, and hyphens")
    return normalized


def _view_model_suffix_from_component_contract_key(component_contract_key: str) -> str:
    return component_contract_key.removeprefix("desktop.contract.component.")


def _view_model_key_from_component_contract_key(component_contract_key: str) -> str:
    suffix = _view_model_suffix_from_component_contract_key(component_contract_key)
    return f"desktop.viewmodel.{suffix}"


def _state_key_from_component_contract_key(
    component_contract_key: str,
    *,
    state_prefix: str,
) -> str:
    suffix = _view_model_suffix_from_component_contract_key(component_contract_key)
    return f"{state_prefix}.{suffix}"


def _state_binding_key_from_component_contract_key(component_contract_key: str) -> str:
    suffix = _view_model_suffix_from_component_contract_key(component_contract_key)
    return f"desktop.binding.{suffix}"


def _action_model_key_from_component_contract_key(component_contract_key: str) -> str:
    suffix = _view_model_suffix_from_component_contract_key(component_contract_key)
    return f"desktop.action.{suffix}"


def _render_assertion_key_from_component_contract_key(component_contract_key: str) -> str:
    suffix = _view_model_suffix_from_component_contract_key(component_contract_key)
    return f"desktop.assert.{suffix}"


def _component_view_model_from_contract(
    contract: ControllerBrainDesktopComponentContractBinding,
    *,
    state_prefix: str,
) -> ControllerBrainDesktopComponentViewModel:
    return ControllerBrainDesktopComponentViewModel(
        view_model_key=_view_model_key_from_component_contract_key(contract.component_contract_key),
        order=contract.order,
        component_contract_key=contract.component_contract_key,
        selector=contract.selector,
        state_key=_state_key_from_component_contract_key(
            contract.component_contract_key,
            state_prefix=state_prefix,
        ),
        component_type=contract.component_type,
        status="view-model-disabled",
        enabled=False,
        passive=True,
        evidence=f"{contract.component_contract_key} is mapped to a disabled future view model",
        blocked_action="mount component view models",
    )


def _state_binding_from_prop(
    prop: ControllerBrainDesktopComponentPropContract,
    *,
    view_model_key: str,
) -> ControllerBrainDesktopStateBinding:
    return ControllerBrainDesktopStateBinding(
        state_binding_key=_state_binding_key_from_component_contract_key(
            prop.component_contract_key
        ),
        order=prop.order,
        view_model_key=view_model_key,
        prop_name=prop.prop_name,
        source_prop_contract_key=prop.prop_contract_key,
        source_state_slice_key=prop.source_state_slice_key,
        source_view_model_path=prop.source_view_model_path,
        fallback_state=prop.initial_state,
        required=prop.required,
        passive=True,
        evidence=f"{prop.prop_contract_key} remains a future disabled state binding",
        blocked_action="execute live state reducer",
    )


def _disabled_action_model_from_event(
    event: ControllerBrainDesktopComponentEventContract,
    *,
    view_model_key: str,
) -> ControllerBrainDesktopDisabledActionModel:
    return ControllerBrainDesktopDisabledActionModel(
        action_model_key=_action_model_key_from_component_contract_key(
            event.component_contract_key
        ),
        order=event.order,
        view_model_key=view_model_key,
        event_name=event.event_name,
        control_state="disabled",
        enabled=False,
        passive=True,
        evidence=f"{event.event_contract_key} remains disabled in the view model",
        blocked_action=event.blocked_action,
    )


def _render_assertion_from_view_model(
    view_model: ControllerBrainDesktopComponentViewModel,
) -> ControllerBrainDesktopRenderAssertion:
    return ControllerBrainDesktopRenderAssertion(
        render_assertion_key=_render_assertion_key_from_component_contract_key(
            view_model.component_contract_key
        ),
        order=view_model.order,
        view_model_key=view_model.view_model_key,
        test_id=view_model.selector,
        required_state="disabled",
        passive=True,
        evidence=f"{view_model.view_model_key} should render disabled in future tests",
        blocked_action="start GUI renderer",
    )


def _controller_brain_desktop_view_model_acceptance_checks() -> (
    tuple[ControllerBrainDesktopViewModelAcceptanceCheck, ...]
):
    rows = (
        (
            "source-component-contract-ready",
            "source component contract is available as passive JSON",
            "mount component view models",
        ),
        (
            "component-view-model-coverage",
            "every component contract has one disabled view model",
            "mount component view models",
        ),
        (
            "state-binding-coverage",
            "every prop contract has one state binding",
            "execute live state reducer",
        ),
        (
            "disabled-action-model-coverage",
            "every event contract has one disabled action model",
            "dispatch Cockpit WebSocket commands",
        ),
        (
            "render-assertion-coverage",
            "every view model has one render assertion",
            "start GUI renderer",
        ),
        (
            "replay-command",
            "operator replay commands remain copy-ready passive CLI commands",
            "dispatch Cockpit WebSocket commands",
        ),
        (
            "passive-boundary",
            "desktop view model launches no GUI, writes no files, opens no ports, and sends no MIDI",
            "open MIDI output",
        ),
    )
    return tuple(
        ControllerBrainDesktopViewModelAcceptanceCheck(
            check_key=key,
            order=index + 1,
            status="ready",
            passive=True,
            evidence=evidence,
            blocked_action=blocked_action,
        )
        for index, (key, evidence, blocked_action) in enumerate(rows)
    )


def build_controller_brain_live_desktop_view_model_report(
    *,
    session_label: str = "Live Session",
    view_model_label: str = _DEFAULT_VIEW_MODEL_LABEL,
    state_prefix: str = _DEFAULT_STATE_PREFIX,
) -> ControllerBrainLiveDesktopViewModelReport:
    """Build passive future desktop view-model metadata from component contracts."""

    normalized_label = _normalize_view_model_label(view_model_label)
    normalized_state_prefix = _normalize_desktop_state_prefix(state_prefix)
    component_contract = build_controller_brain_live_desktop_component_contract_report(
        session_label=session_label,
    )
    component_view_models = tuple(
        _component_view_model_from_contract(contract, state_prefix=normalized_state_prefix)
        for contract in component_contract.component_contracts
    )
    state_bindings = tuple(
        _state_binding_from_prop(prop, view_model_key=view_model.view_model_key)
        for prop, view_model in zip(
            component_contract.prop_contracts,
            component_view_models,
            strict=True,
        )
    )
    disabled_action_models = tuple(
        _disabled_action_model_from_event(event, view_model_key=view_model.view_model_key)
        for event, view_model in zip(
            component_contract.event_contracts,
            component_view_models,
            strict=True,
        )
    )
    render_assertions = tuple(
        _render_assertion_from_view_model(view_model) for view_model in component_view_models
    )
    return ControllerBrainLiveDesktopViewModelReport(
        title=REPORT_TITLE,
        desktop_view_model_version=DESKTOP_VIEW_MODEL_VERSION,
        desktop_view_model_status=DESKTOP_VIEW_MODEL_STATUS,
        session_label=session_label,
        view_model_label=normalized_label,
        state_prefix=normalized_state_prefix,
        source_report=SOURCE_DESKTOP_COMPONENT_CONTRACT_REPORT,
        source_desktop_component_contract_version=DESKTOP_COMPONENT_CONTRACT_VERSION,
        source_desktop_component_contract_status=DESKTOP_COMPONENT_CONTRACT_STATUS,
        source_component_contract_count=component_contract.component_contract_count,
        source_prop_contract_count=component_contract.prop_contract_count,
        source_event_contract_count=component_contract.event_contract_count,
        component_view_models=component_view_models,
        state_bindings=state_bindings,
        disabled_action_models=disabled_action_models,
        render_assertions=render_assertions,
        acceptance_checks=_controller_brain_desktop_view_model_acceptance_checks(),
        blocked_actions=_desktop_view_model_unique_tuple(
            BASE_BLOCKED_ACTIONS,
            component_contract.blocked_actions,
        ),
        safety_lines=_desktop_view_model_unique_tuple(
            BASE_SAFETY_LINES,
            component_contract.safety_lines,
        ),
        replay_commands=REPLAY_COMMANDS,
    )


def _component_view_model_to_payload(
    view_model: ControllerBrainDesktopComponentViewModel,
) -> dict[str, object]:
    return {
        "view_model_key": view_model.view_model_key,
        "order": view_model.order,
        "component_contract_key": view_model.component_contract_key,
        "selector": view_model.selector,
        "state_key": view_model.state_key,
        "component_type": view_model.component_type,
        "status": view_model.status,
        "enabled": view_model.enabled,
        "passive": view_model.passive,
        "evidence": view_model.evidence,
        "blocked_action": view_model.blocked_action,
    }


def _desktop_state_binding_to_payload(
    binding: ControllerBrainDesktopStateBinding,
) -> dict[str, object]:
    return {
        "state_binding_key": binding.state_binding_key,
        "order": binding.order,
        "view_model_key": binding.view_model_key,
        "prop_name": binding.prop_name,
        "source_prop_contract_key": binding.source_prop_contract_key,
        "source_state_slice_key": binding.source_state_slice_key,
        "source_view_model_path": binding.source_view_model_path,
        "fallback_state": binding.fallback_state,
        "required": binding.required,
        "passive": binding.passive,
        "evidence": binding.evidence,
        "blocked_action": binding.blocked_action,
    }


def _disabled_action_model_to_payload(
    action: ControllerBrainDesktopDisabledActionModel,
) -> dict[str, object]:
    return {
        "action_model_key": action.action_model_key,
        "order": action.order,
        "view_model_key": action.view_model_key,
        "event_name": action.event_name,
        "control_state": action.control_state,
        "enabled": action.enabled,
        "passive": action.passive,
        "evidence": action.evidence,
        "blocked_action": action.blocked_action,
    }


def _render_assertion_to_payload(
    assertion: ControllerBrainDesktopRenderAssertion,
) -> dict[str, object]:
    return {
        "render_assertion_key": assertion.render_assertion_key,
        "order": assertion.order,
        "view_model_key": assertion.view_model_key,
        "test_id": assertion.test_id,
        "required_state": assertion.required_state,
        "passive": assertion.passive,
        "evidence": assertion.evidence,
        "blocked_action": assertion.blocked_action,
    }


def _desktop_view_model_acceptance_check_to_payload(
    check: ControllerBrainDesktopViewModelAcceptanceCheck,
) -> dict[str, object]:
    return {
        "check_key": check.check_key,
        "order": check.order,
        "status": check.status,
        "passive": check.passive,
        "evidence": check.evidence,
        "blocked_action": check.blocked_action,
    }


def build_controller_brain_live_desktop_view_model_payload(
    *,
    session_label: str = "Live Session",
    view_model_label: str = _DEFAULT_VIEW_MODEL_LABEL,
    state_prefix: str = _DEFAULT_STATE_PREFIX,
) -> dict[str, object]:
    """Return JSON-ready passive desktop view-model metadata."""

    report = build_controller_brain_live_desktop_view_model_report(
        session_label=session_label,
        view_model_label=view_model_label,
        state_prefix=state_prefix,
    )
    return {
        "controller_brain_live_desktop_view_model": {
            "title": report.title,
            "desktop_view_model_version": report.desktop_view_model_version,
            "desktop_view_model_status": report.desktop_view_model_status,
            "session_label": report.session_label,
            "view_model_label": report.view_model_label,
            "state_prefix": report.state_prefix,
            "source_report": report.source_report,
            "source_desktop_component_contract_version": (
                report.source_desktop_component_contract_version
            ),
            "source_desktop_component_contract_status": (
                report.source_desktop_component_contract_status
            ),
            "source_component_contract_count": report.source_component_contract_count,
            "source_prop_contract_count": report.source_prop_contract_count,
            "source_event_contract_count": report.source_event_contract_count,
            "component_view_model_count": report.component_view_model_count,
            "state_binding_count": report.state_binding_count,
            "disabled_action_model_count": report.disabled_action_model_count,
            "render_assertion_count": report.render_assertion_count,
            "acceptance_check_count": report.acceptance_check_count,
            "component_view_models": [
                _component_view_model_to_payload(view_model)
                for view_model in report.component_view_models
            ],
            "state_bindings": [
                _desktop_state_binding_to_payload(binding) for binding in report.state_bindings
            ],
            "disabled_action_models": [
                _disabled_action_model_to_payload(action)
                for action in report.disabled_action_models
            ],
            "render_assertions": [
                _render_assertion_to_payload(assertion) for assertion in report.render_assertions
            ],
            "acceptance_checks": [
                _desktop_view_model_acceptance_check_to_payload(check)
                for check in report.acceptance_checks
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def _format_desktop_view_model_body(
    report: ControllerBrainLiveDesktopViewModelReport,
) -> list[str]:
    lines = [
        "Controller brain live desktop view model:",
        f"- version: {report.desktop_view_model_version}",
        f"- status: {report.desktop_view_model_status}",
        f"- session: {report.session_label}",
        f"- view model label: {report.view_model_label}",
        f"- state prefix: {report.state_prefix}",
        f"- source desktop component contract: {report.source_report}",
        f"- source desktop component contract version: {report.source_desktop_component_contract_version}",
        f"- source desktop component contract status: {report.source_desktop_component_contract_status}",
        f"- source component contracts: {report.source_component_contract_count}",
        f"- source prop contracts: {report.source_prop_contract_count}",
        f"- source event contracts: {report.source_event_contract_count}",
        f"- component view models: {report.component_view_model_count}",
        f"- state bindings: {report.state_binding_count}",
        f"- disabled action models: {report.disabled_action_model_count}",
        f"- render assertions: {report.render_assertion_count}",
        f"- acceptance checks: {report.acceptance_check_count}",
        "Component view models:",
    ]
    for view_model in report.component_view_models:
        lines.append(f"- {view_model.view_model_key}: {view_model.status}")
        lines.append(f"  component contract: {view_model.component_contract_key}")
        lines.append(f"  selector: {view_model.selector}")
        lines.append(f"  state key: {view_model.state_key}")
        lines.append(f"  enabled: {view_model.enabled}")
        lines.append(f"  passive: {view_model.passive}")
        lines.append(f"  blocked: {view_model.blocked_action}")
    lines.append("State bindings:")
    for binding in report.state_bindings:
        lines.append(f"- {binding.state_binding_key}: {binding.prop_name}")
        lines.append(f"  view model: {binding.view_model_key}")
        lines.append(f"  source prop: {binding.source_prop_contract_key}")
        lines.append(f"  fallback: {binding.fallback_state}")
        lines.append(f"  passive: {binding.passive}")
    lines.append("Disabled action models:")
    for action in report.disabled_action_models:
        lines.append(f"- {action.action_model_key}: {action.event_name}")
        lines.append(f"  view model: {action.view_model_key}")
        lines.append(f"  control state: {action.control_state}")
        lines.append(f"  enabled: {action.enabled}")
        lines.append(f"  passive: {action.passive}")
        lines.append(f"  blocked: {action.blocked_action}")
    lines.append("Render assertions:")
    for assertion in report.render_assertions:
        lines.append(f"- {assertion.render_assertion_key}: {assertion.test_id}")
        lines.append(f"  view model: {assertion.view_model_key}")
        lines.append(f"  required state: {assertion.required_state}")
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


def format_controller_brain_live_desktop_view_model_report(
    report: ControllerBrainLiveDesktopViewModelReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing desktop view-model text."""

    source = build_controller_brain_live_desktop_view_model_report() if report is None else report
    return passive_report_lines(_HEADER, _format_desktop_view_model_body(source))


def _pop_desktop_view_model_cli_value(remaining: list[str]) -> str:
    if not remaining:
        raise ValueError(_ARG_ERROR)
    return remaining.pop(0)


def _parse_desktop_view_model_cli_args(argv: Sequence[str]) -> dict[str, object]:
    view_model_label = _DEFAULT_VIEW_MODEL_LABEL
    state_prefix = _DEFAULT_STATE_PREFIX
    json_output = False
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
        elif option == "--view-model-label":
            view_model_label = _normalize_view_model_label(
                _pop_desktop_view_model_cli_value(remaining)
            )
        elif option == "--state-prefix":
            state_prefix = _normalize_desktop_state_prefix(
                _pop_desktop_view_model_cli_value(remaining)
            )
        else:
            raise ValueError(_ARG_ERROR)
    return {
        "view_model_label": view_model_label,
        "state_prefix": state_prefix,
        "json_output": json_output,
    }


def _handle_desktop_view_model_report(
    *,
    view_model_label: str,
    state_prefix: str,
    json_output: bool,
) -> int:
    if json_output:
        sys.stdout.write(
            json.dumps(
                build_controller_brain_live_desktop_view_model_payload(
                    view_model_label=view_model_label,
                    state_prefix=state_prefix,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0
    report = build_controller_brain_live_desktop_view_model_report(
        view_model_label=view_model_label,
        state_prefix=state_prefix,
    )
    sys.stdout.write("\n".join(format_controller_brain_live_desktop_view_model_report(report)))
    sys.stdout.write("\n")
    return 0


def _format_desktop_view_model_error(exc: Exception) -> str:
    return f"Error: {exc}"


CONTROLLER_BRAIN_LIVE_DESKTOP_VIEW_MODEL_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="controller-brain-live-desktop-view-model-report",
    summary="Print passive controller-brain desktop view models and state bindings.",
    args_parser=_parse_desktop_view_model_cli_args,
    handler=_handle_desktop_view_model_report,
    error_formatter=_format_desktop_view_model_error,
)

register(CONTROLLER_BRAIN_LIVE_DESKTOP_VIEW_MODEL_CLI_COMMAND)

__all__ = (
    "BASE_BLOCKED_ACTIONS",
    "BASE_SAFETY_LINES",
    "CONTROLLER_BRAIN_LIVE_DESKTOP_VIEW_MODEL_CLI_COMMAND",
    "ControllerBrainDesktopComponentViewModel",
    "ControllerBrainDesktopDisabledActionModel",
    "ControllerBrainDesktopRenderAssertion",
    "ControllerBrainDesktopStateBinding",
    "ControllerBrainDesktopViewModelAcceptanceCheck",
    "ControllerBrainLiveDesktopViewModelReport",
    "DESKTOP_VIEW_MODEL_STATUS",
    "DESKTOP_VIEW_MODEL_VERSION",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SOURCE_DESKTOP_COMPONENT_CONTRACT_REPORT",
    "SOURCE_MODULE",
    "_desktop_view_model_count",
    "_desktop_view_model_slug",
    "_desktop_view_model_unique_tuple",
    "_normalize_desktop_state_prefix",
    "_normalize_view_model_label",
    "_state_key_from_component_contract_key",
    "_view_model_key_from_component_contract_key",
    "build_controller_brain_live_desktop_view_model_payload",
    "build_controller_brain_live_desktop_view_model_report",
    "format_controller_brain_live_desktop_view_model_report",
)
