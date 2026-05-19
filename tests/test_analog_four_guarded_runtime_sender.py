import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_a4_guarded_runtime_sender_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four.guarded_runtime_sender; "
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


def test_a4_guarded_runtime_dry_run_emits_balanced_mock_messages():
    from rytm_randomizer.analog_four.guarded_runtime_sender import (
        build_analog_four_runtime_guarded_send_dry_run,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan

    plan = build_analog_four_runtime_plan(profile="balanced")
    result = build_analog_four_runtime_guarded_send_dry_run(plan)

    assert result.device == "Elektron Analog Four MKII"
    assert result.accepted is True
    assert result.reason == "accepted_a4_guarded_mock_only"
    assert result.plan_ready is True
    assert result.eligible_message_count == 20
    assert result.blocked_event_count == 0
    assert result.emitted_message_count == 20
    assert result.track_count == 4
    assert result.starter_profile_key == "balanced"
    assert result.starter_profile_label == "Balanced"
    assert result.mock_only is True
    assert result.sends_real_midi is False

    first = result.emitted_messages[0]
    assert first.type == "cc"
    assert first.channel == 0
    assert first.control == 95
    assert first.value == 104
    assert first.metadata["guard"] == "analog_four_runtime_guarded_send_dry_run"
    assert first.metadata["device"] == "Elektron Analog Four MKII"
    assert first.metadata["track"] == 1
    assert first.metadata["midi_channel"] == 1
    assert first.metadata["wire_channel"] == 0
    assert first.metadata["role"] == "bass / low tonal anchor"
    assert first.metadata["parameter"] == "Track Level"
    assert first.metadata["starter_profile_key"] == "balanced"
    assert first.metadata["mock_only"] is True
    assert first.metadata["sends_real_midi"] is False


def test_a4_guarded_runtime_preserves_birmingham_dark_values():
    from rytm_randomizer.analog_four.guarded_runtime_sender import (
        build_analog_four_runtime_guarded_send_dry_run,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan

    plan = build_analog_four_runtime_plan(profile="birmingham-dark")
    result = build_analog_four_runtime_guarded_send_dry_run(plan)

    assert result.accepted is True
    first = result.emitted_messages[0]
    assert first.channel == 0
    assert first.control == 95
    assert first.value == 106
    assert first.metadata["role"] == "dark bass pressure"
    assert first.metadata["starter_profile_key"] == "birmingham-dark"


def test_a4_guarded_runtime_accepts_single_track_filtered_plan():
    from rytm_randomizer.analog_four.guarded_runtime_sender import (
        build_analog_four_runtime_guarded_send_dry_run,
    )
    from rytm_randomizer.analog_four.runtime_plan import (
        build_analog_four_runtime_plan,
        filter_analog_four_runtime_plan_to_track,
    )

    plan = filter_analog_four_runtime_plan_to_track(
        build_analog_four_runtime_plan(profile="peak-time"),
        track=4,
    )
    result = build_analog_four_runtime_guarded_send_dry_run(plan)

    assert result.accepted is True
    assert result.eligible_message_count == 5
    assert result.emitted_message_count == 5
    assert result.track_count == 1
    assert {message.metadata["track"] for message in result.emitted_messages} == {4}
    assert {message.channel for message in result.emitted_messages} == {3}


def test_a4_guarded_runtime_blocks_without_arming_or_confirmation():
    from rytm_randomizer.analog_four.guarded_runtime_sender import (
        execute_analog_four_runtime_guarded_send,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan
    from rytm_randomizer.mock_midi import MockMidiSender

    plan = build_analog_four_runtime_plan(profile="balanced")
    sender = MockMidiSender()

    missing_armed = execute_analog_four_runtime_guarded_send(
        plan,
        sender,
        armed=False,
        dry_run_confirmed=True,
    )
    assert missing_armed.accepted is False
    assert missing_armed.reason == "missing_arming"
    assert missing_armed.emitted_message_count == 0
    assert len(sender.sent_messages) == 0

    missing_confirmation = execute_analog_four_runtime_guarded_send(
        plan,
        sender,
        armed=True,
        dry_run_confirmed=False,
    )
    assert missing_confirmation.accepted is False
    assert missing_confirmation.reason == "missing_dry_run_confirmation"
    assert missing_confirmation.emitted_message_count == 0
    assert len(sender.sent_messages) == 0


def test_format_a4_guarded_runtime_report_shows_policy_and_stream():
    from rytm_randomizer.analog_four.guarded_runtime_sender import (
        build_analog_four_runtime_guarded_send_dry_run,
        format_analog_four_runtime_guarded_send_dry_run_report,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan

    result = build_analog_four_runtime_guarded_send_dry_run(
        build_analog_four_runtime_plan(profile="detroit-classic")
    )
    report = format_analog_four_runtime_guarded_send_dry_run_report(result)

    assert report[0] == "RytmRandomizer passive Analog Four Guarded Runtime Dry-Run Report"
    assert "Device: Elektron Analog Four MKII" in report
    assert "Starter profile: Detroit Classic / detroit-classic" in report
    assert "Accepted: True" in report
    assert "Reason: accepted_a4_guarded_mock_only" in report
    assert "Plan ready: True" in report
    assert "Eligible mapped CC messages: 20" in report
    assert "Emitted mock messages: 20" in report
    assert "- Track 1 / analog bass motif: 5 message(s)" in report
    assert "- Track 1 ch 1 wire 0 / Track Level CC95 -> 100" in report
    assert "- A4-only guarded dry-run" in report
    assert "- no Rytm MIDI sending" in report
    assert "- no MIDI sending" in report


def test_a4_guarded_runtime_cli_accepts_profile():
    result = run_cli("analog-four-runtime-guarded-send-dry-run", "--profile", "birmingham-dark")

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four Guarded Runtime Dry-Run Report" in result.stdout
    assert "Starter profile: Birmingham Dark / birmingham-dark" in result.stdout
    assert "Accepted: True" in result.stdout
    assert "Track 1 ch 1 wire 0 / Track Level CC95 -> 106" in result.stdout
    assert "- no Rytm MIDI sending" in result.stdout
    assert result.stderr == ""


def test_a4_guarded_runtime_cli_rejects_unknown_profile_safely():
    result = run_cli("analog-four-runtime-guarded-send-dry-run", "--profile", "acid-swamp")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "RytmRandomizer passive Analog Four Guarded Runtime Dry-Run Report" in result.stderr
    assert "Unknown Analog Four starter profile: acid-swamp" in result.stderr
    assert "No MIDI was sent" in result.stderr
