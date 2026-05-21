"""Tests for passive dual-machine live style audition reports."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _live_audition_framed(payload: bytes) -> bytes:
    return bytes([0xF0]) + payload + bytes([0xF7])


def _live_audition_a4_payload(name: bytes) -> bytes:
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + name[:16].ljust(16, b"\x00")
    return _live_audition_framed(payload)


def _live_audition_bank_files(tmp_path: Path) -> tuple[Path, Path]:
    from conftest import rytm_real_layout_kit_payload

    rytm_path = tmp_path / "rytm-live-bank.syx"
    rytm_path.write_bytes(
        _live_audition_framed(rytm_real_layout_kit_payload(name=b"LIVE RYTM ONE"))
        + _live_audition_framed(rytm_real_layout_kit_payload(name=b"LIVE RYTM TWO"))
    )
    a4_path = tmp_path / "a4-live-bank.syx"
    a4_path.write_bytes(
        _live_audition_a4_payload(b"LIVE A4 ONE") + _live_audition_a4_payload(b"LIVE A4 TWO")
    )
    return rytm_path, a4_path


def test_live_audition_builds_multi_style_dual_sequence_when_given_saved_banks(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_live_audition import (
        build_dual_machine_style_live_audition_report,
    )

    rytm_path, a4_path = _live_audition_bank_files(tmp_path)
    plan = build_dual_machine_style_live_audition_report(
        ("jose_core_techno", "birmingham_pressure"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )

    assert plan.style_keys == ("jose_core_techno", "birmingham_pressure")
    assert plan.scope == "dual"
    assert plan.style_count == 2
    assert plan.ready_style_count == 0
    assert plan.partial_style_count == 2
    assert plan.blocked_style_count == 0
    assert plan.total_mock_message_count > 0
    assert plan.total_event_row_count == sum(
        entry.preview_plan.total_event_row_count for entry in plan.entries
    )
    assert [entry.position for entry in plan.entries] == [1, 2]
    assert [entry.style_key for entry in plan.entries] == [
        "jose_core_techno",
        "birmingham_pressure",
    ]
    assert all(entry.preview_plan.rytm_preview is not None for entry in plan.entries)
    assert all(entry.preview_plan.analog_four_preview is not None for entry in plan.entries)


def test_live_audition_builds_rytm_only_ranked_sequence_when_a4_is_unavailable(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_live_audition import (
        build_dual_machine_style_live_audition_report,
    )

    rytm_path, _ = _live_audition_bank_files(tmp_path)
    plan = build_dual_machine_style_live_audition_report(
        ("jose_core_techno", "warehouse_peak"),
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
        selection_rank=2,
    )

    assert plan.scope == "rytm-only"
    assert plan.selection_rank == 2
    assert plan.ready_style_count == 2
    assert plan.partial_style_count == 0
    assert plan.blocked_style_count == 0
    assert all(entry.preview_plan.rytm_preview is not None for entry in plan.entries)
    assert all(entry.preview_plan.rytm_preview.slot == 1 for entry in plan.entries)
    assert all(entry.preview_plan.analog_four_preview is None for entry in plan.entries)
    assert all("leave Analog Four unchanged" in entry.operator_action for entry in plan.entries)


def test_live_audition_rejects_empty_style_sequence_and_bad_limits(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_live_audition import (
        _event_preview_lines,
        build_dual_machine_style_live_audition_report,
        format_dual_machine_style_live_audition_report,
    )

    rytm_path, _ = _live_audition_bank_files(tmp_path)

    with pytest.raises(ValueError, match="at least one style key"):
        build_dual_machine_style_live_audition_report((), rytm_sysex_path=rytm_path)

    plan = build_dual_machine_style_live_audition_report(
        ("jose_core_techno",),
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
    )
    with pytest.raises(ValueError, match="event_limit must be >= 0"):
        format_dual_machine_style_live_audition_report(
            plan,
            include_events=True,
            event_limit=-1,
        )
    with pytest.raises(ValueError, match="event_limit must be >= 0"):
        _event_preview_lines(plan.entries[0], event_limit=-1)


def test_live_audition_formats_single_machine_scopes_and_event_limit_variants(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_live_audition import (
        build_dual_machine_style_live_audition_report,
        format_dual_machine_style_live_audition_report,
    )

    rytm_path, a4_path = _live_audition_bank_files(tmp_path)
    rytm_plan = build_dual_machine_style_live_audition_report(
        ("jose_core_techno",),
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
    )
    rytm_lines = format_dual_machine_style_live_audition_report(
        rytm_plan,
        include_events=True,
        event_limit=0,
    )
    summary_lines = format_dual_machine_style_live_audition_report(rytm_plan)

    assert "  Analog Four: unchanged by scope" in rytm_lines
    assert "- Showing all events" in rytm_lines
    assert "Event preview for jose_core_techno:" not in summary_lines

    a4_plan = build_dual_machine_style_live_audition_report(
        ("jose_core_techno",),
        analog_four_sysex_path=a4_path,
        scope="analog-four-only",
    )
    a4_lines = format_dual_machine_style_live_audition_report(
        a4_plan,
        include_events=True,
    )

    assert "  Rytm: unchanged by scope" in a4_lines
    assert "- No mock rows available because the selected preview is not ready." in a4_lines


def test_live_audition_formats_analog_four_mock_event_row():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_mock_preview import (
        AnalogFourStyleMutationMockPreviewEvent,
    )
    from rytm_randomizer.reports.dual_machine_style_live_audition import (
        _format_analog_four_event_row,
    )

    line = _format_analog_four_event_row(
        AnalogFourStyleMutationMockPreviewEvent(
            track=2,
            role_key="lead",
            zone="filter",
            parameter="Filter 1 Frequency",
            channel=1,
            control=18,
            value=93,
            target_bias=18,
            mutation_depth="groove",
            target_direction="higher",
        )
    )

    assert line == (
        "- Analog Four Track 2 | lead | filter | Filter 1 Frequency | "
        "ch 1 | CC18 -> 93 | bias 18 | depth groove | direction higher"
    )


def test_live_audition_formats_operator_report_with_event_details(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_live_audition import (
        build_dual_machine_style_live_audition_report,
        format_dual_machine_style_live_audition_report,
    )

    rytm_path, a4_path = _live_audition_bank_files(tmp_path)
    plan = build_dual_machine_style_live_audition_report(
        ("jose_core_techno", "birmingham_pressure"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    lines = format_dual_machine_style_live_audition_report(
        plan,
        include_events=True,
        event_limit=1,
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive dual-machine style live audition"
    assert "Scope: dual" in lines
    assert "Style sequence:" in lines
    assert "1. jose_core_techno" in lines
    assert "2. birmingham_pressure" in lines
    assert "Ready styles: 0" in lines
    assert "Partial styles: 2" in lines
    assert "Audition entries:" in lines
    assert "Event preview for jose_core_techno:" in lines
    assert "- Showing first 1 of " in text
    assert "Rytm Pad 1" in text
    assert "- live audition selection set" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_live_audition_serializes_json_contract_for_gui_and_future_analyzer(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_live_audition import (
        build_dual_machine_style_live_audition_report,
        to_dual_machine_style_live_audition_json,
    )

    rytm_path, _ = _live_audition_bank_files(tmp_path)
    plan = build_dual_machine_style_live_audition_report(
        ("jose_core_techno", "warehouse_peak"),
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
        discovery_amount=95,
    )
    payload = to_dual_machine_style_live_audition_json(plan)

    assert payload["style_keys"] == ["jose_core_techno", "warehouse_peak"]
    assert payload["scope"] == "rytm-only"
    assert payload["discovery_amount"] == 95
    assert payload["totals"]["styles"] == 2
    assert payload["totals"]["ready"] == 2
    assert payload["entries"][0]["position"] == 1
    assert payload["entries"][0]["style_key"] == "jose_core_techno"
    assert payload["entries"][0]["preview"]["machines"]["rytm"]["kit_name"] == ("LIVE RYTM ONE")
    assert payload["entries"][0]["preview"]["machines"]["analog_four"] is None
    assert payload["safety"][0] == "passive/read-only"


def test_live_audition_cli_parser_accepts_multiple_styles_and_options():
    from rytm_randomizer.reports.dual_machine_style_live_audition import _parse_cli_args

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
            "--discovery",
            "75",
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
        "discovery_amount": 75,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }


def test_live_audition_cli_parser_infers_scope_from_supplied_banks():
    from rytm_randomizer.reports.dual_machine_style_live_audition import _parse_cli_args

    assert (
        _parse_cli_args(
            [
                "jose_core_techno",
                "warehouse_peak",
                "--rytm",
                "rytm.syx",
                "--analog-four",
                "a4.syx",
            ]
        )["scope"]
        == "dual"
    )
    assert _parse_cli_args(["jose_core_techno", "--rytm", "rytm.syx"])["scope"] == "rytm-only"
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
        (["jose_core_techno", "--rytm", "rytm.syx", "--rank", "bad"], "integer"),
        (["jose_core_techno", "--rytm", "rytm.syx", "--discovery", "bad"], "integer"),
        (["jose_core_techno", "--rytm", "rytm.syx", "--limit", "-1"], "must be >= 0"),
        (["jose_core_techno", "--rytm"], "usage"),
        (["jose_core_techno", "--rytm", "rytm.syx", "--bogus", "x"], "usage"),
    ],
)
def test_live_audition_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.dual_machine_style_live_audition import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_live_audition_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_live_audition import _handle_cli_report

    rytm_path, a4_path = _live_audition_bank_files(tmp_path)
    rc = _handle_cli_report(
        style_keys=("jose_core_techno", "birmingham_pressure"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope="dual",
        selection_rank=1,
        discovery_amount=45,
        include_events=True,
        event_limit=1,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive dual-machine style live audition" in captured.out
    assert "1. jose_core_techno" in captured.out
    assert "2. birmingham_pressure" in captured.out
    assert "LIVE RYTM ONE" in captured.out
    assert "LIVE A4 ONE" in captured.out
    assert captured.err == ""


def test_live_audition_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_live_audition import _handle_cli_report

    rytm_path, _ = _live_audition_bank_files(tmp_path)
    rc = _handle_cli_report(
        style_keys=("jose_core_techno", "warehouse_peak"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=None,
        scope="rytm-only",
        selection_rank=1,
        discovery_amount=45,
        include_events=False,
        event_limit=24,
        json_output=True,
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["totals"]["styles"] == 2
    assert payload["entries"][1]["style_key"] == "warehouse_peak"
    assert payload["entries"][1]["preview"]["machines"]["rytm"]["kit_name"] == ("LIVE RYTM ONE")
    assert captured.err == ""


def test_live_audition_cli_handler_reports_errors(capsys: pytest.CaptureFixture[str]):
    from rytm_randomizer.reports.dual_machine_style_live_audition import _handle_cli_report

    rc = _handle_cli_report(
        style_keys=("jose_core_techno",),
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope="dual",
        selection_rank=1,
        discovery_amount=45,
        include_events=False,
        event_limit=24,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "requires --rytm" in captured.err


def test_live_audition_cli_error_formatter():
    from rytm_randomizer.reports.dual_machine_style_live_audition import _format_cli_error

    assert _format_cli_error(ValueError("bad live audition")) == "Error: bad live audition"
