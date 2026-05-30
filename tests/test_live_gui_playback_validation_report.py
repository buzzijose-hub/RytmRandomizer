"""Tests for passive live GUI playback validation matrix reporting."""

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
        derived_at="2026-05-23T17:45:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _playback_transcript(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_playback_transcript import (
        build_style_performance_arc_live_gui_playback_transcript_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_playback_transcript_report(
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
        queue_label="Warehouse validation queue",
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
    )


def test_live_gui_playback_validation_builds_matrix_from_transcript(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_playback_validation import (
        build_style_performance_arc_live_gui_playback_validation_from_transcript,
        format_style_performance_arc_live_gui_playback_validation_report,
        to_style_performance_arc_live_gui_playback_validation_json,
    )

    playback = _playback_transcript(tmp_path)
    report = build_style_performance_arc_live_gui_playback_validation_from_transcript(
        playback,
        validation_label="Warehouse validation matrix",
    )

    assert report.validation_version == "live-gui-playback-validation-v1"
    assert len(report.validation_id) == 16
    assert report.validation_label == "Warehouse validation matrix"
    assert report.validation_status == "ready"
    assert report.playback_id == playback.playback_id
    assert report.controller_id == playback.controller_id
    assert report.selected_arc_key == playback.selected_arc_key
    assert report.scope == playback.scope
    assert report.harness_steps[0].step_key == "validation-step-load-playback-transcript"
    assert report.harness_steps[0].passive is True
    categories = {case.category for case in report.validation_cases}
    assert {"timeline", "assertion", "analyzer", "safety"} <= categories
    assert any(
        case.category == "timeline" and case.source_key == playback.events[0].event_key
        for case in report.validation_cases
    )
    assert any(
        case.category == "analyzer" and "meter widget" in case.assertion
        for case in report.validation_cases
    )
    assert any(
        case.category == "safety" and case.expected == "no MIDI sending"
        for case in report.validation_cases
    )
    assert "no GUI test runner dispatch" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-playback-validation-report"
    )
    assert "style-performance-arc-live-gui-playback-transcript-report" not in (
        report.replay_commands[0]
    )
    assert "--playback-label 'Warehouse playback transcript'" in report.replay_commands[0]
    assert "--validation-label 'Warehouse validation matrix'" in report.replay_commands[0]
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-playback-transcript-report"
    )

    lines = format_style_performance_arc_live_gui_playback_validation_report(report)
    text = "\n".join(lines)
    assert lines[0] == (
        "RytmRandomizer passive style performance arc live GUI playback validation matrix"
    )
    assert "Live GUI playback validation summary:" in lines
    assert "Validation harness steps:" in lines
    assert "Validation cases:" in lines
    assert "Passive GUI playback validation metadata only" in text
    assert "- no GUI test runner dispatch" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_playback_validation_json(report)
    validation = payload["live_gui_playback_validation"]
    assert validation["validation_version"] == "live-gui-playback-validation-v1"
    assert validation["validation_id"] == report.validation_id
    assert validation["playback_id"] == playback.playback_id
    assert validation["validation_cases"][0]["category"] == "timeline"
    assert payload["live_gui_playback_transcript"]["playback_id"] == playback.playback_id
    assert payload["live_gui_controller_state"]["controller_id"] == playback.controller_id
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_playback_validation_status_and_replay_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_playback_validation import (
        build_style_performance_arc_live_gui_playback_validation_from_transcript,
    )

    playback = _playback_transcript(tmp_path)
    blocked_report = build_style_performance_arc_live_gui_playback_validation_from_transcript(
        replace(playback, playback_status="blocked", events=())
    )
    assert blocked_report.validation_status == "blocked"
    assert "hold playback validation matrix before GUI test harness binding" in (
        blocked_report.blocked_actions
    )

    review_report = build_style_performance_arc_live_gui_playback_validation_from_transcript(
        replace(playback, playback_status="review-needed")
    )
    assert review_report.validation_status == "review-needed"
    assert any(case.category == "assertion" for case in review_report.validation_cases)

    for malformed_command in (
        "python -m rytm_randomizer.cli upstream",
        "echo style-performance-arc-live-gui-playback-transcript-report",
        "style-performance-arc-live-gui-playback-transcript-report --description x",
    ):
        malformed_replay_report = (
            build_style_performance_arc_live_gui_playback_validation_from_transcript(
                replace(playback, replay_commands=(malformed_command,))
            )
        )
        assert malformed_replay_report.replay_commands == ()

    empty_replay_report = build_style_performance_arc_live_gui_playback_validation_from_transcript(
        replace(playback, replay_commands=())
    )
    assert empty_replay_report.replay_commands == ()

    description_false_positive_report = (
        build_style_performance_arc_live_gui_playback_validation_from_transcript(
            replace(
                playback,
                replay_commands=(
                    "python -m rytm_randomizer.cli "
                    "style-performance-arc-live-gui-playback-transcript-report "
                    "--description 'mentions --validation-label in text'",
                ),
            )
        )
    )
    assert "--description 'mentions --validation-label in text'" in (
        description_false_positive_report.replay_commands[0]
    )
    assert (
        "--validation-label 'Live GUI playback validation matrix'"
        in description_false_positive_report.replay_commands[0]
    )

    with pytest.raises(ValueError, match="validation_label"):
        build_style_performance_arc_live_gui_playback_validation_from_transcript(
            playback,
            validation_label=" ",
        )


def test_live_gui_playback_validation_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_playback_validation import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_PLAYBACK_VALIDATION_CLI_COMMAND,
        build_style_performance_arc_live_gui_playback_validation_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = STYLE_PERFORMANCE_ARC_LIVE_GUI_PLAYBACK_VALIDATION_CLI_COMMAND.args_parser(
        [
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--playback-label",
            "Warehouse playback",
            "--validation-label",
            "Warehouse validation",
            "--json",
        ]
    )
    assert parsed["playback_label"] == "Warehouse playback"
    assert parsed["validation_label"] == "Warehouse validation"
    assert parsed["json_output"] is True

    with pytest.raises(ValueError, match="usage"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_PLAYBACK_VALIDATION_CLI_COMMAND.args_parser(
            ["--validation-label"]
        )

    report = build_style_performance_arc_live_gui_playback_validation_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        capture_description="captured warehouse take",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        playback_label="Warehouse playback",
        validation_label="Warehouse validation",
    )
    assert report.validation_label == "Warehouse validation"

    rc = main(
        [
            "style-performance-arc-live-gui-playback-validation-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--playback-label",
            "Warehouse playback",
            "--validation-label",
            "Warehouse validation",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["live_gui_playback_validation"]["validation_label"] == ("Warehouse validation")
    assert "live_gui_playback_transcript" in payload

    rc = main(
        [
            "style-performance-arc-live-gui-playback-validation-report",
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
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "Live GUI playback validation summary:" in captured.out
    assert "Validation cases:" in captured.out
    assert captured.err == ""

    rc = main(
        [
            "style-performance-arc-live-gui-playback-validation-report",
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
            "style-performance-arc-live-gui-playback-validation-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--validation-label",
            " ",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "validation_label" in captured.err

    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main({[
        "style-performance-arc-live-gui-playback-validation-report",
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


def test_live_gui_playback_validation_help_mentions_passive_contract():
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("style-performance-arc-live-gui-playback-validation-report")
    assert help_text.startswith(
        "RytmRandomizer passive CLI: " "style-performance-arc-live-gui-playback-validation-report"
    )
    assert "GUI playback validation" in help_text
    assert "no GUI launch" in help_text
    assert "no MIDI sending" in help_text
    assert "no port opening" in help_text
