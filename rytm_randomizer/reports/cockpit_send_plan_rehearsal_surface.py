"""Passive GUI-facing cockpit send-plan rehearsal surface."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from ..cli_registry import CliCommand, register
from ..cockpit.data import CockpitSendPlan
from ._passive_section import (
    PassiveJsonField,
    PassiveLineField,
    passive_dataclass_json,
    passive_section_lines,
)
from .cockpit_send_plan_operator_readiness import (
    CockpitSendPlanOperatorReadinessReport,
    build_cockpit_send_plan_operator_readiness_report,
    to_cockpit_send_plan_operator_readiness_json,
)
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value, status_severity

SurfaceStatus = Literal["ready", "blocked"]
ScreenState = Literal["send-ready-review", "send-blocked-review"]
SendControlState = Literal["review-required", "disabled"]

REPORT_TITLE: Final[str] = "RytmRandomizer passive cockpit send-plan rehearsal surface"
SOURCE_MODULE: Final[str] = "reports.cockpit_send_plan_rehearsal_surface"
SEND_PLAN_REHEARSAL_SURFACE_VERSION: Final[str] = "cockpit-send-plan-rehearsal-surface-v1"
_DEFAULT_SURFACE_LABEL: Final[str] = "Cockpit send-plan rehearsal surface"
_COMMAND_NAME: Final[str] = "cockpit-send-plan-rehearsal-surface-report"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "GUI-facing send-plan rehearsal metadata only",
    "consumes CockpitSendPlan/readiness report metadata only",
    "action controls are declarative and disabled",
    "state bindings are declarative metadata only",
    "does not prepare a new plan",
    "does not apply a plan",
    "does not connect to cockpit sidecar",
    "does not open a WebSocket",
    "does not launch GUI",
    "does not launch app",
    "does not dispatch GUI actions",
    "does not mutate GUI state stores",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_USAGE: Final[str] = (
    "cockpit-send-plan-rehearsal-surface-report usage: "
    "(--plan-json <json>|--plan-file <path>|"
    "--readiness-json <json>|--readiness-file <path>) "
    "[--label <text>] [--json]"
)
SURFACE_STATUS_VALUES: Final[tuple[SurfaceStatus, ...]] = ("ready", "blocked")
SCREEN_STATE_VALUES: Final[tuple[ScreenState, ...]] = (
    "send-ready-review",
    "send-blocked-review",
)
SEND_CONTROL_STATE_VALUES: Final[tuple[SendControlState, ...]] = (
    "review-required",
    "disabled",
)
_SURFACE_STATUS_BY_READINESS: Final[dict[str, SurfaceStatus]] = {
    "ready": "ready",
    "blocked": "blocked",
}
_SCREEN_STATE_BY_STATUS: Final[dict[SurfaceStatus, ScreenState]] = {
    "ready": "send-ready-review",
    "blocked": "send-blocked-review",
}
_SEND_CONTROL_STATE_BY_STATUS: Final[dict[SurfaceStatus, SendControlState]] = {
    "ready": "review-required",
    "blocked": "disabled",
}


@dataclass(frozen=True)
class CockpitSendPlanRehearsalPanelSpec:
    """Static identity fields for one rehearsal-surface panel."""

    panel_key: str
    label: str
    source_key: str


PANEL_SPECS: Final[tuple[CockpitSendPlanRehearsalPanelSpec, ...]] = (
    CockpitSendPlanRehearsalPanelSpec(
        panel_key="summary",
        label="Send plan summary",
        source_key="cockpit_send_plan_operator_readiness",
    ),
    CockpitSendPlanRehearsalPanelSpec(
        panel_key="pad-packets",
        label="Prepared pad packets",
        source_key="pad_summaries",
    ),
    CockpitSendPlanRehearsalPanelSpec(
        panel_key="readiness-checks",
        label="Readiness checks",
        source_key="readiness_checks",
    ),
    CockpitSendPlanRehearsalPanelSpec(
        panel_key="safety-locks",
        label="Passive safety locks",
        source_key="blocked_actions",
    ),
)
_PANEL_JSON_FIELDS: Final[tuple[PassiveJsonField, ...]] = (
    PassiveJsonField("panel_key", "panel_key"),
    PassiveJsonField("label", "label"),
    PassiveJsonField("status", "status"),
    PassiveJsonField("severity", "severity"),
    PassiveJsonField("source_key", "source_key"),
    PassiveJsonField("summary", "summary"),
    PassiveJsonField("value_text", "value_text"),
    PassiveJsonField("passive", "passive"),
)
_BINDING_JSON_FIELDS: Final[tuple[PassiveJsonField, ...]] = (
    PassiveJsonField("state_key", "state_key"),
    PassiveJsonField("source_json_key", "source_json_key"),
    PassiveJsonField("label", "label"),
    PassiveJsonField("value", "value"),
    PassiveJsonField("required", "required"),
    PassiveJsonField("passive", "passive"),
)
_ACTION_CONTROL_JSON_FIELDS: Final[tuple[PassiveJsonField, ...]] = (
    PassiveJsonField("action_key", "action_key"),
    PassiveJsonField("label", "label"),
    PassiveJsonField("control_state", "control_state"),
    PassiveJsonField("gate_status", "gate_status"),
    PassiveJsonField("enabled", "enabled"),
    PassiveJsonField("bound_state_key", "bound_state_key"),
    PassiveJsonField("blocked_reason", "blocked_reason"),
    PassiveJsonField("operator_action", "operator_action"),
    PassiveJsonField("passive", "passive"),
)
_SURFACE_CHECK_JSON_FIELDS: Final[tuple[PassiveJsonField, ...]] = (
    PassiveJsonField("check_key", "check_key"),
    PassiveJsonField("label", "label"),
    PassiveJsonField("status", "status"),
    PassiveJsonField("severity", "severity"),
    PassiveJsonField("source_id", "source_id"),
    PassiveJsonField("message", "message"),
    PassiveJsonField("operator_action", "operator_action"),
    PassiveJsonField("passive", "passive"),
)
_PANEL_LINE_FIELDS: Final[tuple[PassiveLineField, ...]] = (
    PassiveLineField("Status", "status"),
    PassiveLineField("Severity", "severity"),
    PassiveLineField("Source", "source_key"),
    PassiveLineField("Summary", "summary"),
    PassiveLineField("Value", "value_text"),
    PassiveLineField("Passive", "passive"),
)
_BINDING_LINE_FIELDS: Final[tuple[PassiveLineField, ...]] = (
    PassiveLineField("Source JSON", "source_json_key"),
    PassiveLineField("Value", "value"),
    PassiveLineField("Required", "required"),
    PassiveLineField("Passive", "passive"),
)
_ACTION_CONTROL_LINE_FIELDS: Final[tuple[PassiveLineField, ...]] = (
    PassiveLineField("Control state", "control_state"),
    PassiveLineField("Gate status", "gate_status"),
    PassiveLineField("Enabled", "enabled"),
    PassiveLineField("Bound state", "bound_state_key"),
    PassiveLineField("Blocked reason", "blocked_reason"),
    PassiveLineField("Operator action", "operator_action"),
    PassiveLineField("Passive", "passive"),
)
_SURFACE_CHECK_LINE_FIELDS: Final[tuple[PassiveLineField, ...]] = (
    PassiveLineField("Status", "status"),
    PassiveLineField("Severity", "severity"),
    PassiveLineField("Source id", "source_id"),
    PassiveLineField("Message", "message"),
    PassiveLineField("Operator action", "operator_action"),
    PassiveLineField("Passive", "passive"),
)


@dataclass(frozen=True)
class CockpitSendPlanRehearsalPanel:
    """One GUI-facing panel for send-plan rehearsal."""

    panel_key: str
    label: str
    status: str
    severity: str
    source_key: str
    summary: str
    value_text: str
    passive: bool


@dataclass(frozen=True)
class CockpitSendPlanRehearsalStateBinding:
    """One future GUI state binding for send-plan rehearsal."""

    state_key: str
    source_json_key: str
    label: str
    value: str
    required: bool
    passive: bool


@dataclass(frozen=True)
class CockpitSendPlanRehearsalActionControl:
    """One disabled future GUI action control."""

    action_key: str
    label: str
    control_state: str
    gate_status: str
    enabled: bool
    bound_state_key: str
    blocked_reason: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class CockpitSendPlanRehearsalSurfaceCheck:
    """One passive acceptance check for the rehearsal surface."""

    check_key: str
    label: str
    status: str
    severity: str
    source_id: str
    message: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class CockpitSendPlanRehearsalSurfaceReport:
    """Passive GUI-ready state for rehearsing one prepared send plan."""

    readiness_report: CockpitSendPlanOperatorReadinessReport
    surface_version: str
    surface_id: str
    surface_label: str
    surface_status: SurfaceStatus
    screen_state: ScreenState
    send_control_state: SendControlState
    primary_operator_action: str
    panels: tuple[CockpitSendPlanRehearsalPanel, ...]
    state_bindings: tuple[CockpitSendPlanRehearsalStateBinding, ...]
    action_controls: tuple[CockpitSendPlanRehearsalActionControl, ...]
    surface_checks: tuple[CockpitSendPlanRehearsalSurfaceCheck, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def readiness_report_id(self) -> str:
        """Return the upstream readiness report id."""

        return self.readiness_report.report_id

    @property
    def send_plan_id(self) -> str:
        """Return the upstream prepared send-plan id."""

        return self.readiness_report.send_plan_id

    @property
    def candidate_id(self) -> str:
        """Return the upstream mutation candidate id."""

        return self.readiness_report.candidate_id

    @property
    def blocked_reasons(self) -> tuple[str, ...]:
        """Return blocked reasons as plain JSON-ready strings."""

        return tuple(self.readiness_report.blocked_reasons)


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _surface_status(readiness: CockpitSendPlanOperatorReadinessReport) -> SurfaceStatus:
    return _SURFACE_STATUS_BY_READINESS.get(readiness.status, "blocked")


def _screen_state(surface_status: SurfaceStatus) -> ScreenState:
    return _SCREEN_STATE_BY_STATUS[surface_status]


def _send_control_state(surface_status: SurfaceStatus) -> SendControlState:
    return _SEND_CONTROL_STATE_BY_STATUS[surface_status]


def _surface_id(
    readiness: CockpitSendPlanOperatorReadinessReport,
    *,
    surface_label: str,
    surface_status: SurfaceStatus,
    screen_state: ScreenState,
    send_control_state: SendControlState,
) -> str:
    payload = "|".join(
        (
            SEND_PLAN_REHEARSAL_SURFACE_VERSION,
            readiness.report_id,
            readiness.send_plan_id,
            readiness.candidate_id,
            surface_status,
            surface_label,
            screen_state,
            send_control_state,
        )
    )
    return f"send-plan-surface-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def _panel(
    *,
    spec: CockpitSendPlanRehearsalPanelSpec,
    status: str,
    summary: str,
    value_text: str,
) -> CockpitSendPlanRehearsalPanel:
    return CockpitSendPlanRehearsalPanel(
        panel_key=spec.panel_key,
        label=spec.label,
        status=status,
        severity=status_severity(status),
        source_key=spec.source_key,
        summary=summary,
        value_text=value_text,
        passive=True,
    )


def _panels(
    readiness: CockpitSendPlanOperatorReadinessReport,
) -> tuple[CockpitSendPlanRehearsalPanel, ...]:
    packet_count = len(readiness.send_plan.packets)
    blocked_reasons = ", ".join(readiness.blocked_reasons) or "none"
    pad_summary = (
        "; ".join(
            f"pad {summary.pad_id}: {summary.parameter_summary}"
            for summary in readiness.pad_summaries
        )
        or "none"
    )
    blocked_count = sum(1 for check in readiness.readiness_checks if check.status == "blocked")
    status_by_panel: Final[dict[str, str]] = {
        "summary": readiness.status,
        "pad-packets": "ready" if packet_count else "review-needed",
        "readiness-checks": readiness.status,
        "safety-locks": "ready",
    }
    summary_by_panel: Final[dict[str, str]] = {
        "summary": f"{readiness.send_plan_id} is {readiness.status}",
        "pad-packets": f"{packet_count} inert packet rows",
        "readiness-checks": f"{blocked_count} blocked checks",
        "safety-locks": f"{len(readiness.blocked_actions)} blocked active actions",
    }
    value_by_panel: Final[dict[str, str]] = {
        "summary": (
            f"{packet_count} packets, {readiness.send_plan.safety_status} safety, "
            f"blocked reasons: {blocked_reasons}"
        ),
        "pad-packets": pad_summary,
        "readiness-checks": readiness.operator_next_action,
        "safety-locks": ", ".join(readiness.blocked_actions),
    }
    return tuple(
        _panel(
            spec=spec,
            status=status_by_panel[spec.panel_key],
            summary=summary_by_panel[spec.panel_key],
            value_text=value_by_panel[spec.panel_key],
        )
        for spec in PANEL_SPECS
    )


def _binding(
    *,
    state_key: str,
    source_json_key: str,
    label: str,
    value: str,
) -> CockpitSendPlanRehearsalStateBinding:
    return CockpitSendPlanRehearsalStateBinding(
        state_key=state_key,
        source_json_key=source_json_key,
        label=label,
        value=value,
        required=True,
        passive=True,
    )


def _state_bindings(
    readiness: CockpitSendPlanOperatorReadinessReport,
    *,
    screen_state: ScreenState,
    send_control_state: SendControlState,
) -> tuple[CockpitSendPlanRehearsalStateBinding, ...]:
    return (
        _binding(
            state_key="cockpit.sendPlan.status",
            source_json_key="cockpit_send_plan_operator_readiness.status",
            label="Send plan readiness status",
            value=readiness.status,
        ),
        _binding(
            state_key="cockpit.sendPlan.screenState",
            source_json_key="cockpit_send_plan_rehearsal_surface.screen_state",
            label="Screen state",
            value=screen_state,
        ),
        _binding(
            state_key="cockpit.sendPlan.send",
            source_json_key="cockpit_send_plan_rehearsal_surface.send_control_state",
            label="SEND control state",
            value=send_control_state,
        ),
        _binding(
            state_key="cockpit.sendPlan.planId",
            source_json_key="cockpit_send_plan_operator_readiness.send_plan_id",
            label="Send plan id",
            value=readiness.send_plan_id,
        ),
        _binding(
            state_key="cockpit.sendPlan.operatorNextAction",
            source_json_key="cockpit_send_plan_operator_readiness.operator_next_action",
            label="Operator next action",
            value=readiness.operator_next_action,
        ),
        _binding(
            state_key="cockpit.sendPlan.blockedReasons",
            source_json_key="cockpit_send_plan_operator_readiness.blocked_reasons",
            label="Blocked reasons",
            value=", ".join(readiness.blocked_reasons) or "none",
        ),
    )


def _action_controls(
    readiness: CockpitSendPlanOperatorReadinessReport,
    *,
    send_control_state: SendControlState,
) -> tuple[CockpitSendPlanRehearsalActionControl, ...]:
    return (
        CockpitSendPlanRehearsalActionControl(
            action_key="send",
            label="SEND",
            control_state=send_control_state,
            gate_status=readiness.status,
            enabled=False,
            bound_state_key="cockpit.sendPlan.send",
            blocked_reason="passive report; SEND requires the armed cockpit runtime",
            operator_action=readiness.operator_next_action,
            passive=True,
        ),
        CockpitSendPlanRehearsalActionControl(
            action_key="prepare-send-plan",
            label="PREPARE",
            control_state="sidecar-required",
            gate_status="ready",
            enabled=False,
            bound_state_key="cockpit.sendPlan.status",
            blocked_reason="passive report does not call prepare_send_plan",
            operator_action="Use the armed cockpit sidecar to prepare a fresh plan.",
            passive=True,
        ),
        CockpitSendPlanRehearsalActionControl(
            action_key="review-plan",
            label="REVIEW",
            control_state="display-only",
            gate_status="ready",
            enabled=False,
            bound_state_key="cockpit.sendPlan.operatorNextAction",
            blocked_reason="passive metadata only; no GUI action dispatch",
            operator_action="Review the displayed packet rows and readiness checks.",
            passive=True,
        ),
    )


def _surface_check(
    *,
    check_key: str,
    label: str,
    status: str,
    source_id: str,
    message: str,
    operator_action: str,
) -> CockpitSendPlanRehearsalSurfaceCheck:
    return CockpitSendPlanRehearsalSurfaceCheck(
        check_key=check_key,
        label=label,
        status=status,
        severity=status_severity(status),
        source_id=source_id,
        message=message,
        operator_action=operator_action,
        passive=True,
    )


def _surface_checks(
    readiness: CockpitSendPlanOperatorReadinessReport,
    *,
    panels: tuple[CockpitSendPlanRehearsalPanel, ...],
    state_bindings: tuple[CockpitSendPlanRehearsalStateBinding, ...],
    action_controls: tuple[CockpitSendPlanRehearsalActionControl, ...],
) -> tuple[CockpitSendPlanRehearsalSurfaceCheck, ...]:
    send_control = action_controls[0]
    return (
        _surface_check(
            check_key="assert-readiness-report",
            label="Operator readiness report",
            status=readiness.status,
            source_id=readiness.report_id,
            message=f"Readiness report status is {readiness.status}.",
            operator_action=readiness.operator_next_action,
        ),
        _surface_check(
            check_key="assert-panel-coverage",
            label="GUI panel coverage",
            status="ready" if panels else "blocked",
            source_id=readiness.report_id,
            message=f"{len(panels)} GUI-facing panels are available.",
            operator_action="Keep panels display-only until the armed GUI runtime consumes them.",
        ),
        _surface_check(
            check_key="assert-state-binding-coverage",
            label="GUI state binding coverage",
            status="ready" if state_bindings else "blocked",
            source_id=readiness.report_id,
            message=f"{len(state_bindings)} declarative state bindings are available.",
            operator_action="Do not mutate GUI stores from passive CLI reports.",
        ),
        _surface_check(
            check_key="assert-send-action-gated",
            label="SEND action gate",
            status=send_control.gate_status,
            source_id=readiness.send_plan_id,
            message=f"SEND control is {send_control.control_state} and disabled in this report.",
            operator_action=send_control.operator_action,
        ),
        _surface_check(
            check_key="assert-passive-boundary",
            label="Passive boundary",
            status="ready",
            source_id=readiness.report_id,
            message="Rehearsal surface emits metadata only.",
            operator_action="Do not launch GUI, open ports, connect sidecar, or send MIDI.",
        ),
    )


def _blocked_actions(readiness: CockpitSendPlanOperatorReadinessReport) -> tuple[str, ...]:
    actions = list(readiness.blocked_actions)
    for action in (
        "no GUI launch",
        "no app launch",
        "no GUI action dispatch",
        "no GUI state-store mutation",
        "no cockpit sidecar connection",
        "no WebSocket opening",
    ):
        if action not in actions:
            actions.append(action)
    return tuple(actions)


def _replay_command(
    readiness: CockpitSendPlanOperatorReadinessReport,
    *,
    surface_label: str,
) -> str:
    plan_json = json.dumps(readiness.send_plan.to_dict(), sort_keys=True, separators=(",", ":"))
    return (
        f"python -m rytm_randomizer.cli {_COMMAND_NAME} "
        f"--plan-json {powershell_literal_arg(plan_json)} "
        f"--label {powershell_literal_arg(surface_label)}"
    )


def build_cockpit_send_plan_rehearsal_surface_from_readiness(
    readiness_report: CockpitSendPlanOperatorReadinessReport,
    *,
    surface_label: str = _DEFAULT_SURFACE_LABEL,
) -> CockpitSendPlanRehearsalSurfaceReport:
    """Build passive GUI-facing rehearsal state from send-plan readiness."""

    normalized_label = _normalize_nonblank(surface_label, field="surface_label")
    surface_status = _surface_status(readiness_report)
    screen_state = _screen_state(surface_status)
    send_control_state = _send_control_state(surface_status)
    panels = _panels(readiness_report)
    state_bindings = _state_bindings(
        readiness_report,
        screen_state=screen_state,
        send_control_state=send_control_state,
    )
    action_controls = _action_controls(
        readiness_report,
        send_control_state=send_control_state,
    )
    checks = _surface_checks(
        readiness_report,
        panels=panels,
        state_bindings=state_bindings,
        action_controls=action_controls,
    )
    return CockpitSendPlanRehearsalSurfaceReport(
        readiness_report=readiness_report,
        surface_version=SEND_PLAN_REHEARSAL_SURFACE_VERSION,
        surface_id=_surface_id(
            readiness_report,
            surface_label=normalized_label,
            surface_status=surface_status,
            screen_state=screen_state,
            send_control_state=send_control_state,
        ),
        surface_label=normalized_label,
        surface_status=surface_status,
        screen_state=screen_state,
        send_control_state=send_control_state,
        primary_operator_action=readiness_report.operator_next_action,
        panels=panels,
        state_bindings=state_bindings,
        action_controls=action_controls,
        surface_checks=checks,
        blocked_actions=_blocked_actions(readiness_report),
        replay_commands=(_replay_command(readiness_report, surface_label=normalized_label),),
    )


def build_cockpit_send_plan_rehearsal_surface_report(
    send_plan: CockpitSendPlan,
    *,
    surface_label: str = _DEFAULT_SURFACE_LABEL,
) -> CockpitSendPlanRehearsalSurfaceReport:
    """Build passive GUI-facing rehearsal state from a prepared send plan."""

    readiness = build_cockpit_send_plan_operator_readiness_report(
        send_plan,
        label=surface_label,
    )
    return build_cockpit_send_plan_rehearsal_surface_from_readiness(
        readiness,
        surface_label=surface_label,
    )


def _panel_json(panel: CockpitSendPlanRehearsalPanel) -> dict[str, object]:
    return passive_dataclass_json(panel, _PANEL_JSON_FIELDS)


def _binding_json(binding: CockpitSendPlanRehearsalStateBinding) -> dict[str, object]:
    return passive_dataclass_json(binding, _BINDING_JSON_FIELDS)


def _action_control_json(control: CockpitSendPlanRehearsalActionControl) -> dict[str, object]:
    return passive_dataclass_json(control, _ACTION_CONTROL_JSON_FIELDS)


def _surface_check_json(check: CockpitSendPlanRehearsalSurfaceCheck) -> dict[str, object]:
    return passive_dataclass_json(check, _SURFACE_CHECK_JSON_FIELDS)


def to_cockpit_send_plan_rehearsal_surface_json(
    report: CockpitSendPlanRehearsalSurfaceReport,
) -> dict[str, object]:
    """Return deterministic JSON for a passive send-plan rehearsal surface."""

    readiness_json = to_cockpit_send_plan_operator_readiness_json(report.readiness_report)
    return {
        "cockpit_send_plan_rehearsal_surface": {
            "surface_version": report.surface_version,
            "surface_id": report.surface_id,
            "surface_label": report.surface_label,
            "surface_status": report.surface_status,
            "screen_state": report.screen_state,
            "send_control_state": report.send_control_state,
            "primary_operator_action": report.primary_operator_action,
            "readiness_report_id": report.readiness_report_id,
            "send_plan_id": report.send_plan_id,
            "candidate_id": report.candidate_id,
            "blocked_reasons": list(report.blocked_reasons),
            "panels": [_panel_json(panel) for panel in report.panels],
            "state_bindings": [_binding_json(binding) for binding in report.state_bindings],
            "action_controls": [
                _action_control_json(control) for control in report.action_controls
            ],
            "surface_checks": [_surface_check_json(check) for check in report.surface_checks],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **readiness_json,
        "safety": list(SAFETY_LINES),
    }


def _panel_lines(panel: CockpitSendPlanRehearsalPanel) -> list[str]:
    return passive_section_lines(
        f"- {panel.panel_key}: {panel.label}",
        panel,
        _PANEL_LINE_FIELDS,
    )


def _binding_lines(binding: CockpitSendPlanRehearsalStateBinding) -> list[str]:
    return passive_section_lines(
        f"- {binding.state_key}: {binding.label}",
        binding,
        _BINDING_LINE_FIELDS,
    )


def _action_control_lines(control: CockpitSendPlanRehearsalActionControl) -> list[str]:
    return passive_section_lines(
        f"- {control.action_key}: {control.label}",
        control,
        _ACTION_CONTROL_LINE_FIELDS,
    )


def _surface_check_lines(check: CockpitSendPlanRehearsalSurfaceCheck) -> list[str]:
    return passive_section_lines(
        f"- {check.check_key}: {check.label}",
        check,
        _SURFACE_CHECK_LINE_FIELDS,
    )


def format_cockpit_send_plan_rehearsal_surface_report(
    report: CockpitSendPlanRehearsalSurfaceReport,
) -> list[str]:
    """Format a passive send-plan rehearsal surface."""

    lines = [
        "Cockpit send-plan rehearsal surface:",
        f"- Surface id: {report.surface_id}",
        f"- Surface label: {report.surface_label}",
        f"- Surface status: {report.surface_status}",
        f"- Screen state: {report.screen_state}",
        f"- SEND control state: {report.send_control_state}",
        f"- Primary operator action: {report.primary_operator_action}",
        f"- Readiness report id: {report.readiness_report_id}",
        f"- Send plan id: {report.send_plan_id}",
        f"- Candidate id: {report.candidate_id}",
        f"- Blocked reasons: {', '.join(report.blocked_reasons) or 'none'}",
        "GUI panels:",
    ]
    for panel in report.panels:
        lines.extend(_panel_lines(panel))
    lines.append("State bindings:")
    for binding in report.state_bindings:
        lines.extend(_binding_lines(binding))
    lines.append("Action controls:")
    for control in report.action_controls:
        lines.extend(_action_control_lines(control))
    lines.append("Surface checks:")
    for check in report.surface_checks:
        lines.extend(_surface_check_lines(check))
    lines.extend(
        [
            "Blocked active actions:",
            *[f"- {action}" for action in report.blocked_actions],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.replay_commands],
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


def _pop_option_value(remaining: list[str]) -> str:
    return pop_option_value(remaining, usage=_USAGE)


def _send_plan_from_json(value: str) -> CockpitSendPlan:
    decoded = json.loads(value)
    if not isinstance(decoded, Mapping):
        raise ValueError("plan JSON must decode to an object")
    return CockpitSendPlan.from_dict(decoded)


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read {path}: {exc}") from exc


def _send_plan_from_file(path: Path) -> CockpitSendPlan:
    return _send_plan_from_json(_read_text_file(path))


def _readiness_from_mapping(
    decoded: Mapping[str, object],
) -> CockpitSendPlanOperatorReadinessReport:
    readiness_obj = decoded.get("cockpit_send_plan_operator_readiness", decoded)
    if not isinstance(readiness_obj, Mapping):
        raise ValueError("readiness JSON must contain a readiness object")
    send_plan_obj = readiness_obj.get("send_plan")
    if not isinstance(send_plan_obj, Mapping):
        raise ValueError("readiness JSON must include send_plan object")
    label_obj = readiness_obj.get("label", _DEFAULT_SURFACE_LABEL)
    send_plan = CockpitSendPlan.from_dict(send_plan_obj)
    return build_cockpit_send_plan_operator_readiness_report(
        send_plan,
        label=str(label_obj),
    )


def _readiness_from_json(value: str) -> CockpitSendPlanOperatorReadinessReport:
    decoded = json.loads(value)
    if not isinstance(decoded, Mapping):
        raise ValueError("readiness JSON must decode to an object")
    return _readiness_from_mapping(decoded)


def _readiness_from_file(path: Path) -> CockpitSendPlanOperatorReadinessReport:
    return _readiness_from_json(_read_text_file(path))


def parse_cockpit_send_plan_rehearsal_surface_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Parse passive cockpit send-plan rehearsal surface CLI args."""

    plan_json: str | None = None
    plan_file: Path | None = None
    readiness_json: str | None = None
    readiness_file: Path | None = None
    surface_label = _DEFAULT_SURFACE_LABEL
    json_output = False
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
        elif option == "--plan-json":
            plan_json = _pop_option_value(remaining)
        elif option == "--plan-file":
            plan_file = Path(_pop_option_value(remaining))
        elif option == "--readiness-json":
            readiness_json = _pop_option_value(remaining)
        elif option == "--readiness-file":
            readiness_file = Path(_pop_option_value(remaining))
        elif option == "--label":
            surface_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="surface_label",
            )
        else:
            raise ValueError(_USAGE)
    source_count = sum(
        source is not None for source in (plan_json, plan_file, readiness_json, readiness_file)
    )
    if source_count != 1:
        raise ValueError(
            "provide exactly one of --plan-json, --plan-file, "
            "--readiness-json, or --readiness-file"
        )
    parsed: dict[str, object] = {
        "surface_label": surface_label,
        "json_output": json_output,
    }
    if plan_json is not None:
        parsed["send_plan"] = _send_plan_from_json(plan_json)
    elif plan_file is not None:
        parsed["send_plan"] = _send_plan_from_file(plan_file)
    elif readiness_json is not None:
        parsed["readiness_report"] = _readiness_from_json(readiness_json)
    else:
        parsed["readiness_report"] = _readiness_from_file(readiness_file)
    return parsed


