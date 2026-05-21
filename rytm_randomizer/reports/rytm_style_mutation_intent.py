"""Passive Rytm style mutation-intent report."""

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
from ..devices.strategies.analog_rytm_style_mutation_intent import (
    RytmStyleMutationIntentPlan,
    RytmStyleMutationIntentRow,
    plan_rytm_style_mutation_intent,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines
from .rytm_snapshot_intelligence import (
    decode_supported_rytm_snapshots_from_path,
    select_supported_rytm_snapshot,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive Rytm style mutation intent"
SOURCE_MODULE: Final[str] = "reports.rytm_style_mutation_intent"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "style mutation intent metadata only",
    "no MIDI rendering",
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
    "rytm-style-mutation-intent-report usage: "
    "<syx-path> <style-key> [--slot N] [--discovery N] [--json]"
)
_DEFAULT_SLOT: Final[int] = 0


def _join(values: Sequence[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def _row_text(row: RytmStyleMutationIntentRow) -> str:
    return (
        f"    - {row.zone} | {row.parameter} | safe {row.low}-{row.high} "
        f"| depth {row.mutation_depth} | bias {row.target_bias} "
        f"| direction {row.target_direction}"
    )


def _body_lines(plan: RytmStyleMutationIntentPlan) -> list[str]:
    lines = [
        f"Kit: {plan.kit_name}",
        f"Slot: {plan.slot}",
        f"Style target: {plan.style_key}",
        f"Discovery amount: {plan.discovery_amount}",
        f"Discovery band: {plan.discovery_band}",
        f"Mutation depth: {plan.mutation_depth}",
        "Summary:",
        f"- Ready pads: {plan.ready_pad_count}",
        f"- Blocked pads: {plan.blocked_pad_count}",
        f"- Intent rows: {plan.intent_row_count}",
        "Pads:",
    ]
    for pad in sorted(plan.pads_by_pad):
        pad_intent = plan.pads_by_pad[pad]
        lines.extend(
            [
                f"Pad {pad_intent.pad} / {pad_intent.track_code} / {pad_intent.label}:",
                f"  Current machine: {pad_intent.current_machine_key or 'unknown'}",
                f"  Profile key: {pad_intent.profile_key or 'none'}",
                f"  Route ready: {pad_intent.route_ready}",
                f"  Reason: {pad_intent.readiness_reason}",
                f"  Favored zones: {_join(pad_intent.favored_zones)}",
            ]
        )
        if not pad_intent.intent_rows:
            lines.append("  Intent rows: none")
        else:
            lines.append("  Intent rows:")
            lines.extend(_row_text(row) for row in pad_intent.intent_rows)
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_rytm_style_mutation_intent_report(
    snapshot_or_plan: RytmKitSnapshot | RytmStyleMutationIntentPlan,
    *,
    style_key: str,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> list[str]:
    """Return deterministic operator-facing style mutation-intent lines."""

    plan = (
        snapshot_or_plan
        if isinstance(snapshot_or_plan, RytmStyleMutationIntentPlan)
        else plan_rytm_style_mutation_intent(
            snapshot_or_plan,
            style_key,
            discovery_amount=discovery_amount,
        )
    )
    return passive_report_lines(_HEADER, _body_lines(plan))


def _row_json(row: RytmStyleMutationIntentRow) -> dict[str, object]:
    return {
        "zone": row.zone,
        "parameter": row.parameter,
        "low": row.low,
        "high": row.high,
        "mutation_depth": row.mutation_depth,
        "target_bias": row.target_bias,
        "target_direction": row.target_direction,
    }


def to_rytm_style_mutation_intent_json(
    plan: RytmStyleMutationIntentPlan,
) -> dict[str, object]:
    """Return deterministic machine-readable Rytm style mutation intent."""

    return {
        "kit_name": plan.kit_name,
        "slot": plan.slot,
        "style_key": plan.style_key,
        "discovery_amount": plan.discovery_amount,
        "discovery_band": plan.discovery_band,
        "mutation_depth": plan.mutation_depth,
        "ready_pad_count": plan.ready_pad_count,
        "blocked_pad_count": plan.blocked_pad_count,
        "intent_row_count": plan.intent_row_count,
        "pads": [
            {
                "pad": pad_intent.pad,
                "track_code": pad_intent.track_code,
                "label": pad_intent.label,
                "current_machine_key": pad_intent.current_machine_key,
                "profile_key": pad_intent.profile_key,
                "route_ready": pad_intent.route_ready,
                "readiness_reason": pad_intent.readiness_reason,
                "favored_zones": list(pad_intent.favored_zones),
                "intent_row_count": pad_intent.intent_row_count,
                "intent_rows": [_row_json(row) for row in pad_intent.intent_rows],
            }
            for pad_intent in (plan.pads_by_pad[pad] for pad in sorted(plan.pads_by_pad))
        ],
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
        if option == "--slot":
            slot = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery":
            discovery_amount = _parse_discovery_amount(value, option=option)
        else:
            raise ValueError(_USAGE)
    return {
        "sysex_path": sysex_path,
        "style_key": style_key,
        "slot": slot,
        "discovery_amount": discovery_amount,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
    sysex_path: Path,
    style_key: str,
    slot: int,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
    json_output: bool = False,
) -> int:
    try:
        snapshots = decode_supported_rytm_snapshots_from_path(sysex_path)
        snapshot = select_supported_rytm_snapshot(sysex_path, slot, snapshots)
        plan = plan_rytm_style_mutation_intent(
            snapshot,
            style_key,
            discovery_amount=discovery_amount,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_rytm_style_mutation_intent_json(plan),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_rytm_style_mutation_intent_report(
            plan,
            style_key=style_key,
            discovery_amount=discovery_amount,
        )
    except (OSError, ValueError, NotImplementedError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


RYTM_STYLE_MUTATION_INTENT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="rytm-style-mutation-intent-report",
    summary="Print passive Rytm style mutation intent for a SysEx file.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(RYTM_STYLE_MUTATION_INTENT_CLI_COMMAND)

__all__ = [
    "REPORT_TITLE",
    "RYTM_STYLE_MUTATION_INTENT_CLI_COMMAND",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "format_rytm_style_mutation_intent_report",
    "to_rytm_style_mutation_intent_json",
]
