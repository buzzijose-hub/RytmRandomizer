"""Internal subpackage for passive style performance arc reports.

The 4,759-line ``rytm_randomizer/reports/style_performance_arcs.py``
module was split into focused sibling modules in PR 11 (CODE_REVIEW.md).
The public surface continues to live at
``rytm_randomizer.reports.style_performance_arcs`` — that module is the
thin facade. External code SHOULD prefer the facade, but importing
from this subpackage is also supported (we re-export every public
symbol below).

No semantic change: the split is purely organizational. Every function,
dataclass, constant, and CLI command keeps its original name; the
``SOURCE_MODULE`` reported in every passive report header continues to
be ``"reports.style_performance_arcs"`` so on-disk fixtures and operator
expectations remain stable.

Submodule responsibilities (dependency-ordered, bottom-up):

* ``_constants`` — titles, safety lines, USAGE strings, option tuples,
  shared headers, defaults.
* ``_helpers`` — small private helpers (``_join``, ``_safety_lines``,
  ``_arc_or_raise`` …) shared by concern modules.
* ``catalog`` — catalog / list / inspect / search / set plan.
* ``readiness`` — readiness matrix derived from set plans.
* ``audition_packet`` — best-arc audition packet derived from readiness.
* ``rehearsal_manifest`` — rehearsal runbook derived from audition packet.
* ``live_session_packet`` — live session packet derived from rehearsal manifest.
* ``live_render_bundle`` — segment-level mock-render bundle.
* ``live_cue_sheet`` — operator live cue sheet, stage cards, stage packet.
* ``reference_match`` — reference description/audio/library scoring against arcs.
* ``cli`` — CLI parsers, dispatchers, and command registrations.

Importing this subpackage (or the facade) triggers CLI registration
exactly once at program start. The registry is NOT idempotent, so
:mod:`.cli` must be imported from exactly one place — the facade
(``reports.style_performance_arcs``) and this ``__init__`` both import
it lazily via the ``from .cli import *``-style re-export of registered
``CliCommand`` constants.
"""

from __future__ import annotations

