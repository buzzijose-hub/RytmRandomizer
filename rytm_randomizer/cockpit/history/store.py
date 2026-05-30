"""In-memory ``HistoryStore`` — the write-side state machine for cockpit history.

The store keeps the chronological chain of :class:`HistoryEntry` plus a
``current_id`` pointer in step with the operator's UNDO / LOAD / SAVE
actions. The contract is exactly the one the spec describes (§"History")
and matches what WS-E will broadcast as ``history_updated`` events.

Design notes
------------

* The store owns two views of the same data — a ``dict`` keyed by
  ``snapshot_id`` for O(1) lookup (used by :meth:`load`) and a ``list``
  for chronological order (used to materialize the immutable
  :class:`History` snapshot returned from every mutating method). Both
  are private; readers only ever see the frozen :class:`History`.

* Mutations construct a fresh :class:`History` from the lists, so the
  values handed out are safe to share across threads / WebSocket frames.

* In-memory only for Phase 1 — state is lost on process restart. The
  spec explicitly leaves persistence as a follow-up.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"History" for the data shape and the operator-facing semantics this
state machine implements.
"""

from __future__ import annotations

from rytm_randomizer.observability.errors import StateError
from rytm_randomizer.observability.logging import get_logger

from ..data import History, HistoryEntry, Snapshot, Via

_logger = get_logger(__name__)
"""Module logger for the cockpit in-memory history store. Bound here so
future structured log calls (snapshot-chain mutation breadcrumbs:
append / undo / load / promote-to-saved) can land in the package's
structured stream without touching this file's imports. See
``OBSERVABILITY_REVIEW.md`` Phase 5."""


class HistoryStore:
    """Append-only chain of snapshots with UNDO / LOAD / promote-to-saved.

    The store starts empty. Call :meth:`initial` once with the first
    captured snapshot, then :meth:`append_post_send` after every
    SEND/REGEN/LOAD/IMPORT to grow the chain. :meth:`undo` walks the
    pointer one step back along the ``parent_id`` chain; :meth:`load`
    jumps to any past entry by id; :meth:`promote_current_to_saved`
    promotes the current entry from ``"auto"`` to ``"saved"`` (with
    an optional label).
    """

    def __init__(self) -> None:
        """Empty history. ``current_id`` is the empty string until :meth:`initial`."""

        self._entries: list[HistoryEntry] = []
        self._by_id: dict[str, HistoryEntry] = {}
        self._current_id: str = ""

    # ------------------------------------------------------------------
    # Read-only views
    # ------------------------------------------------------------------

    @property
    def current(self) -> History:
        """Return an immutable :class:`History` view of the store's state."""

        return History(entries=tuple(self._entries), current_id=self._current_id)

    @property
    def has_entries(self) -> bool:
        """``True`` once :meth:`initial` (or any subsequent append) has been called."""

        return bool(self._entries)

    @property
    def can_undo(self) -> bool:
        """``True`` when the current entry has a parent the pointer can walk to.

        Walking is permitted only if the parent is itself still present in
        the store (it always is in normal operation — the store never drops
        entries — but the check keeps the property honest if that ever
        changes).
        """

        return self._resolve_parent_for_undo() is not None

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def initial(self, snapshot: Snapshot) -> History:
        """Bootstrap with the first captured snapshot.

        Records the snapshot as ``kind="auto"`` with ``parent_id=None``
        and ``via=None`` (it didn't come from any operator action), and
        sets ``current_id`` to its snapshot id. Must be called before any
        other mutator. Raises :class:`RuntimeError` if called twice.
        """

        if self._entries:
            raise StateError("initial() may only be called once on an empty HistoryStore")
        entry = HistoryEntry(
            snapshot=snapshot,
            kind="auto",
            parent_id=None,
            via=None,
            label=None,
        )
        self._add(entry)
        self._current_id = snapshot.snapshot_id
        return self.current

    def append_post_send(self, snapshot: Snapshot, via: Via) -> History:
        """Append a new ``kind="auto"`` entry after a SEND/REGEN/LOAD/IMPORT.

        The new entry's ``parent_id`` is the current ``current_id`` and
        the pointer advances to the new snapshot. Requires the store to
        have been bootstrapped via :meth:`initial`; raises
        :class:`RuntimeError` otherwise. Raises :class:`ValueError` if a
        snapshot with the same id is already present (snapshot ids are
        ULIDs and collisions are a programmer error).
        """

        if not self._entries:
            raise StateError("append_post_send() requires initial() to have been called first")
        if snapshot.snapshot_id in self._by_id:
            raise ValueError(f"snapshot_id {snapshot.snapshot_id!r} already present in history")
        entry = HistoryEntry(
            snapshot=snapshot,
            kind="auto",
            parent_id=self._current_id,
            via=via,
            label=None,
        )
        self._add(entry)
        self._current_id = snapshot.snapshot_id
        return self.current

    def undo(self) -> History:
        """Walk ``current_id`` one step back along the ``parent_id`` chain.

        Raises :class:`ValueError` if the current entry has no parent
        (the operator is already at the chain root or the store is
        empty).
        """

        parent_id = self._resolve_parent_for_undo()
        if parent_id is None:
            raise ValueError("no parent to undo to (already at the start of history)")
        self._current_id = parent_id
        return self.current

    def load(self, snapshot_id: str) -> History:
        """Set ``current_id`` to any snapshot already present in history.

        Raises :class:`KeyError` if the id is not present.
        """

        if snapshot_id not in self._by_id:
            raise KeyError(f"snapshot_id {snapshot_id!r} not present in history")
        self._current_id = snapshot_id
        return self.current

    def promote_current_to_saved(self, label: str | None) -> History:
        """Promote the current entry from ``"auto"`` to ``"saved"`` with ``label``.

        Idempotent — re-promoting an already-saved entry simply updates
        the label (or keeps it ``None``). Raises :class:`RuntimeError`
        if the store has no current entry.
        """

        if not self._current_id:
            raise StateError("promote_current_to_saved() requires a current entry")
        current = self._by_id[self._current_id]
        promoted = HistoryEntry(
            snapshot=current.snapshot,
            kind="saved",
            parent_id=current.parent_id,
            via=current.via,
            label=label,
        )
        self._replace(current, promoted)
        return self.current

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_parent_for_undo(self) -> str | None:
        """Return the current entry's ``parent_id`` if undo can walk to it.

        Returns ``None`` when the store is empty OR the current entry is
        the chain root (``parent_id is None``). Centralizing the check
        keeps :meth:`undo` and :attr:`can_undo` in lockstep — both call
        this helper and react to the same answer.

        The store never removes entries, so once ``_current_id`` names a
        present entry, the id is guaranteed to be in ``_by_id`` — no
        defensive ``get`` / re-lookup is needed.
        """

        if not self._current_id:
            return None
        return self._by_id[self._current_id].parent_id

    def _add(self, entry: HistoryEntry) -> None:
        """Append ``entry`` to both the ordered list and the id index."""

        self._entries.append(entry)
        self._by_id[entry.snapshot.snapshot_id] = entry

    def _replace(self, old: HistoryEntry, new: HistoryEntry) -> None:
        """Replace ``old`` with ``new`` in both views, preserving order.

        Used by :meth:`promote_current_to_saved` to swap an auto entry
        for its saved counterpart in place.
        """

        idx = self._entries.index(old)
        self._entries[idx] = new
        self._by_id[new.snapshot.snapshot_id] = new


__all__ = ["HistoryStore"]
