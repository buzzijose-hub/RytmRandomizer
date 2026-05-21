"""Tests for selection-driven passive dual-machine style mock previews."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _framed(payload: bytes) -> bytes:
    return bytes([0xF0]) + payload + bytes([0xF7])


def _framed_a4_payload(name: bytes) -> bytes:
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + name[:16].ljust(16, b"\x00")
    return _framed(payload)


def _bank_files(tmp_path: Path) -> tuple[Path, Path]:
    from conftest import rytm_real_layout_kit_payload

    rytm_path = tmp_path / "rytm-bank.syx"
    rytm_path.write_bytes(
        _framed(rytm_real_layout_kit_payload(name=b"RYTM ONE"))
        + _framed(rytm_real_layout_kit_payload(name=b"RYTM TWO"))
    )
    a4_path = tmp_path / "a4-bank.syx"
    a4_path.write_bytes(_framed_a4_payload(b"A4 ONE") + _framed_a4_payload(b"A4 TWO"))
    return rytm_path, a4_path


def test_selection_mock_preview_builds_dual_preview_from_top_selection(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        build_dual_machine_style_selection_mock_preview_report,
    )

    rytm_path, a4_path = _bank_files(tmp_path)
    plan = build_dual_machine_style_selection_mock_preview_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )

    assert plan.scope == "dual"
    assert plan.selection_rank == 1
    assert plan.selection_readiness == "partial"
    assert plan.operator_action.startswith("Use the Rytm snapshot now")
    assert plan.rytm_preview is not None
    assert plan.rytm_preview.slot == 0
    assert plan.rytm_preview.kit_name == "RYTM ONE"
    assert plan.rytm_preview.preview_ready is True
    assert plan.analog_four_preview is not None
    assert plan.analog_four_preview.slot == 0
    assert plan.analog_four_preview.kit_name == "A4 ONE"
    assert plan.analog_four_preview.preview_ready is False
    assert plan.total_mock_message_count == plan.rytm_preview.mock_message_count
    assert plan.total_deferred_row_count == plan.analog_four_preview.deferred_row_count


def test_selection_mock_preview_supports_rytm_only_scope_and_rank(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        build_dual_machine_style_selection_mock_preview_report,
    )

    rytm_path, _ = _bank_files(tmp_path)
    plan = build_dual_machine_style_selection_mock_preview_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
        selection_rank=2,
    )

    assert plan.scope == "rytm-only"
    assert plan.selection_rank == 2
    assert plan.selection_readiness == "ready"
    assert plan.rytm_preview is not None
    assert plan.rytm_preview.slot == 1
    assert plan.rytm_preview.kit_name == "RYTM TWO"
    assert plan.analog_four_preview is None
    assert "leave Analog Four unchanged" in plan.operator_action


def test_selection_mock_preview_supports_a4_only_alias(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        build_dual_machine_style_selection_mock_preview_report,
    )

    _, a4_path = _bank_files(tmp_path)
    plan = build_dual_machine_style_selection_mock_preview_report(
        "jose_core_techno",
        analog_four_sysex_path=a4_path,
        scope="a4-only",
    )

    assert plan.scope == "analog-four-only"
    assert plan.selection_readiness == "blocked"
    assert plan.rytm_preview is None
    assert plan.analog_four_preview is not None
    assert plan.analog_four_preview.kit_name == "A4 ONE"
    assert "leave Rytm unchanged" in plan.operator_action


def test_selection_mock_preview_rejects_out_of_range_rank(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        _selected_entry,
        build_dual_machine_style_selection_mock_preview_report,
    )

    rytm_path, _ = _bank_files(tmp_path)

    with pytest.raises(ValueError, match="selection_rank must be >= 1"):
        build_dual_machine_style_selection_mock_preview_report(
            "jose_core_techno",
            rytm_sysex_path=rytm_path,
            scope="rytm-only",
            selection_rank=0,
        )
    with pytest.raises(ValueError, match="selection_rank must be between 1 and 2"):
        build_dual_machine_style_selection_mock_preview_report(
            "jose_core_techno",
            rytm_sysex_path=rytm_path,
            scope="rytm-only",
            selection_rank=3,
        )
    with pytest.raises(ValueError, match="selection has no candidates"):
        _selected_entry((), selection_rank=1)


def test_selection_mock_preview_formats_operator_report_with_events(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        build_dual_machine_style_selection_mock_preview_report,
        format_dual_machine_style_selection_mock_preview_report,
    )

    rytm_path, a4_path = _bank_files(tmp_path)
    plan = build_dual_machine_style_selection_mock_preview_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    lines = format_dual_machine_style_selection_mock_preview_report(
        plan,
        include_events=True,
        event_limit=1,
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive dual-machine style selection mock preview"
    assert "Scope: dual" in lines
    assert "Selection rank: 1" in lines
    assert "Selection readiness: partial" in lines
    assert "- Kit: RYTM ONE" in lines
    assert "- Kit: A4 ONE" in lines
    assert "Event preview:" in lines
    assert "- Showing first 1 of " in text
    assert "Rytm Pad 1" in text
    assert "Deferred rows:" in lines
    assert "- selection-driven mock preview" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_selection_mock_preview_formats_unchanged_machine_and_rejects_bad_limit(
    tmp_path: Path,
):
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        build_dual_machine_style_selection_mock_preview_report,
        format_dual_machine_style_selection_mock_preview_report,
    )

    rytm_path, _ = _bank_files(tmp_path)
    plan = build_dual_machine_style_selection_mock_preview_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
    )

    lines = format_dual_machine_style_selection_mock_preview_report(plan)

    assert "Analog Four:" in lines
    assert "- unchanged by scope" in lines
    with pytest.raises(ValueError, match="event_limit must be >= 0"):
        format_dual_machine_style_selection_mock_preview_report(
            plan,
            include_events=True,
            event_limit=-1,
        )


def test_selection_mock_preview_formats_all_events_and_no_event_rows(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        build_dual_machine_style_selection_mock_preview_report,
        format_dual_machine_style_selection_mock_preview_report,
    )

    rytm_path, a4_path = _bank_files(tmp_path)
    dual_plan = build_dual_machine_style_selection_mock_preview_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    all_event_lines = format_dual_machine_style_selection_mock_preview_report(
        dual_plan,
        include_events=True,
        event_limit=0,
    )

    assert "- Showing all events" in all_event_lines

    a4_only_plan = build_dual_machine_style_selection_mock_preview_report(
        "jose_core_techno",
        analog_four_sysex_path=a4_path,
        scope="analog-four-only",
    )
    no_event_lines = format_dual_machine_style_selection_mock_preview_report(
        a4_only_plan,
        include_events=True,
    )

    assert "Rytm:" in no_event_lines
    assert "- unchanged by scope" in no_event_lines
    assert "- No mock rows available because the selected preview is not ready." in no_event_lines


def test_selection_mock_preview_formats_analog_four_mock_event_row():
    from rytm_randomizer.devices.strategies.analog_four_style_mutation_mock_preview import (
        AnalogFourStyleMutationMockPreviewEvent,
    )
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        _format_analog_four_event_row,
    )

    line = _format_analog_four_event_row(
        AnalogFourStyleMutationMockPreviewEvent(
            track=1,
            role_key="bassline",
            zone="filter",
            parameter="Filter 1 Frequency",
            channel=0,
            control=18,
            value=96,
            target_bias=22,
            mutation_depth="groove",
            target_direction="higher",
        )
    )

    assert line == (
        "- Analog Four Track 1 | bassline | filter | Filter 1 Frequency | "
        "ch 0 | CC18 -> 96 | bias 22 | depth groove | direction higher"
    )


def test_selection_mock_preview_serializes_json_contract(tmp_path: Path):
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        build_dual_machine_style_selection_mock_preview_report,
        to_dual_machine_style_selection_mock_preview_json,
    )

    rytm_path, _ = _bank_files(tmp_path)
    plan = build_dual_machine_style_selection_mock_preview_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
    )
    payload = to_dual_machine_style_selection_mock_preview_json(plan)

    assert payload["scope"] == "rytm-only"
    assert payload["selection"]["rank"] == 1
    assert payload["selection"]["readiness"] == "ready"
    assert payload["machines"]["rytm"]["kit_name"] == "RYTM ONE"
    assert payload["machines"]["analog_four"] is None
    assert payload["safety"][0] == "passive/read-only"


def test_selection_mock_preview_cli_parser_accepts_selection_options():
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        _parse_cli_args,
    )

    assert _parse_cli_args(
        [
            "jose_core_techno",
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
        "style_key": "jose_core_techno",
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "dual",
        "selection_rank": 2,
        "discovery_amount": 75,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }


def test_selection_mock_preview_cli_parser_infers_scopes():
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        _parse_cli_args,
    )

    assert (
        _parse_cli_args(["jose_core_techno", "--rytm", "rytm.syx", "--analog-four", "a4.syx"])[
            "scope"
        ]
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
def test_selection_mock_preview_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        _parse_cli_args,
    )

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_selection_mock_preview_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        _handle_cli_report,
    )

    rytm_path, a4_path = _bank_files(tmp_path)
    rc = _handle_cli_report(
        style_key="jose_core_techno",
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
    assert "RytmRandomizer passive dual-machine style selection mock preview" in captured.out
    assert "- Kit: RYTM ONE" in captured.out
    assert "- Kit: A4 ONE" in captured.out
    assert "Selection readiness: partial" in captured.out
    assert captured.err == ""


def test_selection_mock_preview_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        _handle_cli_report,
    )

    rytm_path, _ = _bank_files(tmp_path)
    rc = _handle_cli_report(
        style_key="jose_core_techno",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=None,
        scope="rytm-only",
        selection_rank=1,
        discovery_amount=95,
        include_events=False,
        event_limit=24,
        json_output=True,
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["discovery_amount"] == 95
    assert payload["machines"]["rytm"]["kit_name"] == "RYTM ONE"
    assert payload["machines"]["analog_four"] is None
    assert captured.err == ""


def test_selection_mock_preview_cli_handler_reports_errors(capsys):
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        _handle_cli_report,
    )

    rc = _handle_cli_report(
        style_key="jose_core_techno",
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


def test_selection_mock_preview_cli_error_formatter():
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        _format_cli_error,
    )

    assert _format_cli_error(ValueError("bad selection preview")) == (
        "Error: bad selection preview"
    )
