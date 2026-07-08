"""Passive shadow-dispatch rehearsal for future controller-brain runtimes."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from .controller_brain_live_bridge_readiness import (
    BRIDGE_READINESS_STATUS,
    BRIDGE_READINESS_VERSION,
    ControllerBrainBridgeContractPacket,
    build_controller_brain_live_bridge_readiness_report,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain live dispatch rehearsal"
SOURCE_MODULE: Final[str] = "reports.controller_brain_live_dispatch_rehearsal"
DISPATCH_REHEARSAL_VERSION: Final[str] = "controller-brain-live-dispatch-rehearsal-v1"
DISPATCH_REHEARSAL_STATUS: Final[str] = "shadow-dispatch-blocked"
SOURCE_BRIDGE_READINESS_REPORT: Final[str] = "controller-brain-live-bridge-readiness-report"
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-brain dispatch rehearsal metadata only",
    "composes controller-brain bridge readiness only",
    "shadow dispatch decisions are metadata only",
    "transport gates are metadata only",
    "JSON/stdout only",
    "no MIDI controller input",
    "no MIDI learn or raw CC capture",
    "no runtime reducer execution",
    "no WebSocket command dispatch",
    "no state-store mutation",
    "no controller feedback emission",
    "no MIDI sending",
    "no port opening",
    "no snapshot mutation",
    "no hardware mutation",
    "no hardware required",
)
BASE_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "open controller input adapter",
    "execute live state reducer",
    "dispatch controller runtime command",
    "dispatch Cockpit WebSocket commands",
    "emit controller feedback",
    "open MIDI output",
    "send hardware MIDI",
    "mutate a snapshot",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-live-dispatch-rehearsal-report",
    "python -m rytm_randomizer.cli controller-brain-live-dispatch-rehearsal-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-bridge-readiness-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-state-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainDispatchDecision:
    """One passive shadow-dispatch decision for a future bridge packet."""

    decision_key: str
    order: int
    source_packet_key: str
    source_kind: str
    dispatch_group: str
    shadow_command: str
    dispatch_status: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainDispatchGroup:
    """One passive summary of shadow dispatch decisions by bridge role."""

    name: str
    decision_count: int
    source_kind: str
    dispatch_status: str
    blocked_action: str
    safety_note: str


@dataclass(frozen=True)
class ControllerBrainTransportGate:
    """One passive transport gate that keeps active dispatch blocked."""

    name: str
    status: str
    blocked: bool
    evidence: str
    blocked_action: str
    operator_action: str
    safety_note: str


@dataclass(frozen=True)
class ControllerBrainLiveDispatchRehearsalReport:
    """Passive shadow-dispatch rehearsal derived from bridge readiness."""

    title: str
    dispatch_rehearsal_version: str
    dispatch_rehearsal_status: str
    session_label: str
    source_report: str
    source_bridge_readiness_version: str
    source_bridge_readiness_status: str
    source_contract_packet_count: int
    dispatch_decisions: tuple[ControllerBrainDispatchDecision, ...]
    dispatch_groups: tuple[ControllerBrainDispatchGroup, ...]
    transport_gates: tuple[ControllerBrainTransportGate, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def dispatch_decision_count(self) -> int:
        """Return shadow-dispatch decision count for summaries and JSON."""

        return _dispatch_rehearsal_count(self.dispatch_decisions)

    @property
    def dispatch_group_count(self) -> int:
        """Return dispatch group count for summaries and JSON."""

        return _dispatch_rehearsal_count(self.dispatch_groups)

    @property
    def transport_gate_count(self) -> int:
        """Return transport gate count for summaries and JSON."""

        return _dispatch_rehearsal_count(self.transport_gates)

    @property
    def blocked_transport_gate_count(self) -> int:
        """Return blocked transport gate count for summaries and JSON."""

        return _dispatch_rehearsal_count(
            tuple(gate for gate in self.transport_gates if gate.blocked)
        )


def _dispatch_rehearsal_unique_tuple(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return tuple(values)


def _dispatch_rehearsal_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def _dispatch_rehearsal_count(values: Sequence[object]) -> int:
    return len(values)


def _shadow_command_from_packet(packet: ControllerBrainBridgeContractPacket) -> str:
    packet_namespace = packet.packet_key.removeprefix("bridge.packet.")
    command_slug = packet_namespace.split(".", maxsplit=1)[-1]
    return f"shadow.{packet.target_bridge_role}.{command_slug}"


def _dispatch_decision_from_packet(
    packet: ControllerBrainBridgeContractPacket,
) -> ControllerBrainDispatchDecision:
    return ControllerBrainDispatchDecision(
        decision_key=packet.packet_key.replace("bridge.packet.", "dispatch.decision.", 1),
        order=packet.order,
        source_packet_key=packet.packet_key,
        source_kind=packet.source_kind,
        dispatch_group=packet.target_bridge_role,
        shadow_command=_shadow_command_from_packet(packet),
        dispatch_status="blocked-shadow-only",
        passive=True,
        evidence=f"{packet.packet_key} rehearses {packet.target_bridge_role} without dispatch",
        blocked_action=packet.blocked_action,
    )


def _dispatch_decisions(
    packets: Sequence[ControllerBrainBridgeContractPacket],
) -> tuple[ControllerBrainDispatchDecision, ...]:
    return tuple(_dispatch_decision_from_packet(packet) for packet in packets)


def _dispatch_groups(
    decisions: Sequence[ControllerBrainDispatchDecision],
) -> tuple[ControllerBrainDispatchGroup, ...]:
    groups: list[ControllerBrainDispatchGroup] = []
    for name, source_kind, blocked_action in (
        ("state-reducer", "state_row", "execute live state reducer"),
        ("queue-reducer", "queued_intent", "dispatch controller runtime command"),
        ("audit-ledger", "audit_event", "write bridge audit side effects"),
    ):
        count = _dispatch_rehearsal_count(
            tuple(decision for decision in decisions if decision.dispatch_group == name)
        )
        groups.append(
            ControllerBrainDispatchGroup(
                name=name,
                decision_count=count,
                source_kind=source_kind,
                dispatch_status="blocked-shadow-only",
                blocked_action=blocked_action,
                safety_note=f"{name} decisions are passive metadata only",
            )
        )
    return tuple(groups)


def _transport_gates() -> tuple[ControllerBrainTransportGate, ...]:
    return (
        ControllerBrainTransportGate(
            name="controller-input",
            status="blocked",
            blocked=True,
            evidence="no controller input adapter is opened by dispatch rehearsal",
            blocked_action="open controller input adapter",
            operator_action="approve the controller adapter before any input opens",
            safety_note="this report never opens MIDI controller input",
        ),
        ControllerBrainTransportGate(
            name="gesture-runtime",
            status="blocked",
            blocked=True,
            evidence="shadow decisions do not execute live reducers",
            blocked_action="execute live state reducer",
            operator_action="implement reducer execution behind a separate active gate",
            safety_note="this report never executes runtime reducers",
        ),
        ControllerBrainTransportGate(
            name="websocket-dispatch",
            status="blocked",
            blocked=True,
            evidence="no Cockpit WebSocket command is dispatched",
            blocked_action="dispatch Cockpit WebSocket commands",
            operator_action="define WebSocket acknowledgements before dispatch",
            safety_note="this report never dispatches WebSocket commands",
        ),
        ControllerBrainTransportGate(
            name="controller-feedback",
            status="blocked",
            blocked=True,
            evidence="no LEDs, rings, displays, or controller feedback are emitted",
            blocked_action="emit controller feedback",
            operator_action="define feedback semantics before controller output",
            safety_note="this report emits no controller feedback",
        ),
        ControllerBrainTransportGate(
            name="midi-output",
            status="blocked",
            blocked=True,
            evidence="no MIDI output path is opened",
            blocked_action="open MIDI output",
            operator_action="use an explicit armed path for real output",
            safety_note="passive CLI never opens real MIDI ports",
        ),
        ControllerBrainTransportGate(
            name="hardware-send",
            status="blocked",
            blocked=True,
            evidence="hardware sends remain outside this passive rehearsal",
            blocked_action="send hardware MIDI",
            operator_action="send only through separately approved armed flows",
            safety_note="this report sends no MIDI",
        ),
        ControllerBrainTransportGate(
            name="snapshot-mutation",
            status="blocked",
            blocked=True,
            evidence="snapshot mutation remains outside dispatch rehearsal",
            blocked_action="mutate a snapshot",
            operator_action="mutate snapshots only through approved armed shell flows",
            safety_note="this report mutates no snapshots",
        ),
    )


def build_controller_brain_live_dispatch_rehearsal_report(
    *,
    session_label: str = "Live Session",
) -> ControllerBrainLiveDispatchRehearsalReport:
    """Build passive shadow-dispatch metadata from bridge-readiness packets."""

    bridge = build_controller_brain_live_bridge_readiness_report(session_label=session_label)
    decisions = _dispatch_decisions(bridge.contract_packets)
    groups = _dispatch_groups(decisions)
    gates = _transport_gates()
    return ControllerBrainLiveDispatchRehearsalReport(
        title=REPORT_TITLE,
        dispatch_rehearsal_version=DISPATCH_REHEARSAL_VERSION,
        dispatch_rehearsal_status=DISPATCH_REHEARSAL_STATUS,
        session_label=session_label,
        source_report=SOURCE_BRIDGE_READINESS_REPORT,
        source_bridge_readiness_version=BRIDGE_READINESS_VERSION,
        source_bridge_readiness_status=BRIDGE_READINESS_STATUS,
        source_contract_packet_count=bridge.contract_packet_count,
        dispatch_decisions=decisions,
        dispatch_groups=groups,
        transport_gates=gates,
        blocked_actions=_dispatch_rehearsal_unique_tuple(
            BASE_BLOCKED_ACTIONS,
            bridge.blocked_actions,
        ),
        safety_lines=_dispatch_rehearsal_unique_tuple(
            BASE_SAFETY_LINES,
            bridge.safety_lines,
        ),
        replay_commands=REPLAY_COMMANDS,
    )


def _dispatch_decision_to_payload(
    decision: ControllerBrainDispatchDecision,
) -> dict[str, object]:
    return {
        "decision_key": decision.decision_key,
        "order": decision.order,
        "source_packet_key": decision.source_packet_key,
        "source_kind": decision.source_kind,
        "dispatch_group": decision.dispatch_group,
        "shadow_command": decision.shadow_command,
        "dispatch_status": decision.dispatch_status,
        "passive": decision.passive,
        "evidence": decision.evidence,
        "blocked_action": decision.blocked_action,
    }


def _dispatch_group_to_payload(group: ControllerBrainDispatchGroup) -> dict[str, object]:
    return {
        "name": group.name,
        "decision_count": group.decision_count,
        "source_kind": group.source_kind,
        "dispatch_status": group.dispatch_status,
        "blocked_action": group.blocked_action,
        "safety_note": group.safety_note,
    }


def _transport_gate_to_payload(gate: ControllerBrainTransportGate) -> dict[str, object]:
    return {
        "name": gate.name,
        "status": gate.status,
        "blocked": gate.blocked,
        "evidence": gate.evidence,
        "blocked_action": gate.blocked_action,
        "operator_action": gate.operator_action,
        "safety_note": gate.safety_note,
    }


def build_controller_brain_live_dispatch_rehearsal_payload(
    *,
    session_label: str = "Live Session",
) -> dict[str, object]:
    """Return JSON-ready passive dispatch rehearsal metadata."""

    report = build_controller_brain_live_dispatch_rehearsal_report(session_label=session_label)
    return {
        "controller_brain_live_dispatch_rehearsal": {
            "title": report.title,
            "dispatch_rehearsal_version": report.dispatch_rehearsal_version,
            "dispatch_rehearsal_status": report.dispatch_rehearsal_status,
            "session_label": report.session_label,
            "source_report": report.source_report,
            "source_bridge_readiness_version": report.source_bridge_readiness_version,
            "source_bridge_readiness_status": report.source_bridge_readiness_status,
            "source_contract_packet_count": report.source_contract_packet_count,
            "dispatch_decision_count": report.dispatch_decision_count,
            "dispatch_group_count": report.dispatch_group_count,
            "transport_gate_count": report.transport_gate_count,
            "blocked_transport_gate_count": report.blocked_transport_gate_count,
            "dispatch_decisions": [
                _dispatch_decision_to_payload(decision) for decision in report.dispatch_decisions
            ],
            "dispatch_groups": [
                _dispatch_group_to_payload(group) for group in report.dispatch_groups
            ],
            "transport_gates": [
                _transport_gate_to_payload(gate) for gate in report.transport_gates
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def _format_dispatch_rehearsal_body(
    report: ControllerBrainLiveDispatchRehearsalReport,
) -> list[str]:
    lines = [
        "Controller brain live dispatch rehearsal:",
        f"- version: {report.dispatch_rehearsal_version}",
        f"- status: {report.dispatch_rehearsal_status}",
        f"- session: {report.session_label}",
        f"- source bridge: {report.source_report}",
        f"- source bridge version: {report.source_bridge_readiness_version}",
        f"- source bridge status: {report.source_bridge_readiness_status}",
        f"- source contract packets: {report.source_contract_packet_count}",
        f"- dispatch decisions: {report.dispatch_decision_count}",
        f"- dispatch groups: {report.dispatch_group_count}",
        f"- transport gates: {report.transport_gate_count}",
        f"- blocked transport gates: {report.blocked_transport_gate_count}",
        "Shadow dispatch decisions:",
    ]
    for decision in report.dispatch_decisions:
        lines.append(
            f"- {decision.decision_key}: " f"{decision.dispatch_group} / {decision.dispatch_status}"
        )
        lines.append(f"  source: {decision.source_kind} / {decision.source_packet_key}")
        lines.append(f"  shadow command: {decision.shadow_command}")
        lines.append(f"  evidence: {decision.evidence}")
        lines.append(f"  blocked: {decision.blocked_action}")
    lines.append("Dispatch groups:")
    for group in report.dispatch_groups:
        lines.append(f"- {group.name}: {group.decision_count} decision(s)")
        lines.append(f"  status: {group.dispatch_status}")
        lines.append(f"  blocked: {group.blocked_action}")
        lines.append(f"  safety: {group.safety_note}")
    lines.append("Transport gates:")
    for gate in report.transport_gates:
        lines.append(f"- {gate.name}: {gate.status} / blocked={gate.blocked}")
        lines.append(f"  evidence: {gate.evidence}")
        lines.append(f"  operator action: {gate.operator_action}")
        lines.append(f"  blocked: {gate.blocked_action}")
        lines.append(f"  safety: {gate.safety_note}")
    lines.append("Blocked active actions:")
    lines.extend(f"- {action}" for action in report.blocked_actions)
    lines.append("Replay commands:")
    lines.extend(f"- {command}" for command in report.replay_commands)
    lines.append("Safety:")
    lines.extend(f"- {line}" for line in report.safety_lines)
    return lines


def format_controller_brain_live_dispatch_rehearsal_report(
    report: ControllerBrainLiveDispatchRehearsalReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing dispatch rehearsal text."""

    source = build_controller_brain_live_dispatch_rehearsal_report() if report is None else report
    return passive_report_lines(_HEADER, _format_dispatch_rehearsal_body(source))


