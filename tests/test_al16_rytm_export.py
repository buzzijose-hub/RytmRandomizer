from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from pytest import MonkeyPatch

from rytm_randomizer.data.al16_rytm import AL16_BANK_STATES, AL16_PAD_ROLES
from rytm_randomizer.data.analog_rytm_kit_layout import (
    RYTM_KIT_RAW_SIZE,
    RYTM_SOUND_MACHINE_TYPE_OFFSET,
)
from rytm_randomizer.data.rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES,
    is_machine_allowed_on_pad,
)
from rytm_randomizer.devices.strategies import al16_rytm_export as exporter
from rytm_randomizer.devices.strategies.al16_rytm_export import (
    build_al16_rytm_kit,
    deterministic_recipe_identifier,
)
from rytm_randomizer.devices.strategies.analog_rytm_saved_kit_codec import (
    encode_analog_rytm_saved_kit_frame,
)

pytestmark = pytest.mark.fast

_HEADER = bytes((0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, 0x00))
_REPO_ROOT = Path(__file__).resolve().parents[1]
_AL02_RECIPE = _REPO_ROOT / "specs" / "al16" / "AL02_LOCK_RYTM.yaml"


def _recipe() -> dict[str, object]:
    parsed = cast(object, json.loads(_AL02_RECIPE.read_text(encoding="utf-8")))
    assert isinstance(parsed, dict)
    return cast(dict[str, object], parsed)


def _synthetic_reference(path: Path) -> bytes:
    reference = encode_analog_rytm_saved_kit_frame(_HEADER, bytes(RYTM_KIT_RAW_SIZE))
    path.write_bytes(reference)
    return reference


def test_al16_bank_reserves_exact_operating_states_and_roles() -> None:
    assert [state.name for state in AL16_BANK_STATES] == [
        "AIRLOCK",
        "LOCK",
        "ROTATION",
        "PRESSURE",
        "ORBIT",
        "OFFSET",
        "SURGE",
        "CROSSING",
        "COMPRESSION",
        "RITUAL",
        "APEX",
        "VACUUM",
        "REENTRY",
        "TERMINAL",
        "FRACTURE",
        "SHUTDOWN",
    ]
    assert AL16_PAD_ROLES[1] == "Main kick"
    assert AL16_PAD_ROLES[9] == "Closed-hat clock"
    assert AL16_PAD_ROLES[12] == "Cowbell / metallic punctuation / alarm tone"


def test_al02_recipe_identifier_is_deterministic() -> None:
    recipe = _recipe()

    assert deterministic_recipe_identifier(recipe) == deterministic_recipe_identifier(recipe)


