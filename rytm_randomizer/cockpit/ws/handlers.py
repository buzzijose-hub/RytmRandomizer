"""Command handlers — one async function per spec command.

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

import asyncio
import base64
import hashlib
import hmac
import importlib.util
import json
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Final, Protocol, SupportsFloat, SupportsInt, cast, runtime_checkable

from ...devices import get_device
from ...observability.errors import RytmRandomizerError
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...observability.tracing import operation
from ..capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    CAPTURE_DEVICE_IDS,
    cockpit_snapshot_from_rytm_capture,
    narrow_kit_capture_device_id,
)
from ..data import (
    CockpitSendPlan,
    History,
    MutationCandidate,
    ProfileModel,
    Snapshot,
    StageDeviceId,
)
from ..device.connection import ConnectionState, active_connection_manager
from ..diagnostics import build_diagnostics_payload
from ..engine import mutate, prepare_send_plan
from ..export import pack_profile_model
from ..library import LibraryStore
from ..mutation_targets import (
    A4_TRACK_TARGET_MAX,
    A4_TRACK_TARGET_MIN,
    RYTM_PAD_TARGET_MAX,
    RYTM_PAD_TARGET_MIN,
    MutationTargets,
)
from .app_version import resolve_app_version
from .protocol import (
    COMMAND_ANALYZE_PATCH_GENOME,
    COMMAND_ARM,
    COMMAND_BUILD_OPERATOR_PACKAGE_RECEIPT,
    COMMAND_CAPTURE_CURRENT_KIT,
    COMMAND_CLEAR_MUTATION_TARGETS,
    COMMAND_DIAGNOSTICS,
    COMMAND_DISARM,
    COMMAND_EXPORT_PROFILE_MODEL,
    COMMAND_LIBRARY_DELETE,
    COMMAND_LIBRARY_IMPORT_CAPTURES,
    COMMAND_LIBRARY_LIST,
    COMMAND_LIBRARY_SEARCH,
    COMMAND_LIBRARY_TAG,
    COMMAND_LIST_CAPTURE_INPUTS,
    COMMAND_LOAD_SNAPSHOT,
    COMMAND_MOCK_APPLY_OPERATOR_PACKAGE,
    COMMAND_PREPARE_SEND_PLAN,
    COMMAND_PREVIEW_OPERATOR_PACKAGE_APPLY,
    COMMAND_REGEN,
    COMMAND_REHEARSE_OPERATOR_PACKAGE_SEQUENCE,
    COMMAND_REHEARSE_OPERATOR_PACKAGE_STEP,
    COMMAND_SAVE,
    COMMAND_SELECT_PROFILE,
    COMMAND_SEND,
    COMMAND_SET_A4_TRACK_LOCK,
    COMMAND_SET_DEPTH,
    COMMAND_SET_MUTATION_TARGETS,
    COMMAND_SET_PAD_LOCK,
    COMMAND_TOGGLE_PREVIEW,
    COMMAND_UNDO,
    ERR_INTERNAL,
    ERR_MISSING_ENVELOPE_KEY,
    ERR_UNKNOWN_COMMAND,
    ERR_VALIDATION,
    EVENT_CONNECTION_CHANGED,
    EVENT_DUAL_MACHINE_STAGE_CHANGED,
    EVENT_HISTORY_UPDATED,
    EVENT_KIT_CAPTURES_CHANGED,
    EVENT_LIBRARY_CHANGED,
    EVENT_MUTATION_LOCKS_CHANGED,
    EVENT_MUTATION_PREVIEWED,
    EVENT_MUTATION_TARGETS_CHANGED,
    EVENT_PATCH_GENOME_CHANGED,
    EVENT_PERFORMANCE_CONSOLE_CHANGED,
    EVENT_PROFILE_CATALOG_CHANGED,
    EVENT_PROFILE_CHANGED,
    EVENT_SEND_PLAN_CHANGED,
    EVENT_SESSION_STATUS,
    EVENT_SNAPSHOT_CHANGED,
    WS_ERROR_CODES,
)
from .session import CockpitSession

_logger = get_logger(__name__)
"""Module logger for the cockpit WS command dispatcher.

Used for the structured forensic record that backs every categorical
error envelope returned by :func:`handle_command` (PR 14 / RR4f). The
``extra=`` payload carries ``repr(exc)`` (which encodes type + args
without using ``str(exc)`` — the AST guard in
``tests/architecture/test_no_raw_exception_messages_on_wire.py`` flags
``str(<exc-name>)`` regardless of whether the result reaches the wire,
so we use :func:`repr` instead) plus the exception type name so
operators can correlate a client-facing categorical ``code`` with the
underlying detail without that detail ever appearing on the wire.

Bound here so future structured log calls (PR O1 — request_id
correlation, PR O2 — RED metrics, PR O4 — fingerprinted error events)
land in the package's structured stream without touching this file's
imports. See ``OBSERVABILITY_REVIEW.md`` Phase 5.
"""


@runtime_checkable
class EventEmitter(Protocol):
    """The minimum interface used for streaming events outside a command cycle.

    Production: a thin wrapper around FastAPI's :class:`WebSocket.send_json`.
    Tests: a recorder appending every emitted dict to a list.
    """

    async def send_event(self, event: dict[str, object]) -> None:
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

    ack: dict[str, object]
    events: list[dict[str, object]] = field(default_factory=list[dict[str, object]])


# ---------------------------------------------------------------------------
# Helpers — event payload builders + collaborator-status snapshots.
# ---------------------------------------------------------------------------


def session_is_armed(session: CockpitSession) -> bool:
    """True when this session holds the one live outbound MIDI handle.

    The :class:`~rytm_randomizer.senders.armed_apply.ArmedApplySession`
    **is** the armed state: it owns the only real output port a cockpit
    session ever opens. ``session.device`` deliberately stays the passive
    adapter across an arm so there is exactly one output handle (a second
    adapter holding its own port was the two-handles defect), which means
    the device's own ``is_armed`` can no longer answer this question.

    ``session.device.is_armed`` is still consulted so a directly-injected
    live adapter (used by a handful of harnesses that never call ``arm``)
    keeps reporting ``live``.
    """

    return session.armed_apply is not None or session.device.is_armed


def _build_session_status(session: CockpitSession) -> dict[str, object]:
    """Construct the ``session_status`` event payload from the live session."""

    armed = session_is_armed(session)
    return {
        "type": EVENT_SESSION_STATUS,
        "armed": armed,
        "midi_port": _midi_port(session),
        "mode": "live" if armed else "mock",
        "connection_phase": _connection_phase(session),
        "unsaved_sends": session.unsaved_sends,
        "capture_enabled": session.kit_capture_service.enabled,
        # Contract I1 (auto-update): read-only server -> client SemVer the
        # cockpit reports for the *sidecar* half of a running install. It
        # rides the existing handshake frame; nothing subscribes to it yet
        # and nothing about it can transmit.
        "app_version": resolve_app_version(),
    }


def resolve_connection_phase(session: CockpitSession) -> str:
    """Resolve the connection phase for ``session_status`` (and /health).

    An armed device adapter is authoritative: the ConnectionManager never
    produces the ``armed`` phase itself (arming is an explicit in-UI
    operator decision, not an enumeration side effect), so while the
    session is armed the phase reads ``armed`` regardless of the
    manager's passive observation. Otherwise, when a
    :class:`~rytm_randomizer.cockpit.device.connection.ConnectionManager`
    is registered (the ``__main__`` boot path), its latest observed phase
    is authoritative. Unwired sessions (unit tests, embedded harnesses)
    fall back to ``disconnected`` — honest for a mock session that has
    no hardware link at all.
    """

    if session_is_armed(session):
        return "armed"
    manager = active_connection_manager()
    if manager is not None:
        return manager.state.phase
    return "disconnected"


#: Backwards-compatible private alias — pre-Wave-4 callers (and tests)
#: reached this helper as ``_connection_phase``; the public name exists so
#: ``server.py``'s ``/health`` endpoint can share the exact same phase
#: resolution without importing an underscore symbol.
_connection_phase = resolve_connection_phase


def build_connection_changed(state: ConnectionState) -> dict[str, object]:
    """Construct the ``connection_changed`` event payload (whole state).

    Public because ``__main__`` uses it to adapt the ConnectionManager's
    ``on_change`` callback into a ``ConnectionRegistry.broadcast_event``
    push; :func:`emit_initial_events` reuses it for the bootstrap frame.
    """

    return {"type": EVENT_CONNECTION_CHANGED, "connection": state.to_dict()}


def _midi_port(session: CockpitSession) -> str | None:
    """Return the armed output-port name, or ``None`` when passive.

    The armed session is the authority: it owns the only real output port
    and knows the exact name the operator confirmed. Falling back to the
    device adapter's optional ``midi_port`` attribute keeps directly-
    injected live adapters (harnesses that never call ``arm``) rendering a
    port in the header strip. The :class:`DeviceAdapter` Protocol doesn't
    require ``midi_port``, so the probe stays :func:`getattr`-based rather
    than an ``isinstance`` ladder.
    """

    if session.armed_apply is not None:
        return session.armed_apply.port_name
    port = getattr(session.device, "midi_port", None)
    if port is None:
        return None
    return str(port)


def _build_snapshot_changed(snapshot: Snapshot) -> dict[str, object]:
    """Construct the ``snapshot_changed`` event payload."""

    return {"type": EVENT_SNAPSHOT_CHANGED, "snapshot": snapshot.to_dict()}


def _build_mutation_previewed(candidate: MutationCandidate | None) -> dict[str, object]:
    """Construct the ``mutation_previewed`` event payload (``None`` clears)."""

    return {
        "type": EVENT_MUTATION_PREVIEWED,
        "candidate": None if candidate is None else candidate.to_dict(),
    }


def _build_send_plan_changed(send_plan: CockpitSendPlan | None) -> dict[str, object]:
    """Construct the ``send_plan_changed`` event payload (``None`` clears)."""

    return {
        "type": EVENT_SEND_PLAN_CHANGED,
        "send_plan": None if send_plan is None else send_plan.to_dict(),
    }


def _build_history_updated(history: History) -> dict[str, object]:
    """Construct the ``history_updated`` event payload."""

    return {"type": EVENT_HISTORY_UPDATED, "history": history.to_dict()}


def _build_profile_changed(profile: ProfileModel | None) -> dict[str, object]:
    """Construct the ``profile_changed`` event payload (``None`` = no active)."""

    return {
        "type": EVENT_PROFILE_CHANGED,
        "profile": None if profile is None else profile.to_dict(),
    }


def _profile_catalog_item(profile: ProfileModel) -> dict[str, str]:
    """Return the compact, JSON-ready metadata shown in the profile catalogue."""

    return {
        "profile_id": profile.profile_id,
        "name": profile.name,
        "kind": profile.kind,
        "model_version": profile.model_version,
        "source_summary": profile.source_summary,
    }


def build_profile_catalog_changed(session: CockpitSession) -> dict[str, object]:
    """Construct the complete built-in + user profile catalogue event."""

    return {
        "type": EVENT_PROFILE_CATALOG_CHANGED,
        "profiles": [
            _profile_catalog_item(profile) for profile in session.profile_registry.list_profiles()
        ],
    }


def _build_patch_genome_changed(description: str, track: int) -> dict[str, object]:
    """Build one passive Analog Four patch-genome compiler event."""

    from ...reports.analog_four_patch_genome import (  # noqa: PLC0415
        build_analog_four_patch_genome_payload,
        build_analog_four_patch_genome_report_from_source,
    )

    report = build_analog_four_patch_genome_report_from_source(
        "--description",
        description,
        track=track,
        selected_candidate=2,
    )
    return {
        "type": EVENT_PATCH_GENOME_CHANGED,
        "patch_genome": build_analog_four_patch_genome_payload(report),
    }


def _build_kit_captures_changed(session: CockpitSession) -> dict[str, object]:
    """Build the whole verified-anchor set in stable device order."""

    return {
        "type": EVENT_KIT_CAPTURES_CHANGED,
        "captures": [
            session.kit_captures[device_id].to_dict()
            for device_id in CAPTURE_DEVICE_IDS
            if device_id in session.kit_captures
        ],
    }


def _build_mutation_targets_changed(session: CockpitSession) -> dict[str, object]:
    """Build both explicit include-lists as one whole-state event."""

    return {
        "type": EVENT_MUTATION_TARGETS_CHANGED,
        **MutationTargets(
            rytm_pad_targets=frozenset(session.rytm_pad_targets),
            a4_track_targets=frozenset(session.a4_track_targets),
        ).to_dict(),
    }


def _build_mutation_locks_changed(session: CockpitSession) -> dict[str, object]:
    """Build both lock deny-lists as one deterministic whole-state event."""

    return {
        "type": EVENT_MUTATION_LOCKS_CHANGED,
        "rytm_pad_locks": sorted(session.pad_locks),
        "a4_track_locks": sorted(session.a4_track_locks),
    }


def _build_dual_machine_stage_changed(session: CockpitSession) -> dict[str, object]:
    """Build the authoritative coordinated stage at its current revision."""

    return {
        "type": EVENT_DUAL_MACHINE_STAGE_CHANGED,
        "stage": session.stage_coordinator.state.to_dict(),
    }


def _record_stage_scope(session: CockpitSession, device_id: StageDeviceId) -> None:
    """Synchronize one lane's targets-or-all-minus-locks scope."""

    targets = MutationTargets(
        rytm_pad_targets=frozenset(session.rytm_pad_targets),
        a4_track_targets=frozenset(session.a4_track_targets),
    )
    if device_id == ANALOG_RYTM_DEVICE_ID:
        available_ids = frozenset(pad.pad_id for pad in session.device.capture_snapshot().pads)
        target_ids = frozenset(session.rytm_pad_targets)
        locked_ids = frozenset(session.pad_locks)
        effective_ids = targets.effective_rytm_pads(available_ids, locked_ids)
    else:
        available_ids = frozenset(range(A4_TRACK_TARGET_MIN, A4_TRACK_TARGET_MAX + 1))
        target_ids = frozenset(session.a4_track_targets)
        locked_ids = frozenset(session.a4_track_locks)
        effective_ids = targets.effective_a4_tracks(available_ids, locked_ids)
    session.stage_coordinator.record_scope(
        device_id,
        target_ids=target_ids,
        locked_ids=locked_ids,
        effective_ids=effective_ids,
    )