CONTROLLER_BRAIN_LIVE_DISPATCH_REHEARSAL_CLI_COMMAND: Final[CliCommand] = (
    make_passive_report_command(
        "controller-brain-live-dispatch-rehearsal-report",
        "Print the passive controller-brain live dispatch rehearsal contract.",
        format_lines=lambda: format_controller_brain_live_dispatch_rehearsal_report(),
        build_payload=build_controller_brain_live_dispatch_rehearsal_payload,
    )
)

register(CONTROLLER_BRAIN_LIVE_DISPATCH_REHEARSAL_CLI_COMMAND)

__all__ = (
    "BASE_BLOCKED_ACTIONS",
    "BASE_SAFETY_LINES",
    "CONTROLLER_BRAIN_LIVE_DISPATCH_REHEARSAL_CLI_COMMAND",
    "ControllerBrainDispatchDecision",
    "ControllerBrainDispatchGroup",
    "ControllerBrainLiveDispatchRehearsalReport",
    "ControllerBrainTransportGate",
    "DISPATCH_REHEARSAL_STATUS",
    "DISPATCH_REHEARSAL_VERSION",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SOURCE_BRIDGE_READINESS_REPORT",
    "SOURCE_MODULE",
    "build_controller_brain_live_dispatch_rehearsal_payload",
    "build_controller_brain_live_dispatch_rehearsal_report",
    "format_controller_brain_live_dispatch_rehearsal_report",
)
