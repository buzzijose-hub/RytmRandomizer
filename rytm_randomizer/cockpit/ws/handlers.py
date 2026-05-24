"""Command handlers — one async function per spec command (10 total).

This module is the *engine-facing* side of the cockpit WebSocket transport.
Each handler:

1. Takes the parsed command body and the :class:`CockpitSession`.
2. Calls into :mod:`rytm_randomizer.cockpit.engine`,
   :mod:`rytm_randomizer.cockpit.history`,
   :mod:`rytm_randomizer.cockpit.device`,
   :mod:`rytm_randomizer.cockpit.profiles`, or
   :mod:`rytm_randomizer.cockpit.export` as appropriate.
3. Returns a :class:`HandlerResult` carrying the per-command
   :class:`CommandAck` payload (without ``request_id`` — the dispatcher
   fills that in) plus the *list of events* the dispatcher should
   broadcast to the client **after** the ack.

The dispatcher sends the ack FIRST, then the events. This matches the
spec's "the UI gets a response, then the corresponding ``*_changed``
event arrives if state changed" wire-ordering contract — a client
correlating its request to an ack always sees the ack before any state
update fires.

Why a duck-typed :class:`EventEmitter` shows up here at all
-----------------------------------------------------------

The connect-time bootstrap path (:func:`emit_initial_events`) emits
events outside any command/ack cycle, so it still needs a streaming
emitter. The Protocol is exported so tests can substitute a recorder.

Errors and the ack
------------------

Every handler returns a :class:`HandlerResult` (no ``request_id``
yet). On any exception inside a handler, the dispatcher catches the
exception and replies with ``{ok: False, error: str(exc)}``. Handlers
do **not** raise to express "the command is invalid" — they return
``{ok: False, error: "..."}`` directly so the error message stays
human-readable. The exception path is the *last-line* safety net for
bugs that shouldn't happen in normal operation.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"The Three Protocols" for the command list and per-command semantics.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from ...observability.errors import RytmRandomizerError
from ..data import History, MutationCandidate, Snapshot
from ..engine import mutate
from ..export import pack_profile_model
from .protocol import (
    COMMAND_EXPORT_PROFILE_MODEL,
    COMMAND_LOAD_SNAPSHOT,
    COMMAND_REGEN,
    COMMAND_SAVE,
    COMMAND_SELECT_PROFILE,
    COMMAND_SEND,
    COMMAND_SET_DEPTH,
    COMMAND_SET_PAD_LOCK,
    COMMAND_TOGGLE_PREVIEW,
    COMMAND_UNDO,
    EVENT_HISTORY_UPDATED,
    EVENT_MUTATION_PREVIEWED,
    EVENT_PROFILE_CHANGED,
    EVENT_SESSION_STATUS,
    EVENT_SNAPSHOT_CHANGED,
)
from .session import CockpitSession


@runtime_checkable
class EventEmitter(Protocol):
    """The minimum interface used for streaming events outside a command cycle.

    Production: a thin wrapper around FastAPI's :class:`WebSocket.send_json`.
    Tests: a recorder appending every emitted dict to a list.
    """

    async def send_event(self, event: dict) -> None:
        """Send one event payload (a plain dict, JSON-serialisable)."""


@dataclass
class HandlerResult:
    """A handler's output: the ack body + the post-ack events.

    ``ack`` is the partial :class:`CommandAck` (no ``request_id``); the
    dispatcher merges in the ``request_id`` before sending. ``events``
    is the list of event dicts the dispatcher will broadcast **after**
    the ack, in declaration order — matching the spec's "ack first,
    then events" wire-ordering contract.
    """

    ack: dict
    events: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers — event payload builders + collaborator-status snapshots.
# ---------------------------------------------------------------------------


def _build_session_status(session: CockpitSession) -> dict:
    """Construct the ``session_status`` event payload from the live session."""

    return {
        "type": EVENT_SESSION_STATUS,
        "armed": session.device.is_armed,
        "midi_port": _midi_port(session),
        "mode": "live" if session.device.is_armed else "mock",
        "unsaved_sends": session.unsaved_sends,
    }


def _midi_port(session: CockpitSession) -> str | None:
    """Return the device adapter's MIDI port name, or ``None`` if not exposed.

    The :class:`DeviceAdapter` Protocol doesn't require a ``midi_port``
    attribute — only the real-MIDI adapter has one. We probe with
    :func:`getattr` so the mock adapter (no port) and the real adapter
    (port name string) both work without an ``isinstance`` ladder.
    """

    port = getattr(session.device, "midi_port", None)
    if port is None:
        return None
    return str(port)


def _build_snapshot_changed(snapshot: Snapshot) -> dict:
    """Construct the ``snapshot_changed`` event payload."""

    return {"type": EVENT_SNAPSHOT_CHANGED, "snapshot": snapshot.to_dict()}


def _build_mutation_previewed(candidate: MutationCandidate | None) -> dict:
    """Construct the ``mutation_previewed`` event payload (``None`` clears)."""

    return {
        "type": EVENT_MUTATION_PREVIEWED,
        "candidate": None if candidate is None else candidate.to_dict(),
    }


def _build_history_updated(history: History) -> dict:
    """Construct the ``history_updated`` event payload."""

    return {"type": EVENT_HISTORY_UPDATED, "history": history.to_dict()}


def _build_profile_changed(profile: Any) -> dict:
    """Construct the ``profile_changed`` event payload (``None`` = no active)."""

    return {
        "type": EVENT_PROFILE_CHANGED,
        "profile": None if profile is None else profile.to_dict(),
    }


async def emit_initial_events(emitter: EventEmitter, session: CockpitSession) -> None:
    """Send the 4 bootstrap events a freshly-connected client expects.

    Order matters for the UI: a client renders the session status pill
    first (so the user sees "armed" or "mock"), then the snapshot (so
    pads render), then the active profile (so the profile chip
    highlights), then the history strip. The cockpit web frontend
    handles them in any order, but this order keeps debug logs readable
    when stepping through a fresh connect.
    """

    await emitter.send_event(_build_session_status(session))
    await emitter.send_event(_build_snapshot_changed(session.device.capture_snapshot()))
    await emitter.send_event(_build_profile_changed(session.active_profile))
    await emitter.send_event(_build_history_updated(session.history_store.current))


# ---------------------------------------------------------------------------
# Internal candidate-recompute helper.
#
# Several commands (set_depth, set_pad_lock, toggle_preview, regen, select_profile)
# need to recompute the current candidate. Centralising the logic keeps the
# dependence-on-profile guard in one place.
# ---------------------------------------------------------------------------


def _recompute_candidate(session: CockpitSession) -> MutationCandidate | None:
    """Recompute and store the current candidate, or ``None`` if not ready.

    The engine needs an active profile + a captured snapshot to mutate.
    With no active profile, we clear ``current_candidate`` to ``None`` and
    return ``None`` — the UI then sees an empty ghost overlay even with
    the preview toggle on.
    """

    if session.active_profile is None:
        session.current_candidate = None
        return None
    snapshot = session.device.capture_snapshot()
    candidate = mutate(snapshot, session.active_profile, session.depth, session.seed)
    session.current_candidate = candidate
    return candidate


# ---------------------------------------------------------------------------
# Per-command handlers.
#
# Each takes (cmd_body, session), returns a :class:`HandlerResult` carrying
# the partial ack and the list of events to broadcast (in declaration order)
# after the ack. The dispatcher fills in ``request_id`` and sends ack-first.
# ---------------------------------------------------------------------------


async def _handle_select_profile(cmd: dict, session: CockpitSession) -> HandlerResult:
    profile_id = str(cmd["profile_id"])
    profile = session.profile_registry.get(profile_id)
    if profile is None:
        return HandlerResult(ack={"ok": False, "error": f"unknown profile_id: {profile_id!r}"})
    session.active_profile = profile
    candidate = _recompute_candidate(session)
    events: list[dict] = [_build_profile_changed(profile)]
    if session.preview_on:
        events.append(_build_mutation_previewed(candidate))
    return HandlerResult(ack={"ok": True}, events=events)


async def _handle_set_depth(cmd: dict, session: CockpitSession) -> HandlerResult:
    depth = float(cmd["depth"])
    session.depth = depth
    candidate = _recompute_candidate(session)
    events: list[dict] = []
    if session.preview_on:
        events.append(_build_mutation_previewed(candidate))
    return HandlerResult(
        ack={"ok": True, "candidate": None if candidate is None else candidate.to_dict()},
        events=events,
    )


async def _handle_set_pad_lock(cmd: dict, session: CockpitSession) -> HandlerResult:
    pad_id = int(cmd["pad_id"])
    locked = bool(cmd["locked"])
    if locked:
        session.pad_locks.add(pad_id)
    else:
        session.pad_locks.discard(pad_id)
    return HandlerResult(ack={"ok": True})


async def _handle_toggle_preview(cmd: dict, session: CockpitSession) -> HandlerResult:
    on = bool(cmd["on"])
    session.preview_on = on
    # Toggling preview on recomputes a fresh candidate (so stale state isn't
    # shown); toggling off keeps the prior candidate in memory but emits a
    # null event so the ghost overlay drops.
    candidate = _recompute_candidate(session) if on else session.current_candidate
    if on:
        events = [_build_mutation_previewed(candidate)]
    else:
        events = [_build_mutation_previewed(None)]
    return HandlerResult(
        ack={
            "ok": True,
            "candidate": None if candidate is None or not on else candidate.to_dict(),
        },
        events=events,
    )


async def _handle_regen(cmd: dict, session: CockpitSession) -> HandlerResult:
    del cmd  # regen has no body fields
    if session.active_profile is None:
        return HandlerResult(
            ack={"ok": False, "error": "no active profile; select one before regen"}
        )
    # Bump the seed so the candidate genuinely changes (without moving depth).
    # Using a fresh 32-bit sample is simpler and indistinguishable from a
    # deterministic next-value, and matches the spec wording ("REGEN bumps
    # the seed to vary the output").
    from .session import _fresh_seed  # local import to keep module surface clean

    session.seed = _fresh_seed()
    candidate = _recompute_candidate(session)
    events: list[dict] = []
    if session.preview_on:
        events.append(_build_mutation_previewed(candidate))
    return HandlerResult(
        ack={"ok": True, "candidate": None if candidate is None else candidate.to_dict()},
        events=events,
    )


async def _handle_send(cmd: dict, session: CockpitSession) -> HandlerResult:
    del cmd
    if session.current_candidate is None:
        return HandlerResult(
            ack={"ok": False, "error": "no current candidate; set a profile and depth first"}
        )
    new_snapshot = session.device.apply(session.current_candidate, frozenset(session.pad_locks))
    session.history_store.append_post_send(new_snapshot, via="send")
    session.unsaved_sends += 1
    # Preview clears after a SEND per spec § "Operator hits SEND" step 4.
    session.current_candidate = None
    return HandlerResult(
        ack={"ok": True, "new_snapshot_id": new_snapshot.snapshot_id},
        events=[
            _build_snapshot_changed(new_snapshot),
            _build_history_updated(session.history_store.current),
            _build_mutation_previewed(None),
            _build_session_status(session),
        ],
    )


async def _handle_save(cmd: dict, session: CockpitSession) -> HandlerResult:
    label = cmd.get("label")
    if label is not None:
        label = str(label)
    current = session.history_store.current
    if not current.entries:
        return HandlerResult(ack={"ok": False, "error": "no current snapshot to save"})
    snapshot = next(
        entry.snapshot
        for entry in current.entries
        if entry.snapshot.snapshot_id == current.current_id
    )
    session.device.commit_kit(snapshot, label)
    session.history_store.promote_current_to_saved(label)
    session.unsaved_sends = 0
    return HandlerResult(
        ack={"ok": True, "snapshot_id": current.current_id},
        events=[
            _build_history_updated(session.history_store.current),
            _build_session_status(session),
        ],
    )


async def _handle_load_snapshot(cmd: dict, session: CockpitSession) -> HandlerResult:
    snapshot_id = str(cmd["snapshot_id"])
    try:
        history = session.history_store.load(snapshot_id)
    except KeyError as exc:
        return HandlerResult(ack={"ok": False, "error": str(exc)})
    loaded_entry = next(
        entry for entry in history.entries if entry.snapshot.snapshot_id == snapshot_id
    )
    return HandlerResult(
        ack={"ok": True, "snapshot_id": snapshot_id},
        events=[
            _build_snapshot_changed(loaded_entry.snapshot),
            _build_history_updated(history),
        ],
    )


async def _handle_undo(cmd: dict, session: CockpitSession) -> HandlerResult:
    del cmd
    if not session.history_store.can_undo:
        return HandlerResult(ack={"ok": False, "error": "nothing to undo"})
    history = session.history_store.undo()
    entry = next(e for e in history.entries if e.snapshot.snapshot_id == history.current_id)
    return HandlerResult(
        ack={"ok": True, "snapshot_id": history.current_id},
        events=[
            _build_snapshot_changed(entry.snapshot),
            _build_history_updated(history),
        ],
    )


async def _handle_export_profile_model(cmd: dict, session: CockpitSession) -> HandlerResult:
    profile_id = str(cmd["profile_id"])
    target = str(cmd["target"])
    if target not in ("binary", "json"):
        return HandlerResult(
            ack={"ok": False, "error": f"target must be 'binary' or 'json'; got {target!r}"}
        )
    profile = session.profile_registry.get(profile_id)
    if profile is None:
        return HandlerResult(ack={"ok": False, "error": f"unknown profile_id: {profile_id!r}"})
    if target == "binary":
        raw = pack_profile_model(profile)
    else:
        # ``json`` target uses the ProfileModel.to_dict() form encoded as UTF-8
        # so the same ``model_bytes_b64`` field carries either flavour and the
        # ack stays uniform on the wire.
        raw = json.dumps(profile.to_dict(), sort_keys=True).encode("utf-8")
    encoded = base64.b64encode(raw).decode("ascii")
    return HandlerResult(ack={"ok": True, "model_bytes_b64": encoded})


# ---------------------------------------------------------------------------
# Dispatcher — the single public entry point exported to server.py.
# ---------------------------------------------------------------------------

_HANDLERS: dict[
    str,
    Callable[[dict, CockpitSession], Awaitable[HandlerResult]],
] = {
    COMMAND_SELECT_PROFILE: _handle_select_profile,
    COMMAND_SET_DEPTH: _handle_set_depth,
    COMMAND_SET_PAD_LOCK: _handle_set_pad_lock,
    COMMAND_TOGGLE_PREVIEW: _handle_toggle_preview,
    COMMAND_REGEN: _handle_regen,
    COMMAND_SEND: _handle_send,
    COMMAND_SAVE: _handle_save,
    COMMAND_LOAD_SNAPSHOT: _handle_load_snapshot,
    COMMAND_UNDO: _handle_undo,
    COMMAND_EXPORT_PROFILE_MODEL: _handle_export_profile_model,
}


async def handle_command(envelope: dict, session: CockpitSession, emitter: EventEmitter) -> dict:
    """Dispatch a command envelope, send the ack-then-events wire sequence.

    The envelope shape is ``{request_id, command: {type, ...}}``. The
    return value is the full ack dict with ``request_id`` populated.
    The dispatcher sends the ack on the wire FIRST (returning it to the
    caller is what does that — the server endpoint calls
    :meth:`websocket.send_json` with the return value), then awaits the
    emitter to push every event in :attr:`HandlerResult.events`.

    Three error paths:

    * Missing ``request_id`` or ``command`` keys → ``KeyError`` from the
      raw dict access; we catch it and reply with ``ok=False`` and the
      raised message. (The client should never send a malformed envelope;
      this is a last-line safety net.)
    * Unknown ``command.type`` → ``ok=False, error="unknown command: ..."``.
    * Handler raises a realistic command/runtime failure → ``ok=False,
      error=str(exc)``.

    Args:
        envelope: The parsed JSON object the client sent over the WebSocket.
        session: The per-process state container.
        emitter: The :class:`EventEmitter` the dispatcher pushes events
            through after the ack is sent.

    Returns:
        A fully populated :class:`CommandAck` dict with ``request_id``
        echoed back.
    """

    request_id = envelope.get("request_id", "")
    try:
        cmd = envelope["command"]
        cmd_type = cmd["type"]
    except KeyError as exc:
        return {"request_id": request_id, "ok": False, "error": f"missing key: {exc.args[0]!r}"}
    handler = _HANDLERS.get(cmd_type)
    if handler is None:
        return {
            "request_id": request_id,
            "ok": False,
            "error": f"unknown command: {cmd_type!r}",
        }
    try:
        result = await handler(cmd, session)
    except (KeyError, TypeError, ValueError, RuntimeError, RytmRandomizerError) as exc:
        return {"request_id": request_id, "ok": False, "error": str(exc)}
    # Push events AFTER the ack — the ack itself is sent by the caller when
    # this coroutine returns the dict below. To honour "ack first then
    # events", we cannot await the emitter before returning. Instead, the
    # server wraps this dispatcher in a small loop that:
    #   1. Calls handle_command(...) → returns the ack dict.
    #   2. Sends the ack via send_json.
    #   3. Drains the events the handler attached to the session under a
    #      private attribute (see below) via the emitter.
    #
    # To avoid an out-of-band channel, we stash the events on the session
    # transiently and the dispatcher's caller (the server's command loop)
    # reads + clears them after sending the ack. This keeps the wire
    # ordering correct without re-shaping the public function signature.
    session._pending_events = list(result.events)  # type: ignore[attr-defined]
    return {"request_id": request_id, **result.ack}


async def drain_pending_events(session: CockpitSession, emitter: EventEmitter) -> None:
    """Send every event the last handler queued on ``session``, then clear.

    Called by the server's command loop *after* the ack has been written
    to the wire. Centralises the ack-first / events-second contract in
    one place so future transports (subprocess pipe, etc.) inherit it
    via the same dispatcher.
    """

    pending = getattr(session, "_pending_events", None)
    if not pending:
        return
    for event in pending:
        await emitter.send_event(event)
    session._pending_events = []  # type: ignore[attr-defined]


__all__ = [
    "EventEmitter",
    "HandlerResult",
    "drain_pending_events",
    "emit_initial_events",
    "handle_command",
]
