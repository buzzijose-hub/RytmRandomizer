import subprocess
import sys
from pathlib import Path

import pytest

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


def test_importing_essence_plan_report_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.essence_plan_report; "
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


def test_parse_essence_tags_normalizes_comma_separated_input():
    from rytm_randomizer.essence_plan_report import parse_essence_tags

    assert parse_essence_tags(" Metallic, bell, Driving ,, repetition ") == (
        "metallic",
        "bell",
        "driving",
        "repetition",
    )


def test_invalid_discovery_value_fails_safely():
    from rytm_randomizer.essence_plan_report import parse_discovery_value

    with pytest.raises(ValueError, match="Discovery must be between 0.0 and 1.0"):
        parse_discovery_value("1.5")

    with pytest.raises(ValueError, match="Discovery must be a number"):
        parse_discovery_value("wide")


def test_format_essence_plan_report_shows_12_pad_plan():
    from rytm_randomizer.essence_plan_report import format_essence_plan_report

    report = format_essence_plan_report(
        tags=("metallic", "bell", "driving", "repetition"),
        discovery=0.35,
    )

    assert report[0] == "RytmRandomizer passive Essence Plan Report"
    assert "Essence tags: metallic, bell, driving, repetition" in report
    assert "Discovery: 0.35" in report
    assert "Candidate mode: mapped mutable engines only" in report
    assert "12-pad role plan:" in report
    assert any(line.startswith("- Pad 1 / Main kick foundation:") for line in report)
    assert any(line.startswith("- Pad 3 / Metallic motif:") for line in report)
    assert any(line.startswith("- Pad 9 / Tonal bell accent:") for line in report)
    assert any("BD FM [mutable]" in line for line in report)
    assert any("SD FM [mutable]" in line for line in report)
    assert all("SY Chip [future]" not in line for line in report)
    assert "- no MIDI sending" in report
    assert "- no hardware mutation" in report


def test_discovery_report_marks_future_inventory_candidates():
    from rytm_randomizer.essence_plan_report import format_essence_plan_report

    report = format_essence_plan_report(
        tags=("metallic", "bell", "digital", "repetition"),
        discovery=1.0,
    )

    assert "Candidate mode: mapped engines plus future inventory candidates" in report
    assert any("SY Chip [future]" in line for line in report)
    assert any("CB Classic [future]" in line for line in report)
    assert "- no Pads 5-12 runtime mutation" in report


def test_essence_plan_report_cli_reads_tags_without_hardware():
    result = run_cli(
        "essence-plan-report",
        "--tags",
        "metallic,bell,driving,repetition",
        "--discovery",
        "0.35",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Essence Plan Report" in result.stdout
    assert "Essence tags: metallic, bell, driving, repetition" in result.stdout
    assert "Discovery: 0.35" in result.stdout
    assert "Pad 3 / Metallic motif" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_essence_plan_report_cli_derives_tags_from_description_without_hardware():
    result = run_cli(
        "essence-plan-report",
        "--description",
        "metallic bell pressure driving repetition Detroit techno",
        "--discovery",
        "1.0",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Essence Plan Report" in result.stdout
    assert "Essence tags: metallic, bell, detroit, driving, pressure, repetition" in result.stdout
    assert "Discovery: 1.00" in result.stdout
    assert "SY Chip [future]" in result.stdout
    assert "- no audio file analysis" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_essence_plan_report_cli_invalid_discovery_fails_safely():
    result = run_cli(
        "essence-plan-report",
        "--tags",
        "metallic,bell",
        "--discovery",
        "1.5",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == "\n".join(
        [
            "RytmRandomizer passive Essence Plan Report",
            "Found: False",
            "Message: Discovery must be between 0.0 and 1.0. No MIDI was sent. No command executed.",
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )


def test_essence_plan_report_cli_imports_no_real_midi_libraries():
    script = "\n".join(
        [
            "import runpy",
            "import sys",
            "sys.argv = [",
            "    'rytm_randomizer.cli',",
            "    'essence-plan-report',",
            "    '--description',",
            "    'metallic bell driving repetition',",
            "    '--discovery',",
            "    '0.35',",
            "]",
            "runpy.run_module('rytm_randomizer.cli', run_name='__main__')",
            "assert 'mido' not in sys.modules",
            "assert 'rtmidi' not in sys.modules",
            "assert 'librosa' not in sys.modules",
        ]
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Essence Plan Report" in result.stdout
    assert result.stderr == ""
