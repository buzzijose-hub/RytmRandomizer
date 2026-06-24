"""Passive implementation bridge metadata for future controller-brain GUI work."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from .controller_brain_live_cockpit_handoff import (
    COCKPIT_HANDOFF_STATUS,
    COCKPIT_HANDOFF_VERSION,
    ControllerBrainCockpitHandoffCard,
    build_controller_brain_live_cockpit_handoff_report,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain live implementation bridge"
SOURCE_MODULE: Final[str] = "reports.controller_brain_live_implementation_bridge"
IMPLEMENTATION_BRIDGE_VERSION: Final[str] = "controller-brain-live-implementation-bridge-v1"
IMPLEMENTATION_BRIDGE_STATUS: Final[str] = "implementation-bridge-passive"
SOURCE_COCKPIT_HANDOFF_REPORT: Final[str] = "controller-brain-live-cockpit-handoff-report"
COMPONENT_KEY: Final[str] = "controller-feedback-preview-card"
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-brain implementation bridge metadata only",
    "composes controller-brain Cockpit handoff only",
    "implementation bindings are declarative metadata only",
    "fixture bundles are metadata only",
    "implementation gates are metadata only",
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
    "no hardware mutation",
    "no hardware required",
)
BASE_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "launch Cockpit GUI runtime",
    "mount implementation bindings",
    "start GUI renderer",
    "execute live state reducer",
    "dispatch Cockpit WebSocket commands",
    "emit controller feedback",
    "open MIDI output",
    "mutate a snapshot",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-live-implementation-bridge-report",
    "python -m rytm_randomizer.cli controller-brain-live-implementation-bridge-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-cockpit-handoff-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-feedback-rehearsal-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainImplementationBinding:
    """One disabled future GUI binding derived from a Cockpit handoff card."""

    binding_key: str
    order: int
    source_card_key: str
    component_key: str
    selector: str
    view_model_path: str
    status: str
    disabled: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainImplementationFixtureBundle:
    """One passive fixture bundle contract for future GUI implementation tests."""

    bundle_key: str
    order: int
    fixture_kind: str
    source_path: str
    target_scope: str
    passive: bool
    evidence: str


@dataclass(frozen=True)
class ControllerBrainImplementationGate:
    """One passive implementation gate for future Cockpit runtime work."""

    gate_key: str
    order: int
    status: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainLiveImplementationBridgeReport:
    """Passive implementation metadata derived from Cockpit handoff cards."""

    title: str
    implementation_bridge_version: str
    implementation_bridge_status: str
    session_label: str
    source_report: str
    source_cockpit_handoff_version: str
    source_cockpit_handoff_status: str
    source_handoff_card_count: int
    implementation_bindings: tuple[ControllerBrainImplementationBinding, ...]
    fixture_bundles: tuple[ControllerBrainImplementationFixtureBundle, ...]
    implementation_gates: tuple[ControllerBrainImplementationGate, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def binding_count(self) -> int:
        """Return implementation binding count for summaries and JSON."""

        return _implementation_count(self.implementation_bindings)

    @property
    def fixture_bundle_count(self) -> int:
        """Return fixture bundle count for summaries and JSON."""

        return _implementation_count(self.fixture_bundles)

    @property
    def implementation_gate_count(self) -> int:
        """Return implementation gate count for summaries and JSON."""

        return _implementation_count(self.implementation_gates)


def _implementation_unique_tuple(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return tuple(values)


def _implementation_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def _implementation_count(values: Sequence[object]) -> int:
    return len(values)


def _binding_suffix_from_card(card: ControllerBrainCockpitHandoffCard) -> str:
    return card.card_key.removeprefix("cockpit.card.")


def _selector_from_key(binding_key: str) -> str:
    suffix = binding_key.removeprefix("implementation.binding.")
    leaf = suffix.split(".", maxsplit=1)[-1]
    return f"{COMPONENT_KEY}--{_implementation_slug(leaf)}"


def _binding_from_card(
    card: ControllerBrainCockpitHandoffCard,
    index: int,
) -> ControllerBrainImplementationBinding:
    suffix = _binding_suffix_from_card(card)
    binding_key = f"implementation.binding.{suffix}"
    return ControllerBrainImplementationBinding(
        binding_key=binding_key,
        order=card.order,
        source_card_key=card.card_key,
        component_key=COMPONENT_KEY,
        selector=_selector_from_key(binding_key),
        view_model_path=(
            "$.controller_brain_live_implementation_bridge." f"implementation_bindings[{index}]"
        ),
        status="disabled-binding-ready",
        disabled=True,
        evidence=f"{card.card_key} is mapped as disabled implementation metadata",
        blocked_action=card.blocked_action,
    )


def _implementation_bindings(
    cards: Sequence[ControllerBrainCockpitHandoffCard],
) -> tuple[ControllerBrainImplementationBinding, ...]:
    return tuple(_binding_from_card(card, index) for index, card in enumerate(cards))


def _controller_brain_fixture_bundles() -> tuple[ControllerBrainImplementationFixtureBundle, ...]:
    rows = (
        (
            "fixture-cockpit-handoff-json",
            "source-handoff",
            "$.controller_brain_live_cockpit_handoff",
            "source Cockpit handoff fixture remains passive JSON",
        ),
        (
            "fixture-implementation-bindings-json",
            "bindings",
            "$.controller_brain_live_implementation_bridge.implementation_bindings",
            "future component bindings are captured as disabled metadata",
        ),
        (
            "fixture-disabled-controls-json",
            "disabled-controls",
            "$.controller_brain_live_implementation_bridge.blocked_actions",
            "runtime controls remain blocked for fixture assertions",
        ),
        (
            "fixture-implementation-gates-json",
            "implementation-gates",
            "$.controller_brain_live_implementation_bridge.implementation_gates",
            "implementation gates are available for future GUI tests",
        ),
        (
            "fixture-replay-commands-json",
            "replay-commands",
            "$.controller_brain_live_implementation_bridge.replay_commands",
            "operator replay commands remain passive CLI commands",
        ),
    )
    return tuple(
        ControllerBrainImplementationFixtureBundle(
            bundle_key=key,
            order=index + 1,
            fixture_kind=kind,
            source_path=source_path,
            target_scope="future GUI test harness",
            passive=True,
            evidence=evidence,
        )
        for index, (key, kind, source_path, evidence) in enumerate(rows)
    )


def _controller_brain_implementation_gates() -> tuple[ControllerBrainImplementationGate, ...]:
    rows = (
        (
            "source-handoff-ready",
            "source Cockpit handoff is available as passive JSON",
            "mount implementation bindings",
        ),
        (
            "binding-coverage",
            "every Cockpit handoff card has one disabled binding",
            "mount implementation bindings",
        ),
        (
            "fixture-coverage",
            "fixture bundles cover handoff, bindings, controls, gates, and replay",
            "start GUI renderer",
        ),
        (
            "disabled-control-coverage",
            "blocked runtime controls stay represented before active GUI work",
            "execute live state reducer",
        ),
        (
            "replay-command",
            "operator replay commands remain copy-ready passive CLI commands",
            "dispatch Cockpit WebSocket commands",
        ),
        (
            "passive-boundary",
            "implementation bridge opens no ports, launches no GUI, and sends no MIDI",
            "open MIDI output",
        ),
    )
    return tuple(
        ControllerBrainImplementationGate(
            gate_key=key,
            order=index + 1,
            status="ready",
            passive=True,
            evidence=evidence,
            blocked_action=blocked_action,
        )
        for index, (key, evidence, blocked_action) in enumerate(rows)
    )


def build_controller_brain_live_implementation_bridge_report(
    *,
    session_label: str = "Live Session",
) -> ControllerBrainLiveImplementationBridgeReport:
    """Build passive future-GUI implementation metadata from Cockpit handoff."""

    handoff = build_controller_brain_live_cockpit_handoff_report(session_label=session_label)
    bindings = _implementation_bindings(handoff.handoff_cards)
    return ControllerBrainLiveImplementationBridgeReport(
        title=REPORT_TITLE,
        implementation_bridge_version=IMPLEMENTATION_BRIDGE_VERSION,
        implementation_bridge_status=IMPLEMENTATION_BRIDGE_STATUS,
        session_label=session_label,
        source_report=SOURCE_COCKPIT_HANDOFF_REPORT,
        source_cockpit_handoff_version=COCKPIT_HANDOFF_VERSION,
        source_cockpit_handoff_status=COCKPIT_HANDOFF_STATUS,
        source_handoff_card_count=handoff.handoff_card_count,
        implementation_bindings=bindings,
        fixture_bundles=_controller_brain_fixture_bundles(),
        implementation_gates=_controller_brain_implementation_gates(),
        blocked_actions=_implementation_unique_tuple(
            BASE_BLOCKED_ACTIONS,
            handoff.blocked_actions,
        ),
        safety_lines=_implementation_unique_tuple(
            BASE_SAFETY_LINES,
            handoff.safety_lines,
        ),
        replay_commands=REPLAY_COMMANDS,
    )


def _binding_to_payload(binding: ControllerBrainImplementationBinding) -> dict[str, object]:
    return {
        "binding_key": binding.binding_key,
        "order": binding.order,
        "source_card_key": binding.source_card_key,
        "component_key": binding.component_key,
        "selector": binding.selector,
        "view_model_path": binding.view_model_path,
        "status": binding.status,
        "disabled": binding.disabled,
        "evidence": binding.evidence,
        "blocked_action": binding.blocked_action,
    }


def _fixture_bundle_to_payload(
    bundle: ControllerBrainImplementationFixtureBundle,
) -> dict[str, object]:
    return {
        "bundle_key": bundle.bundle_key,
        "order": bundle.order,
        "fixture_kind": bundle.fixture_kind,
        "source_path": bundle.source_path,
        "target_scope": bundle.target_scope,
        "passive": bundle.passive,
        "evidence": bundle.evidence,
    }


def _implementation_gate_to_payload(
    gate: ControllerBrainImplementationGate,
) -> dict[str, object]:
    return {
        "gate_key": gate.gate_key,
        "order": gate.order,
        "status": gate.status,
        "passive": gate.passive,
        "evidence": gate.evidence,
        "blocked_action": gate.blocked_action,
    }


def build_controller_brain_live_implementation_bridge_payload(
    *,
    session_label: str = "Live Session",
) -> dict[str, object]:
    """Return JSON-ready passive implementation bridge metadata."""

    report = build_controller_brain_live_implementation_bridge_report(session_label=session_label)
    return {
        "controller_brain_live_implementation_bridge": {
            "title": report.title,
            "implementation_bridge_version": report.implementation_bridge_version,
            "implementation_bridge_status": report.implementation_bridge_status,
            "session_label": report.session_label,
            "source_report": report.source_report,
            "source_cockpit_handoff_version": report.source_cockpit_handoff_version,
            "source_cockpit_handoff_status": report.source_cockpit_handoff_status,
            "source_handoff_card_count": report.source_handoff_card_count,
            "binding_count": report.binding_count,
            "fixture_bundle_count": report.fixture_bundle_count,
            "implementation_gate_count": report.implementation_gate_count,
            "implementation_bindings": [
                _binding_to_payload(binding) for binding in report.implementation_bindings
            ],
            "fixture_bundles": [
                _fixture_bundle_to_payload(bundle) for bundle in report.fixture_bundles
            ],
            "implementation_gates": [
                _implementation_gate_to_payload(gate) for gate in report.implementation_gates
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def _format_implementation_bridge_body(
    report: ControllerBrainLiveImplementationBridgeReport,
) -> list[str]:
    lines = [
        "Controller brain live implementation bridge:",
        f"- version: {report.implementation_bridge_version}",
        f"- status: {report.implementation_bridge_status}",
        f"- session: {report.session_label}",
        f"- source handoff: {report.source_report}",
        f"- source handoff version: {report.source_cockpit_handoff_version}",
        f"- source handoff status: {report.source_cockpit_handoff_status}",
        f"- source handoff cards: {report.source_handoff_card_count}",
        f"- implementation bindings: {report.binding_count}",
        f"- fixture bundles: {report.fixture_bundle_count}",
        f"- implementation gates: {report.implementation_gate_count}",
        "Implementation bindings:",
    ]
    for binding in report.implementation_bindings:
        lines.append(f"- {binding.binding_key}: {binding.status}")
        lines.append(f"  source: {binding.source_card_key}")
        lines.append(f"  component: {binding.component_key}")
        lines.append(f"  selector: {binding.selector}")
        lines.append(f"  view model: {binding.view_model_path}")
        lines.append(f"  disabled: {binding.disabled}")
        lines.append(f"  evidence: {binding.evidence}")
        lines.append(f"  blocked: {binding.blocked_action}")
    lines.append("Fixture bundles:")
    for bundle in report.fixture_bundles:
        lines.append(f"- {bundle.bundle_key}: {bundle.fixture_kind}")
        lines.append(f"  source path: {bundle.source_path}")
        lines.append(f"  target: {bundle.target_scope}")
        lines.append(f"  passive: {bundle.passive}")
        lines.append(f"  evidence: {bundle.evidence}")
    lines.append("Implementation gates:")
    for gate in report.implementation_gates:
        lines.append(f"- {gate.gate_key}: {gate.status}")
        lines.append(f"  passive: {gate.passive}")
        lines.append(f"  evidence: {gate.evidence}")
        lines.append(f"  blocked: {gate.blocked_action}")
    lines.append("Blocked active actions:")
    lines.extend(f"- {action}" for action in report.blocked_actions)
    lines.append("Replay commands:")
    lines.extend(f"- {command}" for command in report.replay_commands)
    lines.append("Safety:")
    lines.extend(f"- {line}" for line in report.safety_lines)
    return lines


def format_controller_brain_live_implementation_bridge_report(
    report: ControllerBrainLiveImplementationBridgeReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing implementation bridge text."""

    source = (
        build_controller_brain_live_implementation_bridge_report() if report is None else report
    )
    return passive_report_lines(_HEADER, _format_implementation_bridge_body(source))


