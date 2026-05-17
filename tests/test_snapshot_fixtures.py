import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_snapshot_fixtures_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.snapshot_fixtures; "
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


def test_am9_mock_snapshot_fixture_has_twelve_pads_and_support_mix():
    from rytm_randomizer.snapshot_fixtures import get_snapshot_fixture

    fixture = get_snapshot_fixture("am9-slot-01")

    assert fixture.key == "am9-slot-01"
    assert fixture.label == "AM9 Slot 01 Mock 12-pad Snapshot"
    assert fixture.capture_status == "captured"
    assert fixture.expected_pad_count == 12
    assert len(fixture.pads) == 12
    assert tuple(pad.pad for pad in fixture.pads) == tuple(range(1, 13))
    assert fixture.pads[0].machine_key == "bd_hard"
    assert fixture.pads[0].machine_value == 0
    assert fixture.pads[4].machine_key == "hat_family"
    assert fixture.pads[4].support_status == "needs_manual_mapping"
    assert fixture.pads[6].machine_key == "rs_family"
    assert fixture.pads[6].support_status == "needs_manual_mapping"
    assert fixture.mapped_pad_count == 9
    assert fixture.future_only_pad_count == 3


def test_snapshot_fixture_lookup_fails_loudly_for_unknown_key():
    from rytm_randomizer.snapshot_fixtures import get_snapshot_fixture

    with pytest.raises(KeyError, match="unknown snapshot fixture"):
        get_snapshot_fixture("missing")


def test_snapshot_state_from_fixture_reports_complete_capture():
    from rytm_randomizer.snapshot_fixtures import (
        get_snapshot_fixture,
        snapshot_state_from_fixture,
    )

    state = snapshot_state_from_fixture(get_snapshot_fixture("am9-slot-01"))

    assert state.mode == "live_snapshot"
    assert state.capture_status == "captured"
    assert state.expected_pad_count == 12
    assert state.captured_pad_count == 12


def test_format_snapshot_fixture_report_is_passive_and_deterministic():
    from rytm_randomizer.snapshot_fixtures import (
        format_snapshot_fixture_report,
        get_snapshot_fixture,
    )

    report = format_snapshot_fixture_report(get_snapshot_fixture("am9-slot-01"))

    assert report[0] == "RytmRandomizer passive Snapshot Fixture Report"
    assert "Fixture: AM9 Slot 01 Mock 12-pad Snapshot" in report
    assert "Capture status: captured" in report
    assert "Pad counts: total 12 / mapped 9 / future-only 3" in report
    assert "- Pad 1: BD Hard [mutable] / baseline params 7" in report
    assert "- Pad 5: CH/OH hat family [future] / baseline params 0" in report
    assert "- no MIDI sending" in report
    assert "- no live SysEx receive" in report
    assert "- no hardware mutation" in report
