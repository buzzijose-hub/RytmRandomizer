"""Passive live GUI status/footer model for desktop shell chrome."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Final

from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive live GUI status/footer model"
SOURCE_MODULE: Final[str] = "reports.live_gui_status_footer_model"
STATUS_FOOTER_MODEL_VERSION: Final[str] = "live-gui-status-footer-model-v1"
DEFAULT_APP_VERSION: Final[str] = "v1.34.0"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI status/footer metadata only",
    "future desktop GUI only",
    "status chips are declarative metadata only",
    "MIDI port state is caller-supplied metadata only",
    "hardware state is caller-supplied metadata only",
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
    "open MIDI port from status footer",
    "send MIDI from status footer",
    "arm hardware from status footer",
    "mutate hardware from status footer",
    "launch GUI from status footer",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_VALID_SAFETY_STATES: Final[tuple[str, ...]] = (
    "mock-safe",
    "armed",
    "review-needed",
    "blocked",
)


@dataclass(frozen=True)
class LiveGuiStatusFooterItem:
    """One passive footer chip for the future live GUI shell."""

    key: str
    order: int
    label: str
    value: str
    state: str
    severity: str
    action_label: str
    action_enabled: bool
    test_id: str


@dataclass(frozen=True)
class LiveGuiStatusFooterModel:
    """Passive footer packet consumed by future desktop shell chrome."""

    status_footer_version: str
    status_footer_id: str
    session_label: str
    items: tuple[LiveGuiStatusFooterItem, ...]
    safety_lines: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]


def _normalize_status_footer_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _safety_item(safety_state: str) -> LiveGuiStatusFooterItem:
    if safety_state == "mock-safe":
        label = "Mock Safe"
        value = "No hardware will be changed"
        state = "safe"
        severity = "safe"
    elif safety_state == "armed":
        label = "Armed Metadata"
        value = "Caller reports armed state; this model remains passive"
        state = "armed"
        severity = "warning"
    elif safety_state == "review-needed":
        label = "Review Needed"
        value = "Operator review required before hardware use"
        state = "review-needed"
        severity = "warning"
    else:
        label = "Blocked"
        value = "Hardware controls stay locked"
        state = "blocked"
        severity = "critical"
    return LiveGuiStatusFooterItem(
        key="safety",
        order=0,
        label=label,
        value=value,
        state=state,
        severity=severity,
        action_label="Review safety",
        action_enabled=False,
        test_id="status-footer-safety",
    )


def _midi_port_item(
    *,
    midi_port_name: str | None,
    midi_port_open: bool,
) -> LiveGuiStatusFooterItem:
    if midi_port_open and midi_port_name is not None:
        label = "MIDI Port Open"
        value = midi_port_name
        state = "open"
        severity = "warning"
    elif midi_port_name is not None:
        label = "MIDI Port Detected"
        value = midi_port_name
        state = "detected"
        severity = "info"
    else:
        label = "No MIDI Port Open"
        value = "No MIDI port selected"
        state = "closed"
        severity = "safe"
    return LiveGuiStatusFooterItem(
        key="midi-port",
        order=1,
        label=label,
        value=value,
        state=state,
        severity=severity,
        action_label="Select Port",
        action_enabled=False,
        test_id="status-footer-midi-port",
    )


def _hardware_item(
    *,
    hardware_connected: bool,
    hardware_enabled: bool,
) -> LiveGuiStatusFooterItem:
    if hardware_enabled:
        label = "Hardware On"
        value = "Hardware state supplied by caller"
        state = "on"
        severity = "warning"
    elif hardware_connected:
        label = "Hardware Detected / Off"
        value = "Detected but not armed"
        state = "detected-off"
        severity = "info"
    else:
        label = "Hardware Off"
        value = "Hardware controls locked"
        state = "off"
        severity = "safe"
    return LiveGuiStatusFooterItem(
        key="hardware",
        order=2,
        label=label,
        value=value,
        state=state,
        severity=severity,
        action_label="Connect",
        action_enabled=False,
        test_id="status-footer-hardware",
    )


def _mode_item(
    *,
    simulation_mode: bool,
    preview_active: bool,
) -> LiveGuiStatusFooterItem:
    if preview_active:
        label = "Preview / Dry Run"
        value = "Dry-run preview is active"
        state = "preview"
    elif simulation_mode:
        label = "Simulation / Mock"
        value = "Simulation mode"
        state = "simulation"
    else:
        label = "Operator Review"
        value = "Live mode requires review"
        state = "operator-review"
    return LiveGuiStatusFooterItem(
        key="mode",
        order=3,
        label=label,
        value=value,
        state=state,
        severity="info",
        action_label="Mode Settings",
        action_enabled=False,
        test_id="status-footer-mode",
    )


def _send_state_item(unsaved_send_count: int) -> LiveGuiStatusFooterItem:
    if unsaved_send_count == 0:
        label = "no unsaved sends"
        value = "Send queue clean"
        severity = "safe"
    else:
        label = f"{unsaved_send_count} unsaved sends"
        value = "Review or discard before arming hardware"
        severity = "warning"
    return LiveGuiStatusFooterItem(
        key="send-state",
        order=4,
        label=label,
        value=value,
        state="clean" if unsaved_send_count == 0 else "dirty",
        severity=severity,
        action_label="Review Sends",
        action_enabled=False,
        test_id="status-footer-send-state",
    )


def _version_item(app_version: str) -> LiveGuiStatusFooterItem:
    return LiveGuiStatusFooterItem(
        key="version",
        order=5,
        label="Version",
        value=app_version,
        state="info",
        severity="info",
        action_label="About",
        action_enabled=False,
        test_id="status-footer-version",
    )


def _status_footer_id(
    *,
    session_label: str,
    safety_state: str,
    midi_port_name: str | None,
    midi_port_open: bool,
    hardware_connected: bool,
    hardware_enabled: bool,
    simulation_mode: bool,
    preview_active: bool,
    unsaved_send_count: int,
    app_version: str,
) -> str:
    payload = "|".join(
        (
            STATUS_FOOTER_MODEL_VERSION,
            session_label,
            safety_state,
            midi_port_name or "",
            str(midi_port_open),
            str(hardware_connected),
            str(hardware_enabled),
            str(simulation_mode),
            str(preview_active),
            str(unsaved_send_count),
            app_version,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _status_footer_replay_command(session_label: str) -> str:
    return (
        "python -m rytm_randomizer.cli live-gui-status-footer-model-report "
        f"--session-label {powershell_literal_arg(session_label)}"
    )


def build_live_gui_status_footer_model(
    *,
    session_label: str = "Live Session",
    safety_state: str = "mock-safe",
    midi_port_name: str | None = None,
    midi_port_open: bool = False,
    hardware_connected: bool = False,
    hardware_enabled: bool = False,
    simulation_mode: bool = True,
    preview_active: bool = False,
    unsaved_send_count: int = 0,
    app_version: str = DEFAULT_APP_VERSION,
) -> LiveGuiStatusFooterModel:
    """Build a deterministic, passive footer packet for the future GUI."""

    normalized_session_label = _normalize_status_footer_nonblank(
        session_label,
        field="session_label",
    )
    normalized_app_version = _normalize_status_footer_nonblank(
        app_version,
        field="app_version",
    )
    normalized_midi_port_name = (
        _normalize_status_footer_nonblank(midi_port_name, field="midi_port_name")
        if midi_port_name is not None
        else None
    )
    if safety_state not in _VALID_SAFETY_STATES:
        raise ValueError(f"unsupported safety_state: {safety_state}")
    if unsaved_send_count < 0:
        raise ValueError("unsaved_send_count must be >= 0")

    items = (
        _safety_item(safety_state),
        _midi_port_item(
            midi_port_name=normalized_midi_port_name,
            midi_port_open=midi_port_open,
        ),
        _hardware_item(
            hardware_connected=hardware_connected,
            hardware_enabled=hardware_enabled,
        ),
        _mode_item(
            simulation_mode=simulation_mode,
            preview_active=preview_active,
        ),
        _send_state_item(unsaved_send_count),
        _version_item(normalized_app_version),
    )
    return LiveGuiStatusFooterModel(
        status_footer_version=STATUS_FOOTER_MODEL_VERSION,
        status_footer_id=_status_footer_id(
            session_label=normalized_session_label,
            safety_state=safety_state,
            midi_port_name=normalized_midi_port_name,
            midi_port_open=midi_port_open,
            hardware_connected=hardware_connected,
            hardware_enabled=hardware_enabled,
            simulation_mode=simulation_mode,
            preview_active=preview_active,
            unsaved_send_count=unsaved_send_count,
            app_version=normalized_app_version,
        ),
        session_label=normalized_session_label,
        items=items,
        safety_lines=SAFETY_LINES,
        blocked_actions=BLOCKED_ACTIONS,
        replay_commands=(_status_footer_replay_command(normalized_session_label),),
    )


def format_live_gui_status_footer_model(report: LiveGuiStatusFooterModel) -> list[str]:
    """Render the passive footer packet as deterministic operator text."""

    body_lines = [
        "Status/footer summary:",
        f"- status footer id: {report.status_footer_id}",
        f"- session: {report.session_label}",
        f"- item count: {len(report.items)}",
        "Footer items:",
    ]
    for item in report.items:
        body_lines.append(
            f"- [{item.order}] {item.key}: {item.label} "
            f"({item.state}, {item.severity}) - {item.value}"
        )
    body_lines.append("Blocked active actions:")
    body_lines.extend(f"- {action}" for action in report.blocked_actions)
    body_lines.append("Replay commands:")
    body_lines.extend(f"- {command}" for command in report.replay_commands)
    body_lines.append(SAFETY_SECTION_HEADER)
    body_lines.extend(f"- {line}" for line in report.safety_lines)
    return passive_report_lines(_HEADER, body_lines)


def to_live_gui_status_footer_model_json(
    report: LiveGuiStatusFooterModel,
) -> dict[str, object]:
    """Return a deterministic JSON-ready payload for the future GUI."""

    return {
        "live_gui_status_footer_model": {
            "status_footer_version": report.status_footer_version,
            "status_footer_id": report.status_footer_id,
            "session_label": report.session_label,
            "items": [asdict(item) for item in report.items],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


__all__ = [
    "BLOCKED_ACTIONS",
    "DEFAULT_APP_VERSION",
    "LiveGuiStatusFooterItem",
    "LiveGuiStatusFooterModel",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STATUS_FOOTER_MODEL_VERSION",
    "build_live_gui_status_footer_model",
    "format_live_gui_status_footer_model",
    "to_live_gui_status_footer_model_json",
]
