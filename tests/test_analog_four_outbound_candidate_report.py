from __future__ import annotations

import json
import sys

import pytest

pytestmark = pytest.mark.fast


def test_a4_outbound_candidate_report_exposes_validation_ladder_and_candidates() -> None:
    from rytm_randomizer.reports.analog_four_outbound_candidate import (
        build_analog_four_outbound_candidate_report,
        format_analog_four_outbound_candidate_report,
    )

    report = build_analog_four_outbound_candidate_report()
    text = "\n".join(format_analog_four_outbound_candidate_report(report))

    assert report.title == "RytmRandomizer passive Analog Four outbound candidate"
    assert report.status == "candidate-only"
    assert [row.track for row in report.candidate_rows] == [1, 2, 3, 4]
    assert [row.mido_channel for row in report.candidate_rows] == [0, 1, 2, 3]
    assert {row.parameter for row in report.candidate_rows} == {"OSC1 PWM Depth"}
    assert {row.cc_msb for row in report.candidate_rows} == {74}
    assert {row.value for row in report.candidate_rows} == {32}
    assert [gate.name for gate in report.validation_ladder] == [
        "passive-input-observation",
        "mock-candidate-proof",
        "dry-run-helper",
        "manual-armed-validation",
    ]
    assert "Analog Four outbound status: candidate-only" in text
    assert "Track 1 | mido channel 0 | OSC1 PWM Depth | CC74 -> 32" in text
    assert "Gate 1: passive-input-observation" in text
    assert "blocked active actions: A4 outbound CC send, A4 outbound macro send" in text
    assert "- no MIDI sending" in text
    assert "- no port opening" in text


def test_a4_outbound_candidate_json_is_deterministic_and_ready_for_gui() -> None:
    from rytm_randomizer.reports.analog_four_outbound_candidate import (
        build_analog_four_outbound_candidate_payload,
    )

    payload = build_analog_four_outbound_candidate_payload()

    assert payload["title"] == "RytmRandomizer passive Analog Four outbound candidate"
    assert payload["status"] == "candidate-only"
    assert payload["candidate_rows"] == [
        {
            "track": 1,
            "mido_channel": 0,
            "parameter": "OSC1 PWM Depth",
            "section": "OSC 1",
            "encoder": "J",
            "cc_msb": 74,
            "value": 32,
            "source": "manual-backed A4 Appendix D table",
            "readiness": "blocked pending manual hardware validation",
        },
        {
            "track": 2,
            "mido_channel": 1,
            "parameter": "OSC1 PWM Depth",
            "section": "OSC 1",
            "encoder": "J",
            "cc_msb": 74,
            "value": 32,
            "source": "manual-backed A4 Appendix D table",
            "readiness": "blocked pending manual hardware validation",
        },
        {
            "track": 3,
            "mido_channel": 2,
            "parameter": "OSC1 PWM Depth",
            "section": "OSC 1",
            "encoder": "J",
            "cc_msb": 74,
            "value": 32,
            "source": "manual-backed A4 Appendix D table",
            "readiness": "blocked pending manual hardware validation",
        },
        {
            "track": 4,
            "mido_channel": 3,
            "parameter": "OSC1 PWM Depth",
            "section": "OSC 1",
            "encoder": "J",
            "cc_msb": 74,
            "value": 32,
            "source": "manual-backed A4 Appendix D table",
            "readiness": "blocked pending manual hardware validation",
        },
    ]
    assert payload["validation_ladder"][0]["operator_action"].startswith("Open A4 input only")
    assert payload["blocked_active_actions"] == [
        "A4 outbound CC send",
        "A4 outbound macro send",
    ]
    assert payload["replay_commands"] == [
        "python -m rytm_randomizer.cli analog-four-outbound-candidate-report",
        "python -m rytm_randomizer.cli analog-four-outbound-candidate-report --json",
    ]
    assert "no MIDI sending" in payload["safety"]
    assert "no hardware required" in payload["safety"]


def test_a4_outbound_candidate_cli_command_prints_text_json_and_rejects_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.analog_four_outbound_candidate import (
        ANALOG_FOUR_OUTBOUND_CANDIDATE_CLI_COMMAND,
    )

    assert ANALOG_FOUR_OUTBOUND_CANDIDATE_CLI_COMMAND.args_parser([]) == {"json_output": False}
    assert ANALOG_FOUR_OUTBOUND_CANDIDATE_CLI_COMMAND.args_parser(["--json"]) == {
        "json_output": True
    }
    with pytest.raises(ValueError, match="usage"):
        ANALOG_FOUR_OUTBOUND_CANDIDATE_CLI_COMMAND.args_parser(["extra"])

    assert ANALOG_FOUR_OUTBOUND_CANDIDATE_CLI_COMMAND.handler(json_output=False) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive Analog Four outbound candidate" in captured.out
    assert "A4 outbound CC send" in captured.out

    assert ANALOG_FOUR_OUTBOUND_CANDIDATE_CLI_COMMAND.handler(json_output=True) == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["candidate_rows"][0]["parameter"] == "OSC1 PWM Depth"
    assert ANALOG_FOUR_OUTBOUND_CANDIDATE_CLI_COMMAND.error_formatter is not None
    assert (
        ANALOG_FOUR_OUTBOUND_CANDIDATE_CLI_COMMAND.error_formatter(ValueError("bad input"))
        == "Error: bad input"
    )


def test_a4_outbound_candidate_rejects_candidate_without_cc_msb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import rytm_randomizer.reports.analog_four_outbound_candidate as report_module
    from rytm_randomizer.data.analog_four_midi import AnalogFourCcMapping

    monkeypatch.setattr(
        report_module,
        "ANALOG_FOUR_SYNTH_TRACK_CC",
        {
            "OSC1 PWM Depth": AnalogFourCcMapping(
                parameter="OSC1 PWM Depth",
                section="OSC 1",
                encoder="J",
                cc_msb=None,
                cc_lsb=None,
                nrpn_msb=1,
                nrpn_lsb=9,
            )
        },
    )

    with pytest.raises(ValueError, match="has no CC MSB"):
        report_module.build_analog_four_outbound_candidate_report()


def test_a4_outbound_candidate_cli_imports_no_real_midi_modules() -> None:
    before = set(sys.modules)

    __import__("rytm_randomizer.reports.analog_four_outbound_candidate")

    imported = set(sys.modules) - before
    assert "mido" not in imported
    assert "rtmidi" not in imported
    assert "rytm_randomizer.real_midi_adapter" not in imported
    assert "rytm_randomizer.mido_provider" not in imported
