"""Integration: ``save`` is refused — no persistent kit-write exists.

SAVE used to ack ``{"ok": true, "snapshot_id": ...}``, promote the current
history entry from ``"auto"`` to ``"saved"``, reset ``unsaved_sends`` to
zero, and emit ``history_updated`` + ``session_status``. That is the full
vocabulary of a durable write — and underneath it, the only call was
``DeviceAdapter.commit_kit``, whose sole implementation was a mock
``logger.info`` line. Nothing was written to any device on any path, while
``docs/COCKPIT_QUICKSTART.md`` told operators "SAVE writes a Rytm SysEx kit
dump to the device's persistent kit memory".

An operator who believes a kit is stored stops treating it as volatile and
loses it on the next power cycle, so the command now fails closed and says
what is missing. It returns to ``ok: true`` when a real SysEx kit write and
the capture-before-write restore path the Live-but-Passive model requires
both land.

This suite pins the refusal end-to-end over the real WebSocket transport:
the ack shape, the absence of events, and — the part that matters most —
that every piece of session state the old handler mutated is untouched.
"""

from __future__ import annotations

import pytest
from cockpit.conftest import drain_events, prepare_send_plan, send_cmd

from rytm_randomizer.cockpit.ws.protocol import EVENT_SESSION_STATUS

pytestmark = pytest.mark.fast


def test_save_is_refused_with_a_categorical_ack(cockpit_ws: object) -> None:
    """The refusal uses the standard error envelope, not a bespoke shape."""

    ack = send_cmd(cockpit_ws, "save", label="opening-kit")

    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert ack["request_id"] == "req-save"


def test_the_refusal_explains_what_is_missing(cockpit_ws: object) -> None:
    """An operator must be able to act on the message without reading code."""

    ack = send_cmd(cockpit_ws, "save", label="opening-kit")

    message = ack["message"]
    assert "not supported" in message
    # Names the two missing capabilities...
    assert "SysEx" in message
    assert "restore path" in message
    # ...and states, explicitly, that nothing happened.
    assert "Nothing was written" in message


def test_save_is_refused_with_or_without_a_label(cockpit_ws: object) -> None:
    """``label`` never made the write real; omitting it changes nothing."""

    assert send_cmd(cockpit_ws, "save")["ok"] is False
    assert send_cmd(cockpit_ws, "save", request_id="req-save-2", label="kit-v1")["ok"] is False


def test_save_does_not_promote_the_current_history_entry(cockpit_ws: object) -> None:
    """No entry may be marked ``saved`` — that label would be a lie."""

    send_cmd(cockpit_ws, "save", label="kit-v1")

    # The next command's events carry the live history; nothing is "saved".
    send_cmd(cockpit_ws, "select_profile", profile_id="scene-industrial")
    drain_events(cockpit_ws, 1)
    send_cmd(cockpit_ws, "set_depth", depth=0.45)
    prepare_send_plan(cockpit_ws)
    send_cmd(cockpit_ws, "send", request_id="req-send")
    events = drain_events(cockpit_ws, 5)

    history = next(e for e in events if e["type"] == "history_updated")["history"]
    assert all(entry["kind"] != "saved" for entry in history["entries"])
    assert all(entry["label"] is None for entry in history["entries"])


def test_save_does_not_reset_the_unsaved_send_counter(cockpit_ws: object) -> None:
    """``unsaved_sends`` is the operator's "you have unpersisted work" signal.

    Zeroing it on a write that never happened is the most actively harmful
    part of the old behaviour: it removed the only warning the UI had.
    """

    send_cmd(cockpit_ws, "select_profile", profile_id="scene-industrial")
    drain_events(cockpit_ws, 1)
    send_cmd(cockpit_ws, "set_depth", depth=0.45)
    prepare_send_plan(cockpit_ws)
    send_cmd(cockpit_ws, "send", request_id="req-send")
    events = drain_events(cockpit_ws, 5)
    before = next(e for e in events if e["type"] == EVENT_SESSION_STATUS)["unsaved_sends"]
    assert before == 1

    assert send_cmd(cockpit_ws, "save", request_id="req-save")["ok"] is False

    # Ask for a fresh status via another command; the counter still stands.
    send_cmd(cockpit_ws, "select_profile", profile_id="scene-rolling")
    drain_events(cockpit_ws, 1)
    send_cmd(cockpit_ws, "set_depth", depth=0.5)
    prepare_send_plan(cockpit_ws)
    send_cmd(cockpit_ws, "send", request_id="req-send-2")
    events = drain_events(cockpit_ws, 5)

    after = next(e for e in events if e["type"] == EVENT_SESSION_STATUS)["unsaved_sends"]
    assert after == 2


def test_save_emits_no_events_at_all(cockpit_ws: object) -> None:
    """A refusal must not perturb any client state.

    Proven by ordering: the frame after the ``save`` ack is the ack of the
    *next* command, so no event slipped into the FIFO queue in between.
    """

    assert send_cmd(cockpit_ws, "save", label="kit-v1")["ok"] is False

    # ``set_pad_lock`` emits nothing of its own, so the very next frame
    # after its ack would be a stray event if ``save`` had queued one.
    next_ack = send_cmd(cockpit_ws, "set_pad_lock", request_id="req-lock", pad_id=1, locked=True)
    following_ack = send_cmd(
        cockpit_ws, "set_pad_lock", request_id="req-lock-2", pad_id=1, locked=False
    )

    assert next_ack["request_id"] == "req-lock"
    assert following_ack["request_id"] == "req-lock-2"
