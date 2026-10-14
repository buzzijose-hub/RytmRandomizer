"""Context-and-address reconciliation independent of parameter-name similarity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..data.analog_four_display import ANALOG_FOUR_PARAMETER_DISPLAY
from ..data.elektron_midi_descriptions import (
    A4_MIDI_DESCRIPTIONS,
    RYTM_MIDI_DESCRIPTIONS,
    MidiParameterDescription,
)
from ..data.midi_csv_reconciliation import MIDI_CSV_A4_SECTIONS, MIDI_CSV_RYTM_SECTIONS
from ..data.rytm_machine_catalog import RYTM_MACHINE_PROFILES
from .device_support_inventory import DeviceSupportInventory, DeviceSupportParameter
from .midi_csv_source import MidiCsvRow, csv_row_issues


@dataclass(frozen=True)
class MidiContext:
    family: str
    track_kind: str
    section: str | None
    machine: str | None = None


@dataclass(frozen=True)
class CanonicalMidiRow:
    """Canonical identity, MIDI domain and existing inventory evidence."""

    identity: str
    context: MidiContext
    parameter: str
    addresses: tuple[int | None, int | None, int | None, int | None]
    minimum: int | None
    maximum: int | None
    orientation: str | None
    value_kind: str | None
    enums: tuple[tuple[int, str], ...]
    display_note: str
    support: DeviceSupportParameter
    reference_description: MidiParameterDescription | None = None


@dataclass(frozen=True)
class MidiCsvMatch:
    context: MidiContext
    status: Literal[
        "matched", "partial_address", "reference_only", "ambiguous", "address_conflict", "unsafe"
    ]
    candidates: tuple[CanonicalMidiRow, ...]
    issues: tuple[str, ...]


def csv_context(row: MidiCsvRow, family: str) -> MidiContext:
    """Identify the track/page or exact machine, not the parameter label."""
    section = row.cell("section")
    if family == "rytm":
        label = section.removeprefix("Synth: ")
        machine = next(
            (
                profile.key
                for profile in RYTM_MACHINE_PROFILES
                if profile.label.casefold() == label.casefold()
            ),
            None,
        )
        if machine is not None:
            return MidiContext(family, "machine_src", machine, machine)
        canonical = MIDI_CSV_RYTM_SECTIONS.get(section)
        return MidiContext(family, "general" if canonical else "unknown", canonical)
    kind = MIDI_CSV_A4_SECTIONS.get(section)
    if section in ("Envelopes", "LFOs"):
        # These shared CSV sections contain both synth-track and CV-track rows.
        kind = "cv" if row.cell("parameter_name").startswith("CV ") else "synth"
    return MidiContext(family, kind or "unknown", section)


def canonical_midi_rows(inventory: DeviceSupportInventory) -> tuple[CanonicalMidiRow, ...]:
    """Project current owners; no parallel wire map or copied capability grant."""
    evidence = {
        (row["device"], row["section"], row["machine"], row["field"]): row
        for row in inventory["parameters"]
        if row["surface"] == "midi_catalog"
    }
    rows: list[CanonicalMidiRow] = []
    for a4 in inventory["midi_addresses"]["a4"]:
        display = ANALOG_FOUR_PARAMETER_DISPLAY.get(a4["parameter"])
        kind = "performance" if a4["section"] == "PERFORMANCE" else "synth"
        rows.append(
            CanonicalMidiRow(
                "a4:" + a4["section"] + ":" + a4["parameter"],
                MidiContext("a4", kind, a4["section"]),
                a4["parameter"],
                (a4["cc_msb"], a4["cc_lsb"], a4["nrpn_msb"], a4["nrpn_lsb"]),
                None,
                None,
                None if display is None else display.display_scale,
                None if display is None else display.display_scale,
                () if display is None else tuple(display.value_labels.items()),
                "" if display is None else display.value_note,
                evidence[("a4", a4["section"], None, a4["parameter"])],
                A4_MIDI_DESCRIPTIONS.get(a4["parameter"]),
            )
        )
    for rytm in inventory["midi_addresses"]["rytm"]:
        machine = rytm["machine_key"]
        rows.append(
            CanonicalMidiRow(
                "rytm:" + (machine or rytm["section"]) + ":" + rytm["parameter"],
                MidiContext(
                    "rytm", "machine_src" if machine else "general", rytm["section"], machine
                ),
                rytm["parameter"],
                (rytm["cc_msb"], rytm["cc_lsb"], rytm["nrpn_msb"], rytm["nrpn_lsb"]),
                rytm["value_min"],
                rytm["value_max"],
                rytm["value_orientation"],
                rytm["value_kind"],
                evidence[("rytm", rytm["section"], machine, rytm["parameter"])]["legal_values"],
                "",
                evidence[("rytm", rytm["section"], machine, rytm["parameter"])],
                RYTM_MIDI_DESCRIPTIONS.get((rytm["section"], rytm["parameter"])),
            )
        )
    return tuple(rows)


def _same_context(left: MidiContext, right: MidiContext) -> bool:
    if left.family != right.family or left.track_kind != right.track_kind:
        return False
    if left.family == "rytm":
        return left.machine == right.machine and left.section == right.section
    return True


def match_midi_csv_row(
    row: MidiCsvRow, family: str, catalog: tuple[CanonicalMidiRow, ...]
) -> MidiCsvMatch:
    """Prefer complete addresses, require every supplied component to agree."""
    context = csv_context(row, family)
    problems = tuple(
        problem for problem in csv_row_issues(row) if not problem.startswith("address_missing_msb:")
    )
    if context.track_kind == "unknown" or problems:
        return MidiCsvMatch(context, "unsafe", (), problems or ("unknown_context",))
    addresses = tuple(row.number(key) for key in ("cc_msb", "cc_lsb", "nrpn_msb", "nrpn_lsb"))
    if all(value is None for value in addresses):
        return MidiCsvMatch(context, "reference_only", (), ("no_address_evidence",))
    scoped = tuple(item for item in catalog if _same_context(context, item.context))
    compatible = tuple(
        item
        for item in scoped
        if all(
            value is None or value == item.addresses[index] for index, value in enumerate(addresses)
        )
    )
    if len(compatible) > 1:
        return MidiCsvMatch(context, "ambiguous", compatible, ("address_not_unique_in_context",))
    if not compatible:
        competing = tuple(
            item
            for item in scoped
            if (addresses[0] is not None and addresses[0] == item.addresses[0])
            or (
                addresses[2] is not None
                and addresses[3] is not None
                and addresses[2:] == item.addresses[2:]
            )
        )
        if competing:
            return MidiCsvMatch(
                context, "address_conflict", competing, ("supplied_addresses_disagree",)
            )
        return MidiCsvMatch(context, "reference_only", (), ("no_canonical_address_in_context",))
    item = compatible[0]
    missing = tuple(
        key
        for key, value, canonical in zip(
            ("cc_msb", "cc_lsb", "nrpn_msb", "nrpn_lsb"), addresses, item.addresses, strict=True
        )
        if value is None and canonical is not None
    )
    partial = bool(missing)
    if addresses[2] is None or addresses[3] is None:
        partial = partial or (addresses[0] is None)
    return MidiCsvMatch(
        context,
        "partial_address" if partial else "matched",
        compatible,
        tuple("missing_csv_component:" + key for key in missing),
    )
