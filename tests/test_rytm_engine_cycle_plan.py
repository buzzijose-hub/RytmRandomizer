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
                "import rytm_randomizer.essence.rytm_engine_cycle_plan; "
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


def test_birmingham_engine_cycle_plan_uses_os172_track_lanes():
    from rytm_randomizer.essence.machine_catalog import is_machine_allowed_on_pad
    from rytm_randomizer.essence.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan

    plan = build_rytm_engine_cycle_plan("Birmingham dark techno", discovery=0.35)

    assert plan.style_prompt == "Birmingham dark techno"
    assert plan.discovery == 0.35
    assert plan.pad_count == 12
    assert plan.top_candidate_count == 12
    assert plan.mock_message_count == 12
    assert all(
        is_machine_allowed_on_pad(pad.pad, pad.top_candidate.machine_key) for pad in plan.pads
    )

    pad3 = plan.pads[2]
    assert pad3.role_label == "RS / Rim shot"
    assert pad3.top_candidate.machine_key == "rs_hard"
    assert pad3.top_candidate.machine_value == 4
    assert pad3.top_candidate.support_status == "machine_selectable"

    pad5 = plan.pads[4]
    assert pad5.role_label == "BT / Bass tom"
    assert pad5.top_candidate.machine_key == "bt_classic"
    assert pad5.top_candidate.machine_value == 7
    assert pad5.top_candidate.support_status == "machine_selectable"

    pad10 = plan.pads[9]
    assert pad10.role_label == "OH / Open hihat"
    assert pad10.top_candidate.machine_key in {"oh_classic", "oh_metallic", "hh_basic", "hh_lab"}
    assert pad10.top_candidate.machine_key != "xt_classic"


def test_engine_cycle_plan_applies_os172_pad_capabilities_to_all_candidates():
    from rytm_randomizer.essence.machine_catalog import is_machine_allowed_on_pad
    from rytm_randomizer.essence.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan

    plan = build_rytm_engine_cycle_plan("schranz industrial hard techno", discovery=0.9)

    assert plan.pad_count == 12
    assert plan.no_candidate_count == 0
    for pad in plan.pads:
        assert pad.candidates
        assert all(
            is_machine_allowed_on_pad(pad.pad, candidate.machine_key)
            for candidate in pad.candidates
        )

    assert plan.pads[4].top_candidate.machine_key == "bt_classic"
    assert plan.pads[5].top_candidate.machine_key == "xt_classic"
    assert plan.pads[6].top_candidate.machine_key == "xt_classic"
    assert plan.pads[7].top_candidate.machine_key == "xt_classic"
    assert plan.pads[9].top_candidate.machine_key in {
        "oh_classic",
        "oh_metallic",
        "hh_basic",
        "hh_lab",
    }


def test_engine_cycle_mock_capture_sends_top_candidate_cc15_per_pad():
    from rytm_randomizer.essence.rytm_engine_cycle_plan import (
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
    assert pad5.value == 7
    assert pad5.metadata["machine_key"] == "bt_classic"


def test_engine_cycle_report_includes_support_boundaries_and_mock_stream():
    from rytm_randomizer.essence.rytm_engine_cycle_plan import (
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
        line.startswith("- Pad 5 / BT / Bass tom: 1. BT Classic CC15 -> 7 [machine_selectable]")
        for line in report
    )
    assert any(line == "- Pad 5 ch 5 wire 4 CC15 -> 7 / BT Classic" for line in report)
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
    assert "Pad 5 / BT / Bass tom: 1. BT Classic CC15 -> 7" in result.stdout
    assert "Pad 9 / CH / Closed hihat: 1. CH Metallic CC15 -> 17" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
