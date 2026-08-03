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

import asyncio
import base64
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

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
from rytm_randomizer.cockpit.ws.server import (
    HANDSHAKE_FIRST_FRAME_TIMEOUT_SECONDS,
    ConnectionQueue,
    ConnectionRegistry,
    _parse_envelope,
    _perform_handshake,
    _reject_handshake,
    _resolve_handshake_timeout_seconds,
    _resolve_max_message_bytes,
    _writer_loop,
    create_app,
)
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
# save flow — refused end-to-end, and inert.
# ---------------------------------------------------------------------------


def test_save_is_refused_over_the_wire_and_changes_nothing(session_factory) -> None:
    """``save`` used to ack a durable write that never happened.

    The handler called ``device.commit_kit`` — a mock log line — then
    acked ``ok: true``, promoted the history entry to ``kind="saved"``,
    and reset ``unsaved_sends`` to zero. Operators were told their kit
    was in the device's persistent memory. No persistent kit-write
    capability exists, so the command now refuses and leaves every piece
    of session state exactly where it was.
    """

    session = session_factory()
    session.unsaved_sends = 2
    client = TestClient(create_app(session, token=TEST_WS_TOKEN))

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        ack = _send_command(ws, "req-1", "save", label="industrial-peak")

    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert "not supported" in ack["message"]
    # Inert: the unsaved counter is NOT cleared and nothing was promoted.
    assert session.unsaved_sends == 2
    assert all(entry.kind != "saved" for entry in session.history_store.current.entries)


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


# ---------------------------------------------------------------------------
# Wave 2b — push-capable transport: server-side emits reach the client
# without a client command, and concurrent connections stay isolated.
# ---------------------------------------------------------------------------


def _await_zero_connections(registry: ConnectionRegistry, timeout: float = 5.0) -> int:
    """Poll until every endpoint teardown has unregistered its queue."""

    deadline = time.monotonic() + timeout
    while registry.connection_count and time.monotonic() < deadline:
        time.sleep(0.01)
    return registry.connection_count


def _await_connection_count(
    registry: ConnectionRegistry, expected: int, timeout: float = 5.0
) -> int:
    """Poll until exactly ``expected`` connections remain registered.

    Endpoint teardown is asynchronous, so a test that closes one of several
    connections must wait for that specific unregister rather than for zero.
    """

    deadline = time.monotonic() + timeout
    while registry.connection_count != expected and time.monotonic() < deadline:
        time.sleep(0.01)
    return registry.connection_count


def test_server_push_reaches_client_without_a_command(session_factory) -> None:
    """A registry broadcast arrives on the wire with no client frame in flight.

    This is the ConnectionManager / live-MIDI-monitor prerequisite: the
    old command-driven loop could only write after a client command; the
    writer task must flush a server-side emit on its own.
    """

    session = session_factory()
    app = create_app(session, token=TEST_WS_TOKEN)
    client = TestClient(app)

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        # The test thread has no running event loop, so this exercises
        # the cross-thread (call_soon_threadsafe) broadcast path.
        delivered = app.state.connection_registry.broadcast_event({"type": "monitor_ping", "n": 1})
        assert delivered == 1
        pushed = ws.receive_json()

    assert pushed == {"type": "monitor_ping", "n": 1}


def test_two_connections_get_isolated_acks_and_shared_broadcasts(session_factory) -> None:
    """Per-connection queues: A's ack/events never leak into B's stream.

    B's first post-bootstrap frame is the broadcast — proving the ack
    (and any events) from A's command were routed only to A's queue.
    Both connections then see the same broadcast (fan-out of 2).
    """

    session = session_factory()
    app = create_app(session, token=TEST_WS_TOKEN)
    client = TestClient(app)
    registry = app.state.connection_registry

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws_a:
        _recv_initial_events(ws_a)
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws_b:
            _recv_initial_events(ws_b)
            assert registry.connection_count == 2

            ack = _send_command(ws_a, "req-a", "set_pad_lock", pad_id=1, locked=True)
            assert ack == {"request_id": "req-a", "ok": True}

            delivered = registry.broadcast_event({"type": "monitor_ping", "n": 2})
            assert delivered == 2
            assert ws_b.receive_json() == {"type": "monitor_ping", "n": 2}
            assert ws_a.receive_json() == {"type": "monitor_ping", "n": 2}

    assert _await_zero_connections(registry) == 0


