"""Passive desktop blueprint metadata for future controller-brain Cockpit work."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from .controller_brain_live_implementation_bridge import (
    IMPLEMENTATION_BRIDGE_STATUS,
    IMPLEMENTATION_BRIDGE_VERSION,
    ControllerBrainImplementationBinding,
    ControllerBrainImplementationFixtureBundle,
    build_controller_brain_live_implementation_bridge_report,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain live desktop blueprint"
SOURCE_MODULE: Final[str] = "reports.controller_brain_live_desktop_blueprint"
DESKTOP_BLUEPRINT_VERSION: Final[str] = "controller-brain-live-desktop-blueprint-v1"
DESKTOP_BLUEPRINT_STATUS: Final[str] = "desktop-blueprint-passive"
SOURCE_IMPLEMENTATION_BRIDGE_REPORT: Final[str] = (
    "controller-brain-live-implementation-bridge-report"
)
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-brain desktop blueprint metadata only",
    "composes controller-brain implementation bridge only",
    "desktop regions are declarative metadata only",
    "component contracts are declarative metadata only",
    "view-model bindings are declarative metadata only",
    "fixture hints are metadata only",
    "acceptance checks are metadata only",
    "JSON/stdout only",
    "no GUI launch",
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
    "start GUI renderer",
    "mount desktop regions",
    "mount component contracts",
    "execute live state reducer",
    "dispatch Cockpit WebSocket commands",
    "emit controller feedback",
    "open MIDI output",
    "mutate a snapshot",
    "write fixture files",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-live-desktop-blueprint-report",
    "python -m rytm_randomizer.cli controller-brain-live-desktop-blueprint-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-implementation-bridge-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-cockpit-handoff-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainDesktopRegion:
    """One disabled desktop region derived from controller-brain implementation metadata."""

    region_key: str
    order: int
    label: str
    layout_area: str
    source_component_key: str
    status: str
    enabled: bool
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopComponentContract:
    """One disabled component contract mapped from an implementation binding."""

    component_key: str
    order: int
    source_binding_key: str
    region_key: str
    selector: str
    view_model_path: str
    status: str
    enabled: bool
    passive: bool
    evidence: str
    blocked_action: str
    source_blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopViewModelBinding:
    """One disabled view-model binding for a future desktop component."""

    binding_key: str
    order: int
    source_component_key: str
    source_binding_key: str
    state_path: str
    target_prop: str
    enabled: bool
    passive: bool
    evidence: str


@dataclass(frozen=True)
class ControllerBrainDesktopFixtureHint:
    """One passive fixture hint for future desktop GUI tests."""

    fixture_key: str
    order: int
    source_bundle_key: str
    fixture_scope: str
    status: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDesktopAcceptanceCheck:
    """One passive acceptance check for future desktop GUI work."""

    check_key: str
    order: int
    status: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainLiveDesktopBlueprintReport:
    """Passive desktop blueprint metadata derived from implementation bindings."""

    title: str
    desktop_blueprint_version: str
    desktop_blueprint_status: str
    session_label: str
    source_report: str
    source_implementation_bridge_version: str
    source_implementation_bridge_status: str
    source_binding_count: int
    desktop_regions: tuple[ControllerBrainDesktopRegion, ...]
    component_contracts: tuple[ControllerBrainDesktopComponentContract, ...]
    view_model_bindings: tuple[ControllerBrainDesktopViewModelBinding, ...]
    fixture_hints: tuple[ControllerBrainDesktopFixtureHint, ...]
    acceptance_checks: tuple[ControllerBrainDesktopAcceptanceCheck, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def region_count(self) -> int:
        """Return desktop region count for summaries and JSON."""

        return _desktop_blueprint_count(self.desktop_regions)

    @property
    def component_contract_count(self) -> int:
        """Return component contract count for summaries and JSON."""

        return _desktop_blueprint_count(self.component_contracts)

    @property
    def view_model_binding_count(self) -> int:
        """Return view-model binding count for summaries and JSON."""

        return _desktop_blueprint_count(self.view_model_bindings)

    @property
    def fixture_hint_count(self) -> int:
        """Return fixture hint count for summaries and JSON."""

        return _desktop_blueprint_count(self.fixture_hints)

    @property
    def acceptance_check_count(self) -> int:
        """Return acceptance check count for summaries and JSON."""

        return _desktop_blueprint_count(self.acceptance_checks)


def _desktop_blueprint_unique_tuple(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return tuple(values)


def _desktop_blueprint_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def _desktop_blueprint_count(values: Sequence[object]) -> int:
    return len(values)


def _component_key_from_binding_key(binding_key: str) -> str:
    suffix = binding_key.removeprefix("implementation.binding.")
    return f"desktop.component.{suffix}"


def _region_key_from_component_key(component_key: str) -> str:
    component_regions = {
        "controller-feedback-preview-card": "desktop.region.controller-feedback-preview",
        "controller-output-gate-card": "desktop.region.controller-output-gates",
        "blocked-runtime-control-card": "desktop.region.blocked-runtime-controls",
        "operator-replay-card": "desktop.region.operator-replay",
        "fixture-bundle-card": "desktop.region.fixture-review",
        "acceptance-check-card": "desktop.region.acceptance-review",
    }
    return component_regions.get(
        component_key,
        f"desktop.region.{_desktop_blueprint_slug(component_key)}",
    )


def _controller_brain_desktop_regions() -> tuple[ControllerBrainDesktopRegion, ...]:
    rows = (
        (
            "desktop.region.controller-feedback-preview",
            "Controller Feedback Preview",
            "feedback-preview",
            "controller-feedback-preview-card",
        ),
        (
            "desktop.region.controller-output-gates",
            "Controller Output Gates",
            "output-gates",
            "controller-output-gate-card",
        ),
        (
            "desktop.region.blocked-runtime-controls",
            "Blocked Runtime Controls",
            "blocked-controls",
            "blocked-runtime-control-card",
        ),
        (
            "desktop.region.operator-replay",
            "Operator Replay",
            "operator-replay",
            "operator-replay-card",
        ),
        (
            "desktop.region.fixture-review",
            "Fixture Review",
            "fixture-review",
            "fixture-bundle-card",
        ),
        (
            "desktop.region.acceptance-review",
            "Acceptance Review",
            "acceptance-review",
            "acceptance-check-card",
        ),
    )
    return tuple(
        ControllerBrainDesktopRegion(
            region_key=region_key,
            order=index + 1,
            label=label,
            layout_area=layout_area,
            source_component_key=source_component_key,
            status="disabled-region-ready",
            enabled=False,
            passive=True,
            evidence=f"{label} is declared for future Cockpit desktop mounting",
            blocked_action="mount desktop regions",
        )
        for index, (region_key, label, layout_area, source_component_key) in enumerate(rows)
    )


def _component_contract_from_binding(
    binding: ControllerBrainImplementationBinding,
) -> ControllerBrainDesktopComponentContract:
    component_key = _component_key_from_binding_key(binding.binding_key)
    return ControllerBrainDesktopComponentContract(
        component_key=component_key,
        order=binding.order,
        source_binding_key=binding.binding_key,
        region_key=_region_key_from_component_key(binding.component_key),
        selector=binding.selector,
        view_model_path=binding.view_model_path,
        status="disabled-component-ready",
        enabled=False,
        passive=True,
        evidence=f"{binding.binding_key} is mapped as a disabled desktop component contract",
        blocked_action="mount component contracts",
        source_blocked_action=binding.blocked_action,
    )


def _controller_brain_component_contracts(
    bindings: Sequence[ControllerBrainImplementationBinding],
) -> tuple[ControllerBrainDesktopComponentContract, ...]:
    return tuple(_component_contract_from_binding(binding) for binding in bindings)


def _view_model_binding_from_component(
    component: ControllerBrainDesktopComponentContract,
) -> ControllerBrainDesktopViewModelBinding:
    suffix = component.component_key.removeprefix("desktop.component.")
    return ControllerBrainDesktopViewModelBinding(
        binding_key=f"desktop.view-model.{suffix}",
        order=component.order,
        source_component_key=component.component_key,
        source_binding_key=component.source_binding_key,
        state_path=component.view_model_path,
        target_prop="viewModel",
        enabled=False,
        passive=True,
        evidence=f"{component.component_key} remains a disabled future view-model binding",
    )


def _controller_brain_view_model_bindings(
    components: Sequence[ControllerBrainDesktopComponentContract],
) -> tuple[ControllerBrainDesktopViewModelBinding, ...]:
    return tuple(_view_model_binding_from_component(component) for component in components)


def _fixture_hint_from_bundle(
    bundle: ControllerBrainImplementationFixtureBundle,
) -> ControllerBrainDesktopFixtureHint:
    fixture_key = bundle.bundle_key.removeprefix("fixture-")
    return ControllerBrainDesktopFixtureHint(
        fixture_key=f"desktop.fixture.{fixture_key}",
        order=bundle.order,
        source_bundle_key=bundle.bundle_key,
        fixture_scope=bundle.target_scope,
        status="fixture-hint-ready",
        passive=True,
        evidence=f"{bundle.bundle_key} can seed future desktop test fixtures",
        blocked_action="write fixture files",
    )


def _controller_brain_fixture_hints(
    bundles: Sequence[ControllerBrainImplementationFixtureBundle],
) -> tuple[ControllerBrainDesktopFixtureHint, ...]:
    return tuple(_fixture_hint_from_bundle(bundle) for bundle in bundles)


def _controller_brain_acceptance_checks() -> tuple[ControllerBrainDesktopAcceptanceCheck, ...]:
    rows = (
        (
            "source-implementation-bridge-ready",
            "source implementation bridge is available as passive JSON",
            "mount component contracts",
        ),
        (
            "region-coverage",
            "desktop regions cover preview, gates, blocked controls, replay, fixtures, and checks",
            "mount desktop regions",
        ),
        (
            "component-contract-coverage",
            "every implementation binding has one disabled component contract",
            "mount component contracts",
        ),
        (
            "view-model-binding-coverage",
            "every component contract has one disabled view-model binding",
            "execute live state reducer",
        ),
        (
            "fixture-hint-coverage",
            "every implementation fixture bundle has one desktop fixture hint",
            "write fixture files",
        ),
        (
            "replay-command",
            "operator replay commands remain copy-ready passive CLI commands",
            "dispatch Cockpit WebSocket commands",
        ),
        (
            "passive-boundary",
            "desktop blueprint launches no GUI, writes no files, opens no ports, and sends no MIDI",
            "open MIDI output",
        ),
    )
    return tuple(
        ControllerBrainDesktopAcceptanceCheck(
            check_key=key,
            order=index + 1,
            status="ready",
            passive=True,
            evidence=evidence,
            blocked_action=blocked_action,
        )
        for index, (key, evidence, blocked_action) in enumerate(rows)
    )


def build_controller_brain_live_desktop_blueprint_report(
    *,
    session_label: str = "Live Session",
) -> ControllerBrainLiveDesktopBlueprintReport:
    """Build passive future-desktop blueprint metadata from implementation bridge data."""

    implementation_bridge = build_controller_brain_live_implementation_bridge_report(
        session_label=session_label
    )
    component_contracts = _controller_brain_component_contracts(
        implementation_bridge.implementation_bindings
    )
    return ControllerBrainLiveDesktopBlueprintReport(
        title=REPORT_TITLE,
        desktop_blueprint_version=DESKTOP_BLUEPRINT_VERSION,
        desktop_blueprint_status=DESKTOP_BLUEPRINT_STATUS,
        session_label=session_label,
        source_report=SOURCE_IMPLEMENTATION_BRIDGE_REPORT,
        source_implementation_bridge_version=IMPLEMENTATION_BRIDGE_VERSION,
        source_implementation_bridge_status=IMPLEMENTATION_BRIDGE_STATUS,
        source_binding_count=implementation_bridge.binding_count,
        desktop_regions=_controller_brain_desktop_regions(),
        component_contracts=component_contracts,
        view_model_bindings=_controller_brain_view_model_bindings(component_contracts),
        fixture_hints=_controller_brain_fixture_hints(implementation_bridge.fixture_bundles),
        acceptance_checks=_controller_brain_acceptance_checks(),
        blocked_actions=_desktop_blueprint_unique_tuple(
            BASE_BLOCKED_ACTIONS,
            implementation_bridge.blocked_actions,
        ),
        safety_lines=_desktop_blueprint_unique_tuple(
            BASE_SAFETY_LINES,
            implementation_bridge.safety_lines,
        ),
        replay_commands=REPLAY_COMMANDS,
    )


def _desktop_region_to_payload(region: ControllerBrainDesktopRegion) -> dict[str, object]:
    return {
        "region_key": region.region_key,
        "order": region.order,
        "label": region.label,
        "layout_area": region.layout_area,
        "source_component_key": region.source_component_key,
        "status": region.status,
        "enabled": region.enabled,
        "passive": region.passive,
        "evidence": region.evidence,
        "blocked_action": region.blocked_action,
    }


def _component_contract_to_payload(
    component: ControllerBrainDesktopComponentContract,
) -> dict[str, object]:
    return {
        "component_key": component.component_key,
        "order": component.order,
        "source_binding_key": component.source_binding_key,
        "region_key": component.region_key,
        "selector": component.selector,
        "view_model_path": component.view_model_path,
        "status": component.status,
        "enabled": component.enabled,
        "passive": component.passive,
        "evidence": component.evidence,
        "blocked_action": component.blocked_action,
        "source_blocked_action": component.source_blocked_action,
    }


def _view_model_binding_to_payload(
    binding: ControllerBrainDesktopViewModelBinding,
) -> dict[str, object]:
    return {
        "binding_key": binding.binding_key,
        "order": binding.order,
        "source_component_key": binding.source_component_key,
        "source_binding_key": binding.source_binding_key,
        "state_path": binding.state_path,
        "target_prop": binding.target_prop,
        "enabled": binding.enabled,
        "passive": binding.passive,
        "evidence": binding.evidence,
    }


def _fixture_hint_to_payload(hint: ControllerBrainDesktopFixtureHint) -> dict[str, object]:
    return {
        "fixture_key": hint.fixture_key,
        "order": hint.order,
        "source_bundle_key": hint.source_bundle_key,
        "fixture_scope": hint.fixture_scope,
        "status": hint.status,
        "passive": hint.passive,
        "evidence": hint.evidence,
        "blocked_action": hint.blocked_action,
    }


def _acceptance_check_to_payload(
    check: ControllerBrainDesktopAcceptanceCheck,
) -> dict[str, object]:
    return {
        "check_key": check.check_key,
        "order": check.order,
        "status": check.status,
        "passive": check.passive,
        "evidence": check.evidence,
        "blocked_action": check.blocked_action,
    }


def build_controller_brain_live_desktop_blueprint_payload(
    *,
    session_label: str = "Live Session",
) -> dict[str, object]:
    """Return JSON-ready passive desktop blueprint metadata."""

    report = build_controller_brain_live_desktop_blueprint_report(session_label=session_label)
    return {
        "controller_brain_live_desktop_blueprint": {
            "title": report.title,
            "desktop_blueprint_version": report.desktop_blueprint_version,
            "desktop_blueprint_status": report.desktop_blueprint_status,
            "session_label": report.session_label,
            "source_report": report.source_report,
            "source_implementation_bridge_version": (report.source_implementation_bridge_version),
            "source_implementation_bridge_status": (report.source_implementation_bridge_status),
            "source_binding_count": report.source_binding_count,
            "region_count": report.region_count,
            "component_contract_count": report.component_contract_count,
            "view_model_binding_count": report.view_model_binding_count,
            "fixture_hint_count": report.fixture_hint_count,
            "acceptance_check_count": report.acceptance_check_count,
            "desktop_regions": [
                _desktop_region_to_payload(region) for region in report.desktop_regions
            ],
            "component_contracts": [
                _component_contract_to_payload(component)
                for component in report.component_contracts
            ],
            "view_model_bindings": [
                _view_model_binding_to_payload(binding) for binding in report.view_model_bindings
            ],
            "fixture_hints": [_fixture_hint_to_payload(hint) for hint in report.fixture_hints],
            "acceptance_checks": [
                _acceptance_check_to_payload(check) for check in report.acceptance_checks
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def _format_desktop_blueprint_body(
    report: ControllerBrainLiveDesktopBlueprintReport,
) -> list[str]:
    lines = [
        "Controller brain live desktop blueprint:",
        f"- version: {report.desktop_blueprint_version}",
        f"- status: {report.desktop_blueprint_status}",
        f"- session: {report.session_label}",
        f"- source implementation bridge: {report.source_report}",
        f"- source implementation bridge version: {report.source_implementation_bridge_version}",
        f"- source implementation bridge status: {report.source_implementation_bridge_status}",
        f"- source implementation bindings: {report.source_binding_count}",
        f"- desktop regions: {report.region_count}",
        f"- component contracts: {report.component_contract_count}",
        f"- view-model bindings: {report.view_model_binding_count}",
        f"- fixture hints: {report.fixture_hint_count}",
        f"- acceptance checks: {report.acceptance_check_count}",
        "Desktop regions:",
    ]
    for region in report.desktop_regions:
        lines.append(f"- {region.region_key}: {region.label}")
        lines.append(f"  layout: {region.layout_area}")
        lines.append(f"  source component: {region.source_component_key}")
        lines.append(f"  enabled: {region.enabled}")
        lines.append(f"  passive: {region.passive}")
        lines.append(f"  evidence: {region.evidence}")
        lines.append(f"  blocked: {region.blocked_action}")
    lines.append("Component contracts:")
    for component in report.component_contracts:
        lines.append(f"- {component.component_key}: {component.status}")
        lines.append(f"  source binding: {component.source_binding_key}")
        lines.append(f"  region: {component.region_key}")
        lines.append(f"  selector: {component.selector}")
        lines.append(f"  view model: {component.view_model_path}")
        lines.append(f"  enabled: {component.enabled}")
        lines.append(f"  passive: {component.passive}")
        lines.append(f"  blocked: {component.blocked_action}")
    lines.append("View-model bindings:")
    for binding in report.view_model_bindings:
        lines.append(f"- {binding.binding_key}: {binding.target_prop}")
        lines.append(f"  source component: {binding.source_component_key}")
        lines.append(f"  source binding: {binding.source_binding_key}")
        lines.append(f"  state: {binding.state_path}")
        lines.append(f"  enabled: {binding.enabled}")
        lines.append(f"  passive: {binding.passive}")
    lines.append("Fixture hints:")
    for hint in report.fixture_hints:
        lines.append(f"- {hint.fixture_key}: {hint.status}")
        lines.append(f"  source bundle: {hint.source_bundle_key}")
        lines.append(f"  scope: {hint.fixture_scope}")
        lines.append(f"  passive: {hint.passive}")
        lines.append(f"  blocked: {hint.blocked_action}")
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


def format_controller_brain_live_desktop_blueprint_report(
    report: ControllerBrainLiveDesktopBlueprintReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing desktop blueprint text."""

    source = build_controller_brain_live_desktop_blueprint_report() if report is None else report
    return passive_report_lines(_HEADER, _format_desktop_blueprint_body(source))


