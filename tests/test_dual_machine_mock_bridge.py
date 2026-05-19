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


def make_rytm_kit_record(slot_index=0, kit_name="BRIDGE", machine_values=None, values=None):
    machine_values = machine_values or ((0,) + tuple(27 for _ in range(11)))
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
        decoded[track_offset + 0x7C] = machine_values[pad - 1]
        for parameter_offset, value in values.get(pad, {}).items():
            decoded[track_offset + parameter_offset] = value
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, slot_index])
        + pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


def make_a4_kit_record(slot_index=0, kit_name="A4 BRIDGE", track_values=None):
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


def test_importing_dual_machine_bridge_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.dual_machine.mock_bridge; "
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


def test_dual_bridge_combines_rytm_snapshot_and_a4_safe_starter(tmp_path):
    from rytm_randomizer.dual_machine.mock_bridge import (
        build_dual_machine_mock_bridge,
        capture_dual_machine_mock_messages,
    )

    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(kit_name="BRIDGE KIT"))

    bridge = build_dual_machine_mock_bridge(str(sysex_path), slot=1, depth="micro")
    sender = capture_dual_machine_mock_messages(bridge)

    assert bridge.rytm_source == "saved-kit snapshot"
    assert bridge.analog_four_source == "safe starter CC plan"
    assert bridge.rytm_plan.kit_name == "BRIDGE KIT"
    assert bridge.rytm_message_count == 6
    assert bridge.analog_four_track_count == 4
    assert bridge.analog_four_message_count == 20
    assert bridge.combined_message_count == 26
    assert len(sender.sent_messages) == 26
    first = sender.sent_messages[0]
    assert first.channel == 0
    assert first.control == 17
    assert first.value == 60
    assert first.metadata["device"] == "Analog Rytm MKII"
    assert first.metadata["baseline_value"] == 59
    a4_messages = [
        message
        for message in sender.sent_messages
        if message.metadata["device"] == "Analog Four MKII"
    ]
    assert [(message.control, message.value) for message in a4_messages[:5]] == [
        (95, 104),
        (69, 96),
        (78, 72),
        (18, 112),
        (10, 60),
    ]
    last = sender.sent_messages[-1]
    assert last.channel == 3
    assert last.metadata["device"] == "Analog Four MKII"
    assert last.metadata["track"] == 4
    assert last.control == 10
    assert last.value == 64
    assert {message.metadata["device"] for message in sender.sent_messages} == {
        "Analog Rytm MKII",
        "Analog Four MKII",
    }


def test_dual_bridge_uses_a4_snapshot_when_path_is_supplied(tmp_path):
    from rytm_randomizer.dual_machine.mock_bridge import (
        build_dual_machine_mock_bridge,
        capture_dual_machine_mock_messages,
    )

    rytm_path = tmp_path / "rytm-kits.syx"
    a4_path = tmp_path / "a4-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record(kit_name="RYTM SNAP"))
    a4_path.write_bytes(
        make_a4_kit_record(
            kit_name="A4 SNAP",
            track_values={
                1: {20: 64, 22: 80, 24: 96},
                2: {20: 32, 22: 48},
            },
        )
    )

    bridge = build_dual_machine_mock_bridge(
        str(rytm_path),
        slot=1,
        depth="micro",
        analog_four_sysex_path=str(a4_path),
        analog_four_slot=1,
    )
    sender = capture_dual_machine_mock_messages(bridge)

    assert bridge.analog_four_source == "saved-kit snapshot candidates"
    assert bridge.analog_four_source_path == str(a4_path)
    assert bridge.analog_four_slot == 1
    assert bridge.analog_four_kit_name == "A4 SNAP"
    assert bridge.rytm_message_count == 6
    assert bridge.analog_four_message_count == 5
    assert bridge.combined_message_count == 11
    assert len(sender.sent_messages) == 11
    first_a4 = next(
        message
        for message in sender.sent_messages
        if message.metadata["device"] == "Analog Four MKII"
    )
    assert first_a4.type == "saved_offset_candidate"
    assert first_a4.channel == 0
    assert first_a4.control == 20
    assert first_a4.value == 67
    assert first_a4.metadata["track"] == 1
    assert first_a4.metadata["track_name"] == "BASS LOW"
    assert first_a4.metadata["saved_offset"] == 20
    assert first_a4.metadata["baseline_value"] == 64
    assert first_a4.metadata["mapping_status"] == "candidate_unverified"
    assert first_a4.metadata["cc_mapping_claimed"] is False
    assert first_a4.metadata["sends_real_midi"] is False


