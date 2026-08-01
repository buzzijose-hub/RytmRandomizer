"""FastAPI app factory + the single ``/ws`` WebSocket endpoint.

The factory pattern (a :func:`create_app` function that takes a
:class:`CockpitSession` plus a per-launch handshake ``token``) keeps the
wiring testable: the test suite constructs a session, generates a known
token, hands both to :func:`create_app`, and uses
``fastapi.testclient.TestClient`` to drive WebSocket round-trips with
zero real network I/O. Production code (``__main__.py``) constructs the
session, generates the token via :func:`secrets.token_urlsafe`, calls
:func:`create_app`, and hands the resulting :class:`FastAPI` to
``uvicorn.run``.

Endpoint contract
-----------------

The single endpoint at ``/ws`` performs **four** steps on every connection:

1. **Negotiate the upgrade with the pinned subprotocol** —
   :data:`WS_SUBPROTOCOL` (``"rytm-rand-cockpit-v1"``). Casual
   ``new WebSocket(url)`` connections from a browser tab omit the
   subprotocol and fail the upgrade before our handler runs (L8).
2. **Handshake** — the client's FIRST frame must be
   ``{"type": "hello", "token": "<urlsafe>"}``. The token is compared
   against the per-launch token loaded at server boot with
   :func:`hmac.compare_digest`. A missing / malformed / mismatched
   token is rejected with ``{"ok": false, "code": "auth_required" |
   "auth_failed"}`` and the socket is closed with policy-violation
   code 1008 (C1). No cockpit command can fire until handshake
   completes. The handshake frames are exchanged directly on the
   socket — the outbound queue does not exist until authentication
   succeeds, so an unauthenticated peer can never occupy a queue slot.
3. **Enqueue the bootstrap event set** —
   :func:`emit_initial_events` pushes ``session_status``,
   ``snapshot_changed``, ``profile_changed``, ``history_updated``, and
   ``performance_console_changed`` onto the connection's outbound
   queue so the UI can render a complete first frame.
4. **Enter the transport loops** — the connection splits into two
   concurrent halves:

   * The **reader** (this coroutine) consumes inbound frames: every
     frame is checked against the per-message byte cap (SX1) before
     parsing; oversize frames enqueue ``{"ok": false, "code":
     "message_too_large"}`` tagged with close code 1009. Each accepted
     command envelope is fed through the dispatcher
     (``handle_command``), the ack is enqueued, then the events the
     handler queued on the session are drained into the same queue.
   * The **writer** (a per-connection task) drains the outbound queue
     to ``send_json`` in strict FIFO order. Because ack + events enter
     the queue back-to-back with no intervening scheduling point, the
     spec's "ack first, then events" wire ordering is preserved
     byte-for-byte — while server-side emitters can ALSO push events
     between command cycles without waiting for a client frame.

The single endpoint matches the spec's "one WebSocket endpoint /ws"
requirement; multiplexing is done at the message-type layer (event
``type`` discriminator + command envelope ``request_id``), not by
multiple URL paths.

Armed-state teardown
--------------------

Arming is an in-UI, per-session operator decision made over this
transport, and the armed session owns an exclusive hardware output port.
Two teardown paths therefore call
:func:`~rytm_randomizer.cockpit.ws.handlers.disarm_session_on_teardown`:
the endpoint's ``finally`` (client disconnect — closing the tab must not
leave the port open) and a FastAPI ``shutdown`` handler (Ctrl+C /
SIGTERM against uvicorn). Both are idempotent, and neither re-arms:
after a reconnect the session is passive until the operator arms again.

Push-capable transport (Wave 2b)
--------------------------------

Every authenticated connection owns one bounded :class:`ConnectionQueue`
registered in the app-level :class:`ConnectionRegistry` (exposed as
``app.state.connection_registry``). ALL outbound frames — bootstrap
events, command acks, post-ack events, and server-side pushes — flow
through that queue, and the writer task is the only code path that
calls ``send_json``. Two coroutines can therefore never interleave a
frame mid-connection.

Server-side emitters (the Wave-3 ConnectionManager and the live MIDI
monitor) call :meth:`ConnectionRegistry.broadcast_event`. The call is
non-blocking and thread-safe: from within the serving event loop it
enqueues directly; from any other thread it marshals onto the loop via
``call_soon_threadsafe``.

Overflow policy: queues are bounded at :data:`DEFAULT_QUEUE_MAXSIZE`
frames. When a slow client falls behind, the OLDEST queued frame is
dropped (drop-oldest, so the newest state always wins) and the drop is
recorded through the observability logger. Enqueueing never blocks the
reader or a broadcaster.

The per-connection queue replaces the old single
``session.pending_events``-to-wire hand-off as the transport buffer;
``pending_events`` itself survives unchanged as the handler-facing
compatibility surface (see :class:`CockpitSession`), and the reader
drains it into the connection's own queue synchronously after each
dispatch so concurrent connections can no longer clobber each other.

Why the message-size cap reads raw text first
---------------------------------------------

``WebSocket.receive_json`` buffers the entire frame into memory before
parsing — a hostile client could stream a gigabyte JSON to OOM the
sidecar. We call :meth:`WebSocket.receive_text` instead and check the
character length against :data:`_DEFAULT_MAX_MESSAGE_BYTES` (or the env
override) *before* :func:`json.loads`. The character-vs-byte distinction
is a slight under-count for multi-byte characters (e.g. emoji) but the
defaults give the cap so much headroom (1 MiB) that the difference is
operationally irrelevant.
"""

