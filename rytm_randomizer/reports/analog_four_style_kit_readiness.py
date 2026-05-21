"""Passive Analog Four style kit-readiness sweep report."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.style_discovery import (
    DEFAULT_STYLE_DISCOVERY_AMOUNT,
    style_discovery_policy,
)
from ..devices.strategies.analog_four_style_mutation_mock_preview import (
    AnalogFourStyleMutationMockPreview,
    build_analog_four_style_mutation_mock_preview,
)
from .analog_four_style_snapshot_routing import (
    decode_supported_analog_four_snapshots_from_path,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four style kit readiness"
SOURCE_MODULE: Final[str] = "reports.analog_four_style_kit_readiness"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "style/mock preview only",
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
    "analog-four-style-kit-readiness-report usage: "
    "<syx-path> <style-key> [--discovery N] [--limit N] [--json]"
)


@dataclass(frozen=True)
class AnalogFourStyleKitReadinessEntry:
    """One kit's passive readiness for a style-aware A4 mock preview."""

    slot: int
    kit_name: str
    snapshot_layout: str
    discovery_band: str
    mutation_depth: str
    preview_ready: bool
    ready_track_count: int
    blocked_track_count: int
    intent_row_count: int
    mock_message_count: int
    deferred_row_count: int
    readiness_reason: str


@dataclass(frozen=True)
class AnalogFourStyleKitReadinessReport:
    """Passive per-kit A4 style readiness summary for a SysEx file."""

    sysex_path: Path
    style_key: str
    discovery_amount: int
    kit_count: int
    preview_ready_count: int
    blocked_kit_count: int
    entries: tuple[AnalogFourStyleKitReadinessEntry, ...]


def _entry_from_preview(
    preview: AnalogFourStyleMutationMockPreview,
) -> AnalogFourStyleKitReadinessEntry:
    return AnalogFourStyleKitReadinessEntry(
        slot=preview.slot,
        kit_name=preview.kit_name,
        snapshot_layout=preview.snapshot_layout,
        discovery_band=preview.discovery_band,
        mutation_depth=preview.mutation_depth,
        preview_ready=preview.preview_ready,
        ready_track_count=preview.ready_track_count,
        blocked_track_count=preview.blocked_track_count,
        intent_row_count=preview.intent_row_count,
        mock_message_count=preview.mock_message_count,
        deferred_row_count=preview.deferred_row_count,
        readiness_reason=preview.readiness_reason,
    )


