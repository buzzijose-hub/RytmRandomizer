"""Passive reference performance arc reports for long-form techno planning.

This module is now a thin re-export facade. PR 11 (CODE_REVIEW.md) split
the original 4,759-line implementation into focused sibling modules
under :mod:`rytm_randomizer.reports.style_performance`. Every public
symbol that used to live here is re-exported below so external imports
keep working unchanged; this includes report dataclasses, builder /
formatter / JSON functions, safety constants, titles, and the registered
:class:`~rytm_randomizer.cli_registry.CliCommand` constants.

``SOURCE_MODULE`` continues to be ``"reports.style_performance_arcs"`` so
on-disk fixtures (every passive report header carries this string),
operator-facing reports, and parity tests remain byte-stable. The split
is purely organizational.

Importing this facade triggers CLI registration exactly once via
:mod:`.style_performance.cli`. Re-importing the facade is safe (Python
caches the module) but never import :mod:`.style_performance.cli`
directly from a second location — :func:`cli_registry.register` raises
on duplicate registration by design.

The facade also re-exports a number of underscore-prefixed dispatchers,
parsers, and helper functions because the regression test suite
(``tests/test_style_performance_arcs_report.py``) imports them by name
to exercise individual code paths. These re-exports are part of the
in-repo testing surface, not a public API.
"""

from __future__ import annotations

# Public re-exports — constants, dataclasses, builders, formatters,
# JSON converters, and registered CliCommand instances.
from .style_performance import (
    AUDITION_PACKET_SAFETY_LINES,
    AUDITION_PACKET_TITLE,
    INSPECT_STYLE_PERFORMANCE_ARC_CLI_COMMAND,
    INSPECT_TITLE,
    LIST_STYLE_PERFORMANCE_ARCS_CLI_COMMAND,
    LIST_TITLE,
    LIVE_CUE_SHEET_SAFETY_LINES,
    LIVE_CUE_SHEET_TITLE,
    LIVE_RENDER_BUNDLE_SAFETY_LINES,
    LIVE_RENDER_BUNDLE_TITLE,
    LIVE_SESSION_PACKET_SAFETY_LINES,
    LIVE_SESSION_PACKET_TITLE,
    READINESS_TITLE,
    REFERENCE_MATCH_SAFETY_LINES,
    REFERENCE_MATCH_TITLE,
    REHEARSAL_MANIFEST_SAFETY_LINES,
    REHEARSAL_MANIFEST_TITLE,
    REPORT_TITLE,
    SAFETY_LINES,
    SEARCH_STYLE_PERFORMANCE_ARCS_CLI_COMMAND,
    SEARCH_TITLE,
    SET_PLAN_TITLE,
    SOURCE_MODULE,
    STYLE_PERFORMANCE_ARC_AUDITION_PACKET_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_LIVE_CUE_SHEET_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_LIVE_RENDER_BUNDLE_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_LIVE_SESSION_PACKET_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_READINESS_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_REFERENCE_MATCH_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_REHEARSAL_MANIFEST_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_REPORT_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_SET_PLAN_CLI_COMMAND,
    StylePerformanceArcAuditionPacketReport,
    StylePerformanceArcCatalogReport,
    StylePerformanceArcLiveCue,
    StylePerformanceArcLiveCueSheetReport,
    StylePerformanceArcLiveRenderBundleReport,
    StylePerformanceArcLiveRenderSegment,
    StylePerformanceArcLiveSessionPacketReport,
    StylePerformanceArcLiveSessionSegment,
    StylePerformanceArcReadinessEntry,
    StylePerformanceArcReadinessReport,
    StylePerformanceArcReferenceMatchEntry,
    StylePerformanceArcReferenceMatchReport,
    StylePerformanceArcReferenceSnapshotPreview,
    StylePerformanceArcRehearsalManifestReport,
    StylePerformanceArcRehearsalSegment,
    StylePerformanceArcSetPlanReport,
    StylePerformanceArcStageCard,
    StylePerformanceArcStagePacket,
    build_style_performance_arc_audition_packet_report,
    build_style_performance_arc_catalog_report,
    build_style_performance_arc_live_cue_sheet_report,
    build_style_performance_arc_live_render_bundle_report,
    build_style_performance_arc_live_session_packet_report,
    build_style_performance_arc_readiness_report,
    build_style_performance_arc_reference_match_report,
    build_style_performance_arc_rehearsal_manifest_report,
    build_style_performance_arc_set_plan_report,
    format_style_performance_arc_audition_packet_report,
    format_style_performance_arc_inspection,
    format_style_performance_arc_list,
    format_style_performance_arc_live_cue_sheet_report,
    format_style_performance_arc_live_render_bundle_report,
    format_style_performance_arc_live_session_packet_report,
    format_style_performance_arc_readiness_report,
    format_style_performance_arc_reference_match_report,
    format_style_performance_arc_rehearsal_manifest_report,
    format_style_performance_arc_report,
    format_style_performance_arc_search,
    format_style_performance_arc_set_plan_report,
    to_style_performance_arc_audition_packet_json,
    to_style_performance_arc_json,
    to_style_performance_arc_live_cue_sheet_json,
    to_style_performance_arc_live_render_bundle_json,
    to_style_performance_arc_live_session_packet_json,
    to_style_performance_arc_readiness_json,
    to_style_performance_arc_reference_match_json,
    to_style_performance_arc_rehearsal_manifest_json,
    to_style_performance_arc_set_plan_json,
)

