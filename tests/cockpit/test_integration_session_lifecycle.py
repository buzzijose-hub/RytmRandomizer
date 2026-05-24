"""Integration: WebSocket session lifecycle — disconnect / reconnect / concurrent clients.

The cockpit's :class:`CockpitSession` is **per-process**, not per-connection
(Phase 1 scope per ``rytm_randomizer.cockpit.ws.session``). That means:

* When a client disconnects and reconnects, the new connection observes the
  same session state — pad locks set in connection #1 are still set when
  connection #2 starts; ``unsaved_sends`` keeps its accumulated count;
  history pointer and saved entries survive the round-trip.
* Two clients connected at the same time talk to one session — a state
  mutation on connection A's commands becomes visible to a fresh connection
  B's bootstrap events.

These tests pin both invariants end-to-end across the FastAPI/TestClient
boundary. They complement :mod:`tests.cockpit.test_integration_lifecycle`
(which covers the bootstrap event quartet) by exercising the *across-
connections* lifecycle the per-command-flow tests cannot reach.

Spec reference: see ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"The Three Protocols" — "Phase 1 binds one session per process".
"""

from __future__ import annotations

import pytest
from cockpit.conftest import (
    collect_initial_events,
    drain_events,
    prepare_send_plan,
    send_cmd,
)
from fastapi.testclient import TestClient