def _record_rytm_candidate(
    session: CockpitSession,
    candidate: MutationCandidate | None,
) -> None:
    """Record whether the current Rytm candidate is freshly usable."""

    session.stage_coordinator.record_candidate(
        ANALOG_RYTM_DEVICE_ID,
        ready=True if candidate is not None else None,
    )


def _build_performance_console_changed() -> dict[str, object]:
    """Construct the passive performance-console packet event."""

    from ...reports.live_gui_performance_console_model import (  # noqa: PLC0415
        live_gui_performance_console_model_payload,
    )

    payload = live_gui_performance_console_model_payload()
    return {
        "type": EVENT_PERFORMANCE_CONSOLE_CHANGED,
        "performance_console": payload["live_gui_performance_console"],
    }


async def emit_initial_events(emitter: EventEmitter, session: CockpitSession) -> None:
    """Send the 11 bootstrap events a freshly-connected client expects.

    Order matters for the UI: a client renders the session status pill
    first (so the user sees "armed" or "mock"), then the snapshot (so
    pads render), then the active profile (so the profile chip
    highlights), then the history strip, then the passive performance
    console packet. The cockpit web frontend handles them in any order,
    but this order keeps debug logs readable when stepping through a
    fresh connect.
    """

    _record_stage_scope(session, ANALOG_RYTM_DEVICE_ID)
    _record_stage_scope(session, ANALOG_FOUR_DEVICE_ID)
    await emitter.send_event(_build_session_status(session))
    await emitter.send_event(_build_snapshot_changed(session.device.capture_snapshot()))
    await emitter.send_event(_build_profile_changed(session.active_profile))
    await emitter.send_event(build_profile_catalog_changed(session))
    await emitter.send_event(_build_history_updated(session.history_store.current))
    await emitter.send_event(
        _build_patch_genome_changed(
            session.patch_genome_description,
            session.patch_genome_track,
        )
    )
    await emitter.send_event(_build_kit_captures_changed(session))
    await emitter.send_event(_build_mutation_targets_changed(session))
    await emitter.send_event(_build_mutation_locks_changed(session))
    await emitter.send_event(_build_dual_machine_stage_changed(session))
    await emitter.send_event(_build_performance_console_changed())
    # Wave 3: when the launch brain is wired (the ``__main__`` boot path),
    # a freshly-connected client also receives the latest passive
    # connection state so the header renders plug/unplug truth without
    # waiting for the next poll diff. Unwired sessions (unit tests,
    # embedded harnesses) keep the authoritative 11-event whole-state
    # bootstrap; wired sessions append this connection frame as event 12.
    manager = active_connection_manager()
    if manager is not None:
        await emitter.send_event(build_connection_changed(manager.state))


# ---------------------------------------------------------------------------
# Internal candidate-recompute helper.
#
# Several commands (set_depth, set_pad_lock, toggle_preview, regen, select_profile)
# need to recompute the current candidate. Centralising the logic keeps the
# dependence-on-profile guard in one place.
# ---------------------------------------------------------------------------


# Bounded LRU memoization for :func:`_recompute_candidate` (CODE_REVIEW.md
# M12). ``mutate(snapshot, profile, depth, seed)`` is a pure function (modulo
# the fresh ``candidate_id`` ULID), so identical four-input tuples produce
# semantically identical candidates. The cockpit UI repeatedly recomputes
# the same candidate during toggle_preview / regen / set_pad_lock churn
# while the operator is still iterating on the same (snapshot, profile,
# depth, seed) tuple — caching elides the redundant ``mutate`` calls
# entirely.
#
# Key: ``(snapshot_id, profile_id, depth, seed)``. The snapshot id changes
# every time the device captures a new snapshot, and the profile id is the
# ULID of the active profile, so two cache keys can only collide when the
# operator is genuinely asking for the same candidate. ``depth`` is a
# float; equality on the snapped slider values (0.10..0.90 step 0.01) is
# exact under IEEE-754 because the UI emits floats with at most two
# fractional decimal digits — but to be safe the cache lookup falls back
# to the engine on any miss.
#
# Size: 16 entries is small enough that the cache occupies trivial memory
# (~16 ``MutationCandidate`` instances per session) and large enough to
# absorb the common "regen this depth a few times, then nudge depth, then
# regen a few more" iteration pattern operators show in the v10 UX
# mockups.
_RECOMPUTE_CACHE_MAXSIZE: Final[int] = 16
_recompute_cache: OrderedDict[
    tuple[str, str, float, int, tuple[int, ...], tuple[int, ...]],
    MutationCandidate,
] = OrderedDict()


def _recompute_candidate(
    session: CockpitSession,
    *,
    force_fresh: bool = False,
) -> MutationCandidate | None:
    """Recompute and store the current candidate, or ``None`` if not ready.

    The engine needs an active profile + a captured snapshot to mutate.
    With no active profile, we clear ``current_candidate`` to ``None`` and
    return ``None`` — the UI then sees an empty ghost overlay even with
    the preview toggle on.

    Memoized via :data:`_recompute_cache` (a bounded LRU keyed on the four
    pure inputs ``(snapshot_id, profile_id, depth, seed)``) so toggling
    preview / locking a pad / regenerating with unchanged depth + seed
    returns the prior candidate without re-running :func:`mutate`. The
    cache survives across handler invocations within a single Python
    process — the cockpit session is one process — and is bounded at
    :data:`_RECOMPUTE_CACHE_MAXSIZE` entries so it cannot grow unbounded
    if the operator churns through many depth values.
    """

    if session.active_profile is None:
        session.current_candidate = None
        return None
    snapshot = session.device.capture_snapshot()
    target_pad_ids = frozenset(session.rytm_pad_targets)
    key = (
        snapshot.snapshot_id,
        session.active_profile.profile_id,
        session.depth,
        session.seed,
        tuple(sorted(target_pad_ids)),
        tuple(sorted(session.pad_locks)),
    )
    cached = None if force_fresh else _recompute_cache.get(key)
    if cached is not None:
        # LRU touch — re-insert moves the key to the most-recent end.
        _recompute_cache.move_to_end(key)
        session.current_candidate = cached
        return cached
    candidate = mutate(
        snapshot,
        session.active_profile,
        session.depth,
        session.seed,
        target_pad_ids=target_pad_ids,
    )
    _recompute_cache[key] = candidate
    # Evict the least-recently-used entry once over capacity. ``popitem
    # (last=False)`` removes the front (oldest) entry; with the touch
    # above this is the classic OrderedDict-as-LRU pattern.
    if len(_recompute_cache) > _RECOMPUTE_CACHE_MAXSIZE:
        _recompute_cache.popitem(last=False)
    session.current_candidate = candidate
    return candidate


def _clear_send_plan_if_needed(session: CockpitSession) -> list[dict[str, object]]:
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


def _error_ack(code: str, message: str) -> dict[str, object]:
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


def _exc_fingerprint(exc: BaseException) -> str | None:
    """Return the taxonomy fingerprint for ``exc`` (or ``None`` for stdlib).

    OBS O4 — every :class:`RytmRandomizerError` subclass declares a
    stable, short ``fingerprint`` class attribute (a lowercase
    ``<subsystem>.<verb>.<noun>`` dot-path) that an operator
    ``grep``s for in logs and a future alerting tier groups on. This
    helper is the single point of truth for "give me the fingerprint
    of any caught exception, or ``None`` if it is not a taxonomy
    member". Used by the structured ``_logger.warning(..., extra={
    "exception_repr": ...})`` call sites in this module so every
    WS-side error log entry carries the same aggregator field when
    the cause is a taxonomy raise.
    """

    if isinstance(exc, RytmRandomizerError):
        return exc.fingerprint
    return None


def _redacted_exception_repr(
    exc: BaseException,
    *,
    sensitive_value: str | None = None,
) -> str:
    """Render ``exc`` while removing an operator's machine-local port name."""

    if sensitive_value:
        # Do not scrub the already-rendered repr: Python can choose either
        # quote style and add multiple escaping layers, so a port containing
        # quotes, backslashes, or control characters can evade token
        # replacement.  The categorical exception type remains useful for
        # diagnosis; the free-form detail is intentionally omitted whenever
        # it may contain an operator's machine-local port name.
        return f"{type(exc).__name__}('<redacted-midi-port>')"
    return repr(exc)


# ---------------------------------------------------------------------------
# Per-command handlers.
#
# Each takes (cmd_body, session), returns a :class:`HandlerResult` carrying
# the partial ack and the list of events to broadcast (in declaration order)
# after the ack. The dispatcher fills in ``request_id`` and sends ack-first.
# ---------------------------------------------------------------------------

_PATCH_GENOME_DESCRIPTION_MAX: Final[int] = 240
_PATCH_GENOME_TRACK_MIN: Final[int] = 1
_PATCH_GENOME_TRACK_MAX: Final[int] = 4


