"""Passive bridge-readiness contract for future controller-brain runtimes."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from .controller_brain_live_state import (
    LIVE_STATE_STATUS,
    LIVE_STATE_VERSION,
    ControllerBrainAuditEvent,
    ControllerBrainLiveStateRow,
    ControllerBrainQueuedIntent,
    build_controller_brain_live_state_report,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain live bridge readiness"
SOURCE_MODULE: Final[str] = "reports.controller_brain_live_bridge_readiness"
BRIDGE_READINESS_VERSION: Final[str] = "controller-brain-live-bridge-readiness-v1"
BRIDGE_READINESS_STATUS: Final[str] = "blocked-awaiting-controller-bridge"
SOURCE_LIVE_STATE_REPORT: Final[str] = "controller-brain-live-state-report"
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-brain bridge readiness metadata only",
    "composes controller-brain live state only",
    "contract packets are metadata only",
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
    "write bridge audit side effects",
    "open MIDI output",
    "send hardware MIDI",
    "mutate a snapshot",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-live-bridge-readiness-report",
    "python -m rytm_randomizer.cli controller-brain-live-bridge-readiness-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-state-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-runbook-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainBridgeContractPacket:
    """One passive packet a future controller bridge may render or test."""

    packet_key: str
    order: int
    source_key: str
    source_kind: str
    target_bridge_role: str
    status: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainBridgeReadinessGate:
    """One passive readiness gate for a future controller-brain bridge."""

    name: str
    status: str
    ready: bool
    evidence: str
    blocked_action: str
    operator_action: str
    safety_note: str


@dataclass(frozen=True)
class ControllerBrainLiveBridgeReadinessReport:
    """Passive bridge-readiness view derived from the live state contract."""

    title: str
    bridge_readiness_version: str
    bridge_readiness_status: str
    session_label: str
    source_report: str
    source_live_state_version: str
    source_live_state_status: str
    state_row_count: int
    queued_intent_count: int
    audit_event_count: int
    contract_packets: tuple[ControllerBrainBridgeContractPacket, ...]
    bridge_readiness_gates: tuple[ControllerBrainBridgeReadinessGate, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def contract_packet_count(self) -> int:
        """Return bridge contract packet count for summaries and JSON."""

        return _bridge_readiness_count(self.contract_packets)

    @property
    def ready_gate_count(self) -> int:
        """Return ready gate count for summaries and JSON."""

        return _bridge_readiness_count(
            tuple(gate for gate in self.bridge_readiness_gates if gate.ready)
        )

    @property
    def blocked_gate_count(self) -> int:
        """Return blocked gate count for summaries and JSON."""

        return _bridge_readiness_count(
            tuple(gate for gate in self.bridge_readiness_gates if not gate.ready)
        )


def _bridge_readiness_unique_tuple(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return tuple(values)


def _bridge_readiness_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def _bridge_readiness_count(values: Sequence[object]) -> int:
    return len(values)


def _bridge_readiness_state_packet(
    row: ControllerBrainLiveStateRow,
) -> ControllerBrainBridgeContractPacket:
    slug = _bridge_readiness_slug(row.intent_key)
    return ControllerBrainBridgeContractPacket(
        packet_key=f"bridge.packet.state.{slug}",
        order=row.step,
        source_key=row.state_key,
        source_kind="state_row",
        target_bridge_role="state-reducer",
        status="ready",
        passive=True,
        evidence=f"{row.state_key} normalizes {row.intent_key} for future reducer input",
        blocked_action="execute live state reducer",
    )


def _bridge_readiness_queue_packet(
    intent: ControllerBrainQueuedIntent,
) -> ControllerBrainBridgeContractPacket:
    slug = _bridge_readiness_slug(intent.intent_key)
    return ControllerBrainBridgeContractPacket(
        packet_key=f"bridge.packet.queue.{slug}",
        order=intent.order,
        source_key=intent.queued_intent_key,
        source_kind="queued_intent",
        target_bridge_role="queue-reducer",
        status="ready",
        passive=True,
        evidence=f"{intent.queued_intent_key} can be rendered as a staged queue intent",
        blocked_action="dispatch controller runtime command",
    )


def _bridge_readiness_audit_packet(
    event: ControllerBrainAuditEvent,
) -> ControllerBrainBridgeContractPacket:
    slug = _bridge_readiness_slug(event.intent_key)
    return ControllerBrainBridgeContractPacket(
        packet_key=f"bridge.packet.audit.{slug}",
        order=event.order,
        source_key=event.audit_event_key,
        source_kind="audit_event",
        target_bridge_role="audit-ledger",
        status="ready",
        passive=True,
        evidence=f"{event.audit_event_key} records passive evidence for {event.intent_key}",
        blocked_action="write bridge audit side effects",
    )


def _bridge_readiness_contract_packets(
    state_rows: Sequence[ControllerBrainLiveStateRow],
    queued_intents: Sequence[ControllerBrainQueuedIntent],
    audit_events: Sequence[ControllerBrainAuditEvent],
) -> tuple[ControllerBrainBridgeContractPacket, ...]:
    return (
        *tuple(_bridge_readiness_state_packet(row) for row in state_rows),
        *tuple(_bridge_readiness_queue_packet(intent) for intent in queued_intents),
        *tuple(_bridge_readiness_audit_packet(event) for event in audit_events),
    )


def _bridge_readiness_gates(
    *,
    state_row_count: int,
    queued_intent_count: int,
    audit_event_count: int,
    contract_packet_count: int,
) -> tuple[ControllerBrainBridgeReadinessGate, ...]:
    return (
        ControllerBrainBridgeReadinessGate(
            name="state-contract",
            status="ready",
            ready=True,
            evidence=f"{state_row_count} state rows are normalized for reducer input",
            blocked_action="execute live state reducer",
            operator_action="review state rows before any runtime bridge is approved",
            safety_note="state rows are passive metadata only",
        ),
        ControllerBrainBridgeReadinessGate(
            name="queue-contract",
            status="ready",
            ready=True,
            evidence=f"{queued_intent_count} queued intents are staged as metadata",
            blocked_action="dispatch controller runtime command",
            operator_action="review queue intent ordering before active dispatch exists",
            safety_note="queue packets are passive metadata only",
        ),
        ControllerBrainBridgeReadinessGate(
            name="audit-contract",
            status="ready",
            ready=True,
            evidence=f"{audit_event_count} audit events back {contract_packet_count} packets",
            blocked_action="write bridge audit side effects",
            operator_action="review audit keys before persistent bridge storage exists",
            safety_note="audit packets are stdout/JSON metadata only",
        ),
        ControllerBrainBridgeReadinessGate(
            name="controller-input",
            status="blocked",
            ready=False,
            evidence="no controller input adapter is approved or opened",
            blocked_action="open controller input adapter",
            operator_action="design and approve the input adapter before opening ports",
            safety_note="this report never opens MIDI controller input",
        ),
        ControllerBrainBridgeReadinessGate(
            name="gesture-runtime",
            status="blocked",
            ready=False,
            evidence="no live gesture reducer executes from this metadata",
            blocked_action="execute live state reducer",
            operator_action="implement the reducer behind an explicit passive-to-active gate",
            safety_note="this report never executes a runtime reducer",
        ),
        ControllerBrainBridgeReadinessGate(
            name="websocket-dispatch",
            status="blocked",
            ready=False,
            evidence="no Cockpit or sidecar WebSocket command is dispatched",
            blocked_action="dispatch Cockpit WebSocket commands",
            operator_action="define bridge acknowledgements before runtime dispatch",
            safety_note="this report never dispatches WebSocket commands",
        ),
        ControllerBrainBridgeReadinessGate(
            name="midi-output",
            status="blocked",
            ready=False,
            evidence="no MIDI output path is opened by this passive CLI",
            blocked_action="open MIDI output",
            operator_action="use an approved --arm path for real output",
            safety_note="passive CLI must never open real MIDI ports",
        ),
        ControllerBrainBridgeReadinessGate(
            name="hardware-send",
            status="blocked",
            ready=False,
            evidence="hardware sends remain confined to explicit armed app paths",
            blocked_action="send hardware MIDI",
            operator_action="run hardware sends only after separate bridge approval",
            safety_note="this report sends no MIDI",
        ),
        ControllerBrainBridgeReadinessGate(
            name="feedback-output",
            status="blocked",
            ready=False,
            evidence="no controller LEDs, rings, or displays receive feedback",
            blocked_action="emit controller feedback",
            operator_action="define feedback semantics before emitting controller output",
            safety_note="this report emits no controller feedback",
        ),
        ControllerBrainBridgeReadinessGate(
            name="snapshot-mutation",
            status="blocked",
            ready=False,
            evidence="snapshot mutation remains outside the passive bridge-readiness packet",
            blocked_action="mutate a snapshot",
            operator_action="mutate snapshots only through approved armed shell flows",
            safety_note="this report mutates no snapshots",
        ),
    )


def build_controller_brain_live_bridge_readiness_report(
    *,
    session_label: str = "Live Session",
) -> ControllerBrainLiveBridgeReadinessReport:
    """Build passive bridge-readiness metadata from the live state contract."""

    live_state = build_controller_brain_live_state_report(session_label=session_label)
    packets = _bridge_readiness_contract_packets(
        live_state.state_rows,
        live_state.queued_intents,
        live_state.audit_events,
    )
    gates = _bridge_readiness_gates(
        state_row_count=live_state.state_row_count,
        queued_intent_count=live_state.queued_intent_count,
        audit_event_count=live_state.audit_event_count,
        contract_packet_count=len(packets),
    )
    return ControllerBrainLiveBridgeReadinessReport(
        title=REPORT_TITLE,
        bridge_readiness_version=BRIDGE_READINESS_VERSION,
        bridge_readiness_status=BRIDGE_READINESS_STATUS,
        session_label=session_label,
        source_report=SOURCE_LIVE_STATE_REPORT,
        source_live_state_version=LIVE_STATE_VERSION,
        source_live_state_status=LIVE_STATE_STATUS,
        state_row_count=live_state.state_row_count,
        queued_intent_count=live_state.queued_intent_count,
        audit_event_count=live_state.audit_event_count,
        contract_packets=packets,
        bridge_readiness_gates=gates,
        blocked_actions=_bridge_readiness_unique_tuple(
            BASE_BLOCKED_ACTIONS,
            live_state.blocked_actions,
        ),
        safety_lines=_bridge_readiness_unique_tuple(
            BASE_SAFETY_LINES,
            live_state.safety_lines,
        ),
        replay_commands=REPLAY_COMMANDS,
    )


def _bridge_readiness_contract_packet_to_payload(
    packet: ControllerBrainBridgeContractPacket,
) -> dict[str, object]:
    return {
        "packet_key": packet.packet_key,
        "order": packet.order,
        "source_key": packet.source_key,
        "source_kind": packet.source_kind,
        "target_bridge_role": packet.target_bridge_role,
        "status": packet.status,
        "passive": packet.passive,
        "evidence": packet.evidence,
        "blocked_action": packet.blocked_action,
    }


def _bridge_readiness_gate_to_payload(
    gate: ControllerBrainBridgeReadinessGate,
) -> dict[str, object]:
    return {
        "name": gate.name,
        "status": gate.status,
        "ready": gate.ready,
        "evidence": gate.evidence,
        "blocked_action": gate.blocked_action,
        "operator_action": gate.operator_action,
        "safety_note": gate.safety_note,
    }


def build_controller_brain_live_bridge_readiness_payload(
    *,
    session_label: str = "Live Session",
) -> dict[str, object]:
    """Return JSON-ready passive bridge-readiness metadata."""

    report = build_controller_brain_live_bridge_readiness_report(session_label=session_label)
    return {
        "controller_brain_live_bridge_readiness": {
            "title": report.title,
            "bridge_readiness_version": report.bridge_readiness_version,
            "bridge_readiness_status": report.bridge_readiness_status,
            "session_label": report.session_label,
            "source_report": report.source_report,
            "source_live_state_version": report.source_live_state_version,
            "source_live_state_status": report.source_live_state_status,
            "state_row_count": report.state_row_count,
            "queued_intent_count": report.queued_intent_count,
            "audit_event_count": report.audit_event_count,
            "contract_packet_count": report.contract_packet_count,
            "ready_gate_count": report.ready_gate_count,
            "blocked_gate_count": report.blocked_gate_count,
            "contract_packets": [
                _bridge_readiness_contract_packet_to_payload(packet)
                for packet in report.contract_packets
            ],
            "bridge_readiness_gates": [
                _bridge_readiness_gate_to_payload(gate) for gate in report.bridge_readiness_gates
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def _format_bridge_readiness_body(
    report: ControllerBrainLiveBridgeReadinessReport,
) -> list[str]:
    lines = [
        "Controller brain live bridge readiness:",
        f"- version: {report.bridge_readiness_version}",
        f"- status: {report.bridge_readiness_status}",
        f"- session: {report.session_label}",
        f"- source state: {report.source_report}",
        f"- source state version: {report.source_live_state_version}",
        f"- source state status: {report.source_live_state_status}",
        f"- state rows: {report.state_row_count}",
        f"- queued intents: {report.queued_intent_count}",
        f"- audit events: {report.audit_event_count}",
        f"- contract packets: {report.contract_packet_count}",
        f"- ready gates: {report.ready_gate_count}",
        f"- blocked gates: {report.blocked_gate_count}",
        "Contract packets:",
    ]
    for packet in report.contract_packets:
        lines.append(f"- {packet.packet_key}: {packet.target_bridge_role} / {packet.status}")
        lines.append(f"  source: {packet.source_kind} / {packet.source_key}")
        lines.append(f"  evidence: {packet.evidence}")
        lines.append(f"  blocked: {packet.blocked_action}")
    lines.append("Readiness gates:")
    for gate in report.bridge_readiness_gates:
        lines.append(f"- {gate.name}: {gate.status} / ready={gate.ready}")
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


def format_controller_brain_live_bridge_readiness_report(
    report: ControllerBrainLiveBridgeReadinessReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing bridge-readiness text."""

    source = build_controller_brain_live_bridge_readiness_report() if report is None else report
    return passive_report_lines(_HEADER, _format_bridge_readiness_body(source))


CONTROLLER_BRAIN_LIVE_BRIDGE_READINESS_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "controller-brain-live-bridge-readiness-report",
    "Print the passive controller-brain live bridge-readiness contract.",
    format_lines=lambda: format_controller_brain_live_bridge_readiness_report(),
    build_payload=build_controller_brain_live_bridge_readiness_payload,
)

register(CONTROLLER_BRAIN_LIVE_BRIDGE_READINESS_CLI_COMMAND)

__all__ = (
    "BASE_BLOCKED_ACTIONS",
    "BASE_SAFETY_LINES",
    "BRIDGE_READINESS_STATUS",
    "BRIDGE_READINESS_VERSION",
    "CONTROLLER_BRAIN_LIVE_BRIDGE_READINESS_CLI_COMMAND",
    "ControllerBrainBridgeContractPacket",
    "ControllerBrainBridgeReadinessGate",
    "ControllerBrainLiveBridgeReadinessReport",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SOURCE_LIVE_STATE_REPORT",
    "SOURCE_MODULE",
    "build_controller_brain_live_bridge_readiness_payload",
    "build_controller_brain_live_bridge_readiness_report",
    "format_controller_brain_live_bridge_readiness_report",
)
