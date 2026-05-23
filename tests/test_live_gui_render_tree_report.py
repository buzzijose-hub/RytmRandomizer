"""Tests for passive live GUI render-tree reporting."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


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
        derived_at="2026-05-23T05:45:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _screen_contract(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_screen_contract import (
        build_style_performance_arc_live_gui_screen_contract_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    return build_style_performance_arc_live_gui_screen_contract_report(
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
        queue_label="Warehouse render queue",
        capture_prefix="warehouse",
        slot_key="capture-001",
        sidecar_label="Warehouse sidecar",
        screen_label="Warehouse screen",
    )


def test_live_gui_render_tree_builds_deterministic_tree_from_screen_contract(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_gui_render_tree import (
        build_style_performance_arc_live_gui_render_tree_from_screen_contract,
        format_style_performance_arc_live_gui_render_tree_report,
        to_style_performance_arc_live_gui_render_tree_json,
    )

    screen = _screen_contract(tmp_path)
    report = build_style_performance_arc_live_gui_render_tree_from_screen_contract(
        screen,
        render_target="desktop-sidecar",
        density="standard",
    )

    assert report.render_tree_version == "live-gui-render-tree-v1"
    assert len(report.render_tree_id) == 16
    assert report.screen_contract_id == screen.screen_id
    assert report.render_status == screen.screen_status
    assert report.render_target == "desktop-sidecar"
    assert report.density == "standard"
    assert report.root_node.key == "root"
    assert report.root_node.parent_key is None
    assert report.root_node.child_keys == tuple(f"region-{region.key}" for region in screen.regions)
    assert {node.node_type for node in report.nodes} >= {
        "root",
        "region",
        "component",
        "table-row",
        "disabled-control",
    }
    assert {node.key for node in report.nodes} >= {
        "region-header",
        "region-analyzer-table",
        "component-selected-arc",
        "component-primary-action",
        "node-analyzer-bpm",
        "node-capture-capture-001",
        "control-disabled-send-midi",
    }
    assert all(node.enabled is False for node in report.nodes)
    assert {binding.key for binding in report.bindings} >= {
        "selected-arc",
        "sidecar-status",
        "current-cue",
        "machine-panels",
        "analyzer-rows",
        "capture-rows",
        "blocked-actions",
    }
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-render-tree-report"
    )
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-screen-contract-report"
    )

    lines = format_style_performance_arc_live_gui_render_tree_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI render tree"
    assert "Live GUI render tree summary:" in lines
    assert "Render nodes:" in lines
    assert "Render bindings:" in lines
    assert "Passive GUI render tree only" in text
    assert "- path options are read-only inputs" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_render_tree_json(report)
    render_tree = payload["live_gui_render_tree"]
    assert render_tree["render_tree_version"] == "live-gui-render-tree-v1"
    assert render_tree["render_tree_id"] == report.render_tree_id
    assert render_tree["screen_contract_id"] == screen.screen_id
    assert render_tree["root_node"]["key"] == "root"
    assert render_tree["nodes"][0]["key"] == "root"
    assert render_tree["bindings"][0]["key"] == "selected-arc"
    assert payload["live_gui_screen_contract"]["screen_id"] == screen.screen_id
    assert payload["safety"][0] == "passive/read-only"
    assert "path options are read-only inputs" in payload["safety"]


def test_live_gui_render_tree_maps_empty_alert_and_replay_fallback_edges(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_gui_render_tree import (
        build_style_performance_arc_live_gui_render_tree_from_screen_contract,
    )
    from rytm_randomizer.reports.live_gui_screen_contract import (
        StylePerformanceArcLiveGuiScreenAlert,
        build_style_performance_arc_live_gui_screen_contract_from_sidecar_session,
    )

    screen = _screen_contract(tmp_path)
    stripped_screen = replace(
        build_style_performance_arc_live_gui_screen_contract_from_sidecar_session(
            replace(
                screen.sidecar_session,
                analyzer_rows=(),
                capture_rows=(),
                disabled_controls=(),
                blocked_actions=("custom block", "custom block", "no MIDI sending"),
                replay_commands=("python -m rytm_randomizer.cli upstream",),
            ),
            screen_label="Compact",
            layout_key="minimal",
            viewport="compact",
        ),
        alerts=(
            StylePerformanceArcLiveGuiScreenAlert(
                key="manual-hold",
                severity="critical",
                label="Manual hold",
                message="Hold the rehearsal screen.",
                source="test",
            ),
        ),
        screen_status="hold",
    )

    report = build_style_performance_arc_live_gui_render_tree_from_screen_contract(
        stripped_screen,
        render_target="test-harness",
        density="compact",
    )

    node_by_key = {node.key: node for node in report.nodes}
    assert node_by_key["node-empty-analyzer"].parent_key == "region-analyzer-table"
    assert node_by_key["node-empty-capture"].parent_key == "region-capture-table"
    assert node_by_key["alert-manual-hold"].parent_key == "region-header"
    assert node_by_key["root"].style_tokens == (
        "target-test-harness",
        "density-compact",
        "status-hold",
        "viewport-compact",
    )
    assert report.blocked_actions.count("custom block") == 1
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-render-tree-report"
    )
    assert "--render-target test-harness" in report.replay_commands[0]
    assert "--density compact" in report.replay_commands[0]

    with pytest.raises(ValueError, match="render_target"):
        build_style_performance_arc_live_gui_render_tree_from_screen_contract(
            screen,
            render_target=" ",
        )
    with pytest.raises(ValueError, match="render target"):
        build_style_performance_arc_live_gui_render_tree_from_screen_contract(
            screen,
            render_target="browser",
        )
    with pytest.raises(ValueError, match="density"):
        build_style_performance_arc_live_gui_render_tree_from_screen_contract(
            screen,
            density="dense",
        )

    fallback_report = build_style_performance_arc_live_gui_render_tree_from_screen_contract(
        replace(screen, replay_commands=("python -m rytm_randomizer.cli upstream",))
    )
    assert fallback_report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-render-tree-report"
    )

    empty_replay_report = build_style_performance_arc_live_gui_render_tree_from_screen_contract(
        replace(screen, replay_commands=())
    )
    assert empty_replay_report.replay_commands == (
        "python -m rytm_randomizer.cli style-performance-arc-live-gui-render-tree-report "
        "--render-target desktop-sidecar --density standard",
    )


def test_live_gui_render_tree_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.live_gui_render_tree import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_RENDER_TREE_CLI_COMMAND,
        build_style_performance_arc_live_gui_render_tree_report,
        to_style_performance_arc_live_gui_render_tree_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = STYLE_PERFORMANCE_ARC_LIVE_GUI_RENDER_TREE_CLI_COMMAND.args_parser(
        [
            "--description",
            "Jeff Mills Oscar Mulero Birmingham pressure",
            "--capture-description",
            "captured warehouse take",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--cue",
            "1",
            "--lookahead",
            "1",
            "--matches",
            "2",
            "--takes",
            "1",
            "--slot",
            "capture-001",
            "--label",
            "Warehouse queue",
            "--capture-prefix",
            "warehouse",
            "--sidecar-label",
            "Warehouse sidecar",
            "--screen-label",
            "Warehouse screen",
            "--layout",
            "operator-cockpit",
            "--viewport",
            "desktop",
            "--render-target",
            "desktop-sidecar",
            "--density",
            "standard",
            "--json",
        ]
    )
    assert parsed["render_target"] == "desktop-sidecar"
    assert parsed["density"] == "standard"
    assert parsed["json_output"] is True

    report = build_style_performance_arc_live_gui_render_tree_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        capture_description="captured warehouse take",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=1,
        match_limit=2,
        take_count=1,
        slot_key="capture-001",
        queue_label="Warehouse queue",
        capture_prefix="warehouse",
        sidecar_label="Warehouse sidecar",
        screen_label="Warehouse screen",
        layout_key="operator-cockpit",
        viewport="desktop",
        render_target="desktop-sidecar",
        density="standard",
    )
    payload = to_style_performance_arc_live_gui_render_tree_json(report)
    assert payload["live_gui_render_tree"]["render_status"] in {
        "ready",
        "needs-repeat",
        "hold",
    }

    with pytest.raises(ValueError, match="render target"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_RENDER_TREE_CLI_COMMAND.args_parser(
            [
                "--description",
                "x",
                "--capture-description",
                "y",
                "--render-target",
                "browser",
            ]
        )
    with pytest.raises(ValueError, match="density"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_RENDER_TREE_CLI_COMMAND.args_parser(
            [
                "--description",
                "x",
                "--capture-description",
                "y",
                "--density",
                "dense",
            ]
        )
    with pytest.raises(ValueError, match="usage"):
        STYLE_PERFORMANCE_ARC_LIVE_GUI_RENDER_TREE_CLI_COMMAND.args_parser(["--render-target"])
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_RENDER_TREE_CLI_COMMAND.error_formatter(ValueError("x"))
        == "Error: x"
    )
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_RENDER_TREE_CLI_COMMAND.handler(
            **{**parsed, "density": "dense"}
        )
        == 2
    )
    captured = capsys.readouterr()
    assert "Error: density must be standard or compact" in captured.err

    assert (
        main(
            [
                "style-performance-arc-live-gui-render-tree-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
                "--capture-description",
                "captured warehouse take",
                "--rytm",
                str(rytm_path),
                "--analog-four",
                str(a4_path),
                "--render-target",
                "desktop-sidecar",
                "--density",
                "standard",
                "--json",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["live_gui_render_tree"]["render_target"] == "desktop-sidecar"
    assert payload["live_gui_render_tree"]["density"] == "standard"
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-render-tree-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
                "--capture-description",
                "captured warehouse take",
                "--rytm",
                str(rytm_path),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc live GUI render tree" in captured.out
    assert "Live GUI render tree summary:" in captured.out
    assert captured.err == ""


def test_live_gui_render_tree_help_mentions_passive_contract():
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("style-performance-arc-live-gui-render-tree-report")
    assert (
        "RytmRandomizer passive CLI: " "style-performance-arc-live-gui-render-tree-report"
    ) in help_text
    assert "GUI render tree" in help_text
    assert "no MIDI sending" in help_text