from __future__ import annotations

import asyncio
import contextlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Final, cast

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from ...observability.logging import get_logger
from .handlers import (
    EventEmitter,
    disarm_session_on_teardown,
    drain_pending_events,
    emit_initial_events,
    handle_command,
    resolve_connection_phase,
    session_is_armed,
)
from .protocol import (
    CLOSE_CODE_MESSAGE_TOO_BIG,
    CLOSE_CODE_POLICY_VIOLATION,
    HANDSHAKE_AUTH_FAILED,
    HANDSHAKE_AUTH_REQUIRED,
    HELLO_FRAME_TYPE,
    MESSAGE_TOO_LARGE_CODE,
    WS_SUBPROTOCOL,
)
from .session import CockpitSession

_logger = get_logger(__name__)
"""Module logger for the cockpit WS server (auth handshake, size-cap,
transport-loop lifecycle, outbound-queue drops). Bound here so PR O1
(request_id correlation) and PR O6 (arch tests on hot-path loggers) can
wire their structured events without touching this file's imports. See
``OBSERVABILITY_REVIEW.md`` Phase 5."""

_DEFAULT_MAX_MESSAGE_BYTES: Final[int] = 1 * 1024 * 1024
"""Default per-message byte cap — 1 MiB. Override via env var (SX1)."""

_MAX_MESSAGE_BYTES_ENV_VAR: Final[str] = "RYTM_RAND_WS_MAX_MESSAGE_BYTES"
"""Env var an operator may set to raise (or lower) the size cap at boot."""

APP_VERSION: Final[str] = "1.0.0"
"""The cockpit sidecar's app version — surfaced by ``GET /health``."""

DEFAULT_QUEUE_MAXSIZE: Final[int] = 256
"""Default per-connection outbound-queue bound (frames, not bytes).

Sized for the live MIDI monitor's worst realistic burst: a full-kit
mutation emits well under a hundred state events, so 256 frames of
headroom means a healthy client never sees a drop while a wedged client
cannot pin unbounded memory. Tests inject a smaller bound through
:class:`ConnectionRegistry` to exercise the drop-oldest policy cheaply.
"""


