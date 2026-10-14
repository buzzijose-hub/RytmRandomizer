"""Row projection keeps reference, canonical MIDI, native and authority apart."""

from __future__ import annotations

from typing import TypedDict

from ..cockpit.data.rytm_parameter_map import cockpit_parameter_key, cockpit_parameter_live_blockers
from ..data.midi_csv_reconciliation import (
    MIDI_CSV_ATTRIBUTION,
    MIDI_CSV_EVIDENCE_NOTES,
    MIDI_CSV_HARDWARE_EVIDENCE,
    MIDI_CSV_LICENSE,
    MIDI_CSV_LICENSE_URL,
    MIDI_CSV_ORIENTATION,
)
from ..data.rytm_machine_catalog import RYTM_MACHINE_PROFILES_BY_KEY
from .device_support_inventory import DeviceSupportInventory
from .midi_csv_matcher import CanonicalMidiRow, MidiCsvMatch
from .midi_csv_records import (
    MidiCsvCanonicalClaims,
    MidiCsvClaims,
    MidiCsvConflict,
    MidiCsvLedgerContext,
    MidiCsvLiveSupport,
    MidiCsvMatchStatus,
    MidiCsvNativeClaims,
    MidiCsvNativeEvidence,
    MidiCsvOfflineSupport,
    MidiCsvProtection,
    MidiCsvRange,
    MidiCsvRecovery,
    MidiCsvReferenceKnowledge,
    MidiCsvSourceCitation,
    midi_csv_addresses_payload,
    midi_csv_choice_payload,
    midi_csv_context_payload,
)
from .midi_csv_source import MidiCsvRow, MidiCsvSource, parse_csv_choices


class MidiCsvLedgerRow(TypedDict):
    """One immutable source record's complete passive reconciliation."""

    entry_id: str
    device_id: str
    source_row: int
    source_line_span: list[int]
    raw_cells: dict[str, str]
    raw_record: str
    source: MidiCsvSourceCitation
    canonical_identity: str | None
    canonical_candidates: list[str]
    context: MidiCsvLedgerContext
    match_status: MidiCsvMatchStatus
    csv_claims: MidiCsvClaims
    canonical_midi_claims: MidiCsvCanonicalClaims | None
    canonical_reference_knowledge: MidiCsvReferenceKnowledge | None
    native_claims: MidiCsvNativeClaims
    native_evidence: list[MidiCsvNativeEvidence]
    conflicts: list[MidiCsvConflict]
    protection: MidiCsvProtection
    supported_offline_mutation_export: MidiCsvOfflineSupport
    live_send: MidiCsvLiveSupport
    recovery: MidiCsvRecovery
    evidence_sources: list[str]
    physical_blockers: list[str]
    historical_audit_evidence: dict[str, object] | None


def _csv_range(row: MidiCsvRow, prefix: str) -> MidiCsvRange:
    return {
        "min": row.number(prefix + "_min_value"),
        "max": row.number(prefix + "_max_value"),
        "default": row.number(prefix + "_default_value"),
    }


def _csv_claims(row: MidiCsvRow) -> tuple[MidiCsvClaims, tuple[str, ...]]:
    choices, issues = parse_csv_choices(row.cell("usage"))
    return {
        "addresses": {
            "cc_msb": row.number("cc_msb"),
            "cc_lsb": row.number("cc_lsb"),
            "nrpn_msb": row.number("nrpn_msb"),
            "nrpn_lsb": row.number("nrpn_lsb"),
        },
        "ranges": {"cc": _csv_range(row, "cc"), "nrpn": _csv_range(row, "nrpn")},
        "orientation": MIDI_CSV_ORIENTATION.get(row.cell("orientation")),
        "orientation_raw": row.cell("orientation"),
        "enums": [midi_csv_choice_payload(choice) for choice in choices],
        "enum_authority": "community_usage_claims; intervals_and_overlaps_preserved",
        "units": None,
        "units_status": "no_explicit_units_column; MIDI scalars are not native or acoustic units",
        "parameter_description": row.cell("parameter_description"),
        "notes": row.cell("notes"),
    }, issues


def _canonical_claims(item: CanonicalMidiRow) -> MidiCsvCanonicalClaims:
    return {
        "addresses": midi_csv_addresses_payload(item.addresses),
        "minimum": item.minimum,
        "maximum": item.maximum,
        "range_authority": item.support["domain_authority"],
        "orientation": item.orientation,
        "kind": item.value_kind,
        "enums": [{"code": code, "label": label} for code, label in item.enums],
        "enum_authority": "canonical_display_catalog_not_native_or_physical_transport_proof",
        "units": "MIDI scalar; not a native/display conversion",
        "display_note": item.display_note,
    }


