"""Export/import contracts at public bounds, strict shared parsing, and inert scope."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data.show_bank import (
    SHOW_BANK_ID_MAX_LENGTH,
    SHOW_BANK_REVISION_MAX,
    SHOW_KIT_BLOCKED_REASON_VALUES,
    SHOW_KIT_DEVICE_ID_VALUES,
    SHOW_PACK_ID_MAX_LENGTH,
    ShowKitScope,
    validate_show_bank_id,
    validate_show_pack_id,
)
from rytm_randomizer.cockpit.data.stage import STAGE_DEVICE_IDS
from rytm_randomizer.cockpit.show_bank.export import ShowPackService
from rytm_randomizer.cockpit.show_bank.readiness import (
    is_catalog_only_show_bank,
    show_bank_readiness,
)
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.cockpit.stage.policy import stage_lane_policy
from rytm_randomizer.cockpit.ws.result import HandlerResult
from rytm_randomizer.devices import get_device
from rytm_randomizer.guardrails.input_validation import (
    canonical_json_bytes,
    require_boolean,
    require_exact_keys,
    require_float,
    require_int,
    require_integer_tuple,
    require_object,
    require_recipe_bool,
    require_sequence,
    require_text,
    require_text_tuple,
)
from rytm_randomizer.snapshot.mutation_scope import registered_mutation_ids

from .conftest import build_show_bank_harness, generate_show_bank_candidates

pytestmark = pytest.mark.fast


@pytest.mark.parametrize("explicit_package_id", [False, True])
def test_maximum_bank_revision_and_package_ids_roundtrip_without_output(
    tmp_path: Path,
    explicit_package_id: bool,
) -> None:
    harness = build_show_bank_harness(tmp_path / "source")
    bank = replace(
        harness.workspace.bank(harness.bank_id),
        bank_id="b" * SHOW_BANK_ID_MAX_LENGTH,
        revision=SHOW_BANK_REVISION_MAX,
    )
    harness.store.save(bank)
    package_id = "p" * SHOW_PACK_ID_MAX_LENGTH if explicit_package_id else None
    exporting = ShowPackService(tmp_path / "packs", store=harness.store, clock=harness.clock)
    exported = exporting.export(bank, package_id=package_id)
    assert exported.package_id == (package_id or f"{bank.bank_id}-r99999999")
    manifest_bytes = (exported.package_dir / "manifest.json").read_bytes()
    verified = exporting.verify(exported.package_id)
    assert verified.bank == bank
    target = ShowBankStore(tmp_path / "target", clock=harness.clock)
    importer = ShowPackService(tmp_path / "packs", store=target, clock=harness.clock)
    imported = importer.import_into_store(exported.package_id)
    assert imported.bank.revision == 0
    assert imported.bank.bank_id == bank.bank_id
    assert target.load(bank.bank_id) == imported.bank
    assert is_catalog_only_show_bank(imported.bank)
    assert imported.bank.entries[0].selected_candidate_id is None
    assert imported.bank.entries[0].show_ready_at is None
    assert (exported.package_dir / "manifest.json").read_bytes() == manifest_bytes
    for artifact in imported.bank.sysex_artifacts():
        assert artifact.retained is not None
        assert (
            target.read_retained(artifact.retained)
            == verified.frames_by_artifact_id[artifact.artifact_id]
        )
    with pytest.raises(FileExistsError, match="namespace already exists"):
        importer.import_into_store(exported.package_id)


def test_package_bound_is_distinct_from_every_bank_entity_id() -> None:
    validate_show_bank_id("b" * SHOW_BANK_ID_MAX_LENGTH)
    validate_show_pack_id("p" * SHOW_PACK_ID_MAX_LENGTH)
    with pytest.raises(ValueError, match="at most 64"):
        validate_show_bank_id("b" * (SHOW_BANK_ID_MAX_LENGTH + 1))
    with pytest.raises(ValueError, match="at most 96"):
        validate_show_pack_id("p" * (SHOW_PACK_ID_MAX_LENGTH + 1))
    for unsafe in ("", "../bank", "bank/child", "Upper"):
        with pytest.raises(ValueError, match="filename-safe"):
            validate_show_pack_id(unsafe)


def test_device_vocabulary_and_scope_are_the_registered_stage_domain() -> None:
    assert SHOW_KIT_DEVICE_ID_VALUES is STAGE_DEVICE_IDS
    for device_id in STAGE_DEVICE_IDS:
        expected = frozenset(range(1, get_device(device_id).track_count + 1))
        assert registered_mutation_ids(device_id) == expected
        assert stage_lane_policy(device_id).available_ids == expected
        assert ShowKitScope(device_id).effective_ids == tuple(sorted(expected))
        with pytest.raises(ValueError, match="ids are unavailable"):
            ShowKitScope(device_id, target_ids=(max(expected) + 1,))
        with pytest.raises(ValueError, match="positive integer"):
            ShowKitScope(device_id, target_ids=(True,))


def test_readiness_tokens_do_not_interpolate_operator_identifiers(tmp_path: Path) -> None:
    harness = build_show_bank_harness(tmp_path)
    bank = harness.workspace.bank(harness.bank_id)
    cue = replace(bank.entries[0], entry_id="operator-chosen-identifier")
    bank = replace(bank, entries=(cue, replace(cue, entry_id="another-cue", cue_index=2)))
    result = show_bank_readiness(bank)
    assert result.blocked_reasons == ("cue_not_show_ready",)
    projection = harness.workspace.state_dict()["banks"][0]
    all_reasons = (
        projection["readiness"]["blocked_reasons"]
        + projection["entries"][0]["readiness"]["blocked_reasons"]
    )
    assert all(reason in SHOW_KIT_BLOCKED_REASON_VALUES for reason in all_reasons)
    assert projection["entries"][0]["readiness"]["blocked_reasons"] == ["paired_candidate_missing"]


@pytest.mark.parametrize("error_type", [TypeError, ValueError])
def test_shared_primitives_preserve_boundary_exception_types(error_type: type[Exception]) -> None:
    for value in (True, 1.0, "1", None):
        with pytest.raises(error_type, match="must be an integer"):
            require_int(value, "count", error_type)
    with pytest.raises(error_type, match="must be numeric"):
        require_float(True, "depth", error_type)
    with pytest.raises(error_type, match="must be a string"):
        require_text(3, "name", error_type)
    with pytest.raises(error_type, match="must be a boolean"):
        require_boolean(1, "confirmed", error_type)
    with pytest.raises(error_type, match="must be an object"):
        require_object([], "entry", error_type)
    with pytest.raises(error_type, match="keys must be strings"):
        require_object({1: "bad"}, "entry", error_type)
    with pytest.raises(error_type, match="must be an array"):
        require_sequence("abc", "entries", error_type)
    with pytest.raises(error_type, match="must be an array"):
        require_sequence((1,), "entries", error_type, kind="list")
    with pytest.raises(error_type, match="must be an array"):
        require_sequence(range(3), "entries", error_type, kind="array")
    assert require_sequence(range(3), "recipe", error_type) == range(3)
    assert require_sequence([1], "entries", error_type, kind="list") == [1]
    assert require_sequence((1,), "entries", error_type, kind="array") == (1,)
    assert require_text_tuple(["entry"], "entries", error_type) == ("entry",)
    assert require_integer_tuple([1], "ids", error_type) == (1,)
    assert require_boolean(True, "confirmed", error_type)
    assert require_recipe_bool(False, "enabled", error_type) == 0
    assert require_object({"name": "ok"}, "entry", error_type) == {"name": "ok"}
    assert require_float(0.25, "depth", error_type) == 0.25


def test_schema_key_and_json_encoding_contracts() -> None:
    require_exact_keys({"a": 1}, frozenset({"a"}), "schema")
    for actual, message in (
        ({}, "missing"),
        ({"a": 1, "b": 2}, "unknown"),
        ({"b": 1}, "missing.*unknown"),
    ):
        with pytest.raises(ValueError, match=message):
            require_exact_keys(actual, frozenset({"a"}), "schema")
    assert canonical_json_bytes({"z": "é", "a": 1}) == '{"a":1,"z":"é"}\n'.encode()
    with pytest.raises(ValueError, match="Out of range float"):
        canonical_json_bytes({"x": float("nan")})


def test_handler_result_fields_are_frozen_but_events_can_be_accumulated() -> None:
    result = HandlerResult(ack={"ok": True})
    result.events.append({"type": "show_bank_changed"})
    assert result.events == [{"type": "show_bank_changed"}]
    with pytest.raises(FrozenInstanceError, match="cannot assign"):
        result.ack = {"ok": False}  # type: ignore[misc]


def test_a4_semantic_mismatch_has_closed_entry_and_bank_tokens(tmp_path: Path) -> None:
    harness = build_show_bank_harness(tmp_path)
    (candidate,) = generate_show_bank_candidates(harness, count=1)
    workspace = harness.workspace
    workspace.mark_favorite(
        harness.bank_id,
        harness.entry_id,
        candidate.candidate_id,
        workspace.bank(harness.bank_id).revision,
    )
    for device_id in STAGE_DEVICE_IDS:
        workspace.attest_saved(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            device_id=device_id,
            hardware_slot=64,
        )
    harness.clock.current += timedelta(minutes=2)
    captures = {
        device: replace(capture, captured_at=harness.clock.current - timedelta(minutes=1))
        for device, capture in harness.captures.items()
    }
    from conftest import analog_four_saved_kit_frame
    from rytm_randomizer.cockpit.capture import decode_kit_capture_frame
    from rytm_randomizer.cockpit.data.stage import ANALOG_FOUR_DEVICE_ID
    from rytm_randomizer.data.analog_four_sysex_calibration import analog_four_sysex_calibration_for

    value = candidate.analog_four_candidate.values[0]
    calibration = analog_four_sysex_calibration_for(value.parameter)
    different_raw = (
        calibration.native_raw_max
        if value.encoded_unsigned_8_8 != calibration.native_raw_max
        else calibration.native_raw_min
    )
    native = different_raw.to_bytes(calibration.native_width, "big")
    changed_frame = analog_four_saved_kit_frame(
        unpacked_overrides={value.unpacked_offset + i: byte for i, byte in enumerate(native)}
    )
    captures[ANALOG_FOUR_DEVICE_ID] = replace(
        decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, changed_frame),
        captured_at=harness.clock.current - timedelta(minutes=1),
    )
    entry = workspace.verify_recaptures(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        captures=captures,
    )
    assert entry.analog_four_recapture is not None
    assert entry.analog_four_recapture.matches_candidate is False
    projection = workspace.state_dict()["banks"][0]
    assert "a4_recapture_mismatch" in projection["readiness"]["blocked_reasons"]
    assert "a4_recapture_mismatch" in projection["entries"][0]["readiness"]["blocked_reasons"]
    assert "rytm_recapture_mismatch" not in projection["readiness"]["blocked_reasons"]


@pytest.mark.parametrize(
    ("storage", "visible", "nul", "value", "message"),
    [
        (1, 2, False, "a", "visible name length"),
        (1, 1, True, "a", "NUL-terminated names"),
        (2, 1, False, "é", "ASCII characters"),
    ],
)
def test_shared_recipe_ascii_refusal_does_not_mutate_bytes(
    storage: int,
    visible: int,
    nul: bool,
    value: str,
    message: str,
) -> None:
    from rytm_randomizer.devices.strategies.elektron_kit_common import write_fixed_width_ascii
    from rytm_randomizer.observability.errors import ElektronKitFieldError

    destination = bytearray(b"unchanged")
    with pytest.raises(ElektronKitFieldError, match=message):
        write_fixed_width_ascii(
            destination,
            offset=0,
            storage_length=storage,
            visible_length=visible,
            value=value,
            nul_terminated=nul,
        )
    assert destination == b"unchanged"
