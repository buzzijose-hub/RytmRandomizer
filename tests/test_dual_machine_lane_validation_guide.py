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


def test_dual_machine_lane_validation_guide_formats_rytm_only_lane():
    from rytm_randomizer.dual_machine.lane_validation_guide import (
        format_dual_machine_lane_validation_guide,
    )

    report = format_dual_machine_lane_validation_guide(target="rytm", rytm_pad=10)
    joined = "\n".join(report)

    assert "Target scope: rytm" in joined
    assert "Recommended Rytm pad: 10" in joined
    assert "Analog Four track: not targeted" in joined
    assert "Expected lane-scoped messages: 6" in joined
    assert "--target rytm --rytm-pad 10" in joined
    assert "--snapshot-target rytm --snapshot-rytm-pad 10" in joined
    assert "--snapshot-analog-four-track" not in joined
    assert "- A4 Track" not in joined


def test_dual_machine_lane_validation_guide_cli_accepts_analog_four_only_target():
    result = run_cli(
        "dual-machine-lane-validation-guide",
        "--target",
        "analog-four",
        "--analog-four-track",
        "2",
    )

    assert result.returncode == 0
    assert "Target scope: analog-four" in result.stdout
    assert "Rytm pad: not targeted" in result.stdout
    assert "Recommended Analog Four track: 2" in result.stdout
    assert "Expected lane-scoped messages: 5" in result.stdout
    assert "--target analog-four --analog-four-track 2" in result.stdout
    assert "--snapshot-target analog-four --snapshot-analog-four-track 2" in result.stdout
    assert "--snapshot-rytm-pad" not in result.stdout
    assert result.stderr == ""


def test_dual_machine_lane_validation_guide_cli_rejects_invalid_rytm_pad_without_hardware():
    result = run_cli("dual-machine-lane-validation-guide", "--rytm-pad", "13")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "Rytm pad must be between 1 and 12" in result.stderr
    assert "No MIDI was sent." in result.stderr


def test_dual_machine_all_lane_validation_guide_lists_every_single_machine_lane():
    from rytm_randomizer.dual_machine.lane_validation_guide import (
        format_dual_machine_all_lane_validation_guide,
    )

    report = format_dual_machine_all_lane_validation_guide()
    joined = "\n".join(report)

    assert report[0] == "RytmRandomizer passive Dual-Machine All-Lane Validation Guide"
    assert "Rytm-only lanes:" in joined
    assert "- Pad 1 / expected 6 messages:" in joined
    assert "- Pad 12 / expected 6 messages:" in joined
    assert "dual-machine-lane-validation-guide --target rytm --rytm-pad 12" in joined
    assert "Analog-Four-only lanes:" in joined
    assert "- Track 1 / expected 5 messages:" in joined
    assert "- Track 4 / expected 5 messages:" in joined
    assert (
        "dual-machine-lane-validation-guide --target analog-four --analog-four-track 4"
        in joined
    )
    assert "Both-machine pilot pairs:" in joined
    assert "- Pad 1 + A4 Track 1 / expected 11 messages:" in joined
    assert "- Pad 10 + A4 Track 3 / expected 11 messages:" in joined
    assert "- no MIDI sending" in joined


def test_dual_machine_lane_validation_guide_cli_accepts_all_lanes_flag():
    result = run_cli("dual-machine-lane-validation-guide", "--all-lanes")

    assert result.returncode == 0
    assert "RytmRandomizer passive Dual-Machine All-Lane Validation Guide" in result.stdout
    assert "Rytm-only lanes:" in result.stdout
    assert "Analog-Four-only lanes:" in result.stdout
    assert "Both-machine pilot pairs:" in result.stdout
    assert "--target rytm --rytm-pad 12" in result.stdout
    assert "--target analog-four --analog-four-track 4" in result.stdout
    assert result.stderr == ""


def test_dual_machine_lane_validation_guide_cli_outputs_without_hardware():
    result = run_cli("dual-machine-lane-validation-guide")

    assert result.returncode == 0
    assert "RytmRandomizer passive Dual-Machine Lane Validation Guide" in result.stdout
    assert "Expected lane-scoped messages: 11" in result.stdout
    assert "--snapshot-rytm-pad 1 --snapshot-analog-four-track 4" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
