"""Passive reference performance arc reports for long-form techno planning."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.style_performance_arcs import STYLE_PERFORMANCE_ARCS, StylePerformanceArc
from ..data.style_profiles import STYLE_PROFILES
from ..data.style_targets import STYLE_TARGET_VECTOR_AXES, STYLE_TARGET_VECTORS
from ..style_analysis.feature_report import FeatureReport
from .dual_machine_style_kit_selection import normalize_selection_scope
from .dual_machine_style_performance_set_plan import (
    DualMachineStylePerformanceSetPlan,
    DualMachineStylePerformanceSetSegment,
    build_dual_machine_style_performance_set_plan_report,
    format_dual_machine_style_performance_set_plan_report,
    to_dual_machine_style_performance_set_plan_json,
)
from .dual_machine_style_selection_mock_preview import (
    format_dual_machine_style_selection_mock_preview_event_rows,
    to_dual_machine_style_selection_mock_preview_json,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc report"
LIST_TITLE: Final[str] = "RytmRandomizer passive style performance arc list"
INSPECT_TITLE: Final[str] = "RytmRandomizer passive style performance arc inspection"
SEARCH_TITLE: Final[str] = "RytmRandomizer passive style performance arc search"
SET_PLAN_TITLE: Final[str] = "RytmRandomizer passive style performance arc set plan"
READINESS_TITLE: Final[str] = "RytmRandomizer passive style performance arc readiness matrix"
AUDITION_PACKET_TITLE: Final[str] = "RytmRandomizer passive style performance arc audition packet"
REHEARSAL_MANIFEST_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc rehearsal manifest"
)
LIVE_SESSION_PACKET_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live session packet"
)
LIVE_RENDER_BUNDLE_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live render bundle"
)
LIVE_CUE_SHEET_TITLE: Final[str] = "RytmRandomizer passive style performance arc live cue sheet"
REFERENCE_MATCH_TITLE: Final[str] = "RytmRandomizer passive style performance arc reference match"
SOURCE_MODULE: Final[str] = "reports.style_performance_arcs"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "metadata and plan expansion only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
AUDITION_PACKET_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "reference arc audition packet",
    "metadata and plan expansion only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
REHEARSAL_MANIFEST_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "reference arc rehearsal manifest",
    "operator runbook only",
    "metadata and plan expansion only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
LIVE_SESSION_PACKET_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live rehearsal session packet",
    "operator checklist only",
    "metadata and plan expansion only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
LIVE_RENDER_BUNDLE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live render bundle",
    "mock render preview only",
    "existing saved-kit snapshots only",
    "metadata and plan expansion only",
    "no real MIDI rendering",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
LIVE_CUE_SHEET_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live cue sheet",
    "operator cue sheet only",
    "uses live render bundle mock rows",
    "existing saved-kit snapshots only",
    "metadata and plan expansion only",
    "no real MIDI rendering",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
REFERENCE_MATCH_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "reference match only",
    "influence-not-replica scoring",
    "metadata and plan expansion only",
    "description-only path has no audio dependency",
    "optional live cue sheet uses saved-kit snapshots only",
    "no real MIDI rendering",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_LIST_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=LIST_TITLE,
    source_module=SOURCE_MODULE,
)
_INSPECT_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=INSPECT_TITLE,
    source_module=SOURCE_MODULE,
)
_SEARCH_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=SEARCH_TITLE,
    source_module=SOURCE_MODULE,
)
_SET_PLAN_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=SET_PLAN_TITLE,
    source_module=SOURCE_MODULE,
)
_READINESS_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=READINESS_TITLE,
    source_module=SOURCE_MODULE,
)
_AUDITION_PACKET_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=AUDITION_PACKET_TITLE,
    source_module=SOURCE_MODULE,
)
_REHEARSAL_MANIFEST_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REHEARSAL_MANIFEST_TITLE,
    source_module=SOURCE_MODULE,
)
_LIVE_SESSION_PACKET_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=LIVE_SESSION_PACKET_TITLE,
    source_module=SOURCE_MODULE,
)
_LIVE_RENDER_BUNDLE_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=LIVE_RENDER_BUNDLE_TITLE,
    source_module=SOURCE_MODULE,
)
_LIVE_CUE_SHEET_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=LIVE_CUE_SHEET_TITLE,
    source_module=SOURCE_MODULE,
)
_REFERENCE_MATCH_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REFERENCE_MATCH_TITLE,
    source_module=SOURCE_MODULE,
)
_SET_PLAN_USAGE: Final[str] = (
    "style-performance-arc-set-plan-report usage: "
    "<arc-key> --rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]"
)
_READINESS_USAGE: Final[str] = (
    "style-performance-arc-readiness-report usage: "
    "[<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--limit N] [--json]"
)
_AUDITION_PACKET_USAGE: Final[str] = (
    "style-performance-arc-audition-packet-report usage: "
    "[<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]"
)
_REHEARSAL_MANIFEST_USAGE: Final[str] = (
    "style-performance-arc-rehearsal-manifest-report usage: "
    "[<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]"
)
_LIVE_SESSION_PACKET_USAGE: Final[str] = (
    "style-performance-arc-live-session-packet-report usage: "
    "[<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]"
)
_LIVE_RENDER_BUNDLE_USAGE: Final[str] = (
    "style-performance-arc-live-render-bundle-report usage: "
    "[<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]"
)
_LIVE_CUE_SHEET_USAGE: Final[str] = (
    "style-performance-arc-live-cue-sheet-report usage: "
    "[<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]"
)
_REFERENCE_MATCH_USAGE: Final[str] = (
    "style-performance-arc-reference-match-report usage: "
    "(--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]"
)
_SET_PLAN_OPTIONS: Final[tuple[str, ...]] = (
    "--rytm",
    "--analog-four",
    "--scope",
    "--rank",
    "--total-minutes",
    "--segment-minutes",
    "--discovery-start",
    "--discovery-end",
    "--events",
    "--limit",
    "--json",
)
_READINESS_OPTIONS: Final[tuple[str, ...]] = (
    "--rytm",
    "--analog-four",
    "--scope",
    "--rank",
    "--total-minutes",
    "--segment-minutes",
    "--discovery-start",
    "--discovery-end",
    "--limit",
    "--json",
)
_AUDITION_PACKET_OPTIONS: Final[tuple[str, ...]] = (
    "--rytm",
    "--analog-four",
    "--scope",
    "--rank",
    "--total-minutes",
    "--segment-minutes",
    "--discovery-start",
    "--discovery-end",
    "--events",
    "--limit",
    "--json",
)
_REHEARSAL_MANIFEST_OPTIONS: Final[tuple[str, ...]] = _AUDITION_PACKET_OPTIONS
_LIVE_SESSION_PACKET_OPTIONS: Final[tuple[str, ...]] = _AUDITION_PACKET_OPTIONS
_LIVE_RENDER_BUNDLE_OPTIONS: Final[tuple[str, ...]] = _AUDITION_PACKET_OPTIONS
_LIVE_CUE_SHEET_OPTIONS: Final[tuple[str, ...]] = _AUDITION_PACKET_OPTIONS
_REFERENCE_MATCH_OPTIONS: Final[tuple[str, ...]] = (
    "--description",
    "--audio",
    "--library",
    "--rytm",
    "--analog-four",
    "--scope",
    "--rank",
    "--total-minutes",
    "--segment-minutes",
    "--discovery-start",
    "--discovery-end",
    "--events",
    "--limit",
    "--json",
)
_DEFAULT_EVENT_LIMIT: Final[int] = 24
_READINESS_SORT_ORDER: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ready": 0,
        "partial": 1,
        "blocked": 2,
    }
)


@dataclass(frozen=True)
class StylePerformanceArcCatalogReport:
    """Passive catalog report for reference performance arcs."""

    arc_count: int
    arcs_by_key: Mapping[str, StylePerformanceArc]


@dataclass(frozen=True)
class StylePerformanceArcSetPlanReport:
    """Passive reference arc expansion into the dual-machine set planner."""

    arc: StylePerformanceArc
    plan: DualMachineStylePerformanceSetPlan


@dataclass(frozen=True)
class StylePerformanceArcReadinessEntry:
    """One ranked arc readiness row derived from an expanded set plan."""

    position: int
    arc: StylePerformanceArc
    readiness: str
    average_selection_score: int
    operator_action: str
    plan: DualMachineStylePerformanceSetPlan


@dataclass(frozen=True)
class StylePerformanceArcReadinessReport:
    """Passive readiness matrix across reference arcs and saved kit banks."""

    scope: str
    arc_count: int
    ready_arc_count: int
    partial_arc_count: int
    blocked_arc_count: int
    total_segment_count: int
    total_event_row_count: int
    total_mock_message_count: int
    total_deferred_row_count: int
    entries: tuple[StylePerformanceArcReadinessEntry, ...]


@dataclass(frozen=True)
class StylePerformanceArcReferenceMatchEntry:
    """One ranked reference-to-performance-arc match row."""

    position: int
    arc: StylePerformanceArc
    score: int
    vector_score: int
    direct_score: int
    max_style_score: int
    matched_terms: tuple[str, ...]
    matched_style_keys: tuple[str, ...]
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcReferenceMatchReport:
    """Passive reference description/feature match against curated arcs."""

    source_kind: str
    source_reference: str | None
    description: str | None
    feature_report: FeatureReport
    axis_scores: Mapping[str, int]
    matched_terms: tuple[str, ...]
    matches: tuple[StylePerformanceArcReferenceMatchEntry, ...]
    live_cue_sheet: StylePerformanceArcLiveCueSheetReport | None

    @property
    def selected_match(self) -> StylePerformanceArcReferenceMatchEntry:
        """Return the top-ranked reference arc match."""

        return self.matches[0]

    @property
    def match_count(self) -> int:
        """Return ranked match count."""

        return len(self.matches)


@dataclass(frozen=True)
class StylePerformanceArcAuditionPacketReport:
    """Passive best-arc audition packet derived from a readiness matrix."""

    readiness_report: StylePerformanceArcReadinessReport
    selected_entry: StylePerformanceArcReadinessEntry

    @property
    def selected_set_plan(self) -> DualMachineStylePerformanceSetPlan:
        """Return the selected timed set plan for operator preview."""

        return self.selected_entry.plan


@dataclass(frozen=True)
class StylePerformanceArcRehearsalSegment:
    """One operator-facing segment row for a selected reference arc rehearsal."""

    position: int
    style_key: str
    time_window: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    readiness: str
    selection_score: int
    operator_action: str
    rytm_preview_summary: str
    analog_four_preview_summary: str
    event_row_count: int
    mock_message_count: int
    deferred_row_count: int


@dataclass(frozen=True)
class StylePerformanceArcRehearsalManifestReport:
    """Passive rehearsal runbook derived from the selected audition packet."""

    audition_packet: StylePerformanceArcAuditionPacketReport
    preflight_steps: tuple[str, ...]
    segments: tuple[StylePerformanceArcRehearsalSegment, ...]

    @property
    def selected_entry(self) -> StylePerformanceArcReadinessEntry:
        """Return the selected reference arc readiness entry."""

        return self.audition_packet.selected_entry

    @property
    def selected_set_plan(self) -> DualMachineStylePerformanceSetPlan:
        """Return the timed set plan used by the rehearsal manifest."""

        return self.audition_packet.selected_set_plan

    @property
    def segment_count(self) -> int:
        """Return the selected set-plan segment count."""

        return self.selected_set_plan.segment_count

    @property
    def ready_segment_count(self) -> int:
        """Return ready segment count for the selected plan."""

        return self.selected_set_plan.ready_segment_count

    @property
    def partial_segment_count(self) -> int:
        """Return partial segment count for the selected plan."""

        return self.selected_set_plan.partial_segment_count

    @property
    def blocked_segment_count(self) -> int:
        """Return blocked segment count for the selected plan."""

        return self.selected_set_plan.blocked_segment_count


@dataclass(frozen=True)
class StylePerformanceArcLiveSessionSegment:
    """One operator-facing segment card for a live rehearsal session."""

    position: int
    style_key: str
    time_window: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    readiness: str
    listen_for: str
    go_no_go_cue: str
    reset_cue: str
    rytm_preview_summary: str
    analog_four_preview_summary: str
    event_row_count: int
    mock_message_count: int
    deferred_row_count: int


@dataclass(frozen=True)
class StylePerformanceArcLiveSessionPacketReport:
    """Passive live-session packet derived from a rehearsal manifest."""

    rehearsal_manifest: StylePerformanceArcRehearsalManifestReport
    launch_checklist: tuple[str, ...]
    suggested_commands: tuple[str, ...]
    segments: tuple[StylePerformanceArcLiveSessionSegment, ...]

    @property
    def selected_entry(self) -> StylePerformanceArcReadinessEntry:
        """Return the selected reference arc readiness entry."""

        return self.rehearsal_manifest.selected_entry

    @property
    def selected_set_plan(self) -> DualMachineStylePerformanceSetPlan:
        """Return the selected timed set plan."""

        return self.rehearsal_manifest.selected_set_plan

    @property
    def segment_count(self) -> int:
        """Return the selected set-plan segment count."""

        return self.rehearsal_manifest.segment_count

    @property
    def ready_segment_count(self) -> int:
        """Return ready segment count for the selected plan."""

        return self.rehearsal_manifest.ready_segment_count

    @property
    def partial_segment_count(self) -> int:
        """Return partial segment count for the selected plan."""

        return self.rehearsal_manifest.partial_segment_count

    @property
    def blocked_segment_count(self) -> int:
        """Return blocked segment count for the selected plan."""

        return self.rehearsal_manifest.blocked_segment_count


@dataclass(frozen=True)
class StylePerformanceArcLiveRenderSegment:
    """One segment-level passive mock-render bundle for live rehearsal."""

    live_segment: StylePerformanceArcLiveSessionSegment
    set_plan_segment: DualMachineStylePerformanceSetSegment
    event_preview_rows: tuple[str, ...]
    deferred_rows: tuple[str, ...]

    @property
    def position(self) -> int:
        """Return the segment position in the selected performance arc."""

        return self.live_segment.position

    @property
    def style_key(self) -> str:
        """Return the segment style key."""

        return self.live_segment.style_key

    @property
    def time_window(self) -> str:
        """Return the segment time window."""

        return self.live_segment.time_window

    @property
    def discovery_amount(self) -> int:
        """Return the segment discovery amount."""

        return self.live_segment.discovery_amount

    @property
    def discovery_band(self) -> str:
        """Return the segment discovery band."""

        return self.live_segment.discovery_band

    @property
    def mutation_depth(self) -> str:
        """Return the segment mutation depth."""

        return self.live_segment.mutation_depth

    @property
    def readiness(self) -> str:
        """Return the segment readiness."""

        return self.live_segment.readiness

    @property
    def listen_for(self) -> str:
        """Return the segment listening cue."""

        return self.live_segment.listen_for

    @property
    def go_no_go_cue(self) -> str:
        """Return the segment go/no-go cue."""

        return self.live_segment.go_no_go_cue

    @property
    def reset_cue(self) -> str:
        """Return the segment reset cue."""

        return self.live_segment.reset_cue

    @property
    def rytm_preview_summary(self) -> str:
        """Return the Rytm preview summary."""

        return self.live_segment.rytm_preview_summary

    @property
    def analog_four_preview_summary(self) -> str:
        """Return the Analog Four preview summary."""

        return self.live_segment.analog_four_preview_summary

    @property
    def event_row_count(self) -> int:
        """Return the segment event row count."""

        return self.live_segment.event_row_count

    @property
    def mock_message_count(self) -> int:
        """Return the segment mock message count."""

        return self.live_segment.mock_message_count

    @property
    def deferred_row_count(self) -> int:
        """Return the segment deferred row count."""

        return self.live_segment.deferred_row_count

    @property
    def preview_json(self) -> dict[str, object]:
        """Return the full existing dual-machine mock preview JSON."""

        return to_dual_machine_style_selection_mock_preview_json(self.set_plan_segment.preview_plan)


@dataclass(frozen=True)
class StylePerformanceArcLiveRenderBundleReport:
    """Passive live render bundle derived from a live-session packet."""

    live_session_packet: StylePerformanceArcLiveSessionPacketReport
    suggested_commands: tuple[str, ...]
    segments: tuple[StylePerformanceArcLiveRenderSegment, ...]

    @property
    def selected_entry(self) -> StylePerformanceArcReadinessEntry:
        """Return the selected reference arc readiness entry."""

        return self.live_session_packet.selected_entry

    @property
    def selected_set_plan(self) -> DualMachineStylePerformanceSetPlan:
        """Return the selected timed set plan."""

        return self.live_session_packet.selected_set_plan

    @property
    def segment_count(self) -> int:
        """Return the selected set-plan segment count."""

        return self.live_session_packet.segment_count

    @property
    def ready_segment_count(self) -> int:
        """Return ready segment count for the selected plan."""

        return self.live_session_packet.ready_segment_count

    @property
    def partial_segment_count(self) -> int:
        """Return partial segment count for the selected plan."""

        return self.live_session_packet.partial_segment_count

    @property
    def blocked_segment_count(self) -> int:
        """Return blocked segment count for the selected plan."""

        return self.live_session_packet.blocked_segment_count

    @property
    def total_event_row_count(self) -> int:
        """Return total segment event rows."""

        return self.selected_set_plan.total_event_row_count

    @property
    def total_mock_message_count(self) -> int:
        """Return total segment mock messages."""

        return self.selected_set_plan.total_mock_message_count

    @property
    def total_deferred_row_count(self) -> int:
        """Return total deferred rows."""

        return self.selected_set_plan.total_deferred_row_count


@dataclass(frozen=True)
class StylePerformanceArcLiveCue:
    """One operator-facing live cue derived from a render segment."""

    render_segment: StylePerformanceArcLiveRenderSegment
    machine_focus: str
    operator_move: str
    risk_level: str
    recovery_action: str

    @property
    def position(self) -> int:
        """Return the segment position."""

        return self.render_segment.position

    @property
    def style_key(self) -> str:
        """Return the segment style key."""

        return self.render_segment.style_key

    @property
    def time_window(self) -> str:
        """Return the segment time window."""

        return self.render_segment.time_window

    @property
    def readiness(self) -> str:
        """Return the segment readiness."""

        return self.render_segment.readiness

    @property
    def render_row_summary(self) -> str:
        """Return a compact render/deferred row summary."""

        return (
            f"{self.render_segment.event_row_count} event row(s), "
            f"{self.render_segment.deferred_row_count} deferred row(s)"
        )


@dataclass(frozen=True)
class StylePerformanceArcLiveCueSheetReport:
    """Passive live-performance cue sheet derived from a render bundle."""

    live_render_bundle: StylePerformanceArcLiveRenderBundleReport
    suggested_commands: tuple[str, ...]
    preflight_cues: tuple[str, ...]
    recovery_cues: tuple[str, ...]
    cues: tuple[StylePerformanceArcLiveCue, ...]

    @property
    def selected_entry(self) -> StylePerformanceArcReadinessEntry:
        """Return the selected reference arc readiness entry."""

        return self.live_render_bundle.selected_entry

    @property
    def selected_set_plan(self) -> DualMachineStylePerformanceSetPlan:
        """Return the selected timed set plan."""

        return self.live_render_bundle.selected_set_plan

    @property
    def segment_count(self) -> int:
        """Return the selected segment count."""

        return self.live_render_bundle.segment_count

    @property
    def cue_count(self) -> int:
        """Return the number of generated cue rows."""

        return len(self.cues)

    @property
    def ready_segment_count(self) -> int:
        """Return ready segment count."""

        return self.live_render_bundle.ready_segment_count

    @property
    def partial_segment_count(self) -> int:
        """Return partial segment count."""

        return self.live_render_bundle.partial_segment_count

    @property
    def blocked_segment_count(self) -> int:
        """Return blocked segment count."""

        return self.live_render_bundle.blocked_segment_count

    @property
    def total_event_row_count(self) -> int:
        """Return total event rows."""

        return self.live_render_bundle.total_event_row_count

    @property
    def total_mock_message_count(self) -> int:
        """Return total mock messages."""

        return self.live_render_bundle.total_mock_message_count

    @property
    def total_deferred_row_count(self) -> int:
        """Return total deferred rows."""

        return self.live_render_bundle.total_deferred_row_count


def _join(values: Sequence[str]) -> str:
    return ", ".join(values)


def _sequence(values: Sequence[str]) -> str:
    return " -> ".join(values)


def _safety_lines() -> list[str]:
    return [SAFETY_SECTION_HEADER, *[f"- {line}" for line in SAFETY_LINES]]


def _audition_packet_safety_lines() -> list[str]:
    return [
        SAFETY_SECTION_HEADER,
        *[f"- {line}" for line in AUDITION_PACKET_SAFETY_LINES],
    ]


def _rehearsal_manifest_safety_lines() -> list[str]:
    return [
        SAFETY_SECTION_HEADER,
        *[f"- {line}" for line in REHEARSAL_MANIFEST_SAFETY_LINES],
    ]


def _live_session_packet_safety_lines() -> list[str]:
    return [
        SAFETY_SECTION_HEADER,
        *[f"- {line}" for line in LIVE_SESSION_PACKET_SAFETY_LINES],
    ]


def _live_render_bundle_safety_lines() -> list[str]:
    return [
        SAFETY_SECTION_HEADER,
        *[f"- {line}" for line in LIVE_RENDER_BUNDLE_SAFETY_LINES],
    ]


def _live_cue_sheet_safety_lines() -> list[str]:
    return [
        SAFETY_SECTION_HEADER,
        *[f"- {line}" for line in LIVE_CUE_SHEET_SAFETY_LINES],
    ]


def _arcs_by_key() -> Mapping[str, StylePerformanceArc]:
    return MappingProxyType(dict(STYLE_PERFORMANCE_ARCS))


def _normalized_arc_key(key: str) -> str:
    return str(key).lower()


def _arc_or_raise(key: str) -> StylePerformanceArc:
    normalized_key = _normalized_arc_key(key)
    arc = STYLE_PERFORMANCE_ARCS.get(normalized_key)
    if arc is None:
        raise KeyError(f"unknown style performance arc: {normalized_key}")
    return arc


def _selected_arc_keys(arc_keys: Sequence[str] | None) -> tuple[str, ...]:
    if arc_keys is None:
        return tuple(sorted(STYLE_PERFORMANCE_ARCS))
    normalized = tuple(_normalized_arc_key(key.strip()) for key in arc_keys if key.strip())
    if not normalized:
        raise ValueError("readiness matrix requires at least one arc key")
    return normalized


def _search_text(arc: StylePerformanceArc) -> str:
    values = [
        arc.key,
        arc.name,
        arc.summary,
        *arc.references,
        *arc.tags,
        *arc.style_keys,
        *arc.operator_notes,
    ]
    return "\n".join(values).lower()


def build_style_performance_arc_catalog_report() -> StylePerformanceArcCatalogReport:
    """Return passive catalog data for all reference performance arcs."""

    arcs_by_key = _arcs_by_key()
    return StylePerformanceArcCatalogReport(
        arc_count=len(arcs_by_key),
        arcs_by_key=arcs_by_key,
    )


def _default_plan_text(arc: StylePerformanceArc) -> str:
    return (
        f"scope={arc.default_scope}, minutes={arc.default_total_minutes}, "
        f"rank={arc.default_selection_rank}, "
        f"discovery={arc.default_discovery_start}->{arc.default_discovery_end}"
    )


def _arc_summary_lines(arc: StylePerformanceArc) -> list[str]:
    return [
        f"Key: {arc.key}",
        f"Name: {arc.name}",
        f"Summary: {arc.summary}",
        f"Primary references: {_join(arc.references[:2])}",
        "References:",
        *[f"- {reference}" for reference in arc.references],
        f"Tags: {_join(arc.tags)}",
        f"Style sequence: {_sequence(arc.style_keys)}",
        f"Default plan: {_default_plan_text(arc)}",
        "Operator notes:",
        *[f"- {note}" for note in arc.operator_notes],
    ]


def format_style_performance_arc_report(
    report: StylePerformanceArcCatalogReport | None = None,
) -> list[str]:
    """Return deterministic catalog lines for all reference performance arcs."""

    source_report = build_style_performance_arc_catalog_report() if report is None else report
    lines = [
        "Summary:",
        f"- Arcs: {source_report.arc_count}",
        "- Purpose: passive reference arcs for long-form live set planning",
        "Arcs:",
    ]
    for key in sorted(source_report.arcs_by_key):
        arc = source_report.arcs_by_key[key]
        lines.extend(
            [
                f"{arc.key}: {arc.name}",
                f"  Primary references: {_join(arc.references[:2])}",
                f"  Default plan: {_default_plan_text(arc)}",
                f"  Style sequence: {_sequence(arc.style_keys)}",
                f"  Summary: {arc.summary}",
            ]
        )
    lines.extend(_safety_lines())
    return passive_report_lines(_HEADER, lines)


def format_style_performance_arc_list() -> list[str]:
    """Return deterministic list lines for all reference arcs."""

    lines = [
        f"Count: {len(STYLE_PERFORMANCE_ARCS)}",
        "Items:",
    ]
    for key in sorted(STYLE_PERFORMANCE_ARCS):
        arc = STYLE_PERFORMANCE_ARCS[key]
        lines.append(f"- {arc.key}: {arc.name} ({_join(arc.tags)})")
    lines.extend(_safety_lines())
    return passive_report_lines(_LIST_HEADER, lines)


def format_style_performance_arc_inspection(key: str) -> list[str]:
    """Return deterministic detail lines for one reference arc."""

    normalized_key = _normalized_arc_key(key)
    arc = STYLE_PERFORMANCE_ARCS.get(normalized_key)
    if arc is None:
        lines = [
            f"Key: {normalized_key}",
            "Found: False",
            "Message: Style performance arc not found. No MIDI was sent. No command executed.",
        ]
        lines.extend(_safety_lines())
        return passive_report_lines(_INSPECT_HEADER, lines)

    lines = [
        f"Key: {arc.key}",
        "Found: True",
        *_arc_summary_lines(arc)[1:],
    ]
    lines.extend(_safety_lines())
    return passive_report_lines(_INSPECT_HEADER, lines)


def format_style_performance_arc_search(query: str) -> list[str]:
    """Return deterministic search lines for reference arc metadata."""

    normalized_query = str(query)
    search_query = normalized_query.lower()
    matches = [
        arc
        for key, arc in sorted(STYLE_PERFORMANCE_ARCS.items())
        if search_query in _search_text(arc)
    ]
    lines = [
        f"Query: {normalized_query}",
        f"Match count: {len(matches)}",
        "Matches:",
    ]
    if not matches:
        lines.append("- no matches found. No MIDI was sent. No command executed.")
    else:
        for arc in matches:
            lines.append(f"- {arc.key}: {arc.name}")
    lines.extend(_safety_lines())
    return passive_report_lines(_SEARCH_HEADER, lines)


def _default_plan_json(arc: StylePerformanceArc) -> dict[str, object]:
    return {
        "scope": arc.default_scope,
        "total_minutes": arc.default_total_minutes,
        "selection_rank": arc.default_selection_rank,
        "discovery_start": arc.default_discovery_start,
        "discovery_end": arc.default_discovery_end,
    }


def to_style_performance_arc_json(arc: StylePerformanceArc) -> dict[str, object]:
    """Return deterministic JSON-ready metadata for one reference arc."""

    return {
        "key": arc.key,
        "name": arc.name,
        "summary": arc.summary,
        "references": list(arc.references),
        "tags": list(arc.tags),
        "style_keys": list(arc.style_keys),
        "default_plan": _default_plan_json(arc),
        "operator_notes": list(arc.operator_notes),
    }


def _scope_from_paths_or_default(
    *,
    arc: StylePerformanceArc,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
) -> str:
    if (
        arc.default_scope == "dual"
        and rytm_sysex_path is not None
        and analog_four_sysex_path is None
    ):
        return "rytm-only"
    if (
        arc.default_scope == "dual"
        and rytm_sysex_path is None
        and analog_four_sysex_path is not None
    ):
        return "analog-four-only"
    return arc.default_scope


def build_style_performance_arc_set_plan_report(
    arc_key: str,
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
) -> StylePerformanceArcSetPlanReport:
    """Expand one passive reference arc into the timed dual-machine set planner."""

    arc = _arc_or_raise(arc_key)
    resolved_scope = (
        _scope_from_paths_or_default(
            arc=arc,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
        )
        if scope is None
        else normalize_selection_scope(scope)
    )
    plan = build_dual_machine_style_performance_set_plan_report(
        arc.style_keys,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        scope=resolved_scope,
        selection_rank=arc.default_selection_rank if selection_rank is None else selection_rank,
        total_minutes=arc.default_total_minutes if total_minutes is None else total_minutes,
        segment_minutes=segment_minutes,
        discovery_start=(
            arc.default_discovery_start if discovery_start is None else discovery_start
        ),
        discovery_end=arc.default_discovery_end if discovery_end is None else discovery_end,
    )
    return StylePerformanceArcSetPlanReport(arc=arc, plan=plan)


def _set_plan_intro_lines(report: StylePerformanceArcSetPlanReport) -> list[str]:
    arc = report.arc
    return [
        f"Arc: {arc.name}",
        f"Key: {arc.key}",
        f"Summary: {arc.summary}",
        f"References: {_join(arc.references)}",
        f"Tags: {_join(arc.tags)}",
        f"Default plan: {_default_plan_text(arc)}",
        "Operator notes:",
        *[f"- {note}" for note in arc.operator_notes],
        "Embedded performance set plan:",
    ]


def format_style_performance_arc_set_plan_report(
    report: StylePerformanceArcSetPlanReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing arc-expanded set plan lines."""

    lines = _set_plan_intro_lines(report)
    lines.extend(
        format_dual_machine_style_performance_set_plan_report(
            report.plan,
            include_events=include_events,
            event_limit=event_limit,
        )
    )
    lines.append(SAFETY_SECTION_HEADER)
    lines.append("- reference performance arc")
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return passive_report_lines(_SET_PLAN_HEADER, lines)


