"""Integration: ``send`` -> snapshot/history events + cleared preview + session_status refresh.

The SEND command is the cockpit's heaviest operator action. The
ack carries the new snapshot id, and five events fire in order:

1. ``snapshot_changed`` - the device's new captured state.
2. ``history_updated`` - the new auto entry appended to the chain.
3. ``mutation_previewed`` (``candidate=None``) - preview clears.
4. ``send_plan_changed`` (``send_plan=None``) clears the prepared plan.
5. ``session_status`` - ``unsaved_sends`` bumps by 1.

Spec reference: see ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
section "Interaction flow examples" - "Operator hits SEND".
"""

from __future__ import annotations

import pytest
from cockpit.conftest import drain_events, prepare_send_plan, send_cmd

from rytm_randomizer.cockpit.ws.protocol import (
    EVENT_HISTORY_UPDATED,
    EVENT_MUTATION_PREVIEWED,
    EVENT_SEND_PLAN_CHANGED,
    EVENT_SESSION_STATUS,
    EVENT_SNAPSHOT_CHANGED,
)

pytestmark = pytest.mark.fast


def _arm_candidate(ws: object, profile_id: str = "scene-industrial", depth: float = 0.45) -> None:
    """Helper: select a profile + set a depth so a candidate is staged."""

    send_cmd(ws, "select_profile", profile_id=profile_id)
    drain_events(ws, 1)
    send_cmd(ws, "set_depth", depth=depth)


def test_send_emits_snapshot_and_history_and_clears_preview(cockpit_ws: object) -> None:
    """SEND emits snapshot_changed + history_updated + null candidate + session_status."""

    _arm_candidate(cockpit_ws)
    send_cmd(cockpit_ws, "toggle_preview", on=True)
    drain_events(cockpit_ws, 1)
    prepare_send_plan(cockpit_ws)

    ack = send_cmd(cockpit_ws, "send")
    events = drain_events(cockpit_ws, 5)
    types = [e["type"] for e in events]

    assert ack["ok"] is True
    assert ack["new_snapshot_id"]
    assert EVENT_SNAPSHOT_CHANGED in types
    assert EVENT_HISTORY_UPDATED in types
    assert EVENT_SEND_PLAN_CHANGED in types
    assert EVENT_SESSION_STATUS in types
    null_preview = next(e for e in events if e["type"] == EVENT_MUTATION_PREVIEWED)
    assert null_preview["candidate"] is None
    null_plan = next(e for e in events if e["type"] == EVENT_SEND_PLAN_CHANGED)
    assert null_plan["send_plan"] is None


def test_send_without_candidate_returns_error(cockpit_ws: object) -> None:
    """SEND without a staged candidate returns ``ok=False`` (no profile set)."""

    ack = send_cmd(cockpit_ws, "send")

    assert ack["ok"] is False
    assert "no current candidate" in ack["error"]


def test_send_with_candidate_but_no_ready_plan_returns_error(cockpit_ws: object) -> None:
    """A staged candidate still needs an explicit ready send plan before SEND."""

    _arm_candidate(cockpit_ws)
    ack = send_cmd(cockpit_ws, "send")

    assert ack["ok"] is False
    assert "no ready send plan" in ack["error"]


def test_send_bumps_unsaved_sends_in_session_status(cockpit_ws: object) -> None:
    """The ``session_status`` event after SEND carries ``unsaved_sends=1``."""

    _arm_candidate(cockpit_ws)
    prepare_send_plan(cockpit_ws)
    send_cmd(cockpit_ws, "send")
    events = drain_events(cockpit_ws, 5)

    status_event = next(e for e in events if e["type"] == EVENT_SESSION_STATUS)
    assert status_event["unsaved_sends"] == 1


def test_send_emits_events_in_documented_order(cockpit_ws: object) -> None:
    """SEND event order includes preview + send-plan clearing before status."""

    _arm_candidate(cockpit_ws)
    prepare_send_plan(cockpit_ws)
    send_cmd(cockpit_ws, "send")
    events = drain_events(cockpit_ws, 5)

    types_in_order = [e["type"] for e in events]
    assert types_in_order == [
        EVENT_SNAPSHOT_CHANGED,
        EVENT_HISTORY_UPDATED,
        EVENT_MUTATION_PREVIEWED,
        EVENT_SEND_PLAN_CHANGED,
        EVENT_SESSION_STATUS,
    ]


def test_send_history_grows_one_entry_per_send(cockpit_ws: object) -> None:
    """Each successful SEND appends one entry to the history chain."""

    _arm_candidate(cockpit_ws)
    prepare_send_plan(cockpit_ws)
    send_cmd(cockpit_ws, "send", request_id="req-send-1")
    events1 = drain_events(cockpit_ws, 5)
    hist1 = next(e for e in events1 if e["type"] == EVENT_HISTORY_UPDATED)["history"]

    send_cmd(cockpit_ws, "set_depth", request_id="req-depth-2", depth=0.6)  # re-arm
    prepare_send_plan(cockpit_ws)
    send_cmd(cockpit_ws, "send", request_id="req-send-2")
    events2 = drain_events(cockpit_ws, 5)
    hist2 = next(e for e in events2 if e["type"] == EVENT_HISTORY_UPDATED)["history"]

    assert len(hist1["entries"]) == 2  # root + first send
    assert len(hist2["entries"]) == 3  # root + first + second send
    # ``current_id`` advances with each send.
    assert hist1["current_id"] != hist2["current_id"]


def test_send_new_snapshot_id_matches_history_current_id(cockpit_ws: object) -> None:
    """The ack's ``new_snapshot_id`` equals the history event's ``current_id``."""

    _arm_candidate(cockpit_ws)
    prepare_send_plan(cockpit_ws)
    ack = send_cmd(cockpit_ws, "send")
    events = drain_events(cockpit_ws, 5)

    history = next(e for e in events if e["type"] == EVENT_HISTORY_UPDATED)["history"]
    snapshot = next(e for e in events if e["type"] == EVENT_SNAPSHOT_CHANGED)["snapshot"]
    assert ack["new_snapshot_id"] == history["current_id"]
    assert ack["new_snapshot_id"] == snapshot["snapshot_id"]
