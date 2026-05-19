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


def test_a4_saved_offset_mapping_parameters_cover_current_starter_profiles():
    from rytm_randomizer.analog_four.saved_offset_mapping_validation_guide import (
        SUPPORTED_MAPPING_PARAMETERS,
    )

    expected = {
        "track-level": ("Track Level", 95),
        "osc1-level": ("OSC1 Level", 69),
        "osc2-level": ("OSC2 Level", 78),
        "osc1-waveform": ("OSC1 Waveform", 70),
        "filter-1-frequency": ("Filter 1 Frequency", 18),
        "filter-2-frequency": ("Filter 2 Frequency", 19),
        "amp-env-decay": ("Amp Env Decay", 105),
        "amp-pan": ("Amp Pan", 10),
        "reverb-send": ("Reverb Send", 93),
        "noise-level": ("Noise Level", 77),
        "noise-fade": ("Noise Fade", 76),
    }

    for key, target in expected.items():
        assert SUPPORTED_MAPPING_PARAMETERS[key] == target


def test_a4_saved_offset_mapping_validation_guide_accepts_filter2_frequency():
    from rytm_randomizer.analog_four.saved_offset_mapping_validation_guide import (
        format_analog_four_saved_offset_mapping_validation_guide,
    )

    report = "\n".join(
        format_analog_four_saved_offset_mapping_validation_guide(
            track=3,
            parameter="filter-2-frequency",
        )
    )

    assert "Track: 3" in report
    assert "Parameter: Filter 2 Frequency" in report
    assert "Known runtime CC: CC19" in report
    assert 'parameter_name="Filter 2 Frequency"' in report
    assert "cc=19" in report


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
