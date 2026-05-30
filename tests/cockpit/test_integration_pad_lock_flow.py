"""Integration: ``set_pad_lock`` — locked pads keep their params on subsequent SEND.

A locked pad in :class:`CockpitSession.pad_locks` is excluded from the
mutation apply step in :meth:`MockDeviceAdapter.apply`. The candidate
still contains a ``PadDelta`` for the pad (so the UI can still preview
what the mutation *would* do), but the SEND skips writing it.

Spec reference: see ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Interaction flow examples" — "Operator locks a pad".
"""

from __future__ import annotations

import pytest
from cockpit.conftest import drain_events, prepare_send_plan, send_cmd

pytestmark = pytest.mark.fast


def _arm_candidate(ws: object) -> None:
    """Pick a profile and set a depth so SEND has something to apply."""

    send_cmd(ws, "select_profile", profile_id="scene-industrial")
    drain_events(ws, 1)
    send_cmd(ws, "set_depth", depth=0.6)


def test_set_pad_lock_returns_ok_with_no_events(cockpit_ws: object) -> None:
    """``set_pad_lock`` emits no events; pad-lock state is internal to the session."""

    ack = send_cmd(cockpit_ws, "set_pad_lock", pad_id=2, locked=True)
    # Confirm no event was queued by sending a follow-up no-event command.
    ack2 = send_cmd(cockpit_ws, "set_pad_lock", request_id="req-2", pad_id=2, locked=False)

    assert ack["ok"] is True
    assert ack2["ok"] is True


def test_locked_pad_keeps_params_after_send(cockpit_ws: object) -> None:
    """Locking pad 2 means SEND leaves pad 2's params byte-identical."""

    # Capture pre-send state.
    send_cmd(cockpit_ws, "set_pad_lock", pad_id=2, locked=True)
    _arm_candidate(cockpit_ws)
    prepare_send_plan(cockpit_ws)
    send_cmd(cockpit_ws, "send")
    events_after = drain_events(cockpit_ws, 5)

    snapshot_after = next(e for e in events_after if e["type"] == "snapshot_changed")["snapshot"]
    pad2_after = next(p for p in snapshot_after["pads"] if p["pad_id"] == 2)
    # The fixture pre-seeds pad 2 with these values; locking must preserve them.
    assert pad2_after["params"] == {"tun": 40, "dec": 60, "lev": 100}


def test_unlocked_pad_changes_after_send(cockpit_ws: object) -> None:
    """Pads NOT in the lock set get mutated by SEND (sanity check vs locked path)."""

    send_cmd(cockpit_ws, "set_pad_lock", pad_id=2, locked=True)
    _arm_candidate(cockpit_ws)
    prepare_send_plan(cockpit_ws)
    send_cmd(cockpit_ws, "send")
    events_after = drain_events(cockpit_ws, 5)

    snapshot_after = next(e for e in events_after if e["type"] == "snapshot_changed")["snapshot"]
    pad1_after = next(p for p in snapshot_after["pads"] if p["pad_id"] == 1)
    # Original pad 1 was {"tun": 32, "dec": 80, "lev": 110}; at depth 0.6 the
    # engine will almost certainly mutate at least one key. Equality on all
    # three values would be a near-zero-probability event.
    assert pad1_after["params"] != {"tun": 32, "dec": 80, "lev": 110}


def test_unlocking_pad_restores_normal_mutation_path(cockpit_ws: object) -> None:
    """Locking then unlocking a pad lets the next SEND mutate it as if never locked."""

    send_cmd(cockpit_ws, "set_pad_lock", request_id="req-lock", pad_id=2, locked=True)
    send_cmd(cockpit_ws, "set_pad_lock", request_id="req-unlock", pad_id=2, locked=False)
    _arm_candidate(cockpit_ws)
    prepare_send_plan(cockpit_ws)
    send_cmd(cockpit_ws, "send")
    events_after = drain_events(cockpit_ws, 5)

    snapshot_after = next(e for e in events_after if e["type"] == "snapshot_changed")["snapshot"]
    pad2_after = next(p for p in snapshot_after["pads"] if p["pad_id"] == 2)
    # After unlock + SEND with non-trivial depth the original values should differ.
    assert pad2_after["params"] != {"tun": 40, "dec": 60, "lev": 100}


def test_multiple_locked_pads_all_skipped(cockpit_ws: object) -> None:
    """Locking pads 1 + 3 leaves both untouched; pads 2 + 4 still mutate."""

    send_cmd(cockpit_ws, "set_pad_lock", request_id="req-1", pad_id=1, locked=True)
    send_cmd(cockpit_ws, "set_pad_lock", request_id="req-3", pad_id=3, locked=True)
    _arm_candidate(cockpit_ws)
    prepare_send_plan(cockpit_ws)
    send_cmd(cockpit_ws, "send")
    events_after = drain_events(cockpit_ws, 5)

    snapshot_after = next(e for e in events_after if e["type"] == "snapshot_changed")["snapshot"]
    pads_after = {p["pad_id"]: p["params"] for p in snapshot_after["pads"]}
    assert pads_after[1] == {"tun": 32, "dec": 80, "lev": 110}  # locked, unchanged
    assert pads_after[3] == {"tun": 50, "dec": 70, "lev": 95}  # locked, unchanged
    # Pads 2 + 4 should now differ from their seed values.
    assert pads_after[2] != {"tun": 40, "dec": 60, "lev": 100}
    assert pads_after[4] != {"tun": 64, "dec": 90, "lev": 85}
