import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_twelve_pad_rytm_runtime_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.essence.twelve_pad_rytm_runtime; "
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


def test_build_twelve_pad_rytm_runtime_plan_uses_auto_profile_and_source_starters():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        build_twelve_pad_rytm_runtime_plan,
    )

    plan = build_twelve_pad_rytm_runtime_plan(
        "Birmingham dark techno",
        discovery=0.35,
    )

    assert plan.style_prompt == "Birmingham dark techno"
    assert plan.discovery == 0.35
    assert plan.starter_profile_key == "birmingham-dark"
    assert plan.starter_profile_label == "Birmingham Dark"
    assert plan.pad_count == 12
    assert plan.event_count == 132
    assert plan.machine_select_event_count == 12
    assert plan.engine_source_event_count == 48
    assert plan.starter_parameter_event_count == 72
    assert plan.blocked_pad_count == 0
    assert plan.source_starter_covered_pad_count == 12
    assert plan.source_starter_skipped_pad_count == 0


def test_twelve_pad_rytm_runtime_plan_preserves_pad_event_order():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        build_twelve_pad_rytm_runtime_plan,
    )

    plan = build_twelve_pad_rytm_runtime_plan(
        "Birmingham dark techno",
        discovery=0.35,
        profile="birmingham-dark",
    )

    pad5 = plan.pads[4]
    assert pad5.pad == 5
    assert pad5.role_label == "BT / Bass tom"
    assert pad5.machine_key == "bt_classic"
    assert pad5.machine_label == "BT Classic"
    assert pad5.source_starter_status == "covered"
    assert len(pad5.events) == 11
    assert [event.event_role for event in pad5.events[:6]] == [
        "machine_select",
        "engine_source_parameter",
        "engine_source_parameter",
        "engine_source_parameter",
        "engine_source_parameter",
        "starter_parameter",
    ]
    assert pad5.events[0].cc == 15
    assert pad5.events[0].value == 7
    assert pad5.events[1].parameter_name == "SRC Slot 1"
    assert pad5.events[1].cc == 16
    assert pad5.events[1].value == 100
    assert pad5.events[5].parameter_name == "FLT Frequency"
    assert pad5.events[5].cc == 74
    assert pad5.events[5].value == 108


def test_twelve_pad_rytm_runtime_keeps_pad10_on_open_hat_lane():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        build_twelve_pad_rytm_runtime_plan,
    )

    plan = build_twelve_pad_rytm_runtime_plan(
        "schranz industrial hard techno",
        discovery=0.9,
        profile="birmingham-dark",
    )

    pad10 = plan.pads[9]
    assert pad10.pad == 10
    assert pad10.role_key == "oh_track_open_hihat"
    assert pad10.role_label == "OH / Open hihat"
    assert pad10.machine_key in {"oh_classic", "oh_metallic", "hh_basic", "hh_lab"}
    assert pad10.machine_key != "xt_classic"
    assert pad10.machine_label != "XT Classic"


def test_twelve_pad_rytm_runtime_mock_capture_has_metadata_and_full_stream():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        build_twelve_pad_rytm_runtime_plan,
        capture_twelve_pad_rytm_runtime_mock_messages,
    )

    plan = build_twelve_pad_rytm_runtime_plan("Birmingham dark techno", discovery=0.35)
    sender = capture_twelve_pad_rytm_runtime_mock_messages(plan)

    assert len(sender.sent_messages) == 132
    assert sender.sent_messages[0].control == 15
    assert sender.sent_messages[0].metadata["source_kind"] == "twelve_pad_rytm_runtime"
    assert sender.sent_messages[0].metadata["style_prompt"] == "Birmingham dark techno"
    assert sender.sent_messages[0].metadata["starter_profile_key"] == "birmingham-dark"
    assert sender.sent_messages[0].metadata["source_starter_status"] == "covered"
    assert sender.sent_messages[0].metadata["mock_only"] is True
    assert sender.sent_messages[0].metadata["sends_real_midi"] is False
    pad5_source = sender.sent_messages[45]
    assert pad5_source.metadata["pad"] == 5
    assert pad5_source.metadata["event_role"] == "engine_source_parameter"
    assert pad5_source.metadata["parameter"] == "SRC Slot 1"
    assert pad5_source.control == 16
    assert pad5_source.value == 100