CONTROLLER_BRAIN_LIVE_IMPLEMENTATION_BRIDGE_CLI_COMMAND: Final[CliCommand] = (
    make_passive_report_command(
        "controller-brain-live-implementation-bridge-report",
        "Print the passive controller-brain live implementation bridge contract.",
        format_lines=lambda: format_controller_brain_live_implementation_bridge_report(),
        build_payload=build_controller_brain_live_implementation_bridge_payload,
    )
)

register(CONTROLLER_BRAIN_LIVE_IMPLEMENTATION_BRIDGE_CLI_COMMAND)

__all__ = (
    "BASE_BLOCKED_ACTIONS",
    "BASE_SAFETY_LINES",
    "COMPONENT_KEY",
    "CONTROLLER_BRAIN_LIVE_IMPLEMENTATION_BRIDGE_CLI_COMMAND",
    "ControllerBrainImplementationBinding",
    "ControllerBrainImplementationFixtureBundle",
    "ControllerBrainImplementationGate",
    "ControllerBrainLiveImplementationBridgeReport",
    "IMPLEMENTATION_BRIDGE_STATUS",
    "IMPLEMENTATION_BRIDGE_VERSION",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SOURCE_COCKPIT_HANDOFF_REPORT",
    "SOURCE_MODULE",
    "build_controller_brain_live_implementation_bridge_payload",
    "build_controller_brain_live_implementation_bridge_report",
    "format_controller_brain_live_implementation_bridge_report",
)
