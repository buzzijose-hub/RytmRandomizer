"""Tests for passive live GUI action-reducer reporting."""

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
    bpm: float = 141.0,
    low_end_weight: float = 0.69,
    spectral_brightness: float = 0.47,
    texture_noise: float = 0.62,
    energy_arc: tuple[float, ...] = (0.24, 0.52, 0.84),
):
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.MEDIUM,
        bpm=bpm,
        tempo_stability=0.88,
        kick_density=0.78,
        percussion_density=0.73,
        low_end_weight=low_end_weight,
        spectral_brightness=spectral_brightness,
        texture_noise=texture_noise,
        energy_arc=energy_arc,
        content_hash="",
        derived_at="2026-05-23T13:15:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _interaction_script(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_action_reducer import (
        build_style_performance_arc_live_gui_interaction_script_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_interaction_script_report(
        feature_report=_feature_report(),
        capture_feature_report=_feature_report(
            bpm=141.5,
            low_end_weight=0.70,
            spectral_brightness=0.48,
            texture_noise=0.60,
            energy_arc=(0.26, 0.54, 0.86),
        ),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=1,
        match_limit=2,
        take_count=2,
        queue_label="Warehouse reducer queue",
        capture_prefix="warehouse",
        slot_key="capture-001",
        sidecar_label="Warehouse sidecar",
        screen_label="Warehouse screen",
        render_target="desktop-sidecar",
        density="standard",
        overlay_label="Warehouse overlay",
        frame_label="Warehouse frame",
        interaction_label="Warehouse interactions",
    )


def test_live_gui_action_reducer_builds_transitions_from_interaction_script(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_gui_action_reducer import (
        build_style_performance_arc_live_gui_action_reducer_from_interaction_script,
        format_style_performance_arc_live_gui_action_reducer_report,
        to_style_performance_arc_live_gui_action_reducer_json,
    )

    interaction_script = _interaction_script(tmp_path)
    report = build_style_performance_arc_live_gui_action_reducer_from_interaction_script(
        interaction_script,
        reducer_label="Warehouse action reducer",
    )

    assert report.reducer_version == "live-gui-action-reducer-v1"
    assert len(report.reducer_id) == 16
    assert report.script_id == interaction_script.script_id
    assert report.frame_id == interaction_script.frame_id
    assert report.reducer_status == "ready"
    assert report.reducer_label == "Warehouse action reducer"
    assert [transition.order for transition in report.transitions] == list(
        range(len(report.transitions))
    )
    assert {transition.control_key for transition in report.transitions} >= {
        "control-review-capture",
        "control-compare-reference",
        "control-accept-capture",
        "control-arm-hardware",
        "control-open-midi-port",
    }
    review_transition = next(
        transition
        for transition in report.transitions
        if transition.control_key == "control-review-capture"
    )
    assert review_transition.allowed is True
    assert review_transition.from_state == "enabled"
    assert review_transition.to_state == "capture-review-open"
    hardware_transition = next(
        transition
        for transition in report.transitions
        if transition.control_key == "control-arm-hardware"
    )
    assert hardware_transition.allowed is False
    assert hardware_transition.to_state == "blocked"
    assert "passive report" in hardware_transition.reason
    assert "no GUI reducer dispatch" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-action-reducer-report"
    )
    assert "style-performance-arc-live-gui-interaction-script-report" not in (
        report.replay_commands[0]
    )
    assert "--interaction-label 'Warehouse interactions'" in report.replay_commands[0]
    assert "--reducer-label 'Warehouse action reducer'" in report.replay_commands[0]
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-interaction-script-report"
    )

    lines = format_style_performance_arc_live_gui_action_reducer_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI action reducer"
    assert "Live GUI action reducer summary:" in lines
    assert "GUI action transitions:" in lines
    assert "Passive GUI reducer metadata only" in text
    assert "- no GUI reducer dispatch" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_action_reducer_json(report)
    reducer = payload["live_gui_action_reducer"]
    assert reducer["reducer_version"] == "live-gui-action-reducer-v1"
    assert reducer["reducer_id"] == report.reducer_id
    assert reducer["script_id"] == interaction_script.script_id
    assert reducer["transitions"][0]["control_key"] == "control-review-capture"
    assert payload["live_gui_interaction_script"]["script_id"] == interaction_script.script_id
    assert payload["live_gui_analyzer_frame"]["frame_id"] == interaction_script.frame_id
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_action_reducer_status_and_replay_fallback_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_action_reducer import (
        build_style_performance_arc_live_gui_action_reducer_from_interaction_script,
        build_style_performance_arc_live_gui_interaction_script_from_frame,
    )

    interaction_script = _interaction_script(tmp_path)
    blocked_script = replace(interaction_script, script_status="blocked")
    blocked_report = build_style_performance_arc_live_gui_action_reducer_from_interaction_script(
        blocked_script
    )
    assert blocked_report.reducer_status == "blocked"
    assert all(not transition.allowed for transition in blocked_report.transitions)
    assert "hold action reducer before GUI controller binding" in blocked_report.blocked_actions

    review_script = build_style_performance_arc_live_gui_interaction_script_from_frame(
        replace(interaction_script.frame, frame_status="review-needed")
    )
    review_report = build_style_performance_arc_live_gui_action_reducer_from_interaction_script(
        review_script
    )
    repeat_transition = next(
        transition
        for transition in review_report.transitions
        if transition.control_key == "control-repeat-take"
    )
    assert review_report.reducer_status == "review-needed"
    assert repeat_transition.allowed is True
    assert repeat_transition.to_state == "repeat-take-queued"

    fallback_script = replace(
        interaction_script,
        replay_commands=("python -m rytm_randomizer.cli upstream",),
    )
    fallback_report = build_style_performance_arc_live_gui_action_reducer_from_interaction_script(
        fallback_script
    )
    assert fallback_report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-action-reducer-report"
    )

    already_labeled_script = replace(
        interaction_script,
        replay_commands=(
            "python -m rytm_randomizer.cli "
            "style-performance-arc-live-gui-interaction-script-report "
            "--reducer-label 'Existing'",
        ),
    )
    already_labeled_report = (
        build_style_performance_arc_live_gui_action_reducer_from_interaction_script(
            already_labeled_script
        )
    )
    assert already_labeled_report.replay_commands[0].count("--reducer-label") == 1

    empty_replay_report = (
        build_style_performance_arc_live_gui_action_reducer_from_interaction_script(
            replace(interaction_script, replay_commands=())
        )
    )
    assert empty_replay_report.replay_commands == (
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-action-reducer-report "
        "--reducer-label 'Live GUI action reducer'",
    )

    with pytest.raises(ValueError, match="reducer_label"):
        build_style_performance_arc_live_gui_action_reducer_from_interaction_script(
            interaction_script,
            reducer_label=" ",
        )


