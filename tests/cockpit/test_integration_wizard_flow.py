"""WS-F: end-to-end integration of the Profile Wizard via FastAPI's TestClient.

This module mirrors :mod:`tests.cockpit.test_wizard_flow` (which exercises
the handler dispatcher directly) one layer up: every command travels
through a REAL WebSocket round-trip via :class:`fastapi.testclient.
TestClient`, so the test catches wire-level regressions like a missing
``send_json`` call, an out-of-order ack/event sequence, or a malformed
envelope shape.

What this safety net asserts
----------------------------

1. The full operator journey works end-to-end on the wire:
   ``wizard_start`` → ``wizard_set_metadata`` → ``wizard_add_source``
   (kind="artist", mode="reference" so no filesystem fixtures are needed)
   → ``wizard_analyze`` → ``wizard_review`` → ``wizard_save``.

2. The **ack-first / events-second** contract holds for every wizard
   command. The :func:`send_cmd` helper in :mod:`tests.cockpit.conftest`
   asserts this by construction (its first ``receive_json`` MUST be the
   ack -- if an event arrived first it would be returned instead and the
   subsequent ``drain_events`` would be short by one frame).

3. After ``wizard_save``, the new profile lives on disk under
   ``{tmp_path}/user/<profile_id>.json`` (the ``tmp_path``-backed
   :class:`ProfileRegistry` from :func:`cockpit_client`), AND a freshly-
   connected client sees the saved profile in its registry on the next
   ``select_profile`` round-trip.

4. The negative paths an integration-level UI would reasonably hit
   (analyze before start, save before review, invalid kind) still
   reach the dispatcher and return ``ok=False`` cleanly without
   tearing down the connection.

The wizard's ``kind="artist", mode="reference"`` path is used throughout
because it is the only analyzer mode that touches no filesystem (the
reference analyzer is a pure in-memory lookup). One additional test
mocks :func:`analyze_source` to verify the analyzer-failure branch
without needing a real broken file.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from cockpit.conftest import drain_events, send_cmd
from fastapi.testclient import TestClient

from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import wizard_handlers
from rytm_randomizer.cockpit.ws.protocol import EVENT_PROFILE_CHANGED
from rytm_randomizer.cockpit.ws.server import create_app
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.cockpit.ws.wizard_protocol import (
    EVENT_ANALYSIS_PROGRESS,
    EVENT_PROFILE_CREATED,
    EVENT_WIZARD_STATE_CHANGED,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# End-to-end happy path.
#
# All commands travel through the FastAPI WebSocket endpoint. The
# :func:`cockpit_ws` fixture has already drained the bootstrap quartet,
# so every ``receive_json`` here is either an ack (returned by
# ``send_cmd``) or a wizard event (returned by ``drain_events``).
# ---------------------------------------------------------------------------


def test_wizard_full_flow_persists_profile_over_websocket(cockpit_ws: object) -> None:
    """The full ``start → save`` flow round-trips cleanly via the live WebSocket."""

    # ----- wizard_start: ack carries wizard_id, one state event follows.
    start_ack = send_cmd(cockpit_ws, "wizard_start")
    start_events = drain_events(cockpit_ws, 1)

    assert start_ack["ok"] is True
    assert start_ack["request_id"] == "req-wizard_start"
    wizard_id = start_ack["wizard_id"]
    assert isinstance(wizard_id, str) and len(wizard_id) == 26
    assert start_events[0]["type"] == EVENT_WIZARD_STATE_CHANGED
    assert start_events[0]["state"]["wizard_id"] == wizard_id
    assert start_events[0]["state"]["step"] == "name"

    # ----- wizard_set_metadata: state updates carry the new name.
    meta_ack = send_cmd(
        cockpit_ws,
        "wizard_set_metadata",
        request_id="req-meta",
        name="my profile",
        description="techno",
    )
    meta_events = drain_events(cockpit_ws, 1)
    assert meta_ack["ok"] is True
    assert meta_events[0]["type"] == EVENT_WIZARD_STATE_CHANGED
    assert meta_events[0]["state"]["name"] == "my profile"
    assert meta_events[0]["state"]["description"] == "techno"

    # ----- wizard_add_source: returns source_id, pending job appears.
    add_ack = send_cmd(
        cockpit_ws,
        "wizard_add_source",
        request_id="req-add",
        kind="artist",
        mode="reference",
        location="Surgeon",
        display_name="Surgeon",
    )
    add_events = drain_events(cockpit_ws, 1)
    assert add_ack["ok"] is True
    source_id = add_ack["source_id"]
    assert isinstance(source_id, str) and len(source_id) == 26
    state_after_add = add_events[0]["state"]
    assert len(state_after_add["sources"]) == 1
    assert state_after_add["sources"][0]["kind"] == "artist"
    assert state_after_add["jobs"][0]["status"] == "pending"

    # ----- wizard_analyze: 2 progress events per source + 1 final state event.
    analyze_ack = send_cmd(cockpit_ws, "wizard_analyze", request_id="req-analyze")
    analyze_events = drain_events(cockpit_ws, 3)
    assert analyze_ack["ok"] is True
    event_types = [e["type"] for e in analyze_events]
    assert event_types == [
        EVENT_ANALYSIS_PROGRESS,  # analyzing
        EVENT_ANALYSIS_PROGRESS,  # ok (terminal)
        EVENT_WIZARD_STATE_CHANGED,  # final state
    ]
    terminal_job = analyze_events[1]["job"]
    assert terminal_job["status"] == "ok"
    assert terminal_job["progress"] == 1.0
    # "Surgeon" yields the curated 4-trait tuple via the reference analyzer.
    trait_names = {t["name"] for t in terminal_job["extracted_traits"]}
    assert trait_names == {
        "rolling_low_end",
        "metallic_tension",
        "hat_density",
        "filter_motion",
    }

    # ----- wizard_review: ack carries candidate, state carries it too.
    review_ack = send_cmd(cockpit_ws, "wizard_review", request_id="req-review")
    review_events = drain_events(cockpit_ws, 1)
    assert review_ack["ok"] is True
    candidate = review_ack["candidate_profile"]
    assert candidate["name"] == "my profile"
    assert candidate["kind"] == "user"
    assert candidate["model_version"] == "1.0.0"
    # The pad_mapping table assigns the 4 canonical traits to pads 1..4.
    assert sorted(pm["pad_id"] for pm in candidate["pad_mappings"]) == [1, 2, 3, 4]
    assert review_events[0]["type"] == EVENT_WIZARD_STATE_CHANGED
    assert review_events[0]["state"]["candidate_profile"] is not None

    # ----- wizard_save: emits BOTH profile_created AND profile_changed.
    save_ack = send_cmd(cockpit_ws, "wizard_save", request_id="req-save")
    save_events = drain_events(cockpit_ws, 2)
    assert save_ack["ok"] is True
    profile_id = save_ack["profile_id"]
    save_event_types = [e["type"] for e in save_events]
    assert EVENT_PROFILE_CREATED in save_event_types
    assert EVENT_PROFILE_CHANGED in save_event_types
    created = next(e for e in save_events if e["type"] == EVENT_PROFILE_CREATED)
    assert created["profile"]["profile_id"] == profile_id
    assert created["profile"]["name"] == "my profile"


def test_wizard_save_writes_profile_file_to_disk_and_is_listable(tmp_path: Path) -> None:
    """After ``wizard_save``, ``{tmp_path}/user/<profile_id>.json`` exists and lists.

    This test owns its session + TestClient so it can introspect the
    ``tmp_path``-backed :class:`ProfileRegistry` AND the on-disk file
    directly (the :func:`cockpit_client` fixture wraps both but doesn't
    expose the tmp directory to the test body).
    """

    from datetime import datetime, timezone

    from rytm_randomizer.cockpit.data import PadState, Snapshot

    initial = Snapshot(
        snapshot_id="01HXY5Q9PJM0000000000000F",
        device="analog_rytm_mk2",
        captured_at=datetime(2026, 5, 24, 12, 0, 0, tzinfo=timezone.utc),
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": 32, "dec": 80, "lev": 110}),
            PadState(pad_id=2, machine="SD Acoustic", params={"tun": 40, "dec": 60, "lev": 100}),
            PadState(pad_id=3, machine="SY Raw", params={"tun": 50, "dec": 70, "lev": 95}),
            PadState(pad_id=4, machine="FX Metal", params={"tun": 64, "dec": 90, "lev": 85}),
        ),
        scene_slot="A01",
        bpm=124.0,
    )
    device = MockDeviceAdapter(initial=initial)
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    registry = ProfileRegistry(profiles_dir=tmp_path)
    session = CockpitSession(profile_registry=registry, history_store=history, device=device)
    app = create_app(session)

    with TestClient(app) as client, client.websocket_connect("/ws") as ws:
        # Drain the bootstrap quartet.
        for _ in range(4):
            ws.receive_json()

        # Drive the full flow via the WebSocket.
        send_cmd(ws, "wizard_start")
        drain_events(ws, 1)
        send_cmd(ws, "wizard_set_metadata", request_id="req-meta", name="end-to-end")
        drain_events(ws, 1)
        send_cmd(
            ws,
            "wizard_add_source",
            request_id="req-add",
            kind="artist",
            mode="reference",
            location="Surgeon",
            display_name="Surgeon",
        )
        drain_events(ws, 1)
        send_cmd(ws, "wizard_analyze", request_id="req-analyze")
        drain_events(ws, 3)
        send_cmd(ws, "wizard_review", request_id="req-review")
        drain_events(ws, 1)
        save_ack = send_cmd(ws, "wizard_save", request_id="req-save")
        drain_events(ws, 2)

    profile_id = save_ack["profile_id"]
    # The registry persisted the profile to disk at the expected path.
    saved_path = tmp_path / "user" / f"{profile_id}.json"
    assert saved_path.is_file()
    # And the registry exposes it through both ``get`` and ``list_profiles``.
    assert session.profile_registry.get(profile_id) is not None
    listed_ids = [p.profile_id for p in session.profile_registry.list_profiles()]
    assert profile_id in listed_ids


def test_wizard_saved_profile_is_visible_to_new_connections(tmp_path: Path) -> None:
    """A second connection on the same registry sees the saved profile via ``select_profile``.

    The ``profile_changed`` bootstrap event of a fresh connect carries
    only the *active* profile (which a freshly-rebuilt session has
    ``None`` for); the registry visibility surfaces via a ``select_profile``
    round-trip that picks the wizard-saved id.
    """

    from datetime import datetime, timezone

    from rytm_randomizer.cockpit.data import PadState, Snapshot

    initial = Snapshot(
        snapshot_id="01HXY5Q9PJM0000000000000G",
        device="analog_rytm_mk2",
        captured_at=datetime(2026, 5, 24, 12, 0, 0, tzinfo=timezone.utc),
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": 32, "dec": 80, "lev": 110}),
            PadState(pad_id=2, machine="SD Acoustic", params={"tun": 40, "dec": 60, "lev": 100}),
            PadState(pad_id=3, machine="SY Raw", params={"tun": 50, "dec": 70, "lev": 95}),
            PadState(pad_id=4, machine="FX Metal", params={"tun": 64, "dec": 90, "lev": 85}),
        ),
        scene_slot="A01",
        bpm=124.0,
    )
    device_one = MockDeviceAdapter(initial=initial)
    history_one = HistoryStore()
    history_one.initial(device_one.capture_snapshot())
    registry_one = ProfileRegistry(profiles_dir=tmp_path)
    session_one = CockpitSession(
        profile_registry=registry_one, history_store=history_one, device=device_one
    )
    app_one = create_app(session_one)

    with TestClient(app_one) as client_one, client_one.websocket_connect("/ws") as ws_one:
        for _ in range(4):
            ws_one.receive_json()
        send_cmd(ws_one, "wizard_start")
        drain_events(ws_one, 1)
        send_cmd(ws_one, "wizard_set_metadata", request_id="req-meta", name="visible")
        drain_events(ws_one, 1)
        send_cmd(
            ws_one,
            "wizard_add_source",
            request_id="req-add",
            kind="artist",
            mode="reference",
            location="Surgeon",
            display_name="Surgeon",
        )
        drain_events(ws_one, 1)
        send_cmd(ws_one, "wizard_analyze", request_id="req-analyze")
        drain_events(ws_one, 3)
        send_cmd(ws_one, "wizard_review", request_id="req-review")
        drain_events(ws_one, 1)
        save_ack = send_cmd(ws_one, "wizard_save", request_id="req-save")
        drain_events(ws_one, 2)
        profile_id = save_ack["profile_id"]

    # Build a NEW session pointed at the SAME profiles directory; this
    # is the moral equivalent of "operator restarts the cockpit".
    device_two = MockDeviceAdapter(initial=initial)
    history_two = HistoryStore()
    history_two.initial(device_two.capture_snapshot())
    registry_two = ProfileRegistry(profiles_dir=tmp_path)
    session_two = CockpitSession(
        profile_registry=registry_two, history_store=history_two, device=device_two
    )
    app_two = create_app(session_two)

    with TestClient(app_two) as client_two, client_two.websocket_connect("/ws") as ws_two:
        for _ in range(4):
            ws_two.receive_json()
        select_ack = send_cmd(
            ws_two,
            "select_profile",
            request_id="req-select",
            profile_id=profile_id,
        )
        select_events = drain_events(ws_two, 1)

    assert select_ack["ok"] is True
    assert select_events[0]["type"] == EVENT_PROFILE_CHANGED
    assert select_events[0]["profile"]["profile_id"] == profile_id
    assert select_events[0]["profile"]["name"] == "visible"
    assert select_events[0]["profile"]["kind"] == "user"


# ---------------------------------------------------------------------------
# Negative paths via the live socket — every error branch the operator
# could plausibly trip.
# ---------------------------------------------------------------------------


def test_wizard_set_metadata_before_start_returns_error_over_ws(cockpit_ws: object) -> None:
    """Setting metadata before ``wizard_start`` returns ``ok=False`` cleanly."""

    ack = send_cmd(cockpit_ws, "wizard_set_metadata", name="x")
    # No events expected — error acks emit nothing.
    assert ack["ok"] is False
    assert "no active wizard" in ack["error"]


def test_wizard_add_source_invalid_kind_returns_error_over_ws(cockpit_ws: object) -> None:
    """An invalid ``kind`` value returns ``ok=False`` without tearing down the connection."""

    send_cmd(cockpit_ws, "wizard_start")
    drain_events(cockpit_ws, 1)

    ack = send_cmd(
        cockpit_ws,
        "wizard_add_source",
        request_id="req-bad",
        kind="bogus",
        mode="reference",
        location="x",
        display_name="x",
    )

    assert ack["ok"] is False
    assert "kind" in ack["error"]


def test_wizard_save_before_review_returns_error_over_ws(cockpit_ws: object) -> None:
    """``wizard_save`` before ``wizard_review`` (no candidate) returns ``ok=False``."""

    send_cmd(cockpit_ws, "wizard_start")
    drain_events(cockpit_ws, 1)

    ack = send_cmd(cockpit_ws, "wizard_save", request_id="req-save")

    assert ack["ok"] is False
    assert "no candidate" in ack["error"]


def test_wizard_cancel_over_ws_clears_session(cockpit_ws: object) -> None:
    """``wizard_cancel`` returns ``ok=True`` and emits no events on the wire."""

    send_cmd(cockpit_ws, "wizard_start")
    drain_events(cockpit_ws, 1)

    cancel_ack = send_cmd(cockpit_ws, "wizard_cancel", request_id="req-cancel")
    # No events expected after cancel. Verify by issuing a follow-up command
    # whose ack arriving immediately confirms no stray event was queued.
    follow_ack = send_cmd(cockpit_ws, "wizard_cancel", request_id="req-cancel-2")

    assert cancel_ack["ok"] is True
    assert follow_ack["ok"] is True  # idempotent


def test_wizard_analyzer_failure_marks_job_failed_over_ws(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When :func:`analyze_source` raises, the wire surfaces a ``failed`` job.

    This test owns its session so it can monkey-patch
    :func:`rytm_randomizer.cockpit.ws.wizard_handlers.analyze_source`
    without affecting other tests' shared :func:`cockpit_ws` fixture.
    """

    from datetime import datetime, timezone

    from rytm_randomizer.cockpit.data import PadState, Snapshot

    initial = Snapshot(
        snapshot_id="01HXY5Q9PJM0000000000000H",
        device="analog_rytm_mk2",
        captured_at=datetime(2026, 5, 24, 12, 0, 0, tzinfo=timezone.utc),
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": 32, "dec": 80, "lev": 110}),
            PadState(pad_id=2, machine="SD Acoustic", params={"tun": 40, "dec": 60, "lev": 100}),
            PadState(pad_id=3, machine="SY Raw", params={"tun": 50, "dec": 70, "lev": 95}),
            PadState(pad_id=4, machine="FX Metal", params={"tun": 64, "dec": 90, "lev": 85}),
        ),
        scene_slot="A01",
        bpm=124.0,
    )
    device = MockDeviceAdapter(initial=initial)
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    registry = ProfileRegistry(profiles_dir=tmp_path)
    session = CockpitSession(profile_registry=registry, history_store=history, device=device)
    app = create_app(session)

    def _boom(_source: object) -> tuple:
        raise RuntimeError("analyzer crashed: simulated")

    monkeypatch.setattr(wizard_handlers, "analyze_source", _boom)

    with TestClient(app) as client, client.websocket_connect("/ws") as ws:
        for _ in range(4):
            ws.receive_json()
        send_cmd(ws, "wizard_start")
        drain_events(ws, 1)
        send_cmd(
            ws,
            "wizard_add_source",
            request_id="req-add",
            kind="artist",
            mode="reference",
            location="Surgeon",
            display_name="Surgeon",
        )
        drain_events(ws, 1)

        analyze_ack = send_cmd(ws, "wizard_analyze", request_id="req-analyze")
        analyze_events = drain_events(ws, 3)

    # The command succeeds; the failure is reported via the job's status.
    assert analyze_ack["ok"] is True
    terminal_job = analyze_events[1]["job"]
    assert terminal_job["status"] == "failed"
    assert "analyzer crashed" in terminal_job["error"]
    assert terminal_job["extracted_traits"] == []