CONTROLLER_BRAIN_LIVE_DESKTOP_BLUEPRINT_CLI_COMMAND: Final[CliCommand] = (
    make_passive_report_command(
        "controller-brain-live-desktop-blueprint-report",
        "Print the passive controller-brain live desktop blueprint contract.",
        format_lines=lambda: format_controller_brain_live_desktop_blueprint_report(),
        build_payload=build_controller_brain_live_desktop_blueprint_payload,
    )
)

register(CONTROLLER_BRAIN_LIVE_DESKTOP_BLUEPRINT_CLI_COMMAND)

__all__ = (
    "BASE_BLOCKED_ACTIONS",
    "BASE_SAFETY_LINES",
    "CONTROLLER_BRAIN_LIVE_DESKTOP_BLUEPRINT_CLI_COMMAND",
    "ControllerBrainDesktopAcceptanceCheck",
    "ControllerBrainDesktopComponentContract",
    "ControllerBrainDesktopFixtureHint",
    "ControllerBrainDesktopRegion",
    "ControllerBrainDesktopViewModelBinding",
    "ControllerBrainLiveDesktopBlueprintReport",
    "DESKTOP_BLUEPRINT_STATUS",
    "DESKTOP_BLUEPRINT_VERSION",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SOURCE_IMPLEMENTATION_BRIDGE_REPORT",
    "SOURCE_MODULE",
    "build_controller_brain_live_desktop_blueprint_payload",
    "build_controller_brain_live_desktop_blueprint_report",
    "format_controller_brain_live_desktop_blueprint_report",
)