def test_broadcast_after_ack_and_events_preserves_fifo_ordering(session_factory) -> None:
    """ack → command events → later broadcast, in exactly that wire order."""

    profile = _profile()
    session = session_factory(profile=profile)
    session.active_profile = profile
    session.preview_on = True
    app = create_app(session, token=TEST_WS_TOKEN)
    client = TestClient(app)

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        _recv_initial_events(ws)
        ack = _send_command(ws, "req-1", "set_depth", depth=0.55)
        event = ws.receive_json()
        app.state.connection_registry.broadcast_event({"type": "monitor_ping", "n": 3})
        pushed = ws.receive_json()

    assert ack["ok"] is True
    assert event["type"] == EVENT_MUTATION_PREVIEWED
    assert pushed == {"type": "monitor_ping", "n": 3}


def test_create_app_uses_injected_connection_registry(session_factory) -> None:
    """An injected registry is honoured verbatim (Wave-3 ConnectionManager seam)."""

    registry = ConnectionRegistry(queue_maxsize=8)
    app = create_app(session_factory(), token=TEST_WS_TOKEN, connection_registry=registry)

    assert app.state.connection_registry is registry


def test_create_app_default_registry_is_exposed_on_app_state(session_factory) -> None:
    """Without injection, a fresh registry is built and published on app.state."""

    app = create_app(session_factory(), token=TEST_WS_TOKEN)

    registry = app.state.connection_registry
    assert isinstance(registry, ConnectionRegistry)
    assert registry.connection_count == 0


# ---------------------------------------------------------------------------
# Wave 2b — ConnectionQueue unit coverage: bounding, drop-oldest, closing.
# ---------------------------------------------------------------------------


def test_connection_queue_drops_oldest_when_full() -> None:
    """Overflow sheds the OLDEST frame; the newest state always survives."""

    async def run() -> tuple[list[int], int]:
        queue = ConnectionQueue(maxsize=3)
        for i in range(5):
            queue.put_frame({"type": "evt", "n": i})
        size = queue.size
        frames = [(await queue.get()).frame for _ in range(size)]
        return [frame["n"] for frame in frames], queue.dropped_count

    survivors, dropped = asyncio.run(run())

    assert survivors == [2, 3, 4]
    assert dropped == 2


def test_connection_queue_under_capacity_never_drops() -> None:
    """The drop loop is skipped entirely while the queue has headroom."""

    async def run() -> tuple[int, int]:
        queue = ConnectionQueue(maxsize=3)
        queue.put_frame({"type": "evt", "n": 0})
        queue.put_frame({"type": "evt", "n": 1})
        return queue.size, queue.dropped_count

    size, dropped = asyncio.run(run())

    assert size == 2
    assert dropped == 0


def test_connection_queue_refuses_frames_after_close_tagged_item() -> None:
    """Once a close-tagged frame is queued, later frames are dropped audibly."""

    async def run() -> tuple[int, int, int | None]:
        queue = ConnectionQueue(maxsize=4)
        queue.put_frame({"ok": False, "code": "message_too_large"}, close_code=1009)
        queue.put_frame({"type": "late-event"})
        item = await queue.get()
        return queue.size, queue.dropped_count, item.close_code

    size, dropped, close_code = asyncio.run(run())

    assert size == 0  # the late event never entered the queue
    assert dropped == 1
    assert close_code == 1009


def test_connection_queue_threadsafe_put_on_the_owning_loop() -> None:
    """From the owning loop, the thread-safe put is a direct enqueue."""

    async def run() -> int:
        queue = ConnectionQueue(maxsize=4)
        queue.put_frame_threadsafe({"type": "evt"})
        return queue.size

    assert asyncio.run(run()) == 1


# ---------------------------------------------------------------------------
# Wave 2b — ConnectionRegistry unit coverage.
# ---------------------------------------------------------------------------


