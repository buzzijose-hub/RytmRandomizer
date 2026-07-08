"""Passive controller-brain live state contract for future controller bridges."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from .controller_brain_live_runbook import (
    RUNBOOK_VERSION,
    ControllerBrainReadinessGate,
    ControllerBrainRunbookStep,
    build_controller_brain_live_runbook_report,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain live state"
SOURCE_MODULE: Final[str] = "reports.controller_brain_live_state"
LIVE_STATE_VERSION: Final[str] = "controller-brain-live-state-v1"
LIVE_STATE_STATUS: Final[str] = "passive-bridge-blocked"
SOURCE_REPORT: Final[str] = "controller-brain-live-runbook-report"
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-brain live state metadata only",
    "composes controller-brain live runbook only",
    "state rows are metadata only",
    "queued intents are metadata only",
    "audit events are metadata only",
    "JSON/stdout only",
    "no MIDI controller input",
    "no MIDI learn or raw CC capture",
    "no WebSocket command dispatch",
    "no MIDI sending",
    "no port opening",
    "no snapshot mutation",
    "no hardware mutation",
    "no hardware required",
)
BASE_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "apply live state reducer",
    "dispatch controller runtime event",
    "write controller audit ledger",
    "emit controller feedback",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-live-state-report",
    "python -m rytm_randomizer.cli controller-brain-live-state-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-runbook-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainLiveStateRow:
    """One passive controller intent as future bridge state metadata."""

    step: int
    state_key: str
    intent_key: str
    controller_assignment: str
    controller_gesture: str
    value_delta: int
    operator_goal: str
    stage_action: str
    inspect_action: str
    preview_state: str
    fire_state: str
    fire_policy: str
    recovery_action: str
    queued_intent_key: str
    audit_event_key: str
    target_device: str
    target_scope: str
    lane: str
    safety_tier: str
    blocked_action: str
    notes: str


@dataclass(frozen=True)
class ControllerBrainQueuedIntent:
    """One passive queued controller intent for future surfaces."""

    queued_intent_key: str
    order: int
    intent_key: str
    state_key: str
    preview_state: str
    fire_state: str
    stage_action: str
    recovery_action: str
    target_device: str
    target_scope: str


@dataclass(frozen=True)
class ControllerBrainAuditEvent:
    """One passive audit event that a future bridge would persist."""

    audit_event_key: str
    order: int
    intent_key: str
    state_key: str
    queued_intent_key: str
    stage_state: str
    fire_state: str
    fire_policy: str
    recovery_action: str
    evidence: str


@dataclass(frozen=True)
class ControllerBrainLiveStateReport:
    """Passive state contract derived from the controller-brain live runbook."""

    title: str
    live_state_version: str
    live_state_status: str
    session_label: str
    source_report: str
    source_runbook_version: str
    controller_profile_key: str
    controller_profile_label: str
    state_rows: tuple[ControllerBrainLiveStateRow, ...]
    queued_intents: tuple[ControllerBrainQueuedIntent, ...]
    audit_events: tuple[ControllerBrainAuditEvent, ...]
    readiness_gates: tuple[ControllerBrainReadinessGate, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def state_row_count(self) -> int:
        """Return state row count for JSON and operator summaries."""

        return _state_row_count(self.state_rows)

    @property
    def queued_intent_count(self) -> int:
        """Return queued intent count for JSON and operator summaries."""

        return _state_row_count(self.queued_intents)

    @property
    def audit_event_count(self) -> int:
        """Return audit event count for JSON and operator summaries."""

        return _state_row_count(self.audit_events)


def _live_state_unique_tuple(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return tuple(values)


def _state_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def _state_row_count(values: Sequence[object]) -> int:
    return len(values)


def _state_row_from_runbook_step(
    step: ControllerBrainRunbookStep,
) -> ControllerBrainLiveStateRow:
    slug = _state_slug(step.intent_key)
    return ControllerBrainLiveStateRow(
        step=step.step,
        state_key=f"state.{slug}",
        intent_key=step.intent_key,
        controller_assignment=step.controller_assignment,
        controller_gesture=step.controller_gesture,
        value_delta=step.value_delta,
        operator_goal=step.operator_goal,
        stage_action=step.stage_action,
        inspect_action=step.inspect_action,
        preview_state="preview-staged",
        fire_state="blocked",
        fire_policy=step.fire_policy,
        recovery_action=step.recovery_action,
        queued_intent_key=f"queued.{slug}",
        audit_event_key=f"audit.{slug}",
        target_device=step.target_device,
        target_scope=step.target_scope,
        lane=step.lane,
        safety_tier=step.safety_tier,
        blocked_action=step.blocked_action,
        notes=step.notes,
    )


def _state_rows(
    runbook_steps: Sequence[ControllerBrainRunbookStep],
) -> tuple[ControllerBrainLiveStateRow, ...]:
    return tuple(_state_row_from_runbook_step(step) for step in runbook_steps)


def _queued_intent_from_state_row(
    row: ControllerBrainLiveStateRow,
) -> ControllerBrainQueuedIntent:
    return ControllerBrainQueuedIntent(
        queued_intent_key=row.queued_intent_key,
        order=row.step,
        intent_key=row.intent_key,
        state_key=row.state_key,
        preview_state=row.preview_state,
        fire_state=row.fire_state,
        stage_action=row.stage_action,
        recovery_action=row.recovery_action,
        target_device=row.target_device,
        target_scope=row.target_scope,
    )


def _queued_intents(
    rows: Sequence[ControllerBrainLiveStateRow],
) -> tuple[ControllerBrainQueuedIntent, ...]:
    return tuple(_queued_intent_from_state_row(row) for row in rows)


def _audit_event_from_state_row(row: ControllerBrainLiveStateRow) -> ControllerBrainAuditEvent:
    return ControllerBrainAuditEvent(
        audit_event_key=row.audit_event_key,
        order=row.step,
        intent_key=row.intent_key,
        state_key=row.state_key,
        queued_intent_key=row.queued_intent_key,
        stage_state="queued",
        fire_state=row.fire_state,
        fire_policy=row.fire_policy,
        recovery_action=row.recovery_action,
        evidence=(
            f"{row.intent_key} is staged as {row.preview_state}; fire remains "
            f"{row.fire_state} until an approved controller bridge exists"
        ),
    )


def _audit_events(
    rows: Sequence[ControllerBrainLiveStateRow],
) -> tuple[ControllerBrainAuditEvent, ...]:
    return tuple(_audit_event_from_state_row(row) for row in rows)


def _state_readiness_gates(
    runbook_gates: Sequence[ControllerBrainReadinessGate],
) -> tuple[ControllerBrainReadinessGate, ...]:
    return (
        *runbook_gates,
        ControllerBrainReadinessGate(
            name="state-reducer",
            status="ready",
            ready=True,
            evidence="runbook intents are normalized into deterministic state rows",
            blocked_action="apply live state reducer",
            safety_note="state reducer output is passive metadata only",
        ),
        ControllerBrainReadinessGate(
            name="audit-ledger",
            status="ready",
            ready=True,
            evidence="each state row has a deterministic queued intent and audit event key",
            blocked_action="write controller audit ledger",
            safety_note="audit events are stdout/JSON metadata only",
        ),
    )


def build_controller_brain_live_state_report(
    *,
    session_label: str = "Live Session",
) -> ControllerBrainLiveStateReport:
    """Build passive controller-brain live state metadata from the runbook."""

    runbook = build_controller_brain_live_runbook_report(session_label=session_label)
    rows = _state_rows(runbook.runbook_steps)
    queued = _queued_intents(rows)
    audit = _audit_events(rows)
    return ControllerBrainLiveStateReport(
        title=REPORT_TITLE,
        live_state_version=LIVE_STATE_VERSION,
        live_state_status=LIVE_STATE_STATUS,
        session_label=session_label,
        source_report=SOURCE_REPORT,
        source_runbook_version=RUNBOOK_VERSION,
        controller_profile_key=runbook.controller_profile_key,
        controller_profile_label=runbook.controller_profile_label,
        state_rows=rows,
        queued_intents=queued,
        audit_events=audit,
        readiness_gates=_state_readiness_gates(runbook.readiness_gates),
        blocked_actions=_live_state_unique_tuple(BASE_BLOCKED_ACTIONS, runbook.blocked_actions),
        safety_lines=_live_state_unique_tuple(BASE_SAFETY_LINES, runbook.safety_lines),
        replay_commands=REPLAY_COMMANDS,
    )


def _state_row_to_payload(row: ControllerBrainLiveStateRow) -> dict[str, object]:
    return {
        "step": row.step,
        "state_key": row.state_key,
        "intent_key": row.intent_key,
        "controller_assignment": row.controller_assignment,
        "controller_gesture": row.controller_gesture,
        "value_delta": row.value_delta,
        "operator_goal": row.operator_goal,
        "stage_action": row.stage_action,
        "inspect_action": row.inspect_action,
        "preview_state": row.preview_state,
        "fire_state": row.fire_state,
        "fire_policy": row.fire_policy,
        "recovery_action": row.recovery_action,
        "queued_intent_key": row.queued_intent_key,
        "audit_event_key": row.audit_event_key,
        "target_device": row.target_device,
        "target_scope": row.target_scope,
        "lane": row.lane,
        "safety_tier": row.safety_tier,
        "blocked_action": row.blocked_action,
        "notes": row.notes,
    }


def _queued_intent_to_payload(intent: ControllerBrainQueuedIntent) -> dict[str, object]:
    return {
        "queued_intent_key": intent.queued_intent_key,
        "order": intent.order,
        "intent_key": intent.intent_key,
        "state_key": intent.state_key,
        "preview_state": intent.preview_state,
        "fire_state": intent.fire_state,
        "stage_action": intent.stage_action,
        "recovery_action": intent.recovery_action,
        "target_device": intent.target_device,
        "target_scope": intent.target_scope,
    }


def _audit_event_to_payload(event: ControllerBrainAuditEvent) -> dict[str, object]:
    return {
        "audit_event_key": event.audit_event_key,
        "order": event.order,
        "intent_key": event.intent_key,
        "state_key": event.state_key,
        "queued_intent_key": event.queued_intent_key,
        "stage_state": event.stage_state,
        "fire_state": event.fire_state,
        "fire_policy": event.fire_policy,
        "recovery_action": event.recovery_action,
        "evidence": event.evidence,
    }


def _live_state_readiness_gate_to_payload(
    gate: ControllerBrainReadinessGate,
) -> dict[str, object]:
    return {
        "name": gate.name,
        "status": gate.status,
        "ready": gate.ready,
        "evidence": gate.evidence,
        "blocked_action": gate.blocked_action,
        "safety_note": gate.safety_note,
    }


def build_controller_brain_live_state_payload(
    *,
    session_label: str = "Live Session",
) -> dict[str, object]:
    """Return JSON-ready passive controller-brain live state metadata."""

    report = build_controller_brain_live_state_report(session_label=session_label)
    return {
        "controller_brain_live_state": {
            "title": report.title,
            "live_state_version": report.live_state_version,
            "live_state_status": report.live_state_status,
            "session_label": report.session_label,
            "source_report": report.source_report,
            "source_runbook_version": report.source_runbook_version,
            "controller_profile_key": report.controller_profile_key,
            "controller_profile_label": report.controller_profile_label,
            "state_row_count": report.state_row_count,
            "queued_intent_count": report.queued_intent_count,
            "audit_event_count": report.audit_event_count,
            "state_rows": [_state_row_to_payload(row) for row in report.state_rows],
            "queued_intents": [
                _queued_intent_to_payload(intent) for intent in report.queued_intents
            ],
            "audit_events": [_audit_event_to_payload(event) for event in report.audit_events],
            "readiness_gates": [
                _live_state_readiness_gate_to_payload(gate) for gate in report.readiness_gates
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def _format_live_state_body(report: ControllerBrainLiveStateReport) -> list[str]:
    lines = [
        "Controller brain live state:",
        f"- version: {report.live_state_version}",
        f"- status: {report.live_state_status}",
        f"- session: {report.session_label}",
        f"- source runbook: {report.source_report}",
        f"- source runbook version: {report.source_runbook_version}",
        f"- controller profile: {report.controller_profile_key}",
        f"- state rows: {report.state_row_count}",
        f"- queued intents: {report.queued_intent_count}",
        f"- audit events: {report.audit_event_count}",
        "State rows:",
    ]
    for row in report.state_rows:
        lines.append(f"- state row: {row.state_key} -> {row.intent_key}")
        lines.append(
            f"  controller: {row.controller_assignment} / {row.controller_gesture} / "
            f"delta {row.value_delta:+d}"
        )
        lines.append(f"  preview/fire: {row.preview_state} / {row.fire_state}")
        lines.append(f"  policy: {row.fire_policy}")
        lines.append(f"  recover: {row.recovery_action}")
    lines.append("Queued intents:")
    for intent in report.queued_intents:
        lines.append(f"- {intent.queued_intent_key}: {intent.preview_state} / {intent.fire_state}")
        lines.append(f"  stage: {intent.stage_action}")
        lines.append(f"  recover: {intent.recovery_action}")
    lines.append("Audit events:")
    for event in report.audit_events:
        lines.append(
            f"- {event.audit_event_key}: stage={event.stage_state} " f"fire={event.fire_state}"
        )
        lines.append(f"  evidence: {event.evidence}")
    lines.append("Readiness gates:")
    for gate in report.readiness_gates:
        lines.append(f"- {gate.name}: {gate.status} / ready={gate.ready}")
        lines.append(f"  evidence: {gate.evidence}")
        lines.append(f"  blocked: {gate.blocked_action}")
    lines.append("Blocked active actions:")
    lines.extend(f"- {action}" for action in report.blocked_actions)
    lines.append("Replay commands:")
    lines.extend(f"- {command}" for command in report.replay_commands)
    lines.append("Safety:")
    lines.extend(f"- {line}" for line in report.safety_lines)
    return lines


def format_controller_brain_live_state_report(
    report: ControllerBrainLiveStateReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing controller-brain live state text."""

    source = build_controller_brain_live_state_report() if report is None else report
    return passive_report_lines(_HEADER, _format_live_state_body(source))


CONTROLLER_BRAIN_LIVE_STATE_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "controller-brain-live-state-report",
    "Print the passive controller-brain live state contract.",
    format_lines=lambda: format_controller_brain_live_state_report(),
    build_payload=build_controller_brain_live_state_payload,
)

register(CONTROLLER_BRAIN_LIVE_STATE_CLI_COMMAND)

__all__ = (
    "BASE_BLOCKED_ACTIONS",
    "BASE_SAFETY_LINES",
    "CONTROLLER_BRAIN_LIVE_STATE_CLI_COMMAND",
    "ControllerBrainAuditEvent",
    "ControllerBrainLiveStateReport",
    "ControllerBrainLiveStateRow",
    "ControllerBrainQueuedIntent",
    "ControllerBrainRunbookStep",
    "LIVE_STATE_STATUS",
    "LIVE_STATE_VERSION",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SOURCE_MODULE",
    "SOURCE_REPORT",
    "build_controller_brain_live_state_payload",
    "build_controller_brain_live_state_report",
    "format_controller_brain_live_state_report",
)