def test_live_gui_action_reducer_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_action_reducer import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ACTION_REDUCER_CLI_COMMAND,
        build_style_performance_arc_live_gui_action_reducer_report,
        to_style_performance_arc_live_gui_action_reducer_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = STYLE_PERFORMANCE_ARC_LIVE_GUI_ACTION_REDUCER_CLI_COMMAND.args_parser(
        [
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--frame-label",
            "Warehouse frame",
            "--interaction-label",
            "Warehouse interactions",
            "--reducer-label",
            "Warehouse reducer",
            "--json",
        ]
    )
    assert parsed["interaction_label"] == "Warehouse interactions"
    assert parsed["reducer_label"] == "Warehouse reducer"
    assert parsed["json_output"] is True

    with pytest.raises(ValueError, match="usage"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_ACTION_REDUCER_CLI_COMMAND.args_parser(["--reducer-label"])

    report = build_style_performance_arc_live_gui_action_reducer_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        capture_description="captured warehouse take",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        interaction_label="Warehouse interactions",
        reducer_label="Warehouse reducer",
    )
    payload = to_style_performance_arc_live_gui_action_reducer_json(report)
    assert payload["live_gui_action_reducer"]["reducer_label"] == "Warehouse reducer"

    rc = main(
        [
            "style-performance-arc-live-gui-action-reducer-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--interaction-label",
            "Warehouse interactions",
            "--reducer-label",
            "Warehouse reducer",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    cli_payload = json.loads(captured.out)
    assert cli_payload["live_gui_action_reducer"]["reducer_label"] == "Warehouse reducer"
    assert captured.err == ""

    rc = main(
        [
            "style-performance-arc-live-gui-action-reducer-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--reducer-label",
            "Warehouse reducer",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "Live GUI action reducer summary:" in captured.out
    assert "GUI action transitions:" in captured.out
    assert captured.err == ""

    rc = main(
        [
            "style-performance-arc-live-gui-action-reducer-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--reducer-label",
            " ",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "reducer_label" in captured.err

    rc = main(
        [
            "style-performance-arc-live-gui-action-reducer-report",
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

    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main({[
        "style-performance-arc-live-gui-action-reducer-report",
        "--description",
        "Jeff Mills Oscar Mulero Birmingham pressure",
        "--capture-description",
        "captured warehouse take",
        "--rytm",
        str(rytm_path),
        "--analog-four",
        str(a4_path),
        "--reducer-label",
        "Warehouse reducer",
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


def test_live_gui_action_reducer_help_mentions_passive_contract():
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("style-performance-arc-live-gui-action-reducer-report")

    assert help_text.startswith(
        "RytmRandomizer passive CLI: style-performance-arc-live-gui-action-reducer-report"
    )
    assert "GUI action reducer" in help_text
    assert "no GUI event dispatch" in help_text
    assert "no MIDI sending" in help_text