def test_twelve_pad_rytm_runtime_mock_capture_matches_guarded_source_starter_stream():
    from rytm_randomizer.essence.rytm_engine_cycle_guarded_sender import (
        build_rytm_engine_cycle_guarded_send_dry_run,
    )
    from rytm_randomizer.essence.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
    from rytm_randomizer.essence.rytm_engine_cycle_starter_profiles import (
        build_rytm_engine_cycle_starter_plan,
    )
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        build_twelve_pad_rytm_runtime_plan,
        capture_twelve_pad_rytm_runtime_mock_messages,
    )

    runtime_sender = capture_twelve_pad_rytm_runtime_mock_messages(
        build_twelve_pad_rytm_runtime_plan(
            "Birmingham dark techno",
            discovery=0.35,
        )
    )
    starter_plan = build_rytm_engine_cycle_starter_plan(
        build_rytm_engine_cycle_plan("Birmingham dark techno", discovery=0.35),
        profile="auto",
        include_engine_source_starters=True,
    )
    guarded_result = build_rytm_engine_cycle_guarded_send_dry_run(starter_plan)

    runtime_stream = [
        (
            message.channel,
            message.control,
            message.value,
            message.metadata["event_role"],
        )
        for message in runtime_sender.sent_messages
    ]
    guarded_stream = [
        (
            message.channel,
            message.control,
            message.value,
            message.metadata["event_role"],
        )
        for message in guarded_result.emitted_messages
    ]

    assert len(runtime_stream) == 132
    assert runtime_stream == guarded_stream


def test_twelve_pad_rytm_runtime_plan_can_filter_to_one_pad():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        build_twelve_pad_rytm_runtime_plan,
        filter_twelve_pad_rytm_runtime_plan_to_pad,
    )

    full_plan = build_twelve_pad_rytm_runtime_plan(
        "Birmingham dark techno",
        discovery=0.35,
    )

    pad10_plan = filter_twelve_pad_rytm_runtime_plan_to_pad(full_plan, pad=10)

    assert pad10_plan.pad_count == 1
    assert pad10_plan.event_count == 11
    assert pad10_plan.machine_select_event_count == 1
    assert pad10_plan.engine_source_event_count == 4
    assert pad10_plan.starter_parameter_event_count == 6
    assert pad10_plan.source_starter_covered_pad_count == 1
    assert pad10_plan.source_starter_skipped_pad_count == 0
    assert pad10_plan.pads[0].pad == 10
    assert pad10_plan.pads[0].role_label == "OH / Open hihat"
    assert {event.pad for event in pad10_plan.pads[0].events} == {10}

    with pytest.raises(ValueError, match="Pad must be between 1 and 12"):
        filter_twelve_pad_rytm_runtime_plan_to_pad(full_plan, pad=13)


def test_build_twelve_pad_rytm_runtime_plan_accepts_one_pad_target():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        build_twelve_pad_rytm_runtime_plan,
    )

    plan = build_twelve_pad_rytm_runtime_plan(
        "Birmingham dark techno",
        discovery=0.35,
        pad=10,
    )

    assert plan.pad_count == 1
    assert plan.event_count == 11
    assert plan.pads[0].pad == 10
    assert plan.pads[0].role_label == "OH / Open hihat"


def test_twelve_pad_rytm_runtime_report_explains_counts_stream_and_safety():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        build_twelve_pad_rytm_runtime_plan,
        format_twelve_pad_rytm_runtime_report,
    )

    plan = build_twelve_pad_rytm_runtime_plan("Birmingham dark techno", discovery=0.35)
    report = "\n".join(format_twelve_pad_rytm_runtime_report(plan))

    assert "RytmRandomizer passive Twelve Pad Rytm Runtime Report" in report
    assert "Style prompt: Birmingham dark techno" in report
    assert "Starter profile: Birmingham Dark / birmingham-dark" in report
    assert "Planned pads: 12" in report
    assert "Blocked pads: 0" in report
    assert "Runtime messages: 132" in report
    assert "Source-starter covered pads: 12" in report
    assert "Source-starter skipped pads: 0" in report
    assert (
        "- Pad 5 / BT / Bass tom / BT Classic: " "11 message(s), source starters covered"
    ) in report
    assert "- Pad 5 / ch 5 wire 4 / machine_select / CC15 -> 7 / BT Classic" in report
    assert "- Pad 5 / ch 5 wire 4 / engine_source_parameter / SRC Slot 1 CC16 -> 100" in report
    assert "- Pad 5 / ch 5 wire 4 / starter_parameter / FLT Frequency CC74 -> 108" in report
    assert "- engine-source starters are enabled by default for this runtime report" in report
    assert "- no MIDI sending" in report
    assert "- no hardware mutation" in report


