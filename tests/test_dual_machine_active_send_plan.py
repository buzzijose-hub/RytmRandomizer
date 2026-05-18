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


def make_rytm_kit_record(slot_index=0, kit_name="SEND PLAN", values=None):
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


def make_a4_kit_record(slot_index=0, kit_name="A4 SEND", track_values=None):
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


def test_importing_dual_machine_active_send_plan_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.dual_machine_active_send_plan; "
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


def test_safe_starter_bridge_has_only_eligible_mapped_cc_events(tmp_path):
    from rytm_randomizer.dual_machine_active_send_plan import (
        build_dual_machine_active_send_plan,
    )
    from rytm_randomizer.dual_machine_mock_bridge import build_dual_machine_mock_bridge

    rytm_path = tmp_path / "rytm-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record())

    bridge = build_dual_machine_mock_bridge(str(rytm_path), slot=1, depth="micro")
    plan = build_dual_machine_active_send_plan(bridge)

    assert plan.ready is True
    assert plan.readiness_reason == "all_active_devices_mapping_ready"
    assert plan.eligible_message_count == 26
    assert plan.blocked_event_count == 0
    assert plan.combined_event_count == 26
    first = plan.events[0]
    assert first.eligible is True
    assert first.reason == "mapped_cc_message"
    assert first.device == "Analog Rytm MKII"
    assert first.message_type == "cc"
    assert first.channel == 0
    assert first.control == 17
    assert first.value == 60
    assert first.source == "saved-kit snapshot"
    assert "Rytm Pad 1" in first.label
    a4_events = [event for event in plan.events if event.device == "Analog Four MKII"]
    assert len(a4_events) == 20
    assert all(event.eligible for event in a4_events)
    assert {event.source for event in a4_events} == {"safe starter CC plan"}
    assert [(event.control, event.value) for event in a4_events[:5]] == [
        (95, 104),
        (69, 96),
        (78, 72),
        (18, 112),
        (10, 60),
    ]


def test_active_send_plan_reports_selected_a4_starter_profile(tmp_path):
    from rytm_randomizer.dual_machine_active_send_plan import (
        build_dual_machine_active_send_plan,
        format_dual_machine_active_send_plan_report,
    )
    from rytm_randomizer.dual_machine_mock_bridge import build_dual_machine_mock_bridge

    rytm_path = tmp_path / "rytm-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record())

    bridge = build_dual_machine_mock_bridge(
        str(rytm_path),
        slot=1,
        depth="micro",
        target="analog-four",
        analog_four_profile="peak time",
    )
    plan = build_dual_machine_active_send_plan(bridge)
    report = "\n".join(format_dual_machine_active_send_plan_report(plan))

    assert plan.analog_four_starter_profile_key == "peak-time"
    assert plan.analog_four_starter_profile_label == "Peak Time"
    assert plan.eligible_message_count == 20
    assert "Analog Four starter profile: Peak Time / peak-time" in report
    assert "- eligible / Analog Four MKII / ch 1 wire 0 / CC95 -> 108" in report


def test_a4_saved_snapshot_candidates_are_blocked_but_rytm_ccs_remain_visible(tmp_path):
    from rytm_randomizer.dual_machine_active_send_plan import (
        build_dual_machine_active_send_plan,
    )
    from rytm_randomizer.dual_machine_mock_bridge import build_dual_machine_mock_bridge

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
    plan = build_dual_machine_active_send_plan(bridge)

    assert plan.ready is False
    assert plan.readiness_reason == "blocked_by_unverified_candidates"
    assert plan.eligible_message_count == 6
    assert plan.blocked_event_count == 5
    assert plan.combined_event_count == 11
    blocked = [event for event in plan.events if not event.eligible]
    assert {event.device for event in blocked} == {"Analog Four MKII"}
    assert {event.message_type for event in blocked} == {"saved_offset_candidate"}
    assert {event.reason for event in blocked} == {"candidate_unverified_no_cc_mapping"}
    assert blocked[0].channel == 0
    assert blocked[0].control == 20
    assert blocked[0].value == 67
    assert blocked[0].source == "saved_parameter_offset_candidate_unverified"
    assert "Track 1" in blocked[0].label


def test_active_send_plan_report_shows_event_policy_and_safety(tmp_path):
    from rytm_randomizer.dual_machine_active_send_plan import (
        build_dual_machine_active_send_plan,
        format_dual_machine_active_send_plan_report,
    )
    from rytm_randomizer.dual_machine_mock_bridge import build_dual_machine_mock_bridge

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
    plan = build_dual_machine_active_send_plan(bridge)
    report = "\n".join(format_dual_machine_active_send_plan_report(plan))

    assert "RytmRandomizer passive Dual-Machine Active Send Plan Report" in report
    assert "Send plan ready: False" in report
    assert "Readiness reason: blocked_by_unverified_candidates" in report
    assert "Eligible mapped CC messages: 6" in report
    assert "Blocked candidate events: 2" in report
    assert "- eligible / Analog Rytm MKII / ch 1 wire 0 / CC17 -> 60" in report
    assert "- blocked / Analog Four MKII / Track 1" in report
    assert "candidate_unverified_no_cc_mapping" in report
    assert "- saved-offset candidate events are blocked" in report
    assert "- no MIDI sending" in report


def test_dual_machine_active_send_plan_cli_reads_saved_dumps(tmp_path):
    rytm_path = tmp_path / "rytm-kits.syx"
    a4_path = tmp_path / "a4-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record(kit_name="CLI SEND RYTM"))
    a4_path.write_bytes(
        make_a4_kit_record(
            kit_name="CLI SEND A4",
            track_values={1: {20: 64, 22: 80}},
        )
    )

    result = run_cli(
        "dual-machine-active-send-plan-report",
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
    assert "RytmRandomizer passive Dual-Machine Active Send Plan Report" in result.stdout
    assert "Send plan ready: False" in result.stdout
    assert "Readiness reason: blocked_by_unverified_candidates" in result.stdout
    assert "Eligible mapped CC messages: 6" in result.stdout
    assert "Blocked candidate events: 2" in result.stdout
    assert "candidate_unverified_no_cc_mapping" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
