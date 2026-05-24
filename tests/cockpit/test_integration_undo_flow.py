"""Integration: ``undo`` — walks the history pointer one step back.

UNDO consumes the current entry's ``parent_id`` and re-emits the
parent's snapshot + the updated history. When the operator is already
at the chain root (``parent_id is None``), UNDO returns ``ok=False``
without modifying any state.

Spec reference: see ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Interaction flow examples" — "Operator hits UNDO".
"""

from __future__ import annotations

import pytest
from cockpit.conftest import drain_events, send_cmd

from rytm_randomizer.cockpit.ws.protocol import (
    EVENT_HISTORY_UPDATED,
    EVENT_SNAPSHOT_CHANGED,
)

pytestmark = pytest.mark.fast


def _send_once(ws: object) -> str:
    """Perform one full SEND (arm + send) and return the new snapshot_id."""

    send_cmd(ws, "select_profile", profile_id="scene-industrial")
    drain_events(ws, 1)
    send_cmd(ws, "set_depth", depth=0.55)
    ack = send_cmd(ws, "send")
    drain_events(ws, 4)
    return ack["new_snapshot_id"]


def test_undo_at_root_returns_error(cockpit_ws: object) -> None:
    """The root entry has ``parent_id=None``; UNDO fails with ``nothing to undo``."""

    ack = send_cmd(cockpit_ws, "undo")

    assert ack["ok"] is False
    assert "nothing to undo" in ack["error"]


def test_undo_after_one_send_returns_to_root(cockpit_ws: object) -> None:
    """After one SEND, UNDO walks back to the root snapshot id."""

    new_snapshot_id = _send_once(cockpit_ws)
    assert new_snapshot_id != "01HXY5Q9PJM00000000000ROOT"  # sanity

    ack = send_cmd(cockpit_ws, "undo")
    events = drain_events(cockpit_ws, 2)

    assert ack["ok"] is True
    assert ack["snapshot_id"] == "01HXY5Q9PJM00000000000ROOT"
    types = [e["type"] for e in events]
    assert EVENT_SNAPSHOT_CHANGED in types
    assert EVENT_HISTORY_UPDATED in types

    history = next(e for e in events if e["type"] == EVENT_HISTORY_UPDATED)["history"]
    assert history["current_id"] == "01HXY5Q9PJM00000000000ROOT"


def test_undo_emits_snapshot_matching_target(cockpit_ws: object) -> None:
    """The ``snapshot_changed`` event after UNDO carries the parent snapshot's params."""

    _send_once(cockpit_ws)
    send_cmd(cockpit_ws, "undo")
    events = drain_events(cockpit_ws, 2)

    snapshot = next(e for e in events if e["type"] == EVENT_SNAPSHOT_CHANGED)["snapshot"]
    assert snapshot["snapshot_id"] == "01HXY5Q9PJM00000000000ROOT"
    # Root snapshot's pad 1 had {"tun": 32, "dec": 80, "lev": 110}.
    pad1 = next(p for p in snapshot["pads"] if p["pad_id"] == 1)
    assert pad1["params"] == {"tun": 32, "dec": 80, "lev": 110}


def test_undo_twice_after_two_sends_walks_back_two_steps(cockpit_ws: object) -> None:
    """Two sends + two undos returns to the chain root."""

    # SEND #1
    send_cmd(cockpit_ws, "select_profile", profile_id="scene-garage")
    drain_events(cockpit_ws, 1)
    send_cmd(cockpit_ws, "set_depth", depth=0.5)
    send_cmd(cockpit_ws, "send", request_id="req-send-1")
    drain_events(cockpit_ws, 4)
    # SEND #2
    send_cmd(cockpit_ws, "set_depth", request_id="req-depth-2", depth=0.7)
    send_cmd(cockpit_ws, "send", request_id="req-send-2")
    drain_events(cockpit_ws, 4)

    # UNDO #1: should land on the SEND #1 snapshot (not root yet).
    ack1 = send_cmd(cockpit_ws, "undo", request_id="req-undo-1")
    drain_events(cockpit_ws, 2)
    # UNDO #2: should land on root.
    ack2 = send_cmd(cockpit_ws, "undo", request_id="req-undo-2")
    drain_events(cockpit_ws, 2)

    assert ack1["ok"] is True
    assert ack2["ok"] is True
    assert ack2["snapshot_id"] == "01HXY5Q9PJM00000000000ROOT"


def test_undo_then_undo_at_root_returns_error(cockpit_ws: object) -> None:
    """After walking back to root, a further UNDO returns the same ``nothing to undo`` error."""

    _send_once(cockpit_ws)
    send_cmd(cockpit_ws, "undo", request_id="req-undo-1")
    drain_events(cockpit_ws, 2)

    ack = send_cmd(cockpit_ws, "undo", request_id="req-undo-2")

    assert ack["ok"] is False
    assert "nothing to undo" in ack["error"]
