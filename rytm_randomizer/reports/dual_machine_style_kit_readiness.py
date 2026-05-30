"""Passive dual-machine style kit-readiness pairing report."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.style_discovery import (
    DEFAULT_STYLE_DISCOVERY_AMOUNT,
    style_discovery_policy,
)
from .analog_four_style_kit_readiness import (
    AnalogFourStyleKitReadinessEntry,
    build_analog_four_style_kit_readiness_report,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines
from .rytm_style_kit_readiness import (
    RytmStyleKitReadinessEntry,
    build_rytm_style_kit_readiness_report,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive dual-machine style kit readiness"
SOURCE_MODULE: Final[str] = "reports.dual_machine_style_kit_readiness"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "rig-level kit-bank readiness only",
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
    "dual-machine-style-kit-readiness-report usage: "
    "<rytm-syx-path> <a4-syx-path> <style-key> "
    "[--discovery N] [--limit N] [--json]"
)
_READINESS_RANK: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ready": 3,
        "partial": 2,
        "blocked": 1,
    }
)


@dataclass(frozen=True)
class DualMachineStyleKitReadinessEntry:
    """One recommended Rytm + Analog Four kit pairing."""

    rig_readiness: str
    score: int
    rytm_slot: int
    rytm_kit_name: str
    rytm_preview_ready: bool
    rytm_ready_pad_count: int
    rytm_blocked_pad_count: int
    rytm_mock_message_count: int
    rytm_payload_fingerprint: str
    rytm_readiness_reason: str
    analog_four_slot: int
    analog_four_kit_name: str
    analog_four_preview_ready: bool
    analog_four_ready_track_count: int
    analog_four_blocked_track_count: int
    analog_four_mock_message_count: int
    analog_four_deferred_row_count: int
    analog_four_payload_fingerprint: str
    analog_four_readiness_reason: str


@dataclass(frozen=True)
class DualMachineStyleKitReadinessReport:
    """Passive rig-level kit-pair readiness summary for two SysEx banks."""

    rytm_sysex_path: Path
    analog_four_sysex_path: Path
    style_key: str
    discovery_amount: int
    rytm_kit_count: int
    analog_four_kit_count: int
    pairing_count: int
    ready_pair_count: int
    partial_pair_count: int
    blocked_pair_count: int
    entries: tuple[DualMachineStyleKitReadinessEntry, ...]


def _rig_readiness(
    rytm_entry: RytmStyleKitReadinessEntry,
    analog_four_entry: AnalogFourStyleKitReadinessEntry,
) -> str:
    if rytm_entry.preview_ready and analog_four_entry.preview_ready:
        return "ready"
    if rytm_entry.preview_ready or analog_four_entry.preview_ready:
        return "partial"
    return "blocked"


def _score(
    *,
    rig_readiness: str,
    rytm_entry: RytmStyleKitReadinessEntry,
    analog_four_entry: AnalogFourStyleKitReadinessEntry,
) -> int:
    readiness_weight = _READINESS_RANK[rig_readiness] * 1000
    ready_weight = (
        rytm_entry.ready_pad_count * 20
        + analog_four_entry.ready_track_count * 20
        - analog_four_entry.blocked_track_count
    )
    mock_weight = rytm_entry.mock_message_count + analog_four_entry.mock_message_count
    return readiness_weight + ready_weight + mock_weight


def _entry_from_pair(
    rytm_entry: RytmStyleKitReadinessEntry,
    analog_four_entry: AnalogFourStyleKitReadinessEntry,
) -> DualMachineStyleKitReadinessEntry:
    readiness = _rig_readiness(rytm_entry, analog_four_entry)
    return DualMachineStyleKitReadinessEntry(
        rig_readiness=readiness,
        score=_score(
            rig_readiness=readiness,
            rytm_entry=rytm_entry,
            analog_four_entry=analog_four_entry,
        ),
        rytm_slot=rytm_entry.slot,
        rytm_kit_name=rytm_entry.kit_name,
        rytm_preview_ready=rytm_entry.preview_ready,
        rytm_ready_pad_count=rytm_entry.ready_pad_count,
        rytm_blocked_pad_count=rytm_entry.blocked_pad_count,
        rytm_mock_message_count=rytm_entry.mock_message_count,
        rytm_payload_fingerprint=rytm_entry.payload_fingerprint,
        rytm_readiness_reason=rytm_entry.readiness_reason,
        analog_four_slot=analog_four_entry.slot,
        analog_four_kit_name=analog_four_entry.kit_name,
        analog_four_preview_ready=analog_four_entry.preview_ready,
        analog_four_ready_track_count=analog_four_entry.ready_track_count,
        analog_four_blocked_track_count=analog_four_entry.blocked_track_count,
        analog_four_mock_message_count=analog_four_entry.mock_message_count,
        analog_four_deferred_row_count=analog_four_entry.deferred_row_count,
        analog_four_payload_fingerprint=analog_four_entry.payload_fingerprint,
        analog_four_readiness_reason=analog_four_entry.readiness_reason,
    )


def _sort_key(entry: DualMachineStyleKitReadinessEntry) -> tuple[int, int, int, int]:
    return (
        -_READINESS_RANK[entry.rig_readiness],
        -entry.score,
        entry.rytm_slot,
        entry.analog_four_slot,
    )


def build_dual_machine_style_kit_readiness_report(
    rytm_sysex_path: Path,
    analog_four_sysex_path: Path,
    style_key: str,
    *,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> DualMachineStyleKitReadinessReport:
    """Return passive recommended kit pairings for Rytm and Analog Four banks."""

    style_discovery_policy(discovery_amount)
    rytm_report = build_rytm_style_kit_readiness_report(
        rytm_sysex_path,
        style_key,
        discovery_amount=discovery_amount,
    )
    analog_four_report = build_analog_four_style_kit_readiness_report(
        analog_four_sysex_path,
        style_key,
        discovery_amount=discovery_amount,
    )
    entries = tuple(
        sorted(
            (
                _entry_from_pair(rytm_entry, analog_four_entry)
                for rytm_entry in rytm_report.entries
                for analog_four_entry in analog_four_report.entries
            ),
            key=_sort_key,
        )
    )
    ready_pair_count = sum(1 for entry in entries if entry.rig_readiness == "ready")
    partial_pair_count = sum(1 for entry in entries if entry.rig_readiness == "partial")
    blocked_pair_count = sum(1 for entry in entries if entry.rig_readiness == "blocked")
    return DualMachineStyleKitReadinessReport(
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        style_key=style_key,
        discovery_amount=discovery_amount,
        rytm_kit_count=rytm_report.kit_count,
        analog_four_kit_count=analog_four_report.kit_count,
        pairing_count=len(entries),
        ready_pair_count=ready_pair_count,
        partial_pair_count=partial_pair_count,
        blocked_pair_count=blocked_pair_count,
        entries=entries,
    )


def _visible_entries(
    entries: Sequence[DualMachineStyleKitReadinessEntry],
    *,
    display_limit: int | None,
) -> tuple[DualMachineStyleKitReadinessEntry, ...]:
    if display_limit is None or display_limit == 0:
        return tuple(entries)
    if display_limit < 0:
        raise ValueError("display_limit must be >= 0")
    return tuple(entries[:display_limit])


def _entry_line(entry: DualMachineStyleKitReadinessEntry) -> str:
    return (
        f"- Rytm slot {entry.rytm_slot} {entry.rytm_kit_name} + "
        f"A4 slot {entry.analog_four_slot} {entry.analog_four_kit_name} | "
        f"readiness {entry.rig_readiness} | score {entry.score} | "
        f"Rytm ready {entry.rytm_preview_ready} / mock rows "
        f"{entry.rytm_mock_message_count} | A4 ready "
        f"{entry.analog_four_preview_ready} / mock rows "
        f"{entry.analog_four_mock_message_count} / deferred rows "
        f"{entry.analog_four_deferred_row_count} | fingerprints "
        f"{entry.rytm_payload_fingerprint}/{entry.analog_four_payload_fingerprint}"
    )


def _body_lines(
    report: DualMachineStyleKitReadinessReport,
    *,
    display_limit: int | None,
) -> list[str]:
    visible_entries = _visible_entries(report.entries, display_limit=display_limit)
    truncated_count = len(report.entries) - len(visible_entries)
    lines = [
        f"Rytm path: {report.rytm_sysex_path}",
        f"Analog Four path: {report.analog_four_sysex_path}",
        f"Style target: {report.style_key}",
        f"Discovery amount: {report.discovery_amount}",
        f"Rytm kits: {report.rytm_kit_count}",
        f"Analog Four kits: {report.analog_four_kit_count}",
        f"Pairings: {report.pairing_count}",
        f"Ready pairings: {report.ready_pair_count}",
        f"Partial pairings: {report.partial_pair_count}",
        f"Blocked pairings: {report.blocked_pair_count}",
        f"Shown pairings: {len(visible_entries)}",
        f"Truncated pairings: {truncated_count}",
        "Recommended pairings:",
    ]
    if visible_entries:
        lines.extend(_entry_line(entry) for entry in visible_entries)
    else:
        lines.append("- none")
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_dual_machine_style_kit_readiness_report(
    report: DualMachineStyleKitReadinessReport,
    *,
    display_limit: int | None = None,
) -> list[str]:
    """Return deterministic operator-facing dual-machine kit-readiness lines."""

    return passive_report_lines(
        _HEADER,
        _body_lines(report, display_limit=display_limit),
    )


def _entry_json(entry: DualMachineStyleKitReadinessEntry) -> dict[str, object]:
    return {
        "rig_readiness": entry.rig_readiness,
        "score": entry.score,
        "rytm": {
            "slot": entry.rytm_slot,
            "kit_name": entry.rytm_kit_name,
            "preview_ready": entry.rytm_preview_ready,
            "ready_pad_count": entry.rytm_ready_pad_count,
            "blocked_pad_count": entry.rytm_blocked_pad_count,
            "mock_message_count": entry.rytm_mock_message_count,
            "payload_fingerprint": entry.rytm_payload_fingerprint,
            "readiness_reason": entry.rytm_readiness_reason,
        },
        "analog_four": {
            "slot": entry.analog_four_slot,
            "kit_name": entry.analog_four_kit_name,
            "preview_ready": entry.analog_four_preview_ready,
            "ready_track_count": entry.analog_four_ready_track_count,
            "blocked_track_count": entry.analog_four_blocked_track_count,
            "mock_message_count": entry.analog_four_mock_message_count,
            "deferred_row_count": entry.analog_four_deferred_row_count,
            "payload_fingerprint": entry.analog_four_payload_fingerprint,
            "readiness_reason": entry.analog_four_readiness_reason,
        },
    }


def to_dual_machine_style_kit_readiness_json(
    report: DualMachineStyleKitReadinessReport,
    *,
    display_limit: int | None = None,
) -> dict[str, object]:
    """Return deterministic machine-readable dual-machine readiness metadata."""

    visible_entries = _visible_entries(report.entries, display_limit=display_limit)
    return {
        "rytm_sysex_path": str(report.rytm_sysex_path),
        "analog_four_sysex_path": str(report.analog_four_sysex_path),
        "style_key": report.style_key,
        "discovery_amount": report.discovery_amount,
        "rytm_kit_count": report.rytm_kit_count,
        "analog_four_kit_count": report.analog_four_kit_count,
        "pairing_count": report.pairing_count,
        "ready_pair_count": report.ready_pair_count,
        "partial_pair_count": report.partial_pair_count,
        "blocked_pair_count": report.blocked_pair_count,
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
    if len(argv) < 3:
        raise ValueError(_USAGE)
    rytm_sysex_path = Path(argv[0])
    analog_four_sysex_path = Path(argv[1])
    style_key = argv[2]
    discovery_amount = DEFAULT_STYLE_DISCOVERY_AMOUNT
    display_limit: int | None = None
    json_output = False
    remaining = list(argv[3:])
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
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "style_key": style_key,
        "discovery_amount": discovery_amount,
        "display_limit": display_limit,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
    rytm_sysex_path: Path,
    analog_four_sysex_path: Path,
    style_key: str,
    discovery_amount: int,
    display_limit: int | None,
    json_output: bool,
) -> int:
    try:
        report = build_dual_machine_style_kit_readiness_report(
            rytm_sysex_path,
            analog_four_sysex_path,
            style_key,
            discovery_amount=discovery_amount,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_dual_machine_style_kit_readiness_json(
                        report,
                        display_limit=display_limit,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_dual_machine_style_kit_readiness_report(
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


DUAL_MACHINE_STYLE_KIT_READINESS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="dual-machine-style-kit-readiness-report",
    summary="Print passive dual-machine style readiness across Rytm and A4 kit banks.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(DUAL_MACHINE_STYLE_KIT_READINESS_CLI_COMMAND)

__all__ = [
    "DUAL_MACHINE_STYLE_KIT_READINESS_CLI_COMMAND",
    "DualMachineStyleKitReadinessEntry",
    "DualMachineStyleKitReadinessReport",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_dual_machine_style_kit_readiness_report",
    "format_dual_machine_style_kit_readiness_report",
    "to_dual_machine_style_kit_readiness_json",
]
