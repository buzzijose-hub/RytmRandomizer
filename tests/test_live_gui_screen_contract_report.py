"""Tests for passive live GUI screen contract reporting."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _feature_report(
    *,
    bpm: float = 141.0,
    confidence=None,
    tempo_stability: float = 0.88,
    kick_density: float = 0.78,
    percussion_density: float = 0.73,
    low_end_weight: float = 0.69,
    spectral_brightness: float = 0.47,
    texture_noise: float = 0.62,
    energy_arc: tuple[float, ...] = (0.24, 0.52, 0.84),
):
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    report_confidence = confidence or Confidence.MEDIUM
    report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=report_confidence,
        bpm=bpm,
        tempo_stability=tempo_stability,
        kick_density=kick_density,
        percussion_density=percussion_density,
        low_end_weight=low_end_weight,
        spectral_brightness=spectral_brightness,
        texture_noise=texture_noise,
        energy_arc=energy_arc,
        content_hash="",
        derived_at="2026-05-23T04:15:00Z",
    )
    return FeatureReport(
        **{
            **report.__dict__,
            "content_hash": compute_feature_report_hash(report),
        }
    )


def _sidecar_report(tmp_path: Path, *, take_count: int = 2):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_review import (
        build_style_performance_arc_live_gui_capture_review_report,
    )
    from rytm_randomizer.reports.live_gui_sidecar_session import (
        build_style_performance_arc_live_gui_sidecar_session_from_capture_review,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    capture_review = build_style_performance_arc_live_gui_capture_review_report(
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
        take_count=take_count,
        queue_label="Warehouse sidecar capture",
        capture_prefix="warehouse",
        slot_key="capture-001",
    )
    return build_style_performance_arc_live_gui_sidecar_session_from_capture_review(
        capture_review,
        sidecar_label="Warehouse sidecar",
    )


def test_live_gui_screen_contract_builds_deterministic_screen_packet_from_sidecar(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_gui_screen_contract import (
        build_style_performance_arc_live_gui_screen_contract_from_sidecar_session,
        format_style_performance_arc_live_gui_screen_contract_report,
        to_style_performance_arc_live_gui_screen_contract_json,
    )

    sidecar = _sidecar_report(tmp_path)
    report = build_style_performance_arc_live_gui_screen_contract_from_sidecar_session(
        sidecar,
        screen_label="Warehouse screen",
        layout_key="operator-cockpit",
        viewport="desktop",
    )

    assert report.screen_version == "live-gui-screen-contract-v1"
    assert len(report.screen_id) == 16
    assert report.screen_label == "Warehouse screen"
    assert report.layout_key == "operator-cockpit"
    assert report.viewport == "desktop"
    assert report.screen_status == "ready"
    assert report.sidecar_session_id == sidecar.sidecar_id
    assert report.selected_arc_key == sidecar.selected_arc_key
    assert report.current_cue_label == sidecar.current_cue_label
    assert report.primary_action.label == "Show GO"
    assert report.primary_action.enabled is False
    assert report.primary_action.reason.startswith("Passive screen contract")
    assert [region.key for region in report.regions] == [
        "header",
        "cue-strip",
        "machine-panels",
        "analyzer-table",
        "capture-table",
        "safety-bar",
    ]
    assert {component.key for component in report.components} >= {
        "selected-arc",
        "sidecar-status",
        "current-cue",
        "primary-action",
        "panel-machines",
        "disabled-send-midi",
    }
    assert all(component.enabled is False for component in report.interaction_controls)
    assert {row.key for row in report.table_rows} >= {
        "analyzer-bpm",
        "analyzer-low-end",
        "capture-capture-001",
    }
    assert report.alerts == ()
    assert any(action == "no MIDI sending" for action in report.blocked_actions)
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-screen-contract-report"
    )
    assert report.replay_commands[1].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-sidecar-session-report"
    )

    lines = format_style_performance_arc_live_gui_screen_contract_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live GUI screen contract"
    assert "Live GUI screen contract summary:" in lines
    assert "Screen regions:" in lines
    assert "Screen components:" in lines
    assert "Interaction contract:" in lines
    assert "Passive GUI screen contract only" in text
    assert "- path options are read-only inputs" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_gui_screen_contract_json(report)
    screen = payload["live_gui_screen_contract"]
    assert screen["screen_version"] == "live-gui-screen-contract-v1"
    assert screen["screen_id"] == report.screen_id
    assert screen["screen_status"] == "ready"
    assert screen["sidecar_session_id"] == sidecar.sidecar_id
    assert screen["regions"][0]["key"] == "header"
    assert screen["components"][0]["key"] == "selected-arc"
    assert screen["primary_action"]["enabled"] is False
    assert payload["live_gui_sidecar_session"]["sidecar_id"] == sidecar.sidecar_id
    assert payload["live_gui_capture_review"]["review_id"] == sidecar.capture_review_id
    assert payload["safety"][0] == "passive/read-only"
    assert "path options are read-only inputs" in payload["safety"]


def test_live_gui_screen_contract_maps_repeat_and_hold_states(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_gui_capture_review import (
        build_style_performance_arc_live_gui_capture_review_report,
    )
    from rytm_randomizer.reports.live_gui_screen_contract import (
        build_style_performance_arc_live_gui_screen_contract_from_sidecar_session,
    )
    from rytm_randomizer.reports.live_gui_sidecar_session import (
        build_style_performance_arc_live_gui_sidecar_session_from_capture_review,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    repeat_review = build_style_performance_arc_live_gui_capture_review_report(
        feature_report=_feature_report(),
        capture_feature_report=_feature_report(
            bpm=144.4,
            low_end_weight=0.52,
            spectral_brightness=0.63,
            texture_noise=0.78,
        ),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        take_count=1,
    )
    repeat_contract = build_style_performance_arc_live_gui_screen_contract_from_sidecar_session(
        build_style_performance_arc_live_gui_sidecar_session_from_capture_review(repeat_review)
    )
    assert repeat_contract.screen_status == "needs-repeat"
    assert repeat_contract.primary_action.label == "Repeat take"
    assert repeat_contract.alerts[0].severity == "warning"

    hold_review = build_style_performance_arc_live_gui_capture_review_report(
        feature_report=_feature_report(),
        capture_feature_report=_feature_report(bpm=0.0, energy_arc=(0.42,)),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        match_limit=1,
        take_count=1,
    )
    hold_contract = build_style_performance_arc_live_gui_screen_contract_from_sidecar_session(
        build_style_performance_arc_live_gui_sidecar_session_from_capture_review(hold_review)
    )
    assert hold_contract.screen_status == "hold"
    assert hold_contract.primary_action.label == "Hold workflow"
    assert hold_contract.alerts[0].severity == "critical"
    assert any(row.status == "blocked" for row in hold_contract.table_rows)


def test_live_gui_screen_contract_covers_empty_fallback_and_replay_edges(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_gui_screen_contract import (
        build_style_performance_arc_live_gui_screen_contract_from_sidecar_session,
    )

    sidecar = _sidecar_report(tmp_path, take_count=1)
    stripped_sidecar = replace(
        sidecar,
        next_cue_labels=(),
        analyzer_rows=(),
        capture_rows=(),
        disabled_controls=(),
        blocked_actions=("custom block", "custom block", "no MIDI sending"),
        replay_commands=("python -m rytm_randomizer.cli upstream",),
    )

    report = build_style_performance_arc_live_gui_screen_contract_from_sidecar_session(
        stripped_sidecar,
        screen_label="Compact",
        layout_key="minimal",
        viewport="compact",
    )
    no_replay_report = build_style_performance_arc_live_gui_screen_contract_from_sidecar_session(
        replace(stripped_sidecar, replay_commands=()),
    )

    assert report.next_cue_labels == ("No lookahead cue queued",)
    assert {row.row_type for row in report.table_rows} == {"empty"}
    assert {component.key for component in report.components} >= {
        "empty-analyzer",
        "empty-capture",
    }
    component_regions = {component.key: component.region_key for component in report.components}
    assert component_regions["empty-analyzer"] == "analyzer-table"
    assert component_regions["empty-capture"] == "capture-table"
    assert report.blocked_actions.count("custom block") == 1
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-screen-contract-report"
    )
    assert "--screen-label Compact" in report.replay_commands[0]
    assert "--layout minimal" in report.replay_commands[0]
    assert "--viewport compact" in report.replay_commands[0]
    assert report.replay_commands[1:] == stripped_sidecar.replay_commands
    assert no_replay_report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-screen-contract-report"
    )

    with pytest.raises(ValueError, match="screen_label"):
        build_style_performance_arc_live_gui_screen_contract_from_sidecar_session(
            sidecar,
            screen_label="   ",
        )
    with pytest.raises(ValueError, match="layout_key"):
        build_style_performance_arc_live_gui_screen_contract_from_sidecar_session(
            sidecar,
            layout_key="   ",
        )
    with pytest.raises(ValueError, match="viewport"):
        build_style_performance_arc_live_gui_screen_contract_from_sidecar_session(
            sidecar,
            viewport="   ",
        )


def test_live_gui_screen_contract_parser_builder_and_cli_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.cli import main
    from rytm_randomizer.help_text import resolve_help_text
    from rytm_randomizer.reports.live_gui_screen_contract import (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_SCREEN_CONTRACT_CLI_COMMAND,
        _parse_cli_args,
        build_style_performance_arc_live_gui_screen_contract_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    parsed = _parse_cli_args(
        [
            "--audio",
            "reference.wav",
            "--capture-audio",
            "capture.wav",
            "--rytm",
            str(rytm_path),
            "--analog-four",
            str(a4_path),
            "--scope",
            "a4-only",
            "--rank",
            "2",
            "--total-minutes",
            "90",
            "--segment-minutes",
            "15",
            "--discovery-start",
            "10",
            "--discovery-end",
            "80",
            "--cue",
            "2",
            "--lookahead",
            "0",
            "--matches",
            "2",
            "--takes",
            "3",
            "--slot",
            "capture-002",
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
            "tablet",
            "--json",
        ]
    )
    assert parsed["audio_path"] == Path("reference.wav")
    assert parsed["capture_audio_path"] == Path("capture.wav")
    assert parsed["scope"] == "analog-four-only"
    assert parsed["screen_label"] == "Warehouse screen"
    assert parsed["layout_key"] == "operator-cockpit"
    assert parsed["viewport"] == "tablet"
    assert parsed["json_output"] is True

    library_parsed = _parse_cli_args(
        [
            "--library",
            "references",
            "--capture-library",
            "captures",
            "--rytm",
            str(rytm_path),
        ]
    )
    assert library_parsed["library_path"] == Path("references")
    assert library_parsed["capture_library_path"] == Path("captures")

    bad_cases = (
        (["--bogus"], "usage"),
        (["--description"], "usage"),
        (["--description", "   ", "--capture-description", "take"], "reference"),
        (["--description", "ref", "--capture-description", "   "], "measured"),
        (["--description", "ref", "--capture-description", "take", "--rank", "0"], ">= 1"),
        (
            ["--description", "ref", "--capture-description", "take", "--lookahead", "-1"],
            ">= 0",
        ),
        (
            ["--description", "ref", "--capture-description", "take", "--matches", "many"],
            "integer",
        ),
        (
            ["--description", "ref", "--capture-description", "take", "--slot", "   "],
            "slot",
        ),
        (
            ["--description", "ref", "--capture-description", "take", "--screen-label", "   "],
            "screen_label",
        ),
        (
            ["--description", "ref", "--capture-description", "take", "--layout", "   "],
            "layout_key",
        ),
        (
            ["--description", "ref", "--capture-description", "take", "--viewport", "watch"],
            "viewport",
        ),
        (["--description", "ref"], "captured evidence"),
        (["--capture-description", "take"], "usage"),
    )
    for argv, message in bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    with pytest.raises(ValueError, match="reference source"):
        build_style_performance_arc_live_gui_screen_contract_report(
            capture_feature_report=_feature_report(),
            rytm_sysex_path=rytm_path,
        )
    with pytest.raises(ValueError, match="reference evidence"):
        build_style_performance_arc_live_gui_screen_contract_report(
            description="   ",
            capture_feature_report=_feature_report(),
            rytm_sysex_path=rytm_path,
        )
    with pytest.raises(ValueError, match="captured evidence"):
        build_style_performance_arc_live_gui_screen_contract_report(
            feature_report=_feature_report(),
            rytm_sysex_path=rytm_path,
        )

    assert (
        main(
            [
                "style-performance-arc-live-gui-screen-contract-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
                "--capture-description",
                "captured warehouse take with tight low end and building pressure",
                "--rytm",
                str(rytm_path),
                "--analog-four",
                str(a4_path),
                "--screen-label",
                "Warehouse screen",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc live GUI screen contract" in (captured.out)
    assert "Live GUI screen contract summary:" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-screen-contract-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
                "--capture-description",
                "captured warehouse take with tight low end and building pressure",
                "--rytm",
                str(rytm_path),
                "--analog-four",
                str(a4_path),
                "--json",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["live_gui_screen_contract"]["screen_status"] in {
        "hold",
        "needs-repeat",
        "ready",
    }
    assert payload["live_gui_screen_contract"]["primary_action"]["enabled"] is False
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-gui-screen-contract-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires exactly one captured evidence source" in captured.err

    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_SCREEN_CONTRACT_CLI_COMMAND.error_formatter(
            ValueError("bad screen")
        )
        == "Error: bad screen"
    )
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_GUI_SCREEN_CONTRACT_CLI_COMMAND.handler(
            description="Jeff Mills Oscar Mulero Birmingham pressure",
            audio_path=None,
            library_path=None,
            capture_description="captured warehouse take with tight low end and building pressure",
            capture_audio_path=None,
            capture_library_path=None,
            rytm_sysex_path=rytm_path,
            analog_four_sysex_path=a4_path,
            scope=None,
            selection_rank=None,
            total_minutes=None,
            segment_minutes=None,
            discovery_start=None,
            discovery_end=None,
            cue_number=1,
            lookahead_count=1,
            match_limit=1,
            take_count=1,
            slot_key="capture-001",
            queue_label="Warehouse queue",
            capture_prefix="warehouse",
            sidecar_label="Warehouse sidecar",
            screen_label="   ",
            layout_key="operator-cockpit",
            viewport="desktop",
            json_output=False,
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "screen_label must not be blank" in captured.err

    help_text = resolve_help_text("style-performance-arc-live-gui-screen-contract-report")
    assert (
        "RytmRandomizer passive CLI: " "style-performance-arc-live-gui-screen-contract-report"
    ) in help_text
    assert "GUI screen contract" in help_text
    assert "no MIDI sending" in help_text
