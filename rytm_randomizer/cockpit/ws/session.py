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

from ..data import CockpitSendPlan, MutationCandidate, ProfileModel
from ..device import DeviceAdapter
from ..history import HistoryStore
from ..profiles import ProfileRegistry
from .wizard_session import WizardSession

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
    current_send_plan: CockpitSendPlan | None = None
    unsaved_sends: int = 0
    active_wizard: WizardSession | None = None
    """The in-flight :class:`WizardSession`, or ``None`` between wizard runs.

    Set by :func:`wizard_handlers._handle_wizard_start` and cleared by
    :func:`wizard_handlers._handle_wizard_save` /
    :func:`wizard_handlers._handle_wizard_cancel`. Every wizard command
    other than ``wizard_start`` / ``wizard_cancel`` requires this field
    to be non-``None`` and returns ``ok=False`` otherwise.
    """

    pending_events: list[dict] = field(default_factory=list)
    """Events the last handler queued for the dispatcher to broadcast post-ack.

    The wire contract is "ack first, then events" (see the spec § "The
    Three Protocols"). :func:`handlers.handle_command` cannot await the
    emitter before returning the ack dict, so it stashes the queued
    events here and the server's command loop calls
    :func:`handlers.drain_pending_events` immediately after writing the
    ack to the wire. The field is mutated between request/response — this
    is intentional and matches the Phase-1 single-tenant scope documented
    in the module docstring above ("one session per process is the only
    supported shape"). When multi-tenant lands, the per-session
    ``pending_events`` will move into the per-connection scope so two
    connections cannot clobber each other's queues.
    """

    def clear_pending_events(self) -> None:
        """Empty the post-ack event queue.

        Called by :func:`handlers.drain_pending_events` once every queued
        event has been pushed through the emitter. Keeping the reset as a
        method (instead of an inline ``session.pending_events = []``)
        documents the mutation at the call-site and gives any future
        multi-tenant rework a single point to override.
        """

        self.pending_events = []


__all__ = ["DEFAULT_DEPTH", "CockpitSession"]
