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


def test_importing_snapshot_mutation_planner_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.snapshot.rytm_mutation_planner; "
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


def test_snapshot_mutation_plan_uses_captured_values_not_anchors():
    from rytm_randomizer.snapshot.rytm_decoder import decode_rytm_kit_snapshot_record
    from rytm_randomizer.snapshot.rytm_mutation_planner import build_snapshot_mutation_plan

    snapshot = decode_rytm_kit_snapshot_record(
        make_rytm_kit_record(
            kit_name="LIVE BASE",
            machine_values=(0, 23) + tuple(27 for _ in range(10)),
            pad_parameter_values={
                1: {
                    0x1E: 59,
                    0x20: 68,
                    0x44: 25,
                    0x46: 14,
                    0x50: 121,
                    0x52: 36,
                },
                2: {
                    0x1E: 63,
                    0x20: 70,
                    0x44: 96,
                    0x46: 18,
                    0x4A: 62,
                    0x50: 88,
                },
            },
        )
    )

    plan = build_snapshot_mutation_plan(snapshot, depth="micro")

    assert plan.kit_name == "LIVE BASE"
    assert plan.depth == "micro"
    assert plan.planned_pad_count == 2
    assert plan.planned_change_count == 12
    pad1 = plan.pads[0]
    assert pad1.machine_label == "BD Hard"
    assert pad1.baseline_status == "bd_hard_parameters"
    pad1_changes = {change.parameter_name: change for change in pad1.changes}
    assert pad1_changes["SRC Tune"].baseline_value == 59
    assert pad1_changes["SRC Tune"].planned_value == 60
    assert pad1_changes["SRC Tune"].delta == 1
    assert pad1_changes["SRC Decay"].baseline_value == 68
    assert pad1_changes["SRC Decay"].planned_value == 65
    assert pad1_changes["FLT Frequency"].baseline_value == 25
    assert pad1_changes["FLT Frequency"].planned_value == 22
    assert pad1_changes["AMP Decay"].baseline_value == 121
    assert pad1_changes["AMP Decay"].planned_value == 118
    pad2 = plan.pads[1]
    assert pad2.machine_label == "SD Natural"
    assert pad2.baseline_status == "generic_machine_parameters"
    pad2_changes = {change.parameter_name: change for change in pad2.changes}
    assert pad2_changes["SRC Slot 2"].baseline_value == 63
    assert pad2_changes["SRC Slot 2"].planned_value == 62
    assert pad2_changes["FLT Frequency"].baseline_value == 96
    assert pad2_changes["FLT Frequency"].planned_value == 99


def test_snapshot_mutation_plan_can_filter_to_one_pad():
    from rytm_randomizer.snapshot.rytm_decoder import decode_rytm_kit_snapshot_record
    from rytm_randomizer.snapshot.rytm_mutation_planner import (
        build_snapshot_mutation_plan,
        filter_snapshot_mutation_plan_to_pad,
    )

    snapshot = decode_rytm_kit_snapshot_record(
        make_rytm_kit_record(
            kit_name="PAD ONLY",
            machine_values=(0, 23) + tuple(27 for _ in range(10)),
            pad_parameter_values={
                1: {
                    0x1E: 59,
                    0x20: 68,
                    0x44: 25,
                    0x46: 14,
                    0x50: 121,
                    0x52: 36,
                },
                2: {
                    0x1E: 63,
                    0x20: 70,
                    0x44: 96,
                    0x46: 18,
                    0x4A: 62,
                    0x50: 88,
                },
            },
        )
    )

    plan = build_snapshot_mutation_plan(snapshot, depth="micro")
    filtered = filter_snapshot_mutation_plan_to_pad(plan, pad=2)

    assert filtered.kit_name == "PAD ONLY"
    assert len(filtered.pads) == 1
    assert filtered.planned_pad_count == 1
    assert filtered.blocked_pad_count == 0
    assert filtered.planned_change_count == 6
    assert filtered.pads[0].pad == 2
    assert filtered.pads[0].midi_channel == 2
    assert {change.pad for change in filtered.pads[0].changes} == {2}


