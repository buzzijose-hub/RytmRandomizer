"""Integration: ``set_depth`` + ``toggle_preview`` + ``regen`` → ``mutation_previewed`` events.

Once a profile is active, the operator drives the candidate through three
commands:

* ``set_depth`` — moves the depth slider and recomputes the candidate.
* ``toggle_preview`` — flips the ghost overlay on/off (clears the
  candidate event payload when off).
* ``regen`` — bumps the seed and recomputes without moving depth.

All three commands take the candidate via :func:`_recompute_candidate`
in handlers.py; the wire-level differences are around which events
fire and whether the ack carries the candidate dict.

Spec reference: see ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Interaction flow examples" — "Operator drags the slider", "Operator
toggles preview", "Operator hits REGEN".
"""

from __future__ import annotations

import pytest
from cockpit.conftest import drain_events, send_cmd

from rytm_randomizer.cockpit.ws.protocol import EVENT_MUTATION_PREVIEWED

pytestmark = pytest.mark.fast


def _select_industrial(ws: object) -> None:
    """Helper: select scene-industrial and drain its profile_changed event."""

    send_cmd(ws, "select_profile", profile_id="scene-industrial")
    drain_events(ws, 1)


# ---------------------------------------------------------------------------
# set_depth
# ---------------------------------------------------------------------------


def test_set_depth_with_preview_off_returns_candidate_in_ack_no_event(
    cockpit_ws: object,
) -> None:
    """With preview off, set_depth puts the candidate on the ack but emits no event."""

    _select_industrial(cockpit_ws)
    ack = send_cmd(cockpit_ws, "set_depth", depth=0.45)

    # No events expected; confirm by sending a no-event command afterward.
    ack2 = send_cmd(cockpit_ws, "set_pad_lock", pad_id=2, locked=True)

    assert ack["ok"] is True
    assert ack["candidate"] is not None
    assert ack["candidate"]["depth"] == 0.45
    assert ack2["ok"] is True


def test_set_depth_with_preview_on_emits_mutation_previewed_event(
    cockpit_ws: object,
) -> None:
    """With preview on, set_depth emits a single ``mutation_previewed`` event."""

    _select_industrial(cockpit_ws)
    send_cmd(cockpit_ws, "toggle_preview", on=True)
    drain_events(cockpit_ws, 1)

    ack = send_cmd(cockpit_ws, "set_depth", depth=0.55)
    events = drain_events(cockpit_ws, 1)

    assert ack["ok"] is True
    assert events[0]["type"] == EVENT_MUTATION_PREVIEWED
    assert events[0]["candidate"]["depth"] == 0.55


def test_set_depth_without_active_profile_returns_null_candidate(
    cockpit_ws: object,
) -> None:
    """Without a profile, set_depth ack carries ``candidate=None`` (engine can't run)."""

    ack = send_cmd(cockpit_ws, "set_depth", depth=0.45)

    assert ack["ok"] is True
    assert ack["candidate"] is None


# ---------------------------------------------------------------------------
# toggle_preview
# ---------------------------------------------------------------------------


def test_toggle_preview_on_emits_candidate_event(cockpit_ws: object) -> None:
    """Toggling preview on with an active profile emits the candidate event."""

    _select_industrial(cockpit_ws)
    ack = send_cmd(cockpit_ws, "toggle_preview", on=True)
    events = drain_events(cockpit_ws, 1)

    assert ack["ok"] is True
    assert ack["candidate"] is not None
    assert events[0]["type"] == EVENT_MUTATION_PREVIEWED
    assert events[0]["candidate"] is not None


def test_toggle_preview_off_emits_null_candidate_event(cockpit_ws: object) -> None:
    """Toggling preview off clears the ghost overlay via a ``candidate=None`` frame."""

    _select_industrial(cockpit_ws)
    send_cmd(cockpit_ws, "toggle_preview", on=True)
    drain_events(cockpit_ws, 1)

    ack = send_cmd(cockpit_ws, "toggle_preview", request_id="req-off", on=False)
    events = drain_events(cockpit_ws, 1)

    assert ack["ok"] is True
    assert ack["candidate"] is None
    assert events[0]["type"] == EVENT_MUTATION_PREVIEWED
    assert events[0]["candidate"] is None


def test_toggle_preview_on_with_no_profile_emits_null_candidate_event(
    cockpit_ws: object,
) -> None:
    """Without a profile, toggling preview on still emits an event but with no candidate."""

    ack = send_cmd(cockpit_ws, "toggle_preview", on=True)
    events = drain_events(cockpit_ws, 1)

    assert ack["ok"] is True
    assert ack["candidate"] is None
    assert events[0]["type"] == EVENT_MUTATION_PREVIEWED
    assert events[0]["candidate"] is None


# ---------------------------------------------------------------------------
# regen
# ---------------------------------------------------------------------------


def test_regen_returns_candidate_and_changes_seed(cockpit_ws: object) -> None:
    """REGEN ack carries a fresh candidate; the new candidate's seed differs from prior."""

    _select_industrial(cockpit_ws)
    ack1 = send_cmd(cockpit_ws, "set_depth", request_id="req-1", depth=0.5)
    ack2 = send_cmd(cockpit_ws, "regen", request_id="req-2")

    assert ack1["ok"] is True and ack1["candidate"] is not None
    assert ack2["ok"] is True and ack2["candidate"] is not None
    # The seed is a 32-bit unsigned int; equality on two random samples is a
    # 1-in-4-billion event. Assert directly.
    assert ack2["candidate"]["seed"] != ack1["candidate"]["seed"]


def test_regen_without_active_profile_returns_error(cockpit_ws: object) -> None:
    """REGEN fails with a human-readable error when no profile is selected."""

    ack = send_cmd(cockpit_ws, "regen")

    assert ack["ok"] is False
    # PR 14: categorical envelope.
    assert ack["code"] == "validation_error"
    assert "no active profile" in ack["message"]


def test_regen_with_preview_on_emits_mutation_previewed_event(cockpit_ws: object) -> None:
    """REGEN with preview on emits exactly one ``mutation_previewed`` event."""

    _select_industrial(cockpit_ws)
    send_cmd(cockpit_ws, "toggle_preview", on=True)
    drain_events(cockpit_ws, 1)

    ack = send_cmd(cockpit_ws, "regen")
    events = drain_events(cockpit_ws, 1)

    assert ack["ok"] is True
    assert events[0]["type"] == EVENT_MUTATION_PREVIEWED
    assert events[0]["candidate"] is not None


def test_regen_with_preview_off_emits_no_events(cockpit_ws: object) -> None:
    """REGEN with preview off emits no events; the candidate is on the ack only."""

    _select_industrial(cockpit_ws)
    ack_regen = send_cmd(cockpit_ws, "regen")
    # Verify zero pending events by sending an event-free command and only
    # reading its ack — if a regen event were pending, the receive_json
    # below would pick it up instead of the lock ack.
    ack_lock = send_cmd(cockpit_ws, "set_pad_lock", request_id="req-lock", pad_id=1, locked=True)

    assert ack_regen["ok"] is True
    assert ack_lock["ok"] is True
    assert ack_lock["request_id"] == "req-lock"
