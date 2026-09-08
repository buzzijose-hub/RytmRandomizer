"""Integration: connect → initial events (the bootstrap event set).

The spec mandates that any client connecting to ``/ws`` immediately
receives eleven event frames before the command loop opens:

1. ``session_status`` — armed/mock pill, unsaved_sends, midi_port.
2. ``snapshot_changed`` — the device's current parameter state.
3. ``profile_changed`` — the active profile (``None`` on first connect).
4. ``profile_catalog_changed`` — the built-in + user profile catalogue.
5. ``history_updated`` — the snapshot history chain + ``current_id``.
6. ``patch_genome_changed`` — passive four-candidate A4 compiler packet.
7. ``kit_captures_changed`` — complete current-kit anchor set (empty on first boot).
8. ``mutation_targets_changed`` — both explicit include-lists (empty by default).
9. ``mutation_locks_changed`` — both lock deny-lists (empty by default).
10. ``dual_machine_stage_changed`` — coordinated Rytm/A4 authority state.
11. ``performance_console_changed`` — passive 12-pad performance console packet.

This file pins that contract end-to-end across the FastAPI / TestClient
boundary. Subsequent integration tests rely on the same ordering when
they drain via the :func:`cockpit_ws` fixture, so a regression here
fails first and gives the clearest signal.

The Spec reference: see ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"v10 Cockpit Binding to the Protocol" — "Connect: server emits ...".
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from cockpit.conftest import (
    _make_default_snapshot,
    collect_initial_events,
    complete_handshake,
)
from fastapi.testclient import TestClient

from conftest import elektron_syx_message, rytm_real_layout_kit_payload
from rytm_randomizer.cockpit.capture import KitCaptureService
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.protocol import (
    EVENT_DUAL_MACHINE_STAGE_CHANGED,
    EVENT_HISTORY_UPDATED,
    EVENT_KIT_CAPTURES_CHANGED,
    EVENT_MUTATION_LOCKS_CHANGED,
    EVENT_MUTATION_TARGETS_CHANGED,
    EVENT_PATCH_GENOME_CHANGED,
    EVENT_PERFORMANCE_CONSOLE_CHANGED,
    EVENT_PROFILE_CATALOG_CHANGED,
    EVENT_PROFILE_CHANGED,
    EVENT_SESSION_STATUS,
    EVENT_SNAPSHOT_CHANGED,
    WS_SUBPROTOCOL,
)
from rytm_randomizer.cockpit.ws.session import CockpitSession

pytestmark = pytest.mark.fast

_ARM_TOKEN = "acceptance-rehearsal-arm-token"
_INPUT_PORT = "Elektron Analog Rytm MK2 In"
_OUTPUT_PORT = "Elektron Analog Rytm MK2 Out"


@dataclass
class _RecordingOutput:
    """Software-only output used to prove the exact prepared plan was sent."""

    sent: list[object] = field(default_factory=list)
    close_calls: int = 0

    def send(self, message: object) -> None:
        self.sent.append(message)

    def close(self) -> None:
        self.close_calls += 1


@dataclass
class _RehearsalMidiAuthority:
    """Injected capture + output authority; never imports or opens real MIDI."""

    frame: bytes
    output: _RecordingOutput = field(default_factory=_RecordingOutput)
    capture_calls: list[str] = field(default_factory=list)
    open_output_calls: list[str] = field(default_factory=list)

    def list_input_names(self) -> tuple[str, ...]:
        return (_INPUT_PORT,)

    def capture_sysex_messages(
        self,
        port_name: str,
        *,
        timeout_seconds: float,
    ) -> tuple[bytes, ...]:
        assert timeout_seconds > 0
        self.capture_calls.append(port_name)
        return (self.frame,)

    def list_output_names(self) -> tuple[str, ...]:
        return (_OUTPUT_PORT,)

    def open_output(self, port_name: str) -> _RecordingOutput:
        self.open_output_calls.append(port_name)
        return self.output


def _dispatch(session: CockpitSession, command: dict[str, object]) -> dict[str, object]:
    return asyncio.run(
        handlers.handle_command(
            {"request_id": "acceptance-rehearsal", "command": command},
            session,
        )
    )


def test_initial_events_on_connect(cockpit_client: TestClient) -> None:
    """On connect, server emits the full eleven-event bootstrap packet."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws)

    types = {e["type"] for e in events}
    assert types == {
        EVENT_SESSION_STATUS,
        EVENT_SNAPSHOT_CHANGED,
        EVENT_PROFILE_CHANGED,
        EVENT_PROFILE_CATALOG_CHANGED,
        EVENT_HISTORY_UPDATED,
        EVENT_PATCH_GENOME_CHANGED,
        EVENT_KIT_CAPTURES_CHANGED,
        EVENT_MUTATION_TARGETS_CHANGED,
        EVENT_MUTATION_LOCKS_CHANGED,
        EVENT_DUAL_MACHINE_STAGE_CHANGED,
        EVENT_PERFORMANCE_CONSOLE_CHANGED,
    }


