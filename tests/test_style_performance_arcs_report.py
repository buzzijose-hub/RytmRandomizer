"""Tests for passive reference performance arc presets."""

from __future__ import annotations

import json
import shlex
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import dual_machine_reference_bank_files as _arc_bank_files

pytestmark = pytest.mark.fast


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
    assert cue_sheet.stage_packet.selected_arc_key == cue_sheet.selected_entry.arc.key
    assert cue_sheet.stage_packet.scope == cue_sheet.selected_set_plan.scope
    assert cue_sheet.stage_packet.cue_count == cue_sheet.cue_count
    assert cue_sheet.stage_packet.stage_cards

    first_cue = cue_sheet.cues[0]
    first_render_segment = cue_sheet.live_render_bundle.segments[0]
    first_stage_card = cue_sheet.stage_packet.stage_cards[0]
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
    assert first_stage_card.cue_number == first_cue.position
    assert first_stage_card.time_window == first_cue.time_window
    assert first_stage_card.style_key == first_cue.style_key
    assert first_stage_card.machine_focus == first_cue.machine_focus
    assert first_stage_card.risk_level == first_cue.risk_level
    assert first_stage_card.planned_rytm_pads
    assert first_stage_card.planned_analog_four_tracks
    assert first_stage_card.render_row_summary == first_cue.render_row_summary

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
    assert "Stage packet:" in text
    assert "Stage cards:" in text
    assert "Hands-on move:" in text
    assert "Risk:" in text
    assert "Recovery:" in text
    assert "Mock render row preview:" in text
    assert "Planned Rytm pads:" in text
    assert "Planned Analog Four tracks:" in text
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
    stage_packet = payload["cue_sheet"]["stage_packet"]
    assert stage_packet["selected_arc_key"] == cue_sheet.selected_entry.arc.key
    assert stage_packet["stage_cards"][0]["cue_number"] == first_cue.position
    assert stage_packet["stage_cards"][0]["planned_rytm_pads"] == list(
        first_stage_card.planned_rytm_pads
    )
    assert stage_packet["stage_cards"][0]["planned_analog_four_tracks"] == list(
        first_stage_card.planned_analog_four_tracks
    )
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
    assert cue_sheet.stage_packet.planned_rytm_pads == ()
    assert cue_sheet.stage_packet.planned_analog_four_tracks
    assert cue_sheet.stage_packet.stage_cards[0].planned_rytm_pads == ()
    assert cue_sheet.stage_packet.stage_cards[0].planned_analog_four_tracks

    text = "\n".join(format_style_performance_arc_live_cue_sheet_report(cue_sheet))
    assert "Scope: analog-four-only" in text
    assert "Leave Rytm unchanged" in text

    payload = to_style_performance_arc_live_cue_sheet_json(cue_sheet)
    assert payload["cue_sheet"]["scope"] == "analog-four-only"
    assert payload["cue_sheet"]["cues"][0]["machine_focus"] == "Analog Four only"
    assert payload["cue_sheet"]["stage_packet"]["planned_rytm_pads"] == []

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
    assert report.stage_packet is report.live_cue_sheet.stage_packet
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
    assert "Reference-selected stage packet:" in text
    assert "Embedded live cue sheet:" in text
    assert "Cue sheet summary:" in text
    assert "Stage cards:" in text
    assert "Mock render row preview:" in text
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines

    payload = to_style_performance_arc_reference_match_json(report)
    assert payload["reference_match"]["source_kind"] == "description"
    assert payload["reference_match"]["source_reference"] is None
    assert payload["reference_match"]["selected"]["arc"]["key"] == "mills_mulero_tunnel"
    assert payload["reference_match"]["embedded_live_cue_sheet"] is True
    assert payload["reference_match"]["stage_packet"]["selected_arc_key"] == ("mills_mulero_tunnel")
    assert payload["live_cue_sheet"]["selected"]["arc"]["key"] == "mills_mulero_tunnel"
    assert payload["safety"][0] == "passive/read-only"


