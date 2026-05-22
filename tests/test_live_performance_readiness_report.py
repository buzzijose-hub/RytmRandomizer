"""Tests for passive live-performance readiness reporting."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def test_live_performance_readiness_report_builds_gui_and_analyzer_gates(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_performance_readiness import (
        build_style_performance_arc_live_readiness_report,
        format_style_performance_arc_live_readiness_report,
        to_style_performance_arc_live_readiness_json,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    report = build_style_performance_arc_live_readiness_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=1,
    )

    gates_by_key = {gate.key: gate for gate in report.gates}

    assert report.readiness_version == "live-performance-readiness-v1"
    assert report.overall_status == "rehearsal-ready"
    assert report.launch_mode == "soundcheck"
    assert report.current_cue_summary.startswith("Cue 1 /")
    assert report.machine_summary == "1 armed-preview | 1 rehearse | 0 blocked"
    assert gates_by_key["live-state-packet"].status == "ready"
    assert gates_by_key["gui-command-surface"].status == "ready"
    assert gates_by_key["machine-panels"].status == "partial"
    assert gates_by_key["audio-analyzer-reference"].status == "preview"
    assert gates_by_key["hardware-send"].status == "disabled"
    assert any("Analyze current audio" in action for action in report.operator_next_actions)
    assert any("Rytm" in row for row in report.machine_panel_rows)
    assert any("Analog Four" in row for row in report.machine_panel_rows)

    lines = format_style_performance_arc_live_readiness_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live readiness"
    assert "Readiness summary:" in lines
    assert "- Overall status: rehearsal-ready" in lines
    assert "Gate stack:" in lines
    assert "Audio analyzer handoff:" in lines
    assert "Machine panels:" in lines
    assert "audio analyzer preview only" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_live_readiness_json(report)
    readiness = payload["live_readiness"]
    assert readiness["readiness_version"] == "live-performance-readiness-v1"
    assert readiness["overall_status"] == "rehearsal-ready"
    assert readiness["machine_summary"] == report.machine_summary
    assert readiness["gates"][0]["key"] == report.gates[0].key
    assert payload["live_state_packet"]["state_id"] == report.live_state.state_id
    assert payload["safety"][0] == "passive/read-only"


def test_live_performance_readiness_from_state_covers_blocked_state_edges(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_performance_readiness import (
        build_style_performance_arc_live_readiness_from_state,
        format_style_performance_arc_live_readiness_report,
    )
    from rytm_randomizer.reports.live_performance_state import (
        build_style_performance_arc_live_state_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    live_state = build_style_performance_arc_live_state_report(
        description="Jeff Mills Oscar Mulero tunnel",
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
        route_status="blocked",
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

    report = build_style_performance_arc_live_readiness_from_state(blocked_state)
    gates_by_key = {gate.key: gate for gate in report.gates}

    assert report.overall_status == "blocked"
    assert report.launch_mode == "hold"
    assert report.machine_summary == "0 armed-preview | 1 rehearse | 1 blocked"
    assert gates_by_key["current-cue"].status == "blocked"
    assert gates_by_key["machine-panels"].status == "blocked"
    assert gates_by_key["hardware-send"].operator_action.startswith("Keep hardware sends disabled")
    assert report.operator_next_actions[0] == "Hold the current machine state."

    lines = format_style_performance_arc_live_readiness_report(report)
    assert "- Overall status: blocked" in lines
    assert "- Blockers: manual safety stop" in lines


def test_live_performance_readiness_from_state_covers_ready_and_review_edges(
    tmp_path: Path,
):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_performance_readiness import (
        build_style_performance_arc_live_readiness_from_state,
    )
    from rytm_randomizer.reports.live_performance_state import (
        build_style_performance_arc_live_state_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)
    live_state = build_style_performance_arc_live_state_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        cue_number=1,
        lookahead_count=0,
    )
    perform_cue = replace(
        live_state.current_cue,
        status_light="GREEN",
        go_no_go="go",
        screen_state="perform",
        route_status="ready",
        warning_text="ready to launch",
    )
    ready_machines = tuple(
        replace(machine, status_light="GREEN", arm_state="armed-preview", ui_badge="GREEN:go")
        for machine in live_state.machine_states
    )
    ready_state = replace(
        live_state,
        live_state="ready",
        screen_mode="perform",
        current_cue=perform_cue,
        machine_states=ready_machines,
        warning_stack=(),
    )

    ready_report = build_style_performance_arc_live_readiness_from_state(ready_state)
    ready_gates = {gate.key: gate for gate in ready_report.gates}

    assert ready_report.overall_status == "performance-ready"
    assert ready_report.launch_mode == "perform"
    assert ready_gates["current-cue"].status == "ready"
    assert ready_gates["machine-panels"].status == "ready"
    assert ready_report.operator_next_actions[0] == "Confirm cue 1, then launch deliberately."

    review_cue = replace(
        live_state.current_cue,
        status_light="AMBER",
        go_no_go="review",
        screen_state="inspect",
        warning_text="needs operator review",
    )
    review_state = replace(
        live_state,
        live_state="ready",
        screen_mode="inspect",
        current_cue=review_cue,
        machine_states=(),
        warning_stack=("needs operator review",),
    )

    review_report = build_style_performance_arc_live_readiness_from_state(review_state)
    review_gates = {gate.key: gate for gate in review_report.gates}

    assert review_report.overall_status == "blocked"
    assert review_gates["current-cue"].status == "review"
    assert review_gates["machine-panels"].status == "blocked"
    assert review_report.machine_summary == "0 armed-preview | 0 rehearse | 0 blocked"


def test_live_performance_readiness_cli_dispatch_json_and_errors(
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
                "style-performance-arc-live-readiness-report",
                "--description",
                "Jeff Mills Oscar Mulero tunnel",
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
    assert "RytmRandomizer passive style performance arc live readiness" in captured.out
    assert "Readiness summary:" in captured.out
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-readiness-report",
                "--description",
                "Jeff Mills Oscar Mulero tunnel",
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
    assert payload["live_readiness"]["overall_status"] == "rehearsal-ready"
    assert captured.err == ""

    assert (
        main(
            [
                "style-performance-arc-live-readiness-report",
                "--description",
                "Jeff Mills Oscar Mulero tunnel",
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires saved-kit source paths" in captured.err

    help_text = resolve_help_text("style-performance-arc-live-readiness-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-live-readiness-report" in help_text
    assert "GUI/audio-analyzer readiness" in help_text
    assert "no MIDI sending" in help_text


def test_live_performance_readiness_parser_and_source_edges(tmp_path: Path):
    from conftest import dual_machine_reference_bank_files

    from rytm_randomizer.reports.live_performance_readiness import (
        STYLE_PERFORMANCE_ARC_LIVE_READINESS_CLI_COMMAND,
        _parse_cli_args,
        _source_option,
        build_style_performance_arc_live_readiness_report,
    )

    rytm_path, a4_path = dual_machine_reference_bank_files(tmp_path)

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
    assert audio_args["total_minutes"] == 300
    assert audio_args["segment_minutes"] == 25
    assert audio_args["discovery_start"] == 5
    assert audio_args["discovery_end"] == 80
    assert audio_args["json_output"] is True

    library_args = _parse_cli_args(["--library", "crate", "--rytm", str(rytm_path)])
    assert library_args["library_path"] == Path("crate")
    assert library_args["rytm_sysex_path"] == rytm_path

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
        build_style_performance_arc_live_readiness_report()
    with pytest.raises(ValueError, match="exactly one selection source"):
        build_style_performance_arc_live_readiness_report(
            arc_key="jose_warehouse_five_hour",
            description="Jeff Mills",
            rytm_sysex_path=rytm_path,
            analog_four_sysex_path=a4_path,
        )

    class FallbackSource:
        selection_source = "feature-report"
        source_reference = None
        selected_arc_key = "jose_warehouse_five_hour"

    assert _source_option(FallbackSource()) == "--arc jose_warehouse_five_hour"
    assert (
        STYLE_PERFORMANCE_ARC_LIVE_READINESS_CLI_COMMAND.error_formatter(
            ValueError("bad readiness")
        )
        == "Error: bad readiness"
    )
