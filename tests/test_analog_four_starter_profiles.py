import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_analog_four_starter_profiles_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four_starter_profiles; "
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


def test_analog_four_starter_profile_lookup_accepts_aliases():
    from rytm_randomizer.analog_four_starter_profiles import (
        get_analog_four_starter_profile,
        list_analog_four_starter_profiles,
    )

    profiles = list_analog_four_starter_profiles()
    birmingham = get_analog_four_starter_profile("birmingham_dark")
    peak_time = get_analog_four_starter_profile("peak time")

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


def test_unknown_analog_four_starter_profile_lists_valid_choices():
    from rytm_randomizer.analog_four_starter_profiles import get_analog_four_starter_profile

    try:
        get_analog_four_starter_profile("ambient-clouds")
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected unknown profile to fail")

    assert "Unknown Analog Four starter profile: ambient-clouds" in message
    assert "balanced, birmingham-dark, detroit-classic, peak-time" in message
