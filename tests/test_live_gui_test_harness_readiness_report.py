"""Tests for passive live GUI test-harness readiness reporting."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)


def _feature_report(
    *,
    bpm: float = 142.0,
    low_end_weight: float = 0.71,
    spectral_brightness: float = 0.45,
    texture_noise: float = 0.66,
    energy_arc: tuple[float, ...] = (0.22, 0.55, 0.88),
):
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.MEDIUM,
        bpm=bpm,
        tempo_stability=0.87,
        kick_density=0.80,
        percussion_density=0.74,
        low_end_weight=low_end_weight,
        spectral_brightness=spectral_brightness,
        texture_noise=texture_noise,
        energy_arc=energy_arc,
        content_hash="",
        derived_at="2026-05-23T22:30:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _test_harness_contract(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_test_harness_contract import (
        build_style_performance_arc_live_gui_test_harness_contract_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_test_harness_contract_report(
        feature_report=_feature_report(),
        capture_feature_report=_feature_report(
            bpm=142.5,
            low_end_weight=0.72,
            spectral_brightness=0.46,
            texture_noise=0.63,
            energy_arc=(0.24, 0.57, 0.90),
        ),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=2,
        lookahead_count=2,
        match_limit=2,
        take_count=2,
        queue_label="Warehouse readiness queue",
        capture_prefix="warehouse",
        slot_key="capture-002",
        sidecar_label="Warehouse sidecar",
        screen_label="Warehouse screen",
        render_target="desktop-sidecar",
        density="standard",
        overlay_label="Warehouse overlay",
        frame_label="Warehouse frame",
        interaction_label="Warehouse interactions",
        reducer_label="Warehouse reducer",
        controller_label="Warehouse controller",
        playback_label="Warehouse playback transcript",
        validation_label="Warehouse validation matrix",
        harness_label="Warehouse harness contract",
    )


def test_live_gui_test_harness_readiness_builds_from_contract(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_test_harness_readiness import (
        build_style_performance_arc_live_gui_test_harness_readiness_from_contract,
        format_style_performance_arc_live_gui_test_harness_readiness_report,
        to_style_performance_arc_live_gui_test_harness_readiness_json,
    )

    contract = _test_harness_contract(tmp_path)
    report = build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
        contract,
        readiness_label="Warehouse readiness packet",
    )

    assert report.readiness_version == "live-gui-test-harness-readiness-v1"
    assert len(report.readiness_id) == 16
    assert report.readiness_label == "Warehouse readiness packet"
    assert report.readiness_status == "ready"
    assert report.rehearsal_mode == "metadata-only"
    assert report.contract_id == contract.contract_id
    assert report.validation_id == contract.validation_id
    assert report.playback_id == contract.playback_id
    assert report.selected_arc_key == contract.selected_arc_key
    assert report.scope == contract.scope
    assert "4 suites" in report.suite_summary
    assert "6 fixtures" in report.fixture_summary
    assert "bindings" in report.binding_summary
    assert {gate.key for gate in report.gates} >= {
        "contract-status",
        "suite-coverage",
        "fixture-coverage",
        "binding-coverage",
        "passive-boundary",
    }
    assert all(gate.passive for gate in report.gates)
    assert any(
        check.category == "suites"
        and check.required_source == "live_gui_test_harness_contract.suites"
        for check in report.readiness_checks
    )
    assert any(
        step.label == "Verify passive boundary"
        and step.action == "confirm metadata-only rehearsal boundary"
        for step in report.rehearsal_steps
    )
    assert "no GUI test runner execution" in report.blocked_actions
    assert "no audio read/compare execution" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-test-harness-readiness-report"
    )
    assert "style-performance-arc-live-gui-test-harness-contract-report" not in (
        report.replay_commands[0]
    )
    assert "--harness-label 'Warehouse harness contract'" in report.replay_commands[0]
    assert "--readiness-label 'Warehouse readiness packet'" in report.replay_commands[0]
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-test-harness-contract-report"
    )

    lines = format_style_performance_arc_live_gui_test_harness_readiness_report(report)
    text = "\n".join(lines)
    assert lines[0] == (
        "RytmRandomizer passive style performance arc live GUI test-harness readiness"
    )
    assert "Live GUI test-harness readiness summary:" in lines
    assert "Readiness gates:" in lines
    assert "Readiness checks:" in lines
    assert "Rehearsal steps:" in lines
    assert "Passive GUI test-harness readiness metadata only" in text
    assert "- no GUI launch" in lines
    assert "- no GUI test runner execution" in lines
    assert "- no audio read/compare execution" in lines
    assert "- no MIDI sending" in lines

    payload = to_style_performance_arc_live_gui_test_harness_readiness_json(report)
    readiness = payload["live_gui_test_harness_readiness"]
    assert readiness["readiness_version"] == "live-gui-test-harness-readiness-v1"
    assert readiness["readiness_id"] == report.readiness_id
    assert readiness["contract_id"] == contract.contract_id
    assert readiness["gates"][0]["key"] == "contract-status"
    assert readiness["readiness_checks"][0]["category"] == "suites"
    assert readiness["rehearsal_steps"][0]["label"] == "Load harness contract"
    assert "live_gui_test_harness_contract" in payload
    assert "live_gui_playback_validation" in payload
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_test_harness_readiness_status_and_replay_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_test_harness_readiness import (
        build_style_performance_arc_live_gui_test_harness_readiness_from_contract,
    )

    contract = _test_harness_contract(tmp_path)

    blocked_report = build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
        replace(contract, contract_status="blocked")
    )
    assert blocked_report.readiness_status == "blocked"
    assert "hold test-harness readiness before GUI/audio harness rehearsal" in (
        blocked_report.blocked_actions
    )

    review_report = build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
        replace(contract, contract_status="review-needed")
    )
    assert review_report.readiness_status == "review-needed"
    assert any(gate.status == "review-needed" for gate in review_report.gates)

    no_suites_report = build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
        replace(contract, suites=())
    )
    assert no_suites_report.readiness_status == "blocked"
    assert any(
        gate.key == "suite-coverage" and gate.status == "blocked" for gate in no_suites_report.gates
    )

    no_fixtures_report = build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
        replace(contract, fixtures=())
    )
    assert no_fixtures_report.readiness_status == "blocked"
    assert any(
        gate.key == "fixture-coverage" and gate.status == "blocked"
        for gate in no_fixtures_report.gates
    )

    no_bindings_report = build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
        replace(contract, bindings=())
    )
    assert no_bindings_report.readiness_status == "blocked"
    assert any(
        gate.key == "binding-coverage" and gate.status == "blocked"
        for gate in no_bindings_report.gates
    )

    non_passive_suite = replace(contract.suites[0], passive=False)
    non_passive_report = build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
        replace(contract, suites=(non_passive_suite, *contract.suites[1:]))
    )
    assert non_passive_report.readiness_status == "blocked"
    assert any(
        gate.key == "passive-boundary" and gate.status == "blocked"
        for gate in non_passive_report.gates
    )

    for malformed_command in (
        "python -m rytm_randomizer.cli upstream",
        "echo style-performance-arc-live-gui-test-harness-contract-report",
        "style-performance-arc-live-gui-test-harness-contract-report --description x",
    ):
        malformed_replay_report = (
            build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
                replace(contract, replay_commands=(malformed_command,))
            )
        )
        assert malformed_replay_report.replay_commands == ()

    empty_replay_report = build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
        replace(contract, replay_commands=())
    )
    assert empty_replay_report.replay_commands == ()

    description_false_positive_report = (
        build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
            replace(
                contract,
                replay_commands=(
                    "python -m rytm_randomizer.cli "
                    "style-performance-arc-live-gui-test-harness-contract-report "
                    "--description 'mentions --readiness-label in text'",
                ),
            )
        )
    )
    assert "--description 'mentions --readiness-label in text'" in (
        description_false_positive_report.replay_commands[0]
    )
    assert (
        "--readiness-label 'Live GUI test-harness readiness'"
        in description_false_positive_report.replay_commands[0]
    )

    with pytest.raises(ValueError, match="readiness_label"):
        build_style_performance_arc_live_gui_test_harness_readiness_from_contract(
            contract,
            readiness_label=" ",
        )


def test_live_gui_test_harness_readiness_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_test_harness_readiness import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_TEST_HARNESS_READINESS_CLI_COMMAND,
        build_style_performance_arc_live_gui_test_harness_readiness_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = STYLE_PERFORMANCE_ARC_LIVE_GUI_TEST_HARNESS_READINESS_CLI_COMMAND.args_parser(
        [
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--harness-label",
            "Warehouse harness",
            "--readiness-label",
            "Warehouse readiness",
            "--json",
        ]
    )
    assert parsed["harness_label"] == "Warehouse harness"
    assert parsed["readiness_label"] == "Warehouse readiness"
    assert parsed["json_output"] is True

    with pytest.raises(ValueError, match="usage"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_TEST_HARNESS_READINESS_CLI_COMMAND.args_parser(
            ["--readiness-label"]
        )

    report = build_style_performance_arc_live_gui_test_harness_readiness_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        capture_description="captured warehouse take",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        harness_label="Warehouse harness",
        readiness_label="Warehouse readiness",
    )
    assert report.readiness_label == "Warehouse readiness"

    rc = main(
        [
            "style-performance-arc-live-gui-test-harness-readiness-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--harness-label",
            "Warehouse harness",
            "--readiness-label",
            "Warehouse readiness",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["live_gui_test_harness_readiness"]["readiness_label"] == ("Warehouse readiness")
    assert "live_gui_test_harness_contract" in payload

    rc = main(
        [
            "style-performance-arc-live-gui-test-harness-readiness-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--readiness-label",
            "Warehouse readiness",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "Live GUI test-harness readiness summary:" in captured.out
    assert "Readiness gates:" in captured.out
    assert captured.err == ""

    rc = main(
        [
            "style-performance-arc-live-gui-test-harness-readiness-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "Error:" in captured.err

    rc = main(
        [
            "style-performance-arc-live-gui-test-harness-readiness-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--readiness-label",
            " ",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "readiness_label" in captured.err

    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main({[
        "style-performance-arc-live-gui-test-harness-readiness-report",
        "--description",
        "Jeff Mills Oscar Mulero Birmingham pressure",
        "--capture-description",
        "captured warehouse take",
        "--rytm",
        str(rytm_path),
        "--analog-four",
        str(a4_path),
        "--readiness-label",
        "Warehouse readiness",
        "--json",
    ]!r})
assert exit_code == 0, exit_code
for module_name in {FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES!r}:
    assert module_name not in sys.modules, module_name
"""
    passive_result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert passive_result.returncode == 0, passive_result.stderr


def test_live_gui_test_harness_readiness_help_mentions_passive_readiness():
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("style-performance-arc-live-gui-test-harness-readiness-report")
    assert help_text.startswith(
        "RytmRandomizer passive CLI: "
        "style-performance-arc-live-gui-test-harness-readiness-report"
    )
    assert "GUI test-harness readiness" in help_text
    assert "no GUI launch" in help_text
    assert "no GUI test runner execution" in help_text
    assert "no audio read/compare execution" in help_text
    assert "no MIDI sending" in help_text
    assert "no port opening" in help_text
