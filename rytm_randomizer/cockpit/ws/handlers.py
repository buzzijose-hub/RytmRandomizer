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
exception and replies with a *categorical* error envelope:
``{ok: False, code: "<ERR_*>", message: "<safe-text>"}``. Handlers
do **not** raise to express "the command is invalid" — they return
the same categorical shape directly via :func:`_error_ack` so the
wire-format contract is one and the same regardless of whether the
failure was a handler-detected precondition or a raised exception.
A structured :func:`logger.warning` call captures ``repr(exc)`` and
the exception type server-side only, *never* on the wire
(CODE_REVIEW.md PR 14, RR4f). ``repr(exc)`` is used (rather than
``str(exc)``) so the AST guard in
``tests/architecture/test_no_raw_exception_messages_on_wire.py`` can
stay at floor 0 for this file.

The four categorical codes (:data:`WS_ERROR_CODES`) are stable
identifiers a TypeScript / log-shipper client can branch on
deterministically. New code values must be added to the tuple AND
mirrored in any client allowlist; renaming an existing one is a
wire-format break.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"The Three Protocols" for the command list and per-command semantics.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Final, Protocol, runtime_checkable

from ...observability.errors import RytmRandomizerError
from ...observability.logging import get_logger
from ..data import CockpitSendPlan, History, MutationCandidate, Snapshot
from ..engine import mutate, prepare_send_plan
from ..export import pack_profile_model
from .protocol import (
    COMMAND_EXPORT_PROFILE_MODEL,
    COMMAND_LOAD_SNAPSHOT,
    COMMAND_PREPARE_SEND_PLAN,
    COMMAND_REGEN,
    COMMAND_SAVE,
    COMMAND_SELECT_PROFILE,
    COMMAND_SEND,
    COMMAND_SET_DEPTH,
    COMMAND_SET_PAD_LOCK,
    COMMAND_TOGGLE_PREVIEW,
    COMMAND_UNDO,
    ERR_INTERNAL,
    ERR_MISSING_ENVELOPE_KEY,
    ERR_UNKNOWN_COMMAND,
    ERR_VALIDATION,
    EVENT_HISTORY_UPDATED,
    EVENT_MUTATION_PREVIEWED,
    EVENT_PROFILE_CHANGED,
    EVENT_SEND_PLAN_CHANGED,
    EVENT_SESSION_STATUS,
    EVENT_SNAPSHOT_CHANGED,
    WS_ERROR_CODES,
)
from .session import CockpitSession

_logger = get_logger(__name__)
"""Module logger for handler diagnostics.

Used for the structured forensic record that backs every categorical
error envelope returned by :func:`handle_command` (PR 14 / RR4f). The
``extra=`` payload carries ``repr(exc)`` (which encodes type + args
without using ``str(exc)`` -- the AST guard in
``tests/architecture/test_no_raw_exception_messages_on_wire.py`` flags
``str(<exc-name>)`` regardless of whether the result reaches the wire,
so we use :func:`repr` instead) plus the exception type name so
operators can correlate a client-facing categorical ``code`` with the
underlying detail without that detail ever appearing on the wire.
"""


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


