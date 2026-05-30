"""Passive live GUI snapshot-history and undo/redo model."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Final, TypedDict

from ..cockpit.data import History, HistoryEntry
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive live GUI snapshot-history model"
SOURCE_MODULE: Final[str] = "reports.live_gui_snapshot_history_model"
SNAPSHOT_HISTORY_MODEL_VERSION: Final[str] = "live-gui-snapshot-history-model-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI snapshot-history metadata only",
    "future desktop GUI only",
    "undo/redo controls are declarative metadata only",
    "history entries are caller-supplied cockpit state only",
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
    "open MIDI port from snapshot history",
    "send MIDI from snapshot history",
    "arm hardware from snapshot history",
    "mutate hardware from snapshot history",
    "launch GUI from snapshot history",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class LiveGuiSnapshotHistoryEntry:
    """One GUI-ready snapshot history row."""

    key: str
    order: int
    snapshot_id: str
    label: str
    kind: str
    via: str | None
    parent_id: str | None
    device: str
    pad_count: int
    scene_slot: str | None
    bpm_label: str
    is_current: bool
    is_saved: bool
    can_load: bool
    can_undo_to: bool
    summary: str
    test_id: str


class LiveGuiSnapshotHistoryEntryDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiSnapshotHistoryEntry`."""

    key: str
    order: int
    snapshot_id: str
    label: str
    kind: str
    via: str | None
    parent_id: str | None
    device: str
    pad_count: int
    scene_slot: str | None
    bpm_label: str
    is_current: bool
    is_saved: bool
    can_load: bool
    can_undo_to: bool
    summary: str
    test_id: str


@dataclass(frozen=True)
class LiveGuiSnapshotHistoryControl:
    """One declarative undo/load/redo control for the future GUI."""

    key: str
    order: int
    label: str
    enabled: bool
    target_snapshot_id: str | None
    reason: str
    test_id: str


class LiveGuiSnapshotHistoryControlDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiSnapshotHistoryControl`."""

    key: str
    order: int
    label: str
    enabled: bool
    target_snapshot_id: str | None
    reason: str
    test_id: str


@dataclass(frozen=True)
class LiveGuiSnapshotHistoryModel:
    """Passive snapshot-history packet consumed by future desktop UI."""

    snapshot_history_version: str
    snapshot_history_id: str
    session_label: str
    current_id: str
    current_index: int
    entry_count: int
    entries: tuple[LiveGuiSnapshotHistoryEntry, ...]
    controls: tuple[LiveGuiSnapshotHistoryControl, ...]
    safety_lines: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]


class LiveGuiSnapshotHistoryModelDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiSnapshotHistoryModel`."""

    snapshot_history_version: str
    snapshot_history_id: str
    session_label: str
    current_id: str
    current_index: int
    entry_count: int
    entries: tuple[LiveGuiSnapshotHistoryEntryDict, ...]
    controls: tuple[LiveGuiSnapshotHistoryControlDict, ...]
    safety_lines: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]


def _snapshot_history_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _snapshot_history_bpm_label(bpm: float | None) -> str:
    if bpm is None:
        return "unknown BPM"
    if bpm.is_integer():
        return f"{int(bpm)} BPM"
    return f"{bpm:g} BPM"


def _snapshot_history_entry_label(entry: HistoryEntry, *, order: int) -> str:
    if entry.label is not None and entry.label.strip():
        return entry.label.strip()
    if order == 0 and entry.parent_id is None:
        return "Initial snapshot"
    return f"{entry.kind.title()} snapshot {order + 1}"


def _snapshot_history_summary(entry: HistoryEntry) -> str:
    snapshot = entry.snapshot
    scene = snapshot.scene_slot if snapshot.scene_slot is not None else "none"
    return (
        f"{snapshot.device}: {len(snapshot.pads)} pad(s), "
        f"scene {scene}, {_snapshot_history_bpm_label(snapshot.bpm)}"
    )


def _snapshot_history_entry_model(
    entry: HistoryEntry,
    *,
    order: int,
    current_id: str,
) -> LiveGuiSnapshotHistoryEntry:
    snapshot = entry.snapshot
    is_current = snapshot.snapshot_id == current_id
    return LiveGuiSnapshotHistoryEntry(
        key=f"snapshot-{order}",
        order=order,
        snapshot_id=snapshot.snapshot_id,
        label=_snapshot_history_entry_label(entry, order=order),
        kind=entry.kind,
        via=entry.via,
        parent_id=entry.parent_id,
        device=snapshot.device,
        pad_count=len(snapshot.pads),
        scene_slot=snapshot.scene_slot,
        bpm_label=_snapshot_history_bpm_label(snapshot.bpm),
        is_current=is_current,
        is_saved=entry.kind == "saved",
        can_load=not is_current,
        can_undo_to=is_current and entry.parent_id is not None,
        summary=_snapshot_history_summary(entry),
        test_id=f"snapshot-history-entry-{order}",
    )


def _snapshot_history_current_entry(history: History) -> HistoryEntry | None:
    if not history.current_id:
        return None
    return next(
        (entry for entry in history.entries if entry.snapshot.snapshot_id == history.current_id),
        None,
    )


def _snapshot_history_current_index(history: History) -> int:
    for index, entry in enumerate(history.entries):
        if entry.snapshot.snapshot_id == history.current_id:
            return index
    return -1


def _snapshot_history_controls(
    history: History,
) -> tuple[LiveGuiSnapshotHistoryControl, ...]:
    current = _snapshot_history_current_entry(history)
    if current is None:
        undo_enabled = False
        undo_target: str | None = None
        undo_reason = "No current snapshot is available to undo from."
        load_target: str | None = None
        load_reason = "No current snapshot is available to load."
    elif current.parent_id is None:
        undo_enabled = False
        undo_target = None
        undo_reason = "Current snapshot has no parent to undo to."
        load_target = current.snapshot.snapshot_id
        load_reason = "Current snapshot is already loaded."
    else:
        undo_enabled = True
        undo_target = current.parent_id
        undo_reason = f"Undo to previous snapshot {current.parent_id}."
        load_target = current.snapshot.snapshot_id
        load_reason = "Current snapshot is already loaded."

    return (
        LiveGuiSnapshotHistoryControl(
            key="undo",
            order=0,
            label="Undo",
            enabled=undo_enabled,
            target_snapshot_id=undo_target,
            reason=undo_reason,
            test_id="snapshot-history-control-undo",
        ),
        LiveGuiSnapshotHistoryControl(
            key="redo",
            order=1,
            label="Redo",
            enabled=False,
            target_snapshot_id=None,
            reason="No redo stack is modeled by the cockpit history store yet.",
            test_id="snapshot-history-control-redo",
        ),
        LiveGuiSnapshotHistoryControl(
            key="load-current",
            order=2,
            label="Load Current",
            enabled=False,
            target_snapshot_id=load_target,
            reason=load_reason,
            test_id="snapshot-history-control-load-current",
        ),
    )


def _snapshot_history_model_id(
    *,
    history: History,
    session_label: str,
    entries: tuple[LiveGuiSnapshotHistoryEntry, ...],
) -> str:
    entry_parts = tuple(
        "|".join(
            (
                entry.snapshot_id,
                entry.kind,
                entry.parent_id or "",
                entry.via or "",
                entry.label,
                entry.device,
                str(entry.pad_count),
                entry.scene_slot or "",
                entry.bpm_label,
            )
        )
        for entry in entries
    )
    payload = "||".join(
        (
            SNAPSHOT_HISTORY_MODEL_VERSION,
            session_label,
            history.current_id,
            *entry_parts,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _snapshot_history_replay_command(session_label: str) -> str:
    return (
        "python -m rytm_randomizer.cli live-gui-snapshot-history-model-report "
        f"--session-label {powershell_literal_arg(session_label)}"
    )


def build_live_gui_snapshot_history_model(
    history: History,
    *,
    session_label: str = "Live Session",
) -> LiveGuiSnapshotHistoryModel:
    """Build a deterministic, passive snapshot-history model for the future GUI."""

    normalized_session_label = _snapshot_history_nonblank(
        session_label,
        field="session_label",
    )
    entries = tuple(
        _snapshot_history_entry_model(
            entry,
            order=order,
            current_id=history.current_id,
        )
        for order, entry in enumerate(history.entries)
    )
    return LiveGuiSnapshotHistoryModel(
        snapshot_history_version=SNAPSHOT_HISTORY_MODEL_VERSION,
        snapshot_history_id=_snapshot_history_model_id(
            history=history,
            session_label=normalized_session_label,
            entries=entries,
        ),
        session_label=normalized_session_label,
        current_id=history.current_id,
        current_index=_snapshot_history_current_index(history),
        entry_count=len(entries),
        entries=entries,
        controls=_snapshot_history_controls(history),
        safety_lines=SAFETY_LINES,
        blocked_actions=BLOCKED_ACTIONS,
        replay_commands=(_snapshot_history_replay_command(normalized_session_label),),
    )


def format_live_gui_snapshot_history_model(
    report: LiveGuiSnapshotHistoryModel,
) -> list[str]:
    """Render the passive snapshot-history packet as deterministic operator text."""

    body_lines = [
        "Snapshot history summary:",
        f"- snapshot history id: {report.snapshot_history_id}",
        f"- session: {report.session_label}",
        f"- current id: {report.current_id or 'none'}",
        f"- current index: {report.current_index}",
        f"- entry count: {report.entry_count}",
        "History entries:",
    ]
    if report.entries:
        for entry in report.entries:
            current_token = "current" if entry.is_current else "past"
            body_lines.append(
                f"- [{entry.order}] {entry.snapshot_id} {entry.kind} "
                f"{current_token}: {entry.label} - {entry.summary}"
            )
    else:
        body_lines.append("- No snapshots in history.")

    body_lines.append("Controls:")
    for control in report.controls:
        state = "enabled" if control.enabled else "disabled"
        target = control.target_snapshot_id if control.target_snapshot_id is not None else "none"
        body_lines.append(f"- {control.key}: {state}, target {target}")

    body_lines.append("Blocked active actions:")
    body_lines.extend(f"- {action}" for action in report.blocked_actions)
    body_lines.append("Replay commands:")
    body_lines.extend(f"- {command}" for command in report.replay_commands)
    body_lines.append(SAFETY_SECTION_HEADER)
    body_lines.extend(f"- {line}" for line in report.safety_lines)
    return passive_report_lines(_HEADER, body_lines)


def to_live_gui_snapshot_history_model_json(
    report: LiveGuiSnapshotHistoryModel,
) -> dict[str, object]:
    """Return a deterministic JSON-ready payload for the future GUI."""

    return {
        "live_gui_snapshot_history_model": {
            "snapshot_history_version": report.snapshot_history_version,
            "snapshot_history_id": report.snapshot_history_id,
            "session_label": report.session_label,
            "current_id": report.current_id,
            "current_index": report.current_index,
            "entry_count": report.entry_count,
            "entries": [asdict(entry) for entry in report.entries],
            "controls": [asdict(control) for control in report.controls],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


__all__ = [
    "BLOCKED_ACTIONS",
    "LiveGuiSnapshotHistoryControl",
    "LiveGuiSnapshotHistoryControlDict",
    "LiveGuiSnapshotHistoryEntry",
    "LiveGuiSnapshotHistoryEntryDict",
    "LiveGuiSnapshotHistoryModel",
    "LiveGuiSnapshotHistoryModelDict",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SNAPSHOT_HISTORY_MODEL_VERSION",
    "SOURCE_MODULE",
    "build_live_gui_snapshot_history_model",
    "format_live_gui_snapshot_history_model",
    "to_live_gui_snapshot_history_model_json",
]
