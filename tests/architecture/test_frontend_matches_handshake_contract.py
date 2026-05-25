"""The TypeScript WS client must honour the backend's handshake contract.

This test exists because PR #113's E2E run failed five wizard journeys
(all timing out on the ``cockpit-root`` selector) for a single root
cause: the desktop frontend's WebSocket client at
``desktop/web/src/ws/client.ts`` had drifted away from the cockpit
backend's handshake contract pinned in
:mod:`rytm_randomizer.cockpit.ws.protocol`.

Specifically, two halves of the contract were missing on the wire:

1. The client opened with ``new WebSocket(url)`` — no subprotocol
   argument — so the FastAPI endpoint at
   ``rytm_randomizer/cockpit/ws/server.py:286-288`` refused the
   upgrade (it requires the pinned ``rytm-rand-cockpit-v1``
   subprotocol per CODE_REVIEW.md L8 / defence-in-depth).
2. ``handleOpen`` flipped status straight to ``connected`` without
   sending the mandatory ``{"type": "hello", "token": "<urlsafe>"}``
   first frame the server demands per CODE_REVIEW.md C1 (the
   handshake-token check). The server then closed the socket with
   policy-violation code 1008 and the UI never received the
   bootstrap event quartet — hence every wizard E2E timing out on
   the cockpit boot marker.

A Python-only architecture test reads the TypeScript source as text
(we are not running tsc / jest from pytest) and asserts on it. We're
not type-checking the frontend; we are verifying the **wire-contract
symbols** the backend defines actually appear in the frontend client.
If a contributor renames the subprotocol or removes the hello frame
on either side, one of these two tests fails with a clear message
that points the contributor at the matching backend constant.

The constants are read live from
:mod:`rytm_randomizer.cockpit.ws.protocol` (not duplicated as
string literals here) so a rename on the Python side automatically
moves the pin — preventing the same drift bug from re-occurring with
the test silently green.

See also:
* ``rytm_randomizer/cockpit/ws/protocol.py`` (:data:`WS_SUBPROTOCOL`,
  :data:`HELLO_FRAME_TYPE`) — the wire-format authority.
* ``rytm_randomizer/cockpit/ws/server.py:286-288`` — the server-side
  enforcement point both halves of the handshake feed into.
* ``tests/architecture/test_no_unauthenticated_ws_endpoints.py`` —
  the matching guard that prevents the backend half from regressing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer.cockpit.ws.protocol import HELLO_FRAME_TYPE, WS_SUBPROTOCOL

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WS_CLIENT_TS: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src" / "ws" / "client.ts"
WS_PROTOCOL_TS: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src" / "ws" / "protocol.ts"

# Matches ``new WebSocket(<ident>, <ident>`` — the two-argument form that
# passes a subprotocol. Single-arg ``new WebSocket(url)`` (the broken
# pre-PR-113 shape) does NOT match. We use simple identifier classes for
# the arguments because the call site uses local variables (``url``,
# ``protocols`` / ``WS_SUBPROTOCOL``) rather than inline expressions.
_TWO_ARG_WEBSOCKET_CTOR: Final[re.Pattern[str]] = re.compile(
    r"new WebSocket\(\s*[A-Za-z0-9_]+\s*,\s*[A-Za-z0-9_]+"
)

# Matches ``JSON.stringify({ ... type: 'hello' ...`` or with double
# quotes. Also accepts ``type: HELLO_FRAME_TYPE`` (the type-safe
# constant the client imports from ``./protocol``). The ``[^}]*`` is
# intentionally non-greedy-ish — we stop at the first closing brace so
# we don't accidentally span multiple object literals.
_HELLO_FRAME_STRINGIFY: Final[re.Pattern[str]] = re.compile(
    r"JSON\.stringify\(\s*\{[^}]*type:\s*(?:['\"]hello['\"]|HELLO_FRAME_TYPE)"
)


def _read_ws_client_source() -> str:
    """Return the on-disk text of the TypeScript WS client.

    Raises ``AssertionError`` with a clear pointer if the file moved —
    the location is a structural contract of the desktop shell and a
    rename would also need this test updated.
    """

    assert WS_CLIENT_TS.is_file(), (
        f"Expected the desktop WS client at {WS_CLIENT_TS.relative_to(PROJECT_ROOT)} "
        "but the file is missing. Either restore it, or update "
        "tests/architecture/test_frontend_matches_handshake_contract.py to "
        "point at the new location (and update its docstring to explain why)."
    )
    return WS_CLIENT_TS.read_text(encoding="utf-8")


def test_ws_client_ts_negotiates_subprotocol() -> None:
    """The TS client must request the pinned WS subprotocol on connect.

    Regression guard: a previous client shipped a
    ``defaultWebSocketFactory`` that called ``new WebSocket(url)`` with
    no subprotocol argument. The server rejects the upgrade in that
    case (L8 defence-in-depth) and every cockpit event surface —
    including the wizard's bootstrap quartet — never fires. The five
    wizard E2E timeouts on ``cockpit-root`` all trace back to this one
    missing argument.

    This test asserts two things on the TS source:

    1. The exact subprotocol string from
       :data:`rytm_randomizer.cockpit.ws.protocol.WS_SUBPROTOCOL`
       appears literally somewhere reachable from the client
       (so a backend rename automatically fails the test until the
       frontend follows).
    2. The ``new WebSocket(`` constructor call uses the two-argument
       form (``new WebSocket(url, subprotocol)``) — the only shape
       that survives the server's handshake.
    """

    source = _read_ws_client_source()
    # The literal lives in protocol.ts (the TS counterpart of
    # ``rytm_randomizer/cockpit/ws/protocol.py``) — client.ts may import
    # ``WS_SUBPROTOCOL`` as a symbol and never spell the literal itself.
    protocol_source = WS_PROTOCOL_TS.read_text(encoding="utf-8") if WS_PROTOCOL_TS.is_file() else ""

    rel = WS_CLIENT_TS.relative_to(PROJECT_ROOT).as_posix()
    protocol_rel = WS_PROTOCOL_TS.relative_to(PROJECT_ROOT).as_posix()
    assert WS_SUBPROTOCOL in source or WS_SUBPROTOCOL in protocol_source, (
        f"frontend missing WS subprotocol literal — neither {rel} nor "
        f"{protocol_rel} contains the pinned subprotocol string "
        f"{WS_SUBPROTOCOL!r} required by the backend handshake (see "
        "rytm_randomizer/cockpit/ws/protocol.py::WS_SUBPROTOCOL and the "
        "enforcement point in rytm_randomizer/cockpit/ws/server.py). "
        "Fix: export ``WS_SUBPROTOCOL`` from desktop/web/src/ws/protocol.ts "
        "(or define it in client.ts) and pass it as the second argument to "
        "``new WebSocket(url, WS_SUBPROTOCOL)`` in defaultWebSocketFactory."
    )

    assert _TWO_ARG_WEBSOCKET_CTOR.search(source) is not None, (
        f"frontend missing WebSocket subprotocol argument — {rel} contains "
        "a ``new WebSocket(...)`` call but not in the two-argument form "
        "``new WebSocket(url, subprotocol)``. Without the subprotocol "
        "argument the server's L8 defence-in-depth check rejects the "
        "upgrade before our handshake runs — every cockpit event then "
        "fails to bootstrap (this is the PR #113 wizard E2E regression). "
        "Fix: change ``new WebSocket(url)`` to ``new WebSocket(url, "
        f"{WS_SUBPROTOCOL!r})`` in defaultWebSocketFactory."
    )


def test_ws_client_ts_sends_hello_frame_on_open() -> None:
    """The TS client must send a ``hello`` frame as its first message.

    Regression guard: a previous ``handleOpen`` called
    ``setStatus('connected')`` and immediately returned — never
    sending the ``{"type":"hello","token":"<urlsafe>"}`` frame the
    server demands (C1 handshake-token check at
    ``rytm_randomizer/cockpit/ws/server.py:286-288``). The server
    closed the socket with policy-violation 1008 and the cockpit
    bootstrap event quartet never reached the UI.

    This test asserts the TS source contains a ``JSON.stringify`` of
    an object literal whose ``type`` is the
    :data:`rytm_randomizer.cockpit.ws.protocol.HELLO_FRAME_TYPE`
    constant — the only first-frame shape the server accepts.
    """

    source = _read_ws_client_source()

    rel = WS_CLIENT_TS.relative_to(PROJECT_ROOT).as_posix()

    # Cross-check the constant: if the backend ever renames it away
    # from the literal "hello", this assertion fires first and tells
    # the contributor to update the regex below in lockstep. (The
    # regex hard-codes ``'hello'`` because TS string-literal matching
    # against a Python value isn't worth the indirection — but the
    # cross-check keeps the two in sync.)
    assert HELLO_FRAME_TYPE == "hello", (
        "HELLO_FRAME_TYPE on the backend is no longer the literal 'hello'. "
        "Update the regex in test_ws_client_ts_sends_hello_frame_on_open "
        "to match the new value (and update the TS client to send the new "
        "type as its first frame)."
    )

    assert _HELLO_FRAME_STRINGIFY.search(source) is not None, (
        f"frontend missing hello-frame send — {rel} does not contain a "
        "``JSON.stringify({ type: 'hello', ... })`` call. The server "
        f"requires the first frame on /ws to be a {HELLO_FRAME_TYPE!r} "
        "envelope carrying the per-launch token "
        "(rytm_randomizer/cockpit/ws/server.py:286-288); without it the "
        "socket is closed with code 1008 and the cockpit bootstrap event "
        "quartet never fires. This is the PR #113 wizard E2E regression "
        "(five tests timed out on ``cockpit-root``). Fix: in handleOpen, "
        "call ``sock.send(JSON.stringify({ type: 'hello', token }))`` "
        "BEFORE flipping status to 'connected'."
    )