def _resolve_max_message_bytes() -> int:
    """Return the per-message byte cap, honouring the env-var override.

    The env var is parsed exactly once per :func:`create_app` call. Tests
    that want to exercise a small cap call :func:`create_app` after
    setting the env var; production code reads the operator's choice at
    sidecar start. Non-positive or unparseable values fall back to the
    default rather than crashing the boot path (the cap is defence in
    depth, not the authentication boundary).
    """

    raw = os.environ.get(_MAX_MESSAGE_BYTES_ENV_VAR)
    if raw is None:
        return _DEFAULT_MAX_MESSAGE_BYTES
    try:
        parsed = int(raw)
    except ValueError:
        return _DEFAULT_MAX_MESSAGE_BYTES
    if parsed <= 0:
        return _DEFAULT_MAX_MESSAGE_BYTES
    return parsed


@dataclass(frozen=True)
class _OutboundItem:
    """One frame queued for the writer task, optionally carrying a close.

    ``close_code`` is ``None`` for ordinary frames. When set, the writer
    sends the frame, closes the socket with the given code, and exits —
    this is how the reader's size-cap rejection reaches the wire without
    the reader ever calling ``send_json`` itself (single-writer rule).
    """

    frame: dict[str, object]
    close_code: int | None = None


class ConnectionQueue:
    """Bounded per-connection outbound queue with a drop-oldest policy.

    All frames a connection will ever send (bootstrap events, acks,
    post-ack events, server pushes, the size-cap rejection) flow through
    this queue in FIFO order; the writer task is the sole consumer.

    Overflow never blocks a producer: when the bound is hit, the OLDEST
    queued frame is dropped (newest state wins) and the drop is logged
    through the observability logger. Once a close-tagged frame has been
    enqueued the queue refuses further frames — the connection is
    winding down and anything else would be sent into a closing socket.

    Must be constructed on the serving event loop (registration happens
    inside the endpoint coroutine); the captured loop is what makes
    :meth:`put_frame_threadsafe` safe to call from any thread.
    """

    def __init__(self, *, maxsize: int = DEFAULT_QUEUE_MAXSIZE) -> None:
        self._maxsize = maxsize
        self._queue: asyncio.Queue[_OutboundItem] = asyncio.Queue()
        self._loop = asyncio.get_running_loop()
        self._closing = False
        self._dropped = 0

    @property
    def size(self) -> int:
        """Number of frames currently queued (bounded by ``maxsize``)."""

        return self._queue.qsize()

    @property
    def dropped_count(self) -> int:
        """Total frames dropped on this connection (overflow + post-close)."""

        return self._dropped

    def put_frame(self, frame: dict[str, object], *, close_code: int | None = None) -> None:
        """Enqueue one outbound frame without ever blocking the caller.

        Args:
            frame: The JSON-serialisable payload the writer will
                ``send_json``.
            close_code: When not ``None``, the writer closes the socket
                with this code immediately after sending ``frame`` and
                exits; the queue then refuses all further frames.
        """

        if self._closing:
            # A close-tagged frame is already queued — the writer will
            # tear the socket down after flushing it. Anything enqueued
            # now could never be delivered; drop it audibly instead of
            # growing a queue nobody will drain.
            self._dropped += 1
            _logger.warning(
                "ws_outbound_frame_dropped",
                extra={
                    "drop_reason": "queue_closing",
                    "dropped_frame_type": str(frame.get("type", "<ack>")),
                    "queue_maxsize": self._maxsize,
                },
            )
            return
        if close_code is not None:
            self._closing = True
        while self._queue.qsize() >= self._maxsize:
            # Drop-oldest: the client is not draining fast enough, so
            # the stalest frame is the least valuable one. The loop (vs
            # a single pop) keeps the invariant even if maxsize was
            # lowered between puts.
            dropped = self._queue.get_nowait()
            self._dropped += 1
            _logger.warning(
                "ws_outbound_frame_dropped",
                extra={
                    "drop_reason": "queue_full",
                    "dropped_frame_type": str(dropped.frame.get("type", "<ack>")),
                    "queue_maxsize": self._maxsize,
                },
            )
        self._queue.put_nowait(_OutboundItem(frame=frame, close_code=close_code))

    def put_frame_threadsafe(self, frame: dict[str, object]) -> None:
        """Enqueue an ordinary frame from any thread, never blocking.

        From within the serving event loop this is a direct
        :meth:`put_frame`; from any other thread (e.g. a MIDI callback
        thread or a test's main thread) the put is marshalled onto the
        connection's loop via ``call_soon_threadsafe`` so the
        :class:`asyncio.Queue` internals are only ever touched on their
        own loop.
        """

        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is self._loop:
            self.put_frame(frame)
        else:
            self._loop.call_soon_threadsafe(self.put_frame, frame)

    async def get(self) -> _OutboundItem:
        """Await and return the next outbound item (writer task only)."""

        return await self._queue.get()


