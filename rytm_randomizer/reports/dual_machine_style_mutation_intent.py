"""Passive dual-machine style mutation-intent report."""

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
from ..devices.strategies import (
    AnalogFourKitSnapshot,
    AnalogFourStyleMutationIntentPlan,
    RytmKitSnapshot,
    RytmStyleMutationIntentPlan,
    plan_analog_four_style_mutation_intent,
    plan_rytm_style_mutation_intent,
)
from .analog_four_style_mutation_intent import (
    to_analog_four_style_mutation_intent_json,
)
from .analog_four_style_snapshot_routing import (
    decode_supported_analog_four_snapshots_from_path,
    select_supported_analog_four_snapshot,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines
from .rytm_snapshot_intelligence import (
    decode_supported_rytm_snapshots_from_path,
    select_supported_rytm_snapshot,
)
from .rytm_style_mutation_intent import to_rytm_style_mutation_intent_json

REPORT_TITLE: Final[str] = "RytmRandomizer passive dual-machine style mutation intent"
SOURCE_MODULE: Final[str] = "reports.dual_machine_style_mutation_intent"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "dual-machine style mutation intent metadata only",
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
    "dual-machine-style-mutation-intent-report usage: "
    "<rytm-syx-path> <a4-syx-path> <style-key> "
    "[--rytm-slot N] [--a4-slot N] [--discovery N] [--json]"
)
_DEFAULT_SLOT: Final[int] = 0


@dataclass(frozen=True)
class DualMachineStyleMutationIntentPlan:
    """Rig-level passive style mutation intent for Rytm plus Analog Four."""

    style_key: str
    discovery_amount: int
    discovery_band: str
    machine_switching_allowed: bool
    mutation_depth: str
    rig_readiness: str
    total_intent_row_count: int
    rytm_kit_name: str
    rytm_slot: int
    rytm_ready_pad_count: int
    rytm_blocked_pad_count: int
    rytm_intent_row_count: int
    analog_four_kit_name: str
    analog_four_slot: int
    analog_four_ready_track_count: int
    analog_four_blocked_track_count: int
    analog_four_intent_row_count: int
    analog_four_candidate_only: bool
    rytm_plan: RytmStyleMutationIntentPlan
    analog_four_plan: AnalogFourStyleMutationIntentPlan


def _rig_readiness(
    *,
    ready_count: int,
    blocked_count: int,
) -> str:
    if ready_count == 0:
        return "blocked"
    if blocked_count == 0:
        return "ready"
    return "partial"


def _as_rytm_plan(
    snapshot_or_plan: RytmKitSnapshot | RytmStyleMutationIntentPlan,
    *,
    style_key: str,
    discovery_amount: int,
) -> RytmStyleMutationIntentPlan:
    return (
        snapshot_or_plan
        if isinstance(snapshot_or_plan, RytmStyleMutationIntentPlan)
        else plan_rytm_style_mutation_intent(
            snapshot_or_plan,
            style_key,
            discovery_amount=discovery_amount,
        )
    )


def _as_analog_four_plan(
    snapshot_or_plan: AnalogFourKitSnapshot | AnalogFourStyleMutationIntentPlan,
    *,
    style_key: str,
    discovery_amount: int,
) -> AnalogFourStyleMutationIntentPlan:
    return (
        snapshot_or_plan
        if isinstance(snapshot_or_plan, AnalogFourStyleMutationIntentPlan)
        else plan_analog_four_style_mutation_intent(
            snapshot_or_plan,
            style_key,
            discovery_amount=discovery_amount,
        )
    )


