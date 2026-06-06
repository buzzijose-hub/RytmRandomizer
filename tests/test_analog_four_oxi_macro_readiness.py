"""Tests for passive Analog Four OXI macro readiness reports."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_a4_macro_readiness_prints_nothing() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rytm_randomizer.reports.analog_four_oxi_macro_readiness",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_a4_macro_readiness_defaults_to_passive_cc_ready_rows() -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_readiness import (
        build_analog_four_oxi_macro_readiness_report,
    )

    report = build_analog_four_oxi_macro_readiness_report(
        "hard-groove",
        seed=7,
        intensity=4,
    )

    assert report.title == "RytmRandomizer passive Analog Four OXI macro readiness"
    assert report.macro_name == "hard-groove"
    assert report.readiness == "review-ready"
    assert report.opens_ports is False
    assert report.sends_midi is False
    assert report.hardware_required is False
    assert report.operator_present_required is True
    assert report.ready_count == len(report.events)
    assert report.review_count == 0
    assert report.blocked_count == 0
    assert {event.status for event in report.events} == {"cc-ready"}
    assert all(0 <= event.value <= 127 for event in report.events)
    assert all(event.channel == event.track - 1 for event in report.events)
    assert all(
        event.validation_command.startswith("python -m rytm_randomizer.app --arm --a4-send-param")
        for event in report.events
    )
    assert all("--parameter " in event.validation_command for event in report.events)


def test_a4_macro_readiness_format_and_json_are_deterministic() -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_readiness import (
        build_analog_four_oxi_macro_readiness_payload,
        build_analog_four_oxi_macro_readiness_report,
        format_analog_four_oxi_macro_readiness_report,
    )

    report = build_analog_four_oxi_macro_readiness_report("dub-pressure", seed=3, intensity=5)
    text = "\n".join(format_analog_four_oxi_macro_readiness_report(report, event_limit=2))
    payload = build_analog_four_oxi_macro_readiness_payload(report, event_limit=2)

    assert text.startswith("RytmRandomizer passive Analog Four OXI macro readiness\n")
    assert "Macro: dub-pressure" in text
    assert "Readiness: review-ready" in text
    assert "Shown events: 2" in text
    assert "Validation commands:" in text
    assert "A4 full macro SEND remains unimplemented" in text
    assert "Source: rytm_randomizer.reports.analog_four_oxi_macro_readiness" in text
    assert "In-memory only: True" in text
    assert payload["title"] == "RytmRandomizer passive Analog Four OXI macro readiness"
    assert payload["macro_name"] == "dub-pressure"
    assert payload["shown_count"] == 2
    assert payload["truncated_count"] == report.event_count - 2
    assert payload["events"][0]["status"] == "cc-ready"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        build_analog_four_oxi_macro_readiness_payload(report, event_limit=2),
        sort_keys=True,
    )


def test_a4_macro_readiness_payload_can_include_all_events() -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_readiness import (
        build_analog_four_oxi_macro_readiness_payload,
        build_analog_four_oxi_macro_readiness_report,
    )

    report = build_analog_four_oxi_macro_readiness_report("industrial-transition")
    payload = build_analog_four_oxi_macro_readiness_payload(report, event_limit=0)

    assert payload["shown_count"] == report.event_count
    assert payload["truncated_count"] == 0
    assert len(payload["events"]) == report.event_count
    assert payload["operator_present_required"] is True
    assert "operator-present validation commands only" in payload["safety"]


def test_a4_macro_readiness_rejects_bad_event_limit() -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_readiness import (
        build_analog_four_oxi_macro_readiness_report,
        format_analog_four_oxi_macro_readiness_report,
    )

    report = build_analog_four_oxi_macro_readiness_report()

    with pytest.raises(ValueError, match="event_limit must be >= 0"):
        format_analog_four_oxi_macro_readiness_report(report, event_limit=-1)


def test_a4_macro_readiness_cli_parser_and_handler(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_readiness import (
        ANALOG_FOUR_OXI_MACRO_READINESS_CLI_COMMAND,
    )

    parsed = ANALOG_FOUR_OXI_MACRO_READINESS_CLI_COMMAND.args_parser(
        ["industrial-transition", "--seed", "8", "--intensity", "6", "--limit", "1"]
    )

    assert parsed == {
        "macro_name": "industrial-transition",
        "seed": 8,
        "intensity": 6,
        "event_limit": 1,
        "json_output": False,
    }
    assert ANALOG_FOUR_OXI_MACRO_READINESS_CLI_COMMAND.handler(**parsed) == 0
    assert "Macro: industrial-transition" in capsys.readouterr().out


def test_a4_macro_readiness_cli_json_mode(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    assert (
        main(
            [
                "analog-four-oxi-macro-readiness-report",
                "hard-groove",
                "--seed",
                "1",
                "--intensity",
                "4",
                "--limit",
                "2",
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["macro_name"] == "hard-groove"
    assert payload["shown_count"] == 2
    assert payload["opens_ports"] is False
    assert payload["sends_midi"] is False


def test_a4_macro_readiness_cli_rejects_bad_args() -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_readiness import (
        _parse_a4_macro_readiness_args,
    )

    with pytest.raises(ValueError, match="--seed requires a value"):
        _parse_a4_macro_readiness_args(["--seed"])
    with pytest.raises(ValueError, match="unknown argument"):
        _parse_a4_macro_readiness_args(["--surprise"])
    with pytest.raises(ValueError, match="macro name can only be provided once"):
        _parse_a4_macro_readiness_args(["home", "hard-groove"])
