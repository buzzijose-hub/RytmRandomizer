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


def test_importing_dual_machine_mapping_validation_queue_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.dual_machine.mapping_validation_queue; "
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


def test_dual_machine_mapping_validation_queue_lists_both_machines_by_default():
    from rytm_randomizer.dual_machine.mapping_validation_queue import (
        format_dual_machine_mapping_validation_queue_report,
    )

    report = "\n".join(format_dual_machine_mapping_validation_queue_report(limit=2))

    assert "RytmRandomizer passive Dual-Machine Mapping Validation Queue" in report
    assert "Target: both" in report
    assert "Per-machine limit: 2" in report
    assert "Analog Four Track 1 / Track Level / CC95 / key track-level" in report
    assert "Rytm Pad 1 / FLT Frequency / CC74 / key flt-frequency" in report
    assert "analog-four-saved-offset-mapping-guide --track 1 --parameter track-level" in report
    assert "rytm-controlled-mapping-proof-report" in report
    assert "- no MIDI sending" in report


def test_dual_machine_mapping_validation_queue_can_filter_to_a4():
    from rytm_randomizer.dual_machine.mapping_validation_queue import (
        format_dual_machine_mapping_validation_queue_report,
    )

    report = "\n".join(
        format_dual_machine_mapping_validation_queue_report(
            target="analog-four",
            limit=3,
        )
    )

    assert "Target: analog-four" in report
    assert "Analog Four Track 1 / Track Level / CC95 / key track-level" in report
    assert "Analog Four Track 1 / Filter 1 Frequency / CC18 / key filter-1-frequency" in report
    assert "Rytm Pad" not in report


def test_dual_machine_mapping_validation_queue_can_filter_to_rytm_in_process():
    from rytm_randomizer.dual_machine.mapping_validation_queue import (
        format_dual_machine_mapping_validation_queue_report,
    )

    report = "\n".join(
        format_dual_machine_mapping_validation_queue_report(
            target="rytm",
            limit=2,
        )
    )

    assert "Target: rytm" in report
    assert "Available controlled mapping targets: 96" in report
    assert "Rytm Pad 1 / FLT Frequency / CC74 / key flt-frequency" in report
    assert "Rytm Pad 1 / FLT Resonance / CC75 / key flt-resonance" in report
    assert "Analog Four Track" not in report
    assert "Guide:" not in report


def test_dual_machine_mapping_validation_queue_accepts_a4_alias():
    from rytm_randomizer.dual_machine.mapping_validation_queue import (
        build_dual_machine_mapping_validation_queue,
    )

    queue = build_dual_machine_mapping_validation_queue(target="a4", limit=1)

    assert len(queue) == 1
    assert queue[0].machine == "Analog Four"
    assert queue[0].lane == "Track 1"


def test_dual_machine_mapping_validation_queue_rejects_invalid_target():
    from rytm_randomizer.dual_machine.mapping_validation_queue import (
        format_dual_machine_mapping_validation_queue_report,
    )

    with pytest.raises(ValueError, match="target must be one of"):
        format_dual_machine_mapping_validation_queue_report(target="octatrack")


def test_dual_machine_mapping_validation_queue_rejects_invalid_limit():
    from rytm_randomizer.dual_machine.mapping_validation_queue import (
        format_dual_machine_mapping_validation_queue_report,
    )

    with pytest.raises(ValueError, match="limit must be at least 1"):
        format_dual_machine_mapping_validation_queue_report(limit=0)


def test_dual_machine_mapping_validation_queue_error_report_is_passive():
    from rytm_randomizer.dual_machine.mapping_validation_queue import (
        format_dual_machine_mapping_validation_queue_error,
    )

    report = "\n".join(format_dual_machine_mapping_validation_queue_error("bad target"))

    assert "Found: False" in report
    assert "bad target" in report
    assert "- no MIDI sending" in report
    assert "- no command execution" in report


def test_dual_machine_mapping_validation_queue_cli_prints_report():
    result = run_cli(
        "dual-machine-mapping-validation-queue-report", "--target", "rytm", "--limit", "1"
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Dual-Machine Mapping Validation Queue" in result.stdout
    assert "Target: rytm" in result.stdout
    assert "Rytm Pad 1 / FLT Frequency / CC74 / key flt-frequency" in result.stdout
    assert "Analog Four Track" not in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
