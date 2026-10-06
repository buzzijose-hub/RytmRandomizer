"""Catalog, native precision and physical evidence remain independent."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from rytm_randomizer.cli import main
from rytm_randomizer.cockpit.data.rytm_parameter_map import (
    cockpit_parameter_key,
    cockpit_parameter_live_blockers,
    cockpit_parameter_mapping,
)
from rytm_randomizer.data.analog_four_kit_fields import A4_TRACK_OFFSETS
from rytm_randomizer.data.analog_four_midi import (
    ANALOG_FOUR_MANUAL_CC,
    ANALOG_FOUR_SYNTH_TRACK_NRPN,
)
from rytm_randomizer.data.analog_four_sysex_calibration import (
    ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS,
    ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS,
)
from rytm_randomizer.data.analog_rytm_kit_layout import RYTM_SOUND_FIELD_BY_NRPN_LSB
from rytm_randomizer.data.analog_rytm_midi import (
    ANALOG_RYTM_MACHINE_SRC_BY_MACHINE,
    ANALOG_RYTM_MANUAL_CC,
    AnalogRytmCcMapping,
)
from rytm_randomizer.data.device_support_inventory import (
    DEVICE_SUPPORT_EVIDENCE,
    DEVICE_SUPPORT_EVIDENCE_FAMILIES,
)
from rytm_randomizer.devices import all_devices, register_device
from rytm_randomizer.devices.analog_rytm import AnalogRytmDevice
from rytm_randomizer.reports.device_support_inventory import (
    DeviceSupportInventory,
    DeviceSupportParameter,
    build_device_support_inventory,
    format_device_support_inventory,
)

pytestmark = pytest.mark.fast
ROOT = Path(__file__).resolve().parents[1]


def _rows(payload: DeviceSupportInventory) -> list[DeviceSupportParameter]:
    return payload["parameters"]


def test_inventory_uses_the_same_live_blockers_as_capture_and_planning() -> None:
    rows = _rows(build_device_support_inventory())
    for mapping in ANALOG_RYTM_MANUAL_CC.values():
        if mapping.machine_key is None:
            continue
        key = cockpit_parameter_key(mapping.machine_key, "SRC", mapping.parameter)
        assert key is not None
        expected = cockpit_parameter_live_blockers(mapping.machine_key, key)
        row = next(
            row
            for row in rows
            if row["device"] == "rytm"
            and row["surface"] == "midi_catalog"
            and row["machine"] == mapping.machine_key
            and row["field"] == mapping.parameter
        )
        assert row["blockers"] == expected
        assert row["live_send"] == ("blocked" if expected else "conditional_guarded_cc7")


@pytest.mark.parametrize("mapping", ANALOG_RYTM_MACHINE_SRC_BY_MACHINE["cy_ride"])
def test_inventory_marks_every_cy_ride_src_slot_blocked(mapping: AnalogRytmCcMapping) -> None:
    payload = build_device_support_inventory()
    row = next(
        row
        for row in payload["parameters"]
        if row["device"] == "rytm"
        and row["surface"] == "midi_catalog"
        and row["machine"] == "cy_ride"
        and row["field"] == mapping.parameter
    )
    assert row["live_send"] == "blocked"
    assert row["blockers"] == ("src_cy_ride_slot_unverified",)
    assert payload["hardware_validation_granted"] is False
    assert any(
        item["category"] == "cy_ride_source_slots" for item in payload["unsupported_categories"]
    )


def test_fallback_src_audit_matches_exact_canonical_native_and_policy_facts() -> None:
    document = (ROOT / "docs" / "RYTM_MAPPING_STATUS.md").read_text(encoding="utf-8")
    _, begin, tail = document.partition("<!-- fallback-src-audit -->")
    table, end, _ = tail.partition("<!-- /fallback-src-audit -->")
    assert begin and end
    cells = [
        tuple(cell.strip().strip("`") for cell in line.split("|")[1:-1])
        for line in table.splitlines()
        if line.startswith("| `src_")
    ]
    assert len(cells) == 29 and len({row[0] for row in cells}) == 29
    inventory = build_device_support_inventory()
    report_rows = {
        (row["machine"], row["field"]): row
        for row in inventory["parameters"]
        if row["device"] == "rytm" and row["surface"] == "midi_catalog"
    }
    src_bindings = {
        (machine, cockpit_parameter_key(machine, row.section, row.parameter)): row
        for machine, mappings in ANALOG_RYTM_MACHINE_SRC_BY_MACHINE.items()
        for row in mappings
    }
    assert len(src_bindings) == 224 and all(key is not None for _, key in src_bindings)
    src_rows = {key: row for (_, key), row in src_bindings.items() if key.startswith("src_")}
    assert len(src_rows) == 68
    eligible = {
        key
        for key, row in src_rows.items()
        if key.startswith("src_") and not cockpit_parameter_live_blockers(row.machine_key, key)
    }
    audited_eligible: set[str] = set()
    audited_blocked: set[str] = set()
    for key, name, cc, nrpn, native, evidence, policy in cells:
        mapping = src_rows[key]
        assert cockpit_parameter_mapping(mapping.machine_key, key) is mapping
        assert (name, int(cc), nrpn) == (
            mapping.parameter,
            mapping.cc_msb,
            f"{mapping.nrpn_msb}:{mapping.nrpn_lsb}",
        )
        assert mapping.mutation_status == "documented_only"
        assert mapping.value_kind == "continuous" and mapping.value_orientation == "zero_based"
        assert (mapping.value_min, mapping.value_max, mapping.cc_lsb) == (0, 127, None)
        offset = RYTM_SOUND_FIELD_BY_NRPN_LSB[mapping.nrpn_lsb].sound_offset
        assert int(native, 16) == offset
        report = report_rows[(mapping.machine_key, name)]
        assert report["locations"] == (offset,)
        assert report["protection"] == "documented_only"
        assert report["evidence"] == DEVICE_SUPPORT_EVIDENCE["rytm_midi"]
        assert all((ROOT / path).is_file() for path in report["evidence"])
        fixture_class = (
            "I"
            if mapping.machine_key in {"cy_classic", "cb_classic"}
            else "R" if mapping.machine_key in {"cy_ride", "cb_metallic"} else "T"
        )
        assert evidence == f"C/S/{fixture_class}"
        if policy == "documented-only eligible":
            assert report["live_send"] == "conditional_guarded_cc7" and not report["blockers"]
            audited_eligible.add(key)
        else:
            assert policy == "src_cy_ride_slot_unverified"
            assert report["live_send"] == "blocked" and report["blockers"] == (policy,)
            audited_blocked.add(key)
    assert audited_eligible == eligible and len(eligible) == 25
    assert audited_blocked == {"src_cy_ride_2", "src_cy_ride_5", "src_cy_ride_6", "src_cy_ride_7"}
    assert (
        inventory["hardware_access"] is False and inventory["hardware_validation_granted"] is False
    )


def _native(field: str) -> DeviceSupportParameter:
    return next(
        row
        for row in _rows(build_device_support_inventory())
        if row["device"] == "a4"
        and row["surface"] == "native_saved_sound"
        and row["field"] == field
    )


def test_inventory_is_reproducible_and_complete_against_catalogs() -> None:
    first = build_device_support_inventory()
    assert json.dumps(first, sort_keys=True) == json.dumps(
        build_device_support_inventory(), sort_keys=True
    )
    rows = _rows(first)
    native = [
        row for row in rows if row["device"] == "a4" and row["surface"] == "native_saved_sound"
    ]
    assert {row["field"] for row in native} == set(A4_TRACK_OFFSETS)
    assert len(
        [row for row in rows if row["device"] == "rytm" and row["surface"] == "midi_catalog"]
    ) == len(ANALOG_RYTM_MANUAL_CC)
    a4 = {**ANALOG_FOUR_MANUAL_CC, **ANALOG_FOUR_SYNTH_TRACK_NRPN}
    assert {
        row["field"] for row in rows if row["device"] == "a4" and row["surface"] == "midi_catalog"
    } == set(a4)
    assert first["hardware_access"] is False
    assert first["hardware_validation_granted"] is False
    for paths in DEVICE_SUPPORT_EVIDENCE.values():
        assert all((ROOT / path).is_file() for path in paths)


def test_inventory_device_set_equals_canonical_registry() -> None:
    payload = build_device_support_inventory()
    summaries = payload["registered_devices"]
    assert set(summaries) == set(all_devices())
    assert tuple(summaries) == tuple(sorted(all_devices()))
    for device_id, device in all_devices().items():
        summary = summaries[device_id]
        family = DEVICE_SUPPORT_EVIDENCE_FAMILIES.get(device_id)
        assert summary["display_name"] == device.display_name
        assert summary["track_count"] == device.track_count
        assert summary["evidence_family"] == family
        assert summary["evidence_row_count"] == sum(
            row["device"] == family for row in payload["parameters"]
        )
        assert device_id in "\n".join(format_device_support_inventory())


def test_future_registered_device_is_explicitly_without_support_evidence(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import rytm_randomizer.devices.registry as registry

    # Isolate the canonical backing store, then use its actual registration API.
    monkeypatch.setattr(registry, "_DEVICES", dict(all_devices()))
    baseline_counts = build_device_support_inventory()["counts"]
    future = AnalogRytmDevice()
    future.device_id = "future_registered_device"
    future.display_name = "Registered device without inventory evidence"
    register_device(future)

    payload = build_device_support_inventory()
    assert set(payload["registered_devices"]) == set(all_devices())
    assert payload["registered_devices"][future.device_id] == {
        "display_name": future.display_name,
        "track_count": future.track_count,
        "evidence_family": None,
        "evidence_row_count": 0,
        "evidence_status": "no_support_evidence",
    }
    assert payload["counts"] == baseline_counts
    assert payload["hardware_access"] is False
    assert payload["hardware_validation_granted"] is False
    assert all(row["device"] != future.device_id for row in payload["parameters"])
    assert any(
        future.device_id in line and "no_support_evidence; 0 evidence rows" in line
        for line in format_device_support_inventory()
    )
    assert main(["device-support-inventory-report", "--json"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert set(cli_payload["registered_devices"]) == set(all_devices())
    assert cli_payload["registered_devices"][future.device_id]["evidence_status"] == (
        "no_support_evidence"
    )


def test_exact_native_fractional_domains_do_not_grant_midi_conversion() -> None:
    frequency = _native("filter1_frequency")
    assert frequency["encoding"] == "unsigned_big_endian_q8.8"
    assert frequency["maximum"] == "127.99609375"
    assert frequency["step"] == "0.00390625"
    assert len(frequency["locations"]) == 2
    depth = _native("env2_depth_a")
    assert depth["minimum"] == "-128.0"
    assert depth["maximum"] == "127.9921875"
    assert depth["step"] == "0.0078125"
    assert _native("env2_depth_a_fraction")["offline_mutation"] == "not_independent; use_mod_depths"
    assert _native("osc1_fine")["domain_authority"] == "display_buckets_preserve_hidden_half_step"
    assert _native("osc1_tune")["step"] == "0.00390625"
    assert all(row["live_send"] == "blocked" for row in (frequency, depth))


def test_studio_native_policy_inventory_matches_public_optional_capability() -> None:
    from rytm_randomizer.devices import get_analog_four_native_field_capability

    metadata = get_analog_four_native_field_capability().native_fields()
    rows = build_device_support_inventory()["a4_studio_native_fields"]
    assert len(rows) == len(metadata) == 106
    assert sum(field.mutation_supported for field in metadata) == 72
    for row, field in zip(rows, metadata, strict=True):
        assert row["parameter"] == field.parameter
        assert row["relative_offsets"] == field.relative_offsets
        assert row["native_encoding"] == field.native_encoding.value
        assert row["legal_codes"] == field.enum_values
        assert row["protection_reason"] == field.protection_reason
        assert row["live_send"] == "blocked"
        assert row["evidence"] == field.evidence
    by_key = {row["parameter"]: row for row in rows}
    assert by_key["filter1_frequency"]["maximum_native"] == 32512
    assert by_key["osc1_tune"]["minimum_native"] is None
    assert by_key["osc1_fine"]["offline_mutation"] == "read_only"
    assert by_key["amp_decay"]["protection_reason"] == "oxi_amp_protection"
    assert by_key["lfo1_phase"]["protection_reason"] == "native_nondefault_evidence_missing"


def test_selectors_are_canonical_choices_not_all_raw_integers() -> None:
    wave = _native("osc1_waveform")
    values = wave["legal_values"]
    assert values == (
        (0, "SAW"),
        (1, "TRP"),
        (2, "PULSE"),
        (3, "TRIANGLE"),
        (4, "INPUT_LEFT"),
        (5, "INPUT_RIGHT"),
        (6, "FEEDBACK_OR_NEIGHBOR"),
        (7, "OFF"),
    )
    assert _native("envf_destination_a")["legal_values"]
    assert _native("osc1_detune")["minimum"] == "-64"
    assert (
        _native("osc1_level")["domain_authority"]
        == "codec_storage_range_not_complete_display_domain"
    )


def test_live_support_protection_and_unimplemented_paths_are_distinct() -> None:
    payload = build_device_support_inventory()
    rows = _rows(payload)
    lfo = next(row for row in rows if row["device"] == "rytm" and row["field"] == "LFO Depth")
    assert lfo["live_send"] == "blocked"
    assert "paired_control_precision_unverified" in lfo["blockers"]
    decay = next(
        row
        for row in rows
        if row["device"] == "rytm" and row["machine"] == "bd_classic" and row["field"] == "Decay"
    )
    assert decay["live_send"] == "conditional_guarded_cc7"
    assert decay["recovery"] == "manual_saved_kit_reload_and_fresh_capture; local_history_only"
    assert decay["offline_mutation"] == "not_inferred_from_MIDI_catalog"
    omissions = payload["unsupported_categories"]
    assert {item["kind"] for item in omissions} >= {
        "intentional_protection",
        "missing_semantic_mapping",
        "hardware_evidence_missing",
    }
    assert payload["rytm_machine_layout_gaps"]
    assert payload["rytm_machine_compatibility"]


def test_codec_accessor_does_not_imply_a_recipe_binding() -> None:
    note = next(
        row
        for row in _rows(build_device_support_inventory())
        if row["device"] == "rytm" and row["field"] == "default_note"
    )
    assert note["offline_mutation"] == "codec_accessor_only"
    assert "no_typed_recipe_binding" in note["blockers"]


def test_typed_inventory_projection_preserves_canonical_address_and_evidence_records() -> None:
    payload = build_device_support_inventory()
    a4_mappings = {**ANALOG_FOUR_MANUAL_CC, **ANALOG_FOUR_SYNTH_TRACK_NRPN}
    assert payload["midi_addresses"]["a4"] == [asdict(mapping) for mapping in a4_mappings.values()]
    assert payload["midi_addresses"]["rytm"] == [
        asdict(mapping) for mapping in ANALOG_RYTM_MANUAL_CC.values()
    ]
    for projected, source in zip(
        payload["a4_field_calibrations"], ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS.values(), strict=True
    ):
        assert projected["parameter"] == source.parameter
        assert projected["status"] == source.status
        assert projected["native_field"] == source.native_field
        assert projected["native_encoding"] == source.native_encoding
        assert projected["native_width"] == source.native_width
        assert projected["native_scale"] == source.native_scale
        assert projected["display_bounds"] == [source.screen_min, source.screen_max]
        assert projected["captures"] == [asdict(item) for item in source.evidence]
        assert projected["write_validations"] == [
            asdict(item) for item in ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS.get(source.parameter, ())
        ]


def test_cli_text_json_and_invalid_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["device-support-inventory-report", "--help"]) == 0
    assert "Storage bounds" in capsys.readouterr().out
    assert main(["device-support-inventory-report"]) == 0
    output = capsys.readouterr().out
    assert "no MIDI/USB access" in output
    assert "Source: rytm_randomizer.reports.device_support_inventory" in output
    assert format_device_support_inventory()
    assert main(["device-support-inventory-report", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["hardware_validation_granted"] is False
    assert main(["device-support-inventory-report", "--arm"]) != 0
    assert "accepts only optional --json" in capsys.readouterr().err


def test_passive_inventory_cannot_import_hardware_provider() -> None:
    script = """
import importlib.abc, json, sys
class RefuseHardware(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {'mido', 'rtmidi', 'rytm_randomizer.mido_provider', 'rytm_randomizer.app'}:
            raise AssertionError('hardware boundary imported: ' + fullname)
sys.meta_path.insert(0, RefuseHardware())
from rytm_randomizer.cli import main
raise SystemExit(main(['device-support-inventory-report', '--json']))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["hardware_access"] is False
