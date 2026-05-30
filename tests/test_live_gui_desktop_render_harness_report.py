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
        derived_at="2026-05-23T19:00:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _render_contract(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_gui_desktop_render_contract import (
        build_style_performance_arc_live_gui_desktop_render_contract_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_desktop_render_contract_report(
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
        queue_label="Warehouse render queue",
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
        readiness_label="Warehouse readiness packet",
        bridge_label="Warehouse implementation bridge",
        blueprint_label="Warehouse desktop blueprint",
        desktop_shell="operator-dashboard",
        app_plan_label="Warehouse desktop app plan",
        framework_target="desktop-python",
        component_contract_label="Warehouse component contract",
        selector_prefix="warehouse-live",
        view_model_label="Warehouse desktop view model",
        state_prefix="warehouse-state",
        render_contract_label="Warehouse render contract",
    )


def test_live_gui_desktop_render_harness_builds_from_render_contract(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_desktop_render_harness import (
        build_style_performance_arc_live_gui_desktop_render_harness_from_render_contract,
        format_style_performance_arc_live_gui_desktop_render_harness_report,
        to_style_performance_arc_live_gui_desktop_render_harness_json,
    )

    render_contract = _render_contract(tmp_path)
    report = build_style_performance_arc_live_gui_desktop_render_harness_from_render_contract(
        render_contract,
        render_harness_label="Warehouse render harness",
        runner_label="Warehouse passive runner",
    )

    assert report.render_harness_version == "live-gui-desktop-render-harness-v1"
    assert len(report.render_harness_id) == 16
    assert report.render_harness_label == "Warehouse render harness"
    assert report.runner_label == "Warehouse passive runner"
    assert report.render_harness_status == "ready"
    assert report.render_contract_id == render_contract.render_contract_id
    assert report.view_model_id == render_contract.view_model_id
    assert report.framework_target == "desktop-python"
    assert report.selected_arc_key == render_contract.selected_arc_key
    assert report.scope == render_contract.scope
    assert "surface harnesses" in report.surface_harness_summary
    assert "binding harnesses" in report.binding_harness_summary
    assert "style-token checks" in report.style_token_check_summary
    assert "harness assertions" in report.assertion_summary
    assert {surface.component_key for surface in report.surface_harnesses} >= {
        "current-cue-panel",
        "machine-panels",
        "analyzer-overlay",
        "capture-review-panel",
    }
    current_cue = next(
        surface
        for surface in report.surface_harnesses
        if surface.component_key == "current-cue-panel"
    )
    assert current_cue.harness_key == "harness-surface-current-cue-panel"
    assert current_cue.render_surface_key == "surface-current-cue-panel"
    assert current_cue.selector == "data-testid=warehouse-live-current-cue-panel"
    assert current_cue.fixture_key == "fixture-surface-current-cue-panel"
    assert current_cue.assertion_key == "assert-surface-current-cue-panel"
    assert current_cue.mount_policy == "metadata-only-no-mount"
    assert current_cue.runner_enabled is False
    assert current_cue.passive is True
    source_binding = next(
        binding
        for binding in report.binding_harnesses
        if binding.binding_key == "harness-binding-render-binding-current-cue-panel-sourceData"
    )
    assert source_binding.surface_harness_key == current_cue.harness_key
    assert source_binding.state_key == current_cue.state_key
    assert source_binding.prop_name == "sourceData"
    assert source_binding.assertion_key == "assert-binding-current-cue-panel-sourceData"
    assert source_binding.evaluation_policy == "metadata-only-no-evaluation"
    style_check = next(
        check for check in report.style_token_checks if check.token_key == "token-surface"
    )
    assert style_check.framework_target == "desktop-python"
    assert style_check.check_policy == "metadata-only-no-style-injection"
    assert style_check.passive is True
    assert any(
        assertion.assertion_key == "assert-render-contract-status" and assertion.status == "ready"
        for assertion in report.harness_assertions
    )
    assert any(
        assertion.assertion_key == "assert-no-runner-execution" and assertion.status == "ready"
        for assertion in report.harness_assertions
    )
    assert "no GUI test runner execution" in report.blocked_actions
    assert "no browser automation execution" in report.blocked_actions
    assert "no screenshot capture" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-desktop-render-harness-report"
    )
    assert "--render-harness-label 'Warehouse render harness'" in report.replay_commands[0]
    assert "--runner-label 'Warehouse passive runner'" in report.replay_commands[0]
    assert report.replay_commands[1] == render_contract.replay_commands[0]

    lines = format_style_performance_arc_live_gui_desktop_render_harness_report(report)
    text = "\n".join(lines)
    assert lines[0] == (
        "RytmRandomizer passive style performance arc live GUI desktop render harness"
    )
    assert "Live GUI desktop render harness summary:" in lines
    assert "Surface harnesses:" in lines
    assert "Binding harnesses:" in lines
    assert "Style-token checks:" in lines
    assert "Harness assertions:" in lines
    assert "Passive GUI desktop render-harness metadata only" in text
    assert "- no GUI test runner execution" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_desktop_render_harness_json(report)
    harness = payload["live_gui_desktop_render_harness"]
    assert harness["render_harness_version"] == "live-gui-desktop-render-harness-v1"
    assert harness["render_harness_id"] == report.render_harness_id
    assert harness["render_contract_id"] == render_contract.render_contract_id
    assert harness["surface_harnesses"][0]["harness_key"] == report.surface_harnesses[0].harness_key
    assert harness["binding_harnesses"][0]["evaluation_policy"] == ("metadata-only-no-evaluation")
    assert harness["style_token_checks"][0]["check_policy"] == ("metadata-only-no-style-injection")
    assert "live_gui_desktop_render_contract" in payload
    assert "live_gui_desktop_view_model" in payload
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_desktop_render_harness_status_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_desktop_render_harness import (
        _harness_assertions,
        _render_harness_status,
        build_style_performance_arc_live_gui_desktop_render_harness_from_render_contract,
    )

    render_contract = _render_contract(tmp_path)
    blocked_report = (
        build_style_performance_arc_live_gui_desktop_render_harness_from_render_contract(
            replace(render_contract, render_contract_status="blocked", render_surfaces=())
        )
    )
    assert blocked_report.render_harness_status == "blocked"
    assert "hold render harness until desktop render contract is clear" in (
        blocked_report.blocked_actions
    )
    assert any(
        assertion.assertion_key == "assert-render-contract-status" and assertion.status == "blocked"
        for assertion in blocked_report.harness_assertions
    )

    review_report = (
        build_style_performance_arc_live_gui_desktop_render_harness_from_render_contract(
            replace(render_contract, render_contract_status="review-needed")
        )
    )
    assert review_report.render_harness_status == "review-needed"
    assert any(
        assertion.status == "review-needed" for assertion in review_report.harness_assertions
    )

    no_replay_report = (
        build_style_performance_arc_live_gui_desktop_render_harness_from_render_contract(
            replace(render_contract, replay_commands=())
        )
    )
    assert no_replay_report.render_harness_status == "review-needed"
    assert no_replay_report.replay_commands == ()

    malformed_replay_report = (
        build_style_performance_arc_live_gui_desktop_render_harness_from_render_contract(
            replace(
                render_contract,
                replay_commands=("python -m rytm_randomizer.cli unrelated-report",),
            )
        )
    )
    assert malformed_replay_report.render_harness_status == "review-needed"
    assert malformed_replay_report.replay_commands == (
        "python -m rytm_randomizer.cli unrelated-report",
    )

    assertions_with_empty_surfaces = _harness_assertions(
        render_contract,
        surface_harnesses=(),
        binding_harnesses=(),
        style_token_checks=(),
        replay_commands=(),
    )
    assert _render_harness_status(render_contract, assertions_with_empty_surfaces) == "blocked"
    assert any(
        assertion.assertion_key == "assert-surface-harness-coverage"
        and assertion.status == "blocked"
        for assertion in assertions_with_empty_surfaces
    )

    with pytest.raises(ValueError, match="render_harness_label"):
        build_style_performance_arc_live_gui_desktop_render_harness_from_render_contract(
            render_contract,
            render_harness_label=" ",
        )
    with pytest.raises(ValueError, match="runner_label"):
        build_style_performance_arc_live_gui_desktop_render_harness_from_render_contract(
            render_contract,
            runner_label=" ",
        )