def _conflicts(
    row: MidiCsvRow,
    match: MidiCsvMatch,
    item: CanonicalMidiRow | None,
    usage_issues: tuple[str, ...],
) -> list[MidiCsvConflict]:
    results: list[MidiCsvConflict] = [
        {
            "kind": "identity_or_usage",
            "field": None,
            "csv": issue,
            "canonical": None,
            "resolution": "unresolved; source preserved",
        }
        for issue in match.issues + usage_issues
    ]
    if item is None:
        return results
    for prefix in ("cc", "nrpn"):
        for limit, current in (("min", item.minimum), ("max", item.maximum)):
            supplied = row.number(prefix + "_" + limit + "_value")
            if supplied is not None and current is not None and supplied != current:
                results.append(
                    {
                        "kind": "range",
                        "field": prefix + "_" + limit,
                        "csv": supplied,
                        "canonical": current,
                        "resolution": "unresolved; raw MIDI and parameter-domain claims may differ",
                    }
                )
    orientation = MIDI_CSV_ORIENTATION.get(row.cell("orientation"))
    canonical_orientation = {"unipolar": "zero_based", "bipolar": "centered"}.get(
        item.orientation or "", item.orientation
    )
    if orientation is not None and canonical_orientation not in (None, "enum", orientation):
        results.append(
            {
                "kind": "orientation",
                "field": "orientation",
                "csv": orientation,
                "canonical": canonical_orientation,
                "resolution": "unresolved; no change to native encoding or range",
            }
        )
    choices, _ = parse_csv_choices(row.cell("usage"))
    source_choices = {
        (choice.minimum, choice.label) for choice in choices if choice.minimum == choice.maximum
    }
    if source_choices and item.enums and source_choices != set(item.enums):
        results.append(
            {
                "kind": "enum_labels_or_codes",
                "field": "usage",
                "csv": [midi_csv_choice_payload(choice) for choice in choices],
                "canonical": list(item.enums),
                "resolution": "unresolved; label differences are not a code conversion",
            }
        )
    return results


def _native_evidence(
    item: CanonicalMidiRow | None, inventory: DeviceSupportInventory
) -> list[MidiCsvNativeEvidence]:
    if item is None:
        return []
    # Only a canonical calibration binding can relate these independent surfaces.
    # Similar names, MIDI addresses or numeric ranges do not establish a binding.
    if item.context.family == "a4":
        return [
            {**calibration}
            for calibration in inventory["a4_field_calibrations"]
            if calibration["parameter"] == item.parameter
            and calibration["native_field"] is not None
        ]
    return [
        {
            "status": "native_slot_relation_requires_separate_evidence",
            "inventory_native_locations": item.support["locations"],
            "domain": "not_equivalent_to_csv_midi_range",
            "encoding": "not_inferred_from_csv",
            "units": None,
            "orientation": None,
            "enums": [],
            "reason": "machine wire identity, native slot semantics and live conversion remain separate",
        }
    ]


