"""Passive dual-machine style mutation mock-preview report."""

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
from ..devices.strategies import AnalogFourKitSnapshot, RytmKitSnapshot
from ..devices.strategies.analog_four_style_mutation_mock_preview import (
    AnalogFourStyleMutationMockPreview,
    AnalogFourStyleMutationMockPreviewDeferredRow,
    AnalogFourStyleMutationMockPreviewEvent,
    build_analog_four_style_mutation_mock_preview,
)
from ..devices.strategies.analog_rytm_style_mutation_mock_preview import (
    RytmStyleMutationMockPreview,
    RytmStyleMutationMockPreviewEvent,
    build_rytm_style_mutation_mock_preview,
)
from .analog_four_style_mutation_mock_preview import (
    to_analog_four_style_mutation_mock_preview_json,
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
from .rytm_style_mutation_mock_preview import to_rytm_style_mutation_mock_preview_json

REPORT_TITLE: Final[str] = "RytmRandomizer passive dual-machine style mutation mock preview"
SOURCE_MODULE: Final[str] = "reports.dual_machine_style_mutation_mock_preview"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "mock-only dual-machine preview",
    "candidate-only A4 offsets still block decoded SysEx mock rows",
    "NRPN-only A4 zones are deferred",
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
    "dual-machine-style-mutation-mock-preview-report usage: "
    "<rytm-syx-path> <a4-syx-path> <style-key> "
    "[--rytm-slot N] [--a4-slot N] [--discovery N] "
    "[--events] [--limit N] [--json]"
)
_DEFAULT_SLOT: Final[int] = 0
_DEFAULT_EVENT_LIMIT: Final[int] = 24


@dataclass(frozen=True)
class DualMachineStyleMutationMockPreviewPlan:
    """Rig-level passive style mutation mock preview for Rytm plus Analog Four."""

    style_key: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    rig_readiness: str
    total_event_row_count: int
    total_mock_message_count: int
    total_deferred_row_count: int
    rytm_kit_name: str
    rytm_slot: int
    rytm_preview_ready: bool
    rytm_readiness_reason: str
    rytm_ready_pad_count: int
    rytm_blocked_pad_count: int
    rytm_render_event_count: int
    rytm_mock_message_count: int
    rytm_planned_pads: tuple[int, ...]
    analog_four_kit_name: str
    analog_four_slot: int
    analog_four_preview_ready: bool
    analog_four_readiness_reason: str
    analog_four_ready_track_count: int
    analog_four_blocked_track_count: int
    analog_four_intent_row_count: int
    analog_four_mock_message_count: int
    analog_four_deferred_row_count: int
    analog_four_planned_tracks: tuple[int, ...]
    rytm_preview: RytmStyleMutationMockPreview
    analog_four_preview: AnalogFourStyleMutationMockPreview


def _planned_numbers_text(planned_numbers: Sequence[int]) -> str:
    if not planned_numbers:
        return "none"
    return ", ".join(str(number) for number in planned_numbers)


def _rig_readiness(
    *,
    rytm_preview: RytmStyleMutationMockPreview,
    analog_four_preview: AnalogFourStyleMutationMockPreview,
) -> str:
    if rytm_preview.preview_ready and analog_four_preview.preview_ready:
        return "ready"
    if rytm_preview.preview_ready or analog_four_preview.preview_ready:
        return "partial"
    return "blocked"


def _as_rytm_preview(
    snapshot_or_preview: RytmKitSnapshot | RytmStyleMutationMockPreview,
    *,
    style_key: str,
    discovery_amount: int,
) -> RytmStyleMutationMockPreview:
    return (
        snapshot_or_preview
        if isinstance(snapshot_or_preview, RytmStyleMutationMockPreview)
        else build_rytm_style_mutation_mock_preview(
            snapshot_or_preview,
            style_key,
            discovery_amount=discovery_amount,
        )
    )


def _as_analog_four_preview(
    snapshot_or_preview: AnalogFourKitSnapshot | AnalogFourStyleMutationMockPreview,
    *,
    style_key: str,
    discovery_amount: int,
) -> AnalogFourStyleMutationMockPreview:
    return (
        snapshot_or_preview
        if isinstance(snapshot_or_preview, AnalogFourStyleMutationMockPreview)
        else build_analog_four_style_mutation_mock_preview(
            snapshot_or_preview,
            style_key,
            discovery_amount=discovery_amount,
        )
    )


