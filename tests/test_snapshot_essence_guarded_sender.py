import subprocess
import sys
from dataclasses import replace
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


def make_rytm_kit_record(
    slot_index=0,
    kit_name="ESS GUARD",
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


def write_guard_fixture(path):
    path.write_bytes(
        make_rytm_kit_record(
            machine_values=(0, 27, 13) + tuple(27 for _ in range(9)),
            pad_parameter_values={
                1: {
                    0x1E: 59,
                    0x20: 68,
                    0x44: 25,
                    0x46: 14,
                    0x4A: 65,
                    0x50: 121,
                },
                3: {
                    0x1E: 71,
                    0x20: 88,
                    0x44: 77,
                    0x46: 20,
                    0x4A: 51,
                    0x50: 96,
                },
            },
        )
    )


def build_ready_plan(tmp_path):
    from rytm_randomizer.snapshot_essence_send_plan import (
        build_snapshot_essence_send_plan_from_file,
    )

    sysex_path = tmp_path / "essence-guard.syx"
    write_guard_fixture(sysex_path)
    return build_snapshot_essence_send_plan_from_file(
        sysex_path,
        slot=1,
        depth="micro",
        style="Birmingham dark techno",
        discovery=0.35,
    )


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_snapshot_essence_guarded_sender_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.snapshot_essence_guarded_sender; "
                "assert 'mido' not in sys.modules; "
                "assert 'rtmidi' not in sys.modules; "
                "assert 'librosa' not in sys.modules"
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
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.snapshot_essence_guarded_sender import (
        execute_snapshot_essence_guarded_send,
    )

    sender = MockMidiSender()
    result = execute_snapshot_essence_guarded_send(
        build_ready_plan(tmp_path),
        sender,
        armed=False,
        dry_run_confirmed=True,
    )

    assert result.accepted is False
    assert result.reason == "missing_arming"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_guarded_send_requires_dry_run_confirmation_before_emitting(tmp_path):
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.snapshot_essence_guarded_sender import (
        execute_snapshot_essence_guarded_send,
    )

    sender = MockMidiSender()
    result = execute_snapshot_essence_guarded_send(
        build_ready_plan(tmp_path),
        sender,
        armed=True,
        dry_run_confirmed=False,
    )

    assert result.accepted is False
    assert result.reason == "missing_dry_run_confirmation"
    assert result.emitted_message_count == 0
    assert sender.sent_messages == ()


def test_guarded_send_refuses_blocked_plan_without_partial_emit(tmp_path):
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.snapshot_essence_guarded_sender import (
        execute_snapshot_essence_guarded_send,
    )

    plan = replace(build_ready_plan(tmp_path), blocked_pad_count=1)
    sender = MockMidiSender()
    result = execute_snapshot_essence_guarded_send(
        plan,
        sender,
        armed=True,
        dry_run_confirmed=True,
    )

    assert result.accepted is False
    assert result.reason == "plan_not_ready"
    assert result.plan_ready is False
    assert result.emitted_message_count == 0
    assert sender.sent_messages == ()


def test_guarded_send_emits_ready_plan_to_mock_sender(tmp_path):
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.snapshot_essence_guarded_sender import (
        execute_snapshot_essence_guarded_send,
    )

    plan = build_ready_plan(tmp_path)
    sender = MockMidiSender()
    result = execute_snapshot_essence_guarded_send(
        plan,
        sender,
        armed=True,
        dry_run_confirmed=True,
    )

    assert result.accepted is True
    assert result.reason == "accepted_guarded_mock_only"
    assert result.plan_ready is True
    assert result.eligible_event_count == plan.eligible_event_count
    assert result.blocked_event_count == 0
    assert result.emitted_message_count == plan.eligible_event_count
    assert sender.sent_messages == result.emitted_messages
    first = sender.sent_messages[0]
    assert first.type == "cc"
    assert first.channel == 0
    assert first.control == 17
    assert first.value == 60
    assert first.metadata["guard"] == "snapshot_essence_guarded_send_dry_run"
    assert first.metadata["event_role"] == "snapshot_mutation"
    assert first.metadata["device"] == "Analog Rytm MKII"


def test_guarded_send_report_formats_policy_and_preview(tmp_path):
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.snapshot_essence_guarded_sender import (
        execute_snapshot_essence_guarded_send,
        format_snapshot_essence_guarded_send_dry_run_report,
    )

    result = execute_snapshot_essence_guarded_send(
        build_ready_plan(tmp_path),
        MockMidiSender(),
        armed=True,
        dry_run_confirmed=True,
    )
    report = "\n".join(format_snapshot_essence_guarded_send_dry_run_report(result))

    assert "RytmRandomizer passive Snapshot Essence Guarded Send Dry-Run Report" in report
    assert "Accepted: True" in report
    assert "Reason: accepted_guarded_mock_only" in report
    assert "Plan ready: True" in report
    assert "Emitted mock messages:" in report
    assert "- Analog Rytm MKII / Pad 1 / ch 1 wire 0 / CC17 -> 60" in report
    assert "- emits eligible snapshot essence CC events only when the whole plan is ready" in report
    assert "- blocked plans emit no partial messages" in report
    assert "- no MIDI sending" in report


def test_snapshot_essence_guarded_send_dry_run_cli_reads_saved_snapshot(tmp_path):
    sysex_path = tmp_path / "essence-guard.syx"
    write_guard_fixture(sysex_path)

    result = run_cli(
        "snapshot-essence-guarded-send-dry-run-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
        "--style",
        "Birmingham dark techno",
        "--discovery",
        "0.35",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Snapshot Essence Guarded Send Dry-Run Report" in result.stdout
    assert "Accepted: True" in result.stdout
    assert "Reason: accepted_guarded_mock_only" in result.stdout
    assert "Plan ready: True" in result.stdout
    assert "Emitted mock messages:" in result.stdout
    assert "- mock-only guarded dry-run" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
