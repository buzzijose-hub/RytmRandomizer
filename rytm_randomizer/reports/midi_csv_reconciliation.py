"""Reproducible full-row ledger of supplied MIDI Guide references, never grants."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Final, Literal, TypedDict

from ..cockpit.export.reader import (
    decode_json_rejecting_duplicate_keys,
    read_bounded_artifact,
)
from ..data.midi_csv_reconciliation import (
    MIDI_CSV_ATTRIBUTION,
    MIDI_CSV_CODE_LICENSE,
    MIDI_CSV_FIRST_AUDIT_ROW,
    MIDI_CSV_LICENSE,
    MIDI_CSV_LICENSE_URL,
    MIDI_CSV_MANUAL_CHECKS,
    MIDI_CSV_REPOSITORY,
    MIDI_CSV_SOURCES,
    MIDI_CSV_UPSTREAM_BLOBS,
    MIDI_CSV_UPSTREAM_COMMIT,
    MIDI_CSV_UPSTREAM_LAST_CHANGE,
)
from ..data.rytm_machine_catalog import RYTM_MACHINE_PROFILES
from ..guardrails.input_validation import (
    require_int,
    require_integer_tuple,
    require_object,
    require_sequence,
    require_text,
    require_text_tuple,
)
from .device_support_inventory import UnsupportedCategory, build_device_support_inventory
from .formatter import sha256_bytes
from .midi_csv_ledger_rows import MidiCsvLedgerRow, build_csv_ledger_row
from .midi_csv_matcher import canonical_midi_rows, match_midi_csv_row
from .midi_csv_records import (
    MidiCsvAuditCounts,
    MidiCsvAuditMetadata,
    MidiCsvLedgerSource,
    MidiCsvMachineAmbiguity,
    MidiCsvManualChecks,
    MidiCsvMatchStatus,
    MidiCsvOmission,
    MidiCsvSummary,
    MidiCsvUpstreamSupplement,
    midi_csv_choice_payload,
    midi_csv_context_payload,
)
from .midi_csv_source import parse_csv_choices, read_midi_csv

_MAX_EVIDENCE_BYTES: Final[int] = 4 * 1024 * 1024


class MidiCsvReconciliationLedger(TypedDict):
    """Complete source rows, plus explicit canonical omissions and uncertainty."""

    schema: Literal["rytmrandomizer.midi-csv-reconciliation.v1"]
    hardware_access: Literal[False]
    hardware_validation_granted: Literal[False]
    runtime_authority_granted: Literal[False]
    attribution: str
    adapted_reference_data_license: str
    license_url: str
    code_license: str
    upstream_supplement: MidiCsvUpstreamSupplement
    provenance_original: dict[str, object]
    audit_v2_metadata: MidiCsvAuditMetadata
    official_manual_checks: dict[str, MidiCsvManualChecks]
    catalog_inventory_sha256: str
    sources: list[MidiCsvLedgerSource]
    entries: list[MidiCsvLedgerRow]
    omission_entries: list[MidiCsvOmission]
    machine_wire_native_ambiguities: list[UnsupportedCategory | MidiCsvMachineAmbiguity]
    summary: MidiCsvSummary


def _mapping(value: object) -> dict[str, object]:
    return dict(require_object(value, "CSV evidence object", ValueError))


def _csv_evidence_records(value: object) -> list[dict[str, object]]:
    return [
        _mapping(record)
        for record in require_sequence(value, "CSV evidence records", ValueError, kind="list")
    ]


def _read_json(path: Path) -> tuple[dict[str, object], str]:
    raw = read_bounded_artifact(path, maximum=_MAX_EVIDENCE_BYTES, label="CSV evidence document")
    return _mapping(decode_json_rejecting_duplicate_keys(raw)), sha256_bytes(raw)


def _audit_index(source: dict[str, object]) -> dict[int, dict[str, object]]:
    comparison = _mapping(source["comparison"])
    results: dict[int, dict[str, object]] = {}
    for classification in (
        "matched",
        "unmatched_csv_rows",
        "ambiguous_csv_rows",
        "differences_or_missing_addresses",
    ):
        for record in _csv_evidence_records(comparison[classification]):
            number = record["row"]
            if type(number) is not int or number < MIDI_CSV_FIRST_AUDIT_ROW:
                raise ValueError("Audit source row identity is unsafe")
            results.setdefault(number, {})[classification] = record
    return results


def _require_provenance(
    provenance: dict[str, object], source: dict[str, object], digest: str, rows: int
) -> None:
    matching = [
        record
        for record in _csv_evidence_records(provenance["files"])
        if record.get("sha256") == digest
    ]
    if len(matching) != 1 or matching[0].get("rows") != rows:
        raise ValueError("Provenance does not identify the pinned source")
    if source.get("sha256") != digest or source.get("rows") != rows:
        raise ValueError("audit-v2 does not identify the pinned source")
    if provenance.get("license_reported_by_site") != MIDI_CSV_LICENSE:
        raise ValueError("Provenance license disagrees with retained reference contract")


def _audit_counts(comparison: object) -> MidiCsvAuditCounts:
    data = _mapping(comparison)
    result: MidiCsvAuditCounts = {}
    if "catalog_rows" in data:
        result["catalog_rows"] = data["catalog_rows"]
    if "matched_csv_rows" in data:
        result["matched_csv_rows"] = data["matched_csv_rows"]
    if "matched_distinct_catalog_rows" in data:
        result["matched_distinct_catalog_rows"] = data["matched_distinct_catalog_rows"]
    return result


def _manual_checks(value: object) -> MidiCsvManualChecks:
    data = require_object(value, "manual checks", ValueError)
    result: MidiCsvManualChecks = {
        "version": require_text(data["version"], "manual version", ValueError),
        "checked_pages": require_integer_tuple(data["checked_pages"], "checked pages", ValueError),
        "method": require_text(data["method"], "manual method", ValueError),
        "findings": require_text_tuple(data["findings"], "manual findings", ValueError),
        "not_checked": require_text(data["not_checked"], "manual limits", ValueError),
    }
    if "retrieved_sha256" in data:
        result["retrieved_sha256"] = require_text(
            data["retrieved_sha256"], "manual hash", ValueError
        )
    if "retrieved_bytes" in data:
        result["retrieved_bytes"] = require_int(data["retrieved_bytes"], "manual bytes", ValueError)
    if "pages" in data:
        result["pages"] = require_int(data["pages"], "manual pages", ValueError)
    return result


def _machine_ambiguities(entries: list[MidiCsvLedgerRow]) -> list[MidiCsvMachineAmbiguity]:
    results: list[MidiCsvMachineAmbiguity] = []
    for row in entries:
        if row["canonical_identity"] != "rytm:COMMON:Track Machine Type":
            continue
        claims, issues = parse_csv_choices(row["raw_cells"]["usage"])
        results.append(
            {
                "source_entry_id": row["entry_id"],
                "source_row": row["source_row"],
                "csv_machine_wire_claims": [midi_csv_choice_payload(claim) for claim in claims],
                "native_catalog_identities": [
                    {
                        "key": profile.key,
                        "native_identity": profile.machine_value,
                        "label": profile.label,
                    }
                    for profile in RYTM_MACHINE_PROFILES
                ],
                "usage_issues": issues,
                "domain_relation": "unresolved; same numeric coordinate is not proof of native-to-MIDI conversion",
                "canonical_reference_conflicts": [
                    {
                        "machine": profile.key,
                        "source_row_including_header": note.source_row,
                        "message": note.message,
                        "source_sha256": note.source.supplied_sha256,
                    }
                    for profile in RYTM_MACHINE_PROFILES
                    for note in profile.reference_notes
                ],
                "protection": "source identity and machine-selection holds remain unchanged",
            }
        )
    return results


def build_midi_csv_reconciliation(
    a4_csv: Path, rytm_csv: Path, audit_v2: Path, provenance: Path
) -> MidiCsvReconciliationLedger:
    """Read only explicit files and canonical passive inventory; never MIDI/USB."""
    audit, audit_hash = _read_json(audit_v2)
    origin, provenance_hash = _read_json(provenance)
    audit_sources = _csv_evidence_records(audit["sources"])
    inventory = build_device_support_inventory()
    catalog = canonical_midi_rows(inventory)
    entries: list[MidiCsvLedgerRow] = []
    sources: list[MidiCsvLedgerSource] = []
    matched: set[str] = set()
    for path, spec in zip((a4_csv, rytm_csv), MIDI_CSV_SOURCES, strict=True):
        source = read_midi_csv(path, spec)
        if source.git_blob != MIDI_CSV_UPSTREAM_BLOBS[spec.family]:
            raise ValueError("Supplied CSV differs from verified upstream Git blob")
        audit_source = [record for record in audit_sources if record.get("sha256") == source.sha256]
        if len(audit_source) != 1:
            raise ValueError("audit-v2 has ambiguous or absent source identity")
        _require_provenance(origin, audit_source[0], source.sha256, len(source.rows))
        historical = _audit_index(audit_source[0])
        for row in source.rows:
            match = match_midi_csv_row(row, spec.family, catalog)
            entry = build_csv_ledger_row(
                source, row, match, inventory, historical.get(row.ordinal + 1)
            )
            entries.append(entry)
            if entry["canonical_identity"] is not None:
                matched.add(entry["canonical_identity"])
        sources.append(
            {
                "family": spec.family,
                "device_id": spec.device_id,
                "device_label": spec.device_label,
                "filename": spec.filename,
                "sha256": spec.sha256,
                "row_count": spec.row_count,
                "source_url": spec.source_url,
                "manual_url": spec.manual_url,
                "byte_count": source.byte_count,
                "git_blob": source.git_blob,
                "header_record": source.header_record,
                "retained_path": "tests/fixtures/midi_guide/" + spec.filename,
                "original_path": audit_source[0]["path"],
                "audit_comparison_counts": _audit_counts(audit_source[0]["comparison"]),
            }
        )
    omissions: list[MidiCsvOmission] = [
        {
            "canonical_identity": item.identity,
            "context": midi_csv_context_payload(item.context),
            "parameter": item.parameter,
            "addresses": item.addresses,
            "range": [item.minimum, item.maximum],
            "orientation": item.orientation,
            "reason": "canonical row absent from supplied CSV; do not invent a source row",
            "existing_support": {**item.support},
            "ledger_grants_authority": False,
        }
        for item in catalog
        if item.identity not in matched
    ]
    statuses: Counter[MidiCsvMatchStatus] = Counter(entry["match_status"] for entry in entries)
    ambiguities: list[UnsupportedCategory | MidiCsvMachineAmbiguity] = [
        {**row} for row in inventory["unsupported_categories"]
    ]
    ambiguities.extend(_machine_ambiguities(entries))
    return {
        "schema": "rytmrandomizer.midi-csv-reconciliation.v1",
        "hardware_access": False,
        "hardware_validation_granted": False,
        "runtime_authority_granted": False,
        "attribution": MIDI_CSV_ATTRIBUTION,
        "adapted_reference_data_license": MIDI_CSV_LICENSE,
        "license_url": MIDI_CSV_LICENSE_URL,
        "code_license": MIDI_CSV_CODE_LICENSE,
        "upstream_supplement": {
            "repository": MIDI_CSV_REPOSITORY,
            "verified_dataset_commit": MIDI_CSV_UPSTREAM_COMMIT,
            "git_blobs": dict(MIDI_CSV_UPSTREAM_BLOBS),
            "last_file_changes": dict(MIDI_CSV_UPSTREAM_LAST_CHANGE),
            "blob_urls": {
                spec.family: MIDI_CSV_REPOSITORY
                + "/blob/"
                + MIDI_CSV_UPSTREAM_COMMIT
                + "/Elektron/"
                + spec.filename.replace(" ", "%20")
                for spec in MIDI_CSV_SOURCES
            },
            "verification": "Git blob computed locally from exact original bytes; agrees with parent-verified upstream API",
            "a4_upstream_claim": "June 10 change describes OS1.55 manual/live-monitor reference; third-party claim, not our physical receipt",
            "supplements_original_provenance": True,
        },
        "provenance_original": origin,
        "audit_v2_metadata": {
            "sha256": audit_hash,
            "provenance_sha256": provenance_hash,
            "source_revision": audit.get("source_revision"),
            "supersedes": audit.get("supersedes"),
            "interpretation": "historical comparison evidence, not current matcher or eligibility authority",
        },
        "catalog_inventory_sha256": sha256_bytes(
            json.dumps(inventory, sort_keys=True, ensure_ascii=True).encode("ascii")
        ),
        "official_manual_checks": {
            family: _manual_checks(checks) for family, checks in MIDI_CSV_MANUAL_CHECKS.items()
        },
        "sources": sources,
        "entries": entries,
        "omission_entries": omissions,
        "machine_wire_native_ambiguities": ambiguities,
        "summary": {
            "source_rows": len(entries),
            "canonical_omissions": len(omissions),
            "match_status_counts": dict(sorted(statuses.items())),
            "rows_with_conflicts_or_missing_evidence": sum(
                bool(entry["conflicts"]) for entry in entries
            ),
            "per_device_status_counts": {
                spec.family: dict(
                    Counter(
                        entry["match_status"]
                        for entry in entries
                        if entry["device_id"] == spec.device_id
                    )
                )
                for spec in MIDI_CSV_SOURCES
            },
            "all_rows_retained": len(entries) == sum(spec.row_count for spec in MIDI_CSV_SOURCES),
        },
    }


def serialize_midi_csv_ledger(ledger: MidiCsvReconciliationLedger) -> bytes:
    """Stable ASCII JSON avoids platform newline and Unicode serialization drift."""
    return (json.dumps(ledger, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def format_midi_csv_gap_summary(ledger: MidiCsvReconciliationLedger) -> bytes:
    """Human review index; the full JSON, not this summary, owns the row ledger."""
    lines = [
        "# MIDI Guide CSV Reconciliation",
        "",
        "All 552 supplied rows are retained verbatim in `midi-csv-reconciliation.json`.",
        "Reference/adapted data: Pencil Research and MIDI Guide community contributors,",
        f"[{MIDI_CSV_LICENSE}]({MIDI_CSV_LICENSE_URL}). Code retains repository {MIDI_CSV_CODE_LICENSE}.",
        "No MIDI/USB discovery, ports, arming, mutation or sending occurs.",
        "",
        "## Reproduce",
        "",
        "From the checkout, using the project interpreter:",
        "",
        "```text",
        "python scripts/reconcile_midi_csv.py --check",
        "```",
        "",
        "Remove `--check` to regenerate the two documentation artifacts atomically.",
        "Inputs are byte-frozen under `tests/fixtures/midi_guide/`; G: is unnecessary.",
        "Original audit-v2/provenance are retained unchanged. Verified Git blob identities",
        "supplement the earlier unknown-upstream statement rather than rewriting it.",
        "",
        "## Source Identity",
        "",
        "| Source | Rows | SHA256 | Git Blob |",
        "| --- | ---: | --- | --- |",
    ]
    for source in ledger["sources"]:
        lines.append(
            f"| {source['filename']} | {source['row_count']} | `{source['sha256']}` | `{source['git_blob']}` |"
        )
    lines.extend(
        [
            "",
            f"Dataset commit: `{MIDI_CSV_UPSTREAM_COMMIT}`.",
            "",
            "## Matching And Representation",
            "",
            "Exact machine/track context plus all supplied address components are required.",
            "A partial address can match only if unique in context; missing is never zero.",
            "CC and NRPN contradictions, unknown contexts and nonunique candidates stay explicit.",
            "Parameter labels alone are never identity. CSV range/orientation/enum claims are",
            "separate from canonical MIDI, native words, display labels and physical evidence.",
            "Usage intervals remain intervals: overlapping destination defaults are conflicts,",
            "not expanded or flattened into 128 invented enum labels. Units are unknown unless",
            "a canonical binding supplies them; notes and raw cells remain intact.",
            "",
            "## Current Counts",
            "",
            "```json",
            json.dumps(ledger["summary"], sort_keys=True, indent=2),
            "```",
            "",
            "## Reference-Only Rows",
            "",
            "| Device | CSV Row | Section | Parameter |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for entry in ledger["entries"]:
        if entry["canonical_identity"] is None:
            cells = entry["raw_cells"]
            lines.append(
                f"| {entry['device_id']} | {entry['source_row']} | {cells['section']} | {cells['parameter_name']} |"
            )
    lines.extend(["", "## Canonical Omissions", ""])
    lines.extend(
        "- " + str(row["canonical_identity"]) + ": " + str(row["reason"])
        for row in ledger["omission_entries"]
    )
    lines.extend(
        [
            "",
            "## Conflict Index",
            "",
            "| Device | CSV Row | Conflict Fields |",
            "| --- | ---: | --- |",
        ]
    )
    for entry in ledger["entries"]:
        if entry["conflicts"]:
            fields = ", ".join(
                sorted({str(issue["field"] or issue["kind"]) for issue in entry["conflicts"]})
            )
            lines.append(f"| {entry['device_id']} | {entry['source_row']} | {fields} |")
    lines.extend(
        [
            "",
            "## Holds And Evidence",
            "",
            "Runtime binding and inventory evidence are reported, not new eligibility grants.",
            "`validated_runtime` is not a physical receipt. Current source/scope/locks/guardrails",
            "and exact-plan validation remain mandatory, including the limited Pad 2 evidence.",
            "A4/BOTH, paired precision, unsaved-state freshness and automatic restore remain held.",
            "All CY Ride SRC controls remain blocked. The narrow inbound HIT/TYP observations",
            "do not resolve native slot semantics or outbound behavior. A4 seven disproved",
            "live ordinals and the F1 native/wire distinction are preserved in retained evidence.",
            "The 125 extra A4 rows include FX/CV pages and Noise Color: no saved-field or SEND promotion.",
            "Physical audition, save/reload chronology and fresh recapture remain operator work.",
            "Official manual and retained hardware-document links accompany every row.",
            "",
        ]
    )
    return ("\n".join(lines)).encode("utf-8")
