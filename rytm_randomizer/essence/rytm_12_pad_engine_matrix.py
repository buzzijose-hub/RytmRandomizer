"""Passive Analog Rytm 12-pad engine compatibility matrix.

This module turns the OS 1.72 pad/machine catalog into an operator-facing
runtime support report. It does not import MIDI libraries, open ports, send
MIDI, receive SysEx, write SysEx, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from .machine_catalog import (
    RytmPadCapability,
    get_machine_profile,
    list_machine_profiles,
    list_rytm_pad_capabilities,
)
from .rytm_engine_cycle_starter_profiles import ENGINE_SOURCE_STARTERS


@dataclass(frozen=True)
class RytmPadEngineSlot:
    """One machine option allowed on one Analog Rytm pad."""

    machine_key: str
    machine_label: str
    family: str
    machine_value: int | None
    support_status: str
    cc15_selectable: bool
    source_starter_status: str


@dataclass(frozen=True)
class RytmPadEngineMatrixRow:
    """Allowed engine/runtime support summary for one Rytm pad."""

    pad: int
    midi_channel: int
    wire_channel: int
    track_code: str
    label: str
    machines: tuple[RytmPadEngineSlot, ...]

    @property
    def machine_count(self) -> int:
        return len(self.machines)

    @property
    def machine_keys(self) -> tuple[str, ...]:
        return tuple(machine.machine_key for machine in self.machines)

    @property
    def cc15_selectable_count(self) -> int:
        return sum(1 for machine in self.machines if machine.cc15_selectable)

    @property
    def source_starter_covered_count(self) -> int:
        return sum(
            1 for machine in self.machines if machine.source_starter_status == "source starter"
        )

    @property
    def source_starter_pending_count(self) -> int:
        return self.machine_count - self.source_starter_covered_count

    @property
    def mutable_v134_count(self) -> int:
        return sum(1 for machine in self.machines if machine.support_status == "mutable_v134")

    @property
    def unmapped_count(self) -> int:
        return sum(1 for machine in self.machines if not machine.cc15_selectable)


@dataclass(frozen=True)
class RytmTwelvePadEngineMatrix:
    """Complete passive 12-pad Rytm engine compatibility matrix."""

    rows: tuple[RytmPadEngineMatrixRow, ...]
    concrete_machine_profile_count: int

    @property
    def pad_count(self) -> int:
        return len(self.rows)

    @property
    def allowed_machine_slot_count(self) -> int:
        return sum(row.machine_count for row in self.rows)

    @property
    def cc15_selectable_slot_count(self) -> int:
        return sum(row.cc15_selectable_count for row in self.rows)

    @property
    def source_starter_covered_slot_count(self) -> int:
        return sum(row.source_starter_covered_count for row in self.rows)

    @property
    def source_starter_pending_slot_count(self) -> int:
        return sum(row.source_starter_pending_count for row in self.rows)

    @property
    def mutable_v134_slot_count(self) -> int:
        return sum(row.mutable_v134_count for row in self.rows)

    @property
    def unmapped_slot_count(self) -> int:
        return sum(row.unmapped_count for row in self.rows)

    def row_for_pad(self, pad: int) -> RytmPadEngineMatrixRow:
        """Return the matrix row for one 1-based pad."""

        for row in self.rows:
            if row.pad == pad:
                return row
        raise KeyError(f"unknown Rytm pad: {pad!r}")


def build_rytm_12_pad_engine_matrix() -> RytmTwelvePadEngineMatrix:
    """Build the passive 12-pad Rytm engine compatibility matrix."""

    concrete_profiles = tuple(
        profile for profile in list_machine_profiles() if profile.machine_value is not None
    )
    return RytmTwelvePadEngineMatrix(
        rows=tuple(_row_from_capability(capability) for capability in list_rytm_pad_capabilities()),
        concrete_machine_profile_count=len(concrete_profiles),
    )


def format_rytm_12_pad_engine_matrix_report(
    matrix: RytmTwelvePadEngineMatrix | None = None,
) -> list[str]:
    """Format a deterministic passive 12-pad engine matrix report."""

    if matrix is None:
        matrix = build_rytm_12_pad_engine_matrix()

    lines = [
        "RytmRandomizer passive Rytm 12-Pad Engine Matrix Report",
        "Reference: Analog Rytm MKII OS 1.72 pad/machine compatibility",
        f"Pads: {matrix.pad_count}",
        f"Concrete machine profiles: {matrix.concrete_machine_profile_count}",
        f"Allowed pad-machine slots: {matrix.allowed_machine_slot_count}",
        f"CC15-selectable slots: {matrix.cc15_selectable_slot_count}",
        f"Source-starter covered slots: {matrix.source_starter_covered_slot_count}",
        f"Source-starter pending slots: {matrix.source_starter_pending_slot_count}",
        f"V1.34 tuned-mutation slots: {matrix.mutable_v134_slot_count}",
        f"Unmapped slots: {matrix.unmapped_slot_count}",
        "Pad engine matrix:",
    ]
    for row in matrix.rows:
        lines.append(_format_row_summary(row))
        lines.append(f"  Machines: {_format_machine_slots(row.machines)}")
    lines.extend(
        [
            "Runtime policy:",
            "- Pads 6-8 are XT tom lanes; Pad 10 is OH open hihat, not XT Classic.",
            "- CC15 engine cycling is eligible only for machines listed under that pad.",
            "- source-starter covered means a starter SRC-slot profile exists for the engine.",
            (
                "- mutable_v134 means deeper tuned anchor/mutation logic already exists; "
                "machine_selectable means engine switch and starter shaping only."
            ),
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


def _row_from_capability(capability: RytmPadCapability) -> RytmPadEngineMatrixRow:
    return RytmPadEngineMatrixRow(
        pad=capability.pad,
        midi_channel=capability.pad,
        wire_channel=capability.pad - 1,
        track_code=capability.track_code,
        label=capability.label,
        machines=tuple(_slot_from_machine_key(key) for key in capability.allowed_machine_keys),
    )


def _slot_from_machine_key(machine_key: str) -> RytmPadEngineSlot:
    profile = get_machine_profile(machine_key)
    return RytmPadEngineSlot(
        machine_key=profile.key,
        machine_label=profile.label,
        family=profile.family,
        machine_value=profile.machine_value,
        support_status=profile.support_status,
        cc15_selectable=profile.machine_value is not None,
        source_starter_status=_source_starter_status(profile.key),
    )


def _source_starter_status(machine_key: str) -> str:
    if machine_key in ENGINE_SOURCE_STARTERS:
        return "source starter"
    return "source starter pending"


def _format_row_summary(row: RytmPadEngineMatrixRow) -> str:
    return (
        f"- Pad {row.pad} / MIDI ch {row.midi_channel} wire {row.wire_channel} / "
        f"{row.track_code} / {row.label}: {row.machine_count} machine(s), "
        f"{row.cc15_selectable_count} CC15-ready, "
        f"{row.source_starter_covered_count} source-starter covered, "
        f"{row.source_starter_pending_count} source-starter pending, "
        f"{row.mutable_v134_count} V1.34 tuned"
    )


def _format_machine_slots(machines: tuple[RytmPadEngineSlot, ...]) -> str:
    return "; ".join(_format_machine_slot(machine) for machine in machines)


def _format_machine_slot(machine: RytmPadEngineSlot) -> str:
    value = "pending" if machine.machine_value is None else str(machine.machine_value)
    return (
        f"{machine.machine_label} CC15 -> {value} "
        f"[{machine.support_status}, {machine.source_starter_status}]"
    )


__all__ = [
    "RytmPadEngineMatrixRow",
    "RytmPadEngineSlot",
    "RytmTwelvePadEngineMatrix",
    "build_rytm_12_pad_engine_matrix",
    "format_rytm_12_pad_engine_matrix_report",
]
