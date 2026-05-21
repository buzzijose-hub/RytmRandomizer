"""Passive Analog Four style mutation mock-preview report."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.style_discovery import (
    DEFAULT_STYLE_DISCOVERY_AMOUNT,
    style_discovery_policy,
)
from ..devices.strategies import AnalogFourKitSnapshot
from ..devices.strategies.analog_four_style_mutation_mock_preview import (
    AnalogFourStyleMutationMockPreview,
    AnalogFourStyleMutationMockPreviewDeferredRow,
    AnalogFourStyleMutationMockPreviewEvent,
    build_analog_four_style_mutation_mock_preview,
)
from .analog_four_style_snapshot_routing import (
    decode_supported_analog_four_snapshots_from_path,
    select_supported_analog_four_snapshot,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four style mutation mock preview"
SOURCE_MODULE: Final[str] = "reports.analog_four_style_mutation_mock_preview"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "mock-only preview",
    "candidate-only A4 offsets still block decoded SysEx mock rows",
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
_USAGE: Final[str] = (
    "analog-four-style-mutation-mock-preview-report usage: "
    "<syx-path> <style-key> [--slot N] [--discovery N] "
    "[--events] [--limit N] [--json]"
)
_DEFAULT_SLOT: Final[int] = 0
_DEFAULT_EVENT_LIMIT: Final[int] = 24


def _planned_tracks_text(planned_tracks: Sequence[int]) -> str:
    if not planned_tracks:
        return "none"
    return ", ".join(str(track) for track in planned_tracks)


def _format_event_row(row: AnalogFourStyleMutationMockPreviewEvent) -> str:
    return (
        f"- Track {row.track} | {row.role_key} | {row.zone} | {row.parameter} | "
        f"ch {row.channel} | CC{row.control} -> {row.value} | "
        f"bias {row.target_bias} | depth {row.mutation_depth} | "
        f"direction {row.target_direction}"
    )


def _format_deferred_row(row: AnalogFourStyleMutationMockPreviewDeferredRow) -> str:
    return (
        f"- Track {row.track} | {row.role_key} | {row.zone} | {row.reason} | "
        f"bias {row.target_bias} | depth {row.mutation_depth} | "
        f"direction {row.target_direction}"
    )


def _event_preview_lines(
    event_rows: Sequence[AnalogFourStyleMutationMockPreviewEvent],
    *,
    event_limit: int,
) -> list[str]:
    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    lines = ["Event preview:"]
    if not event_rows:
        lines.append("- No mock rows available because the preview is not ready.")
        return lines

    if event_limit == 0 or event_limit >= len(event_rows):
        selected_rows = tuple(event_rows)
        lines.append("- Showing all events")
    else:
        selected_rows = tuple(event_rows[:event_limit])
        lines.append(f"- Showing first {event_limit} of {len(event_rows)} events")
    lines.extend(_format_event_row(row) for row in selected_rows)
    return lines


def _deferred_preview_lines(
    deferred_rows: Sequence[AnalogFourStyleMutationMockPreviewDeferredRow],
) -> list[str]:
    lines = ["Deferred rows:"]
    if not deferred_rows:
        lines.append("- none")
        return lines
    lines.extend(_format_deferred_row(row) for row in deferred_rows)
    return lines


def _body_lines(
    preview: AnalogFourStyleMutationMockPreview,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    lines = [
        f"Kit: {preview.kit_name}",
        f"Slot: {preview.slot}",
        f"Style target: {preview.style_key}",
        f"Discovery amount: {preview.discovery_amount}",
        f"Discovery band: {preview.discovery_band}",
        f"Mutation depth: {preview.mutation_depth}",
        f"Preview ready: {preview.preview_ready}",
        f"Readiness reason: {preview.readiness_reason}",
        "Preview:",
        f"- Ready tracks: {preview.ready_track_count}",
        f"- Blocked tracks: {preview.blocked_track_count}",
        f"- Intent rows: {preview.intent_row_count}",
        f"- Mock messages: {preview.mock_message_count}",
        f"- Deferred rows: {preview.deferred_row_count}",
        f"- Planned tracks: {_planned_tracks_text(preview.planned_tracks)}",
    ]
    if include_events:
        lines.extend(_event_preview_lines(preview.event_rows, event_limit=event_limit))
    lines.extend(_deferred_preview_lines(preview.deferred_rows))
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_analog_four_style_mutation_mock_preview_report(
    snapshot_or_preview: AnalogFourKitSnapshot | AnalogFourStyleMutationMockPreview,
    *,
    style_key: str,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing A4 style mock-preview lines."""

    preview = (
        snapshot_or_preview
        if isinstance(snapshot_or_preview, AnalogFourStyleMutationMockPreview)
        else build_analog_four_style_mutation_mock_preview(
            snapshot_or_preview,
            style_key,
            discovery_amount=discovery_amount,
        )
    )
    return passive_report_lines(
        _HEADER,
        _body_lines(preview, include_events=include_events, event_limit=event_limit),
    )


