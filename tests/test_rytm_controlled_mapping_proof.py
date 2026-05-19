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


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_rytm_controlled_mapping_proof_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.rytm.controlled_mapping_proof; "
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


def test_rytm_controlled_mapping_proof_accepts_single_matching_parameter():
    from rytm_randomizer.rytm.controlled_mapping_proof import (
        build_rytm_controlled_mapping_proof_from_bytes,
    )

    before = make_rytm_kit_record(
        slot_index=0,
        kit_name="BASE",
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={1: {0x44: 27}},
    )
    after = make_rytm_kit_record(
        slot_index=0,
        kit_name="BASE",
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={1: {0x44: 96}},
    )

    proof = build_rytm_controlled_mapping_proof_from_bytes(
        before,
        after,
        slot=1,
        pad=1,
        parameter="flt-frequency",
        limit=8,
    )

    assert proof.ready is True
    assert proof.reason == "single_changed_parameter_ready_for_review"
    assert proof.pad == 1
    assert proof.parameter_key == "fltfrequency"
    assert proof.entry is not None
    assert proof.entry.machine_label == "BD Hard"
    assert proof.entry.parameter_name == "FLT Frequency"
    assert proof.entry.cc == 74
    assert proof.entry.block_offset == 0x44


def test_rytm_controlled_mapping_proof_blocks_multiple_changed_parameters():
    from rytm_randomizer.rytm.controlled_mapping_proof import (
        build_rytm_controlled_mapping_proof_from_bytes,
    )

    before = make_rytm_kit_record(
        slot_index=0,
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={1: {0x44: 27, 0x50: 86}},
    )
    after = make_rytm_kit_record(
        slot_index=0,
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={1: {0x44: 96, 0x50: 100}},
    )

    proof = build_rytm_controlled_mapping_proof_from_bytes(
        before,
        after,
        slot=1,
        pad=1,
        parameter="flt-frequency",
        limit=8,
    )

    assert proof.ready is False
    assert proof.reason == "blocked_multiple_changed_parameters"
    assert proof.entry is None


def test_rytm_controlled_mapping_proof_blocks_parameter_mismatch():
    from rytm_randomizer.rytm.controlled_mapping_proof import (
        build_rytm_controlled_mapping_proof_from_bytes,
    )

    before = make_rytm_kit_record(
        slot_index=0,
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={1: {0x50: 86}},
    )
    after = make_rytm_kit_record(
        slot_index=0,
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={1: {0x50: 100}},
    )

    proof = build_rytm_controlled_mapping_proof_from_bytes(
        before,
        after,
        slot=1,
        pad=1,
        parameter="flt-frequency",
        limit=8,
    )

    assert proof.ready is False
    assert proof.reason == "blocked_parameter_mismatch"
    assert proof.entry is None


def test_format_rytm_controlled_mapping_proof_report_includes_review_entry():
    from rytm_randomizer.rytm.controlled_mapping_proof import (
        build_rytm_controlled_mapping_proof_from_bytes,
        format_rytm_controlled_mapping_proof_report,
    )

    before = make_rytm_kit_record(
        slot_index=0,
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={1: {0x44: 27}},
    )
    after = make_rytm_kit_record(
        slot_index=0,
        machine_values=(0,) + tuple(27 for _ in range(11)),
        pad_parameter_values={1: {0x44: 96}},
    )

    proof = build_rytm_controlled_mapping_proof_from_bytes(
        before,
        after,
        slot=1,
        pad=1,
        parameter="cc74",
        limit=8,
    )
    report = "\n".join(format_rytm_controlled_mapping_proof_report(proof))

    assert "RytmRandomizer passive Rytm Controlled Mapping Proof Report" in report
    assert "Ready: True" in report
    assert "Reason: single_changed_parameter_ready_for_review" in report
    assert "Requested parameter: cc74" in report
    assert "RytmControlledMappingProofEntry(" in report
    assert '    parameter_name="FLT Frequency",' in report
    assert "    cc=74," in report
    assert "    block_offset=0x0044," in report
    assert "- no MIDI sending" in report


def test_rytm_controlled_mapping_proof_cli_reads_saved_files(tmp_path):
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
        "rytm-controlled-mapping-proof-report",
        str(before_path),
        str(after_path),
        "--slot",
        "1",
        "--pad",
        "1",
        "--parameter",
        "flt-frequency",
        "--limit",
        "4",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm Controlled Mapping Proof Report" in result.stdout
    assert "Ready: True" in result.stdout
    assert "FLT Frequency" in result.stdout
    assert "block_offset=0x0044" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