def test_initial_events_order_is_stable(cockpit_client: TestClient) -> None:
    """The bootstrap event set arrives in the documented order."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws)

    types_in_order = [e["type"] for e in events]
    assert types_in_order == [
        EVENT_SESSION_STATUS,
        EVENT_SNAPSHOT_CHANGED,
        EVENT_PROFILE_CHANGED,
        EVENT_PROFILE_CATALOG_CHANGED,
        EVENT_HISTORY_UPDATED,
        EVENT_PATCH_GENOME_CHANGED,
        EVENT_KIT_CAPTURES_CHANGED,
        EVENT_MUTATION_TARGETS_CHANGED,
        EVENT_MUTATION_LOCKS_CHANGED,
        EVENT_DUAL_MACHINE_STAGE_CHANGED,
        EVENT_PERFORMANCE_CONSOLE_CHANGED,
    ]


def test_initial_session_status_marks_mock_mode(cockpit_client: TestClient) -> None:
    """Mock device adapter reports ``mode='mock'``, ``armed=False``, ``midi_port=None``."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws)

    status = next(e for e in events if e["type"] == EVENT_SESSION_STATUS)
    assert status["mode"] == "mock"
    assert status["armed"] is False
    assert status["midi_port"] is None
    assert status["unsaved_sends"] == 0


def test_initial_snapshot_event_carries_reference_pads(cockpit_client: TestClient) -> None:
    """The bootstrap snapshot event reflects the 12-pad reference layout."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws)

    snapshot = next(e for e in events if e["type"] == EVENT_SNAPSHOT_CHANGED)["snapshot"]
    pad_ids = [pad["pad_id"] for pad in snapshot["pads"]]
    machines = [pad["machine"] for pad in snapshot["pads"]]
    assert pad_ids == list(range(1, 13))
    assert machines == [
        "BD Hard",
        "SD Classic",
        "CH Closed",
        "OH Open",
        "BT Rim",
        "LT Low",
        "MT Mid",
        "HT High",
        "CP Clap",
        "RS Riser",
        "SY Raw",
        "BD Acoustic",
    ]
    assert snapshot["device"] == "analog_rytm_mk2"


def test_initial_profile_event_is_null_on_fresh_session(cockpit_client: TestClient) -> None:
    """No profile is active on connect; the profile_changed event payload is ``None``."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws)

    profile = next(e for e in events if e["type"] == EVENT_PROFILE_CHANGED)["profile"]
    assert profile is None


