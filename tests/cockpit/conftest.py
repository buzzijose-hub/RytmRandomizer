"""Shared fixtures for cockpit integration tests (WS-K).

These fixtures spin up a real :func:`rytm_randomizer.cockpit.ws.server.create_app`
FastAPI instance in-process and drive it through ``fastapi.testclient.TestClient``
so every command in the spec (11 total) and every event (6 total) can be
exercised end-to-end across the JSON-over-WebSocket protocol.

The two top-level fixtures:

* :func:`cockpit_client` — yields a configured :class:`fastapi.testclient.TestClient`
  bound to a freshly-constructed :class:`CockpitSession`. The session is
  pre-seeded with a 4-pad reference snapshot and a temp-directory-backed
  :class:`ProfileRegistry`, so the seven built-in scenes are always
  available without filesystem mutation.
* :func:`cockpit_ws` — opens a WebSocket connection against
  :func:`cockpit_client`, **drains the four bootstrap events** so tests
  start at the "live command loop" cursor, and yields the live socket.

Four helpers that integration tests call directly:

* :func:`send_cmd` — write a command envelope, read the matching ack frame.
* :func:`drain_events` — read all queued events until the socket buffer is empty.
* :func:`prepare_send_plan` — run the inert PREPARE step before SEND.
* :func:`collect_initial_events` — read the bootstrap events on a *fresh*
  socket (the :func:`cockpit_ws` fixture already drains them; tests that
  need to inspect them open their own connection via :func:`cockpit_client`).

Single source of truth: every integration test file imports from this module,
not from sibling test files, per Gate 11 (fixture deduplication).
"""

from __future__ import annotations

from collections.abc import Generator, Iterator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rytm_randomizer.cockpit.data import PadState, Snapshot
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws.server import create_app
from rytm_randomizer.cockpit.ws.session import CockpitSession

pytestmark = pytest.mark.fast

_INITIAL_SNAPSHOT_ID = "01HXY5Q9PJM00000000000ROOT"
"""Deterministic root snapshot id used by every integration test.

Integration tests assert against this id by string equality when they
need to verify history-pointer behavior (e.g. load_snapshot back to root).
"""

_FIXED_TIMESTAMP = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)
"""Frozen captured_at so to_dict round-trips are reproducible across runs."""


def _make_default_snapshot() -> Snapshot:
    """Build the 4-pad reference Rytm snapshot every integration test starts with.

    Pad layout matches the v10 cockpit mockup and the built-in scenes:
    pad 1 = BD (kick), pad 2 = SD (snare), pad 3 = SY (synth), pad 4 = FX
    (filter). Three CC params per pad ensures the mutation engine produces
    a non-empty ``pad_deltas`` for every pad in every test.
    """

    return Snapshot(
        snapshot_id=_INITIAL_SNAPSHOT_ID,
        device="analog_rytm_mk2",
        captured_at=_FIXED_TIMESTAMP,
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": 32, "dec": 80, "lev": 110}),
            PadState(pad_id=2, machine="SD Acoustic", params={"tun": 40, "dec": 60, "lev": 100}),
            PadState(pad_id=3, machine="SY Raw", params={"tun": 50, "dec": 70, "lev": 95}),
            PadState(pad_id=4, machine="FX Metal", params={"tun": 64, "dec": 90, "lev": 85}),
        ),
        scene_slot="A01",
        bpm=124.0,
    )


@pytest.fixture
def cockpit_client(tmp_path: Path) -> Generator[TestClient, None, None]:
    """Spin up the cockpit WS server in-process against a fresh mock device + temp profile dir.

    The session is bootstrapped end-to-end exactly as ``__main__.py`` would
    do at production startup: build the :class:`MockDeviceAdapter` with the
    reference snapshot, build a :class:`ProfileRegistry` against ``tmp_path``
    (so user-profile writes don't leak across tests), bootstrap the
    :class:`HistoryStore` with the device's initial snapshot, hand them to
    :class:`CockpitSession`, then ``create_app`` and yield a TestClient.
    """

    initial = _make_default_snapshot()
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path),
        history_store=HistoryStore(),
        device=MockDeviceAdapter(initial=initial),
    )
    session.history_store.initial(initial)
    app = create_app(session)
    with TestClient(app) as client:
        yield client


@pytest.fixture
def cockpit_ws(cockpit_client: TestClient) -> Iterator[object]:
    """Open a WebSocket, drain the bootstrap quartet, yield the live socket.

    Tests that need to inspect the bootstrap events themselves should open
    their own connection through :func:`cockpit_client` and call
    :func:`collect_initial_events`. This fixture is for tests that operate
    in the steady-state command loop and need the buffer empty on entry.
    """

    with cockpit_client.websocket_connect("/ws") as ws:
        # Drain the four bootstrap events emitted by ``emit_initial_events``
        # so the first ``receive_json`` inside the test body is the
        # response to its first command, not a leftover bootstrap frame.
        for _ in range(4):
            ws.receive_json()
        yield ws


def collect_initial_events(ws: object, count: int = 4) -> list[dict]:
    """Read ``count`` event frames in order (default: the bootstrap quartet).

    Use only on a freshly-connected WebSocket whose bootstrap events have
    not yet been drained. The :func:`cockpit_ws` fixture has already
    drained them for steady-state tests.
    """

    return [ws.receive_json() for _ in range(count)]  # type: ignore[attr-defined]


def send_cmd(ws: object, cmd_type: str, request_id: str | None = None, **body: object) -> dict:
    """Send one command envelope and return the matching ack frame.

    ``request_id`` defaults to ``"req-<cmd_type>"`` so tests that don't
    care about correlation can still verify the ack echoes the id. Any
    additional keyword arguments are inlined into the ``command`` dict
    alongside the ``type`` discriminator.
    """

    if request_id is None:
        request_id = f"req-{cmd_type}"
    envelope = {"request_id": request_id, "command": {"type": cmd_type, **body}}
    ws.send_json(envelope)  # type: ignore[attr-defined]
    return ws.receive_json()  # type: ignore[attr-defined]


def drain_events(ws: object, count: int) -> list[dict]:
    """Read exactly ``count`` event frames in order.

    Tests know the expected event count per command from the spec
    (e.g. ``send`` emits exactly 5 events after its ack). Passing the
    expected count keeps the helper synchronous and deterministic — there
    is no idle ``select`` / timeout dance.
    """

    return [ws.receive_json() for _ in range(count)]  # type: ignore[attr-defined]


def prepare_send_plan(ws: object, request_id: str = "req-prepare-send-plan") -> dict:
    """Prepare and drain the inert SEND-plan event before a SEND command."""

    ack = send_cmd(ws, "prepare_send_plan", request_id=request_id)
    if ack.get("ok") is not True:
        raise AssertionError(f"prepare_send_plan failed: {ack}")
    if ack["send_plan"]["ready"] is not True:
        raise AssertionError(f"prepare_send_plan blocked: {ack['send_plan']}")
    drain_events(ws, 1)
    return ack


__all__ = [
    "cockpit_client",
    "cockpit_ws",
    "collect_initial_events",
    "drain_events",
    "prepare_send_plan",
    "send_cmd",
]
