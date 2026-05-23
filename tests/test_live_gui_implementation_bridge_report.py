"""Tests for passive live GUI implementation bridge reporting."""

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
        derived_at="2026-05-23T23:45:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _readiness_report(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_test_harness_readiness import (
        build_style_performance_arc_live_gui_test_harness_readiness_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_test_harness_readiness_report(
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
        queue_label="Warehouse bridge queue",
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
    )


def test_live_gui_implementation_bridge_builds_from_readiness(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_implementation_bridge import (
        build_style_performance_arc_live_gui_implementation_bridge_from_readiness,
        format_style_performance_arc_live_gui_implementation_bridge_report,
        to_style_performance_arc_live_gui_implementation_bridge_json,
    )

    readiness = _readiness_report(tmp_path)
    report = build_style_performance_arc_live_gui_implementation_bridge_from_readiness(
        readiness,
        bridge_label="Warehouse implementation bridge",
    )

    assert report.bridge_version == "live-gui-implementation-bridge-v1"
    assert len(report.bridge_id) == 16
    assert report.bridge_label == "Warehouse implementation bridge"
    assert report.bridge_status == "ready"
    assert report.readiness_id == readiness.readiness_id
    assert report.contract_id == readiness.contract_id
    assert report.selected_arc_key == readiness.selected_arc_key
    assert report.scope == readiness.scope
    assert "view-model packets" in report.view_model_summary
    assert "component mounts" in report.component_mount_summary
    assert "fixture bundles" in report.fixture_bundle_summary
    assert {packet.packet_key for packet in report.view_model_packets} >= {
        "sidecar-session",
        "screen-contract",
        "render-tree",
        "controller-state",
        "test-harness-readiness",
    }
    assert all(packet.passive for packet in report.view_model_packets)
    assert {mount.component_key for mount in report.component_mounts} >= {
        "current-cue-panel",
        "machine-panels",
        "analyzer-overlay",
        "capture-review-panel",
        "controller-actions",
        "test-harness-panel",
    }
    assert all(not mount.mount_enabled for mount in report.component_mounts)
    assert {bundle.bundle_key for bundle in report.fixture_bundles} >= {
        "fixture-sidecar-session-json",
        "fixture-render-tree-json",
        "fixture-controller-state-json",
        "fixture-test-harness-readiness-json",
    }
    assert all(bundle.passive for bundle in report.fixture_bundles)
    assert {gate.key for gate in report.implementation_gates} >= {
        "readiness-status",
        "view-model-coverage",
        "component-mount-coverage",
        "fixture-bundle-coverage",
        "passive-boundary",
    }
    assert "no GUI launch" in report.blocked_actions
    assert "no renderer execution" in report.blocked_actions
    assert "no GUI event dispatch" in report.blocked_actions
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-implementation-bridge-report"
    )
    assert "style-performance-arc-live-gui-test-harness-readiness-report" not in (
        report.replay_commands[0]
    )
    assert "--readiness-label 'Warehouse readiness packet'" in report.replay_commands[0]
    assert "--bridge-label 'Warehouse implementation bridge'" in report.replay_commands[0]
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-test-harness-readiness-report"
    )

    lines = format_style_performance_arc_live_gui_implementation_bridge_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI implementation bridge"
    assert "Live GUI implementation bridge summary:" in lines
    assert "View-model packets:" in lines
    assert "Component mounts:" in lines
    assert "Fixture bundles:" in lines
    assert "Implementation gates:" in lines
    assert "Passive GUI implementation bridge metadata only" in text
    assert "- no GUI launch" in lines
    assert "- no renderer execution" in lines
    assert "- no MIDI sending" in lines

    payload = to_style_performance_arc_live_gui_implementation_bridge_json(report)
    bridge = payload["live_gui_implementation_bridge"]
    assert bridge["bridge_version"] == "live-gui-implementation-bridge-v1"
    assert bridge["bridge_id"] == report.bridge_id
    assert bridge["readiness_id"] == readiness.readiness_id
    assert bridge["view_model_packets"][0]["packet_key"] == "sidecar-session"
    assert bridge["component_mounts"][0]["component_key"] == "current-cue-panel"
    assert bridge["fixture_bundles"][0]["bundle_key"] == "fixture-sidecar-session-json"
    assert bridge["implementation_gates"][0]["key"] == "readiness-status"
    assert "live_gui_test_harness_readiness" in payload
    assert "live_gui_test_harness_contract" in payload
    assert payload["safety"][0] == "passive/read-only"


