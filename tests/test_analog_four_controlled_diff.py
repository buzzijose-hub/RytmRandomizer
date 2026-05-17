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


def make_a4_kit_record(slot_index=0, kit_name="A4 KIT", track_values=None):
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


def test_importing_analog_four_controlled_diff_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four_controlled_diff; "
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


def test_build_controlled_diff_report_finds_changed_track_words_only():
    from rytm_randomizer.analog_four_controlled_diff import (
        build_analog_four_controlled_diff_report_from_bytes,
    )

    before = make_a4_kit_record(
        slot_index=0,
        kit_name="BASE",
        track_values={1: {20: 10, 22: 30, 24: 900}},
    )
    after = make_a4_kit_record(
        slot_index=0,
        kit_name="BASE",
        track_values={1: {20: 40, 22: 30, 24: 901}},
    )

    report = build_analog_four_controlled_diff_report_from_bytes(
        before,
        after,
        slot=1,
        track=1,
        limit=8,
    )

    assert report.slot == 1
    assert report.track == 1
    assert report.before_kit_name == "BASE"
    assert report.after_kit_name == "BASE"
    assert report.changed_candidate_count == 1
    change = report.changes[0]
    assert change.relative_offset == 20
    assert change.word_index == 10
    assert change.before_value == 10
    assert change.after_value == 40
    assert change.delta == 30
    assert change.mapping_status == "candidate_unverified"


def test_build_controlled_diff_report_rejects_invalid_slot():
    from rytm_randomizer.analog_four_controlled_diff import (
        AnalogFourControlledDiffError,
        build_analog_four_controlled_diff_report_from_bytes,
    )

    with pytest.raises(AnalogFourControlledDiffError, match="slot must be 1-128"):
        build_analog_four_controlled_diff_report_from_bytes(
            make_a4_kit_record(),
            make_a4_kit_record(),
            slot=0,
            track=1,
        )


def test_format_controlled_diff_report_marks_offsets_unverified():
    from rytm_randomizer.analog_four_controlled_diff import (
        build_analog_four_controlled_diff_report_from_bytes,
        format_analog_four_controlled_diff_report,
    )

    before = make_a4_kit_record(slot_index=0, track_values={2: {28: 12}})
    after = make_a4_kit_record(slot_index=0, track_values={2: {28: 96}})
    report = build_analog_four_controlled_diff_report_from_bytes(
        before,
        after,
        slot=1,
        track=2,
    )
    output = "\n".join(format_analog_four_controlled_diff_report(report))

    assert "RytmRandomizer passive Analog Four controlled diff report" in output
    assert "Slot: 1" in output
    assert "Track: 2" in output
    assert "- Offset +28 / word 14: 12 -> 96 (delta +84), candidate_unverified" in output
    assert "- controlled comparison only" in output
    assert "- no parameter names claimed" in output
    assert "- no MIDI sending" in output
    assert "- no SysEx writes" in output


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_analog_four_controlled_diff_cli_reads_two_saved_files_without_hardware(tmp_path):
    before_path = tmp_path / "a4-before.syx"
    after_path = tmp_path / "a4-after.syx"
    before_path.write_bytes(make_a4_kit_record(slot_index=0, track_values={1: {20: 10}}))
    after_path.write_bytes(make_a4_kit_record(slot_index=0, track_values={1: {20: 40}}))

    result = run_cli(
        "analog-four-controlled-diff-report",
        str(before_path),
        str(after_path),
        "--slot",
        "1",
        "--track",
        "1",
        "--limit",
        "4",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four controlled diff report" in result.stdout
    assert "Before path:" in result.stdout
    assert "After path:" in result.stdout
    assert "Slot: 1" in result.stdout
    assert "Track: 1" in result.stdout
    assert "candidate_unverified" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
