"""Cockpit history subpackage — in-memory ``HistoryStore``.

The store wraps the pure-data :class:`History` / :class:`HistoryEntry`
dataclasses from :mod:`rytm_randomizer.cockpit.data` with the write-side
state machine the cockpit needs: bootstrap an initial snapshot, append
after a SEND/REGEN/LOAD/IMPORT, walk back one step via UNDO, jump to any
past entry via LOAD, and promote the current entry to ``"saved"``.

Phase 1 is in-memory only — state is lost on process restart; on-disk
persistence is a deliberate follow-up (see the WS-D plan note). The
public surface re-exports :class:`HistoryStore` so callers can ``from
rytm_randomizer.cockpit.history import HistoryStore`` without reaching
into the submodule.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"History" for the authoritative data shape and the operator semantics
of UNDO / LOAD / SAVE this store implements.
"""

from __future__ import annotations

from .store import HistoryStore

__all__ = ["HistoryStore"]