async def _handle_analyze_patch_genome(
    cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
    """Compile four real, passive Analog Four candidates from a text description."""

    description_raw = cmd["description"]
    track_raw = cmd["track"]
    if not isinstance(description_raw, str):
        raise ValueError("description must be a string")
    description = description_raw.strip()
    if not description:
        raise ValueError("description must not be empty")
    if len(description) > _PATCH_GENOME_DESCRIPTION_MAX:
        raise ValueError("description is too long")
    if isinstance(track_raw, bool) or not isinstance(track_raw, int):
        raise ValueError("track must be an integer")
    if not (_PATCH_GENOME_TRACK_MIN <= track_raw <= _PATCH_GENOME_TRACK_MAX):
        raise ValueError("track must be between 1 and 4")
    effective_tracks = MutationTargets(
        a4_track_targets=frozenset(session.a4_track_targets)
    ).effective_a4_tracks(
        range(A4_TRACK_TARGET_MIN, A4_TRACK_TARGET_MAX + 1),
        session.a4_track_locks,
    )
    if track_raw not in effective_tracks:
        return HandlerResult(
            ack=_error_ack(
                ERR_VALIDATION,
                "selected A4 track is not sendable under the current targets and locks",
            )
        )

    event = _build_patch_genome_changed(description, track_raw)
    patch_genome = cast("dict[str, object]", event["patch_genome"])
    genome = cast("dict[str, object]", patch_genome["genome"])
    candidates = cast("list[object]", genome["candidates"])
    session.patch_genome_description = description
    session.patch_genome_track = track_raw
    _record_stage_scope(session, ANALOG_FOUR_DEVICE_ID)
    session.stage_coordinator.record_candidate(
        ANALOG_FOUR_DEVICE_ID,
        ready=False,
        blocked_reason="a4_semantic_mapping_unpromoted",
    )
    session.stage_coordinator.record_plan(ANALOG_FOUR_DEVICE_ID, ready=False)
    _logger.info(
        "patch_genome_analyzed",
        extra={
            "description_length": len(description),
            "selected_track": track_raw,
            "candidate_count": len(candidates),
            "opened_midi_port": False,
            "sent_midi": False,
        },
    )
    return HandlerResult(
        ack={"ok": True, "patch_genome": patch_genome},
        events=[event, _build_dual_machine_stage_changed(session)],
    )


async def _handle_list_capture_inputs(
    cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
    """Enumerate MIDI inputs only after the operator opens a capture workflow."""

    device_id = narrow_kit_capture_device_id(cmd["device_id"])
    names = await asyncio.to_thread(session.kit_capture_service.list_input_names)
    return HandlerResult(
        ack={
            "ok": True,
            "capture_enabled": session.kit_capture_service.enabled,
            "capture_device_id": device_id,
            "capture_inputs": list(names),
        }
    )


async def _handle_capture_current_kit(
    cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
    """Wait input-only for one selected machine's current KIT SysEx dump."""

    device_id = narrow_kit_capture_device_id(cmd["device_id"])
    input_port = cmd["input_port"]
    if not isinstance(input_port, str) or not input_port.strip():
        raise ValueError("capture input_port must be a non-empty string")
    try:
        result = await asyncio.to_thread(
            session.kit_capture_service.capture,
            device_id,
            input_port.strip(),
        )
    except (OSError, RuntimeError, TypeError, ValueError, RytmRandomizerError) as exc:
        _logger.warning(
            "cockpit_kit_capture_failed",
            extra={
                "device_id": device_id,
                "exception_type": type(exc).__name__,
                "exception_repr": _redacted_exception_repr(
                    exc,
                    sensitive_value=input_port.strip(),
                ),
                "fingerprint": _CAPTURE_FAILED_FINGERPRINT,
            },
        )
        session.error_journal.record(
            _CAPTURE_FAILED_FINGERPRINT,
            "current-kit capture failed",
            context={"device_id": device_id},
        )
        get_metrics().record_error(_CAPTURE_FAILED_FINGERPRINT)
        session.stage_coordinator.record_capture(
            device_id,
            succeeded=False,
            connected=None,
            error="current-kit capture failed",
        )
        failure_events: list[dict[str, object]] = []
        if device_id == ANALOG_RYTM_DEVICE_ID:
            failure_events.extend(_clear_send_plan_if_needed(session))
            session.current_candidate = None
            if session.preview_on:
                failure_events.append(_build_mutation_previewed(None))
        failure_events.append(_build_dual_machine_stage_changed(session))
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "current-kit capture failed"),
            events=failure_events,
        )
    events: list[dict[str, object]] = []
    session.stage_coordinator.record_capture(
        device_id,
        succeeded=True,
        connected=True,
    )
    if device_id == ANALOG_RYTM_DEVICE_ID:
        snapshot = cockpit_snapshot_from_rytm_capture(result)
        events.extend(_clear_send_plan_if_needed(session))
        session.device.adopt_snapshot(snapshot)
        if session.history_store.has_entries:
            session.history_store.append_post_send(snapshot, via="capture")
        else:
            session.history_store.initial(snapshot)
        session.current_candidate = None
        candidate = _recompute_candidate(session, force_fresh=True)
        _record_stage_scope(session, ANALOG_RYTM_DEVICE_ID)
        _record_rytm_candidate(session, candidate)
        events.extend(
            [
                _build_snapshot_changed(snapshot),
                _build_history_updated(session.history_store.current),
            ]
        )
        if session.preview_on:
            events.append(_build_mutation_previewed(candidate))
    else:
        _record_stage_scope(session, ANALOG_FOUR_DEVICE_ID)
    session.kit_captures[device_id] = result
    events.insert(0, _build_kit_captures_changed(session))
    events.append(_build_dual_machine_stage_changed(session))
    return HandlerResult(
        ack={"ok": True, "kit_capture": result.to_dict()},
        events=events,
    )


async def _handle_select_profile(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    profile_id = str(cmd["profile_id"])
    profile = session.profile_registry.get(profile_id)
    if profile is None:
        return HandlerResult(ack=_error_ack(ERR_VALIDATION, f"unknown profile_id: {profile_id!r}"))
    events = _clear_send_plan_if_needed(session)
    session.active_profile = profile
    candidate = _recompute_candidate(session)
    _record_rytm_candidate(session, candidate)
    events.append(_build_profile_changed(profile))
    if session.preview_on:
        events.append(_build_mutation_previewed(candidate))
    events.append(_build_dual_machine_stage_changed(session))
    return HandlerResult(ack={"ok": True}, events=events)


async def _handle_set_depth(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    # ``cast`` mirrors the historical ``float(<wire value>)`` coercion
    # exactly: a non-numeric wire value still raises through ``float``.
    depth = float(cast(SupportsFloat, cmd["depth"]))
    events = _clear_send_plan_if_needed(session)
    session.depth = depth
    candidate = _recompute_candidate(session)
    _record_rytm_candidate(session, candidate)
    if session.preview_on:
        events.append(_build_mutation_previewed(candidate))
    events.append(_build_dual_machine_stage_changed(session))
    return HandlerResult(
        ack={"ok": True, "candidate": None if candidate is None else candidate.to_dict()},
        events=events,
    )


async def _handle_set_pad_lock(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    pad_id = cmd["pad_id"]
    locked = cmd["locked"]
    if isinstance(pad_id, bool) or not isinstance(pad_id, int):
        raise ValueError("pad_id must be an integer")
    if not (RYTM_PAD_TARGET_MIN <= pad_id <= RYTM_PAD_TARGET_MAX):
        raise ValueError("pad_id must be between 1 and 12")
    if not isinstance(locked, bool):
        raise ValueError("locked must be a boolean")
    if locked:
        session.pad_locks.add(pad_id)
    else:
        session.pad_locks.discard(pad_id)
    events = _clear_send_plan_if_needed(session)
    session.current_candidate = None
    _record_stage_scope(session, ANALOG_RYTM_DEVICE_ID)
    candidate = _recompute_candidate(session, force_fresh=True)
    _record_rytm_candidate(session, candidate)
    _logger.info(
        "mutation_lock_changed",
        extra={
            "device_id": ANALOG_RYTM_DEVICE_ID,
            "item_id": pad_id,
            "locked": locked,
            "locked_item_ids": sorted(session.pad_locks),
        },
    )
    events.append(_build_mutation_locks_changed(session))
    if session.preview_on:
        events.append(_build_mutation_previewed(candidate))
    events.append(_build_dual_machine_stage_changed(session))
    return HandlerResult(ack={"ok": True}, events=events)


async def _handle_set_a4_track_lock(
    cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
    """Set the A4 deny-list state without granting any SEND authority."""

    track = cmd["track"]
    locked = cmd["locked"]
    if isinstance(track, bool) or not isinstance(track, int):
        raise ValueError("track must be an integer")
    if not (A4_TRACK_TARGET_MIN <= track <= A4_TRACK_TARGET_MAX):
        raise ValueError("track must be between 1 and 4")
    if not isinstance(locked, bool):
        raise ValueError("locked must be a boolean")
    if locked:
        session.a4_track_locks.add(track)
    else:
        session.a4_track_locks.discard(track)
    _record_stage_scope(session, ANALOG_FOUR_DEVICE_ID)
    _logger.info(
        "mutation_lock_changed",
        extra={
            "device_id": ANALOG_FOUR_DEVICE_ID,
            "item_id": track,
            "locked": locked,
            "locked_item_ids": sorted(session.a4_track_locks),
        },
    )
    return HandlerResult(
        ack={"ok": True},
        events=[
            _build_mutation_locks_changed(session),
            _build_dual_machine_stage_changed(session),
        ],
    )


def _target_ids_from_command(cmd: dict[str, object], *, device_id: str) -> frozenset[int]:
    """Validate one target replacement at the untrusted WS boundary."""

    raw_target_ids = cmd["target_ids"]
    if not isinstance(raw_target_ids, (list, tuple)):
        raise ValueError("target_ids must be a list")
    target_items = cast("list[object] | tuple[object, ...]", raw_target_ids)
    validated_ids: set[int] = set()
    for value in target_items:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("target_ids must contain integers")
        validated_ids.add(value)
    target_ids = frozenset(validated_ids)
    if device_id == ANALOG_RYTM_DEVICE_ID:
        return MutationTargets(rytm_pad_targets=target_ids).rytm_pad_targets
    return MutationTargets(a4_track_targets=target_ids).a4_track_targets


async def _handle_set_mutation_targets(
    cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
    """Replace one device's explicit include-list and invalidate stale plans."""

    device_id = narrow_kit_capture_device_id(cmd["device_id"])
    target_ids = _target_ids_from_command(cmd, device_id=device_id)
    events: list[dict[str, object]] = []
    candidate: MutationCandidate | None = None
    if device_id == ANALOG_RYTM_DEVICE_ID:
        events.extend(_clear_send_plan_if_needed(session))
        session.rytm_pad_targets = set(target_ids)
        session.current_candidate = None
        _record_stage_scope(session, ANALOG_RYTM_DEVICE_ID)
        candidate = _recompute_candidate(session, force_fresh=True)
        _record_rytm_candidate(session, candidate)
    else:
        session.a4_track_targets = set(target_ids)
        _record_stage_scope(session, ANALOG_FOUR_DEVICE_ID)
    _logger.info(
        "mutation_targets_changed",
        extra={
            "device_id": device_id,
            "target_ids": sorted(target_ids),
        },
    )
    events.append(_build_mutation_targets_changed(session))
    if device_id == ANALOG_RYTM_DEVICE_ID and session.preview_on:
        events.append(_build_mutation_previewed(candidate))
    events.append(_build_dual_machine_stage_changed(session))
    return HandlerResult(ack={"ok": True}, events=events)


async def _handle_clear_mutation_targets(
    cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
    """Clear one include-list, restoring the historical all-scope default."""

    device_id = narrow_kit_capture_device_id(cmd["device_id"])
    events: list[dict[str, object]] = []
    candidate: MutationCandidate | None = None
    if device_id == ANALOG_RYTM_DEVICE_ID:
        events.extend(_clear_send_plan_if_needed(session))
        session.rytm_pad_targets.clear()
        session.current_candidate = None
        _record_stage_scope(session, ANALOG_RYTM_DEVICE_ID)
        candidate = _recompute_candidate(session, force_fresh=True)
        _record_rytm_candidate(session, candidate)
    else:
        session.a4_track_targets.clear()
        _record_stage_scope(session, ANALOG_FOUR_DEVICE_ID)
    _logger.info(
        "mutation_targets_changed",
        extra={"device_id": device_id, "target_ids": []},
    )
    events.append(_build_mutation_targets_changed(session))
    if device_id == ANALOG_RYTM_DEVICE_ID and session.preview_on:
        events.append(_build_mutation_previewed(candidate))
    events.append(_build_dual_machine_stage_changed(session))
    return HandlerResult(ack={"ok": True}, events=events)


async def _handle_toggle_preview(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    on = bool(cmd["on"])
    events = _clear_send_plan_if_needed(session)
    session.preview_on = on
    # Toggling preview on recomputes a fresh candidate (so stale state isn't
    # shown); toggling off keeps the prior candidate in memory but emits a
    # null event so the ghost overlay drops.
    candidate = _recompute_candidate(session) if on else session.current_candidate
    _record_rytm_candidate(session, candidate)
    if on:
        events.append(_build_mutation_previewed(candidate))
    else:
        events.append(_build_mutation_previewed(None))
    events.append(_build_dual_machine_stage_changed(session))
    return HandlerResult(
        ack={
            "ok": True,
            "candidate": None if candidate is None or not on else candidate.to_dict(),
        },
        events=events,
    )


async def _handle_regen(_cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    # regen has no body fields
    if session.active_profile is None:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "no active profile; select one before regen")
        )
    # Bump the seed so the candidate genuinely changes (without moving depth).
    # Using a fresh 32-bit sample is simpler and indistinguishable from a
    # deterministic next-value, and matches the spec wording ("REGEN bumps
    # the seed to vary the output").
    from .session import fresh_seed  # local import to keep module surface clean

    events = _clear_send_plan_if_needed(session)
    session.seed = fresh_seed()
    candidate = _recompute_candidate(session, force_fresh=True)
    _record_rytm_candidate(session, candidate)
    if session.preview_on:
        events.append(_build_mutation_previewed(candidate))
    events.append(_build_dual_machine_stage_changed(session))
    return HandlerResult(
        ack={"ok": True, "candidate": None if candidate is None else candidate.to_dict()},
        events=events,
    )


async def _handle_prepare_send_plan(
    _cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
    if session.current_candidate is None:
        session.stage_coordinator.record_plan(ANALOG_RYTM_DEVICE_ID, ready=False)
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "no current candidate; set a profile and depth first"),
            events=[_build_dual_machine_stage_changed(session)],
        )
    plan = prepare_send_plan(
        session.device.capture_snapshot(),
        session.active_profile,
        session.current_candidate,
        frozenset(session.pad_locks),
        pad_targets=frozenset(session.rytm_pad_targets),
    )
    if plan is None:
        session.stage_coordinator.record_plan(ANALOG_RYTM_DEVICE_ID, ready=False)
        return HandlerResult(
            ack=_error_ack(
                ERR_VALIDATION, "no active profile; select one before preparing send plan"
            ),
            events=[_build_dual_machine_stage_changed(session)],
        )
    session.current_send_plan = plan
    session.stage_coordinator.record_plan(ANALOG_RYTM_DEVICE_ID, ready=plan.ready)
    return HandlerResult(
        ack={"ok": True, "send_plan": plan.to_dict()},
        events=[
            _build_send_plan_changed(plan),
            _build_dual_machine_stage_changed(session),
        ],
    )


async def _handle_send(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    if session.current_candidate is None:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "no current candidate; set a profile and depth first")
        )
    if session.current_send_plan is None or not session.current_send_plan.ready:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "no ready send plan; run prepare_send_plan first")
        )
    sent_plan = session.current_send_plan
    requested_plan_id = cmd.get("send_plan_id")
    if requested_plan_id is not None and not isinstance(requested_plan_id, str):
        return HandlerResult(ack=_error_ack(ERR_VALIDATION, "send_plan_id must be a string"))
    if requested_plan_id is not None and requested_plan_id != sent_plan.plan_id:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "send_plan_id does not match the prepared plan")
        )
    if (
        session.armed_apply is not None or session.device.is_armed
    ) and requested_plan_id != sent_plan.plan_id:
        return HandlerResult(
            ack=_error_ack(
                ERR_VALIDATION,
                "armed SEND requires confirmation of the current prepared plan",
            )
        )
    if session.armed_apply is not None:
        refusal = _armed_send_over_seam(session, sent_plan, cmd)
        if refusal is not None:
            return refusal
    elif session.hardware_intent:
        # The operator armed and never explicitly disarmed, but the seam is
        # gone — an INVOLUNTARY auto-disarm (device unplugged, provider
        # error, transport teardown) cleared it. Falling through here would
        # skip the per-action confirmation, write to the mock adapter, and
        # ack ok:True with a new snapshot id while putting ZERO bytes on the
        # wire: the operator keeps performing, believing the device is
        # following. Refuse instead, and say why.
        return HandlerResult(
            ack=_error_ack(
                ERR_VALIDATION,
                "hardware was disarmed automatically (device lost or send "
                "failed); re-arm to send to hardware, or disarm explicitly "
                "to continue in mock mode",
            )
        )
    elif session.device.is_armed:
        _logger.info(
            "cockpit_live_send_authorized",
            extra={
                "send_plan_id": sent_plan.plan_id,
                "packet_count": len(sent_plan.packets),
                "pad_ids": sorted({packet.pad_id for packet in sent_plan.packets}),
            },
        )
    try:
        new_snapshot = session.device.apply_send_plan(sent_plan)
    except (OSError, RuntimeError, RytmRandomizerError) as exc:
        _logger.warning(
            "cockpit_guarded_send_failed",
            extra={
                "exception_type": type(exc).__name__,
                "exception_repr": repr(exc),
                "fingerprint": _GUARDED_SEND_FAILED_FINGERPRINT,
                "send_plan_id": sent_plan.plan_id,
            },
        )
        session.error_journal.record(
            _GUARDED_SEND_FAILED_FINGERPRINT,
            "send failed at the guarded device boundary",
            context={"plan_id": sent_plan.plan_id},
        )
        get_metrics().record_error(_GUARDED_SEND_FAILED_FINGERPRINT)
        session.stage_coordinator.record_send(ANALOG_RYTM_DEVICE_ID, succeeded=False)
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "send failed at the guarded device boundary"),
            events=[_build_dual_machine_stage_changed(session)],
        )
    session.history_store.append_post_send(new_snapshot, via="send")
    session.unsaved_sends += 1
    # Preview clears after a SEND per spec § "Operator hits SEND" step 4.
    session.current_candidate = None
    session.current_send_plan = None
    session.stage_coordinator.record_send(ANALOG_RYTM_DEVICE_ID, succeeded=True)
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
            _build_dual_machine_stage_changed(session),
        ],
    )