def test_live_gui_implementation_bridge_status_edges(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_implementation_bridge import (
        _bridge_status,
        _implementation_gates,
        build_style_performance_arc_live_gui_implementation_bridge_from_readiness,
    )

    readiness = _readiness_report(tmp_path)

    blocked_report = build_style_performance_arc_live_gui_implementation_bridge_from_readiness(
        replace(readiness, readiness_status="blocked")
    )
    assert blocked_report.bridge_status == "blocked"
    assert "hold GUI implementation bridge until readiness is clear" in (
        blocked_report.blocked_actions
    )
    assert any(
        gate.key == "readiness-status" and gate.status == "blocked"
        for gate in blocked_report.implementation_gates
    )

    review_report = build_style_performance_arc_live_gui_implementation_bridge_from_readiness(
        replace(readiness, readiness_status="review-needed")
    )
    assert review_report.bridge_status == "review-needed"
    assert any(gate.status == "review-needed" for gate in review_report.implementation_gates)

    no_replay_report = build_style_performance_arc_live_gui_implementation_bridge_from_readiness(
        replace(readiness, replay_commands=())
    )
    assert no_replay_report.bridge_status == "review-needed"
    assert no_replay_report.replay_commands == ()
    assert any(
        gate.key == "replay-command" and gate.status == "review-needed"
        for gate in no_replay_report.implementation_gates
    )

    malformed_replay_report = (
        build_style_performance_arc_live_gui_implementation_bridge_from_readiness(
            replace(readiness, replay_commands=("python -m rytm_randomizer.cli other-report",))
        )
    )
    assert malformed_replay_report.bridge_status == "review-needed"
    assert malformed_replay_report.replay_commands == (
        "python -m rytm_randomizer.cli other-report",
    )

    gates_with_empty_coverage = _implementation_gates(
        readiness,
        view_model_packets=(),
        component_mounts=(),
        fixture_bundles=(),
        replay_commands=malformed_replay_report.replay_commands,
    )
    assert _bridge_status(readiness, gates_with_empty_coverage) == "blocked"
    assert any(
        gate.key == "view-model-coverage" and gate.status == "blocked"
        for gate in gates_with_empty_coverage
    )


def test_live_gui_implementation_bridge_rejects_blank_label(tmp_path: Path):
    from rytm_randomizer.reports.live_gui_implementation_bridge import (
        build_style_performance_arc_live_gui_implementation_bridge_from_readiness,
        parse_style_performance_arc_live_gui_implementation_bridge_cli_args,
    )

    with pytest.raises(ValueError, match="bridge_label must not be blank"):
        build_style_performance_arc_live_gui_implementation_bridge_from_readiness(
            _readiness_report(tmp_path),
            bridge_label=" ",
        )

    with pytest.raises(ValueError, match="usage"):
        parse_style_performance_arc_live_gui_implementation_bridge_cli_args(["--description"])

    with pytest.raises(ValueError, match="bridge_label must not be blank"):
        parse_style_performance_arc_live_gui_implementation_bridge_cli_args(
            [
                "--description",
                "Jeff Mills pressure",
                "--capture-description",
                "captured warehouse pressure",
                "--bridge-label",
                " ",
            ]
        )


def test_live_gui_implementation_bridge_wrapper_and_parser_support_custom_labels(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_implementation_bridge import (
        build_style_performance_arc_live_gui_implementation_bridge_report,
        parse_style_performance_arc_live_gui_implementation_bridge_cli_args,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    report = build_style_performance_arc_live_gui_implementation_bridge_report(
        feature_report=_feature_report(),
        capture_feature_report=_feature_report(
            bpm=141.8,
            low_end_weight=0.70,
            spectral_brightness=0.43,
            texture_noise=0.61,
            energy_arc=(0.20, 0.54, 0.86),
        ),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=3,
        lookahead_count=1,
        match_limit=1,
        take_count=1,
        slot_key="capture-001",
        bridge_label="Direct wrapper bridge",
    )
    assert report.bridge_status == "ready"
    assert report.bridge_label == "Direct wrapper bridge"
    assert report.replay_commands[0].endswith("--bridge-label 'Direct wrapper bridge'")

    parsed = parse_style_performance_arc_live_gui_implementation_bridge_cli_args(
        [
            "--description",
            "Jeff Mills and Oscar Mulero pressure",
            "--capture-description",
            "captured warehouse take",
            "--bridge-label",
            "Parsed bridge",
            "--json",
        ]
    )
    assert parsed["description"] == "Jeff Mills and Oscar Mulero pressure"
    assert parsed["capture_description"] == "captured warehouse take"
    assert parsed["bridge_label"] == "Parsed bridge"
    assert parsed["json_output"] is True


def test_live_gui_implementation_bridge_handler_outputs_text_json_and_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_implementation_bridge import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_IMPLEMENTATION_BRIDGE_CLI_COMMAND,
        _format_cli_error,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    base_kwargs = {
        "description": "Jeff Mills Birmingham pressure",
        "audio_path": None,
        "library_path": None,
        "capture_description": "captured warehouse take",
        "capture_audio_path": None,
        "capture_library_path": None,
        "rytm_sysex_path": rytm_path,
        "analog_four_sysex_path": a4_path,
        "scope": None,
        "selection_rank": None,
        "total_minutes": None,
        "segment_minutes": None,
        "discovery_start": None,
        "discovery_end": None,
        "cue_number": 1,
        "lookahead_count": 1,
        "match_limit": 1,
        "take_count": 1,
        "slot_key": "capture-001",
        "queue_label": "Live GUI capture queue",
        "capture_prefix": "live-capture",
        "sidecar_label": "Live performance sidecar",
        "screen_label": "Live GUI screen contract",
        "layout_key": "operator-default",
        "viewport": "desktop",
        "render_target": "desktop-sidecar",
        "density": "standard",
        "overlay_label": "Live GUI overlay",
        "frame_label": "Live GUI frame",
        "interaction_label": "Live GUI interaction script",
        "reducer_label": "Live GUI action reducer",
        "controller_label": "Live GUI controller state",
        "playback_label": "Live GUI playback transcript",
        "validation_label": "Live GUI playback validation matrix",
        "harness_label": "Live GUI test-harness contract",
        "readiness_label": "Live GUI test-harness readiness",
        "bridge_label": "Handler bridge",
    }

    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_IMPLEMENTATION_BRIDGE_CLI_COMMAND.handler(
            **base_kwargs,
            json_output=False,
        )
        == 0
    )
    text_output = capsys.readouterr()
    assert "Live GUI implementation bridge summary:" in text_output.out
    assert text_output.err == ""

    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_IMPLEMENTATION_BRIDGE_CLI_COMMAND.handler(
            **base_kwargs,
            json_output=True,
        )
        == 0
    )
    json_output = capsys.readouterr()
    assert (
        json.loads(json_output.out)["live_gui_implementation_bridge"]["bridge_label"]
        == "Handler bridge"
    )
    assert json_output.err == ""

    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_IMPLEMENTATION_BRIDGE_CLI_COMMAND.handler(
            **{**base_kwargs, "bridge_label": " "},
            json_output=True,
        )
        == 2
    )
    error_output = capsys.readouterr()
    assert "bridge_label must not be blank" in error_output.err

    assert _format_cli_error(ValueError("boom")) == "Error: boom"


