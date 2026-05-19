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


def test_importing_rytm_engine_cycle_starter_profiles_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.essence.rytm_engine_cycle_starter_profiles; "
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


def test_rytm_starter_profile_lookup_accepts_aliases():
    from rytm_randomizer.essence.rytm_engine_cycle_starter_profiles import (
        get_rytm_starter_profile,
        list_rytm_starter_profiles,
    )

    profiles = list_rytm_starter_profiles()
    birmingham = get_rytm_starter_profile("birmingham_dark")
    peak_time = get_rytm_starter_profile("peak time")

    assert tuple(profile.key for profile in profiles) == (
        "balanced",
        "birmingham-dark",
        "detroit-classic",
        "peak-time",
    )
    assert birmingham.key == "birmingham-dark"
    assert birmingham.label == "Birmingham Dark"
    assert peak_time.key == "peak-time"
    assert peak_time.label == "Peak Time"


def test_unknown_rytm_starter_profile_lists_valid_choices():
    from rytm_randomizer.essence.rytm_engine_cycle_starter_profiles import get_rytm_starter_profile

    try:
        get_rytm_starter_profile("ambient-clouds")
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected unknown profile to fail")

    assert "Unknown Rytm starter profile: ambient-clouds" in message
    assert "balanced, birmingham-dark, detroit-classic, peak-time" in message


def test_rytm_starter_profile_auto_selects_from_style_prompt():
    from rytm_randomizer.essence.rytm_engine_cycle_starter_profiles import (
        choose_rytm_starter_profile_for_style,
    )

    assert choose_rytm_starter_profile_for_style("Birmingham dark techno").key == "birmingham-dark"
    assert choose_rytm_starter_profile_for_style("classic Detroit techno").key == "detroit-classic"
    assert choose_rytm_starter_profile_for_style("schranz peak time").key == "peak-time"
    assert choose_rytm_starter_profile_for_style("broken electro sketches").key == "balanced"


def test_engine_cycle_starter_plan_accepts_auto_profile():
    from rytm_randomizer.essence.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
    from rytm_randomizer.essence.rytm_engine_cycle_starter_profiles import (
        build_rytm_engine_cycle_starter_plan,
    )

    engine_plan = build_rytm_engine_cycle_plan("classic Detroit techno", discovery=0.45)
    starter_plan = build_rytm_engine_cycle_starter_plan(engine_plan, profile="auto")

    assert starter_plan.starter_profile_key == "detroit-classic"
    assert starter_plan.starter_profile_label == "Detroit Classic"
    assert starter_plan.event_count == 84


def test_engine_cycle_starter_plan_adds_common_safe_shaping_to_all_12_pads():
    from rytm_randomizer.essence.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
    from rytm_randomizer.essence.rytm_engine_cycle_starter_profiles import (
        build_rytm_engine_cycle_starter_plan,
    )

    engine_plan = build_rytm_engine_cycle_plan("Birmingham dark techno", discovery=0.35)
    starter_plan = build_rytm_engine_cycle_starter_plan(
        engine_plan,
        profile="birmingham_dark",
    )

    assert starter_plan.style_prompt == "Birmingham dark techno"
    assert starter_plan.discovery == 0.35
    assert starter_plan.starter_profile_key == "birmingham-dark"
    assert starter_plan.starter_profile_label == "Birmingham Dark"
    assert starter_plan.pad_count == 12
    assert starter_plan.event_count == 84
    assert starter_plan.starter_parameter_event_count == 72

    pad5 = starter_plan.pads[4]
    assert pad5.pad == 5
    assert pad5.role_label == "BT / Bass tom"
    assert pad5.machine_key == "bt_classic"
    assert pad5.machine_label == "BT Classic"
    assert len(pad5.events) == 7
    assert pad5.events[0].event_role == "machine_select"
    assert pad5.events[0].cc == 15
    assert pad5.events[0].value == 7

    starter_events = {event.parameter_name: event for event in pad5.events[1:]}
    assert starter_events["FLT Frequency"].cc == 74
    assert starter_events["FLT Frequency"].value == 108
    assert starter_events["AMP Decay"].cc == 80
    assert starter_events["AMP Decay"].value == 34
    assert starter_events["AMP Pan"].cc == 10
    assert starter_events["AMP Pan"].value == 58


