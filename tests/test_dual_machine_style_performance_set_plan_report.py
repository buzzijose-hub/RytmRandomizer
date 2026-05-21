"""Tests for passive dual-machine live performance set plans."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _performance_set_framed(payload: bytes) -> bytes:
    return bytes([0xF0]) + payload + bytes([0xF7])


def _performance_set_a4_payload(name: bytes) -> bytes:
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + name[:16].ljust(16, b"\x00")
    return _performance_set_framed(payload)


def _performance_set_bank_files(tmp_path: Path) -> tuple[Path, Path]:
    from conftest import rytm_real_layout_kit_payload

    rytm_path = tmp_path / "rytm-performance-bank.syx"
    rytm_path.write_bytes(
        _performance_set_framed(rytm_real_layout_kit_payload(name=b"SET RYTM ONE"))
        + _performance_set_framed(rytm_real_layout_kit_payload(name=b"SET RYTM TWO"))
    )
    a4_path = tmp_path / "a4-performance-bank.syx"
    a4_path.write_bytes(
        _performance_set_a4_payload(b"SET A4 ONE") + _performance_set_a4_payload(b"SET A4 TWO")
    )
    return rytm_path, a4_path


def test_performance_set_plan_builds_timed_dual_segments_when_given_saved_banks(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        build_dual_machine_style_performance_set_plan_report,
    )

    rytm_path, a4_path = _performance_set_bank_files(tmp_path)
    plan = build_dual_machine_style_performance_set_plan_report(
        ("jose_core_techno", "birmingham_pressure", "warehouse_peak"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=300,
        discovery_start=35,
        discovery_end=75,
    )

    assert plan.style_keys == ("jose_core_techno", "birmingham_pressure", "warehouse_peak")
    assert plan.scope == "dual"
    assert plan.total_minutes == 300
    assert plan.segment_count == 3
    assert plan.ready_segment_count == 0
    assert plan.partial_segment_count == 3
    assert plan.blocked_segment_count == 0
    assert [segment.start_minute for segment in plan.segments] == [0, 100, 200]
    assert [segment.end_minute for segment in plan.segments] == [100, 200, 300]
    assert [segment.duration_minutes for segment in plan.segments] == [100, 100, 100]
    assert [segment.discovery_amount for segment in plan.segments] == [35, 55, 75]
    assert [segment.style_key for segment in plan.segments] == [
        "jose_core_techno",
        "birmingham_pressure",
        "warehouse_peak",
    ]
    assert all(segment.preview_plan.rytm_preview is not None for segment in plan.segments)
    assert all(segment.preview_plan.analog_four_preview is not None for segment in plan.segments)
    assert plan.total_event_row_count == sum(segment.event_row_count for segment in plan.segments)
    assert plan.total_deferred_row_count == sum(
        segment.deferred_row_count for segment in plan.segments
    )


def test_performance_set_plan_supports_rytm_only_fixed_segment_minutes(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        build_dual_machine_style_performance_set_plan_report,
    )

    rytm_path, _ = _performance_set_bank_files(tmp_path)
    plan = build_dual_machine_style_performance_set_plan_report(
        ("jose_core_techno", "warehouse_peak"),
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
        selection_rank=2,
        segment_minutes=45,
        discovery_start=40,
        discovery_end=40,
    )

    assert plan.scope == "rytm-only"
    assert plan.total_minutes == 90
    assert plan.selection_rank == 2
    assert [segment.start_minute for segment in plan.segments] == [0, 45]
    assert [segment.end_minute for segment in plan.segments] == [45, 90]
    assert [segment.discovery_amount for segment in plan.segments] == [40, 40]
    assert plan.ready_segment_count == 2
    assert plan.partial_segment_count == 0
    assert all(segment.preview_plan.rytm_preview is not None for segment in plan.segments)
    assert all(segment.preview_plan.rytm_preview.slot == 1 for segment in plan.segments)
    assert all(segment.preview_plan.analog_four_preview is None for segment in plan.segments)
    assert all(
        "leave Analog Four unchanged" in segment.operator_action for segment in plan.segments
    )


def test_performance_set_plan_rejects_empty_styles_and_bad_timing(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        build_dual_machine_style_performance_set_plan_report,
        format_dual_machine_style_performance_set_plan_report,
    )

    rytm_path, _ = _performance_set_bank_files(tmp_path)
    with pytest.raises(ValueError, match="at least one style key"):
        build_dual_machine_style_performance_set_plan_report((), rytm_sysex_path=rytm_path)
    with pytest.raises(ValueError, match="total_minutes must be >= 1"):
        build_dual_machine_style_performance_set_plan_report(
            ("jose_core_techno",),
            rytm_sysex_path=rytm_path,
            total_minutes=0,
        )
    with pytest.raises(ValueError, match="segment_minutes must be >= 1"):
        build_dual_machine_style_performance_set_plan_report(
            ("jose_core_techno",),
            rytm_sysex_path=rytm_path,
            segment_minutes=0,
        )
    plan = build_dual_machine_style_performance_set_plan_report(
        ("jose_core_techno",),
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
    )
    with pytest.raises(ValueError, match="event_limit must be >= 0"):
        format_dual_machine_style_performance_set_plan_report(
            plan,
            include_events=True,
            event_limit=-1,
        )


def test_performance_set_plan_formats_operator_report_with_event_details(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        build_dual_machine_style_performance_set_plan_report,
        format_dual_machine_style_performance_set_plan_report,
    )

    rytm_path, a4_path = _performance_set_bank_files(tmp_path)
    plan = build_dual_machine_style_performance_set_plan_report(
        ("jose_core_techno", "birmingham_pressure", "warehouse_peak"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=300,
        discovery_start=35,
        discovery_end=75,
    )
    lines = format_dual_machine_style_performance_set_plan_report(
        plan,
        include_events=True,
        event_limit=1,
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive dual-machine style performance set plan"
    assert "Scope: dual" in lines
    assert "Total duration minutes: 300" in lines
    assert "Segment count: 3" in lines
    assert "Discovery ramp: 35 -> 75" in lines
    assert "Performance segments:" in lines
    assert "- 1. 00:00-01:40 | jose_core_techno | discovery 35" in text
    assert "- 3. 03:20-05:00 | warehouse_peak | discovery 75" in text
    assert "Event preview for segment 1 / jose_core_techno:" in lines
    assert "- Showing first 1 of " in text
    assert "Rytm Pad 1" in text
    assert "- performance set plan" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_performance_set_plan_formats_all_events_and_unchanged_rytm_scope(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        build_dual_machine_style_performance_set_plan_report,
        format_dual_machine_style_performance_set_plan_report,
    )

    rytm_path, a4_path = _performance_set_bank_files(tmp_path)
    rytm_plan = build_dual_machine_style_performance_set_plan_report(
        ("jose_core_techno",),
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
    )
    all_event_lines = format_dual_machine_style_performance_set_plan_report(
        rytm_plan,
        include_events=True,
        event_limit=0,
    )
    assert "- Showing all events" in all_event_lines

    a4_plan = build_dual_machine_style_performance_set_plan_report(
        ("jose_core_techno",),
        analog_four_sysex_path=a4_path,
        scope="analog-four-only",
    )
    blocked_event_lines = format_dual_machine_style_performance_set_plan_report(
        a4_plan,
        include_events=True,
    )
    assert "  Rytm: unchanged by scope" in blocked_event_lines
    assert "- No mock rows available because the selected preview is not ready." in (
        blocked_event_lines
    )


def test_performance_set_plan_serializes_json_contract_for_gui_and_analyzer(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        build_dual_machine_style_performance_set_plan_report,
        to_dual_machine_style_performance_set_plan_json,
    )

    rytm_path, _ = _performance_set_bank_files(tmp_path)
    plan = build_dual_machine_style_performance_set_plan_report(
        ("jose_core_techno", "warehouse_peak"),
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
        segment_minutes=60,
        discovery_start=25,
        discovery_end=85,
    )
    payload = to_dual_machine_style_performance_set_plan_json(plan)

    assert payload["style_keys"] == ["jose_core_techno", "warehouse_peak"]
    assert payload["scope"] == "rytm-only"
    assert payload["total_minutes"] == 120
    assert payload["discovery_ramp"] == {"start": 25, "end": 85}
    assert payload["totals"]["segments"] == 2
    assert payload["segments"][0]["time_window"] == "00:00-01:00"
    assert payload["segments"][1]["discovery_amount"] == 85
    assert payload["segments"][0]["preview"]["machines"]["rytm"]["kit_name"] == ("SET RYTM ONE")
    assert payload["segments"][0]["preview"]["machines"]["analog_four"] is None
    assert payload["safety"][0] == "passive/read-only"


def test_performance_set_plan_cli_parser_accepts_show_options():
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        _parse_cli_args,
    )

    assert _parse_cli_args(
        [
            "jose_core_techno",
            "birmingham_pressure",
            "--rytm",
            "rytm.syx",
            "--analog-four",
            "a4.syx",
            "--scope",
            "dual",
            "--rank",
            "2",
            "--total-minutes",
            "300",
            "--segment-minutes",
            "60",
            "--discovery-start",
            "25",
            "--discovery-end",
            "85",
            "--events",
            "--limit",
            "0",
            "--json",
        ]
    ) == {
        "style_keys": ("jose_core_techno", "birmingham_pressure"),
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "dual",
        "selection_rank": 2,
        "total_minutes": 300,
        "segment_minutes": 60,
        "discovery_start": 25,
        "discovery_end": 85,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }


def test_performance_set_plan_cli_parser_auto_scopes_from_paths():
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        _parse_cli_args,
    )

    assert (
        _parse_cli_args(["jose_core_techno", "--rytm", "rytm.syx", "--analog-four", "a4.syx"])[
            "scope"
        ]
        == "dual"
    )
    assert _parse_cli_args(["jose_core_techno", "--rytm", "rytm.syx"])["scope"] == ("rytm-only")
    assert (
        _parse_cli_args(["jose_core_techno", "--analog-four", "a4.syx"])["scope"]
        == "analog-four-only"
    )


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["--json"], "usage"),
        (["jose_core_techno"], "requires at least one"),
        (["jose_core_techno", "--scope", "weird"], "unsupported scope"),
        (["jose_core_techno", "--rytm", "rytm.syx", "--rank", "0"], "must be >= 1"),
        (["jose_core_techno", "--rytm", "rytm.syx", "--total-minutes", "0"], ">= 1"),
        (["jose_core_techno", "--rytm", "rytm.syx", "--segment-minutes", "0"], ">= 1"),
        (["jose_core_techno", "--rytm", "rytm.syx", "--discovery-start", "bad"], "integer"),
        (["jose_core_techno", "--rytm", "rytm.syx", "--limit", "-1"], ">= 0"),
        (["jose_core_techno", "--rytm", "rytm.syx", "--limit", "bad"], "integer"),
        (["jose_core_techno", "--rytm"], "usage"),
        (["jose_core_techno", "--rytm", "rytm.syx", "--bogus", "x"], "usage"),
    ],
)
def test_performance_set_plan_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        _parse_cli_args,
    )

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_performance_set_plan_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        _handle_cli_report,
    )

    rytm_path, a4_path = _performance_set_bank_files(tmp_path)
    rc = _handle_cli_report(
        style_keys=("jose_core_techno", "warehouse_peak"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope="dual",
        selection_rank=1,
        total_minutes=120,
        segment_minutes=None,
        discovery_start=35,
        discovery_end=75,
        include_events=True,
        event_limit=1,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive dual-machine style performance set plan" in captured.out
    assert "00:00-01:00" in captured.out
    assert "01:00-02:00" in captured.out
    assert "SET RYTM ONE" in captured.out
    assert "SET A4 ONE" in captured.out
    assert captured.err == ""


def test_performance_set_plan_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        _handle_cli_report,
    )

    rytm_path, _ = _performance_set_bank_files(tmp_path)
    rc = _handle_cli_report(
        style_keys=("jose_core_techno", "warehouse_peak"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=None,
        scope="rytm-only",
        selection_rank=1,
        total_minutes=120,
        segment_minutes=None,
        discovery_start=35,
        discovery_end=75,
        include_events=False,
        event_limit=24,
        json_output=True,
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["totals"]["segments"] == 2
    assert payload["segments"][1]["style_key"] == "warehouse_peak"
    assert payload["segments"][1]["preview"]["machines"]["rytm"]["kit_name"] == ("SET RYTM ONE")
    assert captured.err == ""


def test_performance_set_plan_cli_handler_reports_errors(capsys: pytest.CaptureFixture[str]):
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        _handle_cli_report,
    )

    rc = _handle_cli_report(
        style_keys=("jose_core_techno",),
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope="dual",
        selection_rank=1,
        total_minutes=120,
        segment_minutes=None,
        discovery_start=35,
        discovery_end=75,
        include_events=False,
        event_limit=24,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "requires --rytm" in captured.err


def test_performance_set_plan_cli_error_formatter():
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        _format_cli_error,
    )

    assert _format_cli_error(ValueError("nope")) == "Error: nope"