from ._constants import (
    AUDITION_PACKET_SAFETY_LINES,
    AUDITION_PACKET_TITLE,
    INSPECT_TITLE,
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
    SEARCH_TITLE,
    SET_PLAN_TITLE,
    SOURCE_MODULE,
)
from .audition_packet import (
    StylePerformanceArcAuditionPacketReport,
    build_style_performance_arc_audition_packet_report,
    format_style_performance_arc_audition_packet_report,
    to_style_performance_arc_audition_packet_json,
)
from .catalog import (
    StylePerformanceArcCatalogReport,
    StylePerformanceArcSetPlanReport,
    build_style_performance_arc_catalog_report,
    build_style_performance_arc_set_plan_report,
    format_style_performance_arc_inspection,
    format_style_performance_arc_list,
    format_style_performance_arc_report,
    format_style_performance_arc_search,
    format_style_performance_arc_set_plan_report,
    to_style_performance_arc_json,
    to_style_performance_arc_set_plan_json,
)
from .cli import (
    INSPECT_STYLE_PERFORMANCE_ARC_CLI_COMMAND,
    LIST_STYLE_PERFORMANCE_ARCS_CLI_COMMAND,
    SEARCH_STYLE_PERFORMANCE_ARCS_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_AUDITION_PACKET_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_LIVE_CUE_SHEET_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_LIVE_RENDER_BUNDLE_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_LIVE_SESSION_PACKET_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_READINESS_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_REFERENCE_MATCH_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_REHEARSAL_MANIFEST_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_REPORT_CLI_COMMAND,
    STYLE_PERFORMANCE_ARC_SET_PLAN_CLI_COMMAND,
)
from .live_cue_sheet import (
    StylePerformanceArcLiveCue,
    StylePerformanceArcLiveCueSheetReport,
    StylePerformanceArcStageCard,
    StylePerformanceArcStagePacket,
    build_style_performance_arc_live_cue_sheet_report,
    format_style_performance_arc_live_cue_sheet_report,
    to_style_performance_arc_live_cue_sheet_json,
)
from .live_render_bundle import (
    StylePerformanceArcLiveRenderBundleReport,
    StylePerformanceArcLiveRenderSegment,
    build_style_performance_arc_live_render_bundle_report,
    format_style_performance_arc_live_render_bundle_report,
    to_style_performance_arc_live_render_bundle_json,
)
from .live_session_packet import (
    StylePerformanceArcLiveSessionPacketReport,
    StylePerformanceArcLiveSessionSegment,
    build_style_performance_arc_live_session_packet_report,
    format_style_performance_arc_live_session_packet_report,
    to_style_performance_arc_live_session_packet_json,
)
from .readiness import (
    StylePerformanceArcReadinessEntry,
    StylePerformanceArcReadinessReport,
    build_style_performance_arc_readiness_report,
    format_style_performance_arc_readiness_report,
    to_style_performance_arc_readiness_json,
)
from .reference_match import (
    StylePerformanceArcReferenceMatchEntry,
    StylePerformanceArcReferenceMatchReport,
    StylePerformanceArcReferenceSnapshotPreview,
    build_style_performance_arc_reference_match_report,
    format_style_performance_arc_reference_match_report,
    to_style_performance_arc_reference_match_json,
)
from .rehearsal_manifest import (
    StylePerformanceArcRehearsalManifestReport,
    StylePerformanceArcRehearsalSegment,
    build_style_performance_arc_rehearsal_manifest_report,
    format_style_performance_arc_rehearsal_manifest_report,
    to_style_performance_arc_rehearsal_manifest_json,
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
    "STYLE_PERFORMANCE_ARC_READINESS_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_REFERENCE_MATCH_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_REHEARSAL_MANIFEST_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_REPORT_CLI_COMMAND",
    "STYLE_PERFORMANCE_ARC_SET_PLAN_CLI_COMMAND",
    "StylePerformanceArcAuditionPacketReport",
    "StylePerformanceArcCatalogReport",
    "StylePerformanceArcLiveCue",
    "StylePerformanceArcLiveCueSheetReport",
    "StylePerformanceArcLiveRenderBundleReport",
    "StylePerformanceArcLiveRenderSegment",
    "StylePerformanceArcLiveSessionPacketReport",
    "StylePerformanceArcLiveSessionSegment",
    "StylePerformanceArcReadinessEntry",
    "StylePerformanceArcReadinessReport",
    "StylePerformanceArcReferenceMatchEntry",
    "StylePerformanceArcReferenceMatchReport",
    "StylePerformanceArcReferenceSnapshotPreview",
    "StylePerformanceArcRehearsalManifestReport",
    "StylePerformanceArcRehearsalSegment",
    "StylePerformanceArcSetPlanReport",
    "StylePerformanceArcStageCard",
    "StylePerformanceArcStagePacket",
    "build_style_performance_arc_audition_packet_report",
    "build_style_performance_arc_catalog_report",
    "build_style_performance_arc_live_cue_sheet_report",
    "build_style_performance_arc_live_render_bundle_report",
    "build_style_performance_arc_live_session_packet_report",
    "build_style_performance_arc_readiness_report",
    "build_style_performance_arc_reference_match_report",
    "build_style_performance_arc_rehearsal_manifest_report",
    "build_style_performance_arc_set_plan_report",
    "format_style_performance_arc_audition_packet_report",
    "format_style_performance_arc_inspection",
    "format_style_performance_arc_list",
    "format_style_performance_arc_live_cue_sheet_report",
    "format_style_performance_arc_live_render_bundle_report",
    "format_style_performance_arc_live_session_packet_report",
    "format_style_performance_arc_readiness_report",
    "format_style_performance_arc_reference_match_report",
    "format_style_performance_arc_rehearsal_manifest_report",
    "format_style_performance_arc_report",
    "format_style_performance_arc_search",
    "format_style_performance_arc_set_plan_report",
    "to_style_performance_arc_audition_packet_json",
    "to_style_performance_arc_json",
    "to_style_performance_arc_live_cue_sheet_json",
    "to_style_performance_arc_live_render_bundle_json",
    "to_style_performance_arc_live_session_packet_json",
    "to_style_performance_arc_readiness_json",
    "to_style_performance_arc_reference_match_json",
    "to_style_performance_arc_rehearsal_manifest_json",
    "to_style_performance_arc_set_plan_json",
]