def _build_send_plan_changed(send_plan: CockpitSendPlan | None) -> dict:
    """Construct the ``send_plan_changed`` event payload (``None`` clears)."""

    return {
        "type": EVENT_SEND_PLAN_CHANGED,
        "send_plan": None if send_plan is None else send_plan.to_dict(),
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


def _clear_send_plan_if_needed(session: CockpitSession) -> list[dict]:
    """Clear a stale plan and emit one null event when a plan existed."""

    if session.current_send_plan is None:
        return []
    session.current_send_plan = None
    return [_build_send_plan_changed(None)]


# ---------------------------------------------------------------------------
# Categorical error envelope helper (CODE_REVIEW.md PR 14 / RR4f).
#
# Every wire-level error ack flows through :func:`_error_ack` so the
# four-field shape -- ``{ok: False, code, message}`` -- is built in one
# place. The ``code`` is one of :data:`WS_ERROR_CODES`; the ``message``
# is a short, *operator-safe* canonical string. The full exception
# detail (``repr(exc)``, ``type(exc).__name__``) is the caller's
# responsibility to log via :data:`_logger` BEFORE calling this helper
# -- the helper itself takes only the safe text.
# ---------------------------------------------------------------------------


def _error_ack(code: str, message: str) -> dict:
    """Build the categorical-error ack body (no ``request_id`` yet).

    Args:
        code: One of :data:`WS_ERROR_CODES`. Stable identifier the client
            branches on (e.g. ``ERR_VALIDATION``).
        message: Short, operator-safe canonical text. MUST NOT include
            ``str(exc)`` or any user-controlled path / id substring
            beyond what the spec already exposes on the wire (e.g. an
            ``unknown profile_id: 'X'`` message echoes the wire-supplied
            id back, which is fine because the client already knows it).

    Returns:
        A two-field ack body ready for :class:`HandlerResult.ack`. The
        dispatcher merges ``request_id`` in before sending.
    """

    if code not in WS_ERROR_CODES:
        # Defensive: a stray ``code`` value would silently break clients
        # branching on :data:`WS_ERROR_CODES`. We raise rather than
        # return a malformed envelope so the dispatcher's catch-all
        # surfaces it as ``ERR_INTERNAL`` (the right bucket for "this
        # is a server bug, not bad input").
        raise ValueError(f"unknown error code: {code!r}")
    return {"ok": False, "code": code, "message": message}


#: Canonical message strings for the two dispatcher-classified codes.
#: Kept as module-level constants so the new categorical-envelope tests
#: can import and assert exact equality rather than re-stating the strings.
_HANDLER_VALIDATION_MESSAGE: Final[str] = "command rejected by handler validation"
_HANDLER_INTERNAL_MESSAGE: Final[str] = "internal error processing command"


def _classify_handler_exception(exc: BaseException) -> tuple[str, str]:
    """Map a handler-raised exception to a ``(code, canonical_message)`` pair.

    * :class:`KeyError` / :class:`ValueError` → ``ERR_VALIDATION`` --
      both arise from invalid wire-supplied data (a missing dict key
      inside a handler that ``cmd[...]``-ed it, or an out-of-range value
      caught by ``int()`` / ``float()``).
    * Everything else in the catch tuple (``TypeError``,
      ``RuntimeError``, :class:`RytmRandomizerError`) → ``ERR_INTERNAL``
      because those represent bugs / state corruption rather than bad
      input. The wire message stays generic; the structured log carries
      the type + ``repr(exc)`` for correlation.

    Importantly, the *canonical* message is constant per code -- the
    caller MUST NOT pass ``str(exc)`` through to the wire (RR4f).
    """

    if isinstance(exc, (KeyError, ValueError)):
        return ERR_VALIDATION, _HANDLER_VALIDATION_MESSAGE
    return ERR_INTERNAL, _HANDLER_INTERNAL_MESSAGE


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
        return HandlerResult(ack=_error_ack(ERR_VALIDATION, f"unknown profile_id: {profile_id!r}"))
    events = _clear_send_plan_if_needed(session)
    session.active_profile = profile
    candidate = _recompute_candidate(session)
    events.append(_build_profile_changed(profile))
    if session.preview_on:
        events.append(_build_mutation_previewed(candidate))
    return HandlerResult(ack={"ok": True}, events=events)


async def _handle_set_depth(cmd: dict, session: CockpitSession) -> HandlerResult:
    depth = float(cmd["depth"])
    events = _clear_send_plan_if_needed(session)
    session.depth = depth
    candidate = _recompute_candidate(session)
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
    return HandlerResult(ack={"ok": True}, events=_clear_send_plan_if_needed(session))


async def _handle_toggle_preview(cmd: dict, session: CockpitSession) -> HandlerResult:
    on = bool(cmd["on"])
    events = _clear_send_plan_if_needed(session)
    session.preview_on = on
    # Toggling preview on recomputes a fresh candidate (so stale state isn't
    # shown); toggling off keeps the prior candidate in memory but emits a
    # null event so the ghost overlay drops.
    candidate = _recompute_candidate(session) if on else session.current_candidate
    if on:
        events.append(_build_mutation_previewed(candidate))
    else:
        events.append(_build_mutation_previewed(None))
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
            ack=_error_ack(ERR_VALIDATION, "no active profile; select one before regen")
        )
    # Bump the seed so the candidate genuinely changes (without moving depth).
    # Using a fresh 32-bit sample is simpler and indistinguishable from a
    # deterministic next-value, and matches the spec wording ("REGEN bumps
    # the seed to vary the output").
    from .session import _fresh_seed  # local import to keep module surface clean

    events = _clear_send_plan_if_needed(session)
    session.seed = _fresh_seed()
    candidate = _recompute_candidate(session)
    if session.preview_on:
        events.append(_build_mutation_previewed(candidate))
    return HandlerResult(
        ack={"ok": True, "candidate": None if candidate is None else candidate.to_dict()},
        events=events,
    )