def test_twelve_pad_rytm_runtime_error_report_is_safe():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        format_twelve_pad_rytm_runtime_error,
    )

    report = "\n".join(format_twelve_pad_rytm_runtime_error("bad style"))

    assert "RytmRandomizer passive Twelve Pad Rytm Runtime Report" in report
    assert "Found: False" in report
    assert "bad style. No MIDI was sent. No command executed." in report
    assert "- no MIDI sending" in report


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_twelve_pad_rytm_runtime_report_cli_accepts_style_discovery_and_profile():
    result = run_cli(
        "twelve-pad-rytm-runtime-report",
        "--style",
        "Birmingham dark techno",
        "--discovery",
        "0.35",
        "--profile",
        "auto",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Twelve Pad Rytm Runtime Report" in result.stdout
    assert "Style prompt: Birmingham dark techno" in result.stdout
    assert "Starter profile: Birmingham Dark / birmingham-dark" in result.stdout
    assert "Runtime messages: 132" in result.stdout
    assert "engine_source_parameter / SRC Slot 1 CC16 -> 100" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_twelve_pad_rytm_runtime_report_cli_accepts_runtime_pad():
    result = run_cli(
        "twelve-pad-rytm-runtime-report",
        "--style",
        "Birmingham dark techno",
        "--discovery",
        "0.35",
        "--runtime-pad",
        "10",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Twelve Pad Rytm Runtime Report" in result.stdout
    assert "Planned pads: 1" in result.stdout
    assert "Runtime messages: 11" in result.stdout
    assert "Source-starter covered pads: 1" in result.stdout
    assert "- Pad 10 / OH / Open hihat" in result.stdout
    assert "- Pad 10 / ch 10 wire 9" in result.stdout
    assert "- Pad 9 / ch 9 wire 8" not in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_twelve_pad_rytm_runtime_report_cli_rejects_bad_runtime_pad():
    result = run_cli(
        "twelve-pad-rytm-runtime-report",
        "--style",
        "Birmingham dark techno",
        "--runtime-pad",
        "13",
    )

    assert result.returncode == 1
    assert "Pad must be between 1 and 12" in result.stderr
    assert "No MIDI was sent" in result.stderr
    assert result.stdout == ""


def test_twelve_pad_rytm_runtime_report_cli_rejects_invalid_discovery():
    result = run_cli(
        "twelve-pad-rytm-runtime-report",
        "--style",
        "Birmingham dark techno",
        "--discovery",
        "2",
    )

    assert result.returncode == 1
    assert "RytmRandomizer passive Twelve Pad Rytm Runtime Report" in result.stderr
    assert "Discovery must be between 0.0 and 1.0" in result.stderr
    assert "No MIDI was sent" in result.stderr
    assert result.stdout == ""


def test_twelve_pad_rytm_runtime_report_cli_main_accepts_runtime_pad(capsys):
    from rytm_randomizer import cli

    result = cli.main(
        [
            "twelve-pad-rytm-runtime-report",
            "--style",
            "Birmingham dark techno",
            "--discovery",
            "0.35",
            "--runtime-pad",
            "10",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "RytmRandomizer passive Twelve Pad Rytm Runtime Report" in captured.out
    assert "Planned pads: 1" in captured.out
    assert "Runtime messages: 11" in captured.out
    assert "- Pad 10 / OH / Open hihat" in captured.out
    assert captured.err == ""


def test_twelve_pad_rytm_runtime_report_cli_main_rejects_usage_error(capsys):
    from rytm_randomizer import cli

    result = cli.main(["twelve-pad-rytm-runtime-report", "--style"])

    captured = capsys.readouterr()
    assert result == 2
    assert "Usage:" in captured.err
    assert captured.out == ""


def test_twelve_pad_rytm_runtime_report_cli_main_rejects_bad_runtime_pad_value(capsys):
    from rytm_randomizer import cli

    result = cli.main(
        [
            "twelve-pad-rytm-runtime-report",
            "--style",
            "Birmingham dark techno",
            "--runtime-pad",
            "hat",
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert "Pad must be between 1 and 12" in captured.err
    assert "No MIDI was sent" in captured.err
    assert captured.out == ""
