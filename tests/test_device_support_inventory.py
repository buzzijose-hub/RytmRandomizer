"""Catalog, native precision and physical evidence remain independent."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from rytm_randomizer.cli import main
from rytm_randomizer.data.analog_four_kit_fields import A4_TRACK_OFFSETS
from rytm_randomizer.data.analog_four_midi import (
    ANALOG_FOUR_MANUAL_CC,
    ANALOG_FOUR_SYNTH_TRACK_NRPN,
)
from rytm_randomizer.data.analog_four_sysex_calibration import (
    ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS,
    ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS,
)
from rytm_randomizer.data.analog_rytm_midi import ANALOG_RYTM_MANUAL_CC
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