SAVE_UNSUPPORTED_MESSAGE: Final[str] = (
    "save is not supported: writing a kit to the device's persistent memory "
    "requires a SysEx kit write plus a capture-before-write restore path, "
    "neither of which exists. Nothing was written and no history entry was "
    "promoted."
)
"""The single, honest refusal text for the ``save`` command.

Spells out what is missing and — critically — states that **nothing
changed**, because the previous ack said the opposite.
"""


async def _handle_save(_cmd: dict[str, object], _session: CockpitSession) -> HandlerResult:
    """Refuse ``save``: no persistent kit-write capability exists.

    This handler used to ack ``{"ok": true, "snapshot_id": ...}`` and
    promote the current history entry to ``kind="saved"`` with
    ``unsaved_sends`` reset to zero — the full vocabulary of a durable
    write. Underneath, the only thing it called was
    ``session.device.commit_kit``, whose sole implementation was a mock
    ``logger.info`` line. Nothing was ever written to a device, on the
    mock path or any other, while ``docs/COCKPIT_QUICKSTART.md`` told
    operators "SAVE writes a Rytm SysEx kit dump to the device's
    persistent kit memory."

    That is the worst failure shape available here: an operator who
    believes a kit is safely stored stops treating it as volatile, and
    loses it on the next power cycle. A refusal costs them a workflow; a
    false success costs them their work.

    So ``save`` now fails closed and says why. It is deliberately
    unconditional — refusing only "when unimplemented" would still leave
    the mock path acking a durable write it cannot perform. The
    capability returns when a real SysEx kit write plus the
    capture-before-write restore path the Live-but-Passive model requires
    both land; until then the armed seam refuses persistent kit/sound
    mutation for exactly the same reason (see
    :class:`~rytm_randomizer.senders.armed_apply.KitMutationUnsupportedError`).

    Emits **no** events: refusing must not perturb history, the unsaved
    counter, or the session status. Both arguments are unused by design.
    """

    return HandlerResult(ack=_error_ack(ERR_VALIDATION, SAVE_UNSUPPORTED_MESSAGE))


