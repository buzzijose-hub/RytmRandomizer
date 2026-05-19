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


def make_a4_kit_record(slot_index=0, kit_name="A4 MAP", track_values=None):
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


def test_importing_a4_saved_offset_mapping_promotion_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four.saved_offset_mapping_promotion; "
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


def test_a4_saved_offset_mapping_promotion_accepts_single_changed_offset():
    from rytm_randomizer.analog_four.saved_offset_mapping_promotion import (
        build_analog_four_saved_offset_mapping_promotion_from_bytes,
    )

    before = make_a4_kit_record(track_values={1: {20: 40, 22: 70}})
    after = make_a4_kit_record(track_values={1: {20: 96, 22: 70}})

    promotion = build_analog_four_saved_offset_mapping_promotion_from_bytes(
        before,
        after,
        slot=1,
        track=1,
        parameter="filter-1-frequency",
        limit=8,
    )

    assert promotion.ready is True
    assert promotion.reason == "single_changed_offset_ready_for_review"
    assert promotion.parameter_name == "Filter 1 Frequency"
    assert promotion.cc == 18
    assert promotion.relative_offset == 20
    assert promotion.mapping is not None
    assert promotion.mapping.track == 1
    assert promotion.mapping.relative_offset == 20
    assert promotion.mapping.parameter_name == "Filter 1 Frequency"
    assert promotion.mapping.cc == 18


def test_a4_saved_offset_mapping_promotion_blocks_multiple_changed_offsets():
    from rytm_randomizer.analog_four.saved_offset_mapping_promotion import (
        build_analog_four_saved_offset_mapping_promotion_from_bytes,
    )

    before = make_a4_kit_record(track_values={1: {20: 40, 22: 70}})
    after = make_a4_kit_record(track_values={1: {20: 96, 22: 80}})

    promotion = build_analog_four_saved_offset_mapping_promotion_from_bytes(
        before,
        after,
        slot=1,
        track=1,
        parameter="filter-1-frequency",
        limit=8,
    )

    assert promotion.ready is False
    assert promotion.reason == "blocked_multiple_changed_offsets"
    assert promotion.changed_candidate_count == 2
    assert promotion.mapping is None


def test_format_a4_saved_offset_mapping_promotion_report_includes_mapping_entry():
    from rytm_randomizer.analog_four.saved_offset_mapping_promotion import (
        build_analog_four_saved_offset_mapping_promotion_from_bytes,
        format_analog_four_saved_offset_mapping_promotion_report,
    )

    before = make_a4_kit_record(track_values={2: {28: 10}})
    after = make_a4_kit_record(track_values={2: {28: 100}})
    promotion = build_analog_four_saved_offset_mapping_promotion_from_bytes(
        before,
        after,
        slot=1,
        track=2,
        parameter="amp-pan",
        limit=8,
    )
    report = "\n".join(format_analog_four_saved_offset_mapping_promotion_report(promotion))

    assert "RytmRandomizer passive Analog Four Saved-Offset Mapping Promotion Report" in report
    assert "Ready: True" in report
    assert "Reason: single_changed_offset_ready_for_review" in report
    assert "Parameter: Amp Pan" in report
    assert "Known runtime CC: CC10" in report
    assert "relative_offset=28" in report
    assert 'parameter_name="Amp Pan"' in report
    assert "cc=10" in report
    assert "- no MIDI sending" in report
    assert "- no SysEx writes" in report


def test_a4_saved_offset_mapping_promotion_cli_reads_saved_files(tmp_path):
    before_path = tmp_path / "a4-before.syx"
    after_path = tmp_path / "a4-after.syx"
    before_path.write_bytes(make_a4_kit_record(track_values={1: {20: 40}}))
    after_path.write_bytes(make_a4_kit_record(track_values={1: {20: 96}}))

    result = run_cli(
        "analog-four-saved-offset-mapping-promotion-report",
        str(before_path),
        str(after_path),
        "--slot",
        "1",
        "--track",
        "1",
        "--parameter",
        "filter-1-frequency",
        "--limit",
        "8",
    )

    assert result.returncode == 0
    assert (
        "RytmRandomizer passive Analog Four Saved-Offset Mapping Promotion Report" in result.stdout
    )
    assert "Ready: True" in result.stdout
    assert "relative_offset=20" in result.stdout
    assert "cc=18" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_a4_saved_offset_mapping_promotion_cli_rejects_invalid_parameter(tmp_path):
    before_path = tmp_path / "a4-before.syx"
    after_path = tmp_path / "a4-after.syx"
    before_path.write_bytes(make_a4_kit_record(track_values={1: {20: 40}}))
    after_path.write_bytes(make_a4_kit_record(track_values={1: {20: 96}}))

    result = run_cli(
        "analog-four-saved-offset-mapping-promotion-report",
        str(before_path),
        str(after_path),
        "--slot",
        "1",
        "--track",
        "1",
        "--parameter",
        "pitch-cloud",
        "--limit",
        "8",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "parameter must be one of" in result.stderr
    assert "No MIDI was sent" in result.stderr
