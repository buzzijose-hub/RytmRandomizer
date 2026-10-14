"""Full retained reference reconciliation stays address-based and hardware inert."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from rytm_randomizer.data.midi_csv_reconciliation import (
    MIDI_CSV_COLUMNS,
    MIDI_CSV_SOURCES,
    MIDI_CSV_UPSTREAM_BLOBS,
)
from rytm_randomizer.reports.device_support_inventory import build_device_support_inventory
from rytm_randomizer.reports.midi_csv_matcher import canonical_midi_rows, match_midi_csv_row
from rytm_randomizer.reports.midi_csv_reconciliation import (
    build_midi_csv_reconciliation,
    format_midi_csv_gap_summary,
    serialize_midi_csv_ledger,
)
from rytm_randomizer.reports.midi_csv_source import (
    MidiCsvRow,
    csv_row_issues,
    parse_csv_choices,
    parse_midi_csv,
    parse_optional_number,
    read_midi_csv,
)

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