class ConnectionRegistry:
    """The server-owned registry of one :class:`ConnectionQueue` per connection.

    Owned by :func:`create_app` (one registry per app instance, exposed
    as ``app.state.connection_registry``). The endpoint registers a
    fresh queue after a successful handshake and unregisters it on
    teardown; server-side emitters fan events out to every live
    connection via :meth:`broadcast_event` without knowing anything
    about sockets or sessions.
    """

    def __init__(self, *, queue_maxsize: int = DEFAULT_QUEUE_MAXSIZE) -> None:
        self._queue_maxsize = queue_maxsize
        self._queues: dict[int, ConnectionQueue] = {}
        self._next_connection_id = 1

    @property
    def connection_count(self) -> int:
        """Number of currently registered (live, authenticated) connections."""

        return len(self._queues)

    def register(self) -> tuple[int, ConnectionQueue]:
        """Create + track a fresh queue; return ``(connection_id, queue)``.

        Called from the endpoint coroutine (on the serving loop) after a
        successful handshake — the queue captures that loop for its
        thread-safe put path.
        """

        connection_id = self._next_connection_id
        self._next_connection_id += 1
        queue = ConnectionQueue(maxsize=self._queue_maxsize)
        self._queues[connection_id] = queue
        return connection_id, queue

    def unregister(self, connection_id: int) -> None:
        """Forget a connection's queue. Idempotent — teardown paths may race."""

        self._queues.pop(connection_id, None)

    def broadcast_event(self, event: dict[str, object]) -> int:
        """Push one event to every live connection; return the fan-out count.

        Non-blocking and thread-safe (delegates to
        :meth:`ConnectionQueue.put_frame_threadsafe` per connection).
        Slow clients shed the oldest frame per the queue's drop policy —
        one wedged tab can never stall the broadcaster or its siblings.
        """

        queues = list(self._queues.values())
        for queue in queues:
            queue.put_frame_threadsafe(event)
        return len(queues)


class _QueueEmitter:
    """Adapt a :class:`ConnectionQueue` to the :class:`EventEmitter` Protocol.

    The handlers module talks to a duck-typed emitter so tests can
    substitute a recorder; in production every ``send_event`` becomes a
    non-blocking enqueue that the writer task flushes to the wire.

    ``send_event`` deliberately contains **no await points**: the reader
    calls ``drain_pending_events(session, emitter)`` immediately after
    ``handle_command`` returns, and because this emitter never yields to
    the event loop, the ``session.pending_events`` hand-off is atomic
    with respect to every other connection's reader — the multi-
    connection clobbering caveat the old single-list transport carried
    is structurally gone.
    """

    def __init__(self, queue: ConnectionQueue) -> None:
        self._queue = queue

    async def send_event(self, event: dict[str, object]) -> None:
        self._queue.put_frame(event)


