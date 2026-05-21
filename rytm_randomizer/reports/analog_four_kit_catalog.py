"""Passive Analog Four kit catalog report."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..devices.strategies import AnalogFourKitSnapshot
from ..devices.strategies.analog_four_offset_manifest import (
    A4_SNAPSHOT_LAYOUT_CANDIDATE,
    A4_SNAPSHOT_LAYOUT_SAVED_KIT,
)
from ..devices.strategies.analog_four_snapshot_decoder import (
    analog_four_snapshot_payload_fingerprint,
)
from .analog_four_style_snapshot_routing import (
    decode_supported_analog_four_snapshots_from_path,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four kit catalog"
SOURCE_MODULE: Final[str] = "reports.analog_four_kit_catalog"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "SysEx decode only",
    "candidate-only A4 offsets still block real mutation",
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
_USAGE: Final[str] = "analog-four-kit-catalog-report usage: <syx-path> [--limit N] [--json]"


@dataclass(frozen=True)
class AnalogFourKitCatalogEntry:
    """Operator-facing catalog row for one decoded Analog Four kit snapshot."""

    slot: int
    kit_name: str
    snapshot_layout: str
    offset_status: str
    offsets_promoted: bool
    mutation_ready: bool
    readiness_reason: str
    payload_fingerprint: str
    raw_byte_count: int
    unpacked_byte_count: int


@dataclass(frozen=True)
class AnalogFourKitCatalogReport:
    """Passive catalog summary for decoded Analog Four kit snapshots."""

    sysex_path: Path
    supported_kit_count: int
    saved_kit_count: int
    candidate_count: int
    promoted_offset_count: int
    mutation_ready_count: int
    entries: tuple[AnalogFourKitCatalogEntry, ...]


def _offset_status(snapshot: AnalogFourKitSnapshot) -> str:
    return "promoted" if snapshot.offsets_promoted else "candidate-only"


def _readiness_reason(snapshot: AnalogFourKitSnapshot) -> str:
    if snapshot.offsets_promoted:
        return "ready for promoted-offset planning"
    if snapshot.snapshot_layout == A4_SNAPSHOT_LAYOUT_SAVED_KIT:
        return "saved-kit decoded; offset promotion required before mutation preview"
    return "candidate layout decoded; offset promotion required before mutation preview"


def _entry_from_snapshot(snapshot: AnalogFourKitSnapshot) -> AnalogFourKitCatalogEntry:
    mutation_ready = snapshot.offsets_promoted
    return AnalogFourKitCatalogEntry(
        slot=snapshot.slot,
        kit_name=snapshot.kit_name,
        snapshot_layout=snapshot.snapshot_layout,
        offset_status=_offset_status(snapshot),
        offsets_promoted=snapshot.offsets_promoted,
        mutation_ready=mutation_ready,
        readiness_reason=_readiness_reason(snapshot),
        payload_fingerprint=analog_four_snapshot_payload_fingerprint(snapshot),
        raw_byte_count=len(snapshot.raw),
        unpacked_byte_count=len(snapshot.unpacked),
    )


def build_analog_four_kit_catalog_report(
    sysex_path: Path,
) -> AnalogFourKitCatalogReport:
    """Return passive Analog Four kit-catalog metadata for ``sysex_path``."""

    snapshots = decode_supported_analog_four_snapshots_from_path(sysex_path)
    entries = tuple(_entry_from_snapshot(snapshot) for snapshot in snapshots)
    return AnalogFourKitCatalogReport(
        sysex_path=sysex_path,
        supported_kit_count=len(entries),
        saved_kit_count=sum(
            1 for entry in entries if entry.snapshot_layout == A4_SNAPSHOT_LAYOUT_SAVED_KIT
        ),
        candidate_count=sum(
            1 for entry in entries if entry.snapshot_layout == A4_SNAPSHOT_LAYOUT_CANDIDATE
        ),
        promoted_offset_count=sum(1 for entry in entries if entry.offsets_promoted),
        mutation_ready_count=sum(1 for entry in entries if entry.mutation_ready),
        entries=entries,
    )


def _visible_entries(
    entries: Sequence[AnalogFourKitCatalogEntry],
    *,
    display_limit: int | None,
) -> tuple[AnalogFourKitCatalogEntry, ...]:
    if display_limit is None or display_limit == 0:
        return tuple(entries)
    if display_limit < 0:
        raise ValueError("display_limit must be >= 0")
    return tuple(entries[:display_limit])


def _entry_line(entry: AnalogFourKitCatalogEntry) -> str:
    return (
        f"- Slot {entry.slot} | {entry.kit_name} | layout {entry.snapshot_layout} | "
        f"offsets {entry.offset_status} | fingerprint {entry.payload_fingerprint} | "
        f"raw {entry.raw_byte_count} bytes | "
        f"unpacked {entry.unpacked_byte_count} bytes | {entry.readiness_reason}"
    )


def _body_lines(
    report: AnalogFourKitCatalogReport,
    *,
    display_limit: int | None,
) -> list[str]:
    visible_entries = _visible_entries(report.entries, display_limit=display_limit)
    truncated_count = len(report.entries) - len(visible_entries)
    lines = [
        f"Path: {report.sysex_path}",
        f"Supported kits: {report.supported_kit_count}",
        f"Saved-kit snapshots: {report.saved_kit_count}",
        f"Candidate snapshots: {report.candidate_count}",
        f"Promoted-offset snapshots: {report.promoted_offset_count}",
        f"Mutation-ready kits: {report.mutation_ready_count}",
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


def format_analog_four_kit_catalog_report(
    report: AnalogFourKitCatalogReport,
    *,
    display_limit: int | None = None,
) -> list[str]:
    """Return deterministic operator-facing A4 kit catalog lines."""

    return passive_report_lines(
        _HEADER,
        _body_lines(report, display_limit=display_limit),
    )


def _entry_json(entry: AnalogFourKitCatalogEntry) -> dict[str, object]:
    return {
        "slot": entry.slot,
        "kit_name": entry.kit_name,
        "snapshot_layout": entry.snapshot_layout,
        "offset_status": entry.offset_status,
        "offsets_promoted": entry.offsets_promoted,
        "mutation_ready": entry.mutation_ready,
        "readiness_reason": entry.readiness_reason,
        "payload_fingerprint": entry.payload_fingerprint,
        "raw_byte_count": entry.raw_byte_count,
        "unpacked_byte_count": entry.unpacked_byte_count,
    }


def to_analog_four_kit_catalog_json(
    report: AnalogFourKitCatalogReport,
    *,
    display_limit: int | None = None,
) -> dict[str, object]:
    """Return deterministic machine-readable A4 kit catalog metadata."""

    visible_entries = _visible_entries(report.entries, display_limit=display_limit)
    return {
        "sysex_path": str(report.sysex_path),
        "supported_kit_count": report.supported_kit_count,
        "saved_kit_count": report.saved_kit_count,
        "candidate_count": report.candidate_count,
        "promoted_offset_count": report.promoted_offset_count,
        "mutation_ready_count": report.mutation_ready_count,
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


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if not argv:
        raise ValueError(_USAGE)
    sysex_path = Path(argv[0])
    display_limit: int | None = None
    json_output = False
    remaining = list(argv[1:])
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
            continue
        if len(remaining) < 1:
            raise ValueError(_USAGE)
        value = remaining.pop(0)
        if option == "--limit":
            display_limit = _parse_nonnegative_int(value, option=option)
        else:
            raise ValueError(_USAGE)
    return {
        "sysex_path": sysex_path,
        "display_limit": display_limit,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
    sysex_path: Path,
    display_limit: int | None,
    json_output: bool,
) -> int:
    try:
        report = build_analog_four_kit_catalog_report(sysex_path)
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_analog_four_kit_catalog_json(report, display_limit=display_limit),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_analog_four_kit_catalog_report(
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


ANALOG_FOUR_KIT_CATALOG_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-kit-catalog-report",
    summary="Print passive Analog Four kit catalog metadata for a SysEx file.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(ANALOG_FOUR_KIT_CATALOG_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_KIT_CATALOG_CLI_COMMAND",
    "AnalogFourKitCatalogEntry",
    "AnalogFourKitCatalogReport",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_analog_four_kit_catalog_report",
    "format_analog_four_kit_catalog_report",
    "to_analog_four_kit_catalog_json",
]
