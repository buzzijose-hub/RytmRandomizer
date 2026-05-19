import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_a4_hardware_runtime_sender_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four.hardware_runtime_sender; "
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


def test_a4_hardware_runtime_refuses_without_arming_or_confirmation(
    fake_mido_session,
    recording_out,
    no_sleep,
):
    from rytm_randomizer.analog_four.hardware_runtime_sender import (
        execute_analog_four_runtime_hardware_send,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan

    plan = build_analog_four_runtime_plan(profile="balanced")
    out = recording_out

    missing_arm = execute_analog_four_runtime_hardware_send(
        plan,
        out,
        port_name="Fake A4",
        armed=False,
        operator_confirmed=True,
        sleep=no_sleep,
    )
    assert missing_arm.accepted is False
    assert missing_arm.reason == "missing_arming"
    assert missing_arm.emitted_message_count == 0
    assert out.sent == []

    missing_confirmation = execute_analog_four_runtime_hardware_send(
        plan,
        out,
        port_name="Fake A4",
        armed=True,
        operator_confirmed=False,
        sleep=no_sleep,
    )
    assert missing_confirmation.accepted is False
    assert missing_confirmation.reason == "missing_operator_confirmation"
    assert missing_confirmation.emitted_message_count == 0
    assert out.sent == []


def test_a4_hardware_runtime_sends_balanced_plan_to_fake_port(
    fake_mido_session,
    recording_out,
    no_sleep,
):
    from rytm_randomizer.analog_four.hardware_runtime_sender import (
        execute_analog_four_runtime_hardware_send,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan

    plan = build_analog_four_runtime_plan(profile="balanced")
    out = recording_out

    result = execute_analog_four_runtime_hardware_send(
        plan,
        out,
        port_name="Fake A4",
        armed=True,
        operator_confirmed=True,
        sleep=no_sleep,
    )

    assert result.accepted is True
    assert result.reason == "accepted_hardware_send"
    assert result.device == "Elektron Analog Four MKII"
    assert result.port_name == "Fake A4"
    assert result.starter_profile_key == "balanced"
    assert result.emitted_message_count == 20
    assert result.sends_real_midi is True
    assert result.mock_only is False
    assert len(out.sent) == 20
    assert out.sent[0].type == "control_change"
    assert out.sent[0].channel == 0
    assert out.sent[0].control == 95
    assert out.sent[0].value == 104
    assert out.sent[-1].channel == 3


def test_a4_hardware_runtime_preserves_birmingham_dark_values(
    fake_mido_session,
    recording_out,
    no_sleep,
):
    from rytm_randomizer.analog_four.hardware_runtime_sender import (
        execute_analog_four_runtime_hardware_send,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan

    plan = build_analog_four_runtime_plan(profile="birmingham-dark")
    out = recording_out

    result = execute_analog_four_runtime_hardware_send(
        plan,
        out,
        port_name="Fake A4",
        armed=True,
        operator_confirmed=True,
        sleep=no_sleep,
    )

    assert result.emitted_messages[0].track == 1
    assert result.emitted_messages[0].control == 95
    assert result.emitted_messages[0].value == 106
    assert result.emitted_messages[0].role == "dark bass pressure"
    assert out.sent[0].control == 95
    assert out.sent[0].value == 106


def test_format_a4_hardware_runtime_report_shows_active_policy(
    fake_mido_session,
    recording_out,
    no_sleep,
):
    from rytm_randomizer.analog_four.hardware_runtime_sender import (
        execute_analog_four_runtime_hardware_send,
        format_analog_four_runtime_hardware_send_report,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan

    result = execute_analog_four_runtime_hardware_send(
        build_analog_four_runtime_plan(profile="detroit-classic"),
        recording_out,
        port_name="Fake A4",
        armed=True,
        operator_confirmed=True,
        sleep=no_sleep,
    )
    report = format_analog_four_runtime_hardware_send_report(result)

    assert report[0] == "RytmRandomizer armed Analog Four Runtime Hardware Send Report"
    assert "Device: Elektron Analog Four MKII" in report
    assert "Starter profile: Detroit Classic / detroit-classic" in report
    assert "Accepted: True" in report
    assert "Reason: accepted_hardware_send" in report
    assert "Port: Fake A4" in report
    assert "Emitted real MIDI messages: 20" in report
    assert "- Track 1 ch 1 wire 0 / Track Level CC95 -> 100" in report
    assert "- A4-only runtime hardware send" in report
    assert "- requires exact SEND confirmation" in report
    assert "- no Rytm MIDI sending" in report
    assert "- no SysEx writes" in report