def test_dual_bridge_rytm_target_emits_only_rytm_messages(tmp_path):
    from rytm_randomizer.dual_machine.mock_bridge import (
        build_dual_machine_mock_bridge,
        capture_dual_machine_mock_messages,
    )

    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(kit_name="RYTM ONLY"))

    bridge = build_dual_machine_mock_bridge(
        str(sysex_path),
        slot=1,
        depth="micro",
        target="rytm",
    )
    sender = capture_dual_machine_mock_messages(bridge)

    assert bridge.target_plan.canonical_target == "rytm"
    assert bridge.target_plan.untouched_device_keys == ("analog_four",)
    assert bridge.rytm_message_count == 6
    assert bridge.analog_four_message_count == 0
    assert bridge.combined_message_count == 6
    assert len(sender.sent_messages) == 6
    assert {message.metadata["device"] for message in sender.sent_messages} == {
        "Analog Rytm MKII",
    }


def test_dual_bridge_analog_four_target_emits_only_a4_messages(tmp_path):
    from rytm_randomizer.dual_machine.mock_bridge import (
        build_dual_machine_mock_bridge,
        capture_dual_machine_mock_messages,
    )

    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(kit_name="A4 ONLY"))

    bridge = build_dual_machine_mock_bridge(
        str(sysex_path),
        slot=1,
        depth="micro",
        target="analog-four",
    )
    sender = capture_dual_machine_mock_messages(bridge)

    assert bridge.target_plan.canonical_target == "analog-four"
    assert bridge.target_plan.untouched_device_keys == ("analog_rytm",)
    assert bridge.rytm_message_count == 0
    assert bridge.analog_four_message_count == 20
    assert bridge.combined_message_count == 20
    assert len(sender.sent_messages) == 20
    assert {message.metadata["device"] for message in sender.sent_messages} == {
        "Analog Four MKII",
    }
    track4_messages = [
        message for message in sender.sent_messages if message.metadata["track"] == 4
    ]
    assert [(message.control, message.value) for message in track4_messages] == [
        (95, 88),
        (77, 72),
        (76, 68),
        (18, 88),
        (10, 64),
    ]


def test_dual_bridge_accepts_birmingham_analog_four_profile(tmp_path):
    from rytm_randomizer.dual_machine.mock_bridge import (
        build_dual_machine_mock_bridge,
        capture_dual_machine_mock_messages,
        format_dual_machine_mock_bridge_report,
    )

    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(kit_name="A4 PROFILE"))

    bridge = build_dual_machine_mock_bridge(
        str(sysex_path),
        slot=1,
        depth="micro",
        target="analog-four",
        analog_four_profile="birmingham_dark",
    )
    sender = capture_dual_machine_mock_messages(bridge)
    report = "\n".join(format_dual_machine_mock_bridge_report(bridge))

    assert bridge.analog_four_starter_profile_key == "birmingham-dark"
    assert bridge.analog_four_starter_profile_label == "Birmingham Dark"
    assert bridge.analog_four_message_count == 20
    assert len(sender.sent_messages) == 20
    assert [(message.control, message.value) for message in sender.sent_messages[:5]] == [
        (95, 106),
        (69, 92),
        (78, 84),
        (18, 96),
        (10, 58),
    ]
    assert "Analog Four starter profile: Birmingham Dark / birmingham-dark" in report
    assert "Track Level: CC95 -> 106" in report


