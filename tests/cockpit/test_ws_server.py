"""Integration tests for ``rytm_randomizer.cockpit.ws.server`` — the WebSocket endpoint.

These tests use FastAPI's :class:`fastapi.testclient.TestClient` to
exercise the ``/ws`` endpoint end-to-end without spinning up a real
uvicorn process. The TestClient's ``websocket_connect`` context manager
mimics a real WebSocket round-trip:

* On enter, the bootstrap event set (session_status, snapshot_changed,
  profile_changed, history_updated, performance_console_changed) arrives
  synchronously.
* Sending a command envelope via ``send_json`` triggers the dispatcher
  and the matching ack + event(s) arrive in order.

Each test exercises one operator-facing flow per the spec's interaction
examples (depth change, send, undo, etc.) so a regression in the
end-to-end wiring fails loudly here even if the unit tests stay green.

These tests aim for 100% branch coverage on
``rytm_randomizer/cockpit/ws/server.py``.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rytm_randomizer.cockpit.data import (
    PadState,
    ProfileModel,
    Snapshot,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws.protocol import (
    EVENT_HISTORY_UPDATED,
    EVENT_MUTATION_PREVIEWED,
    EVENT_PERFORMANCE_CONSOLE_CHANGED,
    EVENT_PROFILE_CHANGED,
    EVENT_SEND_PLAN_CHANGED,
    EVENT_SESSION_STATUS,
    EVENT_SNAPSHOT_CHANGED,
    WS_SUBPROTOCOL,
)
from rytm_randomizer.cockpit.ws.server import create_app
from rytm_randomizer.cockpit.ws.session import CockpitSession

from .conftest import TEST_WS_TOKEN, complete_handshake

pytestmark = pytest.mark.fast


_FIXED_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _snapshot(snapshot_id: str = "01HXY5Q9PJM0000000000000A") -> Snapshot:
    return Snapshot(
        snapshot_id=snapshot_id,
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": 30, "dec": 80, "lev": 110}),
            PadState(pad_id=2, machine="SD Acoustic", params={"tun": 40, "dec": 60, "lev": 100}),
        ),
        scene_slot="A01",
        bpm=124.0,
    )


def _profile(profile_id: str = "profile-test") -> ProfileModel:
    return ProfileModel(
        profile_id=profile_id,
        name="test-profile",
        kind="user",
        model_version="1.0.0",
        traits=(StyleTrait(name="t1", value=0.6),),
        pad_mappings=(
            TraitPadWeight(trait="t1", pad_id=1, weight=0.5),
            TraitPadWeight(trait="t1", pad_id=2, weight=0.3),
        ),
        transition_curve="linear",
        source_summary="test fixture",
    )


@pytest.fixture
def session_factory(tmp_path: Path):
    """Return a builder that constructs a fresh session per test."""

    def _build(profile: ProfileModel | None = None) -> CockpitSession:
        device = MockDeviceAdapter(initial=_snapshot())
        history = HistoryStore()
        history.initial(device.capture_snapshot())
        registry = ProfileRegistry(profiles_dir=tmp_path)
        if profile is not None:
            registry.save(profile)
        return CockpitSession(profile_registry=registry, history_store=history, device=device)

    return _build


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _recv_initial_events(ws) -> list[dict]:
    """Run the handshake then drain the five bootstrap events.

    Per CODE_REVIEW.md PR 1 finding C1, the cockpit WS endpoint now
    requires a handshake before bootstrap fires. Folding the handshake
    into this helper keeps every existing test in this file working
    against the hardened endpoint without per-call edits.
    """

    complete_handshake(ws)
    return [ws.receive_json() for _ in range(5)]


def _send_command(ws, request_id: str, cmd_type: str, **body) -> dict:
    """Send a command envelope, return the ack frame (first ``receive_json``)."""

    ws.send_json({"request_id": request_id, "command": {"type": cmd_type, **body}})
    return ws.receive_json()


def _drain(ws, n: int) -> list[dict]:
    return [ws.receive_json() for _ in range(n)]


def _prepare_send_plan(ws, request_id: str = "req-prepare") -> dict:
    ack = _send_command(ws, request_id, "prepare_send_plan")
    if ack.get("ok") is not True:
        raise AssertionError(f"prepare_send_plan failed: {ack}")
    if ack["send_plan"]["ready"] is not True:
        raise AssertionError(f"prepare_send_plan blocked: {ack['send_plan']}")
    _drain(ws, 1)
    return ack


# ---------------------------------------------------------------------------
# Connect-time bootstrap event set.
# ---------------------------------------------------------------------------


def test_connect_emits_five_initial_events_in_order(session_factory) -> None:
    session = session_factory()
    app = create_app(session, token=TEST_WS_TOKEN)
    client = TestClient(app)

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        events = _recv_initial_events(ws)

    types_emitted = [e["type"] for e in events]
    assert types_emitted == [
        EVENT_SESSION_STATUS,
        EVENT_SNAPSHOT_CHANGED,
        EVENT_PROFILE_CHANGED,
        EVENT_HISTORY_UPDATED,
        EVENT_PERFORMANCE_CONSOLE_CHANGED,
    ]
    assert events[0]["mode"] == "mock"  # MockDeviceAdapter
    assert events[2]["profile"] is None  # No active profile yet


# ---------------------------------------------------------------------------
# select_profile flow.
# ---------------------------------------------------------------------------


def test_select_profile_command_emits_profile_changed(session_factory) -> None:
    profile = _profile()
    session = session_factory(profile=profile)
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        ack = _send_command(ws, "req-1", "select_profile", profile_id=profile.profile_id)
        events_after = _drain(ws, 1)

    assert ack == {"request_id": "req-1", "ok": True}
    assert events_after[0]["type"] == EVENT_PROFILE_CHANGED
    assert events_after[0]["profile"]["profile_id"] == profile.profile_id


# ---------------------------------------------------------------------------
# set_depth and toggle_preview flows.
# ---------------------------------------------------------------------------


def test_set_depth_with_preview_off_returns_candidate_no_event(session_factory) -> None:
    profile = _profile()
    session = session_factory(profile=profile)
    session.active_profile = profile
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        ack = _send_command(ws, "req-1", "set_depth", depth=0.55)
        # No follow-up events expected — set test buffer expectation
        # by sending another command immediately.
        ack2 = _send_command(ws, "req-2", "set_pad_lock", pad_id=1, locked=True)

    assert ack["ok"] is True
    assert ack["candidate"] is not None
    assert ack["candidate"]["depth"] == 0.55
    assert ack2["ok"] is True


def test_set_depth_with_preview_on_emits_mutation_previewed(session_factory) -> None:
    profile = _profile()
    session = session_factory(profile=profile)
    session.active_profile = profile
    session.preview_on = True
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        ack = _send_command(ws, "req-1", "set_depth", depth=0.55)
        event = ws.receive_json()

    assert ack["ok"] is True
    assert event["type"] == EVENT_MUTATION_PREVIEWED
    assert event["candidate"]["depth"] == 0.55


def test_toggle_preview_on_then_off_cycle(session_factory) -> None:
    profile = _profile()
    session = session_factory(profile=profile)
    session.active_profile = profile
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        ack_on = _send_command(ws, "req-1", "toggle_preview", on=True)
        event_on = ws.receive_json()
        ack_off = _send_command(ws, "req-2", "toggle_preview", on=False)
        event_off = ws.receive_json()

    assert ack_on["ok"] is True and ack_on["candidate"] is not None
    assert event_on["type"] == EVENT_MUTATION_PREVIEWED
    assert event_on["candidate"] is not None
    assert ack_off["ok"] is True and ack_off["candidate"] is None
    assert event_off["type"] == EVENT_MUTATION_PREVIEWED
    assert event_off["candidate"] is None


# ---------------------------------------------------------------------------
# regen flow.
# ---------------------------------------------------------------------------


def test_regen_returns_new_candidate(session_factory) -> None:
    profile = _profile()
    session = session_factory(profile=profile)
    session.active_profile = profile
    original_seed = session.seed
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        ack = _send_command(ws, "req-1", "regen")

    assert ack["ok"] is True
    assert ack["candidate"] is not None
    assert session.seed != original_seed


# ---------------------------------------------------------------------------
# send flow + pad-lock interaction.
# ---------------------------------------------------------------------------


def test_send_after_set_depth_emits_five_events(session_factory) -> None:
    profile = _profile()
    session = session_factory(profile=profile)
    session.active_profile = profile
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        _send_command(ws, "req-1", "set_depth", depth=0.55)  # primes candidate
        _prepare_send_plan(ws)
        ack = _send_command(ws, "req-2", "send")
        events_after = _drain(ws, 5)

    assert ack["ok"] is True
    assert ack["new_snapshot_id"]
    types_emitted = [e["type"] for e in events_after]
    assert types_emitted == [
        EVENT_SNAPSHOT_CHANGED,
        EVENT_HISTORY_UPDATED,
        EVENT_MUTATION_PREVIEWED,
        EVENT_SEND_PLAN_CHANGED,
        EVENT_SESSION_STATUS,
    ]
    null_event = next(e for e in events_after if e["type"] == EVENT_MUTATION_PREVIEWED)
    assert null_event["candidate"] is None
    status_event = next(e for e in events_after if e["type"] == EVENT_SESSION_STATUS)
    assert status_event["unsaved_sends"] == 1


def test_send_respects_pad_lock(session_factory) -> None:
    profile = _profile()
    session = session_factory(profile=profile)
    session.active_profile = profile
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        _send_command(ws, "req-1", "set_pad_lock", pad_id=1, locked=True)
        _send_command(ws, "req-2", "set_depth", depth=0.55)
        pre_pad1 = dict(session.device.capture_snapshot().pads[0].params)
        _prepare_send_plan(ws)
        _send_command(ws, "req-3", "send")
        _drain(ws, 5)

    post_pad1 = dict(session.device.capture_snapshot().pads[0].params)
    assert pre_pad1 == post_pad1  # locked pad untouched


# ---------------------------------------------------------------------------
# undo flow.
# ---------------------------------------------------------------------------


def test_undo_after_send_emits_snapshot_and_history(session_factory) -> None:
    profile = _profile()
    session = session_factory(profile=profile)
    session.active_profile = profile
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        _send_command(ws, "req-1", "set_depth", depth=0.55)
        _prepare_send_plan(ws)
        _send_command(ws, "req-2", "send")
        _drain(ws, 5)
        ack = _send_command(ws, "req-3", "undo")
        events_after = _drain(ws, 2)

    assert ack["ok"] is True
    types_emitted = [e["type"] for e in events_after]
    assert EVENT_SNAPSHOT_CHANGED in types_emitted
    assert EVENT_HISTORY_UPDATED in types_emitted


# ---------------------------------------------------------------------------
# save flow.
# ---------------------------------------------------------------------------


def test_save_promotes_entry_and_resets_unsaved_sends(session_factory) -> None:
    session = session_factory()
    session.unsaved_sends = 2
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        ack = _send_command(ws, "req-1", "save", label="industrial-peak")
        events_after = _drain(ws, 2)

    assert ack["ok"] is True
    types_emitted = [e["type"] for e in events_after]
    assert EVENT_HISTORY_UPDATED in types_emitted
    assert EVENT_SESSION_STATUS in types_emitted
    status_event = next(e for e in events_after if e["type"] == EVENT_SESSION_STATUS)
    assert status_event["unsaved_sends"] == 0


# ---------------------------------------------------------------------------
# load_snapshot flow.
# ---------------------------------------------------------------------------


def test_load_snapshot_jumps_to_past_entry(session_factory) -> None:
    profile = _profile()
    session = session_factory(profile=profile)
    session.active_profile = profile
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        _send_command(ws, "req-1", "set_depth", depth=0.55)
        _prepare_send_plan(ws)
        send_ack = _send_command(ws, "req-2", "send")
        _drain(ws, 5)
        load_ack = _send_command(
            ws, "req-3", "load_snapshot", snapshot_id="01HXY5Q9PJM0000000000000A"
        )
        events_after = _drain(ws, 2)

    assert send_ack["ok"] is True
    assert load_ack["ok"] is True
    assert load_ack["snapshot_id"] == "01HXY5Q9PJM0000000000000A"
    types_emitted = [e["type"] for e in events_after]
    assert EVENT_SNAPSHOT_CHANGED in types_emitted
    assert EVENT_HISTORY_UPDATED in types_emitted


# ---------------------------------------------------------------------------
# export_profile_model flow.
# ---------------------------------------------------------------------------


def test_export_profile_model_binary_returns_blob(session_factory) -> None:
    profile = _profile()
    session = session_factory(profile=profile)
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        ack = _send_command(
            ws,
            "req-1",
            "export_profile_model",
            profile_id=profile.profile_id,
            target="binary",
        )

    assert ack["ok"] is True
    raw = base64.b64decode(ack["model_bytes_b64"])
    assert raw[:4] == b"RYMP"


def test_export_profile_model_json_returns_serialisable_json(session_factory) -> None:
    profile = _profile()
    session = session_factory(profile=profile)
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        ack = _send_command(
            ws,
            "req-1",
            "export_profile_model",
            profile_id=profile.profile_id,
            target="json",
        )

    assert ack["ok"] is True
    payload = json.loads(base64.b64decode(ack["model_bytes_b64"]).decode("utf-8"))
    assert payload["profile_id"] == profile.profile_id


# ---------------------------------------------------------------------------
# Error path: unknown command.
# ---------------------------------------------------------------------------


def test_unknown_command_returns_error_ack(session_factory) -> None:
    session = session_factory()
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        ack = _send_command(ws, "req-1", "totally_made_up_command")

    assert ack["ok"] is False
    # PR 14: categorical envelope (``code``/``message`` replace ``error``).
    assert ack["code"] == "unknown_command"
    assert "unknown command" in ack["message"]


# ---------------------------------------------------------------------------
# Disconnect path — the server must exit the loop cleanly.
# ---------------------------------------------------------------------------


def test_endpoint_handles_clean_disconnect(session_factory) -> None:
    """Closing the WebSocket exits the server loop without raising."""

    session = session_factory()
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        # Closing the context manager triggers WebSocketDisconnect server-side.
    # If the disconnect path raises, TestClient surfaces the exception above.


def test_endpoint_round_trip_supports_multiple_commands(session_factory) -> None:
    """Verify the command loop survives several round-trips per connection."""

    session = session_factory()
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        for i in range(5):
            ack = _send_command(ws, f"req-{i}", "set_pad_lock", pad_id=1, locked=bool(i % 2))
            assert ack["ok"] is True
            assert ack["request_id"] == f"req-{i}"
