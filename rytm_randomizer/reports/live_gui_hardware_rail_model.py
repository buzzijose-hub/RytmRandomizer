"""Passive live GUI hardware rail model for future desktop surfaces."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from .formatter import PassiveReportHeader, passive_report_lines, powershell_literal_arg

REPORT_TITLE: Final[str] = "RytmRandomizer passive live GUI hardware rail model"
SOURCE_MODULE: Final[str] = "reports.live_gui_hardware_rail_model"
MODEL_VERSION: Final[str] = "live-gui-hardware-rail-v1"
DEFAULT_SESSION_LABEL: Final[str] = "Live Session"
DEFAULT_DEVICE_LABEL: Final[str] = "Analog Rytm MKII"
DEFAULT_MODE_LABEL: Final[str] = "Simulation / Mock"
_SAFETY_CHECK_KEYS: Final[tuple[str, ...]] = (
    "no_conflicting_sessions",
    "guards_enabled",
    "snapshot_compatible",
    "parameter_limits_safe",
)
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "right-rail metadata only",
    "available MIDI ports are caller-provided labels only",
    "selected MIDI port is a caller-provided label only",
    "no MIDI port enumeration",
    "no MIDI port opened",
    "no MIDI sending",
    "no command dispatch",
    "no GUI launch",
    "no file writing",
    "no hardware mutation",
    "hardware arm state is declarative metadata only",
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "no MIDI port enumeration",
    "no MIDI port opened",
    "no MIDI sending",
    "no command dispatch",
    "no GUI launch",
    "no file writing",
    "no hardware mutation",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class LiveGuiHardwareRailAction:
    """One passive right-rail control action."""

    key: str
    label: str
    enabled: bool
    reason: str
    test_id: str


@dataclass(frozen=True)
class LiveGuiHardwareRailCard:
    """One passive right-rail card for the future GUI."""

    key: str
    title: str
    status: str
    severity: str
    summary: str
    details: tuple[str, ...]
    actions: tuple[LiveGuiHardwareRailAction, ...]
    test_id: str


@dataclass(frozen=True)
class LiveGuiHardwareRailSafetyCheck:
    """One passive safety-check row."""

    key: str
    label: str
    passed: bool
    status: str
    test_id: str


@dataclass(frozen=True)
class LiveGuiHardwareRailModel:
    """Passive hardware rail payload for the future desktop GUI."""

    model_version: str
    rail_id: str
    session_label: str
    device_label: str
    mode_label: str
    rail_status: str
    dry_run_active: bool
    hardware_requested: bool
    port_status: str
    selected_port_name: str | None
    available_ports: tuple[str, ...]
    safety_checks: tuple[LiveGuiHardwareRailSafetyCheck, ...]
    safety_check_count: int
    safety_checks_passed: int
    failing_safety_checks: tuple[str, ...]
    arm_status: str
    arm_locked: bool
    cards: tuple[LiveGuiHardwareRailCard, ...]
    required_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]
    safety: tuple[str, ...]


def _hardware_rail_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _hardware_rail_display_key(key: str) -> str:
    return key.replace("_", "-")


def _hardware_rail_normalize_ports(available_ports: Sequence[str]) -> tuple[str, ...]:
    normalized_ports: list[str] = []
    seen: set[str] = set()
    blank_seen = False
    for port_name in available_ports:
        normalized = port_name.strip()
        if not normalized:
            blank_seen = True
            continue
        if normalized not in seen:
            normalized_ports.append(normalized)
            seen.add(normalized)
    if blank_seen and not normalized_ports:
        raise ValueError("available_ports must contain at least one nonblank port label")
    return tuple(normalized_ports)


def _hardware_rail_safety_checks(
    safety_checks: Mapping[str, bool] | None,
) -> tuple[LiveGuiHardwareRailSafetyCheck, ...]:
    checks: dict[str, bool] = dict.fromkeys(_SAFETY_CHECK_KEYS, True)
    if safety_checks is not None:
        if set(safety_checks) != set(_SAFETY_CHECK_KEYS):
            expected = ", ".join(_SAFETY_CHECK_KEYS)
            raise ValueError(f"safety_checks must contain exactly: {expected}")
        checks = {key: bool(safety_checks[key]) for key in _SAFETY_CHECK_KEYS}
    return tuple(
        LiveGuiHardwareRailSafetyCheck(
            key=_hardware_rail_display_key(key),
            label=_hardware_rail_display_key(key),
            passed=passed,
            status="passed" if passed else "failed",
            test_id=f"hardware-rail-safety-{_hardware_rail_display_key(key)}",
        )
        for key, passed in checks.items()
    )


def _hardware_rail_port_status(
    *,
    selected_port_name: str | None,
    available_ports: tuple[str, ...],
) -> str:
    if selected_port_name is None:
        return "none"
    if selected_port_name not in available_ports:
        return "missing"
    return "selected"


def _hardware_rail_failing_checks(
    safety_checks: tuple[LiveGuiHardwareRailSafetyCheck, ...],
) -> tuple[str, ...]:
    return tuple(check.key for check in safety_checks if not check.passed)


def _hardware_rail_arm_reason(
    *,
    dry_run_active: bool,
    port_status: str,
    failing_safety_checks: tuple[str, ...],
    hardware_requested: bool,
) -> str:
    if dry_run_active:
        return "dry-run mode is active"
    if port_status == "none":
        return "no MIDI port selected"
    if port_status == "missing":
        return "selected MIDI port is unavailable"
    if failing_safety_checks:
        return f"failed safety checks: {', '.join(failing_safety_checks)}"
    if not hardware_requested:
        return "hardware arm has not been requested"
    return "all passive readiness prerequisites are satisfied"


def _hardware_rail_arm_status(
    *,
    dry_run_active: bool,
    port_status: str,
    failing_safety_checks: tuple[str, ...],
    hardware_requested: bool,
) -> str:
    if failing_safety_checks:
        return "blocked"
    if dry_run_active or port_status != "selected" or not hardware_requested:
        return "locked"
    return "ready"


def _hardware_rail_required_actions(
    *,
    dry_run_active: bool,
    port_status: str,
    failing_safety_checks: tuple[str, ...],
    hardware_requested: bool,
) -> tuple[str, ...]:
    if failing_safety_checks:
        return ("resolve-safety-checks",)
    if port_status == "missing":
        return ("select-valid-midi-port",)
    actions: list[str] = []
    if port_status == "none":
        actions.append("select-midi-port")
    if dry_run_active:
        actions.append("disable-dry-run-before-hardware")
    if not hardware_requested:
        actions.append("request-hardware-arm")
    if actions:
        return tuple(actions)
    return ("operator-confirm-arm",)


def _hardware_rail_rail_status(
    *,
    dry_run_active: bool,
    arm_status: str,
) -> str:
    if arm_status == "blocked":
        return "blocked"
    if arm_status == "ready":
        return "ready"
    if dry_run_active:
        return "mock-safe"
    return "locked"


def _hardware_rail_port_summary(port_status: str) -> str:
    if port_status == "selected":
        return "MIDI port is selected in passive metadata."
    if port_status == "missing":
        return "Selected MIDI port is not in the available passive list."
    return "No MIDI port selected or opened."


def _hardware_rail_card_details(
    *,
    available_ports: tuple[str, ...],
    selected_port_name: str | None,
) -> tuple[str, ...]:
    details: list[str] = []
    if selected_port_name is not None:
        details.append(f"selected port: {selected_port_name}")
    if available_ports:
        details.append(f"available ports: {', '.join(available_ports)}")
    return tuple(details)


def _hardware_rail_cards(
    *,
    dry_run_active: bool,
    port_status: str,
    available_ports: tuple[str, ...],
    selected_port_name: str | None,
    arm_status: str,
    arm_reason: str,
    arm_locked: bool,
) -> tuple[LiveGuiHardwareRailCard, ...]:
    mock_card = LiveGuiHardwareRailCard(
        key="mock-dry-run",
        title="Mock / Dry Run",
        status="active" if dry_run_active else "off",
        severity="safe" if dry_run_active else "review",
        summary=(
            "All changes are simulated. No hardware will be modified."
            if dry_run_active
            else "Dry-run is off; hardware controls still require explicit arm readiness."
        ),
        details=("preview and dry-run controls are metadata only",),
        actions=(
            LiveGuiHardwareRailAction(
                key="toggle-dry-run",
                label="Toggle dry run",
                enabled=True,
                reason="passive GUI state toggle metadata only",
                test_id="hardware-rail-action-toggle-dry-run",
            ),
        ),
        test_id="hardware-rail-card-mock-dry-run",
    )
    port_card = LiveGuiHardwareRailCard(
        key="midi-port",
        title="MIDI Port",
        status=port_status,
        severity="ready" if port_status == "selected" else "blocked",
        summary=_hardware_rail_port_summary(port_status),
        details=_hardware_rail_card_details(
            available_ports=available_ports,
            selected_port_name=selected_port_name,
        ),
        actions=(
            LiveGuiHardwareRailAction(
                key="select-midi-port",
                label="Select MIDI port",
                enabled=bool(available_ports),
                reason=(
                    "caller supplied passive port labels"
                    if available_ports
                    else "no passive port labels supplied"
                ),
                test_id="hardware-rail-action-select-midi-port",
            ),
        ),
        test_id="hardware-rail-card-midi-port",
    )
    arm_card = LiveGuiHardwareRailCard(
        key="arm-hardware",
        title="Arm Hardware",
        status=arm_status,
        severity="ready" if arm_status == "ready" else "blocked",
        summary=(
            "Hardware arm metadata is ready for an operator confirmation."
            if arm_status == "ready"
            else (
                "Hardware arm is blocked by failed safety checks."
                if arm_status == "blocked"
                else "Hardware arm is locked until prerequisites are satisfied."
            )
        ),
        details=(arm_reason,),
        actions=(
            LiveGuiHardwareRailAction(
                key="arm-hardware",
                label="Arm hardware",
                enabled=not arm_locked,
                reason=arm_reason,
                test_id="hardware-rail-action-arm-hardware",
            ),
        ),
        test_id="hardware-rail-card-arm-hardware",
    )
    return (mock_card, port_card, arm_card)


def _hardware_rail_id(
    *,
    session_label: str,
    device_label: str,
    mode_label: str,
    rail_status: str,
    dry_run_active: bool,
    hardware_requested: bool,
    port_status: str,
    selected_port_name: str | None,
    available_ports: tuple[str, ...],
    failing_safety_checks: tuple[str, ...],
) -> str:
    payload = "|".join(
        (
            MODEL_VERSION,
            session_label,
            device_label,
            mode_label,
            rail_status,
            str(dry_run_active),
            str(hardware_requested),
            port_status,
            selected_port_name or "",
            ",".join(available_ports),
            ",".join(failing_safety_checks),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _hardware_rail_replay_command(
    *,
    session_label: str,
    device_label: str,
    selected_port_name: str | None,
    hardware_requested: bool,
    dry_run_active: bool,
) -> str:
    command = (
        "python -m rytm_randomizer.cli live-gui-hardware-rail-report "
        f"--session {powershell_literal_arg(session_label)} "
        f"--device {powershell_literal_arg(device_label)}"
    )
    if selected_port_name is not None:
        command += f" --port {powershell_literal_arg(selected_port_name)}"
    if hardware_requested:
        command += " --hardware-requested"
    command += f" --dry-run {'on' if dry_run_active else 'off'}"
    return command


def build_live_gui_hardware_rail_model(
    *,
    session_label: str = DEFAULT_SESSION_LABEL,
    device_label: str = DEFAULT_DEVICE_LABEL,
    mode_label: str = DEFAULT_MODE_LABEL,
    available_ports: Sequence[str] = (),
    selected_port_name: str | None = None,
    dry_run_active: bool = True,
    hardware_requested: bool = False,
    safety_checks: Mapping[str, bool] | None = None,
) -> LiveGuiHardwareRailModel:
    """Build a passive hardware rail model from caller-provided metadata."""

    normalized_session_label = _hardware_rail_nonblank(
        session_label,
        field="session_label",
    )
    normalized_device_label = _hardware_rail_nonblank(device_label, field="device_label")
    normalized_mode_label = _hardware_rail_nonblank(mode_label, field="mode_label")
    normalized_ports = _hardware_rail_normalize_ports(available_ports)
    normalized_selected_port = (
        _hardware_rail_nonblank(selected_port_name, field="selected_port_name")
        if selected_port_name is not None
        else None
    )
    normalized_safety_checks = _hardware_rail_safety_checks(safety_checks)
    failing_safety_checks = _hardware_rail_failing_checks(normalized_safety_checks)
    port_status = _hardware_rail_port_status(
        selected_port_name=normalized_selected_port,
        available_ports=normalized_ports,
    )
    arm_status = _hardware_rail_arm_status(
        dry_run_active=dry_run_active,
        port_status=port_status,
        failing_safety_checks=failing_safety_checks,
        hardware_requested=hardware_requested,
    )
    arm_locked = arm_status != "ready"
    rail_status = _hardware_rail_rail_status(
        dry_run_active=dry_run_active,
        arm_status=arm_status,
    )
    arm_reason = _hardware_rail_arm_reason(
        dry_run_active=dry_run_active,
        port_status=port_status,
        failing_safety_checks=failing_safety_checks,
        hardware_requested=hardware_requested,
    )
    cards = _hardware_rail_cards(
        dry_run_active=dry_run_active,
        port_status=port_status,
        available_ports=normalized_ports,
        selected_port_name=normalized_selected_port,
        arm_status=arm_status,
        arm_reason=arm_reason,
        arm_locked=arm_locked,
    )
    return LiveGuiHardwareRailModel(
        model_version=MODEL_VERSION,
        rail_id=_hardware_rail_id(
            session_label=normalized_session_label,
            device_label=normalized_device_label,
            mode_label=normalized_mode_label,
            rail_status=rail_status,
            dry_run_active=dry_run_active,
            hardware_requested=hardware_requested,
            port_status=port_status,
            selected_port_name=normalized_selected_port,
            available_ports=normalized_ports,
            failing_safety_checks=failing_safety_checks,
        ),
        session_label=normalized_session_label,
        device_label=normalized_device_label,
        mode_label=normalized_mode_label,
        rail_status=rail_status,
        dry_run_active=dry_run_active,
        hardware_requested=hardware_requested,
        port_status=port_status,
        selected_port_name=normalized_selected_port,
        available_ports=normalized_ports,
        safety_checks=normalized_safety_checks,
        safety_check_count=len(normalized_safety_checks),
        safety_checks_passed=sum(1 for check in normalized_safety_checks if check.passed),
        failing_safety_checks=failing_safety_checks,
        arm_status=arm_status,
        arm_locked=arm_locked,
        cards=cards,
        required_actions=_hardware_rail_required_actions(
            dry_run_active=dry_run_active,
            port_status=port_status,
            failing_safety_checks=failing_safety_checks,
            hardware_requested=hardware_requested,
        ),
        blocked_actions=BLOCKED_ACTIONS,
        replay_commands=(
            _hardware_rail_replay_command(
                session_label=normalized_session_label,
                device_label=normalized_device_label,
                selected_port_name=normalized_selected_port,
                hardware_requested=hardware_requested,
                dry_run_active=dry_run_active,
            ),
        ),
        safety=SAFETY_LINES,
    )


def _hardware_rail_action_json(action: LiveGuiHardwareRailAction) -> dict[str, object]:
    return {
        "key": action.key,
        "label": action.label,
        "enabled": action.enabled,
        "reason": action.reason,
        "test_id": action.test_id,
    }


def _hardware_rail_card_json(card: LiveGuiHardwareRailCard) -> dict[str, object]:
    return {
        "key": card.key,
        "title": card.title,
        "status": card.status,
        "severity": card.severity,
        "summary": card.summary,
        "details": list(card.details),
        "actions": [_hardware_rail_action_json(action) for action in card.actions],
        "test_id": card.test_id,
    }


def _hardware_rail_safety_json(
    safety_check: LiveGuiHardwareRailSafetyCheck,
) -> dict[str, object]:
    return {
        "key": safety_check.key,
        "label": safety_check.label,
        "passed": safety_check.passed,
        "status": safety_check.status,
        "test_id": safety_check.test_id,
    }


def to_live_gui_hardware_rail_model_json(
    report: LiveGuiHardwareRailModel,
) -> dict[str, object]:
    """Return a deterministic JSON-compatible payload for the hardware rail."""

    return {
        "live_gui_hardware_rail": {
            "model_version": report.model_version,
            "rail_id": report.rail_id,
            "session_label": report.session_label,
            "device_label": report.device_label,
            "mode_label": report.mode_label,
            "rail_status": report.rail_status,
            "dry_run_active": report.dry_run_active,
            "hardware_requested": report.hardware_requested,
            "port_status": report.port_status,
            "selected_port_name": report.selected_port_name,
            "available_ports": list(report.available_ports),
            "safety_checks": [_hardware_rail_safety_json(check) for check in report.safety_checks],
            "safety_check_count": report.safety_check_count,
            "safety_checks_passed": report.safety_checks_passed,
            "failing_safety_checks": list(report.failing_safety_checks),
            "arm_status": report.arm_status,
            "arm_locked": report.arm_locked,
            "cards": [_hardware_rail_card_json(card) for card in report.cards],
            "required_actions": list(report.required_actions),
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety),
    }


def format_live_gui_hardware_rail_model(
    report: LiveGuiHardwareRailModel,
) -> list[str]:
    """Render the passive hardware rail model as operator-readable lines."""

    body: list[str] = [
        "",
        "Hardware rail summary:",
        f"- rail status: {report.rail_status}",
        f"- session: {report.session_label}",
        f"- device: {report.device_label}",
        f"- mode: {report.mode_label}",
        f"- dry run active: {report.dry_run_active}",
        f"- port status: {report.port_status}",
        f"- selected port: {report.selected_port_name or 'none'}",
        f"- safety checks: {report.safety_checks_passed}/{report.safety_check_count}",
        f"- arm status: {report.arm_status}",
        "",
        "Right rail cards:",
    ]
    for card in report.cards:
        body.append(f"- {card.key}: {card.status} ({card.severity})")
        body.append(f"  summary: {card.summary}")
        for detail in card.details:
            body.append(f"  detail: {detail}")
    body.extend(
        (
            "",
            "Required actions:",
        )
    )
    body.extend(f"- {action}" for action in report.required_actions)
    body.extend(("", "Blocked actions:"))
    body.extend(f"- {action}" for action in report.blocked_actions)
    body.extend(("", "Replay commands:"))
    body.extend(f"- {command}" for command in report.replay_commands)
    body.extend(("", "Safety:"))
    body.extend(f"- {line}" for line in report.safety)
    return passive_report_lines(_HEADER, body)


__all__ = [
    "BLOCKED_ACTIONS",
    "DEFAULT_DEVICE_LABEL",
    "DEFAULT_MODE_LABEL",
    "DEFAULT_SESSION_LABEL",
    "LiveGuiHardwareRailAction",
    "LiveGuiHardwareRailCard",
    "LiveGuiHardwareRailModel",
    "LiveGuiHardwareRailSafetyCheck",
    "MODEL_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_live_gui_hardware_rail_model",
    "format_live_gui_hardware_rail_model",
    "to_live_gui_hardware_rail_model_json",
]