def test_dual_bridge_filters_rytm_pad_and_a4_starter_track(tmp_path):
    from rytm_randomizer.dual_machine.mock_bridge import (
        build_dual_machine_mock_bridge,
        capture_dual_machine_mock_messages,
        format_dual_machine_mock_bridge_report,
    )

    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(
        make_rytm_kit_record(
            kit_name="LANE FILTER",
            machine_values=(0, 23) + tuple(27 for _ in range(10)),
            values={
                1: {
                    0x1E: 59,
                    0x20: 68,
                    0x44: 25,
                    0x46: 14,
                    0x4A: 65,
                    0x50: 121,
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

    bridge = build_dual_machine_mock_bridge(
        str(sysex_path),
        slot=1,
        depth="micro",
        rytm_pad=2,
        analog_four_track=4,
    )
    sender = capture_dual_machine_mock_messages(bridge)
    report = "\n".join(format_dual_machine_mock_bridge_report(bridge))

    assert bridge.rytm_message_count == 6
    assert bridge.analog_four_track_count == 1
    assert bridge.analog_four_message_count == 5
    assert bridge.combined_message_count == 11
    assert {
        message.metadata.get("pad") for message in sender.sent_messages if "pad" in message.metadata
    } == {2}
    assert {
        message.metadata.get("track")
        for message in sender.sent_messages
        if message.metadata["device"] == "Analog Four MKII"
    } == {4}
    assert "Rytm planned pads: 1 / 1" in report
    assert "Analog Four tracks: 1 / 1" in report
    assert "- Rytm Pad 2 / SD Natural: 6 message(s)" in report
    assert "- Analog Four Track 4 / FX / noise / transition: 5 message(s)" in report
    assert "- Rytm Pad 1 " not in report
    assert "- Analog Four Track 1 " not in report


def test_dual_bridge_filters_a4_snapshot_track(tmp_path):
    from rytm_randomizer.dual_machine.mock_bridge import (
        build_dual_machine_mock_bridge,
        capture_dual_machine_mock_messages,
        format_dual_machine_mock_bridge_report,
    )

    rytm_path = tmp_path / "rytm-kits.syx"
    a4_path = tmp_path / "a4-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record(kit_name="RYTM LANE"))
    a4_path.write_bytes(
        make_a4_kit_record(
            kit_name="A4 LANE",
            track_values={
                1: {20: 64, 22: 80, 24: 96},
                2: {20: 32, 22: 48},
            },
        )
    )

    bridge = build_dual_machine_mock_bridge(
        str(rytm_path),
        slot=1,
        depth="micro",
        analog_four_sysex_path=str(a4_path),
        analog_four_slot=1,
        analog_four_track=2,
    )
    sender = capture_dual_machine_mock_messages(bridge)
    report = "\n".join(format_dual_machine_mock_bridge_report(bridge))

    assert bridge.analog_four_source == "saved-kit snapshot candidates"
    assert bridge.analog_four_track_count == 1
    assert bridge.analog_four_message_count == 2
    assert bridge.combined_message_count == 8
    assert {
        message.metadata.get("track")
        for message in sender.sent_messages
        if message.metadata["device"] == "Analog Four MKII"
    } == {2}
    assert "Analog Four tracks: 1 / 1" in report
    assert "- Analog Four Track 2 / STAB HIT: 2 message(s)" in report
    assert "- Analog Four Track 1 " not in report


def test_dual_bridge_rejects_starter_profile_with_a4_snapshot_path(tmp_path):
    from rytm_randomizer.dual_machine.mock_bridge import build_dual_machine_mock_bridge

    rytm_path = tmp_path / "rytm-kits.syx"
    a4_path = tmp_path / "a4-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record(kit_name="RYTM SNAP"))
    a4_path.write_bytes(make_a4_kit_record(kit_name="A4 SNAP"))

    try:
        build_dual_machine_mock_bridge(
            str(rytm_path),
            slot=1,
            depth="micro",
            analog_four_sysex_path=str(a4_path),
            analog_four_slot=1,
            analog_four_profile="birmingham-dark",
        )
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected profile/source conflict to fail")

    assert (
        "Analog Four starter profile cannot be combined with Analog Four snapshot path" in message
    )


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_dual_machine_mock_bridge_cli_reads_saved_kit_without_hardware(tmp_path):
    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(kit_name="CLI BRIDGE"))

    result = run_cli(
        "dual-machine-mock-bridge-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Dual-Machine Mock Bridge Report" in result.stdout
    assert "Rytm source: saved-kit snapshot" in result.stdout
    assert "Analog Four source: safe starter CC plan" in result.stdout
    assert "Combined mock messages: 26" in result.stdout
    assert "- Analog Four Track 4 / FX / noise / transition: 5 message(s)" in result.stdout
    assert "Noise Level: CC77 -> 72" in result.stdout
    assert "- mock sender only" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_dual_machine_mock_bridge_cli_accepts_a4_snapshot_path(tmp_path):
    rytm_path = tmp_path / "rytm-kits.syx"
    a4_path = tmp_path / "a4-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record(kit_name="CLI RYTM SNAP"))
    a4_path.write_bytes(
        make_a4_kit_record(
            kit_name="CLI A4 SNAP",
            track_values={
                1: {20: 64, 22: 80, 24: 96},
                2: {20: 32, 22: 48},
            },
        )
    )

    result = run_cli(
        "dual-machine-mock-bridge-report",
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
    assert "RytmRandomizer passive Dual-Machine Mock Bridge Report" in result.stdout
    assert "Analog Four source: saved-kit snapshot candidates" in result.stdout
    assert f"Analog Four source path: {a4_path}" in result.stdout
    assert "Analog Four kit: CLI A4 SNAP" in result.stdout
    assert "Analog Four mock messages: 5" in result.stdout
    assert "Combined mock messages: 11" in result.stdout
    assert "- Analog Four Track 1 / BASS LOW: 3 message(s)" in result.stdout
    assert "Offset +20: 64 -> 67" in result.stdout
    assert "candidate_unverified" in result.stdout
    assert "- no CC mapping claimed" in result.stdout
    assert result.stderr == ""


def test_dual_machine_mock_bridge_cli_accepts_target_scope(tmp_path):
    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(kit_name="CLI TARGET"))

    result = run_cli(
        "dual-machine-mock-bridge-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
        "--target",
        "rytm",
    )

    assert result.returncode == 0
    assert "Target: rytm" in result.stdout
    assert "Active devices: Analog Rytm MKII" in result.stdout
    assert "Untouched devices: Analog Four MKII" in result.stdout
    assert "Analog Four mock messages: 0" in result.stdout
    assert "Combined mock messages: 6" in result.stdout
    assert "- Analog Four Track" not in result.stdout
    assert result.stderr == ""


def test_dual_machine_mock_bridge_cli_accepts_analog_four_profile(tmp_path):
    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(kit_name="CLI A4 PROFILE"))

    result = run_cli(
        "dual-machine-mock-bridge-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
        "--target",
        "analog-four",
        "--analog-four-profile",
        "birmingham-dark",
    )

    assert result.returncode == 0
    assert "Target: analog-four" in result.stdout
    assert "Analog Four starter profile: Birmingham Dark / birmingham-dark" in result.stdout
    assert "Combined mock messages: 20" in result.stdout
    assert "Track Level: CC95 -> 106" in result.stdout
    assert result.stderr == ""


def test_dual_machine_mock_bridge_cli_accepts_lane_filters(tmp_path):
    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(
        make_rytm_kit_record(
            kit_name="CLI LANES",
            machine_values=(0, 23) + tuple(27 for _ in range(10)),
            values={
                1: {
                    0x1E: 59,
                    0x20: 68,
                    0x44: 25,
                    0x46: 14,
                    0x4A: 65,
                    0x50: 121,
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
        "dual-machine-mock-bridge-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
        "--rytm-pad",
        "2",
        "--analog-four-track",
        "4",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Dual-Machine Mock Bridge Report" in result.stdout
    assert "Rytm planned pads: 1 / 1" in result.stdout
    assert "Analog Four tracks: 1 / 1" in result.stdout
    assert "Combined mock messages: 11" in result.stdout
    assert "- Rytm Pad 2 / SD Natural: 6 message(s)" in result.stdout
    assert "- Analog Four Track 4 / FX / noise / transition: 5 message(s)" in result.stdout
    assert "- Rytm Pad 1 " not in result.stdout
    assert "- Analog Four Track 1 " not in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_dual_machine_mock_bridge_cli_rejects_a4_snapshot_profile_conflict(tmp_path):
    rytm_path = tmp_path / "rytm-kits.syx"
    a4_path = tmp_path / "a4-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record(kit_name="CLI RYTM SNAP"))
    a4_path.write_bytes(make_a4_kit_record(kit_name="CLI A4 SNAP"))

    result = run_cli(
        "dual-machine-mock-bridge-report",
        str(rytm_path),
        "--slot",
        "1",
        "--depth",
        "micro",
        "--analog-four-path",
        str(a4_path),
        "--analog-four-slot",
        "1",
        "--analog-four-profile",
        "birmingham-dark",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        "Analog Four starter profile cannot be combined with Analog Four snapshot path"
        in result.stderr
    )


def test_dual_machine_mock_bridge_cli_main_covers_lane_success(tmp_path, capsys):
    from rytm_randomizer import cli

    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(
        make_rytm_kit_record(
            kit_name="MAIN LANES",
            machine_values=(0, 23) + tuple(27 for _ in range(10)),
            values={
                1: {
                    0x1E: 59,
                    0x20: 68,
                    0x44: 25,
                    0x46: 14,
                    0x4A: 65,
                    0x50: 121,
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

    result = cli.main(
        [
            "dual-machine-mock-bridge-report",
            str(sysex_path),
            "--slot",
            "1",
            "--depth",
            "micro",
            "--rytm-pad",
            "2",
            "--analog-four-track",
            "4",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "RytmRandomizer passive Dual-Machine Mock Bridge Report" in captured.out
    assert "Rytm planned pads: 1 / 1" in captured.out
    assert "Analog Four tracks: 1 / 1" in captured.out
    assert "Combined mock messages: 11" in captured.out
    assert captured.err == ""


def test_dual_machine_readiness_cli_main_covers_both_lane_success(tmp_path, capsys):
    from rytm_randomizer import cli

    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(kit_name="READY LANES"))

    result = cli.main(
        [
            "dual-machine-live-snapshot-readiness-report",
            str(sysex_path),
            "--slot",
            "1",
            "--depth",
            "micro",
            "--target",
            "both",
            "--rytm-pad",
            "1",
            "--analog-four-track",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "RytmRandomizer passive Dual-Machine Live Snapshot Readiness Report" in captured.out
    assert "Target: both" in captured.out
    assert "Ready: True" in captured.out
    assert "Combined mock messages: 11" in captured.out
    assert captured.err == ""


def test_dual_machine_active_send_cli_main_covers_rytm_lane_success(tmp_path, capsys):
    from rytm_randomizer import cli

    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(kit_name="ACTIVE LANES"))

    result = cli.main(
        [
            "dual-machine-active-send-plan-report",
            str(sysex_path),
            "--slot",
            "1",
            "--depth",
            "micro",
            "--target",
            "rytm",
            "--rytm-pad",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "RytmRandomizer passive Dual-Machine Active Send Plan Report" in captured.out
    assert "Target: rytm" in captured.out
    assert "Eligible mapped CC messages: 6" in captured.out
    assert "target_scope_leave_alone" not in captured.out
    assert captured.err == ""


def test_dual_machine_guarded_send_cli_main_covers_a4_lane_success(tmp_path, capsys):
    from rytm_randomizer import cli

    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(kit_name="GUARDED LANES"))

    result = cli.main(
        [
            "dual-machine-guarded-send-dry-run-report",
            str(sysex_path),
            "--slot",
            "1",
            "--depth",
            "micro",
            "--target",
            "analog-four",
            "--analog-four-track",
            "2",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "RytmRandomizer passive Dual-Machine Guarded Send Dry-Run Report" in captured.out
    assert "Target: analog-four" in captured.out
    assert "Emitted mock messages: 5" in captured.out
    assert "Analog Four MKII / ch 2 wire 1" in captured.out
    assert captured.err == ""
