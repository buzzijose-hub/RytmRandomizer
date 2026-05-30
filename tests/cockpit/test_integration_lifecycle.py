"""Integration: connect → initial events (the bootstrap quartet).

The spec mandates that any client connecting to ``/ws`` immediately
receives four event frames before the command loop opens:

1. ``session_status`` — armed/mock pill, unsaved_sends, midi_port.
2. ``snapshot_changed`` — the device's current parameter state.
3. ``profile_changed`` — the active profile (``None`` on first connect).
4. ``history_updated`` — the snapshot history chain + ``current_id``.

This file pins that contract end-to-end across the FastAPI / TestClient
boundary. Subsequent integration tests rely on the same ordering when
they drain via the :func:`cockpit_ws` fixture, so a regression here
fails first and gives the clearest signal.

The Spec reference: see ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"v10 Cockpit Binding to the Protocol" — "Connect: server emits ...".
"""

from __future__ import annotations

import pytest
from cockpit.conftest import collect_initial_events, complete_handshake
from fastapi.testclient import TestClient

from rytm_randomizer.cockpit.ws.protocol import (
    EVENT_HISTORY_UPDATED,
    EVENT_PROFILE_CHANGED,
    EVENT_SESSION_STATUS,
    EVENT_SNAPSHOT_CHANGED,
    WS_SUBPROTOCOL,
)

pytestmark = pytest.mark.fast


def test_initial_events_on_connect(cockpit_client: TestClient) -> None:
    """On connect, server emits session_status, snapshot_changed, profile_changed, history_updated."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws, count=4)

    types = {e["type"] for e in events}
    assert types == {
        EVENT_SESSION_STATUS,
        EVENT_SNAPSHOT_CHANGED,
        EVENT_PROFILE_CHANGED,
        EVENT_HISTORY_UPDATED,
    }


def test_initial_events_order_is_stable(cockpit_client: TestClient) -> None:
    """The bootstrap quartet arrives in the documented order (status → snapshot → profile → history)."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws, count=4)

    types_in_order = [e["type"] for e in events]
    assert types_in_order == [
        EVENT_SESSION_STATUS,
        EVENT_SNAPSHOT_CHANGED,
        EVENT_PROFILE_CHANGED,
        EVENT_HISTORY_UPDATED,
    ]


def test_initial_session_status_marks_mock_mode(cockpit_client: TestClient) -> None:
    """Mock device adapter reports ``mode='mock'``, ``armed=False``, ``midi_port=None``."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws, count=4)

    status = next(e for e in events if e["type"] == EVENT_SESSION_STATUS)
    assert status["mode"] == "mock"
    assert status["armed"] is False
    assert status["midi_port"] is None
    assert status["unsaved_sends"] == 0


def test_initial_snapshot_event_carries_reference_pads(cockpit_client: TestClient) -> None:
    """The bootstrap snapshot event reflects the 12-pad reference layout."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws, count=4)

    snapshot = next(e for e in events if e["type"] == EVENT_SNAPSHOT_CHANGED)["snapshot"]
    pad_ids = [pad["pad_id"] for pad in snapshot["pads"]]
    machines = [pad["machine"] for pad in snapshot["pads"]]
    assert pad_ids == list(range(1, 13))
    assert machines == [
        "BD Hard",
        "SD Classic",
        "CH Closed",
        "OH Open",
        "BT Rim",
        "LT Low",
        "MT Mid",
        "HT High",
        "CP Clap",
        "RS Riser",
        "SY Raw",
        "BD Acoustic",
    ]
    assert snapshot["device"] == "analog_rytm_mk2"


def test_initial_profile_event_is_null_on_fresh_session(cockpit_client: TestClient) -> None:
    """No profile is active on connect; the profile_changed event payload is ``None``."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws, count=4)

    profile = next(e for e in events if e["type"] == EVENT_PROFILE_CHANGED)["profile"]
    assert profile is None


def test_initial_history_event_has_root_entry(cockpit_client: TestClient) -> None:
    """The bootstrap history strip carries the root snapshot as ``current_id``."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws, count=4)

    history = next(e for e in events if e["type"] == EVENT_HISTORY_UPDATED)["history"]
    assert len(history["entries"]) == 1
    assert history["current_id"] == history["entries"][0]["snapshot"]["snapshot_id"]
    assert history["entries"][0]["kind"] == "auto"
    assert history["entries"][0]["parent_id"] is None
