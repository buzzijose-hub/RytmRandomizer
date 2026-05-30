"""Passive multi-style live audition planning for dual-machine saved kits."""

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
from .dual_machine_style_kit_selection import normalize_selection_scope
from .dual_machine_style_selection_mock_preview import (
    SAFETY_LINES as SELECTION_MOCK_PREVIEW_SAFETY_LINES,
)
from .dual_machine_style_selection_mock_preview import (
    DualMachineStyleSelectionMockPreviewPlan,
    build_dual_machine_style_selection_mock_preview_report,
    format_dual_machine_style_selection_mock_preview_event_rows,
    to_dual_machine_style_selection_mock_preview_json,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive dual-machine style live audition"
SOURCE_MODULE: Final[str] = "reports.dual_machine_style_live_audition"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live audition selection set",
) + tuple(line for line in SELECTION_MOCK_PREVIEW_SAFETY_LINES if line != "passive/read-only")
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_USAGE: Final[str] = (
    "dual-machine-style-live-audition-report usage: "
    "<style-key> [<style-key> ...] --rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--discovery N] [--events] [--limit N] [--json]"
)
_DEFAULT_SELECTION_RANK: Final[int] = 1
_DEFAULT_EVENT_LIMIT: Final[int] = 24
_CLI_OPTIONS: Final[tuple[str, ...]] = (
    "--rytm",
    "--analog-four",
    "--scope",
    "--rank",
    "--discovery",
    "--events",
    "--limit",
    "--json",
)


@dataclass(frozen=True)
class DualMachineStyleLiveAuditionEntry:
    """One style stop inside a passive live-audition sequence."""

    position: int
    style_key: str
    selection_readiness: str
    selection_score: int
    operator_action: str
    event_row_count: int
    mock_message_count: int
    deferred_row_count: int
    preview_plan: DualMachineStyleSelectionMockPreviewPlan


@dataclass(frozen=True)
class DualMachineStyleLiveAuditionPlan:
    """Passive operator plan for auditioning multiple style targets in order."""

    style_keys: tuple[str, ...]
    scope: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    selection_rank: int
    style_count: int
    ready_style_count: int
    partial_style_count: int
    blocked_style_count: int
    total_event_row_count: int
    total_mock_message_count: int
    total_deferred_row_count: int
    entries: tuple[DualMachineStyleLiveAuditionEntry, ...]


