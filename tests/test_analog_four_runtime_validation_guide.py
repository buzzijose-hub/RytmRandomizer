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


def test_importing_a4_runtime_validation_guide_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four.runtime_validation_guide; "
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


def test_a4_runtime_validation_guide_report_lists_single_track_sequence():
    from rytm_randomizer.analog_four.runtime_validation_guide import (
        format_analog_four_runtime_validation_guide,
    )

    report = format_analog_four_runtime_validation_guide()

    assert report[0] == "RytmRandomizer passive Analog Four Runtime Validation Guide"
    assert "Single-track validation order:" in report
    assert (
        "python -m rytm_randomizer.cli analog-four-runtime-report " "--profile peak-time --track 1"
    ) in report
    assert "Profile preflight:" in report
    assert "python -m rytm_randomizer.cli analog-four-runtime-report --profile peak-time" in report
    assert "Track identity sanity checks:" in report
    assert "- Runtime labels below come from the passive A4 runtime plan." in report
    assert (
        "rytm-randomizer --dry-run --analog-four-runtime "
        "--analog-four-profile peak-time --analog-four-runtime-track 1"
    ) in report
    assert (
        "rytm-randomizer --arm --analog-four-runtime "
        "--analog-four-profile peak-time --analog-four-runtime-track 4"
    ) in report
    assert "Expected single-track messages: 5" in report
    assert "Expected full-profile messages: 20" in report
    assert "- no MIDI sending" in report
    assert "- no port opening" in report


def test_a4_runtime_validation_guide_prints_actual_track_roles():
    from rytm_randomizer.analog_four.runtime_validation_guide import (
        format_analog_four_runtime_validation_guide,
    )

    report = format_analog_four_runtime_validation_guide()
    joined = "\n".join(report)

    assert "- Track 1 / bright bass anchor dry-run:" in joined
    assert "- Track 2 / peak stab pressure dry-run:" in joined
    assert "- Track 3 / large motion layer dry-run:" in joined
    assert "- Track 4 / bright riser texture dry-run:" in joined


def test_a4_runtime_validation_guide_cli_prints_report():
    result = run_cli("analog-four-runtime-validation-guide")

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four Runtime Validation Guide" in result.stdout
    assert "rytm-randomizer --arm --analog-four-runtime" in result.stdout
    assert (
        "python -m rytm_randomizer.cli analog-four-runtime-report --profile peak-time"
        in result.stdout
    )
    assert "Track 3 / large motion layer" in result.stdout
    assert "Track 1, Track 2, Track 3, Track 4, then full profile" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""
