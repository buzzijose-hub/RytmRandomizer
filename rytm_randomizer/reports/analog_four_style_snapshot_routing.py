"""Passive Analog Four style snapshot routing report."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..devices.strategies import (
    AnalogFourKitSnapshot,
    AnalogFourSnapshotDecoder,
    AnalogFourStyleSnapshotRoutingPlan,
    AnalogFourStyleTrackPlan,
)
from ..devices.strategies.analog_four_style_snapshot_routing import (
    plan_analog_four_style_snapshot_routes,
)
from ..snapshot.sysex_file import read_sysex_payloads_from_path
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four style snapshot routing"
SOURCE_MODULE: Final[str] = "reports.analog_four_style_snapshot_routing"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "style routing metadata only",
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
    "analog-four-style-snapshot-routing-report usage: " "<syx-path> <style-key> [--slot N]"
)
_DEFAULT_SLOT: Final[int] = 0


def _join(values: Sequence[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def _track_lines(track_plan: AnalogFourStyleTrackPlan) -> list[str]:
    return [
        f"Track {track_plan.track} / {track_plan.role_key} / {track_plan.label}:",
        f"  Route ready: {track_plan.route_ready}",
        f"  Reason: {track_plan.readiness_reason or 'ready for promoted-offset planning'}",
        f"  Score: {track_plan.score}",
        f"  Favored zones: {_join(track_plan.favored_zones)}",
    ]


def _body_lines(plan: AnalogFourStyleSnapshotRoutingPlan) -> list[str]:
    lines = [
        f"Kit: {plan.kit_name}",
        f"Slot: {plan.slot}",
        f"Style target: {plan.style_key}",
        "Summary:",
        f"- Ready tracks: {plan.ready_track_count}",
        f"- Blocked tracks: {plan.blocked_track_count}",
        f"- Partial snapshot mutation ready: {plan.partial_snapshot_mutation_ready}",
        f"Favored zones: {_join(plan.favored_zones)}",
        "Analog Four focus:",
        *[f"- {focus}" for focus in plan.style_focus],
        "Tracks:",
    ]
    for track in sorted(plan.tracks_by_track):
        lines.extend(_track_lines(plan.tracks_by_track[track]))

    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_analog_four_style_snapshot_routing_report(
    snapshot_or_plan: AnalogFourKitSnapshot | AnalogFourStyleSnapshotRoutingPlan,
    *,
    style_key: str,
) -> list[str]:
    """Return deterministic operator-facing lines for A4 style routing."""

    plan = (
        snapshot_or_plan
        if isinstance(snapshot_or_plan, AnalogFourStyleSnapshotRoutingPlan)
        else plan_analog_four_style_snapshot_routes(snapshot_or_plan, style_key)
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


def decode_supported_analog_four_snapshots_from_path(
    sysex_path: Path,
) -> tuple[AnalogFourKitSnapshot, ...]:
    """Return supported Analog Four kit snapshots from a framed SysEx file."""

    decoder = AnalogFourSnapshotDecoder()
    errors: list[str] = []
    snapshots: list[AnalogFourKitSnapshot] = []
    for index, payload in enumerate(read_sysex_payloads_from_path(sysex_path), start=1):
        try:
            snapshots.append(decoder.decode(payload, slot=len(snapshots)))
        except ValueError as exc:
            errors.append(f"frame {index}: {exc}")
    if snapshots:
        return tuple(snapshots)
    detail = "; ".join(errors) if errors else "no SysEx payloads found"
    raise ValueError(f"No supported Analog Four kit snapshot found in {sysex_path}: {detail}")


def _available_slot_lines(snapshots: Sequence[AnalogFourKitSnapshot]) -> tuple[str, ...]:
    return tuple(f"Slot {snapshot.slot}: {snapshot.kit_name}" for snapshot in snapshots)


def select_supported_analog_four_snapshot(
    sysex_path: Path,
    slot: int,
    snapshots: Sequence[AnalogFourKitSnapshot],
) -> AnalogFourKitSnapshot:
    """Return the supported A4 snapshot for ``slot`` or raise an operator error."""

    if slot < len(snapshots):
        return snapshots[slot]
    snapshot_noun = "snapshot" if len(snapshots) == 1 else "snapshots"
    available = "; ".join(_available_slot_lines(snapshots))
    raise ValueError(
        f"Requested --slot {slot}, but only {len(snapshots)} supported Analog Four "
        f"kit {snapshot_noun} found in {sysex_path}. Available slots: {available}"
    )


def _handle_cli_report(*, sysex_path: Path, style_key: str, slot: int) -> int:
    try:
        snapshots = decode_supported_analog_four_snapshots_from_path(sysex_path)
        snapshot = select_supported_analog_four_snapshot(sysex_path, slot, snapshots)
        lines = format_analog_four_style_snapshot_routing_report(
            snapshot,
            style_key=style_key,
        )
    except (OSError, ValueError, NotImplementedError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


ANALOG_FOUR_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-style-snapshot-routing-report",
    summary="Print passive Analog Four style snapshot routing for a SysEx file.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(ANALOG_FOUR_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "decode_supported_analog_four_snapshots_from_path",
    "format_analog_four_style_snapshot_routing_report",
    "select_supported_analog_four_snapshot",
]