def to_style_performance_arc_set_plan_json(
    report: StylePerformanceArcSetPlanReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready metadata for an arc-expanded set plan."""

    return {
        "arc": to_style_performance_arc_json(report.arc),
        "performance_plan": to_dual_machine_style_performance_set_plan_json(report.plan),
        "safety": list(SAFETY_LINES),
    }


def _readiness_for_plan(plan: DualMachineStylePerformanceSetPlan) -> str:
    if plan.blocked_segment_count:
        return "blocked"
    if plan.partial_segment_count:
        return "partial"
    return "ready"


def _average_selection_score(plan: DualMachineStylePerformanceSetPlan) -> int:
    if not plan.segments:
        return 0
    return round(sum(segment.selection_score for segment in plan.segments) / len(plan.segments))


def _readiness_operator_action(
    *,
    readiness: str,
    plan: DualMachineStylePerformanceSetPlan,
) -> str:
    if readiness == "ready":
        return "Ready for live audition with all segments route-ready."
    if readiness == "partial":
        return (
            "Live-audition candidate with caveats: review partial segments, "
            f"{plan.total_deferred_row_count} deferred rows, and keep hardware unchanged "
            "until the mock preview is acceptable."
        )
    return (
        "Blocked for this kit-bank/scope combination: choose another arc, change scope, "
        "or load a different saved-kit bank before audition."
    )


def _readiness_entry_from_set_plan(
    *,
    arc: StylePerformanceArc,
    plan: DualMachineStylePerformanceSetPlan,
) -> StylePerformanceArcReadinessEntry:
    readiness = _readiness_for_plan(plan)
    return StylePerformanceArcReadinessEntry(
        position=0,
        arc=arc,
        readiness=readiness,
        average_selection_score=_average_selection_score(plan),
        operator_action=_readiness_operator_action(readiness=readiness, plan=plan),
        plan=plan,
    )


def _ranked_readiness_entry(
    *,
    position: int,
    entry: StylePerformanceArcReadinessEntry,
) -> StylePerformanceArcReadinessEntry:
    return StylePerformanceArcReadinessEntry(
        position=position,
        arc=entry.arc,
        readiness=entry.readiness,
        average_selection_score=entry.average_selection_score,
        operator_action=entry.operator_action,
        plan=entry.plan,
    )


def _readiness_sort_key(
    entry: StylePerformanceArcReadinessEntry,
) -> tuple[int, int, str]:
    return (
        _READINESS_SORT_ORDER[entry.readiness],
        -entry.average_selection_score,
        entry.arc.key,
    )


def _readiness_count(
    entries: Sequence[StylePerformanceArcReadinessEntry],
    readiness: str,
) -> int:
    return sum(1 for entry in entries if entry.readiness == readiness)


def build_style_performance_arc_readiness_report(
    arc_keys: Sequence[str] | None = None,
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
) -> StylePerformanceArcReadinessReport:
    """Rank passive reference arcs against saved kit banks and scope."""

    raw_entries = []
    for arc_key in _selected_arc_keys(arc_keys):
        set_plan = build_style_performance_arc_set_plan_report(
            arc_key,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
        )
        raw_entries.append(
            _readiness_entry_from_set_plan(
                arc=set_plan.arc,
                plan=set_plan.plan,
            )
        )
    sorted_entries = tuple(sorted(raw_entries, key=_readiness_sort_key))
    entries = tuple(
        _ranked_readiness_entry(position=index + 1, entry=entry)
        for index, entry in enumerate(sorted_entries)
    )
    return StylePerformanceArcReadinessReport(
        scope=entries[0].plan.scope,
        arc_count=len(entries),
        ready_arc_count=_readiness_count(entries, "ready"),
        partial_arc_count=_readiness_count(entries, "partial"),
        blocked_arc_count=_readiness_count(entries, "blocked"),
        total_segment_count=sum(entry.plan.segment_count for entry in entries),
        total_event_row_count=sum(entry.plan.total_event_row_count for entry in entries),
        total_mock_message_count=sum(entry.plan.total_mock_message_count for entry in entries),
        total_deferred_row_count=sum(entry.plan.total_deferred_row_count for entry in entries),
        entries=entries,
    )


def _readiness_entry_lines(entry: StylePerformanceArcReadinessEntry) -> list[str]:
    plan = entry.plan
    arc = entry.arc
    return [
        f"- {entry.position}. {arc.key} | {arc.name} | {entry.readiness}",
        f"  Average selection score: {entry.average_selection_score}",
        (
            f"  Segments: {plan.segment_count} total / {plan.ready_segment_count} ready / "
            f"{plan.partial_segment_count} partial / {plan.blocked_segment_count} blocked"
        ),
        (
            f"  Rows: {plan.total_event_row_count} events / "
            f"{plan.total_mock_message_count} mock messages / "
            f"{plan.total_deferred_row_count} deferred"
        ),
        (
            f"  Defaults: {arc.default_total_minutes} min / "
            f"discovery {arc.default_discovery_start}->{arc.default_discovery_end}"
        ),
        f"  Style sequence: {_sequence(arc.style_keys)}",
        f"  Action: {entry.operator_action}",
    ]


def _limited_readiness_entries(
    report: StylePerformanceArcReadinessReport,
    *,
    entry_limit: int,
) -> tuple[StylePerformanceArcReadinessEntry, ...]:
    if entry_limit < 0:
        raise ValueError("entry_limit must be >= 0")
    if entry_limit == 0 or entry_limit >= len(report.entries):
        return report.entries
    return report.entries[:entry_limit]


def format_style_performance_arc_readiness_report(
    report: StylePerformanceArcReadinessReport,
    *,
    entry_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing reference arc readiness lines."""

    selected_entries = _limited_readiness_entries(report, entry_limit=entry_limit)
    lines = [
        f"Scope: {report.scope}",
        f"Arc count: {report.arc_count}",
        f"Ready arcs: {report.ready_arc_count}",
        f"Partial arcs: {report.partial_arc_count}",
        f"Blocked arcs: {report.blocked_arc_count}",
        f"Total segments: {report.total_segment_count}",
        f"Total event rows: {report.total_event_row_count}",
        f"Total mock messages: {report.total_mock_message_count}",
        f"Total deferred rows: {report.total_deferred_row_count}",
        "Arc readiness matrix:",
    ]
    if len(selected_entries) == len(report.entries):
        lines.append("- Showing all arcs")
    else:
        lines.append(f"- Showing first {entry_limit} of {len(report.entries)} arcs")
    for entry in selected_entries:
        lines.extend(_readiness_entry_lines(entry))
    lines.append(SAFETY_SECTION_HEADER)
    lines.append("- reference arc readiness matrix")
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return passive_report_lines(_READINESS_HEADER, lines)


def _readiness_totals_json(report: StylePerformanceArcReadinessReport) -> dict[str, object]:
    return {
        "arcs": report.arc_count,
        "ready": report.ready_arc_count,
        "partial": report.partial_arc_count,
        "blocked": report.blocked_arc_count,
        "segments": report.total_segment_count,
        "event_rows": report.total_event_row_count,
        "mock_messages": report.total_mock_message_count,
        "deferred_rows": report.total_deferred_row_count,
    }


def _readiness_entry_json(entry: StylePerformanceArcReadinessEntry) -> dict[str, object]:
    return {
        "position": entry.position,
        "arc": to_style_performance_arc_json(entry.arc),
        "readiness": entry.readiness,
        "average_selection_score": entry.average_selection_score,
        "operator_action": entry.operator_action,
        "performance_plan": to_dual_machine_style_performance_set_plan_json(entry.plan),
    }


def to_style_performance_arc_readiness_json(
    report: StylePerformanceArcReadinessReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready reference arc readiness metadata."""

    return {
        "scope": report.scope,
        "totals": _readiness_totals_json(report),
        "entries": [_readiness_entry_json(entry) for entry in report.entries],
        "safety": list(SAFETY_LINES),
    }


def build_style_performance_arc_audition_packet_report(
    arc_keys: Sequence[str] | None = None,
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
) -> StylePerformanceArcAuditionPacketReport:
    """Return the highest-ranked passive reference arc audition packet."""

    readiness_report = build_style_performance_arc_readiness_report(
        arc_keys,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        scope=scope,
        selection_rank=selection_rank,
        total_minutes=total_minutes,
        segment_minutes=segment_minutes,
        discovery_start=discovery_start,
        discovery_end=discovery_end,
    )
    if not readiness_report.entries:
        raise ValueError("audition packet requires at least one readiness entry")
    return StylePerformanceArcAuditionPacketReport(
        readiness_report=readiness_report,
        selected_entry=readiness_report.entries[0],
    )


def _selected_set_plan_report(
    report: StylePerformanceArcAuditionPacketReport,
) -> StylePerformanceArcSetPlanReport:
    return StylePerformanceArcSetPlanReport(
        arc=report.selected_entry.arc,
        plan=report.selected_entry.plan,
    )


def format_style_performance_arc_audition_packet_report(
    report: StylePerformanceArcAuditionPacketReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing best-arc audition packet lines."""

    selected = report.selected_entry
    readiness = report.readiness_report
    set_plan_lines = format_style_performance_arc_set_plan_report(
        _selected_set_plan_report(report),
        include_events=include_events,
        event_limit=event_limit,
    )
    lines = [
        "Summary:",
        f"- Scope: {readiness.scope}",
        f"- Evaluated arcs: {readiness.arc_count}",
        (
            "- Readiness totals: "
            f"{readiness.ready_arc_count} ready, "
            f"{readiness.partial_arc_count} partial, "
            f"{readiness.blocked_arc_count} blocked"
        ),
        "Selected arc:",
        f"- Position: {selected.position}",
        f"- Key: {selected.arc.key}",
        f"- Name: {selected.arc.name}",
        f"- Readiness: {selected.readiness}",
        f"- Average selection score: {selected.average_selection_score}",
        f"- Operator action: {selected.operator_action}",
        "Readiness matrix:",
        *[
            (
                f"- #{entry.position}: {entry.arc.key} | {entry.readiness} | "
                f"score {entry.average_selection_score}"
            )
            for entry in readiness.entries
        ],
        "Selected set plan:",
        *[f"  {line}" for line in set_plan_lines],
        *_audition_packet_safety_lines(),
    ]
    return passive_report_lines(_AUDITION_PACKET_HEADER, lines)


def to_style_performance_arc_audition_packet_json(
    report: StylePerformanceArcAuditionPacketReport,
) -> dict[str, object]:
    """Return deterministic JSON data for the selected reference arc packet."""

    return {
        "selected": _readiness_entry_json(report.selected_entry),
        "readiness_matrix": to_style_performance_arc_readiness_json(report.readiness_report),
        "selected_set_plan": to_style_performance_arc_set_plan_json(
            _selected_set_plan_report(report)
        ),
        "safety": list(AUDITION_PACKET_SAFETY_LINES),
    }


def _rytm_preview_summary(segment: DualMachineStylePerformanceSetSegment) -> str:
    preview = segment.preview_plan.rytm_preview
    if preview is None:
        return "unchanged by scope"
    return (
        f"slot {preview.slot} {preview.kit_name} "
        f"/ ready {preview.preview_ready} "
        f"/ mock rows {preview.mock_message_count}"
    )


def _analog_four_preview_summary(segment: DualMachineStylePerformanceSetSegment) -> str:
    preview = segment.preview_plan.analog_four_preview
    if preview is None:
        return "unchanged by scope"
    return (
        f"slot {preview.slot} {preview.kit_name} "
        f"/ ready {preview.preview_ready} "
        f"/ deferred rows {preview.deferred_row_count}"
    )


def _rehearsal_segment_from_set_segment(
    segment: DualMachineStylePerformanceSetSegment,
) -> StylePerformanceArcRehearsalSegment:
    return StylePerformanceArcRehearsalSegment(
        position=segment.position,
        style_key=segment.style_key,
        time_window=segment.time_window,
        discovery_amount=segment.discovery_amount,
        discovery_band=segment.discovery_band,
        mutation_depth=segment.mutation_depth,
        readiness=segment.selection_readiness,
        selection_score=segment.selection_score,
        operator_action=segment.operator_action,
        rytm_preview_summary=_rytm_preview_summary(segment),
        analog_four_preview_summary=_analog_four_preview_summary(segment),
        event_row_count=segment.event_row_count,
        mock_message_count=segment.mock_message_count,
        deferred_row_count=segment.deferred_row_count,
    )


def _rehearsal_preflight_steps(plan: DualMachineStylePerformanceSetPlan) -> tuple[str, ...]:
    steps = []
    if plan.scope in {"dual", "rytm-only"}:
        steps.append("Confirm the saved Rytm kit bank before rehearsal.")
    else:
        steps.append("Rytm is unchanged by this scope; leave its current kit alone.")
    if plan.scope in {"dual", "analog-four-only"}:
        steps.append("Confirm the saved Analog Four kit bank before rehearsal.")
    else:
        steps.append("Analog Four is unchanged by this scope; leave its current kit alone.")
    steps.extend(
        [
            "Keep this command passive; it is a rehearsal manifest, not an armed send.",
            "Audition one segment at a time before trusting the full arc live.",
        ]
    )
    return tuple(steps)


def build_style_performance_arc_rehearsal_manifest_report(
    arc_keys: Sequence[str] | None = None,
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
) -> StylePerformanceArcRehearsalManifestReport:
    """Return a passive rehearsal manifest for the selected reference arc."""

    audition_packet = build_style_performance_arc_audition_packet_report(
        arc_keys,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        scope=scope,
        selection_rank=selection_rank,
        total_minutes=total_minutes,
        segment_minutes=segment_minutes,
        discovery_start=discovery_start,
        discovery_end=discovery_end,
    )
    plan = audition_packet.selected_set_plan
    return StylePerformanceArcRehearsalManifestReport(
        audition_packet=audition_packet,
        preflight_steps=_rehearsal_preflight_steps(plan),
        segments=tuple(_rehearsal_segment_from_set_segment(segment) for segment in plan.segments),
    )


def _rehearsal_event_preview_lines(
    plan: DualMachineStylePerformanceSetPlan,
    *,
    event_limit: int,
) -> list[str]:
    set_plan_lines = format_dual_machine_style_performance_set_plan_report(
        plan,
        include_events=True,
        event_limit=event_limit,
    )
    selected_lines: list[str] = []
    capture = False
    for line in set_plan_lines:
        if line == SAFETY_SECTION_HEADER:
            capture = False
        elif line.startswith("Event preview for segment"):
            capture = True
        if capture:
            selected_lines.append(line)
    return selected_lines


def _rehearsal_segment_json(
    segment: StylePerformanceArcRehearsalSegment,
) -> dict[str, object]:
    return {
        "position": segment.position,
        "style_key": segment.style_key,
        "time_window": segment.time_window,
        "discovery_amount": segment.discovery_amount,
        "discovery_band": segment.discovery_band,
        "mutation_depth": segment.mutation_depth,
        "readiness": segment.readiness,
        "selection_score": segment.selection_score,
        "operator_action": segment.operator_action,
        "rytm_preview": segment.rytm_preview_summary,
        "analog_four_preview": segment.analog_four_preview_summary,
        "event_row_count": segment.event_row_count,
        "mock_message_count": segment.mock_message_count,
        "deferred_row_count": segment.deferred_row_count,
    }


def format_style_performance_arc_rehearsal_manifest_report(
    report: StylePerformanceArcRehearsalManifestReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing rehearsal manifest lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    selected = report.selected_entry
    plan = report.selected_set_plan
    lines = [
        "Summary:",
        f"- Scope: {plan.scope}",
        f"- Total duration minutes: {plan.total_minutes}",
        f"- Segment count: {report.segment_count}",
        (
            "- Segment readiness: "
            f"{report.ready_segment_count} ready, "
            f"{report.partial_segment_count} partial, "
            f"{report.blocked_segment_count} blocked"
        ),
        "Selected arc:",
        f"- Position: {selected.position}",
        f"- Key: {selected.arc.key}",
        f"- Name: {selected.arc.name}",
        f"- Readiness: {selected.readiness}",
        f"- Operator action: {selected.operator_action}",
        "Preflight checklist:",
        *[f"- {step}" for step in report.preflight_steps],
        "Segment runbook:",
    ]
    for segment in report.segments:
        lines.extend(
            [
                (
                    f"- {segment.position}. {segment.time_window} | {segment.style_key} "
                    f"| discovery {segment.discovery_amount} | {segment.discovery_band} "
                    f"| depth {segment.mutation_depth} | readiness {segment.readiness} "
                    f"| score {segment.selection_score}"
                ),
                f"  Action: {segment.operator_action}",
                f"  Rytm preview: {segment.rytm_preview_summary}",
                f"  Analog Four preview: {segment.analog_four_preview_summary}",
                (
                    f"  Counts: events {segment.event_row_count}, "
                    f"mock messages {segment.mock_message_count}, "
                    f"deferred {segment.deferred_row_count}"
                ),
            ]
        )
    if include_events:
        lines.append("Event previews:")
        lines.extend(
            _rehearsal_event_preview_lines(
                plan,
                event_limit=event_limit,
            )
        )
    lines.extend(_rehearsal_manifest_safety_lines())
    return passive_report_lines(_REHEARSAL_MANIFEST_HEADER, lines)


def to_style_performance_arc_rehearsal_manifest_json(
    report: StylePerformanceArcRehearsalManifestReport,
) -> dict[str, object]:
    """Return deterministic JSON data for a reference arc rehearsal manifest."""

    plan = report.selected_set_plan
    return {
        "selected": _readiness_entry_json(report.selected_entry),
        "audition_packet": to_style_performance_arc_audition_packet_json(report.audition_packet),
        "manifest": {
            "scope": plan.scope,
            "total_minutes": plan.total_minutes,
            "selection_rank": plan.selection_rank,
            "discovery_start": plan.discovery_start,
            "discovery_end": plan.discovery_end,
            "preflight": list(report.preflight_steps),
            "totals": {
                "segments": report.segment_count,
                "ready": report.ready_segment_count,
                "partial": report.partial_segment_count,
                "blocked": report.blocked_segment_count,
                "event_rows": plan.total_event_row_count,
                "mock_messages": plan.total_mock_message_count,
                "deferred_rows": plan.total_deferred_row_count,
            },
            "segments": [_rehearsal_segment_json(segment) for segment in report.segments],
        },
        "safety": list(REHEARSAL_MANIFEST_SAFETY_LINES),
    }


def _live_session_launch_checklist(
    manifest: StylePerformanceArcRehearsalManifestReport,
) -> tuple[str, ...]:
    plan = manifest.selected_set_plan
    return (
        *manifest.preflight_steps,
        "Keep this packet passive until the rehearsal notes are reviewed.",
        "Run each segment as its own audition before trusting the full arc live.",
        f"Use scope {plan.scope} so unchanged machines stay parked.",
        "Reset to a known-good kit before moving from rehearsal into performance.",
    )


def _live_session_machine_path_flags(scope: str) -> str:
    if scope == "analog-four-only":
        return "--analog-four <analog-four-syx-path> --scope analog-four-only"
    if scope == "rytm-only":
        return "--rytm <rytm-syx-path> --scope rytm-only"
    return "--rytm <rytm-syx-path> --analog-four <analog-four-syx-path> --scope dual"


def _live_session_plan_flags(plan: DualMachineStylePerformanceSetPlan) -> str:
    return (
        f"--rank {plan.selection_rank} --total-minutes {plan.total_minutes} "
        f"--discovery-start {plan.discovery_start} --discovery-end {plan.discovery_end}"
    )


def _live_session_suggested_commands(
    manifest: StylePerformanceArcRehearsalManifestReport,
) -> tuple[str, ...]:
    arc_key = manifest.selected_entry.arc.key
    plan = manifest.selected_set_plan
    base_args = (
        f"{arc_key} {_live_session_machine_path_flags(plan.scope)} "
        f"{_live_session_plan_flags(plan)}"
    )
    return (
        (
            "python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report "
            f"{base_args} --events --limit 8"
        ),
        (
            "python -m rytm_randomizer.cli style-performance-arc-rehearsal-manifest-report "
            f"{base_args} --events --limit 8"
        ),
        (
            "python -m rytm_randomizer.cli style-performance-arc-audition-packet-report "
            f"{base_args} --events --limit 8"
        ),
        (
            "python -m rytm_randomizer.cli style-performance-arc-readiness-report "
            f"{base_args} --limit 8"
        ),
        (
            "python -m rytm_randomizer.cli style-performance-arc-set-plan-report "
            f"{base_args} --events --limit 8"
        ),
    )


def _live_session_listen_for(segment: StylePerformanceArcRehearsalSegment) -> str:
    if segment.discovery_amount <= 35:
        return "Subtle variation while the loaded kit identity stays recognizable."
    if segment.discovery_amount >= 75:
        return "Surprise, edge, and whether the machine still supports the live set."
    return "Useful groove movement and tonal pressure without losing the segment role."


def _live_session_go_no_go_cue(segment: StylePerformanceArcRehearsalSegment) -> str:
    if segment.readiness == "ready":
        return "Auditionable: move forward if the segment supports the room."
    if segment.readiness == "partial":
        return "Rehearse carefully: continue only if the weak machine is not exposed."
    return "Planning-only: skip live use until better saved kit material exists."


def _live_session_reset_cue(segment: StylePerformanceArcRehearsalSegment) -> str:
    if segment.readiness == "blocked":
        return "Reset to the previous known-good kit before live use."
    if segment.discovery_amount >= 75:
        return "Reset after audition if the edge overwhelms the groove."
    return "Reset only if the segment pulls focus away from the live arc."


def _live_session_segment_from_rehearsal(
    segment: StylePerformanceArcRehearsalSegment,
) -> StylePerformanceArcLiveSessionSegment:
    return StylePerformanceArcLiveSessionSegment(
        position=segment.position,
        style_key=segment.style_key,
        time_window=segment.time_window,
        discovery_amount=segment.discovery_amount,
        discovery_band=segment.discovery_band,
        mutation_depth=segment.mutation_depth,
        readiness=segment.readiness,
        listen_for=_live_session_listen_for(segment),
        go_no_go_cue=_live_session_go_no_go_cue(segment),
        reset_cue=_live_session_reset_cue(segment),
        rytm_preview_summary=segment.rytm_preview_summary,
        analog_four_preview_summary=segment.analog_four_preview_summary,
        event_row_count=segment.event_row_count,
        mock_message_count=segment.mock_message_count,
        deferred_row_count=segment.deferred_row_count,
    )


def build_style_performance_arc_live_session_packet_report(
    arc_keys: Sequence[str] | None = None,
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
) -> StylePerformanceArcLiveSessionPacketReport:
    """Return a passive live-session packet for the selected reference arc."""

    manifest = build_style_performance_arc_rehearsal_manifest_report(
        arc_keys,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        scope=scope,
        selection_rank=selection_rank,
        total_minutes=total_minutes,
        segment_minutes=segment_minutes,
        discovery_start=discovery_start,
        discovery_end=discovery_end,
    )
    return StylePerformanceArcLiveSessionPacketReport(
        rehearsal_manifest=manifest,
        launch_checklist=_live_session_launch_checklist(manifest),
        suggested_commands=_live_session_suggested_commands(manifest),
        segments=tuple(
            _live_session_segment_from_rehearsal(segment) for segment in manifest.segments
        ),
    )


def _live_session_segment_json(
    segment: StylePerformanceArcLiveSessionSegment,
) -> dict[str, object]:
    return {
        "position": segment.position,
        "style_key": segment.style_key,
        "time_window": segment.time_window,
        "discovery_amount": segment.discovery_amount,
        "discovery_band": segment.discovery_band,
        "mutation_depth": segment.mutation_depth,
        "readiness": segment.readiness,
        "listen_for": segment.listen_for,
        "go_no_go_cue": segment.go_no_go_cue,
        "reset_cue": segment.reset_cue,
        "rytm_preview": segment.rytm_preview_summary,
        "analog_four_preview": segment.analog_four_preview_summary,
        "event_row_count": segment.event_row_count,
        "mock_message_count": segment.mock_message_count,
        "deferred_row_count": segment.deferred_row_count,
    }


def format_style_performance_arc_live_session_packet_report(
    report: StylePerformanceArcLiveSessionPacketReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing live-session packet lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    selected = report.selected_entry
    plan = report.selected_set_plan
    lines = [
        "Summary:",
        f"- Scope: {plan.scope}",
        f"- Total duration minutes: {plan.total_minutes}",
        f"- Segment count: {report.segment_count}",
        (
            "- Segment readiness: "
            f"{report.ready_segment_count} ready, "
            f"{report.partial_segment_count} partial, "
            f"{report.blocked_segment_count} blocked"
        ),
        "Selected arc:",
        f"- Position: {selected.position}",
        f"- Key: {selected.arc.key}",
        f"- Name: {selected.arc.name}",
        f"- Readiness: {selected.readiness}",
        f"- Operator action: {selected.operator_action}",
        "Launch checklist:",
        *[f"- {step}" for step in report.launch_checklist],
        "Suggested passive commands:",
        *[f"- {command}" for command in report.suggested_commands],
        "Segment cards:",
    ]
    for segment in report.segments:
        lines.extend(
            [
                (
                    f"- {segment.position}. {segment.time_window} | {segment.style_key} "
                    f"| discovery {segment.discovery_amount} | {segment.discovery_band} "
                    f"| depth {segment.mutation_depth} | readiness {segment.readiness}"
                ),
                f"  Listen for: {segment.listen_for}",
                f"  Go/no-go cue: {segment.go_no_go_cue}",
                f"  Reset cue: {segment.reset_cue}",
                f"  Rytm preview: {segment.rytm_preview_summary}",
                f"  Analog Four preview: {segment.analog_four_preview_summary}",
                (
                    f"  Counts: events {segment.event_row_count}, "
                    f"mock messages {segment.mock_message_count}, "
                    f"deferred {segment.deferred_row_count}"
                ),
            ]
        )
    if include_events:
        lines.append("Event previews:")
        lines.extend(
            _rehearsal_event_preview_lines(
                plan,
                event_limit=event_limit,
            )
        )
    lines.extend(_live_session_packet_safety_lines())
    return passive_report_lines(_LIVE_SESSION_PACKET_HEADER, lines)


def to_style_performance_arc_live_session_packet_json(
    report: StylePerformanceArcLiveSessionPacketReport,
) -> dict[str, object]:
    """Return deterministic JSON data for a live rehearsal session packet."""

    plan = report.selected_set_plan
    return {
        "selected": _readiness_entry_json(report.selected_entry),
        "rehearsal_manifest": to_style_performance_arc_rehearsal_manifest_json(
            report.rehearsal_manifest
        ),
        "session_packet": {
            "scope": plan.scope,
            "total_minutes": plan.total_minutes,
            "selection_rank": plan.selection_rank,
            "discovery_start": plan.discovery_start,
            "discovery_end": plan.discovery_end,
            "launch_checklist": list(report.launch_checklist),
            "suggested_commands": list(report.suggested_commands),
            "totals": {
                "segments": report.segment_count,
                "ready": report.ready_segment_count,
                "partial": report.partial_segment_count,
                "blocked": report.blocked_segment_count,
                "event_rows": plan.total_event_row_count,
                "mock_messages": plan.total_mock_message_count,
                "deferred_rows": plan.total_deferred_row_count,
            },
            "segments": [_live_session_segment_json(segment) for segment in report.segments],
        },
        "safety": list(LIVE_SESSION_PACKET_SAFETY_LINES),
    }


def _live_render_bundle_suggested_commands(
    packet: StylePerformanceArcLiveSessionPacketReport,
) -> tuple[str, ...]:
    arc_key = packet.selected_entry.arc.key
    plan = packet.selected_set_plan
    base_args = (
        f"{arc_key} {_live_session_machine_path_flags(plan.scope)} "
        f"{_live_session_plan_flags(plan)}"
    )
    return (
        (
            "python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report "
            f"{base_args} --events --limit 8"
        ),
        *packet.suggested_commands,
    )


def _live_render_bundle_event_rows(
    segment: DualMachineStylePerformanceSetSegment,
) -> tuple[str, ...]:
    return format_dual_machine_style_selection_mock_preview_event_rows(segment.preview_plan)


def _live_render_bundle_deferred_rows(
    segment: DualMachineStylePerformanceSetSegment,
) -> tuple[str, ...]:
    analog_four_preview = segment.preview_plan.analog_four_preview
    if analog_four_preview is None or not analog_four_preview.deferred_rows:
        return ("- none",)
    return tuple(
        (
            f"- Analog Four Track {row.track} | {row.role_key} | {row.zone} | "
            f"{row.reason} | bias {row.target_bias} | depth {row.mutation_depth} | "
            f"direction {row.target_direction}"
        )
        for row in analog_four_preview.deferred_rows
    )


def _live_render_segment(
    *,
    live_segment: StylePerformanceArcLiveSessionSegment,
    set_plan_segment: DualMachineStylePerformanceSetSegment,
) -> StylePerformanceArcLiveRenderSegment:
    return StylePerformanceArcLiveRenderSegment(
        live_segment=live_segment,
        set_plan_segment=set_plan_segment,
        event_preview_rows=_live_render_bundle_event_rows(set_plan_segment),
        deferred_rows=_live_render_bundle_deferred_rows(set_plan_segment),
    )


def build_style_performance_arc_live_render_bundle_report(
    arc_keys: Sequence[str] | None = None,
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
) -> StylePerformanceArcLiveRenderBundleReport:
    """Return a passive segment-level mock-render bundle for live rehearsal."""

    packet = build_style_performance_arc_live_session_packet_report(
        arc_keys,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        scope=scope,
        selection_rank=selection_rank,
        total_minutes=total_minutes,
        segment_minutes=segment_minutes,
        discovery_start=discovery_start,
        discovery_end=discovery_end,
    )
    live_segments = packet.segments
    set_plan_segments = packet.selected_set_plan.segments
    if len(live_segments) != len(set_plan_segments):
        raise ValueError(
            "live render bundle requires matching live-session and set-plan segment counts"
        )
    segments = tuple(
        _live_render_segment(
            live_segment=live_segment,
            set_plan_segment=set_plan_segment,
        )
        for live_segment, set_plan_segment in zip(
            live_segments,
            set_plan_segments,
            strict=True,
        )
    )
    return StylePerformanceArcLiveRenderBundleReport(
        live_session_packet=packet,
        suggested_commands=_live_render_bundle_suggested_commands(packet),
        segments=segments,
    )


def _limited_event_rows(
    rows: Sequence[str],
    *,
    event_limit: int,
) -> tuple[str, ...]:
    if event_limit == 0 or event_limit >= len(rows):
        return tuple(rows)
    return tuple(rows[:event_limit])


def _live_render_segment_lines(
    segment: StylePerformanceArcLiveRenderSegment,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    lines = [
        (
            f"- {segment.position}. {segment.time_window} | {segment.style_key} "
            f"| discovery {segment.discovery_amount} | {segment.discovery_band} "
            f"| depth {segment.mutation_depth} | readiness {segment.readiness}"
        ),
        f"  Listen for: {segment.listen_for}",
        f"  Go/no-go cue: {segment.go_no_go_cue}",
        f"  Reset cue: {segment.reset_cue}",
        f"  Rytm preview: {segment.rytm_preview_summary}",
        f"  Analog Four preview: {segment.analog_four_preview_summary}",
        (
            f"  Counts: events {segment.event_row_count}, "
            f"mock messages {segment.mock_message_count}, "
            f"deferred {segment.deferred_row_count}"
        ),
        "  Deferred rows:",
        *[f"  {row}" for row in segment.deferred_rows],
    ]
    if include_events:
        lines.append(f"  Mock render preview: Event preview for segment {segment.position}")
        if not segment.event_preview_rows:
            lines.append("  - No mock rows available because the selected preview is not ready.")
        else:
            selected_rows = _limited_event_rows(
                segment.event_preview_rows,
                event_limit=event_limit,
            )
            if len(selected_rows) == len(segment.event_preview_rows):
                lines.append("  - Showing all events")
            else:
                lines.append(
                    f"  - Showing first {event_limit} of {len(segment.event_preview_rows)} events"
                )
            lines.extend(f"  {row}" for row in selected_rows)
    return lines


def format_style_performance_arc_live_render_bundle_report(
    report: StylePerformanceArcLiveRenderBundleReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic live render bundle lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    selected = report.selected_entry
    plan = report.selected_set_plan
    lines = [
        "Render bundle summary:",
        f"- Scope: {plan.scope}",
        f"- Total duration minutes: {plan.total_minutes}",
        f"- Selection rank: {plan.selection_rank}",
        f"- Segment count: {report.segment_count}",
        (
            "- Segment readiness: "
            f"{report.ready_segment_count} ready, "
            f"{report.partial_segment_count} partial, "
            f"{report.blocked_segment_count} blocked"
        ),
        f"- Total event rows: {report.total_event_row_count}",
        f"- Total mock messages: {report.total_mock_message_count}",
        f"- Total deferred rows: {report.total_deferred_row_count}",
        "Selected arc:",
        f"- Position: {selected.position}",
        f"- Key: {selected.arc.key}",
        f"- Name: {selected.arc.name}",
        f"- Readiness: {selected.readiness}",
        f"- Operator action: {selected.operator_action}",
        "Replayable passive commands:",
        *[f"- {command}" for command in report.suggested_commands],
        "Segment render bundles:",
    ]
    for segment in report.segments:
        lines.extend(
            _live_render_segment_lines(
                segment,
                include_events=include_events,
                event_limit=event_limit,
            )
        )
    lines.extend(_live_render_bundle_safety_lines())
    return passive_report_lines(_LIVE_RENDER_BUNDLE_HEADER, lines)


def _live_render_segment_json(
    segment: StylePerformanceArcLiveRenderSegment,
) -> dict[str, object]:
    return {
        "position": segment.position,
        "style_key": segment.style_key,
        "time_window": segment.time_window,
        "discovery_amount": segment.discovery_amount,
        "discovery_band": segment.discovery_band,
        "mutation_depth": segment.mutation_depth,
        "readiness": segment.readiness,
        "listen_for": segment.listen_for,
        "go_no_go_cue": segment.go_no_go_cue,
        "reset_cue": segment.reset_cue,
        "rytm_preview": segment.rytm_preview_summary,
        "analog_four_preview": segment.analog_four_preview_summary,
        "event_row_count": segment.event_row_count,
        "mock_message_count": segment.mock_message_count,
        "deferred_row_count": segment.deferred_row_count,
        "event_preview_rows": list(segment.event_preview_rows),
        "deferred_rows": list(segment.deferred_rows),
        "preview": segment.preview_json,
    }


def to_style_performance_arc_live_render_bundle_json(
    report: StylePerformanceArcLiveRenderBundleReport,
) -> dict[str, object]:
    """Return deterministic JSON data for a live render bundle."""

    plan = report.selected_set_plan
    return {
        "selected": _readiness_entry_json(report.selected_entry),
        "live_session_packet": to_style_performance_arc_live_session_packet_json(
            report.live_session_packet
        ),
        "render_bundle": {
            "scope": plan.scope,
            "total_minutes": plan.total_minutes,
            "selection_rank": plan.selection_rank,
            "discovery_start": plan.discovery_start,
            "discovery_end": plan.discovery_end,
            "suggested_commands": list(report.suggested_commands),
            "totals": {
                "segments": report.segment_count,
                "ready": report.ready_segment_count,
                "partial": report.partial_segment_count,
                "blocked": report.blocked_segment_count,
                "event_rows": report.total_event_row_count,
                "mock_messages": report.total_mock_message_count,
                "deferred_rows": report.total_deferred_row_count,
            },
            "segments": [_live_render_segment_json(segment) for segment in report.segments],
        },
        "safety": list(LIVE_RENDER_BUNDLE_SAFETY_LINES),
    }


def _live_cue_sheet_suggested_commands(
    bundle: StylePerformanceArcLiveRenderBundleReport,
) -> tuple[str, ...]:
    arc_key = bundle.selected_entry.arc.key
    plan = bundle.selected_set_plan
    base_args = (
        f"{arc_key} {_live_session_machine_path_flags(plan.scope)} "
        f"{_live_session_plan_flags(plan)}"
    )
    return (
        (
            "python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report "
            f"{base_args} --events --limit 8"
        ),
        *bundle.suggested_commands,
    )


def _live_cue_machine_focus(
    segment: StylePerformanceArcLiveRenderSegment,
    *,
    scope: str,
) -> str:
    if scope == "analog-four-only":
        return "Analog Four only"
    if scope == "rytm-only":
        return "Rytm only"
    if segment.rytm_preview_summary == "unchanged by scope":
        return "Analog Four only"
    if segment.analog_four_preview_summary == "unchanged by scope":
        return "Rytm only"
    return "Rytm + Analog Four"


def _live_cue_operator_move(
    segment: StylePerformanceArcLiveRenderSegment,
    *,
    machine_focus: str,
) -> str:
    if machine_focus == "Analog Four only":
        return (
            "Leave Rytm unchanged; cue Analog Four movement while listening for "
            f"{segment.listen_for}."
        )
    if machine_focus == "Rytm only":
        return (
            "Cue Rytm movement and leave Analog Four unchanged; listen for "
            f"{segment.listen_for}."
        )
    return "Cue both machines from the passive render rows; listen for " f"{segment.listen_for}."


def _live_cue_risk_level(segment: StylePerformanceArcLiveRenderSegment) -> str:
    if segment.readiness == "blocked" or segment.event_row_count == 0:
        return "red"
    if segment.readiness == "partial" or segment.deferred_row_count:
        return "amber"
    return "green"


def _live_cue_recovery_action(
    segment: StylePerformanceArcLiveRenderSegment,
    *,
    risk_level: str,
) -> str:
    if risk_level == "red":
        return f"Skip this cue if uncertain, then recover with: {segment.reset_cue}"
    if risk_level == "amber":
        return f"Keep one hand on recovery and use: {segment.reset_cue}"
    return f"If the room drifts, recover with: {segment.reset_cue}"


def _live_cue_from_segment(
    segment: StylePerformanceArcLiveRenderSegment,
    *,
    scope: str,
) -> StylePerformanceArcLiveCue:
    machine_focus = _live_cue_machine_focus(segment, scope=scope)
    risk_level = _live_cue_risk_level(segment)
    return StylePerformanceArcLiveCue(
        render_segment=segment,
        machine_focus=machine_focus,
        operator_move=_live_cue_operator_move(
            segment,
            machine_focus=machine_focus,
        ),
        risk_level=risk_level,
        recovery_action=_live_cue_recovery_action(
            segment,
            risk_level=risk_level,
        ),
    )


def _live_cue_sheet_preflight_cues(
    bundle: StylePerformanceArcLiveRenderBundleReport,
) -> tuple[str, ...]:
    plan = bundle.selected_set_plan
    return (
        f"Load saved-kit source scope: {plan.scope}.",
        f"Confirm {bundle.segment_count} planned segment cue(s) before launch.",
        f"Keep the live render bundle nearby for mock row detail: {bundle.selected_entry.arc.key}.",
        *bundle.live_session_packet.launch_checklist,
    )


def _live_cue_sheet_recovery_cues(
    cues: Sequence[StylePerformanceArcLiveCue],
) -> tuple[str, ...]:
    recovery_rows: list[str] = []
    seen: set[str] = set()
    for cue in cues:
        if cue.recovery_action in seen:
            continue
        seen.add(cue.recovery_action)
        recovery_rows.append(cue.recovery_action)
    return tuple(recovery_rows)


def build_style_performance_arc_live_cue_sheet_report(
    arc_keys: Sequence[str] | None = None,
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
) -> StylePerformanceArcLiveCueSheetReport:
    """Return an operator-facing passive live cue sheet."""

    bundle = build_style_performance_arc_live_render_bundle_report(
        arc_keys,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        scope=scope,
        selection_rank=selection_rank,
        total_minutes=total_minutes,
        segment_minutes=segment_minutes,
        discovery_start=discovery_start,
        discovery_end=discovery_end,
    )
    cues = tuple(
        _live_cue_from_segment(segment, scope=bundle.selected_set_plan.scope)
        for segment in bundle.segments
    )
    return StylePerformanceArcLiveCueSheetReport(
        live_render_bundle=bundle,
        suggested_commands=_live_cue_sheet_suggested_commands(bundle),
        preflight_cues=_live_cue_sheet_preflight_cues(bundle),
        recovery_cues=_live_cue_sheet_recovery_cues(cues),
        cues=cues,
    )


def _live_cue_lines(
    cue: StylePerformanceArcLiveCue,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    segment = cue.render_segment
    lines = [
        (
            f"- {cue.position}. {cue.time_window} | {cue.style_key} | "
            f"{cue.machine_focus} | readiness {cue.readiness}"
        ),
        f"  Risk: {cue.risk_level}",
        f"  Hands-on move: {cue.operator_move}",
        f"  Listen for: {segment.listen_for}",
        f"  Go/no-go: {segment.go_no_go_cue}",
        f"  Recovery: {cue.recovery_action}",
        f"  Rytm: {segment.rytm_preview_summary}",
        f"  Analog Four: {segment.analog_four_preview_summary}",
        f"  Render rows: {cue.render_row_summary}",
    ]
    if include_events:
        lines.append("  Mock render row preview:")
        if not segment.event_preview_rows:
            lines.append("  - No mock rows available because the selected preview is not ready.")
        else:
            selected_rows = _limited_event_rows(
                segment.event_preview_rows,
                event_limit=event_limit,
            )
            if len(selected_rows) == len(segment.event_preview_rows):
                lines.append("  - Showing all events")
            else:
                lines.append(
                    f"  - Showing first {event_limit} of {len(segment.event_preview_rows)} events"
                )
            lines.extend(f"  {row}" for row in selected_rows)
    return lines


def format_style_performance_arc_live_cue_sheet_report(
    report: StylePerformanceArcLiveCueSheetReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic live cue-sheet lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    selected = report.selected_entry
    plan = report.selected_set_plan
    lines = [
        "Cue sheet summary:",
        f"- Scope: {plan.scope}",
        f"- Total duration minutes: {plan.total_minutes}",
        f"- Cue count: {report.cue_count}",
        (
            "- Segment readiness: "
            f"{report.ready_segment_count} ready, "
            f"{report.partial_segment_count} partial, "
            f"{report.blocked_segment_count} blocked"
        ),
        f"- Total event rows: {report.total_event_row_count}",
        f"- Total deferred rows: {report.total_deferred_row_count}",
        "Selected arc:",
        f"- Position: {selected.position}",
        f"- Key: {selected.arc.key}",
        f"- Name: {selected.arc.name}",
        "Replayable passive commands:",
        *[f"- {command}" for command in report.suggested_commands],
        "Preflight cues:",
        *[f"- {cue}" for cue in report.preflight_cues],
        "Performance cues:",
    ]
    for cue in report.cues:
        lines.extend(
            _live_cue_lines(
                cue,
                include_events=include_events,
                event_limit=event_limit,
            )
        )
    lines.extend(["Recovery cues:", *[f"- {cue}" for cue in report.recovery_cues]])
    lines.extend(_live_cue_sheet_safety_lines())
    return passive_report_lines(_LIVE_CUE_SHEET_HEADER, lines)


def _live_cue_json(cue: StylePerformanceArcLiveCue) -> dict[str, object]:
    segment = cue.render_segment
    return {
        "position": cue.position,
        "time_window": cue.time_window,
        "style_key": cue.style_key,
        "readiness": cue.readiness,
        "machine_focus": cue.machine_focus,
        "operator_move": cue.operator_move,
        "risk_level": cue.risk_level,
        "recovery_action": cue.recovery_action,
        "listen_for": segment.listen_for,
        "go_no_go_cue": segment.go_no_go_cue,
        "reset_cue": segment.reset_cue,
        "rytm_preview": segment.rytm_preview_summary,
        "analog_four_preview": segment.analog_four_preview_summary,
        "event_row_count": segment.event_row_count,
        "mock_message_count": segment.mock_message_count,
        "deferred_row_count": segment.deferred_row_count,
        "render_row_summary": cue.render_row_summary,
    }


def to_style_performance_arc_live_cue_sheet_json(
    report: StylePerformanceArcLiveCueSheetReport,
) -> dict[str, object]:
    """Return deterministic JSON data for a live cue sheet."""

    plan = report.selected_set_plan
    return {
        "selected": _readiness_entry_json(report.selected_entry),
        "live_render_bundle": to_style_performance_arc_live_render_bundle_json(
            report.live_render_bundle
        ),
        "cue_sheet": {
            "scope": plan.scope,
            "total_minutes": plan.total_minutes,
            "selection_rank": plan.selection_rank,
            "discovery_start": plan.discovery_start,
            "discovery_end": plan.discovery_end,
            "suggested_commands": list(report.suggested_commands),
            "preflight_cues": list(report.preflight_cues),
            "recovery_cues": list(report.recovery_cues),
            "totals": {
                "cues": report.cue_count,
                "segments": report.segment_count,
                "ready": report.ready_segment_count,
                "partial": report.partial_segment_count,
                "blocked": report.blocked_segment_count,
                "event_rows": report.total_event_row_count,
                "mock_messages": report.total_mock_message_count,
                "deferred_rows": report.total_deferred_row_count,
            },
            "cues": [_live_cue_json(cue) for cue in report.cues],
        },
        "safety": list(LIVE_CUE_SHEET_SAFETY_LINES),
    }


_REFERENCE_TERM_STYLE_BOOSTS: Final[Mapping[str, Mapping[str, int]]] = MappingProxyType(
    {
        "jeff mills": MappingProxyType({"mills_hypnotic": 34, "jose_core_techno": 14}),
        "mills": MappingProxyType({"mills_hypnotic": 28, "jose_core_techno": 12}),
        "bell": MappingProxyType({"mills_hypnotic": 24}),
        "bells": MappingProxyType({"mills_hypnotic": 26}),
        "futurist": MappingProxyType({"mills_hypnotic": 24}),
        "futuristic": MappingProxyType({"mills_hypnotic": 24}),
        "oscar mulero": MappingProxyType({"deep_dark_hypnosis": 30, "jose_core_techno": 16}),
        "mulero": MappingProxyType({"deep_dark_hypnosis": 26, "jose_core_techno": 14}),
        "dark": MappingProxyType({"deep_dark_hypnosis": 20, "industrial_dark": 16}),
        "deep": MappingProxyType({"deep_dark_hypnosis": 18}),
        "tunnel": MappingProxyType({"deep_dark_hypnosis": 26}),
        "hypnotic": MappingProxyType(
            {
                "deep_dark_hypnosis": 20,
                "mills_hypnotic": 18,
                "detroit_minimal": 10,
            }
        ),
        "stigmata": MappingProxyType(
            {"birmingham_pressure": 34, "industrial_dark": 24, "jose_core_techno": 18}
        ),
        "birmingham": MappingProxyType(
            {"birmingham_pressure": 36, "industrial_dark": 22, "jose_core_techno": 16}
        ),
        "regis": MappingProxyType({"industrial_dark": 30, "birmingham_pressure": 22}),
        "surgeon": MappingProxyType({"industrial_dark": 30, "birmingham_pressure": 22}),
        "glenn wilson": MappingProxyType({"birmingham_pressure": 28, "industrial_dark": 20}),
        "nightshift": MappingProxyType({"birmingham_pressure": 24}),
        "thomas krome": MappingProxyType({"birmingham_pressure": 24}),
        "krome": MappingProxyType({"birmingham_pressure": 20}),
        "kay d smith": MappingProxyType({"birmingham_pressure": 22}),
        "industrial": MappingProxyType({"industrial_dark": 34, "birmingham_pressure": 22}),
        "raw": MappingProxyType({"birmingham_pressure": 18, "industrial_dark": 14}),
        "hard": MappingProxyType({"birmingham_pressure": 16, "warehouse_peak": 12}),
        "warehouse": MappingProxyType({"warehouse_peak": 24, "jose_core_techno": 12}),
        "peak": MappingProxyType({"warehouse_peak": 26}),
        "pressure": MappingProxyType(
            {
                "birmingham_pressure": 18,
                "warehouse_peak": 16,
                "jose_core_techno": 14,
            }
        ),
        "hardgroove": MappingProxyType({"hardgroove_percussive": 36}),
        "rolling": MappingProxyType({"hardgroove_percussive": 22, "deep_dark_hypnosis": 14}),
        "funky": MappingProxyType({"hardgroove_percussive": 22, "ur_machine_funk": 18}),
        "machine funk": MappingProxyType({"ur_machine_funk": 32}),
        "underground resistance": MappingProxyType({"ur_machine_funk": 26}),
        "ur": MappingProxyType({"ur_machine_funk": 18}),
        "hood": MappingProxyType({"hood_stripped": 26, "detroit_minimal": 14}),
        "robert hood": MappingProxyType({"hood_stripped": 32, "detroit_minimal": 18}),
        "detroit": MappingProxyType(
            {
                "detroit_minimal": 20,
                "mills_hypnotic": 16,
                "ur_machine_funk": 16,
            }
        ),
        "minimal": MappingProxyType({"hood_stripped": 20, "detroit_minimal": 18}),
        "stripped": MappingProxyType({"hood_stripped": 24, "detroit_minimal": 18}),
        "jose": MappingProxyType({"jose_core_techno": 36}),
    }
)

_REFERENCE_TERM_AXIS_BOOSTS: Final[Mapping[str, Mapping[str, int]]] = MappingProxyType(
    {
        "bell": MappingProxyType({"metallicity": 82, "motion_amount": 76}),
        "bells": MappingProxyType({"metallicity": 86, "motion_amount": 78}),
        "futurist": MappingProxyType({"motion_amount": 82, "metallicity": 76}),
        "futuristic": MappingProxyType({"motion_amount": 82, "metallicity": 76}),
        "dark": MappingProxyType({"darkness": 86}),
        "deep": MappingProxyType({"darkness": 78, "space_depth": 78}),
        "tunnel": MappingProxyType({"darkness": 82, "repetition_hypnosis": 86}),
        "hypnotic": MappingProxyType({"repetition_hypnosis": 90}),
        "stigmata": MappingProxyType({"industrial_edge": 92, "noise_grit": 88}),
        "birmingham": MappingProxyType(
            {"industrial_edge": 92, "drive_pressure": 88, "noise_grit": 84}
        ),
        "regis": MappingProxyType({"industrial_edge": 90, "darkness": 88}),
        "surgeon": MappingProxyType({"industrial_edge": 90, "darkness": 86}),
        "glenn wilson": MappingProxyType({"drive_pressure": 88, "noise_grit": 82}),
        "industrial": MappingProxyType({"industrial_edge": 94, "noise_grit": 92, "darkness": 88}),
        "raw": MappingProxyType({"noise_grit": 84, "drive_pressure": 78}),
        "hard": MappingProxyType({"drive_pressure": 82, "warehouse_intensity": 76}),
        "warehouse": MappingProxyType({"warehouse_intensity": 88}),
        "peak": MappingProxyType({"warehouse_intensity": 92, "drive_pressure": 84}),
        "pressure": MappingProxyType({"drive_pressure": 84}),
        "hardgroove": MappingProxyType(
            {"percussive_density": 92, "transient_density": 84, "groove": 80}
        ),
        "rolling": MappingProxyType({"percussive_density": 76, "motion_amount": 70}),
        "percussive": MappingProxyType({"percussive_density": 88, "transient_density": 82}),
        "machine funk": MappingProxyType({"motion_amount": 76, "percussive_density": 78}),
        "detroit": MappingProxyType({"repetition_hypnosis": 78, "minimal_restraint": 62}),
        "minimal": MappingProxyType({"minimal_restraint": 90, "repetition_hypnosis": 84}),
        "stripped": MappingProxyType({"minimal_restraint": 92}),
    }
)

_REFERENCE_PHRASES: Final[tuple[str, ...]] = tuple(
    sorted(
        (
            {
                term
                for term in (
                    tuple(_REFERENCE_TERM_STYLE_BOOSTS)
                    + tuple(_REFERENCE_TERM_AXIS_BOOSTS)
                    + tuple(
                        reference.lower()
                        for arc in STYLE_PERFORMANCE_ARCS.values()
                        for reference in arc.references
                    )
                )
                if " " in term
            }
        ),
        key=lambda term: (-len(term), term),
    )
)
_REFERENCE_SINGLE_TERMS: Final[frozenset[str]] = frozenset(
    term
    for term in (
        tuple(_REFERENCE_TERM_STYLE_BOOSTS)
        + tuple(_REFERENCE_TERM_AXIS_BOOSTS)
        + tuple(
            token
            for arc in STYLE_PERFORMANCE_ARCS.values()
            for source in (
                arc.tags + arc.style_keys + tuple(reference.lower() for reference in arc.references)
            )
            for token in re.sub(r"[^a-z0-9]+", " ", source.lower()).strip().split()
        )
    )
    if " " not in term and len(term) > 2
)


def _reference_match_safety_lines() -> list[str]:
    return [SAFETY_SECTION_HEADER, *[f"- {line}" for line in REFERENCE_MATCH_SAFETY_LINES]]


def _canonical_reference_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _reference_terms_from_text(description: str | None) -> tuple[str, ...]:
    if not description:
        return ()
    normalized = f" {_canonical_reference_text(description)} "
    terms: set[str] = set()
    for phrase in _REFERENCE_PHRASES:
        if f" {_canonical_reference_text(phrase)} " in normalized:
            terms.add(phrase)
    terms.update(token for token in normalized.split() if token in _REFERENCE_SINGLE_TERMS)
    return tuple(sorted(terms))


def _bounded_int(value: float) -> int:
    if value < 0:
        return 0
    if value > 100:
        return 100
    return int(round(value))


def _axis_scores_from_feature_report(report: FeatureReport) -> dict[str, int]:
    scores: dict[str, int] = {}
    if report.low_end_weight:
        scores["low_end_weight"] = _bounded_int(report.low_end_weight * 100)
    density = max(report.kick_density, report.percussion_density)
    if density:
        scores["transient_density"] = _bounded_int(density * 100)
        scores["percussive_density"] = _bounded_int(report.percussion_density * 100)
    if report.kick_density:
        scores["drive_pressure"] = _bounded_int(report.kick_density * 100)
    if report.spectral_brightness:
        scores["attack_sharpness"] = _bounded_int(report.spectral_brightness * 100)
        scores["darkness"] = _bounded_int((1.0 - report.spectral_brightness) * 100)
    if report.texture_noise:
        scores["noise_grit"] = _bounded_int(report.texture_noise * 100)
        scores["industrial_edge"] = _bounded_int((report.texture_noise * 80) + 15)
    if report.tempo_stability:
        scores["repetition_hypnosis"] = _bounded_int(report.tempo_stability * 100)
    if report.bpm:
        bpm_pressure = min(max((report.bpm - 118.0) / 22.0, 0.0), 1.0)
        if bpm_pressure:
            scores["drive_pressure"] = max(
                scores.get("drive_pressure", 0),
                _bounded_int(bpm_pressure * 100),
            )
            scores["warehouse_intensity"] = max(
                scores.get("warehouse_intensity", 0),
                _bounded_int(bpm_pressure * 92),
            )
    if report.energy_arc and any(sample != 0 for sample in report.energy_arc):
        arc = tuple(report.energy_arc)
        arc_peak = max(arc)
        arc_rise = arc[-1] - arc[0]
        if arc_peak:
            scores["warehouse_intensity"] = max(
                scores.get("warehouse_intensity", 0),
                _bounded_int(arc_peak * 100),
            )
        if arc_rise > 0:
            scores["motion_amount"] = max(
                scores.get("motion_amount", 0),
                _bounded_int(min(arc_rise, 1.0) * 100),
            )
        if len(arc) > 1 and max(arc) - min(arc) <= 0.2:
            scores["minimal_restraint"] = max(scores.get("minimal_restraint", 0), 72)
    return {key: value for key, value in scores.items() if key in STYLE_TARGET_VECTOR_AXES}


def _axis_scores_from_terms(terms: Sequence[str]) -> dict[str, int]:
    scores: dict[str, int] = {}
    for term in terms:
        for axis, score in _REFERENCE_TERM_AXIS_BOOSTS.get(term, {}).items():
            if axis not in STYLE_TARGET_VECTOR_AXES:
                continue
            scores[axis] = max(scores.get(axis, 0), score)
    return scores


def _merged_axis_scores(report: FeatureReport, terms: Sequence[str]) -> Mapping[str, int]:
    scores = _axis_scores_from_feature_report(report)
    for axis, score in _axis_scores_from_terms(terms).items():
        scores[axis] = max(scores.get(axis, 0), score)
    return MappingProxyType(dict(sorted(scores.items())))


def _style_score_from_axes(style_key: str, axis_scores: Mapping[str, int]) -> int:
    if not axis_scores:
        return 0
    target = STYLE_TARGET_VECTORS[style_key].as_mapping()
    total = 0
    for axis, score in axis_scores.items():
        total += max(0, 100 - abs(score - target[axis]))
    return _bounded_int(total / len(axis_scores))


def _style_term_bonus(style_key: str, terms: Sequence[str]) -> int:
    bonus = 0
    profile = STYLE_PROFILES[style_key]
    profile_text = _canonical_reference_text(
        " ".join(
            (
                profile.key,
                profile.name,
                profile.summary,
                " ".join(profile.tags),
                " ".join(profile.analyzer_targets),
            )
        )
    )
    for term in terms:
        bonus += _REFERENCE_TERM_STYLE_BOOSTS.get(term, {}).get(style_key, 0)
        if f" {_canonical_reference_text(term)} " in f" {profile_text} ":
            bonus += 4
    return min(bonus, 45)


def _style_scores(
    axis_scores: Mapping[str, int],
    terms: Sequence[str],
) -> Mapping[str, int]:
    scores = {
        style_key: min(
            100,
            _style_score_from_axes(style_key, axis_scores) + _style_term_bonus(style_key, terms),
        )
        for style_key in STYLE_PROFILES
    }
    return MappingProxyType(scores)


def _arc_text(arc: StylePerformanceArc) -> str:
    return _canonical_reference_text(
        " ".join(
            (
                arc.key,
                arc.name,
                arc.summary,
                " ".join(arc.references),
                " ".join(arc.tags),
                " ".join(arc.style_keys),
                " ".join(arc.operator_notes),
            )
        )
    )


def _arc_direct_score(
    arc: StylePerformanceArc, terms: Sequence[str]
) -> tuple[int, tuple[str, ...]]:
    arc_text = f" {_arc_text(arc)} "
    matched: list[str] = []
    score = 0
    for term in terms:
        canonical = _canonical_reference_text(term)
        if not canonical or f" {canonical} " not in arc_text:
            continue
        matched.append(term)
        score += 14 if " " in term else 6
    return min(score, 85), tuple(sorted(set(matched)))


def _reference_match_entry(
    *,
    position: int,
    arc: StylePerformanceArc,
    style_scores: Mapping[str, int],
    terms: Sequence[str],
) -> StylePerformanceArcReferenceMatchEntry:
    style_key_scores = tuple(style_scores[style_key] for style_key in arc.style_keys)
    mean_style = sum(style_key_scores) / len(style_key_scores)
    max_style = max(style_key_scores)
    vector_score = _bounded_int((mean_style * 0.6) + (max_style * 0.4))
    direct_score, matched_terms = _arc_direct_score(arc, terms)
    matched_style_keys = tuple(
        style_key for style_key in arc.style_keys if style_scores[style_key] >= 70
    )
    score = _bounded_int((vector_score * 0.65) + (direct_score * 0.35))
    if score >= 80:
        operator_action = "audition this arc first; evidence is strong enough for rehearsal prep"
    elif score >= 55:
        operator_action = "audition carefully; evidence is partial but useful"
    else:
        operator_action = "use only as a weak planning hint; refine the reference"
    return StylePerformanceArcReferenceMatchEntry(
        position=position,
        arc=arc,
        score=score,
        vector_score=vector_score,
        direct_score=direct_score,
        max_style_score=max_style,
        matched_terms=matched_terms,
        matched_style_keys=matched_style_keys,
        operator_action=operator_action,
    )


def _rank_reference_matches(
    *,
    axis_scores: Mapping[str, int],
    terms: Sequence[str],
) -> tuple[StylePerformanceArcReferenceMatchEntry, ...]:
    style_scores = _style_scores(axis_scores, terms)
    unsorted_entries = tuple(
        _reference_match_entry(
            position=0,
            arc=arc,
            style_scores=style_scores,
            terms=terms,
        )
        for arc in STYLE_PERFORMANCE_ARCS.values()
    )
    sorted_entries = sorted(
        unsorted_entries,
        key=lambda entry: (
            -entry.score,
            -entry.direct_score,
            -entry.vector_score,
            -entry.max_style_score,
            -len(entry.matched_style_keys),
            entry.arc.default_selection_rank,
            entry.arc.default_total_minutes,
            entry.arc.key,
        ),
    )
    return tuple(
        StylePerformanceArcReferenceMatchEntry(
            position=index,
            arc=entry.arc,
            score=entry.score,
            vector_score=entry.vector_score,
            direct_score=entry.direct_score,
            max_style_score=entry.max_style_score,
            matched_terms=entry.matched_terms,
            matched_style_keys=entry.matched_style_keys,
            operator_action=entry.operator_action,
        )
        for index, entry in enumerate(sorted_entries, start=1)
    )


def _source_count(
    *,
    description: str | None,
    feature_report: FeatureReport | None,
    audio_path: Path | None,
    library_path: Path | None,
) -> int:
    return sum(
        source is not None for source in (description, feature_report, audio_path, library_path)
    )


def _feature_report_for_reference_match(
    *,
    description: str | None,
    feature_report: FeatureReport | None,
    audio_path: Path | None,
    library_path: Path | None,
) -> tuple[str, str | None, FeatureReport]:
    source_count = _source_count(
        description=description,
        feature_report=feature_report,
        audio_path=audio_path,
        library_path=library_path,
    )
    if source_count != 1:
        raise ValueError("reference match requires exactly one reference source")
    if description is not None:
        if not description.strip():
            raise ValueError("description must include reference evidence")
        from ..style_analysis import extract_from_description

        return "description", None, extract_from_description(description)
    if feature_report is not None:
        return "feature-report", None, feature_report
    if audio_path is not None:
        from ..style_analysis import extract_from_audio

        return "audio", str(audio_path), extract_from_audio(audio_path)
    if library_path is not None:
        from ..style_analysis import analyze_library

        return "library", str(library_path), analyze_library(library_path)
    raise ValueError(  # pragma: no cover - defensive after source-count validation.
        "reference match requires exactly one reference source"
    )


def build_style_performance_arc_reference_match_report(
    *,
    description: str | None = None,
    feature_report: FeatureReport | None = None,
    audio_path: Path | None = None,
    library_path: Path | None = None,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
    include_live_cue_sheet: bool = False,
) -> StylePerformanceArcReferenceMatchReport:
    """Return passive reference-to-arc matches and optional live cue sheet."""

    source_kind, source_reference, measured_report = _feature_report_for_reference_match(
        description=description,
        feature_report=feature_report,
        audio_path=audio_path,
        library_path=library_path,
    )
    terms = _reference_terms_from_text(description)
    axis_scores = _merged_axis_scores(measured_report, terms)
    if not axis_scores and not terms:
        raise ValueError("reference match requires reference evidence")
    matches = _rank_reference_matches(axis_scores=axis_scores, terms=terms)
    live_cue_sheet = None
    if include_live_cue_sheet and (
        rytm_sysex_path is not None or analog_four_sysex_path is not None
    ):
        live_cue_sheet = build_style_performance_arc_live_cue_sheet_report(
            (matches[0].arc.key,),
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
        )
    return StylePerformanceArcReferenceMatchReport(
        source_kind=source_kind,
        source_reference=source_reference,
        description=description,
        feature_report=measured_report,
        axis_scores=axis_scores,
        matched_terms=terms,
        matches=matches,
        live_cue_sheet=live_cue_sheet,
    )


def _feature_report_json(report: FeatureReport) -> dict[str, object]:
    return {
        "source_type": report.source_type.value,
        "confidence": report.confidence.value,
        "bpm": report.bpm,
        "tempo_stability": report.tempo_stability,
        "kick_density": report.kick_density,
        "percussion_density": report.percussion_density,
        "low_end_weight": report.low_end_weight,
        "spectral_brightness": report.spectral_brightness,
        "texture_noise": report.texture_noise,
        "energy_arc": list(report.energy_arc),
        "content_hash": report.content_hash,
        "derived_at": report.derived_at,
    }


def _reference_match_entry_json(
    entry: StylePerformanceArcReferenceMatchEntry,
) -> dict[str, object]:
    return {
        "position": entry.position,
        "arc": to_style_performance_arc_json(entry.arc),
        "score": entry.score,
        "vector_score": entry.vector_score,
        "direct_score": entry.direct_score,
        "max_style_score": entry.max_style_score,
        "matched_terms": list(entry.matched_terms),
        "matched_style_keys": list(entry.matched_style_keys),
        "operator_action": entry.operator_action,
    }


def to_style_performance_arc_reference_match_json(
    report: StylePerformanceArcReferenceMatchReport,
) -> dict[str, object]:
    """Return deterministic JSON data for a reference-match report."""

    return {
        "reference_match": {
            "source_kind": report.source_kind,
            "source_reference": report.source_reference,
            "description": report.description,
            "feature_report": _feature_report_json(report.feature_report),
            "axis_scores": dict(report.axis_scores),
            "matched_terms": list(report.matched_terms),
            "selected": _reference_match_entry_json(report.selected_match),
            "matches": [_reference_match_entry_json(entry) for entry in report.matches],
            "embedded_live_cue_sheet": report.live_cue_sheet is not None,
        },
        "live_cue_sheet": (
            None
            if report.live_cue_sheet is None
            else to_style_performance_arc_live_cue_sheet_json(report.live_cue_sheet)
        ),
        "safety": list(REFERENCE_MATCH_SAFETY_LINES),
    }


def _reference_match_lines(report: StylePerformanceArcReferenceMatchReport) -> list[str]:
    selected = report.selected_match
    confidence = report.feature_report.confidence.value
    lines = [
        "Reference match summary:",
        f"- Source kind: {report.source_kind}",
        f"- Feature confidence: {confidence}",
        f"- Feature report hash: {report.feature_report.content_hash}",
        f"- Axis evidence count: {len(report.axis_scores)}",
        f"- Matched term count: {len(report.matched_terms)}",
        f"- Selected arc: {selected.arc.key} / {selected.arc.name}",
        f"- Selected score: {selected.score}",
        f"- Selected action: {selected.operator_action}",
        "Axis evidence:",
        *[f"- {axis}: {score}" for axis, score in report.axis_scores.items()],
        "Matched terms:",
        *[f"- {term}" for term in report.matched_terms],
        "Ranked arc matches:",
        *[
            (
                f"- {entry.position}. {entry.arc.key} | {entry.arc.name} | "
                f"score {entry.score} | vector {entry.vector_score} | direct {entry.direct_score}"
            )
            for entry in report.matches
        ],
    ]
    if report.source_reference is not None:
        lines.insert(2, f"- Source reference: {report.source_reference}")
    return lines


def format_style_performance_arc_reference_match_report(
    report: StylePerformanceArcReferenceMatchReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic reference-match lines."""

    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    lines = _reference_match_lines(report)
    if report.live_cue_sheet is None:
        lines.append("Embedded live cue sheet: none")
    else:
        lines.append("Embedded live cue sheet:")
        lines.extend(
            format_style_performance_arc_live_cue_sheet_report(
                report.live_cue_sheet,
                include_events=include_events,
                event_limit=event_limit,
            )
        )
    lines.extend(_reference_match_safety_lines())
    return passive_report_lines(_REFERENCE_MATCH_HEADER, lines)


def _parse_no_args(argv: Sequence[str]) -> dict[str, object]:
    if argv:
        raise ValueError("command takes no arguments")
    return {}


def _parse_arc_key(argv: Sequence[str]) -> dict[str, object]:
    if len(argv) != 1:
        raise ValueError("command requires exactly one arc key")
    return {"key": argv[0]}


def _parse_query(argv: Sequence[str]) -> dict[str, object]:
    if len(argv) != 1:
        raise ValueError("command requires exactly one query")
    return {"query": argv[0]}


def _parse_nonnegative_int(value: str, *, option: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{option} must be >= 0")
    return parsed


def _parse_positive_int(value: str, *, option: str) -> int:
    parsed = _parse_nonnegative_int(value, option=option)
    if parsed < 1:
        raise ValueError(f"{option} must be >= 1")
    return parsed


def _pop_option_value(remaining: list[str], *, usage: str = _SET_PLAN_USAGE) -> str:
    if not remaining:
        raise ValueError(usage)
    return remaining.pop(0)


def _parse_arc_set_plan_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if not argv:
        raise ValueError(_SET_PLAN_USAGE)
    arc_key = argv[0]
    if arc_key.startswith("--"):
        raise ValueError(_SET_PLAN_USAGE)
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank: int | None = None
    total_minutes: int | None = None
    segment_minutes: int | None = None
    discovery_start: int | None = None
    discovery_end: int | None = None
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    remaining = list(argv[1:])
    while remaining:
        option = remaining.pop(0)
        if option == "--events":
            include_events = True
            continue
        if option == "--json":
            json_output = True
            continue
        if option not in _SET_PLAN_OPTIONS:
            raise ValueError(_SET_PLAN_USAGE)
        value = _pop_option_value(remaining, usage=_SET_PLAN_USAGE)
        if option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--rank":
            selection_rank = _parse_positive_int(value, option=option)
        elif option == "--total-minutes":
            total_minutes = _parse_positive_int(value, option=option)
        elif option == "--segment-minutes":
            segment_minutes = _parse_positive_int(value, option=option)
        elif option == "--discovery-start":
            discovery_start = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery-end":
            discovery_end = _parse_nonnegative_int(value, option=option)
        else:
            event_limit = _parse_nonnegative_int(value, option=option)
    return {
        "arc_key": arc_key,
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": scope,
        "selection_rank": selection_rank,
        "total_minutes": total_minutes,
        "segment_minutes": segment_minutes,
        "discovery_start": discovery_start,
        "discovery_end": discovery_end,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _parse_arc_readiness_cli_args(argv: Sequence[str]) -> dict[str, object]:
    remaining = list(argv)
    arc_keys: list[str] = []
    while remaining and not remaining[0].startswith("--"):
        arc_keys.append(remaining.pop(0))
    if remaining and remaining[0] == "--json" and not arc_keys:
        raise ValueError(_READINESS_USAGE)
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank: int | None = None
    total_minutes: int | None = None
    segment_minutes: int | None = None
    discovery_start: int | None = None
    discovery_end: int | None = None
    entry_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
            continue
        if option not in _READINESS_OPTIONS:
            raise ValueError(_READINESS_USAGE)
        value = _pop_option_value(remaining, usage=_READINESS_USAGE)
        if option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--rank":
            selection_rank = _parse_positive_int(value, option=option)
        elif option == "--total-minutes":
            total_minutes = _parse_positive_int(value, option=option)
        elif option == "--segment-minutes":
            segment_minutes = _parse_positive_int(value, option=option)
        elif option == "--discovery-start":
            discovery_start = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery-end":
            discovery_end = _parse_nonnegative_int(value, option=option)
        else:
            entry_limit = _parse_nonnegative_int(value, option=option)
    return {
        "arc_keys": None if not arc_keys else tuple(arc_keys),
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": scope,
        "selection_rank": selection_rank,
        "total_minutes": total_minutes,
        "segment_minutes": segment_minutes,
        "discovery_start": discovery_start,
        "discovery_end": discovery_end,
        "entry_limit": entry_limit,
        "json_output": json_output,
    }


def _parse_arc_audition_packet_cli_args(argv: Sequence[str]) -> dict[str, object]:
    remaining = list(argv)
    arc_keys: list[str] = []
    while remaining and not remaining[0].startswith("--"):
        arc_keys.append(remaining.pop(0))
    if remaining and remaining[0] == "--json" and not arc_keys:
        raise ValueError(_AUDITION_PACKET_USAGE)
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank: int | None = None
    total_minutes: int | None = None
    segment_minutes: int | None = None
    discovery_start: int | None = None
    discovery_end: int | None = None
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    while remaining:
        option = remaining.pop(0)
        if option == "--events":
            include_events = True
            continue
        if option == "--json":
            json_output = True
            continue
        if option not in _AUDITION_PACKET_OPTIONS:
            raise ValueError(_AUDITION_PACKET_USAGE)
        value = _pop_option_value(remaining, usage=_AUDITION_PACKET_USAGE)
        if option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--rank":
            selection_rank = _parse_positive_int(value, option=option)
        elif option == "--total-minutes":
            total_minutes = _parse_positive_int(value, option=option)
        elif option == "--segment-minutes":
            segment_minutes = _parse_positive_int(value, option=option)
        elif option == "--discovery-start":
            discovery_start = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery-end":
            discovery_end = _parse_nonnegative_int(value, option=option)
        else:
            event_limit = _parse_nonnegative_int(value, option=option)
    return {
        "arc_keys": None if not arc_keys else tuple(arc_keys),
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": scope,
        "selection_rank": selection_rank,
        "total_minutes": total_minutes,
        "segment_minutes": segment_minutes,
        "discovery_start": discovery_start,
        "discovery_end": discovery_end,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _parse_arc_rehearsal_manifest_cli_args(argv: Sequence[str]) -> dict[str, object]:
    remaining = list(argv)
    arc_keys: list[str] = []
    while remaining and not remaining[0].startswith("--"):
        arc_keys.append(remaining.pop(0))
    if remaining and remaining[0] == "--json" and not arc_keys:
        raise ValueError(_REHEARSAL_MANIFEST_USAGE)
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank: int | None = None
    total_minutes: int | None = None
    segment_minutes: int | None = None
    discovery_start: int | None = None
    discovery_end: int | None = None
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    while remaining:
        option = remaining.pop(0)
        if option == "--events":
            include_events = True
            continue
        if option == "--json":
            json_output = True
            continue
        if option not in _REHEARSAL_MANIFEST_OPTIONS:
            raise ValueError(_REHEARSAL_MANIFEST_USAGE)
        value = _pop_option_value(remaining, usage=_REHEARSAL_MANIFEST_USAGE)
        if option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--rank":
            selection_rank = _parse_positive_int(value, option=option)
        elif option == "--total-minutes":
            total_minutes = _parse_positive_int(value, option=option)
        elif option == "--segment-minutes":
            segment_minutes = _parse_positive_int(value, option=option)
        elif option == "--discovery-start":
            discovery_start = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery-end":
            discovery_end = _parse_nonnegative_int(value, option=option)
        else:
            event_limit = _parse_nonnegative_int(value, option=option)
    return {
        "arc_keys": None if not arc_keys else tuple(arc_keys),
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": scope,
        "selection_rank": selection_rank,
        "total_minutes": total_minutes,
        "segment_minutes": segment_minutes,
        "discovery_start": discovery_start,
        "discovery_end": discovery_end,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _parse_arc_live_session_packet_cli_args(argv: Sequence[str]) -> dict[str, object]:
    remaining = list(argv)
    arc_keys: list[str] = []
    while remaining and not remaining[0].startswith("--"):
        arc_keys.append(remaining.pop(0))
    if remaining and remaining[0] == "--json" and not arc_keys:
        raise ValueError(_LIVE_SESSION_PACKET_USAGE)
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank: int | None = None
    total_minutes: int | None = None
    segment_minutes: int | None = None
    discovery_start: int | None = None
    discovery_end: int | None = None
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    while remaining:
        option = remaining.pop(0)
        if option == "--events":
            include_events = True
            continue
        if option == "--json":
            json_output = True
            continue
        if option not in _LIVE_SESSION_PACKET_OPTIONS:
            raise ValueError(_LIVE_SESSION_PACKET_USAGE)
        value = _pop_option_value(remaining, usage=_LIVE_SESSION_PACKET_USAGE)
        if option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--rank":
            selection_rank = _parse_positive_int(value, option=option)
        elif option == "--total-minutes":
            total_minutes = _parse_positive_int(value, option=option)
        elif option == "--segment-minutes":
            segment_minutes = _parse_positive_int(value, option=option)
        elif option == "--discovery-start":
            discovery_start = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery-end":
            discovery_end = _parse_nonnegative_int(value, option=option)
        else:
            event_limit = _parse_nonnegative_int(value, option=option)
    return {
        "arc_keys": None if not arc_keys else tuple(arc_keys),
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": scope,
        "selection_rank": selection_rank,
        "total_minutes": total_minutes,
        "segment_minutes": segment_minutes,
        "discovery_start": discovery_start,
        "discovery_end": discovery_end,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _parse_arc_live_render_bundle_cli_args(argv: Sequence[str]) -> dict[str, object]:
    remaining = list(argv)
    arc_keys: list[str] = []
    while remaining and not remaining[0].startswith("--"):
        arc_keys.append(remaining.pop(0))
    if remaining and remaining[0] == "--json" and not arc_keys:
        raise ValueError(_LIVE_RENDER_BUNDLE_USAGE)
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank: int | None = None
    total_minutes: int | None = None
    segment_minutes: int | None = None
    discovery_start: int | None = None
    discovery_end: int | None = None
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    while remaining:
        option = remaining.pop(0)
        if option == "--events":
            include_events = True
            continue
        if option == "--json":
            json_output = True
            continue
        if option not in _LIVE_RENDER_BUNDLE_OPTIONS:
            raise ValueError(_LIVE_RENDER_BUNDLE_USAGE)
        value = _pop_option_value(remaining, usage=_LIVE_RENDER_BUNDLE_USAGE)
        if option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--rank":
            selection_rank = _parse_positive_int(value, option=option)
        elif option == "--total-minutes":
            total_minutes = _parse_positive_int(value, option=option)
        elif option == "--segment-minutes":
            segment_minutes = _parse_positive_int(value, option=option)
        elif option == "--discovery-start":
            discovery_start = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery-end":
            discovery_end = _parse_nonnegative_int(value, option=option)
        else:
            event_limit = _parse_nonnegative_int(value, option=option)
    return {
        "arc_keys": None if not arc_keys else tuple(arc_keys),
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": scope,
        "selection_rank": selection_rank,
        "total_minutes": total_minutes,
        "segment_minutes": segment_minutes,
        "discovery_start": discovery_start,
        "discovery_end": discovery_end,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _parse_arc_live_cue_sheet_cli_args(argv: Sequence[str]) -> dict[str, object]:
    remaining = list(argv)
    arc_keys: list[str] = []
    while remaining and not remaining[0].startswith("--"):
        arc_keys.append(remaining.pop(0))
    if remaining and remaining[0] == "--json" and not arc_keys:
        raise ValueError(_LIVE_CUE_SHEET_USAGE)
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank: int | None = None
    total_minutes: int | None = None
    segment_minutes: int | None = None
    discovery_start: int | None = None
    discovery_end: int | None = None
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    while remaining:
        option = remaining.pop(0)
        if option == "--events":
            include_events = True
            continue
        if option == "--json":
            json_output = True
            continue
        if option not in _LIVE_CUE_SHEET_OPTIONS:
            raise ValueError(_LIVE_CUE_SHEET_USAGE)
        value = _pop_option_value(remaining, usage=_LIVE_CUE_SHEET_USAGE)
        if option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--rank":
            selection_rank = _parse_positive_int(value, option=option)
        elif option == "--total-minutes":
            total_minutes = _parse_positive_int(value, option=option)
        elif option == "--segment-minutes":
            segment_minutes = _parse_positive_int(value, option=option)
        elif option == "--discovery-start":
            discovery_start = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery-end":
            discovery_end = _parse_nonnegative_int(value, option=option)
        else:
            event_limit = _parse_nonnegative_int(value, option=option)
    return {
        "arc_keys": None if not arc_keys else tuple(arc_keys),
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": scope,
        "selection_rank": selection_rank,
        "total_minutes": total_minutes,
        "segment_minutes": segment_minutes,
        "discovery_start": discovery_start,
        "discovery_end": discovery_end,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _parse_arc_reference_match_cli_args(argv: Sequence[str]) -> dict[str, object]:
    remaining = list(argv)
    description: str | None = None
    audio_path: Path | None = None
    library_path: Path | None = None
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank: int | None = None
    total_minutes: int | None = None
    segment_minutes: int | None = None
    discovery_start: int | None = None
    discovery_end: int | None = None
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    while remaining:
        option = remaining.pop(0)
        if option == "--events":
            include_events = True
            continue
        if option == "--json":
            json_output = True
            continue
        if option not in _REFERENCE_MATCH_OPTIONS:
            raise ValueError(_REFERENCE_MATCH_USAGE)
        value = _pop_option_value(remaining, usage=_REFERENCE_MATCH_USAGE)
        if option == "--description":
            description = value
        elif option == "--audio":
            audio_path = Path(value)
        elif option == "--library":
            library_path = Path(value)
        elif option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--rank":
            selection_rank = _parse_positive_int(value, option=option)
        elif option == "--total-minutes":
            total_minutes = _parse_positive_int(value, option=option)
        elif option == "--segment-minutes":
            segment_minutes = _parse_positive_int(value, option=option)
        elif option == "--discovery-start":
            discovery_start = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery-end":
            discovery_end = _parse_nonnegative_int(value, option=option)
        else:
            event_limit = _parse_nonnegative_int(value, option=option)
    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if (
        _source_count(
            description=description,
            feature_report=None,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError("reference match requires exactly one reference source")
    return {
        "description": description,
        "audio_path": audio_path,
        "library_path": library_path,
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": scope,
        "selection_rank": selection_rank,
        "total_minutes": total_minutes,
        "segment_minutes": segment_minutes,
        "discovery_start": discovery_start,
        "discovery_end": discovery_end,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _write_lines(lines: Sequence[str]) -> int:
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _handle_style_performance_arc_report() -> int:
    return _write_lines(format_style_performance_arc_report())


def _handle_style_performance_arc_list() -> int:
    return _write_lines(format_style_performance_arc_list())


def _handle_style_performance_arc_inspection(key: str) -> int:
    lines = format_style_performance_arc_inspection(key)
    output = "\n".join(lines)
    if "Found: True" in lines:
        sys.stdout.write(f"{output}\n")
        return 0
    sys.stderr.write(f"{output}\n")
    return 1


def _handle_style_performance_arc_search(query: str) -> int:
    return _write_lines(format_style_performance_arc_search(query))


def _handle_style_performance_arc_set_plan_report(
    *,
    arc_key: str,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str | None,
    selection_rank: int | None,
    total_minutes: int | None,
    segment_minutes: int | None,
    discovery_start: int | None,
    discovery_end: int | None,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_set_plan_report(
            arc_key,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_set_plan_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_set_plan_report(
            report,
            include_events=include_events,
            event_limit=event_limit,
        )
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    return _write_lines(lines)


def _handle_style_performance_arc_readiness_report(
    *,
    arc_keys: Sequence[str] | None,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str | None,
    selection_rank: int | None,
    total_minutes: int | None,
    segment_minutes: int | None,
    discovery_start: int | None,
    discovery_end: int | None,
    entry_limit: int,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_readiness_report(
            arc_keys,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_readiness_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_readiness_report(
            report,
            entry_limit=entry_limit,
        )
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    return _write_lines(lines)


def _handle_style_performance_arc_audition_packet_report(
    *,
    arc_keys: Sequence[str] | None,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str | None,
    selection_rank: int | None,
    total_minutes: int | None,
    segment_minutes: int | None,
    discovery_start: int | None,
    discovery_end: int | None,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_audition_packet_report(
            arc_keys,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_audition_packet_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_audition_packet_report(
            report,
            include_events=include_events,
            event_limit=event_limit,
        )
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    return _write_lines(lines)


def _handle_style_performance_arc_rehearsal_manifest_report(
    *,
    arc_keys: Sequence[str] | None,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str | None,
    selection_rank: int | None,
    total_minutes: int | None,
    segment_minutes: int | None,
    discovery_start: int | None,
    discovery_end: int | None,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_rehearsal_manifest_report(
            arc_keys,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_rehearsal_manifest_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_rehearsal_manifest_report(
            report,
            include_events=include_events,
            event_limit=event_limit,
        )
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    return _write_lines(lines)


def _handle_style_performance_arc_live_session_packet_report(
    *,
    arc_keys: Sequence[str] | None,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str | None,
    selection_rank: int | None,
    total_minutes: int | None,
    segment_minutes: int | None,
    discovery_start: int | None,
    discovery_end: int | None,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_session_packet_report(
            arc_keys,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_session_packet_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_session_packet_report(
            report,
            include_events=include_events,
            event_limit=event_limit,
        )
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    return _write_lines(lines)


def _handle_style_performance_arc_live_render_bundle_report(
    *,
    arc_keys: Sequence[str] | None,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str | None,
    selection_rank: int | None,
    total_minutes: int | None,
    segment_minutes: int | None,
    discovery_start: int | None,
    discovery_end: int | None,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_render_bundle_report(
            arc_keys,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_render_bundle_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_render_bundle_report(
            report,
            include_events=include_events,
            event_limit=event_limit,
        )
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    return _write_lines(lines)


def _handle_style_performance_arc_live_cue_sheet_report(
    *,
    arc_keys: Sequence[str] | None,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str | None,
    selection_rank: int | None,
    total_minutes: int | None,
    segment_minutes: int | None,
    discovery_start: int | None,
    discovery_end: int | None,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_cue_sheet_report(
            arc_keys,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_cue_sheet_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_cue_sheet_report(
            report,
            include_events=include_events,
            event_limit=event_limit,
        )
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    return _write_lines(lines)


def _handle_style_performance_arc_reference_match_report(
    *,
    description: str | None,
    audio_path: Path | None,
    library_path: Path | None,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str | None,
    selection_rank: int | None,
    total_minutes: int | None,
    segment_minutes: int | None,
    discovery_start: int | None,
    discovery_end: int | None,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_reference_match_report(
            description=description,
            audio_path=audio_path,
            library_path=library_path,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
            include_live_cue_sheet=(
                rytm_sysex_path is not None or analog_four_sysex_path is not None
            ),
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_reference_match_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_reference_match_report(
            report,
            include_events=include_events,
            event_limit=event_limit,
        )
    except (
        OSError,
        ValueError,
        RuntimeError,
        NotImplementedError,
        TypeError,
        KeyError,
    ) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    return _write_lines(lines)


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_REPORT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-report",
    summary="Print the passive style performance arc report.",
    args_parser=_parse_no_args,
    handler=_handle_style_performance_arc_report,
)
LIST_STYLE_PERFORMANCE_ARCS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="list-style-performance-arcs",
    summary="List passive style performance arc keys and names.",
    args_parser=_parse_no_args,
    handler=_handle_style_performance_arc_list,
)
INSPECT_STYLE_PERFORMANCE_ARC_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="inspect-style-performance-arc",
    summary="Inspect passive style performance arc metadata by key.",
    args_parser=_parse_arc_key,
    handler=_handle_style_performance_arc_inspection,
)
SEARCH_STYLE_PERFORMANCE_ARCS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="search-style-performance-arcs",
    summary="Search passive style performance arc metadata.",
    args_parser=_parse_query,
    handler=_handle_style_performance_arc_search,
)
STYLE_PERFORMANCE_ARC_SET_PLAN_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-set-plan-report",
    summary="Print passive timed performance set plans from a reference arc.",
    args_parser=_parse_arc_set_plan_cli_args,
    handler=_handle_style_performance_arc_set_plan_report,
    error_formatter=_format_cli_error,
)
STYLE_PERFORMANCE_ARC_READINESS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-readiness-report",
    summary="Rank passive reference arcs against saved kit banks.",
    args_parser=_parse_arc_readiness_cli_args,
    handler=_handle_style_performance_arc_readiness_report,
    error_formatter=_format_cli_error,
)
STYLE_PERFORMANCE_ARC_AUDITION_PACKET_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-audition-packet-report",
    summary="Build passive best-arc audition packets from saved kit banks.",
    args_parser=_parse_arc_audition_packet_cli_args,
    handler=_handle_style_performance_arc_audition_packet_report,
    error_formatter=_format_cli_error,
)
STYLE_PERFORMANCE_ARC_REHEARSAL_MANIFEST_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-rehearsal-manifest-report",
    summary="Build passive reference-arc rehearsal manifests from saved kit banks.",
    args_parser=_parse_arc_rehearsal_manifest_cli_args,
    handler=_handle_style_performance_arc_rehearsal_manifest_report,
    error_formatter=_format_cli_error,
)
STYLE_PERFORMANCE_ARC_LIVE_SESSION_PACKET_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-session-packet-report",
    summary="Build passive live rehearsal session packets from saved kit banks.",
    args_parser=_parse_arc_live_session_packet_cli_args,
    handler=_handle_style_performance_arc_live_session_packet_report,
    error_formatter=_format_cli_error,
)
STYLE_PERFORMANCE_ARC_LIVE_RENDER_BUNDLE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-render-bundle-report",
    summary="Build passive live render bundles from saved kit banks.",
    args_parser=_parse_arc_live_render_bundle_cli_args,
    handler=_handle_style_performance_arc_live_render_bundle_report,
    error_formatter=_format_cli_error,
)
STYLE_PERFORMANCE_ARC_LIVE_CUE_SHEET_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-cue-sheet-report",
    summary="Build passive live performance cue sheets from saved kit banks.",
    args_parser=_parse_arc_live_cue_sheet_cli_args,
    handler=_handle_style_performance_arc_live_cue_sheet_report,
    error_formatter=_format_cli_error,
)
STYLE_PERFORMANCE_ARC_REFERENCE_MATCH_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-reference-match-report",
    summary="Match references to passive performance arcs and optional cue sheets.",
    args_parser=_parse_arc_reference_match_cli_args,
    handler=_handle_style_performance_arc_reference_match_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_REPORT_CLI_COMMAND)
register(LIST_STYLE_PERFORMANCE_ARCS_CLI_COMMAND)
register(INSPECT_STYLE_PERFORMANCE_ARC_CLI_COMMAND)
register(SEARCH_STYLE_PERFORMANCE_ARCS_CLI_COMMAND)
register(STYLE_PERFORMANCE_ARC_SET_PLAN_CLI_COMMAND)
register(STYLE_PERFORMANCE_ARC_READINESS_CLI_COMMAND)
register(STYLE_PERFORMANCE_ARC_AUDITION_PACKET_CLI_COMMAND)
register(STYLE_PERFORMANCE_ARC_REHEARSAL_MANIFEST_CLI_COMMAND)
register(STYLE_PERFORMANCE_ARC_LIVE_SESSION_PACKET_CLI_COMMAND)
register(STYLE_PERFORMANCE_ARC_LIVE_RENDER_BUNDLE_CLI_COMMAND)
register(STYLE_PERFORMANCE_ARC_LIVE_CUE_SHEET_CLI_COMMAND)
register(STYLE_PERFORMANCE_ARC_REFERENCE_MATCH_CLI_COMMAND)

__all__ = [
    "AUDITION_PACKET_SAFETY_LINES",
    "AUDITION_PACKET_TITLE",
    "INSPECT_STYLE_PERFORMANCE_ARC_CLI_COMMAND",
    "LIST_STYLE_PERFORMANCE_ARCS_CLI_COMMAND",
    "LIVE_CUE_SHEET_SAFETY_LINES",
    "LIVE_CUE_SHEET_TITLE",
    "LIVE_SESSION_PACKET_SAFETY_LINES",
    "LIVE_SESSION_PACKET_TITLE",
    "LIVE_RENDER_BUNDLE_SAFETY_LINES",
    "LIVE_RENDER_BUNDLE_TITLE",
    "REPORT_TITLE",
    "REHEARSAL_MANIFEST_SAFETY_LINES",
    "REHEARSAL_MANIFEST_TITLE",
    "SAFETY_LINES",
    "SEARCH_STYLE_PERFORMANCE_ARCS_CLI_COMMAND",
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
    "StylePerformanceArcRehearsalManifestReport",
    "StylePerformanceArcRehearsalSegment",
    "StylePerformanceArcReadinessEntry",
    "StylePerformanceArcReadinessReport",
    "StylePerformanceArcSetPlanReport",
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
