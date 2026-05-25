"""Titles, safety lines, USAGE strings, and option tuples for the style
performance arc reports.

These constants were moved out of ``reports/style_performance_arcs.py``
in PR 11. They are imported by every concern submodule in the
``style_performance`` subpackage. The facade re-exports the public
constants so external callers keep working unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from ..formatter import PassiveReportHeader

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

# Reported in every passive header for this concern. Tests, fixtures, and
# operators rely on this exact string; keep it stable even though the
# implementation now lives under ``reports/style_performance/`` — the
# public facade is ``reports.style_performance_arcs``.
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
    "optional live cue sheet and stage packet use saved-kit snapshots only",
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
    "[<arc-key> ...] [--rytm <syx-path>] [--analog-four <syx-path>] "
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