def test_live_gui_desktop_render_harness_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_desktop_render_harness import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_RENDER_HARNESS_CLI_COMMAND,
        build_style_performance_arc_live_gui_desktop_render_harness_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_RENDER_HARNESS_CLI_COMMAND.args_parser(
        [
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--render-contract-label",
            "Warehouse render contract",
            "--render-harness-label",
            "Warehouse render harness",
            "--runner-label",
            "Warehouse passive runner",
            "--json",
        ]
    )
    assert parsed["render_contract_label"] == "Warehouse render contract"
    assert parsed["render_harness_label"] == "Warehouse render harness"
    assert parsed["runner_label"] == "Warehouse passive runner"
    assert parsed["json_output"] is True

    with pytest.raises(ValueError, match="usage"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_DESKTOP_RENDER_HARNESS_CLI_COMMAND.args_parser(
            ["--runner-label"]
        )

    report = build_style_performance_arc_live_gui_desktop_render_harness_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        capture_description="captured warehouse take",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        render_contract_label="Warehouse render contract",
        render_harness_label="Warehouse render harness",
        runner_label="Warehouse passive runner",
    )
    assert report.render_harness_label == "Warehouse render harness"
    assert report.render_contract.render_contract_label == "Warehouse render contract"

    rc = main(
        [
            "style-performance-arc-live-gui-desktop-render-harness-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--render-harness-label",
            "Warehouse render harness",
            "--runner-label",
            "Warehouse passive runner",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["live_gui_desktop_render_harness"]["render_harness_label"] == (
        "Warehouse render harness"
    )
    assert "live_gui_desktop_render_contract" in payload

    rc = main(
        [
            "style-performance-arc-live-gui-desktop-render-harness-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--render-harness-label",
            "Warehouse render harness",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "Live GUI desktop render harness summary:" in captured.out
    assert "Surface harnesses:" in captured.out
    assert captured.err == ""

    rc = main(
        [
            "style-performance-arc-live-gui-desktop-render-harness-report",
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
            "style-performance-arc-live-gui-desktop-render-harness-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--render-harness-label",
            " ",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "render_harness_label" in captured.err


def test_live_gui_desktop_render_harness_cli_json_is_passive(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    command = [
        sys.executable,
        "-m",
        "rytm_randomizer.cli",
        "style-performance-arc-live-gui-desktop-render-harness-report",
        "--description",
        "Jeff Mills Oscar Mulero Birmingham pressure",
        "--capture-description",
        "captured warehouse take with tight low end and building pressure",
        "--rytm",
        str(rytm_path),
        "--analog-four",
        str(a4_path),
        "--cue",
        "1",
        "--lookahead",
        "2",
        "--matches",
        "2",
        "--takes",
        "2",
        "--slot",
        "capture-001",
        "--capture-prefix",
        "warehouse",
        "--sidecar-label",
        "Warehouse sidecar",
        "--screen-label",
        "Warehouse screen",
        "--render-target",
        "desktop-sidecar",
        "--density",
        "standard",
        "--overlay-label",
        "Warehouse overlay",
        "--frame-label",
        "Warehouse frame",
        "--interaction-label",
        "Warehouse interactions",
        "--reducer-label",
        "Warehouse reducer",
        "--controller-label",
        "Warehouse controller",
        "--playback-label",
        "Warehouse playback",
        "--validation-label",
        "Warehouse validation",
        "--harness-label",
        "Warehouse harness",
        "--readiness-label",
        "Warehouse readiness",
        "--bridge-label",
        "Warehouse implementation bridge",
        "--blueprint-label",
        "Warehouse desktop blueprint",
        "--desktop-shell",
        "operator-dashboard",
        "--app-plan-label",
        "Warehouse desktop app plan",
        "--framework-target",
        "desktop-python",
        "--component-contract-label",
        "Warehouse component contract",
        "--selector-prefix",
        "warehouse-live",
        "--view-model-label",
        "Warehouse desktop view model",
        "--state-prefix",
        "warehouse-state",
        "--render-contract-label",
        "Warehouse render contract",
        "--render-harness-label",
        "Warehouse render harness",
        "--runner-label",
        "Warehouse passive runner",
        "--json",
    ]
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["live_gui_desktop_render_harness"]["render_harness_status"] in {
        "ready",
        "review-needed",
        "blocked",
    }
    assert payload["live_gui_desktop_render_harness"]["render_harness_label"] == (
        "Warehouse render harness"
    )
    assert "live_gui_desktop_render_contract" in payload
    assert completed.stderr == ""

    module_snapshot = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.reports.live_gui_desktop_render_harness; "
                "print('\\n'.join(sorted(sys.modules)))"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert module_snapshot.returncode == 0, module_snapshot.stderr
    imported_modules = set(module_snapshot.stdout.splitlines())
    assert not imported_modules.intersection(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)


def test_live_gui_desktop_render_harness_help_mentions_passive_contract():
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("style-performance-arc-live-gui-desktop-render-harness-report")
    assert help_text.startswith(
        "RytmRandomizer passive CLI: "
        "style-performance-arc-live-gui-desktop-render-harness-report"
    )
    assert "GUI desktop render harness" in help_text
    assert "no GUI launch" in help_text
    assert "no MIDI sending" in help_text
    assert "no port opening" in help_text