def test_al02_build_fails_closed_and_writes_precise_reports(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    reference = _synthetic_reference(reference_path)
    output_path = tmp_path / "output" / "AL02_LOCK_RYTM.syx"

    result = build_al16_rytm_kit(
        reference_path=reference_path,
        recipe_path=_AL02_RECIPE,
        destination_slot=127,
        output_path=output_path,
    )

    assert result.status == "blocked"
    assert not output_path.exists()
    assert reference_path.read_bytes() == reference
    assert result.manifest_path.is_file()
    assert result.validation_path.is_file()
    assert result.byte_diff_path.is_file()

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["build_status"] == "blocked"
    assert manifest["destination_slot"] == 127
    assert manifest["kit_name"] == "AL02 LOCK"
    assert manifest["preserved_tracks"] == [2, 4, 5, 7, 8, 10, 11, 12]
    assert manifest["reference_round_trip_byte_identical"] is True
    assert manifest["changed_semantic_fields"] == []
    assert manifest["semantic_field_audits"]
    assert manifest["intentionally_changed_raw_bytes"] == 0
    assert manifest["output_emitted"] is False
    assert manifest["unknown_and_reserved_bytes_unchanged"] is True
    assert manifest["manual_hardware_import_authorized"] is False
    assert manifest["midi_ports_enumerated"] == 0
    assert manifest["midi_ports_opened"] == 0
    assert manifest["midi_messages_sent"] == 0
    gap_paths = {gap["semantic_path"] for gap in manifest["critical_mapping_gaps"]}
    assert "destination_slot" in gap_paths
    assert "tracks.1.machine" in gap_paths
    assert "tracks.6.source.target_note" in gap_paths
    assert "tracks.9.machine" in gap_paths
    assert "tracks.1.amp.vol" in gap_paths
    validation = result.validation_path.read_text(encoding="utf-8")
    assert "BLOCKED: no SysEx was emitted" in validation
    assert "MIDI ports opened: 0" in validation
    assert "Manual hardware import authorized: no" in validation
    assert "CH BASIC" in validation
    assert "CH Classic or HH Basic" in validation
    assert "intentionally changed raw bytes: 0" in result.byte_diff_path.read_text(encoding="utf-8")


def test_offline_exporter_has_no_midi_backend_dependency() -> None:
    source = (
        _REPO_ROOT / "rytm_randomizer" / "devices" / "strategies" / "al16_rytm_export.py"
    ).read_text(encoding="utf-8")

    assert "import mido" not in source
    assert "import rtmidi" not in source
    assert "MidoMidiPortProvider" not in source


def test_al16_value_readers_and_converters_fail_closed() -> None:
    for value in ([], {1: "value"}):
        with pytest.raises(ValueError, match="string keys"):
            exporter._as_mapping(value, "test")
    for value in ("", 1):
        with pytest.raises(ValueError, match="non-empty string"):
            exporter._as_string(value, "test")
    for value in (True, "1"):
        with pytest.raises(ValueError, match="must be an integer"):
            exporter._as_int(value, "test")

    assert exporter._convert_supported_value("verified_7bit", 127) == (127, 127)
    with pytest.raises(ValueError, match="0..127"):
        exporter._convert_supported_value("verified_7bit", 128)
    assert exporter._convert_supported_value("centered_7bit", "neutral") == (0, 64)
    assert exporter._convert_supported_value("centered_7bit", "center") == (0, 64)
    assert exporter._convert_supported_value("centered_7bit", -64) == (-64, 0)
    with pytest.raises(ValueError, match="-64..63"):
        exporter._convert_supported_value("centered_7bit", 64)
    assert exporter._convert_supported_value("filter_type_enum", "hp2") == ("HP2", 4)
    with pytest.raises(ValueError, match="unsupported filter type"):
        exporter._convert_supported_value("filter_type_enum", "unknown")
    with pytest.raises(ValueError, match="unknown AL16 converter"):
        exporter._convert_supported_value("missing", 0)


def test_al16_original_semantic_and_machine_labels_are_explicit() -> None:
    assert exporter._original_semantic("centered_7bit", 0) == -64
    assert exporter._original_semantic("filter_type_enum", 4) == "HP2"
    assert exporter._original_semantic("filter_type_enum", 127) == "unknown filter type 127"
    assert exporter._original_semantic("verified_7bit", 129) == 1
    assert exporter._machine_label_for_raw(RYTM_MACHINE_PROFILES[0].machine_value) == (
        RYTM_MACHINE_PROFILES[0].label
    )
    assert exporter._machine_label_for_raw(0x7F).startswith("unknown machine value")


def test_al16_machine_validation_covers_preserve_and_wrong_pad() -> None:
    raw = bytearray(RYTM_KIT_RAW_SIZE)
    allowed = next(
        profile for profile in RYTM_MACHINE_PROFILES if is_machine_allowed_on_pad(1, profile.key)
    )
    machine_offset = exporter._track_offset(1, RYTM_SOUND_MACHINE_TYPE_OFFSET)
    raw[machine_offset] = allowed.machine_value
    audits: list[exporter.FieldAudit] = []
    gaps: list[exporter.MappingGap] = []

    assert exporter._record_machine(raw, 1, {"machine": allowed.key}, audits, gaps) == allowed.key
    assert audits[-1].verification_status == "verified_preserved_machine"
    assert not gaps

    disallowed_pad, disallowed = next(
        (pad, profile)
        for pad in range(1, 13)
        for profile in RYTM_MACHINE_PROFILES
        if not is_machine_allowed_on_pad(pad, profile.key)
    )
    assert (
        exporter._record_machine(
            raw,
            disallowed_pad,
            {"machine": disallowed.key},
            audits,
            gaps,
        )
        == disallowed.key
    )
    assert audits[-1].verification_status == "invalid_machine_for_pad"


def test_al16_tuning_resolution_requires_an_approved_machine_table(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(exporter, "AL16_RYTM_APPROVED_TUNING", {("xt_classic", "F2"): 42})
    audits: list[exporter.FieldAudit] = []
    gaps: list[exporter.MappingGap] = []

    exporter._record_source_fields(6, "xt_classic", {"target_note": "f2"}, audits, gaps)

    assert audits == [
        exporter.FieldAudit(
            semantic_path="tracks.6.source.target_note",
            original_semantic_value=None,
            requested_semantic_value="F2",
            normalized_semantic_value="F2",
            encoded_raw_value_or_bytes=[42],
            raw_location=None,
            converter_or_enumeration="approved_tuning_table:xt_classic",
            verification_status="resolved_tuning_pending_source_writer",
        )
    ]
    assert not gaps


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda recipe: recipe.update(project_id="OTHER"), "project_id must be AL16"),
        (
            lambda recipe: cast(dict[str, object], recipe["kit"]).update(name="X" * 17),
            "16-byte ASCII",
        ),
        (lambda recipe: cast(dict[str, object], recipe["tracks"]).pop("12"), "pads 1..12"),
        (
            lambda recipe: cast(
                dict[str, object], cast(dict[str, object], recipe["tracks"])["1"]
            ).update(role="Wrong role"),
            "permanent AL16 pad role",
        ),
        (
            lambda recipe: cast(
                dict[str, object], cast(dict[str, object], recipe["tracks"])["1"]
            ).update(mode="other"),
            "must be patch or preserve",
        ),
    ],
)
def test_al16_recipe_validation_rejects_invalid_contracts(
    mutate: object,
    message: str,
) -> None:
    recipe = _recipe()
    apply_mutation = mutate
    assert callable(apply_mutation)
    apply_mutation(recipe)

    with pytest.raises(ValueError, match=message):
        exporter._inspect_recipe(recipe, bytes(RYTM_KIT_RAW_SIZE), 127)