def _handle_cli_report(
    *,
    send_plan: object | None = None,
    readiness_report: object | None = None,
    surface_label: object = _DEFAULT_SURFACE_LABEL,
    json_output: object = False,
) -> int:
    try:
        if not isinstance(surface_label, str):
            raise TypeError("surface_label must be a string")
        if isinstance(readiness_report, CockpitSendPlanOperatorReadinessReport):
            report = build_cockpit_send_plan_rehearsal_surface_from_readiness(
                readiness_report,
                surface_label=surface_label,
            )
        else:
            if readiness_report is not None:
                raise TypeError("readiness_report must be a CockpitSendPlanOperatorReadinessReport")
            if not isinstance(send_plan, CockpitSendPlan):
                raise TypeError("send_plan must be a CockpitSendPlan")
            report = build_cockpit_send_plan_rehearsal_surface_report(
                send_plan,
                surface_label=surface_label,
            )
        if json_output is True:
            sys.stdout.write(
                json.dumps(
                    to_cockpit_send_plan_rehearsal_surface_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_cockpit_send_plan_rehearsal_surface_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=_COMMAND_NAME,
    summary="Build passive GUI-facing cockpit SEND plan rehearsal state.",
    args_parser=parse_cockpit_send_plan_rehearsal_surface_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND)

__all__ = [
    "COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND",
    "PANEL_SPECS",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SCREEN_STATE_VALUES",
    "SEND_CONTROL_STATE_VALUES",
    "SEND_PLAN_REHEARSAL_SURFACE_VERSION",
    "SOURCE_MODULE",
    "SURFACE_STATUS_VALUES",
    "CockpitSendPlanRehearsalActionControl",
    "CockpitSendPlanRehearsalPanel",
    "CockpitSendPlanRehearsalPanelSpec",
    "CockpitSendPlanRehearsalStateBinding",
    "CockpitSendPlanRehearsalSurfaceCheck",
    "CockpitSendPlanRehearsalSurfaceReport",
    "build_cockpit_send_plan_rehearsal_surface_from_readiness",
    "build_cockpit_send_plan_rehearsal_surface_report",
    "format_cockpit_send_plan_rehearsal_surface_report",
    "parse_cockpit_send_plan_rehearsal_surface_cli_args",
    "to_cockpit_send_plan_rehearsal_surface_json",
]
