"""Passive live GUI safety-checklist and arm-hardware gate model."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Final, TypedDict

from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive live GUI safety-checklist model"
SOURCE_MODULE: Final[str] = "reports.live_gui_safety_checklist_model"
SAFETY_CHECKLIST_MODEL_VERSION: Final[str] = "live-gui-safety-checklist-model-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI safety-checklist metadata only",
    "future desktop GUI only",
    "arm gate is declarative metadata only",
    "caller-supplied readiness metadata only",
    "JSON/stdout only",
    "no GUI launch",
    "no app launch",
    "no GUI event dispatch",
    "no GUI controller dispatch",
    "no GUI state-store mutation",
    "no real MIDI rendering",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "arm hardware from safety checklist",
    "open MIDI port from safety checklist",
    "send MIDI from safety checklist",
    "mutate hardware from safety checklist",
    "launch GUI from safety checklist",
)
ARM_REQUIREMENTS: Final[tuple[str, ...]] = (
    "send plan ready",
    "dry run complete",
    "MIDI port open",
    "hardware connected",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class LiveGuiSafetyChecklistItem:
    """One passive safety checklist row for the future GUI right rail."""

    key: str
    order: int
    label: str
    status: str
    severity: str
    message: str
    operator_action: str
    test_id: str


class LiveGuiSafetyChecklistItemDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiSafetyChecklistItem`."""

    key: str
    order: int
    label: str
    status: str
    severity: str
    message: str
    operator_action: str
    test_id: str


@dataclass(frozen=True)
class LiveGuiArmHardwareGate:
    """Declarative future Arm Hardware control state."""

    key: str
    label: str
    state: str
    enabled: bool
    reason: str
    requirements: tuple[str, ...]
    midi_port_name: str | None
    midi_port_open: bool
    hardware_connected: bool
    send_plan_ready: bool
    dry_run_complete: bool
    test_id: str


class LiveGuiArmHardwareGateDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiArmHardwareGate`."""

    key: str
    label: str
    state: str
    enabled: bool
    reason: str
    requirements: tuple[str, ...]
    midi_port_name: str | None
    midi_port_open: bool
    hardware_connected: bool
    send_plan_ready: bool
    dry_run_complete: bool
    test_id: str


@dataclass(frozen=True)
class LiveGuiSafetyChecklistModel:
    """Passive safety checklist packet consumed by future desktop UI."""

    safety_checklist_version: str
    safety_checklist_id: str
    session_label: str
    checklist_status: str
    passed_count: int
    total_count: int
    items: tuple[LiveGuiSafetyChecklistItem, ...]
    arm_gate: LiveGuiArmHardwareGate
    safety_lines: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]


class LiveGuiSafetyChecklistModelDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiSafetyChecklistModel`."""

    safety_checklist_version: str
    safety_checklist_id: str
    session_label: str
    checklist_status: str
    passed_count: int
    total_count: int
    items: tuple[LiveGuiSafetyChecklistItemDict, ...]
    arm_gate: LiveGuiArmHardwareGateDict
    safety_lines: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]


def _safety_checklist_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _safety_checklist_status(items: tuple[LiveGuiSafetyChecklistItem, ...]) -> str:
    if all(item.status == "passed" for item in items):
        return "passed"
    return "blocked"


def _safety_item(
    *,
    key: str,
    order: int,
    label: str,
    passed: bool,
    passed_message: str,
    blocked_message: str,
    blocked_action: str,
) -> LiveGuiSafetyChecklistItem:
    return LiveGuiSafetyChecklistItem(
        key=key,
        order=order,
        label=label,
        status="passed" if passed else "blocked",
        severity="safe" if passed else "critical",
        message=passed_message if passed else blocked_message,
        operator_action="No action required." if passed else blocked_action,
        test_id=f"safety-checklist-{key}",
    )


def _safety_checklist_items(
    *,
    conflicting_session_count: int,
    guards_enabled: bool,
    snapshot_compatible: bool,
    parameter_limits_ok: bool,
) -> tuple[LiveGuiSafetyChecklistItem, ...]:
    return (
        _safety_item(
            key="conflicting-sessions",
            order=0,
            label="No conflicting sessions",
            passed=conflicting_session_count == 0,
            passed_message="No conflicting sessions detected",
            blocked_message=f"{conflicting_session_count} conflicting session(s) detected",
            blocked_action="Close or resolve conflicting sessions first.",
        ),
        _safety_item(
            key="guards-enabled",
            order=1,
            label="All guards enabled",
            passed=guards_enabled,
            passed_message="All safety guards enabled",
            blocked_message="One or more safety guards are disabled",
            blocked_action="Re-enable all safety guards before arm review.",
        ),
        _safety_item(
            key="snapshot-compatible",
            order=2,
            label="Snapshot compatibility verified",
            passed=snapshot_compatible,
            passed_message="Snapshot compatibility verified",
            blocked_message="Snapshot compatibility is not verified",
            blocked_action="Load a compatible snapshot before arm review.",
        ),
        _safety_item(
            key="parameter-limits",
            order=3,
            label="Parameter limits within safe range",
            passed=parameter_limits_ok,
            passed_message="Parameter limits within safe range",
            blocked_message="One or more parameters are outside the safe range",
            blocked_action="Regenerate or lower mutation depth before arm review.",
        ),
    )


def _arm_gate(
    *,
    checklist_status: str,
    midi_port_name: str | None,
    midi_port_open: bool,
    hardware_connected: bool,
    send_plan_ready: bool,
    dry_run_complete: bool,
) -> LiveGuiArmHardwareGate:
    if checklist_status == "blocked":
        state = "blocked"
        enabled = False
        reason = "Resolve blocked safety checklist rows before arming."
    elif send_plan_ready and dry_run_complete and midi_port_open and hardware_connected:
        state = "ready-to-arm"
        enabled = True
        reason = "Future GUI may enable Arm Hardware after explicit operator confirmation."
    else:
        state = "locked"
        enabled = False
        reason = (
            "Arm Hardware stays locked until SEND readiness, dry run, MIDI port, "
            "and hardware metadata are all ready."
        )

    return LiveGuiArmHardwareGate(
        key="arm-hardware",
        label="Arm Hardware",
        state=state,
        enabled=enabled,
        reason=reason,
        requirements=ARM_REQUIREMENTS,
        midi_port_name=midi_port_name,
        midi_port_open=midi_port_open,
        hardware_connected=hardware_connected,
        send_plan_ready=send_plan_ready,
        dry_run_complete=dry_run_complete,
        test_id="safety-checklist-arm-hardware",
    )


def _safety_checklist_id(
    *,
    session_label: str,
    items: tuple[LiveGuiSafetyChecklistItem, ...],
    arm_gate: LiveGuiArmHardwareGate,
) -> str:
    item_parts = tuple(
        "|".join((item.key, item.status, item.message, item.operator_action)) for item in items
    )
    payload = "||".join(
        (
            SAFETY_CHECKLIST_MODEL_VERSION,
            session_label,
            arm_gate.state,
            str(arm_gate.enabled),
            arm_gate.midi_port_name or "",
            str(arm_gate.midi_port_open),
            str(arm_gate.hardware_connected),
            str(arm_gate.send_plan_ready),
            str(arm_gate.dry_run_complete),
            *item_parts,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_live_gui_safety_checklist_model(
    *,
    session_label: str = "Live Session",
    conflicting_session_count: int = 0,
    guards_enabled: bool = True,
    snapshot_compatible: bool = True,
    parameter_limits_ok: bool = True,
    midi_port_name: str | None = None,
    midi_port_open: bool = False,
    hardware_connected: bool = False,
    send_plan_ready: bool = False,
    dry_run_complete: bool = False,
) -> LiveGuiSafetyChecklistModel:
    """Build deterministic passive safety checklist metadata for future GUI."""

    normalized_session_label = _safety_checklist_nonblank(
        session_label,
        field="session_label",
    )
    normalized_midi_port_name = (
        _safety_checklist_nonblank(midi_port_name, field="midi_port_name")
        if midi_port_name is not None
        else None
    )
    if conflicting_session_count < 0:
        raise ValueError("conflicting_session_count must be >= 0")

    items = _safety_checklist_items(
        conflicting_session_count=conflicting_session_count,
        guards_enabled=guards_enabled,
        snapshot_compatible=snapshot_compatible,
        parameter_limits_ok=parameter_limits_ok,
    )
    checklist_status = _safety_checklist_status(items)
    arm_gate = _arm_gate(
        checklist_status=checklist_status,
        midi_port_name=normalized_midi_port_name,
        midi_port_open=midi_port_open,
        hardware_connected=hardware_connected,
        send_plan_ready=send_plan_ready,
        dry_run_complete=dry_run_complete,
    )
    passed_count = sum(1 for item in items if item.status == "passed")
    return LiveGuiSafetyChecklistModel(
        safety_checklist_version=SAFETY_CHECKLIST_MODEL_VERSION,
        safety_checklist_id=_safety_checklist_id(
            session_label=normalized_session_label,
            items=items,
            arm_gate=arm_gate,
        ),
        session_label=normalized_session_label,
        checklist_status=checklist_status,
        passed_count=passed_count,
        total_count=len(items),
        items=items,
        arm_gate=arm_gate,
        safety_lines=SAFETY_LINES,
        blocked_actions=BLOCKED_ACTIONS,
        # The former replay command pointed at the never-registered
        # `live-gui-safety-checklist-model-report` CLI command (dead wiring,
        # retired 2026-07-28 per the live-GUI retirement evidence doc §3).
        replay_commands=(),
    )


def format_live_gui_safety_checklist_model(
    report: LiveGuiSafetyChecklistModel,
) -> list[str]:
    """Render the passive safety checklist packet as deterministic operator text."""

    body_lines = [
        "Safety checklist summary:",
        f"- safety checklist id: {report.safety_checklist_id}",
        f"- session: {report.session_label}",
        f"- checklist: {report.passed_count} / {report.total_count} passed",
        f"- arm hardware: {report.arm_gate.state}",
        "Safety checklist rows:",
    ]
    for item in report.items:
        body_lines.append(f"- {item.key}: {item.status} - {item.message}")
    body_lines.append("Arm hardware gate:")
    body_lines.append(f"- enabled: {report.arm_gate.enabled}")
    body_lines.append(f"- reason: {report.arm_gate.reason}")
    body_lines.append("Blocked active actions:")
    body_lines.extend(f"- {action}" for action in report.blocked_actions)
    body_lines.append("Replay commands:")
    body_lines.extend(f"- {command}" for command in report.replay_commands)
    body_lines.append(SAFETY_SECTION_HEADER)
    body_lines.extend(f"- {line}" for line in report.safety_lines)
    return passive_report_lines(_HEADER, body_lines)


def to_live_gui_safety_checklist_model_json(
    report: LiveGuiSafetyChecklistModel,
) -> dict[str, object]:
    """Return a deterministic JSON-ready payload for the future GUI."""

    return {
        "live_gui_safety_checklist_model": {
            "safety_checklist_version": report.safety_checklist_version,
            "safety_checklist_id": report.safety_checklist_id,
            "session_label": report.session_label,
            "checklist_status": report.checklist_status,
            "passed_count": report.passed_count,
            "total_count": report.total_count,
            "items": [asdict(item) for item in report.items],
            "arm_gate": asdict(report.arm_gate),
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


__all__ = [
    "ARM_REQUIREMENTS",
    "BLOCKED_ACTIONS",
    "LiveGuiArmHardwareGate",
    "LiveGuiArmHardwareGateDict",
    "LiveGuiSafetyChecklistItem",
    "LiveGuiSafetyChecklistItemDict",
    "LiveGuiSafetyChecklistModel",
    "LiveGuiSafetyChecklistModelDict",
    "REPORT_TITLE",
    "SAFETY_CHECKLIST_MODEL_VERSION",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_live_gui_safety_checklist_model",
    "format_live_gui_safety_checklist_model",
    "to_live_gui_safety_checklist_model_json",
]