def test_engine_cycle_starter_plan_can_include_engine_source_starters():
    from rytm_randomizer.essence.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
    from rytm_randomizer.essence.rytm_engine_cycle_starter_profiles import (
        build_rytm_engine_cycle_starter_plan,
    )

    engine_plan = build_rytm_engine_cycle_plan("Birmingham dark techno", discovery=0.35)
    starter_plan = build_rytm_engine_cycle_starter_plan(
        engine_plan,
        profile="birmingham-dark",
        include_engine_source_starters=True,
    )

    assert starter_plan.event_count == 132
    assert starter_plan.engine_source_event_count == 48
    assert starter_plan.starter_parameter_event_count == 72

    pad5 = starter_plan.pads[4]
    assert len(pad5.events) == 11
    assert pad5.events[0].event_role == "machine_select"
    assert pad5.events[1].event_role == "engine_source_parameter"
    assert pad5.events[1].parameter_name == "SRC Slot 1"
    assert pad5.events[1].cc == 16
    assert pad5.events[1].value == 100
    assert pad5.events[4].parameter_name == "SRC Slot 8"
    assert pad5.events[4].cc == 23
    assert pad5.events[4].value == 72
    assert pad5.events[5].event_role == "starter_parameter"
    assert pad5.events[5].parameter_name == "FLT Frequency"
    assert pad5.events[5].cc == 74
    assert pad5.events[5].value == 108


def test_engine_source_starters_cover_all_os172_matrix_machine_slots():
    from rytm_randomizer.essence.rytm_12_pad_engine_matrix import (
        build_rytm_12_pad_engine_matrix,
    )
    from rytm_randomizer.essence.rytm_engine_cycle_starter_profiles import (
        ENGINE_SOURCE_STARTERS,
    )

    matrix = build_rytm_12_pad_engine_matrix()

    assert matrix.source_starter_covered_slot_count == 116
    assert matrix.source_starter_pending_slot_count == 0
    assert set(ENGINE_SOURCE_STARTERS) >= {
        "bd_sharp",
        "bd_fm",
        "bd_plastic",
        "bd_silky",
        "sd_classic",
        "sd_fm",
        "sy_raw",
        "sd_natural",
        "sd_acoustic",
    }
    assert ENGINE_SOURCE_STARTERS["bd_fm"][:4] == (
        ("SRC Level", 16, 100),
        ("SRC Tune", 17, 60),
        ("SRC Sweep Time", 18, 82),
        ("SRC FM Decay", 19, 38),
    )
    assert ENGINE_SOURCE_STARTERS["sy_raw"][:4] == (
        ("SRC Level", 16, 100),
        ("SRC Tune", 17, 69),
        ("SRC Detune", 18, 23),
        ("SRC Noise Level", 19, 5),
    )


def test_engine_cycle_starter_plan_can_filter_to_one_runtime_pad():
    from rytm_randomizer.essence.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
    from rytm_randomizer.essence.rytm_engine_cycle_starter_profiles import (
        build_rytm_engine_cycle_starter_plan,
        filter_rytm_engine_cycle_starter_plan_to_pad,
    )

    starter_plan = build_rytm_engine_cycle_starter_plan(
        build_rytm_engine_cycle_plan("Birmingham dark techno", discovery=0.35),
        profile="auto",
        include_engine_source_starters=True,
    )

    pad10_plan = filter_rytm_engine_cycle_starter_plan_to_pad(starter_plan, pad=10)

    assert pad10_plan.pad_count == 1
    assert pad10_plan.event_count == 11
    assert pad10_plan.machine_select_event_count == 1
    assert pad10_plan.engine_source_event_count == 4
    assert pad10_plan.starter_parameter_event_count == 6
    assert pad10_plan.pads[0].pad == 10
    assert pad10_plan.pads[0].role_label == "OH / Open hihat"
    assert {event.pad for event in pad10_plan.pads[0].events} == {10}

    with pytest.raises(ValueError, match="Pad must be between 1 and 12"):
        filter_rytm_engine_cycle_starter_plan_to_pad(starter_plan, pad=13)


