import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_twelve_pad_smoke_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.twelve_pad_smoke; "
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


def test_build_twelve_pad_smoke_steps_targets_pads_5_to_12():
    from rytm_randomizer.twelve_pad_smoke import build_twelve_pad_smoke_steps

    steps = build_twelve_pad_smoke_steps()

    assert len(steps) == 48
    assert tuple(sorted({step.pad for step in steps})) == tuple(range(5, 13))
    assert tuple(sorted({step.midi_channel for step in steps})) == tuple(range(5, 13))
    assert tuple(sorted({step.wire_channel for step in steps})) == tuple(range(4, 12))
    assert steps[0].pad == 5
    assert steps[0].wire_channel == 4
    assert steps[0].control == 10
    assert steps[0].value == 24
    assert steps[-1].pad == 12
    assert steps[-1].wire_channel == 11
    assert steps[-1].control == 74
    assert steps[-1].value == 64


def test_run_twelve_pad_smoke_test_captures_mock_stream_without_sleeping():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.twelve_pad_smoke import run_twelve_pad_smoke_test

    sender = MockMidiSender()
    sleeps = []
    result = run_twelve_pad_smoke_test(sender, sleep=sleeps.append)

    assert result.pad_count == 8
    assert result.message_count == 48
    assert len(sender.sent_messages) == 48
    assert len(sleeps) == 48
    assert sender.sent_messages[0].channel == 4
    assert sender.sent_messages[0].control == 10
    assert sender.sent_messages[0].value == 24
    assert sender.sent_messages[0].metadata["pad"] == 5
    assert sender.sent_messages[-1].channel == 11
    assert sender.sent_messages[-1].control == 74
    assert sender.sent_messages[-1].value == 64
    assert sender.sent_messages[-1].metadata["pad"] == 12


def test_format_twelve_pad_smoke_report_includes_safety_and_summary():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.twelve_pad_smoke import (
        format_twelve_pad_smoke_report,
        run_twelve_pad_smoke_test,
    )

    result = run_twelve_pad_smoke_test(MockMidiSender(), sleep=lambda _seconds: None)
    report = format_twelve_pad_smoke_report(result, mode="dry-run")

    assert report[0] == "RytmRandomizer Twelve-Pad Hardware Smoke Report"
    assert "Mode: dry-run" in report
    assert "Pads tested: 5-12" in report
    assert "Messages sent: 48" in report
    assert "Controls: Pan CC10 and Filter Frequency CC74" in report
    assert "- Pad 5 / MIDI channel 5 / wire channel 4: 6 message(s)" in report
    assert "- Pad 12 / MIDI channel 12 / wire channel 11: 6 message(s)" in report
    assert "- no Analog Four MIDI sending" in report
    assert "- no machine/engine cycling" in report
