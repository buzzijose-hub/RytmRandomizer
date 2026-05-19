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


def normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def test_importing_sysex_bank_analyzer_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.sysex.bank_analyzer; "
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
    from rytm_randomizer.sysex.bank_analyzer import analyze_sysex_kit_bank_bytes

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


def test_analyzer_adds_snapshot_readiness_for_decodable_rytm_kit_records():
    from rytm_randomizer.sysex.bank_analyzer import analyze_sysex_kit_bank_bytes

    first_machines = [27 for _ in range(12)]
    first_machines[0] = 0
    first_machines[9] = 10
    second_machines = [27 for _ in range(12)]
    second_machines[9] = 8  # Pad 10 is OH/open hihat, not an XT tom lane.
    bank = b"".join(
        [
            make_rytm_kit_record(
                slot_index=0,
                kit_name="READY KIT",
                machine_values=tuple(first_machines),
                pad_parameter_values={
                    1: {0x1E: 59, 0x20: 68, 0x44: 25, 0x50: 121},
                    10: {0x1E: 63, 0x20: 70, 0x44: 96, 0x50: 88},
                },
            ),
            make_rytm_kit_record(
                slot_index=1,
                kit_name="BAD KIT",
                machine_values=tuple(second_machines),
                pad_parameter_values={10: {0x1E: 63, 0x20: 70, 0x44: 96, 0x50: 88}},
            ),
        ]
    )

    analysis = analyze_sysex_kit_bank_bytes(bank)

    assert analysis.snapshot_decoded_slot_count == 2
    assert analysis.snapshot_machine_compatibility_totals == {
        "allowed_on_pad": 2,
        "machine_disabled": 21,
        "unknown_machine": 0,
        "incompatible_with_pad": 1,
    }
    assert analysis.snapshot_readiness_totals == {
        "ready": 2,
        "machine_disabled": 21,
        "unknown_machine": 0,
        "incompatible_with_pad": 1,
        "no_mutable_legal_pads": 0,
    }
    usage_by_pad = {
        usage.pad: dict(usage.machine_counts) for usage in analysis.snapshot_machine_usage_by_pad
    }
    assert usage_by_pad[1] == {"BD Hard": 1, "Disabled": 1}
    assert usage_by_pad[10] == {"OH Classic": 1, "XT Classic": 1}


def test_analyzer_rejects_bytes_without_complete_sysex_messages():
    from rytm_randomizer.sysex.bank_analyzer import (
        SysexBankAnalysisError,
        analyze_sysex_kit_bank_bytes,
    )

    with pytest.raises(SysexBankAnalysisError, match="no complete SysEx messages"):
        analyze_sysex_kit_bank_bytes(b"not a sysex bank")


def test_report_formatter_keeps_live_snapshot_boundaries_explicit():
    from rytm_randomizer.sysex.bank_analyzer import (
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


def test_report_formatter_includes_snapshot_readiness_when_records_decode():
    from rytm_randomizer.sysex.bank_analyzer import (
        analyze_sysex_kit_bank_bytes,
        format_sysex_kit_bank_report,
    )

    machines = [27 for _ in range(12)]
    machines[0] = 0
    machines[9] = 10
    report = format_sysex_kit_bank_report(
        analyze_sysex_kit_bank_bytes(
            make_rytm_kit_record(
                slot_index=0,
                kit_name="READY KIT",
                machine_values=tuple(machines),
                pad_parameter_values={
                    1: {0x1E: 59, 0x20: 68, 0x44: 25, 0x50: 121},
                    10: {0x1E: 63, 0x20: 70, 0x44: 96, 0x50: 88},
                },
            )
        )
    )

    assert "Snapshot decoded slots: 1 / 1" in report
    assert (
        "Snapshot machine compatibility: allowed 2 / disabled 10 / unknown 0 / incompatible 0"
        in report
    )
    assert (
        "Snapshot readiness: ready 2 / disabled 10 / unknown 0 / "
        "incompatible 0 / no mutable legal pads 0" in report
    )
    assert "- Pad 1: BD Hard 1" in report
    assert "- Pad 10: OH Classic 1" in report


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


def test_sysex_kit_bank_report_cli_prints_snapshot_readiness_for_full_kits(tmp_path):
    bank_path = tmp_path / "full-kits.syx"
    machines = [27 for _ in range(12)]
    machines[0] = 0
    machines[9] = 10
    bank_path.write_bytes(
        make_rytm_kit_record(
            slot_index=0,
            kit_name="CLI FULL",
            machine_values=tuple(machines),
            pad_parameter_values={
                1: {0x1E: 59, 0x20: 68, 0x44: 25, 0x50: 121},
                10: {0x1E: 63, 0x20: 70, 0x44: 96, 0x50: 88},
            },
        )
    )

    result = run_cli("sysex-kit-bank-report", str(bank_path))

    assert result.returncode == 0
    assert "RytmRandomizer passive SysEx kit bank report" in result.stdout
    assert "Snapshot decoded slots: 1 / 1" in result.stdout
    assert "Snapshot readiness: ready 2 / disabled 10" in result.stdout
    assert "- Pad 10: OH Classic 1" in result.stdout
    assert "- no MIDI sending" in result.stdout
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
