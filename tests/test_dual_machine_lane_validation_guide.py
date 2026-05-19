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


def test_importing_dual_machine_lane_validation_guide_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.dual_machine.lane_validation_guide; "
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


def test_dual_machine_lane_validation_guide_formats_operator_sequence():
    from rytm_randomizer.dual_machine.lane_validation_guide import (
        format_dual_machine_lane_validation_guide,
    )

    report = format_dual_machine_lane_validation_guide()

    assert report[0] == "RytmRandomizer passive Dual-Machine Lane Validation Guide"
    joined = "\n".join(report)
    assert "Expected lane-scoped messages: 11" in joined
    assert "--snapshot-rytm-pad 1 --snapshot-analog-four-track 4" in joined
    assert "dual-machine-mock-bridge-report" in joined
    assert "dual-machine-live-snapshot-readiness-report" in joined
    assert "rytm-randomizer --dry-run --dual-machine-snapshot-send" in joined
    assert "rytm-randomizer --arm --dual-machine-snapshot-send" in joined
    assert "- no MIDI sending" in joined
    assert "- no hardware required" in joined


def test_dual_machine_lane_validation_guide_cli_outputs_without_hardware():
    result = run_cli("dual-machine-lane-validation-guide")

    assert result.returncode == 0
    assert "RytmRandomizer passive Dual-Machine Lane Validation Guide" in result.stdout
    assert "Expected lane-scoped messages: 11" in result.stdout
    assert "--snapshot-rytm-pad 1 --snapshot-analog-four-track 4" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
