"""Passive live GUI command queue, last-action, and undo-stack model."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Final

from ..cockpit.data.history import History, HistoryEntry
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive live GUI command queue model"
SOURCE_MODULE: Final[str] = "reports.live_gui_command_queue_model"
COMMAND_QUEUE_MODEL_VERSION: Final[str] = "live-gui-command-queue-model-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI command queue metadata only",
    "future desktop GUI only",
    "queued command cards are declarative only",
    "last actions are derived from caller-supplied history only",
    "undo stack is display metadata only",
    "JSON/stdout only",
    "no GUI launch",
    "no GUI event dispatch",
    "no command execution",
    "no state-store mutation",
    "no real MIDI rendering",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "dispatch queued command from model",
    "run undo from model",
    "load snapshot from model",
    "open MIDI port from model",
    "send MIDI from model",
    "mutate hardware from model",
    "launch GUI from model",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_DEFAULT_HISTORY_LIMIT: Final[int] = 5
_DEFAULT_COMMANDS: Final[tuple[tuple[str, str, str, str, int], ...]] = (
    (
        "queued-command-snapshot-save",
        "Snapshot Save (Pre-Mutation)",
        "snapshot-save",
        "history",
        0,
    ),
    (
        "queued-command-mutate-pad-11",
        "Mutate Pad 11 (SY Raw)",
        "mutate-pad",
        "Pad 11 / SY Raw",
        8,
    ),
    (
        "queued-command-mutate-pad-1",
        "Mutate Pad 1 (BD Hard)",
        "mutate-pad",
        "Pad 1 / BD Hard",
        7,
    ),
    (
        "queued-command-parameter-lock-check",
        "Parameter Lock Check",
        "preflight-check",
        "snapshot compatibility",
        0,
    ),
)


@dataclass(frozen=True)
class LiveGuiQueuedCommand:
    """One declarative future-GUI command card."""

    key: str
    order: int
    label: str
    status: str
    enabled: bool
    action_type: str
    target: str
    dry_run_only: bool
    estimated_message_count: int
    operator_action: str
    test_id: str


@dataclass(frozen=True)
class LiveGuiLastAction:
    """One recent action row derived from cockpit history metadata."""

    key: str
    order: int
    label: str
    status: str
    action_type: str
    snapshot_id: str
    device: str
    result: str
    detail: str
    test_id: str


@dataclass(frozen=True)
class LiveGuiUndoStackEntry:
    """One passive undo-stack row for the future GUI."""

    key: str
    order: int
    label: str
    status: str
    snapshot_id: str
    is_current: bool
    is_undo_target: bool
    is_load_target: bool
    action_type: str
    test_id: str


@dataclass(frozen=True)
class LiveGuiCommandQueueModel:
    """Passive packet consumed by future command queue / action history UI."""

    command_queue_version: str
    command_queue_id: str
    session_label: str
    queue_status: str
    dry_run_active: bool
    hardware_armed: bool
    active_command_key: str | None
    queued_commands: tuple[LiveGuiQueuedCommand, ...]
    last_actions: tuple[LiveGuiLastAction, ...]
    undo_stack: tuple[LiveGuiUndoStackEntry, ...]
    safety_lines: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]


def _command_queue_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _command_queue_status(*, dry_run_active: bool) -> str:
    if dry_run_active:
        return "queued"
    return "blocked"


def _command_status(*, dry_run_active: bool) -> str:
    if dry_run_active:
        return "queued"
    return "blocked"


def _command_operator_action(*, dry_run_active: bool) -> str:
    if dry_run_active:
        return "Review this queued command; dispatch remains disabled in passive mode."
    return "Run a dry-run preview before allowing this command card."


def _queued_commands(
    *,
    dry_run_active: bool,
) -> tuple[LiveGuiQueuedCommand, ...]:
    return tuple(
        LiveGuiQueuedCommand(
            key=key,
            order=order,
            label=label,
            status=_command_status(dry_run_active=dry_run_active),
            enabled=False,
            action_type=action_type,
            target=target,
            dry_run_only=True,
            estimated_message_count=estimated_message_count,
            operator_action=_command_operator_action(dry_run_active=dry_run_active),
            test_id=key,
        )
        for order, (
            key,
            label,
            action_type,
            target,
            estimated_message_count,
        ) in enumerate(_DEFAULT_COMMANDS)
    )


def _history_current_entry(history: History) -> HistoryEntry | None:
    return next(
        entry for entry in history.entries if entry.snapshot.snapshot_id == history.current_id
    )


def _history_action_type(entry: HistoryEntry) -> str:
    if entry.via is None:
        return "root"
    return entry.via


def _history_label(entry: HistoryEntry) -> str:
    if entry.label:
        return entry.label
    action_type = _history_action_type(entry)
    if action_type == "root":
        return "Initial snapshot"
    return f"{action_type.title()} snapshot"


def _empty_last_actions() -> tuple[LiveGuiLastAction, ...]:
    return (
        LiveGuiLastAction(
            key="last-action-empty",
            order=0,
            label="No last actions",
            status="empty",
            action_type="none",
            snapshot_id="",
            device="",
            result="none",
            detail="No cockpit history was supplied.",
            test_id="last-action-empty",
        ),
    )


def _last_actions(
    history: History | None,
    *,
    history_limit: int,
) -> tuple[LiveGuiLastAction, ...]:
    if history is None or not history.entries:
        return _empty_last_actions()
    entries = tuple(reversed(history.entries))[:history_limit]
    return tuple(
        LiveGuiLastAction(
            key=f"last-action-{entry.snapshot.snapshot_id}",
            order=order,
            label=_history_label(entry),
            status="current" if entry.snapshot.snapshot_id == history.current_id else "past",
            action_type=_history_action_type(entry),
            snapshot_id=entry.snapshot.snapshot_id,
            device=entry.snapshot.device,
            result="ok",
            detail=f"{entry.kind} snapshot via {_history_action_type(entry)}",
            test_id=f"last-action-{order}",
        )
        for order, entry in enumerate(entries)
    )


def _empty_undo_stack() -> tuple[LiveGuiUndoStackEntry, ...]:
    return (
        LiveGuiUndoStackEntry(
            key="undo-stack-empty",
            order=0,
            label="No undo stack",
            status="empty",
            snapshot_id="",
            is_current=False,
            is_undo_target=False,
            is_load_target=False,
            action_type="none",
            test_id="undo-stack-empty",
        ),
    )


def _undo_stack(
    history: History | None,
    *,
    history_limit: int,
) -> tuple[LiveGuiUndoStackEntry, ...]:
    if history is None or not history.entries:
        return _empty_undo_stack()
    current_entry = _history_current_entry(history)
    undo_target_id = current_entry.parent_id if current_entry is not None else None
    entries = tuple(reversed(history.entries))[:history_limit]
    return tuple(
        LiveGuiUndoStackEntry(
            key=f"undo-stack-{entry.snapshot.snapshot_id}",
            order=order,
            label=_history_label(entry),
            status="current" if entry.snapshot.snapshot_id == history.current_id else "available",
            snapshot_id=entry.snapshot.snapshot_id,
            is_current=entry.snapshot.snapshot_id == history.current_id,
            is_undo_target=entry.snapshot.snapshot_id == undo_target_id,
            is_load_target=entry.snapshot.snapshot_id != history.current_id,
            action_type=_history_action_type(entry),
            test_id=f"undo-stack-{order}",
        )
        for order, entry in enumerate(entries)
    )


def _command_queue_id(
    *,
    session_label: str,
    queue_status: str,
    dry_run_active: bool,
    hardware_armed: bool,
    active_command_key: str | None,
    queued_commands: Sequence[LiveGuiQueuedCommand],
    last_actions: Sequence[LiveGuiLastAction],
    undo_stack: Sequence[LiveGuiUndoStackEntry],
) -> str:
    command_parts = tuple(
        "|".join((command.key, command.status, command.label)) for command in queued_commands
    )
    action_parts = tuple(
        "|".join((action.snapshot_id, action.status, action.action_type)) for action in last_actions
    )
    undo_parts = tuple(
        "|".join((entry.snapshot_id, entry.status, str(entry.is_undo_target)))
        for entry in undo_stack
    )
    payload = "||".join(
        (
            COMMAND_QUEUE_MODEL_VERSION,
            session_label,
            queue_status,
            str(dry_run_active),
            str(hardware_armed),
            active_command_key or "",
            *command_parts,
            *action_parts,
            *undo_parts,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _command_queue_replay_command(session_label: str) -> str:
    return (
        "python -m rytm_randomizer.cli live-gui-command-queue-model-report "
        f"--session-label {powershell_literal_arg(session_label)}"
    )


def build_live_gui_command_queue_model(
    *,
    session_label: str = "Live Session",
    history: History | None = None,
    dry_run_active: bool = True,
    hardware_armed: bool = False,
    active_command_key: str | None = None,
    history_limit: int = _DEFAULT_HISTORY_LIMIT,
) -> LiveGuiCommandQueueModel:
    """Build deterministic passive command queue metadata for future GUI."""

    normalized_session_label = _command_queue_nonblank(
        session_label,
        field="session_label",
    )
    normalized_active_key = (
        _command_queue_nonblank(active_command_key, field="active_command_key")
        if active_command_key is not None
        else None
    )
    if history_limit < 1:
        raise ValueError("history_limit must be >= 1")

    queued_commands = _queued_commands(dry_run_active=dry_run_active)
    command_keys = {command.key for command in queued_commands}
    if normalized_active_key is not None and normalized_active_key not in command_keys:
        raise ValueError(
            f"active_command_key must name a queued command; got {active_command_key!r}"
        )

    queue_status = _command_queue_status(dry_run_active=dry_run_active)
    last_actions = _last_actions(history, history_limit=history_limit)
    undo_stack = _undo_stack(history, history_limit=history_limit)
    return LiveGuiCommandQueueModel(
        command_queue_version=COMMAND_QUEUE_MODEL_VERSION,
        command_queue_id=_command_queue_id(
            session_label=normalized_session_label,
            queue_status=queue_status,
            dry_run_active=dry_run_active,
            hardware_armed=hardware_armed,
            active_command_key=normalized_active_key,
            queued_commands=queued_commands,
            last_actions=last_actions,
            undo_stack=undo_stack,
        ),
        session_label=normalized_session_label,
        queue_status=queue_status,
        dry_run_active=dry_run_active,
        hardware_armed=hardware_armed,
        active_command_key=normalized_active_key,
        queued_commands=queued_commands,
        last_actions=last_actions,
        undo_stack=undo_stack,
        safety_lines=SAFETY_LINES,
        blocked_actions=BLOCKED_ACTIONS,
        replay_commands=(_command_queue_replay_command(normalized_session_label),),
    )


def format_live_gui_command_queue_model(
    report: LiveGuiCommandQueueModel,
) -> list[str]:
    """Render command queue metadata as deterministic operator text."""

    body_lines = [
        "Command queue summary:",
        f"- command queue id: {report.command_queue_id}",
        f"- session: {report.session_label}",
        f"- queue status: {report.queue_status}",
        f"- dry run active: {report.dry_run_active}",
        f"- hardware armed: {report.hardware_armed}",
        "Queued commands:",
    ]
    for command in report.queued_commands:
        body_lines.append(f"- {command.key}: {command.status} - {command.label}")
    body_lines.append("Last actions:")
    for action in report.last_actions:
        body_lines.append(f"- {action.key}: {action.status} - {action.label}")
    body_lines.append("Undo stack:")
    for entry in report.undo_stack:
        body_lines.append(f"- {entry.key}: {entry.status} - {entry.label}")
    body_lines.append("Blocked active actions:")
    body_lines.extend(f"- {action}" for action in report.blocked_actions)
    body_lines.append("Replay commands:")
    body_lines.extend(f"- {command}" for command in report.replay_commands)
    body_lines.append(SAFETY_SECTION_HEADER)
    body_lines.extend(f"- {line}" for line in report.safety_lines)
    return passive_report_lines(_HEADER, body_lines)


def to_live_gui_command_queue_model_json(
    report: LiveGuiCommandQueueModel,
) -> dict[str, object]:
    """Return a deterministic JSON-ready payload for future GUI consumers."""

    return {
        "live_gui_command_queue_model": {
            "command_queue_version": report.command_queue_version,
            "command_queue_id": report.command_queue_id,
            "session_label": report.session_label,
            "queue_status": report.queue_status,
            "dry_run_active": report.dry_run_active,
            "hardware_armed": report.hardware_armed,
            "active_command_key": report.active_command_key,
            "queued_commands": [asdict(command) for command in report.queued_commands],
            "last_actions": [asdict(action) for action in report.last_actions],
            "undo_stack": [asdict(entry) for entry in report.undo_stack],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


__all__ = [
    "BLOCKED_ACTIONS",
    "COMMAND_QUEUE_MODEL_VERSION",
    "LiveGuiCommandQueueModel",
    "LiveGuiLastAction",
    "LiveGuiQueuedCommand",
    "LiveGuiUndoStackEntry",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_live_gui_command_queue_model",
    "format_live_gui_command_queue_model",
    "to_live_gui_command_queue_model_json",
]
