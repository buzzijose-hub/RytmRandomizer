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


def test_importing_rytm_engine_cycle_plan_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.rytm_engine_cycle_plan; "
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


def test_birmingham_engine_cycle_plan_prefers_real_hat_and_metallic_engines():
    from rytm_randomizer.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan

    plan = build_rytm_engine_cycle_plan("Birmingham dark techno", discovery=0.35)

    assert plan.style_prompt == "Birmingham dark techno"
    assert plan.discovery == 0.35
    assert plan.pad_count == 12
    assert plan.top_candidate_count == 12
    assert plan.mock_message_count == 12

    pad3 = plan.pads[2]
    assert pad3.role_label == "Metallic motif"
    assert pad3.top_candidate.machine_key == "sy_chip"
    assert pad3.top_candidate.machine_value == 29
    assert pad3.top_candidate.support_status == "machine_selectable"

    pad5 = plan.pads[4]
    assert pad5.role_label == "Closed hat pulse"
    assert pad5.top_candidate.machine_key == "ch_metallic"
    assert pad5.top_candidate.machine_value == 17
    assert pad5.top_candidate.support_status == "machine_selectable"


def test_engine_cycle_mock_capture_sends_top_candidate_cc15_per_pad():
    from rytm_randomizer.rytm_engine_cycle_plan import (
        build_rytm_engine_cycle_plan,
        capture_rytm_engine_cycle_mock_messages,
    )

    plan = build_rytm_engine_cycle_plan("Birmingham dark techno", discovery=0.35)
    sender = capture_rytm_engine_cycle_mock_messages(plan)

    assert len(sender.sent_messages) == 12
    assert sender.sent_messages[0].channel == 0
    assert sender.sent_messages[0].control == 15
    assert sender.sent_messages[0].metadata["pad"] == 1
    assert sender.sent_messages[0].metadata["event_role"] == "engine_cycle_top_candidate"
    pad5 = sender.sent_messages[4]
    assert pad5.channel == 4
    assert pad5.control == 15
    assert pad5.value == 17
    assert pad5.metadata["machine_key"] == "ch_metallic"


def test_engine_cycle_report_includes_support_boundaries_and_mock_stream():
    from rytm_randomizer.rytm_engine_cycle_plan import (
        build_rytm_engine_cycle_plan,
        format_rytm_engine_cycle_plan_report,
    )

    plan = build_rytm_engine_cycle_plan("schranz", discovery=0.82)
    report = format_rytm_engine_cycle_plan_report(plan)

    assert report[0] == "RytmRandomizer passive Rytm Engine Cycle Plan Report"
    assert "Style prompt: schranz" in report
    assert "Discovery: 0.82" in report
    assert "Pad counts: planned 12 / no-candidate 0" in report
    assert "Mock CC15 top-candidate stream: 12 message(s)" in report
    assert any(
        line.startswith(
            "- Pad 5 / Closed hat pulse: 1. CH Metallic CC15 -> 17 [machine_selectable]"
        )
        for line in report
    )
    assert any(line == "- Pad 5 ch 5 wire 4 CC15 -> 17 / CH Metallic" for line in report)
    assert "- machine_selectable means engine switch only; tuned anchors are pending" in report
    assert "- no MIDI sending" in report


def test_rytm_engine_cycle_plan_report_cli_accepts_style_prompt():
    result = run_cli(
        "rytm-engine-cycle-plan-report",
        "--style",
        "Birmingham dark techno",
        "--discovery",
        "0.35",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm Engine Cycle Plan Report" in result.stdout
    assert "Style prompt: Birmingham dark techno" in result.stdout
    assert "Pad counts: planned 12 / no-candidate 0" in result.stdout
    assert "Pad 5 / Closed hat pulse: 1. CH Metallic CC15 -> 17" in result.stdout
    assert "Pad 9 / Tonal bell accent: 1. CB Classic CC15 -> 12" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
