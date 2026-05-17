import subprocess
import sys
from pathlib import Path

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


def make_rytm_kit_record(slot_index=0, kit_name="GUARDED", values=None):
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


def make_a4_kit_record(slot_index=0, kit_name="A4 GUARD", track_values=None):
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


def build_plan(tmp_path, *, target="both", with_a4_snapshot=False):
    from rytm_randomizer.dual_machine_active_send_plan import (
        build_dual_machine_active_send_plan,
    )
    from rytm_randomizer.dual_machine_mock_bridge import build_dual_machine_mock_bridge

    rytm_path = tmp_path / "rytm-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record())
    kwargs = {}
    if with_a4_snapshot:
        a4_path = tmp_path / "a4-kits.syx"
        a4_path.write_bytes(
            make_a4_kit_record(
                track_values={
                    1: {20: 64, 22: 80},
                }
            )
        )
        kwargs = {
            "analog_four_sysex_path": str(a4_path),
            "analog_four_slot": 1,
        }

    bridge = build_dual_machine_mock_bridge(
        str(rytm_path),
        slot=1,
        depth="micro",
        target=target,
        **kwargs,
    )
    return build_dual_machine_active_send_plan(bridge)


def test_importing_dual_machine_guarded_sender_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.dual_machine_guarded_sender; "
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


