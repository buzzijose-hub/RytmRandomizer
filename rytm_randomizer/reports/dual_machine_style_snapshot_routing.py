"""Passive dual-machine style snapshot routing report."""

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
    AnalogFourStyleSnapshotRoutingPlan,
    RytmKitSnapshot,
    RytmStyleSnapshotRoutingPlan,
)
from ..devices.strategies.analog_four_style_snapshot_routing import (
    plan_analog_four_style_snapshot_routes,
)
from ..devices.strategies.analog_rytm_style_snapshot_routing import (
    plan_rytm_style_snapshot_routes,
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

REPORT_TITLE: Final[str] = "RytmRandomizer passive dual-machine style snapshot routing"
SOURCE_MODULE: Final[str] = "reports.dual_machine_style_snapshot_routing"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "dual-machine style routing metadata only",
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
_USAGE: Final[str] = (
    "dual-machine-style-snapshot-routing-report usage: "
    "<rytm-syx-path> <a4-syx-path> <style-key> "
    "[--rytm-slot N] [--a4-slot N] [--discovery N] [--json]"
)
_DEFAULT_SLOT: Final[int] = 0


@dataclass(frozen=True)
class DualMachineStyleSnapshotRoutingPlan:
    """Rig-level passive style-routing summary for Rytm plus Analog Four."""

    style_key: str
    discovery_amount: int
    discovery_band: str
    machine_switching_allowed: bool
    favored_zones: tuple[str, ...]
    rig_readiness: str
    rytm_kit_name: str
    rytm_slot: int
    rytm_ready_pad_count: int
    rytm_blocked_pad_count: int
    rytm_partial_snapshot_mutation_ready: bool
    analog_four_kit_name: str
    analog_four_slot: int
    analog_four_ready_track_count: int
    analog_four_blocked_track_count: int
    analog_four_partial_snapshot_mutation_ready: bool
    analog_four_candidate_only: bool


def _join(values: Sequence[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


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
    snapshot_or_plan: RytmKitSnapshot | RytmStyleSnapshotRoutingPlan,
    *,
    style_key: str,
    discovery_amount: int,
) -> RytmStyleSnapshotRoutingPlan:
    return (
        snapshot_or_plan
        if isinstance(snapshot_or_plan, RytmStyleSnapshotRoutingPlan)
        else plan_rytm_style_snapshot_routes(
            snapshot_or_plan,
            style_key,
            discovery_amount=discovery_amount,
        )
    )


def _as_analog_four_plan(
    snapshot_or_plan: AnalogFourKitSnapshot | AnalogFourStyleSnapshotRoutingPlan,
    *,
    style_key: str,
    discovery_amount: int,
) -> AnalogFourStyleSnapshotRoutingPlan:
    return (
        snapshot_or_plan
        if isinstance(snapshot_or_plan, AnalogFourStyleSnapshotRoutingPlan)
        else plan_analog_four_style_snapshot_routes(
            snapshot_or_plan,
            style_key,
            discovery_amount=discovery_amount,
        )
    )


def build_dual_machine_style_snapshot_routing_report(
    rytm_snapshot_or_plan: RytmKitSnapshot | RytmStyleSnapshotRoutingPlan,
    analog_four_snapshot_or_plan: AnalogFourKitSnapshot | AnalogFourStyleSnapshotRoutingPlan,
    *,
    style_key: str,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> DualMachineStyleSnapshotRoutingPlan:
    """Return a passive rig-level style-routing summary."""

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
    favored_zones = tuple(
        dict.fromkeys((*rytm_plan.favored_zones, *analog_four_plan.favored_zones))
    )
    return DualMachineStyleSnapshotRoutingPlan(
        style_key=rytm_plan.style_key,
        discovery_amount=policy.amount,
        discovery_band=policy.band,
        machine_switching_allowed=policy.machine_switching_allowed,
        favored_zones=favored_zones,
        rig_readiness=_rig_readiness(ready_count=ready_count, blocked_count=blocked_count),
        rytm_kit_name=rytm_plan.kit_name,
        rytm_slot=rytm_plan.slot,
        rytm_ready_pad_count=rytm_plan.ready_pad_count,
        rytm_blocked_pad_count=rytm_plan.blocked_pad_count,
        rytm_partial_snapshot_mutation_ready=rytm_plan.partial_snapshot_mutation_ready,
        analog_four_kit_name=analog_four_plan.kit_name,
        analog_four_slot=analog_four_plan.slot,
        analog_four_ready_track_count=analog_four_plan.ready_track_count,
        analog_four_blocked_track_count=analog_four_plan.blocked_track_count,
        analog_four_partial_snapshot_mutation_ready=(
            analog_four_plan.partial_snapshot_mutation_ready
        ),
        analog_four_candidate_only=not analog_four_plan.partial_snapshot_mutation_ready,
    )


def _body_lines(plan: DualMachineStyleSnapshotRoutingPlan) -> list[str]:
    lines = [
        f"Style target: {plan.style_key}",
        f"Discovery amount: {plan.discovery_amount}",
        f"Discovery band: {plan.discovery_band}",
        f"Machine switching allowed: {plan.machine_switching_allowed}",
        f"Rig readiness: {plan.rig_readiness}",
        f"Favored zones: {_join(plan.favored_zones)}",
        "Rytm:",
        f"- Kit: {plan.rytm_kit_name}",
        f"- Slot: {plan.rytm_slot}",
        f"- Ready pads: {plan.rytm_ready_pad_count}",
        f"- Blocked pads: {plan.rytm_blocked_pad_count}",
        f"- Partial snapshot mutation ready: {plan.rytm_partial_snapshot_mutation_ready}",
        "Analog Four:",
        f"- Kit: {plan.analog_four_kit_name}",
        f"- Slot: {plan.analog_four_slot}",
        f"- Ready tracks: {plan.analog_four_ready_track_count}",
        f"- Blocked tracks: {plan.analog_four_blocked_track_count}",
        "- Partial snapshot mutation ready: " f"{plan.analog_four_partial_snapshot_mutation_ready}",
        f"- Candidate-only A4 offsets: {plan.analog_four_candidate_only}",
        SAFETY_SECTION_HEADER,
    ]
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_dual_machine_style_snapshot_routing_report(
    plan: DualMachineStyleSnapshotRoutingPlan,
) -> list[str]:
    """Return deterministic operator-facing lines for dual-machine style routing."""

    return passive_report_lines(_HEADER, _body_lines(plan))


def to_dual_machine_style_snapshot_routing_json(
    plan: DualMachineStyleSnapshotRoutingPlan,
) -> dict[str, object]:
    """Return a deterministic machine-readable payload for future UI/analyzer use."""

    return {
        "style_key": plan.style_key,
        "discovery_amount": plan.discovery_amount,
        "discovery_band": plan.discovery_band,
        "machine_switching_allowed": plan.machine_switching_allowed,
        "rig_readiness": plan.rig_readiness,
        "favored_zones": list(plan.favored_zones),
        "machines": {
            "analog_four": {
                "blocked_track_count": plan.analog_four_blocked_track_count,
                "candidate_only_offsets": plan.analog_four_candidate_only,
                "kit_name": plan.analog_four_kit_name,
                "partial_snapshot_mutation_ready": (
                    plan.analog_four_partial_snapshot_mutation_ready
                ),
                "ready_track_count": plan.analog_four_ready_track_count,
                "slot": plan.analog_four_slot,
            },
            "rytm": {
                "blocked_pad_count": plan.rytm_blocked_pad_count,
                "kit_name": plan.rytm_kit_name,
                "partial_snapshot_mutation_ready": plan.rytm_partial_snapshot_mutation_ready,
                "ready_pad_count": plan.rytm_ready_pad_count,
                "slot": plan.rytm_slot,
            },
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
        plan = build_dual_machine_style_snapshot_routing_report(
            rytm_snapshot,
            analog_four_snapshot,
            style_key=style_key,
            discovery_amount=discovery_amount,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_dual_machine_style_snapshot_routing_json(plan),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_dual_machine_style_snapshot_routing_report(plan)
    except (OSError, ValueError, NotImplementedError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


DUAL_MACHINE_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="dual-machine-style-snapshot-routing-report",
    summary="Print passive dual-machine style snapshot routing for Rytm and A4 SysEx files.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(DUAL_MACHINE_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND)

__all__ = [
    "DUAL_MACHINE_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND",
    "DualMachineStyleSnapshotRoutingPlan",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_dual_machine_style_snapshot_routing_report",
    "format_dual_machine_style_snapshot_routing_report",
    "to_dual_machine_style_snapshot_routing_json",
]
