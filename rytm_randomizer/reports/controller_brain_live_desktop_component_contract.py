"""Passive desktop component-contract metadata for future controller-brain Cockpit work."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from .controller_brain_live_desktop_app_plan import (
    DESKTOP_APP_PLAN_STATUS,
    DESKTOP_APP_PLAN_VERSION,
    ControllerBrainDesktopComponentFileHint,
    ControllerBrainDesktopStateSlice,
    build_controller_brain_live_desktop_app_plan_report,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain live desktop component contract"
SOURCE_MODULE: Final[str] = "reports.controller_brain_live_desktop_component_contract"
DESKTOP_COMPONENT_CONTRACT_VERSION: Final[str] = (
    "controller-brain-live-desktop-component-contract-v1"
)
DESKTOP_COMPONENT_CONTRACT_STATUS: Final[str] = "desktop-component-contract-passive"
SOURCE_DESKTOP_APP_PLAN_REPORT: Final[str] = "controller-brain-live-desktop-app-plan-report"
_DEFAULT_COMPONENT_CONTRACT_LABEL: Final[str] = "Controller brain desktop component contract"
_DEFAULT_SELECTOR_PREFIX: Final[str] = "rr-controller"
_ARG_ERROR: Final[str] = (
    "controller-brain-live-desktop-component-contract-report accepts --json, "
    "--component-contract-label, and --selector-prefix only"
)
_SELECTOR_PREFIX_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z][a-zA-Z0-9-]*$")
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-brain desktop component contract metadata only",
    "composes controller-brain desktop app plan only",
    "component contracts are declarative metadata only",
    "prop contracts are declarative metadata only",
    "event contracts are disabled metadata only",
    "test hooks are declarative metadata only",
    "fixture contracts are advisory metadata only",
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
    "mount component contracts",
    "write component files",
    "execute live state reducer",
    "dispatch Cockpit WebSocket commands",
    "emit controller feedback",
    "open MIDI output",
    "mutate a snapshot",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-live-desktop-component-contract-report",
    "python -m rytm_randomizer.cli controller-brain-live-desktop-component-contract-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-desktop-app-plan-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-desktop-blueprint-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainDesktopComponentContractBinding:
    """One disabled future component API contract."""

    component_contract_key: str
    order: int
    source_component_file_key: str
    source_component_key: str
    route_key: str
    suggested_module: str
    selector: str
    component_type: str
    status: str
    enabled: bool
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopComponentPropContract:
    """One future component prop contract."""

    prop_contract_key: str
    order: int
    component_contract_key: str
    prop_name: str
    source_state_slice_key: str
    source_view_model_path: str
    initial_state: str
    required: bool
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopComponentEventContract:
    """One disabled future component event contract."""

    event_contract_key: str
    order: int
    component_contract_key: str
    event_name: str
    enabled: bool
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopComponentTestHook:
    """One future component test hook."""

    test_hook_key: str
    order: int
    component_contract_key: str
    test_id: str
    purpose: str
    passive: bool


@dataclass(frozen=True)
class ControllerBrainDesktopComponentFixtureContract:
    """One advisory future fixture contract."""

    fixture_contract_key: str
    order: int
    component_contract_key: str
    fixture_key: str
    fixture_scope: str
    write_file: bool
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopComponentAcceptanceCheck:
    """One passive component-contract acceptance check."""

    check_key: str
    order: int
    status: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainLiveDesktopComponentContractReport:
    """Passive component-contract metadata derived from the desktop app plan."""

    title: str
    desktop_component_contract_version: str
    desktop_component_contract_status: str
    session_label: str
    component_contract_label: str
    selector_prefix: str
    source_report: str
    source_desktop_app_plan_version: str
    source_desktop_app_plan_status: str
    source_route_count: int
    source_component_file_hint_count: int
    source_state_slice_count: int
    component_contracts: tuple[ControllerBrainDesktopComponentContractBinding, ...]
    prop_contracts: tuple[ControllerBrainDesktopComponentPropContract, ...]
    event_contracts: tuple[ControllerBrainDesktopComponentEventContract, ...]
    test_hooks: tuple[ControllerBrainDesktopComponentTestHook, ...]
    fixture_contracts: tuple[ControllerBrainDesktopComponentFixtureContract, ...]
    acceptance_checks: tuple[ControllerBrainDesktopComponentAcceptanceCheck, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def component_contract_count(self) -> int:
        """Return future component contract count for summaries and JSON."""

        return _desktop_component_contract_count(self.component_contracts)

    @property
    def prop_contract_count(self) -> int:
        """Return future prop contract count for summaries and JSON."""

        return _desktop_component_contract_count(self.prop_contracts)

    @property
    def event_contract_count(self) -> int:
        """Return future event contract count for summaries and JSON."""

        return _desktop_component_contract_count(self.event_contracts)

    @property
    def test_hook_count(self) -> int:
        """Return future test hook count for summaries and JSON."""

        return _desktop_component_contract_count(self.test_hooks)

    @property
    def fixture_contract_count(self) -> int:
        """Return future fixture contract count for summaries and JSON."""

        return _desktop_component_contract_count(self.fixture_contracts)

    @property
    def acceptance_check_count(self) -> int:
        """Return acceptance check count for summaries and JSON."""

        return _desktop_component_contract_count(self.acceptance_checks)


def _desktop_component_contract_unique_tuple(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return tuple(values)


def _desktop_component_contract_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def _desktop_component_contract_count(values: Sequence[object]) -> int:
    return len(values)


def _normalize_component_contract_label(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("component_contract_label must not be blank")
    return normalized


def _normalize_selector_prefix(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("selector_prefix must not be blank")
    if _SELECTOR_PREFIX_PATTERN.fullmatch(normalized) is None:
        raise ValueError("selector_prefix must use letters, numbers, and hyphens")
    return normalized


def _component_contract_suffix_from_file_key(component_file_key: str) -> str:
    return component_file_key.removeprefix("desktop.file.component.")


def _component_contract_key_from_component_file_key(component_file_key: str) -> str:
    suffix = _component_contract_suffix_from_file_key(component_file_key)
    return f"desktop.contract.component.{suffix}"


def _prop_contract_key_from_state_slice_key(state_slice_key: str) -> str:
    suffix = state_slice_key.removeprefix("desktop.state.")
    return f"desktop.prop.{suffix}"


def _event_contract_key_from_component_file_key(component_file_key: str) -> str:
    suffix = _component_contract_suffix_from_file_key(component_file_key)
    return f"desktop.event.{suffix}"


def _test_hook_key_from_component_file_key(component_file_key: str) -> str:
    suffix = _component_contract_suffix_from_file_key(component_file_key)
    return f"desktop.test.{suffix}"


def _fixture_contract_key_from_component_file_key(component_file_key: str) -> str:
    suffix = _component_contract_suffix_from_file_key(component_file_key)
    return f"desktop.fixture.{suffix}"


def _fixture_key_from_component_file_key(component_file_key: str) -> str:
    suffix = _component_contract_suffix_from_file_key(component_file_key)
    return f"fixture.{suffix}"


def _selector_from_component_file_key(component_file_key: str, *, selector_prefix: str) -> str:
    suffix = _component_contract_suffix_from_file_key(component_file_key)
    return f"{selector_prefix}-{_desktop_component_contract_slug(suffix)}"


def _component_contract_from_hint(
    hint: ControllerBrainDesktopComponentFileHint,
    *,
    selector_prefix: str,
) -> ControllerBrainDesktopComponentContractBinding:
    return ControllerBrainDesktopComponentContractBinding(
        component_contract_key=_component_contract_key_from_component_file_key(
            hint.component_file_key
        ),
        order=hint.order,
        source_component_file_key=hint.component_file_key,
        source_component_key=hint.source_component_key,
        route_key=hint.route_key,
        suggested_module=hint.suggested_module,
        selector=_selector_from_component_file_key(
            hint.component_file_key,
            selector_prefix=selector_prefix,
        ),
        component_type=hint.component_type,
        status="component-contract-disabled",
        enabled=False,
        passive=True,
        evidence=f"{hint.component_file_key} is mapped to a disabled future component API",
        blocked_action="mount component contracts",
    )


def _prop_contract_from_state_slice(
    slice_: ControllerBrainDesktopStateSlice,
    *,
    component_contract_key: str,
) -> ControllerBrainDesktopComponentPropContract:
    return ControllerBrainDesktopComponentPropContract(
        prop_contract_key=_prop_contract_key_from_state_slice_key(slice_.state_slice_key),
        order=slice_.order,
        component_contract_key=component_contract_key,
        prop_name="viewModel",
        source_state_slice_key=slice_.state_slice_key,
        source_view_model_path=slice_.source_view_model_path,
        initial_state=slice_.initial_state,
        required=True,
        passive=True,
        evidence=f"{slice_.state_slice_key} remains a disabled future view-model prop",
        blocked_action="execute live state reducer",
    )


def _event_contract_from_binding(
    binding: ControllerBrainDesktopComponentContractBinding,
) -> ControllerBrainDesktopComponentEventContract:
    return ControllerBrainDesktopComponentEventContract(
        event_contract_key=_event_contract_key_from_component_file_key(
            binding.source_component_file_key
        ),
        order=binding.order,
        component_contract_key=binding.component_contract_key,
        event_name="onIntentPreview",
        enabled=False,
        passive=True,
        evidence=f"{binding.component_contract_key} keeps future preview intent disabled",
        blocked_action="dispatch Cockpit WebSocket commands",
    )


def _test_hook_from_binding(
    binding: ControllerBrainDesktopComponentContractBinding,
) -> ControllerBrainDesktopComponentTestHook:
    return ControllerBrainDesktopComponentTestHook(
        test_hook_key=_test_hook_key_from_component_file_key(binding.source_component_file_key),
        order=binding.order,
        component_contract_key=binding.component_contract_key,
        test_id=binding.selector,
        purpose="future controller-brain desktop component selector",
        passive=True,
    )


def _fixture_contract_from_binding(
    binding: ControllerBrainDesktopComponentContractBinding,
) -> ControllerBrainDesktopComponentFixtureContract:
    return ControllerBrainDesktopComponentFixtureContract(
        fixture_contract_key=_fixture_contract_key_from_component_file_key(
            binding.source_component_file_key
        ),
        order=binding.order,
        component_contract_key=binding.component_contract_key,
        fixture_key=_fixture_key_from_component_file_key(binding.source_component_file_key),
        fixture_scope="future desktop component harness",
        write_file=False,
        passive=True,
        evidence=f"{binding.component_contract_key} fixture remains advisory only",
        blocked_action="write component files",
    )


def _controller_brain_desktop_component_acceptance_checks() -> (
    tuple[ControllerBrainDesktopComponentAcceptanceCheck, ...]
):
    rows = (
        (
            "source-app-plan-ready",
            "source desktop app plan is available as passive JSON",
            "mount component contracts",
        ),
        (
            "component-contract-coverage",
            "every component file hint has one disabled component contract",
            "mount component contracts",
        ),
        (
            "prop-contract-coverage",
            "every state slice has one future view-model prop contract",
            "execute live state reducer",
        ),
        (
            "event-contract-coverage",
            "every component contract has one disabled event contract",
            "dispatch Cockpit WebSocket commands",
        ),
        (
            "test-hook-coverage",
            "every component contract has one future test hook",
            "start GUI renderer",
        ),
        (
            "fixture-contract-coverage",
            "every component contract has one advisory fixture contract",
            "write component files",
        ),
        (
            "passive-boundary",
            "desktop component contract launches no GUI, writes no files, opens no ports, and sends no MIDI",
            "open MIDI output",
        ),
    )
    return tuple(
        ControllerBrainDesktopComponentAcceptanceCheck(
            check_key=key,
            order=index + 1,
            status="ready",
            passive=True,
            evidence=evidence,
            blocked_action=blocked_action,
        )
        for index, (key, evidence, blocked_action) in enumerate(rows)
    )


def build_controller_brain_live_desktop_component_contract_report(
    *,
    session_label: str = "Live Session",
    component_contract_label: str = _DEFAULT_COMPONENT_CONTRACT_LABEL,
    selector_prefix: str = _DEFAULT_SELECTOR_PREFIX,
) -> ControllerBrainLiveDesktopComponentContractReport:
    """Build passive future desktop component-contract metadata from the app plan."""

    normalized_label = _normalize_component_contract_label(component_contract_label)
    normalized_selector_prefix = _normalize_selector_prefix(selector_prefix)
    app_plan = build_controller_brain_live_desktop_app_plan_report(
        session_label=session_label,
    )
    component_contracts = tuple(
        _component_contract_from_hint(hint, selector_prefix=normalized_selector_prefix)
        for hint in app_plan.component_file_hints
    )
    prop_contracts = tuple(
        _prop_contract_from_state_slice(
            slice_,
            component_contract_key=component_contract.component_contract_key,
        )
        for slice_, component_contract in zip(
            app_plan.state_slices,
            component_contracts,
            strict=True,
        )
    )
    event_contracts = tuple(
        _event_contract_from_binding(binding) for binding in component_contracts
    )
    test_hooks = tuple(_test_hook_from_binding(binding) for binding in component_contracts)
    fixture_contracts = tuple(
        _fixture_contract_from_binding(binding) for binding in component_contracts
    )
    return ControllerBrainLiveDesktopComponentContractReport(
        title=REPORT_TITLE,
        desktop_component_contract_version=DESKTOP_COMPONENT_CONTRACT_VERSION,
        desktop_component_contract_status=DESKTOP_COMPONENT_CONTRACT_STATUS,
        session_label=session_label,
        component_contract_label=normalized_label,
        selector_prefix=normalized_selector_prefix,
        source_report=SOURCE_DESKTOP_APP_PLAN_REPORT,
        source_desktop_app_plan_version=DESKTOP_APP_PLAN_VERSION,
        source_desktop_app_plan_status=DESKTOP_APP_PLAN_STATUS,
        source_route_count=app_plan.route_count,
        source_component_file_hint_count=app_plan.component_file_hint_count,
        source_state_slice_count=app_plan.state_slice_count,
        component_contracts=component_contracts,
        prop_contracts=prop_contracts,
        event_contracts=event_contracts,
        test_hooks=test_hooks,
        fixture_contracts=fixture_contracts,
        acceptance_checks=_controller_brain_desktop_component_acceptance_checks(),
        blocked_actions=_desktop_component_contract_unique_tuple(
            BASE_BLOCKED_ACTIONS,
            app_plan.blocked_actions,
        ),
        safety_lines=_desktop_component_contract_unique_tuple(
            BASE_SAFETY_LINES,
            app_plan.safety_lines,
        ),
        replay_commands=REPLAY_COMMANDS,
    )


def _desktop_component_contract_binding_to_payload(
    contract: ControllerBrainDesktopComponentContractBinding,
) -> dict[str, object]:
    return {
        "component_contract_key": contract.component_contract_key,
        "order": contract.order,
        "source_component_file_key": contract.source_component_file_key,
        "source_component_key": contract.source_component_key,
        "route_key": contract.route_key,
        "suggested_module": contract.suggested_module,
        "selector": contract.selector,
        "component_type": contract.component_type,
        "status": contract.status,
        "enabled": contract.enabled,
        "passive": contract.passive,
        "evidence": contract.evidence,
        "blocked_action": contract.blocked_action,
    }


def _prop_contract_to_payload(
    prop: ControllerBrainDesktopComponentPropContract,
) -> dict[str, object]:
    return {
        "prop_contract_key": prop.prop_contract_key,
        "order": prop.order,
        "component_contract_key": prop.component_contract_key,
        "prop_name": prop.prop_name,
        "source_state_slice_key": prop.source_state_slice_key,
        "source_view_model_path": prop.source_view_model_path,
        "initial_state": prop.initial_state,
        "required": prop.required,
        "passive": prop.passive,
        "evidence": prop.evidence,
        "blocked_action": prop.blocked_action,
    }


def _event_contract_to_payload(
    event: ControllerBrainDesktopComponentEventContract,
) -> dict[str, object]:
    return {
        "event_contract_key": event.event_contract_key,
        "order": event.order,
        "component_contract_key": event.component_contract_key,
        "event_name": event.event_name,
        "enabled": event.enabled,
        "passive": event.passive,
        "evidence": event.evidence,
        "blocked_action": event.blocked_action,
    }


def _test_hook_to_payload(hook: ControllerBrainDesktopComponentTestHook) -> dict[str, object]:
    return {
        "test_hook_key": hook.test_hook_key,
        "order": hook.order,
        "component_contract_key": hook.component_contract_key,
        "test_id": hook.test_id,
        "purpose": hook.purpose,
        "passive": hook.passive,
    }


def _fixture_contract_to_payload(
    fixture: ControllerBrainDesktopComponentFixtureContract,
) -> dict[str, object]:
    return {
        "fixture_contract_key": fixture.fixture_contract_key,
        "order": fixture.order,
        "component_contract_key": fixture.component_contract_key,
        "fixture_key": fixture.fixture_key,
        "fixture_scope": fixture.fixture_scope,
        "write_file": fixture.write_file,
        "passive": fixture.passive,
        "evidence": fixture.evidence,
        "blocked_action": fixture.blocked_action,
    }


def _desktop_component_contract_acceptance_check_to_payload(
    check: ControllerBrainDesktopComponentAcceptanceCheck,
) -> dict[str, object]:
    return {
        "check_key": check.check_key,
        "order": check.order,
        "status": check.status,
        "passive": check.passive,
        "evidence": check.evidence,
        "blocked_action": check.blocked_action,
    }


def build_controller_brain_live_desktop_component_contract_payload(
    *,
    session_label: str = "Live Session",
    component_contract_label: str = _DEFAULT_COMPONENT_CONTRACT_LABEL,
    selector_prefix: str = _DEFAULT_SELECTOR_PREFIX,
) -> dict[str, object]:
    """Return JSON-ready passive desktop component-contract metadata."""

    report = build_controller_brain_live_desktop_component_contract_report(
        session_label=session_label,
        component_contract_label=component_contract_label,
        selector_prefix=selector_prefix,
    )
    return {
        "controller_brain_live_desktop_component_contract": {
            "title": report.title,
            "desktop_component_contract_version": report.desktop_component_contract_version,
            "desktop_component_contract_status": report.desktop_component_contract_status,
            "session_label": report.session_label,
            "component_contract_label": report.component_contract_label,
            "selector_prefix": report.selector_prefix,
            "source_report": report.source_report,
            "source_desktop_app_plan_version": report.source_desktop_app_plan_version,
            "source_desktop_app_plan_status": report.source_desktop_app_plan_status,
            "source_route_count": report.source_route_count,
            "source_component_file_hint_count": report.source_component_file_hint_count,
            "source_state_slice_count": report.source_state_slice_count,
            "component_contract_count": report.component_contract_count,
            "prop_contract_count": report.prop_contract_count,
            "event_contract_count": report.event_contract_count,
            "test_hook_count": report.test_hook_count,
            "fixture_contract_count": report.fixture_contract_count,
            "acceptance_check_count": report.acceptance_check_count,
            "component_contracts": [
                _desktop_component_contract_binding_to_payload(contract)
                for contract in report.component_contracts
            ],
            "prop_contracts": [_prop_contract_to_payload(prop) for prop in report.prop_contracts],
            "event_contracts": [
                _event_contract_to_payload(event) for event in report.event_contracts
            ],
            "test_hooks": [_test_hook_to_payload(hook) for hook in report.test_hooks],
            "fixture_contracts": [
                _fixture_contract_to_payload(fixture) for fixture in report.fixture_contracts
            ],
            "acceptance_checks": [
                _desktop_component_contract_acceptance_check_to_payload(check)
                for check in report.acceptance_checks
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def _format_desktop_component_contract_body(
    report: ControllerBrainLiveDesktopComponentContractReport,
) -> list[str]:
    lines = [
        "Controller brain live desktop component contract:",
        f"- version: {report.desktop_component_contract_version}",
        f"- status: {report.desktop_component_contract_status}",
        f"- session: {report.session_label}",
        f"- component contract label: {report.component_contract_label}",
        f"- selector prefix: {report.selector_prefix}",
        f"- source desktop app plan: {report.source_report}",
        f"- source desktop app plan version: {report.source_desktop_app_plan_version}",
        f"- source desktop app plan status: {report.source_desktop_app_plan_status}",
        f"- source app routes: {report.source_route_count}",
        f"- source component file hints: {report.source_component_file_hint_count}",
        f"- source state slices: {report.source_state_slice_count}",
        f"- component contracts: {report.component_contract_count}",
        f"- prop contracts: {report.prop_contract_count}",
        f"- event contracts: {report.event_contract_count}",
        f"- test hooks: {report.test_hook_count}",
        f"- fixture contracts: {report.fixture_contract_count}",
        f"- acceptance checks: {report.acceptance_check_count}",
        "Component contracts:",
    ]
    for contract in report.component_contracts:
        lines.append(f"- {contract.component_contract_key}: {contract.status}")
        lines.append(f"  source file: {contract.source_component_file_key}")
        lines.append(f"  source component: {contract.source_component_key}")
        lines.append(f"  selector: {contract.selector}")
        lines.append(f"  suggested module: {contract.suggested_module}")
        lines.append(f"  enabled: {contract.enabled}")
        lines.append(f"  passive: {contract.passive}")
        lines.append(f"  blocked: {contract.blocked_action}")
    lines.append("Prop contracts:")
    for prop in report.prop_contracts:
        lines.append(f"- {prop.prop_contract_key}: {prop.prop_name}")
        lines.append(f"  component: {prop.component_contract_key}")
        lines.append(f"  state slice: {prop.source_state_slice_key}")
        lines.append(f"  initial state: {prop.initial_state}")
        lines.append(f"  passive: {prop.passive}")
    lines.append("Event contracts:")
    for event in report.event_contracts:
        lines.append(f"- {event.event_contract_key}: {event.event_name}")
        lines.append(f"  component: {event.component_contract_key}")
        lines.append(f"  enabled: {event.enabled}")
        lines.append(f"  passive: {event.passive}")
        lines.append(f"  blocked: {event.blocked_action}")
    lines.append("Test hooks:")
    for hook in report.test_hooks:
        lines.append(f"- {hook.test_hook_key}: {hook.test_id}")
        lines.append(f"  component: {hook.component_contract_key}")
        lines.append(f"  passive: {hook.passive}")
    lines.append("Fixture contracts:")
    for fixture in report.fixture_contracts:
        lines.append(f"- {fixture.fixture_contract_key}: {fixture.fixture_key}")
        lines.append(f"  component: {fixture.component_contract_key}")
        lines.append(f"  write file: {fixture.write_file}")
        lines.append(f"  passive: {fixture.passive}")
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


def format_controller_brain_live_desktop_component_contract_report(
    report: ControllerBrainLiveDesktopComponentContractReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing desktop component-contract text."""

    source = (
        build_controller_brain_live_desktop_component_contract_report()
        if report is None
        else report
    )
    return passive_report_lines(_HEADER, _format_desktop_component_contract_body(source))


