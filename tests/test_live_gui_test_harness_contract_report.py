"""Tests for passive live GUI test-harness contract reporting."""

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
        derived_at="2026-05-23T18:30:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _playback_validation(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_playback_validation import (
        build_style_performance_arc_live_gui_playback_validation_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_playback_validation_report(
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
        queue_label="Warehouse harness queue",
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
    )


def test_live_gui_test_harness_contract_builds_from_validation(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_test_harness_contract import (
        build_style_performance_arc_live_gui_test_harness_contract_from_validation,
        format_style_performance_arc_live_gui_test_harness_contract_report,
        to_style_performance_arc_live_gui_test_harness_contract_json,
    )

    validation = _playback_validation(tmp_path)
    report = build_style_performance_arc_live_gui_test_harness_contract_from_validation(
        validation,
        harness_label="Warehouse harness contract",
    )

    assert report.contract_version == "live-gui-test-harness-contract-v1"
    assert len(report.contract_id) == 16
    assert report.harness_label == "Warehouse harness contract"
    assert report.contract_status == "ready"
    assert report.validation_id == validation.validation_id
    assert report.playback_id == validation.playback_id
    assert report.selected_arc_key == validation.selected_arc_key
    assert report.scope == validation.scope
    assert {suite.category for suite in report.suites} >= {
        "timeline",
        "assertion",
        "analyzer",
        "safety",
    }
    assert any(
        suite.suite_key == "harness-suite-timeline"
        and suite.required_fixture == "fixture-playback-transcript"
        for suite in report.suites
    )
    assert any(
        fixture.fixture_key == "fixture-playback-validation"
        and fixture.source_id == validation.validation_id
        for fixture in report.fixtures
    )
    assert any(
        binding.selector.startswith("[data-validation-case='")
        and binding.expected_outcome == "metadata assertion only"
        for binding in report.bindings
    )
    assert "no GUI test runner execution" in report.blocked_actions
    assert "no audio comparison execution" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-test-harness-contract-report"
    )
    assert "style-performance-arc-live-gui-playback-validation-report" not in (
        report.replay_commands[0]
    )
    assert "--validation-label 'Warehouse validation matrix'" in report.replay_commands[0]
    assert "--harness-label 'Warehouse harness contract'" in report.replay_commands[0]
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-playback-validation-report"
    )

    lines = format_style_performance_arc_live_gui_test_harness_contract_report(report)
    text = "\n".join(lines)
    assert lines[0] == (
        "RytmRandomizer passive style performance arc live GUI test-harness contract"
    )
    assert "Live GUI test-harness contract summary:" in lines
    assert "Harness suites:" in lines
    assert "Harness fixtures:" in lines
    assert "Harness bindings:" in lines
    assert "Passive GUI test-harness contract metadata only" in text
    assert "- no GUI test runner execution" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_test_harness_contract_json(report)
    contract = payload["live_gui_test_harness_contract"]
    assert contract["contract_version"] == "live-gui-test-harness-contract-v1"
    assert contract["contract_id"] == report.contract_id
    assert contract["validation_id"] == validation.validation_id
    assert contract["suites"][0]["suite_key"] == "harness-suite-timeline"
    assert contract["fixtures"][0]["fixture_key"] == "fixture-playback-validation"
    assert "live_gui_playback_validation" in payload
    assert "live_gui_playback_transcript" in payload
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_test_harness_contract_status_and_replay_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_test_harness_contract import (
        build_style_performance_arc_live_gui_test_harness_contract_from_validation,
    )

    validation = _playback_validation(tmp_path)
    blocked_report = build_style_performance_arc_live_gui_test_harness_contract_from_validation(
        replace(validation, validation_status="blocked", validation_cases=())
    )
    assert blocked_report.contract_status == "blocked"
    assert "hold test-harness contract before GUI harness binding" in (
        blocked_report.blocked_actions
    )

    review_report = build_style_performance_arc_live_gui_test_harness_contract_from_validation(
        replace(validation, validation_status="review-needed")
    )
    assert review_report.contract_status == "review-needed"
    assert any(suite.category == "assertion" for suite in review_report.suites)

    for malformed_command in (
        "python -m rytm_randomizer.cli upstream",
        "echo style-performance-arc-live-gui-playback-validation-report",
        "style-performance-arc-live-gui-playback-validation-report --description x",
    ):
        malformed_replay_report = (
            build_style_performance_arc_live_gui_test_harness_contract_from_validation(
                replace(validation, replay_commands=(malformed_command,))
            )
        )
        assert malformed_replay_report.replay_commands == ()

    empty_replay_report = (
        build_style_performance_arc_live_gui_test_harness_contract_from_validation(
            replace(validation, replay_commands=())
        )
    )
    assert empty_replay_report.replay_commands == ()

    description_false_positive_report = (
        build_style_performance_arc_live_gui_test_harness_contract_from_validation(
            replace(
                validation,
                replay_commands=(
                    "python -m rytm_randomizer.cli "
                    "style-performance-arc-live-gui-playback-validation-report "
                    "--description 'mentions --harness-label in text'",
                ),
            )
        )
    )
    assert "--description 'mentions --harness-label in text'" in (
        description_false_positive_report.replay_commands[0]
    )
    assert (
        "--harness-label 'Live GUI test-harness contract'"
        in description_false_positive_report.replay_commands[0]
    )

    with pytest.raises(ValueError, match="harness_label"):
        build_style_performance_arc_live_gui_test_harness_contract_from_validation(
            validation,
            harness_label=" ",
        )


