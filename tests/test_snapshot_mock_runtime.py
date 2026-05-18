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
    kit_name="KIT A",
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


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_snapshot_mock_runtime_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.snapshot_mock_runtime; "
                "assert 'mido' not in sys.modules; "
                "assert 'rtmidi' not in sys.modules"
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


def test_snapshot_mock_runtime_captures_planned_changes_as_inert_cc_messages():
    from rytm_randomizer.snapshot_mock_runtime import capture_snapshot_mutation_mock_messages
    from rytm_randomizer.snapshot_mutation_planner import build_snapshot_mutation_plan
    from rytm_randomizer.sysex_snapshot_decoder import decode_rytm_kit_snapshot_record

    snapshot = decode_rytm_kit_snapshot_record(
        make_rytm_kit_record(
            kit_name="MOCK BASE",
            machine_values=(0, 27, 32) + tuple(27 for _ in range(9)),
            pad_parameter_values={
                1: {
                    0x1E: 59,
                    0x20: 68,
                    0x44: 25,
                    0x46: 14,
                    0x50: 121,
                    0x52: 36,
                },
                3: {
                    0x1C: 100,
                    0x1E: 69,
                    0x20: 23,
                    0x44: 98,
                    0x50: 25,
                    0x5E: 96,
                    0x6C: 86,
                },
            },
        )
    )
    plan = build_snapshot_mutation_plan(snapshot, depth="micro")

    sender = capture_snapshot_mutation_mock_messages(plan)

    assert len(sender.sent_messages) == plan.planned_change_count == 12
    first = sender.sent_messages[0]
    assert first.type == "cc"
    assert first.channel == 0
    assert first.control == 17
    assert first.value == 60
    assert first.metadata["source_kind"] == "snapshot_mutation_plan"
    assert first.metadata["pad"] == 1
    assert first.metadata["midi_channel"] == 1
    assert first.metadata["machine_label"] == "BD Hard"
    assert first.metadata["parameter"] == "SRC Tune"
    assert first.metadata["baseline_value"] == 59
    assert first.metadata["planned_value"] == 60
    assert first.metadata["delta"] == 1
    pad3_message = next(
        message
        for message in sender.sent_messages
        if message.metadata["pad"] == 3 and message.control == 74
    )
    assert pad3_message.channel == 2
    assert pad3_message.metadata["machine_label"] == "SY Raw"
    assert pad3_message.metadata["parameter"] == "FLT Frequency"


def test_snapshot_mock_runtime_cli_reads_saved_kit_without_hardware(tmp_path):
    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(
        make_rytm_kit_record(
            kit_name="CLI MOCK",
            machine_values=(0,) + tuple(27 for _ in range(11)),
            pad_parameter_values={
                1: {
                    0x1E: 59,
                    0x20: 68,
                    0x44: 25,
                    0x46: 14,
                    0x50: 121,
                    0x52: 36,
                }
            },
        )
    )

    result = run_cli(
        "sysex-snapshot-mock-runtime-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Snapshot Mock Runtime Report" in result.stdout
    assert "Kit: CLI MOCK" in result.stdout
    assert "Depth: micro" in result.stdout
    assert "Planned pads: 1 / 12" in result.stdout
    assert "Mock sender captured: 6 message(s)" in result.stdout
    assert "- Pad 1 ch 1 wire 0 BD Hard / SRC Tune: CC17 -> 60" in result.stdout
    assert "baseline 59 / delta +1" in result.stdout
    assert "- captured-value relative" in result.stdout
    assert "- mock sender only" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
