"""Passive Analog Four style mutation-intent report."""

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
from ..devices.strategies.analog_four_style_mutation_intent import (
    AnalogFourStyleMutationIntentPlan,
    AnalogFourStyleMutationIntentRow,
    plan_analog_four_style_mutation_intent,
)
from .analog_four_style_snapshot_routing import (
    decode_supported_analog_four_snapshots_from_path,
    select_supported_analog_four_snapshot,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four style mutation intent"
SOURCE_MODULE: Final[str] = "reports.analog_four_style_mutation_intent"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "style mutation intent metadata only",
    "candidate-only A4 offsets still block real mutation",
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
    "analog-four-style-mutation-intent-report usage: "
    "<syx-path> <style-key> [--slot N] [--discovery N] [--json]"
)
_DEFAULT_SLOT: Final[int] = 0


def _join(values: Sequence[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def _row_text(row: AnalogFourStyleMutationIntentRow) -> str:
    return (
        f"    - {row.zone} | depth {row.mutation_depth} "
        f"| bias {row.target_bias} | direction {row.target_direction}"
    )


def _body_lines(plan: AnalogFourStyleMutationIntentPlan) -> list[str]:
    lines = [
        f"Kit: {plan.kit_name}",
        f"Slot: {plan.slot}",
        f"Style target: {plan.style_key}",
        f"Discovery amount: {plan.discovery_amount}",
        f"Discovery band: {plan.discovery_band}",
        f"Mutation depth: {plan.mutation_depth}",
        "Summary:",
        f"- Ready tracks: {plan.ready_track_count}",
        f"- Blocked tracks: {plan.blocked_track_count}",
        f"- Intent rows: {plan.intent_row_count}",
        "Tracks:",
    ]
    for track in sorted(plan.tracks_by_track):
        track_intent = plan.tracks_by_track[track]
        lines.extend(
            [
                (
                    f"Track {track_intent.track} / {track_intent.role_key} / "
                    f"{track_intent.label}:"
                ),
                f"  Route ready: {track_intent.route_ready}",
                f"  Reason: {track_intent.readiness_reason or 'ready for promoted-offset planning'}",
                f"  Favored zones: {_join(track_intent.favored_zones)}",
            ]
        )
        if not track_intent.intent_rows:
            lines.append("  Zone intents: none")
        else:
            lines.append("  Zone intents:")
            lines.extend(_row_text(row) for row in track_intent.intent_rows)
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_analog_four_style_mutation_intent_report(
    snapshot_or_plan: AnalogFourKitSnapshot | AnalogFourStyleMutationIntentPlan,
    *,
    style_key: str,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> list[str]:
    """Return deterministic operator-facing A4 style mutation-intent lines."""

    plan = (
        snapshot_or_plan
        if isinstance(snapshot_or_plan, AnalogFourStyleMutationIntentPlan)
        else plan_analog_four_style_mutation_intent(
            snapshot_or_plan,
            style_key,
            discovery_amount=discovery_amount,
        )
    )
    return passive_report_lines(_HEADER, _body_lines(plan))


def _row_json(row: AnalogFourStyleMutationIntentRow) -> dict[str, object]:
    return {
        "zone": row.zone,
        "mutation_depth": row.mutation_depth,
        "target_bias": row.target_bias,
        "target_direction": row.target_direction,
    }


def to_analog_four_style_mutation_intent_json(
    plan: AnalogFourStyleMutationIntentPlan,
) -> dict[str, object]:
    """Return deterministic machine-readable A4 style mutation intent."""

    return {
        "kit_name": plan.kit_name,
        "slot": plan.slot,
        "style_key": plan.style_key,
        "discovery_amount": plan.discovery_amount,
        "discovery_band": plan.discovery_band,
        "mutation_depth": plan.mutation_depth,
        "ready_track_count": plan.ready_track_count,
        "blocked_track_count": plan.blocked_track_count,
        "intent_row_count": plan.intent_row_count,
        "tracks": [
            {
                "track": track_intent.track,
                "role_key": track_intent.role_key,
                "label": track_intent.label,
                "route_ready": track_intent.route_ready,
                "readiness_reason": track_intent.readiness_reason,
                "favored_zones": list(track_intent.favored_zones),
                "mutation_depth": track_intent.mutation_depth,
                "intent_row_count": track_intent.intent_row_count,
                "intent_rows": [_row_json(row) for row in track_intent.intent_rows],
            }
            for track_intent in (
                plan.tracks_by_track[track] for track in sorted(plan.tracks_by_track)
            )
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
        snapshots = decode_supported_analog_four_snapshots_from_path(sysex_path)
        snapshot = select_supported_analog_four_snapshot(sysex_path, slot, snapshots)
        plan = plan_analog_four_style_mutation_intent(
            snapshot,
            style_key,
            discovery_amount=discovery_amount,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_analog_four_style_mutation_intent_json(plan),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_analog_four_style_mutation_intent_report(
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


ANALOG_FOUR_STYLE_MUTATION_INTENT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-style-mutation-intent-report",
    summary="Print passive Analog Four style mutation intent for a SysEx file.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(ANALOG_FOUR_STYLE_MUTATION_INTENT_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_STYLE_MUTATION_INTENT_CLI_COMMAND",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "format_analog_four_style_mutation_intent_report",
    "to_analog_four_style_mutation_intent_json",
]
