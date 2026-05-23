"""Tests for passive live GUI controller-state reporting."""

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
        derived_at="2026-05-23T14:30:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _action_reducer(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_action_reducer import (
        build_style_performance_arc_live_gui_action_reducer_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_action_reducer_report(
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
        queue_label="Warehouse controller queue",
        capture_prefix="warehouse",
        slot_key="capture-001",
        sidecar_label="Warehouse sidecar",
        screen_label="Warehouse screen",
        render_target="desktop-sidecar",
        density="standard",
        overlay_label="Warehouse overlay",
        frame_label="Warehouse frame",
        interaction_label="Warehouse interactions",
        reducer_label="Warehouse reducer",
    )


def test_live_gui_controller_state_builds_view_model_from_action_reducer(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_gui_controller_state import (
        build_style_performance_arc_live_gui_controller_state_from_action_reducer,
        format_style_performance_arc_live_gui_controller_state_report,
        to_style_performance_arc_live_gui_controller_state_json,
    )

    action_reducer = _action_reducer(tmp_path)
    report = build_style_performance_arc_live_gui_controller_state_from_action_reducer(
        action_reducer,
        controller_label="Warehouse controller state",
    )

    assert report.controller_version == "live-gui-controller-state-v1"
    assert len(report.controller_id) == 16
    assert report.reducer_id == action_reducer.reducer_id
    assert report.script_id == action_reducer.script_id
    assert report.controller_status == "ready"
    assert report.controller_label == "Warehouse controller state"
    assert len(report.control_states) == len(action_reducer.transitions)
    assert [state.order for state in report.control_states] == list(
        range(len(report.control_states))
    )
    review_state = next(
        state for state in report.control_states if state.control_key == "control-review-capture"
    )
    assert review_state.enabled is True
    assert review_state.current_state == "capture-review-open"
    assert review_state.reducer_transition_key == "action-transition-control-review-capture"
    hardware_state = next(
        state for state in report.control_states if state.control_key == "control-arm-hardware"
    )
    assert hardware_state.enabled is False
    assert hardware_state.current_state == "blocked"
    assert "control-arm-hardware" in report.blocked_controls
    assert {action.control_key for action in report.queued_actions} >= {
        "control-review-capture",
        "control-compare-reference",
    }
    assert "control-arm-hardware" not in {action.control_key for action in report.queued_actions}
    assert "no GUI controller dispatch" in report.blocked_actions
    assert "no GUI state-store mutation" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-controller-state-report"
    )
    assert "style-performance-arc-live-gui-action-reducer-report" not in (report.replay_commands[0])
    assert "--reducer-label 'Warehouse reducer'" in report.replay_commands[0]
    assert "--controller-label 'Warehouse controller state'" in report.replay_commands[0]
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-action-reducer-report"
    )

    lines = format_style_performance_arc_live_gui_controller_state_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI controller state"
    assert "Live GUI controller state summary:" in lines
    assert "GUI control states:" in lines
    assert "Queued allowed GUI actions:" in lines
    assert "Passive GUI controller-state metadata only" in text
    assert "- no GUI controller dispatch" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_controller_state_json(report)
    controller = payload["live_gui_controller_state"]
    assert controller["controller_version"] == "live-gui-controller-state-v1"
    assert controller["controller_id"] == report.controller_id
    assert controller["reducer_id"] == action_reducer.reducer_id
    assert controller["control_states"][0]["control_key"] == "control-review-capture"
    assert payload["live_gui_action_reducer"]["reducer_id"] == action_reducer.reducer_id
    assert payload["live_gui_interaction_script"]["script_id"] == action_reducer.script_id
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_controller_state_status_and_replay_fallback_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_controller_state import (
        build_style_performance_arc_live_gui_controller_state_from_action_reducer,
    )

    action_reducer = _action_reducer(tmp_path)
    blocked_report = build_style_performance_arc_live_gui_controller_state_from_action_reducer(
        replace(action_reducer, reducer_status="blocked")
    )
    assert blocked_report.controller_status == "blocked"
    assert all(not state.enabled for state in blocked_report.control_states)
    assert not blocked_report.queued_actions
    assert "hold controller state before GUI runtime binding" in blocked_report.blocked_actions

    review_report = build_style_performance_arc_live_gui_controller_state_from_action_reducer(
        replace(action_reducer, reducer_status="review-needed")
    )
    assert review_report.controller_status == "review-needed"
    assert any(state.enabled for state in review_report.control_states)

    malformed_replay_report = (
        build_style_performance_arc_live_gui_controller_state_from_action_reducer(
            replace(action_reducer, replay_commands=("python -m rytm_randomizer.cli upstream",))
        )
    )
    assert malformed_replay_report.replay_commands == ()

    already_labeled_report = (
        build_style_performance_arc_live_gui_controller_state_from_action_reducer(
            replace(
                action_reducer,
                replay_commands=(
                    "python -m rytm_randomizer.cli "
                    "style-performance-arc-live-gui-action-reducer-report "
                    "--controller-label 'Existing'",
                ),
            )
        )
    )
    assert already_labeled_report.replay_commands[0].count("--controller-label") == 1

    empty_replay_report = build_style_performance_arc_live_gui_controller_state_from_action_reducer(
        replace(action_reducer, replay_commands=())
    )
    assert empty_replay_report.replay_commands == ()

    with pytest.raises(ValueError, match="controller_label"):
        build_style_performance_arc_live_gui_controller_state_from_action_reducer(
            action_reducer,
            controller_label=" ",
        )


