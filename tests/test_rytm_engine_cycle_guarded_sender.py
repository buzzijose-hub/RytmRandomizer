import subprocess
import sys
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_plan():
    from rytm_randomizer.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan

    return build_rytm_engine_cycle_plan("Birmingham dark techno", discovery=0.35)


def test_importing_rytm_engine_cycle_guarded_sender_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.rytm_engine_cycle_guarded_sender; "
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


def test_guarded_engine_cycle_requires_arming_before_mock_emit():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.rytm_engine_cycle_guarded_sender import (
        execute_rytm_engine_cycle_guarded_send,
    )

    sender = MockMidiSender()
    result = execute_rytm_engine_cycle_guarded_send(
        build_plan(),
        sender,
        armed=False,
        dry_run_confirmed=True,
    )

    assert result.accepted is False
    assert result.reason == "missing_arming"
    assert result.emitted_message_count == 0
    assert sender.sent_messages == ()


def test_guarded_engine_cycle_requires_dry_run_confirmation_before_mock_emit():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.rytm_engine_cycle_guarded_sender import (
        execute_rytm_engine_cycle_guarded_send,
    )

    sender = MockMidiSender()
    result = execute_rytm_engine_cycle_guarded_send(
        build_plan(),
        sender,
        armed=True,
        dry_run_confirmed=False,
    )

    assert result.accepted is False
    assert result.reason == "missing_dry_run_confirmation"
    assert result.emitted_message_count == 0
    assert sender.sent_messages == ()


def test_guarded_engine_cycle_refuses_unresolved_pad_without_partial_emit():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.rytm_engine_cycle_guarded_sender import (
        execute_rytm_engine_cycle_guarded_send,
    )

    plan = build_plan()
    unresolved_pad = replace(plan.pads[0], candidates=())
    plan = replace(plan, pads=(unresolved_pad, *plan.pads[1:]))
    sender = MockMidiSender()

    result = execute_rytm_engine_cycle_guarded_send(
        plan,
        sender,
        armed=True,
        dry_run_confirmed=True,
    )

    assert result.accepted is False
    assert result.reason == "plan_has_unresolved_pads"
    assert result.no_candidate_count == 1
    assert result.emitted_message_count == 0
    assert sender.sent_messages == ()


def test_guarded_engine_cycle_emits_12_cc15_messages_to_mock_sender():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.rytm_engine_cycle_guarded_sender import (
        execute_rytm_engine_cycle_guarded_send,
    )

    sender = MockMidiSender()
    result = execute_rytm_engine_cycle_guarded_send(
        build_plan(),
        sender,
        armed=True,
        dry_run_confirmed=True,
    )

    assert result.accepted is True
    assert result.reason == "accepted_guarded_mock_only"
    assert result.style_prompt == "Birmingham dark techno"
    assert result.planned_pad_count == 12
    assert result.emitted_message_count == 12
    assert sender.sent_messages == result.emitted_messages
    assert result.emitted_messages[0].channel == 0
    assert result.emitted_messages[0].control == 15
    assert result.emitted_messages[0].value == 0
    assert result.emitted_messages[0].metadata["guard"] == "rytm_engine_cycle_guarded_send_dry_run"
    assert result.emitted_messages[4].channel == 4
    assert result.emitted_messages[4].value == 17
    assert result.emitted_messages[4].metadata["machine_key"] == "ch_metallic"


def test_guarded_engine_cycle_report_formats_policy_and_preview():
    from rytm_randomizer.rytm_engine_cycle_guarded_sender import (
        build_rytm_engine_cycle_guarded_send_dry_run,
        format_rytm_engine_cycle_guarded_send_dry_run_report,
    )

    result = build_rytm_engine_cycle_guarded_send_dry_run(build_plan())
    report = "\n".join(format_rytm_engine_cycle_guarded_send_dry_run_report(result))

    assert "RytmRandomizer passive Rytm Engine Cycle Guarded Send Dry-Run Report" in report
    assert "Accepted: True" in report
    assert "Emitted mock messages: 12" in report
    assert "Pad 5 / ch 5 wire 4 / CC15 -> 17 / CH Metallic" in report
    assert "- mock-only guarded Rytm engine-cycle send" in report
    assert "- emits top-candidate CC15 machine-select events only" in report
    assert "- no MIDI sending" in report
