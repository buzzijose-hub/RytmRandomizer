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


def test_importing_style_intent_profiles_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.essence.style_intent_profiles; "
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


def test_style_intent_alias_lookup_handles_birmingham_and_schranz():
    from rytm_randomizer.essence.style_intent_profiles import match_style_intent_profiles

    birmingham = match_style_intent_profiles("Birmingham style dark techno")
    schranz = match_style_intent_profiles("hardcore schranz")

    assert tuple(profile.key for profile in birmingham) == (
        "dark_techno",
        "birmingham_techno",
    )
    assert tuple(profile.key for profile in schranz) == ("hardcore", "schranz")


def test_style_intent_derives_ordered_essence_tags():
    from rytm_randomizer.essence.style_intent_profiles import derive_style_intent_tags

    tags = derive_style_intent_tags("broken techno Birmingham dark techno")

    assert tags == (
        "metallic",
        "driving",
        "pressure",
        "repetition",
        "density",
        "low",
        "deep",
        "noise",
        "raw",
        "motion",
        "tension",
        "groove",
    )


def test_build_style_intent_request_uses_profile_discovery_hint():
    from rytm_randomizer.essence.style_intent_profiles import build_style_intent_request

    request = build_style_intent_request("classic Detroit techno")

    assert request.prompt == "classic Detroit techno"
    assert tuple(profile.key for profile in request.matched_profiles) == ("classic_detroit_techno",)
    assert request.discovery == 0.45
    assert request.tags == (
        "bell",
        "detroit",
        "driving",
        "repetition",
        "analog",
        "classic",
        "groove",
    )


def test_build_style_intent_request_accepts_discovery_override():
    from rytm_randomizer.essence.style_intent_profiles import build_style_intent_request

    request = build_style_intent_request("peak time techno", discovery=0.9)

    assert request.discovery == 0.9
    assert tuple(profile.key for profile in request.matched_profiles) == ("peak_time_techno",)


def test_format_style_intent_report_includes_analog_four_future_note_and_plan():
    from rytm_randomizer.essence.style_intent_profiles import format_style_intent_report

    report = format_style_intent_report("Birmingham dark techno")

    assert report[0] == "RytmRandomizer passive Style Intent Report"
    assert "Style prompt: Birmingham dark techno" in report
    assert "Matched profiles: Dark Techno, Birmingham Techno" in report
    assert "Analog Four: future expansion target only; no current A4 mapping" in report
    assert "12-pad style kit plan:" in report
    assert any(line.startswith("- Pad 3 / RS / Rim shot:") for line in report)
    assert "- no MIDI sending" in report
    assert "- no Analog Four runtime support" in report


def test_style_intent_report_cli_runs_without_hardware():
    result = run_cli("style-intent-report", "--style", "Birmingham dark techno")

    assert result.returncode == 0
    assert "RytmRandomizer passive Style Intent Report" in result.stdout
    assert "Matched profiles: Dark Techno, Birmingham Techno" in result.stdout
    assert "Essence tags: metallic, driving, pressure" in result.stdout
    assert "Analog Four: future expansion target only; no current A4 mapping" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_style_intent_report_cli_accepts_discovery_override():
    result = run_cli(
        "style-intent-report",
        "--style",
        "classic Detroit techno",
        "--discovery",
        "0.9",
    )

    assert result.returncode == 0
    assert "Discovery: 0.90" in result.stdout
    assert "SY Chip [future]" in result.stdout
    assert result.stderr == ""


def test_style_intent_report_cli_invalid_discovery_fails_safely():
    result = run_cli(
        "style-intent-report",
        "--style",
        "classic Detroit techno",
        "--discovery",
        "wide",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == "\n".join(
        [
            "RytmRandomizer passive Style Intent Report",
            "Found: False",
            "Message: Discovery must be a number. No MIDI was sent. No command executed.",
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no hardware required",
        ]
    )
