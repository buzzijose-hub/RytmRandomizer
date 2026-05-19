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


def test_importing_rytm_runtime_validation_guide_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.essence.rytm_runtime_validation_guide; "
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


def test_rytm_runtime_validation_guide_lists_one_pad_sequence():
    from rytm_randomizer.essence.rytm_runtime_validation_guide import (
        format_rytm_runtime_validation_guide,
    )

    report = format_rytm_runtime_validation_guide()

    assert report[0] == "RytmRandomizer passive Twelve Pad Rytm Runtime Validation Guide"
    assert "One-pad validation order:" in report
    assert (
        "rytm-randomizer --dry-run --twelve-pad-rytm-runtime "
        '--runtime-style "Birmingham dark techno" --runtime-discovery 0.35 '
        "--runtime-pad 1"
    ) in report
    assert (
        "rytm-randomizer --arm --twelve-pad-rytm-runtime "
        '--runtime-style "Birmingham dark techno" --runtime-discovery 0.35 '
        "--runtime-pad 12"
    ) in report
    assert "Expected one-pad messages: 11" in report
    assert "Expected full-runtime messages: 132" in report
    assert "Matrix preflight:" in report
    assert "python -m rytm_randomizer.cli rytm-12-pad-engine-matrix-report" in report
    assert "Pad identity sanity checks:" in report
    assert "- Pad 10 is OH / Open hihat; XT Classic belongs only to Pads 6-8." in report
    assert "- Pad 1 through Pad 12, then full 12-pad runtime" in report
    assert "- no MIDI sending" in report
    assert "- no port opening" in report


def test_rytm_runtime_validation_guide_prints_actual_pad_lanes_and_engines():
    from rytm_randomizer.essence.rytm_runtime_validation_guide import (
        format_rytm_runtime_validation_guide,
    )

    report = format_rytm_runtime_validation_guide()
    joined = "\n".join(report)

    assert "- Pad 6 / LT / Low tom / XT Classic dry-run:" in joined
    assert "- Pad 7 / MT / Mid tom / XT Classic dry-run:" in joined
    assert "- Pad 8 / HT / Hi tom / XT Classic dry-run:" in joined
    assert "- Pad 10 / OH / Open hihat / OH Metallic dry-run:" in joined
    assert "- Pad 10 / OH / Open hihat / XT Classic" not in joined


def test_rytm_runtime_validation_guide_cli_prints_report():
    result = run_cli("twelve-pad-rytm-runtime-validation-guide")

    assert result.returncode == 0
    assert "RytmRandomizer passive Twelve Pad Rytm Runtime Validation Guide" in result.stdout
    assert "rytm-randomizer --arm --twelve-pad-rytm-runtime" in result.stdout
    assert "python -m rytm_randomizer.cli rytm-12-pad-engine-matrix-report" in result.stdout
    assert "Pad 10 / OH / Open hihat / OH Metallic" in result.stdout
    assert "Pad 1 through Pad 12, then full 12-pad runtime" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""