async def _handle_prepare_send_plan(cmd: dict, session: CockpitSession) -> HandlerResult:
    del cmd
    if session.current_candidate is None:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "no current candidate; set a profile and depth first")
        )
    plan = prepare_send_plan(
        session.device.capture_snapshot(),
        session.active_profile,
        session.current_candidate,
        frozenset(session.pad_locks),
    )
    if plan is None:
        return HandlerResult(
            ack=_error_ack(
                ERR_VALIDATION, "no active profile; select one before preparing send plan"
            )
        )
    session.current_send_plan = plan
    return HandlerResult(
        ack={"ok": True, "send_plan": plan.to_dict()},
        events=[_build_send_plan_changed(plan)],
    )


async def _handle_send(cmd: dict, session: CockpitSession) -> HandlerResult:
    del cmd
    if session.current_candidate is None:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "no current candidate; set a profile and depth first")
        )
    if session.current_send_plan is None or not session.current_send_plan.ready:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "no ready send plan; run prepare_send_plan first")
        )
    sent_plan = session.current_send_plan
    new_snapshot = session.device.apply_send_plan(sent_plan)
    session.history_store.append_post_send(new_snapshot, via="send")
    session.unsaved_sends += 1
    # Preview clears after a SEND per spec § "Operator hits SEND" step 4.
    session.current_candidate = None
    session.current_send_plan = None
    return HandlerResult(
        ack={
            "ok": True,
            "new_snapshot_id": new_snapshot.snapshot_id,
            "send_plan_id": sent_plan.plan_id,
        },
        events=[
            _build_snapshot_changed(new_snapshot),
            _build_history_updated(session.history_store.current),
            _build_mutation_previewed(None),
            _build_send_plan_changed(None),
            _build_session_status(session),
        ],
    )