def test_live_gui_implementation_bridge_cli_json_is_passive(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    command = [
        sys.executable,
        "-m",
        "rytm_randomizer.cli",
        "style-performance-arc-live-gui-implementation-bridge-report",
        "--description",
        "Jeff Mills Oscar Mulero Birmingham pressure",
        "--capture-description",
        "captured warehouse take with tight low end and building pressure",
        "--rytm",
        str(rytm_path),
        "--analog-four",
        str(a4_path),
        "--cue",
        "2",
        "--lookahead",
        "2",
        "--matches",
        "2",
        "--takes",
        "2",
        "--slot",
        "capture-002",
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
        "--harness-label",
        "Warehouse harness contract",
        "--readiness-label",
        "Warehouse readiness packet",
        "--bridge-label",
        "Warehouse implementation bridge",
        "--json",
    ]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["live_gui_implementation_bridge"]["bridge_status"] == "blocked"
    assert payload["live_gui_implementation_bridge"]["bridge_label"] == (
        "Warehouse implementation bridge"
    )
    assert (
        "hold GUI implementation bridge until readiness is clear"
        in payload["live_gui_implementation_bridge"]["blocked_actions"]
    )
    assert "live_gui_test_harness_readiness" in payload

    module_snapshot_command = [
        sys.executable,
        "-c",
        (
            "import sys; "
            "import rytm_randomizer.reports.live_gui_implementation_bridge; "
            "print('\\n'.join(sorted(sys.modules)))"
        ),
    ]
    module_snapshot = subprocess.run(
        module_snapshot_command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert module_snapshot.returncode == 0, module_snapshot.stderr
    imported_modules = set(module_snapshot.stdout.splitlines())
    assert not imported_modules.intersection(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
