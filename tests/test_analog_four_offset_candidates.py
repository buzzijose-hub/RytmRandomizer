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


def test_importing_analog_four_offset_candidates_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four_offset_candidates; "
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


def test_build_offset_candidate_report_finds_varying_track_words():
    from rytm_randomizer.analog_four_offset_candidates import (
        build_analog_four_offset_candidate_report_from_bytes,
    )

    data = b"".join(
        (
            make_a4_kit_record(0, "KIT 1", {1: {20: 10, 22: 30}}),
            make_a4_kit_record(1, "KIT 2", {1: {20: 40, 22: 30}}),
            make_a4_kit_record(2, "KIT 3", {1: {20: 70, 22: 30}}),
        )
    )

    report = build_analog_four_offset_candidate_report_from_bytes(
        data,
        track=1,
        limit=8,
    )

    assert report.track == 1
    assert report.kit_count == 3
    assert report.candidate_count == 1
    candidate = report.candidates[0]
    assert candidate.relative_offset == 20
    assert candidate.word_index == 10
    assert candidate.sample_count == 3
    assert candidate.unique_value_count == 3
    assert candidate.min_value == 10
    assert candidate.max_value == 70
    assert candidate.values_preview == (10, 40, 70)
    assert candidate.mapping_status == "candidate_unverified"


def test_build_offset_candidate_report_rejects_invalid_track():
    from rytm_randomizer.analog_four_offset_candidates import (
        AnalogFourOffsetCandidateError,
        build_analog_four_offset_candidate_report_from_bytes,
    )

    with pytest.raises(AnalogFourOffsetCandidateError, match="track must be 1-4"):
        build_analog_four_offset_candidate_report_from_bytes(make_a4_kit_record(), track=0)


def test_format_offset_candidate_report_marks_candidates_unverified():
    from rytm_randomizer.analog_four_offset_candidates import (
        build_analog_four_offset_candidate_report_from_bytes,
        format_analog_four_offset_candidate_report,
    )

    data = b"".join(
        (
            make_a4_kit_record(0, "KIT 1", {2: {28: 12}}),
            make_a4_kit_record(1, "KIT 2", {2: {28: 96}}),
        )
    )
    report = build_analog_four_offset_candidate_report_from_bytes(data, track=2, limit=4)
    output = "\n".join(format_analog_four_offset_candidate_report(report))

    assert "RytmRandomizer passive Analog Four offset candidate report" in output
    assert "Track: 2" in output
    assert "Kit records scanned: 2" in output
    assert "- Offset +28 / word 14: samples 2, unique 2, range 12-96" in output
    assert "candidate_unverified" in output
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


def test_analog_four_offset_candidate_cli_reads_saved_kits_without_hardware(tmp_path):
    sysex_path = tmp_path / "a4-kits.syx"
    sysex_path.write_bytes(
        b"".join(
            (
                make_a4_kit_record(0, "KIT 1", {1: {20: 10}}),
                make_a4_kit_record(1, "KIT 2", {1: {20: 40}}),
            )
        )
    )

    result = run_cli(
        "analog-four-offset-candidate-report",
        str(sysex_path),
        "--track",
        "1",
        "--limit",
        "4",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four offset candidate report" in result.stdout
    assert "Track: 1" in result.stdout
    assert "Kit records scanned: 2" in result.stdout
    assert "candidate_unverified" in result.stdout
    assert "- no parameter names claimed" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
