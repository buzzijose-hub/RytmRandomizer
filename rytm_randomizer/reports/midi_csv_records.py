"""Fixed passive ledger records; original historical JSON remains opaque."""

from __future__ import annotations

from typing import Literal, TypeAlias, TypedDict

from .device_support_inventory import A4FieldCalibration, DeviceSupportParameter
from .midi_csv_matcher import MidiContext
from .midi_csv_source import CsvChoice

MidiCsvMatchStatus: TypeAlias = Literal[
    "matched", "partial_address", "reference_only", "ambiguous", "address_conflict", "unsafe"
]


class MidiCsvContext(TypedDict):
    family: str
    track_kind: str
    section: str | None
    machine: str | None


class MidiCsvLedgerContext(MidiCsvContext):
    source_track_index: None
    source_midi_channel: None
    registered_track_count: int
    role: str
    native_machine_identity: int | None
    machine_wire_identity: Literal["not_inferred_from_native_identity"]


class MidiCsvSourceCitation(TypedDict):
    filename: str
    sha256: str
    git_blob: str
    url: str
    attribution: str
    license: str
    license_url: str


class MidiCsvAddresses(TypedDict):
    cc_msb: int | None
    cc_lsb: int | None
    nrpn_msb: int | None
    nrpn_lsb: int | None


class MidiCsvRange(TypedDict):
    min: int | None
    max: int | None
    default: int | None


class MidiCsvRanges(TypedDict):
    cc: MidiCsvRange
    nrpn: MidiCsvRange


class MidiCsvChoice(TypedDict):
    minimum: int
    maximum: int
    label: str


class MidiCsvEnumLabel(TypedDict):
    code: int
    label: str


class MidiCsvClaims(TypedDict):
    addresses: MidiCsvAddresses
    ranges: MidiCsvRanges
    orientation: str | None
    orientation_raw: str
    enums: list[MidiCsvChoice]
    enum_authority: str
    units: None
    units_status: str
    parameter_description: str
    notes: str


class MidiCsvCanonicalClaims(TypedDict):
    addresses: MidiCsvAddresses
    minimum: int | None
    maximum: int | None
    range_authority: str
    orientation: str | None
    kind: str | None
    enums: list[MidiCsvEnumLabel]
    enum_authority: str
    units: str
    display_note: str


class MidiCsvReferenceKnowledge(TypedDict):
    source_row_including_header: int | None
    source_sha256: str
    cc_range: tuple[int, int] | None
    nrpn_range: tuple[int, int] | None
    orientation: str | None
    enums: tuple[tuple[int, str], ...]
    qualitative_units: tuple[str, ...]
    notes: tuple[str, ...]
    supporting_urls: tuple[str, ...]
    missing_source_fields: tuple[str, ...]
    code_authority: Literal["reference_only"]


class MidiCsvNativeRelation(TypedDict):
    status: Literal["native_slot_relation_requires_separate_evidence"]
    inventory_native_locations: tuple[int, ...]
    domain: str
    encoding: str
    units: None
    orientation: None
    enums: list[MidiCsvEnumLabel]
    reason: str


MidiCsvNativeEvidence: TypeAlias = A4FieldCalibration | MidiCsvNativeRelation


class MidiCsvNativeClaims(TypedDict):
    binding_status: Literal["canonical_calibration_binding", "unestablished_from_csv"]
    field: str | None
    range: list[int | None] | None
    orientation: None
    encoding: str | None
    enums: tuple[tuple[int, str], ...] | list[tuple[int, str]]
    units: str | None
    display_quantum: str | None
    offline_policy: str | None
    protection: str | None
    CSV_to_native_conversion: Literal["not_inferred"]


class MidiCsvConflict(TypedDict):
    kind: Literal["identity_or_usage", "range", "orientation", "enum_labels_or_codes"]
    field: str | None
    csv: str | int | list[MidiCsvChoice]
    canonical: str | int | list[tuple[int, str]] | None
    resolution: str


class MidiCsvProtection(TypedDict):
    existing_policy: str | None
    scope: str
    notes: tuple[str, ...]


