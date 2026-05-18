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


def test_importing_performance_snapshot_target_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.performance.snapshot_target; "
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


def test_rytm_target_leaves_analog_four_untouched():
    from rytm_randomizer.performance.snapshot_target import (
        build_performance_snapshot_target_plan,
    )

    plan = build_performance_snapshot_target_plan("rytm")

    assert plan.canonical_target == "rytm"
    assert plan.active_device_keys == ("analog_rytm",)
    assert plan.untouched_device_keys == ("analog_four",)
    assert plan.active_devices[0].capture_enabled is True
    assert plan.active_devices[0].mutation_enabled is True
    assert plan.untouched_devices[0].label == "Analog Four MKII"
    assert plan.untouched_devices[0].leave_alone is True


def test_analog_four_target_leaves_rytm_untouched():
    from rytm_randomizer.performance.snapshot_target import (
        build_performance_snapshot_target_plan,
    )

    plan = build_performance_snapshot_target_plan("a4")

    assert plan.canonical_target == "analog-four"
    assert plan.active_device_keys == ("analog_four",)
    assert plan.untouched_device_keys == ("analog_rytm",)
    assert plan.active_devices[0].label == "Analog Four MKII"
    assert plan.untouched_devices[0].label == "Analog Rytm MKII"


def test_both_target_arms_both_devices_and_leaves_none_untouched():
    from rytm_randomizer.performance.snapshot_target import (
        build_performance_snapshot_target_plan,
    )

    plan = build_performance_snapshot_target_plan("all")

    assert plan.canonical_target == "both"
    assert plan.active_device_keys == ("analog_rytm", "analog_four")
    assert plan.untouched_device_keys == ()
    assert plan.active_device_labels == ("Analog Rytm MKII", "Analog Four MKII")
    assert plan.untouched_device_labels == ()


def test_target_scope_rejects_unknown_target():
    from rytm_randomizer.performance.snapshot_target import (
        PerformanceSnapshotTargetError,
        build_performance_snapshot_target_plan,
    )

    with pytest.raises(
        PerformanceSnapshotTargetError,
        match="target must be rytm, analog-four, or both",
    ):
        build_performance_snapshot_target_plan("octatrack")


def test_target_scope_report_marks_untouched_devices():
    from rytm_randomizer.performance.snapshot_target import (
        build_performance_snapshot_target_plan,
        format_performance_snapshot_target_report,
    )

    report = format_performance_snapshot_target_report(
        build_performance_snapshot_target_plan("analog-four")
    )

    assert report[:8] == [
        "RytmRandomizer passive Performance Snapshot Target Report",
        "Mode: live_snapshot",
        "Requested target: analog-four",
        "Active devices: Analog Four MKII",
        "Untouched devices: Analog Rytm MKII",
        "Device actions:",
        "- Analog Four MKII: capture enabled / mutation enabled / restore target captured snapshot",
        "- Analog Rytm MKII: untouched / no capture / no mutation / no restore",
    ]
    assert "- no MIDI sending" in report
    assert "- no port opening" in report


def test_performance_snapshot_target_cli_reports_rytm_only_scope():
    result = run_cli("performance-snapshot-target-report", "--target", "rytm")

    assert result.returncode == 0
    assert "RytmRandomizer passive Performance Snapshot Target Report" in result.stdout
    assert "Requested target: rytm" in result.stdout
    assert "Active devices: Analog Rytm MKII" in result.stdout
    assert "Untouched devices: Analog Four MKII" in result.stdout
    assert "- Analog Four MKII: untouched / no capture / no mutation / no restore" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
