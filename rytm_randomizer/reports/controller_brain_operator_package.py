"""Passive controller-brain to operator-package ledger."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, cast

from ..cli_registry import CliCommand, make_passive_report_command, register
from .controller_brain_rehearsal import build_controller_brain_rehearsal_payload
from .formatter import PassiveReportHeader, passive_report_lines
from .live_gui_performance_console_model import build_live_gui_performance_console_model
from .performance_console.payload_helpers import dict_sequence

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain operator package ledger"
SOURCE_MODULE: Final[str] = "reports.controller_brain_operator_package"
LEDGER_VERSION: Final[str] = "controller-brain-operator-package-ledger-v1"
LEDGER_STATUS: Final[str] = "passive-ready"
READY_STATUS: Final[str] = "mock-safe"
SOURCE_CONTROLLER_REPORT: Final[str] = "controller-brain-rehearsal-report"
SOURCE_OPERATOR_PACKAGE: Final[str] = "live-kit-operator-package"
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller/package ledger only",
    "virtual controller gestures only",
    "operator package metadata only",
    "no MIDI controller input",
    "no MIDI learn or raw CC capture",
    "no WebSocket command dispatch",
    "no file writing",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-rehearsal-report --json",
    "python -m rytm_randomizer.cli live-gui-performance-console-report --json",
    "python -m rytm_randomizer.cli controller-brain-operator-package-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainOperatorPackageBinding:
    """One virtual controller gesture resolved to an operator-package intent."""

    step: int
    assignment_key: str
    intent_key: str
    controller_action: str
    controller_target: str
    operator_target: str
    package_step_key: str
    slot_key: str
    package_export_key: str
    queue_key: str
    cockpit_binding: str
    recovery_command: str
    readiness_status: str
    mock_safe: bool
    operator_action: str
    notes: str


@dataclass(frozen=True)
class ControllerBrainOperatorPackageReadiness:
    """Side-effect readiness summary for the passive ledger."""

    status: str
    ready_for_cockpit_preview: bool
    ready_for_hardware_send: bool
    opened_controller_input: bool
    captured_raw_cc: bool
    dispatched_websocket: bool
    opened_midi_port: bool
    sent_midi: bool
    wrote_files: bool
    mutated_snapshot: bool
    armed_hardware: bool


@dataclass(frozen=True)
class ControllerBrainOperatorPackageReport:
    """Passive controller-brain to operator-package report model."""

    title: str
    ledger_version: str
    ledger_status: str
    source_controller_report: str
    source_operator_package: str
    controller_profile_key: str
    controller_scenario_key: str
    operator_package_id: str
    operator_package_status: str
    operator_slots: tuple[Mapping[str, object], ...]
    operator_steps: tuple[Mapping[str, object], ...]
    gesture_bindings: tuple[ControllerBrainOperatorPackageBinding, ...]
    readiness: ControllerBrainOperatorPackageReadiness
    safety_lines: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def gesture_binding_count(self) -> int:
        """Return the number of bound virtual gestures."""

        return len(self.gesture_bindings)

    @property
    def operator_slot_count(self) -> int:
        """Return the number of operator-package slots available."""

        return len(self.operator_slots)


def _ledger_payload_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if isinstance(value, str):
        return value
    return ""


def _ledger_payload_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, int):
        return value
    return 0


def _ledger_payload_text_list(payload: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _source_controller_payload() -> Mapping[str, object]:
    payload = build_controller_brain_rehearsal_payload()
    source = payload.get("controller_brain_rehearsal")
    if not isinstance(source, dict):
        return {}
    return source


def _source_operator_package() -> Mapping[str, object]:
    model = build_live_gui_performance_console_model()
    return cast(Mapping[str, object], model.live_kit_operator_package)


def _dedupe_ledger_values(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return tuple(deduped)


def _slots_by_key(slots: Sequence[Mapping[str, object]]) -> dict[str, Mapping[str, object]]:
    rows: dict[str, Mapping[str, object]] = {}
    for slot in slots:
        slot_key = _ledger_payload_text(slot, "slot_key")
        if slot_key:
            rows[slot_key] = slot
    return rows


def _steps_by_slot_key(
    steps: Sequence[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    rows: dict[str, Mapping[str, object]] = {}
    for step in steps:
        slot_key = _ledger_payload_text(step, "slot_key")
        if slot_key:
            rows[slot_key] = step
    return rows


def _slot_key_for_intent(intent_key: str) -> str:
    if intent_key == "macro.industrial":
        return "industrial-pressure"
    if intent_key.startswith("macro."):
        return "hard-groove-lift"
    if intent_key == "queue.next_1":
        return "industrial-pressure"
    if intent_key.startswith("queue."):
        return "hard-groove-lift"
    if intent_key.startswith("snapshot."):
        return "recovery-return"
    if intent_key.startswith("rytm.pad"):
        return "hard-groove-lift"
    if intent_key.startswith("global."):
        return "captured-base"
    return ""


def _operator_target_for_intent(intent_key: str) -> str:
    if intent_key.startswith("global."):
        return "operator-package.depth-review"
    if intent_key.startswith("macro."):
        return "operator-package.slot-selection"
    if intent_key.startswith("rytm.pad"):
        return "operator-package.pad-lane-review"
    if intent_key.startswith("a4."):
        return "operator-package.a4-review-only"
    if intent_key.startswith("crate."):
        return "operator-package.crate-review"
    if intent_key.startswith("queue."):
        return "operator-package.queue-stage"
    if intent_key.startswith("snapshot."):
        return "operator-package.recovery"
    return "operator-package.review"


def _binding_notes(
    *,
    intent_key: str,
    slot_key: str,
    operator_target: str,
) -> str:
    if intent_key.startswith("a4."):
        return "A4 controller gesture remains review-only until A4 hardware promotion gates pass."
    if intent_key.startswith("crate."):
        return "Style-crate gesture reviews package direction without dispatching Cockpit commands."
    if intent_key.startswith("snapshot."):
        return "Recovery gesture points at the package recovery slot and remains manual."
    if slot_key:
        return f"Gesture stages {operator_target} against package slot {slot_key}."
    return f"Gesture stages {operator_target} without selecting an operator package slot."


def _operator_package_binding(
    *,
    outcome: Mapping[str, object],
    slots_by_key: Mapping[str, Mapping[str, object]],
    steps_by_slot_key: Mapping[str, Mapping[str, object]],
) -> ControllerBrainOperatorPackageBinding:
    intent_key = _ledger_payload_text(outcome, "resolved_intent_key")
    slot_key = _slot_key_for_intent(intent_key)
    slot = slots_by_key.get(slot_key, {})
    step = steps_by_slot_key.get(slot_key, {})
    operator_target = _operator_target_for_intent(intent_key)
    package_step_key = _ledger_payload_text(step, "step_key")
    local_action = _ledger_payload_text(step, "local_action")
    controller_action = _ledger_payload_text(outcome, "resolved_action")
    operator_action = local_action or controller_action
    return ControllerBrainOperatorPackageBinding(
        step=_ledger_payload_int(outcome, "step"),
        assignment_key=_ledger_payload_text(outcome, "assignment_key"),
        intent_key=intent_key,
        controller_action=controller_action,
        controller_target=_ledger_payload_text(outcome, "resolved_target_scope"),
        operator_target=operator_target,
        package_step_key=package_step_key,
        slot_key=slot_key,
        package_export_key=_ledger_payload_text(slot, "package_export_key"),
        queue_key=_ledger_payload_text(slot, "queue_key"),
        cockpit_binding=_ledger_payload_text(step, "cockpit_binding"),
        recovery_command=_ledger_payload_text(step, "recovery_command"),
        readiness_status="mock-safe-staged",
        mock_safe=True,
        operator_action=operator_action,
        notes=_binding_notes(
            intent_key=intent_key,
            slot_key=slot_key,
            operator_target=operator_target,
        ),
    )


def _gesture_bindings(
    controller_payload: Mapping[str, object],
    operator_package: Mapping[str, object],
) -> tuple[ControllerBrainOperatorPackageBinding, ...]:
    operator_slots = dict_sequence(operator_package.get("slot_bindings", []))
    operator_steps = dict_sequence(operator_package.get("operator_steps", []))
    slots = _slots_by_key(operator_slots)
    steps = _steps_by_slot_key(operator_steps)
    bindings: list[ControllerBrainOperatorPackageBinding] = []
    for outcome in dict_sequence(controller_payload.get("gesture_outcomes", [])):
        bindings.append(
            _operator_package_binding(
                outcome=outcome,
                slots_by_key=slots,
                steps_by_slot_key=steps,
            )
        )
    return tuple(bindings)


def _readiness() -> ControllerBrainOperatorPackageReadiness:
    return ControllerBrainOperatorPackageReadiness(
        status=READY_STATUS,
        ready_for_cockpit_preview=True,
        ready_for_hardware_send=False,
        opened_controller_input=False,
        captured_raw_cc=False,
        dispatched_websocket=False,
        opened_midi_port=False,
        sent_midi=False,
        wrote_files=False,
        mutated_snapshot=False,
        armed_hardware=False,
    )


def build_controller_brain_operator_package_report() -> ControllerBrainOperatorPackageReport:
    """Build the deterministic passive controller-brain operator-package ledger."""

    controller_payload = _source_controller_payload()
    operator_package = _source_operator_package()
    operator_slots = dict_sequence(operator_package.get("slot_bindings", []))
    operator_steps = dict_sequence(operator_package.get("operator_steps", []))
    controller_blocked_actions = _ledger_payload_text_list(
        controller_payload, "blocked_active_actions"
    )
    operator_blocked_actions = _ledger_payload_text_list(operator_package, "blocked_actions")
    controller_safety_lines = _ledger_payload_text_list(controller_payload, "safety")
    operator_safety_lines = _ledger_payload_text_list(operator_package, "safety_lines")
    return ControllerBrainOperatorPackageReport(
        title=REPORT_TITLE,
        ledger_version=LEDGER_VERSION,
        ledger_status=LEDGER_STATUS,
        source_controller_report=SOURCE_CONTROLLER_REPORT,
        source_operator_package=SOURCE_OPERATOR_PACKAGE,
        controller_profile_key=_ledger_payload_text(controller_payload, "profile_key"),
        controller_scenario_key=_ledger_payload_text(controller_payload, "scenario_key"),
        operator_package_id=_ledger_payload_text(operator_package, "operator_package_id"),
        operator_package_status=_ledger_payload_text(operator_package, "operator_package_status"),
        operator_slots=operator_slots,
        operator_steps=operator_steps,
        gesture_bindings=_gesture_bindings(controller_payload, operator_package),
        readiness=_readiness(),
        safety_lines=_dedupe_ledger_values(
            (*BASE_SAFETY_LINES, *controller_safety_lines, *operator_safety_lines)
        ),
        blocked_actions=_dedupe_ledger_values(
            (*controller_blocked_actions, *operator_blocked_actions)
        ),
        replay_commands=REPLAY_COMMANDS,
    )


def _format_summary(report: ControllerBrainOperatorPackageReport) -> list[str]:
    return [
        f"Ledger version: {report.ledger_version}",
        f"Ledger status: {report.ledger_status}",
        f"Controller source: {report.source_controller_report}",
        f"Controller profile: {report.controller_profile_key}",
        f"Controller scenario: {report.controller_scenario_key}",
        f"Operator package source: {report.source_operator_package}",
        f"Operator package id: {report.operator_package_id}",
        f"Operator package status: {report.operator_package_status}",
        f"Operator slots: {report.operator_slot_count}",
        f"Controller gestures bound: {report.gesture_binding_count}",
    ]


def _format_bindings(report: ControllerBrainOperatorPackageReport) -> list[str]:
    lines = ["", "Gesture package bindings:"]
    for binding in report.gesture_bindings:
        slot_detail = binding.slot_key or "no-slot"
        export_detail = binding.package_export_key or "no-export"
        lines.append(
            f"- {binding.assignment_key}: {binding.intent_key} -> "
            f"{binding.operator_target} / slot={slot_detail} / "
            f"export={export_detail} / status={binding.readiness_status}"
        )
    return lines


def _format_readiness(report: ControllerBrainOperatorPackageReport) -> list[str]:
    readiness = report.readiness
    return [
        "",
        "Readiness:",
        f"- Status: {readiness.status}",
        f"- Ready for Cockpit preview: {readiness.ready_for_cockpit_preview}",
        f"- Ready for hardware send: {readiness.ready_for_hardware_send}",
        f"- Opened controller input: {readiness.opened_controller_input}",
        f"- Captured raw CC: {readiness.captured_raw_cc}",
        f"- Dispatched WebSocket: {readiness.dispatched_websocket}",
        f"- Opened MIDI port: {readiness.opened_midi_port}",
        f"- Sent MIDI: {readiness.sent_midi}",
        f"- Wrote files: {readiness.wrote_files}",
        f"- Mutated snapshot: {readiness.mutated_snapshot}",
        f"- Armed hardware: {readiness.armed_hardware}",
    ]


def _format_ledger_passive_contract(
    report: ControllerBrainOperatorPackageReport,
) -> list[str]:
    return [
        "",
        "Blocked active actions:",
        *[f"- {action}" for action in report.blocked_actions],
        "",
        "Safety:",
        *[f"- {line}" for line in report.safety_lines],
        "",
        "Replay commands:",
        *[f"- {command}" for command in report.replay_commands],
    ]


def format_controller_brain_operator_package_report(
    report: ControllerBrainOperatorPackageReport | None = None,
) -> tuple[str, ...]:
    """Format ``report`` as deterministic operator-readable lines."""

    source_report = build_controller_brain_operator_package_report() if report is None else report
    body_lines: list[str] = []
    body_lines.extend(_format_summary(source_report))
    body_lines.extend(_format_bindings(source_report))
    body_lines.extend(_format_readiness(source_report))
    body_lines.extend(_format_ledger_passive_contract(source_report))
    return tuple(passive_report_lines(_HEADER, body_lines))


def _binding_payload(binding: ControllerBrainOperatorPackageBinding) -> dict[str, object]:
    return {
        "step": binding.step,
        "assignment_key": binding.assignment_key,
        "intent_key": binding.intent_key,
        "controller_action": binding.controller_action,
        "controller_target": binding.controller_target,
        "operator_target": binding.operator_target,
        "package_step_key": binding.package_step_key,
        "slot_key": binding.slot_key,
        "package_export_key": binding.package_export_key,
        "queue_key": binding.queue_key,
        "cockpit_binding": binding.cockpit_binding,
        "recovery_command": binding.recovery_command,
        "readiness_status": binding.readiness_status,
        "mock_safe": binding.mock_safe,
        "operator_action": binding.operator_action,
        "notes": binding.notes,
    }


def _readiness_payload(readiness: ControllerBrainOperatorPackageReadiness) -> dict[str, object]:
    return {
        "status": readiness.status,
        "ready_for_cockpit_preview": readiness.ready_for_cockpit_preview,
        "ready_for_hardware_send": readiness.ready_for_hardware_send,
        "opened_controller_input": readiness.opened_controller_input,
        "captured_raw_cc": readiness.captured_raw_cc,
        "dispatched_websocket": readiness.dispatched_websocket,
        "opened_midi_port": readiness.opened_midi_port,
        "sent_midi": readiness.sent_midi,
        "wrote_files": readiness.wrote_files,
        "mutated_snapshot": readiness.mutated_snapshot,
        "armed_hardware": readiness.armed_hardware,
    }


def build_controller_brain_operator_package_payload() -> dict[str, object]:
    """Build deterministic JSON-ready controller-brain operator-package data."""

    report = build_controller_brain_operator_package_report()
    return {
        "controller_brain_operator_package_ledger": {
            "title": report.title,
            "ledger_version": report.ledger_version,
            "ledger_status": report.ledger_status,
            "source_controller_report": report.source_controller_report,
            "source_operator_package": report.source_operator_package,
            "controller_profile_key": report.controller_profile_key,
            "controller_scenario_key": report.controller_scenario_key,
            "operator_package_id": report.operator_package_id,
            "operator_package_status": report.operator_package_status,
            "operator_slot_count": report.operator_slot_count,
            "gesture_binding_count": report.gesture_binding_count,
            "gesture_bindings": [_binding_payload(binding) for binding in report.gesture_bindings],
            "readiness": _readiness_payload(report.readiness),
            "blocked_actions": list(report.blocked_actions),
            "safety_lines": list(report.safety_lines),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


CONTROLLER_BRAIN_OPERATOR_PACKAGE_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "controller-brain-operator-package-report",
    "Passive controller-brain to operator-package ledger.",
    format_lines=lambda: format_controller_brain_operator_package_report(),
    build_payload=build_controller_brain_operator_package_payload,
)

register(CONTROLLER_BRAIN_OPERATOR_PACKAGE_CLI_COMMAND)

__all__ = (
    "CONTROLLER_BRAIN_OPERATOR_PACKAGE_CLI_COMMAND",
    "ControllerBrainOperatorPackageBinding",
    "ControllerBrainOperatorPackageReadiness",
    "ControllerBrainOperatorPackageReport",
    "build_controller_brain_operator_package_payload",
    "build_controller_brain_operator_package_report",
    "format_controller_brain_operator_package_report",
)
