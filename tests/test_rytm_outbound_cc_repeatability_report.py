"""Tests for passive Rytm outbound CC repeatability readiness."""

from __future__ import annotations

import json
import sys

import pytest

pytestmark = pytest.mark.fast

FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)


def test_outbound_repeatability_report_defaults_to_all_12_tracks() -> None:
    from rytm_randomizer.reports.rytm_outbound_cc_repeatability import (
        build_rytm_outbound_cc_repeatability_report,
        format_rytm_outbound_cc_repeatability_report,
        to_rytm_outbound_cc_repeatability_json,
    )

    report = build_rytm_outbound_cc_repeatability_report()

    assert report.model_version == "rytm-outbound-cc-repeatability-v1"
    assert report.track_count == 12
    assert report.control == 17
    assert report.value == 64
    assert report.validation_mode == "repeatability"
    assert report.source_evidence_path == (
        "docs/hardware-validation/2026-05-26-outbound-12-track-cc-results.md"
    )
    assert len(report.steps) == 12
    assert [step.track for step in report.steps] == list(range(1, 13))
    assert [step.mido_channel for step in report.steps] == list(range(12))
    assert report.steps[0].command == (
        "python -m rytm_randomizer.app --arm --validate-one-cc "
        "--channel 0 --control 17 --value 64"
    )
    assert report.steps[-1].expected_result == "Only Track 12 changes"
    assert "no MIDI sending" in report.safety_lines
    assert "no port opening" in report.safety_lines
    assert "run unattended hardware loop" in report.blocked_actions
    assert "test new CC number in repeatability pass" in report.blocked_actions
    assert report.replay_commands == (
        "python -m rytm_randomizer.cli rytm-outbound-cc-repeatability-report",
    )

    lines = format_rytm_outbound_cc_repeatability_report(report)
    assert lines[0] == "RytmRandomizer passive Rytm outbound CC repeatability report"
    assert "Track steps:" in lines
    assert "- Track 12 -> mido channel 11 / CC 17 / value 64: Only Track 12 changes" in lines
    assert "Stop conditions:" in lines
    assert "- any non-target pad changes" in lines
    assert "Safety:" in lines
    assert "Source: rytm_randomizer.reports.rytm_outbound_cc_repeatability" in lines

    payload = to_rytm_outbound_cc_repeatability_json(report)
    assert payload["rytm_outbound_cc_repeatability"]["track_count"] == 12
    assert payload["rytm_outbound_cc_repeatability"]["steps"][11]["mido_channel"] == 11
    json.dumps(payload, sort_keys=True)


def test_outbound_repeatability_report_customizes_control_and_value() -> None:
    from rytm_randomizer.reports.rytm_outbound_cc_repeatability import (
        build_rytm_outbound_cc_repeatability_report,
    )

    report = build_rytm_outbound_cc_repeatability_report(control=18, value=96)

    assert report.control == 18
    assert report.value == 96
    assert report.steps[3].command.endswith("--channel 3 --control 18 --value 96")
    assert report.replay_commands == (
        "python -m rytm_randomizer.cli rytm-outbound-cc-repeatability-report "
        "--control 18 --value 96",
    )

    with pytest.raises(ValueError, match="control"):
        build_rytm_outbound_cc_repeatability_report(control=128)
    with pytest.raises(ValueError, match="value"):
        build_rytm_outbound_cc_repeatability_report(value=-1)


def test_outbound_repeatability_report_imports_no_real_midi_modules() -> None:
    before_modules = set(sys.modules)

    from rytm_randomizer.reports.rytm_outbound_cc_repeatability import (
        build_rytm_outbound_cc_repeatability_report,
        to_rytm_outbound_cc_repeatability_json,
    )

    report = build_rytm_outbound_cc_repeatability_report()
    json.dumps(to_rytm_outbound_cc_repeatability_json(report), sort_keys=True)

    imported_modules = set(sys.modules) - before_modules
    assert not (set(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES) & imported_modules)


def test_outbound_repeatability_report_passive_cli_text_and_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer import cli

    rc = cli.main(["rytm-outbound-cc-repeatability-report"])

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Rytm outbound CC repeatability report" in captured.out
    assert "Track 01 -> mido channel 0 / CC 17 / value 64" in captured.out
    assert "no MIDI sending" in captured.out
    assert captured.err == ""

    rc = cli.main(
        ["rytm-outbound-cc-repeatability-report", "--control", "18", "--value", "96", "--json"]
    )

    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["rytm_outbound_cc_repeatability"]["control"] == 18
    assert payload["rytm_outbound_cc_repeatability"]["value"] == 96
    assert payload["rytm_outbound_cc_repeatability"]["steps"][0]["command"].endswith(
        "--channel 0 --control 18 --value 96"
    )
    assert captured.err == ""