def _event_json(row: AnalogFourStyleMutationMockPreviewEvent) -> dict[str, object]:
    return {
        "track": row.track,
        "role_key": row.role_key,
        "zone": row.zone,
        "parameter": row.parameter,
        "channel": row.channel,
        "control": row.control,
        "value": row.value,
        "target_bias": row.target_bias,
        "mutation_depth": row.mutation_depth,
        "target_direction": row.target_direction,
    }


def _deferred_json(row: AnalogFourStyleMutationMockPreviewDeferredRow) -> dict[str, object]:
    return {
        "track": row.track,
        "role_key": row.role_key,
        "zone": row.zone,
        "target_bias": row.target_bias,
        "mutation_depth": row.mutation_depth,
        "target_direction": row.target_direction,
        "reason": row.reason,
    }


def to_analog_four_style_mutation_mock_preview_json(
    preview: AnalogFourStyleMutationMockPreview,
) -> dict[str, object]:
    """Return deterministic machine-readable A4 style mock-preview metadata."""

    return {
        "kit_name": preview.kit_name,
        "slot": preview.slot,
        "style_key": preview.style_key,
        "discovery_amount": preview.discovery_amount,
        "discovery_band": preview.discovery_band,
        "mutation_depth": preview.mutation_depth,
        "preview_ready": preview.preview_ready,
        "readiness_reason": preview.readiness_reason,
        "ready_track_count": preview.ready_track_count,
        "blocked_track_count": preview.blocked_track_count,
        "intent_row_count": preview.intent_row_count,
        "mock_message_count": preview.mock_message_count,
        "deferred_row_count": preview.deferred_row_count,
        "planned_tracks": list(preview.planned_tracks),
        "events": [_event_json(row) for row in preview.event_rows],
        "deferred_rows": [_deferred_json(row) for row in preview.deferred_rows],
        "safety": list(SAFETY_LINES),
    }


def _parse_nonnegative_int(value: str, *, option: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{option} must be >= 0")
    return parsed


def _parse_discovery_amount(value: str, *, option: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc
    style_discovery_policy(parsed)
    return parsed


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if len(argv) < 2:
        raise ValueError(_USAGE)
    sysex_path = Path(argv[0])
    style_key = argv[1]
    slot = _DEFAULT_SLOT
    discovery_amount = DEFAULT_STYLE_DISCOVERY_AMOUNT
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    remaining = list(argv[2:])
    while remaining:
        option = remaining.pop(0)
        if option == "--events":
            include_events = True
            continue
        if option == "--json":
            json_output = True
            continue
        if len(remaining) < 1:
            raise ValueError(_USAGE)
        value = remaining.pop(0)
        if option == "--slot":
            slot = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery":
            discovery_amount = _parse_discovery_amount(value, option=option)
        elif option == "--limit":
            event_limit = _parse_nonnegative_int(value, option=option)
        else:
            raise ValueError(_USAGE)
    return {
        "sysex_path": sysex_path,
        "style_key": style_key,
        "slot": slot,
        "discovery_amount": discovery_amount,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
    sysex_path: Path,
    style_key: str,
    slot: int,
    discovery_amount: int,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        snapshots = decode_supported_analog_four_snapshots_from_path(sysex_path)
        snapshot = select_supported_analog_four_snapshot(sysex_path, slot, snapshots)
        preview = build_analog_four_style_mutation_mock_preview(
            snapshot,
            style_key,
            discovery_amount=discovery_amount,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_analog_four_style_mutation_mock_preview_json(preview),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_analog_four_style_mutation_mock_preview_report(
            preview,
            style_key=style_key,
            discovery_amount=discovery_amount,
            include_events=include_events,
            event_limit=event_limit,
        )
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


ANALOG_FOUR_STYLE_MUTATION_MOCK_PREVIEW_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-style-mutation-mock-preview-report",
    summary="Print passive Analog Four style mutation mock-preview rows for a SysEx file.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(ANALOG_FOUR_STYLE_MUTATION_MOCK_PREVIEW_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_STYLE_MUTATION_MOCK_PREVIEW_CLI_COMMAND",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "format_analog_four_style_mutation_mock_preview_report",
    "to_analog_four_style_mutation_mock_preview_json",
]
