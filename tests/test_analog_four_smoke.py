import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_analog_four_smoke_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four_smoke; "
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


def test_build_analog_four_smoke_steps_targets_tracks_1_to_4():
    from rytm_randomizer.analog_four_smoke import build_analog_four_smoke_steps

    steps = build_analog_four_smoke_steps()

    assert len(steps) == 12
    assert tuple(sorted({step.track for step in steps})) == (1, 2, 3, 4)
    assert tuple(sorted({step.midi_channel for step in steps})) == (1, 2, 3, 4)
    assert tuple(sorted({step.wire_channel for step in steps})) == (0, 1, 2, 3)
    assert steps[0].track == 1
    assert steps[0].wire_channel == 0
    assert steps[0].control == 10
    assert steps[0].value == 24
    assert steps[-1].track == 4
    assert steps[-1].wire_channel == 3
    assert steps[-1].control == 10
    assert steps[-1].value == 64


def test_build_analog_four_track_smoke_steps_targets_one_track():
    from rytm_randomizer.analog_four_smoke import build_analog_four_track_smoke_steps

    steps = build_analog_four_track_smoke_steps(3)

    assert len(steps) == 3
    assert tuple(step.track for step in steps) == (3, 3, 3)
    assert tuple(step.midi_channel for step in steps) == (3, 3, 3)
    assert tuple(step.wire_channel for step in steps) == (2, 2, 2)
    assert tuple(step.control for step in steps) == (10, 10, 10)
    assert tuple(step.value for step in steps) == (24, 104, 64)
    assert tuple(step.label for step in steps) == ("pan left", "pan right", "pan center")


def test_build_analog_four_track_smoke_steps_rejects_invalid_track():
    from rytm_randomizer.analog_four_smoke import build_analog_four_track_smoke_steps

    for track in (0, 5):
        try:
            build_analog_four_track_smoke_steps(track)
        except ValueError as exc:
            assert "Track must be between 1 and 4" in str(exc)
        else:
            raise AssertionError(f"track {track} should have failed")


def test_build_analog_four_track_filter_smoke_steps_targets_one_track_filter_1():
    from rytm_randomizer.analog_four_smoke import (
        build_analog_four_track_filter_smoke_steps,
    )

    steps = build_analog_four_track_filter_smoke_steps(2)

    assert len(steps) == 3
    assert tuple(step.track for step in steps) == (2, 2, 2)
    assert tuple(step.midi_channel for step in steps) == (2, 2, 2)
    assert tuple(step.wire_channel for step in steps) == (1, 1, 1)
    assert tuple(step.control for step in steps) == (18, 18, 18)
    assert tuple(step.value for step in steps) == (48, 112, 127)
    assert tuple(step.label for step in steps) == (
        "filter 1 frequency low",
        "filter 1 frequency open",
        "filter 1 frequency open return",
    )


def test_build_analog_four_track_filter_smoke_steps_rejects_invalid_track():
    from rytm_randomizer.analog_four_smoke import (
        build_analog_four_track_filter_smoke_steps,
    )

    for track in (0, 5):
        try:
            build_analog_four_track_filter_smoke_steps(track)
        except ValueError as exc:
            assert "Track must be between 1 and 4" in str(exc)
        else:
            raise AssertionError(f"track {track} should have failed")


def test_run_analog_four_smoke_test_captures_mock_stream_without_sleeping():
    from rytm_randomizer.analog_four_smoke import run_analog_four_smoke_test
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    sleeps = []
    result = run_analog_four_smoke_test(sender, sleep=sleeps.append)

    assert result.track_count == 4
    assert result.message_count == 12
    assert len(sender.sent_messages) == 12
    assert len(sleeps) == 12
    assert sender.sent_messages[0].channel == 0
    assert sender.sent_messages[0].control == 10
    assert sender.sent_messages[0].value == 24
    assert sender.sent_messages[0].metadata["track"] == 1
    assert sender.sent_messages[-1].channel == 3
    assert sender.sent_messages[-1].control == 10
    assert sender.sent_messages[-1].value == 64
    assert sender.sent_messages[-1].metadata["track"] == 4


def test_format_analog_four_smoke_report_includes_safety_and_summary():
    from rytm_randomizer.analog_four_smoke import (
        format_analog_four_smoke_report,
        run_analog_four_smoke_test,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    result = run_analog_four_smoke_test(MockMidiSender(), sleep=lambda _seconds: None)
    report = format_analog_four_smoke_report(result, mode="dry-run")

    assert report[0] == "RytmRandomizer Analog Four Hardware Smoke Report"
    assert "Mode: dry-run" in report
    assert "Tracks tested: 1-4" in report
    assert "Messages sent: 12" in report
    assert "Controls: Amp Pan CC10 only" in report
    assert "- Track 1 / MIDI channel 1 / wire channel 0: 3 message(s)" in report
    assert "- Track 4 / MIDI channel 4 / wire channel 3: 3 message(s)" in report
    assert "- Pan CC10 returns to 64" in report
    assert "- no Rytm MIDI sending" in report


def test_format_analog_four_track_filter_smoke_report_includes_single_track_summary():
    from rytm_randomizer.analog_four_smoke import (
        format_analog_four_track_filter_smoke_report,
        run_analog_four_track_filter_smoke_test,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    result = run_analog_four_track_filter_smoke_test(
        MockMidiSender(),
        track=1,
        sleep=lambda _seconds: None,
    )
    report = format_analog_four_track_filter_smoke_report(result, mode="dry-run")

    assert report[0] == "RytmRandomizer Analog Four Track Filter Smoke Report"
    assert "Mode: dry-run" in report
    assert "Track tested: 1" in report
    assert "Messages sent: 3" in report
    assert "Controls: Filter 1 Frequency CC18 only" in report
    assert "- Track 1 / MIDI channel 1 / wire channel 0: 3 message(s)" in report
    assert "- Filter 1 Frequency CC18 returns to 127/open" in report
    assert "- no Rytm MIDI sending" in report
    assert "- no resonance/level/pitch mutation" in report
    assert "- no SysEx receive" in report


def test_format_analog_four_track_smoke_report_includes_single_track_summary():
    from rytm_randomizer.analog_four_smoke import (
        format_analog_four_track_smoke_report,
        run_analog_four_track_smoke_test,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    result = run_analog_four_track_smoke_test(
        MockMidiSender(),
        track=4,
        sleep=lambda _seconds: None,
    )
    report = format_analog_four_track_smoke_report(result, mode="dry-run")

    assert report[0] == "RytmRandomizer Analog Four Track Smoke Report"
    assert "Mode: dry-run" in report
    assert "Track tested: 4" in report
    assert "Messages sent: 3" in report
    assert "Controls: Amp Pan CC10 only" in report
    assert "- Track 4 / MIDI channel 4 / wire channel 3: 3 message(s)" in report
    assert "- Pan CC10 returns to 64" in report
    assert "- no Rytm MIDI sending" in report
