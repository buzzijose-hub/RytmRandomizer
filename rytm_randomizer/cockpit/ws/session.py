"""``CockpitSession`` — per-process state the WebSocket handlers mutate.

The session bundles every long-lived collaborator the handlers need:

* the :class:`ProfileRegistry` (built-ins + user profiles on disk),
* the :class:`HistoryStore` (the snapshot chain + ``current_id``),
* the :class:`DeviceAdapter` (mock by default, real-MIDI when ``--arm``),
* plus the transient operator state (``active_profile``, ``depth``,
  ``seed``, ``pad_locks``, ``preview_on``, ``current_candidate``,
  ``unsaved_sends``).

Why a mutable dataclass and not a frozen one
--------------------------------------------

The session models a live editing session. Every command may legitimately
mutate one or two fields (set_depth → ``depth`` + ``current_candidate``;
toggle_preview → ``preview_on``; send → ``current_candidate`` + ``unsaved_sends``).
A frozen dataclass would force every handler to rebuild the whole session,
which obscures intent and pulls the snapshot chain along with every
mutation. The dataclass is intentionally mutable; the *event payloads*
sent over the wire are constructed from the immutable views the
collaborators return (``HistoryStore.current`` returns a fresh
:class:`History`; :class:`Snapshot` is frozen; etc.).

Phase 1 scope: one session per process is the only supported shape. The
WebSocket endpoint binds to this one shared session — multi-tenant
sessions land in a later spec (the protocol itself is already
session-id-free, so adding one would not break the wire format).

See the spec §"The Three Protocols" for what each field models and how
the handlers consume them.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Final

from ..data import MutationCandidate, ProfileModel
from ..device import DeviceAdapter
from ..history import HistoryStore
from ..profiles import ProfileRegistry

DEFAULT_DEPTH: Final[float] = 0.45
"""Default depth value matching the v10 UX mockup (slider mid-position, 45%)."""

_SEED_BITS: Final[int] = 32
"""xorshift32 (the engine PRNG) consumes a 32-bit seed; sample exactly that width."""


def _fresh_seed() -> int:
    """Return a fresh 32-bit unsigned seed sampled from :func:`secrets.randbits`."""

    return secrets.randbits(_SEED_BITS)


@dataclass
class CockpitSession:
    """Mutable per-process state the WebSocket handlers wire through.

    The three collaborator fields (``profile_registry``, ``history_store``,
    ``device``) have no defaults — they are required at construction time
    and the session never substitutes them. The remaining six fields
    model the operator's live editing state and default to a fresh
    session shape (no profile selected, default depth, fresh random seed,
    no locks, preview off, no candidate, zero unsaved sends).
    """

    profile_registry: ProfileRegistry
    history_store: HistoryStore
    device: DeviceAdapter
    active_profile: ProfileModel | None = None
    depth: float = DEFAULT_DEPTH
    seed: int = field(default_factory=_fresh_seed)
    pad_locks: set[int] = field(default_factory=set)
    preview_on: bool = False
    current_candidate: MutationCandidate | None = None
    unsaved_sends: int = 0


__all__ = ["DEFAULT_DEPTH", "CockpitSession"]
