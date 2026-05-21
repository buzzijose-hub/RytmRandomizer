"""Tests for passive reference performance arc presets."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _arc_framed(payload: bytes) -> bytes:
    return bytes([0xF0]) + payload + bytes([0xF7])


def _arc_a4_payload(name: bytes) -> bytes:
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + name[:16].ljust(16, b"\x00")
    return _arc_framed(payload)


def _arc_bank_files(tmp_path: Path) -> tuple[Path, Path]:
    from conftest import rytm_real_layout_kit_payload

    rytm_path = tmp_path / "rytm-reference-arc-bank.syx"
    rytm_path.write_bytes(
        _arc_framed(rytm_real_layout_kit_payload(name=b"ARC RYTM ONE"))
        + _arc_framed(rytm_real_layout_kit_payload(name=b"ARC RYTM TWO"))
    )
    a4_path = tmp_path / "a4-reference-arc-bank.syx"
    a4_path.write_bytes(_arc_a4_payload(b"ARC A4 ONE") + _arc_a4_payload(b"ARC A4 TWO"))
    return rytm_path, a4_path


def test_style_performance_arc_catalog_contains_jose_reference_arc():
    from rytm_randomizer.data.style_performance_arcs import STYLE_PERFORMANCE_ARCS

    arc = STYLE_PERFORMANCE_ARCS["jose_warehouse_five_hour"]

    assert arc.name == "Jose Warehouse Five Hour"
    assert arc.default_total_minutes == 300
    assert arc.default_scope == "dual"
    assert arc.default_selection_rank == 1
    assert arc.default_discovery_start == 30
    assert arc.default_discovery_end == 85
    assert arc.style_keys == (
        "jose_core_techno",
        "mills_hypnotic",
        "deep_dark_hypnosis",
        "birmingham_pressure",
        "industrial_dark",
        "warehouse_peak",
        "hood_stripped",
    )
    assert "Jeff Mills" in arc.references
    assert "Oscar Mulero" in arc.references
    assert "Chris Liebing & Andre Walter Stigmata 1-10" in arc.references
    assert "Surgeon" in arc.references


def test_style_performance_arc_validation_rejects_invalid_fact_rows():
    from rytm_randomizer.data.style_performance_arcs import (
        StylePerformanceArc,
        _validated_arcs,
    )

    valid = StylePerformanceArc(
        key="valid",
        name="Valid",
        summary="Valid reference arc.",
        references=("Jeff Mills",),
        tags=("valid",),
        style_keys=("mills_hypnotic",),
        default_scope="dual",
        default_total_minutes=60,
        default_selection_rank=1,
        default_discovery_start=30,
        default_discovery_end=60,
        operator_notes=("keep it passive",),
    )

    with pytest.raises(ValueError, match="default_total_minutes"):
        _validated_arcs((replace(valid, default_total_minutes=0),))
    with pytest.raises(ValueError, match="default_selection_rank"):
        _validated_arcs((replace(valid, default_selection_rank=0),))
    with pytest.raises(ValueError, match="default_discovery_start"):
        _validated_arcs((replace(valid, default_discovery_start=-1),))
    with pytest.raises(ValueError, match="default_discovery_end"):
        _validated_arcs((replace(valid, default_discovery_end=101),))
    with pytest.raises(ValueError, match="unknown styles"):
        _validated_arcs((replace(valid, style_keys=("missing",)),))


def test_style_performance_arc_report_formats_catalog_and_safety():
    from rytm_randomizer.reports.style_performance_arcs import (
        format_style_performance_arc_report,
    )

    lines = format_style_performance_arc_report()
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive style performance arc report"
    assert "- Arcs: 4" in lines
    assert "- Purpose: passive reference arcs for long-form live set planning" in lines
    assert "jose_warehouse_five_hour: Jose Warehouse Five Hour" in text
    assert "Primary references: Jeff Mills, Oscar Mulero" in text
    assert "Default plan: scope=dual, minutes=300, rank=1, discovery=30->85" in text
    assert "Style sequence: jose_core_techno -> mills_hypnotic" in text
    assert "- metadata and plan expansion only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_style_performance_arc_inspect_search_and_json_contract():
    from rytm_randomizer.data.style_performance_arcs import STYLE_PERFORMANCE_ARCS
    from rytm_randomizer.reports.style_performance_arcs import (
        format_style_performance_arc_inspection,
        format_style_performance_arc_search,
        to_style_performance_arc_json,
    )

    inspection = format_style_performance_arc_inspection("JOSE_WAREHOUSE_FIVE_HOUR")
    search = format_style_performance_arc_search("stigmata")
    missing = format_style_performance_arc_inspection("does_not_exist")
    payload = to_style_performance_arc_json(STYLE_PERFORMANCE_ARCS["jose_warehouse_five_hour"])

    assert "Key: jose_warehouse_five_hour" in inspection
    assert "Found: True" in inspection
    assert "References:" in inspection
    assert "- Jeff Mills" in inspection
    assert "Match count: 2" in search
    assert "- jose_warehouse_five_hour: Jose Warehouse Five Hour" in search
    assert "- stigmata_birmingham_assault: Stigmata Birmingham Assault" in search
    assert "Found: False" in missing
    assert payload["key"] == "jose_warehouse_five_hour"
    assert payload["default_plan"]["total_minutes"] == 300
    assert payload["style_keys"][0] == "jose_core_techno"
    assert payload["references"][:2] == ["Jeff Mills", "Oscar Mulero"]

    no_match = format_style_performance_arc_search("NO_MATCH")
    assert "Match count: 0" in no_match
    assert "- no matches found. No MIDI was sent. No command executed." in no_match


def test_style_performance_arc_set_plan_expands_to_dual_machine_plan(tmp_path: Path):
    from rytm_randomizer.data.style_performance_arcs import STYLE_PERFORMANCE_ARCS
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_set_plan_report,
        format_style_performance_arc_set_plan_report,
        to_style_performance_arc_set_plan_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_set_plan_report(
        "jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    arc = STYLE_PERFORMANCE_ARCS["jose_warehouse_five_hour"]

    assert report.arc.key == "jose_warehouse_five_hour"
    assert report.plan.style_keys == arc.style_keys
    assert report.plan.scope == "dual"
    assert report.plan.total_minutes == 300
    assert report.plan.discovery_start == 30
    assert report.plan.discovery_end == 85
    assert report.plan.segment_count == len(arc.style_keys)
    assert report.plan.partial_segment_count == len(arc.style_keys)
    assert all(segment.preview_plan.rytm_preview is not None for segment in report.plan.segments)
    assert all(
        segment.preview_plan.analog_four_preview is not None for segment in report.plan.segments
    )

    lines = format_style_performance_arc_set_plan_report(
        report,
        include_events=True,
        event_limit=1,
    )
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc set plan"
    assert "Arc: Jose Warehouse Five Hour" in lines
    assert "Key: jose_warehouse_five_hour" in lines
    assert "References: Jeff Mills, Oscar Mulero" in text
    assert "Embedded performance set plan:" in lines
    assert "- 1. 00:00-" in text
    assert "Event preview for segment 1 / jose_core_techno:" in text
    assert "- reference performance arc" in lines

    payload = to_style_performance_arc_set_plan_json(report)
    assert payload["arc"]["key"] == "jose_warehouse_five_hour"
    assert payload["performance_plan"]["style_keys"] == list(arc.style_keys)
    assert payload["performance_plan"]["totals"]["segments"] == len(arc.style_keys)
    assert payload["safety"][0] == "passive/read-only"


def test_style_performance_arc_set_plan_auto_scopes_a4_only(tmp_path: Path):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_set_plan_report,
    )

    _, a4_path = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_set_plan_report(
        "jose_warehouse_five_hour",
        analog_four_sysex_path=a4_path,
    )

    assert report.plan.scope == "analog-four-only"
    assert all(segment.preview_plan.rytm_preview is None for segment in report.plan.segments)
    assert all(
        segment.preview_plan.analog_four_preview is not None for segment in report.plan.segments
    )


def test_style_performance_arc_set_plan_supports_rytm_only_overrides(tmp_path: Path):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_set_plan_report,
    )

    rytm_path, _ = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_set_plan_report(
        "mills_mulero_tunnel",
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
        selection_rank=2,
        segment_minutes=30,
        discovery_start=40,
        discovery_end=40,
    )

    assert report.plan.scope == "rytm-only"
    assert report.plan.selection_rank == 2
    assert report.plan.total_minutes == 120
    assert [segment.discovery_amount for segment in report.plan.segments] == [40, 40, 40, 40]
    assert all(segment.preview_plan.rytm_preview is not None for segment in report.plan.segments)
    assert all(segment.preview_plan.analog_four_preview is None for segment in report.plan.segments)
    assert all(
        "leave Analog Four unchanged" in segment.operator_action for segment in report.plan.segments
    )


def test_style_performance_arc_set_plan_rejects_unknown_arc(tmp_path: Path):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_set_plan_report,
    )

    rytm_path, _ = _arc_bank_files(tmp_path)

    with pytest.raises(KeyError, match="unknown style performance arc"):
        build_style_performance_arc_set_plan_report(
            "does_not_exist",
            rytm_sysex_path=rytm_path,
        )


def test_style_performance_arc_set_plan_parser_and_handlers(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.style_performance_arcs import (
        _handle_style_performance_arc_set_plan_report,
        _parse_arc_set_plan_cli_args,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)

    assert _parse_arc_set_plan_cli_args(
        [
            "jose_warehouse_five_hour",
            "--rytm",
            "rytm.syx",
            "--analog-four",
            "a4.syx",
            "--scope",
            "dual",
            "--rank",
            "2",
            "--total-minutes",
            "240",
            "--segment-minutes",
            "30",
            "--discovery-start",
            "25",
            "--discovery-end",
            "90",
            "--events",
            "--limit",
            "0",
            "--json",
        ]
    ) == {
        "arc_key": "jose_warehouse_five_hour",
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "dual",
        "selection_rank": 2,
        "total_minutes": 240,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 90,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }

    rc = _handle_style_performance_arc_set_plan_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope="dual",
        selection_rank=1,
        total_minutes=None,
        segment_minutes=None,
        discovery_start=None,
        discovery_end=None,
        include_events=True,
        event_limit=1,
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive style performance arc set plan" in captured.out
    assert "Jose Warehouse Five Hour" in captured.out
    assert "ARC RYTM ONE" in captured.out
    assert captured.err == ""

    rc = _handle_style_performance_arc_set_plan_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=None,
        scope="rytm-only",
        selection_rank=1,
        total_minutes=None,
        segment_minutes=20,
        discovery_start=None,
        discovery_end=None,
        include_events=False,
        event_limit=24,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["arc"]["key"] == "jose_warehouse_five_hour"
    assert payload["performance_plan"]["scope"] == "rytm-only"
    assert captured.err == ""

    rc = _handle_style_performance_arc_set_plan_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope="dual",
        selection_rank=1,
        total_minutes=None,
        segment_minutes=None,
        discovery_start=None,
        discovery_end=None,
        include_events=False,
        event_limit=24,
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "requires --rytm" in captured.err


def test_style_performance_arc_set_plan_parser_rejects_bad_args():
    from rytm_randomizer.reports.style_performance_arcs import (
        _format_cli_error,
        _parse_arc_key,
        _parse_arc_set_plan_cli_args,
        _parse_no_args,
        _parse_query,
    )

    bad_cases = [
        ([], "usage"),
        (["--json"], "usage"),
        (["jose_warehouse_five_hour", "--rytm"], "usage"),
        (["jose_warehouse_five_hour", "--bogus"], "usage"),
        (["jose_warehouse_five_hour", "--limit", "bad"], "integer"),
        (["jose_warehouse_five_hour", "--limit", "-1"], ">= 0"),
        (["jose_warehouse_five_hour", "--rank", "0"], ">= 1"),
    ]
    for argv, message in bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_arc_set_plan_cli_args(argv)

    with pytest.raises(ValueError, match="no arguments"):
        _parse_no_args(["unexpected"])
    with pytest.raises(ValueError, match="exactly one"):
        _parse_arc_key([])
    with pytest.raises(ValueError, match="exactly one"):
        _parse_query([])
    assert _format_cli_error(ValueError("nope")) == "Error: nope"


def test_style_performance_arc_cli_dispatch_and_help(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.cli import main
    from rytm_randomizer.help_text import resolve_help_text

    rytm_path, a4_path = _arc_bank_files(tmp_path)

    assert main(["list-style-performance-arcs"]) == 0
    captured = capsys.readouterr()
    assert "jose_warehouse_five_hour" in captured.out
    assert captured.err == ""

    assert main(["style-performance-arc-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc report" in captured.out

    assert main(["inspect-style-performance-arc", "jose_warehouse_five_hour"]) == 0
    captured = capsys.readouterr()
    assert "Found: True" in captured.out
    assert "Jeff Mills" in captured.out

    assert main(["inspect-style-performance-arc", "does_not_exist"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Found: False" in captured.err

    assert main(["search-style-performance-arcs", "Regis"]) == 0
    captured = capsys.readouterr()
    assert "jose_warehouse_five_hour" in captured.out

    assert (
        main(
            [
                "style-performance-arc-set-plan-report",
                "jose_warehouse_five_hour",
                "--rytm",
                str(rytm_path),
                "--analog-four",
                str(a4_path),
                "--events",
                "--limit",
                "1",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "Jose Warehouse Five Hour" in captured.out
    assert "Embedded performance set plan:" in captured.out

    help_text = resolve_help_text("--help")
    assert "style-performance-arc-report" in help_text
    assert "list-style-performance-arcs" in help_text
    assert "style-performance-arc-set-plan-report <arc-key>" in help_text
    arc_help = resolve_help_text("style-performance-arc-set-plan-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-set-plan-report" in arc_help
    assert "Expands a named passive reference arc into a timed performance set plan." in arc_help
