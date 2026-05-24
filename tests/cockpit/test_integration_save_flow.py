"""Integration: ``save`` — promotes the current history entry to ``kind="saved"``.

SAVE writes the current snapshot to the device adapter's persistent kit
memory (a no-op + log for the mock adapter), promotes the current entry
from ``"auto"`` to ``"saved"`` (carrying an optional label), and resets
``unsaved_sends`` to zero. Two events fire after the ack:

1. ``history_updated`` — the promoted entry's ``kind`` is now ``"saved"``
   and ``label`` is the operator's chosen string.
2. ``session_status`` — ``unsaved_sends`` resets to 0.

Spec reference: see ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Interaction flow examples" — "Operator hits SAVE".
"""

from __future__ import annotations

import pytest
from cockpit.conftest import drain_events, send_cmd

from rytm_randomizer.cockpit.ws.protocol import (
    EVENT_HISTORY_UPDATED,
    EVENT_SESSION_STATUS,
)

pytestmark = pytest.mark.fast


def test_save_promotes_current_entry_to_saved(cockpit_ws: object) -> None:
    """SAVE flips the current entry's ``kind`` from ``auto`` to ``saved``."""

    ack = send_cmd(cockpit_ws, "save", label="opening-kit")
    events = drain_events(cockpit_ws, 2)

    assert ack["ok"] is True
    history = next(e for e in events if e["type"] == EVENT_HISTORY_UPDATED)["history"]
    current = next(
        entry
        for entry in history["entries"]
        if entry["snapshot"]["snapshot_id"] == ack["snapshot_id"]
    )
    assert current["kind"] == "saved"
    assert current["label"] == "opening-kit"


def test_save_resets_unsaved_sends_to_zero(cockpit_ws: object) -> None:
    """SAVE emits a ``session_status`` event with ``unsaved_sends=0``."""

    # Stage some "unsaved" work by issuing a SEND first.
    send_cmd(cockpit_ws, "select_profile", profile_id="scene-industrial")
    drain_events(cockpit_ws, 1)
    send_cmd(cockpit_ws, "set_depth", depth=0.45)
    send_cmd(cockpit_ws, "send", request_id="req-send")
    drain_events(cockpit_ws, 4)

    ack = send_cmd(cockpit_ws, "save", request_id="req-save")
    events = drain_events(cockpit_ws, 2)

    assert ack["ok"] is True
    status = next(e for e in events if e["type"] == EVENT_SESSION_STATUS)
    assert status["unsaved_sends"] == 0


def test_save_without_label_records_null_label(cockpit_ws: object) -> None:
    """Omitting ``label`` records ``label=None`` on the promoted entry."""

    ack = send_cmd(cockpit_ws, "save")  # no label
    events = drain_events(cockpit_ws, 2)

    assert ack["ok"] is True
    history = next(e for e in events if e["type"] == EVENT_HISTORY_UPDATED)["history"]
    current = next(
        entry
        for entry in history["entries"]
        if entry["snapshot"]["snapshot_id"] == ack["snapshot_id"]
    )
    assert current["label"] is None
    assert current["kind"] == "saved"


def test_save_emits_history_then_session_status_events(cockpit_ws: object) -> None:
    """SAVE event order: history_updated → session_status."""

    send_cmd(cockpit_ws, "save", label="kit-v1")
    events = drain_events(cockpit_ws, 2)

    types_in_order = [e["type"] for e in events]
    assert types_in_order == [EVENT_HISTORY_UPDATED, EVENT_SESSION_STATUS]


def test_save_acks_with_current_snapshot_id(cockpit_ws: object) -> None:
    """The save ack carries the snapshot_id of the entry that was promoted."""

    ack = send_cmd(cockpit_ws, "save", label="bootstrap-kit")
    drain_events(cockpit_ws, 2)

    # On a fresh session the current entry is the root snapshot.
    assert ack["snapshot_id"] == "01HXY5Q9PJM00000000000ROOT"


def test_save_then_new_send_re_increments_unsaved_sends(cockpit_ws: object) -> None:
    """After SAVE resets the counter, the next SEND still increments unsaved_sends."""

    send_cmd(cockpit_ws, "save", request_id="req-save-1")
    drain_events(cockpit_ws, 2)

    send_cmd(cockpit_ws, "select_profile", profile_id="scene-rolling")
    drain_events(cockpit_ws, 1)
    send_cmd(cockpit_ws, "set_depth", depth=0.5)
    send_cmd(cockpit_ws, "send", request_id="req-send-1")
    events = drain_events(cockpit_ws, 4)

    status = next(e for e in events if e["type"] == EVENT_SESSION_STATUS)
    assert status["unsaved_sends"] == 1