def build_dual_machine_style_mutation_mock_preview_report(
    rytm_snapshot_or_preview: RytmKitSnapshot | RytmStyleMutationMockPreview,
    analog_four_snapshot_or_preview: AnalogFourKitSnapshot | AnalogFourStyleMutationMockPreview,
    *,
    style_key: str,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> DualMachineStyleMutationMockPreviewPlan:
    """Return a passive rig-level style mutation mock-preview summary."""

    policy = style_discovery_policy(discovery_amount)
    rytm_preview = _as_rytm_preview(
        rytm_snapshot_or_preview,
        style_key=style_key,
        discovery_amount=policy.amount,
    )
    analog_four_preview = _as_analog_four_preview(
        analog_four_snapshot_or_preview,
        style_key=style_key,
        discovery_amount=policy.amount,
    )
    total_event_row_count = rytm_preview.render_event_count + len(analog_four_preview.event_rows)
    total_mock_message_count = (
        rytm_preview.mock_message_count + analog_four_preview.mock_message_count
    )
    return DualMachineStyleMutationMockPreviewPlan(
        style_key=rytm_preview.style_key,
        discovery_amount=policy.amount,
        discovery_band=policy.band,
        mutation_depth=policy.mutation_depth,
        rig_readiness=_rig_readiness(
            rytm_preview=rytm_preview,
            analog_four_preview=analog_four_preview,
        ),
        total_event_row_count=total_event_row_count,
        total_mock_message_count=total_mock_message_count,
        total_deferred_row_count=analog_four_preview.deferred_row_count,
        rytm_kit_name=rytm_preview.kit_name,
        rytm_slot=rytm_preview.slot,
        rytm_preview_ready=rytm_preview.preview_ready,
        rytm_readiness_reason=rytm_preview.readiness_reason,
        rytm_ready_pad_count=rytm_preview.ready_pad_count,
        rytm_blocked_pad_count=rytm_preview.blocked_pad_count,
        rytm_render_event_count=rytm_preview.render_event_count,
        rytm_mock_message_count=rytm_preview.mock_message_count,
        rytm_planned_pads=rytm_preview.planned_pads,
        analog_four_kit_name=analog_four_preview.kit_name,
        analog_four_slot=analog_four_preview.slot,
        analog_four_preview_ready=analog_four_preview.preview_ready,
        analog_four_readiness_reason=analog_four_preview.readiness_reason,
        analog_four_ready_track_count=analog_four_preview.ready_track_count,
        analog_four_blocked_track_count=analog_four_preview.blocked_track_count,
        analog_four_intent_row_count=analog_four_preview.intent_row_count,
        analog_four_mock_message_count=analog_four_preview.mock_message_count,
        analog_four_deferred_row_count=analog_four_preview.deferred_row_count,
        analog_four_planned_tracks=analog_four_preview.planned_tracks,
        rytm_preview=rytm_preview,
        analog_four_preview=analog_four_preview,
    )


def _format_rytm_event_row(row: RytmStyleMutationMockPreviewEvent) -> str:
    return (
        f"- Rytm Pad {row.pad} | profile {row.profile_key} | {row.zone} | "
        f"{row.parameter} | ch {row.channel} | CC{row.control} -> {row.value} | "
        f"window {row.window_low}-{row.window_high} | depth {row.mutation_depth} | "
        f"direction {row.target_direction}"
    )


def _format_analog_four_event_row(row: AnalogFourStyleMutationMockPreviewEvent) -> str:
    return (
        f"- Analog Four Track {row.track} | {row.role_key} | {row.zone} | "
        f"{row.parameter} | ch {row.channel} | CC{row.control} -> {row.value} | "
        f"bias {row.target_bias} | depth {row.mutation_depth} | "
        f"direction {row.target_direction}"
    )


def _format_analog_four_deferred_row(
    row: AnalogFourStyleMutationMockPreviewDeferredRow,
) -> str:
    return (
        f"- Analog Four Track {row.track} | {row.role_key} | {row.zone} | "
        f"{row.reason} | bias {row.target_bias} | depth {row.mutation_depth} | "
        f"direction {row.target_direction}"
    )


def _combined_event_lines(
    plan: DualMachineStyleMutationMockPreviewPlan,
    *,
    event_limit: int,
) -> list[str]:
    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    rows = tuple(_format_rytm_event_row(row) for row in plan.rytm_preview.event_rows) + tuple(
        _format_analog_four_event_row(row) for row in plan.analog_four_preview.event_rows
    )
    lines = ["Event preview:"]
    if not rows:
        lines.append("- No mock rows available because the rig preview is not ready.")
        return lines
    if event_limit == 0 or event_limit >= len(rows):
        selected_rows = rows
        lines.append("- Showing all events")
    else:
        selected_rows = rows[:event_limit]
        lines.append(f"- Showing first {event_limit} of {len(rows)} events")
    lines.extend(selected_rows)
    return lines


def _deferred_preview_lines(
    deferred_rows: Sequence[AnalogFourStyleMutationMockPreviewDeferredRow],
) -> list[str]:
    lines = ["Deferred rows:"]
    if not deferred_rows:
        lines.append("- none")
        return lines
    lines.extend(_format_analog_four_deferred_row(row) for row in deferred_rows)
    return lines


def _body_lines(
    plan: DualMachineStyleMutationMockPreviewPlan,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    lines = [
        f"Style target: {plan.style_key}",
        f"Discovery amount: {plan.discovery_amount}",
        f"Discovery band: {plan.discovery_band}",
        f"Mutation depth: {plan.mutation_depth}",
        f"Rig readiness: {plan.rig_readiness}",
        f"Total event rows: {plan.total_event_row_count}",
        f"Total mock messages: {plan.total_mock_message_count}",
        f"Total deferred rows: {plan.total_deferred_row_count}",
        "Rytm:",
        f"- Kit: {plan.rytm_kit_name}",
        f"- Slot: {plan.rytm_slot}",
        f"- Preview ready: {plan.rytm_preview_ready}",
        f"- Readiness reason: {plan.rytm_readiness_reason}",
        f"- Ready pads: {plan.rytm_ready_pad_count}",
        f"- Blocked pads: {plan.rytm_blocked_pad_count}",
        f"- Render events: {plan.rytm_render_event_count}",
        f"- Mock messages: {plan.rytm_mock_message_count}",
        f"- Planned pads: {_planned_numbers_text(plan.rytm_planned_pads)}",
        "Analog Four:",
        f"- Kit: {plan.analog_four_kit_name}",
        f"- Slot: {plan.analog_four_slot}",
        f"- Preview ready: {plan.analog_four_preview_ready}",
        f"- Readiness reason: {plan.analog_four_readiness_reason}",
        f"- Ready tracks: {plan.analog_four_ready_track_count}",
        f"- Blocked tracks: {plan.analog_four_blocked_track_count}",
        f"- Intent rows: {plan.analog_four_intent_row_count}",
        f"- Mock messages: {plan.analog_four_mock_message_count}",
        f"- Deferred rows: {plan.analog_four_deferred_row_count}",
        f"- Planned tracks: {_planned_numbers_text(plan.analog_four_planned_tracks)}",
    ]
    if include_events:
        lines.extend(_combined_event_lines(plan, event_limit=event_limit))
    lines.extend(_deferred_preview_lines(plan.analog_four_preview.deferred_rows))
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_dual_machine_style_mutation_mock_preview_report(
    plan: DualMachineStyleMutationMockPreviewPlan,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing dual-machine mock-preview lines."""

    return passive_report_lines(
        _HEADER,
        _body_lines(plan, include_events=include_events, event_limit=event_limit),
    )


def to_dual_machine_style_mutation_mock_preview_json(
    plan: DualMachineStyleMutationMockPreviewPlan,
) -> dict[str, object]:
    """Return a deterministic machine-readable rig mock-preview payload."""

    return {
        "style_key": plan.style_key,
        "discovery_amount": plan.discovery_amount,
        "discovery_band": plan.discovery_band,
        "mutation_depth": plan.mutation_depth,
        "rig_readiness": plan.rig_readiness,
        "total_event_row_count": plan.total_event_row_count,
        "total_mock_message_count": plan.total_mock_message_count,
        "total_deferred_row_count": plan.total_deferred_row_count,
        "machines": {
            "analog_four": to_analog_four_style_mutation_mock_preview_json(
                plan.analog_four_preview
            ),
            "rytm": to_rytm_style_mutation_mock_preview_json(plan.rytm_preview),
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
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    remaining = list(argv[3:])
    while remaining:
        option = remaining.pop(0)
        if option == "--events":
            include_events = True
            continue
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
        elif option == "--limit":
            event_limit = _parse_nonnegative_int(value, option=option)
        else:
            raise ValueError(_USAGE)
    return {
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "style_key": style_key,
        "rytm_slot": rytm_slot,
        "analog_four_slot": analog_four_slot,
        "discovery_amount": discovery_amount,
        "include_events": include_events,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
    rytm_sysex_path: Path,
    analog_four_sysex_path: Path,
    style_key: str,
    rytm_slot: int,
    analog_four_slot: int,
    discovery_amount: int,
    include_events: bool,
    event_limit: int,
    json_output: bool,
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
        plan = build_dual_machine_style_mutation_mock_preview_report(
            rytm_snapshot,
            analog_four_snapshot,
            style_key=style_key,
            discovery_amount=discovery_amount,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_dual_machine_style_mutation_mock_preview_json(plan),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_dual_machine_style_mutation_mock_preview_report(
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


DUAL_MACHINE_STYLE_MUTATION_MOCK_PREVIEW_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="dual-machine-style-mutation-mock-preview-report",
    summary="Print passive dual-machine style mutation mock-preview rows for Rytm and A4.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(DUAL_MACHINE_STYLE_MUTATION_MOCK_PREVIEW_CLI_COMMAND)

__all__ = [
    "DUAL_MACHINE_STYLE_MUTATION_MOCK_PREVIEW_CLI_COMMAND",
    "DualMachineStyleMutationMockPreviewPlan",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_dual_machine_style_mutation_mock_preview_report",
    "format_dual_machine_style_mutation_mock_preview_report",
    "to_dual_machine_style_mutation_mock_preview_json",
]