def test_connection_registry_register_broadcast_unregister_cycle() -> None:
    """Registration hands out unique ids; broadcast fans out; unregister is idempotent."""

    async def run() -> tuple[bool, int, int, int, int, int, int]:
        registry = ConnectionRegistry(queue_maxsize=4)
        id_a, queue_a = registry.register()
        id_b, queue_b = registry.register()
        count_live = registry.connection_count
        reached = registry.broadcast_event({"type": "evt"})
        registry.unregister(id_a)
        count_after_one = registry.connection_count
        registry.unregister(id_a)  # idempotent — teardown paths may race
        return (
            id_a != id_b,
            count_live,
            reached,
            queue_a.size,
            queue_b.size,
            count_after_one,
            registry.connection_count,
        )

    ids_unique, live, reached, size_a, size_b, after_one, after_dup = asyncio.run(run())

    assert ids_unique
    assert live == 2
    assert reached == 2
    assert size_a == 1
    assert size_b == 1
    assert after_one == 1
    assert after_dup == 1


def test_connection_registry_broadcast_with_no_connections_is_a_noop() -> None:
    """Broadcasting into an empty registry returns a fan-out of zero."""

    registry = ConnectionRegistry()

    assert registry.broadcast_event({"type": "evt"}) == 0


# ---------------------------------------------------------------------------
# Wave 2b — writer-loop unit coverage (stub socket; no network).
# ---------------------------------------------------------------------------


class _StubWebSocket:
    """Duck-typed WebSocket capturing sends/closes, with injectable failures."""

    def __init__(self, *, fail_on_send: bool = False, fail_on_close: bool = False) -> None:
        self.sent: list[dict] = []
        self.closed_codes: list[int] = []
        self._fail_on_send = fail_on_send
        self._fail_on_close = fail_on_close

    async def send_json(self, frame: dict) -> None:
        if self._fail_on_send:
            raise WebSocketDisconnect(code=1006)
        self.sent.append(frame)

    async def close(self, code: int) -> None:
        if self._fail_on_close:
            raise RuntimeError("Cannot call close once a close message has been sent.")
        self.closed_codes.append(code)


def test_writer_loop_sends_frames_in_fifo_order_then_closes() -> None:
    """Ordinary frames flush in order; a close-tagged item closes and exits."""

    async def run() -> _StubWebSocket:
        queue = ConnectionQueue(maxsize=8)
        stub = _StubWebSocket()
        queue.put_frame({"type": "a"})
        queue.put_frame({"type": "b"})
        queue.put_frame({"ok": False, "code": "message_too_large"}, close_code=1009)
        await _writer_loop(stub, queue)  # type: ignore[arg-type]
        return stub

    stub = asyncio.run(run())

    assert stub.sent == [
        {"type": "a"},
        {"type": "b"},
        {"ok": False, "code": "message_too_large"},
    ]
    assert stub.closed_codes == [1009]


def test_writer_loop_exits_when_the_socket_dies_mid_send() -> None:
    """A disconnect during send ends the writer without touching close."""

    async def run() -> _StubWebSocket:
        queue = ConnectionQueue(maxsize=8)
        stub = _StubWebSocket(fail_on_send=True)
        queue.put_frame({"type": "a"})
        await _writer_loop(stub, queue)  # type: ignore[arg-type]
        return stub

    stub = asyncio.run(run())

    assert stub.sent == []
    assert stub.closed_codes == []


def test_writer_loop_swallows_close_failure_on_half_closed_socket() -> None:
    """A RuntimeError from close() is absorbed — the rejection frame still flushed."""

    async def run() -> _StubWebSocket:
        queue = ConnectionQueue(maxsize=8)
        stub = _StubWebSocket(fail_on_close=True)
        queue.put_frame({"ok": False, "code": "message_too_large"}, close_code=1009)
        await _writer_loop(stub, queue)  # type: ignore[arg-type]
        return stub

    stub = asyncio.run(run())

    assert stub.sent == [{"ok": False, "code": "message_too_large"}]
    assert stub.closed_codes == []


