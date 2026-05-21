"""Selection-driven passive dual-machine style mutation mock preview."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from ..cli_registry import CliCommand, register
from ..data.style_discovery import (
    DEFAULT_STYLE_DISCOVERY_AMOUNT,
    style_discovery_policy,
)
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
from .dual_machine_style_kit_selection import (
    DualMachineStyleKitSelectionEntry,
    build_dual_machine_style_kit_selection_report,
    normalize_selection_scope,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines
from .rytm_snapshot_intelligence import (
    decode_supported_rytm_snapshots_from_path,
    select_supported_rytm_snapshot,
)
from .rytm_style_mutation_mock_preview import to_rytm_style_mutation_mock_preview_json

REPORT_TITLE: Final[str] = "RytmRandomizer passive dual-machine style selection mock preview"
SOURCE_MODULE: Final[str] = "reports.dual_machine_style_selection_mock_preview"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "selection-driven mock preview",
    "single-machine scope leaves the other machine unchanged",
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
    "dual-machine-style-selection-mock-preview-report usage: "
    "<style-key> --rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--discovery N] [--events] [--limit N] [--json]"
)
_DEFAULT_SELECTION_RANK: Final[int] = 1
_DEFAULT_EVENT_LIMIT: Final[int] = 24


@dataclass(frozen=True)
class DualMachineStyleSelectionMockPreviewPlan:
    """Passive mock-preview plan built from a ranked style kit selection."""

    style_key: str
    scope: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    selection_rank: int
    selection_readiness: str
    selection_score: int
    operator_action: str
    total_event_row_count: int
    total_mock_message_count: int
    total_deferred_row_count: int
    selection: DualMachineStyleKitSelectionEntry
    rytm_preview: RytmStyleMutationMockPreview | None
    analog_four_preview: AnalogFourStyleMutationMockPreview | None


def _selected_entry(
    entries: Sequence[DualMachineStyleKitSelectionEntry],
    *,
    selection_rank: int,
) -> DualMachineStyleKitSelectionEntry:
    if selection_rank < 1:
        raise ValueError("selection_rank must be >= 1")
    if not entries:
        raise ValueError("selection has no candidates")
    if selection_rank > len(entries):
        raise ValueError(f"selection_rank must be between 1 and {len(entries)}")
    return entries[selection_rank - 1]


def _build_rytm_preview(
    *,
    sysex_path: Path | None,
    selection: DualMachineStyleKitSelectionEntry,
    style_key: str,
    discovery_amount: int,
) -> RytmStyleMutationMockPreview | None:
    if selection.rytm_choice is None:
        return None
    path = cast(Path, sysex_path)
    snapshots = decode_supported_rytm_snapshots_from_path(path)
    snapshot = select_supported_rytm_snapshot(
        path,
        selection.rytm_choice.slot,
        snapshots,
    )
    return build_rytm_style_mutation_mock_preview(
        snapshot,
        style_key,
        discovery_amount=discovery_amount,
    )


def _build_analog_four_preview(
    *,
    sysex_path: Path | None,
    selection: DualMachineStyleKitSelectionEntry,
    style_key: str,
    discovery_amount: int,
) -> AnalogFourStyleMutationMockPreview | None:
    if selection.analog_four_choice is None:
        return None
    path = cast(Path, sysex_path)
    snapshots = decode_supported_analog_four_snapshots_from_path(path)
    snapshot = select_supported_analog_four_snapshot(
        path,
        selection.analog_four_choice.slot,
        snapshots,
    )
    return build_analog_four_style_mutation_mock_preview(
        snapshot,
        style_key,
        discovery_amount=discovery_amount,
    )


def build_dual_machine_style_selection_mock_preview_report(
    style_key: str,
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int = _DEFAULT_SELECTION_RANK,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> DualMachineStyleSelectionMockPreviewPlan:
    """Return a passive style mock-preview plan from the ranked kit selection."""

    policy = style_discovery_policy(discovery_amount)
    selection_report = build_dual_machine_style_kit_selection_report(
        style_key,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        scope=scope,
        discovery_amount=policy.amount,
    )
    selection = _selected_entry(selection_report.entries, selection_rank=selection_rank)
    rytm_preview = _build_rytm_preview(
        sysex_path=rytm_sysex_path,
        selection=selection,
        style_key=style_key,
        discovery_amount=policy.amount,
    )
    analog_four_preview = _build_analog_four_preview(
        sysex_path=analog_four_sysex_path,
        selection=selection,
        style_key=style_key,
        discovery_amount=policy.amount,
    )
    total_event_row_count = (0 if rytm_preview is None else rytm_preview.render_event_count) + (
        0 if analog_four_preview is None else len(analog_four_preview.event_rows)
    )
    total_mock_message_count = (0 if rytm_preview is None else rytm_preview.mock_message_count) + (
        0 if analog_four_preview is None else analog_four_preview.mock_message_count
    )
    total_deferred_row_count = (
        0 if analog_four_preview is None else analog_four_preview.deferred_row_count
    )
    return DualMachineStyleSelectionMockPreviewPlan(
        style_key=style_key,
        scope=selection_report.scope,
        discovery_amount=policy.amount,
        discovery_band=policy.band,
        mutation_depth=policy.mutation_depth,
        selection_rank=selection_rank,
        selection_readiness=selection.selection_readiness,
        selection_score=selection.score,
        operator_action=selection.operator_action,
        total_event_row_count=total_event_row_count,
        total_mock_message_count=total_mock_message_count,
        total_deferred_row_count=total_deferred_row_count,
        selection=selection,
        rytm_preview=rytm_preview,
        analog_four_preview=analog_four_preview,
    )


def _planned_numbers_text(planned_numbers: Sequence[int]) -> str:
    if not planned_numbers:
        return "none"
    return ", ".join(str(number) for number in planned_numbers)


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


def _event_rows(plan: DualMachineStyleSelectionMockPreviewPlan) -> tuple[str, ...]:
    rytm_rows = (
        ()
        if plan.rytm_preview is None
        else tuple(_format_rytm_event_row(row) for row in plan.rytm_preview.event_rows)
    )
    analog_four_rows = (
        ()
        if plan.analog_four_preview is None
        else tuple(
            _format_analog_four_event_row(row) for row in plan.analog_four_preview.event_rows
        )
    )
    return rytm_rows + analog_four_rows


def _event_preview_lines(
    plan: DualMachineStyleSelectionMockPreviewPlan,
    *,
    event_limit: int,
) -> list[str]:
    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")

    rows = _event_rows(plan)
    lines = ["Event preview:"]
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


def _deferred_preview_lines(
    analog_four_preview: AnalogFourStyleMutationMockPreview | None,
) -> list[str]:
    lines = ["Deferred rows:"]
    if analog_four_preview is None or not analog_four_preview.deferred_rows:
        lines.append("- none")
        return lines
    lines.extend(_format_analog_four_deferred_row(row) for row in analog_four_preview.deferred_rows)
    return lines


def _rytm_lines(preview: RytmStyleMutationMockPreview | None) -> list[str]:
    lines = ["Rytm:"]
    if preview is None:
        lines.append("- unchanged by scope")
        return lines
    lines.extend(
        [
            f"- Kit: {preview.kit_name}",
            f"- Slot: {preview.slot}",
            f"- Preview ready: {preview.preview_ready}",
            f"- Readiness reason: {preview.readiness_reason}",
            f"- Ready pads: {preview.ready_pad_count}",
            f"- Blocked pads: {preview.blocked_pad_count}",
            f"- Render events: {preview.render_event_count}",
            f"- Mock messages: {preview.mock_message_count}",
            f"- Planned pads: {_planned_numbers_text(preview.planned_pads)}",
        ]
    )
    return lines


def _analog_four_lines(preview: AnalogFourStyleMutationMockPreview | None) -> list[str]:
    lines = ["Analog Four:"]
    if preview is None:
        lines.append("- unchanged by scope")
        return lines
    lines.extend(
        [
            f"- Kit: {preview.kit_name}",
            f"- Slot: {preview.slot}",
            f"- Preview ready: {preview.preview_ready}",
            f"- Readiness reason: {preview.readiness_reason}",
            f"- Ready tracks: {preview.ready_track_count}",
            f"- Blocked tracks: {preview.blocked_track_count}",
            f"- Intent rows: {preview.intent_row_count}",
            f"- Mock messages: {preview.mock_message_count}",
            f"- Deferred rows: {preview.deferred_row_count}",
            f"- Planned tracks: {_planned_numbers_text(preview.planned_tracks)}",
        ]
    )
    return lines


def _body_lines(
    plan: DualMachineStyleSelectionMockPreviewPlan,
    *,
    include_events: bool,
    event_limit: int,
) -> list[str]:
    lines = [
        f"Scope: {plan.scope}",
        f"Style target: {plan.style_key}",
        f"Discovery amount: {plan.discovery_amount}",
        f"Discovery band: {plan.discovery_band}",
        f"Mutation depth: {plan.mutation_depth}",
        f"Selection rank: {plan.selection_rank}",
        f"Selection readiness: {plan.selection_readiness}",
        f"Selection score: {plan.selection_score}",
        f"Operator action: {plan.operator_action}",
        f"Total event rows: {plan.total_event_row_count}",
        f"Total mock messages: {plan.total_mock_message_count}",
        f"Total deferred rows: {plan.total_deferred_row_count}",
    ]
    lines.extend(_rytm_lines(plan.rytm_preview))
    lines.extend(_analog_four_lines(plan.analog_four_preview))
    if include_events:
        lines.extend(_event_preview_lines(plan, event_limit=event_limit))
    lines.extend(_deferred_preview_lines(plan.analog_four_preview))
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_dual_machine_style_selection_mock_preview_report(
    plan: DualMachineStyleSelectionMockPreviewPlan,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    """Return deterministic operator-facing selection-driven mock-preview lines."""

    return passive_report_lines(
        _HEADER,
        _body_lines(plan, include_events=include_events, event_limit=event_limit),
    )


def _selection_json(
    plan: DualMachineStyleSelectionMockPreviewPlan,
) -> dict[str, object]:
    return {
        "rank": plan.selection_rank,
        "readiness": plan.selection_readiness,
        "score": plan.selection_score,
        "operator_action": plan.operator_action,
    }


def to_dual_machine_style_selection_mock_preview_json(
    plan: DualMachineStyleSelectionMockPreviewPlan,
) -> dict[str, object]:
    """Return deterministic machine-readable selection-driven preview metadata."""

    return {
        "style_key": plan.style_key,
        "scope": plan.scope,
        "discovery_amount": plan.discovery_amount,
        "discovery_band": plan.discovery_band,
        "mutation_depth": plan.mutation_depth,
        "selection": _selection_json(plan),
        "total_event_row_count": plan.total_event_row_count,
        "total_mock_message_count": plan.total_mock_message_count,
        "total_deferred_row_count": plan.total_deferred_row_count,
        "machines": {
            "analog_four": (
                None
                if plan.analog_four_preview is None
                else to_analog_four_style_mutation_mock_preview_json(plan.analog_four_preview)
            ),
            "rytm": (
                None
                if plan.rytm_preview is None
                else to_rytm_style_mutation_mock_preview_json(plan.rytm_preview)
            ),
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
    raise ValueError("selection preview requires at least one of --rytm or --analog-four")


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if not argv:
        raise ValueError(_USAGE)
    style_key = argv[0]
    if style_key.startswith("--"):
        raise ValueError(_USAGE)
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank = _DEFAULT_SELECTION_RANK
    discovery_amount = DEFAULT_STYLE_DISCOVERY_AMOUNT
    include_events = False
    event_limit = _DEFAULT_EVENT_LIMIT
    json_output = False
    remaining = list(argv[1:])
    while remaining:
        option = remaining.pop(0)
        if option == "--events":
            include_events = True
            continue
        if option == "--json":
            json_output = True
            continue
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
        elif option == "--limit":
            event_limit = _parse_nonnegative_int(value, option=option)
        else:
            raise ValueError(_USAGE)
    normalized_scope = (
        _auto_scope(rytm_sysex_path, analog_four_sysex_path) if scope is None else scope
    )
    return {
        "style_key": style_key,
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
    style_key: str,
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
        plan = build_dual_machine_style_selection_mock_preview_report(
            style_key,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            discovery_amount=discovery_amount,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_dual_machine_style_selection_mock_preview_json(plan),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_dual_machine_style_selection_mock_preview_report(
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


DUAL_MACHINE_STYLE_SELECTION_MOCK_PREVIEW_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="dual-machine-style-selection-mock-preview-report",
    summary="Print passive style mock previews from the best saved-kit selection.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(DUAL_MACHINE_STYLE_SELECTION_MOCK_PREVIEW_CLI_COMMAND)

__all__ = [
    "DUAL_MACHINE_STYLE_SELECTION_MOCK_PREVIEW_CLI_COMMAND",
    "DualMachineStyleSelectionMockPreviewPlan",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_dual_machine_style_selection_mock_preview_report",
    "format_dual_machine_style_selection_mock_preview_report",
    "to_dual_machine_style_selection_mock_preview_json",
]
