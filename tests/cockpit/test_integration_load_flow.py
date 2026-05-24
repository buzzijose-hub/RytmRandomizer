"""Integration: ``load_snapshot`` — navigate to any past entry by id.

LOAD lets the operator jump ``current_id`` to an arbitrary snapshot in
the chain (not just the immediate parent, which is what UNDO does).
The handler does not mutate the device's in-memory state — it merely
emits the chosen snapshot via ``snapshot_changed`` so the UI can re-render,
and the updated history so the strip's selection chip moves.

Spec reference: see ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Interaction flow examples" — "Operator clicks a past history chip".
"""

from __future__ import annotations

import pytest
from cockpit.conftest import drain_events, prepare_send_plan, send_cmd

from rytm_randomizer.cockpit.ws.protocol import (
    EVENT_HISTORY_UPDATED,
    EVENT_SNAPSHOT_CHANGED,
)

pytestmark = pytest.mark.fast


def _send_chain(ws: object, *depths: float) -> list[str]:
    """Issue one SEND per ``depths`` value; return the new snapshot ids in order."""

    send_cmd(ws, "select_profile", profile_id="scene-industrial")
    drain_events(ws, 1)
    new_ids: list[str] = []
    for i, depth in enumerate(depths):
        send_cmd(ws, "set_depth", request_id=f"req-depth-{i}", depth=depth)
        prepare_send_plan(ws, request_id=f"req-prepare-{i}")
        ack = send_cmd(ws, "send", request_id=f"req-send-{i}")
        drain_events(ws, 5)
        new_ids.append(ack["new_snapshot_id"])
    return new_ids


def test_load_snapshot_jumps_to_root(cockpit_ws: object) -> None:
    """LOAD with the root snapshot id moves ``current_id`` back to the root."""

    new_ids = _send_chain(cockpit_ws, 0.45, 0.6)
    assert new_ids  # sanity

    ack = send_cmd(
        cockpit_ws,
        "load_snapshot",
        snapshot_id="01HXY5Q9PJM00000000000ROOT",
    )
    events = drain_events(cockpit_ws, 2)

    assert ack["ok"] is True
    assert ack["snapshot_id"] == "01HXY5Q9PJM00000000000ROOT"
    history = next(e for e in events if e["type"] == EVENT_HISTORY_UPDATED)["history"]
    assert history["current_id"] == "01HXY5Q9PJM00000000000ROOT"


def test_load_snapshot_jumps_to_arbitrary_mid_entry(cockpit_ws: object) -> None:
    """LOAD with the id of a non-current entry lands the pointer on that entry."""

    new_ids = _send_chain(cockpit_ws, 0.45, 0.55, 0.64)
    target_id = new_ids[1]  # middle of the chain

    ack = send_cmd(cockpit_ws, "load_snapshot", snapshot_id=target_id)
    events = drain_events(cockpit_ws, 2)

    assert ack["ok"] is True
    assert ack["snapshot_id"] == target_id
    snapshot = next(e for e in events if e["type"] == EVENT_SNAPSHOT_CHANGED)["snapshot"]
    assert snapshot["snapshot_id"] == target_id


def test_load_snapshot_unknown_id_returns_error(cockpit_ws: object) -> None:
    """An unknown snapshot_id returns ``ok=False`` with a human-readable message."""

    ack = send_cmd(
        cockpit_ws,
        "load_snapshot",
        snapshot_id="01HXY5Q9PJM00000000FAKEID0",
    )

    assert ack["ok"] is False
    # ``HistoryStore.load`` raises a KeyError whose str payload includes the id.
    assert "01HXY5Q9PJM00000000FAKEID0" in ack["error"]


def test_load_snapshot_emits_snapshot_then_history(cockpit_ws: object) -> None:
    """LOAD event order: snapshot_changed → history_updated."""

    _send_chain(cockpit_ws, 0.5)

    send_cmd(
        cockpit_ws,
        "load_snapshot",
        snapshot_id="01HXY5Q9PJM00000000000ROOT",
    )
    events = drain_events(cockpit_ws, 2)

    types_in_order = [e["type"] for e in events]
    assert types_in_order == [EVENT_SNAPSHOT_CHANGED, EVENT_HISTORY_UPDATED]


def test_load_then_load_back_to_latest_round_trip(cockpit_ws: object) -> None:
    """Load to root, then load back to the most recent entry, ends on the latest."""

    new_ids = _send_chain(cockpit_ws, 0.45, 0.55)
    latest = new_ids[-1]

    send_cmd(
        cockpit_ws,
        "load_snapshot",
        request_id="req-load-root",
        snapshot_id="01HXY5Q9PJM00000000000ROOT",
    )
    drain_events(cockpit_ws, 2)

    ack = send_cmd(
        cockpit_ws,
        "load_snapshot",
        request_id="req-load-latest",
        snapshot_id=latest,
    )
    events = drain_events(cockpit_ws, 2)

    assert ack["ok"] is True
    assert ack["snapshot_id"] == latest
    history = next(e for e in events if e["type"] == EVENT_HISTORY_UPDATED)["history"]
    assert history["current_id"] == latest