def test_initial_history_event_has_root_entry(cockpit_client: TestClient) -> None:
    """The bootstrap history strip carries the root snapshot as ``current_id``."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws)

    history = next(e for e in events if e["type"] == EVENT_HISTORY_UPDATED)["history"]
    assert len(history["entries"]) == 1
    assert history["current_id"] == history["entries"][0]["snapshot"]["snapshot_id"]
    assert history["entries"][0]["kind"] == "auto"
    assert history["entries"][0]["parent_id"] is None


def test_initial_performance_console_event_is_passive(cockpit_client: TestClient) -> None:
    """The bootstrap performance-console packet remains passive and 12-pad aware."""

    with cockpit_client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
        complete_handshake(ws)
        events = collect_initial_events(ws)

    model = next(e for e in events if e["type"] == EVENT_PERFORMANCE_CONSOLE_CHANGED)[
        "performance_console"
    ]
    assert model["console_version"] == "live-gui-performance-console-v1"
    assert model["hardware_mode"] == "passive"
    assert model["rytm_pad_surface"]["pad_count"] == 12
    assert "open_midi_port_without_arm" in model["blocked_actions"]


def test_verified_capture_to_targeted_send_and_snapshot_recovery(tmp_path: Path) -> None:
    """Rehearse one complete live set with verified input and fake output only."""

    authority = _RehearsalMidiAuthority(
        elektron_syx_message(rytm_real_layout_kit_payload(b"ACCEPT LIVE KIT"))
    )
    initial = _make_default_snapshot()
    device = MockDeviceAdapter(initial)
    history = HistoryStore()
    history.initial(initial)
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=history,
        device=device,
        kit_capture_service=KitCaptureService(authority),
        arm_secret=_ARM_TOKEN,
    )
    session.arm_port_provider = authority

    capture_ack = _dispatch(
        session,
        {
            "type": "capture_current_kit",
            "device_id": "analog_rytm_mk2",
            "input_port": _INPUT_PORT,
        },
    )

    assert capture_ack["ok"] is True
    capture = capture_ack["kit_capture"]
    assert capture["kit_name"] == "ACCEPT LIVE KIT"
    assert capture["round_trip_verified"] is True
    assert capture["input_only"] is True
    assert capture["sent_midi"] is False
    assert authority.capture_calls == [_INPUT_PORT]
    assert authority.open_output_calls == []
    captured_snapshot = device.capture_snapshot()
    captured_snapshot_id = captured_snapshot.snapshot_id
    assert len(captured_snapshot.pads) == 12
    assert history.current.entries[-1].via == "capture"
    assert session.stage_coordinator.state.rytm.capture_state == "captured"
    assert session.stage_coordinator.state.rytm.authority_state == "not_armed"

    target_ack = _dispatch(
        session,
        {
            "type": "set_mutation_targets",
            "device_id": "analog_rytm_mk2",
            "target_ids": [1, 2],
        },
    )
    lock_ack = _dispatch(
        session,
        {"type": "set_pad_lock", "pad_id": 2, "locked": True},
    )
    assert target_ack["ok"] is True
    assert lock_ack["ok"] is True
    assert session.rytm_pad_targets == {1, 2}
    assert session.pad_locks == {2}
    assert session.stage_coordinator.state.rytm.effective_ids == frozenset({1})

    assert (
        _dispatch(
            session,
            {"type": "select_profile", "profile_id": "scene-industrial"},
        )["ok"]
        is True
    )
    depth_ack = _dispatch(session, {"type": "set_depth", "depth": 0.55})
    preview_ack = _dispatch(session, {"type": "toggle_preview", "on": True})
    assert depth_ack["ok"] is True
    assert preview_ack["ok"] is True
    assert session.depth == 0.55
    assert session.preview_on is True
    assert session.current_candidate is not None
    # Preview and final SEND share the canonical targets-minus-locks scope.
    assert {delta.pad_id for delta in session.current_candidate.pad_deltas} == {1}

    prepare_ack = _dispatch(session, {"type": "prepare_send_plan"})
    assert prepare_ack["ok"] is True
    plan = session.current_send_plan
    assert plan is not None
    plan_payload = prepare_ack["send_plan"]
    expected_message_count = len(plan.packets)
    assert plan_payload["plan_id"] == plan.plan_id
    assert plan_payload["source_snapshot_id"] == captured_snapshot_id
    assert plan_payload["target_pad_ids"] == [1, 2]
    assert plan_payload["locked_pad_ids"] == [2]
    assert plan_payload["pad_count"] == 1
    assert plan_payload["estimated_midi_msgs"] == expected_message_count
    assert len(plan_payload["packets"]) == expected_message_count
    assert expected_message_count > 0
    assert {packet.pad_id for packet in plan.packets} == {1}
    assert session.stage_coordinator.state.rytm.plan_state == "ready"

    arm_ack = _dispatch(
        session,
        {
            "type": "arm",
            "arm_token": _ARM_TOKEN,
            "confirm": True,
            "port_name": _OUTPUT_PORT,
        },
    )
    assert arm_ack["ok"] is True
    assert session.armed_apply is not None
    assert session.device is device
    assert authority.open_output_calls == [_OUTPUT_PORT]
    assert authority.output.sent == []
    assert session.stage_coordinator.state.rytm.authority_state == "armed"
    assert session.stage_coordinator.state.analog_four.authority_state == "blocked"

    before_send = device.capture_snapshot()
    send_ack = _dispatch(
        session,
        {
            "type": "send",
            "confirm": True,
            "send_plan_id": plan.plan_id,
        },
    )

    assert send_ack["ok"] is True
    assert send_ack["send_plan_id"] == plan.plan_id
    assert authority.output.sent == [
        (packet.channel, packet.control, packet.value) for packet in plan.packets
    ]
    assert len(authority.output.sent) == expected_message_count
    assert session.stage_coordinator.state.rytm.plan_state == "none"
    after_send = device.capture_snapshot()
    assert send_ack["new_snapshot_id"] == after_send.snapshot_id
    before_by_pad = {pad.pad_id: pad for pad in before_send.pads}
    after_by_pad = {pad.pad_id: pad for pad in after_send.pads}
    assert after_by_pad[2] == before_by_pad[2]
    assert {pad_id: after_by_pad[pad_id] for pad_id in range(3, 13)} == {
        pad_id: before_by_pad[pad_id] for pad_id in range(3, 13)
    }

    load_ack = _dispatch(
        session,
        {"type": "load_snapshot", "snapshot_id": captured_snapshot_id},
    )
    assert load_ack["ok"] is True
    assert load_ack["snapshot_id"] == captured_snapshot_id
    assert history.current.current_id == captured_snapshot_id
    device.adopt_snapshot(captured_snapshot)
    assert device.capture_snapshot() == captured_snapshot

    sent_snapshot_id = after_send.snapshot_id
    assert (
        _dispatch(
            session,
            {"type": "load_snapshot", "snapshot_id": sent_snapshot_id},
        )["ok"]
        is True
    )
    device.adopt_snapshot(after_send)
    undo_ack = _dispatch(session, {"type": "undo"})
    assert undo_ack["ok"] is True
    assert undo_ack["snapshot_id"] == captured_snapshot_id
    recovered = next(
        entry.snapshot
        for entry in history.current.entries
        if entry.snapshot.snapshot_id == history.current.current_id
    )
    device.adopt_snapshot(recovered)
    assert device.capture_snapshot() == captured_snapshot

    disarm_ack = _dispatch(session, {"type": "disarm"})
    assert disarm_ack["ok"] is True
    assert authority.output.close_calls == 1
    assert session.stage_coordinator.state.rytm.authority_state == "not_armed"
