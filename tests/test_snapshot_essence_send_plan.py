import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def pack_7bit_payload(payload):
    packed = bytearray()
    for index in range(0, len(payload), 7):
        chunk = payload[index : index + 7]
        mask = 0
        data = bytearray()
        for bit, value in enumerate(chunk):
            if value & 0x80:
                mask |= 1 << bit
            data.append(value & 0x7F)
        packed.append(mask)
        packed.extend(data)
    return bytes(packed)


def make_rytm_kit_record(
    slot_index=0,
    kit_name="ESS SEND",
    machine_values=None,
    pad_parameter_values=None,
):
    machine_values = machine_values or tuple(27 for _ in range(12))
    pad_parameter_values = pad_parameter_values or {}
    decoded = bytearray(58 + (12 * 162) + 8)
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    for pad in range(1, 13):
        sound_name = f"SOUND {pad}"
        offset = 58 + ((pad - 1) * 162)
        track_offset = 46 + ((pad - 1) * 162)
        decoded[offset : offset + len(sound_name)] = sound_name.encode("ascii")
        decoded[track_offset + 0x7C] = machine_values[pad - 1]
        for parameter_offset, value in pad_parameter_values.get(pad, {}).items():
            decoded[track_offset + parameter_offset] = value
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, slot_index])
        + pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


def write_send_plan_fixture(path):
    path.write_bytes(
        make_rytm_kit_record(
            machine_values=(0, 27, 13) + tuple(27 for _ in range(9)),
            pad_parameter_values={
                1: {
                    0x1E: 59,
                    0x20: 68,
                    0x44: 25,
                    0x46: 14,
                    0x4A: 65,
                    0x50: 121,
                },
                3: {
                    0x1E: 71,
                    0x20: 88,
                    0x44: 77,
                    0x46: 20,
                    0x4A: 51,
                    0x50: 96,
                },
            },
        )
    )


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_snapshot_essence_send_plan_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.snapshot_essence_send_plan; "
                "assert 'mido' not in sys.modules; "
                "assert 'rtmidi' not in sys.modules; "
                "assert 'librosa' not in sys.modules"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_snapshot_essence_send_plan_orders_switches_anchors_and_snapshot_changes(tmp_path):
    from rytm_randomizer.snapshot_essence_send_plan import (
        build_snapshot_essence_send_plan_from_file,
    )

    sysex_path = tmp_path / "essence-send.syx"
    write_send_plan_fixture(sysex_path)

    plan = build_snapshot_essence_send_plan_from_file(
        sysex_path,
        slot=1,
        depth="micro",
        style="Birmingham dark techno",
        discovery=0.35,
    )

    assert plan.kit_name == "ESS SEND"
    assert plan.ready is True
    assert plan.blocked_pad_count == 0
    assert plan.same_engine_pad_count == 2
    assert plan.engine_switch_pad_count == 10
    assert plan.machine_switch_event_count == 10
    assert plan.snapshot_mutation_event_count == 11
    assert plan.selected_profile_anchor_event_count > 10
    assert plan.event_count == len(plan.events)

    pad1_events = [event for event in plan.events if event.pad == 1]
    assert {event.event_role for event in pad1_events} == {"snapshot_mutation"}
    assert pad1_events[0].control == 17
    assert pad1_events[0].value == 60
    assert pad1_events[0].source == "captured_snapshot_mutation"

    pad5_events = [event for event in plan.events if event.pad == 5]
    assert pad5_events[0].event_role == "machine_switch"
    assert pad5_events[0].control == 15
    assert pad5_events[0].value == 0
    assert pad5_events[0].source == "style_engine_switch"
    assert pad5_events[1].event_role == "selected_profile_anchor"
    assert pad5_events[1].source == "selected_profile_anchor"
    assert all(event.eligible for event in plan.events)


def test_snapshot_essence_send_plan_mock_capture_matches_eligible_events(tmp_path):
    from rytm_randomizer.snapshot_essence_send_plan import (
        build_snapshot_essence_send_plan_from_file,
        capture_snapshot_essence_send_mock_messages,
    )

    sysex_path = tmp_path / "essence-send.syx"
    write_send_plan_fixture(sysex_path)
    plan = build_snapshot_essence_send_plan_from_file(
        sysex_path,
        slot=1,
        depth="micro",
        style="Birmingham dark techno",
    )

    sender = capture_snapshot_essence_send_mock_messages(plan)

    assert len(sender.sent_messages) == plan.eligible_event_count
    first = sender.sent_messages[0]
    assert first.type == "cc"
    assert first.channel == 0
    assert first.control == 17
    assert first.metadata["device"] == "Analog Rytm MKII"
    assert first.metadata["source_kind"] == "snapshot_essence_send_plan"
    assert first.metadata["event_role"] == "snapshot_mutation"
    switch = next(message for message in sender.sent_messages if message.metadata["pad"] == 5)
    assert switch.control == 15
    assert switch.value == 0
    assert switch.metadata["event_role"] == "machine_switch"


def test_snapshot_essence_send_plan_cli_reads_saved_snapshot(tmp_path):
    sysex_path = tmp_path / "essence-send.syx"
    write_send_plan_fixture(sysex_path)

    result = run_cli(
        "snapshot-essence-send-plan-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
        "--style",
        "Birmingham dark techno",
        "--discovery",
        "0.35",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Snapshot Essence Send Plan Report" in result.stdout
    assert "Style prompt: Birmingham dark techno" in result.stdout
    assert "Kit: ESS SEND" in result.stdout
    assert "Send plan ready: True" in result.stdout
    assert "Pad counts: same-engine 2 / engine-switch 10 / blocked 0" in result.stdout
    assert "Machine switch events: 10" in result.stdout
    assert "Snapshot mutation events: 11" in result.stdout
    assert "Mock sender captured:" in result.stdout
    assert "- Pad 5 ch 5 wire 4 machine_switch: CC15 -> 0" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no hardware mutation" in result.stdout
    assert result.stderr == ""