async def _handle_save(cmd: dict, session: CockpitSession) -> HandlerResult:
    label = cmd.get("label")
    if label is not None:
        label = str(label)
    current = session.history_store.current
    if not current.entries:
        return HandlerResult(ack=_error_ack(ERR_VALIDATION, "no current snapshot to save"))
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
        # PR 14 / RR4f: never echo the underlying exception text back
        # over the wire -- ``HistoryStore.load`` raises
        # ``KeyError(snapshot_id)`` whose representation embeds the
        # requested id (which is fine, the client already knows it) but
        # the categorical envelope is the contract regardless. Full
        # forensic detail goes to the structured log via :func:`repr` so
        # operators can correlate ``code=validation_error`` acks with
        # the underlying ``KeyError`` without ``str(exc)`` appearing on
        # the wire side at all. ``repr(exc)`` is intentional -- it
        # carries the exception type + args without using ``str(exc)``
        # (the AST guard in
        # ``tests/architecture/test_no_raw_exception_messages_on_wire.py``
        # specifically flags ``str(<exc-name>)`` and treats the new floor
        # of 0 as an absolute ceiling).
        _logger.warning(
            "load_snapshot_unknown_id",
            extra={
                "snapshot_id": snapshot_id,
                "exception_type": type(exc).__name__,
                "exception_repr": repr(exc),
            },
        )
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, f"unknown snapshot_id: {snapshot_id!r}")
        )
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
        return HandlerResult(ack=_error_ack(ERR_VALIDATION, "nothing to undo"))
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
            ack=_error_ack(ERR_VALIDATION, f"target must be 'binary' or 'json'; got {target!r}")
        )
    profile = session.profile_registry.get(profile_id)
    if profile is None:
        return HandlerResult(ack=_error_ack(ERR_VALIDATION, f"unknown profile_id: {profile_id!r}"))
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
    COMMAND_PREPARE_SEND_PLAN: _handle_prepare_send_plan,
    COMMAND_SEND: _handle_send,
    COMMAND_SAVE: _handle_save,
    COMMAND_LOAD_SNAPSHOT: _handle_load_snapshot,
    COMMAND_UNDO: _handle_undo,
    COMMAND_EXPORT_PROFILE_MODEL: _handle_export_profile_model,
}


