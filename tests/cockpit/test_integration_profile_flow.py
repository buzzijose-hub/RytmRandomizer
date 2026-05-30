"""Integration: ``select_profile`` command → ``profile_changed`` event.

Selecting a profile sets ``CockpitSession.active_profile``, triggers a
candidate recompute (so the engine is warmed for the next preview), and
emits a single ``profile_changed`` event carrying the new profile dict.

Spec reference: see ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Interaction flow examples" — "Operator picks a Scene".

Built-in scenes are always available (no filesystem state needed) so
these tests use the seven scene_* profile_ids shipped under
``rytm_randomizer.cockpit.profiles.builtin``.
"""

from __future__ import annotations

import pytest
from cockpit.conftest import drain_events, send_cmd

from rytm_randomizer.cockpit.ws.protocol import (
    EVENT_MUTATION_PREVIEWED,
    EVENT_PROFILE_CHANGED,
)

pytestmark = pytest.mark.fast


def test_select_profile_emits_profile_changed(cockpit_ws: object) -> None:
    """Selecting a built-in scene emits one ``profile_changed`` event."""

    ack = send_cmd(cockpit_ws, "select_profile", profile_id="scene-industrial")
    events = drain_events(cockpit_ws, 1)

    assert ack["ok"] is True
    assert ack["request_id"] == "req-select_profile"
    assert events[0]["type"] == EVENT_PROFILE_CHANGED
    assert events[0]["profile"]["profile_id"] == "scene-industrial"
    assert events[0]["profile"]["name"] == "industrial"
    assert events[0]["profile"]["kind"] == "scene"


def test_select_profile_unknown_id_returns_error(cockpit_ws: object) -> None:
    """An unknown profile_id returns ``ok=False`` with a human-readable error."""

    ack = send_cmd(cockpit_ws, "select_profile", profile_id="scene-does-not-exist")

    assert ack["ok"] is False
    # PR 14: categorical envelope.
    assert ack["code"] == "validation_error"
    assert "unknown profile_id" in ack["message"]
    assert "scene-does-not-exist" in ack["message"]


def test_select_profile_switching_emits_event_per_switch(cockpit_ws: object) -> None:
    """Each ``select_profile`` invocation emits a fresh ``profile_changed`` frame."""

    ack1 = send_cmd(cockpit_ws, "select_profile", request_id="req-1", profile_id="scene-garage")
    events1 = drain_events(cockpit_ws, 1)

    ack2 = send_cmd(cockpit_ws, "select_profile", request_id="req-2", profile_id="scene-rolling")
    events2 = drain_events(cockpit_ws, 1)

    assert ack1["ok"] is True
    assert events1[0]["profile"]["profile_id"] == "scene-garage"
    assert ack2["ok"] is True
    assert events2[0]["profile"]["profile_id"] == "scene-rolling"


def test_select_profile_with_preview_on_also_emits_mutation_previewed(
    cockpit_ws: object,
) -> None:
    """With preview enabled, ``select_profile`` warms the candidate and emits the preview event."""

    # Turn preview on first (with no active profile this emits a ``None`` candidate).
    send_cmd(cockpit_ws, "toggle_preview", on=True)
    drain_events(cockpit_ws, 1)

    ack = send_cmd(cockpit_ws, "select_profile", profile_id="scene-hypnotic")
    events = drain_events(cockpit_ws, 2)

    assert ack["ok"] is True
    types = [e["type"] for e in events]
    assert EVENT_PROFILE_CHANGED in types
    assert EVENT_MUTATION_PREVIEWED in types
    preview = next(e for e in events if e["type"] == EVENT_MUTATION_PREVIEWED)
    assert preview["candidate"] is not None
    assert preview["candidate"]["profile_id"] == "scene-hypnotic"


def test_select_profile_preview_off_emits_only_profile_changed(cockpit_ws: object) -> None:
    """With preview off, only the ``profile_changed`` event fires after select."""

    ack = send_cmd(cockpit_ws, "select_profile", profile_id="scene-drone")
    events = drain_events(cockpit_ws, 1)

    assert ack["ok"] is True
    assert len(events) == 1
    assert events[0]["type"] == EVENT_PROFILE_CHANGED