def test_guarded_send_requires_arming_before_emitting(tmp_path):
    from rytm_randomizer.dual_machine_guarded_sender import (
        execute_dual_machine_guarded_send,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    result = execute_dual_machine_guarded_send(
        build_plan(tmp_path),
        sender,
        armed=False,
        dry_run_confirmed=True,
    )

    assert result.accepted is False
    assert result.reason == "missing_arming"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_guarded_send_requires_dry_run_confirmation_before_emitting(tmp_path):
    from rytm_randomizer.dual_machine_guarded_sender import (
        execute_dual_machine_guarded_send,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    result = execute_dual_machine_guarded_send(
        build_plan(tmp_path),
        sender,
        armed=True,
        dry_run_confirmed=False,
    )

    assert result.accepted is False
    assert result.reason == "missing_dry_run_confirmation"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_guarded_send_emits_safe_starter_eligible_ccs_to_mock_sender(tmp_path):
    from rytm_randomizer.dual_machine_guarded_sender import (
        execute_dual_machine_guarded_send,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    result = execute_dual_machine_guarded_send(
        build_plan(tmp_path),
        sender,
        armed=True,
        dry_run_confirmed=True,
    )

    assert result.accepted is True
    assert result.reason == "accepted_guarded_mock_only"
    assert result.eligible_message_count == 26
    assert result.blocked_event_count == 0
    assert result.emitted_message_count == 26
    assert sender.sent_messages == result.emitted_messages
    first = sender.sent_messages[0]
    assert first.type == "cc"
    assert first.channel == 0
    assert first.control == 17
    assert first.value == 60
    assert first.metadata["device"] == "Analog Rytm MKII"
    assert first.metadata["guard"] == "dual_machine_guarded_send_dry_run"
    a4_messages = [
        message
        for message in sender.sent_messages
        if message.metadata["device"] == "Analog Four MKII"
    ]
    assert len(a4_messages) == 20
    assert a4_messages[0].control == 95
    assert a4_messages[0].value == 104


def test_guarded_send_report_includes_selected_a4_starter_profile(tmp_path):
    from rytm_randomizer.dual_machine_guarded_sender import (
        build_dual_machine_guarded_send_dry_run,
        format_dual_machine_guarded_send_dry_run_report,
    )
    from rytm_randomizer.dual_machine_mock_bridge import build_dual_machine_mock_bridge

    rytm_path = tmp_path / "rytm-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record())
    bridge = build_dual_machine_mock_bridge(
        str(rytm_path),
        slot=1,
        depth="micro",
        target="analog-four",
        analog_four_profile="birmingham-dark",
    )

    result = build_dual_machine_guarded_send_dry_run(bridge)
    report = "\n".join(format_dual_machine_guarded_send_dry_run_report(result))

    assert result.analog_four_starter_profile_key == "birmingham-dark"
    assert result.analog_four_starter_profile_label == "Birmingham Dark"
    assert result.emitted_message_count == 20
    assert "Analog Four starter profile: Birmingham Dark / birmingham-dark" in report
    assert "- Analog Four MKII / ch 1 wire 0 / CC95 -> 106" in report


def test_guarded_send_refuses_combined_a4_snapshot_candidates_without_partial_emit(tmp_path):
    from rytm_randomizer.dual_machine_guarded_sender import (
        execute_dual_machine_guarded_send,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    result = execute_dual_machine_guarded_send(
        build_plan(tmp_path, with_a4_snapshot=True),
        sender,
        armed=True,
        dry_run_confirmed=True,
    )

    assert result.accepted is False
    assert result.reason == "blocked_by_unverified_candidates"
    assert result.eligible_message_count == 6
    assert result.blocked_event_count == 2
    assert result.emitted_message_count == 0
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_guarded_send_target_rytm_ignores_a4_snapshot_candidates_and_emits_rytm_only(tmp_path):
    from rytm_randomizer.dual_machine_guarded_sender import (
        execute_dual_machine_guarded_send,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    result = execute_dual_machine_guarded_send(
        build_plan(tmp_path, target="rytm", with_a4_snapshot=True),
        sender,
        armed=True,
        dry_run_confirmed=True,
    )

    assert result.accepted is True
    assert result.reason == "accepted_guarded_mock_only"
    assert result.eligible_message_count == 6
    assert result.blocked_event_count == 0
    assert result.emitted_message_count == 6
    assert {message.metadata["device"] for message in sender.sent_messages} == {
        "Analog Rytm MKII",
    }


def test_guarded_send_report_formats_refusal_policy(tmp_path):
    from rytm_randomizer.dual_machine_guarded_sender import (
        execute_dual_machine_guarded_send,
        format_dual_machine_guarded_send_dry_run_report,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    result = execute_dual_machine_guarded_send(
        build_plan(tmp_path, with_a4_snapshot=True),
        MockMidiSender(),
        armed=True,
        dry_run_confirmed=True,
    )
    report = "\n".join(format_dual_machine_guarded_send_dry_run_report(result))

    assert "RytmRandomizer passive Dual-Machine Guarded Send Dry-Run Report" in report
    assert "Accepted: False" in report
    assert "Reason: blocked_by_unverified_candidates" in report
    assert "Eligible mapped CC messages: 6" in report
    assert "Blocked candidate events: 2" in report
    assert "Emitted mock messages: 0" in report
    assert "- blocked plans emit no partial messages" in report
    assert "- no MIDI sending" in report


def test_dual_machine_guarded_send_dry_run_cli_refuses_combined_a4_candidates(tmp_path):
    rytm_path = tmp_path / "rytm-kits.syx"
    a4_path = tmp_path / "a4-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record(kit_name="CLI GUARD"))
    a4_path.write_bytes(
        make_a4_kit_record(
            kit_name="CLI A4 GUARD",
            track_values={1: {20: 64, 22: 80}},
        )
    )

    result = run_cli(
        "dual-machine-guarded-send-dry-run-report",
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
    assert "RytmRandomizer passive Dual-Machine Guarded Send Dry-Run Report" in result.stdout
    assert "Accepted: False" in result.stdout
    assert "Reason: blocked_by_unverified_candidates" in result.stdout
    assert "Blocked candidate events: 2" in result.stdout
    assert "Emitted mock messages: 0" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_dual_machine_guarded_send_dry_run_cli_accepts_rytm_target_scope(tmp_path):
    rytm_path = tmp_path / "rytm-kits.syx"
    a4_path = tmp_path / "a4-kits.syx"
    rytm_path.write_bytes(make_rytm_kit_record(kit_name="CLI RYTM ONLY"))
    a4_path.write_bytes(
        make_a4_kit_record(
            kit_name="CLI A4 IGNORED",
            track_values={1: {20: 64, 22: 80}},
        )
    )

    result = run_cli(
        "dual-machine-guarded-send-dry-run-report",
        str(rytm_path),
        "--slot",
        "1",
        "--depth",
        "micro",
        "--analog-four-path",
        str(a4_path),
        "--analog-four-slot",
        "1",
        "--target",
        "rytm",
    )

    assert result.returncode == 0
    assert "Target: rytm" in result.stdout
    assert "Accepted: True" in result.stdout
    assert "Reason: accepted_guarded_mock_only" in result.stdout
    assert "Blocked candidate events: 0" in result.stdout
    assert "Emitted mock messages: 6" in result.stdout
    assert result.stderr == ""
