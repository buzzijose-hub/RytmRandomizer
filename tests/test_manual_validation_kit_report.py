"""Tests for the passive manual validation kit report."""

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


def test_manual_validation_kit_report_defaults_to_full_passive_itinerary() -> None:
    from rytm_randomizer.reports.manual_validation_kit import (
        build_manual_validation_kit_report,
        format_manual_validation_kit_report,
        to_manual_validation_kit_json,
    )

    report = build_manual_validation_kit_report()

    assert report.model_version == "manual-validation-kit-v1"
    assert report.phase_filter is None
    assert [phase.slug for phase in report.phases] == [
        "installer_bootstrap",
        "profile_workflow",
        "mock_rehearsal",
        "armed_smoke",
        "evidence_closeout",
    ]
    assert len(report.steps) >= 10
    assert any(step.requires_hardware for step in report.steps)
    assert all(
        not command.startswith("& ") for step in report.steps for command in step.passive_commands
    )
    assert "open MIDI ports" in report.blocked_actions
    assert "send MIDI" in report.blocked_actions
    assert report.safety["opens_midi_ports"] is False
    assert report.safety["sends_midi"] is False

    lines = format_manual_validation_kit_report(report)
    assert lines[0] == "RytmRandomizer passive manual validation kit report"
    assert "Validation phases:" in lines
    assert "- installer_bootstrap: Installer bootstrap" in lines
    assert "Manual commands (instruction text only):" in lines
    assert any("--arm --validate-one-cc" in line for line in lines)
    assert "Safety:" in lines
    assert "Source: rytm_randomizer.reports.manual_validation_kit" in lines

    payload = to_manual_validation_kit_json(report)
    assert payload["manual_validation_kit"]["phase_count"] == 5
    assert payload["manual_validation_kit"]["safety"]["executes_printed_commands"] is False
    json.dumps(payload, sort_keys=True)


def test_manual_validation_kit_report_filters_to_one_phase() -> None:
    from rytm_randomizer.reports.manual_validation_kit import (
        build_manual_validation_kit_report,
        format_manual_validation_kit_report,
    )

    report = build_manual_validation_kit_report(phase="profile_workflow")

    assert report.phase_filter == "profile_workflow"
    assert [phase.slug for phase in report.phases] == ["profile_workflow"]
    assert {step.phase for step in report.steps} == {"profile_workflow"}
    assert any("Create profile" in step.title for step in report.steps)
    assert all(not step.requires_hardware for step in report.steps)

    lines = format_manual_validation_kit_report(report)
    assert "Phase filter: profile_workflow" in lines
    assert "- profile_workflow: Profile workflow" in lines
    assert "- installer_bootstrap: Installer bootstrap" not in lines


def test_manual_validation_kit_report_rejects_unknown_phase() -> None:
    from rytm_randomizer.reports.manual_validation_kit import build_manual_validation_kit_report

    with pytest.raises(ValueError, match="Unknown manual validation phase"):
        build_manual_validation_kit_report(phase="missing")


def test_manual_validation_kit_report_imports_no_real_midi_modules() -> None:
    before_modules = set(sys.modules)

    from rytm_randomizer.reports.manual_validation_kit import (
        build_manual_validation_kit_report,
        to_manual_validation_kit_json,
    )

    report = build_manual_validation_kit_report()
    json.dumps(to_manual_validation_kit_json(report), sort_keys=True)

    imported_modules = set(sys.modules) - before_modules
    assert not (set(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES) & imported_modules)


def test_manual_validation_kit_report_passive_cli_text_json_and_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer import cli
    from rytm_randomizer.help_text import resolve_help_text

    rc = cli.main(["manual-validation-kit-report", "--phase", "mock_rehearsal"])

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive manual validation kit report" in captured.out
    assert "Phase filter: mock_rehearsal" in captured.out
    assert "Mock rehearsal" in captured.out
    assert "no MIDI ports opened" in captured.out
    assert captured.err == ""

    rc = cli.main(["manual-validation-kit-report", "--phase", "armed_smoke", "--json"])

    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["manual_validation_kit"]["phase_filter"] == "armed_smoke"
    assert payload["manual_validation_kit"]["phases"][0]["slug"] == "armed_smoke"
    assert payload["manual_validation_kit"]["safety"]["sends_midi"] is False
    assert captured.err == ""

    help_text = resolve_help_text("manual-validation-kit-report")
    assert help_text.startswith("RytmRandomizer passive CLI: manual-validation-kit-report")
    assert "manual-validation-kit-report [--phase <slug>] [--json]" in help_text


def test_manual_validation_kit_report_cli_rejects_bad_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer import cli

    rc = cli.main(["manual-validation-kit-report", "--phase"])

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "manual-validation-kit-report [--phase <slug>] [--json]" in captured.err
    assert "--phase requires a phase slug" in captured.err

    rc = cli.main(["manual-validation-kit-report", "--unknown"])

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "Unknown option for manual-validation-kit-report: --unknown" in captured.err