def test_al16_recipe_validation_rejects_invalid_destination_slot() -> None:
    with pytest.raises(ValueError, match="destination slot"):
        exporter._inspect_recipe(_recipe(), bytes(RYTM_KIT_RAW_SIZE), 128)


def test_al16_build_refuses_round_trip_drift_and_stale_output(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    _synthetic_reference(reference_path)
    output_path = tmp_path / "AL02_LOCK_RYTM.syx"
    original_encoder = exporter.encode_analog_rytm_saved_kit_frame
    monkeypatch.setattr(
        exporter,
        "encode_analog_rytm_saved_kit_frame",
        lambda header, unpacked: original_encoder(header, unpacked)[:-1] + b"\x00",
    )
    with pytest.raises(ValueError, match="not byte-identical"):
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=output_path,
        )

    monkeypatch.setattr(exporter, "encode_analog_rytm_saved_kit_frame", original_encoder)
    output_path.write_bytes(b"stale")
    with pytest.raises(FileExistsError, match="potentially stale output"):
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=output_path,
        )


def test_al16_build_timestamp_supports_reproducible_and_live_modes(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    assert exporter._build_timestamp() == "1970-01-01T00:00:00+00:00"
    monkeypatch.delenv("SOURCE_DATE_EPOCH")
    assert exporter._build_timestamp().endswith("+00:00")
