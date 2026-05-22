"""Tests for passive reference performance arc presets."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

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


def test_style_performance_arc_readiness_matrix_ranks_all_arcs_against_saved_banks(
    tmp_path: Path,
):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_readiness_report,
        format_style_performance_arc_readiness_report,
        to_style_performance_arc_readiness_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_readiness_report(
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )

    assert report.scope == "dual"
    assert report.arc_count == 4
    assert len(report.entries) == 4
    assert report.ready_arc_count == 0
    assert report.partial_arc_count == 4
    assert report.blocked_arc_count == 0
    assert report.total_segment_count == sum(entry.plan.segment_count for entry in report.entries)
    assert report.total_event_row_count == sum(
        entry.plan.total_event_row_count for entry in report.entries
    )

    jose_entry = next(
        entry for entry in report.entries if entry.arc.key == "jose_warehouse_five_hour"
    )
    assert jose_entry.readiness == "partial"
    assert jose_entry.plan.segment_count == len(jose_entry.arc.style_keys)
    assert jose_entry.average_selection_score > 0
    assert "audition" in jose_entry.operator_action

    lines = format_style_performance_arc_readiness_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc readiness matrix"
    assert "Scope: dual" in lines
    assert "Arc count: 4" in lines
    assert "Partial arcs: 4" in lines
    assert "Arc readiness matrix:" in lines
    assert "jose_warehouse_five_hour | Jose Warehouse Five Hour | partial" in text
    assert "Average selection score:" in text
    assert "- reference arc readiness matrix" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_readiness_json(report)
    assert payload["scope"] == "dual"
    assert payload["totals"]["arcs"] == 4
    assert payload["totals"]["partial"] == 4
    assert payload["entries"][0]["arc"]["key"]
    assert payload["entries"][0]["readiness"] == "partial"
    assert payload["entries"][0]["performance_plan"]["totals"]["segments"] >= 1


def test_style_performance_arc_readiness_covers_blocked_and_empty_plan_edges(
    tmp_path: Path,
):
    from rytm_randomizer.data.style_performance_arcs import STYLE_PERFORMANCE_ARCS
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        DualMachineStylePerformanceSetPlan,
    )
    from rytm_randomizer.reports.style_performance_arcs import (
        StylePerformanceArcReadinessReport,
        _readiness_entry_from_set_plan,
        build_style_performance_arc_readiness_report,
        format_style_performance_arc_readiness_report,
        to_style_performance_arc_readiness_json,
    )

    rytm_path, _ = _arc_bank_files(tmp_path)
    rytm_only_report = build_style_performance_arc_readiness_report(
        ("jose_warehouse_five_hour",),
        rytm_sysex_path=rytm_path,
    )
    assert rytm_only_report.scope == "rytm-only"

    with pytest.raises(ValueError, match="requires at least one arc"):
        build_style_performance_arc_readiness_report((), rytm_sysex_path=rytm_path)

    arc = STYLE_PERFORMANCE_ARCS["jose_warehouse_five_hour"]
    blocked_plan = DualMachineStylePerformanceSetPlan(
        style_keys=arc.style_keys,
        scope="dual",
        total_minutes=0,
        discovery_start=30,
        discovery_end=85,
        selection_rank=1,
        segment_count=1,
        ready_segment_count=0,
        partial_segment_count=0,
        blocked_segment_count=1,
        total_event_row_count=0,
        total_mock_message_count=0,
        total_deferred_row_count=0,
        segments=(),
    )
    entry = _readiness_entry_from_set_plan(arc=arc, plan=blocked_plan)
    report = StylePerformanceArcReadinessReport(
        scope="dual",
        arc_count=1,
        ready_arc_count=0,
        partial_arc_count=0,
        blocked_arc_count=1,
        total_segment_count=1,
        total_event_row_count=0,
        total_mock_message_count=0,
        total_deferred_row_count=0,
        entries=(entry,),
    )

    lines = format_style_performance_arc_readiness_report(report, entry_limit=0)
    payload = to_style_performance_arc_readiness_json(report)

    assert entry.readiness == "blocked"
    assert entry.average_selection_score == 0
    assert "Blocked for this kit-bank" in entry.operator_action
    assert "Blocked arcs: 1" in lines
    assert payload["entries"][0]["operator_action"] == entry.operator_action
    with pytest.raises(ValueError, match="entry_limit"):
        format_style_performance_arc_readiness_report(report, entry_limit=-1)


def test_style_performance_arc_audition_packet_selects_best_arc_and_embeds_plan(
    tmp_path: Path,
):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_audition_packet_report,
        format_style_performance_arc_audition_packet_report,
        to_style_performance_arc_audition_packet_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_audition_packet_report(
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )

    assert report.selected_entry in report.readiness_report.entries
    assert report.selected_entry.position == 1
    assert report.selected_entry.plan.segment_count >= 1
    assert report.selected_entry.plan is report.selected_set_plan

    lines = format_style_performance_arc_audition_packet_report(
        report,
        include_events=True,
        event_limit=1,
    )
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc audition packet"
    assert "Selected arc:" in text
    assert "Readiness matrix:" in text
    assert "Selected set plan:" in text
    assert "Event preview for segment" in text
    assert "- reference arc audition packet" in lines
    assert "- no MIDI sending" in lines

    payload = to_style_performance_arc_audition_packet_json(report)
    assert payload["selected"]["arc"]["key"] == report.selected_entry.arc.key
    assert payload["selected"]["readiness"] == report.selected_entry.readiness
    assert payload["readiness_matrix"]["totals"]["arcs"] == report.readiness_report.arc_count
    assert payload["selected_set_plan"]["performance_plan"]["totals"]["segments"] >= 1
    assert payload["safety"][0] == "passive/read-only"


def test_style_performance_arc_rehearsal_manifest_builds_operator_runbook(
    tmp_path: Path,
):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_rehearsal_manifest_report,
        format_style_performance_arc_rehearsal_manifest_report,
        to_style_performance_arc_rehearsal_manifest_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_rehearsal_manifest_report(
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )

    assert report.selected_entry is report.audition_packet.selected_entry
    assert report.selected_set_plan is report.audition_packet.selected_set_plan
    assert report.segment_count == report.selected_set_plan.segment_count
    assert report.ready_segment_count == report.selected_set_plan.ready_segment_count
    assert report.partial_segment_count == report.selected_set_plan.partial_segment_count
    assert report.blocked_segment_count == report.selected_set_plan.blocked_segment_count
    assert report.segments

    first_segment = report.segments[0]
    first_plan_segment = report.selected_set_plan.segments[0]
    assert first_segment.position == 1
    assert first_segment.style_key == first_plan_segment.style_key
    assert first_segment.time_window == first_plan_segment.time_window
    assert first_segment.discovery_amount == first_plan_segment.discovery_amount
    assert first_segment.readiness == first_plan_segment.selection_readiness
    assert first_segment.event_row_count == first_plan_segment.event_row_count
    assert first_segment.mock_message_count == first_plan_segment.mock_message_count
    assert "slot" in first_segment.rytm_preview_summary
    assert "slot" in first_segment.analog_four_preview_summary

    lines = format_style_performance_arc_rehearsal_manifest_report(
        report,
        include_events=True,
        event_limit=1,
    )
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc rehearsal manifest"
    assert "Selected arc:" in lines
    assert "Preflight checklist:" in lines
    assert "- Confirm the saved Rytm kit bank before rehearsal." in lines
    assert "- Confirm the saved Analog Four kit bank before rehearsal." in lines
    assert "Segment runbook:" in lines
    assert "- 1. 00:00-" in text
    assert "Rytm preview:" in text
    assert "Analog Four preview:" in text
    assert "Event preview for segment" in text
    assert "- reference arc rehearsal manifest" in lines
    assert "- no MIDI sending" in lines

    payload = to_style_performance_arc_rehearsal_manifest_json(report)
    assert payload["selected"]["arc"]["key"] == report.selected_entry.arc.key
    assert payload["manifest"]["totals"]["segments"] == report.segment_count
    assert payload["manifest"]["segments"][0]["style_key"] == first_segment.style_key
    assert payload["manifest"]["segments"][0]["rytm_preview"] == (
        first_segment.rytm_preview_summary
    )
    assert payload["manifest"]["preflight"][0] == (
        "Confirm the saved Rytm kit bank before rehearsal."
    )
    assert payload["audition_packet"]["selected"]["arc"]["key"] == (report.selected_entry.arc.key)
    assert payload["safety"][0] == "passive/read-only"


def test_style_performance_arc_rehearsal_manifest_covers_single_machine_edges(
    tmp_path: Path,
):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_rehearsal_manifest_report,
        format_style_performance_arc_rehearsal_manifest_report,
    )

    _, a4_path = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_rehearsal_manifest_report(
        ("jose_warehouse_five_hour",),
        analog_four_sysex_path=a4_path,
        scope="analog-four-only",
    )

    assert report.selected_set_plan.scope == "analog-four-only"
    assert report.segments[0].rytm_preview_summary == "unchanged by scope"
    assert "Rytm is unchanged by this scope; leave its current kit alone." in (
        report.preflight_steps
    )
    assert "Confirm the saved Analog Four kit bank before rehearsal." in (report.preflight_steps)

    lines = format_style_performance_arc_rehearsal_manifest_report(report)
    text = "\n".join(lines)
    assert "Event previews:" not in lines
    assert "Rytm preview: unchanged by scope" in text
    assert "Analog Four preview: slot" in text

    with pytest.raises(ValueError, match="event_limit"):
        format_style_performance_arc_rehearsal_manifest_report(
            report,
            event_limit=-1,
        )


def test_style_performance_arc_live_session_packet_builds_operator_packet(
    tmp_path: Path,
):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_live_session_packet_report,
        format_style_performance_arc_live_session_packet_report,
        to_style_performance_arc_live_session_packet_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    packet = build_style_performance_arc_live_session_packet_report(
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )

    assert packet.selected_entry is packet.rehearsal_manifest.selected_entry
    assert packet.selected_set_plan is packet.rehearsal_manifest.selected_set_plan
    assert packet.segment_count == packet.rehearsal_manifest.segment_count
    assert packet.ready_segment_count == packet.rehearsal_manifest.ready_segment_count
    assert packet.partial_segment_count == packet.rehearsal_manifest.partial_segment_count
    assert packet.blocked_segment_count == packet.rehearsal_manifest.blocked_segment_count
    assert packet.launch_checklist
    assert packet.suggested_commands
    assert packet.segments
    suggested_commands = "\n".join(packet.suggested_commands)
    selected_arc_key = packet.selected_entry.arc.key
    selected_plan = packet.selected_set_plan
    assert f"style-performance-arc-live-session-packet-report {selected_arc_key}" in (
        suggested_commands
    )
    assert f"style-performance-arc-rehearsal-manifest-report {selected_arc_key}" in (
        suggested_commands
    )
    assert f"style-performance-arc-audition-packet-report {selected_arc_key}" in (
        suggested_commands
    )
    assert f"style-performance-arc-readiness-report {selected_arc_key}" in (suggested_commands)
    assert f"style-performance-arc-set-plan-report {selected_arc_key}" in (suggested_commands)
    assert f"--scope {selected_plan.scope}" in suggested_commands
    assert f"--rank {selected_plan.selection_rank}" in suggested_commands
    assert f"--total-minutes {selected_plan.total_minutes}" in suggested_commands
    assert f"--discovery-start {selected_plan.discovery_start}" in suggested_commands
    assert f"--discovery-end {selected_plan.discovery_end}" in suggested_commands

    first_segment = packet.segments[0]
    first_manifest_segment = packet.rehearsal_manifest.segments[0]
    assert first_segment.position == first_manifest_segment.position
    assert first_segment.style_key == first_manifest_segment.style_key
    assert first_segment.time_window == first_manifest_segment.time_window
    assert first_segment.discovery_amount == first_manifest_segment.discovery_amount
    assert first_segment.discovery_band == first_manifest_segment.discovery_band
    assert first_segment.mutation_depth == first_manifest_segment.mutation_depth
    assert first_segment.readiness == first_manifest_segment.readiness
    assert first_segment.listen_for
    assert first_segment.go_no_go_cue
    assert first_segment.reset_cue
    assert first_segment.rytm_preview_summary == first_manifest_segment.rytm_preview_summary
    assert first_segment.analog_four_preview_summary == (
        first_manifest_segment.analog_four_preview_summary
    )

    lines = format_style_performance_arc_live_session_packet_report(
        packet,
        include_events=True,
        event_limit=1,
    )
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live session packet"
    assert "Launch checklist:" in lines
    assert "Suggested passive commands:" in lines
    assert "Segment cards:" in lines
    assert "Listen for:" in text
    assert "Go/no-go cue:" in text
    assert "Reset cue:" in text
    assert "Event preview for segment" in text
    assert "- live rehearsal session packet" in lines
    assert "- no MIDI sending" in lines

    payload = to_style_performance_arc_live_session_packet_json(packet)
    assert payload["selected"]["arc"]["key"] == packet.selected_entry.arc.key
    assert payload["rehearsal_manifest"]["selected"]["arc"]["key"] == (
        packet.selected_entry.arc.key
    )
    assert payload["session_packet"]["scope"] == packet.selected_set_plan.scope
    assert payload["session_packet"]["launch_checklist"][0] == packet.launch_checklist[0]
    assert payload["session_packet"]["suggested_commands"][0] == packet.suggested_commands[0]
    assert payload["session_packet"]["segments"][0]["listen_for"] == first_segment.listen_for
    assert payload["safety"][0] == "passive/read-only"


def test_style_performance_arc_live_session_packet_covers_single_machine_edges(
    tmp_path: Path,
):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_live_session_packet_report,
        format_style_performance_arc_live_session_packet_report,
    )

    _, a4_path = _arc_bank_files(tmp_path)
    packet = build_style_performance_arc_live_session_packet_report(
        ("jose_warehouse_five_hour",),
        analog_four_sysex_path=a4_path,
        scope="analog-four-only",
    )

    assert packet.selected_set_plan.scope == "analog-four-only"
    assert "Rytm is unchanged by this scope; leave its current kit alone." in (
        packet.launch_checklist
    )
    assert "--analog-four <analog-four-syx-path> --scope analog-four-only" in (
        "\n".join(packet.suggested_commands)
    )
    assert packet.segments[0].rytm_preview_summary == "unchanged by scope"
    assert "Analog Four preview: slot" in "\n".join(
        format_style_performance_arc_live_session_packet_report(packet)
    )

    with pytest.raises(ValueError, match="event_limit"):
        format_style_performance_arc_live_session_packet_report(
            packet,
            event_limit=-1,
        )


def test_style_performance_arc_live_render_bundle_builds_segment_mock_packet(
    tmp_path: Path,
):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_live_render_bundle_report,
        format_style_performance_arc_live_render_bundle_report,
        to_style_performance_arc_live_render_bundle_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    bundle = build_style_performance_arc_live_render_bundle_report(
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )

    assert bundle.live_session_packet.selected_set_plan is bundle.selected_set_plan
    assert bundle.segment_count == bundle.selected_set_plan.segment_count
    assert bundle.total_event_row_count == bundle.selected_set_plan.total_event_row_count
    assert bundle.total_mock_message_count == bundle.selected_set_plan.total_mock_message_count
    assert bundle.total_deferred_row_count == bundle.selected_set_plan.total_deferred_row_count
    assert bundle.suggested_commands
    assert bundle.segments

    first_segment = bundle.segments[0]
    first_live_segment = bundle.live_session_packet.segments[0]
    first_set_segment = bundle.selected_set_plan.segments[0]
    assert first_segment.live_segment is first_live_segment
    assert first_segment.set_plan_segment is first_set_segment
    assert first_segment.position == first_live_segment.position
    assert first_segment.style_key == first_live_segment.style_key
    assert first_segment.time_window == first_live_segment.time_window
    assert first_segment.event_preview_rows
    assert first_segment.deferred_rows
    assert first_segment.preview_json["style_key"] == first_segment.style_key
    assert first_segment.preview_json["machines"]["rytm"] is not None
    assert first_segment.preview_json["machines"]["analog_four"] is not None
    assert "slot" in first_segment.rytm_preview_summary
    assert "slot" in first_segment.analog_four_preview_summary

    suggested_commands = "\n".join(bundle.suggested_commands)
    selected_arc_key = bundle.selected_entry.arc.key
    assert f"style-performance-arc-live-render-bundle-report {selected_arc_key}" in (
        suggested_commands
    )
    assert "style-performance-arc-live-session-packet-report" in suggested_commands
    assert "style-performance-arc-rehearsal-manifest-report" in suggested_commands

    lines = format_style_performance_arc_live_render_bundle_report(
        bundle,
        include_events=True,
        event_limit=1,
    )
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style performance arc live render bundle"
    assert "Render bundle summary:" in lines
    assert "Replayable passive commands:" in lines
    assert "Segment render bundles:" in lines
    assert "Mock render preview:" in text
    assert "Deferred rows:" in text
    assert "Event preview for segment" in text
    assert "- live render bundle" in lines
    assert "- mock render preview only" in lines
    assert "- no real MIDI rendering" in lines
    assert "- no MIDI sending" in lines

    all_event_lines = format_style_performance_arc_live_render_bundle_report(
        bundle,
        include_events=True,
        event_limit=0,
    )
    assert "  - Showing all events" in "\n".join(all_event_lines)

    sized_event_lines = format_style_performance_arc_live_render_bundle_report(
        bundle,
        include_events=True,
        event_limit=len(first_segment.event_preview_rows),
    )
    assert "  - Showing all events" in "\n".join(sized_event_lines)

    empty_event_bundle = replace(
        bundle,
        segments=(replace(first_segment, event_preview_rows=()),),
    )
    empty_event_lines = format_style_performance_arc_live_render_bundle_report(
        empty_event_bundle,
        include_events=True,
        event_limit=1,
    )
    assert "No mock rows available because the selected preview is not ready" in "\n".join(
        empty_event_lines
    )

    payload = to_style_performance_arc_live_render_bundle_json(bundle)
    assert payload["selected"]["arc"]["key"] == bundle.selected_entry.arc.key
    assert payload["live_session_packet"]["selected"]["arc"]["key"] == (
        bundle.selected_entry.arc.key
    )
    assert payload["render_bundle"]["scope"] == bundle.selected_set_plan.scope
    assert payload["render_bundle"]["totals"]["segments"] == bundle.segment_count
    assert payload["render_bundle"]["segments"][0]["style_key"] == first_segment.style_key
    assert payload["render_bundle"]["segments"][0]["event_preview_rows"] == list(
        first_segment.event_preview_rows
    )
    assert payload["render_bundle"]["segments"][0]["deferred_rows"] == list(
        first_segment.deferred_rows
    )
    assert payload["render_bundle"]["segments"][0]["preview"]["style_key"] == (
        first_segment.style_key
    )
    assert payload["safety"][0] == "passive/read-only"


def test_style_performance_arc_live_render_bundle_covers_single_machine_scope(
    tmp_path: Path,
):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_live_render_bundle_report,
        format_style_performance_arc_live_render_bundle_report,
        to_style_performance_arc_live_render_bundle_json,
    )

    _, a4_path = _arc_bank_files(tmp_path)
    bundle = build_style_performance_arc_live_render_bundle_report(
        ("jose_warehouse_five_hour",),
        analog_four_sysex_path=a4_path,
        scope="analog-four-only",
    )

    assert bundle.selected_set_plan.scope == "analog-four-only"
    assert "--analog-four <analog-four-syx-path> --scope analog-four-only" in (
        "\n".join(bundle.suggested_commands)
    )
    first_segment = bundle.segments[0]
    assert first_segment.rytm_preview_summary == "unchanged by scope"
    assert first_segment.preview_json["machines"]["rytm"] is None
    assert first_segment.preview_json["machines"]["analog_four"] is not None

    text = "\n".join(format_style_performance_arc_live_render_bundle_report(bundle))
    assert "Rytm preview: unchanged by scope" in text
    assert "Analog Four preview: slot" in text

    payload = to_style_performance_arc_live_render_bundle_json(bundle)
    assert payload["render_bundle"]["scope"] == "analog-four-only"
    assert payload["render_bundle"]["segments"][0]["preview"]["machines"]["rytm"] is None

    with pytest.raises(ValueError, match="event_limit"):
        format_style_performance_arc_live_render_bundle_report(
            bundle,
            event_limit=-1,
        )


def test_style_performance_arc_live_render_bundle_rejects_mismatched_segments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import rytm_randomizer.reports.style_performance_arcs as report_module

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    packet = report_module.build_style_performance_arc_live_session_packet_report(
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    mismatched_packet = replace(packet, segments=packet.segments[:-1])
    monkeypatch.setattr(
        report_module,
        "build_style_performance_arc_live_session_packet_report",
        lambda *_args, **_kwargs: mismatched_packet,
    )

    with pytest.raises(ValueError, match="matching live-session and set-plan"):
        report_module.build_style_performance_arc_live_render_bundle_report(
            rytm_sysex_path=rytm_path,
            analog_four_sysex_path=a4_path,
        )


def test_style_performance_arc_live_cue_sheet_builds_operator_cues(
    tmp_path: Path,
):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_live_cue_sheet_report,
        format_style_performance_arc_live_cue_sheet_report,
        to_style_performance_arc_live_cue_sheet_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    cue_sheet = build_style_performance_arc_live_cue_sheet_report(
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )

    assert cue_sheet.live_render_bundle.selected_set_plan is cue_sheet.selected_set_plan
    assert cue_sheet.segment_count == cue_sheet.selected_set_plan.segment_count
    assert cue_sheet.cue_count == cue_sheet.segment_count
    assert cue_sheet.total_event_row_count == (cue_sheet.selected_set_plan.total_event_row_count)
    assert cue_sheet.total_deferred_row_count == (
        cue_sheet.selected_set_plan.total_deferred_row_count
    )
    assert cue_sheet.preflight_cues
    assert cue_sheet.recovery_cues
    assert cue_sheet.cues

    first_cue = cue_sheet.cues[0]
    first_render_segment = cue_sheet.live_render_bundle.segments[0]
    assert first_cue.render_segment is first_render_segment
    assert first_cue.position == first_render_segment.position
    assert first_cue.time_window == first_render_segment.time_window
    assert first_cue.style_key == first_render_segment.style_key
    assert first_cue.risk_level in {"green", "amber", "red"}
    assert first_cue.operator_move
    assert first_cue.recovery_action
    assert first_cue.render_row_summary == (
        f"{first_render_segment.event_row_count} event row(s), "
        f"{first_render_segment.deferred_row_count} deferred row(s)"
    )

    text = "\n".join(
        format_style_performance_arc_live_cue_sheet_report(
            cue_sheet,
            include_events=True,
            event_limit=1,
        )
    )
    assert "RytmRandomizer passive style performance arc live cue sheet" in text
    assert "Cue sheet summary:" in text
    assert "Preflight cues:" in text
    assert "Performance cues:" in text
    assert "Hands-on move:" in text
    assert "Risk:" in text
    assert "Recovery:" in text
    assert "Mock render row preview:" in text
    assert "- operator cue sheet only" in text
    assert "- no MIDI sending" in text

    payload = to_style_performance_arc_live_cue_sheet_json(cue_sheet)
    assert payload["selected"]["arc"]["key"] == cue_sheet.selected_entry.arc.key
    assert payload["live_render_bundle"]["selected"]["arc"]["key"] == (
        cue_sheet.selected_entry.arc.key
    )
    assert payload["cue_sheet"]["scope"] == cue_sheet.selected_set_plan.scope
    assert payload["cue_sheet"]["totals"]["cues"] == cue_sheet.cue_count
    assert payload["cue_sheet"]["cues"][0]["style_key"] == first_cue.style_key
    assert payload["cue_sheet"]["cues"][0]["risk_level"] == first_cue.risk_level
    assert payload["safety"][0] == "passive/read-only"


def test_style_performance_arc_live_cue_sheet_covers_single_machine_scope(
    tmp_path: Path,
):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_live_cue_sheet_report,
        format_style_performance_arc_live_cue_sheet_report,
        to_style_performance_arc_live_cue_sheet_json,
    )

    _, a4_path = _arc_bank_files(tmp_path)
    cue_sheet = build_style_performance_arc_live_cue_sheet_report(
        ("jose_warehouse_five_hour",),
        analog_four_sysex_path=a4_path,
        scope="analog-four-only",
    )

    assert cue_sheet.selected_set_plan.scope == "analog-four-only"
    assert "--analog-four <analog-four-syx-path> --scope analog-four-only" in (
        "\n".join(cue_sheet.suggested_commands)
    )
    assert cue_sheet.cues[0].render_segment.rytm_preview_summary == "unchanged by scope"

    text = "\n".join(format_style_performance_arc_live_cue_sheet_report(cue_sheet))
    assert "Scope: analog-four-only" in text
    assert "Leave Rytm unchanged" in text

    payload = to_style_performance_arc_live_cue_sheet_json(cue_sheet)
    assert payload["cue_sheet"]["scope"] == "analog-four-only"
    assert payload["cue_sheet"]["cues"][0]["machine_focus"] == "Analog Four only"

    with pytest.raises(ValueError, match="event_limit"):
        format_style_performance_arc_live_cue_sheet_report(
            cue_sheet,
            event_limit=-1,
        )


def test_style_performance_arc_live_cue_sheet_covers_focus_and_risk_edges(
    tmp_path: Path,
):
    from rytm_randomizer.reports.style_performance_arcs import (
        _live_cue_from_segment,
        _live_cue_lines,
        build_style_performance_arc_live_cue_sheet_report,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    cue_sheet = build_style_performance_arc_live_cue_sheet_report(
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    segment = cue_sheet.live_render_bundle.segments[0]

    rytm_scope_cue = _live_cue_from_segment(segment, scope="rytm-only")
    assert rytm_scope_cue.machine_focus == "Rytm only"
    assert "leave Analog Four unchanged" in rytm_scope_cue.operator_move

    dual_a4_only_cue = _live_cue_from_segment(
        replace(
            segment,
            live_segment=replace(segment.live_segment, rytm_preview_summary="unchanged by scope"),
        ),
        scope="dual",
    )
    assert dual_a4_only_cue.machine_focus == "Analog Four only"

    dual_rytm_only_cue = _live_cue_from_segment(
        replace(
            segment,
            live_segment=replace(
                segment.live_segment,
                analog_four_preview_summary="unchanged by scope",
            ),
        ),
        scope="dual",
    )
    assert dual_rytm_only_cue.machine_focus == "Rytm only"

    green_cue = _live_cue_from_segment(
        replace(
            segment,
            live_segment=replace(
                segment.live_segment,
                readiness="ready",
                event_row_count=1,
                deferred_row_count=0,
            ),
            event_preview_rows=("  - mock event",),
        ),
        scope="dual",
    )
    assert green_cue.risk_level == "green"
    assert "If the room drifts" in green_cue.recovery_action
    assert "Showing all events" in "\n".join(
        _live_cue_lines(green_cue, include_events=True, event_limit=1)
    )

    red_cue = _live_cue_from_segment(
        replace(
            segment,
            live_segment=replace(
                segment.live_segment,
                readiness="blocked",
                event_row_count=0,
            ),
            event_preview_rows=(),
        ),
        scope="dual",
    )
    assert red_cue.risk_level == "red"
    assert "Skip this cue" in red_cue.recovery_action
    assert "No mock rows available" in "\n".join(
        _live_cue_lines(red_cue, include_events=True, event_limit=8)
    )


def test_style_performance_arc_reference_match_ranks_description_and_embeds_cue_sheet(
    tmp_path: Path,
):
    from rytm_randomizer.guardrails.schema import Confidence
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_reference_match_report,
        format_style_performance_arc_reference_match_report,
        to_style_performance_arc_reference_match_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_reference_match_report(
        description=(
            "Jeff Mills and Oscar Mulero dark hypnotic tunnel techno with "
            "futurist bells, Detroit pressure, and restrained warehouse motion"
        ),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        include_live_cue_sheet=True,
    )

    assert report.feature_report.confidence is Confidence.LOW
    assert report.source_kind == "description"
    assert report.source_reference is None
    assert report.selected_match.arc.key == "mills_mulero_tunnel"
    assert report.live_cue_sheet is not None
    assert report.live_cue_sheet.selected_entry.arc.key == "mills_mulero_tunnel"
    assert report.matches[0].score >= report.matches[1].score
    assert "jeff mills" in report.selected_match.matched_terms
    assert "oscar mulero" in report.selected_match.matched_terms

    lines = format_style_performance_arc_reference_match_report(
        report,
        include_events=True,
        event_limit=1,
    )
    text = "\n".join(lines)
    assert "RytmRandomizer passive style performance arc reference match" in text
    assert "Reference match summary:" in text
    assert "- Source kind: description" in text
    assert "- Selected arc: mills_mulero_tunnel / Mills Mulero Tunnel" in text
    assert "Ranked arc matches:" in text
    assert "Embedded live cue sheet:" in text
    assert "Cue sheet summary:" in text
    assert "Mock render row preview:" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_reference_match_json(report)
    assert payload["reference_match"]["source_kind"] == "description"
    assert payload["reference_match"]["source_reference"] is None
    assert payload["reference_match"]["selected"]["arc"]["key"] == "mills_mulero_tunnel"
    assert payload["reference_match"]["embedded_live_cue_sheet"] is True
    assert payload["live_cue_sheet"]["selected"]["arc"]["key"] == "mills_mulero_tunnel"
    assert payload["safety"][0] == "passive/read-only"


def test_style_performance_arc_reference_match_summarizes_snapshot_preview(
    tmp_path: Path,
):
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_reference_match_report,
        format_style_performance_arc_reference_match_report,
        to_style_performance_arc_reference_match_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_reference_match_report(
        description="Stigmata Birmingham Regis Surgeon Glenn Wilson warehouse pressure",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        include_live_cue_sheet=True,
    )

    assert report.snapshot_preview is not None
    assert report.snapshot_preview.selected_arc_key == report.selected_match.arc.key
    assert report.snapshot_preview.scope == report.live_cue_sheet.selected_set_plan.scope
    assert report.snapshot_preview.style_keys == report.selected_match.arc.style_keys
    assert report.snapshot_preview.total_event_row_count == (
        report.live_cue_sheet.total_event_row_count
    )
    assert report.snapshot_preview.total_deferred_row_count == (
        report.live_cue_sheet.total_deferred_row_count
    )
    assert report.snapshot_preview.planned_rytm_pads
    assert report.snapshot_preview.planned_analog_four_tracks
    assert "no MIDI" in report.snapshot_preview.operator_action

    text = "\n".join(format_style_performance_arc_reference_match_report(report))
    assert "Reference-selected snapshot preview:" in text
    assert f"- Scope: {report.snapshot_preview.scope}" in text
    planned_rytm_pads = ", ".join(str(pad) for pad in report.snapshot_preview.planned_rytm_pads)
    assert f"- Planned Rytm pads: {planned_rytm_pads}" in text
    assert "Analog Four kits:" in text
    assert "This is still a passive preview; no MIDI is sent." in text

    payload = to_style_performance_arc_reference_match_json(report)
    preview = payload["reference_match"]["snapshot_preview"]
    assert preview["selected_arc_key"] == report.selected_match.arc.key
    assert preview["planned_rytm_pads"] == list(report.snapshot_preview.planned_rytm_pads)
    assert preview["planned_analog_four_tracks"] == list(
        report.snapshot_preview.planned_analog_four_tracks
    )
    assert preview["total_mock_message_count"] == report.snapshot_preview.total_mock_message_count


def test_style_performance_arc_reference_match_has_no_snapshot_preview_without_saved_kits():
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_reference_match_report,
        format_style_performance_arc_reference_match_report,
        to_style_performance_arc_reference_match_json,
    )

    report = build_style_performance_arc_reference_match_report(
        description="Jeff Mills Oscar Mulero tunnel hypnosis",
    )

    assert report.snapshot_preview is None
    assert "Reference-selected snapshot preview: none" in "\n".join(
        format_style_performance_arc_reference_match_report(report)
    )
    assert (
        to_style_performance_arc_reference_match_json(report)["reference_match"]["snapshot_preview"]
        is None
    )


def test_style_performance_arc_reference_match_snapshot_preview_edges():
    from rytm_randomizer.reports.style_performance_arcs import (
        StylePerformanceArcReferenceSnapshotPreview,
        _reference_snapshot_preview_lines,
        _reference_snapshot_preview_operator_action,
    )

    blocked_preview = StylePerformanceArcReferenceSnapshotPreview(
        selected_arc_key="arc",
        scope="dual",
        style_keys=("industrial_dark",),
        readiness="blocked",
        segment_count=1,
        ready_segment_count=0,
        partial_segment_count=0,
        blocked_segment_count=1,
        total_event_row_count=0,
        total_mock_message_count=0,
        total_deferred_row_count=0,
        rytm_kit_names=(),
        analog_four_kit_names=(),
        planned_rytm_pads=(),
        planned_analog_four_tracks=(),
        operator_action="",
    )
    assert "Resolve blocked segments" in _reference_snapshot_preview_operator_action(
        blocked_preview
    )
    blocked_lines = _reference_snapshot_preview_lines(
        replace(
            blocked_preview,
            operator_action=_reference_snapshot_preview_operator_action(blocked_preview),
        )
    )
    assert "- Rytm kits: none" in blocked_lines
    assert "- Planned Analog Four tracks: none" in blocked_lines

    ready_preview = replace(
        blocked_preview,
        readiness="ready",
        blocked_segment_count=0,
        ready_segment_count=1,
        total_event_row_count=4,
        total_mock_message_count=4,
        planned_rytm_pads=(1, 9),
    )
    assert "rehearsal checklist" in _reference_snapshot_preview_operator_action(ready_preview)

    empty_preview = replace(
        blocked_preview,
        readiness="empty",
        blocked_segment_count=0,
    )
    assert "planning guidance" in _reference_snapshot_preview_operator_action(empty_preview)


def test_style_performance_arc_reference_match_snapshot_preview_helper_edges():
    from rytm_randomizer.reports.style_performance_arcs import (
        _reference_snapshot_preview_from_cue_sheet,
        _reference_snapshot_preview_readiness,
    )

    def cue_counts(
        *,
        blocked: int = 0,
        partial: int = 0,
        deferred: int = 0,
        events: int = 0,
    ):
        return SimpleNamespace(
            blocked_segment_count=blocked,
            partial_segment_count=partial,
            total_deferred_row_count=deferred,
            total_event_row_count=events,
        )

    assert _reference_snapshot_preview_readiness(cue_counts(blocked=1)) == "blocked"
    assert _reference_snapshot_preview_readiness(cue_counts(partial=1)) == "partial"
    assert _reference_snapshot_preview_readiness(cue_counts(events=1)) == "ready"
    assert _reference_snapshot_preview_readiness(cue_counts()) == "empty"

    rytm_preview = SimpleNamespace(kit_name="ONLY RYTM", planned_pads=(1, 9))
    a4_preview = SimpleNamespace(
        kit_name="ONLY A4",
        planned_tracks=(1,),
        deferred_rows=(SimpleNamespace(track=4),),
    )
    cue_sheet = SimpleNamespace(
        live_render_bundle=SimpleNamespace(
            segments=(
                SimpleNamespace(
                    set_plan_segment=SimpleNamespace(
                        preview_plan=SimpleNamespace(
                            rytm_preview=None,
                            analog_four_preview=a4_preview,
                        )
                    )
                ),
                SimpleNamespace(
                    set_plan_segment=SimpleNamespace(
                        preview_plan=SimpleNamespace(
                            rytm_preview=rytm_preview,
                            analog_four_preview=None,
                        )
                    )
                ),
            )
        ),
        selected_entry=SimpleNamespace(
            arc=SimpleNamespace(key="edge_arc", style_keys=("industrial_dark",))
        ),
        selected_set_plan=SimpleNamespace(scope="dual"),
        segment_count=2,
        ready_segment_count=1,
        partial_segment_count=1,
        blocked_segment_count=0,
        total_event_row_count=2,
        total_mock_message_count=2,
        total_deferred_row_count=1,
    )

    preview = _reference_snapshot_preview_from_cue_sheet(cue_sheet)

    assert preview.readiness == "partial"
    assert preview.rytm_kit_names == ("ONLY RYTM",)
    assert preview.analog_four_kit_names == ("ONLY A4",)
    assert preview.planned_rytm_pads == (1, 9)
    assert preview.planned_analog_four_tracks == (1, 4)
    assert "Review deferred Analog Four rows" in preview.operator_action


def test_style_performance_arc_reference_match_scores_feature_report_without_text():
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.reports.style_performance_arcs import (
        build_style_performance_arc_reference_match_report,
        to_style_performance_arc_reference_match_json,
    )
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    feature_report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=138.0,
        tempo_stability=0.92,
        kick_density=0.85,
        percussion_density=0.82,
        low_end_weight=0.88,
        spectral_brightness=0.18,
        texture_noise=0.9,
        energy_arc=(0.35, 0.45, 0.55, 0.7, 0.85, 0.95, 0.92, 0.88),
        content_hash="",
        derived_at="2026-05-21T12:00:00Z",
    )
    feature_report = replace(
        feature_report,
        content_hash=compute_feature_report_hash(feature_report),
    )

    report = build_style_performance_arc_reference_match_report(
        feature_report=feature_report,
    )

    assert report.source_kind == "feature-report"
    assert report.source_reference is None
    assert report.selected_match.arc.key == "stigmata_birmingham_assault"
    assert report.live_cue_sheet is None
    assert report.matches[0].vector_score >= 70
    assert report.matches[0].vector_score >= report.matches[1].vector_score

    payload = to_style_performance_arc_reference_match_json(report)
    assert payload["reference_match"]["feature_report"]["confidence"] == "HIGH"
    assert payload["reference_match"]["selected"]["arc"]["key"] == ("stigmata_birmingham_assault")
    assert payload["live_cue_sheet"] is None


def test_style_performance_arc_reference_match_covers_edge_sources(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    import rytm_randomizer.style_analysis as style_analysis
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.reports.style_performance_arcs import (
        _axis_scores_from_feature_report,
        _bounded_int,
        _handle_style_performance_arc_reference_match_report,
        _parse_arc_reference_match_cli_args,
        build_style_performance_arc_reference_match_report,
        format_style_performance_arc_reference_match_report,
    )
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    feature_report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=110.0,
        tempo_stability=0.42,
        kick_density=0.0,
        percussion_density=0.0,
        low_end_weight=0.0,
        spectral_brightness=0.0,
        texture_noise=0.0,
        energy_arc=(),
        content_hash="",
        derived_at="2026-05-21T12:00:00Z",
    )
    feature_report = replace(
        feature_report,
        content_hash=compute_feature_report_hash(feature_report),
    )
    empty_feature_report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.LOW,
        bpm=0.0,
        tempo_stability=0.0,
        kick_density=0.0,
        percussion_density=0.0,
        low_end_weight=0.0,
        spectral_brightness=0.0,
        texture_noise=0.0,
        energy_arc=(0.0, 0.0, 0.0, 0.0),
        content_hash="",
        derived_at="2026-05-21T12:00:00Z",
    )
    empty_feature_report = replace(
        empty_feature_report,
        content_hash=compute_feature_report_hash(empty_feature_report),
    )

    assert _bounded_int(-1) == 0
    assert _bounded_int(101) == 100

    for empty_kwargs in (
        {"description": ""},
        {"description": "   "},
        {"description": "florb zibble quarn"},
        {"feature_report": empty_feature_report},
    ):
        with pytest.raises(ValueError, match="reference evidence"):
            build_style_performance_arc_reference_match_report(**empty_kwargs)

    stable_arc_scores = _axis_scores_from_feature_report(
        replace(
            feature_report,
            bpm=0.0,
            tempo_stability=0.0,
            energy_arc=(0.4, 0.4, 0.4),
        )
    )
    assert stable_arc_scores["minimal_restraint"] == 72
    assert "motion_amount" not in stable_arc_scores
    peakless_arc_scores = _axis_scores_from_feature_report(
        replace(
            feature_report,
            bpm=0.0,
            tempo_stability=0.0,
            energy_arc=(-0.2, 0.0),
        )
    )
    assert peakless_arc_scores["motion_amount"] == 20

    report = build_style_performance_arc_reference_match_report(
        feature_report=feature_report,
    )
    assert report.match_count == len(report.matches)
    assert "Embedded live cue sheet: none" in "\n".join(
        format_style_performance_arc_reference_match_report(report)
    )
    with pytest.raises(ValueError, match="event_limit"):
        format_style_performance_arc_reference_match_report(report, event_limit=-1)

    hardgroove_report = build_style_performance_arc_reference_match_report(
        description="hardgroove percussive rolling machine funk"
    )
    assert hardgroove_report.selected_match.arc.key == "hardgroove_detroit_machine_funk"

    with pytest.raises(ValueError, match="exactly one reference source"):
        build_style_performance_arc_reference_match_report(
            description="Jeff Mills",
            feature_report=feature_report,
        )

    def fake_audio_report(path: Path) -> FeatureReport:
        assert path == Path("track.wav")
        return feature_report

    def fake_library_report(path: Path) -> FeatureReport:
        assert path == Path("library")
        return feature_report

    monkeypatch.setattr(style_analysis, "extract_from_audio", fake_audio_report)
    monkeypatch.setattr(style_analysis, "analyze_library", fake_library_report)

    audio_report = build_style_performance_arc_reference_match_report(audio_path=Path("track.wav"))
    assert audio_report.source_kind == "audio"
    assert audio_report.source_reference == "track.wav"
    assert "- Source reference: track.wav" in "\n".join(
        format_style_performance_arc_reference_match_report(audio_report)
    )
    library_report = build_style_performance_arc_reference_match_report(
        library_path=Path("library")
    )
    assert library_report.source_kind == "library"
    assert library_report.source_reference == "library"
    assert _parse_arc_reference_match_cli_args(["--library", "library"])["library_path"] == Path(
        "library"
    )

    def broken_audio_report(path: Path) -> FeatureReport:
        raise RuntimeError(f"audio unavailable: {path}")

    monkeypatch.setattr(style_analysis, "extract_from_audio", broken_audio_report)
    rc = _handle_style_performance_arc_reference_match_report(
        description=None,
        audio_path=Path("missing.wav"),
        library_path=None,
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope=None,
        selection_rank=None,
        total_minutes=None,
        segment_minutes=None,
        discovery_start=None,
        discovery_end=None,
        include_events=False,
        event_limit=1,
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "audio unavailable: missing.wav" in captured.err

    rc = _handle_style_performance_arc_reference_match_report(
        description="florb zibble quarn",
        audio_path=None,
        library_path=None,
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope=None,
        selection_rank=None,
        total_minutes=None,
        segment_minutes=None,
        discovery_start=None,
        discovery_end=None,
        include_events=False,
        event_limit=1,
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "reference evidence" in captured.err


def test_style_performance_arc_reference_match_parser_and_handlers(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.style_performance_arcs import (
        _handle_style_performance_arc_reference_match_report,
        _parse_arc_reference_match_cli_args,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)

    assert _parse_arc_reference_match_cli_args(
        [
            "--description",
            "Jeff Mills Oscar Mulero tunnel",
            "--rytm",
            "rytm.syx",
            "--analog-four",
            "a4.syx",
            "--scope",
            "dual",
            "--rank",
            "2",
            "--total-minutes",
            "120",
            "--segment-minutes",
            "30",
            "--discovery-start",
            "25",
            "--discovery-end",
            "80",
            "--events",
            "--limit",
            "2",
            "--json",
        ]
    ) == {
        "description": "Jeff Mills Oscar Mulero tunnel",
        "audio_path": None,
        "library_path": None,
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "dual",
        "selection_rank": 2,
        "total_minutes": 120,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 80,
        "include_events": True,
        "event_limit": 2,
        "json_output": True,
    }

    rc = _handle_style_performance_arc_reference_match_report(
        description="Stigmata Birmingham Regis Surgeon Glenn Wilson pressure",
        audio_path=None,
        library_path=None,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope=None,
        selection_rank=None,
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
    assert "RytmRandomizer passive style performance arc reference match" in captured.out
    assert "stigmata_birmingham_assault" in captured.out
    assert "Embedded live cue sheet:" in captured.out
    assert captured.err == ""

    rc = _handle_style_performance_arc_reference_match_report(
        description="Jeff Mills Oscar Mulero",
        audio_path=None,
        library_path=None,
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope=None,
        selection_rank=None,
        total_minutes=None,
        segment_minutes=None,
        discovery_start=None,
        discovery_end=None,
        include_events=False,
        event_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["reference_match"]["selected"]["arc"]["key"] == "mills_mulero_tunnel"
    assert payload["reference_match"]["embedded_live_cue_sheet"] is False
    assert captured.err == ""

    for argv, message in (
        ([], "exactly one reference source"),
        (["--description", "x", "--audio", "track.wav"], "exactly one reference source"),
        (["--description"], "usage"),
        (["--description", "   "], "description must include reference evidence"),
        (["--description", "x", "--limit", "-1"], ">= 0"),
        (["--description", "x", "--rank", "0"], ">= 1"),
        (["--description", "x", "--bogus"], "usage"),
    ):
        with pytest.raises(ValueError, match=message):
            _parse_arc_reference_match_cli_args(argv)


def test_style_performance_arc_audition_packet_rejects_empty_readiness(
    monkeypatch: pytest.MonkeyPatch,
):
    import rytm_randomizer.reports.style_performance_arcs as report_module

    empty_readiness = report_module.StylePerformanceArcReadinessReport(
        scope="dual",
        arc_count=0,
        ready_arc_count=0,
        partial_arc_count=0,
        blocked_arc_count=0,
        total_segment_count=0,
        total_event_row_count=0,
        total_mock_message_count=0,
        total_deferred_row_count=0,
        entries=(),
    )

    def fake_readiness_report(*_args: object, **_kwargs: object):
        return empty_readiness

    monkeypatch.setattr(
        report_module,
        "build_style_performance_arc_readiness_report",
        fake_readiness_report,
    )

    with pytest.raises(ValueError, match="requires at least one readiness entry"):
        report_module.build_style_performance_arc_audition_packet_report()


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


def test_style_performance_arc_readiness_parser_and_handlers(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.style_performance_arcs import (
        _handle_style_performance_arc_audition_packet_report,
        _handle_style_performance_arc_live_cue_sheet_report,
        _handle_style_performance_arc_live_render_bundle_report,
        _handle_style_performance_arc_live_session_packet_report,
        _handle_style_performance_arc_readiness_report,
        _handle_style_performance_arc_reference_match_report,
        _handle_style_performance_arc_rehearsal_manifest_report,
        _parse_arc_audition_packet_cli_args,
        _parse_arc_live_cue_sheet_cli_args,
        _parse_arc_live_render_bundle_cli_args,
        _parse_arc_live_session_packet_cli_args,
        _parse_arc_readiness_cli_args,
        _parse_arc_reference_match_cli_args,
        _parse_arc_rehearsal_manifest_cli_args,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)

    assert _parse_arc_audition_packet_cli_args(
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
            "1",
            "--json",
        ]
    ) == {
        "arc_keys": ("jose_warehouse_five_hour",),
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "dual",
        "selection_rank": 2,
        "total_minutes": 240,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 90,
        "include_events": True,
        "event_limit": 1,
        "json_output": True,
    }

    assert _parse_arc_rehearsal_manifest_cli_args(
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
            "1",
            "--json",
        ]
    ) == {
        "arc_keys": ("jose_warehouse_five_hour",),
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "dual",
        "selection_rank": 2,
        "total_minutes": 240,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 90,
        "include_events": True,
        "event_limit": 1,
        "json_output": True,
    }

    assert _parse_arc_live_session_packet_cli_args(
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
            "1",
            "--json",
        ]
    ) == {
        "arc_keys": ("jose_warehouse_five_hour",),
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "dual",
        "selection_rank": 2,
        "total_minutes": 240,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 90,
        "include_events": True,
        "event_limit": 1,
        "json_output": True,
    }

    assert _parse_arc_live_render_bundle_cli_args(
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
            "1",
            "--json",
        ]
    ) == {
        "arc_keys": ("jose_warehouse_five_hour",),
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "dual",
        "selection_rank": 2,
        "total_minutes": 240,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 90,
        "include_events": True,
        "event_limit": 1,
        "json_output": True,
    }

    assert _parse_arc_live_cue_sheet_cli_args(
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
            "1",
            "--json",
        ]
    ) == {
        "arc_keys": ("jose_warehouse_five_hour",),
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "dual",
        "selection_rank": 2,
        "total_minutes": 240,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 90,
        "include_events": True,
        "event_limit": 1,
        "json_output": True,
    }

    assert _parse_arc_reference_match_cli_args(
        [
            "--description",
            "Jeff Mills Oscar Mulero tunnel",
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
            "1",
            "--json",
        ]
    ) == {
        "description": "Jeff Mills Oscar Mulero tunnel",
        "audio_path": None,
        "library_path": None,
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "dual",
        "selection_rank": 2,
        "total_minutes": 240,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 90,
        "include_events": True,
        "event_limit": 1,
        "json_output": True,
    }

    assert _parse_arc_readiness_cli_args(
        [
            "jose_warehouse_five_hour",
            "mills_mulero_tunnel",
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
            "--limit",
            "0",
            "--json",
        ]
    ) == {
        "arc_keys": ("jose_warehouse_five_hour", "mills_mulero_tunnel"),
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "dual",
        "selection_rank": 2,
        "total_minutes": 240,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 90,
        "entry_limit": 0,
        "json_output": True,
    }

    rc = _handle_style_performance_arc_readiness_report(
        arc_keys=None,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope=None,
        selection_rank=None,
        total_minutes=None,
        segment_minutes=None,
        discovery_start=None,
        discovery_end=None,
        entry_limit=1,
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive style performance arc readiness matrix" in captured.out
    assert "Arc readiness matrix:" in captured.out
    assert "Average selection score:" in captured.out
    assert captured.err == ""

    rc = _handle_style_performance_arc_readiness_report(
        arc_keys=("jose_warehouse_five_hour",),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=None,
        scope="rytm-only",
        selection_rank=None,
        total_minutes=None,
        segment_minutes=20,
        discovery_start=None,
        discovery_end=None,
        entry_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["scope"] == "rytm-only"
    assert payload["totals"]["arcs"] == 1
    assert payload["entries"][0]["arc"]["key"] == "jose_warehouse_five_hour"
    assert captured.err == ""

    rc = _handle_style_performance_arc_readiness_report(
        arc_keys=None,
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope=None,
        selection_rank=None,
        total_minutes=None,
        segment_minutes=None,
        discovery_start=None,
        discovery_end=None,
        entry_limit=24,
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "requires --rytm" in captured.err

    rc = _handle_style_performance_arc_audition_packet_report(
        arc_keys=None,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope=None,
        selection_rank=None,
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
    assert "RytmRandomizer passive style performance arc audition packet" in captured.out
    assert "Selected set plan:" in captured.out
    assert "Event preview for segment" in captured.out
    assert captured.err == ""

    rc = _handle_style_performance_arc_audition_packet_report(
        arc_keys=("jose_warehouse_five_hour",),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=None,
        scope="rytm-only",
        selection_rank=None,
        total_minutes=None,
        segment_minutes=20,
        discovery_start=None,
        discovery_end=None,
        include_events=False,
        event_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["selected"]["arc"]["key"] == "jose_warehouse_five_hour"
    assert payload["selected_set_plan"]["performance_plan"]["scope"] == "rytm-only"
    assert captured.err == ""

    rc = _handle_style_performance_arc_rehearsal_manifest_report(
        arc_keys=None,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope=None,
        selection_rank=None,
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
    assert "RytmRandomizer passive style performance arc rehearsal manifest" in captured.out
    assert "Preflight checklist:" in captured.out
    assert "Segment runbook:" in captured.out
    assert "Event preview for segment" in captured.out
    assert captured.err == ""

    rc = _handle_style_performance_arc_rehearsal_manifest_report(
        arc_keys=("jose_warehouse_five_hour",),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=None,
        scope="rytm-only",
        selection_rank=None,
        total_minutes=None,
        segment_minutes=20,
        discovery_start=None,
        discovery_end=None,
        include_events=False,
        event_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["selected"]["arc"]["key"] == "jose_warehouse_five_hour"
    assert payload["manifest"]["scope"] == "rytm-only"
    assert captured.err == ""

    rc = _handle_style_performance_arc_audition_packet_report(
        arc_keys=None,
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope=None,
        selection_rank=None,
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

    rc = _handle_style_performance_arc_live_session_packet_report(
        arc_keys=None,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope=None,
        selection_rank=None,
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
    assert "RytmRandomizer passive style performance arc live session packet" in captured.out
    assert "Launch checklist:" in captured.out
    assert "Segment cards:" in captured.out
    assert "Event preview for segment" in captured.out
    assert captured.err == ""

    rc = _handle_style_performance_arc_live_session_packet_report(
        arc_keys=("jose_warehouse_five_hour",),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=None,
        scope="rytm-only",
        selection_rank=None,
        total_minutes=None,
        segment_minutes=20,
        discovery_start=None,
        discovery_end=None,
        include_events=False,
        event_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["selected"]["arc"]["key"] == "jose_warehouse_five_hour"
    assert payload["session_packet"]["scope"] == "rytm-only"
    assert captured.err == ""

    rc = _handle_style_performance_arc_rehearsal_manifest_report(
        arc_keys=None,
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope=None,
        selection_rank=None,
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

    rc = _handle_style_performance_arc_live_session_packet_report(
        arc_keys=None,
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope=None,
        selection_rank=None,
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

    rc = _handle_style_performance_arc_live_render_bundle_report(
        arc_keys=None,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope=None,
        selection_rank=None,
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
    assert "RytmRandomizer passive style performance arc live render bundle" in captured.out
    assert "Render bundle summary:" in captured.out
    assert "Segment render bundles:" in captured.out
    assert "Mock render preview:" in captured.out
    assert captured.err == ""

    rc = _handle_style_performance_arc_live_render_bundle_report(
        arc_keys=("jose_warehouse_five_hour",),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=None,
        scope="rytm-only",
        selection_rank=None,
        total_minutes=None,
        segment_minutes=20,
        discovery_start=None,
        discovery_end=None,
        include_events=False,
        event_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["selected"]["arc"]["key"] == "jose_warehouse_five_hour"
    assert payload["render_bundle"]["scope"] == "rytm-only"
    assert captured.err == ""

    rc = _handle_style_performance_arc_live_cue_sheet_report(
        arc_keys=None,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope=None,
        selection_rank=None,
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
    assert "RytmRandomizer passive style performance arc live cue sheet" in captured.out
    assert "Cue sheet summary:" in captured.out
    assert "Performance cues:" in captured.out
    assert "Mock render row preview:" in captured.out
    assert captured.err == ""

    rc = _handle_style_performance_arc_live_cue_sheet_report(
        arc_keys=("jose_warehouse_five_hour",),
        rytm_sysex_path=None,
        analog_four_sysex_path=a4_path,
        scope="analog-four-only",
        selection_rank=None,
        total_minutes=None,
        segment_minutes=20,
        discovery_start=None,
        discovery_end=None,
        include_events=False,
        event_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["selected"]["arc"]["key"] == "jose_warehouse_five_hour"
    assert payload["cue_sheet"]["scope"] == "analog-four-only"
    assert captured.err == ""

    rc = _handle_style_performance_arc_live_cue_sheet_report(
        arc_keys=None,
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope=None,
        selection_rank=None,
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

    rc = _handle_style_performance_arc_reference_match_report(
        description="Jeff Mills Oscar Mulero tunnel",
        audio_path=None,
        library_path=None,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope=None,
        selection_rank=None,
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
    assert "RytmRandomizer passive style performance arc reference match" in captured.out
    assert "Embedded live cue sheet:" in captured.out
    assert captured.err == ""

    rc = _handle_style_performance_arc_reference_match_report(
        description="Jeff Mills Oscar Mulero tunnel",
        audio_path=None,
        library_path=None,
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope=None,
        selection_rank=None,
        total_minutes=None,
        segment_minutes=None,
        discovery_start=None,
        discovery_end=None,
        include_events=False,
        event_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["reference_match"]["selected"]["arc"]["key"] == "mills_mulero_tunnel"
    assert payload["live_cue_sheet"] is None
    assert captured.err == ""

    rc = _handle_style_performance_arc_live_render_bundle_report(
        arc_keys=None,
        rytm_sysex_path=None,
        analog_four_sysex_path=None,
        scope=None,
        selection_rank=None,
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
        _parse_arc_audition_packet_cli_args,
        _parse_arc_key,
        _parse_arc_live_cue_sheet_cli_args,
        _parse_arc_live_render_bundle_cli_args,
        _parse_arc_live_session_packet_cli_args,
        _parse_arc_readiness_cli_args,
        _parse_arc_reference_match_cli_args,
        _parse_arc_rehearsal_manifest_cli_args,
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

    readiness_bad_cases = [
        (["--json"], "usage"),
        (["jose_warehouse_five_hour", "--rytm"], "usage"),
        (["jose_warehouse_five_hour", "--bogus"], "usage"),
        (["jose_warehouse_five_hour", "--limit", "-1"], ">= 0"),
        (["jose_warehouse_five_hour", "--rank", "0"], ">= 1"),
    ]
    for argv, message in readiness_bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_arc_readiness_cli_args(argv)

    audition_bad_cases = [
        (["--json"], "usage"),
        (["jose_warehouse_five_hour", "--rytm"], "usage"),
        (["jose_warehouse_five_hour", "--bogus"], "usage"),
        (["jose_warehouse_five_hour", "--limit", "-1"], ">= 0"),
        (["jose_warehouse_five_hour", "--rank", "0"], ">= 1"),
    ]
    for argv, message in audition_bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_arc_audition_packet_cli_args(argv)

    rehearsal_bad_cases = [
        (["--json"], "usage"),
        (["jose_warehouse_five_hour", "--rytm"], "usage"),
        (["jose_warehouse_five_hour", "--bogus"], "usage"),
        (["jose_warehouse_five_hour", "--limit", "-1"], ">= 0"),
        (["jose_warehouse_five_hour", "--rank", "0"], ">= 1"),
    ]
    for argv, message in rehearsal_bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_arc_rehearsal_manifest_cli_args(argv)

    live_session_bad_cases = [
        (["--json"], "usage"),
        (["jose_warehouse_five_hour", "--rytm"], "live-session-packet-report usage"),
        (["jose_warehouse_five_hour", "--bogus"], "usage"),
        (["jose_warehouse_five_hour", "--limit", "-1"], ">= 0"),
        (["jose_warehouse_five_hour", "--rank", "0"], ">= 1"),
    ]
    for argv, message in live_session_bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_arc_live_session_packet_cli_args(argv)

    live_render_bad_cases = [
        (["--json"], "usage"),
        (["jose_warehouse_five_hour", "--rytm"], "live-render-bundle-report usage"),
        (["jose_warehouse_five_hour", "--bogus"], "usage"),
        (["jose_warehouse_five_hour", "--limit", "-1"], ">= 0"),
        (["jose_warehouse_five_hour", "--rank", "0"], ">= 1"),
    ]
    for argv, message in live_render_bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_arc_live_render_bundle_cli_args(argv)

    live_cue_bad_cases = [
        (["--json"], "usage"),
        (["jose_warehouse_five_hour", "--rytm"], "live-cue-sheet-report usage"),
        (["jose_warehouse_five_hour", "--bogus"], "usage"),
        (["jose_warehouse_five_hour", "--limit", "-1"], ">= 0"),
        (["jose_warehouse_five_hour", "--rank", "0"], ">= 1"),
    ]
    for argv, message in live_cue_bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_arc_live_cue_sheet_cli_args(argv)

    reference_match_bad_cases = [
        ([], "exactly one reference source"),
        (["--description", "x", "--audio", "track.wav"], "exactly one reference source"),
        (["--description"], "reference-match-report usage"),
        (["--description", "   "], "description must include reference evidence"),
        (["--description", "x", "--bogus"], "usage"),
        (["--description", "x", "--limit", "-1"], ">= 0"),
        (["--description", "x", "--rank", "0"], ">= 1"),
    ]
    for argv, message in reference_match_bad_cases:
        with pytest.raises(ValueError, match=message):
            _parse_arc_reference_match_cli_args(argv)


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

    assert (
        main(
            [
                "style-performance-arc-readiness-report",
                "--rytm",
                str(rytm_path),
                "--analog-four",
                str(a4_path),
                "--limit",
                "1",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc readiness matrix" in captured.out
    assert "Arc readiness matrix:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-audition-packet-report",
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
    assert "RytmRandomizer passive style performance arc audition packet" in captured.out
    assert "Selected set plan:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-rehearsal-manifest-report",
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
    assert "RytmRandomizer passive style performance arc rehearsal manifest" in captured.out
    assert "Segment runbook:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-live-session-packet-report",
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
    assert "RytmRandomizer passive style performance arc live session packet" in captured.out
    assert "Segment cards:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-live-render-bundle-report",
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
    assert "RytmRandomizer passive style performance arc live render bundle" in captured.out
    assert "Segment render bundles:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-live-cue-sheet-report",
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
    assert "RytmRandomizer passive style performance arc live cue sheet" in captured.out
    assert "Performance cues:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-reference-match-report",
                "--description",
                "Jeff Mills Oscar Mulero tunnel",
                "--events",
                "--limit",
                "1",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc reference match" in captured.out
    assert "mills_mulero_tunnel" in captured.out

    help_text = resolve_help_text("--help")
    assert "style-performance-arc-report" in help_text
    assert "list-style-performance-arcs" in help_text
    assert "style-performance-arc-set-plan-report <arc-key>" in help_text
    assert "style-performance-arc-readiness-report" in help_text
    assert "style-performance-arc-audition-packet-report" in help_text
    assert "style-performance-arc-rehearsal-manifest-report" in help_text
    assert "style-performance-arc-live-session-packet-report" in help_text
    assert "style-performance-arc-live-render-bundle-report" in help_text
    assert "style-performance-arc-live-cue-sheet-report" in help_text
    assert "style-performance-arc-reference-match-report" in help_text
    report_help = resolve_help_text("style-performance-arc-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-report" in report_help
    assert "Prints passive reference/performance arc presets" in report_help
    arc_help = resolve_help_text("style-performance-arc-set-plan-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-set-plan-report" in arc_help
    assert "Expands a named passive reference arc into a timed performance set plan." in arc_help
    readiness_help = resolve_help_text("style-performance-arc-readiness-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-readiness-report" in (readiness_help)
    assert "Ranks named passive reference arcs against saved kit banks." in readiness_help
    audition_help = resolve_help_text("style-performance-arc-audition-packet-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-audition-packet-report" in (
        audition_help
    )
    assert "Builds a passive best-arc audition packet from saved kit banks." in (audition_help)
    rehearsal_help = resolve_help_text("style-performance-arc-rehearsal-manifest-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-rehearsal-manifest-report" in (
        rehearsal_help
    )
    assert "Builds a passive rehearsal manifest from saved kit banks." in (rehearsal_help)
    live_session_help = resolve_help_text("style-performance-arc-live-session-packet-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-live-session-packet-report" in (
        live_session_help
    )
    assert "Builds a passive live rehearsal session packet from saved kit banks." in (
        live_session_help
    )
    live_render_help = resolve_help_text("style-performance-arc-live-render-bundle-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-live-render-bundle-report" in (
        live_render_help
    )
    assert "Builds a passive live render bundle from saved kit banks." in (live_render_help)
    live_cue_help = resolve_help_text("style-performance-arc-live-cue-sheet-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-live-cue-sheet-report" in (
        live_cue_help
    )
    assert "Builds a passive live performance cue sheet from saved kit banks." in (live_cue_help)
    reference_match_help = resolve_help_text("style-performance-arc-reference-match-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-reference-match-report" in (
        reference_match_help
    )
    assert "Matches a reference description or FeatureReport to performance arcs." in (
        reference_match_help
    )
