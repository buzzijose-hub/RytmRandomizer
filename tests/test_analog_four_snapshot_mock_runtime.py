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


def make_a4_kit_record(slot_index=0, kit_name="A4 MOCK", track_values=None):
    track_values = track_values or {}
    decoded = bytearray(2414)
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    for track, offset, name in (
        (1, 44, "BASS LOW"),
        (2, 394, "STAB HIT"),
        (3, 744, "DRONE PAD"),
        (4, 1094, "NOISE FX"),
    ):
        decoded[offset : offset + len(name)] = name.encode("ascii")
        for relative_offset, value in track_values.get(track, {}).items():
            decoded[offset + relative_offset] = (value >> 8) & 0xFF
            decoded[offset + relative_offset + 1] = value & 0xFF
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, 0x06, 0x00, 0x52, 0x01, 0x01, slot_index])
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


def test_importing_analog_four_snapshot_mock_runtime_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four_snapshot_mock_runtime; "
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


def test_analog_four_snapshot_mock_runtime_captures_saved_offset_candidates():
    from rytm_randomizer.analog_four_snapshot_mock_runtime import (
        capture_analog_four_snapshot_mock_messages,
    )
    from rytm_randomizer.analog_four_snapshot_mutation_planner import (
        build_analog_four_snapshot_mutation_plan_from_bytes,
    )

    plan = build_analog_four_snapshot_mutation_plan_from_bytes(
        make_a4_kit_record(
            kit_name="MOCK A4",
            track_values={
                1: {20: 64, 22: 80, 24: 96},
                2: {20: 32, 22: 48},
                3: {20: 100, 22: 111},
                4: {20: 12, 22: 24},
            },
        ),
        slot=1,
        depth="micro",
    )

    sender = capture_analog_four_snapshot_mock_messages(plan)

    assert len(sender.sent_messages) == plan.planned_change_count == 9
    first = sender.sent_messages[0]
    assert first.type == "saved_offset_candidate"
    assert first.channel == 0
    assert first.control == 20
    assert first.value == 67
    assert first.metadata["source_kind"] == "analog_four_snapshot_mutation_plan"
    assert first.metadata["device"] == "Analog Four MKII"
    assert first.metadata["track"] == 1
    assert first.metadata["midi_channel"] == 1
    assert first.metadata["saved_offset"] == 20
    assert first.metadata["word_index"] == 10
    assert first.metadata["baseline_value"] == 64
    assert first.metadata["planned_value"] == 67
    assert first.metadata["delta"] == 3
    assert first.metadata["mapping_status"] == "candidate_unverified"
    assert first.metadata["cc_mapping_claimed"] is False
    assert first.metadata["sends_real_midi"] is False


def test_analog_four_snapshot_mock_runtime_cli_reads_saved_kit_without_hardware(tmp_path):
    sysex_path = tmp_path / "a4-kits.syx"
    sysex_path.write_bytes(
        make_a4_kit_record(
            kit_name="CLI A4 MOCK",
            track_values={
                1: {20: 64, 22: 80, 24: 96},
                2: {20: 32, 22: 48},
            },
        )
    )

    result = run_cli(
        "analog-four-snapshot-mock-runtime-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four Snapshot Mock Runtime Report" in result.stdout
    assert "Kit: CLI A4 MOCK" in result.stdout
    assert "Depth: micro" in result.stdout
    assert "Planned tracks: 2 / 4" in result.stdout
    assert "Mock sender captured: 5 message(s)" in result.stdout
    assert "- Track 1 ch 1 wire 0 BASS LOW / Offset +20: 64 -> 67" in result.stdout
    assert "candidate_unverified" in result.stdout
    assert "- saved-offset candidate events only" in result.stdout
    assert "- no CC mapping claimed" in result.stdout
    assert "- mock sender only" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
