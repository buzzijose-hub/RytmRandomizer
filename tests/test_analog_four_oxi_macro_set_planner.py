"""Tests for passive Analog Four OXI macro set-planner reports."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_a4_macro_set_planner_prints_nothing() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rytm_randomizer.reports.analog_four_oxi_macro_set_planner",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_default_set_planner_sequences_existing_a4_macros_passively() -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_set_planner import (
        build_analog_four_oxi_macro_set_planner_report,
    )

    report = build_analog_four_oxi_macro_set_planner_report(seed=10)

    assert report.title == "RytmRandomizer passive Analog Four OXI macro set planner"
    assert report.set_name == "warehouse-arc"
    assert [step.macro_name for step in report.steps] == [
        "home",
        "hard-groove",
        "dub-pressure",
        "industrial-transition",
        "home",
    ]
    assert [step.order for step in report.steps] == [1, 2, 3, 4, 5]
    assert report.current_step.macro_name == "home"
    assert [step.macro_name for step in report.up_next] == [
        "hard-groove",
        "dub-pressure",
        "industrial-transition",
        "home",
    ]
    assert report.opens_ports is False
    assert report.sends_midi is False
    assert report.hardware_required is False
    assert "A4 full macro SEND" in report.blocked_active_actions
    assert "A4 unattended macro playback" in report.blocked_active_actions
    assert all(step.readiness == "review-ready" for step in report.steps)
    assert all(step.ready_count == step.event_count for step in report.steps)
    assert all(
        step.validation_command.startswith("analog-four-oxi-macro-readiness-report")
        for step in report.steps
    )
    assert all(
        step.recovery_action == "reload saved A4 kit or return to home macro"
        for step in report.steps
    )


def test_set_planner_text_and_json_are_deterministic() -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_set_planner import (
        build_analog_four_oxi_macro_set_planner_payload,
        build_analog_four_oxi_macro_set_planner_report,
        format_analog_four_oxi_macro_set_planner_report,
    )

    report = build_analog_four_oxi_macro_set_planner_report(
        sequence=("home", "dub-pressure", "industrial-transition"),
        set_name="late-room",
        seed=4,
    )
    text = "\n".join(format_analog_four_oxi_macro_set_planner_report(report))
    payload = build_analog_four_oxi_macro_set_planner_payload(report)

    assert text.startswith("RytmRandomizer passive Analog Four OXI macro set planner\n")
    assert "Set: late-room" in text
    assert "1. home / Home" in text
    assert "2. dub-pressure / Dub Pressure" in text
    assert "3. industrial-transition / Industrial Transition" in text
    assert "Blocked active actions:" in text
    assert "- A4 full macro SEND" in text
    assert "- no MIDI sending" in text
    assert "- no port opening" in text
    assert payload["set_name"] == "late-room"
    assert payload["step_count"] == 3
    assert payload["current_step"]["macro_name"] == "home"
    assert payload["up_next"][0]["macro_name"] == "dub-pressure"
    assert payload["steps"][2]["macro_name"] == "industrial-transition"
    assert payload["blocked_active_actions"] == [
        "A4 full macro SEND",
        "A4 unattended macro playback",
    ]
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        build_analog_four_oxi_macro_set_planner_payload(report),
        sort_keys=True,
    )


def test_set_planner_rejects_empty_and_unknown_sequences() -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_set_planner import (
        build_analog_four_oxi_macro_set_planner_report,
    )

    with pytest.raises(ValueError, match="sequence must include at least one macro"):
        build_analog_four_oxi_macro_set_planner_report(sequence=())

    with pytest.raises(ValueError, match="unknown Analog Four OXI macro"):
        build_analog_four_oxi_macro_set_planner_report(sequence=("home", "ghost"))


def test_set_planner_cli_parser_accepts_custom_sequence_and_rejects_bad_args() -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_set_planner import (
        ANALOG_FOUR_OXI_MACRO_SET_PLANNER_CLI_COMMAND,
    )

    parsed = ANALOG_FOUR_OXI_MACRO_SET_PLANNER_CLI_COMMAND.args_parser(
        [
            "--set-name",
            "custom",
            "--sequence",
            "home,dub-pressure",
            "--seed",
            "8",
            "--json",
        ]
    )

    assert parsed == {
        "set_name": "custom",
        "sequence": ("home", "dub-pressure"),
        "seed": 8,
        "json_output": True,
    }

    with pytest.raises(ValueError, match="--sequence requires a value"):
        ANALOG_FOUR_OXI_MACRO_SET_PLANNER_CLI_COMMAND.args_parser(["--sequence"])
    with pytest.raises(ValueError, match="--seed must be an integer"):
        ANALOG_FOUR_OXI_MACRO_SET_PLANNER_CLI_COMMAND.args_parser(["--seed", "nope"])
    with pytest.raises(ValueError, match="unknown argument"):
        ANALOG_FOUR_OXI_MACRO_SET_PLANNER_CLI_COMMAND.args_parser(["--surprise"])
    with pytest.raises(ValueError, match="sequence must include at least one macro"):
        ANALOG_FOUR_OXI_MACRO_SET_PLANNER_CLI_COMMAND.args_parser(["--sequence", ","])


def test_set_planner_cli_outputs_text_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    assert main(["analog-four-oxi-macro-set-planner-report", "--set-name", "custom"]) == 0
    text = capsys.readouterr()
    assert "Set: custom" in text.out
    assert "A4 full macro SEND" in text.out
    assert text.err == ""

    assert (
        main(
            [
                "analog-four-oxi-macro-set-planner-report",
                "--sequence",
                "home,dub-pressure",
                "--seed",
                "3",
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["step_count"] == 2
    assert payload["steps"][1]["macro_name"] == "dub-pressure"
    assert payload["opens_ports"] is False
    assert payload["sends_midi"] is False
