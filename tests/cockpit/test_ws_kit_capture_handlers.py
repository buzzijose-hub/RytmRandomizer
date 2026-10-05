"""WebSocket command coverage for one-at-a-time current-kit capture."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from conftest import (
    analog_four_saved_kit_frame,
    elektron_syx_message,
    rytm_frame_with_machine_values,
    rytm_real_layout_kit_payload,
)
from rytm_randomizer.cockpit.capture import KitCaptureService
from rytm_randomizer.cockpit.capture import bridge as capture_bridge
from rytm_randomizer.cockpit.capture import cockpit_snapshot_from_rytm_capture
from rytm_randomizer.cockpit.data import MutationCandidate, PadDelta, PadState, Snapshot
from rytm_randomizer.cockpit.data.rytm_parameter_map import (
    cockpit_parameter_control,
    cockpit_parameter_key,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.engine import mutate
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.protocol import (
    COMMAND_CAPTURE_CURRENT_KIT,
    COMMAND_LIST_CAPTURE_INPUTS,
    EVENT_DUAL_MACHINE_STAGE_CHANGED,
    EVENT_HISTORY_UPDATED,
    EVENT_KIT_CAPTURES_CHANGED,
    EVENT_MUTATION_PREVIEWED,
    EVENT_SNAPSHOT_CHANGED,
)
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.data.analog_rytm_midi import ANALOG_RYTM_MACHINE_SRC_BY_MACHINE
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


@dataclass(frozen=True)
class _TypeErrorProvider:
    """Capture provider whose diagnostic includes its machine-local port."""

    name: str

    def list_input_names(self) -> tuple[str, ...]:
        return (self.name,)

    def capture_sysex_messages(
        self,
        port_name: str,
        *,
        timeout_seconds: float,
    ) -> tuple[bytes, ...]:
        del timeout_seconds
        raise TypeError(f'capture "decoder" failed on {port_name!r}')


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


def test_rytm_capture_bootstraps_empty_history_and_refreshes_preview(tmp_path: Path) -> None:
    frame = elektron_syx_message(rytm_real_layout_kit_payload(b"EMPTY HISTORY"))
    session = _session(tmp_path, KitCaptureService(_Provider(frame)))
    session.history_store = HistoryStore()
    session.active_profile = session.profile_registry.list_profiles()[0]
    session.preview_on = True

    ack = _dispatch(
        session,
        {
            "type": COMMAND_CAPTURE_CURRENT_KIT,
            "device_id": "analog_rytm_mk2",
            "input_port": "Rytm Input",
        },
    )

    assert ack["ok"] is True
    assert [event["type"] for event in session.pending_events] == [
        EVENT_KIT_CAPTURES_CHANGED,
        EVENT_SNAPSHOT_CHANGED,
        EVENT_HISTORY_UPDATED,
        EVENT_MUTATION_PREVIEWED,
        EVENT_DUAL_MACHINE_STAGE_CHANGED,
    ]
    assert session.history_store.current.current_id == session.device.capture_snapshot().snapshot_id
    assert session.history_store.current.entries[-1].via is None
    assert session.pending_events[-2]["candidate"] is not None


def test_a4_capture_retains_exact_evidence_without_touching_rytm_state(
    tmp_path: Path,
) -> None:
    frame = analog_four_saved_kit_frame(name=b"LIVE A4 KIT")
    session = _session(tmp_path, KitCaptureService(_Provider(frame)))
    rytm_snapshot = session.device.capture_snapshot()
    rytm_history = session.history_store.current

    ack = _dispatch(
        session,
        {
            "type": COMMAND_CAPTURE_CURRENT_KIT,
            "device_id": "analog_four_mk2",
            "input_port": "A4 Input",
        },
    )

    assert ack["ok"] is True
    assert ack["kit_capture"]["device_id"] == "analog_four_mk2"
    assert ack["kit_capture"]["parameter_readiness"] == "filter1_frequency_offline_ready"
    assert [event["type"] for event in session.pending_events] == [
        EVENT_KIT_CAPTURES_CHANGED,
        EVENT_DUAL_MACHINE_STAGE_CHANGED,
    ]
    assert session.device.capture_snapshot() == rytm_snapshot
    assert session.history_store.current == rytm_history


def _single_parameter_candidate(session: CockpitSession, parameter: str) -> MutationCandidate:
    candidate = session.current_candidate
    assert candidate is not None
    pad = session.device.capture_snapshot().pads[0]
    before = pad.params[parameter]
    return replace(
        candidate,
        pad_deltas=(
            PadDelta(
                pad_id=pad.pad_id,
                proposed_params={**pad.params, parameter: before - 1 if before > 0 else 1},
                changed_keys=frozenset({parameter}),
            ),
        ),
        estimated_midi_msgs=1,
    )


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
    session.current_candidate = _single_parameter_candidate(session, "flt")

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


@pytest.mark.parametrize(("target_pad_id", "seed"), ((1, 21), (2, 27), (6, 12), (8, 7)))
def test_target_unit_capture_preserves_machine_src_through_targeted_planning(
    tmp_path: Path, rytm_rio_return_frame: bytes, target_pad_id: int, seed: int
) -> None:
    session = _session(tmp_path, KitCaptureService(_Provider(rytm_rio_return_frame)))
    capture_ack = _dispatch(
        session,
        {
            "type": COMMAND_CAPTURE_CURRENT_KIT,
            "device_id": "analog_rytm_mk2",
            "input_port": "Rytm Input",
        },
    )
    assert capture_ack["ok"] is True
    capture = session.kit_captures["analog_rytm_mk2"]
    assert capture.frame == rytm_rio_return_frame
    assert capture.round_trip_verified is True
    assert all(
        row["status"] == "mutation_ready" for row in capture_ack["kit_capture"]["layout_items"]
    )
    anchor = capture_bridge.build_snapshot_shell_anchor(capture.snapshot)
    snapshot = session.device.capture_snapshot()
    expected_src = {
        1: {
            "tun": 59,
            "dec": 58,
            "sweep_depth": 40,
            "swt": 81,
            "hold": 93,
            "tick": 1,
            "wave": 11,
        },
        2: {
            "tun": 71,
            "dec": 34,
            "sweep_depth": 26,
            "tick": 84,
            "noise_decay": 28,
            "noise_level": 60,
            "swt": 30,
        },
        6: {
            "tun": 46,
            "dec": 64,
            "sweep_depth": 28,
            "swt": 36,
            "noise_decay": 28,
            "noise_level": 18,
            "noise_tone": 34,
        },
        7: {
            "tun": 60,
            "dec": 44,
            "sweep_depth": 20,
            "swt": 26,
            "noise_decay": 20,
            "noise_level": 20,
            "noise_tone": 56,
        },
        8: {
            "tun": 78,
            "dec": 32,
            "sweep_depth": 14,
            "swt": 18,
            "noise_decay": 18,
            "noise_level": 24,
            "noise_tone": 82,
        },
    }
    for pad_id, expected in expected_src.items():
        pad = snapshot.pads[pad_id - 1]
        assert {key: pad.params[key] for key in expected} == expected
        source_events = tuple(
            event for event in anchor.events_by_pad[pad_id] if event.source == "machine_src"
        )
        assert len(source_events) == len(expected)
        for event in source_events:
            compact_key = cockpit_parameter_key(event.machine_key, event.section, event.parameter)
            assert compact_key is not None
            assert cockpit_parameter_control(event.machine_key, compact_key) == event.cc_msb
        assert "lev" not in pad.params
        assert "amp_volume" not in pad.params
    # Descriptive fallback bindings do not promote protected source values.
    assert not any(key.startswith("src_cy_ride_") for key in snapshot.pads[10].params)
    assert "tun" not in snapshot.pads[10].params
    assert "tun" not in snapshot.pads[11].params

    session.active_profile = session.profile_registry.list_profiles()[0]
    targets = frozenset({target_pad_id, 7})
    locks = frozenset({7})
    assert (
        _dispatch(
            session,
            {
                "type": "set_mutation_targets",
                "device_id": "analog_rytm_mk2",
                "target_ids": sorted(targets),
            },
        )["ok"]
        is True
    )
    assert _dispatch(session, {"type": "set_pad_lock", "pad_id": 7, "locked": True})["ok"] is True
    candidate = mutate(
        snapshot,
        session.active_profile,
        0.1,
        seed,
        target_pad_ids=targets,
        locked_pad_ids=locks,
    )
    assert {delta.pad_id for delta in candidate.pad_deltas} == targets - locks
    assert all(delta.changed_keys for delta in candidate.pad_deltas)
    # Fixed seeds exercise the public all-parameter engine without changing
    # paired LFO Depth or stripping common fields from the captured anchor.
    assert all(
        delta.changed_keys & expected_src[delta.pad_id].keys() for delta in candidate.pad_deltas
    )
    assert all("lfo_depth" not in delta.changed_keys for delta in candidate.pad_deltas)
    session.current_candidate = candidate
    prepared = _dispatch(session, {"type": "prepare_send_plan"})
    assert prepared["ok"] is True
    assert prepared["send_plan"]["ready"] is True
    packets = prepared["send_plan"]["packets"]
    assert {packet["pad_id"] for packet in packets} == targets - locks
    assert any(packet["parameter"] in expected_src[target_pad_id] for packet in packets)
    for packet in packets:
        pad = snapshot.pads[packet["pad_id"] - 1]
        assert packet["parameter"] in pad.params
        assert packet["control"] == cockpit_parameter_control(pad.machine, packet["parameter"])
        assert packet["channel"] == pad.pad_id - 1
    assert session.device.capture_snapshot() == snapshot
    assert session.kit_captures["analog_rytm_mk2"] is capture


@pytest.mark.parametrize(
    "slot", tuple(row.nrpn_lsb for row in ANALOG_RYTM_MACHINE_SRC_BY_MACHINE["cy_ride"])
)
def test_every_cy_ride_src_proposal_refuses_send_of_its_safe_common_subset(
    tmp_path: Path, rytm_rio_return_frame: bytes, slot: int
) -> None:
    session = _session(tmp_path, KitCaptureService(_Provider(rytm_rio_return_frame)))
    captured = _dispatch(
        session,
        {
            "type": COMMAND_CAPTURE_CURRENT_KIT,
            "device_id": "analog_rytm_mk2",
            "input_port": "Rytm Input",
        },
    )
    assert captured["ok"] is True
    capture = session.kit_captures["analog_rytm_mk2"]
    source_bytes = capture.snapshot.unpacked
    snapshot = session.device.capture_snapshot()
    ride = snapshot.pads[10]
    assert ride.pad_id == 11 and ride.machine == "CY Ride"
    assert not any(key.startswith("src_cy_ride_") for key in ride.params)
    key = f"src_cy_ride_{slot}"
    session.active_profile = session.profile_registry.list_profiles()[0]
    session.current_candidate = MutationCandidate(
        candidate_id=f"ride-slot-{slot}",
        source_snapshot_id=snapshot.snapshot_id,
        profile_id=session.active_profile.profile_id,
        depth=0.1,
        seed=12,
        safety_status="safe",
        pad_deltas=(
            PadDelta(
                pad_id=11,
                proposed_params={key: 1, "flt": (ride.params["flt"] + 1) % 128},
                changed_keys=frozenset({key, "flt"}),
            ),
        ),
        estimated_midi_msgs=2,
    )
    prepared = _dispatch(session, {"type": "prepare_send_plan"})
    assert prepared["ok"] is True
    assert prepared["send_plan"]["ready"] is False
    assert prepared["send_plan"]["blocked_reasons"] == ["candidate_high_risk"]
    assert [packet["parameter"] for packet in prepared["send_plan"]["packets"]] == ["flt"]
    refused = _dispatch(session, {"type": "send"})
    assert refused["ok"] is False
    assert "no ready send plan" in refused["message"]
    assert session.device.capture_snapshot() == snapshot
    assert session.kit_captures["analog_rytm_mk2"] is capture
    assert capture.frame == rytm_rio_return_frame and capture.round_trip_verified
    assert capture.snapshot.unpacked == source_bytes  # Includes unknown and low bytes.


@pytest.mark.parametrize("machine_value", (0, 15, 16, 127, 0x88))
def test_unverified_tom_capture_does_not_acquire_sendable_machine_src(
    tmp_path: Path, rytm_rio_return_frame: bytes, machine_value: int
) -> None:
    frame = rytm_frame_with_machine_values(rytm_rio_return_frame, {6: machine_value})
    session = _session(tmp_path, KitCaptureService(_Provider(frame)))
    capture_ack = _dispatch(
        session,
        {
            "type": COMMAND_CAPTURE_CURRENT_KIT,
            "device_id": "analog_rytm_mk2",
            "input_port": "Rytm Input",
        },
    )
    assert capture_ack["ok"] is True
    capture = session.kit_captures["analog_rytm_mk2"]
    assert capture.frame == frame
    assert capture.round_trip_verified is True
    assert capture_ack["kit_capture"]["layout_items"][5]["status"] == "captured_mapping_pending"
    fact = capture.snapshot.machine_facts.facts_by_pad[6]
    assert fact.raw_machine_value == machine_value
    assert fact.decoded_machine_value is None
    assert fact.promoted is False

    anchor = capture_bridge.build_snapshot_shell_anchor(capture.snapshot)
    source_events = tuple(
        event for event in anchor.events_by_pad.get(6, ()) if event.source == "machine_src"
    )
    if machine_value == 0x88:
        assert len(source_events) == 7
        assert all(event.machine_key == "xt_classic" for event in source_events)
    snapshot = session.device.capture_snapshot()
    pad = snapshot.pads[5]
    for event in source_events:
        compact_key = cockpit_parameter_key(event.machine_key, event.section, event.parameter)
        assert compact_key is None or compact_key not in pad.params
    xt_source_keys = {
        "tun",
        "dec",
        "sweep_depth",
        "swt",
        "noise_decay",
        "noise_level",
        "noise_tone",
    }
    assert not (xt_source_keys & pad.params.keys())
    baseline = cockpit_snapshot_from_rytm_capture(
        KitCaptureService(_Provider(rytm_rio_return_frame)).capture("analog_rytm_mk2", "Rytm Input")
    )
    for key in ("flt", "overdrive", "reverb", "lfo_depth"):
        assert pad.params[key] == baseline.pads[5].params[key]
    if machine_value == 127:
        assert pad.machine == "Unknown Rytm machine"

    session.active_profile = session.profile_registry.list_profiles()[0]
    session.rytm_pad_targets = {6}
    session.current_candidate = mutate(
        snapshot,
        session.active_profile,
        0.1,
        8,
        target_pad_ids=frozenset({6}),
    )
    changed_keys = session.current_candidate.pad_deltas[0].changed_keys
    assert changed_keys
    assert not (changed_keys & xt_source_keys)
    assert "lfo_depth" not in changed_keys
    prepared = _dispatch(session, {"type": "prepare_send_plan"})
    assert prepared["ok"] is True
    assert prepared["send_plan"]["ready"] is True
    packets = prepared["send_plan"]["packets"]
    assert packets
    assert {packet["pad_id"] for packet in packets} == {6}
    assert all(packet["parameter"] in pad.params for packet in packets)
    assert all(packet["parameter"] not in xt_source_keys for packet in packets)
    assert session.device.capture_snapshot() == snapshot


def test_captured_rytm_paired_field_is_retained_but_refuses_a_send(
    tmp_path: Path, rytm_rio_return_frame: bytes
) -> None:
    session = _session(tmp_path, KitCaptureService(_Provider(rytm_rio_return_frame)))
    assert (
        _dispatch(
            session,
            {
                "type": COMMAND_CAPTURE_CURRENT_KIT,
                "device_id": "analog_rytm_mk2",
                "input_port": "Rytm Input",
            },
        )["ok"]
        is True
    )
    capture = session.kit_captures["analog_rytm_mk2"]
    before_snapshot = session.device.capture_snapshot()
    before_history = session.history_store.current
    assert "lfo_depth" in before_snapshot.pads[0].params
    session.active_profile = session.profile_registry.list_profiles()[0]
    assert (
        _dispatch(
            session,
            {"type": "set_mutation_targets", "device_id": "analog_rytm_mk2", "target_ids": [1]},
        )["ok"]
        is True
    )
    session.current_candidate = _single_parameter_candidate(session, "lfo_depth")

    prepared = _dispatch(session, {"type": "prepare_send_plan"})
    assert prepared["ok"] is True
    assert prepared["send_plan"]["ready"] is False
    assert prepared["send_plan"]["readiness_reason"] == "paired_control_precision_unverified"
    assert prepared["send_plan"]["packets"] == []
    assert _dispatch(session, {"type": "send"})["ok"] is False
    assert session.device.capture_snapshot() == before_snapshot
    assert session.history_store.current == before_history
    assert session.kit_captures["analog_rytm_mk2"] is capture


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
            event.source == "machine_src"
            and (key := cockpit_parameter_key(event.machine_key, event.section, event.parameter))
            is not None
            and cockpit_parameter_control(event.machine_key, key) == event.cc_msb
        )
    )
    common = next(event for event in original_anchor.events if event.section == "FILTER")
    fake_anchor = replace(
        original_anchor,
        events=(mapped, common),
        events_by_pad={
            1: (
                mapped,
                common,
                replace(mapped, parameter="Unmapped Parameter"),
                replace(mapped, cc_msb=(mapped.cc_msb + 1) % 128),
                replace(mapped, section="xt_classic"),
                replace(mapped, machine_key="xt_classic", section="xt_classic"),
                replace(
                    mapped, machine_key="unknown_future_machine", section="unknown_future_machine"
                ),
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
    assert len(promoted_with_fallbacks.pads[0].params) == 2
    assert len(promoted.pads[0].params) == 1
    assert "tun" not in promoted.pads[0].params
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


@pytest.mark.parametrize(
    "private_port",
    [
        "PRIVATE_INPUT_Jose's_Rytm",
        'PRIVATE_INPUT_"Jose_Rytm"',
        "PRIVATE_INPUT_Jose\\Rytm\nControl\tPort",
    ],
)
def test_capture_type_error_records_failure_without_logging_the_port(
    tmp_path: Path,
    ws_handler_caplog: pytest.LogCaptureFixture,
    private_port: str,
) -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()
    session = _session(tmp_path, KitCaptureService(_TypeErrorProvider(private_port)))

    with ws_handler_caplog.at_level(logging.WARNING):
        ack = _dispatch(
            session,
            {
                "type": COMMAND_CAPTURE_CURRENT_KIT,
                "device_id": "analog_rytm_mk2",
                "input_port": private_port,
            },
        )

    assert ack["ok"] is False
    assert session.stage_coordinator.state.rytm.capture_state == "failed"
    assert session.error_journal.entries[-1].fingerprint == "cockpit.capture.failed"
    assert get_metrics().errors_by_kind["cockpit.capture.failed"] == 1
    record = next(
        record for record in ws_handler_caplog.records if record.msg == "cockpit_kit_capture_failed"
    )
    exception_repr = str(record.__dict__["exception_repr"])
    assert exception_repr == "TypeError('<redacted-midi-port>')"
    assert private_port not in exception_repr
    assert private_port.encode("unicode_escape").decode("ascii") not in exception_repr
    assert "<redacted-midi-port>" in exception_repr
    reset_metrics()
