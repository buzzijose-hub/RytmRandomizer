import subprocess
import sys
from pathlib import Path

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
                "import rytm_randomizer.rytm_engine_cycle_starter_profiles; "
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
    from rytm_randomizer.rytm_engine_cycle_starter_profiles import (
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
    from rytm_randomizer.rytm_engine_cycle_starter_profiles import get_rytm_starter_profile

    try:
        get_rytm_starter_profile("ambient-clouds")
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected unknown profile to fail")

    assert "Unknown Rytm starter profile: ambient-clouds" in message
    assert "balanced, birmingham-dark, detroit-classic, peak-time" in message


def test_engine_cycle_starter_plan_adds_common_safe_shaping_to_all_12_pads():
    from rytm_randomizer.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
    from rytm_randomizer.rytm_engine_cycle_starter_profiles import (
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
    assert pad5.role_label == "Closed hat pulse"
    assert pad5.machine_key == "ch_metallic"
    assert pad5.machine_label == "CH Metallic"
    assert len(pad5.events) == 7
    assert pad5.events[0].event_role == "machine_select"
    assert pad5.events[0].cc == 15
    assert pad5.events[0].value == 17

    starter_events = {event.parameter_name: event for event in pad5.events[1:]}
    assert starter_events["FLT Frequency"].cc == 74
    assert starter_events["FLT Frequency"].value == 108
    assert starter_events["AMP Decay"].cc == 80
    assert starter_events["AMP Decay"].value == 34
    assert starter_events["AMP Pan"].cc == 10
    assert starter_events["AMP Pan"].value == 58


def test_engine_cycle_starter_mock_capture_emits_machine_select_then_shaping():
    from rytm_randomizer.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
    from rytm_randomizer.rytm_engine_cycle_starter_profiles import (
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
    assert pad5_machine_select.value == 17
    assert pad5_machine_select.metadata["event_role"] == "machine_select"
    assert pad5_machine_select.metadata["machine_key"] == "ch_metallic"
    assert pad5_frequency.channel == 4
    assert pad5_frequency.control == 74
    assert pad5_frequency.value == 108
    assert pad5_frequency.metadata["event_role"] == "starter_parameter"
    assert pad5_frequency.metadata["parameter"] == "FLT Frequency"
    assert pad5_frequency.metadata["starter_profile_key"] == "birmingham-dark"
    assert pad5_frequency.metadata["mock_only"] is True
    assert pad5_frequency.metadata["sends_real_midi"] is False


def test_engine_cycle_starter_report_includes_profile_preview_and_safety():
    from rytm_randomizer.rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
    from rytm_randomizer.rytm_engine_cycle_starter_profiles import (
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
    assert "- Pad 5 / Closed hat pulse / CH Metallic: 7 message(s)" in report
    assert (
        "- Pad 5 / ch 5 wire 4 / machine_select / CC15 -> 17 / CH Metallic"
        in report
    )
    assert (
        "- Pad 5 / ch 5 wire 4 / starter_parameter / FLT Frequency CC74 -> 108"
        in report
    )
    assert "- common filter/amp starter values only" in report
    assert "- no MIDI sending" in report


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
    assert "Pad 5 / Closed hat pulse / CH Metallic: 7 message(s)" in result.stdout
    assert "starter_parameter / FLT Frequency CC74 -> 108" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