async def handle_command(envelope: dict, session: CockpitSession) -> dict:
    """Dispatch a command envelope; queue events on the session for post-ack drain.

    The envelope shape is ``{request_id, command: {type, ...}}``. The
    return value is the full ack dict with ``request_id`` populated.
    The dispatcher does NOT touch the wire — the caller (the server's
    command loop, see :func:`server.create_app`) sends the ack via
    :meth:`websocket.send_json` and then calls
    :func:`drain_pending_events` to push the events queued on
    :attr:`CockpitSession.pending_events`. The two-call shape honours
    the spec's "ack first, then events" contract without forcing the
    dispatcher to also know how to emit.

    Three error paths -- each maps to one of :data:`WS_ERROR_CODES`:

    * Missing ``request_id`` or ``command`` keys → ``KeyError`` from the
      raw dict access; we catch it and reply with
      ``code=ERR_MISSING_ENVELOPE_KEY``. The full ``repr(exc)`` is logged
      server-side via :data:`_logger`. (The client should never send a
      malformed envelope; this is a last-line safety net.)
    * Unknown ``command.type`` → ``code=ERR_UNKNOWN_COMMAND``, message
      echoes the offending type so the operator can fix a typo.
    * Handler raises a realistic command/runtime failure -- ``ValueError``
      maps to ``code=ERR_VALIDATION`` (operator-supplied wire value was
      invalid); ``KeyError`` (handler-level, distinct from the envelope
      ``KeyError`` above) also maps to ``ERR_VALIDATION`` (a referenced
      id wasn't found); everything else (``TypeError`` / ``RuntimeError``
      / :class:`RytmRandomizerError`) maps to ``code=ERR_INTERNAL`` and
      is the last-line safety net for genuine bugs. In every case the
      full ``repr(exc)`` and exception type are logged server-side; only
      the categorical ``code`` and a short canonical ``message`` reach
      the wire (PR 14 / RR4f).

    Args:
        envelope: The parsed JSON object the client sent over the WebSocket.
        session: The per-process state container. The dispatcher overwrites
            :attr:`CockpitSession.pending_events` with the handler's
            ``HandlerResult.events`` so the caller can drain them after
            sending the ack.

    Returns:
        A fully populated :class:`CommandAck` dict with ``request_id``
        echoed back.
    """

    request_id = envelope.get("request_id", "")
    try:
        cmd = envelope["command"]
        cmd_type = cmd["type"]
    except KeyError as exc:
        missing_key = exc.args[0] if exc.args else "<unknown>"
        # PR 14 / RR4f: the underlying exception detail (which echoes
        # the missing key) is captured server-side via :func:`repr`;
        # the wire-level ``message`` is a short canonical string that
        # names which envelope key is missing. We use ``repr(exc)``
        # (not ``str(exc)``) so the AST guard in
        # ``tests/architecture/test_no_raw_exception_messages_on_wire.py``
        # stays at floor 0 for this file.
        _logger.warning(
            "envelope_missing_key",
            extra={
                "missing_key": missing_key,
                "exception_type": type(exc).__name__,
                "exception_repr": repr(exc),
                "request_id": request_id,
            },
        )
        return {
            "request_id": request_id,
            **_error_ack(
                ERR_MISSING_ENVELOPE_KEY,
                f"envelope missing required key: {missing_key!r}",
            ),
        }
    if isinstance(cmd_type, str) and cmd_type.startswith("wizard_"):
        # Delegate the wizard-namespaced commands to the wizard surface.
        # Lazy-import keeps the wizard dispatcher table out of the import
        # graph of cockpit boot paths that never touch the wizard.
        from .wizard_handlers import WIZARD_HANDLERS

        handler = WIZARD_HANDLERS.get(cmd_type)
    else:
        handler = _HANDLERS.get(cmd_type)
    if handler is None:
        return {
            "request_id": request_id,
            **_error_ack(ERR_UNKNOWN_COMMAND, f"unknown command: {cmd_type!r}"),
        }
    try:
        result = await handler(cmd, session)
    except (KeyError, TypeError, ValueError, RuntimeError, RytmRandomizerError) as exc:
        # PR 14 / RR4f: never echo the underlying exception text back
        # over the wire -- exception messages routinely embed filesystem
        # paths, profile ids the server has rejected, or stack-traceable
        # details. Map to a categorical code and surface the full
        # forensic record via :data:`_logger` so operators can still
        # correlate. ``repr(exc)`` is used in the structured ``extra``
        # payload (rather than ``str(exc)``) so the AST guard in
        # ``tests/architecture/test_no_raw_exception_messages_on_wire.py``
        # stays at floor 0 for this file -- ``repr`` still carries the
        # exception type + args for forensic purposes.
        code, message = _classify_handler_exception(exc)
        _logger.warning(
            "handler_exception",
            extra={
                "code": code,
                "cmd_type": cmd_type,
                "exception_type": type(exc).__name__,
                "exception_repr": repr(exc),
                "request_id": request_id,
            },
        )
        return {"request_id": request_id, **_error_ack(code, message)}
    # Queue events on the session for the caller to drain AFTER it sends
    # the ack on the wire. We cannot await the emitter from here without
    # inverting the ack-first / events-second wire ordering, so the
    # dispatcher hands ownership of the queue to
    # :func:`drain_pending_events` via the real ``pending_events`` field
    # on :class:`CockpitSession`.
    session.pending_events = list(result.events)
    return {"request_id": request_id, **result.ack}


async def drain_pending_events(session: CockpitSession, emitter: EventEmitter) -> None:
    """Send every event the last handler queued on ``session``, then clear.

    Called by the server's command loop *after* the ack has been written
    to the wire. Centralises the ack-first / events-second contract in
    one place so future transports (subprocess pipe, etc.) inherit it
    via the same dispatcher.
    """

    if not session.pending_events:
        return
    for event in session.pending_events:
        await emitter.send_event(event)
    session.clear_pending_events()


__all__ = [
    "ERR_INTERNAL",
    "ERR_MISSING_ENVELOPE_KEY",
    "ERR_UNKNOWN_COMMAND",
    "ERR_VALIDATION",
    "EventEmitter",
    "HandlerResult",
    "WS_ERROR_CODES",
    "drain_pending_events",
    "emit_initial_events",
    "handle_command",
]
