"""Passive Rytm style snapshot routing report."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..devices.strategies import RytmKitSnapshot, RytmStyleSnapshotRoutingPlan
from ..devices.strategies.analog_rytm_style_snapshot_routing import (
    RytmStyleMachineCandidate,
    plan_rytm_style_snapshot_routes,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines
from .rytm_snapshot_intelligence import (
    decode_supported_rytm_snapshots_from_path,
    select_supported_rytm_snapshot,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive Rytm style snapshot routing"
SOURCE_MODULE: Final[str] = "reports.rytm_style_snapshot_routing"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "style routing metadata only",
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
    "rytm-style-snapshot-routing-report usage: " "<syx-path> <style-key> [--slot N]"
)
_DEFAULT_SLOT: Final[int] = 0


def _join(values: Sequence[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def _candidate_text(candidate: RytmStyleMachineCandidate) -> str:
    return (
        f"{candidate.machine_key} / CC15 {candidate.machine_value} "
        f"({candidate.support_status}, score {candidate.score})"
    )


def _candidate_lines(
    title: str,
    candidates: Sequence[RytmStyleMachineCandidate],
) -> list[str]:
    if not candidates:
        return [f"  {title}: none"]
    return [f"  {title}:"] + [f"    - {_candidate_text(candidate)}" for candidate in candidates]


def _body_lines(plan: RytmStyleSnapshotRoutingPlan) -> list[str]:
    lines = [
        f"Kit: {plan.kit_name}",
        f"Slot: {plan.slot}",
        f"Style target: {plan.style_key}",
        "Summary:",
        f"- Ready pads: {plan.ready_pad_count}",
        f"- Blocked pads: {plan.blocked_pad_count}",
        f"- Partial snapshot mutation ready: {plan.partial_snapshot_mutation_ready}",
        f"Favored zones: {_join(plan.favored_zones)}",
        "Pads:",
    ]
    for pad in sorted(plan.pads_by_pad):
        pad_plan = plan.pads_by_pad[pad]
        machine_text = (
            "unknown"
            if pad_plan.current_machine_key is None
            else f"{pad_plan.current_machine_key} / CC15 {pad_plan.current_machine_value}"
        )
        lines.extend(
            [
                f"Pad {pad_plan.pad} / {pad_plan.track_code} / {pad_plan.label}:",
                f"  Current machine: {machine_text}",
                f"  Profile key: {pad_plan.profile_key or 'none'}",
                f"  Route ready: {pad_plan.route_ready}",
                f"  Reason: {pad_plan.readiness_reason}",
                f"  Favored zones: {_join(pad_plan.favored_zones)}",
            ]
        )
        lines.extend(_candidate_lines("Mutable candidates", pad_plan.mutable_machine_candidates))
        lines.extend(
            _candidate_lines(
                "Compatible candidates",
                pad_plan.compatible_machine_candidates,
            )
        )
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_rytm_style_snapshot_routing_report(
    snapshot_or_plan: RytmKitSnapshot | RytmStyleSnapshotRoutingPlan,
    *,
    style_key: str,
) -> list[str]:
    """Return deterministic operator-facing lines for style snapshot routing."""

    plan = (
        snapshot_or_plan
        if isinstance(snapshot_or_plan, RytmStyleSnapshotRoutingPlan)
        else plan_rytm_style_snapshot_routes(snapshot_or_plan, style_key)
    )
    return passive_report_lines(_HEADER, _body_lines(plan))


def _parse_nonnegative_int(value: str, *, option: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{option} must be >= 0")
    return parsed


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if len(argv) < 2:
        raise ValueError(_USAGE)
    sysex_path = Path(argv[0])
    style_key = argv[1]
    slot = _DEFAULT_SLOT
    remaining = list(argv[2:])
    while remaining:
        option = remaining.pop(0)
        if len(remaining) < 1:
            raise ValueError(_USAGE)
        value = remaining.pop(0)
        if option == "--slot":
            slot = _parse_nonnegative_int(value, option=option)
        else:
            raise ValueError(_USAGE)
    return {"sysex_path": sysex_path, "style_key": style_key, "slot": slot}


def _handle_cli_report(*, sysex_path: Path, style_key: str, slot: int) -> int:
    try:
        snapshots = decode_supported_rytm_snapshots_from_path(sysex_path)
        snapshot = select_supported_rytm_snapshot(sysex_path, slot, snapshots)
        lines = format_rytm_style_snapshot_routing_report(snapshot, style_key=style_key)
    except (OSError, ValueError, NotImplementedError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


RYTM_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="rytm-style-snapshot-routing-report",
    summary="Print passive Rytm style snapshot routing for a SysEx file.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(RYTM_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND)

__all__ = [
    "REPORT_TITLE",
    "RYTM_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "format_rytm_style_snapshot_routing_report",
]