async def _perform_handshake(websocket: WebSocket, expected_token: str) -> bool:
    """Run the auth handshake; return ``True`` iff the client is authenticated.

    Wire contract (CODE_REVIEW.md PR 1 — C1):

    * The first frame MUST be a JSON object of shape
      ``{"type": "hello", "token": "<urlsafe>"}``.
    * The token MUST equal ``expected_token`` under
      :func:`hmac.compare_digest` (constant-time comparison — naive
      ``==`` leaks timing).

    Rejection paths (each closes the socket with code 1008 after writing
    a typed ack so a programmatic client can branch on the ``code``):

    * **Missing key, wrong type, or non-string token** → ``code:
      auth_required``. We treat "well-formed but wrong shape" as
      "no auth attempted" — the operator's mental model is "I have no
      credentials in hand," not "I tried and failed."
    * **Well-formed ``hello`` but token mismatch** →
      ``code: auth_failed``. This is the only path that reveals "the
      token you sent didn't match"; the constant-time check prevents an
      attacker from using response timing to reconstruct the token.
    * **Client disconnects before sending any frame** → return ``False``;
      the caller skips the bootstrap and exits cleanly.
    """

    try:
        raw = await websocket.receive_text()
    except WebSocketDisconnect:
        return False
    try:
        frame = json.loads(raw)
    except (TypeError, ValueError):
        await _reject_handshake(websocket, HANDSHAKE_AUTH_REQUIRED)
        return False
    if not isinstance(frame, dict):
        await _reject_handshake(websocket, HANDSHAKE_AUTH_REQUIRED)
        return False
    hello = cast("dict[str, object]", frame)
    if hello.get("type") != HELLO_FRAME_TYPE:
        await _reject_handshake(websocket, HANDSHAKE_AUTH_REQUIRED)
        return False
    token = hello.get("token")
    if not isinstance(token, str):
        await _reject_handshake(websocket, HANDSHAKE_AUTH_REQUIRED)
        return False
    if not hmac.compare_digest(token, expected_token):
        await _reject_handshake(websocket, HANDSHAKE_AUTH_FAILED)
        return False
    await websocket.send_json({"ok": True})
    return True


async def _reject_handshake(websocket: WebSocket, code: str) -> None:
    """Write the rejection ack and close the socket with policy-violation 1008.

    The two-step (send ack, then close) is required so the client can
    actually read the ``code`` discriminator on the way out — closing
    first would race the ack into a buffer the client never drains.

    This is the one place outside the writer task that writes to the
    socket: at handshake time the connection has no queue and no writer
    yet, so the single-writer rule is trivially satisfied.
    """

    try:
        await websocket.send_json({"ok": False, "code": code})
    except (WebSocketDisconnect, RuntimeError):
        # The client may have disconnected between receive_text and
        # send_json. RuntimeError covers "Cannot call send once a close
        # message has been sent" if the connection is already half-closed.
        return
    try:
        await websocket.close(code=CLOSE_CODE_POLICY_VIOLATION)
    except (WebSocketDisconnect, RuntimeError):
        return


def _parse_envelope(raw: str) -> dict[str, object]:
    """Parse one under-cap inbound frame into a command envelope.

    Malformed JSON and non-object JSON are funnelled into the
    dispatcher's existing "missing key" error path so the wire shape
    stays uniform; the client gets an ``ok: false`` ack and the
    connection stays open.
    """

    try:
        envelope = json.loads(raw)
    except (TypeError, ValueError):
        return {"request_id": "", "command": {}}
    if not isinstance(envelope, dict):
        return {"request_id": "", "command": {}}
    return cast("dict[str, object]", envelope)


