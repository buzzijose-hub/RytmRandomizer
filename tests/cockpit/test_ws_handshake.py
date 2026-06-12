"""Tests for the cockpit WS handshake, subprotocol, and message-size cap.

This module is the dedicated safety net for CODE_REVIEW.md PR 1
findings:

* **C1** — every WebSocket connection must complete an authenticated
  handshake (``{"type": "hello", "token": "<urlsafe>"}``) before any
  cockpit command (or even the bootstrap event set) is permitted.
* **L8** — the server must pin a subprotocol so a casual
  ``new WebSocket(url)`` from a foreign tab fails the upgrade.
* **SX1** — the server must reject oversized frames before they OOM the
  sidecar.
* **C4** — bonus coverage for the wizard ``set_metadata`` three-state
  wire semantics that landed in the same PR, exercised end-to-end via
  the live TestClient (the handler-level unit tests live in
  :mod:`tests.cockpit.test_ws_wizard_handlers`).

Every test uses :class:`fastapi.testclient.TestClient` so the round-trip
exercises the real ``starlette`` WebSocket stack without binding a real
port.
"""

from __future__ import annotations

import json
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from rytm_randomizer.cockpit.data import PadState, Snapshot
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws.protocol import (
    CLOSE_CODE_MESSAGE_TOO_BIG,
    CLOSE_CODE_POLICY_VIOLATION,
    EVENT_HISTORY_UPDATED,
    EVENT_PERFORMANCE_CONSOLE_CHANGED,
    EVENT_PROFILE_CHANGED,
    EVENT_SESSION_STATUS,
    EVENT_SNAPSHOT_CHANGED,
    HANDSHAKE_AUTH_FAILED,
    HANDSHAKE_AUTH_REQUIRED,
    HELLO_FRAME_TYPE,
    MESSAGE_TOO_LARGE_CODE,
    WS_SUBPROTOCOL,
)
from rytm_randomizer.cockpit.ws.server import create_app
from rytm_randomizer.cockpit.ws.session import CockpitSession

pytestmark = pytest.mark.fast

_TOKEN = "test-handshake-token-for-pytest-only"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _snapshot() -> Snapshot:
    return Snapshot(
        snapshot_id="01HXY5Q9PJM0000000000HSHAKE",
        device="analog_rytm_mk2",
        captured_at=datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc),
        pads=(PadState(pad_id=1, machine="BD Hard", params={"tun": 30, "dec": 80, "lev": 110}),),
        scene_slot="A01",
        bpm=124.0,
    )


@pytest.fixture
def session(tmp_path: Path) -> CockpitSession:
    """Build a fresh cockpit session backed by a tmp-path profile registry."""

    initial = _snapshot()
    device = MockDeviceAdapter(initial=initial)
    history = HistoryStore()
    history.initial(initial)
    return CockpitSession(
        profile_registry=ProfileRegistry(profiles_dir=tmp_path),
        history_store=history,
        device=device,
    )


@pytest.fixture
def client(session: CockpitSession) -> Generator[TestClient, None, None]:
    """Spin up a TestClient bound to a freshly-created app with the test token."""

    with TestClient(create_app(session, token=_TOKEN)) as testclient:
        yield testclient


def _hello(token: str) -> dict:
    return {"type": HELLO_FRAME_TYPE, "token": token}


# ---------------------------------------------------------------------------
# AC #4 — subprotocol pinned (L8)
# ---------------------------------------------------------------------------


def test_server_echoes_pinned_subprotocol_on_accept(client: TestClient) -> None:
    """A client that requests ``rytm-rand-cockpit-v1`` sees it accepted back."""

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        assert ws.accepted_subprotocol == WS_SUBPROTOCOL
        # Complete the handshake so the connection teardown is graceful
        # (avoids a noisy "client never authenticated" race in the log).
        ws.send_json(_hello(_TOKEN))
        ws.receive_json()


# ---------------------------------------------------------------------------
# AC #1 — token-based handshake (C1)
# ---------------------------------------------------------------------------


def test_handshake_with_valid_token_unlocks_bootstrap_events(client: TestClient) -> None:
    """Happy path: valid token → ``ok=true`` ack → bootstrap event set flows."""

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        ws.send_json(_hello(_TOKEN))
        ack = ws.receive_json()
        assert ack == {"ok": True}

        # The five bootstrap events arrive in the documented order.
        events = [ws.receive_json() for _ in range(5)]
        assert [e["type"] for e in events] == [
            EVENT_SESSION_STATUS,
            EVENT_SNAPSHOT_CHANGED,
            EVENT_PROFILE_CHANGED,
            EVENT_HISTORY_UPDATED,
            EVENT_PERFORMANCE_CONSOLE_CHANGED,
        ]


