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
        derived_at="2026-05-23T22:00:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _render_harness(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_desktop_render_harness import (
        build_style_performance_arc_live_gui_desktop_render_harness_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_desktop_render_harness_report(
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
        render_harness_label="Warehouse render harness",
        runner_label="Warehouse passive runner",
    )


def test_live_gui_cockpit_boundary_readiness_builds_from_render_harness(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_cockpit_boundary_readiness import (
        build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness,
        format_style_performance_arc_live_gui_cockpit_boundary_readiness_report,
        to_style_performance_arc_live_gui_cockpit_boundary_readiness_json,
    )

    render_harness = _render_harness(tmp_path)
    report = build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness(
        render_harness,
        boundary_label="Warehouse cockpit boundary",
        hardware_entrypoint="python -m rytm_randomizer.app --arm",
        passive_entrypoint="python -m rytm_randomizer.cli",
        ws_port_env="RYTM_RAND_WS_PORT",
    )

    assert report.boundary_readiness_version == "live-gui-cockpit-boundary-readiness-v1"
    assert len(report.boundary_readiness_id) == 16
    assert report.boundary_label == "Warehouse cockpit boundary"
    assert report.boundary_status == "ready"
    assert report.render_harness_id == render_harness.render_harness_id
    assert report.render_contract_id == render_harness.render_contract_id
    assert report.view_model_id == render_harness.view_model_id
    assert report.scope == "dual"
    assert report.hardware_entrypoint == "python -m rytm_randomizer.app --arm"
    assert report.passive_entrypoint == "python -m rytm_randomizer.cli"
    assert report.ws_port_env == "RYTM_RAND_WS_PORT"
    assert report.device_scope_summary == (
        "Rytm 12-pad and Analog Four 4-track scope is explicit for future cockpit work."
    )
    assert report.env_var_summary == (
        "RYTM_RAND_WS_PORT documentation targets CONTRIBUTING.md, "
        "docs/LOCAL_DEV_TOOLING_NOTES.md, and future COCKPIT_QUICKSTART.md."
    )
    assert report.toolchain_summary == (
        "Future cockpit toolchain remains optional and lockfile-governed."
    )
    assert {scope.device_key for scope in report.device_scope_checks} == {
        "analog-rytm-mkii",
        "analog-four-mkii",
    }
    rytm_scope = next(
        scope for scope in report.device_scope_checks if scope.device_key == "analog-rytm-mkii"
    )
    assert rytm_scope.required_lanes == 12
    assert rytm_scope.available_lanes == 12
    assert rytm_scope.scope_status == "ready"
    assert "pads 1-12" in rytm_scope.operator_action
    a4_scope = next(
        scope for scope in report.device_scope_checks if scope.device_key == "analog-four-mkii"
    )
    assert a4_scope.required_lanes == 4
    assert a4_scope.available_lanes == 4
    assert a4_scope.scope_status == "ready"
    assert "tracks 1-4" in a4_scope.operator_action
    assert any(
        check.check_key == "active-hardware-entrypoint"
        and check.status == "ready"
        and "app --arm" in check.message
        for check in report.boundary_checks
    )
    assert any(
        check.check_key == "no-cockpit-hardware-entrypoint" and check.status == "ready"
        for check in report.boundary_checks
    )
    assert any(
        guardrail.guardrail_key == "python-sidecar-websocket-port"
        and guardrail.status == "ready"
        and guardrail.required_artifact == "RYTM_RAND_WS_PORT"
        for guardrail in report.toolchain_guardrails
    )
    assert any(
        guardrail.guardrail_key == "tauri-web-lockfiles" and guardrail.status == "review-needed"
        for guardrail in report.toolchain_guardrails
    )
    assert "no cockpit hardware entrypoint" in report.blocked_actions
    assert "no Tauri launch" in report.blocked_actions
    assert "no webview launch" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert "no port opening" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-cockpit-boundary-readiness-report"
    )
    assert "--boundary-label 'Warehouse cockpit boundary'" in report.replay_commands[0]
    assert "--hardware-entrypoint 'python -m rytm_randomizer.app --arm'" in (
        report.replay_commands[0]
    )
    assert report.replay_commands[1] == render_harness.replay_commands[0]

    lines = format_style_performance_arc_live_gui_cockpit_boundary_readiness_report(report)
    text = "\n".join(lines)
    assert lines[0] == (
        "RytmRandomizer passive style performance arc live GUI cockpit boundary readiness"
    )
    assert "Live GUI cockpit boundary readiness summary:" in lines
    assert "Device scope checks:" in lines
    assert "Toolchain guardrails:" in lines
    assert "Boundary checks:" in lines
    assert "active hardware remains app --arm only" in text
    assert "Rytm 12-pad" in text
    assert "Analog Four 4-track" in text
    assert "- no cockpit hardware entrypoint" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_cockpit_boundary_readiness_json(report)
    boundary = payload["live_gui_cockpit_boundary_readiness"]
    assert boundary["boundary_readiness_version"] == ("live-gui-cockpit-boundary-readiness-v1")
    assert boundary["boundary_readiness_id"] == report.boundary_readiness_id
    assert boundary["render_harness_id"] == render_harness.render_harness_id
    assert boundary["device_scope_checks"][0]["required_lanes"] == 12
    assert boundary["toolchain_guardrails"][0]["guardrail_key"] == ("python-sidecar-websocket-port")
    assert "live_gui_desktop_render_harness" in payload
    assert "live_gui_desktop_render_contract" in payload
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_cockpit_boundary_readiness_status_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_cockpit_boundary_readiness import (
        _boundary_checks,
        _boundary_status,
        _included_lanes,
        build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness,
    )

    render_harness = _render_harness(tmp_path)
    review_report = (
        build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness(
            replace(render_harness, render_harness_status="review-needed")
        )
    )
    assert review_report.boundary_status == "review-needed"
    assert any(check.status == "review-needed" for check in review_report.boundary_checks)

    blocked_report = (
        build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness(
            replace(render_harness, render_harness_status="blocked")
        )
    )
    assert blocked_report.boundary_status == "blocked"
    assert "hold cockpit work until desktop render harness is clear" in (
        blocked_report.blocked_actions
    )

    assert (
        _included_lanes("analog-four-only", device_key="analog-rytm-mkii", required_lanes=12) == 0
    )

    cockpit_entrypoint_report = (
        build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness(
            render_harness,
            hardware_entrypoint="python -m rytm_randomizer.cockpit --arm",
        )
    )
    assert cockpit_entrypoint_report.boundary_status == "blocked"
    assert any(
        check.check_key == "active-hardware-entrypoint" and check.status == "blocked"
        for check in cockpit_entrypoint_report.boundary_checks
    )

    no_replay_report = (
        build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness(
            replace(render_harness, replay_commands=())
        )
    )
    assert no_replay_report.boundary_status == "review-needed"
    assert no_replay_report.replay_commands == ()

    malformed_replay_report = (
        build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness(
            replace(
                render_harness,
                replay_commands=("python -m rytm_randomizer.cli unrelated-report",),
            )
        )
    )
    assert malformed_replay_report.boundary_status == "review-needed"
    assert malformed_replay_report.replay_commands == (
        "python -m rytm_randomizer.cli unrelated-report",
    )

    checks = _boundary_checks(
        render_harness,
        hardware_entrypoint="python -m rytm_randomizer.app --arm",
        passive_entrypoint="python -m rytm_randomizer.cli",
        ws_port_env="",
        replay_commands=(),
    )
    assert _boundary_status(render_harness, checks) == "review-needed"
    assert any(
        check.check_key == "ws-port-env-docs" and check.status == "review-needed"
        for check in checks
    )

    with pytest.raises(ValueError, match="boundary_label"):
        build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness(
            render_harness,
            boundary_label=" ",
        )
    with pytest.raises(ValueError, match="hardware_entrypoint"):
        build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness(
            render_harness,
            hardware_entrypoint=" ",
        )
    with pytest.raises(ValueError, match="passive_entrypoint"):
        build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness(
            render_harness,
            passive_entrypoint=" ",
        )


