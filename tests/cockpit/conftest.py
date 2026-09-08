"""Shared fixtures for cockpit integration tests (WS-K).

These fixtures spin up a real :func:`rytm_randomizer.cockpit.ws.server.create_app`
FastAPI instance in-process and drive it through ``fastapi.testclient.TestClient``
so every command and event in the spec can be
exercised end-to-end across the JSON-over-WebSocket protocol.

The two top-level fixtures:

* :func:`cockpit_client` — yields a configured :class:`fastapi.testclient.TestClient`
  bound to a freshly-constructed :class:`CockpitSession`. The session is
  pre-seeded with a 12-pad reference snapshot and a temp-directory-backed
  :class:`ProfileRegistry`, so the seven built-in scenes are always
  available without filesystem mutation.
* :func:`cockpit_ws` — opens a WebSocket connection against
  :func:`cockpit_client`, **drains the authoritative bootstrap events** so tests
  start at the "live command loop" cursor, and yields the live socket.

One autouse fixture every cockpit test module inherits:

* :func:`_reset_active_connection_manager` — clears the process-level
  :class:`ConnectionManager` registration before and after each test.
  Four modules used to carry a private copy of this fixture under four
  different names (``_reset_active_connection_manager``,
  ``_clean_active_manager``, ``_no_active_manager`` ×2), three of which
  only cleaned up on the way out. Autouse in the package conftest is the
  Gate-11 single source of truth: a module that registers a manager
  cannot leak it into a sibling module's worker regardless of whether
  its author remembered the fixture.

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

import hashlib
import logging
from collections.abc import Generator, Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import pytest
from fastapi.testclient import TestClient

from rytm_randomizer.cockpit.capture import KitCaptureResult, KitCaptureService
from rytm_randomizer.cockpit.data import PadState, Snapshot
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.device.connection import set_active_connection_manager
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws.protocol import (
    HELLO_FRAME_TYPE,
    INITIAL_EVENT_COUNT,
    WS_SUBPROTOCOL,
)
from rytm_randomizer.cockpit.ws.server import create_app
from rytm_randomizer.cockpit.ws.session import CockpitSession

TEST_WS_TOKEN: Final[str] = "test-token-only-for-pytest-do-not-use-in-prod"
"""The fixed handshake token every cockpit test fixture passes to ``create_app``.

Per CODE_REVIEW.md PR 1 (finding C1), ``create_app`` now requires a
non-empty per-launch token and refuses to start without one. The test
suite uses a single hard-coded value so every fixture, helper, and
direct ``create_app`` call site can agree on what the client sends in
its ``hello`` frame without threading a fresh token through each
parameter list. Cockpit tests never bind a real port, so the literal
never leaves the process.
"""

pytestmark = pytest.mark.fast


@dataclass
class MutableClock:
    """Explicit test clock shared by capture and show-bank lifecycle harnesses."""

    current: datetime

    def __call__(self) -> datetime:
        return self.current


@dataclass
class FixedFrameCaptureProvider:
    """Input-only fake that returns one supplied frame without opening MIDI."""

    frame: bytes
    port_name: str = "Mock input"

    def list_input_names(self) -> tuple[str, ...]:
        return (self.port_name,)

    def capture_sysex_messages(
        self,
        _port_name: str,
        *,
        timeout_seconds: float,
    ) -> tuple[bytes, ...]:
        assert timeout_seconds > 0
        return (self.frame,)


def capture_fixed_frame(
    device_id: str, frame: bytes, *, port_name: str = "Mock input"
) -> KitCaptureResult:
    """Exercise the public capture service with the shared input-only fake."""

    return KitCaptureService(FixedFrameCaptureProvider(frame, port_name)).capture(
        device_id, port_name
    )


@pytest.fixture
def ws_handler_caplog(
    caplog: pytest.LogCaptureFixture,
) -> Iterator[pytest.LogCaptureFixture]:
    """Capture handler records despite package-level propagation being disabled."""

    logger = logging.getLogger("rytm_randomizer.cockpit.ws.handlers")
    logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)


_INITIAL_SNAPSHOT_ID = "01HXY5Q9PJM00000000000ROOT"
"""Deterministic root snapshot id used by every integration test.