async def _handle_load_snapshot(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
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
                # OBS O4 — taxonomy fingerprint pass-through. ``KeyError``
                # is a stdlib exception (no fingerprint); the helper
                # returns ``None`` and the log entry carries an explicit
                # ``fingerprint=None`` so the field exists for log
                # shippers' presence-based filters either way.
                "fingerprint": _exc_fingerprint(exc),
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


async def _handle_undo(_cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
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


async def _handle_export_profile_model(
    cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
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


def _live_kit_operator_package_payload() -> dict[str, object]:
    """Return the current passive live-kit operator package payload."""

    from ...reports.live_gui_performance_console_model import (  # noqa: PLC0415
        live_gui_performance_console_model_payload,
    )

    console_payload = cast(
        "Mapping[str, object]",
        live_gui_performance_console_model_payload()["live_gui_performance_console"],
    )
    return cast("dict[str, object]", console_payload["live_kit_operator_package"])


def _row_objects(rows: object) -> list[object]:
    """Narrow one wire-supplied payload field to a list of opaque rows."""

    if not isinstance(rows, list):
        return []
    return cast("list[object]", rows)


def _operator_package_steps(package: Mapping[str, object]) -> list[Mapping[str, object]]:
    rows = _row_objects(package.get("operator_steps", []))
    return [cast("Mapping[str, object]", row) for row in rows if isinstance(row, dict)]


def _operator_package_bindings(package: Mapping[str, object]) -> list[Mapping[str, object]]:
    rows = _row_objects(package.get("slot_bindings", []))
    return [cast("Mapping[str, object]", row) for row in rows if isinstance(row, dict)]


def _operator_package_blocked_actions(package: Mapping[str, object]) -> list[str]:
    rows = _row_objects(package.get("blocked_actions", []))
    return [row for row in rows if isinstance(row, str)]


def _operator_package_safety_lines(package: Mapping[str, object]) -> list[str]:
    rows = _row_objects(package.get("safety_lines", []))
    return [row for row in rows if isinstance(row, str)]


def _validate_operator_package_header(
    cmd: Mapping[str, object],
    package: Mapping[str, object],
) -> dict[str, object] | None:
    if cmd.get("mock_safe") is not True:
        return _error_ack(ERR_VALIDATION, "mock_safe must be true for operator package rehearsal")
    operator_package_id = str(cmd["operator_package_id"])
    expected_package_id = str(package["operator_package_id"])
    if operator_package_id != expected_package_id:
        return _error_ack(
            ERR_VALIDATION,
            f"unknown operator_package_id: {operator_package_id!r}",
        )
    return None


def _operator_package_step_by_key(
    package: Mapping[str, object],
    step_key: str,
) -> Mapping[str, object] | None:
    return next(
        (row for row in _operator_package_steps(package) if row.get("step_key") == step_key),
        None,
    )


def _operator_package_binding_by_slot(
    package: Mapping[str, object],
    slot_key: str,
) -> Mapping[str, object]:
    empty_binding: Mapping[str, object] = {}
    return next(
        (row for row in _operator_package_bindings(package) if row.get("slot_key") == slot_key),
        empty_binding,
    )


def _expected_operator_package_export_key(
    *,
    step: Mapping[str, object],
    binding: Mapping[str, object],
) -> str:
    fallback_slot = str(step["slot_key"])
    return str(binding.get("package_export_key", f"operator-package-{fallback_slot}"))


def _operator_package_export_key_mismatch_ack(
    *,
    step_key: str,
    expected_package_export_key: str,
    provided_package_export_key: str | None,
) -> dict[str, object] | None:
    if provided_package_export_key is None:
        return None
    if provided_package_export_key == expected_package_export_key:
        return None
    return _error_ack(
        ERR_VALIDATION,
        f"package_export_key mismatch for operator package step: {step_key!r}",
    )


def _operator_package_step_rehearsal(
    *,
    package: Mapping[str, object],
    step: Mapping[str, object],
    binding: Mapping[str, object],
    snapshot_id: str,
) -> dict[str, object]:
    step_key = str(step["step_key"])
    slot_key = str(step["slot_key"])
    depth_percent = int(cast(SupportsInt, binding.get("depth_percent", 0)))
    package_export_key = _expected_operator_package_export_key(step=step, binding=binding)
    return {
        "rehearsal_id": f"operator-package-rehearsal:{step_key}",
        "operator_package_id": str(package["operator_package_id"]),
        "step_key": step_key,
        "slot_key": slot_key,
        "label": str(step["label"]),
        "cockpit_binding": str(step["cockpit_binding"]),
        "local_action": str(step["local_action"]),
        "stage_target": str(step["stage_target"]),
        "recovery_command": str(step["recovery_command"]),
        "operator_command": str(step["operator_command"]),
        "package_export_key": package_export_key,
        "snapshot_id": snapshot_id,
        "depth_percent": depth_percent,
        "mock_safe": True,
        "rehearsal_status": "mock_safe_ready",
        "safety_status": str(step["safety_status"]),
        "opened_midi_port": False,
        "sent_midi": False,
        "writes_files": False,
        "blocked_actions": _operator_package_blocked_actions(package),
        "safety_lines": _operator_package_safety_lines(package),
    }


def _operator_package_recovery_requirements(
    package: Mapping[str, object],
) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in cast(
            list[Mapping[str, object]],
            package["recovery_requirements"],
        )
    ]


def _operator_package_apply_preview_step(
    *,
    order: int,
    step: Mapping[str, object],
    package_export_key: str,
) -> dict[str, object]:
    return {
        "order": order,
        "step_key": str(step["step_key"]),
        "slot_key": str(step["slot_key"]),
        "label": str(step["label"]),
        "package_export_key": package_export_key,
        "local_action": str(step["local_action"]),
        "operator_command": str(step["operator_command"]),
        "recovery_command": str(step["recovery_command"]),
        "readiness_status": "ready_for_mock_apply_preview",
        "blocked_action": "real_send_blocked",
    }


def _operator_package_mock_apply_step(
    *,
    order: int,
    step: Mapping[str, object],
    package_export_key: str,
) -> dict[str, object]:
    return {
        "order": order,
        "step_key": str(step["step_key"]),
        "slot_key": str(step["slot_key"]),
        "label": str(step["label"]),
        "package_export_key": package_export_key,
        "local_action": str(step["local_action"]),
        "operator_command": str(step["operator_command"]),
        "recovery_command": str(step["recovery_command"]),
        "mock_apply_status": "accepted_for_mock_apply",
        "blocked_action": "real_apply_blocked",
    }


def _operator_package_apply_preview_readiness_checks(
    *,
    operator_package_id: str,
    step_count: int,
) -> list[dict[str, object]]:
    return [
        {"check": "mock_safe", "status": "passed", "required": True},
        {
            "check": "operator_package_id",
            "status": "passed",
            "operator_package_id": operator_package_id,
        },
        {"check": "selected_steps", "status": "passed", "step_count": step_count},
        {
            "check": "package_export_keys",
            "status": "passed",
            "binding_count": step_count,
        },
    ]


def _operator_package_apply_preview_summary(*, step_count: int) -> dict[str, object]:
    return {
        "apply_policy": "preview_only",
        "would_apply_steps": step_count,
        "would_open_midi_port": False,
        "would_send_midi": False,
        "would_write_files": False,
        "would_mutate_snapshot": False,
        "events_emitted": False,
    }


def _operator_package_mock_apply_summary(*, step_count: int) -> dict[str, object]:
    return {
        "apply_policy": "mock_apply_only",
        "mock_applied_steps": step_count,
        "opened_midi_port": False,
        "sent_midi": False,
        "writes_files": False,
        "mutated_snapshot": False,
        "applied_send_plan": False,
        "events_emitted": False,
    }


def _operator_package_receipt_summary(*, step_count: int) -> dict[str, object]:
    return {
        "receipt_policy": "passive_audit_only",
        "recorded_steps": step_count,
        "records_apply_preview": True,
        "would_open_midi_port": False,
        "would_send_midi": False,
        "would_write_files": False,
        "would_mutate_snapshot": False,
        "would_apply_send_plan": False,
        "events_emitted": False,
    }


def _operator_package_receipt_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _operator_package_step_keys_from_command(
    cmd: Mapping[str, object],
    package: Mapping[str, object],
) -> list[str]:
    requested = cmd.get("step_keys", [])
    if not isinstance(requested, list) or not requested:
        return [str(row["step_key"]) for row in _operator_package_steps(package)]
    return [str(step_key) for step_key in cast("list[object]", requested)]


def _operator_package_export_keys_from_command(cmd: Mapping[str, object]) -> dict[str, str]:
    provided = cmd.get("package_export_keys", {})
    if not isinstance(provided, dict):
        return {}
    rows = cast("dict[object, object]", provided)
    return {str(key): str(value) for key, value in rows.items()}


async def _handle_rehearse_operator_package_step(
    cmd: dict[str, object], _session: CockpitSession
) -> HandlerResult:
    """Rehearse one operator package step through the WS bridge without side effects."""

    package = _live_kit_operator_package_payload()
    invalid_ack = _validate_operator_package_header(cmd, package)
    if invalid_ack is not None:
        return HandlerResult(ack=invalid_ack)
    step_key = str(cmd["step_key"])
    slot_key = str(cmd["slot_key"])
    step = _operator_package_step_by_key(package, step_key)
    if step is None:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, f"unknown operator package step: {step_key!r}")
        )
    if str(step["slot_key"]) != slot_key:
        return HandlerResult(
            ack=_error_ack(
                ERR_VALIDATION,
                f"slot_key mismatch for operator package step: {slot_key!r}",
            )
        )
    binding = _operator_package_binding_by_slot(package, slot_key)
    package_export_key = _expected_operator_package_export_key(step=step, binding=binding)
    mismatch_ack = _operator_package_export_key_mismatch_ack(
        step_key=step_key,
        expected_package_export_key=package_export_key,
        provided_package_export_key=str(cmd["package_export_key"]),
    )
    if mismatch_ack is not None:
        return HandlerResult(ack=mismatch_ack)
    rehearsal = _operator_package_step_rehearsal(
        package=package,
        step=step,
        binding=binding,
        snapshot_id=str(cmd["snapshot_id"]),
    )
    return HandlerResult(ack={"ok": True, "operator_package_rehearsal": rehearsal})


async def _handle_rehearse_operator_package_sequence(
    cmd: dict[str, object], _session: CockpitSession
) -> HandlerResult:
    """Rehearse selected operator package steps as one mock-safe sequence."""

    package = _live_kit_operator_package_payload()
    invalid_ack = _validate_operator_package_header(cmd, package)
    if invalid_ack is not None:
        return HandlerResult(ack=invalid_ack)
    requested_step_keys = _operator_package_step_keys_from_command(cmd, package)
    provided_export_keys = _operator_package_export_keys_from_command(cmd)
    snapshot_id = str(cmd["snapshot_id"])
    step_rehearsals: list[dict[str, object]] = []
    for step_key in requested_step_keys:
        step = _operator_package_step_by_key(package, step_key)
        if step is None:
            return HandlerResult(
                ack=_error_ack(ERR_VALIDATION, f"unknown operator package step: {step_key!r}")
            )
        binding = _operator_package_binding_by_slot(package, str(step["slot_key"]))
        package_export_key = _expected_operator_package_export_key(step=step, binding=binding)
        mismatch_ack = _operator_package_export_key_mismatch_ack(
            step_key=step_key,
            expected_package_export_key=package_export_key,
            provided_package_export_key=provided_export_keys.get(step_key),
        )
        if mismatch_ack is not None:
            return HandlerResult(ack=mismatch_ack)
        step_rehearsals.append(
            _operator_package_step_rehearsal(
                package=package,
                step=step,
                binding=binding,
                snapshot_id=snapshot_id,
            )
        )
    rehearsal = {
        "rehearsal_id": f"operator-package-sequence-rehearsal:{package['operator_package_id']}",
        "operator_package_id": str(package["operator_package_id"]),
        "step_count": len(step_rehearsals),
        "step_keys": requested_step_keys,
        "snapshot_id": snapshot_id,
        "mock_safe": True,
        "rehearsal_status": "mock_safe_ready",
        "opened_midi_port": False,
        "sent_midi": False,
        "writes_files": False,
        "blocked_actions": _operator_package_blocked_actions(package),
        "safety_lines": _operator_package_safety_lines(package),
        "step_rehearsals": step_rehearsals,
    }
    return HandlerResult(ack={"ok": True, "operator_package_sequence_rehearsal": rehearsal})


async def _handle_preview_operator_package_apply(
    cmd: dict[str, object], _session: CockpitSession
) -> HandlerResult:
    """Preview applying selected operator package steps without side effects."""

    package = _live_kit_operator_package_payload()
    invalid_ack = _validate_operator_package_header(cmd, package)
    if invalid_ack is not None:
        return HandlerResult(ack=invalid_ack)
    requested_step_keys = _operator_package_step_keys_from_command(cmd, package)
    provided_export_keys = _operator_package_export_keys_from_command(cmd)
    snapshot_id = str(cmd["snapshot_id"])
    apply_steps: list[dict[str, object]] = []
    for order, step_key in enumerate(requested_step_keys, start=1):
        step = _operator_package_step_by_key(package, step_key)
        if step is None:
            return HandlerResult(
                ack=_error_ack(ERR_VALIDATION, f"unknown operator package step: {step_key!r}")
            )
        binding = _operator_package_binding_by_slot(package, str(step["slot_key"]))
        package_export_key = _expected_operator_package_export_key(step=step, binding=binding)
        mismatch_ack = _operator_package_export_key_mismatch_ack(
            step_key=step_key,
            expected_package_export_key=package_export_key,
            provided_package_export_key=provided_export_keys.get(step_key),
        )
        if mismatch_ack is not None:
            return HandlerResult(ack=mismatch_ack)
        apply_steps.append(
            _operator_package_apply_preview_step(
                order=order,
                step=step,
                package_export_key=package_export_key,
            )
        )
    operator_package_id = str(package["operator_package_id"])
    step_count = len(apply_steps)
    preview = {
        "preview_id": (
            f"operator-package-apply-preview:{operator_package_id}:"
            f"{snapshot_id}:{','.join(requested_step_keys)}"
        ),
        "operator_package_id": operator_package_id,
        "snapshot_id": snapshot_id,
        "mock_safe": True,
        "preview_status": "mock_safe_ready",
        "apply_policy": "preview_only",
        "opened_midi_port": False,
        "sent_midi": False,
        "writes_files": False,
        "step_count": step_count,
        "step_keys": requested_step_keys,
        "apply_steps": apply_steps,
        "readiness_checks": _operator_package_apply_preview_readiness_checks(
            operator_package_id=operator_package_id,
            step_count=step_count,
        ),
        "recovery_requirements": _operator_package_recovery_requirements(package),
        "blocked_actions": _operator_package_blocked_actions(package),
        "safety_lines": _operator_package_safety_lines(package),
        "dry_run_summary": _operator_package_apply_preview_summary(step_count=step_count),
    }
    return HandlerResult(ack={"ok": True, "operator_package_apply_preview": preview})


async def _handle_mock_apply_operator_package(
    cmd: dict[str, object], _session: CockpitSession
) -> HandlerResult:
    """Accept selected operator package steps in mock only without side effects."""

    package = _live_kit_operator_package_payload()
    invalid_ack = _validate_operator_package_header(cmd, package)
    if invalid_ack is not None:
        return HandlerResult(ack=invalid_ack)
    requested_step_keys = _operator_package_step_keys_from_command(cmd, package)
    provided_export_keys = _operator_package_export_keys_from_command(cmd)
    snapshot_id = str(cmd["snapshot_id"])
    mock_apply_steps: list[dict[str, object]] = []
    for order, step_key in enumerate(requested_step_keys, start=1):
        step = _operator_package_step_by_key(package, step_key)
        if step is None:
            return HandlerResult(
                ack=_error_ack(ERR_VALIDATION, f"unknown operator package step: {step_key!r}")
            )
        binding = _operator_package_binding_by_slot(package, str(step["slot_key"]))
        package_export_key = _expected_operator_package_export_key(step=step, binding=binding)
        mismatch_ack = _operator_package_export_key_mismatch_ack(
            step_key=step_key,
            expected_package_export_key=package_export_key,
            provided_package_export_key=provided_export_keys.get(step_key),
        )
        if mismatch_ack is not None:
            return HandlerResult(ack=mismatch_ack)
        mock_apply_steps.append(
            _operator_package_mock_apply_step(
                order=order,
                step=step,
                package_export_key=package_export_key,
            )
        )
    operator_package_id = str(package["operator_package_id"])
    step_count = len(mock_apply_steps)
    mock_apply = {
        "mock_apply_id": (
            f"operator-package-mock-apply:{operator_package_id}:"
            f"{snapshot_id}:{','.join(requested_step_keys)}"
        ),
        "operator_package_id": operator_package_id,
        "snapshot_id": snapshot_id,
        "mock_safe": True,
        "mock_apply_status": "mock_applied",
        "apply_policy": "mock_apply_only",
        "opened_midi_port": False,
        "sent_midi": False,
        "writes_files": False,
        "mutated_snapshot": False,
        "applied_send_plan": False,
        "emitted_events": False,
        "step_count": step_count,
        "step_keys": requested_step_keys,
        "mock_apply_steps": mock_apply_steps,
        "readiness_checks": _operator_package_apply_preview_readiness_checks(
            operator_package_id=operator_package_id,
            step_count=step_count,
        ),
        "recovery_requirements": _operator_package_recovery_requirements(package),
        "blocked_actions": _operator_package_blocked_actions(package),
        "safety_lines": _operator_package_safety_lines(package),
        "dry_run_summary": _operator_package_mock_apply_summary(step_count=step_count),
    }
    return HandlerResult(ack={"ok": True, "operator_package_mock_apply": mock_apply})


