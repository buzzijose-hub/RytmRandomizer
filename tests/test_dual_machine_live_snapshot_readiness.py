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


def make_rytm_kit_record(slot_index=0, kit_name="READY", values=None):
    values = values or {
        1: {
            0x1E: 59,
            0x20: 68,
            0x44: 25,
            0x46: 14,
            0x4A: 65,
            0x50: 121,
        }
    }
    decoded = bytearray(58 + (12 * 162) + 8)
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    for pad in range(1, 13):
        sound_name = f"SOUND {pad}"
        offset = 58 + ((pad - 1) * 162)
        track_offset = 46 + ((pad - 1) * 162)
        decoded[offset : offset + len(sound_name)] = sound_name.encode("ascii")
        decoded[track_offset + 0x7C] = 0 if pad == 1 else 27
        for parameter_offset, value in values.get(pad, {}).items():
            decoded[track_offset + parameter_offset] = value
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, slot_index])
        + pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


def make_a4_kit_record(slot_index=0, kit_name="A4 READY", track_values=None):
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


def test_importing_dual_machine_live_snapshot_readiness_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.dual_machine.live_snapshot_readiness; "
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


def test_safe_starter_bridge_is_mapping_ready(tmp_path):
    from rytm_randomizer.dual_machine.live_snapshot_readiness import (
        evaluate_dual_machine_live_snapshot_readiness,
    )
    from rytm_randomizer.dual_machine.mock_bridge import build_dual_machine_mock_bridge

    rytm_path = tmp_path / "rytm-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record())

    bridge = build_dual_machine_mock_bridge(str(rytm_path), slot=1, depth="micro")
    readiness = evaluate_dual_machine_live_snapshot_readiness(bridge)

    assert readiness.ready is True
    assert readiness.reason == "all_active_devices_mapping_ready"
    assert readiness.combined_message_count == 26
    assert readiness.devices[0].status == "ready_mapped_cc"
    assert readiness.devices[0].mapped_cc_count == 6
    assert readiness.devices[1].status == "ready_safe_starter_cc"
    assert readiness.devices[1].mapped_cc_count == 20
    assert readiness.devices[1].candidate_event_count == 0


def test_a4_snapshot_candidates_block_live_snapshot_readiness(tmp_path):
    from rytm_randomizer.dual_machine.live_snapshot_readiness import (
        evaluate_dual_machine_live_snapshot_readiness,
    )
    from rytm_randomizer.dual_machine.mock_bridge import build_dual_machine_mock_bridge

    rytm_path = tmp_path / "rytm-kits.syx"
    a4_path = tmp_path / "a4-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record())
    a4_path.write_bytes(
        make_a4_kit_record(
            track_values={
                1: {20: 64, 22: 80, 24: 96},
                2: {20: 32, 22: 48},
            }
        )
    )

    bridge = build_dual_machine_mock_bridge(
        str(rytm_path),
        slot=1,
        depth="micro",
        analog_four_sysex_path=str(a4_path),
        analog_four_slot=1,
    )
    readiness = evaluate_dual_machine_live_snapshot_readiness(bridge)

    assert readiness.ready is False
    assert readiness.reason == "blocked_by_unverified_candidates"
    assert readiness.combined_message_count == 11
    assert readiness.devices[0].status == "ready_mapped_cc"
    assert readiness.devices[1].status == "blocked_candidate_unverified"
    assert readiness.devices[1].message_count == 5
    assert readiness.devices[1].candidate_event_count == 5
    assert readiness.devices[1].reason == "candidate_unverified_no_cc_mapping"


def test_readiness_report_marks_a4_snapshot_candidates_blocked(tmp_path):
    from rytm_randomizer.dual_machine.live_snapshot_readiness import (
        evaluate_dual_machine_live_snapshot_readiness,
        format_dual_machine_live_snapshot_readiness_report,
    )
    from rytm_randomizer.dual_machine.mock_bridge import build_dual_machine_mock_bridge

    rytm_path = tmp_path / "rytm-kits.syx"
    a4_path = tmp_path / "a4-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record(kit_name="REPORT RYTM"))
    a4_path.write_bytes(
        make_a4_kit_record(
            kit_name="REPORT A4",
            track_values={1: {20: 64, 22: 80}},
        )
    )

    bridge = build_dual_machine_mock_bridge(
        str(rytm_path),
        slot=1,
        depth="micro",
        analog_four_sysex_path=str(a4_path),
        analog_four_slot=1,
    )
    readiness = evaluate_dual_machine_live_snapshot_readiness(bridge)
    report = "\n".join(format_dual_machine_live_snapshot_readiness_report(readiness))

    assert "RytmRandomizer passive Dual-Machine Live Snapshot Readiness Report" in report
    assert "Ready: False" in report
    assert "Reason: blocked_by_unverified_candidates" in report
    assert (
        "Analog Four MKII: active / saved-kit snapshot candidates / blocked_candidate_unverified"
        in report
    )
    assert "candidate events 2" in report
    assert "- saved-offset candidate events block hardware sending" in report
    assert "- no MIDI sending" in report


def test_dual_machine_live_snapshot_readiness_cli_reads_saved_dumps(tmp_path):
    rytm_path = tmp_path / "rytm-kits.syx"
    a4_path = tmp_path / "a4-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record(kit_name="CLI READY RYTM"))
    a4_path.write_bytes(
        make_a4_kit_record(
            kit_name="CLI READY A4",
            track_values={1: {20: 64, 22: 80}},
        )
    )

    result = run_cli(
        "dual-machine-live-snapshot-readiness-report",
        str(rytm_path),
        "--slot",
        "1",
        "--depth",
        "micro",
        "--analog-four-path",
        str(a4_path),
        "--analog-four-slot",
        "1",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Dual-Machine Live Snapshot Readiness Report" in result.stdout
    assert "Ready: False" in result.stdout
    assert "Reason: blocked_by_unverified_candidates" in result.stdout
    assert (
        "Analog Four MKII: active / saved-kit snapshot candidates / blocked_candidate_unverified"
        in result.stdout
    )
    assert "candidate_unverified_no_cc_mapping" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_dual_machine_live_snapshot_readiness_cli_accepts_lane_filters(tmp_path):
    rytm_path = tmp_path / "rytm-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record(kit_name="CLI READY LANES"))

    result = run_cli(
        "dual-machine-live-snapshot-readiness-report",
        str(rytm_path),
        "--slot",
        "1",
        "--depth",
        "micro",
        "--rytm-pad",
        "1",
        "--analog-four-track",
        "4",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Dual-Machine Live Snapshot Readiness Report" in result.stdout
    assert "Ready: True" in result.stdout
    assert "Combined mock messages: 11" in result.stdout
    assert (
        "Analog Rytm MKII: active / saved-kit snapshot / ready_mapped_cc / "
        "messages 6 / mapped CC 6" in result.stdout
    )
    assert (
        "Analog Four MKII: active / safe starter CC plan / ready_safe_starter_cc / "
        "messages 5 / mapped CC 5" in result.stdout
    )
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