from rytm_randomizer.cockpit.ws.protocol import (
    EVENT_HISTORY_UPDATED,
    EVENT_SESSION_STATUS,
    EVENT_SNAPSHOT_CHANGED,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Disconnect → reconnect — state persists across the gap.
# ---------------------------------------------------------------------------


def test_pad_locks_persist_across_reconnect(cockpit_client: TestClient) -> None:
    """A pad lock set in connection #1 is still set on the bootstrap of connection #2."""

    # Connection #1: set pad 3 locked, then close.
    with cockpit_client.websocket_connect("/ws") as ws:
        collect_initial_events(ws, count=4)
        ack = send_cmd(ws, "set_pad_lock", pad_id=3, locked=True)
        assert ack["ok"] is True

    # Connection #2: same session, lock should still be set.
    # We verify indirectly by arming a SEND and checking pad 3 is unchanged.
    with cockpit_client.websocket_connect("/ws") as ws:
        collect_initial_events(ws, count=4)
        send_cmd(ws, "select_profile", profile_id="scene-industrial")
        drain_events(ws, 1)
        send_cmd(ws, "set_depth", depth=0.64)
        prepare_send_plan(ws)
        send_cmd(ws, "send")
        events = drain_events(ws, 5)

    snapshot = next(e for e in events if e["type"] == EVENT_SNAPSHOT_CHANGED)["snapshot"]
    pad3 = next(p for p in snapshot["pads"] if p["pad_id"] == 3)
    # The lock persisted; pad 3's params remain the seed values.
    assert pad3["params"] == {"tun": 50, "dec": 70, "lev": 95}


def test_unsaved_sends_persists_across_reconnect(cockpit_client: TestClient) -> None:
    """The ``unsaved_sends`` counter survives the disconnect/reconnect cycle."""

    # Connection #1: do one SEND, then disconnect.
    with cockpit_client.websocket_connect("/ws") as ws:
        collect_initial_events(ws, count=4)
        send_cmd(ws, "select_profile", profile_id="scene-industrial")
        drain_events(ws, 1)
        send_cmd(ws, "set_depth", depth=0.55)
        prepare_send_plan(ws)
        send_cmd(ws, "send")
        drain_events(ws, 5)

    # Connection #2: the bootstrap ``session_status`` carries the preserved count.
    with cockpit_client.websocket_connect("/ws") as ws:
        bootstrap = collect_initial_events(ws, count=4)

    status = next(e for e in bootstrap if e["type"] == EVENT_SESSION_STATUS)
    assert status["unsaved_sends"] == 1


def test_history_chain_persists_across_reconnect(cockpit_client: TestClient) -> None:
    """The snapshot chain (root + sends) survives a reconnect — the strip rehydrates."""

    # Connection #1: SEND twice → chain of 3 entries (root + 2 sends).
    with cockpit_client.websocket_connect("/ws") as ws:
        collect_initial_events(ws, count=4)
        send_cmd(ws, "select_profile", profile_id="scene-industrial")
        drain_events(ws, 1)
        send_cmd(ws, "set_depth", request_id="req-d-1", depth=0.45)
        prepare_send_plan(ws, request_id="req-prepare-1")
        send_cmd(ws, "send", request_id="req-s-1")
        drain_events(ws, 5)
        send_cmd(ws, "set_depth", request_id="req-d-2", depth=0.6)
        prepare_send_plan(ws, request_id="req-prepare-2")
        send_cmd(ws, "send", request_id="req-s-2")
        drain_events(ws, 5)

    # Connection #2: the bootstrap history event reflects all 3 entries.
    with cockpit_client.websocket_connect("/ws") as ws:
        bootstrap = collect_initial_events(ws, count=4)

    history = next(e for e in bootstrap if e["type"] == EVENT_HISTORY_UPDATED)["history"]
    assert len(history["entries"]) == 3


def test_saved_entry_persists_across_reconnect(cockpit_client: TestClient) -> None:
    """A SAVE done in connection #1 is reflected in connection #2's bootstrap."""

    with cockpit_client.websocket_connect("/ws") as ws:
        collect_initial_events(ws, count=4)
        ack = send_cmd(ws, "save", label="boot-kit")
        assert ack["ok"] is True
        drain_events(ws, 2)

    with cockpit_client.websocket_connect("/ws") as ws:
        bootstrap = collect_initial_events(ws, count=4)

    history = next(e for e in bootstrap if e["type"] == EVENT_HISTORY_UPDATED)["history"]
    saved = next(e for e in history["entries"] if e["kind"] == "saved")
    assert saved["label"] == "boot-kit"


def test_clean_disconnect_does_not_leak_pending_events(
    cockpit_client: TestClient,
) -> None:
    """Disconnecting between command + drain doesn't crash subsequent connections."""

    # Connection #1: send a command but disconnect before draining its events.
    with cockpit_client.websocket_connect("/ws") as ws:
        collect_initial_events(ws, count=4)
        send_cmd(ws, "select_profile", profile_id="scene-industrial")
        # NOTE: deliberately do NOT drain_events(ws, 1) — close mid-stream.

    # Connection #2: bootstrap still works; the leftover events from #1
    # are bound to that closed socket and do not bleed into the new one.
    with cockpit_client.websocket_connect("/ws") as ws:
        bootstrap = collect_initial_events(ws, count=4)

    assert {e["type"] for e in bootstrap} == {
        EVENT_SESSION_STATUS,
        EVENT_SNAPSHOT_CHANGED,
        "profile_changed",
        EVENT_HISTORY_UPDATED,
    }


# ---------------------------------------------------------------------------
# Two concurrent clients — both see the same shared session state.
# ---------------------------------------------------------------------------


def test_two_concurrent_clients_see_same_bootstrap_snapshot(
    cockpit_client: TestClient,
) -> None:
    """Two clients connecting at the same time both bootstrap the same snapshot id."""

    with (
        cockpit_client.websocket_connect("/ws") as ws_a,
        cockpit_client.websocket_connect("/ws") as ws_b,
    ):
        events_a = collect_initial_events(ws_a, count=4)
        events_b = collect_initial_events(ws_b, count=4)

    snap_a = next(e for e in events_a if e["type"] == EVENT_SNAPSHOT_CHANGED)["snapshot"]
    snap_b = next(e for e in events_b if e["type"] == EVENT_SNAPSHOT_CHANGED)["snapshot"]
    assert snap_a["snapshot_id"] == snap_b["snapshot_id"]


def test_concurrent_clients_share_session_state_after_command(
    cockpit_client: TestClient,
) -> None:
    """A SAVE issued by client A is observable on client B's next bootstrap."""

    with cockpit_client.websocket_connect("/ws") as ws_a:
        collect_initial_events(ws_a, count=4)
        send_cmd(ws_a, "save", label="from-client-a")
        drain_events(ws_a, 2)

        # Open a brand-new connection while the first is still alive.
        with cockpit_client.websocket_connect("/ws") as ws_b:
            events_b = collect_initial_events(ws_b, count=4)

    history_b = next(e for e in events_b if e["type"] == EVENT_HISTORY_UPDATED)["history"]
    saved_b = next(e for e in history_b["entries"] if e["kind"] == "saved")
    assert saved_b["label"] == "from-client-a"


def test_concurrent_clients_independent_command_loops(cockpit_client: TestClient) -> None:
    """Each connection has its own command loop; acks correlate per connection."""

    with (
        cockpit_client.websocket_connect("/ws") as ws_a,
        cockpit_client.websocket_connect("/ws") as ws_b,
    ):
        collect_initial_events(ws_a, count=4)
        collect_initial_events(ws_b, count=4)

        ack_a = send_cmd(ws_a, "set_pad_lock", request_id="req-a", pad_id=1, locked=True)
        ack_b = send_cmd(ws_b, "set_pad_lock", request_id="req-b", pad_id=2, locked=True)

    # Per-connection request_ids never cross over.
    assert ack_a["request_id"] == "req-a"
    assert ack_b["request_id"] == "req-b"
    assert ack_a["ok"] is True
    assert ack_b["ok"] is True