# ---------------------------------------------------------------------------
# Dispatcher — the single public entry point exported to server.py.
# ---------------------------------------------------------------------------


async def _handle_build_operator_package_receipt(
    cmd: dict[str, object], _session: CockpitSession
) -> HandlerResult:
    """Build a deterministic passive receipt for reviewed operator package steps."""

    package = _live_kit_operator_package_payload()
    invalid_ack = _validate_operator_package_header(cmd, package)
    if invalid_ack is not None:
        return HandlerResult(ack=invalid_ack)
    requested_step_keys = _operator_package_step_keys_from_command(cmd, package)
    provided_export_keys = _operator_package_export_keys_from_command(cmd)
    snapshot_id = str(cmd["snapshot_id"])
    receipt_steps: list[dict[str, object]] = []
    for order, step_key in enumerate(requested_step_keys, start=1):
        step = _operator_package_step_by_key(package, step_key)
        if step is None:
            return HandlerResult(
                ack=_error_ack(ERR_VALIDATION, f"unknown operator package step: {step_key!r}")
            )
        binding = _operator_package_binding_by_slot(package, str(step["slot_key"]))
        package_export_key = _expected_operator_package_export_key(step=step, binding=binding)
        mismatch_ack = _operator_package_export_key_mismatch_ack(
            step_key=step_key,
            expected_package_export_key=package_export_key,
            provided_package_export_key=provided_export_keys.get(step_key),
        )
        if mismatch_ack is not None:
            return HandlerResult(ack=mismatch_ack)
        receipt_step = _operator_package_apply_preview_step(
            order=order,
            step=step,
            package_export_key=package_export_key,
        )
        receipt_step["receipt_status"] = "recorded_for_review"
        receipt_steps.append(receipt_step)
    operator_package_id = str(package["operator_package_id"])
    step_count = len(receipt_steps)
    digest_basis = {
        "operator_package_id": operator_package_id,
        "snapshot_id": snapshot_id,
        "step_keys": requested_step_keys,
        "receipt_steps": receipt_steps,
    }
    receipt = {
        "receipt_id": (
            f"operator-package-receipt:{operator_package_id}:"
            f"{snapshot_id}:{','.join(requested_step_keys)}"
        ),
        "receipt_digest": _operator_package_receipt_digest(digest_basis),
        "operator_package_id": operator_package_id,
        "snapshot_id": snapshot_id,
        "mock_safe": True,
        "receipt_status": "mock_safe_receipt_ready",
        "receipt_policy": "passive_audit_only",
        "opened_midi_port": False,
        "sent_midi": False,
        "writes_files": False,
        "mutated_snapshot": False,
        "applied_send_plan": False,
        "events_emitted": False,
        "step_count": step_count,
        "step_keys": requested_step_keys,
        "receipt_steps": receipt_steps,
        "readiness_checks": [
            *_operator_package_apply_preview_readiness_checks(
                operator_package_id=operator_package_id,
                step_count=step_count,
            ),
            {
                "check": "receipt_mode",
                "status": "passed",
                "writes_files": False,
                "events_emitted": False,
            },
        ],
        "recovery_requirements": _operator_package_recovery_requirements(package),
        "blocked_actions": _operator_package_blocked_actions(package),
        "safety_lines": _operator_package_safety_lines(package),
        "audit_summary": _operator_package_receipt_summary(step_count=step_count),
    }
    return HandlerResult(ack={"ok": True, "operator_package_receipt": receipt})


# ---------------------------------------------------------------------------
# Wave-4 arm / disarm — the in-UI half of the Live-but-Passive model.
#
# The ``arm`` command is the ONLY path that ever opens a real output port,
# and it does so exclusively through the ``senders`` ArmedApply seam:
# confirm + a token checked against the SERVER-minted per-launch ARM
# secret (``CockpitSession.arm_secret``), exact-name output resolution
# (fail-closed), refusal of any port that cannot be closed, and
# auto-disarm on provider error. The mock adapter stays the default;
# unwired sessions never see any of this surface.
#
# The arm secret is a real authentication factor: it is minted by
# ``__main__`` and written 0600, so a caller must be able to read the
# operator's own files to arm. An earlier revision accepted any non-empty
# client string and then derived the "expected" token from that same
# string — ``compare_digest(x, x)`` — which authenticated nothing.
# ---------------------------------------------------------------------------

_ARM_FAILED_FINGERPRINT: Final[str] = "cockpit.arm.failed"
"""Journal fingerprint for a refused/failed explicit arm attempt."""

_ARM_DEVICE_LOST_FINGERPRINT: Final[str] = "cockpit.arm.device_lost"
"""Journal fingerprint for the watchdog's device-gone auto-disarm."""


_ARM_SEND_REFUSED_FINGERPRINT: Final[str] = "cockpit.arm.send_refused"
"""Journal fingerprint for an armed SEND the seam refused."""

_CAPTURE_FAILED_FINGERPRINT: Final[str] = "cockpit.capture.failed"
"""Journal fingerprint for an input-only saved-KIT capture failure."""

_GUARDED_SEND_FAILED_FINGERPRINT: Final[str] = "cockpit.send.guarded_boundary_failed"
"""Journal fingerprint for a guarded-device apply failure."""

_ARMED_SEND_DEVICE_ID: Final[str] = "analog_rytm_mk2"
"""Registered device the cockpit's armed send reports against.

The cockpit is Rytm-only today. The device is passed to the seam purely
for its ``device_id`` (result attribution) and readiness vocabulary — the
wire triples come from the plan's own preflight-resolved packets via
:func:`_send_plan_triples`, never from a device strategy.
"""


def _send_plan_triples(plan: object) -> list[tuple[int, int, int]]:
    """Project a prepared :class:`CockpitSendPlan` into wire triples.

    The seam's :data:`~rytm_randomizer.senders.armed_apply.PlanRenderer`
    for the cockpit. Preflight already resolved every packet's
    ``(channel, control, value)``; this projection transmits exactly those
    and recomputes nothing at the hardware boundary (the SEND contract in
    :meth:`~rytm_randomizer.cockpit.device.adapter.DeviceAdapter.apply_send_plan`).
    """

    if not isinstance(plan, CockpitSendPlan):  # pragma: no cover - defensive
        raise TypeError("armed cockpit send requires a CockpitSendPlan")
    return [(packet.channel, packet.control, packet.value) for packet in plan.packets]


def _armed_send_over_seam(
    session: CockpitSession,
    plan: CockpitSendPlan,
    cmd: Mapping[str, object],
) -> HandlerResult | None:
    """Transmit ``plan`` through the ArmedApply seam; ``None`` when sent.

    This is the **only** way a cockpit SEND reaches hardware. Returning a
    :class:`HandlerResult` means the seam refused and the caller must not
    proceed; returning ``None`` means the bytes went out and the caller
    should update snapshot/history state as usual.

    The command must carry its own ``confirm: true``: "armed" is a session
    state, but every individual write is a separate operator decision, so
    the per-action confirmation is minted here and consumed by
    :meth:`~rytm_randomizer.senders.armed_apply.ArmedApplySession.apply`.

    ``mutates_kit=False`` is passed deliberately and is load-bearing: a
    cockpit SEND is a live-dial CC burst into the device's working RAM,
    reversible by reloading the kit from the device's own memory. It is
    **not** a persistent kit/sound write — those are refused outright by
    the seam (:class:`~rytm_randomizer.senders.armed_apply.KitMutationUnsupportedError`)
    because no capture-before-write or restore path exists. ``save`` /
    ``commit_kit`` remains the un-implemented persistent path.
    """

    from ...senders.armed_apply import ArmedApplyError  # noqa: PLC0415

    armed = session.armed_apply
    if armed is None:  # pragma: no cover - guarded by the caller
        return None
    confirmed_plan_id = cmd.get("send_plan_id")
    if not isinstance(confirmed_plan_id, str) or confirmed_plan_id != plan.plan_id:
        return HandlerResult(
            ack=_error_ack(
                ERR_VALIDATION,
                "armed SEND requires confirmation of the current prepared plan",
            )
        )
    if cmd.get("confirm") is not True:
        return HandlerResult(
            ack=_error_ack(
                ERR_VALIDATION,
                "armed send requires confirm: true (per-action operator confirmation)",
            )
        )

    device = get_device(_ARMED_SEND_DEVICE_ID)
    try:
        armed.confirm(confirmed_plan_id)
        result = armed.apply(
            device,
            plan,
            action_id=plan.plan_id,
            mutates_kit=False,
            renderer=_send_plan_triples,
        )
    except ArmedApplyError as exc:
        # A provider error already auto-disarmed the seam; drop the rest of
        # the armed state so the session is honestly passive again.
        if not armed.is_armed:
            _teardown_armed_state(session)
        partial_outcome = exc.partial_outcome
        if partial_outcome is not None:
            for packet in plan.packets[: partial_outcome.sent_count]:
                get_metrics().record_cc_sent(packet.channel)
        _logger.warning(
            "armed_send_refused",
            extra={
                "exception_type": type(exc).__name__,
                "exception_repr": repr(exc),
                "fingerprint": _ARM_SEND_REFUSED_FINGERPRINT,
                "sent_count": 0 if partial_outcome is None else partial_outcome.sent_count,
                "expected_count": (
                    0 if partial_outcome is None else partial_outcome.expected_count
                ),
            },
        )
        session.error_journal.record(
            _ARM_SEND_REFUSED_FINGERPRINT,
            "armed send refused at the guarded seam",
            context={"plan_id": plan.plan_id},
        )
        get_metrics().record_error(_ARM_SEND_REFUSED_FINGERPRINT)
        session.stage_coordinator.record_send(ANALOG_RYTM_DEVICE_ID, succeeded=False)
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "armed send refused at the guarded seam"),
            events=[
                _build_session_status(session),
                _build_dual_machine_stage_changed(session),
            ],
        )
    if not result.ok:
        _logger.warning(
            "armed_send_refused",
            extra={
                "fingerprint": _ARM_SEND_REFUSED_FINGERPRINT,
                "sent_count": result.sent_count,
                "expected_count": result.expected_count,
                "status": result.status,
            },
        )
        session.error_journal.record(
            _ARM_SEND_REFUSED_FINGERPRINT,
            "armed send refused because the prepared plan was not ready",
            context={"plan_id": plan.plan_id},
        )
        get_metrics().record_error(_ARM_SEND_REFUSED_FINGERPRINT)
        session.stage_coordinator.record_plan(ANALOG_RYTM_DEVICE_ID, ready=False)
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "armed send refused: plan not ready"),
            events=[_build_dual_machine_stage_changed(session)],
        )
    for packet in plan.packets[: result.sent_count]:
        get_metrics().record_cc_sent(packet.channel)
    _logger.info(
        "armed_send_complete",
        extra={
            "send_plan_id": plan.plan_id,
            "sent_count": result.sent_count,
            "expected_count": result.expected_count,
            "status": result.status,
        },
    )
    return None


def _teardown_armed_state(session: CockpitSession) -> None:
    """Return the session to the passive baseline (idempotent).

    Disarms the ArmedApply seam, which closes the one armed output port.
    The device adapter is never swapped on arm any more (the seam owns
    the only output handle), so there is nothing to restore here. Never
    re-arms.

    This is the single teardown entry point every exit path funnels
    through: the ``disarm`` handler, the armed watchdog's device-gone
    auto-disarm, a WebSocket disconnect, and app shutdown
    (:func:`disarm_session_on_teardown`). Idempotent, so overlapping
    teardowns close the port exactly once.
    """

    armed = session.armed_apply
    session.armed_apply = None
    if armed is not None:
        armed.disarm()
    session.stage_coordinator.record_rytm_authority(armed=False)
    _logger.info(
        "cockpit_armed_state_revoked",
        extra={"had_armed_seam": armed is not None},
    )