def build_csv_ledger_row(
    source: MidiCsvSource,
    row: MidiCsvRow,
    match: MidiCsvMatch,
    inventory: DeviceSupportInventory,
    audit_evidence: dict[str, object] | None,
) -> MidiCsvLedgerRow:
    """No resolution here can alter runtime policy or physical acceptance."""
    item = match.candidates[0] if len(match.candidates) == 1 else None
    identified = item is not None and match.status in ("matched", "partial_address")
    claims, usage_issues = _csv_claims(row)
    support = item.support if item is not None else None
    blockers = (
        list(support["blockers"]) if support is not None else ["canonical_identity_unestablished"]
    )
    key: str | None = None
    if item is not None and source.spec.family == "rytm":
        key = cockpit_parameter_key(
            item.context.machine or "unknown",
            "SRC" if item.context.machine else item.context.section or "",
            item.parameter,
        )
        if key is not None:
            blockers.extend(cockpit_parameter_live_blockers(item.context.machine or "unknown", key))
    if not identified:
        blockers.append("reference_identity_cannot_authorize_runtime")
    blockers.extend(
        category["blocker"]
        for category in inventory["unsupported_categories"]
        if category["device"] in (source.spec.family, "both")
        and category["kind"] in ("hardware_evidence_missing", "physical_validation_pending")
    )
    blockers = list(dict.fromkeys(blockers))
    native = _native_evidence(item if identified else None, inventory)
    native_field = next(
        (
            calibration["native_field"]
            for calibration in native
            if "native_field" in calibration and calibration["native_field"] is not None
        ),
        None,
    )
    native_policy = next(
        (
            field
            for field in inventory["a4_studio_native_fields"]
            if source.spec.family == "a4" and field["parameter"] == native_field
        ),
        None,
    )
    profile = RYTM_MACHINE_PROFILES_BY_KEY.get(match.context.machine or "")
    context: MidiCsvLedgerContext = {
        **midi_csv_context_payload(match.context),
        "source_track_index": None,
        "source_midi_channel": None,
        "registered_track_count": inventory["registered_devices"][source.spec.device_id][
            "track_count"
        ],
        "role": "not_declared_by_reference_csv; no role-specific mutation grant",
        "native_machine_identity": None if profile is None else profile.machine_value,
        "machine_wire_identity": "not_inferred_from_native_identity",
    }
    return {
        "entry_id": source.sha256 + ":" + str(row.ordinal),
        "device_id": source.spec.device_id,
        "source_row": row.ordinal,
        "source_line_span": [row.line_start, row.line_end],
        "raw_cells": dict(row.cells),
        "raw_record": row.raw_record,
        "source": {
            "filename": source.spec.filename,
            "sha256": source.sha256,
            "git_blob": source.git_blob,
            "url": source.spec.source_url,
            "attribution": MIDI_CSV_ATTRIBUTION,
            "license": MIDI_CSV_LICENSE,
            "license_url": MIDI_CSV_LICENSE_URL,
        },
        "canonical_identity": item.identity if identified and item is not None else None,
        "canonical_candidates": [candidate.identity for candidate in match.candidates],
        "context": context,
        "match_status": match.status,
        "csv_claims": claims,
        "canonical_midi_claims": None if item is None else _canonical_claims(item),
        "canonical_reference_knowledge": (
            None
            if item is None or item.reference_description is None
            else {
                "source_row_including_header": item.reference_description.source_row,
                "source_sha256": item.reference_description.source.supplied_sha256,
                "cc_range": item.reference_description.cc_range,
                "nrpn_range": item.reference_description.nrpn_range,
                "orientation": item.reference_description.orientation,
                "enums": item.reference_description.reference_labels,
                "qualitative_units": item.reference_description.units,
                "notes": item.reference_description.notes,
                "supporting_urls": item.reference_description.supporting_urls,
                "missing_source_fields": item.reference_description.missing_source_fields,
                "code_authority": item.reference_description.code_authority,
            }
        ),
        "native_claims": {
            "binding_status": (
                "canonical_calibration_binding" if native_policy else "unestablished_from_csv"
            ),
            "field": native_field,
            "range": (
                None
                if native_policy is None
                else [native_policy["minimum_native"], native_policy["maximum_native"]]
            ),
            "orientation": None,
            "encoding": None if native_policy is None else native_policy["native_encoding"],
            "enums": [] if native_policy is None else native_policy["legal_codes"],
            "units": None if native_policy is None else "encoded native word; not CSV MIDI scalar",
            "display_quantum": None if native_policy is None else native_policy["display_quantum"],
            "offline_policy": None if native_policy is None else native_policy["offline_mutation"],
            "protection": None if native_policy is None else native_policy["protection_reason"],
            "CSV_to_native_conversion": "not_inferred",
        },
        "native_evidence": native,
        "conflicts": _conflicts(row, match, item, usage_issues),
        "protection": {
            "existing_policy": None if support is None else support["protection"],
            "scope": "current target-minus-lock and immutable source policy remains authoritative",
            "notes": MIDI_CSV_EVIDENCE_NOTES[source.spec.family],
        },
        "supported_offline_mutation_export": {
            "inventory_status": None if support is None else support["offline_mutation"],
            "native_binding": (
                "canonical_field_calibration"
                if native and source.spec.family == "a4"
                else "unestablished_from_csv"
            ),
            "ledger_grants_mutation_or_export": False,
            "reference_only": not identified,
            "status": "consult_current_Device_native_strategy; reference_csv_is_not_a_recipe",
        },
        "live_send": {
            "inventory_status": None if support is None else support["live_send"],
            "runtime_binding": key,
            "runtime_eligibility": "not_granted; requires_current_source_scope_guardrail_and_exact_plan_validation",
            "ledger_grants_send": False,
            "physical_validation_granted": False,
        },
        "recovery": {
            "inventory_status": None if support is None else support["recovery"],
            "automatic_restore": False,
            "source_reload": "manual_reload_and_fresh_capture; local_history_is_not_a_device_backup",
        },
        "evidence_sources": list(
            dict.fromkeys(
                [
                    source.spec.source_url,
                    source.spec.manual_url,
                    *MIDI_CSV_HARDWARE_EVIDENCE,
                    *(support["evidence"] if support is not None else ()),
                ]
            )
        ),
        "physical_blockers": blockers,
        "historical_audit_evidence": audit_evidence,
    }