def test_engine_cycle_starter_mock_capture_emits_machine_select_then_shaping():
    from rytm_randomizer.essence.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
    from rytm_randomizer.essence.rytm_engine_cycle_starter_profiles import (
        build_rytm_engine_cycle_starter_plan,
        capture_rytm_engine_cycle_starter_mock_messages,
    )

    engine_plan = build_rytm_engine_cycle_plan("Birmingham dark techno", discovery=0.35)
    starter_plan = build_rytm_engine_cycle_starter_plan(engine_plan, profile="birmingham-dark")
    sender = capture_rytm_engine_cycle_starter_mock_messages(starter_plan)

    assert len(sender.sent_messages) == 84
    pad5_machine_select = sender.sent_messages[28]
    pad5_frequency = sender.sent_messages[29]
    assert pad5_machine_select.channel == 4
    assert pad5_machine_select.control == 15
    assert pad5_machine_select.value == 7
    assert pad5_machine_select.metadata["event_role"] == "machine_select"
    assert pad5_machine_select.metadata["machine_key"] == "bt_classic"
    assert pad5_frequency.channel == 4
    assert pad5_frequency.control == 74
    assert pad5_frequency.value == 108
    assert pad5_frequency.metadata["event_role"] == "starter_parameter"
    assert pad5_frequency.metadata["parameter"] == "FLT Frequency"
    assert pad5_frequency.metadata["starter_profile_key"] == "birmingham-dark"
    assert pad5_frequency.metadata["mock_only"] is True
    assert pad5_frequency.metadata["sends_real_midi"] is False


def test_engine_cycle_starter_report_includes_profile_preview_and_safety():
    from rytm_randomizer.essence.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
    from rytm_randomizer.essence.rytm_engine_cycle_starter_profiles import (
        build_rytm_engine_cycle_starter_plan,
        format_rytm_engine_cycle_starter_plan_report,
    )

    engine_plan = build_rytm_engine_cycle_plan("Birmingham dark techno", discovery=0.35)
    starter_plan = build_rytm_engine_cycle_starter_plan(engine_plan, profile="birmingham-dark")
    report = format_rytm_engine_cycle_starter_plan_report(starter_plan)

    assert report[0] == "RytmRandomizer passive Rytm Engine Cycle Starter Plan Report"
    assert "Style prompt: Birmingham dark techno" in report
    assert "Starter profile: Birmingham Dark / birmingham-dark" in report
    assert "Planned pads: 12" in report
    assert "Starter messages: 84" in report
    assert "- Pad 5 / BT / Bass tom / BT Classic: 7 message(s)" in report
    assert "- Pad 5 / ch 5 wire 4 / machine_select / CC15 -> 7 / BT Classic" in report
    assert "- Pad 5 / ch 5 wire 4 / starter_parameter / FLT Frequency CC74 -> 108" in report
    assert "- common filter/amp starter values only" in report
    assert "- no MIDI sending" in report


def test_engine_cycle_starter_report_includes_engine_source_preview_when_enabled():
    from rytm_randomizer.essence.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
    from rytm_randomizer.essence.rytm_engine_cycle_starter_profiles import (
        build_rytm_engine_cycle_starter_plan,
        format_rytm_engine_cycle_starter_plan_report,
    )

    engine_plan = build_rytm_engine_cycle_plan("Birmingham dark techno", discovery=0.35)
    starter_plan = build_rytm_engine_cycle_starter_plan(
        engine_plan,
        profile="birmingham-dark",
        include_engine_source_starters=True,
    )
    report = format_rytm_engine_cycle_starter_plan_report(starter_plan)

    assert "Engine-source parameter messages: 48" in report
    assert "Starter messages: 132" in report
    assert "- Pad 5 / BT / Bass tom / BT Classic: 11 message(s)" in report
    assert "- Pad 5 / ch 5 wire 4 / engine_source_parameter / SRC Slot 1 CC16 -> 100" in report
    assert "- engine-source starters use mapped SRC slots only" in report


def test_rytm_engine_cycle_starter_plan_report_cli_accepts_style_and_profile():
    result = run_cli(
        "rytm-engine-cycle-starter-plan-report",
        "--style",
        "Birmingham dark techno",
        "--discovery",
        "0.35",
        "--profile",
        "birmingham-dark",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm Engine Cycle Starter Plan Report" in result.stdout
    assert "Style prompt: Birmingham dark techno" in result.stdout
    assert "Starter profile: Birmingham Dark / birmingham-dark" in result.stdout
    assert "Starter messages: 84" in result.stdout
    assert "Pad 5 / BT / Bass tom / BT Classic: 7 message(s)" in result.stdout
    assert "starter_parameter / FLT Frequency CC74 -> 108" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_rytm_engine_cycle_starter_plan_report_cli_accepts_auto_profile():
    result = run_cli(
        "rytm-engine-cycle-starter-plan-report",
        "--style",
        "schranz peak time",
        "--profile",
        "auto",
    )

    assert result.returncode == 0
    assert "Starter profile: Peak Time / peak-time" in result.stdout
    assert "Starter messages: 84" in result.stdout
    assert result.stderr == ""
