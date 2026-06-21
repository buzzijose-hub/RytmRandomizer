"""Integration: every command type round-trips correctly over the WebSocket.

For each of the 12 spec commands, sends an envelope and verifies:

* the ack frame's ``request_id`` echoes the request,
* ``ok`` is ``True`` for valid commands,
* the command-specific result keys are present where the spec requires them
  (``candidate`` / ``new_snapshot_id`` / ``snapshot_id`` / ``model_bytes_b64``).

Also covers the invalid-input paths the WebSocket boundary cares about:

* Unknown ``command.type`` → ack with ``ok=False, error="unknown command: ..."``.
* Missing required envelope keys → ack with ``ok=False, error="missing key: ..."``.
* Malformed JSON / non-dict envelopes → connection closes cleanly (no server crash).

Why a separate file when ``test_integration_*_flow.py`` already covers each
command's *behavior*? Those files assert on the engine side (events, history,
candidate values). This file pins the **wire contract**: request_id echo,
ack-field presence, and unknown-command degradation. A regression on either
class fails the right file first.

Spec reference: see ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"The Three Protocols" — "Every command is wrapped in CommandEnvelope".
"""

from __future__ import annotations

import pytest
from cockpit.conftest import collect_initial_events, complete_handshake, drain_events, send_cmd
from fastapi.testclient import TestClient