# ---------------------------------------------------------------------------
# Handshake helper edge arms (client vanishes mid-handshake) — stub sockets.
# ---------------------------------------------------------------------------


class _HandshakeStubWebSocket:
    """Duck-typed socket for the handshake helpers' disconnect edge arms."""

    def __init__(
        self,
        *,
        raise_on_receive: bool = False,
        hang_on_receive: bool = False,
        fail_on_send: bool = False,
        fail_on_close: bool = False,
    ) -> None:
        self.sent: list[dict] = []
        self.closed_codes: list[int] = []
        self._raise_on_receive = raise_on_receive
        self._hang_on_receive = hang_on_receive
        self._fail_on_send = fail_on_send
        self._fail_on_close = fail_on_close

    async def receive_text(self) -> str:
        if self._hang_on_receive:
            # A silent peer: never produces a first frame. Cancellable so
            # ``asyncio.wait_for`` can enforce the handshake deadline.
            await asyncio.Event().wait()
        raise WebSocketDisconnect(code=1006)

    async def send_json(self, frame: dict) -> None:
        if self._fail_on_send:
            raise WebSocketDisconnect(code=1006)
        self.sent.append(frame)

    async def close(self, code: int) -> None:
        if self._fail_on_close:
            raise RuntimeError("Cannot call close once a close message has been sent.")
        self.closed_codes.append(code)


def test_perform_handshake_returns_false_when_client_disconnects_first() -> None:
    """A client vanishing before its hello frame skips bootstrap cleanly."""

    stub = _HandshakeStubWebSocket(raise_on_receive=True)

    result = asyncio.run(_perform_handshake(stub, "expected-token"))  # type: ignore[arg-type]

    assert result is False
    assert stub.sent == []


def test_perform_handshake_times_out_silent_peer_with_auth_required() -> None:
    """No first frame before the deadline → auth_required ack + close 1008.

    The defect this pins: a client that never sends its hello (the
    browser client withholds it when it has no token) used to hold an
    authenticated-looking OPEN socket forever, so the UI showed a false
    "connected". The deadline turns that park into the same visible
    reject → close → redial loop a wrong token produces.
    """

    stub = _HandshakeStubWebSocket(hang_on_receive=True)

    result = asyncio.run(
        _perform_handshake(
            stub,  # type: ignore[arg-type]
            "expected-token",
            first_frame_timeout_seconds=0.01,
        )
    )

    assert result is False
    assert stub.sent == [{"ok": False, "code": "auth_required"}]
    assert stub.closed_codes == [1008]


def test_reject_handshake_absorbs_send_failure_on_dead_socket() -> None:
    """The rejection ack failing to send short-circuits before close."""

    stub = _HandshakeStubWebSocket(fail_on_send=True)

    asyncio.run(_reject_handshake(stub, "auth_required"))  # type: ignore[arg-type]

    assert stub.sent == []
    assert stub.closed_codes == []


def test_reject_handshake_absorbs_close_failure_on_half_closed_socket() -> None:
    """A close() failure after the ack flushed is swallowed."""

    stub = _HandshakeStubWebSocket(fail_on_close=True)

    asyncio.run(_reject_handshake(stub, "auth_required"))  # type: ignore[arg-type]

    assert stub.sent == [{"ok": False, "code": "auth_required"}]
    assert stub.closed_codes == []


# ---------------------------------------------------------------------------
# Wave 2b — envelope parsing + size-cap resolution unit coverage.
# ---------------------------------------------------------------------------


def test_parse_envelope_malformed_json_funnels_to_missing_key_path() -> None:
    assert _parse_envelope("{this is not json") == {"request_id": "", "command": {}}


def test_parse_envelope_non_dict_json_funnels_to_missing_key_path() -> None:
    assert _parse_envelope("[1, 2, 3]") == {"request_id": "", "command": {}}


def test_parse_envelope_passes_well_formed_envelopes_through() -> None:
    raw = json.dumps({"request_id": "req-1", "command": {"type": "regen"}})

    assert _parse_envelope(raw) == {"request_id": "req-1", "command": {"type": "regen"}}


