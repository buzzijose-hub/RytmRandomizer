"""Full retained reference reconciliation stays address-based and hardware inert."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tomllib
from dataclasses import asdict, replace
from pathlib import Path
from typing import Literal, get_args, get_type_hints, is_typeddict

import pytest

from rytm_randomizer.cockpit.export import reader as artifact_reader
from rytm_randomizer.data.midi_csv_reconciliation import (
    MIDI_CSV_ADDRESS_COLUMNS,
    MIDI_CSV_COLUMNS,
    MIDI_CSV_MANUAL_CHECKS,
    MIDI_CSV_SOURCES,
    MIDI_CSV_UPSTREAM_BLOBS,
)
from rytm_randomizer.observability.errors import DataError
from rytm_randomizer.reports.device_support_inventory import build_device_support_inventory
from rytm_randomizer.reports.midi_csv_ledger_rows import MidiCsvLedgerRow
from rytm_randomizer.reports.midi_csv_matcher import (
    MidiCsvMatch,
    canonical_midi_rows,
    match_midi_csv_row,
)
from rytm_randomizer.reports.midi_csv_reconciliation import (
    MidiCsvReconciliationLedger,
    build_midi_csv_reconciliation,
    format_midi_csv_gap_summary,
    serialize_midi_csv_ledger,
)
from rytm_randomizer.reports.midi_csv_records import (
    MidiCsvLiveSupport,
    MidiCsvOfflineSupport,
    MidiCsvOmission,
    MidiCsvRecovery,
    midi_csv_addresses_payload,
    midi_csv_choice_payload,
    midi_csv_context_payload,
)
from rytm_randomizer.reports.midi_csv_source import (
    MidiCsvRow,
    csv_row_issues,
    parse_csv_choices,
    parse_midi_csv,
    parse_optional_number,
    read_midi_csv,
)
from scripts.reconcile_midi_csv import main as reconcile_midi_csv_main

pytestmark = pytest.mark.fast
ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "tests" / "fixtures" / "midi_guide"


@pytest.fixture(scope="module")
def ledger():
    return build_midi_csv_reconciliation(
        INPUTS / MIDI_CSV_SOURCES[0].filename,
        INPUTS / MIDI_CSV_SOURCES[1].filename,
        INPUTS / "audit-v2.json",
        INPUTS / "provenance.json",
    )


@pytest.fixture(scope="module")
def catalog():
    return canonical_midi_rows(build_device_support_inventory())


def _row(family: str, **changes: str) -> MidiCsvRow:
    spec = next(spec for spec in MIDI_CSV_SOURCES if spec.family == family)
    row = read_midi_csv(INPUTS / spec.filename, spec).rows[0]
    return replace(row, cells=tuple((key, changes.get(key, value)) for key, value in row.cells))


def _csv_bytes(**changes: str) -> bytes:
    row = _row("a4", **changes)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(MIDI_CSV_COLUMNS)
    writer.writerow(dict(row.cells).values())
    return output.getvalue().encode("utf-8")


def test_ledger_retains_every_record_when_full_sources_are_used(ledger):
    assert len(ledger["entries"]) == 552
    assert ledger["summary"]["all_rows_retained"] is True
    for source in MIDI_CSV_SOURCES:
        raw = (INPUTS / source.filename).read_bytes()
        parsed = read_midi_csv(INPUTS / source.filename, source)
        assert parsed.git_blob == MIDI_CSV_UPSTREAM_BLOBS[source.family]
        assert parsed.sha256 == source.sha256
        rows = [row for row in ledger["entries"] if row["device_id"] == source.device_id]
        assert len(rows) == source.row_count
        assert (parsed.header_record + "".join(row["raw_record"] for row in rows)).encode(
            "utf-8"
        ) == raw
        assert all(len(row["raw_cells"]) == 18 for row in rows)


def test_ledger_separates_reference_only_rows_when_a4_fx_cv_are_present(ledger):
    rows = [
        row
        for row in ledger["entries"]
        if row["device_id"] == "analog_four_mk2" and row["match_status"] == "reference_only"
    ]
    assert len(rows) == 125
    assert {row["context"]["track_kind"] for row in rows} == {"fx", "cv", "synth"}
    assert [
        row["raw_cells"]["parameter_name"]
        for row in rows
        if row["context"]["track_kind"] == "synth"
    ] == ["Noise: Color"]
    assert all(row["canonical_identity"] is None for row in rows)
    assert all(not row["live_send"]["ledger_grants_send"] for row in rows)


def test_ledger_lists_omission_when_bt_classic_sweep_depth_is_absent(ledger):
    assert [row["canonical_identity"] for row in ledger["omission_entries"]] == [
        "rytm:bt_classic:Sweep Depth"
    ]


def test_ledger_separates_representation_when_native_and_midi_are_distinct(ledger):
    f1 = next(
        row
        for row in ledger["entries"]
        if row["canonical_identity"] == "a4:FILTERS:Filter1 Frequency"
    )
    assert f1["csv_claims"]["units"] is None
    assert f1["native_claims"]["binding_status"] == "canonical_calibration_binding"
    assert f1["native_claims"]["CSV_to_native_conversion"] == "not_inferred"
    for row in ledger["entries"]:
        assert {"ranges", "orientation", "enums", "units"} <= row["csv_claims"].keys()
        assert {"range", "orientation", "enums", "units"} <= row["native_claims"].keys()
        assert row["source"]["license"] == "CC-BY-SA-4.0"


def test_ledger_preserves_holds_when_inventory_category_is_validated_runtime(ledger):
    cy_ride = [row for row in ledger["entries"] if row["context"]["machine"] == "cy_ride"]
    assert len(cy_ride) == 8
    assert all("src_cy_ride_slot_unverified" in row["physical_blockers"] for row in cy_ride)
    assert not ledger["runtime_authority_granted"]
    assert not ledger["hardware_validation_granted"]
    for row in ledger["entries"]:
        assert not row["live_send"]["physical_validation_granted"]
        assert not row["recovery"]["automatic_restore"]
        assert not row["supported_offline_mutation_export"]["ledger_grants_mutation_or_export"]


def test_ledger_keeps_old_provenance_when_upstream_verification_supplements_it(ledger):
    assert ledger["provenance_original"] == json.loads((INPUTS / "provenance.json").read_bytes())
    assert ledger["upstream_supplement"]["supplements_original_provenance"] is True
    assert ledger["upstream_supplement"]["git_blobs"] == dict(MIDI_CSV_UPSTREAM_BLOBS)
    assert "supersedes" in ledger["audit_v2_metadata"]


@pytest.mark.parametrize(
    "value, expected", [("", None), (" ", None), ("0", 0), ("127", 127), ("-1", -1)]
)
def test_number_preserves_missing_when_cells_are_blank(value, expected):
    assert parse_optional_number(value) == expected


@pytest.mark.parametrize("value", ["False", "1.5", "NaN", "1e2", "0x10"])
def test_number_rejects_noninteger_when_cell_is_malformed(value):
    with pytest.raises(ValueError, match="integer"):
        parse_optional_number(value)


def test_usage_preserves_sparse_and_overlapping_claims_when_intervals_exist():
    choices, issues = parse_csv_choices("96: META None; 34: F1 Frequency; 0-127: META None")
    assert [(item.minimum, item.maximum) for item in choices] == [(96, 96), (34, 34), (0, 127)]
    assert issues == ("overlapping_usage_claims",)
    assert len(choices) == 3


def test_usage_retains_unparsed_claim_when_description_is_not_enum():
    choices, issues = parse_csv_choices("0: Off; arbitrary description; 10-2: reversed; 99999: bad")
    assert len(choices) == 1
    assert len(issues) == 3
    assert parse_csv_choices("") == ((), ())


@pytest.mark.parametrize(
    "changes, issue",
    [
        ({"cc_msb": "128"}, "address_outside_u7:cc_msb"),
        ({"cc_max_value": "128"}, "range_outside_midi_domain:cc"),
        ({"cc_min_value": "12", "cc_max_value": "1"}, "reversed_range:cc"),
        ({"cc_default_value": "128"}, "default_outside_range:cc"),
        ({"nrpn_max_value": "20000"}, "range_outside_midi_domain:nrpn"),
        ({"cc_msb": "", "cc_lsb": "3"}, "address_missing_msb:cc"),
    ],
)
def test_bounds_record_issue_when_reference_has_unsafe_value(changes, issue):
    assert issue in csv_row_issues(_row("a4", **changes))


def test_matcher_uses_machine_context_when_src_addresses_are_reused(catalog):
    row = _row(
        "rytm",
        section="Synth: BD Classic",
        parameter_name="misleading label",
        cc_msb="19",
        nrpn_msb="1",
        nrpn_lsb="3",
    )
    result = match_midi_csv_row(row, "rytm", catalog)
    assert result.candidates[0].identity == "rytm:bd_classic:Hold"
    other = replace(
        row,
        cells=tuple(
            (key, "Synth: BT Classic" if key == "section" else value) for key, value in row.cells
        ),
    )
    result = match_midi_csv_row(other, "rytm", catalog)
    assert result.candidates[0].identity == "rytm:bt_classic:Sweep Depth"


def test_matcher_does_not_match_label_when_address_is_missing(catalog):
    row = _row("a4", parameter_name="Performance Parameter A", cc_msb="", nrpn_msb="", nrpn_lsb="")
    result = match_midi_csv_row(row, "a4", catalog)
    assert result.status == "reference_only"
    assert not result.candidates


def test_matcher_marks_partial_when_unique_component_is_supported(catalog):
    result = match_midi_csv_row(_row("a4", nrpn_msb="", nrpn_lsb=""), "a4", catalog)
    assert result.status == "partial_address"
    assert result.candidates[0].parameter == "Performance Parameter A"
    assert "missing_csv_component:nrpn_msb" in result.issues


def test_matcher_accepts_partial_when_only_nrpn_lsb_is_unique_in_context(catalog):
    result = match_midi_csv_row(_row("a4", cc_msb="", nrpn_msb="", nrpn_lsb="0"), "a4", catalog)
    assert result.status == "partial_address"
    assert result.candidates[0].parameter == "Performance Parameter A"


def test_ledger_keeps_machine_code_ambiguities_when_wire_and_native_claims_differ(ledger):
    machine = next(
        row for row in ledger["machine_wire_native_ambiguities"] if "csv_machine_wire_claims" in row
    )
    assert "unresolved" in machine["domain_relation"]
    assert {conflict["machine"] for conflict in machine["canonical_reference_conflicts"]} == {
        "bd_hard",
        "rs_classic",
    }
    speed = next(
        row for row in ledger["entries"] if row["canonical_identity"] == "rytm:sy_chip:Speed"
    )
    assert speed["canonical_reference_knowledge"]["qualitative_units"] == (
        "BPM note divisions",
        "Hz",
        "single-shot",
    )
    assert speed["canonical_reference_knowledge"]["code_authority"] == "reference_only"


def test_matcher_marks_ambiguity_when_partial_address_has_multiple_candidates(catalog):
    row = _row("a4", cc_msb="", nrpn_msb="0", nrpn_lsb="")
    result = match_midi_csv_row(row, "a4", catalog)
    assert result.status == "ambiguous"
    assert len(result.candidates) == 10


def test_matcher_keeps_competing_identities_when_cc_nrpn_disagree(catalog):
    result = match_midi_csv_row(_row("a4", cc_msb="4"), "a4", catalog)
    assert result.status == "address_conflict"
    assert len(result.candidates) == 2


def test_matcher_rejects_unknown_context_when_labels_look_valid(catalog):
    result = match_midi_csv_row(_row("rytm", section="Synth: Evil"), "rytm", catalog)
    assert result.status == "unsafe"
    assert not result.candidates


@pytest.mark.parametrize("mutation", ["hash", "device", "count", "columns", "truncated"])
def test_parser_refuses_unsafe_source_when_contract_is_not_satisfied(mutation):
    raw = _csv_bytes(device="Unknown") if mutation == "device" else _csv_bytes()
    spec = replace(MIDI_CSV_SOURCES[0], sha256=hashlib.sha256(raw).hexdigest(), row_count=1)
    if mutation == "hash":
        spec = replace(spec, sha256="0" * 64)
    elif mutation == "count":
        spec = replace(spec, row_count=2)
    elif mutation == "columns":
        raw = raw.replace(b"manufacturer,", b"bad,", 1)
        spec = replace(spec, sha256=hashlib.sha256(raw).hexdigest())
    elif mutation == "truncated":
        raw = raw.rsplit(b",", 1)[0] + b"\n"
        spec = replace(spec, sha256=hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError):
        parse_midi_csv(raw, spec)


def test_parser_retains_multiline_record_when_notes_contain_newlines():
    raw = _csv_bytes(notes="line one\nline two")
    spec = replace(MIDI_CSV_SOURCES[0], sha256=hashlib.sha256(raw).hexdigest(), row_count=1)
    source = parse_midi_csv(raw, spec)
    assert source.rows[0].line_end == 3
    assert source.rows[0].cell("notes") == "line one\nline two"
    assert (source.header_record + source.rows[0].raw_record).encode("utf-8") == raw


def test_generation_is_deterministic_when_inputs_are_retained(ledger):
    assert (
        serialize_midi_csv_ledger(ledger)
        == (ROOT / "docs/catalogs/midi-csv-reconciliation.json").read_bytes()
    )
    assert (
        format_midi_csv_gap_summary(ledger)
        == (ROOT / "docs/catalogs/midi-csv-reconciliation.md").read_bytes()
    )


def test_fixed_row_contracts_match_all_generated_record_keys(ledger):
    contracts = get_type_hints(MidiCsvLedgerRow)
    for field in (
        "source",
        "context",
        "csv_claims",
        "canonical_midi_claims",
        "canonical_reference_knowledge",
        "native_claims",
        "protection",
        "supported_offline_mutation_export",
        "live_send",
        "recovery",
    ):
        annotation = contracts[field]
        contract = (
            annotation
            if is_typeddict(annotation)
            else next(option for option in get_args(annotation) if is_typeddict(option))
        )
        assert is_typeddict(contract)
        records = [entry[field] for entry in ledger["entries"] if entry[field] is not None]
        assert records
        assert all(set(record) == contract.__required_keys__ for record in records)
    assert contracts["match_status"] == get_type_hints(MidiCsvMatch)["status"]


def test_fixed_ledger_contracts_match_generated_sources_omissions_and_summary(ledger):
    contracts = get_type_hints(MidiCsvReconciliationLedger)
    for field in ("upstream_supplement", "audit_v2_metadata", "summary"):
        contract = contracts[field]
        assert is_typeddict(contract)
        assert set(ledger[field]) == contract.__required_keys__
    for field in ("sources", "omission_entries"):
        (contract,) = get_args(contracts[field])
        assert is_typeddict(contract)
        assert ledger[field]
        assert all(set(record) == contract.__required_keys__ for record in ledger[field])
    _, manual_contract = get_args(contracts["official_manual_checks"])
    assert is_typeddict(manual_contract)
    for checks in ledger["official_manual_checks"].values():
        assert manual_contract.__required_keys__ <= checks.keys()
        assert (
            checks.keys() <= manual_contract.__required_keys__ | manual_contract.__optional_keys__
        )
    assert ledger["official_manual_checks"] == {
        family: dict(checks) for family, checks in MIDI_CSV_MANUAL_CHECKS.items()
    }


def test_fixed_authority_contracts_cannot_describe_hardware_or_mutation_grants():
    for contract, fields in (
        (
            MidiCsvReconciliationLedger,
            ("hardware_access", "hardware_validation_granted", "runtime_authority_granted"),
        ),
        (MidiCsvLiveSupport, ("ledger_grants_send", "physical_validation_granted")),
        (MidiCsvOfflineSupport, ("ledger_grants_mutation_or_export",)),
        (MidiCsvRecovery, ("automatic_restore",)),
        (MidiCsvOmission, ("ledger_grants_authority",)),
    ):
        annotations = get_type_hints(contract)
        assert all(annotations[field] == Literal[False] for field in fields)


def test_fixed_projection_helpers_preserve_existing_source_and_choice_records(catalog):
    for item in catalog:
        assert midi_csv_context_payload(item.context) == asdict(item.context)
        assert midi_csv_addresses_payload(item.addresses) == dict(
            zip(MIDI_CSV_ADDRESS_COLUMNS, item.addresses, strict=True)
        )
    choices, _ = parse_csv_choices("96: META None; 34: F1 Frequency; 0-127: META None")
    assert [midi_csv_choice_payload(choice) for choice in choices] == [
        asdict(choice) for choice in choices
    ]


@pytest.mark.parametrize("include_counts", [False, True])
def test_fixed_source_records_keep_historical_json_opaque(tmp_path: Path, include_counts: bool):
    audit = json.loads((INPUTS / "audit-v2.json").read_bytes())
    historical_path = {"original_path_claim": [None, False, "not current source authority"]}
    historical_count = {"unknown_count_claim": True}
    audit["source_revision"] = {"historical_revision": None}
    audit["supersedes"] = ["opaque", {"metadata": False}]
    source = next(
        record for record in audit["sources"] if record["sha256"] == MIDI_CSV_SOURCES[0].sha256
    )
    source["path"] = historical_path
    source["comparison"]["catalog_rows"] = historical_count
    if not include_counts:
        for key in ("catalog_rows", "matched_csv_rows", "matched_distinct_catalog_rows"):
            source["comparison"].pop(key, None)
    path = tmp_path / "audit-v2.json"
    path.write_text(json.dumps(audit), encoding="utf-8")
    result = build_midi_csv_reconciliation(
        INPUTS / MIDI_CSV_SOURCES[0].filename,
        INPUTS / MIDI_CSV_SOURCES[1].filename,
        path,
        INPUTS / "provenance.json",
    )
    assert result["sources"][0]["original_path"] == historical_path
    if include_counts:
        assert result["sources"][0]["audit_comparison_counts"]["catalog_rows"] == historical_count
    else:
        assert result["sources"][0]["audit_comparison_counts"] == {}
    assert result["audit_v2_metadata"]["source_revision"] == audit["source_revision"]
    assert result["audit_v2_metadata"]["supersedes"] == audit["supersedes"]
    assert result["provenance_original"] == json.loads((INPUTS / "provenance.json").read_bytes())


def test_code_license_matches_repository_metadata_and_is_separate_from_csv_license(ledger):
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert ledger["code_license"] == metadata["project"]["license"]
    assert (
        (ROOT / "LICENSE")
        .read_text(encoding="utf-8")
        .startswith("# PolyForm Noncommercial License 1.0.0")
    )
    assert ledger["adapted_reference_data_license"] == "CC-BY-SA-4.0"


@pytest.mark.parametrize(
    "failure", ["oversized", "unsafe-row", "missing-source", "duplicate-source", "wrong-row-count"]
)
def test_audit_failure_is_bound_to_real_files_before_any_publication(tmp_path: Path, failure: str):
    path = tmp_path / "audit-v2.json"
    original = json.loads((INPUTS / "audit-v2.json").read_bytes())
    if failure == "oversized":
        path.write_bytes(b" " * (4 * 1024 * 1024 + 1))
    else:
        if failure == "unsafe-row":
            original["sources"][0]["comparison"]["matched"][0]["row"] = True
        elif failure == "missing-source":
            original["sources"] = []
        elif failure == "duplicate-source":
            original["sources"].append(original["sources"][0])
        else:
            original["sources"][0]["rows"] = 0
        path.write_text(json.dumps(original), encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(DataError if failure == "oversized" else ValueError):
        build_midi_csv_reconciliation(
            INPUTS / "Analog Four MKII.csv",
            INPUTS / "Analog Rytm MKII.csv",
            path,
            INPUTS / "provenance.json",
        )
    assert path.read_bytes() == before


def test_upstream_identity_disagreement_refuses_without_changing_sources(
    monkeypatch: pytest.MonkeyPatch,
):
    from rytm_randomizer.reports import midi_csv_reconciliation as report

    before = {path.name: path.read_bytes() for path in INPUTS.iterdir() if path.is_file()}
    monkeypatch.setattr(
        report, "MIDI_CSV_UPSTREAM_BLOBS", {"a4": "0" * 40, "rytm": MIDI_CSV_UPSTREAM_BLOBS["rytm"]}
    )
    with pytest.raises(ValueError, match="Git blob"):
        build_midi_csv_reconciliation(
            INPUTS / "Analog Four MKII.csv",
            INPUTS / "Analog Rytm MKII.csv",
            INPUTS / "audit-v2.json",
            INPUTS / "provenance.json",
        )
    assert {path.name: path.read_bytes() for path in INPUTS.iterdir() if path.is_file()} == before


@pytest.mark.parametrize(
    "failure",
    [
        "missing-csv",
        "corrupt-csv",
        "corrupt-audit",
        "corrupt-provenance",
        "provenance-license",
        "provenance-identity",
        "provenance-rows",
    ],
)
def test_on_disk_source_refusal_preserves_existing_ledger_outputs(tmp_path: Path, failure: str):
    inputs = tmp_path / "inputs"
    shutil.copytree(INPUTS, inputs)
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    originals = {
        "midi-csv-reconciliation.json": b"original json",
        "midi-csv-reconciliation.md": b"original markdown",
    }
    for name, value in originals.items():
        (outputs / name).write_bytes(value)
    if failure == "missing-csv":
        (inputs / "Analog Four MKII.csv").unlink()
    elif failure == "corrupt-csv":
        (inputs / "Analog Four MKII.csv").write_bytes(b"not the pinned CSV")
    elif failure in ("corrupt-audit", "corrupt-provenance"):
        name = "audit-v2.json" if failure == "corrupt-audit" else "provenance.json"
        (inputs / name).write_bytes(b"{broken")
    else:
        path = inputs / "provenance.json"
        provenance = json.loads(path.read_bytes())
        if failure == "provenance-license":
            provenance["license_reported_by_site"] = "unverified"
        elif failure == "provenance-identity":
            provenance["files"][0]["sha256"] = "a" * 64
        else:
            provenance["files"][0]["rows"] = 0
        path.write_text(json.dumps(provenance), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/reconcile_midi_csv.py"),
            "--input-dir",
            str(inputs),
            "--output-dir",
            str(outputs),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "unrecognized arguments" not in result.stderr
    with pytest.raises((ValueError, OSError, DataError)):
        build_midi_csv_reconciliation(
            inputs / "Analog Four MKII.csv",
            inputs / "Analog Rytm MKII.csv",
            inputs / "audit-v2.json",
            inputs / "provenance.json",
        )
    assert {path.name: path.read_bytes() for path in outputs.iterdir()} == originals


@pytest.fixture
def retained_reader_paths(tmp_path: Path) -> tuple[Path, Path]:
    inputs = tmp_path / "inputs"
    shutil.copytree(INPUTS, inputs)
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    (outputs / "midi-csv-reconciliation.json").write_bytes(b"retained ledger")
    (outputs / "midi-csv-reconciliation.md").write_bytes(b"retained summary")
    return inputs, outputs


def _retained_output_state(outputs: Path) -> dict[str, tuple[bytes, int]]:
    return {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in outputs.iterdir()}


@pytest.mark.parametrize(
    "filename, maximum",
    [
        ("Analog Four MKII.csv", 1024 * 1024),
        ("Analog Rytm MKII.csv", 1024 * 1024),
        ("audit-v2.json", 4 * 1024 * 1024),
        ("provenance.json", 4 * 1024 * 1024),
    ],
)
@pytest.mark.parametrize("failure", ["empty", "oversized", "nonregular"])
def test_shared_reader_refuses_unsafe_file_before_publication(
    retained_reader_paths: tuple[Path, Path], filename: str, maximum: int, failure: str
):
    inputs, outputs = retained_reader_paths
    target = inputs / filename
    if failure == "nonregular":
        target.unlink()
        target.mkdir()
        expected = "not a regular file"
    else:
        target.write_bytes(b"" if failure == "empty" else b"x" * (maximum + 1))
        expected = "size is outside the supported bound"
    before = _retained_output_state(outputs)
    original = target.read_bytes() if target.is_file() else None
    with pytest.raises(DataError, match=expected):
        reconcile_midi_csv_main(["--input-dir", str(inputs), "--output-dir", str(outputs)])
    assert _retained_output_state(outputs) == before
    if original is None:
        assert target.is_dir()
    else:
        assert target.read_bytes() == original


@pytest.mark.parametrize("filename", ["audit-v2.json", "provenance.json"])
@pytest.mark.parametrize("nested", [False, True])
def test_shared_json_decoder_rejects_duplicate_claims_before_publication(
    retained_reader_paths: tuple[Path, Path], filename: str, nested: bool
):
    inputs, outputs = retained_reader_paths
    target = inputs / filename
    raw = json.dumps(json.loads(target.read_bytes())).encode("utf-8")
    if nested:
        duplicate = raw.replace(b'"sha256": "', b'"sha256": "untrusted", "sha256": "', 1)
    else:
        key = b'"sources"' if filename == "audit-v2.json" else b'"files"'
        duplicate = b"{" + key + b": [], " + raw[1:]
    assert duplicate != raw
    assert json.loads(duplicate) == json.loads(raw)
    target.write_bytes(duplicate)
    before = _retained_output_state(outputs)
    with pytest.raises(ValueError, match="duplicate JSON object key"):
        reconcile_midi_csv_main(["--input-dir", str(inputs), "--output-dir", str(outputs)])
    assert target.read_bytes() == duplicate
    assert _retained_output_state(outputs) == before


@pytest.mark.parametrize(
    "filename", ["Analog Four MKII.csv", "Analog Rytm MKII.csv", "audit-v2.json", "provenance.json"]
)
def test_shared_reader_refuses_stale_bytes_before_publication(
    retained_reader_paths: tuple[Path, Path], filename: str, monkeypatch: pytest.MonkeyPatch
):
    inputs, outputs = retained_reader_paths
    target = inputs / filename
    original = target.read_bytes()
    identity = target.stat()
    before = _retained_output_state(outputs)
    native_fstat = artifact_reader.os.fstat
    changed = False

    def change_source_during_read(descriptor: int) -> os.stat_result:
        nonlocal changed
        opened = native_fstat(descriptor)
        if not changed and (opened.st_dev, opened.st_ino) == (identity.st_dev, identity.st_ino):
            changed = True
            target.write_bytes(original + b"\n")
        return opened

    monkeypatch.setattr(artifact_reader.os, "fstat", change_source_during_read)
    with pytest.raises(DataError, match="changed while it was read"):
        reconcile_midi_csv_main(["--input-dir", str(inputs), "--output-dir", str(outputs)])
    assert changed
    assert target.read_bytes() == original + b"\n"
    assert _retained_output_state(outputs) == before


def test_shared_reader_preserves_exact_regular_csv_at_maximum(tmp_path: Path):
    maximum = 1024 * 1024
    base = _csv_bytes(notes="")
    header, record = base.split(b"\r\n", 1)
    header += b"\r\n"
    row_count = 16
    padding, remainder = divmod(maximum - len(header) - row_count * len(record), row_count)
    # Keep each cell below csv's field-size limit while exercising the file cap.
    raw = header + b"".join(
        _csv_bytes(notes="x" * (padding + (index < remainder))).split(b"\r\n", 1)[1]
        for index in range(row_count)
    )
    assert len(raw) == maximum
    path = tmp_path / "bounded.csv"
    path.write_bytes(raw)
    spec = replace(MIDI_CSV_SOURCES[0], sha256=hashlib.sha256(raw).hexdigest(), row_count=row_count)
    source = read_midi_csv(path, spec)
    assert source.byte_count == maximum
    assert source.sha256 == spec.sha256
    assert (source.header_record + "".join(row.raw_record for row in source.rows)).encode(
        "utf-8"
    ) == raw
    assert path.read_bytes() == raw


@pytest.mark.parametrize("filename", ["audit-v2.json", "provenance.json"])
def test_shared_reader_preserves_regular_json_at_maximum(
    retained_reader_paths: tuple[Path, Path], filename: str
):
    inputs, outputs = retained_reader_paths
    path = inputs / filename
    original = path.read_bytes()
    raw = original + b" " * (4 * 1024 * 1024 - len(original))
    path.write_bytes(raw)
    before = _retained_output_state(outputs)
    result = build_midi_csv_reconciliation(
        inputs / MIDI_CSV_SOURCES[0].filename,
        inputs / MIDI_CSV_SOURCES[1].filename,
        inputs / "audit-v2.json",
        inputs / "provenance.json",
    )
    if filename == "audit-v2.json":
        assert result["audit_v2_metadata"]["sha256"] == hashlib.sha256(raw).hexdigest()
    else:
        assert result["audit_v2_metadata"]["provenance_sha256"] == hashlib.sha256(raw).hexdigest()
        assert result["provenance_original"] == json.loads(original)
    assert path.read_bytes() == raw
    assert _retained_output_state(outputs) == before


@pytest.mark.parametrize("current", [False, True])
def test_check_mode_never_rewrites_existing_outputs(tmp_path: Path, current: bool):
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    for name in ("midi-csv-reconciliation.json", "midi-csv-reconciliation.md"):
        (outputs / name).write_bytes(
            (ROOT / "docs/catalogs" / name).read_bytes() if current else b"stale-but-retained"
        )
    before = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in outputs.iterdir()}
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/reconcile_midi_csv.py"),
            "--output-dir",
            str(outputs),
            "--check",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == (0 if current else 1)
    assert {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in outputs.iterdir()
    } == before


def test_import_is_passive_when_hardware_libraries_are_trapped():
    code = """
import sys
class NoHardware:
    def find_spec(self, fullname, path=None, target=None):
        if fullname in ("mido", "rtmidi", "usb"):
            raise AssertionError("hardware library imported")
sys.meta_path.insert(0, NoHardware())
from pathlib import Path
from rytm_randomizer.reports.midi_csv_reconciliation import build_midi_csv_reconciliation
p = Path("tests/fixtures/midi_guide")
x = build_midi_csv_reconciliation(p / "Analog Four MKII.csv", p / "Analog Rytm MKII.csv", p / "audit-v2.json", p / "provenance.json")
assert len(x["entries"]) == 552 and not x["hardware_access"]
print("passive import")
"""
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "passive import"
