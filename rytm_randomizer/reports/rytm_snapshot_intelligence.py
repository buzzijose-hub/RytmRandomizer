"""Passive Analog Rytm snapshot intelligence report."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, register
from ..devices.strategies.analog_rytm_snapshot_decoder import (
    AnalogRytmSnapshotDecoder,
    RytmKitSnapshot,
)
from ..devices.strategies.analog_rytm_snapshot_routing import (
    RytmSnapshotMachineRoute,
    route_rytm_snapshot_machine_values,
)
from ..snapshot.sysex_file import read_sysex_payloads_from_path
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Rytm snapshot intelligence"
CATALOG_REPORT_TITLE: Final[str] = "RytmRandomizer passive Rytm snapshot file catalog"
SOURCE_MODULE: Final[str] = "reports.rytm_snapshot_intelligence"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
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
_CATALOG_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=CATALOG_REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_RYTM_PAD_COUNT: Final[int] = 12
_USAGE: Final[str] = "rytm-snapshot-intelligence-report usage: <syx-path> [--slot N|--list]"


@dataclass(frozen=True)
class RytmSnapshotIntelligencePadReport:
    """Passive decoded/routed machine fact for one 1-based Rytm pad."""

    pad: int
    raw_machine_value: int
    decoded_machine_value: int | None
    fact_promoted: bool
    fact_reason: str
    machine_key: str | None
    profile_key: str | None
    route_ready: bool
    route_reason: str


@dataclass(frozen=True)
class RytmSnapshotIntelligenceReport:
    """Passive snapshot intelligence summary for one Rytm kit snapshot."""

    kit_name: str
    slot: int
    pad_count: int
    promoted_fact_count: int
    candidate_fact_count: int
    route_ready_count: int
    route_blocked_count: int
    full_snapshot_mutation_ready: bool
    partial_snapshot_mutation_ready: bool
    readiness_reason: str
    pads_by_pad: Mapping[int, RytmSnapshotIntelligencePadReport]


def _candidate_pad_report(
    pad: int,
    raw_machine_value: int,
    decoded_machine_value: int | None,
    fact_promoted: bool,
    fact_reason: str,
) -> RytmSnapshotIntelligencePadReport:
    return RytmSnapshotIntelligencePadReport(
        pad=pad,
        raw_machine_value=raw_machine_value,
        decoded_machine_value=decoded_machine_value,
        fact_promoted=fact_promoted,
        fact_reason=fact_reason,
        machine_key=None,
        profile_key=None,
        route_ready=False,
        route_reason=fact_reason,
    )


def _routed_pad_report(
    pad: int,
    raw_machine_value: int,
    decoded_machine_value: int | None,
    fact_promoted: bool,
    fact_reason: str,
    route: RytmSnapshotMachineRoute | None,
) -> RytmSnapshotIntelligencePadReport:
    if route is None:
        return _candidate_pad_report(
            pad=pad,
            raw_machine_value=raw_machine_value,
            decoded_machine_value=decoded_machine_value,
            fact_promoted=fact_promoted,
            fact_reason=fact_reason,
        )
    return RytmSnapshotIntelligencePadReport(
        pad=pad,
        raw_machine_value=raw_machine_value,
        decoded_machine_value=decoded_machine_value,
        fact_promoted=fact_promoted,
        fact_reason=fact_reason,
        machine_key=route.machine_key,
        profile_key=route.profile_key,
        route_ready=route.ready,
        route_reason=route.reason,
    )


def _readiness_reason(
    candidate_fact_count: int,
    route_ready_count: int,
    route_readiness_reason: str,
) -> str:
    if candidate_fact_count:
        return "snapshot contains candidate-only machine facts; full snapshot mutation is blocked"
    if route_ready_count and not route_readiness_reason:
        return "snapshot machine facts route to mutable V1.34 profiles"
    if route_readiness_reason:
        return route_readiness_reason
    return "snapshot has no promoted machine facts"


def build_rytm_snapshot_intelligence_report(
    snapshot: RytmKitSnapshot,
) -> RytmSnapshotIntelligenceReport:
    """Return passive decoded/routed machine facts for ``snapshot``."""

    if not isinstance(snapshot, RytmKitSnapshot):
        raise ValueError(
            "build_rytm_snapshot_intelligence_report: snapshot must be a RytmKitSnapshot"
        )

    promoted_machine_values = {
        pad: fact.decoded_machine_value
        for pad, fact in snapshot.machine_facts.facts_by_pad.items()
        if fact.promoted and fact.decoded_machine_value is not None
    }
    routing = route_rytm_snapshot_machine_values(promoted_machine_values)

    pad_reports: dict[int, RytmSnapshotIntelligencePadReport] = {}
    promoted_fact_count = 0
    candidate_fact_count = 0
    for pad in range(1, _RYTM_PAD_COUNT + 1):
        fact = snapshot.machine_facts.facts_by_pad.get(pad)
        if fact is None:
            candidate_fact_count += 1
            pad_reports[pad] = _candidate_pad_report(
                pad=pad,
                raw_machine_value=-1,
                decoded_machine_value=None,
                fact_promoted=False,
                fact_reason="missing snapshot machine fact",
            )
            continue
        if fact.promoted:
            promoted_fact_count += 1
        else:
            candidate_fact_count += 1
        pad_reports[pad] = _routed_pad_report(
            pad=pad,
            raw_machine_value=fact.raw_machine_value,
            decoded_machine_value=fact.decoded_machine_value,
            fact_promoted=fact.promoted,
            fact_reason=fact.reason,
            route=routing.routes_by_pad.get(pad),
        )

    readiness_reason = _readiness_reason(
        candidate_fact_count,
        routing.ready_pad_count,
        routing.readiness_reason,
    )
    all_pads_promoted = promoted_fact_count == _RYTM_PAD_COUNT and candidate_fact_count == 0
    full_ready = snapshot.machine_facts.promoted and all_pads_promoted and routing.ready
    return RytmSnapshotIntelligenceReport(
        kit_name=snapshot.kit_name,
        slot=snapshot.slot,
        pad_count=_RYTM_PAD_COUNT,
        promoted_fact_count=promoted_fact_count,
        candidate_fact_count=candidate_fact_count,
        route_ready_count=routing.ready_pad_count,
        route_blocked_count=routing.blocked_pad_count,
        full_snapshot_mutation_ready=full_ready,
        partial_snapshot_mutation_ready=routing.ready_pad_count > 0,
        readiness_reason=readiness_reason,
        pads_by_pad=MappingProxyType(pad_reports),
    )


def _body_lines(report: RytmSnapshotIntelligenceReport) -> list[str]:
    lines = [
        f"Kit: {report.kit_name}",
        f"Slot: {report.slot}",
        "Summary:",
        f"- Pads: {report.pad_count}",
        f"- Promoted machine facts: {report.promoted_fact_count}",
        f"- Candidate-only machine facts: {report.candidate_fact_count}",
        f"- Routed mutable pads: {report.route_ready_count}",
        f"- Routed blocked pads: {report.route_blocked_count}",
        f"- Full snapshot mutation ready: {report.full_snapshot_mutation_ready}",
        f"- Partial snapshot mutation ready: {report.partial_snapshot_mutation_ready}",
        f"- Reason: {report.readiness_reason}",
        "Pads:",
    ]

    for pad in sorted(report.pads_by_pad):
        pad_report = report.pads_by_pad[pad]
        machine_key = pad_report.machine_key or "none"
        profile_key = pad_report.profile_key or "none"
        lines.extend(
            [
                (
                    f"Pad {pad}: raw={pad_report.raw_machine_value} "
                    f"decoded={pad_report.decoded_machine_value} "
                    f"route_ready={pad_report.route_ready}"
                ),
                f"  Fact promoted: {pad_report.fact_promoted}",
                f"  Machine key: {machine_key}",
                f"  Profile key: {profile_key}",
                f"  Fact reason: {pad_report.fact_reason}",
                f"  Route reason: {pad_report.route_reason}",
            ]
        )

    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_rytm_snapshot_intelligence_report(
    snapshot_or_report: RytmKitSnapshot | RytmSnapshotIntelligenceReport,
) -> list[str]:
    """Return deterministic operator-facing lines for snapshot intelligence."""

    report = (
        snapshot_or_report
        if isinstance(snapshot_or_report, RytmSnapshotIntelligenceReport)
        else build_rytm_snapshot_intelligence_report(snapshot_or_report)
    )
    return passive_report_lines(_HEADER, _body_lines(report))


def _catalog_body_lines(
    sysex_path: Path,
    snapshots: Sequence[RytmKitSnapshot],
) -> list[str]:
    lines = [
        f"File: {sysex_path}",
        f"Supported Rytm kit snapshots: {len(snapshots)}",
        "Slots:",
    ]
    lines.extend(f"Slot {snapshot.slot}: {snapshot.kit_name}" for snapshot in snapshots)
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_rytm_snapshot_file_catalog_report(
    sysex_path: Path,
    snapshots: Sequence[RytmKitSnapshot],
) -> list[str]:
    """Return deterministic operator-facing lines for supported kit snapshots."""

    return passive_report_lines(_CATALOG_HEADER, _catalog_body_lines(sysex_path, snapshots))


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if not argv:
        raise ValueError("rytm-snapshot-intelligence-report requires <syx-path>")
    if len(argv) not in (1, 2, 3):
        raise ValueError(_USAGE)
    sysex_path = Path(argv[0])
    slot = 0
    list_slots = False
    if len(argv) == 2:
        if argv[1] != "--list":
            raise ValueError(_USAGE)
        list_slots = True
    if len(argv) == 3:
        if argv[1] != "--slot":
            raise ValueError(_USAGE)
        try:
            slot = int(argv[2])
        except ValueError as exc:
            raise ValueError("--slot must be an integer") from exc
        if slot < 0:
            raise ValueError("--slot must be >= 0")
    return {"sysex_path": sysex_path, "slot": slot, "list_slots": list_slots}


def _decode_supported_snapshots(sysex_path: Path) -> tuple[RytmKitSnapshot, ...]:
    decoder = AnalogRytmSnapshotDecoder()
    errors: list[str] = []
    snapshots: list[RytmKitSnapshot] = []
    for index, payload in enumerate(read_sysex_payloads_from_path(sysex_path), start=1):
        try:
            snapshots.append(decoder.decode(payload, slot=len(snapshots)))
        except (NotImplementedError, ValueError) as exc:
            errors.append(f"frame {index}: {exc}")
    if snapshots:
        return tuple(snapshots)
    detail = "; ".join(errors) if errors else "no SysEx payloads found"
    raise ValueError(f"No supported Analog Rytm kit snapshot found in {sysex_path}: {detail}")


def _available_slot_lines(snapshots: Sequence[RytmKitSnapshot]) -> tuple[str, ...]:
    return tuple(f"Slot {snapshot.slot}: {snapshot.kit_name}" for snapshot in snapshots)


def _slot_out_of_range_message(
    sysex_path: Path,
    slot: int,
    snapshots: Sequence[RytmKitSnapshot],
) -> str:
    snapshot_noun = "snapshot" if len(snapshots) == 1 else "snapshots"
    available = "; ".join(_available_slot_lines(snapshots))
    return (
        f"Requested --slot {slot}, but only {len(snapshots)} supported Analog Rytm "
        f"kit {snapshot_noun} found in {sysex_path}. Available slots: {available}"
    )


def _select_supported_snapshot(
    sysex_path: Path,
    slot: int,
    snapshots: Sequence[RytmKitSnapshot],
) -> RytmKitSnapshot:
    if slot < len(snapshots):
        return snapshots[slot]
    raise ValueError(_slot_out_of_range_message(sysex_path, slot, snapshots))


def _handle_cli_report(*, sysex_path: Path, slot: int, list_slots: bool = False) -> int:
    try:
        snapshots = _decode_supported_snapshots(sysex_path)
        if list_slots:
            sys.stdout.write(
                "\n".join(format_rytm_snapshot_file_catalog_report(sysex_path, snapshots))
            )
            sys.stdout.write("\n")
            return 0
        snapshot = _select_supported_snapshot(sysex_path, slot, snapshots)
    except (OSError, ValueError, NotImplementedError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(format_rytm_snapshot_intelligence_report(snapshot)))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


RYTM_SNAPSHOT_INTELLIGENCE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="rytm-snapshot-intelligence-report",
    summary="Print passive Rytm snapshot intelligence for a SysEx file.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(RYTM_SNAPSHOT_INTELLIGENCE_CLI_COMMAND)


__all__ = [
    "CATALOG_REPORT_TITLE",
    "REPORT_TITLE",
    "RYTM_SNAPSHOT_INTELLIGENCE_CLI_COMMAND",
    "RytmSnapshotIntelligencePadReport",
    "RytmSnapshotIntelligenceReport",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_rytm_snapshot_intelligence_report",
    "format_rytm_snapshot_file_catalog_report",
    "format_rytm_snapshot_intelligence_report",
]