async def _writer_loop(websocket: WebSocket, queue: ConnectionQueue) -> None:
    """Drain the connection's outbound queue onto the wire, in FIFO order.

    The sole ``send_json`` call site for an authenticated connection —
    acks, events, and server pushes all serialise through here, which is
    what makes concurrent server-side emits safe (no interleaved frames)
    and preserves the ack-then-events ordering byte-for-byte.

    Exit conditions:

    * A close-tagged item — send the frame, close with its code, return
      (the size-cap rejection path, SX1).
    * The socket dies mid-send — the client is gone; return and let the
      reader observe the same disconnect.
    * Cancellation by the endpoint's teardown (normal client disconnect).
    """

    while True:
        item = await queue.get()
        try:
            await websocket.send_json(item.frame)
        except (WebSocketDisconnect, RuntimeError):
            return
        if item.close_code is None:
            continue
        try:
            await websocket.close(code=item.close_code)
        except (WebSocketDisconnect, RuntimeError):
            # Closing an already-half-closed socket is a no-op failure;
            # the rejection frame above still made it out (or the client
            # is gone and nobody is reading either way).
            pass
        return


async def _reader_loop(
    websocket: WebSocket,
    *,
    session: CockpitSession,
    queue: ConnectionQueue,
    emitter: EventEmitter,
    max_bytes: int,
) -> bool:
    """Consume inbound command frames until disconnect or size-cap breach.

    Returns ``True`` when a close-tagged rejection was enqueued (the
    writer will flush it and exit on its own — the caller should await
    the writer rather than cancel it) and ``False`` on a plain client
    disconnect.

    Per-command sequence: size cap (SX1) → parse → ``handle_command`` →
    enqueue ack → drain the handler's queued events into the same
    queue. The ack + events enqueues happen with no intervening await
    that yields to the event loop, so (a) FIFO delivery preserves the
    spec's ack-first / events-second contract exactly, and (b) the
    shared ``session.pending_events`` hand-off cannot be clobbered by a
    sibling connection's reader.
    """

    while True:
        try:
            raw = await websocket.receive_text()
        except WebSocketDisconnect:
            # Client closed the connection — normal teardown path; no log
            # noise needed (Uvicorn's access log records the disconnect).
            return False
        if len(raw.encode("utf-8")) > max_bytes:
            # Ack + close on a size-cap violation (SX1). Routed through
            # the queue so the writer stays the only sender; the tagged
            # close_code makes the writer tear the socket down with
            # 1009 (message too big) right after the ack flushes.
            queue.put_frame(
                {"ok": False, "code": MESSAGE_TOO_LARGE_CODE},
                close_code=CLOSE_CODE_MESSAGE_TOO_BIG,
            )
            return True
        envelope = _parse_envelope(raw)
        ack = await handle_command(envelope, session)
        # ack-first, events-second per spec § "The Three Protocols" —
        # both enter the FIFO queue back-to-back, so the client sees the
        # ack it can correlate to its request before any state update.
        queue.put_frame(ack)
        await drain_pending_events(session, emitter)


