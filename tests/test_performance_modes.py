import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_performance_modes_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.performance.modes; "
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


def test_performance_modes_keep_safe_anchors_first_and_live_snapshot_second():
    from rytm_randomizer.performance.modes import list_performance_modes

    safe_anchors, live_snapshot = list_performance_modes()

    assert safe_anchors.key == "safe_anchors"
    assert safe_anchors.label == "Safe Anchors"
    assert safe_anchors.menu_number == "1"
    assert safe_anchors.baseline_source == "validated_app_anchors"
    assert safe_anchors.return_target == "validated_app_anchors"
    assert safe_anchors.expected_pad_count == 4
    assert safe_anchors.requires_hardware_capture is False

    assert live_snapshot.key == "live_snapshot"
    assert live_snapshot.label == "Live Snapshot"
    assert live_snapshot.menu_number == "2"
    assert live_snapshot.baseline_source == "captured_loaded_kit"
    assert live_snapshot.return_target == "captured_loaded_kit"
    assert live_snapshot.expected_pad_count == 12
    assert live_snapshot.requires_hardware_capture is True
    assert live_snapshot.continuous_tracking is False


def test_performance_mode_prompt_matches_checkpoint_design():
    from rytm_randomizer.performance.modes import format_performance_mode_prompt

    assert format_performance_mode_prompt() == [
        "Select performance mode:",
        "",
        "1 = Safe Anchors",
        "    Load validated app anchors, then mutate from them.",
        "",
        "2 = Live Snapshot",
        "    Capture the currently loaded Rytm kit, then mutate from that snapshot.",
        "",
        "Mode:",
    ]


def test_live_snapshot_blocks_mutation_until_full_snapshot_is_captured():
    from rytm_randomizer.performance.modes import (
        SnapshotState,
        evaluate_mutation_readiness,
    )

    not_captured = SnapshotState(
        mode="live_snapshot",
        capture_status="not_requested",
        expected_pad_count=12,
        captured_pad_count=0,
    )
    partial = SnapshotState(
        mode="live_snapshot",
        capture_status="partial",
        expected_pad_count=12,
        captured_pad_count=8,
    )
    failed = SnapshotState(
        mode="live_snapshot",
        capture_status="failed",
        expected_pad_count=12,
        captured_pad_count=0,
    )
    captured = SnapshotState(
        mode="live_snapshot",
        capture_status="captured",
        expected_pad_count=12,
        captured_pad_count=12,
    )

    assert evaluate_mutation_readiness(not_captured).ready is False
    assert evaluate_mutation_readiness(not_captured).reason == "snapshot_not_captured"
    assert evaluate_mutation_readiness(partial).ready is False
    assert evaluate_mutation_readiness(partial).reason == "snapshot_incomplete"
    assert evaluate_mutation_readiness(failed).ready is False
    assert evaluate_mutation_readiness(failed).reason == "snapshot_capture_failed"
    assert evaluate_mutation_readiness(captured).ready is True
    assert evaluate_mutation_readiness(captured).reason == "snapshot_ready"


def test_safe_anchors_mode_is_ready_without_hardware_capture():
    from rytm_randomizer.performance.modes import (
        SnapshotState,
        evaluate_mutation_readiness,
    )

    state = SnapshotState(
        mode="safe_anchors",
        capture_status="not_requested",
        expected_pad_count=4,
        captured_pad_count=0,
    )

    result = evaluate_mutation_readiness(state)

    assert result.ready is True
    assert result.reason == "safe_anchors_ready"