def test_resolve_max_message_bytes_unparseable_env_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RYTM_RAND_WS_MAX_MESSAGE_BYTES", "not-a-number")

    assert _resolve_max_message_bytes() == 1 * 1024 * 1024


def test_resolve_max_message_bytes_non_positive_env_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RYTM_RAND_WS_MAX_MESSAGE_BYTES", "-5")

    assert _resolve_max_message_bytes() == 1 * 1024 * 1024


def test_resolve_max_message_bytes_valid_env_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RYTM_RAND_WS_MAX_MESSAGE_BYTES", "4096")

    assert _resolve_max_message_bytes() == 4096


def test_resolve_handshake_timeout_defaults_when_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RYTM_RAND_WS_HANDSHAKE_TIMEOUT_SECONDS", raising=False)

    assert _resolve_handshake_timeout_seconds() == HANDSHAKE_FIRST_FRAME_TIMEOUT_SECONDS


def test_resolve_handshake_timeout_unparseable_env_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RYTM_RAND_WS_HANDSHAKE_TIMEOUT_SECONDS", "not-a-number")

    assert _resolve_handshake_timeout_seconds() == HANDSHAKE_FIRST_FRAME_TIMEOUT_SECONDS


def test_resolve_handshake_timeout_non_positive_env_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A zero/negative override would disable the deadline — refuse it."""

    monkeypatch.setenv("RYTM_RAND_WS_HANDSHAKE_TIMEOUT_SECONDS", "0")

    assert _resolve_handshake_timeout_seconds() == HANDSHAKE_FIRST_FRAME_TIMEOUT_SECONDS


def test_resolve_handshake_timeout_valid_env_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RYTM_RAND_WS_HANDSHAKE_TIMEOUT_SECONDS", "0.25")

    assert _resolve_handshake_timeout_seconds() == 0.25


def test_sibling_disconnect_leaves_the_armed_session_armed(session_factory) -> None:
    """Closing a SECOND connection must not disarm the performing one.

    One ``CockpitSession`` is shared by every connection, so an
    unconditional disarm in the ``/ws`` teardown let any sibling transport
    close the armed operator's exclusive output port. Concretely: the
    operator arms in tab A and starts a live set, glances at diagnostics in
    tab B, closes B — and A's port dies mid-song with no warning and no
    action of their own.

    Teardown must therefore disarm only when the LAST connection leaves.
    """

    from rytm_randomizer.cockpit.ws import handlers

    session = session_factory()
    app = create_app(session, token=TEST_WS_TOKEN)
    client = TestClient(app)
    registry = app.state.connection_registry

    class _Port:
        name = "Elektron Analog Rytm MK2 Out"

        def __init__(self) -> None:
            self.closed = 0

        def send(self, message: object) -> None:  # pragma: no cover - unused
            raise AssertionError("this test never transmits")

        def close(self) -> None:
            self.closed += 1

    class _Provider:
        def __init__(self) -> None:
            self.port = _Port()

        def list_output_names(self) -> tuple[str, ...]:
            return (self.port.name,)

        def open_output(self, port_name: str) -> _Port:
            assert port_name == self.port.name
            return self.port

    provider = _Provider()
    session.arm_port_provider = provider
    session.arm_secret = "test-arm-secret"

    with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws_a:
        _recv_initial_events(ws_a)
        ack = _send_command(
            ws_a,
            "req-arm",
            "arm",
            arm_token="test-arm-secret",  # noqa: S106 — the session's own test secret
            confirm=True,
            port_name=provider.port.name,
        )
        assert ack["ok"] is True, ack
        assert handlers.session_is_armed(session) is True

        # A sibling connection comes and goes while A is still performing.
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws_b:
            _recv_initial_events(ws_b)
            assert registry.connection_count == 2
        _await_connection_count(registry, 1)

        # A is untouched: still armed, port never closed.
        assert session.armed_apply is not None
        assert handlers.session_is_armed(session) is True
        assert provider.port.closed == 0

    # Last connection gone -> deterministic teardown still happens.
    assert _await_zero_connections(registry) == 0
    assert session.armed_apply is None
    assert provider.port.closed == 1