# Private re-exports — CLI parsers, dispatchers, and a handful of
# concern-module helpers exercised directly by the regression test
# suite ``tests/test_style_performance_arcs_report.py``. Names starting
# with an underscore are NOT part of the public API; they are
# in-repo testing affordances. New code should not import these.
from .style_performance.cli import (  # noqa: F401
    _format_cli_error,
    _handle_style_performance_arc_audition_packet_report,
    _handle_style_performance_arc_live_cue_sheet_report,
    _handle_style_performance_arc_live_render_bundle_report,
    _handle_style_performance_arc_live_session_packet_report,
    _handle_style_performance_arc_readiness_report,
    _handle_style_performance_arc_reference_match_report,
    _handle_style_performance_arc_rehearsal_manifest_report,
    _handle_style_performance_arc_set_plan_report,
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
from .style_performance.live_cue_sheet import (  # noqa: F401
    _live_cue_from_segment,
    _live_cue_lines,
)
from .style_performance.readiness import (  # noqa: F401
    _readiness_entry_from_set_plan,
)
from .style_performance.reference_match import (  # noqa: F401
    _axis_scores_from_feature_report,
    _bounded_int,
    _reference_snapshot_preview_from_cue_sheet,
    _reference_snapshot_preview_lines,
    _reference_snapshot_preview_operator_action,
    _reference_snapshot_preview_readiness,
)

__all__ = [
    "AUDITION_PACKET_SAFETY_LINES",
    "AUDITION_PACKET_TITLE",
    "INSPECT_STYLE_PERFORMANCE_ARC_CLI_COMMAND",
    "INSPECT_TITLE",
    "LIST_STYLE_PERFORMANCE_ARCS_CLI_COMMAND",
    "LIST_TITLE",
    "LIVE_CUE_SHEET_SAFETY_LINES",
    "LIVE_CUE_SHEET_TITLE",
    "LIVE_RENDER_BUNDLE_SAFETY_LINES",
    "LIVE_RENDER_BUNDLE_TITLE",
    "LIVE_SESSION_PACKET_SAFETY_LINES",
    "LIVE_SESSION_PACKET_TITLE",
    "READINESS_TITLE",
    "REFERENCE_MATCH_SAFETY_LINES",
    "REFERENCE_MATCH_TITLE",
    "REHEARSAL_MANIFEST_SAFETY_LINES",
    "REHEARSAL_MANIFEST_TITLE",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SEARCH_STYLE_PERFORMANCE_ARCS_CLI_COMMAND",
    "SEARCH_TITLE",
    "SET_PLAN_TITLE",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_AUDITION_PACKET_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_LIVE_CUE_SHEET_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_LIVE_RENDER_BUNDLE_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_LIVE_SESSION_PACKET_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_REFERENCE_MATCH_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_REHEARSAL_MANIFEST_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_REPORT_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_READINESS_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_SET_PLAN_CLI_COMMAND",
    "StylePerformanceArcAuditionPacketReport",
    "StylePerformanceArcCatalogReport",
    "StylePerformanceArcLiveCue",
    "StylePerformanceArcLiveCueSheetReport",
    "StylePerformanceArcLiveRenderBundleReport",
    "StylePerformanceArcLiveRenderSegment",
    "StylePerformanceArcLiveSessionPacketReport",
    "StylePerformanceArcLiveSessionSegment",
    "StylePerformanceArcReferenceMatchEntry",
    "StylePerformanceArcReferenceMatchReport",
    "StylePerformanceArcReferenceSnapshotPreview",
    "StylePerformanceArcRehearsalManifestReport",
    "StylePerformanceArcRehearsalSegment",
    "StylePerformanceArcReadinessEntry",
    "StylePerformanceArcReadinessReport",
    "StylePerformanceArcSetPlanReport",
    "StylePerformanceArcStageCard",
    "StylePerformanceArcStagePacket",
    "build_style_performance_arc_audition_packet_report",
    "build_style_performance_arc_catalog_report",
    "build_style_performance_arc_live_cue_sheet_report",
    "build_style_performance_arc_live_session_packet_report",
    "build_style_performance_arc_live_render_bundle_report",
    "build_style_performance_arc_reference_match_report",
    "build_style_performance_arc_rehearsal_manifest_report",
    "build_style_performance_arc_readiness_report",
    "build_style_performance_arc_set_plan_report",
    "format_style_performance_arc_audition_packet_report",
    "format_style_performance_arc_live_cue_sheet_report",
    "format_style_performance_arc_live_session_packet_report",
    "format_style_performance_arc_live_render_bundle_report",
    "format_style_performance_arc_reference_match_report",
    "format_style_performance_arc_rehearsal_manifest_report",
    "format_style_performance_arc_readiness_report",
    "format_style_performance_arc_inspection",
    "format_style_performance_arc_list",
    "format_style_performance_arc_report",
    "format_style_performance_arc_search",
    "format_style_performance_arc_set_plan_report",
    "to_style_performance_arc_audition_packet_json",
    "to_style_performance_arc_json",
    "to_style_performance_arc_live_cue_sheet_json",
    "to_style_performance_arc_live_session_packet_json",
    "to_style_performance_arc_live_render_bundle_json",
    "to_style_performance_arc_reference_match_json",
    "to_style_performance_arc_rehearsal_manifest_json",
    "to_style_performance_arc_readiness_json",
    "to_style_performance_arc_set_plan_json",
]