def test_snapshot_mutation_plan_blocks_pad_machine_incompatibility():
    from rytm_randomizer.snapshot.rytm_decoder import decode_rytm_kit_snapshot_record
    from rytm_randomizer.snapshot.rytm_mutation_planner import build_snapshot_mutation_plan

    machine_values = [27 for _ in range(12)]
    machine_values[9] = 8  # Pad 10 is OH/open hihat; XT Classic belongs on Pads 6-8.
    snapshot = decode_rytm_kit_snapshot_record(
        make_rytm_kit_record(
            kit_name="BAD PAD",
            machine_values=tuple(machine_values),
            pad_parameter_values={
                10: {
                    0x1E: 63,
                    0x20: 70,
                    0x44: 96,
                    0x50: 88,
                }
            },
        )
    )

    plan = build_snapshot_mutation_plan(snapshot, depth="micro")
    pad10 = plan.pads[9]

    assert pad10.machine_label == "XT Classic"
    assert pad10.machine_compatibility_status == "incompatible_with_pad"
    assert pad10.plan_status == "blocked_machine_incompatible_with_pad"
    assert pad10.changes == ()
    assert plan.planned_pad_count == 0


def test_snapshot_mutation_plan_rejects_invalid_pad_filter():
    from rytm_randomizer.snapshot.rytm_decoder import decode_rytm_kit_snapshot_record
    from rytm_randomizer.snapshot.rytm_mutation_planner import (
        build_snapshot_mutation_plan,
        filter_snapshot_mutation_plan_to_pad,
    )

    snapshot = decode_rytm_kit_snapshot_record(
        make_rytm_kit_record(machine_values=(0,) + tuple(27 for _ in range(11)))
    )
    plan = build_snapshot_mutation_plan(snapshot, depth="micro")

    with pytest.raises(ValueError, match="Rytm snapshot pad must be 1 through 12"):
        filter_snapshot_mutation_plan_to_pad(plan, pad=13)


def test_snapshot_mutation_plan_rejects_unknown_depth():
    from rytm_randomizer.snapshot.rytm_decoder import decode_rytm_kit_snapshot_record
    from rytm_randomizer.snapshot.rytm_mutation_planner import (
        SnapshotMutationPlanError,
        build_snapshot_mutation_plan,
    )

    snapshot = decode_rytm_kit_snapshot_record(
        make_rytm_kit_record(machine_values=(0,) + tuple(27 for _ in range(11)))
    )

    with pytest.raises(SnapshotMutationPlanError, match="depth must be micro, groove, or strong"):
        build_snapshot_mutation_plan(snapshot, depth="chaos")


def test_snapshot_mutation_plan_cli_reads_saved_kit_without_hardware(tmp_path):
    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(
        make_rytm_kit_record(
            kit_name="CLI BASE",
            machine_values=(0,) + tuple(27 for _ in range(11)),
            pad_parameter_values={
                1: {
                    0x1E: 59,
                    0x20: 68,
                    0x44: 25,
                    0x46: 14,
                    0x50: 121,
                    0x52: 36,
                }
            },
        )
    )

    result = run_cli(
        "sysex-snapshot-mutation-plan-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Snapshot Mutation Plan Report" in result.stdout
    assert "Kit: CLI BASE" in result.stdout
    assert "Depth: micro" in result.stdout
    assert "Planned pads: 1 / 12" in result.stdout
    assert "Planned changes: 6" in result.stdout
    assert "- Pad 1 BD Hard / SRC Tune: CC17 59 -> 60 (delta +1)" in result.stdout
    assert "- captured-value relative" in result.stdout
    assert "- no anchor loading" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_snapshot_mutation_plan_cli_filters_to_one_pad(tmp_path):
    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(
        make_rytm_kit_record(
            kit_name="CLI PAD",
            machine_values=(0, 23) + tuple(27 for _ in range(10)),
            pad_parameter_values={
                1: {
                    0x1E: 59,
                    0x20: 68,
                    0x44: 25,
                    0x46: 14,
                    0x50: 121,
                    0x52: 36,
                },
                2: {
                    0x1E: 63,
                    0x20: 70,
                    0x44: 96,
                    0x46: 18,
                    0x4A: 62,
                    0x50: 88,
                },
            },
        )
    )

    result = run_cli(
        "sysex-snapshot-mutation-plan-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
        "--pad",
        "2",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Snapshot Mutation Plan Report" in result.stdout
    assert "Kit: CLI PAD" in result.stdout
    assert "Pads scanned: 2" in result.stdout
    assert "Planned pads: 1 / 1" in result.stdout
    assert "Blocked pads: 0 / 1" in result.stdout
    assert "Planned changes: 6" in result.stdout
    assert "- Pad 2 / MIDI channel 2:" in result.stdout
    assert "- Pad 1 " not in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
