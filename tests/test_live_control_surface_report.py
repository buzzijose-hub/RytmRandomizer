"""Tests for passive live-performance control-surface reporting."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def test_live_control_surface_report_builds_gui_dashboard_and_analyzer_cards(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_control_surface import (
        build_style_performance_arc_live_control_surface_report,
        format_style_performance_arc_live_control_surface_report,
        to_style_performance_arc_live_control_surface_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    report = build_style_performance_arc_live_control_surface_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=2,
    )

    assert report.control_surface_version == "live-control-surface-v1"
    assert report.surface_status == "rehearsal-ready"
    assert report.surface_mode == "soundcheck"
    assert report.surface_title == "Cue 1 control surface"
    assert report.now_cue.cue_number == 1
    assert report.now_cue.status_light in {"GREEN", "AMBER", "RED", "WHITE"}
    assert len(report.next_cues) == 2
    assert len(report.header_tiles) >= 4
    assert any(tile.key == "arc" for tile in report.header_tiles)
    assert any("Analyze" in control for control in report.transport_controls)
    assert any(card.machine == "rytm" for card in report.machine_cards)
    assert any(card.machine == "analog-four" for card in report.machine_cards)
    assert {card.key for card in report.analyzer_cards} == {
        "reference",
        "listen-target",
        "machine-focus",
        "comparison-rules",
    }
    assert any(decision.key == "hardware-send" for decision in report.decision_strip)
    assert any("Keep hardware sends disabled" in control for control in report.recovery_controls)
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli style-performance-arc-live-control-surface-report"
    )

    lines = format_style_performance_arc_live_control_surface_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live control surface"
    assert "Control surface summary:" in lines
    assert "- Surface status: rehearsal-ready" in lines
    assert "Header tiles:" in lines
    assert "Transport controls:" in lines
    assert "Now cue:" in lines
    assert "Next cue strip:" in lines
    assert "Machine cards:" in lines
    assert "Audio analyzer cards:" in lines
    assert "Decision strip:" in lines
    assert "audio analyzer preview only" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_control_surface_json(report)
    surface = payload["live_control_surface"]
    assert surface["control_surface_version"] == "live-control-surface-v1"
    assert surface["surface_status"] == report.surface_status
    assert surface["now_cue"]["cue_number"] == 1
    assert surface["analyzer_cards"][0]["key"] == report.analyzer_cards[0].key
    assert payload["live_readiness"]["readiness_id"] == report.readiness_report.readiness_id
    assert payload["live_state_packet"]["state_id"] == report.readiness_report.live_state.state_id
    assert payload["safety"][0] == "passive/read-only"


def test_live_control_surface_from_readiness_covers_blocked_and_ready_edges(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.reports.live_control_surface import (
        build_style_performance_arc_live_control_surface_from_readiness,
        format_style_performance_arc_live_control_surface_report,
    )
    from rytm_randomizer.reports.live_performance_readiness import (
        build_style_performance_arc_live_readiness_from_state,
    )
    from rytm_randomizer.reports.live_performance_state import (
        build_style_performance_arc_live_state_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    live_state = build_style_performance_arc_live_state_report(
        description="Jeff Mills Oscar Mulero Birmingham pressure",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=0,
    )

    blocked_cue = replace(
        live_state.current_cue,
        status_light="RED",
        go_no_go="do-not-arm",
        screen_state="hold",
        blocker_summary="manual safety stop",
    )
    blocked_machine = replace(
        live_state.machine_states[0],
        status_light="RED",
        arm_state="do-not-arm",
        ui_badge="RED:hold",
        operator_check="Do not arm this machine.",
    )
    blocked_state = replace(
        live_state,
        live_state="blocked",
        screen_mode="hold",
        current_cue=blocked_cue,
        machine_states=(blocked_machine, *live_state.machine_states[1:]),
        warning_stack=("manual safety stop",),
    )
    blocked_readiness = build_style_performance_arc_live_readiness_from_state(blocked_state)

    blocked_surface = build_style_performance_arc_live_control_surface_from_readiness(
        blocked_readiness
    )

    assert blocked_surface.surface_status == "blocked"
    assert blocked_surface.surface_mode == "hold"
    assert blocked_surface.transport_controls[0] == "Hold current machine state."
    assert blocked_surface.now_cue.warning_level == "critical"
    assert blocked_surface.decision_strip[0].severity in {"info", "warning", "critical"}

    ready_cue = replace(
        live_state.current_cue,
        status_light="GREEN",
        go_no_go="go",
        screen_state="perform",
        blocker_summary="none",
    )
    ready_machines = tuple(
        replace(machine, status_light="GREEN", arm_state="armed-preview", ui_badge="GREEN:go")
        for machine in live_state.machine_states
    )
    ready_state = replace(
        live_state,
        live_state="ready",
        screen_mode="perform",
        current_cue=ready_cue,
        machine_states=ready_machines,
        warning_stack=(),
    )
    ready_readiness = build_style_performance_arc_live_readiness_from_state(ready_state)

    ready_surface = build_style_performance_arc_live_control_surface_from_readiness(ready_readiness)

    assert ready_surface.surface_status == "performance-ready"
    assert ready_surface.surface_mode == "perform"
    assert ready_surface.transport_controls[0] == "Confirm cue 1."
    assert ready_surface.now_cue.warning_level == "info"

    empty_state = replace(
        live_state,
        live_state="ready",
        screen_mode="inspect",
        current_cue=ready_cue,
        next_cues=(),
        machine_states=(),
        warning_stack=(),
    )
    empty_readiness = build_style_performance_arc_live_readiness_from_state(empty_state)
    empty_surface = build_style_performance_arc_live_control_surface_from_readiness(empty_readiness)
    lines = format_style_performance_arc_live_control_surface_report(empty_surface)

    assert "- No next cues requested." in lines
    assert "- No machine cards available." in lines

    no_units_state = replace(
        live_state,
        live_state="ready",
        screen_mode="inspect",
        current_cue=ready_cue,
        next_cues=(),
        machine_states=(replace(live_state.machine_states[0], planned_units=()),),
        warning_stack=(),
    )
    no_units_readiness = build_style_performance_arc_live_readiness_from_state(no_units_state)
    no_units_surface = build_style_performance_arc_live_control_surface_from_readiness(
        no_units_readiness
    )
    assert "  Planned units: none" in format_style_performance_arc_live_control_surface_report(
        no_units_surface
    )


def test_live_control_surface_cli_dispatch_json_and_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conftest import dual_machine_reference_bank_files
    from rytm_randomizer.cli import main
    from rytm_randomizer.help_text import resolve_help_text

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)

    assert (
        main(
            [
                "style-performance-arc-live-control-surface-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
                "--rytm",
                str(rytm_path),
                "--analog-four",
                str(a4_path),
                "--cue",
                "1",
                "--lookahead",
                "1",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc live control surface" in captured.out
    assert "Control surface summary:" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-control-surface-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
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
    assert payload["live_control_surface"]["surface_status"] == "rehearsal-ready"
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-control-surface-report",
                "--description",
                "Jeff Mills Oscar Mulero Birmingham pressure",
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires saved-kit source paths" in captured.err

    help_text = resolve_help_text("style-performance-arc-live-control-surface-report")
    assert (
        "RytmRandomizer passive CLI: style-performance-arc-live-control-surface-report" in help_text
    )
    assert "GUI/audio-analyzer control surface" in help_text
    assert "no MIDI sending" in help_text


def test_live_control_surface_parser_edges():
    from rytm_randomizer.reports.live_control_surface import (
        STYLE_PERFORMANCE_ARC_LIVE_CONTROL_SURFACE_CLI_COMMAND,
        _parse_cli_args,
        _source_option,
        build_style_performance_arc_live_control_surface_report,
    )

    audio_args = _parse_cli_args(
        [
            "--audio",
            "track.wav",
            "--scope",
            "a4-only",
            "--rank",
            "2",
            "--total-minutes",
            "300",
            "--segment-minutes",
            "25",
            "--discovery-start",
            "5",
            "--discovery-end",
            "80",
            "--json",
        ]
    )
    assert audio_args["audio_path"] == Path("track.wav")
    assert audio_args["scope"] == "analog-four-only"
    assert audio_args["selection_rank"] == 2
    assert audio_args["json_output"] is True

    library_args = _parse_cli_args(["--library", "crate"])
    assert library_args["library_path"] == Path("crate")

    arc_args = _parse_cli_args(["--arc", "jose_warehouse_five_hour"])
    assert arc_args["arc_key"] == "jose_warehouse_five_hour"

    bad_cases = (
        ([], "usage"),
        (["--arc"], "usage"),
        (["--bogus"], "usage"),
        (["--audio", "track.wav", "--rank", "0"], ">= 1"),
        (["--audio", "track.wav", "--lookahead", "-1"], ">= 0"),
        (["--audio", "track.wav", "--cue", "x"], "must be an integer"),
    )
    for argv, message in bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    with pytest.raises(ValueError, match="exactly one selection source"):
        build_style_performance_arc_live_control_surface_report()
    with pytest.raises(ValueError, match="exactly one selection source"):
        build_style_performance_arc_live_control_surface_report(
            arc_key="jose_warehouse_five_hour",
            description="Jeff Mills",
        )

    class FallbackSource:
        selection_source = "feature-report"
        source_reference = None
        selected_arc_key = "jose_warehouse_five_hour"

    assert _source_option(FallbackSource()) == "--arc jose_warehouse_five_hour"
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_CONTROL_SURFACE_CLI_COMMAND.error_formatter(
            ValueError("bad surface")
        )
        == "Error: bad surface"
    )