def test_live_gui_test_harness_contract_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_test_harness_contract import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_TEST_HARNESS_CONTRACT_CLI_COMMAND,
        build_style_performance_arc_live_gui_test_harness_contract_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = STYLE_PERFORMANCE_ARC_LIVE_GUI_TEST_HARNESS_CONTRACT_CLI_COMMAND.args_parser(
        [
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--validation-label",
            "Warehouse validation",
            "--harness-label",
            "Warehouse harness",
            "--json",
        ]
    )
    assert parsed["validation_label"] == "Warehouse validation"
    assert parsed["harness_label"] == "Warehouse harness"
    assert parsed["json_output"] is True

    with pytest.raises(ValueError, match="usage"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_TEST_HARNESS_CONTRACT_CLI_COMMAND.args_parser(
            ["--harness-label"]
        )

    report = build_style_performance_arc_live_gui_test_harness_contract_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        capture_description="captured warehouse take",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        validation_label="Warehouse validation",
        harness_label="Warehouse harness",
    )
    assert report.harness_label == "Warehouse harness"

    rc = main(
        [
            "style-performance-arc-live-gui-test-harness-contract-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--validation-label",
            "Warehouse validation",
            "--harness-label",
            "Warehouse harness",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["live_gui_test_harness_contract"]["harness_label"] == "Warehouse harness"
    assert "live_gui_playback_validation" in payload

    rc = main(
        [
            "style-performance-arc-live-gui-test-harness-contract-report",
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
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "Live GUI test-harness contract summary:" in captured.out
    assert "Harness suites:" in captured.out
    assert captured.err == ""

    rc = main(
        [
            "style-performance-arc-live-gui-test-harness-contract-report",
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
            "style-performance-arc-live-gui-test-harness-contract-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--harness-label",
            " ",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "harness_label" in captured.err

    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main({[
        "style-performance-arc-live-gui-test-harness-contract-report",
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


def test_live_gui_test_harness_contract_help_mentions_passive_contract():
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("style-performance-arc-live-gui-test-harness-contract-report")
    assert help_text.startswith(
        "RytmRandomizer passive CLI: " "style-performance-arc-live-gui-test-harness-contract-report"
    )
    assert "GUI test-harness contract" in help_text
    assert "no GUI launch" in help_text
    assert "no MIDI sending" in help_text
    assert "no port opening" in help_text
