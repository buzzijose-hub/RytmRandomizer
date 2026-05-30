"""Tests for passive live GUI playback transcript reporting."""

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
        derived_at="2026-05-23T15:30:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _controller_state(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_controller_state import (
        build_style_performance_arc_live_gui_controller_state_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_controller_state_report(
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
        queue_label="Warehouse playback queue",
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
    )


def test_live_gui_playback_transcript_builds_timeline_from_controller_state(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_gui_playback_transcript import (
        build_style_performance_arc_live_gui_playback_transcript_from_controller_state,
        format_style_performance_arc_live_gui_playback_transcript_report,
        to_style_performance_arc_live_gui_playback_transcript_json,
    )

    controller_state = _controller_state(tmp_path)
    report = build_style_performance_arc_live_gui_playback_transcript_from_controller_state(
        controller_state,
        playback_label="Warehouse playback transcript",
    )

    assert report.playback_version == "live-gui-playback-transcript-v1"
    assert len(report.playback_id) == 16
    assert report.controller_id == controller_state.controller_id
    assert report.reducer_id == controller_state.reducer_id
    assert report.playback_status == "ready"
    assert report.playback_label == "Warehouse playback transcript"
    assert report.selected_arc_key == controller_state.selected_arc_key
    assert report.scope == controller_state.scope
    assert report.events[0].event_key == "playback-event-bootstrap-screen-contract"
    assert report.events[0].phase == "bootstrap"
    assert report.events[0].source_id == controller_state.screen_contract_id
    assert report.events[0].passive is True
    phases = {event.phase for event in report.events}
    assert {
        "bootstrap",
        "hydrate",
        "queue-gui-action",
        "assert",
        "safety",
    } <= phases
    assert any(
        event.source_key == "control-review-capture" and event.phase == "queue-gui-action"
        for event in report.events
    )
    assert any(assertion.target == "blocked_actions" for assertion in report.assertions)
    assert any(assertion.expected == "no MIDI sending" for assertion in report.assertions)
    assert "no GUI event dispatch" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-playback-transcript-report"
    )
    assert "style-performance-arc-live-gui-controller-state-report" not in (
        report.replay_commands[0]
    )
    assert "--controller-label 'Warehouse controller'" in report.replay_commands[0]
    assert "--playback-label 'Warehouse playback transcript'" in report.replay_commands[0]
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-controller-state-report"
    )

    lines = format_style_performance_arc_live_gui_playback_transcript_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI playback transcript"
    assert "Live GUI playback transcript summary:" in lines
    assert "Playback timeline:" in lines
    assert "GUI playback assertions:" in lines
    assert "Passive GUI playback transcript metadata only" in text
    assert "- no GUI event dispatch" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_playback_transcript_json(report)
    playback = payload["live_gui_playback_transcript"]
    assert playback["playback_version"] == "live-gui-playback-transcript-v1"
    assert playback["playback_id"] == report.playback_id
    assert playback["controller_id"] == controller_state.controller_id
    assert playback["events"][0]["event_key"] == "playback-event-bootstrap-screen-contract"
    assert payload["live_gui_controller_state"]["controller_id"] == controller_state.controller_id
    assert payload["live_gui_action_reducer"]["reducer_id"] == controller_state.reducer_id
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_playback_transcript_status_and_replay_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_playback_transcript import (
        build_style_performance_arc_live_gui_playback_transcript_from_controller_state,
    )

    controller_state = _controller_state(tmp_path)
    blocked_report = build_style_performance_arc_live_gui_playback_transcript_from_controller_state(
        replace(controller_state, controller_status="blocked", queued_actions=())
    )
    assert blocked_report.playback_status == "blocked"
    assert not [event for event in blocked_report.events if event.phase == "queue-gui-action"]
    assert "hold playback transcript before GUI runtime binding" in blocked_report.blocked_actions

    review_report = build_style_performance_arc_live_gui_playback_transcript_from_controller_state(
        replace(controller_state, controller_status="review-needed")
    )
    assert review_report.playback_status == "review-needed"
    assert any(event.phase == "assert" for event in review_report.events)

    for malformed_command in (
        "python -m rytm_randomizer.cli upstream",
        "echo style-performance-arc-live-gui-controller-state-report",
        "style-performance-arc-live-gui-controller-state-report --description x",
    ):
        malformed_replay_report = (
            build_style_performance_arc_live_gui_playback_transcript_from_controller_state(
                replace(controller_state, replay_commands=(malformed_command,))
            )
        )
        assert malformed_replay_report.replay_commands == ()

    empty_replay_report = (
        build_style_performance_arc_live_gui_playback_transcript_from_controller_state(
            replace(controller_state, replay_commands=())
        )
    )
    assert empty_replay_report.replay_commands == ()

    already_labeled_report = (
        build_style_performance_arc_live_gui_playback_transcript_from_controller_state(
            replace(
                controller_state,
                replay_commands=(
                    "python -m rytm_randomizer.cli "
                    "style-performance-arc-live-gui-controller-state-report "
                    "--playback-label 'Existing'",
                ),
            )
        )
    )
    assert already_labeled_report.replay_commands[0].count("--playback-label") == 1

    with pytest.raises(ValueError, match="playback_label"):
        build_style_performance_arc_live_gui_playback_transcript_from_controller_state(
            controller_state,
            playback_label=" ",
        )


def test_live_gui_playback_transcript_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_playback_transcript import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_PLAYBACK_TRANSCRIPT_CLI_COMMAND,
        build_style_performance_arc_live_gui_playback_transcript_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = STYLE_PERFORMANCE_ARC_LIVE_GUI_PLAYBACK_TRANSCRIPT_CLI_COMMAND.args_parser(
        [
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--controller-label",
            "Warehouse controller",
            "--playback-label",
            "Warehouse playback",
            "--json",
        ]
    )
    assert parsed["controller_label"] == "Warehouse controller"
    assert parsed["playback_label"] == "Warehouse playback"
    assert parsed["json_output"] is True

    with pytest.raises(ValueError, match="usage"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_PLAYBACK_TRANSCRIPT_CLI_COMMAND.args_parser(
            ["--playback-label"]
        )

    report = build_style_performance_arc_live_gui_playback_transcript_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        capture_description="captured warehouse take",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        controller_label="Warehouse controller",
        playback_label="Warehouse playback",
    )
    assert report.playback_label == "Warehouse playback"

    rc = main(
        [
            "style-performance-arc-live-gui-playback-transcript-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--controller-label",
            "Warehouse controller",
            "--playback-label",
            "Warehouse playback",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["live_gui_playback_transcript"]["playback_label"] == "Warehouse playback"
    assert "live_gui_controller_state" in payload

    rc = main(
        [
            "style-performance-arc-live-gui-playback-transcript-report",
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
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "Live GUI playback transcript summary:" in captured.out
    assert "Playback timeline:" in captured.out
    assert captured.err == ""

    rc = main(
        [
            "style-performance-arc-live-gui-playback-transcript-report",
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
            "style-performance-arc-live-gui-playback-transcript-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--playback-label",
            " ",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "playback_label" in captured.err

    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main({[
        "style-performance-arc-live-gui-playback-transcript-report",
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


def test_live_gui_playback_transcript_help_mentions_passive_contract():
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("style-performance-arc-live-gui-playback-transcript-report")
    assert help_text.startswith(
        "RytmRandomizer passive CLI: " "style-performance-arc-live-gui-playback-transcript-report"
    )
    assert "GUI playback transcript" in help_text
    assert "no GUI launch" in help_text
    assert "no MIDI sending" in help_text
    assert "no port opening" in help_text