def _normalized_style_keys(style_keys: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(key.strip() for key in style_keys if key.strip())
    if not normalized:
        raise ValueError("live audition requires at least one style key")
    return normalized


def _readiness_count(
    entries: Sequence[DualMachineStyleLiveAuditionEntry],
    readiness: str,
) -> int:
    return sum(1 for entry in entries if entry.selection_readiness == readiness)


def _entry_from_preview(
    *,
    position: int,
    preview_plan: DualMachineStyleSelectionMockPreviewPlan,
) -> DualMachineStyleLiveAuditionEntry:
    return DualMachineStyleLiveAuditionEntry(
        position=position,
        style_key=preview_plan.style_key,
        selection_readiness=preview_plan.selection_readiness,
        selection_score=preview_plan.selection_score,
        operator_action=preview_plan.operator_action,
        event_row_count=preview_plan.total_event_row_count,
        mock_message_count=preview_plan.total_mock_message_count,
        deferred_row_count=preview_plan.total_deferred_row_count,
        preview_plan=preview_plan,
    )


def build_dual_machine_style_live_audition_report(
    style_keys: Sequence[str],
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int = _DEFAULT_SELECTION_RANK,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> DualMachineStyleLiveAuditionPlan:
    """Return a passive multi-style audition plan from saved-kit selections."""

    normalized_keys = _normalized_style_keys(style_keys)
    policy = style_discovery_policy(discovery_amount)
    previews = tuple(
        build_dual_machine_style_selection_mock_preview_report(
            style_key,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            discovery_amount=policy.amount,
        )
        for style_key in normalized_keys
    )
    entries = tuple(
        _entry_from_preview(position=index + 1, preview_plan=preview)
        for index, preview in enumerate(previews)
    )
    return DualMachineStyleLiveAuditionPlan(
        style_keys=normalized_keys,
        scope=previews[0].scope,
        discovery_amount=policy.amount,
        discovery_band=policy.band,
        mutation_depth=policy.mutation_depth,
        selection_rank=selection_rank,
        style_count=len(entries),
        ready_style_count=_readiness_count(entries, "ready"),
        partial_style_count=_readiness_count(entries, "partial"),
        blocked_style_count=_readiness_count(entries, "blocked"),
        total_event_row_count=sum(entry.event_row_count for entry in entries),
        total_mock_message_count=sum(entry.mock_message_count for entry in entries),
        total_deferred_row_count=sum(entry.deferred_row_count for entry in entries),
        entries=entries,
    )


def _event_preview_lines(
    entry: DualMachineStyleLiveAuditionEntry,
    *,
    event_limit: int,
) -> list[str]:
    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    rows = format_dual_machine_style_selection_mock_preview_event_rows(entry.preview_plan)
    lines = [f"Event preview for {entry.style_key}:"]
    if not rows:
        lines.append("- No mock rows available because the selected preview is not ready.")
        return lines
    if event_limit == 0 or event_limit >= len(rows):
        selected_rows = rows
        lines.append("- Showing all events")
    else:
        selected_rows = rows[:event_limit]
        lines.append(f"- Showing first {event_limit} of {len(rows)} events")
    lines.extend(selected_rows)
    return lines


def _machine_summary_lines(entry: DualMachineStyleLiveAuditionEntry) -> list[str]:
    preview = entry.preview_plan
    if preview.rytm_preview is None:
        rytm_line = "  Rytm: unchanged by scope"
    else:
        rytm_line = (
            f"  Rytm: slot {preview.rytm_preview.slot} {preview.rytm_preview.kit_name} "
            f"/ ready {preview.rytm_preview.preview_ready} "
            f"/ mock rows {preview.rytm_preview.mock_message_count}"
        )
    if preview.analog_four_preview is None:
        analog_four_line = "  Analog Four: unchanged by scope"
    else:
        analog_four_line = (
            f"  Analog Four: slot {preview.analog_four_preview.slot} "
            f"{preview.analog_four_preview.kit_name} "
            f"/ ready {preview.analog_four_preview.preview_ready} "
            f"/ deferred rows {preview.analog_four_preview.deferred_row_count}"
        )
    return [rytm_line, analog_four_line]


def _entry_lines(entry: DualMachineStyleLiveAuditionEntry) -> list[str]:
    lines = [
        (
            f"- {entry.position}. {entry.style_key} | readiness {entry.selection_readiness} "
            f"| score {entry.selection_score} | events {entry.event_row_count} "
            f"| mock messages {entry.mock_message_count} "
            f"| deferred {entry.deferred_row_count}"
        ),
        f"  Action: {entry.operator_action}",
    ]
    lines.extend(_machine_summary_lines(entry))
    return lines


def _body_lines(
    plan: DualMachineStyleLiveAuditionPlan,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    lines = [
        f"Scope: {plan.scope}",
        f"Discovery amount: {plan.discovery_amount}",
        f"Discovery band: {plan.discovery_band}",
        f"Mutation depth: {plan.mutation_depth}",
        f"Selection rank: {plan.selection_rank}",
        f"Styles: {plan.style_count}",
        f"Ready styles: {plan.ready_style_count}",
        f"Partial styles: {plan.partial_style_count}",
        f"Blocked styles: {plan.blocked_style_count}",
        f"Total event rows: {plan.total_event_row_count}",
        f"Total mock messages: {plan.total_mock_message_count}",
        f"Total deferred rows: {plan.total_deferred_row_count}",
        "Style sequence:",
    ]
    lines.extend(f"{entry.position}. {entry.style_key}" for entry in plan.entries)
    lines.append("Audition entries:")
    for entry in plan.entries:
        lines.extend(_entry_lines(entry))
        if include_events:
            lines.extend(_event_preview_lines(entry, event_limit=event_limit))
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_dual_machine_style_live_audition_report(
    plan: DualMachineStyleLiveAuditionPlan,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing live audition report lines."""

    return passive_report_lines(
        _HEADER,
        _body_lines(plan, include_events=include_events, event_limit=event_limit),
    )


def _totals_json(plan: DualMachineStyleLiveAuditionPlan) -> dict[str, object]:
    return {
        "styles": plan.style_count,
        "ready": plan.ready_style_count,
        "partial": plan.partial_style_count,
        "blocked": plan.blocked_style_count,
        "event_rows": plan.total_event_row_count,
        "mock_messages": plan.total_mock_message_count,
        "deferred_rows": plan.total_deferred_row_count,
    }


def _entry_json(entry: DualMachineStyleLiveAuditionEntry) -> dict[str, object]:
    return {
        "position": entry.position,
        "style_key": entry.style_key,
        "selection_readiness": entry.selection_readiness,
        "selection_score": entry.selection_score,
        "operator_action": entry.operator_action,
        "event_row_count": entry.event_row_count,
        "mock_message_count": entry.mock_message_count,
        "deferred_row_count": entry.deferred_row_count,
        "preview": to_dual_machine_style_selection_mock_preview_json(entry.preview_plan),
    }


def to_dual_machine_style_live_audition_json(
    plan: DualMachineStyleLiveAuditionPlan,
) -> dict[str, object]:
    """Return deterministic live-audition metadata for GUI/analyzer consumers."""

    return {
        "style_keys": list(plan.style_keys),
        "scope": plan.scope,
        "discovery_amount": plan.discovery_amount,
        "discovery_band": plan.discovery_band,
        "mutation_depth": plan.mutation_depth,
        "selection_rank": plan.selection_rank,
        "totals": _totals_json(plan),
        "entries": [_entry_json(entry) for entry in plan.entries],
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


def _parse_positive_int(value: str, *, option: str) -> int:
    parsed = _parse_nonnegative_int(value, option=option)
    if parsed < 1:
        raise ValueError(f"{option} must be >= 1")
    return parsed


def _parse_discovery_amount(value: str, *, option: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc
    style_discovery_policy(parsed)
    return parsed


def _pop_option_value(remaining: list[str]) -> str:
    if not remaining:
        raise ValueError(_USAGE)
    return remaining.pop(0)


def _auto_scope(
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
) -> str:
    if rytm_sysex_path is not None and analog_four_sysex_path is not None:
        return "dual"
    if rytm_sysex_path is not None:
        return "rytm-only"
    if analog_four_sysex_path is not None:
        return "analog-four-only"
    raise ValueError("live audition requires at least one of --rytm or --analog-four")


def _parse_style_keys(remaining: list[str]) -> tuple[str, ...]:
    style_keys: list[str] = []
    while remaining and not remaining[0].startswith("--"):
        style_keys.append(remaining.pop(0))
    if not style_keys:
        raise ValueError(_USAGE)
    return _normalized_style_keys(style_keys)


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if not argv:
        raise ValueError(_USAGE)
    remaining = list(argv)
    style_keys = _parse_style_keys(remaining)
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank = _DEFAULT_SELECTION_RANK
    discovery_amount = DEFAULT_STYLE_DISCOVERY_AMOUNT
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
        if option not in _CLI_OPTIONS:
            raise ValueError(_USAGE)
        value = _pop_option_value(remaining)
        if option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--rank":
            selection_rank = _parse_positive_int(value, option=option)
        elif option == "--discovery":
            discovery_amount = _parse_discovery_amount(value, option=option)
        else:
            event_limit = _parse_nonnegative_int(value, option=option)
    normalized_scope = (
        _auto_scope(rytm_sysex_path, analog_four_sysex_path) if scope is None else scope
    )
    return {
        "style_keys": style_keys,
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": normalized_scope,
        "selection_rank": selection_rank,
        "discovery_amount": discovery_amount,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
    style_keys: Sequence[str],
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str,
    selection_rank: int,
    discovery_amount: int,
    include_events: bool,
    event_limit: int,
    json_output: bool,
) -> int:
    try:
        plan = build_dual_machine_style_live_audition_report(
            style_keys,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            discovery_amount=discovery_amount,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_dual_machine_style_live_audition_json(plan),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_dual_machine_style_live_audition_report(
            plan,
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


DUAL_MACHINE_STYLE_LIVE_AUDITION_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="dual-machine-style-live-audition-report",
    summary="Print passive live-audition plans from multiple style selections.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(DUAL_MACHINE_STYLE_LIVE_AUDITION_CLI_COMMAND)

__all__ = [
    "DUAL_MACHINE_STYLE_LIVE_AUDITION_CLI_COMMAND",
    "DualMachineStyleLiveAuditionEntry",
    "DualMachineStyleLiveAuditionPlan",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_dual_machine_style_live_audition_report",
    "format_dual_machine_style_live_audition_report",
    "to_dual_machine_style_live_audition_json",
]
