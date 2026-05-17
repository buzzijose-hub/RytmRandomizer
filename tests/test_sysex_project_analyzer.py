import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def make_project_record(device_family, object_type, slot_index, record_length):
    record = bytearray(record_length)
    record[0:10] = bytes(
        [
            0xF0,
            0x00,
            0x20,
            0x3C,
            device_family,
            0x00,
            object_type,
            0x01,
            0x01,
            slot_index,
        ]
    )
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


def test_importing_sysex_project_analyzer_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.sysex_project_analyzer; "
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


def test_analyzer_groups_whole_project_records_by_device_type_length_and_slots():
    from rytm_randomizer.sysex_project_analyzer import analyze_sysex_project_bytes

    project = b"".join(
        [
            make_project_record(0x07, 0x52, 0, 64),
            make_project_record(0x07, 0x52, 1, 64),
            make_project_record(0x07, 0x53, 0, 48),
            make_project_record(0x07, 0x54, 0, 72),
            make_project_record(0x07, 0x54, 1, 72),
            make_project_record(0x07, 0x57, 0, 40),
        ]
    )

    analysis = analyze_sysex_project_bytes(project)

    assert analysis.record_count == 6
    assert analysis.valid_sysex_boundaries is True
    assert analysis.complete_stream is True
    assert analysis.leading_bytes == 0
    assert analysis.trailing_bytes == 0
    assert analysis.manufacturer_id == "00 20 3C"
    assert analysis.device_family_byte == 0x07
    assert analysis.device_label == "Analog Rytm MKII"
    assert [(group.label, group.count, group.record_length, group.slot_numbers) for group in analysis.record_groups] == [
        ("kits", 2, 64, (1, 2)),
        ("sounds", 1, 48, (1,)),
        ("patterns", 2, 72, (1, 2)),
        ("global_slots", 1, 40, (1,)),
    ]


def test_analyzer_rejects_bytes_without_complete_sysex_messages():
    from rytm_randomizer.sysex_project_analyzer import SysexProjectAnalysisError
    from rytm_randomizer.sysex_project_analyzer import analyze_sysex_project_bytes

    with pytest.raises(SysexProjectAnalysisError, match="no complete SysEx messages"):
        analyze_sysex_project_bytes(b"not a project dump")


def test_report_formatter_keeps_snapshot_relevance_and_safety_explicit():
    from rytm_randomizer.sysex_project_analyzer import (
        analyze_sysex_project_bytes,
        format_sysex_project_report,
    )

    project = b"".join(
        [
            make_project_record(0x06, 0x52, 0, 64),
            make_project_record(0x06, 0x83, 0, 48),
            make_project_record(0x06, 0x54, 0, 72),
            make_project_record(0x06, 0x56, 0, 40),
        ]
    )

    report = format_sysex_project_report(analyze_sysex_project_bytes(project))

    assert report == [
        "RytmRandomizer passive SysEx project report",
        "Device: Analog Four MKII",
        "Device family byte: 06",
        "Manufacturer ID: 00 20 3C",
        "Complete SysEx records: 4",
        "Complete stream: True",
        "Valid SysEx boundaries: True",
        "Leading bytes before first SysEx: 0",
        "Trailing bytes after last SysEx: 0",
        "Record groups:",
        "- kits: 1 record(s), 64 bytes each, slots 1",
        "- unknown_0x83: 1 record(s), 48 bytes each, slots 1",
        "- patterns: 1 record(s), 72 bytes each, slots 1",
        "- project_settings: 1 record(s), 40 bytes each, slots 1",
        "Live Snapshot relevance:",
        "- contains kit records",
        "- contains pattern records",
        "- contains project/global records",
        "- suitable raw source for future Live Snapshot decode",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


def test_sysex_project_report_cli_reads_file_without_hardware(tmp_path):
    project_path = tmp_path / "project.syx"
    project_path.write_bytes(
        b"".join(
            [
                make_project_record(0x07, 0x52, 0, 64),
                make_project_record(0x07, 0x54, 0, 72),
                make_project_record(0x07, 0x57, 0, 40),
            ]
        )
    )

    result = run_cli("sysex-project-report", str(project_path))

    assert result.returncode == 0
    assert "RytmRandomizer passive SysEx project report" in result.stdout
    assert "Device: Analog Rytm MKII" in result.stdout
    assert "- kits: 1 record(s), 64 bytes each, slots 1" in result.stdout
    assert "- patterns: 1 record(s), 72 bytes each, slots 1" in result.stdout
    assert "- global_slots: 1 record(s), 40 bytes each, slots 1" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no SysEx writes" in result.stdout
    assert result.stderr == ""


def test_sysex_project_report_cli_missing_file_fails_safely(tmp_path):
    missing_path = tmp_path / "missing-project.syx"

    result = run_cli("sysex-project-report", str(missing_path))

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == "\n".join(
        [
            "RytmRandomizer passive SysEx project report",
            f"Path: {missing_path}",
            "Found: False",
            "Message: File not found. No MIDI was sent. No command executed.",
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )


def test_sysex_project_report_cli_imports_no_real_midi_libraries(tmp_path):
    project_path = tmp_path / "project.syx"
    project_path.write_bytes(make_project_record(0x07, 0x52, 0, 64))
    script = "\n".join(
        [
            "import runpy",
            "import sys",
            f"sys.argv = ['rytm_randomizer.cli', 'sysex-project-report', {str(project_path)!r}]",
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
    assert "RytmRandomizer passive SysEx project report" in result.stdout
    assert result.stderr == ""
