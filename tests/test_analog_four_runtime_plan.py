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


def test_importing_analog_four_runtime_plan_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four.runtime_plan; "
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


def test_analog_four_runtime_plan_builds_profile_tracks_from_manual_reference():
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan

    plan = build_analog_four_runtime_plan(profile="balanced")

    assert plan.device == "Elektron Analog Four MKII"
    assert plan.manual_os == "OS1.51C"
    assert plan.manual_midi_pages == "100-108"
    assert plan.starter_profile_key == "balanced"
    assert plan.starter_profile_label == "Balanced"
    assert plan.track_count == 4
    assert plan.event_count == 20
    assert plan.runtime_status == "passive_mock_ready"

    track1 = plan.tracks[0]
    assert track1.track == 1
    assert track1.midi_channel == 1
    assert track1.wire_channel == 0
    assert track1.role_label == "bass / low tonal anchor"
    assert track1.events[0].parameter_name == "Track Level"
    assert track1.events[0].cc == 95
    assert track1.events[0].value == 104
    assert track1.events[3].parameter_name == "Filter 1 Frequency"
    assert track1.events[3].cc == 18
    assert track1.events[4].parameter_name == "Amp Pan"
    assert track1.events[4].cc == 10


def test_analog_four_runtime_mock_capture_uses_cc_metadata_without_real_midi():
    from rytm_randomizer.analog_four.runtime_plan import (
        build_analog_four_runtime_plan,
        capture_analog_four_runtime_mock_messages,
    )

    plan = build_analog_four_runtime_plan(profile="birmingham-dark")
    sender = capture_analog_four_runtime_mock_messages(plan)

    assert len(sender.sent_messages) == 20
    first = sender.sent_messages[0]
    assert first.type == "cc"
    assert first.channel == 0
    assert first.control == 95
    assert first.value == 106
    assert first.metadata["source_kind"] == "analog_four_runtime_plan"
    assert first.metadata["device"] == "Elektron Analog Four MKII"
    assert first.metadata["track"] == 1
    assert first.metadata["midi_channel"] == 1
    assert first.metadata["role"] == "dark bass pressure"
    assert first.metadata["parameter"] == "Track Level"
    assert first.metadata["starter_profile_key"] == "birmingham-dark"
    assert first.metadata["runtime_status"] == "passive_mock_ready"
    assert first.metadata["mock_only"] is True
    assert first.metadata["sends_real_midi"] is False


def test_format_analog_four_runtime_report_shows_tracks_stream_and_safety():
    from rytm_randomizer.analog_four.runtime_plan import (
        build_analog_four_runtime_plan,
        capture_analog_four_runtime_mock_messages,
        format_analog_four_runtime_report,
    )

    plan = build_analog_four_runtime_plan(profile="detroit-classic")
    sender = capture_analog_four_runtime_mock_messages(plan)
    report = format_analog_four_runtime_report(plan, sender)

    assert report[0] == "RytmRandomizer passive Analog Four Runtime Plan Report"
    assert "Device: Elektron Analog Four MKII" in report
    assert "Manual OS: OS1.51C" in report
    assert "Starter profile: Detroit Classic / detroit-classic" in report
    assert "Runtime status: passive_mock_ready" in report
    assert "Tracks planned: 4" in report
    assert "Mock sender captured: 20 message(s)" in report
    assert "- Track 1 / analog bass motif: 5 event(s)" in report
    assert "- Track 1 ch 1 wire 0 / Track Level CC95 -> 100" in report
    assert "- passive/mock A4 runtime planning only" in report
    assert "- no MIDI sending" in report
    assert "- no hardware mutation" in report


def test_analog_four_runtime_report_cli_accepts_profile():
    result = run_cli("analog-four-runtime-report", "--profile", "birmingham-dark")

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four Runtime Plan Report" in result.stdout
    assert "Starter profile: Birmingham Dark / birmingham-dark" in result.stdout
    assert "Track 4 / noise transition: 5 event(s)" in result.stdout
    assert "Track 1 ch 1 wire 0 / Track Level CC95 -> 106" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_analog_four_runtime_report_cli_rejects_unknown_profile_safely():
    result = run_cli("analog-four-runtime-report", "--profile", "acid-swamp")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "RytmRandomizer passive Analog Four Runtime Plan Report" in result.stderr
    assert "Unknown Analog Four starter profile: acid-swamp" in result.stderr
    assert "No MIDI was sent" in result.stderr
