"""WebSocket command coverage for one-at-a-time current-kit capture."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from conftest import elektron_syx_message, rytm_real_layout_kit_payload
from rytm_randomizer.cockpit.capture import KitCaptureService
from rytm_randomizer.cockpit.capture import bridge as capture_bridge
from rytm_randomizer.cockpit.capture import cockpit_snapshot_from_rytm_capture
from rytm_randomizer.cockpit.data import PadState, Snapshot
from rytm_randomizer.cockpit.data.rytm_parameter_map import (
    cockpit_parameter_control,
    cockpit_parameter_key,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.protocol import (
    COMMAND_CAPTURE_CURRENT_KIT,
    COMMAND_LIST_CAPTURE_INPUTS,
    EVENT_DUAL_MACHINE_STAGE_CHANGED,
    EVENT_HISTORY_UPDATED,
    EVENT_KIT_CAPTURES_CHANGED,
    EVENT_SNAPSHOT_CHANGED,
)
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.devices.strategies import RytmSnapshotMachineFacts

pytestmark = pytest.mark.fast


@dataclass(frozen=True)
class _Provider:
    frame: bytes

    def list_input_names(self) -> tuple[str, ...]:
        return ("Rytm Input", "A4 Input")

    def capture_sysex_messages(
        self,
        port_name: str,
        *,
        timeout_seconds: float,
    ) -> tuple[bytes, ...]:
        del port_name, timeout_seconds
        return (self.frame,)


def _session(tmp_path: Path, service: KitCaptureService | None = None) -> CockpitSession:
    snapshot = Snapshot(
        snapshot_id="capture-root",
        device="analog_rytm_mk2",
        captured_at=datetime(2026, 8, 26, tzinfo=timezone.utc),
        pads=(PadState(pad_id=1, machine="BD Hard", params={"tun": 64}),),
        scene_slot=None,
        bpm=124.0,
    )
    device = MockDeviceAdapter(initial=snapshot)
    history = HistoryStore()
    history.initial(snapshot)
    return CockpitSession(
        profile_registry=ProfileRegistry(tmp_path),
        history_store=history,
        device=device,
        kit_capture_service=service or KitCaptureService.disabled(),
    )


def _dispatch(session: CockpitSession, command: dict) -> dict:
    return asyncio.run(
        handle_command(
            {"request_id": "capture-request", "command": command},
            session,
        )
    )


def test_list_capture_inputs_reports_passive_lock_without_enumerating(tmp_path: Path) -> None:
    session = _session(tmp_path)

    ack = _dispatch(
        session,
        {"type": COMMAND_LIST_CAPTURE_INPUTS, "device_id": "analog_rytm_mk2"},
    )

    assert ack == {
        "request_id": "capture-request",
        "ok": True,
        "capture_enabled": False,
        "capture_device_id": "analog_rytm_mk2",
        "capture_inputs": [],
    }
    assert session.pending_events == []


def test_list_capture_inputs_returns_armed_provider_names(tmp_path: Path) -> None:
    frame = elektron_syx_message(rytm_real_layout_kit_payload())
    session = _session(tmp_path, KitCaptureService(_Provider(frame)))

    ack = _dispatch(
        session,
        {"type": COMMAND_LIST_CAPTURE_INPUTS, "device_id": "analog_four_mk2"},
    )

    assert ack["ok"] is True
    assert ack["capture_enabled"] is True
    assert ack["capture_inputs"] == ["Rytm Input", "A4 Input"]


def test_capture_current_kit_updates_full_anchor_event(tmp_path: Path) -> None:
    frame = elektron_syx_message(rytm_real_layout_kit_payload(b"LIVE CURRENT KIT"))
    session = _session(tmp_path, KitCaptureService(_Provider(frame)))

    ack = _dispatch(
        session,
        {
            "type": COMMAND_CAPTURE_CURRENT_KIT,
            "device_id": "analog_rytm_mk2",
            "input_port": " Rytm Input ",
        },
    )

    assert ack["ok"] is True
    assert ack["kit_capture"]["kit_name"] == "LIVE CURRENT KIT"
    assert ack["kit_capture"]["sent_midi"] is False
    assert [event["type"] for event in session.pending_events] == [
        EVENT_KIT_CAPTURES_CHANGED,
        EVENT_SNAPSHOT_CHANGED,
        EVENT_HISTORY_UPDATED,
        EVENT_DUAL_MACHINE_STAGE_CHANGED,
    ]
    assert session.pending_events[0] == {
        "type": EVENT_KIT_CAPTURES_CHANGED,
        "captures": [ack["kit_capture"]],
    }
    promoted = session.device.capture_snapshot()
    assert promoted.snapshot_id != "capture-root"
    assert len(promoted.pads) == 12
    assert session.history_store.current.entries[-1].via == "capture"


def test_captured_rytm_anchor_mutates_and_prepares_only_selected_pad(
    tmp_path: Path,
) -> None:
    frame = elektron_syx_message(rytm_real_layout_kit_payload(b"TARGETED LIVE KIT"))
    session = _session(tmp_path, KitCaptureService(_Provider(frame)))
    _dispatch(
        session,
        {
            "type": COMMAND_CAPTURE_CURRENT_KIT,
            "device_id": "analog_rytm_mk2",
            "input_port": "Rytm Input",
        },
    )
    session.clear_pending_events()
    session.active_profile = session.profile_registry.list_profiles()[0]

    target_ack = _dispatch(
        session,
        {
            "type": "set_mutation_targets",
            "device_id": "analog_rytm_mk2",
            "target_ids": [1],
        },
    )
    assert target_ack["ok"] is True
    assert session.current_candidate is not None
    assert {delta.pad_id for delta in session.current_candidate.pad_deltas} == {1}

    prepare_ack = _dispatch(session, {"type": "prepare_send_plan"})
    assert prepare_ack["ok"] is True
    assert prepare_ack["send_plan"]["ready"] is True
    assert {packet["pad_id"] for packet in prepare_ack["send_plan"]["packets"]} == {1}

    before_send = session.device.capture_snapshot()
    before_untargeted = {pad.pad_id: pad for pad in before_send.pads if pad.pad_id != 1}
    send_ack = _dispatch(session, {"type": "send"})

    assert send_ack["ok"] is True
    after_send = session.device.capture_snapshot()
    after_untargeted = {pad.pad_id: pad for pad in after_send.pads if pad.pad_id != 1}
    assert after_untargeted == before_untargeted


def test_rytm_capture_promotion_fails_closed_on_untrusted_result_shapes() -> None:
    frame = elektron_syx_message(rytm_real_layout_kit_payload(b"FAIL CLOSED"))
    result = KitCaptureService(_Provider(frame)).capture(
        "analog_rytm_mk2",
        "Rytm Input",
    )

    with pytest.raises(ValueError, match="only Analog Rytm"):
        cockpit_snapshot_from_rytm_capture(
            replace(result, device_id="analog_four_mk2")  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="exact codec round-trip"):
        cockpit_snapshot_from_rytm_capture(replace(result, round_trip_verified=False))
    with pytest.raises(TypeError, match="RytmKitSnapshot"):
        cockpit_snapshot_from_rytm_capture(
            replace(result, snapshot=object())  # type: ignore[arg-type]
        )


def test_rytm_capture_promotion_omits_unmapped_or_mismatched_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = elektron_syx_message(rytm_real_layout_kit_payload(b"SAFE ROWS"))
    result = KitCaptureService(_Provider(frame)).capture(
        "analog_rytm_mk2",
        "Rytm Input",
    )
    original_anchor = capture_bridge.build_snapshot_shell_anchor(result.snapshot)
    mapped = next(
        event
        for event in original_anchor.events
        if (
            (key := cockpit_parameter_key(event.machine_key, event.section, event.parameter))
            is not None
            and cockpit_parameter_control(event.machine_key, key) == event.cc_msb
        )
    )
    fake_anchor = replace(
        original_anchor,
        events=(mapped,),
        events_by_pad={
            1: (
                mapped,
                replace(mapped, parameter="Unmapped Parameter"),
                replace(mapped, cc_msb=(mapped.cc_msb + 1) % 128),
            )
        },
    )
    monkeypatch.setattr(
        capture_bridge, "build_snapshot_shell_anchor", lambda _snapshot: fake_anchor
    )

    promoted_with_fallbacks = cockpit_snapshot_from_rytm_capture(result)
    snapshot_without_fallbacks = replace(
        result.snapshot,
        machine_facts=RytmSnapshotMachineFacts(facts_by_pad={}, promoted=False),
    )
    promoted = cockpit_snapshot_from_rytm_capture(
        replace(result, snapshot=snapshot_without_fallbacks)
    )

    assert promoted_with_fallbacks.pads[1].machine != "Unknown Rytm machine"
    assert len(promoted.pads[0].params) == 1
    assert promoted.pads[1].machine == "Unknown Rytm machine"


@pytest.mark.parametrize(
    "command",
    [
        {"type": COMMAND_LIST_CAPTURE_INPUTS, "device_id": "digitakt"},
        {
            "type": COMMAND_CAPTURE_CURRENT_KIT,
            "device_id": "analog_rytm_mk2",
            "input_port": "",
        },
    ],
)
def test_capture_commands_fail_closed_on_invalid_wire_values(
    tmp_path: Path,
    command: dict,
) -> None:
    session = _session(tmp_path)

    ack = _dispatch(session, command)

    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert session.kit_captures == {}