Integration tests assert against this id by string equality when they
need to verify history-pointer behavior (e.g. load_snapshot back to root).
"""

_FIXED_TIMESTAMP = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)
"""Frozen captured_at so to_dict round-trips are reproducible across runs."""


def _make_default_snapshot() -> Snapshot:
    """Build the 12-pad reference Rytm snapshot every integration test starts with.

    Pad layout matches the v10 cockpit mockup and the built-in scenes:
    the first four pads carry the current scene defaults, and pads 5-12
    represent the remaining Rytm tracks. Three CC params per pad ensures
    the mutation engine produces a non-empty ``pad_deltas`` for every pad
    in every test.
    """

    return Snapshot(
        snapshot_id=_INITIAL_SNAPSHOT_ID,
        device="analog_rytm_mk2",
        captured_at=_FIXED_TIMESTAMP,
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": 32, "dec": 80, "lev": 110}),
            PadState(pad_id=2, machine="SD Classic", params={"tun": 40, "dec": 60, "lev": 100}),
            PadState(pad_id=3, machine="CH Closed", params={"tun": 50, "dec": 70, "lev": 95}),
            PadState(pad_id=4, machine="OH Open", params={"tun": 64, "dec": 90, "lev": 85}),
            PadState(pad_id=5, machine="BT Rim", params={"tun": 58, "dec": 72, "lev": 90}),
            PadState(pad_id=6, machine="LT Low", params={"tun": 45, "dec": 74, "lev": 92}),
            PadState(pad_id=7, machine="MT Mid", params={"tun": 52, "dec": 68, "lev": 88}),
            PadState(pad_id=8, machine="HT High", params={"tun": 71, "dec": 55, "lev": 84}),
            PadState(pad_id=9, machine="CP Clap", params={"tun": 62, "dec": 67, "lev": 96}),
            PadState(pad_id=10, machine="RS Riser", params={"tun": 75, "dec": 88, "lev": 76}),
            PadState(pad_id=11, machine="SY Raw", params={"tun": 81, "dec": 38, "lev": 82}),
            PadState(pad_id=12, machine="BD Acoustic", params={"tun": 36, "dec": 86, "lev": 104}),
        ),
        scene_slot="A01",
        bpm=124.0,
    )


def _seed_for_test_node(nodeid: str) -> int:
    """Return a deterministic non-zero 32-bit seed for one pytest node."""

    seed = int.from_bytes(hashlib.sha256(nodeid.encode("utf-8")).digest()[:4], "big")
    return seed or 1


@pytest.fixture(autouse=True)
def _reset_active_connection_manager() -> Iterator[None]:
    """Every cockpit test starts AND ends with no registered ConnectionManager.

    ``set_active_connection_manager`` writes process-level state. A test
    that registers a manager and does not clear it changes what every
    later test in the same xdist worker observes: the handlers'
    ``session_status`` phase silently switches from the device-derived
    fallback to the leaked manager's state, so failures land in an
    unrelated module and depend on collection order.

    Autouse and package-wide so the guarantee does not depend on each
    module remembering to opt in. Clearing on the way *in* as well as out
    means a leak from a non-cockpit test cannot poison this package
    either.
    """

    set_active_connection_manager(None)
    yield
    set_active_connection_manager(None)


@pytest.fixture
def cockpit_client(
    tmp_path: Path, request: pytest.FixtureRequest
) -> Generator[TestClient, None, None]:
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
        seed=_seed_for_test_node(request.node.nodeid),
    )
    session.history_store.initial(initial)
    app = create_app(session, token=TEST_WS_TOKEN)
    with TestClient(app) as client:
        yield client


@pytest.fixture
def cockpit_ws(cockpit_client: TestClient) -> Iterator[object]:
    """Open a WebSocket, complete the handshake, drain bootstrap, yield the live socket.

    Per CODE_REVIEW.md PR 1 finding C1, the cockpit WS endpoint now
    requires a handshake before the bootstrap event set fires. This
    fixture:

    1. Connects on the pinned :data:`WS_SUBPROTOCOL` so the server
       accepts the upgrade (L8).
    2. Sends ``{"type": "hello", "token": TEST_WS_TOKEN}`` and reads the
       ``{"ok": true}`` ack (C1).
    3. Drains the bootstrap events emitted by
       :func:`emit_initial_events` so the first ``receive_json`` inside
       the test body is the response to its first command.

    Tests that need to inspect the bootstrap events themselves should
    open their own connection through :func:`cockpit_client`, call
    :func:`complete_handshake`, and then :func:`collect_initial_events`.
    """

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        for _ in range(INITIAL_EVENT_COUNT):
            ws.receive_json()
        yield ws


def complete_handshake(ws: object, token: str = TEST_WS_TOKEN) -> dict:
    """Send the ``hello`` frame, read the ack, return it.

    Centralises the handshake the live :func:`cockpit_ws` fixture and
    the direct-``create_app`` tests both rely on. Returns the ack so
    negative-path tests can assert on the ``ok`` / ``code`` fields when
    a non-default token is passed.
    """

    ws.send_json({"type": HELLO_FRAME_TYPE, "token": token})  # type: ignore[attr-defined]
    return ws.receive_json()  # type: ignore[attr-defined]


def collect_initial_events(ws: object, count: int = INITIAL_EVENT_COUNT) -> list[dict]:
    """Read ``count`` event frames in order (default: the bootstrap event set).

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
    for _ in range(64):
        frame = ws.receive_json()  # type: ignore[attr-defined]
        if frame.get("request_id") == request_id and "ok" in frame:
            return frame
    raise AssertionError(f"no matching ack received for {request_id!r}")


def drain_events(ws: object, count: int) -> list[dict]:
    """Read exactly ``count`` event frames in order.

    Tests know the expected event count per command from the spec
    (e.g. ``send`` emits exactly 5 events after its ack). Passing the
    expected count keeps the helper synchronous and deterministic — there
    is no idle ``select`` / timeout dance.
    """

    return [ws.receive_json() for _ in range(count)]  # type: ignore[attr-defined]


def prepare_send_plan(ws: object, request_id: str = "req-prepare-send-plan") -> dict:
    """Prepare and drain plan plus authoritative-stage events before SEND."""

    ack = send_cmd(ws, "prepare_send_plan", request_id=request_id)
    if ack.get("ok") is not True:
        raise AssertionError(f"prepare_send_plan failed: {ack}")
    if ack["send_plan"]["ready"] is not True:
        raise AssertionError(f"prepare_send_plan blocked: {ack['send_plan']}")
    drain_events(ws, 2)
    return ack


__all__ = [
    "FixedFrameCaptureProvider",
    "MutableClock",
    "TEST_WS_TOKEN",
    "capture_fixed_frame",
    "cockpit_client",
    "cockpit_ws",
    "collect_initial_events",
    "complete_handshake",
    "drain_events",
    "prepare_send_plan",
    "send_cmd",
]
