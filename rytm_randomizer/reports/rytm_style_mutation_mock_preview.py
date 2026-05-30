"""Passive Rytm style mutation mock-preview report."""

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
from ..devices.strategies import RytmKitSnapshot
from ..devices.strategies.analog_rytm_style_mutation_mock_preview import (
    RytmStyleMutationMockPreview,
    RytmStyleMutationMockPreviewEvent,
    build_rytm_style_mutation_mock_preview,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines
from .rytm_snapshot_intelligence import (
    decode_supported_rytm_snapshots_from_path,
    select_supported_rytm_snapshot,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive Rytm style mutation mock preview"
SOURCE_MODULE: Final[str] = "reports.rytm_style_mutation_mock_preview"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "mock-only preview",
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
    "rytm-style-mutation-mock-preview-report usage: "
    "<syx-path> <style-key> [--slot N] [--discovery N] "
    "[--events] [--limit N] [--json]"
)
_DEFAULT_SLOT: Final[int] = 0
_DEFAULT_EVENT_LIMIT: Final[int] = 24


def _planned_pads_text(planned_pads: Sequence[int]) -> str:
    if not planned_pads:
        return "none"
    return ", ".join(str(pad) for pad in planned_pads)


def _format_event_row(row: RytmStyleMutationMockPreviewEvent) -> str:
    return (
        f"- Pad {row.pad} | profile {row.profile_key} | {row.zone} | {row.parameter} | "
        f"ch {row.channel} | CC{row.control} -> {row.value} | "
        f"window {row.window_low}-{row.window_high} | depth {row.mutation_depth} | "
        f"direction {row.target_direction}"
    )


def _event_preview_lines(
    event_rows: Sequence[RytmStyleMutationMockPreviewEvent],
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


def _body_lines(
    preview: RytmStyleMutationMockPreview,
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
        f"- Ready pads: {preview.ready_pad_count}",
        f"- Blocked pads: {preview.blocked_pad_count}",
        f"- Render events: {preview.render_event_count}",
        f"- Mock messages: {preview.mock_message_count}",
        f"- Planned pads: {_planned_pads_text(preview.planned_pads)}",
    ]
    if include_events:
        lines.extend(_event_preview_lines(preview.event_rows, event_limit=event_limit))
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_rytm_style_mutation_mock_preview_report(
    snapshot_or_preview: RytmKitSnapshot | RytmStyleMutationMockPreview,
    *,
    style_key: str,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing style mock-preview lines."""

    preview = (
        snapshot_or_preview
        if isinstance(snapshot_or_preview, RytmStyleMutationMockPreview)
        else build_rytm_style_mutation_mock_preview(
            snapshot_or_preview,
            style_key,
            discovery_amount=discovery_amount,
        )
    )
    return passive_report_lines(
        _HEADER,
        _body_lines(preview, include_events=include_events, event_limit=event_limit),
    )


def _event_json(row: RytmStyleMutationMockPreviewEvent) -> dict[str, object]:
    return {
        "pad": row.pad,
        "profile_key": row.profile_key,
        "zone": row.zone,
        "parameter": row.parameter,
        "channel": row.channel,
        "control": row.control,
        "value": row.value,
        "target_value": row.target_value,
        "window_low": row.window_low,
        "window_high": row.window_high,
        "mutation_depth": row.mutation_depth,
        "target_direction": row.target_direction,
    }


def to_rytm_style_mutation_mock_preview_json(
    preview: RytmStyleMutationMockPreview,
) -> dict[str, object]:
    """Return deterministic machine-readable Rytm style mock-preview metadata."""

    return {
        "kit_name": preview.kit_name,
        "slot": preview.slot,
        "style_key": preview.style_key,
        "discovery_amount": preview.discovery_amount,
        "discovery_band": preview.discovery_band,
        "mutation_depth": preview.mutation_depth,
        "preview_ready": preview.preview_ready,
        "readiness_reason": preview.readiness_reason,
        "ready_pad_count": preview.ready_pad_count,
        "blocked_pad_count": preview.blocked_pad_count,
        "render_event_count": preview.render_event_count,
        "mock_message_count": preview.mock_message_count,
        "planned_pads": list(preview.planned_pads),
        "events": [_event_json(row) for row in preview.event_rows],
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
        snapshots = decode_supported_rytm_snapshots_from_path(sysex_path)
        snapshot = select_supported_rytm_snapshot(sysex_path, slot, snapshots)
        preview = build_rytm_style_mutation_mock_preview(
            snapshot,
            style_key,
            discovery_amount=discovery_amount,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_rytm_style_mutation_mock_preview_json(preview),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_rytm_style_mutation_mock_preview_report(
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


RYTM_STYLE_MUTATION_MOCK_PREVIEW_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="rytm-style-mutation-mock-preview-report",
    summary="Print passive Rytm style mutation mock-preview rows for a SysEx file.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(RYTM_STYLE_MUTATION_MOCK_PREVIEW_CLI_COMMAND)

__all__ = [
    "REPORT_TITLE",
    "RYTM_STYLE_MUTATION_MOCK_PREVIEW_CLI_COMMAND",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "format_rytm_style_mutation_mock_preview_report",
    "to_rytm_style_mutation_mock_preview_json",
]
