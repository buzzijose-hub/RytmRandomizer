"""Passive dual-machine style kit-selection report."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

from ..cli_registry import CliCommand, register
from ..data.style_discovery import (
    DEFAULT_STYLE_DISCOVERY_AMOUNT,
    style_discovery_policy,
)
from .analog_four_style_kit_readiness import (
    AnalogFourStyleKitReadinessEntry,
    build_analog_four_style_kit_readiness_report,
)
from .dual_machine_style_kit_readiness import (
    DualMachineStyleKitReadinessEntry,
    build_dual_machine_style_kit_readiness_report,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines
from .rytm_style_kit_readiness import (
    RytmStyleKitReadinessEntry,
    build_rytm_style_kit_readiness_report,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive dual-machine style kit selection"
SOURCE_MODULE: Final[str] = "reports.dual_machine_style_kit_selection"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "operator selection only",
    "style/mock readiness inputs only",
    "single-machine scope leaves the other machine unchanged",
    "candidate-only A4 offsets still block decoded SysEx mock rows",
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
    "dual-machine-style-kit-selection-report usage: "
    "<style-key> --rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--discovery N] [--limit N] [--json]"
)
_SCOPE_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "dual": "dual",
        "rytm-only": "rytm-only",
        "analog-four-only": "analog-four-only",
        "a4-only": "analog-four-only",
    }
)
_READINESS_RANK: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ready": 3,
        "partial": 2,
        "blocked": 1,
    }
)


@dataclass(frozen=True)
class StyleKitSelectionMachineChoice:
    """One selected machine snapshot for an operator-facing style kit choice."""

    device: str
    slot: int
    kit_name: str
    preview_ready: bool
    ready_unit_count: int
    blocked_unit_count: int
    mock_message_count: int
    deferred_row_count: int
    payload_fingerprint: str
    readiness_reason: str


@dataclass(frozen=True)
class DualMachineStyleKitSelectionEntry:
    """One ranked operator selection for dual or single-machine style use."""

    scope: str
    selection_readiness: str
    score: int
    operator_action: str
    rytm_choice: StyleKitSelectionMachineChoice | None
    analog_four_choice: StyleKitSelectionMachineChoice | None


@dataclass(frozen=True)
class DualMachineStyleKitSelectionReport:
    """Passive operator-facing style kit-selection summary."""

    style_key: str
    discovery_amount: int
    scope: str
    rytm_sysex_path: Path | None
    analog_four_sysex_path: Path | None
    candidate_count: int
    ready_selection_count: int
    partial_selection_count: int
    blocked_selection_count: int
    entries: tuple[DualMachineStyleKitSelectionEntry, ...]


def normalize_selection_scope(scope: str) -> str:
    """Return the canonical selection scope or raise for an unsupported value."""

    normalized = scope.strip().lower()
    canonical = _SCOPE_ALIASES.get(normalized)
    if canonical is None:
        raise ValueError("unsupported scope; use dual, rytm-only, analog-four-only, or a4-only")
    return canonical


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
    raise ValueError("selection requires at least one of --rytm or --analog-four")


def _validate_scope_paths(
    *,
    scope: str,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
) -> None:
    if scope == "dual":
        if rytm_sysex_path is None:
            raise ValueError("dual scope requires --rytm")
        if analog_four_sysex_path is None:
            raise ValueError("dual scope requires --analog-four")
    elif scope == "rytm-only":
        if rytm_sysex_path is None:
            raise ValueError("rytm-only scope requires --rytm")
    elif scope == "analog-four-only" and analog_four_sysex_path is None:
        raise ValueError("analog-four-only scope requires --analog-four")


def _choice_from_rytm_entry(
    entry: RytmStyleKitReadinessEntry,
) -> StyleKitSelectionMachineChoice:
    return StyleKitSelectionMachineChoice(
        device="rytm",
        slot=entry.slot,
        kit_name=entry.kit_name,
        preview_ready=entry.preview_ready,
        ready_unit_count=entry.ready_pad_count,
        blocked_unit_count=entry.blocked_pad_count,
        mock_message_count=entry.mock_message_count,
        deferred_row_count=0,
        payload_fingerprint=entry.payload_fingerprint,
        readiness_reason=entry.readiness_reason,
    )


def _choice_from_analog_four_entry(
    entry: AnalogFourStyleKitReadinessEntry,
) -> StyleKitSelectionMachineChoice:
    return StyleKitSelectionMachineChoice(
        device="analog-four",
        slot=entry.slot,
        kit_name=entry.kit_name,
        preview_ready=entry.preview_ready,
        ready_unit_count=entry.ready_track_count,
        blocked_unit_count=entry.blocked_track_count,
        mock_message_count=entry.mock_message_count,
        deferred_row_count=entry.deferred_row_count,
        payload_fingerprint=entry.payload_fingerprint,
        readiness_reason=entry.readiness_reason,
    )


def _choice_from_dual_rytm_entry(
    entry: DualMachineStyleKitReadinessEntry,
) -> StyleKitSelectionMachineChoice:
    return StyleKitSelectionMachineChoice(
        device="rytm",
        slot=entry.rytm_slot,
        kit_name=entry.rytm_kit_name,
        preview_ready=entry.rytm_preview_ready,
        ready_unit_count=entry.rytm_ready_pad_count,
        blocked_unit_count=entry.rytm_blocked_pad_count,
        mock_message_count=entry.rytm_mock_message_count,
        deferred_row_count=0,
        payload_fingerprint=entry.rytm_payload_fingerprint,
        readiness_reason=entry.rytm_readiness_reason,
    )


def _choice_from_dual_analog_four_entry(
    entry: DualMachineStyleKitReadinessEntry,
) -> StyleKitSelectionMachineChoice:
    return StyleKitSelectionMachineChoice(
        device="analog-four",
        slot=entry.analog_four_slot,
        kit_name=entry.analog_four_kit_name,
        preview_ready=entry.analog_four_preview_ready,
        ready_unit_count=entry.analog_four_ready_track_count,
        blocked_unit_count=entry.analog_four_blocked_track_count,
        mock_message_count=entry.analog_four_mock_message_count,
        deferred_row_count=entry.analog_four_deferred_row_count,
        payload_fingerprint=entry.analog_four_payload_fingerprint,
        readiness_reason=entry.analog_four_readiness_reason,
    )


def _single_readiness(choice: StyleKitSelectionMachineChoice) -> str:
    if choice.preview_ready:
        return "ready"
    return "blocked"


def _single_score(choice: StyleKitSelectionMachineChoice) -> int:
    readiness = _single_readiness(choice)
    return (
        _READINESS_RANK[readiness] * 1000
        + choice.ready_unit_count * 20
        + choice.mock_message_count
        - choice.deferred_row_count
    )


def _single_sort_key(entry: DualMachineStyleKitSelectionEntry) -> tuple[int, int, int]:
    choice = entry.rytm_choice or entry.analog_four_choice
    slot = 999 if choice is None else choice.slot
    return (-_READINESS_RANK[entry.selection_readiness], -entry.score, slot)


def _selection_sort_key(
    entry: DualMachineStyleKitSelectionEntry,
) -> tuple[int, int, int, int]:
    rytm_slot = 999 if entry.rytm_choice is None else entry.rytm_choice.slot
    analog_four_slot = 999 if entry.analog_four_choice is None else entry.analog_four_choice.slot
    return (
        -_READINESS_RANK[entry.selection_readiness],
        -entry.score,
        rytm_slot,
        analog_four_slot,
    )


def _dual_operator_action(
    rytm_choice: StyleKitSelectionMachineChoice,
    analog_four_choice: StyleKitSelectionMachineChoice,
) -> str:
    if rytm_choice.preview_ready and analog_four_choice.preview_ready:
        return "Select both snapshots; both machines are preview-ready."
    if rytm_choice.preview_ready:
        return (
            "Use the Rytm snapshot now; leave or hand-tweak Analog Four "
            "until A4 offsets are promoted."
        )
    if analog_four_choice.preview_ready:
        return (
            "Use the Analog Four snapshot now; leave or hand-tweak Rytm "
            "until Rytm readiness is available."
        )
    return "Do not automate this pair yet; both machine snapshots are blocked."


def _entry_from_dual_readiness(
    entry: DualMachineStyleKitReadinessEntry,
) -> DualMachineStyleKitSelectionEntry:
    rytm_choice = _choice_from_dual_rytm_entry(entry)
    analog_four_choice = _choice_from_dual_analog_four_entry(entry)
    return DualMachineStyleKitSelectionEntry(
        scope="dual",
        selection_readiness=entry.rig_readiness,
        score=entry.score,
        operator_action=_dual_operator_action(rytm_choice, analog_four_choice),
        rytm_choice=rytm_choice,
        analog_four_choice=analog_four_choice,
    )


def _entry_from_rytm_choice(
    choice: StyleKitSelectionMachineChoice,
) -> DualMachineStyleKitSelectionEntry:
    readiness = _single_readiness(choice)
    if choice.preview_ready:
        action = "Select this Rytm snapshot; mutate Rytm only and leave Analog Four unchanged."
    else:
        action = "Do not automate this Rytm snapshot yet; leave Analog Four unchanged."
    return DualMachineStyleKitSelectionEntry(
        scope="rytm-only",
        selection_readiness=readiness,
        score=_single_score(choice),
        operator_action=action,
        rytm_choice=choice,
        analog_four_choice=None,
    )


def _entry_from_analog_four_choice(
    choice: StyleKitSelectionMachineChoice,
) -> DualMachineStyleKitSelectionEntry:
    readiness = _single_readiness(choice)
    if choice.preview_ready:
        action = "Select this Analog Four snapshot; mutate A4 only and leave Rytm unchanged."
    else:
        action = "Do not automate this Analog Four snapshot yet; leave Rytm unchanged."
    return DualMachineStyleKitSelectionEntry(
        scope="analog-four-only",
        selection_readiness=readiness,
        score=_single_score(choice),
        operator_action=action,
        rytm_choice=None,
        analog_four_choice=choice,
    )


def _build_dual_entries(
    *,
    rytm_sysex_path: Path,
    analog_four_sysex_path: Path,
    style_key: str,
    discovery_amount: int,
) -> tuple[DualMachineStyleKitSelectionEntry, ...]:
    readiness_report = build_dual_machine_style_kit_readiness_report(
        rytm_sysex_path,
        analog_four_sysex_path,
        style_key,
        discovery_amount=discovery_amount,
    )
    return tuple(
        sorted(
            (_entry_from_dual_readiness(entry) for entry in readiness_report.entries),
            key=_selection_sort_key,
        )
    )


def _build_rytm_entries(
    *,
    rytm_sysex_path: Path,
    style_key: str,
    discovery_amount: int,
) -> tuple[DualMachineStyleKitSelectionEntry, ...]:
    readiness_report = build_rytm_style_kit_readiness_report(
        rytm_sysex_path,
        style_key,
        discovery_amount=discovery_amount,
    )
    return tuple(
        sorted(
            (
                _entry_from_rytm_choice(_choice_from_rytm_entry(entry))
                for entry in readiness_report.entries
            ),
            key=_single_sort_key,
        )
    )


def _build_analog_four_entries(
    *,
    analog_four_sysex_path: Path,
    style_key: str,
    discovery_amount: int,
) -> tuple[DualMachineStyleKitSelectionEntry, ...]:
    readiness_report = build_analog_four_style_kit_readiness_report(
        analog_four_sysex_path,
        style_key,
        discovery_amount=discovery_amount,
    )
    return tuple(
        sorted(
            (
                _entry_from_analog_four_choice(_choice_from_analog_four_entry(entry))
                for entry in readiness_report.entries
            ),
            key=_single_sort_key,
        )
    )


def build_dual_machine_style_kit_selection_report(
    style_key: str,
    *,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> DualMachineStyleKitSelectionReport:
    """Return passive ranked style kit selections for one or both machines."""

    style_discovery_policy(discovery_amount)
    normalized_scope = (
        _auto_scope(rytm_sysex_path, analog_four_sysex_path)
        if scope is None
        else normalize_selection_scope(scope)
    )
    _validate_scope_paths(
        scope=normalized_scope,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
    )
    if normalized_scope == "dual":
        rytm_path = cast(Path, rytm_sysex_path)
        analog_four_path = cast(Path, analog_four_sysex_path)
        entries = _build_dual_entries(
            rytm_sysex_path=rytm_path,
            analog_four_sysex_path=analog_four_path,
            style_key=style_key,
            discovery_amount=discovery_amount,
        )
    elif normalized_scope == "rytm-only":
        rytm_path = cast(Path, rytm_sysex_path)
        entries = _build_rytm_entries(
            rytm_sysex_path=rytm_path,
            style_key=style_key,
            discovery_amount=discovery_amount,
        )
    else:
        analog_four_path = cast(Path, analog_four_sysex_path)
        entries = _build_analog_four_entries(
            analog_four_sysex_path=analog_four_path,
            style_key=style_key,
            discovery_amount=discovery_amount,
        )
    ready_selection_count = sum(1 for entry in entries if entry.selection_readiness == "ready")
    partial_selection_count = sum(1 for entry in entries if entry.selection_readiness == "partial")
    blocked_selection_count = sum(1 for entry in entries if entry.selection_readiness == "blocked")
    return DualMachineStyleKitSelectionReport(
        style_key=style_key,
        discovery_amount=discovery_amount,
        scope=normalized_scope,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        candidate_count=len(entries),
        ready_selection_count=ready_selection_count,
        partial_selection_count=partial_selection_count,
        blocked_selection_count=blocked_selection_count,
        entries=entries,
    )


def _visible_entries(
    entries: Sequence[DualMachineStyleKitSelectionEntry],
    *,
    display_limit: int | None,
) -> tuple[DualMachineStyleKitSelectionEntry, ...]:
    if display_limit is None or display_limit == 0:
        return tuple(entries)
    if display_limit < 0:
        raise ValueError("display_limit must be >= 0")
    return tuple(entries[:display_limit])


def _choice_line(label: str, choice: StyleKitSelectionMachineChoice | None) -> str:
    if choice is None:
        return f"{label} unchanged"
    return (
        f"{label} slot {choice.slot} {choice.kit_name} ready {choice.preview_ready} "
        f"/ units {choice.ready_unit_count} ready, {choice.blocked_unit_count} blocked "
        f"/ mock rows {choice.mock_message_count} / deferred rows {choice.deferred_row_count} "
        f"/ fingerprint {choice.payload_fingerprint}"
    )


def _fingerprints(entry: DualMachineStyleKitSelectionEntry) -> str:
    values: list[str] = []
    if entry.rytm_choice is not None:
        values.append(entry.rytm_choice.payload_fingerprint)
    if entry.analog_four_choice is not None:
        values.append(entry.analog_four_choice.payload_fingerprint)
    if not values:
        return "none"
    return "/".join(values)


def _entry_line(entry: DualMachineStyleKitSelectionEntry) -> str:
    return (
        f"- Scope {entry.scope} | readiness {entry.selection_readiness} | "
        f"score {entry.score} | action {entry.operator_action} | "
        f"{_choice_line('Rytm', entry.rytm_choice)} | "
        f"{_choice_line('A4', entry.analog_four_choice)} | "
        f"fingerprints {_fingerprints(entry)}"
    )


def _body_lines(
    report: DualMachineStyleKitSelectionReport,
    *,
    display_limit: int | None,
) -> list[str]:
    visible_entries = _visible_entries(report.entries, display_limit=display_limit)
    truncated_count = len(report.entries) - len(visible_entries)
    lines = [
        f"Scope: {report.scope}",
        f"Style target: {report.style_key}",
        f"Discovery amount: {report.discovery_amount}",
        f"Rytm path: {report.rytm_sysex_path if report.rytm_sysex_path is not None else 'not used'}",
        (
            "Analog Four path: "
            f"{report.analog_four_sysex_path if report.analog_four_sysex_path is not None else 'not used'}"
        ),
        f"Candidates: {report.candidate_count}",
        f"Ready selections: {report.ready_selection_count}",
        f"Partial selections: {report.partial_selection_count}",
        f"Blocked selections: {report.blocked_selection_count}",
        f"Shown selections: {len(visible_entries)}",
        f"Truncated selections: {truncated_count}",
        "Recommended selections:",
    ]
    if visible_entries:
        lines.extend(_entry_line(entry) for entry in visible_entries)
    else:
        lines.append("- none")
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_dual_machine_style_kit_selection_report(
    report: DualMachineStyleKitSelectionReport,
    *,
    display_limit: int | None = None,
) -> list[str]:
    """Return deterministic operator-facing dual-machine kit-selection lines."""

    return passive_report_lines(
        _HEADER,
        _body_lines(report, display_limit=display_limit),
    )


def _choice_json(choice: StyleKitSelectionMachineChoice | None) -> dict[str, object] | None:
    if choice is None:
        return None
    return {
        "device": choice.device,
        "slot": choice.slot,
        "kit_name": choice.kit_name,
        "preview_ready": choice.preview_ready,
        "ready_unit_count": choice.ready_unit_count,
        "blocked_unit_count": choice.blocked_unit_count,
        "mock_message_count": choice.mock_message_count,
        "deferred_row_count": choice.deferred_row_count,
        "payload_fingerprint": choice.payload_fingerprint,
        "readiness_reason": choice.readiness_reason,
    }


def _entry_json(entry: DualMachineStyleKitSelectionEntry) -> dict[str, object]:
    return {
        "scope": entry.scope,
        "selection_readiness": entry.selection_readiness,
        "score": entry.score,
        "operator_action": entry.operator_action,
        "rytm": _choice_json(entry.rytm_choice),
        "analog_four": _choice_json(entry.analog_four_choice),
    }


def to_dual_machine_style_kit_selection_json(
    report: DualMachineStyleKitSelectionReport,
    *,
    display_limit: int | None = None,
) -> dict[str, object]:
    """Return deterministic machine-readable dual-machine selection metadata."""

    visible_entries = _visible_entries(report.entries, display_limit=display_limit)
    return {
        "style_key": report.style_key,
        "discovery_amount": report.discovery_amount,
        "scope": report.scope,
        "rytm_sysex_path": (
            None if report.rytm_sysex_path is None else str(report.rytm_sysex_path)
        ),
        "analog_four_sysex_path": (
            None if report.analog_four_sysex_path is None else str(report.analog_four_sysex_path)
        ),
        "candidate_count": report.candidate_count,
        "ready_selection_count": report.ready_selection_count,
        "partial_selection_count": report.partial_selection_count,
        "blocked_selection_count": report.blocked_selection_count,
        "shown_count": len(visible_entries),
        "truncated_count": len(report.entries) - len(visible_entries),
        "entries": [_entry_json(entry) for entry in visible_entries],
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


def _pop_option_value(remaining: list[str], *, option: str) -> str:
    if not remaining:
        raise ValueError(_USAGE)
    return remaining.pop(0)


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if not argv:
        raise ValueError(_USAGE)
    style_key = argv[0]
    if style_key.startswith("--"):
        raise ValueError(_USAGE)
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    discovery_amount = DEFAULT_STYLE_DISCOVERY_AMOUNT
    display_limit: int | None = None
    json_output = False
    remaining = list(argv[1:])
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
            continue
        value = _pop_option_value(remaining, option=option)
        if option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--discovery":
            discovery_amount = _parse_discovery_amount(value, option=option)
        elif option == "--limit":
            display_limit = _parse_nonnegative_int(value, option=option)
        else:
            raise ValueError(_USAGE)
    normalized_scope = (
        _auto_scope(rytm_sysex_path, analog_four_sysex_path) if scope is None else scope
    )
    _validate_scope_paths(
        scope=normalized_scope,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
    )
    return {
        "style_key": style_key,
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": normalized_scope,
        "discovery_amount": discovery_amount,
        "display_limit": display_limit,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
    style_key: str,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str,
    discovery_amount: int,
    display_limit: int | None,
    json_output: bool,
) -> int:
    try:
        report = build_dual_machine_style_kit_selection_report(
            style_key,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            discovery_amount=discovery_amount,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_dual_machine_style_kit_selection_json(
                        report,
                        display_limit=display_limit,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_dual_machine_style_kit_selection_report(
            report,
            display_limit=display_limit,
        )
    except (OSError, ValueError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


DUAL_MACHINE_STYLE_KIT_SELECTION_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="dual-machine-style-kit-selection-report",
    summary="Print passive style kit selections for Rytm, A4, or both machines.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(DUAL_MACHINE_STYLE_KIT_SELECTION_CLI_COMMAND)

__all__ = [
    "DUAL_MACHINE_STYLE_KIT_SELECTION_CLI_COMMAND",
    "DualMachineStyleKitSelectionEntry",
    "DualMachineStyleKitSelectionReport",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "StyleKitSelectionMachineChoice",
    "build_dual_machine_style_kit_selection_report",
    "format_dual_machine_style_kit_selection_report",
    "normalize_selection_scope",
    "to_dual_machine_style_kit_selection_json",
]
