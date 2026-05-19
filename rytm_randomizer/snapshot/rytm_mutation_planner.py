"""Passive mutation planning from decoded Rytm kit snapshots.

This module plans relative CC moves from saved kit values only. It does not
import MIDI libraries, open ports, send messages, request SysEx, receive live
SysEx, write SysEx, load anchors, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..observability.errors import DataError
from .rytm_decoder import (
    RytmKitSnapshot,
    RytmSnapshotPad,
    RytmSnapshotParameter,
    decode_rytm_kit_snapshot_file,
    format_rytm_kit_snapshot_error,
)

DEPTH_DELTAS = {
    "micro": {"pitch": 1, "default": 3, "lfo": 5},
    "groove": {"pitch": 3, "default": 8, "lfo": 12},
    "strong": {"pitch": 5, "default": 14, "lfo": 20},
}

MUTATION_PARAMETER_PRIORITY = (
    "SRC Tune",
    "SRC Slot 2",
    "SRC Decay",
    "SRC Slot 3",
    "FLT Frequency",
    "FLT Resonance",
    "FLT Env Depth",
    "AMP Decay",
    "AMP Overdrive",
    "LFO Speed",
    "LFO Depth",
)

MAX_CHANGES_PER_PAD = 6
PAD_COUNT = 12
READINESS_COUNT_KEYS = (
    "ready",
    "machine_disabled",
    "unknown_machine",
    "incompatible_with_pad",
    "no_mutable_legal_pads",
)


class SnapshotMutationPlanError(DataError, ValueError):
    """Raised when a passive snapshot mutation plan cannot be built."""


@dataclass(frozen=True)
class SnapshotPlannedChange:
    """One relative CC change proposed from a captured snapshot value."""

    pad: int
    midi_channel: int
    machine_label: str
    parameter_name: str
    cc: int
    baseline_value: int
    planned_value: int
    delta: int
    source: str


@dataclass(frozen=True)
class SnapshotPadMutationPlan:
    """Passive mutation plan for one captured Rytm pad."""

    pad: int
    midi_channel: int
    sound_name: str
    machine_label: str
    machine_value: int
    machine_compatibility_status: str
    baseline_status: str
    plan_status: str
    changes: tuple[SnapshotPlannedChange, ...]


@dataclass(frozen=True)
class SnapshotMutationPlan:
    """Passive 12-pad mutation plan derived from one decoded kit snapshot."""

    slot_number: int
    kit_name: str
    depth: str
    snapshot_parameter_map_status: str
    pads: tuple[SnapshotPadMutationPlan, ...]

    @property
    def planned_pad_count(self) -> int:
        return sum(1 for pad in self.pads if pad.changes)

    @property
    def blocked_pad_count(self) -> int:
        return sum(1 for pad in self.pads if not pad.changes)

    @property
    def planned_change_count(self) -> int:
        return sum(len(pad.changes) for pad in self.pads)

    @property
    def scanned_pad_count(self) -> int:
        return len(self.pads)

    @property
    def readiness_counts(self) -> dict[str, int]:
        counts = dict.fromkeys(READINESS_COUNT_KEYS, 0)
        for pad in self.pads:
            if pad.changes:
                counts["ready"] += 1
            elif pad.machine_compatibility_status == "machine_disabled":
                counts["machine_disabled"] += 1
            elif pad.machine_compatibility_status == "unknown_machine":
                counts["unknown_machine"] += 1
            elif pad.machine_compatibility_status == "incompatible_with_pad":
                counts["incompatible_with_pad"] += 1
            else:
                counts["no_mutable_legal_pads"] += 1
        return counts


def build_snapshot_mutation_plan(
    snapshot: RytmKitSnapshot,
    *,
    depth: str,
) -> SnapshotMutationPlan:
    """Build a deterministic passive mutation plan from captured kit values."""

    if depth not in DEPTH_DELTAS:
        raise SnapshotMutationPlanError("depth must be micro, groove, or strong")

    return SnapshotMutationPlan(
        slot_number=snapshot.slot_number,
        kit_name=snapshot.kit_name,
        depth=depth,
        snapshot_parameter_map_status=snapshot.parameter_map_status,
        pads=tuple(_build_pad_plan(pad, depth) for pad in snapshot.pads),
    )


def build_snapshot_mutation_plan_from_file(
    path: str | Path,
    *,
    slot: int,
    depth: str,
) -> SnapshotMutationPlan:
    """Decode a saved kit slot and plan relative mutations from it."""

    snapshot = decode_rytm_kit_snapshot_file(path, slot=slot)
    return build_snapshot_mutation_plan(snapshot, depth=depth)


def filter_snapshot_mutation_plan_to_pad(
    plan: SnapshotMutationPlan,
    *,
    pad: int,
) -> SnapshotMutationPlan:
    """Return a copy of a Rytm snapshot mutation plan for one pad."""

    if not isinstance(plan, SnapshotMutationPlan):
        raise TypeError("plan must be a SnapshotMutationPlan")
    if pad not in range(1, PAD_COUNT + 1):
        raise SnapshotMutationPlanError("Rytm snapshot pad must be 1 through 12")

    selected_pads = tuple(pad_plan for pad_plan in plan.pads if pad_plan.pad == pad)
    if not selected_pads:
        raise SnapshotMutationPlanError("Rytm snapshot pad must be 1 through 12")

    return SnapshotMutationPlan(
        slot_number=plan.slot_number,
        kit_name=plan.kit_name,
        depth=plan.depth,
        snapshot_parameter_map_status=plan.snapshot_parameter_map_status,
        pads=selected_pads,
    )


def format_snapshot_mutation_plan_report(plan: SnapshotMutationPlan) -> list[str]:
    """Format a deterministic passive snapshot mutation plan report."""

    lines = [
        "RytmRandomizer passive Snapshot Mutation Plan Report",
        f"Source slot: {plan.slot_number}",
        f"Kit: {plan.kit_name or '<blank>'}",
        f"Depth: {plan.depth}",
        f"Snapshot parameter map: {plan.snapshot_parameter_map_status}",
        f"Pads scanned: {_format_scanned_pads(plan)}",
        f"Planned pads: {plan.planned_pad_count} / {plan.scanned_pad_count}",
        f"Blocked pads: {plan.blocked_pad_count} / {plan.scanned_pad_count}",
        format_snapshot_readiness_summary(plan),
        f"Planned changes: {plan.planned_change_count}",
        "Pad plans:",
    ]
    for pad in plan.pads:
        lines.append(
            f"- Pad {pad.pad} / MIDI channel {pad.midi_channel}: "
            f"{pad.machine_label} / {pad.machine_compatibility_status} / "
            f"{pad.baseline_status} / "
            f"{len(pad.changes)} change(s)"
        )
    if plan.planned_change_count:
        lines.append("Planned CC changes:")
        for pad in plan.pads:
            lines.extend(_format_change_line(change) for change in pad.changes)
    lines.extend(
        [
            "Mutation policy:",
            "- captured-value relative",
            "- bounded deterministic deltas",
            "- no anchor loading",
            "- no machine switching",
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no MIDI receive",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
    return lines


def format_snapshot_mutation_plan_error(path: str | Path, message: str) -> list[str]:
    """Format a deterministic passive mutation-plan error."""

    lines = format_rytm_kit_snapshot_error(path, message)
    lines[0] = "RytmRandomizer passive Snapshot Mutation Plan Report"
    return lines


def _build_pad_plan(
    pad: RytmSnapshotPad,
    depth: str,
) -> SnapshotPadMutationPlan:
    if pad.machine_compatibility_status == "incompatible_with_pad":
        changes: tuple[SnapshotPlannedChange, ...] = ()
        plan_status = "blocked_machine_incompatible_with_pad"
    else:
        changes = tuple(
            _build_change(pad, parameter, depth) for parameter in _select_parameters(pad)
        )
        changes = tuple(
            change for change in changes if change.planned_value != change.baseline_value
        )
        plan_status = "planned" if changes else "blocked_no_mutable_snapshot_parameters"
    return SnapshotPadMutationPlan(
        pad=pad.pad,
        midi_channel=pad.midi_channel,
        sound_name=pad.sound_name,
        machine_label=pad.machine_label,
        machine_value=pad.machine_value,
        machine_compatibility_status=pad.machine_compatibility_status,
        baseline_status=pad.parameter_map_status,
        plan_status=plan_status,
        changes=changes,
    )


def format_snapshot_readiness_summary(plan: SnapshotMutationPlan) -> str:
    """Format the operator-facing snapshot mutation readiness bucket summary."""

    counts = plan.readiness_counts
    return (
        "Readiness summary: "
        f"ready {counts['ready']} / "
        f"disabled {counts['machine_disabled']} / "
        f"unknown {counts['unknown_machine']} / "
        f"incompatible {counts['incompatible_with_pad']} / "
        f"no mutable legal pads {counts['no_mutable_legal_pads']}"
    )


def _select_parameters(pad: RytmSnapshotPad) -> tuple[RytmSnapshotParameter, ...]:
    by_name = {parameter.name: parameter for parameter in pad.parameters}
    selected = [by_name[name] for name in MUTATION_PARAMETER_PRIORITY if name in by_name]
    return tuple(selected[:MAX_CHANGES_PER_PAD])


def _build_change(
    pad: RytmSnapshotPad,
    parameter: RytmSnapshotParameter,
    depth: str,
) -> SnapshotPlannedChange:
    delta = _signed_delta(pad=pad.pad, cc=parameter.cc, name=parameter.name, depth=depth)
    planned_value = _clamp_midi_value(parameter.value + delta)
    return SnapshotPlannedChange(
        pad=pad.pad,
        midi_channel=pad.midi_channel,
        machine_label=pad.machine_label,
        parameter_name=parameter.name,
        cc=parameter.cc,
        baseline_value=parameter.value,
        planned_value=planned_value,
        delta=planned_value - parameter.value,
        source=parameter.source,
    )


def _signed_delta(*, pad: int, cc: int, name: str, depth: str) -> int:
    delta = DEPTH_DELTAS[depth][_delta_family(name, cc)]
    direction = 1 if (pad + cc) % 2 == 0 else -1
    return delta * direction


def _delta_family(name: str, cc: int) -> str:
    if name.endswith("Tune") or cc == 17:
        return "pitch"
    if name.startswith("LFO "):
        return "lfo"
    return "default"


def _clamp_midi_value(value: int) -> int:
    return max(0, min(127, value))


def _format_change_line(change: SnapshotPlannedChange) -> str:
    return (
        f"- Pad {change.pad} {change.machine_label} / {change.parameter_name}: "
        f"CC{change.cc} {change.baseline_value} -> {change.planned_value} "
        f"(delta {change.delta:+d})"
    )


def _format_scanned_pads(plan: SnapshotMutationPlan) -> str:
    pads = tuple(pad.pad for pad in plan.pads)
    if pads == tuple(range(1, PAD_COUNT + 1)):
        return "1-12"
    return ", ".join(str(pad) for pad in pads) if pads else "none"


__all__ = [
    "SnapshotMutationPlan",
    "SnapshotMutationPlanError",
    "SnapshotPadMutationPlan",
    "SnapshotPlannedChange",
    "build_snapshot_mutation_plan",
    "build_snapshot_mutation_plan_from_file",
    "filter_snapshot_mutation_plan_to_pad",
    "format_snapshot_readiness_summary",
    "format_snapshot_mutation_plan_error",
    "format_snapshot_mutation_plan_report",
]