def build_dual_machine_style_mutation_intent_report(
    rytm_snapshot_or_plan: RytmKitSnapshot | RytmStyleMutationIntentPlan,
    analog_four_snapshot_or_plan: AnalogFourKitSnapshot | AnalogFourStyleMutationIntentPlan,
    *,
    style_key: str,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> DualMachineStyleMutationIntentPlan:
    """Return a passive rig-level mutation-intent summary."""

    policy = style_discovery_policy(discovery_amount)
    rytm_plan = _as_rytm_plan(
        rytm_snapshot_or_plan,
        style_key=style_key,
        discovery_amount=policy.amount,
    )
    analog_four_plan = _as_analog_four_plan(
        analog_four_snapshot_or_plan,
        style_key=style_key,
        discovery_amount=policy.amount,
    )
    ready_count = rytm_plan.ready_pad_count + analog_four_plan.ready_track_count
    blocked_count = rytm_plan.blocked_pad_count + analog_four_plan.blocked_track_count
    total_intent_row_count = rytm_plan.intent_row_count + analog_four_plan.intent_row_count
    return DualMachineStyleMutationIntentPlan(
        style_key=rytm_plan.style_key,
        discovery_amount=policy.amount,
        discovery_band=policy.band,
        machine_switching_allowed=policy.machine_switching_allowed,
        mutation_depth=policy.mutation_depth,
        rig_readiness=_rig_readiness(ready_count=ready_count, blocked_count=blocked_count),
        total_intent_row_count=total_intent_row_count,
        rytm_kit_name=rytm_plan.kit_name,
        rytm_slot=rytm_plan.slot,
        rytm_ready_pad_count=rytm_plan.ready_pad_count,
        rytm_blocked_pad_count=rytm_plan.blocked_pad_count,
        rytm_intent_row_count=rytm_plan.intent_row_count,
        analog_four_kit_name=analog_four_plan.kit_name,
        analog_four_slot=analog_four_plan.slot,
        analog_four_ready_track_count=analog_four_plan.ready_track_count,
        analog_four_blocked_track_count=analog_four_plan.blocked_track_count,
        analog_four_intent_row_count=analog_four_plan.intent_row_count,
        analog_four_candidate_only=analog_four_plan.blocked_track_count > 0,
        rytm_plan=rytm_plan,
        analog_four_plan=analog_four_plan,
    )


def _body_lines(plan: DualMachineStyleMutationIntentPlan) -> list[str]:
    lines = [
        f"Style target: {plan.style_key}",
        f"Discovery amount: {plan.discovery_amount}",
        f"Discovery band: {plan.discovery_band}",
        f"Machine switching allowed: {plan.machine_switching_allowed}",
        f"Mutation depth: {plan.mutation_depth}",
        f"Rig readiness: {plan.rig_readiness}",
        f"Total intent rows: {plan.total_intent_row_count}",
        "Rytm:",
        f"- Kit: {plan.rytm_kit_name}",
        f"- Slot: {plan.rytm_slot}",
        f"- Ready pads: {plan.rytm_ready_pad_count}",
        f"- Blocked pads: {plan.rytm_blocked_pad_count}",
        f"- Intent rows: {plan.rytm_intent_row_count}",
        "Analog Four:",
        f"- Kit: {plan.analog_four_kit_name}",
        f"- Slot: {plan.analog_four_slot}",
        f"- Ready tracks: {plan.analog_four_ready_track_count}",
        f"- Blocked tracks: {plan.analog_four_blocked_track_count}",
        f"- Intent rows: {plan.analog_four_intent_row_count}",
        f"- Candidate-only A4 offsets: {plan.analog_four_candidate_only}",
        SAFETY_SECTION_HEADER,
    ]
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_dual_machine_style_mutation_intent_report(
    plan: DualMachineStyleMutationIntentPlan,
) -> list[str]:
    """Return deterministic operator-facing lines for dual-machine mutation intent."""

    return passive_report_lines(_HEADER, _body_lines(plan))


def to_dual_machine_style_mutation_intent_json(
    plan: DualMachineStyleMutationIntentPlan,
) -> dict[str, object]:
    """Return a deterministic machine-readable rig mutation-intent payload."""

    return {
        "style_key": plan.style_key,
        "discovery_amount": plan.discovery_amount,
        "discovery_band": plan.discovery_band,
        "machine_switching_allowed": plan.machine_switching_allowed,
        "mutation_depth": plan.mutation_depth,
        "rig_readiness": plan.rig_readiness,
        "total_intent_row_count": plan.total_intent_row_count,
        "machines": {
            "analog_four": to_analog_four_style_mutation_intent_json(plan.analog_four_plan),
            "rytm": to_rytm_style_mutation_intent_json(plan.rytm_plan),
        },
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
    rytm_slot = _DEFAULT_SLOT
    analog_four_slot = _DEFAULT_SLOT
    discovery_amount = DEFAULT_STYLE_DISCOVERY_AMOUNT
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
        if option == "--rytm-slot":
            rytm_slot = _parse_nonnegative_int(value, option=option)
        elif option == "--a4-slot":
            analog_four_slot = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery":
            discovery_amount = _parse_discovery_amount(value, option=option)
        else:
            raise ValueError(_USAGE)
    return {
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "style_key": style_key,
        "rytm_slot": rytm_slot,
        "analog_four_slot": analog_four_slot,
        "discovery_amount": discovery_amount,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
    rytm_sysex_path: Path,
    analog_four_sysex_path: Path,
    style_key: str,
    rytm_slot: int,
    analog_four_slot: int,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
    json_output: bool = False,
) -> int:
    try:
        rytm_snapshots = decode_supported_rytm_snapshots_from_path(rytm_sysex_path)
        rytm_snapshot = select_supported_rytm_snapshot(
            rytm_sysex_path,
            rytm_slot,
            rytm_snapshots,
        )
        analog_four_snapshots = decode_supported_analog_four_snapshots_from_path(
            analog_four_sysex_path
        )
        analog_four_snapshot = select_supported_analog_four_snapshot(
            analog_four_sysex_path,
            analog_four_slot,
            analog_four_snapshots,
        )
        plan = build_dual_machine_style_mutation_intent_report(
            rytm_snapshot,
            analog_four_snapshot,
            style_key=style_key,
            discovery_amount=discovery_amount,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_dual_machine_style_mutation_intent_json(plan),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_dual_machine_style_mutation_intent_report(plan)
    except (OSError, ValueError, NotImplementedError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


DUAL_MACHINE_STYLE_MUTATION_INTENT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="dual-machine-style-mutation-intent-report",
    summary="Print passive dual-machine style mutation intent for Rytm and A4 SysEx files.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(DUAL_MACHINE_STYLE_MUTATION_INTENT_CLI_COMMAND)

__all__ = [
    "DUAL_MACHINE_STYLE_MUTATION_INTENT_CLI_COMMAND",
    "DualMachineStyleMutationIntentPlan",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_dual_machine_style_mutation_intent_report",
    "format_dual_machine_style_mutation_intent_report",
    "to_dual_machine_style_mutation_intent_json",
]