def test_handshake_missing_token_returns_auth_required_and_closes(client: TestClient) -> None:
    """First frame omitting ``token`` is rejected as auth_required + close 1008."""

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            ws.send_json({"type": HELLO_FRAME_TYPE})  # token missing
            ack = ws.receive_json()
            assert ack == {"ok": False, "code": HANDSHAKE_AUTH_REQUIRED}
            ws.receive_json()  # triggers the WebSocketDisconnect

    assert excinfo.value.code == CLOSE_CODE_POLICY_VIOLATION


def test_handshake_wrong_token_returns_auth_failed_and_closes(client: TestClient) -> None:
    """A well-formed ``hello`` whose token mismatches → auth_failed + close 1008."""

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            ws.send_json(_hello("definitely-not-the-token"))
            ack = ws.receive_json()
            assert ack == {"ok": False, "code": HANDSHAKE_AUTH_FAILED}
            ws.receive_json()

    assert excinfo.value.code == CLOSE_CODE_POLICY_VIOLATION


def test_handshake_first_frame_not_a_dict_is_rejected(client: TestClient) -> None:
    """A JSON list as the first frame is treated as a malformed handshake."""

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            ws.send_text(json.dumps(["not", "a", "dict"]))
            ack = ws.receive_json()
            assert ack == {"ok": False, "code": HANDSHAKE_AUTH_REQUIRED}
            ws.receive_json()

    assert excinfo.value.code == CLOSE_CODE_POLICY_VIOLATION


def test_handshake_first_frame_wrong_type_is_rejected(client: TestClient) -> None:
    """A dict whose ``type`` is not ``hello`` is treated as malformed."""

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            ws.send_json({"type": "not-a-hello", "token": _TOKEN})
            ack = ws.receive_json()
            assert ack == {"ok": False, "code": HANDSHAKE_AUTH_REQUIRED}
            ws.receive_json()

    assert excinfo.value.code == CLOSE_CODE_POLICY_VIOLATION


def test_handshake_non_string_token_is_rejected(client: TestClient) -> None:
    """A ``hello`` frame whose ``token`` is not a string is malformed (C1)."""

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            ws.send_json({"type": HELLO_FRAME_TYPE, "token": 12345})
            ack = ws.receive_json()
            assert ack == {"ok": False, "code": HANDSHAKE_AUTH_REQUIRED}
            ws.receive_json()


def test_handshake_malformed_json_first_frame_is_rejected(client: TestClient) -> None:
    """Invalid JSON as the first frame is treated as malformed (C1)."""

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            ws.send_text("{this is not json")
            ack = ws.receive_json()
            assert ack == {"ok": False, "code": HANDSHAKE_AUTH_REQUIRED}
            ws.receive_json()


def test_create_app_rejects_empty_token() -> None:
    """An empty token would be guessable — ``create_app`` must refuse to start."""

    snap = _snapshot()
    sess = CockpitSession(
        profile_registry=ProfileRegistry(profiles_dir=Path(".")),
        history_store=HistoryStore(),
        device=MockDeviceAdapter(initial=snap),
    )
    with pytest.raises(ValueError):
        create_app(sess, token="")


# ---------------------------------------------------------------------------
# AC #5 — message size cap (SX1)
# ---------------------------------------------------------------------------