def disarm_session_on_teardown(session: CockpitSession) -> None:
    """Public teardown hook: drop a session to passive and close its port.

    Wired by the transport and the sidecar entrypoint so an armed session
    can never outlive the thing that armed it:

    * :func:`~rytm_randomizer.cockpit.ws.server.create_app`'s ``/ws``
      endpoint calls it in its ``finally`` — the WS disconnect that used
      to only unregister the queue and cancel the writer now also
      releases the hardware handle. Closing the browser tab with the
      session armed left the port open indefinitely.
    * ``__main__`` registers it as a FastAPI ``shutdown`` handler, so
      Ctrl+C / SIGTERM against uvicorn tears the port down as well.

    Idempotent and exception-free by construction: it delegates to
    :func:`_teardown_armed_state`, whose ``disarm`` swallows a dying
    port's close error. A teardown path must never raise.
    """

    _teardown_armed_state(session)


def build_armed_watchdog(
    session: CockpitSession,
    broadcaster: Callable[[dict[str, object]], object] | None = None,
) -> Callable[[ConnectionState], None]:
    """Build the ConnectionManager notify hook that auto-disarms on loss.

    Wired by ``__main__`` via
    :meth:`~rytm_randomizer.cockpit.device.connection.ConnectionManager.add_notify_hook`.
    When a passive poll observes the device gone while the session is
    armed (phase dropped out of ``listening``, or the armed output port
    vanished from the enumeration), the hook tears the armed state down,
    records a journal entry, and broadcasts a fresh ``session_status``
    fault signal. Reconnecting NEVER re-arms — the operator must run the
    explicit arm sequence again.
    """

    def _on_connection_change(state: ConnectionState) -> None:
        if session.armed_apply is None and not session.device.is_armed:
            return
        armed_port = None
        if session.armed_apply is not None:
            armed_port = session.armed_apply.port_name
        if armed_port is None:
            armed_port = _midi_port(session)
        phase_lost = state.phase not in ("listening", "armed")
        port_lost = armed_port is not None and armed_port not in state.available_outputs
        if not phase_lost and not port_lost:
            return
        _teardown_armed_state(session)
        session.stage_coordinator.record_connection(
            ANALOG_RYTM_DEVICE_ID,
            connected=False,
        )
        session.error_journal.record(
            _ARM_DEVICE_LOST_FINGERPRINT,
            "device disappeared while armed; auto-disarmed",
            context={"phase": state.phase},
        )
        _logger.warning(
            "cockpit_armed_device_lost",
            extra={
                "phase": state.phase,
                "fingerprint": _ARM_DEVICE_LOST_FINGERPRINT,
            },
        )
        get_metrics().record_error(_ARM_DEVICE_LOST_FINGERPRINT)
        if broadcaster is not None:
            broadcaster(_build_session_status(session))
            broadcaster(_build_dual_machine_stage_changed(session))

    return _on_connection_change


_ARM_PORT_REQUIRED: Final[str] = (
    "arm requires an explicit port_name naming one enumerated MIDI output"
)
"""The single refusal text for every unusable ``port_name`` on ``arm``.

Deliberately uniform: which of the four rejection reasons fired (missing,
empty, unknown, ambiguous) is a detail the wire must not leak, and the
operator's remedy is identical in all four cases — pick a port from the
selector.
"""


def _resolve_arm_port_name(cmd: Mapping[str, object]) -> str | None:
    """Resolve the exact output port an ``arm`` command targets, or ``None``.

    **Fail closed, and never guess.** The operator must name the exact
    instrument. With a Rytm and an Analog Four both plugged in, a
    convenience auto-pick ("first Elektron-looking output") can arm the
    wrong machine — so the ConnectionManager's ``selected_output`` is
    deliberately *not* consulted here. That auto-pick still drives the
    passive "listening" display, where guessing wrong is harmless.

    ``None`` (the command must fail) whenever ``port_name`` is missing,
    not a string, empty, absent from the live enumeration, or matches more
    than one enumerated output.

    When no ConnectionManager is registered (unit tests, embedded
    harnesses) there is no enumeration to check against, so a well-formed
    name is taken at face value; the seam's own
    :class:`~rytm_randomizer.senders.hardware.ExactOutputOpener` still
    fails closed against the provider a moment later.
    """

    raw = cmd.get("port_name")
    if not isinstance(raw, str) or not raw:
        return None
    manager = active_connection_manager()
    if manager is None:
        return raw
    matches = [name for name in manager.state.available_outputs if name == raw]
    if len(matches) != 1:
        return None
    return raw


_ARM_UNAVAILABLE_MESSAGE: Final[str] = (  # noqa: S105 — refusal text, not a credential
    "arm is unavailable: no ARM secret is configured for this launch"
)
"""Refusal text when the session has no server-minted ARM secret.

Fail closed: without a secret there is nothing to authenticate the
client's ``arm_token`` against, so arming is simply not offered.
"""

_ARM_REJECTED_MESSAGE: Final[str] = (  # noqa: S105 — refusal text, not a credential
    "arm refused: invalid arm_token"
)
"""Refusal text for a client token that does not match the ARM secret.

Deliberately identical for "empty", "wrong type", and "wrong value" — the
wire must not tell a caller which part of its guess was closer.
"""


def _arm_token_authorised(session: CockpitSession, supplied: object) -> bool:
    """Validate the client's ``arm_token`` against the server's ARM secret.

    The whole point of the check: the expected value comes from
    :attr:`CockpitSession.arm_secret` — server-minted at launch and
    written 0600 — **never** from the command. The previous
    implementation built the expected token from the client's own
    submission and then ran ``compare_digest(x, x)``, which is a
    tautology: any non-empty string armed the device. Nothing was
    authenticated.

    Fails closed on a missing secret (nothing to compare against) and on
    any non-string / empty submission, and uses
    :func:`hmac.compare_digest` so response timing does not leak a
    prefix of the secret.
    """

    secret = session.arm_secret
    if not isinstance(secret, str) or not secret:
        return False
    if not isinstance(supplied, str) or not supplied:
        return False
    return hmac.compare_digest(supplied, secret)


async def _handle_arm(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    """Explicit in-UI arm: server-secret auth + confirm, then the ArmedApply seam."""

    if cmd.get("confirm") is not True:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "arm requires confirm: true (explicit in-UI arm)")
        )
    token = cmd.get("arm_token")
    if not isinstance(token, str) or not token:
        return HandlerResult(ack=_error_ack(ERR_VALIDATION, "arm requires a non-empty arm_token"))
    if session.arm_secret is None:
        # No secret provisioned for this launch -> the transmit capability
        # is not offered at all. Distinguished from a mismatch because the
        # operator's remedy differs (configure the sidecar vs. re-read the
        # secret file), and it leaks nothing about any secret's value.
        _logger.warning(
            "arm_refused_no_secret",
            extra={"fingerprint": _ARM_FAILED_FINGERPRINT},
        )
        session.error_journal.record(
            _ARM_FAILED_FINGERPRINT,
            "arm refused: no ARM secret configured for this launch",
        )
        get_metrics().record_error(_ARM_FAILED_FINGERPRINT)
        return HandlerResult(ack=_error_ack(ERR_VALIDATION, _ARM_UNAVAILABLE_MESSAGE))
    if not _arm_token_authorised(session, token):
        _logger.warning(
            "arm_token_mismatch",
            extra={"fingerprint": _ARM_FAILED_FINGERPRINT},
        )
        session.error_journal.record(
            _ARM_FAILED_FINGERPRINT,
            "arm refused: arm_token did not match the launch ARM secret",
        )
        get_metrics().record_error(_ARM_FAILED_FINGERPRINT)
        return HandlerResult(ack=_error_ack(ERR_VALIDATION, _ARM_REJECTED_MESSAGE))
    if session_is_armed(session):
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "session is already armed; disarm first")
        )
    port_name = _resolve_arm_port_name(cmd)
    if not port_name:
        return HandlerResult(ack=_error_ack(ERR_VALIDATION, _ARM_PORT_REQUIRED))
    provider = session.arm_port_provider
    if provider is None:
        if importlib.util.find_spec("mido") is None:
            return HandlerResult(
                ack=_error_ack(ERR_VALIDATION, "mido is not installed; cannot arm")
            )
        # Lazy import keeps the real-MIDI boundary module out of every
        # session that never arms (mock stays the default).
        from ...mido_provider import build_mido_midi_port_provider  # noqa: PLC0415

        provider = build_mido_midi_port_provider()

    # Local imports keep the armed seam off the passive import path.
    from ...senders.armed_apply import ArmedApplyError, ArmedApplySession  # noqa: PLC0415
    from ...senders.hardware import ExactOutputOpener  # noqa: PLC0415

    # The seam is constructed with the SERVER's secret, never with the
    # client-supplied value. ``token`` has already been proven equal to it
    # above; passing the secret makes that explicit and keeps the seam's
    # own token check a genuine second comparison against server state
    # rather than a restatement of the client's input.
    armed_apply = ArmedApplySession(
        opener=ExactOutputOpener(provider),
        port_name=port_name,
        arm_token=session.arm_secret,
    )
    try:
        armed_apply.arm(token)
    except ArmedApplyError as exc:
        # RR4f: the categorical wire message stays canonical; the full
        # detail goes to the structured log + the error journal.
        _logger.warning(
            "arm_failed",
            extra={
                "exception_type": type(exc).__name__,
                "exception_repr": _redacted_exception_repr(
                    exc,
                    sensitive_value=port_name,
                ),
                "fingerprint": _ARM_FAILED_FINGERPRINT,
            },
        )
        session.error_journal.record(
            _ARM_FAILED_FINGERPRINT,
            "arm refused: output port could not be resolved or opened",
        )
        get_metrics().record_error(_ARM_FAILED_FINGERPRINT)
        return HandlerResult(
            ack=_error_ack(
                ERR_VALIDATION, "arm failed: output port could not be resolved or opened"
            )
        )
    # The device adapter is deliberately NOT swapped for a real-MIDI one.
    # ``armed_apply`` now owns the session's single output port; installing
    # a second adapter here would open a second handle whose sends bypass
    # every gate above (the defect this arm path exists to prevent). The
    # passive adapter keeps modelling snapshot/history state; the seam does
    # the transmitting.
    session.armed_apply = armed_apply
    # Records the operator's INTENT to be live. Survives an involuntary
    # auto-disarm so a later SEND is refused rather than silently
    # downgraded to a mock write (see CockpitSession.hardware_intent).
    session.hardware_intent = True
    session.stage_coordinator.record_connection(
        ANALOG_RYTM_DEVICE_ID,
        connected=True,
    )
    session.stage_coordinator.record_rytm_authority(armed=True)
    return HandlerResult(
        ack={"ok": True, "armed": True, "midi_port": port_name},
        events=[
            _build_session_status(session),
            _build_dual_machine_stage_changed(session),
        ],
    )


