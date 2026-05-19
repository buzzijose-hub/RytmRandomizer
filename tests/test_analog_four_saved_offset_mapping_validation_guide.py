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


def test_importing_a4_saved_offset_mapping_validation_guide_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four.saved_offset_mapping_validation_guide; "
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


def test_a4_saved_offset_mapping_validation_guide_defaults_to_track1_filter():
    from rytm_randomizer.analog_four.saved_offset_mapping_validation_guide import (
        format_analog_four_saved_offset_mapping_validation_guide,
    )

    report = "\n".join(format_analog_four_saved_offset_mapping_validation_guide())

    assert "RytmRandomizer passive Analog Four Saved-Offset Mapping Validation Guide" in report
    assert "Track: 1" in report
    assert "Parameter: Filter 1 Frequency" in report
    assert "Known runtime CC: CC18" in report
    assert "analog-four-controlled-diff-report" in report
    assert "--track 1" in report
    assert "AnalogFourVerifiedSavedOffsetMapping(" in report
    assert 'parameter_name="Filter 1 Frequency"' in report
    assert "cc=18" in report
    assert "- no MIDI sending" in report
    assert "- no live SysEx receive" in report


def test_a4_saved_offset_mapping_validation_guide_accepts_track_and_parameter():
    from rytm_randomizer.analog_four.saved_offset_mapping_validation_guide import (
        format_analog_four_saved_offset_mapping_validation_guide,
    )

    report = "\n".join(
        format_analog_four_saved_offset_mapping_validation_guide(
            track=2,
            parameter="amp-pan",
        )
    )

    assert "Track: 2" in report
    assert "Parameter: Amp Pan" in report
    assert "Known runtime CC: CC10" in report
    assert "--track 2" in report
    assert "cc=10" in report


def test_a4_saved_offset_mapping_validation_guide_rejects_unknown_parameter():
    from rytm_randomizer.analog_four.saved_offset_mapping_validation_guide import (
        format_analog_four_saved_offset_mapping_validation_guide,
    )

    with pytest.raises(ValueError, match="parameter must be one of"):
        format_analog_four_saved_offset_mapping_validation_guide(parameter="pitch-cloud")


def test_a4_saved_offset_mapping_validation_guide_cli_prints_report():
    result = run_cli(
        "analog-four-saved-offset-mapping-guide",
        "--track",
        "2",
        "--parameter",
        "amp-pan",
    )

    assert result.returncode == 0
    assert (
        "RytmRandomizer passive Analog Four Saved-Offset Mapping Validation Guide" in result.stdout
    )
    assert "Track: 2" in result.stdout
    assert "Parameter: Amp Pan" in result.stdout
    assert "Known runtime CC: CC10" in result.stdout
    assert "analog-four-controlled-diff-report" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_a4_saved_offset_mapping_validation_guide_cli_rejects_invalid_track():
    result = run_cli("analog-four-saved-offset-mapping-guide", "--track", "7")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "track must be 1-4" in result.stderr
    assert "No MIDI was sent" in result.stderr
