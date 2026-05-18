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


def normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def test_importing_essence_application_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.essence_application; "
                "assert 'mido' not in sys.modules; "
                "assert 'rtmidi' not in sys.modules; "
                "assert 'librosa' not in sys.modules"
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


def test_safe_anchors_marks_only_current_four_pad_runtime_as_ready():
    from rytm_randomizer.essence_application import evaluate_essence_application_readiness

    readiness = evaluate_essence_application_readiness(
        mode="safe_anchors",
        tags=("metallic", "bell", "driving", "repetition"),
        discovery=0.35,
    )

    assert readiness.ready is False
    assert readiness.reason == "safe_anchors_partial_runtime_only"
    assert readiness.ready_pad_count == 4
    assert readiness.blocked_pad_count == 8
    assert readiness.future_only_pad_count == 0
    assert readiness.pads[0].pad == 1
    assert readiness.pads[0].status == "ready"
    assert readiness.pads[0].reason == "mapped_pad_supported"
    assert readiness.pads[4].pad == 5
    assert readiness.pads[4].status == "blocked"
    assert readiness.pads[4].reason == "pads_5_12_not_runtime_supported"


def test_live_snapshot_blocks_all_pads_until_snapshot_is_captured():
    from rytm_randomizer.essence_application import evaluate_essence_application_readiness
    from rytm_randomizer.performance.modes import SnapshotState

    readiness = evaluate_essence_application_readiness(
        mode="live_snapshot",
        tags=("metallic", "bell", "driving", "repetition"),
        discovery=0.35,
        snapshot_state=SnapshotState(
            mode="live_snapshot",
            capture_status="not_requested",
            expected_pad_count=12,
            captured_pad_count=0,
        ),
    )

    assert readiness.ready is False
    assert readiness.reason == "snapshot_not_captured"
    assert readiness.ready_pad_count == 0
    assert readiness.blocked_pad_count == 12
    assert {pad.reason for pad in readiness.pads} == {"snapshot_not_captured"}


def test_live_snapshot_with_complete_snapshot_and_mapped_candidates_is_ready():
    from rytm_randomizer.essence_application import evaluate_essence_application_readiness
    from rytm_randomizer.performance.modes import SnapshotState

    readiness = evaluate_essence_application_readiness(
        mode="live_snapshot",
        tags=("metallic", "bell", "driving", "repetition"),
        discovery=0.35,
        snapshot_state=SnapshotState(
            mode="live_snapshot",
            capture_status="captured",
            expected_pad_count=12,
            captured_pad_count=12,
        ),
    )

    assert readiness.ready is True
    assert readiness.reason == "full_12_pad_application_ready"
    assert readiness.ready_pad_count == 12
    assert readiness.blocked_pad_count == 0
    assert readiness.future_only_pad_count == 0
    assert {pad.status for pad in readiness.pads} == {"ready"}


def test_future_inventory_candidate_blocks_application_after_snapshot_capture():
    from rytm_randomizer.essence_application import evaluate_essence_application_readiness
    from rytm_randomizer.performance.modes import SnapshotState

    readiness = evaluate_essence_application_readiness(
        mode="live_snapshot",
        tags=("metallic", "bell", "digital", "repetition"),
        discovery=1.0,
        snapshot_state=SnapshotState(
            mode="live_snapshot",
            capture_status="captured",
            expected_pad_count=12,
            captured_pad_count=12,
        ),
    )

    pad3 = readiness.pads[2]

    assert readiness.ready is False
    assert readiness.reason == "candidate_mapping_incomplete"
    assert pad3.pad == 3
    assert pad3.selected_machine_label == "SY Chip"
    assert pad3.status == "future_only"
    assert pad3.reason == "machine_needs_manual_mapping"


def test_live_snapshot_fixture_blocks_unmapped_captured_machines():
    from rytm_randomizer.essence_application import evaluate_essence_application_readiness
    from rytm_randomizer.snapshot.fixtures import get_snapshot_fixture

    readiness = evaluate_essence_application_readiness(
        mode="live_snapshot",
        tags=("metallic", "bell", "driving", "repetition"),
        discovery=0.35,
        snapshot_fixture=get_snapshot_fixture("am9-slot-01"),
    )

    assert readiness.ready is False
    assert readiness.reason == "snapshot_mapping_incomplete"
    assert readiness.snapshot_fixture_label == "AM9 Slot 01 Mock 12-pad Snapshot"
    assert readiness.ready_pad_count == 9
    assert readiness.future_only_pad_count == 3
    assert readiness.pads[4].pad == 5
    assert readiness.pads[4].captured_machine_label == "CH/OH hat family"
    assert readiness.pads[4].status == "future_only"
    assert readiness.pads[4].reason == "snapshot_machine_needs_manual_mapping"


