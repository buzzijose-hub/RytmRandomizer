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


def make_a4_kit_record(
    slot_index=0,
    kit_name="A4 BANK",
    track_names=None,
    track_values=None,
):
    track_names = track_names or ("BASS LOW", "STAB HIT", "DRONE PAD", "NOISE FX")
    track_values = track_values or {}
    decoded = bytearray(2414)
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    for track, offset, name in zip(
        range(1, 5),
        (44, 394, 744, 1094),
        track_names,
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


def normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def test_importing_analog_four_bank_analyzer_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four.bank_analyzer; "
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


def test_analyzer_summarizes_decoded_analog_four_kit_bank():
    from rytm_randomizer.analog_four.bank_analyzer import (
        analyze_analog_four_kit_bank_bytes,
    )

    bank = b"".join(
        [
            make_a4_kit_record(
                slot_index=0,
                kit_name="A4 ONE",
                track_names=("BASS", "STAB", "PAD", "FX"),
                track_values={
                    1: {20: 64, 22: 80},
                    2: {20: 32},
                    3: {20: 96},
                    4: {20: 12},
                },
            ),
            make_a4_kit_record(
                slot_index=1,
                kit_name="A4 TWO",
                track_names=("BASS", "LEAD", "PAD", "FX"),
                track_values={
                    1: {20: 60},
                    2: {20: 70},
                    3: {20: 90},
                    4: {20: 30},
                },
            ),
        ]
    )

    analysis = analyze_analog_four_kit_bank_bytes(bank)

    assert analysis.complete_sysex_message_count == 2
    assert analysis.kit_record_count == 2
    assert analysis.decoded_snapshot_count == 2
    assert analysis.planned_track_count == 8
    assert analysis.blocked_track_count == 0
    assert analysis.planned_candidate_change_count == 9
    usage_by_track = {usage.track: dict(usage.name_counts) for usage in analysis.track_name_usage}
    assert usage_by_track[1] == {"BASS": 2}
    assert usage_by_track[2] == {"STAB": 1, "LEAD": 1}


def test_report_formatter_includes_bank_level_a4_readiness():
    from rytm_randomizer.analog_four.bank_analyzer import (
        analyze_analog_four_kit_bank_bytes,
        format_analog_four_kit_bank_report,
    )

    report = format_analog_four_kit_bank_report(
        analyze_analog_four_kit_bank_bytes(
            make_a4_kit_record(
                slot_index=0,
                kit_name="A4 ONE",
                track_names=("BASS", "STAB", "PAD", "FX"),
                track_values={1: {20: 64}, 2: {20: 32}},
            )
        )
    )

    assert report[:12] == [
        "RytmRandomizer passive Analog Four kit bank report",
        "Complete SysEx messages: 1",
        "Analog Four kit records: 1",
        "Decoded kit snapshots: 1 / 1",
        "Snapshot tracks: planned 2 / blocked 2 / total 4",
        "Planned candidate changes: 2",
        "Candidate status: candidate_unverified",
        "Track name usage:",
        "- Track 1: BASS 1",
        "- Track 2: STAB 1",
        "- Track 3: PAD 1",
        "- Track 4: FX 1",
    ]
    assert "- candidate offsets only" in report
    assert "- no MIDI sending" in report
    assert "- no SysEx writes" in report


def test_report_formatter_limits_long_track_name_usage_lines():
    from rytm_randomizer.analog_four.bank_analyzer import (
        analyze_analog_four_kit_bank_bytes,
        format_analog_four_kit_bank_report,
    )

    bank = b"".join(
        make_a4_kit_record(
            slot_index=slot,
            kit_name=f"KIT {slot + 1}",
            track_names=(f"BASS {slot:02d}", "STAB", "PAD", "FX"),
            track_values={1: {20: 64}, 2: {20: 32}},
        )
        for slot in range(14)
    )

    report = format_analog_four_kit_bank_report(analyze_analog_four_kit_bank_bytes(bank))
    track1_line = next(line for line in report if line.startswith("- Track 1:"))

    assert "BASS 00 1" in track1_line
    assert "BASS 11 1" in track1_line
    assert "BASS 12 1" not in track1_line
    assert "... 2 more" in track1_line


def test_analog_four_kit_bank_report_cli_reads_file_without_hardware(tmp_path):
    sysex_path = tmp_path / "a4-bank.syx"
    sysex_path.write_bytes(
        make_a4_kit_record(
            slot_index=0,
            kit_name="CLI A4 BANK",
            track_names=("BASS", "STAB", "PAD", "FX"),
            track_values={1: {20: 64}, 2: {20: 32}},
        )
    )

    result = run_cli("analog-four-kit-bank-report", str(sysex_path))

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four kit bank report" in result.stdout
    assert "Decoded kit snapshots: 1 / 1" in result.stdout
    assert "Snapshot tracks: planned 2 / blocked 2 / total 4" in result.stdout
    assert "- Track 1: BASS 1" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_analog_four_kit_bank_report_cli_missing_file_fails_safely(tmp_path):
    missing_path = tmp_path / "missing.syx"

    result = run_cli("analog-four-kit-bank-report", str(missing_path))

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == "\n".join(
        [
            "RytmRandomizer passive Analog Four kit bank report",
            f"Path: {missing_path}",
            "Found: False",
            "Message: File not found. No MIDI was sent. No command executed.",
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no MIDI receive",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