class MidiCsvOfflineSupport(TypedDict):
    inventory_status: str | None
    native_binding: Literal["canonical_field_calibration", "unestablished_from_csv"]
    ledger_grants_mutation_or_export: Literal[False]
    reference_only: bool
    status: str


class MidiCsvLiveSupport(TypedDict):
    inventory_status: str | None
    runtime_binding: str | None
    runtime_eligibility: str
    ledger_grants_send: Literal[False]
    physical_validation_granted: Literal[False]


class MidiCsvRecovery(TypedDict):
    inventory_status: str | None
    automatic_restore: Literal[False]
    source_reload: str


class MidiCsvAuditCounts(TypedDict, total=False):
    """Historical values are copied verbatim, not asserted to be current counts."""

    catalog_rows: object
    matched_csv_rows: object
    matched_distinct_catalog_rows: object


class MidiCsvLedgerSource(TypedDict):
    family: str
    device_id: str
    device_label: str
    filename: str
    sha256: str
    row_count: int
    source_url: str
    manual_url: str
    byte_count: int
    git_blob: str
    header_record: str
    retained_path: str
    original_path: object
    audit_comparison_counts: MidiCsvAuditCounts


class MidiCsvOmission(TypedDict):
    canonical_identity: str
    context: MidiCsvContext
    parameter: str
    addresses: tuple[int | None, int | None, int | None, int | None]
    range: list[int | None]
    orientation: str | None
    reason: str
    existing_support: DeviceSupportParameter
    ledger_grants_authority: Literal[False]


class MidiCsvNativeMachineIdentity(TypedDict):
    key: str
    native_identity: int
    label: str


class MidiCsvMachineReferenceConflict(TypedDict):
    machine: str
    source_row_including_header: int
    message: str
    source_sha256: str


class MidiCsvMachineAmbiguity(TypedDict):
    source_entry_id: str
    source_row: int
    csv_machine_wire_claims: list[MidiCsvChoice]
    native_catalog_identities: list[MidiCsvNativeMachineIdentity]
    usage_issues: tuple[str, ...]
    domain_relation: str
    canonical_reference_conflicts: list[MidiCsvMachineReferenceConflict]
    protection: str


class MidiCsvUpstreamSupplement(TypedDict):
    repository: str
    verified_dataset_commit: str
    git_blobs: dict[str, str]
    last_file_changes: dict[str, str]
    blob_urls: dict[str, str]
    verification: str
    a4_upstream_claim: str
    supplements_original_provenance: Literal[True]


class MidiCsvAuditMetadata(TypedDict):
    sha256: str
    provenance_sha256: str
    source_revision: object
    supersedes: object
    interpretation: str


class _MidiCsvOptionalManualChecks(TypedDict, total=False):
    retrieved_sha256: str
    retrieved_bytes: int
    pages: int


class MidiCsvManualChecks(_MidiCsvOptionalManualChecks):
    version: str
    checked_pages: tuple[int, ...]
    method: str
    findings: tuple[str, ...]
    not_checked: str


class MidiCsvSummary(TypedDict):
    source_rows: int
    canonical_omissions: int
    match_status_counts: dict[MidiCsvMatchStatus, int]
    rows_with_conflicts_or_missing_evidence: int
    per_device_status_counts: dict[str, dict[MidiCsvMatchStatus, int]]
    all_rows_retained: bool


def midi_csv_context_payload(context: MidiContext) -> MidiCsvContext:
    return {
        "family": context.family,
        "track_kind": context.track_kind,
        "section": context.section,
        "machine": context.machine,
    }


def midi_csv_choice_payload(choice: CsvChoice) -> MidiCsvChoice:
    return {"minimum": choice.minimum, "maximum": choice.maximum, "label": choice.label}


def midi_csv_addresses_payload(
    addresses: tuple[int | None, int | None, int | None, int | None],
) -> MidiCsvAddresses:
    return {
        "cc_msb": addresses[0],
        "cc_lsb": addresses[1],
        "nrpn_msb": addresses[2],
        "nrpn_lsb": addresses[3],
    }