def build_analog_four_style_kit_readiness_report(
    sysex_path: Path,
    style_key: str,
    *,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> AnalogFourStyleKitReadinessReport:
    """Return passive per-kit A4 style readiness for ``sysex_path``."""

    style_discovery_policy(discovery_amount)
    snapshots = decode_supported_analog_four_snapshots_from_path(sysex_path)
    entries = tuple(
        _entry_from_preview(
            build_analog_four_style_mutation_mock_preview(
                snapshot,
                style_key,
                discovery_amount=discovery_amount,
            )
        )
        for snapshot in snapshots
    )
    preview_ready_count = sum(1 for entry in entries if entry.preview_ready)
    return AnalogFourStyleKitReadinessReport(
        sysex_path=sysex_path,
        style_key=style_key,
        discovery_amount=discovery_amount,
        kit_count=len(entries),
        preview_ready_count=preview_ready_count,
        blocked_kit_count=len(entries) - preview_ready_count,
        entries=entries,
    )


def _visible_entries(
    entries: Sequence[AnalogFourStyleKitReadinessEntry],
    *,
    display_limit: int | None,
) -> tuple[AnalogFourStyleKitReadinessEntry, ...]:
    if display_limit is None or display_limit == 0:
        return tuple(entries)
    if display_limit < 0:
        raise ValueError("display_limit must be >= 0")
    return tuple(entries[:display_limit])


def _entry_line(entry: AnalogFourStyleKitReadinessEntry) -> str:
    return (
        f"- Slot {entry.slot} | {entry.kit_name} | layout {entry.snapshot_layout} | "
        f"preview_ready {entry.preview_ready} | ready tracks {entry.ready_track_count} | "
        f"blocked tracks {entry.blocked_track_count} | mock rows {entry.mock_message_count} | "
        f"deferred rows {entry.deferred_row_count} | {entry.readiness_reason}"
    )


def _body_lines(
    report: AnalogFourStyleKitReadinessReport,
    *,
    display_limit: int | None,
) -> list[str]:
    visible_entries = _visible_entries(report.entries, display_limit=display_limit)
    truncated_count = len(report.entries) - len(visible_entries)
    lines = [
        f"Path: {report.sysex_path}",
        f"Style target: {report.style_key}",
        f"Discovery amount: {report.discovery_amount}",
        f"Supported kits: {report.kit_count}",
        f"Preview-ready kits: {report.preview_ready_count}",
        f"Blocked kits: {report.blocked_kit_count}",
        f"Shown kits: {len(visible_entries)}",
        f"Truncated kits: {truncated_count}",
        "Kits:",
    ]
    if visible_entries:
        lines.extend(_entry_line(entry) for entry in visible_entries)
    else:
        lines.append("- none")
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_analog_four_style_kit_readiness_report(
    report: AnalogFourStyleKitReadinessReport,
    *,
    display_limit: int | None = None,
) -> list[str]:
    """Return deterministic operator-facing A4 style kit-readiness lines."""

    return passive_report_lines(
        _HEADER,
        _body_lines(report, display_limit=display_limit),
    )


def _entry_json(entry: AnalogFourStyleKitReadinessEntry) -> dict[str, object]:
    return {
        "slot": entry.slot,
        "kit_name": entry.kit_name,
        "snapshot_layout": entry.snapshot_layout,
        "discovery_band": entry.discovery_band,
        "mutation_depth": entry.mutation_depth,
        "preview_ready": entry.preview_ready,
        "ready_track_count": entry.ready_track_count,
        "blocked_track_count": entry.blocked_track_count,
        "intent_row_count": entry.intent_row_count,
        "mock_message_count": entry.mock_message_count,
        "deferred_row_count": entry.deferred_row_count,
        "readiness_reason": entry.readiness_reason,
    }


def to_analog_four_style_kit_readiness_json(
    report: AnalogFourStyleKitReadinessReport,
    *,
    display_limit: int | None = None,
) -> dict[str, object]:
    """Return deterministic machine-readable A4 style kit-readiness metadata."""

    visible_entries = _visible_entries(report.entries, display_limit=display_limit)
    return {
        "sysex_path": str(report.sysex_path),
        "style_key": report.style_key,
        "discovery_amount": report.discovery_amount,
        "kit_count": report.kit_count,
        "preview_ready_count": report.preview_ready_count,
        "blocked_kit_count": report.blocked_kit_count,
        "shown_count": len(visible_entries),
        "truncated_count": len(report.entries) - len(visible_entries),
        "entries": [_entry_json(entry) for entry in visible_entries],
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
    discovery_amount = DEFAULT_STYLE_DISCOVERY_AMOUNT
    display_limit: int | None = None
    json_output = False
    remaining = list(argv[2:])
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
            continue
        if len(remaining) < 1:
            raise ValueError(_USAGE)
        value = remaining.pop(0)
        if option == "--discovery":
            discovery_amount = _parse_discovery_amount(value, option=option)
        elif option == "--limit":
            display_limit = _parse_nonnegative_int(value, option=option)
        else:
            raise ValueError(_USAGE)
    return {
        "sysex_path": sysex_path,
        "style_key": style_key,
        "discovery_amount": discovery_amount,
        "display_limit": display_limit,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
    sysex_path: Path,
    style_key: str,
    discovery_amount: int,
    display_limit: int | None,
    json_output: bool,
) -> int:
    try:
        report = build_analog_four_style_kit_readiness_report(
            sysex_path,
            style_key,
            discovery_amount=discovery_amount,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_analog_four_style_kit_readiness_json(
                        report,
                        display_limit=display_limit,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_analog_four_style_kit_readiness_report(
            report,
            display_limit=display_limit,
        )
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


ANALOG_FOUR_STYLE_KIT_READINESS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-style-kit-readiness-report",
    summary="Print passive Analog Four style readiness for every decoded kit.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(ANALOG_FOUR_STYLE_KIT_READINESS_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_STYLE_KIT_READINESS_CLI_COMMAND",
    "AnalogFourStyleKitReadinessEntry",
    "AnalogFourStyleKitReadinessReport",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_analog_four_style_kit_readiness_report",
    "format_analog_four_style_kit_readiness_report",
    "to_analog_four_style_kit_readiness_json",
]
