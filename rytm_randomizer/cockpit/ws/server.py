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
   completes.
3. **Push the bootstrap event quartet** —
   :func:`emit_initial_events` sends ``session_status``,
   ``snapshot_changed``, ``profile_changed``, and ``history_updated``
   so the UI can render a complete first frame.
4. **Enter the command loop** — every inbound frame is checked against
   the per-message byte cap (SX1) before parsing; oversize frames are
   rejected with ``{"ok": false, "code": "message_too_large"}`` +
   close code 1009 (message too big). Each accepted command envelope
   is fed through the dispatcher (``handle_command``), the ack is
   written to the wire, then queued events are drained.

The single endpoint matches the spec's "one WebSocket endpoint /ws"
requirement; multiplexing is done at the message-type layer (event
``type`` discriminator + command envelope ``request_id``), not by
multiple URL paths.

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

import hmac
import json
import os
from typing import Final

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .handlers import (
    EventEmitter,
    drain_pending_events,
    emit_initial_events,
    handle_command,
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

_DEFAULT_MAX_MESSAGE_BYTES: Final[int] = 1 * 1024 * 1024
"""Default per-message byte cap — 1 MiB. Override via env var (SX1)."""

_MAX_MESSAGE_BYTES_ENV_VAR: Final[str] = "RYTM_RAND_WS_MAX_MESSAGE_BYTES"
"""Env var an operator may set to raise (or lower) the size cap at boot."""


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


class _WebSocketEmitter:
    """Adapt a FastAPI :class:`WebSocket` to the :class:`EventEmitter` Protocol.

    The handlers module talks to a duck-typed emitter so tests can
    substitute a recorder; in production we wrap the live WebSocket so
    every ``send_event`` becomes a ``send_json`` on the wire.
    """

    def __init__(self, websocket: WebSocket) -> None:
        self._websocket = websocket

    async def send_event(self, event: dict) -> None:
        await self._websocket.send_json(event)


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
    if not isinstance(frame, dict) or frame.get("type") != HELLO_FRAME_TYPE:
        await _reject_handshake(websocket, HANDSHAKE_AUTH_REQUIRED)
        return False
    token = frame.get("token")
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


async def _receive_command(websocket: WebSocket, max_bytes: int) -> dict | None:
    """Read one command envelope, enforcing the per-message size cap.

    Returns the parsed envelope on success, ``None`` if the socket was
    closed (the caller exits its loop), and raises nothing else. On
    oversize or unparseable frames the rejection ack is written and the
    socket is closed with code 1009 (message too big); the caller treats
    a ``None`` return as "no more work to do."
    """

    try:
        raw = await websocket.receive_text()
    except WebSocketDisconnect:
        return None
    if len(raw.encode("utf-8")) > max_bytes:
        await _reject_oversize(websocket)
        return None
    try:
        envelope = json.loads(raw)
    except (TypeError, ValueError):
        # Malformed JSON is funnelled into the dispatcher's existing
        # "missing key" error path so the wire shape stays uniform; the
        # client gets an ``ok: false`` ack and the connection stays open.
        return {"request_id": "", "command": {}}
    if not isinstance(envelope, dict):
        return {"request_id": "", "command": {}}
    return envelope


async def _reject_oversize(websocket: WebSocket) -> None:
    """Ack + close on a size-cap violation (SX1)."""

    try:
        await websocket.send_json({"ok": False, "code": MESSAGE_TOO_LARGE_CODE})
    except (WebSocketDisconnect, RuntimeError):
        return
    try:
        await websocket.close(code=CLOSE_CODE_MESSAGE_TOO_BIG)
    except (WebSocketDisconnect, RuntimeError):
        return


def create_app(session: CockpitSession, *, token: str) -> FastAPI:
    """Build a FastAPI app that serves the cockpit WebSocket on ``/ws``.

    Args:
        session: The shared :class:`CockpitSession` every connection
            drives. Phase 1 binds one session per process
            (multi-tenant deferred).
        token: The per-launch handshake token the client must echo in
            its first ``hello`` frame. Generated by
            ``__main__.main()`` via :func:`secrets.token_urlsafe` and
            captured in the WS endpoint's closure for a constant-time
            comparison on every connect.

    Returns:
        A configured :class:`FastAPI` instance. Hand it to
        ``uvicorn.run(app, host=..., port=...)`` to serve.
    """

    if not isinstance(token, str) or not token:
        # An empty token would make the HMAC comparison pass against the
        # empty string a client could trivially send. Refuse to start
        # rather than ship a broken authenticator.
        raise ValueError("create_app requires a non-empty token (see CODE_REVIEW.md C1)")

    max_message_bytes = _resolve_max_message_bytes()
    app = FastAPI(title="rytm-randomizer-cockpit", version="1.0.0")

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        """The cockpit's single WebSocket endpoint.

        Negotiates the pinned subprotocol, runs the auth handshake,
        sends the bootstrap event quartet, then loops on size-capped
        command frames until the client disconnects.
        """

        await websocket.accept(subprotocol=WS_SUBPROTOCOL)
        if not await _perform_handshake(websocket, token):
            return
        emitter: EventEmitter = _WebSocketEmitter(websocket)
        await emit_initial_events(emitter, session)
        try:
            while True:
                envelope = await _receive_command(websocket, max_message_bytes)
                if envelope is None:
                    return
                # PR 4 dropped the emitter from handle_command's signature
                # (it's only used by drain_pending_events below). PR 1's
                # _receive_command + size-cap stays.
                ack = await handle_command(envelope, session)
                # ack-first, events-second per spec § "The Three Protocols"
                # — drain whatever the handler queued only after the client
                # has the ack and can correlate it to their request.
                await websocket.send_json(ack)
                await drain_pending_events(session, emitter)
        except WebSocketDisconnect:
            # Client closed the connection — normal teardown path; no log
            # noise needed (Uvicorn's access log records the disconnect).
            return

    return app


__all__ = ["create_app"]
