"""Tests for the passive manual feedback packet report."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_build_default_packet_is_passive_and_reviewer_ready() -> None:
    from rytm_randomizer.reports.manual_feedback_packet import (
        build_manual_feedback_packet_report,
    )

    report = build_manual_feedback_packet_report()

    assert report.scenario_key == "full"
    assert report.step_count == 10
    assert report.safety["passive"] is True
    assert report.safety["opens_midi_ports"] is False
    assert report.safety["sends_midi"] is False
    assert report.safety["launches_gui"] is False
    assert "export-model-no-op" in report.blocker_keys
    assert "analyzer-style-extra" in report.blocker_keys
    assert "pad-scope-gap" in report.review_focus_keys
    assert report.replay_commands == (
        "python -m rytm_randomizer.cli manual-feedback-packet-report --scenario full",
        "python -m rytm_randomizer.cli manual-feedback-packet-report --scenario full --json",
    )


def test_profile_scenario_focuses_analyzer_export_and_pad_scope() -> None:
    from rytm_randomizer.reports.manual_feedback_packet import (
        build_manual_feedback_packet_report,
    )

    report = build_manual_feedback_packet_report("profile")
    keys = tuple(step.key for step in report.steps)

    assert report.scenario_key == "profile"
    assert keys == (
        "profile-create-flow",
        "analyzer-style-extra",
        "reference-analysis-result",
        "export-model-no-op",
        "pad-scope-gap",
    )
    assert report.step_count == 5


def test_format_text_report_includes_manual_observation_prompts() -> None:
    from rytm_randomizer.reports.manual_feedback_packet import (
        format_manual_feedback_packet_report,
    )

    lines = format_manual_feedback_packet_report("profile")
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive manual feedback packet"
    assert "Scenario: profile / Profile wizard and analyzer feedback" in lines
    assert "Step analyzer-style-extra / Analyzer dependency gate:" in text
    assert "- Capture: exact missing-extra/error text and whether retry succeeds" in text
    assert "Step export-model-no-op / Export model action:" in text
    assert "- Capture: screenshot plus backend/console output after pressing Export Model" in text
    assert "Step pad-scope-gap / Pad/device scope expectation:" in text
    assert (
        "- Expected: Rytm 12-pad path is tracked separately from current 4-pad mock surface" in text
    )
    assert "- sends_midi: False" in lines
    assert "Source: rytm_randomizer.reports.manual_feedback_packet" in lines


def test_format_json_report_is_deterministic_and_passive() -> None:
    from rytm_randomizer.reports.manual_feedback_packet import (
        format_manual_feedback_packet_report_json,
    )

    first = format_manual_feedback_packet_report_json("hardware")
    second = format_manual_feedback_packet_report_json("hardware")
    payload = json.loads(first)

    assert first == second
    assert payload["scenario"]["key"] == "hardware"
    assert payload["summary"]["step_count"] == 3
    assert payload["safety"]["sends_midi"] is False
    assert payload["steps"][0]["key"] == "hardware-arm-boundary"
    assert payload["steps"][0]["category"] == "hardware"
    assert (
        "manual-feedback-packet-report --scenario hardware --json" in payload["replay_commands"][1]
    )


def test_cli_text_and_json_paths_are_passive() -> None:
    text_result = run_cli("manual-feedback-packet-report", "--scenario", "profile")
    json_result = run_cli("manual-feedback-packet-report", "--scenario", "hardware", "--json")

    assert text_result.returncode == 0
    assert text_result.stderr == ""
    assert "RytmRandomizer passive manual feedback packet" in text_result.stdout
    assert "No MIDI would be sent." in text_result.stdout

    assert json_result.returncode == 0
    assert json_result.stderr == ""
    payload = json.loads(json_result.stdout)
    assert payload["scenario"]["key"] == "hardware"
    assert payload["safety"]["opens_midi_ports"] is False


def test_cli_help_is_registered_for_passive_safety_sweep() -> None:
    result = run_cli("manual-feedback-packet-report", "--help")

    assert result.returncode == 0
    assert result.stderr == ""
    assert "RytmRandomizer passive CLI: manual-feedback-packet-report" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert "no port opening" in result.stdout


def test_cli_rejects_unknown_scenario_safely() -> None:
    result = run_cli("manual-feedback-packet-report", "--scenario", "surprise")

    assert result.returncode == 2
    assert "Usage: python -m rytm_randomizer.cli" in result.stderr
    assert result.stdout == ""


def test_builder_rejects_unknown_scenario_with_known_keys() -> None:
    from rytm_randomizer.reports.manual_feedback_packet import (
        build_manual_feedback_packet_report,
    )

    with pytest.raises(ValueError, match="unknown scenario 'surprise'; expected one of:"):
        build_manual_feedback_packet_report("surprise")


def test_parser_reports_missing_values_and_unknown_arguments() -> None:
    from rytm_randomizer.reports.manual_feedback_packet import (
        MANUAL_FEEDBACK_PACKET_CLI_COMMAND,
    )

    with pytest.raises(ValueError, match="--scenario requires a value"):
        MANUAL_FEEDBACK_PACKET_CLI_COMMAND.args_parser(["--scenario"])

    with pytest.raises(ValueError, match="unknown scenario 'surprise'"):
        MANUAL_FEEDBACK_PACKET_CLI_COMMAND.args_parser(["--scenario", "surprise"])

    with pytest.raises(ValueError, match="unknown argument: --bogus"):
        MANUAL_FEEDBACK_PACKET_CLI_COMMAND.args_parser(["--bogus"])

    assert MANUAL_FEEDBACK_PACKET_CLI_COMMAND.args_parser(["--json"]) == {
        "scenario_key": "full",
        "json_output": True,
    }
    assert MANUAL_FEEDBACK_PACKET_CLI_COMMAND.error_formatter(ValueError("boom")).endswith(
        "Error: boom"
    )


def test_handler_json_and_error_paths_are_in_process(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.reports.manual_feedback_packet import (
        MANUAL_FEEDBACK_PACKET_CLI_COMMAND,
    )

    json_rc = MANUAL_FEEDBACK_PACKET_CLI_COMMAND.handler(
        scenario_key="review",
        json_output=True,
    )
    json_captured = capsys.readouterr()
    payload = json.loads(json_captured.out)

    assert json_rc == 0
    assert json_captured.err == ""
    assert payload["scenario"]["key"] == "review"

    error_rc = MANUAL_FEEDBACK_PACKET_CLI_COMMAND.handler(
        scenario_key="surprise",
        json_output=False,
    )
    error_captured = capsys.readouterr()

    assert error_rc == 2
    assert error_captured.out == ""
    assert "unknown scenario 'surprise'" in error_captured.err


def test_importing_report_module_loads_no_real_midi_modules() -> None:
    code = """
import sys
from rytm_randomizer.reports import manual_feedback_packet
manual_feedback_packet.build_manual_feedback_packet_report()
for module_name in ("mido", "rtmidi", "pythonrtmidi", "rytm_randomizer.real_midi_adapter"):
    assert module_name not in sys.modules, module_name
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
