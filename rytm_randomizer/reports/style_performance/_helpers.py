"""Shared helpers used across the style performance arc concern modules.

These were private module-level helpers in the original
``reports/style_performance_arcs.py``. They are imported by every
concern submodule in the ``style_performance`` subpackage but are NOT
re-exported from the public facade — they remain implementation detail.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType

from ...data.style_performance_arcs import STYLE_PERFORMANCE_ARCS, StylePerformanceArc
from ..formatter import SAFETY_SECTION_HEADER
from ._constants import (
    AUDITION_PACKET_SAFETY_LINES,
    LIVE_CUE_SHEET_SAFETY_LINES,
    LIVE_RENDER_BUNDLE_SAFETY_LINES,
    LIVE_SESSION_PACKET_SAFETY_LINES,
    REFERENCE_MATCH_SAFETY_LINES,
    REHEARSAL_MANIFEST_SAFETY_LINES,
    SAFETY_LINES,
)


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


def _reference_match_safety_lines() -> list[str]:
    return [SAFETY_SECTION_HEADER, *[f"- {line}" for line in REFERENCE_MATCH_SAFETY_LINES]]


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


def _number_sequence(values: Sequence[int]) -> str:
    if not values:
        return "none"
    return ", ".join(str(value) for value in values)


def _string_sequence(values: Sequence[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def _readiness_from_counts(
    *,
    blocked_segment_count: int,
    partial_segment_count: int,
    total_deferred_row_count: int,
    total_event_row_count: int,
) -> str:
    if blocked_segment_count:
        return "blocked"
    if partial_segment_count or total_deferred_row_count:
        return "partial"
    if total_event_row_count:
        return "ready"
    return "empty"
