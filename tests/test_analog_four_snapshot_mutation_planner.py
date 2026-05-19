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


def make_a4_kit_record(slot_index=0, kit_name="A4 PLAN", track_values=None):
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


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_analog_four_snapshot_mutation_planner_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four.snapshot_mutation_planner; "
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


def test_analog_four_snapshot_mutation_plan_uses_captured_values_not_starters():
    from rytm_randomizer.analog_four.snapshot_mutation_planner import (
        build_analog_four_snapshot_mutation_plan_from_bytes,
    )

    plan = build_analog_four_snapshot_mutation_plan_from_bytes(
        make_a4_kit_record(
            kit_name="CAPTURED A4",
            track_values={
                1: {20: 64, 22: 80, 24: 96},
                2: {20: 32, 22: 48},
                3: {20: 100, 22: 111},
                4: {20: 12, 22: 24},
            },
        ),
        slot=1,
        depth="micro",
    )

    assert plan.slot_number == 1
    assert plan.kit_name == "CAPTURED A4"
    assert plan.depth == "micro"
    assert plan.planned_track_count == 4
    assert plan.planned_change_count == 9
    track1 = plan.tracks[0]
    assert track1.track == 1
    assert track1.name == "BASS LOW"
    assert track1.plan_status == "planned_candidate_offsets"
    first = track1.changes[0]
    assert first.relative_offset == 20
    assert first.word_index == 10
    assert first.baseline_value == 64
    assert first.planned_value == 67
    assert first.delta == 3
    assert first.mapping_status == "candidate_unverified"
    assert first.source == "saved_parameter_offset_candidate_unverified"
    track2_change = plan.tracks[1].changes[0]
    assert track2_change.baseline_value == 32
    assert track2_change.planned_value == 35


def test_analog_four_snapshot_mutation_plan_can_filter_to_one_track():
    from rytm_randomizer.analog_four.snapshot_mutation_planner import (
        build_analog_four_snapshot_mutation_plan_from_bytes,
        filter_analog_four_snapshot_mutation_plan_to_track,
    )

    plan = build_analog_four_snapshot_mutation_plan_from_bytes(
        make_a4_kit_record(
            kit_name="TRACK ONLY",
            track_values={
                1: {20: 64, 22: 80},
                2: {20: 32, 22: 48, 24: 60},
                3: {20: 100},
                4: {20: 12},
            },
        ),
        slot=1,
        depth="micro",
    )

    filtered = filter_analog_four_snapshot_mutation_plan_to_track(plan, track=2)

    assert filtered.kit_name == "TRACK ONLY"
    assert len(filtered.tracks) == 1
    assert filtered.planned_track_count == 1
    assert filtered.blocked_track_count == 0
    assert filtered.planned_change_count == 3
    assert filtered.tracks[0].track == 2
    assert filtered.tracks[0].wire_channel == 1
    assert {change.track for change in filtered.tracks[0].changes} == {2}


def test_analog_four_snapshot_mutation_plan_rejects_invalid_track_filter():
    from rytm_randomizer.analog_four.snapshot_mutation_planner import (
        build_analog_four_snapshot_mutation_plan_from_bytes,
        filter_analog_four_snapshot_mutation_plan_to_track,
    )

    plan = build_analog_four_snapshot_mutation_plan_from_bytes(
        make_a4_kit_record(track_values={1: {20: 64}}),
        slot=1,
        depth="micro",
    )

    with pytest.raises(ValueError, match="Analog Four snapshot track must be 1, 2, 3, or 4"):
        filter_analog_four_snapshot_mutation_plan_to_track(plan, track=5)


def test_analog_four_snapshot_mutation_plan_rejects_unknown_depth():
    from rytm_randomizer.analog_four.snapshot_mutation_planner import (
        AnalogFourSnapshotMutationPlanError,
        build_analog_four_snapshot_mutation_plan_from_bytes,
    )

    with pytest.raises(
        AnalogFourSnapshotMutationPlanError,
        match="depth must be micro, groove, or strong",
    ):
        build_analog_four_snapshot_mutation_plan_from_bytes(
            make_a4_kit_record(track_values={1: {20: 64}}),
            slot=1,
            depth="maximum",
        )


def test_format_analog_four_snapshot_mutation_plan_report_marks_unverified_boundary():
    from rytm_randomizer.analog_four.snapshot_mutation_planner import (
        build_analog_four_snapshot_mutation_plan_from_bytes,
        format_analog_four_snapshot_mutation_plan_report,
    )

    plan = build_analog_four_snapshot_mutation_plan_from_bytes(
        make_a4_kit_record(track_values={1: {20: 64}, 2: {20: 32}}),
        slot=1,
        depth="micro",
    )
    report = "\n".join(format_analog_four_snapshot_mutation_plan_report(plan))

    assert "RytmRandomizer passive Analog Four Snapshot Mutation Plan Report" in report
    assert "Kit: A4 PLAN" in report
    assert "Planned tracks: 2 / 4" in report
    assert "- Track 1 BASS LOW / Offset +20 / word 10: 64 -> 67" in report
    assert "candidate_unverified" in report
    assert "- captured-value relative" in report
    assert "- candidate offsets only" in report
    assert "- no parameter names claimed" in report
    assert "- no MIDI sending" in report


def test_analog_four_snapshot_mutation_plan_cli_reads_saved_kit_without_hardware(tmp_path):
    sysex_path = tmp_path / "a4-kits.syx"
    sysex_path.write_bytes(
        make_a4_kit_record(
            kit_name="CLI PLAN",
            track_values={1: {20: 64, 22: 80}, 2: {20: 32}},
        )
    )

    result = run_cli(
        "analog-four-snapshot-mutation-plan-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four Snapshot Mutation Plan Report" in result.stdout
    assert "Kit: CLI PLAN" in result.stdout
    assert "Planned changes: 3" in result.stdout
    assert "candidate_unverified" in result.stdout
    assert "- no parameter names claimed" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_analog_four_snapshot_mutation_plan_cli_filters_to_one_track(tmp_path):
    sysex_path = tmp_path / "a4-kits.syx"
    sysex_path.write_bytes(
        make_a4_kit_record(
            kit_name="CLI ONE TRACK",
            track_values={
                1: {20: 64, 22: 80},
                2: {20: 32, 22: 48, 24: 60},
            },
        )
    )

    result = run_cli(
        "analog-four-snapshot-mutation-plan-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
        "--track",
        "2",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four Snapshot Mutation Plan Report" in result.stdout
    assert "Kit: CLI ONE TRACK" in result.stdout
    assert "Tracks scanned: 2" in result.stdout
    assert "Planned tracks: 1 / 1" in result.stdout
    assert "Planned changes: 3" in result.stdout
    assert "- Track 2 / MIDI channel 2: STAB HIT" in result.stdout
    assert "- Track 1 " not in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
