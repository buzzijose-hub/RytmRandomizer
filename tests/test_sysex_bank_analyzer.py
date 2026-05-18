import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def make_kit_record(slot_index, name="", record_length=64, payload_seed=0):
    record = bytearray(record_length)
    record[0:10] = bytes([0xF0, 0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, slot_index])
    record[14] = 0x06
    for offset, byte in enumerate(name.encode("ascii")):
        record[15 + offset] = byte
    record[40] = payload_seed
    record[-1] = 0xF7
    return bytes(record)


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


def test_importing_sysex_bank_analyzer_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.sysex_bank_analyzer; "
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


def test_analyzer_splits_fixed_length_bank_and_extracts_slot_metadata():
    from rytm_randomizer.sysex_bank_analyzer import analyze_sysex_kit_bank_bytes

    bank = b"".join(
        [
            make_kit_record(0, "KIT 1", payload_seed=11),
            make_kit_record(1, "KIT 2", payload_seed=22),
            make_kit_record(2),
            make_kit_record(3),
        ]
    )

    analysis = analyze_sysex_kit_bank_bytes(bank)

    assert analysis.record_count == 4
    assert analysis.record_length == 64
    assert analysis.fixed_length_records is True
    assert analysis.valid_sysex_boundaries is True
    assert analysis.manufacturer_id == "00 20 3C"
    assert analysis.nonblank_slots == (1, 2)
    assert analysis.blank_candidate_slots == (3, 4)
    assert analysis.largest_duplicate_group_slots == (3, 4)

    first, second, third = analysis.records[:3]
    assert first.slot_number == 1
    assert first.header_slot_index == 0
    assert first.name == "KIT 1"
    assert first.offset == 0
    assert first.ends_with_f7 is True

    assert second.slot_number == 2
    assert second.header_slot_index == 1
    assert second.name == "KIT 2"

    assert third.slot_number == 3
    assert third.header_slot_index == 2
    assert third.name == ""


def test_analyzer_rejects_bytes_without_complete_sysex_messages():
    from rytm_randomizer.sysex_bank_analyzer import (
        SysexBankAnalysisError,
        analyze_sysex_kit_bank_bytes,
    )

    with pytest.raises(SysexBankAnalysisError, match="no complete SysEx messages"):
        analyze_sysex_kit_bank_bytes(b"not a sysex bank")


def test_report_formatter_keeps_live_snapshot_boundaries_explicit():
    from rytm_randomizer.sysex_bank_analyzer import (
        analyze_sysex_kit_bank_bytes,
        format_sysex_kit_bank_report,
    )

    bank = b"".join(
        [
            make_kit_record(0, "KIT 1", payload_seed=11),
            make_kit_record(1, "KIT 2", payload_seed=22),
            make_kit_record(2),
            make_kit_record(3),
        ]
    )

    report = format_sysex_kit_bank_report(analyze_sysex_kit_bank_bytes(bank))

    assert report == [
        "RytmRandomizer passive SysEx kit bank report",
        "Record count: 4",
        "Record length: 64",
        "Fixed-length records: True",
        "Valid SysEx boundaries: True",
        "Manufacturer ID: 00 20 3C",
        "Nonblank kit slots: 1-2",
        "Blank/default candidate slots: 3-4",
        "Largest duplicate normalized group: 3-4",
        "Kit records:",
        "- Slot 1: KIT 1 / header index 0 / offset 0 / bytes 64",
        "- Slot 2: KIT 2 / header index 1 / offset 64 / bytes 64",
        "- Slot 3: <blank> / header index 2 / offset 128 / bytes 64",
        "- Slot 4: <blank> / header index 3 / offset 192 / bytes 64",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no SysEx writes",
        "- no hardware required",
    ]


def test_sysex_kit_bank_report_cli_reads_file_without_hardware(tmp_path):
    bank_path = tmp_path / "demo.syx"
    bank_path.write_bytes(
        b"".join(
            [
                make_kit_record(0, "KIT 1", payload_seed=11),
                make_kit_record(1, "KIT 2", payload_seed=22),
                make_kit_record(2),
                make_kit_record(3),
            ]
        )
    )

    result = run_cli("sysex-kit-bank-report", str(bank_path))

    assert result.returncode == 0
    assert "RytmRandomizer passive SysEx kit bank report" in result.stdout
    assert "Record count: 4" in result.stdout
    assert "Nonblank kit slots: 1-2" in result.stdout
    assert "Blank/default candidate slots: 3-4" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no SysEx writes" in result.stdout
    assert result.stderr == ""


def test_sysex_kit_bank_report_cli_missing_file_fails_safely(tmp_path):
    missing_path = tmp_path / "missing.syx"

    result = run_cli("sysex-kit-bank-report", str(missing_path))

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == "\n".join(
        [
            "RytmRandomizer passive SysEx kit bank report",
            f"Path: {missing_path}",
            "Found: False",
            "Message: File not found. No MIDI was sent. No command executed.",
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )


def test_sysex_kit_bank_report_cli_imports_no_real_midi_libraries(tmp_path):
    bank_path = tmp_path / "demo.syx"
    bank_path.write_bytes(make_kit_record(0, "KIT 1", payload_seed=11))
    script = "\n".join(
        [
            "import runpy",
            "import sys",
            f"sys.argv = ['rytm_randomizer.cli', 'sysex-kit-bank-report', {str(bank_path)!r}]",
            "runpy.run_module('rytm_randomizer.cli', run_name='__main__')",
            "assert 'mido' not in sys.modules",
            "assert 'rtmidi' not in sys.modules",
        ]
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive SysEx kit bank report" in result.stdout
    assert result.stderr == ""
