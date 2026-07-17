"""Passive controller-brain live runbook for future hardware-controller surfaces."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from .controller_brain_rehearsal import build_controller_brain_rehearsal_payload
from .formatter import PassiveReportHeader, passive_report_lines
from .live_gui_performance_console_model import (
    build_live_gui_performance_console_model,
    live_gui_performance_console_model_payload,
)
from .oxi_live_set_strategy import build_oxi_live_set_strategy_payload

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain live runbook"
SOURCE_MODULE: Final[str] = "reports.controller_brain_live_runbook"
RUNBOOK_VERSION: Final[str] = "controller-brain-live-runbook-v1"
RUNBOOK_STATUS: Final[str] = "passive-ready"
RUNBOOK_FIRE_POLICY: Final[str] = "blocked until approved controller bridge"
SOURCE_REPORTS: Final[tuple[str, ...]] = (
    "controller-brain-rehearsal-report",
    "oxi-live-set-strategy-report",
    "live-gui-performance-console-report",
)
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-brain live runbook metadata only",
    "composes existing passive reports only",
    "JSON/stdout only",
    "no MIDI controller input",
    "no MIDI learn or raw CC capture",
    "no WebSocket command dispatch",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
BASE_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "open MIDI controller input",
    "MIDI learn or raw CC capture",
    "dispatch Cockpit WebSocket commands",
    "open MIDI output",
    "arm hardware",
    "send hardware MIDI",
    "mutate a snapshot",
    "dispatch controller gesture to active runtime",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-live-runbook-report",
    "python -m rytm_randomizer.cli controller-brain-live-runbook-report --json",
    "python -m rytm_randomizer.cli controller-brain-rehearsal-report --json",
    "python -m rytm_randomizer.cli oxi-live-set-strategy-report --json",
    "python -m rytm_randomizer.cli live-gui-performance-console-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainRunbookStep:
    """One staged controller intent with explicit inspect/fire/recover semantics."""

    step: int
    intent_key: str
    controller_assignment: str
    controller_gesture: str
    value_delta: int
    operator_goal: str
    stage_action: str
    inspect_action: str
    fire_policy: str
    recovery_action: str
    target_device: str
    target_scope: str
    lane: str
    safety_tier: str
    readiness: str
    blocked_action: str
    notes: str


@dataclass(frozen=True)
class ControllerBrainReadinessGate:
    """One passive readiness gate for the future controller bridge."""

    name: str
    status: str
    ready: bool
    evidence: str
    blocked_action: str
    safety_note: str


@dataclass(frozen=True)
class ControllerBrainLiveRunbookReport:
    """Passive controller-brain runbook composed from existing report packets."""

    title: str
    runbook_version: str
    runbook_status: str
    session_label: str
    source_reports: tuple[str, ...]
    controller_profile_key: str
    controller_profile_label: str
    controller_family: str
    controller_layout: str
    controller_template_row_count: int
    controller_page_count: int
    gesture_count: int
    live_chapter_count: int
    console_status: str
    console_hardware_mode: str
    runbook_steps: tuple[ControllerBrainRunbookStep, ...]
    readiness_gates: tuple[ControllerBrainReadinessGate, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]


def _runbook_payload_dict(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key, {})
    if not isinstance(value, dict):
        return {}
    return value


def _runbook_payload_list(payload: dict[str, object], key: str) -> list[object]:
    value = payload.get(key, ())
    if not isinstance(value, list):
        return []
    return value


def _runbook_payload_string(payload: dict[str, object], key: str) -> str:
    value = payload.get(key, "")
    if not isinstance(value, str):
        return ""
    return value


def _runbook_payload_int(payload: dict[str, object], key: str) -> int:
    value = payload.get(key, 0)
    if not isinstance(value, int):
        return 0
    return value


def _runbook_unique_tuple(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return tuple(values)


def _runbook_string_tuple(payload: dict[str, object], key: str) -> tuple[str, ...]:
    values = payload.get(key, ())
    if not isinstance(values, (list, tuple)):
        return ()
    return tuple(str(value) for value in values)


def _runbook_stage_action(intent_key: str) -> str:
    if intent_key == "global.preview_depth":
        return "adjust passive preview depth"
    if intent_key == "macro.industrial":
        return "stage Rytm macro industrial"
    if intent_key == "rytm.pad5.source_amount":
        return "stage Pad 5 SRC movement"
    if intent_key == "rytm.pad6.source_amount":
        return "stage Pad 6 SRC movement"
    if intent_key == "rytm.pad12.source_amount":
        return "confirm optional Pad 12 SRC mapping"
    if intent_key == "a4.track1.macro_depth":
        return "review A4 macro runway"
    if intent_key == "crate.dark_hypnotic":
        return "select Dark Hypnotic crate"
    if intent_key == "queue.next_1":
        return "stage upcoming queue move"
    if intent_key == "snapshot.panic_home":
        return "recover captured anchor"
    return f"stage intent {intent_key}"


def _runbook_step_payload(source: dict[str, object]) -> ControllerBrainRunbookStep:
    intent_key = _runbook_payload_string(source, "resolved_intent_key")
    return ControllerBrainRunbookStep(
        step=_runbook_payload_int(source, "step"),
        intent_key=intent_key,
        controller_assignment=_runbook_payload_string(source, "assignment_key"),
        controller_gesture=_runbook_payload_string(source, "gesture"),
        value_delta=_runbook_payload_int(source, "value_delta"),
        operator_goal=_runbook_payload_string(source, "operator_goal"),
        stage_action=_runbook_stage_action(intent_key),
        inspect_action="review staged intent before any send decision",
        fire_policy=RUNBOOK_FIRE_POLICY,
        recovery_action=_runbook_payload_string(source, "recovery_action"),
        target_device=_runbook_payload_string(source, "resolved_target_device"),
        target_scope=_runbook_payload_string(source, "resolved_target_scope"),
        lane=_runbook_payload_string(source, "lane"),
        safety_tier=_runbook_payload_string(source, "safety_tier"),
        readiness="passive-intent-only",
        blocked_action="dispatch controller gesture to active runtime",
        notes=_runbook_payload_string(source, "notes"),
    )


def _runbook_steps(
    gesture_outcomes: Sequence[object],
) -> tuple[ControllerBrainRunbookStep, ...]:
    steps: list[ControllerBrainRunbookStep] = []
    for outcome in gesture_outcomes:
        if not isinstance(outcome, dict):
            continue
        steps.append(_runbook_step_payload(outcome))
    return tuple(steps)


def _readiness_gates(
    *,
    template_row_count: int,
    controller_page_count: int,
    gesture_count: int,
    console_status: str,
) -> tuple[ControllerBrainReadinessGate, ...]:
    return (
        ControllerBrainReadinessGate(
            name="controller-template",
            status="ready",
            ready=True,
            evidence=(
                f"{template_row_count} template rows across {controller_page_count} pages; "
                f"{gesture_count} virtual gestures resolved"
            ),
            blocked_action="none",
            safety_note="template rows are passive metadata only",
        ),
        ControllerBrainReadinessGate(
            name="controller-input",
            status="blocked",
            ready=False,
            evidence="no raw controller input bridge is active",
            blocked_action="open MIDI controller input",
            safety_note="future controller input needs an explicit approved design",
        ),
        ControllerBrainReadinessGate(
            name="raw-cc-capture",
            status="blocked",
            ready=False,
            evidence="controller mapping stores intent keys, not raw CC/channel numbers",
            blocked_action="MIDI learn or raw CC capture",
            safety_note="do not learn controller messages in this passive report",
        ),
        ControllerBrainReadinessGate(
            name="websocket-dispatch",
            status="blocked",
            ready=False,
            evidence="runbook does not dispatch Cockpit commands",
            blocked_action="dispatch Cockpit WebSocket commands",
            safety_note="future WS dispatch must keep ack/event safety gates",
        ),
        ControllerBrainReadinessGate(
            name="midi-output",
            status="blocked",
            ready=False,
            evidence="no MIDI output path is opened by this CLI command",
            blocked_action="open MIDI output",
            safety_note="passive CLI must never open real MIDI ports",
        ),
        ControllerBrainReadinessGate(
            name="hardware-send",
            status="blocked",
            ready=False,
            evidence="hardware send remains confined to explicit --arm app paths",
            blocked_action="send hardware MIDI",
            safety_note="operator must use an approved armed path for real sends",
        ),
        ControllerBrainReadinessGate(
            name="snapshot-mutation",
            status="blocked",
            ready=False,
            evidence=f"Cockpit console status is {console_status}; this packet mutates nothing",
            blocked_action="mutate a snapshot",
            safety_note="runbook explains intent only",
        ),
    )


def build_controller_brain_live_runbook_report(
    *,
    session_label: str = "Live Session",
) -> ControllerBrainLiveRunbookReport:
    """Build a deterministic passive live runbook for controller-brain rehearsal."""

    controller_payload = build_controller_brain_rehearsal_payload()
    controller = _runbook_payload_dict(controller_payload, "controller_brain_rehearsal")
    strategy_payload = build_oxi_live_set_strategy_payload()
    console_payload = live_gui_performance_console_model_payload(
        build_live_gui_performance_console_model(session_label=session_label)
    )
    console = _runbook_payload_dict(console_payload, "live_gui_performance_console")

    template_rows = _runbook_payload_list(controller, "template_rows")
    gesture_outcomes = _runbook_payload_list(controller, "gesture_outcomes")
    strategy_chapters = _runbook_payload_list(strategy_payload, "chapters")
    template_page_count = len(
        {_runbook_payload_string(row, "page_key") for row in template_rows if isinstance(row, dict)}
    )
    template_row_count = _runbook_payload_int(controller, "template_row_count")
    gesture_count = len(gesture_outcomes)
    console_status = _runbook_payload_string(console, "console_status")
    blocked_actions = _runbook_unique_tuple(
        BASE_BLOCKED_ACTIONS,
        _runbook_string_tuple(controller, "blocked_active_actions"),
        _runbook_string_tuple(console, "blocked_actions"),
    )
    safety_lines = _runbook_unique_tuple(
        BASE_SAFETY_LINES,
        _runbook_string_tuple(controller_payload, "safety"),
        _runbook_string_tuple(console_payload, "safety"),
    )

    return ControllerBrainLiveRunbookReport(
        title=REPORT_TITLE,
        runbook_version=RUNBOOK_VERSION,
        runbook_status=RUNBOOK_STATUS,
        session_label=session_label,
        source_reports=SOURCE_REPORTS,
        controller_profile_key=_runbook_payload_string(controller, "profile_key"),
        controller_profile_label=_runbook_payload_string(controller, "profile_label"),
        controller_family=_runbook_payload_string(controller, "controller_family"),
        controller_layout=_runbook_payload_string(controller, "controller_layout"),
        controller_template_row_count=template_row_count,
        controller_page_count=template_page_count,
        gesture_count=gesture_count,
        live_chapter_count=len(strategy_chapters),
        console_status=console_status,
        console_hardware_mode=_runbook_payload_string(console, "hardware_mode"),
        runbook_steps=_runbook_steps(gesture_outcomes),
        readiness_gates=_readiness_gates(
            template_row_count=template_row_count,
            controller_page_count=template_page_count,
            gesture_count=gesture_count,
            console_status=console_status,
        ),
        blocked_actions=blocked_actions,
        safety_lines=safety_lines,
        replay_commands=REPLAY_COMMANDS,
    )


def _runbook_step_to_payload(step: ControllerBrainRunbookStep) -> dict[str, object]:
    return {
        "step": step.step,
        "intent_key": step.intent_key,
        "controller_assignment": step.controller_assignment,
        "controller_gesture": step.controller_gesture,
        "value_delta": step.value_delta,
        "operator_goal": step.operator_goal,
        "stage_action": step.stage_action,
        "inspect_action": step.inspect_action,
        "fire_policy": step.fire_policy,
        "recovery_action": step.recovery_action,
        "target_device": step.target_device,
        "target_scope": step.target_scope,
        "lane": step.lane,
        "safety_tier": step.safety_tier,
        "readiness": step.readiness,
        "blocked_action": step.blocked_action,
        "notes": step.notes,
    }


def _readiness_gate_to_payload(gate: ControllerBrainReadinessGate) -> dict[str, object]:
    return {
        "name": gate.name,
        "status": gate.status,
        "ready": gate.ready,
        "evidence": gate.evidence,
        "blocked_action": gate.blocked_action,
        "safety_note": gate.safety_note,
    }


def build_controller_brain_live_runbook_payload(
    *,
    session_label: str = "Live Session",
) -> dict[str, object]:
    """Return JSON-ready passive controller-brain live runbook metadata."""

    report = build_controller_brain_live_runbook_report(session_label=session_label)
    return {
        "controller_brain_live_runbook": {
            "title": report.title,
            "runbook_version": report.runbook_version,
            "runbook_status": report.runbook_status,
            "session_label": report.session_label,
            "source_reports": list(report.source_reports),
            "controller_profile_key": report.controller_profile_key,
            "controller_profile_label": report.controller_profile_label,
            "controller_family": report.controller_family,
            "controller_layout": report.controller_layout,
            "controller_template_row_count": report.controller_template_row_count,
            "controller_page_count": report.controller_page_count,
            "gesture_count": report.gesture_count,
            "live_chapter_count": report.live_chapter_count,
            "console_status": report.console_status,
            "console_hardware_mode": report.console_hardware_mode,
            "runbook_steps": [_runbook_step_to_payload(step) for step in report.runbook_steps],
            "readiness_gates": [
                _readiness_gate_to_payload(gate) for gate in report.readiness_gates
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def _format_runbook_body(report: ControllerBrainLiveRunbookReport) -> list[str]:
    lines = [
        "Controller brain live runbook:",
        f"- version: {report.runbook_version}",
        f"- status: {report.runbook_status}",
        f"- session: {report.session_label}",
        f"- source reports: {', '.join(report.source_reports)}",
        f"Controller profile: {report.controller_profile_key}",
        f"- profile label: {report.controller_profile_label}",
        f"- controller family: {report.controller_family}",
        f"- controller layout: {report.controller_layout}",
        f"- template rows: {report.controller_template_row_count}",
        f"- controller pages: {report.controller_page_count}",
        f"- virtual gestures: {report.gesture_count}",
        f"- live chapters: {report.live_chapter_count}",
        f"- console status: {report.console_status}",
        f"- console hardware mode: {report.console_hardware_mode}",
        "Runbook steps:",
    ]
    for step in report.runbook_steps:
        lines.append(f"- runbook step: {step.intent_key} -> {step.stage_action}")
        lines.append(
            f"  controller: {step.controller_assignment} / {step.controller_gesture} / "
            f"delta {step.value_delta:+d}"
        )
        lines.append(f"  inspect: {step.inspect_action}")
        lines.append(f"  fire: {step.fire_policy}")
        lines.append(f"  recover: {step.recovery_action}")
        lines.append(f"  target: {step.target_device} / {step.target_scope}")
    lines.append("Readiness gates:")
    for gate in report.readiness_gates:
        lines.append(f"- {gate.name}: {gate.status} / ready={gate.ready}")
        lines.append(f"  evidence: {gate.evidence}")
        lines.append(f"  blocked: {gate.blocked_action}")
        lines.append(f"  safety: {gate.safety_note}")
    lines.append("Blocked active actions:")
    lines.extend(f"- {action}" for action in report.blocked_actions)
    lines.append("Replay commands:")
    lines.extend(f"- {command}" for command in report.replay_commands)
    lines.append("Safety:")
    lines.extend(f"- {line}" for line in report.safety_lines)
    return lines


def format_controller_brain_live_runbook_report(
    report: ControllerBrainLiveRunbookReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing controller-brain runbook text."""

    source = build_controller_brain_live_runbook_report() if report is None else report
    return passive_report_lines(_HEADER, _format_runbook_body(source))


CONTROLLER_BRAIN_LIVE_RUNBOOK_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "controller-brain-live-runbook-report",
    "Print the passive controller-brain live runbook.",
    format_lines=lambda: format_controller_brain_live_runbook_report(),
    build_payload=build_controller_brain_live_runbook_payload,
)

register(CONTROLLER_BRAIN_LIVE_RUNBOOK_CLI_COMMAND)

__all__ = (
    "BASE_BLOCKED_ACTIONS",
    "BASE_SAFETY_LINES",
    "CONTROLLER_BRAIN_LIVE_RUNBOOK_CLI_COMMAND",
    "ControllerBrainLiveRunbookReport",
    "ControllerBrainReadinessGate",
    "ControllerBrainRunbookStep",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "RUNBOOK_STATUS",
    "RUNBOOK_VERSION",
    "SOURCE_MODULE",
    "SOURCE_REPORTS",
    "build_controller_brain_live_runbook_payload",
    "build_controller_brain_live_runbook_report",
    "format_controller_brain_live_runbook_report",
)