from rytm_randomizer.cockpit.ws.protocol import (
    COMMAND_EXPORT_PROFILE_MODEL,
    COMMAND_LOAD_SNAPSHOT,
    COMMAND_PREPARE_SEND_PLAN,
    COMMAND_REGEN,
    COMMAND_REHEARSE_OPERATOR_PACKAGE_STEP,
    COMMAND_SAVE,
    COMMAND_SELECT_PROFILE,
    COMMAND_SEND,
    COMMAND_SET_DEPTH,
    COMMAND_SET_PAD_LOCK,
    COMMAND_TOGGLE_PREVIEW,
    COMMAND_TYPES,
    COMMAND_UNDO,
    WS_SUBPROTOCOL,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Per-command round-trip: request_id echo + ok=True + command-specific fields.
# ---------------------------------------------------------------------------


def test_select_profile_roundtrips_with_ok_ack(cockpit_ws: object) -> None:
    """``select_profile`` round-trip: request_id echoes, ok=True, no per-cmd fields."""

    ack = send_cmd(
        cockpit_ws,
        COMMAND_SELECT_PROFILE,
        request_id="rt-select",
        profile_id="scene-industrial",
    )
    drain_events(cockpit_ws, 1)

    assert ack["request_id"] == "rt-select"
    assert ack["ok"] is True


def test_set_depth_roundtrips_with_candidate_field(cockpit_ws: object) -> None:
    """``set_depth`` round-trip: ack carries ``candidate`` (None when no profile)."""

    ack = send_cmd(
        cockpit_ws,
        COMMAND_SET_DEPTH,
        request_id="rt-depth",
        depth=0.5,
    )

    assert ack["request_id"] == "rt-depth"
    assert ack["ok"] is True
    # ``candidate`` is always present on a set_depth ack (None or dict).
    assert "candidate" in ack


def test_set_pad_lock_roundtrips_with_no_extras(cockpit_ws: object) -> None:
    """``set_pad_lock`` round-trip: only ``ok`` + ``request_id``."""

    ack = send_cmd(
        cockpit_ws,
        COMMAND_SET_PAD_LOCK,
        request_id="rt-lock",
        pad_id=1,
        locked=True,
    )

    assert ack["request_id"] == "rt-lock"
    assert ack["ok"] is True


def test_toggle_preview_roundtrips_with_candidate_field(cockpit_ws: object) -> None:
    """``toggle_preview`` round-trip: ack carries ``candidate`` field."""

    ack = send_cmd(
        cockpit_ws,
        COMMAND_TOGGLE_PREVIEW,
        request_id="rt-preview",
        on=True,
    )
    drain_events(cockpit_ws, 1)

    assert ack["request_id"] == "rt-preview"
    assert ack["ok"] is True
    assert "candidate" in ack


def test_regen_roundtrips_after_profile_selected(cockpit_ws: object) -> None:
    """``regen`` round-trip: ack carries ``candidate`` after a profile is active."""

    send_cmd(cockpit_ws, COMMAND_SELECT_PROFILE, profile_id="scene-industrial")
    drain_events(cockpit_ws, 1)
    ack = send_cmd(cockpit_ws, COMMAND_REGEN, request_id="rt-regen")

    assert ack["request_id"] == "rt-regen"
    assert ack["ok"] is True
    assert ack["candidate"] is not None


def test_prepare_send_plan_roundtrips_with_send_plan_field(cockpit_ws: object) -> None:
    """``prepare_send_plan`` round-trip: ack carries the inert send-plan packet."""

    send_cmd(cockpit_ws, COMMAND_SELECT_PROFILE, profile_id="scene-industrial")
    drain_events(cockpit_ws, 1)
    send_cmd(cockpit_ws, COMMAND_SET_DEPTH, depth=0.5)
    ack = send_cmd(cockpit_ws, COMMAND_PREPARE_SEND_PLAN, request_id="rt-prepare")
    drain_events(cockpit_ws, 1)

    assert ack["request_id"] == "rt-prepare"
    assert ack["ok"] is True
    assert "send_plan" in ack
    assert ack["send_plan"]["ready"] is True


def test_send_roundtrips_with_new_snapshot_id_field(cockpit_ws: object) -> None:
    """``send`` round-trip: ack carries ``new_snapshot_id``."""

    send_cmd(cockpit_ws, COMMAND_SELECT_PROFILE, profile_id="scene-industrial")
    drain_events(cockpit_ws, 1)
    send_cmd(cockpit_ws, COMMAND_SET_DEPTH, depth=0.5)
    send_cmd(cockpit_ws, COMMAND_PREPARE_SEND_PLAN)
    drain_events(cockpit_ws, 1)
    ack = send_cmd(cockpit_ws, COMMAND_SEND, request_id="rt-send")
    drain_events(cockpit_ws, 5)

    assert ack["request_id"] == "rt-send"
    assert ack["ok"] is True
    assert "new_snapshot_id" in ack
    assert isinstance(ack["new_snapshot_id"], str)


def test_save_roundtrips_with_snapshot_id_field(cockpit_ws: object) -> None:
    """``save`` round-trip: ack carries ``snapshot_id`` of the saved entry."""

    ack = send_cmd(cockpit_ws, COMMAND_SAVE, request_id="rt-save", label="kit-A")
    drain_events(cockpit_ws, 2)

    assert ack["request_id"] == "rt-save"
    assert ack["ok"] is True
    assert "snapshot_id" in ack


def test_load_snapshot_roundtrips_with_snapshot_id_field(cockpit_ws: object) -> None:
    """``load_snapshot`` round-trip: ack echoes the requested snapshot_id."""

    send_cmd(cockpit_ws, COMMAND_SELECT_PROFILE, profile_id="scene-industrial")
    drain_events(cockpit_ws, 1)
    send_cmd(cockpit_ws, COMMAND_SET_DEPTH, depth=0.5)
    send_cmd(cockpit_ws, COMMAND_PREPARE_SEND_PLAN)
    drain_events(cockpit_ws, 1)
    send_cmd(cockpit_ws, COMMAND_SEND)
    drain_events(cockpit_ws, 5)

    ack = send_cmd(
        cockpit_ws,
        COMMAND_LOAD_SNAPSHOT,
        request_id="rt-load",
        snapshot_id="01HXY5Q9PJM00000000000ROOT",
    )
    drain_events(cockpit_ws, 2)

    assert ack["request_id"] == "rt-load"
    assert ack["ok"] is True
    assert ack["snapshot_id"] == "01HXY5Q9PJM00000000000ROOT"


def test_undo_roundtrips_with_snapshot_id_field(cockpit_ws: object) -> None:
    """``undo`` round-trip: ack carries the parent snapshot_id after walking back."""

    send_cmd(cockpit_ws, COMMAND_SELECT_PROFILE, profile_id="scene-industrial")
    drain_events(cockpit_ws, 1)
    send_cmd(cockpit_ws, COMMAND_SET_DEPTH, depth=0.55)
    send_cmd(cockpit_ws, COMMAND_PREPARE_SEND_PLAN)
    drain_events(cockpit_ws, 1)
    send_cmd(cockpit_ws, COMMAND_SEND)
    drain_events(cockpit_ws, 5)

    ack = send_cmd(cockpit_ws, COMMAND_UNDO, request_id="rt-undo")
    drain_events(cockpit_ws, 2)

    assert ack["request_id"] == "rt-undo"
    assert ack["ok"] is True
    assert ack["snapshot_id"] == "01HXY5Q9PJM00000000000ROOT"


def test_export_profile_model_roundtrips_with_model_bytes_b64_field(
    cockpit_ws: object,
) -> None:
    """``export_profile_model`` round-trip: ack carries ``model_bytes_b64``."""

    ack = send_cmd(
        cockpit_ws,
        COMMAND_EXPORT_PROFILE_MODEL,
        request_id="rt-export",
        profile_id="scene-industrial",
        target="binary",
    )

    assert ack["request_id"] == "rt-export"
    assert ack["ok"] is True
    assert "model_bytes_b64" in ack
    assert isinstance(ack["model_bytes_b64"], str)


def test_rehearse_operator_package_step_roundtrips_with_mock_safe_rehearsal_ack(
    cockpit_ws: object,
) -> None:
    """``rehearse_operator_package_step`` returns mock-safe operator package evidence."""

    ack = send_cmd(
        cockpit_ws,
        COMMAND_REHEARSE_OPERATOR_PACKAGE_STEP,
        request_id="rt-operator-package",
        operator_package_id="live-kit-operator-package",
        step_key="operator-step-hard-groove-lift",
        slot_key="hard-groove-lift",
        package_export_key="operator-package-hard-groove-lift",
        snapshot_id="snap-06",
        depth_percent=70,
        mock_safe=True,
    )

    assert ack["request_id"] == "rt-operator-package"
    assert ack["ok"] is True
    rehearsal = ack["operator_package_rehearsal"]
    assert rehearsal["rehearsal_status"] == "mock_safe_ready"
    assert rehearsal["opened_midi_port"] is False
    assert rehearsal["sent_midi"] is False


def test_all_twelve_cockpit_command_types_are_exercised(cockpit_ws: object) -> None:
    """Pin invariant: every cockpit-native command has a matching round-trip test above.

    ``COMMAND_TYPES`` is the union of the cockpit + wizard command surfaces
    (12 cockpit + 8 wizard = 20 total). This test pins the 12 cockpit-native
    commands; the wizard subset is exercised end-to-end in
    ``test_integration_wizard_flow.py``. If a new cockpit command lands and
    this assertion is not extended, the file falls out of sync silently —
    this test makes that drift visible at the integration boundary.
    """

    assert len(COMMAND_TYPES) == 20
    cockpit_native = {
        COMMAND_SELECT_PROFILE,
        COMMAND_SET_DEPTH,
        COMMAND_SET_PAD_LOCK,
        COMMAND_TOGGLE_PREVIEW,
        COMMAND_REGEN,
        COMMAND_PREPARE_SEND_PLAN,
        COMMAND_SEND,
        COMMAND_SAVE,
        COMMAND_LOAD_SNAPSHOT,
        COMMAND_UNDO,
        COMMAND_EXPORT_PROFILE_MODEL,
        COMMAND_REHEARSE_OPERATOR_PACKAGE_STEP,
    }
    assert cockpit_native <= COMMAND_TYPES
    assert len(cockpit_native) == 12


# ---------------------------------------------------------------------------
# Negative paths: unknown command type, missing keys, malformed JSON.
# ---------------------------------------------------------------------------


def test_unknown_command_type_returns_error_ack(cockpit_ws: object) -> None:
    """An unrecognised ``command.type`` returns ``ok=False`` with a clear error."""

    ack = send_cmd(cockpit_ws, "definitely_not_a_command", request_id="rt-bad")

    assert ack["request_id"] == "rt-bad"
    assert ack["ok"] is False
    # PR 14: categorical envelope.
    assert ack["code"] == "unknown_command"
    assert "unknown command" in ack["message"]


def test_envelope_missing_command_key_returns_error_ack(cockpit_ws: object) -> None:
    """An envelope lacking ``command`` returns ``ok=False, code=missing_envelope_key``."""

    cockpit_ws.send_json({"request_id": "rt-no-cmd"})  # type: ignore[attr-defined]
    ack = cockpit_ws.receive_json()  # type: ignore[attr-defined]

    assert ack["request_id"] == "rt-no-cmd"
    assert ack["ok"] is False
    # PR 14: categorical envelope.
    assert ack["code"] == "missing_envelope_key"
    assert "command" in ack["message"]


def test_envelope_command_missing_type_returns_error_ack(cockpit_ws: object) -> None:
    """An envelope whose ``command`` dict lacks ``type`` returns the same shape."""

    cockpit_ws.send_json(  # type: ignore[attr-defined]
        {"request_id": "rt-no-type", "command": {"profile_id": "scene-industrial"}}
    )
    ack = cockpit_ws.receive_json()  # type: ignore[attr-defined]

    assert ack["request_id"] == "rt-no-type"
    assert ack["ok"] is False
    # PR 14: categorical envelope.
    assert ack["code"] == "missing_envelope_key"
    assert "type" in ack["message"]


def test_envelope_missing_request_id_still_dispatches(cockpit_ws: object) -> None:
    """An envelope without ``request_id`` still produces an ack (with empty echo)."""

    cockpit_ws.send_json({"command": {"type": "set_pad_lock", "pad_id": 1, "locked": False}})  # type: ignore[attr-defined]
    ack = cockpit_ws.receive_json()  # type: ignore[attr-defined]

    # The dispatcher defaults the missing request_id to "" rather than crashing.
    assert ack["request_id"] == ""
    assert ack["ok"] is True


def test_malformed_json_closes_connection_but_server_keeps_serving(
    cockpit_client: TestClient,
) -> None:
    """A non-JSON text frame is rejected gracefully; subsequent connects still work.

    Post-PR-1 (CODE_REVIEW.md §C1+SX1) the server reads inbound frames
    as text first (so the size cap can fire before ``json.loads`` ever
    runs). When the body is not valid JSON the server closes the socket
    politely instead of letting the exception propagate. The TestClient
    observes the close without surfacing the underlying
    :class:`json.JSONDecodeError`.

    The load-bearing invariant for the spec's "malformed JSON → graceful
    handling" wording is: **the server process does not die**. We pin
    that by opening a fresh connection after the broken one and
    confirming the bootstrap event set still arrives.
    """

    # The server now closes the socket on malformed JSON; we tolerate
    # any exit shape from the TestClient (clean close, WebSocketDisconnect,
    # or a residual JSONDecodeError on older TestClient versions).
    try:
        with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            complete_handshake(ws)
            collect_initial_events(ws, count=5)
            ws.send_text("this is not json at all")
    except Exception:
        # Either path is acceptable; the spec-bearing assertion is below.
        pass

    # Prove the server still serves: open a fresh connection and bootstrap.
    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        bootstrap = collect_initial_events(ws, count=5)
    assert len(bootstrap) == 5


def test_request_id_round_trips_with_unicode_payload(cockpit_ws: object) -> None:
    """``request_id`` echoes back verbatim even for unicode strings."""

    rid = "req-emoji-🎛️-id"
    ack = send_cmd(cockpit_ws, COMMAND_SET_PAD_LOCK, request_id=rid, pad_id=1, locked=True)

    assert ack["request_id"] == rid
    assert ack["ok"] is True


def test_multiple_commands_per_connection_preserve_request_id_pairing(
    cockpit_ws: object,
) -> None:
    """Five sequential commands on one socket: each ack pairs to its own request_id."""

    expected_ids = [f"rt-multi-{i}" for i in range(5)]
    actual_ids: list[str] = []
    for rid in expected_ids:
        ack = send_cmd(cockpit_ws, COMMAND_SET_PAD_LOCK, request_id=rid, pad_id=1, locked=False)
        actual_ids.append(ack["request_id"])
    assert actual_ids == expected_ids