def _pop_desktop_component_contract_cli_value(remaining: list[str]) -> str:
    if not remaining:
        raise ValueError(_ARG_ERROR)
    return remaining.pop(0)


def _parse_desktop_component_contract_cli_args(argv: Sequence[str]) -> dict[str, object]:
    component_contract_label = _DEFAULT_COMPONENT_CONTRACT_LABEL
    selector_prefix = _DEFAULT_SELECTOR_PREFIX
    json_output = False
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
        elif option == "--component-contract-label":
            component_contract_label = _normalize_component_contract_label(
                _pop_desktop_component_contract_cli_value(remaining)
            )
        elif option == "--selector-prefix":
            selector_prefix = _normalize_selector_prefix(
                _pop_desktop_component_contract_cli_value(remaining)
            )
        else:
            raise ValueError(_ARG_ERROR)
    return {
        "component_contract_label": component_contract_label,
        "selector_prefix": selector_prefix,
        "json_output": json_output,
    }


def _handle_desktop_component_contract_report(
    *,
    component_contract_label: str,
    selector_prefix: str,
    json_output: bool,
) -> int:
    if json_output:
        sys.stdout.write(
            json.dumps(
                build_controller_brain_live_desktop_component_contract_payload(
                    component_contract_label=component_contract_label,
                    selector_prefix=selector_prefix,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0
    report = build_controller_brain_live_desktop_component_contract_report(
        component_contract_label=component_contract_label,
        selector_prefix=selector_prefix,
    )
    sys.stdout.write(
        "\n".join(format_controller_brain_live_desktop_component_contract_report(report))
    )
    sys.stdout.write("\n")
    return 0


def _format_desktop_component_contract_error(exc: Exception) -> str:
    return f"Error: {exc}"


CONTROLLER_BRAIN_LIVE_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="controller-brain-live-desktop-component-contract-report",
    summary="Print passive controller-brain desktop component API contracts.",
    args_parser=_parse_desktop_component_contract_cli_args,
    handler=_handle_desktop_component_contract_report,
    error_formatter=_format_desktop_component_contract_error,
)

register(CONTROLLER_BRAIN_LIVE_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND)

__all__ = (
    "BASE_BLOCKED_ACTIONS",
    "BASE_SAFETY_LINES",
    "CONTROLLER_BRAIN_LIVE_DESKTOP_COMPONENT_CONTRACT_CLI_COMMAND",
    "ControllerBrainDesktopComponentAcceptanceCheck",
    "ControllerBrainDesktopComponentContractBinding",
    "ControllerBrainDesktopComponentEventContract",
    "ControllerBrainDesktopComponentFixtureContract",
    "ControllerBrainDesktopComponentPropContract",
    "ControllerBrainDesktopComponentTestHook",
    "ControllerBrainLiveDesktopComponentContractReport",
    "DESKTOP_COMPONENT_CONTRACT_STATUS",
    "DESKTOP_COMPONENT_CONTRACT_VERSION",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SOURCE_DESKTOP_APP_PLAN_REPORT",
    "SOURCE_MODULE",
    "_component_contract_key_from_component_file_key",
    "_desktop_component_contract_count",
    "_desktop_component_contract_slug",
    "_desktop_component_contract_unique_tuple",
    "_normalize_component_contract_label",
    "_normalize_selector_prefix",
    "_prop_contract_key_from_state_slice_key",
    "build_controller_brain_live_desktop_component_contract_payload",
    "build_controller_brain_live_desktop_component_contract_report",
    "format_controller_brain_live_desktop_component_contract_report",
)
