"""Passive Analog Rytm snapshot mutation preview report."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..devices.analog_rytm import AnalogRytmDevice
from ..devices.strategies import MAX_DEPTH, RytmKitSnapshot
from ..senders.guarded import guarded_send
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines
from .rytm_snapshot_intelligence import (
    decode_supported_rytm_snapshots_from_path,
    select_supported_rytm_snapshot,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive Rytm snapshot mutation preview"
SOURCE_MODULE: Final[str] = "reports.rytm_snapshot_mutation_preview"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "mock-only preview",
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
    "rytm-snapshot-mutation-preview-report usage: <syx-path> [--slot N] [--depth N]"
)
_DEFAULT_SLOT: Final[int] = 0
_DEFAULT_DEPTH: Final[int] = 1


@dataclass(frozen=True)
class RytmSnapshotMutationPreviewReport:
    """Passive mutation-plan preview for one decoded Rytm kit snapshot."""

    kit_name: str
    slot: int
    depth: int
    plan_ready: bool
    readiness_reason: str
    mutation_event_count: int
    mock_message_count: int
    planned_pads: tuple[int, ...]


def build_rytm_snapshot_mutation_preview_report(
    snapshot: RytmKitSnapshot,
    *,
    depth: int,
) -> RytmSnapshotMutationPreviewReport:
    """Return a no-hardware mutation preview for ``snapshot`` at ``depth``."""

    device = AnalogRytmDevice()
    plan = device.mutation_planner.plan_for_snapshot_machine_facts(snapshot, depth)
    result = guarded_send(device, plan)
    planned_pads = tuple(sorted({event.pad for event in plan.events}))
    readiness_reason = "ready" if result.ready else result.reason
    return RytmSnapshotMutationPreviewReport(
        kit_name=snapshot.kit_name,
        slot=snapshot.slot,
        depth=depth,
        plan_ready=result.ready,
        readiness_reason=readiness_reason,
        mutation_event_count=len(plan.events),
        mock_message_count=result.sent_count,
        planned_pads=planned_pads,
    )


def _planned_pads_text(planned_pads: Sequence[int]) -> str:
    if not planned_pads:
        return "none"
    return ", ".join(str(pad) for pad in planned_pads)


def _body_lines(report: RytmSnapshotMutationPreviewReport) -> list[str]:
    lines = [
        f"Kit: {report.kit_name}",
        f"Slot: {report.slot}",
        f"Depth: {report.depth}",
        "Preview:",
        f"- Plan ready: {report.plan_ready}",
        f"- Readiness reason: {report.readiness_reason}",
        f"- Mutation events: {report.mutation_event_count}",
        f"- Mock messages: {report.mock_message_count}",
        f"- Planned pads: {_planned_pads_text(report.planned_pads)}",
        SAFETY_SECTION_HEADER,
    ]
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_rytm_snapshot_mutation_preview_report(
    snapshot_or_report: RytmKitSnapshot | RytmSnapshotMutationPreviewReport,
    *,
    depth: int = _DEFAULT_DEPTH,
) -> list[str]:
    """Return deterministic operator-facing lines for a mutation preview."""

    report = (
        snapshot_or_report
        if isinstance(snapshot_or_report, RytmSnapshotMutationPreviewReport)
        else build_rytm_snapshot_mutation_preview_report(snapshot_or_report, depth=depth)
    )
    return passive_report_lines(_HEADER, _body_lines(report))


def _parse_nonnegative_int(value: str, *, option: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{option} must be >= 0")
    return parsed


def _parse_depth(value: str) -> int:
    try:
        depth = int(value)
    except ValueError as exc:
        raise ValueError("--depth must be an integer") from exc
    if depth < 0 or depth > MAX_DEPTH:
        raise ValueError(f"--depth must be in [0, {MAX_DEPTH}]")
    return depth


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if not argv:
        raise ValueError("rytm-snapshot-mutation-preview-report requires <syx-path>")
    sysex_path = Path(argv[0])
    slot = _DEFAULT_SLOT
    depth = _DEFAULT_DEPTH
    remaining = list(argv[1:])
    while remaining:
        if len(remaining) < 2:
            raise ValueError(_USAGE)
        option = remaining.pop(0)
        value = remaining.pop(0)
        if option == "--slot":
            slot = _parse_nonnegative_int(value, option=option)
        elif option == "--depth":
            depth = _parse_depth(value)
        else:
            raise ValueError(_USAGE)
    return {"sysex_path": sysex_path, "slot": slot, "depth": depth}


def _handle_cli_report(*, sysex_path: Path, slot: int, depth: int) -> int:
    try:
        snapshots = decode_supported_rytm_snapshots_from_path(sysex_path)
        snapshot = select_supported_rytm_snapshot(sysex_path, slot, snapshots)
    except (OSError, ValueError, NotImplementedError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(format_rytm_snapshot_mutation_preview_report(snapshot, depth=depth)))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


RYTM_SNAPSHOT_MUTATION_PREVIEW_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="rytm-snapshot-mutation-preview-report",
    summary="Print passive Rytm snapshot mutation preview for a SysEx file.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(RYTM_SNAPSHOT_MUTATION_PREVIEW_CLI_COMMAND)


__all__ = [
    "REPORT_TITLE",
    "RYTM_SNAPSHOT_MUTATION_PREVIEW_CLI_COMMAND",
    "RytmSnapshotMutationPreviewReport",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_rytm_snapshot_mutation_preview_report",
    "format_rytm_snapshot_mutation_preview_report",
]