def test_oversize_message_after_handshake_is_rejected(
    session: CockpitSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 2 MiB frame is rejected with ``message_too_large`` + close 1009 (SX1).

    Uses an env-var-shrunk cap (8 KiB) so the test stays fast and does
    not actually allocate megabytes per round trip. Exercises the same
    code path as the 1 MiB default.
    """

    monkeypatch.setenv("RYTM_RAND_WS_MAX_MESSAGE_BYTES", str(8 * 1024))
    app = create_app(session, token=_TOKEN)

    with TestClient(app) as testclient, pytest.raises(WebSocketDisconnect) as excinfo:
        with testclient.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            ws.send_json(_hello(_TOKEN))
            assert ws.receive_json() == {"ok": True}
            for _ in range(5):
                ws.receive_json()  # drain bootstrap

            # Build a request envelope whose JSON serialization comfortably
            # exceeds 8 KiB.
            big_body = "A" * (16 * 1024)
            ws.send_json(
                {
                    "request_id": "req-big",
                    "command": {"type": "set_pad_lock", "pad_id": 1, "locked": True, "x": big_body},
                }
            )
            ack = ws.receive_json()
            assert ack == {"ok": False, "code": MESSAGE_TOO_LARGE_CODE}
            ws.receive_json()  # disconnect

    assert excinfo.value.code == CLOSE_CODE_MESSAGE_TOO_BIG


def test_under_cap_message_after_handshake_is_processed(client: TestClient) -> None:
    """A regular-sized frame after handshake routes to the dispatcher normally."""

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        ws.send_json(_hello(_TOKEN))
        assert ws.receive_json() == {"ok": True}
        for _ in range(5):
            ws.receive_json()  # drain bootstrap

        ws.send_json(
            {
                "request_id": "req-small",
                "command": {"type": "set_pad_lock", "pad_id": 1, "locked": True},
            }
        )
        ack = ws.receive_json()
        assert ack["ok"] is True
        assert ack["request_id"] == "req-small"


# ---------------------------------------------------------------------------
# AC #6 — C4: wizard set_metadata three-state wire semantics over the live socket.
# ---------------------------------------------------------------------------


def _handshake_and_drain_bootstrap(ws: object) -> None:
    """Authenticate and drain bootstrap so the test starts at the command cursor."""

    ws.send_json(_hello(_TOKEN))  # type: ignore[attr-defined]
    ack = ws.receive_json()  # type: ignore[attr-defined]
    assert ack == {"ok": True}
    for _ in range(5):
        ws.receive_json()  # type: ignore[attr-defined]


def _start_wizard_with_initial_metadata(ws: object) -> None:
    ws.send_json({"request_id": "req-start", "command": {"type": "wizard_start"}})  # type: ignore[attr-defined]
    ws.receive_json()  # type: ignore[attr-defined]
    ws.receive_json()  # type: ignore[attr-defined]  # wizard_state_changed
    ws.send_json(  # type: ignore[attr-defined]
        {
            "request_id": "req-meta-init",
            "command": {
                "type": "wizard_set_metadata",
                "name": "initial",
                "description": "initial-desc",
            },
        }
    )
    ws.receive_json()  # type: ignore[attr-defined]
    ws.receive_json()  # type: ignore[attr-defined]  # wizard_state_changed


def test_wizard_set_metadata_missing_key_leaves_state_unchanged_over_ws(
    client: TestClient,
) -> None:
    """Sending ``wizard_set_metadata`` without ``name`` preserves the prior value (C4)."""

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _handshake_and_drain_bootstrap(ws)
        _start_wizard_with_initial_metadata(ws)

        # Envelope intentionally carries neither ``name`` nor ``description``.
        ws.send_json({"request_id": "req-no-fields", "command": {"type": "wizard_set_metadata"}})
        ack = ws.receive_json()
        ws.receive_json()  # wizard_state_changed

        assert ack["ok"] is True
        assert ack["state"]["name"] == "initial"
        assert ack["state"]["description"] == "initial-desc"


def test_wizard_set_metadata_null_name_clears_field_over_ws(client: TestClient) -> None:
    """Explicit ``null`` on ``name`` clears the field on the wire (C4 fix)."""

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _handshake_and_drain_bootstrap(ws)
        _start_wizard_with_initial_metadata(ws)

        ws.send_json(
            {
                "request_id": "req-null-name",
                "command": {"type": "wizard_set_metadata", "name": None},
            }
        )
        ack = ws.receive_json()
        ws.receive_json()

        assert ack["ok"] is True
        # Cleared (renderers treat "" as "no value set").
        assert ack["state"]["name"] == ""
        # Description was not touched.
        assert ack["state"]["description"] == "initial-desc"


def test_wizard_set_metadata_string_name_sets_field_over_ws(client: TestClient) -> None:
    """A plain string value sets the field verbatim (the unchanged happy path)."""

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _handshake_and_drain_bootstrap(ws)
        _start_wizard_with_initial_metadata(ws)

        ws.send_json(
            {
                "request_id": "req-set-name",
                "command": {"type": "wizard_set_metadata", "name": "renamed"},
            }
        )
        ack = ws.receive_json()
        ws.receive_json()

        assert ack["ok"] is True
        assert ack["state"]["name"] == "renamed"
        assert ack["state"]["description"] == "initial-desc"