async def _handle_disarm(_cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    """Explicit disarm: tear the armed seam down, restore the passive device."""

    if session.armed_apply is None and not session.device.is_armed:
        return HandlerResult(ack=_error_ack(ERR_VALIDATION, "session is not armed"))
    _teardown_armed_state(session)
    # EXPLICIT disarm is the only thing that clears hardware intent: the
    # operator has chosen to go passive, so a subsequent mock SEND is what
    # they asked for. Involuntary auto-disarms deliberately leave the flag
    # set so SEND refuses instead of silently writing to the mock.
    session.hardware_intent = False
    return HandlerResult(
        ack={"ok": True, "armed": False},
        events=[
            _build_session_status(session),
            _build_dual_machine_stage_changed(session),
        ],
    )


async def _handle_diagnostics(_cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    """Read-only health packet: journal + metrics + connection + hints."""

    manager = active_connection_manager()
    connection_state = None if manager is None else manager.state.to_dict()
    payload = build_diagnostics_payload(
        journal=session.error_journal,
        connection_state=connection_state,
    )
    payload["connection_phase"] = _connection_phase(session)
    return HandlerResult(ack={"ok": True, "diagnostics": payload})


# ---------------------------------------------------------------------------
# Wave-4 library commands — injected store, whole-state change events.
# ---------------------------------------------------------------------------


def _library_store_or_none(session: CockpitSession) -> LibraryStore | None:
    """The session's injected library store (``None`` for unwired sessions)."""

    return session.library_store


def _library_unconfigured_ack() -> HandlerResult:
    """The uniform refusal for library commands on an unwired session."""

    return HandlerResult(
        ack=_error_ack(ERR_VALIDATION, "library store is not configured for this session")
    )


def _build_library_changed(store: LibraryStore) -> dict[str, object]:
    """Construct the whole-state ``library_changed`` event payload."""

    return {
        "type": EVENT_LIBRARY_CHANGED,
        "library": {"records": [record.to_dict() for record in store.list_records()]},
    }


async def _handle_library_list(_cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    store = _library_store_or_none(session)
    if store is None:
        return _library_unconfigured_ack()
    records = [record.to_dict() for record in store.list_records()]
    return HandlerResult(ack={"ok": True, "library_records": records})


async def _handle_library_search(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    store = _library_store_or_none(session)
    if store is None:
        return _library_unconfigured_ack()
    query = str(cmd.get("query", ""))
    records = [record.to_dict() for record in store.search(query)]
    return HandlerResult(ack={"ok": True, "library_records": records})


async def _handle_library_tag(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    store = _library_store_or_none(session)
    if store is None:
        return _library_unconfigured_ack()
    record_id = str(cmd["record_id"])
    tags = cmd.get("tags", [])
    if not isinstance(tags, list):
        return HandlerResult(ack=_error_ack(ERR_VALIDATION, "tags must be a list of strings"))
    try:
        record = store.tag(record_id, [str(tag) for tag in cast("list[object]", tags)])
    except ValueError:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, f"unknown library record_id: {record_id!r}")
        )
    return HandlerResult(
        ack={"ok": True, "library_record": record.to_dict()},
        events=[_build_library_changed(store)],
    )


async def _handle_library_delete(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    store = _library_store_or_none(session)
    if store is None:
        return _library_unconfigured_ack()
    record_id = str(cmd["record_id"])
    try:
        deleted = store.delete(record_id)
    except ValueError:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, f"unknown library record_id: {record_id!r}")
        )
    if not deleted:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, f"unknown library record_id: {record_id!r}")
        )
    return HandlerResult(
        ack={"ok": True, "library_record_id": record_id},
        events=[_build_library_changed(store)],
    )


async def _handle_library_import_captures(
    _cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
    store = _library_store_or_none(session)
    if store is None:
        return _library_unconfigured_ack()
    try:
        result = store.import_captures()
    except ValueError:
        return HandlerResult(
            ack=_error_ack(ERR_VALIDATION, "library captures directory is not available")
        )
    events = [_build_library_changed(store)] if result.imported else []
    return HandlerResult(
        ack={"ok": True, "library_import": result.to_dict()},
        events=events,
    )


HandlerFn = Callable[[dict[str, object], CockpitSession], Awaitable[HandlerResult]]

_CORE_HANDLERS: dict[str, HandlerFn] = {
    COMMAND_ANALYZE_PATCH_GENOME: _handle_analyze_patch_genome,
    COMMAND_LIST_CAPTURE_INPUTS: _handle_list_capture_inputs,
    COMMAND_CAPTURE_CURRENT_KIT: _handle_capture_current_kit,
    COMMAND_CLEAR_MUTATION_TARGETS: _handle_clear_mutation_targets,
    COMMAND_SELECT_PROFILE: _handle_select_profile,
    COMMAND_SET_DEPTH: _handle_set_depth,
    COMMAND_SET_A4_TRACK_LOCK: _handle_set_a4_track_lock,
    COMMAND_SET_MUTATION_TARGETS: _handle_set_mutation_targets,
    COMMAND_SET_PAD_LOCK: _handle_set_pad_lock,
    COMMAND_TOGGLE_PREVIEW: _handle_toggle_preview,
    COMMAND_REGEN: _handle_regen,
    COMMAND_PREPARE_SEND_PLAN: _handle_prepare_send_plan,
    COMMAND_SEND: _handle_send,
    COMMAND_SAVE: _handle_save,
    COMMAND_LOAD_SNAPSHOT: _handle_load_snapshot,
    COMMAND_UNDO: _handle_undo,
    COMMAND_EXPORT_PROFILE_MODEL: _handle_export_profile_model,
    COMMAND_REHEARSE_OPERATOR_PACKAGE_STEP: _handle_rehearse_operator_package_step,
    COMMAND_REHEARSE_OPERATOR_PACKAGE_SEQUENCE: _handle_rehearse_operator_package_sequence,
    COMMAND_PREVIEW_OPERATOR_PACKAGE_APPLY: _handle_preview_operator_package_apply,
    COMMAND_MOCK_APPLY_OPERATOR_PACKAGE: _handle_mock_apply_operator_package,
    COMMAND_BUILD_OPERATOR_PACKAGE_RECEIPT: _handle_build_operator_package_receipt,
    COMMAND_ARM: _handle_arm,
    COMMAND_DISARM: _handle_disarm,
    COMMAND_DIAGNOSTICS: _handle_diagnostics,
    COMMAND_LIBRARY_LIST: _handle_library_list,
    COMMAND_LIBRARY_SEARCH: _handle_library_search,
    COMMAND_LIBRARY_TAG: _handle_library_tag,
    COMMAND_LIBRARY_DELETE: _handle_library_delete,
    COMMAND_LIBRARY_IMPORT_CAPTURES: _handle_library_import_captures,
}

#: Backwards-compatibility alias for the legacy ``_HANDLERS`` symbol some
#: tests may import directly. IH5 renamed the core table to
#: :data:`_CORE_HANDLERS` so the registry-of-registries naming reads
#: clearly alongside :func:`_resolve_handler`. Kept as a thin alias rather
#: than dropped wholesale so the rename does not snag downstream importers.
_HANDLERS = _CORE_HANDLERS


def _resolve_handler(cmd_type: str) -> HandlerFn | None:
    """Resolve a command type to its handler, preserving wizard lazy-load.

    IH5: the dispatcher previously hand-branched on
    ``cmd_type.startswith("wizard_")`` to pick between two dispatch
    tables. This helper centralises that decision so :func:`handle_command`
    does a single registry lookup. The wizard module is still imported
    lazily -- only when a ``wizard_*`` command actually lands -- so the
    cockpit boot path that never touches the wizard still does not pay
    the wizard's import cost.

    Returns ``None`` when no handler is registered for ``cmd_type``; the
    dispatcher converts that into an ``ERR_UNKNOWN_COMMAND`` ack.
    """

    if cmd_type in _CORE_HANDLERS:
        return _CORE_HANDLERS[cmd_type]
    if cmd_type.startswith("wizard_"):
        # Lazy import keeps the wizard dispatcher table out of the import
        # graph of cockpit boot paths that never touch the wizard.
        # ``WIZARD_HANDLERS`` is now declared ``Mapping[str, WizardHandlerFn]``
        # — structurally identical to ``HandlerFn`` — so no cast is needed.
        from .wizard_handlers import WIZARD_HANDLERS  # noqa: PLC0415

        return WIZARD_HANDLERS.get(cmd_type)
    return None


async def handle_command(envelope: dict[str, object], session: CockpitSession) -> dict[str, object]:
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
    # OBS O2 — RED metrics. Start the wall-clock here so the duration
    # captures envelope parsing AND handler runtime AND post-handler
    # bookkeeping. The cmd_type label is unknown until after the envelope
    # parse, so the missing-envelope-key path records under the special
    # ``"<malformed>"`` bucket.
    _metrics = get_metrics()
    _t0 = time.perf_counter()
    try:
        # ``cast`` mirrors the historical duck-typed access exactly: a
        # non-dict ``command`` still raises ``TypeError`` on the ``["type"]``
        # subscript, which the handler-exception path classifies below.
        cmd = cast("dict[str, object]", envelope["command"])
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
                "fingerprint": _exc_fingerprint(exc),
                "request_id": request_id,
            },
        )
        _metrics.record_ws_command(
            "<malformed>",
            (time.perf_counter() - _t0) * 1000.0,
            error_code=ERR_MISSING_ENVELOPE_KEY,
        )
        return {
            "request_id": request_id,
            **_error_ack(
                ERR_MISSING_ENVELOPE_KEY,
                f"envelope missing required key: {missing_key!r}",
            ),
        }
    # IH5: single dispatch surface via :func:`_resolve_handler` --
    # collapses the prior inline ``cmd_type.startswith("wizard_")``
    # branch into one registry-of-registries lookup. The wizard table is
    # still imported lazily inside :func:`_resolve_handler` so cockpit
    # boot paths that never touch a ``wizard_*`` command do not pay the
    # wizard's import cost.
    handler = _resolve_handler(cmd_type) if isinstance(cmd_type, str) else None
    # OBS O2 — bucket label for the RED counters. Use the actual cmd_type
    # if it's a string; non-string types collapse to the same "<unknown>"
    # label the operation span uses, so the operator sees one consistent
    # vocabulary across logs and metrics.
    _label = cmd_type if isinstance(cmd_type, str) else "<unknown>"
    if handler is None:
        _metrics.record_ws_command(
            _label,
            (time.perf_counter() - _t0) * 1000.0,
            error_code=ERR_UNKNOWN_COMMAND,
        )
        return {
            "request_id": request_id,
            **_error_ack(ERR_UNKNOWN_COMMAND, f"unknown command: {cmd_type!r}"),
        }
    # OBS O1 — wrap the handler invocation in operation() so every log
    # call inside the handler chain carries this request_id as the
    # op_id correlator. Operators correlating "the cockpit hung when I
    # hit SEND" reports can grep `op_id` in JSON-mode logs and see
    # every breadcrumb the dispatcher + handler + downstream emitted
    # during that one client request — wizard analyzer, atomic_write,
    # signing, verifier, etc.
    op_name = f"ws.{_label}"
    with operation(op_name, logger=_logger, request_id=request_id):
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
            # Wave 4: taxonomy errors also land in the session's bounded
            # error journal so the ``diagnostics`` command can replay the
            # last 50 categorized failures without log access. The
            # fingerprint is the wire-safe taxonomy string (OBS O4);
            # stdlib exceptions have none and are journalled by the
            # structured log only.
            fingerprint = _exc_fingerprint(exc)
            if fingerprint is not None:
                # ``_label`` equals ``cmd_type`` on every path that reaches
                # a handler (a non-string type never resolves a handler).
                session.error_journal.record(
                    fingerprint,
                    message,
                    context={"cmd_type": _label, "code": code},
                )
            _logger.warning(
                "handler_exception",
                extra={
                    "code": code,
                    "cmd_type": cmd_type,
                    "exception_type": type(exc).__name__,
                    "exception_repr": repr(exc),
                    # OBS O4 — when ``exc`` is a :class:`RytmRandomizerError`
                    # subclass (one of the arms of the except tuple above),
                    # this is the stable ``<subsystem>.<verb>.<noun>``
                    # aggregator string an operator greps in logs and a
                    # future Sentry tier groups on. stdlib exceptions in
                    # the same except tuple surface as ``None``.
                    "fingerprint": _exc_fingerprint(exc),
                    "request_id": request_id,
                },
            )
            _metrics.record_ws_command(
                _label,
                (time.perf_counter() - _t0) * 1000.0,
                error_code=code,
            )
            return {"request_id": request_id, **_error_ack(code, message)}
        # Queue events on the session for the caller to drain AFTER it sends
        # the ack on the wire. We cannot await the emitter from here without
        # inverting the ack-first / events-second wire ordering, so the
        # dispatcher hands ownership of the queue to
        # :func:`drain_pending_events` via the real ``pending_events`` field
        # on :class:`CockpitSession`.
        session.pending_events = list(result.events)
        # OBS O2 — record success. If the handler returned an error envelope
        # (ack.ok is False) we still treat it as an error bucket — handlers
        # producing ``{ok: False, code: ...}`` directly (rather than raising)
        # are the same kind of failure from a RED perspective.
        # ``HandlerResult.ack`` is always a dict by type; the ``code`` field
        # only ever carries :data:`WS_ERROR_CODES` strings (``_error_ack``
        # enforces it), so the cast re-states the runtime contract.
        ack_error = cast(
            "str | None",
            result.ack.get("code") if not result.ack.get("ok", True) else None,
        )
        _metrics.record_ws_command(
            _label,
            (time.perf_counter() - _t0) * 1000.0,
            error_code=ack_error,
        )
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
    "build_armed_watchdog",
    "build_connection_changed",
    "drain_pending_events",
    "emit_initial_events",
    "handle_command",
    "resolve_connection_phase",
]