def test_live_gui_cockpit_boundary_readiness_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_cockpit_boundary_readiness import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_COCKPIT_BOUNDARY_READINESS_CLI_COMMAND,
        build_style_performance_arc_live_gui_cockpit_boundary_readiness_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = STYLE_PERFORMANCE_ARC_LIVE_GUI_COCKPIT_BOUNDARY_READINESS_CLI_COMMAND.args_parser(
        [
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
            "--boundary-label",
            "Warehouse cockpit boundary",
            "--hardware-entrypoint",
            "python -m rytm_randomizer.app --arm",
            "--passive-entrypoint",
            "python -m rytm_randomizer.cli",
            "--ws-port-env",
            "RYTM_RAND_WS_PORT",
            "--json",
        ]
    )
    assert parsed["render_harness_label"] == "Warehouse render harness"
    assert parsed["boundary_label"] == "Warehouse cockpit boundary"
    assert parsed["hardware_entrypoint"] == "python -m rytm_randomizer.app --arm"
    assert parsed["passive_entrypoint"] == "python -m rytm_randomizer.cli"
    assert parsed["ws_port_env"] == "RYTM_RAND_WS_PORT"
    assert parsed["json_output"] is True

    with pytest.raises(ValueError, match="usage"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_COCKPIT_BOUNDARY_READINESS_CLI_COMMAND.args_parser(
            ["--boundary-label"]
        )

    report = build_style_performance_arc_live_gui_cockpit_boundary_readiness_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        capture_description="captured warehouse take",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        render_harness_label="Warehouse render harness",
        boundary_label="Warehouse cockpit boundary",
    )
    assert report.boundary_label == "Warehouse cockpit boundary"
    assert report.render_harness.render_harness_label == "Warehouse render harness"

    rc = main(
        [
            "style-performance-arc-live-gui-cockpit-boundary-readiness-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--boundary-label",
            "Warehouse cockpit boundary",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["live_gui_cockpit_boundary_readiness"]["boundary_label"] == (
        "Warehouse cockpit boundary"
    )
    assert "live_gui_desktop_render_harness" in payload

    rc = main(
        [
            "style-performance-arc-live-gui-cockpit-boundary-readiness-report",
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--boundary-label",
            "Warehouse cockpit boundary",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "Live GUI cockpit boundary readiness summary:" in captured.out
    assert "Device scope checks:" in captured.out
    assert captured.err == ""

    rc = main(
        [
            "style-performance-arc-live-gui-cockpit-boundary-readiness-report",
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


def test_live_gui_cockpit_boundary_readiness_cli_json_is_passive(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    command = [
        sys.executable,
        "-m",
        "rytm_randomizer.cli",
        "style-performance-arc-live-gui-cockpit-boundary-readiness-report",
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
        "--render-harness-label",
        "Warehouse render harness",
        "--boundary-label",
        "Warehouse cockpit boundary",
        "--json",
    ]
    script = (
        "import json, subprocess, sys; "
        f"forbidden={FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES!r}; "
        f"result=subprocess.run({command!r}, cwd={str(PROJECT_ROOT)!r}, "
        "text=True, capture_output=True, check=False); "
        "loaded=[name for name in forbidden if name in sys.modules]; "
        "print(json.dumps({'returncode': result.returncode, "
        "'stdout': result.stdout, 'stderr': result.stderr, 'loaded': loaded}, "
        "sort_keys=True))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["returncode"] == 0
    assert payload["stderr"] == ""
    assert payload["loaded"] == []
    report_payload = json.loads(payload["stdout"])
    boundary = report_payload["live_gui_cockpit_boundary_readiness"]
    assert boundary["boundary_status"] in {"ready", "review-needed", "blocked"}
    assert any(
        check["check_key"] == "active-hardware-entrypoint" and check["status"] == "ready"
        for check in boundary["boundary_checks"]
    )
    assert "no MIDI sending" in boundary["blocked_actions"]
    assert "no port opening" in boundary["blocked_actions"]


def test_live_gui_cockpit_boundary_readiness_help_mentions_passive_contract():
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text(
        "style-performance-arc-live-gui-cockpit-boundary-readiness-report"
    )

    assert help_text.startswith(
        "RytmRandomizer passive CLI: "
        "style-performance-arc-live-gui-cockpit-boundary-readiness-report"
    )
    assert "cockpit boundary readiness" in help_text
    assert "active hardware remains app --arm only" in help_text
    assert "Rytm 12-pad" in help_text
    assert "Analog Four 4-track" in help_text
    assert "no Tauri launch" in help_text
    assert "no MIDI sending" in help_text
    assert "no port opening" in help_text
