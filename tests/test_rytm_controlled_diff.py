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


def make_rytm_kit_record(
    slot_index=0,
    kit_name="KIT A",
    sound_names=None,
    machine_values=None,
    pad_parameter_values=None,
):
    sound_names = sound_names or tuple(f"SOUND {pad}" for pad in range(1, 13))
    machine_values = machine_values or tuple(27 for _ in range(12))
    pad_parameter_values = pad_parameter_values or {}
    decoded = bytearray(58 + (12 * 162) + 8)
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    for pad, sound_name in enumerate(sound_names, start=1):
        sound_offset = 58 + ((pad - 1) * 162)
        track_offset = 46 + ((pad - 1) * 162)
        decoded[sound_offset : sound_offset + len(sound_name)] = sound_name.encode("ascii")
        decoded[track_offset + 0x0C : track_offset + 0x0C + len(sound_name)] = sound_name.encode(
            "ascii"
        )
        decoded[track_offset + 0x7C] = machine_values[pad - 1]
        for parameter_offset, value in pad_parameter_values.get(pad, {}).items():
            decoded[track_offset + parameter_offset] = value
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, slot_index])
        + pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


def test_importing_rytm_controlled_diff_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.rytm_controlled_diff; "
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


def test_build_rytm_controlled_diff_report_finds_changed_mapped_parameters_only():
    from rytm_randomizer.rytm_controlled_diff import (
        build_rytm_controlled_diff_report_from_bytes,
    )

    before = make_rytm_kit_record(
        slot_index=0,
        kit_name="BASE",
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={1: {0x44: 27, 0x50: 86}},
    )
    after = make_rytm_kit_record(
        slot_index=0,
        kit_name="BASE",
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={1: {0x44: 96, 0x50: 86}},
    )

    report = build_rytm_controlled_diff_report_from_bytes(
        before,
        after,
        slot=1,
        pad=1,
        limit=8,
    )

    assert report.slot == 1
    assert report.pad == 1
    assert report.before_kit_name == "BASE"
    assert report.after_kit_name == "BASE"
    assert report.before_machine_label == "BD Hard"
    assert report.after_machine_label == "BD Hard"
    assert report.changed_parameter_count == 1
    change = report.changes[0]
    assert change.name == "FLT Frequency"
    assert change.cc == 74
    assert change.block_offset == 0x44
    assert change.before_value == 27
    assert change.after_value == 96
    assert change.delta == 69
    assert change.mapping_status == "bd_hard_parameters"


def test_build_rytm_controlled_diff_report_rejects_invalid_pad():
    from rytm_randomizer.rytm_controlled_diff import (
        RytmControlledDiffError,
        build_rytm_controlled_diff_report_from_bytes,
    )

    with pytest.raises(RytmControlledDiffError, match="pad must be 1-12"):
        build_rytm_controlled_diff_report_from_bytes(
            make_rytm_kit_record(),
            make_rytm_kit_record(),
            slot=1,
            pad=13,
        )


def test_format_rytm_controlled_diff_report_marks_safety_boundary():
    from rytm_randomizer.rytm_controlled_diff import (
        build_rytm_controlled_diff_report_from_bytes,
        format_rytm_controlled_diff_report,
    )

    before = make_rytm_kit_record(
        slot_index=0,
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={1: {0x1E: 61}},
    )
    after = make_rytm_kit_record(
        slot_index=0,
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={1: {0x1E: 66}},
    )
    report = build_rytm_controlled_diff_report_from_bytes(before, after, slot=1, pad=1)
    output = "\n".join(format_rytm_controlled_diff_report(report))

    assert "RytmRandomizer passive Rytm controlled diff report" in output
    assert "Slot: 1" in output
    assert "Pad: 1" in output
    assert "- SRC Tune / CC17 @0x001E: 61 -> 66 (delta +5), bd_hard_parameters" in output
    assert "- mapped saved parameters only" in output
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


def test_rytm_controlled_diff_cli_reads_two_saved_files_without_hardware(tmp_path):
    before_path = tmp_path / "rytm-before.syx"
    after_path = tmp_path / "rytm-after.syx"
    before_path.write_bytes(
        make_rytm_kit_record(
            slot_index=0,
            machine_values=(0,) + tuple(27 for _ in range(11)),
            pad_parameter_values={1: {0x44: 27}},
        )
    )
    after_path.write_bytes(
        make_rytm_kit_record(
            slot_index=0,
            machine_values=(0,) + tuple(27 for _ in range(11)),
            pad_parameter_values={1: {0x44: 96}},
        )
    )

    result = run_cli(
        "rytm-controlled-diff-report",
        str(before_path),
        str(after_path),
        "--slot",
        "1",
        "--pad",
        "1",
        "--limit",
        "4",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm controlled diff report" in result.stdout
    assert "Before path:" in result.stdout
    assert "After path:" in result.stdout
    assert "Slot: 1" in result.stdout
    assert "Pad: 1" in result.stdout
    assert "FLT Frequency" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