def test_format_essence_application_readiness_report():
    from rytm_randomizer.essence_application import (
        evaluate_essence_application_readiness,
        format_essence_application_readiness_report,
    )

    readiness = evaluate_essence_application_readiness(
        mode="safe_anchors",
        tags=("metallic", "bell", "driving", "repetition"),
        discovery=0.35,
    )
    report = format_essence_application_readiness_report(readiness)

    assert report[0] == "RytmRandomizer passive Essence Application Readiness Report"
    assert "Mode: Safe Anchors" in report
    assert "Ready: False" in report
    assert "Reason: safe_anchors_partial_runtime_only" in report
    assert "Pad counts: ready 4 / blocked 8 / future-only 0" in report
    assert any(
        line
        == "- Pad 5 / Closed hat pulse: BD FM [mutable] -> blocked (pads_5_12_not_runtime_supported)"
        for line in report
    )
    assert "- no MIDI sending" in report
    assert "- no hardware mutation" in report


def test_essence_application_readiness_cli_description_live_snapshot_captured():
    result = run_cli(
        "essence-application-readiness-report",
        "--mode",
        "live-snapshot",
        "--description",
        "metallic bell driving repetition Detroit techno",
        "--discovery",
        "1.0",
        "--snapshot",
        "captured",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Essence Application Readiness Report" in result.stdout
    assert "Mode: Live Snapshot" in result.stdout
    assert "Ready: False" in result.stdout
    assert "Reason: candidate_mapping_incomplete" in result.stdout
    assert "SY Chip [future] -> future-only (machine_needs_manual_mapping)" in result.stdout
    assert "- no live SysEx receive" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_essence_application_readiness_cli_tags_safe_anchors():
    result = run_cli(
        "essence-application-readiness-report",
        "--mode",
        "safe-anchors",
        "--tags",
        "metallic,bell,driving,repetition",
        "--discovery",
        "0.35",
    )

    assert result.returncode == 0
    assert "Mode: Safe Anchors" in result.stdout
    assert "Reason: safe_anchors_partial_runtime_only" in result.stdout
    assert "Pad counts: ready 4 / blocked 8 / future-only 0" in result.stdout
    assert result.stderr == ""


def test_essence_application_readiness_cli_uses_snapshot_fixture():
    result = run_cli(
        "essence-application-readiness-report",
        "--mode",
        "live-snapshot",
        "--description",
        "metallic bell driving repetition Detroit techno",
        "--discovery",
        "0.35",
        "--fixture",
        "am9-slot-01",
    )

    assert result.returncode == 0
    assert "Snapshot fixture: AM9 Slot 01 Mock 12-pad Snapshot" in result.stdout
    assert "Reason: snapshot_mapping_incomplete" in result.stdout
    assert "Pad counts: ready 9 / blocked 0 / future-only 3" in result.stdout
    assert (
        "Pad 5 / Closed hat pulse: BD FM [mutable] / captured CH/OH hat family [future] "
        "-> future-only (snapshot_machine_needs_manual_mapping)"
    ) in result.stdout
    assert result.stderr == ""


def test_essence_application_readiness_cli_accepts_style_intent_with_profile_discovery():
    result = run_cli(
        "essence-application-readiness-report",
        "--mode",
        "live-snapshot",
        "--style",
        "schranz",
        "--fixture",
        "am9-slot-01",
    )

    assert result.returncode == 0
    assert "Source: Style Intent" in result.stdout
    assert "Style prompt: schranz" in result.stdout
    assert "Matched profiles: Schranz" in result.stdout
    assert (
        "Essence tags: metallic, driving, pressure, repetition, density, bright, noise, raw, tension"
        in result.stdout
    )
    assert "Discovery: 0.82" in result.stdout
    assert "Snapshot fixture: AM9 Slot 01 Mock 12-pad Snapshot" in result.stdout
    assert "Reason: snapshot_mapping_incomplete" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_essence_application_readiness_cli_style_intent_allows_discovery_override():
    result = run_cli(
        "essence-application-readiness-report",
        "--mode",
        "live-snapshot",
        "--style",
        "Birmingham dark techno",
        "--discovery",
        "0.35",
        "--snapshot",
        "captured",
    )

    assert result.returncode == 0
    assert "Source: Style Intent" in result.stdout
    assert "Style prompt: Birmingham dark techno" in result.stdout
    assert "Matched profiles: Dark Techno, Birmingham Techno" in result.stdout
    assert "Discovery: 0.35" in result.stdout
    assert "Mode: Live Snapshot" in result.stdout
    assert "Ready: True" in result.stdout
    assert "Reason: full_12_pad_application_ready" in result.stdout
    assert result.stderr == ""


def test_essence_application_readiness_cli_invalid_mode_fails_safely():
    result = run_cli(
        "essence-application-readiness-report",
        "--mode",
        "stage",
        "--tags",
        "metallic,bell",
        "--discovery",
        "0.35",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == "\n".join(
        [
            "RytmRandomizer passive Essence Application Readiness Report",
            "Found: False",
            "Message: Mode must be safe-anchors or live-snapshot. No MIDI was sent. No command executed.",
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