def create_app(
    session: CockpitSession,
    *,
    token: object,
    connection_registry: ConnectionRegistry | None = None,
) -> FastAPI:
    """Build a FastAPI app that serves the cockpit WebSocket on ``/ws``.

    Args:
        session: The shared :class:`CockpitSession` every connection
            drives. Phase 1 binds one session per process
            (multi-tenant deferred).
        token: The per-launch handshake token the client must echo in
            its first ``hello`` frame. Generated by
            ``__main__.main()`` via :func:`secrets.token_urlsafe` and
            captured in the WS endpoint's closure for a constant-time
            comparison on every connect. Typed ``object`` so the
            fail-closed ``isinstance`` guard below stays genuine runtime
            validation against misconfigured boot wiring.
        connection_registry: Optionally inject the per-connection queue
            registry (tests use a small ``queue_maxsize``; the Wave-3
            ConnectionManager will hold a reference for pushes). When
            ``None``, a fresh default-bounded registry is created. The
            registry is always exposed as ``app.state.connection_registry``.

    Returns:
        A configured :class:`FastAPI` instance. Hand it to
        ``uvicorn.run(app, host=..., port=...)`` to serve.
    """

    if not isinstance(token, str) or not token:
        # An empty token would make the HMAC comparison pass against the
        # empty string a client could trivially send. Refuse to start
        # rather than ship a broken authenticator.
        raise ValueError("create_app requires a non-empty token (see CODE_REVIEW.md C1)")
    expected_token = token

    max_message_bytes = _resolve_max_message_bytes()
    registry = connection_registry if connection_registry is not None else ConnectionRegistry()
    app = FastAPI(title="rytm-randomizer-cockpit", version=APP_VERSION)
    app.state.connection_registry = registry

    # Justified suppression: FastAPI's route decorator registers the
    # closure with the framework — the framework is the only caller, so
    # Pyright's "not accessed" is a false positive for decorated routes.
    @app.get("/health")
    async def health() -> dict[str, object]:  # pyright: ignore[reportUnusedFunction]
        """Loopback, token-free, read-only liveness probe (Wave 4).

        Deliberately unauthenticated: it exposes no command surface and
        no secrets — just enough for the Tauri shell (or an operator's
        ``curl``) to confirm the sidecar is up, which mode the one
        session is in, and the current passive connection phase. The
        WS handshake token stays the sole gate on every state-changing
        surface.
        """

        return {
            "version": APP_VERSION,
            "mode": "live" if session_is_armed(session) else "mock",
            "connection_phase": resolve_connection_phase(session),
        }

    # Justified suppression: same decorated-route false positive as
    # ``health`` above — FastAPI owns the only call site.
    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:  # pyright: ignore[reportUnusedFunction]
        """The cockpit's single WebSocket endpoint.

        Negotiates the pinned subprotocol, runs the auth handshake,
        registers the connection's outbound queue, enqueues the
        bootstrap event set, then runs the reader loop with a
        concurrent writer task until the client disconnects (or a
        size-cap rejection closes the socket).
        """

        await websocket.accept(subprotocol=WS_SUBPROTOCOL)
        if not await _perform_handshake(websocket, expected_token):
            return
        connection_id, queue = registry.register()
        emitter: EventEmitter = _QueueEmitter(queue)
        writer_task = asyncio.create_task(_writer_loop(websocket, queue))
        try:
            await emit_initial_events(emitter, session)
            close_enqueued = await _reader_loop(
                websocket,
                session=session,
                queue=queue,
                emitter=emitter,
                max_bytes=max_message_bytes,
            )
            if close_enqueued:
                # The writer owns flushing the rejection + close (1009);
                # wait for it so the frames actually reach the wire
                # before teardown cancels anything.
                await writer_task
        finally:
            registry.unregister(connection_id)
            writer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await writer_task
            # Deterministic teardown of the armed hardware handle, but ONLY
            # when this was the last connection. Arming is an in-UI operator
            # decision; when the LAST transport goes away there is no
            # operator left to disarm, so an armed session would otherwise
            # sit holding the device's exclusive output port until the
            # process exited.
            #
            # The count check is load-bearing: one CockpitSession is shared
            # by every connection (see create_app), so disarming
            # unconditionally let a SIBLING connection tear down the armed
            # port of a still-open, actively-performing one — e.g. closing a
            # second diagnostics tab killed the live set's output mid-song.
            # ``registry.unregister`` above already removed this connection,
            # so a zero count means nobody is left.
            #
            # Never auto-re-arms on reconnect — the operator must run the
            # explicit arm sequence again.
            if registry.connection_count == 0:
                disarm_session_on_teardown(session)

    def _disarm_on_shutdown() -> None:
        """App-lifecycle teardown of the armed hardware handle.

        Covers Ctrl+C / SIGTERM against uvicorn and any shutdown that
        does not go through a client disconnect (e.g. the session was
        armed by an embedded harness and no client ever connected).
        Idempotent with the endpoint's ``finally``.
        """

        disarm_session_on_teardown(session)

    app.router.add_event_handler("shutdown", _disarm_on_shutdown)

    return app


__all__ = [
    "APP_VERSION",
    "DEFAULT_QUEUE_MAXSIZE",
    "ConnectionQueue",
    "ConnectionRegistry",
    "create_app",
]
