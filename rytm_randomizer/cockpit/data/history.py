"""``HistoryEntry`` and ``History`` frozen dataclasses.

The cockpit's history strip is a linear, chronological chain of snapshots
with metadata about how each came into being. UNDO walks left one step;
LOAD jumps to any past entry; SAVE promotes an ``auto`` entry to ``saved``
with a label.

This module is pure data — the write-side state machine (append-after-send,
undo, promote, load) lives in WS-D's ``HistoryStore``. Keeping the
state-machine logic out of the dataclass lets the same shape serve the
in-memory store, the WebSocket payload, and any future on-disk persistence.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"History" for the authoritative shape.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self, TypedDict

from .snapshot import Snapshot, SnapshotDict
from .types import (
    HISTORY_KIND_VALUES,
    VIA_VALUES,
    HistoryKind,
    Via,
    narrow_history_kind,
    narrow_via,
)


class HistoryEntryDict(TypedDict):
    """Wire shape of :class:`HistoryEntry` (M1/P2 — replaces ``Mapping[str, object]``).

    ``snapshot`` is a nested :class:`SnapshotDict`; the optional fields
    accept ``None`` because the root entry of a fresh session has no
    parent and no "via" cause. The literal-valued ``kind`` / ``via``
    keys are NOT typed as their ``Literal`` aliases because the wire
    layer may receive any string — runtime narrowing in
    :meth:`HistoryEntry.from_dict` is the validation boundary.
    """

    snapshot: SnapshotDict
    kind: str
    parent_id: str | None
    via: str | None
    label: str | None


class HistoryDict(TypedDict):
    """Wire shape of :class:`History` (M1/P2)."""

    entries: list[HistoryEntryDict]
    current_id: str


@dataclass(frozen=True)
class HistoryEntry:
    """One entry in the cockpit history strip.

    ``kind`` is the entry's promotion status (``"auto"`` for a post-SEND
    snapshot, ``"saved"`` for one promoted to the device's persistent
    kit memory). ``parent_id`` and ``via`` are ``None`` only for the
    root entry of a fresh session.
    """

    snapshot: Snapshot
    kind: HistoryKind
    parent_id: str | None
    via: Via | None
    label: str | None

    def __post_init__(self) -> None:
        if self.kind not in HISTORY_KIND_VALUES:
            raise ValueError(f"kind must be one of {HISTORY_KIND_VALUES}; got {self.kind!r}")
        if self.via is not None and self.via not in VIA_VALUES:
            raise ValueError(f"via must be None or one of {VIA_VALUES}; got {self.via!r}")

    def to_dict(self) -> dict[str, object]:
        return {
            "snapshot": self.snapshot.to_dict(),
            "kind": self.kind,
            "parent_id": self.parent_id,
            "via": self.via,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        snap_obj = data["snapshot"]
        if not isinstance(snap_obj, Mapping):
            raise TypeError(f"snapshot must be a Mapping; got {type(snap_obj).__name__}")
        parent_obj = data["parent_id"]
        via_obj = data["via"]
        label_obj = data["label"]
        return cls(
            snapshot=Snapshot.from_dict(snap_obj),
            kind=narrow_history_kind(str(data["kind"])),
            parent_id=None if parent_obj is None else str(parent_obj),
            via=None if via_obj is None else narrow_via(str(via_obj)),
            label=None if label_obj is None else str(label_obj),
        )


@dataclass(frozen=True)
class History:
    """The linear, chronological chain of ``HistoryEntry`` plus a current pointer.

    ``current_id`` names the snapshot id of the "now" entry. UNDO walks
    one step backwards along the chain; LOAD sets ``current_id`` to any
    chosen entry's snapshot id. An empty session has zero entries and an
    empty ``current_id``.
    """

    entries: tuple[HistoryEntry, ...]
    current_id: str

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for entry in self.entries:
            sid = entry.snapshot.snapshot_id
            if sid in seen:
                raise ValueError(f"duplicate snapshot_id {sid!r} in entries")
            seen.add(sid)
        if not self.entries:
            if self.current_id != "":
                raise ValueError(
                    "current_id must be empty when entries is empty; " f"got {self.current_id!r}"
                )
        elif self.current_id not in seen:
            raise ValueError(f"current_id {self.current_id!r} must name an entry's snapshot_id")

    def to_dict(self) -> dict[str, object]:
        return {
            "entries": [e.to_dict() for e in self.entries],
            "current_id": self.current_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        entries_obj = data["entries"]
        if not isinstance(entries_obj, (list, tuple)):
            raise TypeError(f"entries must be a list/tuple; got {type(entries_obj).__name__}")
        return cls(
            entries=tuple(HistoryEntry.from_dict(e) for e in entries_obj),
            current_id=str(data["current_id"]),
        )


__all__ = ["History", "HistoryDict", "HistoryEntry", "HistoryEntryDict"]