def test_live_gui_controller_state_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_controller_state import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_CONTROLLER_STATE_CLI_COMMAND,
        build_style_performance_arc_live_gui_controller_state_report,
        to_style_performance_arc_live_gui_controller_state_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = STYLE_PERFORMANCE_ARC_LIVE_GUI_CONTROLLER_STATE_CLI_COMMAND.args_parser(
        [
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
            "--controller-label",
            "Warehouse controller",
            "--json",
        ]
    )
    assert parsed["reducer_label"] == "Warehouse reducer"
    assert parsed["controller_label"] == "Warehouse controller"
    assert parsed["json_output"] is True

    with pytest.raises(ValueError, match="usage"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_CONTROLLER_STATE_CLI_COMMAND.args_parser(
            ["--controller-label"]
        )

    report = build_style_performance_arc_live_gui_controller_state_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        capture_description="captured warehouse take",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        reducer_label="Warehouse reducer",
        controller_label="Warehouse controller",
    )
    payload = to_style_performance_arc_live_gui_controller_state_json(report)
    assert payload["live_gui_controller_state"]["controller_label"] == "Warehouse controller"

    rc = main(
        [
            "style-performance-arc-live-gui-controller-state-report",
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
            "--controller-label",
            "Warehouse controller",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    cli_payload = json.loads(captured.out)
    assert cli_payload["live_gui_controller_state"]["controller_label"] == ("Warehouse controller")
    assert captured.err == ""

    rc = main(
        [
            "style-performance-arc-live-gui-controller-state-report",
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
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "Live GUI controller state summary:" in captured.out
    assert "GUI control states:" in captured.out
    assert captured.err == ""

    rc = main(
        [
            "style-performance-arc-live-gui-controller-state-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--controller-label",
            " ",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "controller_label" in captured.err

    rc = main(
        [
            "style-performance-arc-live-gui-controller-state-report",
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
        "style-performance-arc-live-gui-controller-state-report",
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


def test_live_gui_controller_state_help_mentions_passive_contract():
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("style-performance-arc-live-gui-controller-state-report")

    assert help_text.startswith(
        "RytmRandomizer passive CLI: style-performance-arc-live-gui-controller-state-report"
    )
    assert "GUI controller state" in help_text
    assert "no GUI event dispatch" in help_text
    assert "no MIDI sending" in help_text
