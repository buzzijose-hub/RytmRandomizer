"""FastAPI app factory + the single ``/ws`` WebSocket endpoint.

The factory pattern (a :func:`create_app` function that takes a
:class:`CockpitSession`) keeps the wiring testable: the test suite
constructs a session, hands it to :func:`create_app`, and uses
``fastapi.testclient.TestClient`` to drive WebSocket round-trips with
zero real network I/O. Production code (``__main__.py``) constructs
the session, calls :func:`create_app`, and hands the result to
``uvicorn.run``.

Endpoint contract
-----------------

The single endpoint at ``/ws`` does three things on every connection:

1. **Accept the upgrade** — required for any WebSocket handshake to
   complete. The FastAPI helper handles the HTTP-101 dance.
2. **Push the bootstrap event quartet** —
   :func:`emit_initial_events` sends ``session_status``,
   ``snapshot_changed``, ``profile_changed``, and ``history_updated``
   so the UI can render a complete first frame.
3. **Enter the command loop** — every ``receive_json`` returns a
   :class:`CommandEnvelope`, the dispatcher (handlers.handle_command)
   builds the ack, the loop sends it back. The loop exits cleanly on
   :class:`WebSocketDisconnect` (the client closed the connection).

The single endpoint matches the spec's "one WebSocket endpoint /ws"
requirement; multiplexing is done at the message-type layer (event
``type`` discriminator + command envelope ``request_id``), not by
multiple URL paths.
"""

from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .handlers import (
    EventEmitter,
    drain_pending_events,
    emit_initial_events,
    handle_command,
)
from .session import CockpitSession


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


def create_app(session: CockpitSession) -> FastAPI:
    """Build a FastAPI app that serves the cockpit WebSocket on ``/ws``.

    Args:
        session: The shared :class:`CockpitSession` every connection drives.
            Phase 1 binds one session per process (multi-tenant deferred).

    Returns:
        A configured :class:`FastAPI` instance. Hand it to
        ``uvicorn.run(app, host=..., port=...)`` to serve.
    """

    app = FastAPI(title="rytm-randomizer-cockpit", version="1.0.0")

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        """The cockpit's single WebSocket endpoint.

        Accepts the connection, sends the bootstrap event quartet, then
        loops on ``receive_json``/``send_json`` pairs until the client
        disconnects.
        """

        await websocket.accept()
        emitter: EventEmitter = _WebSocketEmitter(websocket)
        await emit_initial_events(emitter, session)
        try:
            while True:
                envelope = await websocket.receive_json()
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
