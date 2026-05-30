"""CLI parsers, dispatchers, and command registrations for the passive
style performance arc family of reports.

This module owns everything between the report builders/formatters and
the global CLI registry: arg parsing, dispatcher handlers that build
the report and print the deterministic text (or JSON) to stdout, and
the :class:`~rytm_randomizer.cli_registry.CliCommand` definitions that
register the commands at import time.

Importing this module performs CLI registration via
:func:`~rytm_randomizer.cli_registry.register`. The public facade
``reports.style_performance_arcs`` imports this module exactly once at
program start; the registry is idempotent so re-importing the facade
in tests is safe.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from ...cli_registry import CliCommand, register
from ..dual_machine_style_kit_selection import normalize_selection_scope
from ._constants import (
    _AUDITION_PACKET_OPTIONS,
    _AUDITION_PACKET_USAGE,
    _DEFAULT_EVENT_LIMIT,
    _LIVE_CUE_SHEET_OPTIONS,
    _LIVE_CUE_SHEET_USAGE,
    _LIVE_RENDER_BUNDLE_OPTIONS,
    _LIVE_RENDER_BUNDLE_USAGE,
    _LIVE_SESSION_PACKET_OPTIONS,
    _LIVE_SESSION_PACKET_USAGE,
    _READINESS_OPTIONS,
    _READINESS_USAGE,
    _REFERENCE_MATCH_OPTIONS,
    _REFERENCE_MATCH_USAGE,
    _REHEARSAL_MANIFEST_OPTIONS,
    _REHEARSAL_MANIFEST_USAGE,
    _SET_PLAN_OPTIONS,
    _SET_PLAN_USAGE,
)
from .audition_packet import (
    build_style_performance_arc_audition_packet_report,
    format_style_performance_arc_audition_packet_report,
    to_style_performance_arc_audition_packet_json,
)
from .catalog import (
    build_style_performance_arc_set_plan_report,
    format_style_performance_arc_inspection,
    format_style_performance_arc_list,
    format_style_performance_arc_report,
    format_style_performance_arc_search,
    format_style_performance_arc_set_plan_report,
    to_style_performance_arc_set_plan_json,
)
from .live_cue_sheet import (
    build_style_performance_arc_live_cue_sheet_report,
    format_style_performance_arc_live_cue_sheet_report,
    to_style_performance_arc_live_cue_sheet_json,
)
from .live_render_bundle import (
    build_style_performance_arc_live_render_bundle_report,
    format_style_performance_arc_live_render_bundle_report,
    to_style_performance_arc_live_render_bundle_json,
)
from .live_session_packet import (
    build_style_performance_arc_live_session_packet_report,
    format_style_performance_arc_live_session_packet_report,
    to_style_performance_arc_live_session_packet_json,
)
from .readiness import (
    build_style_performance_arc_readiness_report,
    format_style_performance_arc_readiness_report,
    to_style_performance_arc_readiness_json,
)
from .reference_match import (
    _source_count,
    build_style_performance_arc_reference_match_report,
    format_style_performance_arc_reference_match_report,
    to_style_performance_arc_reference_match_json,
)
from .rehearsal_manifest import (
    build_style_performance_arc_rehearsal_manifest_report,
    format_style_performance_arc_rehearsal_manifest_report,
    to_style_performance_arc_rehearsal_manifest_json,
)


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
    summary="Match references to arcs, cue sheets, snapshot previews, and stage packets.",
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