def test_style_performance_arc_live_runbook_builds_direct_arc_packet(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_performance_runbook import (
        build_style_performance_arc_live_runbook_report,
        format_style_performance_arc_live_runbook_report,
        to_style_performance_arc_live_runbook_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    runbook = build_style_performance_arc_live_runbook_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )

    assert runbook.selection_source == "arc"
    assert runbook.source_reference == "jose_warehouse_five_hour"
    assert runbook.reference_match is None
    assert runbook.selected_arc_key == "jose_warehouse_five_hour"
    assert runbook.stage_packet is runbook.live_cue_sheet.stage_packet
    assert runbook.show_mode == "dual-machine"
    assert runbook.launch_brief
    assert runbook.timeline_cards
    assert runbook.suggested_commands == runbook.live_cue_sheet.suggested_commands

    text = "\n".join(
        format_style_performance_arc_live_runbook_report(
            runbook,
            include_events=True,
            event_limit=1,
        )
    )
    assert "RytmRandomizer passive style performance arc live runbook" in text
    assert "Runbook summary:" in text
    assert "Launch brief:" in text
    assert "Replayable passive commands:" in text
    assert "Stage packet:" in text
    assert "Timeline cards:" in text
    assert "Cue event preview:" in text
    assert "Recovery cues:" in text
    assert "- no MIDI sending" in text
    assert "- no port opening" in text

    payload = to_style_performance_arc_live_runbook_json(runbook)
    assert payload["live_runbook"]["selection_source"] == "arc"
    assert payload["live_runbook"]["selected_arc_key"] == "jose_warehouse_five_hour"
    assert payload["live_runbook"]["show_mode"] == "dual-machine"
    assert payload["live_runbook"]["stage_packet"]["selected_arc_key"] == (
        "jose_warehouse_five_hour"
    )
    assert payload["live_runbook"]["timeline_cards"][0]["cue_number"] == 1
    assert payload["cue_sheet"]["selected"]["arc"]["key"] == "jose_warehouse_five_hour"
    assert payload["reference_match"] is None
    assert payload["safety"][0] == "passive/read-only"


def test_style_performance_arc_live_runbook_builds_reference_matched_packet(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_performance_runbook import (
        build_style_performance_arc_live_runbook_report,
        format_style_performance_arc_live_runbook_report,
        to_style_performance_arc_live_runbook_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    runbook = build_style_performance_arc_live_runbook_report(
        description="Jeff Mills Oscar Mulero tunnel bells",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )

    assert runbook.selection_source == "description"
    assert runbook.reference_match is not None
    assert runbook.selected_arc_key == "mills_mulero_tunnel"
    assert runbook.reference_match.stage_packet is runbook.stage_packet

    text = "\n".join(format_style_performance_arc_live_runbook_report(runbook))
    assert "Reference match:" in text
    assert "mills_mulero_tunnel" in text
    assert "Matched terms:" in text

    payload = to_style_performance_arc_live_runbook_json(runbook)
    assert payload["live_runbook"]["selection_source"] == "description"
    assert payload["live_runbook"]["selected_arc_key"] == "mills_mulero_tunnel"
    assert payload["reference_match"]["reference_match"]["selected"]["arc"]["key"] == (
        "mills_mulero_tunnel"
    )


def test_style_performance_arc_live_runbook_rejects_bad_sources(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_performance_runbook import (
        _source_reference,
        _string_sequence,
        build_style_performance_arc_live_runbook_report,
        format_style_performance_arc_live_runbook_report,
    )

    rytm_path, _ = _arc_bank_files(tmp_path)

    with pytest.raises(ValueError, match="exactly one selection source"):
        build_style_performance_arc_live_runbook_report(rytm_sysex_path=rytm_path)

    with pytest.raises(ValueError, match="exactly one selection source"):
        build_style_performance_arc_live_runbook_report(
            arc_key="jose_warehouse_five_hour",
            description="Jeff Mills",
            rytm_sysex_path=rytm_path,
        )

    with pytest.raises(ValueError, match="saved-kit source"):
        build_style_performance_arc_live_runbook_report(description="Jeff Mills")

    runbook = build_style_performance_arc_live_runbook_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
    )
    with pytest.raises(ValueError, match="event_limit must be >= 0"):
        format_style_performance_arc_live_runbook_report(runbook, event_limit=-1)

    with pytest.raises(ValueError, match="exactly one selection source"):
        _source_reference(
            arc_key=None,
            description=None,
            feature_report=None,
            audio_path=None,
            library_path=None,
        )
    assert _string_sequence(()) == "none"


def test_style_performance_arc_live_runbook_covers_single_machine_and_event_edges(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_performance_runbook import (
        build_style_performance_arc_live_runbook_report,
        format_style_performance_arc_live_runbook_report,
        to_style_performance_arc_live_runbook_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    rytm_runbook = build_style_performance_arc_live_runbook_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
        total_minutes=60,
        segment_minutes=30,
    )
    a4_runbook = build_style_performance_arc_live_runbook_report(
        arc_key="jose_warehouse_five_hour",
        analog_four_sysex_path=a4_path,
        scope="a4-only",
        total_minutes=60,
        segment_minutes=30,
    )

    assert rytm_runbook.show_mode == "Rytm only"
    assert a4_runbook.show_mode == "Analog Four only"

    rytm_text = "\n".join(
        format_style_performance_arc_live_runbook_report(
            rytm_runbook,
            include_events=True,
            event_limit=0,
        )
    )
    assert "- Planned Analog Four tracks: none" in rytm_text
    assert "  - Showing all events" in rytm_text
    assert (
        to_style_performance_arc_live_runbook_json(rytm_runbook)["live_runbook"]["show_mode"]
        == "Rytm only"
    )

    a4_text = "\n".join(format_style_performance_arc_live_runbook_report(a4_runbook))
    assert "- Planned Rytm pads: none" in a4_text

    empty_card = replace(rytm_runbook.timeline_cards[0], event_preview_rows=())
    empty_runbook = replace(rytm_runbook, timeline_cards=(empty_card,))
    empty_text = "\n".join(
        format_style_performance_arc_live_runbook_report(
            empty_runbook,
            include_events=True,
        )
    )
    assert "No mock rows available because the selected preview is not ready." in empty_text

    custom_stage_packet = replace(rytm_runbook.stage_packet, scope="custom")
    custom_cue_sheet = replace(
        rytm_runbook.live_cue_sheet,
        stage_packet=custom_stage_packet,
    )
    custom_runbook = replace(rytm_runbook, live_cue_sheet=custom_cue_sheet)
    assert custom_runbook.show_mode == "custom"


def test_style_performance_arc_live_runbook_supports_reference_sources(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    import rytm_randomizer.style_analysis as style_analysis
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.reports.live_performance_runbook import (
        build_style_performance_arc_live_runbook_report,
        format_style_performance_arc_live_runbook_report,
    )
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    rytm_path, a4_path = _arc_bank_files(tmp_path)
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

    feature_runbook = build_style_performance_arc_live_runbook_report(
        feature_report=feature_report,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert feature_runbook.selection_source == "feature-report"
    assert feature_runbook.source_reference == feature_report.content_hash
    assert feature_runbook.reference_match is not None
    assert feature_runbook.reference_match.source_kind == "feature-report"

    def fake_audio_report(path: Path) -> FeatureReport:
        assert path == Path("track.wav")
        return feature_report

    def fake_library_report(path: Path) -> FeatureReport:
        assert path == Path("library")
        return feature_report

    monkeypatch.setattr(style_analysis, "extract_from_audio", fake_audio_report)
    monkeypatch.setattr(style_analysis, "analyze_library", fake_library_report)

    audio_runbook = build_style_performance_arc_live_runbook_report(
        audio_path=Path("track.wav"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert audio_runbook.selection_source == "audio"
    assert audio_runbook.source_reference == "track.wav"
    assert audio_runbook.reference_match is not None
    assert audio_runbook.reference_match.source_reference == "track.wav"
    assert "- Source reference: track.wav" in "\n".join(
        format_style_performance_arc_live_runbook_report(audio_runbook)
    )

    library_runbook = build_style_performance_arc_live_runbook_report(
        library_path=Path("library"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert library_runbook.selection_source == "library"
    assert library_runbook.source_reference == "library"


def test_style_performance_arc_live_runbook_parser_and_handlers(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.live_performance_runbook import (
        _format_cli_error,
        _handle_cli_report,
        _parse_cli_args,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    parsed = _parse_cli_args(
        [
            "--arc",
            "jose_warehouse_five_hour",
            "--rytm",
            "rytm.syx",
            "--analog-four",
            "a4.syx",
            "--scope",
            "a4-only",
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
            "0",
            "--json",
        ]
    )
    assert parsed == {
        "arc_key": "jose_warehouse_five_hour",
        "description": None,
        "audio_path": None,
        "library_path": None,
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "analog-four-only",
        "selection_rank": 2,
        "total_minutes": 120,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 80,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }

    assert _parse_cli_args(["--description", "Jeff Mills"])["description"] == "Jeff Mills"
    assert _parse_cli_args(["--audio", "track.wav"])["audio_path"] == Path("track.wav")
    assert _parse_cli_args(["--library", "library"])["library_path"] == Path("library")

    for argv, message in (
        ([], "usage"),
        (["--arc"], "usage"),
        (["--arc", "x", "--bogus"], "usage"),
        (["--arc", "x", "--limit", "oops"], "must be an integer"),
        (["--arc", "x", "--limit", "-1"], ">= 0"),
        (["--arc", "x", "--rank", "0"], ">= 1"),
        (["--arc", "x", "--description", "Jeff Mills"], "usage"),
    ):
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    rc = _handle_cli_report(
        arc_key="jose_warehouse_five_hour",
        description=None,
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
        include_events=False,
        event_limit=1,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["live_runbook"]["selected_arc_key"] == "jose_warehouse_five_hour"
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
        description=None,
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
    assert "live runbook requires exactly one selection source" in captured.err
    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"


def test_style_performance_arc_stage_snapshot_routing_builds_route_cards(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_stage_snapshot_routing import (
        build_style_performance_arc_stage_snapshot_routing_report,
        format_style_performance_arc_stage_snapshot_routing_report,
        to_style_performance_arc_stage_snapshot_routing_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_stage_snapshot_routing_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=60,
        segment_minutes=30,
    )

    assert report.selected_arc_key == "jose_warehouse_five_hour"
    assert report.cue_count == report.runbook.cue_count
    assert len(report.route_cards) == report.runbook.cue_count
    assert report.stage_packet is report.runbook.stage_packet
    assert any(
        "SCN -> GM -> S1A -> S3A -> S3B -> S4B -> S5 -> Z -> Q" in line
        for line in report.live_set_card
    )

    first_card = report.route_cards[0]
    assert first_card.cue_number == 1
    assert first_card.rytm_kit_name == "ARC RYTM ONE"
    assert first_card.rytm_slot == 0
    assert first_card.rytm_payload_fingerprint
    assert first_card.analog_four_kit_name == "ARC A4 ONE"
    assert first_card.analog_four_slot == 0
    assert first_card.analog_four_payload_fingerprint
    assert first_card.planned_rytm_pads
    assert first_card.planned_analog_four_tracks
    assert first_card.rytm_mock_row_count > 0
    assert first_card.analog_four_deferred_row_count >= first_card.analog_four_mock_row_count
    assert first_card.route_status in {"ready", "partial", "blocked", "empty"}
    assert "candidate-only" in first_card.blocker_summary

    text = "\n".join(
        format_style_performance_arc_stage_snapshot_routing_report(
            report,
            include_events=True,
            event_limit=1,
        )
    )
    assert "RytmRandomizer passive style performance arc stage snapshot routing" in text
    assert "Stage snapshot routing summary:" in text
    assert "Live set card:" in text
    assert "Route cards:" in text
    assert "Rytm snapshot: slot 0 ARC RYTM ONE" in text
    assert "Analog Four snapshot: slot 0 ARC A4 ONE" in text
    assert "A4 deferred/candidate rows:" in text
    assert "Rescue sequence: S5 -> Z -> Q" in text
    assert "Cue event preview:" in text
    assert "Showing first 1 of" in text
    assert "- no MIDI sending" in text
    assert "- no port opening" in text

    payload = to_style_performance_arc_stage_snapshot_routing_json(report)
    route_payload = payload["stage_snapshot_routing"]["route_cards"][0]
    assert route_payload["cue_number"] == 1
    assert route_payload["rytm"]["kit_name"] == "ARC RYTM ONE"
    assert route_payload["rytm"]["slot"] == 0
    assert route_payload["analog_four"]["kit_name"] == "ARC A4 ONE"
    assert route_payload["analog_four"]["slot"] == 0
    assert route_payload["rytm"]["mock_row_count"] == first_card.rytm_mock_row_count
    assert (
        route_payload["analog_four"]["deferred_row_count"]
        == first_card.analog_four_deferred_row_count
    )
    assert payload["live_runbook"]["selected_arc_key"] == "jose_warehouse_five_hour"


def test_style_performance_arc_stage_snapshot_routing_supports_references_and_edges(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    import rytm_randomizer.style_analysis as style_analysis
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.reports.live_stage_snapshot_routing import (
        _blocker_summary,
        _route_cards_from_runbook,
        _route_status,
        _stage_routing_command,
        _string_sequence,
        build_style_performance_arc_stage_snapshot_routing_report,
        format_style_performance_arc_stage_snapshot_routing_report,
    )
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_stage_snapshot_routing_report(
        description="Jeff Mills Oscar Mulero tunnel hypnosis",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert report.selection_source == "description"
    assert report.reference_match is not None
    assert report.selected_arc_key == "mills_mulero_tunnel"

    text = "\n".join(format_style_performance_arc_stage_snapshot_routing_report(report))
    assert "Reference match:" in text
    assert "mills_mulero_tunnel" in text

    rytm_only = build_style_performance_arc_stage_snapshot_routing_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
        total_minutes=60,
        segment_minutes=30,
    )
    assert rytm_only.show_mode == "Rytm only"
    assert rytm_only.route_cards[0].analog_four_kit_name is None
    assert "Analog Four snapshot: unchanged by scope" in "\n".join(
        format_style_performance_arc_stage_snapshot_routing_report(rytm_only)
    )

    a4_only = build_style_performance_arc_stage_snapshot_routing_report(
        arc_key="jose_warehouse_five_hour",
        analog_four_sysex_path=a4_path,
        scope="a4-only",
        total_minutes=60,
        segment_minutes=30,
    )
    assert a4_only.show_mode == "Analog Four only"
    assert a4_only.route_cards[0].rytm_kit_name is None
    assert "Rytm snapshot: unchanged by scope" in "\n".join(
        format_style_performance_arc_stage_snapshot_routing_report(a4_only)
    )

    empty_card = replace(report.route_cards[0], event_preview_rows=())
    empty_report = replace(report, route_cards=(empty_card,))
    assert "No mock rows available because the selected preview is not ready." in "\n".join(
        format_style_performance_arc_stage_snapshot_routing_report(
            empty_report,
            include_events=True,
        )
    )
    assert "Showing all events" in "\n".join(
        format_style_performance_arc_stage_snapshot_routing_report(
            report,
            include_events=True,
            event_limit=0,
        )
    )

    with pytest.raises(ValueError, match="event_limit"):
        format_style_performance_arc_stage_snapshot_routing_report(report, event_limit=-1)

    mismatched_runbook = replace(report.runbook, timeline_cards=())
    with pytest.raises(ValueError, match="matching runbook cue counts"):
        _route_cards_from_runbook(mismatched_runbook)

    assert _string_sequence(()) == "none"
    assert _route_status(readiness="custom", event_row_count=0, deferred_row_count=1) == "partial"
    assert _route_status(readiness="custom", event_row_count=1, deferred_row_count=0) == "ready"
    assert _route_status(readiness="custom", event_row_count=0, deferred_row_count=0) == "empty"
    assert (
        _blocker_summary(
            preview_plan=SimpleNamespace(analog_four_preview=None),
            event_row_count=3,
            deferred_rows=("- manual deferred row",),
        )
        == "Deferred rows are present; rehearse this cue before armed live use."
    )
    assert (
        _blocker_summary(
            preview_plan=SimpleNamespace(analog_four_preview=None),
            event_row_count=0,
            deferred_rows=("- none",),
        )
        == "No mock rows are available because the selected preview is not ready."
    )

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
        derived_at="2026-05-22T12:00:00Z",
    )
    feature_report = replace(
        feature_report,
        content_hash=compute_feature_report_hash(feature_report),
    )

    feature_route = build_style_performance_arc_stage_snapshot_routing_report(
        feature_report=feature_report,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert feature_route.selection_source == "feature-report"
    assert feature_route.source_reference == feature_report.content_hash
    assert "--description" in _stage_routing_command(feature_route.runbook)

    monkeypatch.setattr(style_analysis, "extract_from_audio", lambda path: feature_report)
    monkeypatch.setattr(style_analysis, "analyze_library", lambda path: feature_report)

    audio_report = build_style_performance_arc_stage_snapshot_routing_report(
        audio_path=Path("track.wav"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    library_report = build_style_performance_arc_stage_snapshot_routing_report(
        library_path=Path("library"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert "--audio track.wav" in _stage_routing_command(audio_report.runbook)
    assert "--library library" in _stage_routing_command(library_report.runbook)
    assert "- Source reference: track.wav" in "\n".join(
        format_style_performance_arc_stage_snapshot_routing_report(audio_report)
    )


def test_style_performance_arc_stage_snapshot_routing_parser_and_handlers(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.live_stage_snapshot_routing import (
        _format_cli_error,
        _handle_cli_report,
        _parse_cli_args,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    parsed = _parse_cli_args(
        [
            "--arc",
            "jose_warehouse_five_hour",
            "--rytm",
            "rytm.syx",
            "--analog-four",
            "a4.syx",
            "--scope",
            "a4-only",
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
            "0",
            "--json",
        ]
    )
    assert parsed == {
        "arc_key": "jose_warehouse_five_hour",
        "description": None,
        "audio_path": None,
        "library_path": None,
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "analog-four-only",
        "selection_rank": 2,
        "total_minutes": 120,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 80,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }

    assert _parse_cli_args(["--description", "Jeff Mills"])["description"] == "Jeff Mills"
    assert _parse_cli_args(["--audio", "track.wav"])["audio_path"] == Path("track.wav")
    assert _parse_cli_args(["--library", "library"])["library_path"] == Path("library")

    for argv, message in (
        ([], "usage"),
        (["--arc"], "usage"),
        (["--arc", "x", "--bogus"], "usage"),
        (["--arc", "x", "--limit", "oops"], "must be an integer"),
        (["--arc", "x", "--limit", "-1"], ">= 0"),
        (["--arc", "x", "--rank", "0"], ">= 1"),
        (["--arc", "x", "--description", "Jeff Mills"], "usage"),
    ):
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    rc = _handle_cli_report(
        arc_key="jose_warehouse_five_hour",
        description=None,
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
        include_events=False,
        event_limit=1,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["stage_snapshot_routing"]["selected_arc_key"] == "jose_warehouse_five_hour"
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
        description=None,
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
    assert "stage snapshot routing requires exactly one selection source" in captured.err
    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"


def test_style_performance_arc_stage_rehearsal_state_builds_operator_packet(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_stage_rehearsal_state import (
        build_style_performance_arc_stage_rehearsal_state_report,
        format_style_performance_arc_stage_rehearsal_state_report,
        to_style_performance_arc_stage_rehearsal_state_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_stage_rehearsal_state_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=60,
        segment_minutes=30,
    )

    assert report.selected_arc_key == "jose_warehouse_five_hour"
    assert report.stage_routing.selected_arc_key == report.selected_arc_key
    assert report.cue_count == report.stage_routing.cue_count
    assert len(report.cue_states) == report.cue_count
    assert report.overall_go_no_go == "rehearse"
    assert report.stage_state == "rehearsal-required"
    assert report.rehearsal_steps == (
        "Run the passive stage routing report and confirm saved-kit slots before arming.",
        "Practice the listed cue moves with the sequencer running and monitor levels.",
        "Treat rehearse cues as soundcheck-only until deferred/candidate rows are resolved.",
        "Keep S5 -> Z -> Q ready as the recovery sequence.",
    )

    first_cue = report.cue_states[0]
    assert first_cue.cue_number == 1
    assert first_cue.go_no_go == "rehearse"
    assert first_cue.operator_prompt.startswith("Rehearse cue 1")
    assert first_cue.rytm_state.status == "loaded"
    assert first_cue.rytm_state.kit_name == "ARC RYTM ONE"
    assert first_cue.rytm_state.slot == 0
    assert first_cue.rytm_state.payload_fingerprint
    assert first_cue.rytm_state.mock_row_count > 0
    assert first_cue.analog_four_state.status == "candidate-deferred"
    assert first_cue.analog_four_state.kit_name == "ARC A4 ONE"
    assert first_cue.analog_four_state.deferred_row_count > 0

    machine_names = {state.machine for state in report.machine_states}
    assert machine_names == {"rytm", "analog-four"}
    rytm_summary = next(state for state in report.machine_states if state.machine == "rytm")
    a4_summary = next(state for state in report.machine_states if state.machine == "analog-four")
    assert rytm_summary.status == "loaded"
    assert rytm_summary.planned_units
    assert rytm_summary.mock_row_count >= first_cue.rytm_state.mock_row_count
    assert a4_summary.status == "candidate-deferred"
    assert a4_summary.deferred_row_count >= first_cue.analog_four_state.deferred_row_count

    text = "\n".join(
        format_style_performance_arc_stage_rehearsal_state_report(
            report,
            include_events=True,
            event_limit=1,
        )
    )
    assert "RytmRandomizer passive style performance arc stage rehearsal state" in text
    assert "Stage rehearsal summary:" in text
    assert "- Stage state: rehearsal-required" in text
    assert "- Go / no-go: rehearse" in text
    assert "Machine states:" in text
    assert "- Rytm: loaded" in text
    assert "- Analog Four: candidate-deferred" in text
    assert "Rehearsal steps:" in text
    assert "Cue states:" in text
    assert "Cue 1. 00:00-" in text
    assert "Operator prompt: Rehearse cue 1" in text
    assert "Rescue sequence: S5 -> Z -> Q" in text
    assert "Cue event preview:" in text
    assert "Showing first 1 of" in text
    assert "- rehearsal state packet only" in text
    assert "- no MIDI sending" in text
    assert "- no port opening" in text

    payload = to_style_performance_arc_stage_rehearsal_state_json(report)
    state_payload = payload["stage_rehearsal_state"]
    assert state_payload["selected_arc_key"] == "jose_warehouse_five_hour"
    assert state_payload["stage_state"] == "rehearsal-required"
    assert state_payload["overall_go_no_go"] == "rehearse"
    assert state_payload["cue_states"][0]["go_no_go"] == first_cue.go_no_go
    assert state_payload["cue_states"][0]["rytm"]["kit_name"] == "ARC RYTM ONE"
    assert state_payload["cue_states"][0]["analog_four"]["status"] == "candidate-deferred"
    assert {state["machine"] for state in state_payload["machine_states"]} == {
        "rytm",
        "analog-four",
    }
    assert payload["stage_snapshot_routing"]["selected_arc_key"] == "jose_warehouse_five_hour"
    assert payload["live_runbook"]["selected_arc_key"] == "jose_warehouse_five_hour"
    assert payload["safety"][0] == "passive/read-only"


def test_style_performance_arc_stage_rehearsal_state_sources_edges_and_parser(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    import rytm_randomizer.style_analysis as style_analysis
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.reports.live_stage_rehearsal_state import (
        _aggregate_machine_state,
        _aggregate_status,
        _cue_state_from_route_card,
        _format_cli_error,
        _handle_cli_report,
        _machine_state_for_card,
        _parse_cli_args,
        _stage_state,
        build_style_performance_arc_stage_rehearsal_state_report,
        format_style_performance_arc_stage_rehearsal_state_report,
    )
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    report = build_style_performance_arc_stage_rehearsal_state_report(
        description="Jeff Mills Oscar Mulero tunnel hypnosis",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert report.selection_source == "description"
    assert report.reference_match is not None
    assert report.selected_arc_key == "mills_mulero_tunnel"
    reference_text = "\n".join(format_style_performance_arc_stage_rehearsal_state_report(report))
    assert "Reference match:" in reference_text
    assert "Source reference: Jeff Mills Oscar Mulero tunnel hypnosis" in reference_text

    first_card = report.stage_routing.route_cards[0]
    loaded_a4_card = replace(
        first_card,
        route_status="ready",
        deferred_row_count=0,
        analog_four_deferred_row_count=0,
        analog_four_mock_row_count=1,
    )
    loaded_a4_state = _machine_state_for_card(loaded_a4_card, machine="analog-four")
    assert loaded_a4_state.status == "loaded"
    assert "Confirm Analog Four kit slot" in loaded_a4_state.operator_check
    assert _cue_state_from_route_card(loaded_a4_card).go_no_go == "go"

    partial_card = replace(loaded_a4_card, route_status="partial")
    assert _cue_state_from_route_card(partial_card).go_no_go == "rehearse"

    blocked_rytm_card = replace(
        loaded_a4_card,
        rytm_mock_row_count=0,
    )
    blocked_rytm_state = _machine_state_for_card(blocked_rytm_card, machine="rytm")
    assert blocked_rytm_state.status == "blocked"
    assert "Do not arm Rytm" in blocked_rytm_state.operator_check
    assert _cue_state_from_route_card(blocked_rytm_card).go_no_go == "do-not-arm"

    blocked_a4_card = replace(
        loaded_a4_card,
        analog_four_mock_row_count=0,
    )
    blocked_a4_state = _machine_state_for_card(blocked_a4_card, machine="analog-four")
    assert blocked_a4_state.status == "blocked"
    assert "Do not arm Analog Four" in blocked_a4_state.operator_check
    assert _cue_state_from_route_card(blocked_a4_card).go_no_go == "do-not-arm"

    assert _aggregate_status(()) == "empty"
    assert _aggregate_status((blocked_a4_state,)) == "blocked"
    assert _aggregate_status((replace(blocked_a4_state, status="parked"),)) == "parked"
    assert (
        _aggregate_machine_state(
            (blocked_a4_state,),
            machine="analog-four",
            label="Analog Four",
        ).operator_check
        == "Resolve Analog Four blocked cues before live use."
    )

    empty_event_report = replace(
        report,
        cue_states=(replace(report.cue_states[0], event_preview_rows=()),),
    )
    assert "No mock rows available because the selected preview is not ready." in "\n".join(
        format_style_performance_arc_stage_rehearsal_state_report(
            empty_event_report,
            include_events=True,
        )
    )

    rytm_only = build_style_performance_arc_stage_rehearsal_state_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
        total_minutes=60,
        segment_minutes=30,
    )
    assert rytm_only.cue_states[0].analog_four_state.status == "unchanged-by-scope"
    assert "Analog Four: unchanged-by-scope" in "\n".join(
        format_style_performance_arc_stage_rehearsal_state_report(rytm_only)
    )

    a4_only = build_style_performance_arc_stage_rehearsal_state_report(
        arc_key="jose_warehouse_five_hour",
        analog_four_sysex_path=a4_path,
        scope="a4-only",
        total_minutes=60,
        segment_minutes=30,
    )
    assert a4_only.cue_states[0].rytm_state.status == "unchanged-by-scope"
    assert "Rytm: unchanged-by-scope" in "\n".join(
        format_style_performance_arc_stage_rehearsal_state_report(a4_only)
    )

    assert "Showing all events" in "\n".join(
        format_style_performance_arc_stage_rehearsal_state_report(
            report,
            include_events=True,
            event_limit=0,
        )
    )
    with pytest.raises(ValueError, match="event_limit"):
        format_style_performance_arc_stage_rehearsal_state_report(report, event_limit=-1)
    assert _stage_state("go") == "ready"
    assert _stage_state("rehearse") == "rehearsal-required"
    assert _stage_state("do-not-arm") == "blocked"

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
        derived_at="2026-05-22T12:00:00Z",
    )
    feature_report = replace(
        feature_report,
        content_hash=compute_feature_report_hash(feature_report),
    )
    feature_state = build_style_performance_arc_stage_rehearsal_state_report(
        feature_report=feature_report,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert feature_state.selection_source == "feature-report"
    assert feature_state.source_reference == feature_report.content_hash

    monkeypatch.setattr(style_analysis, "extract_from_audio", lambda path: feature_report)
    monkeypatch.setattr(style_analysis, "analyze_library", lambda path: feature_report)
    audio_state = build_style_performance_arc_stage_rehearsal_state_report(
        audio_path=Path("track.wav"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    library_state = build_style_performance_arc_stage_rehearsal_state_report(
        library_path=Path("library"),
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert "track.wav" in (audio_state.source_reference or "")
    assert "library" in (library_state.source_reference or "")
    assert "Source reference: track.wav" in "\n".join(
        format_style_performance_arc_stage_rehearsal_state_report(audio_state)
    )

    parsed = _parse_cli_args(
        [
            "--arc",
            "jose_warehouse_five_hour",
            "--rytm",
            "rytm.syx",
            "--analog-four",
            "a4.syx",
            "--scope",
            "a4-only",
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
            "0",
            "--json",
        ]
    )
    assert parsed == {
        "arc_key": "jose_warehouse_five_hour",
        "description": None,
        "audio_path": None,
        "library_path": None,
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "analog-four-only",
        "selection_rank": 2,
        "total_minutes": 120,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 80,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }
    assert _parse_cli_args(["--description", "Jeff Mills"])["description"] == "Jeff Mills"
    assert _parse_cli_args(["--audio", "track.wav"])["audio_path"] == Path("track.wav")
    assert _parse_cli_args(["--library", "library"])["library_path"] == Path("library")
    for argv, message in (
        ([], "usage"),
        (["--arc"], "usage"),
        (["--arc", "x", "--bogus"], "usage"),
        (["--arc", "x", "--limit", "oops"], "must be an integer"),
        (["--arc", "x", "--limit", "-1"], ">= 0"),
        (["--arc", "x", "--rank", "0"], ">= 1"),
        (["--arc", "x", "--description", "Jeff Mills"], "usage"),
    ):
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    rc = _handle_cli_report(
        arc_key="jose_warehouse_five_hour",
        description=None,
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
        include_events=False,
        event_limit=1,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["stage_rehearsal_state"]["selected_arc_key"] == "jose_warehouse_five_hour"
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key="jose_warehouse_five_hour",
        description=None,
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
        include_events=False,
        event_limit=1,
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive style performance arc stage rehearsal state" in captured.out
    assert "Stage rehearsal summary:" in captured.out
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
        description=None,
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
    assert "stage rehearsal state requires exactly one selection source" in captured.err
    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"


def test_style_performance_arc_live_set_cockpit_builds_stage_dashboard(tmp_path: Path):
    from rytm_randomizer.reports.live_set_cockpit import (
        build_style_performance_arc_live_set_cockpit_report,
        format_style_performance_arc_live_set_cockpit_report,
        to_style_performance_arc_live_set_cockpit_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)

    report = build_style_performance_arc_live_set_cockpit_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=45,
        segment_minutes=15,
    )

    assert report.selected_arc_key == "mills_mulero_tunnel"
    assert report.stage_rehearsal_state.selected_arc_key == report.selected_arc_key
    assert report.cue_count == report.stage_rehearsal_state.cue_count
    assert report.cockpit_status == "rehearsal-required"
    assert report.operator_mode == "soundcheck"
    assert report.overall_go_no_go == "rehearse"
    assert report.next_best_action.startswith("Rehearse")
    assert report.cue_cards[0].status_light == "AMBER"
    assert report.cue_cards[0].deck_label == "Cue 1"
    assert "Rytm loaded" in report.cue_cards[0].machine_arm_summary
    assert "Analog Four candidate-deferred" in report.cue_cards[0].machine_arm_summary
    assert report.machine_panels[0].label == "Rytm"
    assert report.machine_panels[1].label == "Analog Four"
    assert report.recovery_controls[-1] == "Exit the script with Q if anything feels wrong."

    text = "\n".join(
        format_style_performance_arc_live_set_cockpit_report(
            report,
            include_events=True,
            event_limit=1,
        )
    )
    assert "RytmRandomizer passive style performance arc live set cockpit" in text
    assert "Cockpit summary:" in text
    assert "- Cockpit status: rehearsal-required" in text
    assert "- Operator mode: soundcheck" in text
    assert "Launch controls:" in text
    assert "Machine panels:" in text
    assert "Cue cockpit cards:" in text
    assert "Recovery controls:" in text
    assert "S5 -> Z -> Q" in text
    assert "Cue event preview:" in text
    assert "Showing first 1 of" in text
    assert "- live set cockpit packet only" in text
    assert "- no MIDI sending" in text
    assert "- no port opening" in text

    payload = to_style_performance_arc_live_set_cockpit_json(report)
    cockpit_payload = payload["live_set_cockpit"]
    assert cockpit_payload["selected_arc_key"] == "mills_mulero_tunnel"
    assert cockpit_payload["cockpit_status"] == "rehearsal-required"
    assert cockpit_payload["operator_mode"] == "soundcheck"
    assert cockpit_payload["cue_cards"][0]["status_light"] == "AMBER"
    assert cockpit_payload["cue_cards"][0]["machine_arm_summary"].startswith("Rytm loaded")
    assert payload["stage_rehearsal_state"]["selected_arc_key"] == "mills_mulero_tunnel"
    assert payload["safety"][-1] == "no hardware required"


def test_style_performance_arc_live_set_cockpit_sources_edges_and_parser(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.reports.live_set_cockpit import (
        _format_cli_error,
        _handle_cli_report,
        _machine_panel,
        _machine_status_light,
        _next_best_action,
        _operator_mode,
        _parse_cli_args,
        _status_light,
        _string_sequence,
        build_style_performance_arc_live_set_cockpit_from_rehearsal_state,
        build_style_performance_arc_live_set_cockpit_report,
        format_style_performance_arc_live_set_cockpit_report,
    )
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    rytm_path, a4_path = _arc_bank_files(tmp_path)

    report = build_style_performance_arc_live_set_cockpit_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope="rytm-only",
        total_minutes=30,
        segment_minutes=15,
    )
    from_rehearsal = build_style_performance_arc_live_set_cockpit_from_rehearsal_state(
        report.stage_rehearsal_state
    )
    assert from_rehearsal.selected_arc_key == report.selected_arc_key
    assert from_rehearsal.operator_mode == report.operator_mode
    assert "Analog Four unchanged-by-scope" in from_rehearsal.cue_cards[0].machine_arm_summary

    assert _string_sequence(()) == "none"
    assert _status_light("go") == "GREEN"
    assert _status_light("do-not-arm") == "RED"
    assert _status_light("custom") == "WHITE"
    assert _machine_status_light("blocked") == "RED"
    assert _machine_status_light("custom") == "WHITE"
    assert _operator_mode("ready") == "performance-ready"
    assert _operator_mode("blocked") == "blocked"
    assert _operator_mode("custom") == "review"
    assert _next_best_action("ready", "go").startswith("Run one passive")
    assert _next_best_action("blocked", "do-not-arm").startswith("Resolve red")
    assert _next_best_action("custom", "custom").startswith("Review cockpit state")
    blocked_panel = _machine_panel(
        replace(report.stage_rehearsal_state.machine_states[0], status="blocked")
    )
    assert blocked_panel.arm_state == "do-not-arm"

    no_event_text = "\n".join(format_style_performance_arc_live_set_cockpit_report(report))
    assert "Cue event preview:" not in no_event_text

    a4_only = build_style_performance_arc_live_set_cockpit_report(
        arc_key="jose_warehouse_five_hour",
        analog_four_sysex_path=a4_path,
        scope="a4-only",
        total_minutes=30,
        segment_minutes=15,
    )
    assert "Rytm unchanged-by-scope" in a4_only.cue_cards[0].machine_arm_summary
    assert "Showing all events" in "\n".join(
        format_style_performance_arc_live_set_cockpit_report(
            report,
            include_events=True,
            event_limit=0,
        )
    )
    assert "No mock rows available because the selected preview is not ready." in "\n".join(
        format_style_performance_arc_live_set_cockpit_report(
            a4_only,
            include_events=True,
            event_limit=0,
        )
    )
    with pytest.raises(ValueError, match="event_limit"):
        format_style_performance_arc_live_set_cockpit_report(report, event_limit=-1)

    parsed = _parse_cli_args(
        [
            "--arc",
            "jose_warehouse_five_hour",
            "--rytm",
            "rytm.syx",
            "--analog-four",
            "a4.syx",
            "--scope",
            "a4-only",
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
            "0",
            "--json",
        ]
    )
    assert parsed == {
        "arc_key": "jose_warehouse_five_hour",
        "description": None,
        "audio_path": None,
        "library_path": None,
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "analog-four-only",
        "selection_rank": 2,
        "total_minutes": 120,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 80,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }
    audio_parsed = _parse_cli_args(["--audio", "track.wav"])
    library_parsed = _parse_cli_args(["--library", "library-root"])
    assert audio_parsed["audio_path"] == Path("track.wav")
    assert library_parsed["library_path"] == Path("library-root")
    for argv, message in (
        ([], "usage"),
        (["--arc"], "usage"),
        (["--arc", "x", "--bogus"], "usage"),
        (["--arc", "x", "--limit", "oops"], "must be an integer"),
        (["--arc", "x", "--limit", "-1"], ">= 0"),
        (["--arc", "x", "--rank", "0"], ">= 1"),
        (["--arc", "x", "--description", "Jeff Mills"], "usage"),
    ):
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    rc = _handle_cli_report(
        arc_key=None,
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
    assert "RytmRandomizer passive style performance arc live set cockpit" in captured.out
    assert "Cockpit summary:" in captured.out
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
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
        include_events=False,
        event_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["live_set_cockpit"]["selected_arc_key"] == "mills_mulero_tunnel"
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
        description=None,
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
    assert "live set cockpit requires exactly one selection source" in captured.err
    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"

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
        derived_at="2026-05-22T12:00:00Z",
    )
    feature_report = replace(
        feature_report,
        content_hash=compute_feature_report_hash(feature_report),
    )
    feature_state = build_style_performance_arc_live_set_cockpit_report(
        feature_report=feature_report,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert feature_state.selection_source == "feature-report"
    assert feature_state.source_reference == feature_report.content_hash
    assert "--arc " in feature_state.suggested_commands[0]
    assert "--feature-report" not in feature_state.suggested_commands[0]


def test_style_performance_arc_live_show_export_builds_show_handoff_packet(
    tmp_path: Path,
):
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.reports.live_show_export import (
        _parse_cli_args,
        build_style_performance_arc_live_show_export_report,
        format_style_performance_arc_live_show_export_report,
        to_style_performance_arc_live_show_export_json,
    )
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    rytm_path, a4_path = _arc_bank_files(tmp_path)

    report = build_style_performance_arc_live_show_export_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=45,
        segment_minutes=15,
    )
    rebuilt = build_style_performance_arc_live_show_export_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=45,
        segment_minutes=15,
    )

    assert report.packet_version == "live-show-export-v1"
    assert report.export_id == rebuilt.export_id
    assert len(report.export_id) == 12

    feature_report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=138.0,
        tempo_stability=0.94,
        kick_density=0.88,
        percussion_density=0.9,
        low_end_weight=0.84,
        spectral_brightness=0.24,
        texture_noise=0.82,
        energy_arc=(0.32, 0.42, 0.53, 0.66, 0.8, 0.93, 0.91, 0.86),
        content_hash="",
        derived_at="2026-05-22T12:00:00Z",
    )
    feature_report = replace(
        feature_report,
        content_hash=compute_feature_report_hash(feature_report),
    )
    later_feature_report = replace(
        feature_report,
        content_hash="",
        derived_at="2026-05-22T12:00:05Z",
    )
    later_feature_report = replace(
        later_feature_report,
        content_hash=compute_feature_report_hash(later_feature_report),
    )
    feature_export = build_style_performance_arc_live_show_export_report(
        feature_report=feature_report,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=45,
        segment_minutes=15,
    )
    later_feature_export = build_style_performance_arc_live_show_export_report(
        feature_report=later_feature_report,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=45,
        segment_minutes=15,
    )
    assert feature_report.content_hash != later_feature_report.content_hash
    assert feature_export.export_id == later_feature_export.export_id

    assert report.selected_arc_key == "mills_mulero_tunnel"
    assert report.go_no_go == "rehearse"
    assert report.show_summary.startswith("mills_mulero_tunnel /")
    assert len(report.cue_steps) == report.cockpit.cue_count
    assert report.cue_steps[0].cue_number == 1
    assert report.cue_steps[0].launch_line.startswith("Cue 1")
    assert "machine focus" in report.cue_steps[0].preflight_check
    assert report.cue_steps[0].passive_command.startswith("python -m rytm_randomizer.cli")
    for command in report.suggested_commands:
        command_args = shlex.split(command)
        if "--description" in command_args:
            description_index = command_args.index("--description") + 1
            assert command_args[description_index] == "Jeff Mills Oscar Mulero tunnel"
        if command_args[3] == "style-performance-arc-live-show-export-report":
            assert (
                _parse_cli_args(command_args[4:])["description"] == "Jeff Mills Oscar Mulero tunnel"
            )
    cue_command = report.cue_steps[0].passive_command.split(" # cue ", 1)[0]
    cue_command_args = shlex.split(cue_command)[4:]
    assert _parse_cli_args(cue_command_args)["description"] == "Jeff Mills Oscar Mulero tunnel"
    assert {machine.label for machine in report.machine_exports} == {"Rytm", "Analog Four"}
    assert any("do not arm" in line.lower() for line in report.recovery_script)

    apostrophe_report = build_style_performance_arc_live_show_export_report(
        description="King's Hall Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=45,
        segment_minutes=15,
    )
    apostrophe_command = apostrophe_report.suggested_commands[0]
    assert "--description 'King''s Hall Jeff Mills Oscar Mulero tunnel'" in (apostrophe_command)
    assert "--description 'King''s Hall Jeff Mills Oscar Mulero tunnel'" in (
        apostrophe_report.cue_steps[0].passive_command
    )

    text = "\n".join(
        format_style_performance_arc_live_show_export_report(
            report,
            include_events=True,
            event_limit=1,
        )
    )
    assert "RytmRandomizer passive style performance arc live show export" in text
    assert "Show export summary:" in text
    assert "Machine handoff manifest:" in text
    assert "Cue launch script:" in text
    assert "Cue event preview:" in text
    assert "Recovery script:" in text
    assert "Replayable passive commands:" in text
    assert "- live show export packet only" in text
    assert "- no file writing" in text
    assert "- no MIDI sending" in text
    assert "- no port opening" in text

    payload = to_style_performance_arc_live_show_export_json(report)
    export_payload = payload["live_show_export"]
    assert export_payload["packet_version"] == "live-show-export-v1"
    assert export_payload["export_id"] == report.export_id
    assert export_payload["selected_arc_key"] == "mills_mulero_tunnel"
    assert export_payload["cue_steps"][0]["launch_line"].startswith("Cue 1")
    assert export_payload["machine_exports"][0]["label"] == "Rytm"
    assert payload["live_set_cockpit"]["selected_arc_key"] == "mills_mulero_tunnel"
    assert payload["stage_rehearsal_state"]["selected_arc_key"] == "mills_mulero_tunnel"
    assert payload["safety"][-1] == "no hardware required"


def test_style_performance_arc_live_show_export_sources_edges_parser_and_cli(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.reports.live_set_cockpit import (
        build_style_performance_arc_live_set_cockpit_report,
    )
    from rytm_randomizer.reports.live_show_export import (
        _format_cli_error,
        _handle_cli_report,
        _machine_export,
        _parse_cli_args,
        _status_action,
        _step_status_light,
        _string_sequence,
        build_style_performance_arc_live_show_export_from_cockpit,
        build_style_performance_arc_live_show_export_report,
        format_style_performance_arc_live_show_export_report,
    )
    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash

    rytm_path, a4_path = _arc_bank_files(tmp_path)

    cockpit = build_style_performance_arc_live_set_cockpit_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        scope="rytm-only",
        total_minutes=30,
        segment_minutes=15,
    )
    from_cockpit = build_style_performance_arc_live_show_export_from_cockpit(cockpit)
    assert from_cockpit.selected_arc_key == cockpit.selected_arc_key
    assert "Analog Four unchanged-by-scope" in from_cockpit.cue_steps[0].machine_focus

    assert _string_sequence(()) == "none"
    assert _string_sequence(("kick", "hat")) == "kick, hat"
    assert _status_action("go") == "launch-ready"
    assert _status_action("rehearse") == "rehearse-before-arm"
    assert _status_action("do-not-arm") == "skip-and-recover"
    assert _status_action("custom") == "review"
    assert _step_status_light("go") == "GREEN"
    assert _step_status_light("rehearse") == "AMBER"
    assert _step_status_light("do-not-arm") == "RED"
    assert _step_status_light("custom") == "WHITE"
    blocked_export = _machine_export(replace(cockpit.machine_panels[0], status="blocked"))
    assert blocked_export.status_action == "do-not-arm"

    no_event_text = "\n".join(format_style_performance_arc_live_show_export_report(from_cockpit))
    assert "Cue event preview:" not in no_event_text
    assert "Showing all events" in "\n".join(
        format_style_performance_arc_live_show_export_report(
            from_cockpit,
            include_events=True,
            event_limit=0,
        )
    )
    a4_only = build_style_performance_arc_live_show_export_report(
        arc_key="jose_warehouse_five_hour",
        analog_four_sysex_path=a4_path,
        scope="a4-only",
        total_minutes=30,
        segment_minutes=15,
    )
    assert (
        "No mock rows available because the selected cue has no ready mock preview."
        in "\n".join(
            format_style_performance_arc_live_show_export_report(
                a4_only,
                include_events=True,
                event_limit=0,
            )
        )
    )
    with pytest.raises(ValueError, match="event_limit"):
        format_style_performance_arc_live_show_export_report(from_cockpit, event_limit=-1)

    parsed = _parse_cli_args(
        [
            "--arc",
            "jose_warehouse_five_hour",
            "--rytm",
            "rytm.syx",
            "--analog-four",
            "a4.syx",
            "--scope",
            "a4-only",
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
            "0",
            "--json",
        ]
    )
    assert parsed == {
        "arc_key": "jose_warehouse_five_hour",
        "description": None,
        "audio_path": None,
        "library_path": None,
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "analog-four-only",
        "selection_rank": 2,
        "total_minutes": 120,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 80,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }
    assert _parse_cli_args(["--audio", "track.wav"])["audio_path"] == Path("track.wav")
    assert _parse_cli_args(["--library", "library-root"])["library_path"] == Path("library-root")
    for argv, message in (
        ([], "usage"),
        (["--arc"], "usage"),
        (["--arc", "x", "--bogus"], "usage"),
        (["--arc", "x", "--limit", "oops"], "must be an integer"),
        (["--arc", "x", "--limit", "-1"], ">= 0"),
        (["--arc", "x", "--rank", "0"], ">= 1"),
        (["--arc", "x", "--description", "Jeff Mills"], "usage"),
    ):
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    rc = _handle_cli_report(
        arc_key=None,
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
    assert "RytmRandomizer passive style performance arc live show export" in captured.out
    assert "Show export summary:" in captured.out
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
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
        include_events=False,
        event_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["live_show_export"]["selected_arc_key"] == "mills_mulero_tunnel"
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
        description=None,
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
    assert "live show export requires exactly one selection source" in captured.err
    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"

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
        derived_at="2026-05-22T12:00:00Z",
    )
    feature_report = replace(
        feature_report,
        content_hash=compute_feature_report_hash(feature_report),
    )
    feature_state = build_style_performance_arc_live_show_export_report(
        feature_report=feature_report,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert feature_state.selection_source == "feature-report"
    assert feature_state.source_reference == feature_report.content_hash
    assert "--feature-report" not in feature_state.suggested_commands[0]


def test_style_performance_arc_live_transition_timeline_builds_operator_timeline(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_show_export import (
        build_style_performance_arc_live_show_export_report,
    )
    from rytm_randomizer.reports.live_transition_timeline import (
        build_style_performance_arc_live_transition_timeline_from_export,
        build_style_performance_arc_live_transition_timeline_report,
        format_style_performance_arc_live_transition_timeline_report,
        to_style_performance_arc_live_transition_timeline_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    show_export = build_style_performance_arc_live_show_export_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=45,
        segment_minutes=15,
    )
    report = build_style_performance_arc_live_transition_timeline_from_export(show_export)
    rebuilt = build_style_performance_arc_live_transition_timeline_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=45,
        segment_minutes=15,
    )

    assert report.timeline_version == "live-transition-timeline-v1"
    assert report.timeline_id == rebuilt.timeline_id
    assert report.timeline_id.startswith(show_export.export_id)
    assert report.selected_arc_key == "mills_mulero_tunnel"
    assert report.go_no_go == show_export.go_no_go
    assert len(report.transition_cards) == len(show_export.cue_steps)
    first = report.transition_cards[0]
    assert first.transition_number == 1
    assert first.cue_number == show_export.cue_steps[0].cue_number
    assert first.phase == "soundcheck"
    assert first.prep_window == "before show"
    assert "Confirm machine focus" in first.prep_actions[0]
    assert first.launch_action.startswith("Cue 1")
    assert "Hold current machines" in first.hold_action
    assert first.machine_handoff.startswith("Rytm:")
    assert "--description 'Jeff Mills Oscar Mulero tunnel'" in first.passive_command
    assert report.operator_timeline[0].startswith("Transition 1")
    assert any("cue 1" in step.lower() for step in report.rehearsal_loop)

    apostrophe_report = build_style_performance_arc_live_transition_timeline_report(
        description="King's Hall Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=45,
        segment_minutes=15,
    )
    assert "--description 'King''s Hall Jeff Mills Oscar Mulero tunnel'" in (
        apostrophe_report.suggested_commands[0]
    )
    assert "--description 'King''s Hall Jeff Mills Oscar Mulero tunnel'" in (
        apostrophe_report.transition_cards[0].passive_command
    )

    base_cue = show_export.cue_steps[0]
    go_export = replace(
        show_export,
        machine_exports=(),
        cue_steps=(
            replace(
                base_cue,
                go_no_go="go",
                blocker_summary="none",
                event_preview_rows=("row one", "row two"),
            ),
        ),
    )
    go_report = build_style_performance_arc_live_transition_timeline_from_export(go_export)
    go_card = go_report.transition_cards[0]
    assert go_card.phase == "launch"
    assert go_card.hold_action.startswith("Hold the groove")
    assert go_card.machine_handoff == "none"
    assert "Resolve blockers" not in "\n".join(go_card.prep_actions)
    assert "Transition event preview:" not in "\n".join(
        format_style_performance_arc_live_transition_timeline_report(go_report)
    )
    limited_text = "\n".join(
        format_style_performance_arc_live_transition_timeline_report(
            go_report,
            include_events=True,
            event_limit=1,
        )
    )
    assert "Showing first 1 of 2" in limited_text

    blocked_export = replace(
        show_export,
        cue_steps=(
            replace(
                base_cue,
                go_no_go="do-not-arm",
                blocker_summary="A4 offsets are deferred",
                event_preview_rows=(),
            ),
        ),
    )
    blocked_report = build_style_performance_arc_live_transition_timeline_from_export(
        blocked_export
    )
    blocked_card = blocked_report.transition_cards[0]
    assert blocked_card.phase == "rescue"
    assert blocked_card.hold_action.startswith("Hold current machine state")
    assert any("Resolve blockers" in action for action in blocked_card.prep_actions)
    no_rows_text = "\n".join(
        format_style_performance_arc_live_transition_timeline_report(
            blocked_report,
            include_events=True,
        )
    )
    assert "No mock rows available" in no_rows_text

    review_export = replace(
        show_export,
        cue_steps=(replace(base_cue, go_no_go="manual-review"),),
    )
    review_report = build_style_performance_arc_live_transition_timeline_from_export(review_export)
    assert review_report.transition_cards[0].phase == "review"
    assert "manual-review" in review_report.transition_cards[0].hold_action

    from rytm_randomizer.style_analysis import FeatureReport, compute_feature_report_hash
    from rytm_randomizer.style_analysis.feature_report import Confidence, SourceType

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
        derived_at="2026-05-22T12:00:00Z",
    )
    feature_report = replace(
        feature_report,
        content_hash=compute_feature_report_hash(feature_report),
    )
    feature_timeline = build_style_performance_arc_live_transition_timeline_report(
        feature_report=feature_report,
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert feature_timeline.selection_source == "feature-report"
    assert f"--arc {feature_timeline.selected_arc_key}" in feature_timeline.suggested_commands[0]

    text = "\n".join(
        format_style_performance_arc_live_transition_timeline_report(
            report,
            include_events=True,
            event_limit=1,
        )
    )
    assert "RytmRandomizer passive style performance arc live transition timeline" in text
    assert "Transition timeline summary:" in text
    assert "Transition cards:" in text
    assert "Operator timeline:" in text
    assert "Rehearsal loop:" in text
    assert "Transition event preview:" in text
    assert "- live transition timeline only" in text
    assert "- no MIDI sending" in text
    assert "- no port opening" in text

    payload = to_style_performance_arc_live_transition_timeline_json(report)
    timeline_payload = payload["live_transition_timeline"]
    assert timeline_payload["timeline_version"] == "live-transition-timeline-v1"
    assert timeline_payload["timeline_id"] == report.timeline_id
    assert timeline_payload["selected_arc_key"] == "mills_mulero_tunnel"
    assert timeline_payload["transition_cards"][0]["phase"] == "soundcheck"
    assert payload["live_show_export"]["export_id"] == show_export.export_id
    assert payload["safety"][-1] == "no hardware required"


def test_style_performance_arc_live_transition_timeline_parser_cli_and_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.live_transition_timeline import (
        _format_cli_error,
        _handle_cli_report,
        _parse_cli_args,
        _transition_phase,
        build_style_performance_arc_live_transition_timeline_report,
        format_style_performance_arc_live_transition_timeline_report,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)

    assert _transition_phase("go") == "launch"
    assert _transition_phase("rehearse") == "soundcheck"
    assert _transition_phase("do-not-arm") == "rescue"
    assert _transition_phase("custom") == "review"
    parsed = _parse_cli_args(
        [
            "--arc",
            "jose_warehouse_five_hour",
            "--rytm",
            "rytm.syx",
            "--analog-four",
            "a4.syx",
            "--scope",
            "a4-only",
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
            "0",
            "--json",
        ]
    )
    assert parsed == {
        "arc_key": "jose_warehouse_five_hour",
        "description": None,
        "audio_path": None,
        "library_path": None,
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "analog-four-only",
        "selection_rank": 2,
        "total_minutes": 120,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 80,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }
    assert _parse_cli_args(["--audio", "track.wav"])["audio_path"] == Path("track.wav")
    assert _parse_cli_args(["--library", "library-root"])["library_path"] == Path("library-root")
    for argv, message in (
        ([], "usage"),
        (["--arc"], "usage"),
        (["--arc", "x", "--bogus"], "usage"),
        (["--arc", "x", "--limit", "oops"], "must be an integer"),
        (["--arc", "x", "--limit", "-1"], ">= 0"),
        (["--arc", "x", "--rank", "0"], ">= 1"),
        (["--arc", "x", "--description", "Jeff Mills"], "usage"),
    ):
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    report = build_style_performance_arc_live_transition_timeline_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=30,
        segment_minutes=15,
    )
    assert "Showing all events" in "\n".join(
        format_style_performance_arc_live_transition_timeline_report(
            report,
            include_events=True,
            event_limit=0,
        )
    )
    with pytest.raises(ValueError, match="event_limit"):
        format_style_performance_arc_live_transition_timeline_report(report, event_limit=-1)

    rc = _handle_cli_report(
        arc_key=None,
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
    assert "RytmRandomizer passive style performance arc live transition timeline" in captured.out
    assert "Transition timeline summary:" in captured.out
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
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
        include_events=False,
        event_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["live_transition_timeline"]["selected_arc_key"] == "mills_mulero_tunnel"
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
        description=None,
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
    assert "live transition timeline requires exactly one selection source" in captured.err
    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"


def test_style_performance_arc_live_command_deck_builds_current_cue_packet(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_command_deck import (
        build_style_performance_arc_live_command_deck_from_timeline,
        build_style_performance_arc_live_command_deck_report,
        format_style_performance_arc_live_command_deck_report,
        to_style_performance_arc_live_command_deck_json,
    )
    from rytm_randomizer.reports.live_transition_timeline import (
        build_style_performance_arc_live_transition_timeline_report,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    timeline = build_style_performance_arc_live_transition_timeline_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=60,
        segment_minutes=15,
    )
    report = build_style_performance_arc_live_command_deck_from_timeline(
        timeline,
        cue_number=2,
        lookahead_count=2,
    )
    rebuilt = build_style_performance_arc_live_command_deck_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=60,
        segment_minutes=15,
        cue_number=2,
        lookahead_count=2,
    )

    assert report.deck_version == "live-command-deck-v1"
    assert report.deck_id == rebuilt.deck_id
    assert report.deck_id.startswith(timeline.timeline_id)
    assert report.timeline is timeline
    assert report.selected_arc_key == "mills_mulero_tunnel"
    assert report.current_cue_number == 2
    assert report.current_cue.cue_number == 2
    assert report.current_cue.source_transition_card is timeline.transition_cards[1]
    assert report.current_cue.command_state in {"perform", "soundcheck", "hold", "review"}
    assert report.current_cue.operator_prompt.startswith("Cue 2")
    assert report.current_cue.launch_sequence
    assert report.current_cue.recovery_action
    assert len(report.lookahead_cues) == 2
    assert report.lookahead_cues[0].cue_number == 3
    assert report.lookahead_cues[1].cue_number == 4
    assert report.launch_sequence[0].startswith("Confirm current cue")
    assert any("Rytm:" in row for row in report.machine_handoff)
    assert any("Cue 2" in row for row in report.recovery_controls)
    assert "style-performance-arc-live-command-deck-report" in report.suggested_commands[0]
    assert "--cue 2" in report.suggested_commands[0]
    assert "--lookahead 2" in report.suggested_commands[0]

    text = "\n".join(
        format_style_performance_arc_live_command_deck_report(
            report,
            include_events=True,
            event_limit=1,
        )
    )
    assert "RytmRandomizer passive style performance arc live command deck" in text
    assert "Command deck summary:" in text
    assert "Now cue:" in text
    assert "Lookahead cues:" in text
    assert "Launch sequence:" in text
    assert "Machine handoff:" in text
    assert "Recovery controls:" in text
    assert "Cue event preview:" in text
    assert "Replayable passive commands:" in text
    assert "- live command deck only" in text
    assert "- no MIDI sending" in text
    assert "- no port opening" in text

    payload = to_style_performance_arc_live_command_deck_json(report)
    deck_payload = payload["live_command_deck"]
    assert deck_payload["deck_version"] == "live-command-deck-v1"
    assert deck_payload["deck_id"] == report.deck_id
    assert deck_payload["selected_arc_key"] == "mills_mulero_tunnel"
    assert deck_payload["current_cue"]["cue_number"] == 2
    assert deck_payload["current_cue"]["source_transition_number"] == 2
    assert deck_payload["lookahead_cues"][0]["cue_number"] == 3
    assert payload["live_transition_timeline"]["timeline_id"] == timeline.timeline_id
    assert payload["live_show_export"]["export_id"] == timeline.live_show_export.export_id
    assert payload["safety"][-1] == "no hardware required"


def test_style_performance_arc_live_command_deck_parser_cli_and_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.live_command_deck import (
        _cue_lines,
        _format_cli_error,
        _handle_cli_report,
        _operator_prompt,
        _parse_cli_args,
        _source_option,
        _to_command_state,
        build_style_performance_arc_live_command_deck_from_timeline,
        build_style_performance_arc_live_command_deck_report,
        format_style_performance_arc_live_command_deck_report,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)

    assert _to_command_state("go") == "perform"
    assert _to_command_state("rehearse") == "soundcheck"
    assert _to_command_state("do-not-arm") == "hold"
    assert _to_command_state("custom") == "review"
    cue_marker = SimpleNamespace(cue_number=7)
    assert _operator_prompt(cue_marker, "perform").startswith("Cue 7 is green")
    assert _operator_prompt(cue_marker, "hold").startswith("Cue 7 is red")
    assert _operator_prompt(cue_marker, "review").startswith("Cue 7 needs review")
    assert (
        _source_option(
            SimpleNamespace(
                selection_source="feature-report",
                source_reference=None,
                selected_arc_key="fallback_arc",
            )
        )
        == "--arc fallback_arc"
    )
    parsed = _parse_cli_args(
        [
            "--arc",
            "jose_warehouse_five_hour",
            "--rytm",
            "rytm.syx",
            "--analog-four",
            "a4.syx",
            "--scope",
            "a4-only",
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
            "--cue",
            "2",
            "--lookahead",
            "3",
            "--events",
            "--limit",
            "0",
            "--json",
        ]
    )
    assert parsed == {
        "arc_key": "jose_warehouse_five_hour",
        "description": None,
        "audio_path": None,
        "library_path": None,
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "analog-four-only",
        "selection_rank": 2,
        "total_minutes": 120,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 80,
        "cue_number": 2,
        "lookahead_count": 3,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }
    assert _parse_cli_args(["--audio", "track.wav"])["audio_path"] == Path("track.wav")
    assert _parse_cli_args(["--library", "library-root"])["library_path"] == Path("library-root")
    for argv, message in (
        ([], "usage"),
        (["--arc"], "usage"),
        (["--arc", "x", "--bogus"], "usage"),
        (["--arc", "x", "--limit", "oops"], "must be an integer"),
        (["--arc", "x", "--limit", "-1"], ">= 0"),
        (["--arc", "x", "--rank", "0"], ">= 1"),
        (["--arc", "x", "--cue", "0"], ">= 1"),
        (["--arc", "x", "--lookahead", "-1"], ">= 0"),
        (["--arc", "x", "--description", "Jeff Mills"], "usage"),
    ):
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    report = build_style_performance_arc_live_command_deck_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=30,
        segment_minutes=15,
        cue_number=1,
        lookahead_count=0,
    )
    assert report.lookahead_cues == ()
    assert "No lookahead cues requested." in "\n".join(
        format_style_performance_arc_live_command_deck_report(report)
    )
    assert "Showing all events" in "\n".join(
        format_style_performance_arc_live_command_deck_report(
            report,
            include_events=True,
            event_limit=0,
        )
    )
    with pytest.raises(ValueError, match="cue must be between 1 and"):
        build_style_performance_arc_live_command_deck_report(
            description="Jeff Mills Oscar Mulero tunnel",
            rytm_sysex_path=rytm_path,
            analog_four_sysex_path=a4_path,
            total_minutes=30,
            segment_minutes=15,
            cue_number=99,
        )
    with pytest.raises(ValueError, match="lookahead_count"):
        build_style_performance_arc_live_command_deck_from_timeline(
            report.timeline,
            lookahead_count=-1,
        )
    with pytest.raises(ValueError, match="event_limit"):
        format_style_performance_arc_live_command_deck_report(report, event_limit=-1)
    cue_without_events = replace(report.current_cue, event_preview_rows=())
    assert "No mock rows available" in "\n".join(
        _cue_lines(cue_without_events, include_events=True, event_limit=1)
    )

    rc = _handle_cli_report(
        arc_key=None,
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
        cue_number=1,
        lookahead_count=1,
        include_events=True,
        event_limit=1,
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive style performance arc live command deck" in captured.out
    assert "Command deck summary:" in captured.out
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
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
        cue_number=1,
        lookahead_count=1,
        include_events=False,
        event_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["live_command_deck"]["selected_arc_key"] == "mills_mulero_tunnel"
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
        description=None,
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
        cue_number=1,
        lookahead_count=1,
        include_events=False,
        event_limit=1,
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "live command deck requires exactly one selection source" in captured.err
    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"


def test_style_performance_arc_live_state_packet_builds_gui_ready_state(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_command_deck import (
        build_style_performance_arc_live_command_deck_report,
    )
    from rytm_randomizer.reports.live_performance_state import (
        STATE_PACKET_VERSION,
        build_style_performance_arc_live_state_from_command_deck,
        build_style_performance_arc_live_state_report,
        format_style_performance_arc_live_state_report,
        to_style_performance_arc_live_state_json,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    command_deck = build_style_performance_arc_live_command_deck_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=60,
        segment_minutes=15,
        cue_number=2,
        lookahead_count=2,
    )
    state = build_style_performance_arc_live_state_from_command_deck(command_deck)
    rebuilt = build_style_performance_arc_live_state_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=60,
        segment_minutes=15,
        cue_number=2,
        lookahead_count=2,
    )

    assert state.state_version == STATE_PACKET_VERSION
    assert state.state_id == rebuilt.state_id
    assert state.state_id.startswith(command_deck.deck_id)
    assert state.command_deck is command_deck
    assert state.screen_title == "Cue 2 live state"
    assert state.screen_mode == command_deck.operator_mode
    assert state.live_state in {"ready", "rehearsal", "blocked", "review"}
    assert state.current_cue.cue_number == 2
    assert state.current_cue.screen_state == state.screen_mode
    assert state.current_cue.primary_action.startswith("Launch:")
    assert state.current_cue.secondary_action.startswith("Hold:")
    assert state.current_cue.warning_text
    assert len(state.next_cues) == 2
    assert state.next_cues[0].cue_number == 3
    assert state.next_cues[1].cue_number == 4
    assert {machine.machine for machine in state.machine_states} == {"rytm", "analog-four"}
    assert all(machine.ui_badge for machine in state.machine_states)
    assert any("Rytm" in machine.handoff_label for machine in state.machine_states)
    assert any("Analog Four" in machine.handoff_label for machine in state.machine_states)
    assert state.action_bar[0].startswith("Now:")
    assert any("Machine:" in action for action in state.action_bar)
    assert any("Recovery:" in recovery for recovery in state.recovery_stack)
    assert any(
        "style-performance-arc-live-state-report" in command for command in state.replay_commands
    )
    assert "style-performance-arc-live-state-report" in state.suggested_commands[0]

    text = "\n".join(
        format_style_performance_arc_live_state_report(
            state,
            include_events=True,
            event_limit=1,
        )
    )
    assert "RytmRandomizer passive style performance arc live state packet" in text
    assert "Live state summary:" in text
    assert "Current GUI state:" in text
    assert "Next cue strip:" in text
    assert "Machine state panels:" in text
    assert "Action bar:" in text
    assert "Warning stack:" in text
    assert "Recovery stack:" in text
    assert "Replayable passive commands:" in text
    assert "Cue event preview:" in text
    assert "- live state packet only" in text
    assert "- no MIDI sending" in text
    assert "- no port opening" in text

    payload = to_style_performance_arc_live_state_json(state)
    state_payload = payload["live_state_packet"]
    assert state_payload["state_version"] == STATE_PACKET_VERSION
    assert state_payload["state_id"] == state.state_id
    assert state_payload["screen_title"] == "Cue 2 live state"
    assert state_payload["current_cue"]["cue_number"] == 2
    assert state_payload["next_cues"][0]["cue_number"] == 3
    assert state_payload["machine_states"][0]["machine"] in {"rytm", "analog-four"}
    assert payload["live_command_deck"]["deck_id"] == command_deck.deck_id
    assert payload["live_transition_timeline"]["timeline_id"] == command_deck.timeline.timeline_id
    assert payload["safety"][-1] == "no hardware required"


def test_style_performance_arc_live_state_packet_parser_cli_and_edges(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.live_performance_state import (
        _format_cli_error,
        _handle_cli_report,
        _parse_cli_args,
        build_style_performance_arc_live_state_from_command_deck,
        build_style_performance_arc_live_state_report,
        format_style_performance_arc_live_state_report,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    parsed = _parse_cli_args(
        [
            "--arc",
            "jose_warehouse_five_hour",
            "--rytm",
            "rytm.syx",
            "--analog-four",
            "a4.syx",
            "--scope",
            "a4-only",
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
            "--cue",
            "2",
            "--lookahead",
            "3",
            "--events",
            "--limit",
            "0",
            "--json",
        ]
    )
    assert parsed == {
        "arc_key": "jose_warehouse_five_hour",
        "description": None,
        "audio_path": None,
        "library_path": None,
        "rytm_sysex_path": Path("rytm.syx"),
        "analog_four_sysex_path": Path("a4.syx"),
        "scope": "analog-four-only",
        "selection_rank": 2,
        "total_minutes": 120,
        "segment_minutes": 30,
        "discovery_start": 25,
        "discovery_end": 80,
        "cue_number": 2,
        "lookahead_count": 3,
        "include_events": True,
        "event_limit": 0,
        "json_output": True,
    }
    assert _parse_cli_args(["--audio", "track.wav"])["audio_path"] == Path("track.wav")
    assert _parse_cli_args(["--library", "library-root"])["library_path"] == Path("library-root")
    for argv, message in (
        ([], "usage"),
        (["--arc"], "usage"),
        (["--arc", "x", "--bogus"], "usage"),
        (["--arc", "x", "--limit", "oops"], "must be an integer"),
        (["--arc", "x", "--limit", "-1"], ">= 0"),
        (["--arc", "x", "--rank", "0"], ">= 1"),
        (["--arc", "x", "--cue", "0"], ">= 1"),
        (["--arc", "x", "--lookahead", "-1"], ">= 0"),
        (["--arc", "x", "--description", "Jeff Mills"], "usage"),
    ):
        with pytest.raises(ValueError, match=message):
            _parse_cli_args(argv)

    state = build_style_performance_arc_live_state_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=30,
        segment_minutes=15,
        cue_number=1,
        lookahead_count=0,
    )
    assert state.next_cues == ()
    assert "No next cues requested." in "\n".join(
        format_style_performance_arc_live_state_report(state)
    )
    assert "Showing all events" in "\n".join(
        format_style_performance_arc_live_state_report(
            state,
            include_events=True,
            event_limit=0,
        )
    )
    with pytest.raises(ValueError, match="event_limit"):
        format_style_performance_arc_live_state_report(state, event_limit=-1)
    with pytest.raises(ValueError, match="cue must be between 1 and"):
        build_style_performance_arc_live_state_report(
            description="Jeff Mills Oscar Mulero tunnel",
            rytm_sysex_path=rytm_path,
            analog_four_sysex_path=a4_path,
            total_minutes=30,
            segment_minutes=15,
            cue_number=99,
        )
    with pytest.raises(ValueError, match="live state packet requires"):
        build_style_performance_arc_live_state_report()
    rebuilt_from_zero_lookahead = build_style_performance_arc_live_state_from_command_deck(
        state.command_deck
    )
    assert rebuilt_from_zero_lookahead.next_cues == ()

    rc = _handle_cli_report(
        arc_key=None,
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
        cue_number=1,
        lookahead_count=1,
        include_events=True,
        event_limit=1,
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive style performance arc live state packet" in captured.out
    assert "Live state summary:" in captured.out
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
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
        cue_number=1,
        lookahead_count=1,
        include_events=False,
        event_limit=0,
        json_output=True,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["live_state_packet"]["selected_arc_key"] == "mills_mulero_tunnel"
    assert captured.err == ""

    rc = _handle_cli_report(
        arc_key=None,
        description=None,
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
        cue_number=1,
        lookahead_count=1,
        include_events=False,
        event_limit=1,
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "live state packet requires exactly one selection source" in captured.err
    assert _format_cli_error(ValueError("bad input")) == "Error: bad input"


def test_style_performance_arc_live_state_packet_formatting_edges(
    tmp_path: Path,
):
    from rytm_randomizer.reports.live_command_deck import (
        build_style_performance_arc_live_command_deck_report,
    )
    from rytm_randomizer.reports.live_performance_state import (
        _first_prefixed,
        _live_state,
        _source_option,
        _warning_stack,
        _warning_text,
        build_style_performance_arc_live_state_from_command_deck,
        build_style_performance_arc_live_state_report,
        format_style_performance_arc_live_state_report,
    )

    rytm_path, a4_path = _arc_bank_files(tmp_path)
    command_deck = build_style_performance_arc_live_command_deck_report(
        description="Jeff Mills Oscar Mulero tunnel",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=60,
        segment_minutes=15,
        cue_number=1,
        lookahead_count=1,
    )
    command_deck = replace(
        command_deck,
        current_cue=replace(
            command_deck.current_cue,
            launch_sequence=("Check transition",),
            command_state="hold",
            blocker_summary="Operator review needed",
            event_preview_rows=(),
        ),
        lookahead_cues=(
            replace(
                command_deck.lookahead_cues[0],
                command_state="perform",
                launch_sequence=("Check next cue",),
            ),
        ),
    )
    state = build_style_performance_arc_live_state_from_command_deck(command_deck)

    assert state.live_state == "blocked"
    assert state.current_cue.primary_action.startswith("Launch:")
    assert state.current_cue.secondary_action.startswith("Hold:")
    assert state.current_cue.warning_text.startswith("Red cue")
    assert any("Blockers: Operator review needed" in warning for warning in state.warning_stack)
    assert any(
        "Machine check" in warning
        for warning in _warning_stack(
            state.current_cue,
            (
                replace(
                    state.machine_states[0],
                    label="Machine check",
                    arm_state="rehearse",
                ),
            ),
        )
    )

    text = "\n".join(
        format_style_performance_arc_live_state_report(
            state,
            include_events=True,
            event_limit=2,
        )
    )
    assert "No mock rows available because the selected preview is not ready." in text

    empty_machine_state = replace(
        state,
        machine_states=(),
    )
    assert "No machine states available." in "\n".join(
        format_style_performance_arc_live_state_report(empty_machine_state)
    )

    no_units_state = replace(
        state,
        machine_states=(replace(state.machine_states[0], planned_units=()),),
    )
    assert "Planned units: none" in "\n".join(
        format_style_performance_arc_live_state_report(no_units_state)
    )

    assert _live_state("perform") == "ready"
    assert _live_state("soundcheck") == "rehearsal"
    assert _live_state("hold") == "blocked"
    assert _live_state("review-needed") == "review"
    assert _warning_text(SimpleNamespace(command_state="perform")).startswith("Green cue")
    assert _warning_text(SimpleNamespace(command_state="hold")).startswith("Red cue")
    assert _warning_text(SimpleNamespace(command_state="unknown")).startswith("Review cue")
    assert _first_prefixed(("Prep:",), "Launch:", "Launch: fallback") == "Launch: fallback"
    assert (
        _source_option(SimpleNamespace(selection_source="feature", selected_arc_key="arc-key"))
        == "--arc arc-key"
    )
    assert _warning_stack(
        replace(state.current_cue, blocker_summary="None"),
        (),
    ) == (state.current_cue.warning_text,)

    arc_state = build_style_performance_arc_live_state_report(
        arc_key="jose_warehouse_five_hour",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
        total_minutes=60,
        segment_minutes=15,
    )
    assert "--arc jose_warehouse_five_hour" in arc_state.replay_commands[0]


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
    assert report.stage_packet is None
    assert "Reference-selected snapshot preview: none" in "\n".join(
        format_style_performance_arc_reference_match_report(report)
    )
    payload = to_style_performance_arc_reference_match_json(report)
    assert payload["reference_match"]["snapshot_preview"] is None
    assert payload["reference_match"]["stage_packet"] is None


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

    assert (
        main(
            [
                "style-performance-arc-live-runbook-report",
                "--description",
                "Jeff Mills Oscar Mulero tunnel",
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
    assert "RytmRandomizer passive style performance arc live runbook" in captured.out
    assert "mills_mulero_tunnel" in captured.out
    assert "Launch brief:" in captured.out
    assert "Timeline cards:" in captured.out
    assert "Stage packet:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-stage-routing-report",
                "--description",
                "Jeff Mills Oscar Mulero tunnel",
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
    assert "RytmRandomizer passive style performance arc stage snapshot routing" in captured.out
    assert "mills_mulero_tunnel" in captured.out
    assert "Live set card:" in captured.out
    assert "Route cards:" in captured.out
    assert "A4 deferred/candidate rows:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-stage-rehearsal-state-report",
                "--description",
                "Jeff Mills Oscar Mulero tunnel",
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
    assert "RytmRandomizer passive style performance arc stage rehearsal state" in captured.out
    assert "mills_mulero_tunnel" in captured.out
    assert "Stage rehearsal summary:" in captured.out
    assert "Machine states:" in captured.out
    assert "Cue states:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-live-set-cockpit-report",
                "--description",
                "Jeff Mills Oscar Mulero tunnel",
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
    assert "RytmRandomizer passive style performance arc live set cockpit" in captured.out
    assert "mills_mulero_tunnel" in captured.out
    assert "Cockpit summary:" in captured.out
    assert "Cue cockpit cards:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-live-show-export-report",
                "--description",
                "Jeff Mills Oscar Mulero tunnel",
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
    assert "RytmRandomizer passive style performance arc live show export" in captured.out
    assert "mills_mulero_tunnel" in captured.out
    assert "Show export summary:" in captured.out
    assert "Cue launch script:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-live-transition-timeline-report",
                "--description",
                "Jeff Mills Oscar Mulero tunnel",
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
    assert "RytmRandomizer passive style performance arc live transition timeline" in (captured.out)
    assert "mills_mulero_tunnel" in captured.out
    assert "Transition timeline summary:" in captured.out
    assert "Transition cards:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-live-command-deck-report",
                "--description",
                "Jeff Mills Oscar Mulero tunnel",
                "--rytm",
                str(rytm_path),
                "--analog-four",
                str(a4_path),
                "--cue",
                "2",
                "--lookahead",
                "1",
                "--events",
                "--limit",
                "1",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc live command deck" in captured.out
    assert "mills_mulero_tunnel" in captured.out
    assert "Command deck summary:" in captured.out
    assert "Now cue:" in captured.out

    assert (
        main(
            [
                "style-performance-arc-live-state-report",
                "--description",
                "Jeff Mills Oscar Mulero tunnel",
                "--rytm",
                str(rytm_path),
                "--analog-four",
                str(a4_path),
                "--cue",
                "2",
                "--lookahead",
                "1",
                "--events",
                "--limit",
                "1",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc live state packet" in captured.out
    assert "mills_mulero_tunnel" in captured.out
    assert "Live state summary:" in captured.out
    assert "Current GUI state:" in captured.out

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
                "2",
                "--lookahead",
                "1",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style performance arc live readiness" in captured.out
    assert "mills_mulero_tunnel" in captured.out
    assert "Readiness summary:" in captured.out
    assert "Audio analyzer handoff:" in captured.out

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
    assert "style-performance-arc-live-runbook-report" in help_text
    assert "style-performance-arc-stage-routing-report" in help_text
    assert "style-performance-arc-stage-rehearsal-state-report" in help_text
    assert "style-performance-arc-live-set-cockpit-report" in help_text
    assert "style-performance-arc-live-show-export-report" in help_text
    assert "style-performance-arc-live-transition-timeline-report" in help_text
    assert "style-performance-arc-live-command-deck-report" in help_text
    assert "style-performance-arc-live-state-report" in help_text
    assert "style-performance-arc-live-readiness-report" in help_text
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
    assert (
        "style-performance-arc-live-cue-sheet-report --analog-four <syx-path> "
        "--scope analog-four-only"
    ) in live_cue_help
    reference_match_help = resolve_help_text("style-performance-arc-reference-match-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-reference-match-report" in (
        reference_match_help
    )
    assert "Matches a reference description or FeatureReport to performance arcs." in (
        reference_match_help
    )
    assert "stage packet with compact cue cards" in reference_match_help
    live_runbook_help = resolve_help_text("style-performance-arc-live-runbook-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-live-runbook-report" in (
        live_runbook_help
    )
    assert "Builds a passive live performance runbook from an arc or reference." in (
        live_runbook_help
    )
    assert "--arc <arc-key>|--description <text>|--audio <path>|--library <dir>" in (
        live_runbook_help
    )
    stage_routing_help = resolve_help_text("style-performance-arc-stage-routing-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-stage-routing-report" in (
        stage_routing_help
    )
    assert "Builds passive stage snapshot routing from an arc or reference." in (stage_routing_help)
    assert "route cards" in stage_routing_help
    assert "--arc <arc-key>|--description <text>|--audio <path>|--library <dir>" in (
        stage_routing_help
    )
    stage_rehearsal_help = resolve_help_text("style-performance-arc-stage-rehearsal-state-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-stage-rehearsal-state-report" in (
        stage_rehearsal_help
    )
    assert "Builds passive stage rehearsal state from an arc or reference." in (
        stage_rehearsal_help
    )
    assert "go/rehearse/do-not-arm cue states" in stage_rehearsal_help
    assert "--arc <arc-key>|--description <text>|--audio <path>|--library <dir>" in (
        stage_rehearsal_help
    )
    live_set_cockpit_help = resolve_help_text("style-performance-arc-live-set-cockpit-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-live-set-cockpit-report" in (
        live_set_cockpit_help
    )
    assert "Builds a passive live set cockpit from an arc or reference." in (live_set_cockpit_help)
    assert "Cue cockpit cards" in live_set_cockpit_help
    assert "--arc <arc-key>|--description <text>|--audio <path>|--library <dir>" in (
        live_set_cockpit_help
    )
    live_show_export_help = resolve_help_text("style-performance-arc-live-show-export-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-live-show-export-report" in (
        live_show_export_help
    )
    assert "Builds a passive live show export packet from an arc or reference." in (
        live_show_export_help
    )
    assert "machine handoff manifest" in live_show_export_help
    assert "--arc <arc-key>|--description <text>|--audio <path>|--library <dir>" in (
        live_show_export_help
    )
    live_transition_timeline_help = resolve_help_text(
        "style-performance-arc-live-transition-timeline-report"
    )
    assert (
        "RytmRandomizer passive CLI: style-performance-arc-live-transition-timeline-report"
        in live_transition_timeline_help
    )
    assert "Builds a passive live transition timeline from an arc or reference." in (
        live_transition_timeline_help
    )
    assert "operator-facing transition cards" in live_transition_timeline_help
    assert "--arc <arc-key>|--description <text>|--audio <path>|--library <dir>" in (
        live_transition_timeline_help
    )
    live_command_deck_help = resolve_help_text("style-performance-arc-live-command-deck-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-live-command-deck-report" in (
        live_command_deck_help
    )
    live_state_help = resolve_help_text("style-performance-arc-live-state-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-live-state-report" in (
        live_state_help
    )
    assert "Builds a passive live performance state packet" in live_state_help
    assert "GUI-ready" in live_state_help
    assert "--cue N --lookahead N" in live_state_help
    assert "no MIDI sending" in live_state_help
    live_readiness_help = resolve_help_text("style-performance-arc-live-readiness-report")
    assert "RytmRandomizer passive CLI: style-performance-arc-live-readiness-report" in (
        live_readiness_help
    )
    assert "GUI/audio-analyzer readiness" in live_readiness_help
    assert "audio analyzer preview only" in live_readiness_help
    assert "--cue N --lookahead N" in live_readiness_help
    assert "no MIDI sending" in live_readiness_help
    assert "Builds a passive live command deck from an arc or reference." in (
        live_command_deck_help
    )
    assert "command cards" in live_command_deck_help
    assert "--arc <arc-key>|--description <text>|--audio <path>|--library <dir>" in (
        live_command_deck_help
    )
