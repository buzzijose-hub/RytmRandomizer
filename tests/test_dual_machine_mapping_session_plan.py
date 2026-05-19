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


def test_importing_dual_machine_mapping_session_plan_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.dual_machine.mapping_session_plan; "
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


def test_dual_machine_mapping_session_plan_formats_operator_run_sheet():
    from rytm_randomizer.dual_machine.mapping_session_plan import (
        format_dual_machine_mapping_session_plan_report,
    )

    report = "\n".join(
        format_dual_machine_mapping_session_plan_report(
            target="both",
            slot=7,
            limit=1,
        )
    )

    assert "RytmRandomizer passive Dual-Machine Mapping Session Plan" in report
    assert "Target: both" in report
    assert "Kit slot: 7" in report
    assert "Per-machine target limit: 1" in report
    assert "analog-four-slot-007-baseline.syx" in report
    assert "analog-four-slot-007-track-1-track-level-after.syx" in report
    assert "rytm-slot-007-baseline.syx" in report
    assert "rytm-slot-007-pad-1-flt-frequency-after.syx" in report
    assert "Analog Four Track 1 / Track Level / CC95 / key track-level" in report
    assert "Rytm Pad 1 / FLT Frequency / CC74 / key flt-frequency" in report
    assert (
        'analog-four-saved-offset-mapping-promotion-report "analog-four-slot-007-baseline.syx" '
        '"analog-four-slot-007-track-1-track-level-after.syx" --slot 7'
    ) in report
    assert (
        'rytm-controlled-mapping-proof-report "rytm-slot-007-baseline.syx" '
        '"rytm-slot-007-pad-1-flt-frequency-after.syx" --slot 7'
    ) in report
    assert '"<before.syx>"' not in report
    assert "--slot <1-128>" not in report
    assert "Accept only if the proof shows exactly one intended mapping change." in report
    assert "- no MIDI sending" in report


def test_dual_machine_mapping_session_plan_can_filter_to_a4_alias():
    from rytm_randomizer.dual_machine.mapping_session_plan import (
        format_dual_machine_mapping_session_plan_report,
    )

    report = "\n".join(
        format_dual_machine_mapping_session_plan_report(
            target="a4",
            slot=12,
            limit=2,
        )
    )

    assert "Target: analog-four" in report
    assert "analog-four-slot-012-baseline.syx" in report
    assert "Analog Four Track 1 / Track Level / CC95 / key track-level" in report
    assert "Analog Four Track 1 / Filter 1 Frequency / CC18 / key filter-1-frequency" in report
    assert "Rytm Pad" not in report


def test_dual_machine_mapping_session_plan_can_filter_to_rytm():
    from rytm_randomizer.dual_machine.mapping_session_plan import (
        format_dual_machine_mapping_session_plan_report,
    )

    report = "\n".join(
        format_dual_machine_mapping_session_plan_report(
            target="rytm",
            slot=3,
            limit=2,
        )
    )

    assert "Target: rytm" in report
    assert "rytm-slot-003-baseline.syx" in report
    assert "Rytm Pad 1 / FLT Frequency / CC74 / key flt-frequency" in report
    assert "Rytm Pad 1 / FLT Resonance / CC75 / key flt-resonance" in report
    assert "Analog Four Track" not in report


def test_dual_machine_mapping_session_plan_rejects_invalid_slot():
    from rytm_randomizer.dual_machine.mapping_session_plan import (
        format_dual_machine_mapping_session_plan_report,
    )

    with pytest.raises(ValueError, match="slot must be between 1 and 128"):
        format_dual_machine_mapping_session_plan_report(slot=0)


def test_dual_machine_mapping_session_plan_rejects_invalid_limit():
    from rytm_randomizer.dual_machine.mapping_session_plan import (
        format_dual_machine_mapping_session_plan_report,
    )

    with pytest.raises(ValueError, match="limit must be at least 1"):
        format_dual_machine_mapping_session_plan_report(limit=0)


def test_dual_machine_mapping_session_plan_error_report_is_passive():
    from rytm_randomizer.dual_machine.mapping_session_plan import (
        format_dual_machine_mapping_session_plan_error,
    )

    report = "\n".join(format_dual_machine_mapping_session_plan_error("bad slot"))

    assert "Found: False" in report
    assert "bad slot" in report
    assert "- no MIDI sending" in report
    assert "- no command execution" in report


def test_dual_machine_mapping_session_plan_cli_prints_report():
    result = run_cli(
        "dual-machine-mapping-session-plan-report",
        "--target",
        "analog-four",
        "--slot",
        "12",
        "--limit",
        "1",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Dual-Machine Mapping Session Plan" in result.stdout
    assert "Target: analog-four" in result.stdout
    assert "analog-four-slot-012-baseline.syx" in result.stdout
    assert "Rytm Pad" not in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_dual_machine_mapping_session_plan_cli_reports_validation_error():
    result = run_cli(
        "dual-machine-mapping-session-plan-report",
        "--slot",
        "129",
    )

    assert result.returncode == 1
    assert "RytmRandomizer passive Dual-Machine Mapping Session Plan" in result.stderr
    assert "slot must be between 1 and 128" in result.stderr
    assert "No MIDI was sent" in result.stderr
    assert result.stdout == ""
