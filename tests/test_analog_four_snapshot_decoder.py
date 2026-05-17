import subprocess
import sys
from pathlib import Path

import pytest

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


def make_a4_kit_record(slot_index=0, kit_name="A4 KIT", track_names=None, device_family=0x06):
    track_names = track_names or ("BASS LOW", "STAB HIT", "DRONE PAD", "NOISE FX")
    decoded = bytearray(2414)
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    for offset, name in zip((44, 394, 744, 1094), track_names):
        decoded[offset : offset + len(name)] = name.encode("ascii")
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, device_family, 0x00, 0x52, 0x01, 0x01, slot_index])
        + pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


def test_importing_analog_four_snapshot_decoder_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four_snapshot_decoder; "
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


def test_decode_analog_four_kit_snapshot_reads_kit_and_four_track_blocks():
    from rytm_randomizer.analog_four_snapshot_decoder import (
        decode_analog_four_kit_snapshot_bytes,
    )

    snapshot = decode_analog_four_kit_snapshot_bytes(
        make_a4_kit_record(kit_name="WAREHOUSE A4"),
        slot=1,
    )

    assert snapshot.slot_number == 1
    assert snapshot.kit_name == "WAREHOUSE A4"
    assert snapshot.record_length > 0
    assert snapshot.decoded_payload_length == 2414
    assert snapshot.manufacturer_id == "00 20 3C"
    assert snapshot.device_family_byte == 0x06
    assert snapshot.object_type == 0x52
    assert len(snapshot.tracks) == 4
    assert [track.name for track in snapshot.tracks] == [
        "BASS LOW",
        "STAB HIT",
        "DRONE PAD",
        "NOISE FX",
    ]
    assert [track.block_offset for track in snapshot.tracks] == [44, 394, 744, 1094]
    assert {track.mapping_status for track in snapshot.tracks} == {
        "saved_parameter_offsets_unmapped"
    }


def test_decode_analog_four_kit_snapshot_rejects_invalid_slot():
    from rytm_randomizer.analog_four_snapshot_decoder import (
        AnalogFourSnapshotDecodeError,
        decode_analog_four_kit_snapshot_bytes,
    )

    with pytest.raises(AnalogFourSnapshotDecodeError, match="slot must be 1-128"):
        decode_analog_four_kit_snapshot_bytes(make_a4_kit_record(), slot=0)


def test_decode_analog_four_kit_snapshot_rejects_non_a4_kit_record():
    from rytm_randomizer.analog_four_snapshot_decoder import (
        AnalogFourSnapshotDecodeError,
        decode_analog_four_kit_snapshot_bytes,
    )

    with pytest.raises(AnalogFourSnapshotDecodeError, match="not an Analog Four kit record"):
        decode_analog_four_kit_snapshot_bytes(make_a4_kit_record(device_family=0x07), slot=1)


def test_format_analog_four_kit_snapshot_report_states_unmapped_offsets():
    from rytm_randomizer.analog_four_snapshot_decoder import (
        decode_analog_four_kit_snapshot_bytes,
        format_analog_four_kit_snapshot_report,
    )

    snapshot = decode_analog_four_kit_snapshot_bytes(make_a4_kit_record(), slot=1)
    report = "\n".join(format_analog_four_kit_snapshot_report(snapshot))

    assert "RytmRandomizer passive Analog Four kit snapshot report" in report
    assert "Kit: A4 KIT" in report
    assert "Track snapshots:" in report
    assert "- Track 4 / MIDI channel 4 / wire channel 3 / offset 1094" in report
    assert "saved_parameter_offsets_unmapped" in report
    assert "- no MIDI sending" in report
    assert "- no SysEx writes" in report


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_analog_four_kit_snapshot_cli_reads_saved_kit_without_hardware(tmp_path):
    sysex_path = tmp_path / "a4-kits.syx"
    sysex_path.write_bytes(make_a4_kit_record(kit_name="CLI A4"))

    result = run_cli(
        "analog-four-kit-snapshot-report",
        str(sysex_path),
        "--slot",
        "1",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four kit snapshot report" in result.stdout
    assert "Kit: CLI A4" in result.stdout
    assert "Track snapshots:" in result.stdout
    assert "saved_parameter_offsets_unmapped" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no SysEx writes" in result.stdout
    assert result.stderr == ""
