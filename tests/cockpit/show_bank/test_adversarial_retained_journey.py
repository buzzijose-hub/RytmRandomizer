"""Distinct retained cues remain independent across migration and profile drift."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.data.show_bank import ShowKitCandidate
from rytm_randomizer.cockpit.library import LibraryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.devices import get_analog_four_native_field_capability
from rytm_randomizer.devices.strategies.analog_four_kit_fields import decode_a4_pitch_components
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
)
from rytm_randomizer.guardrails.input_validation import canonical_json_bytes
from rytm_randomizer.observability.errors import DataError

from .test_native_offline_journey import (
    _RIO,
    _disk,
    _favorite,
    _frame,
    _generate,
    _Journey,
    _journey,
)

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


def _distinct_cues(root: Path) -> tuple[_Journey, _Journey]:
    first = _journey(root, "A4_Test2_T1_OSC1_FIN_P1_Kit.syx")
    originals = {
        ANALOG_RYTM_DEVICE_ID: (_RIO / "RYTM_Test1_Init_Kit.syx").read_bytes(),
        ANALOG_FOUR_DEVICE_ID: (_RIO / "A4_Test3_T1_OSC1_FIN_M1_Kit.syx").read_bytes(),
    }
    library = LibraryStore(root / "library")
    records = {
        device: library.retain_source(decode_kit_capture_frame(device, frame), origin="file_import")
        for device, frame in originals.items()
    }
    bank = first.workspace.bank(first.bank_id)
    entry = first.workspace.adopt_retained_sources(
        bank.bank_id,
        bank.revision,
        library=library,
        rytm_record_id=records[ANALOG_RYTM_DEVICE_ID].record_id,
        analog_four_record_id=records[ANALOG_FOUR_DEVICE_ID].record_id,
        rytm_slot=30,
        analog_four_slot=31,
        entry_id="distinct-source-cue",
    )
    return first, replace(first, originals=originals, entry_id=entry.entry_id)


def _assert_native_isolation(journey: _Journey, candidate: ShowKitCandidate) -> None:
    source = journey.originals[ANALOG_FOUR_DEVICE_ID]
    frame = _frame(journey, candidate)
    capability = get_analog_four_native_field_capability()
    before = capability.read_native_fields(source)
    after = capability.read_native_fields(frame)
    approved: set[int] = set()
    assert candidate.analog_four_candidate.values
    for value in candidate.analog_four_candidate.values:
        assert value.track_id == 1
        cell = after.value(value.parameter, value.track_id)
        assert (value.encoded_native, value.screen_value, value.unpacked_offsets) == (
            cell.encoded_native,
            cell.screen_value,
            cell.unpacked_offsets,
        )
        approved.update(
            cell.unpacked_offsets[:1] if value.parameter.endswith("tune") else cell.unpacked_offsets
        )
    original = decode_analog_four_saved_kit_payload(source[1:-1], require_trailer=True).unpacked
    rendered = decode_analog_four_saved_kit_payload(frame[1:-1], require_trailer=True).unpacked
    changed = {
        offset
        for offset, (old, new) in enumerate(zip(original, rendered, strict=True))
        if old != new
    }
    assert changed and changed <= approved
    assert (
        decode_a4_pitch_components(after.value("osc1_tune", 1).encoded_native)[1:]
        == decode_a4_pitch_components(before.value("osc1_tune", 1).encoded_native)[1:]
    )
    for cell in before.values:
        if not set(cell.unpacked_offsets).intersection(approved):
            assert after.value(cell.parameter, cell.track).native_bytes == cell.native_bytes
    assert candidate.rytm_candidate.estimated_midi_msgs == 0
    assert after.output_authority == "local-file-only" and not after.hardware_send_validated


@pytest.mark.parametrize("profile_change", ("edited", "deleted"))
def test_workspace_recalls_distinct_native_favorites_when_library_and_registry_change(
    tmp_path: Path, profile_change: str
) -> None:
    first, second = _distinct_cues(tmp_path)
    retained: dict[str, tuple[_Journey, ShowKitCandidate, bytes]] = {}
    for journey in (first, second):
        candidates = _generate(journey, fields=("osc1_tune", "filter2_resonance", "osc1_pwm_speed"))
        for candidate in candidates:
            _assert_native_isolation(journey, candidate)
        _favorite(journey, candidates[1])
        retained[journey.entry_id] = journey, candidates[1], _frame(journey, candidates[1])
    assert retained[first.entry_id][1].candidate_id != retained[second.entry_id][1].candidate_id
    assert first.originals != second.originals
    workspace = first.workspace
    bank = workspace.bank(first.bank_id)
    copied = workspace.duplicate(bank.bank_id, first.entry_id, bank.revision)
    retained[copied.entry_id] = retained[first.entry_id]
    bank = workspace.bank(bank.bank_id)
    reordered = workspace.reorder(
        bank.bank_id, bank.revision, (second.entry_id, copied.entry_id, first.entry_id)
    )
    registry = ProfileRegistry(tmp_path / "profiles")
    registry.save(first.profile)
    if profile_change == "edited":
        registry.save(
            replace(
                first.profile,
                name="Edited after favorites were kept",
                traits=tuple(replace(trait, value=0.0) for trait in first.profile.traits),
            ),
            overwrite=True,
        )
        assert registry.get(first.profile.profile_id) != first.profile
    else:
        (tmp_path / "profiles" / "user" / f"{first.profile.profile_id}.json").unlink()
        registry.reload()
        assert registry.get(first.profile.profile_id) is None
    library = LibraryStore(tmp_path / "library")
    for record in library.list_records():
        assert library.delete(record.record_id)
        assert record.source_frame is not None
        (library.library_dir / record.source_frame.artifact_name).unlink()
    assert library.list_records() == ()
    before = _disk(workspace.store.root)
    restarted = ShowKitForgeWorkspace(ShowBankStore(workspace.store.root))
    assert restarted.bank(first.bank_id) == reordered
    state = restarted.state_dict()
    foreign_id = retained[second.entry_id][1].candidate_id
    with pytest.raises(ValueError):
        restarted.select_candidate(
            first.bank_id, first.entry_id, foreign_id, reordered.revision, offline_only=True
        )
    with pytest.raises(ValueError):
        restarted.mark_favorite(
            first.bank_id,
            first.entry_id,
            foreign_id,
            reordered.revision,
            replace_existing=True,
            offline_only=True,
        )
    assert restarted.state_dict() == state and _disk(workspace.store.root) == before
    for entry_id, (journey, expected, exact_frame) in retained.items():
        source, favorite, frame = restarted.favorite_context(first.bank_id, entry_id)
        assert favorite == expected and frame == exact_frame
        assert favorite.recipe.profile == first.profile
        entry = reordered.entry(entry_id)
        assert source.snapshot_id == entry.rytm_source.snapshot_id
        assert source.captured_at == entry.rytm_source.captured_at
        assert restarted.original_source_frames(first.bank_id, entry_id) == journey.originals
        assert favorite.source_rytm_fingerprint == entry.rytm_source.fingerprint
        assert favorite.source_a4_fingerprint == entry.analog_four_source.fingerprint
        with pytest.raises(ValueError, match="catalog-only"):
            restarted.audition_context(first.bank_id, entry_id)
    assert _disk(workspace.store.root) == before
    assert not restarted.state_dict()["banks"][0]["readiness"]["show_ready"]


@pytest.mark.parametrize("version", ("show-bank-v1", "show-bank-v2", "show-bank-v4"))
def test_store_preserves_distinct_retained_cues_when_reading_legacy_or_newer_schema(
    tmp_path: Path, version: str
) -> None:
    first, second = _distinct_cues(tmp_path)
    for journey in (first, second):
        (candidate,) = _generate(journey, fields=("osc1_tune",), count=1)
        _favorite(journey, candidate)
    store = first.workspace.store
    bank = first.workspace.bank(first.bank_id)
    payload = bank.to_dict()
    payload["schema_version"] = version
    manifest = store.root / f"{bank.bank_id}.r{bank.revision:08d}.show-bank.json"
    manifest.write_bytes(canonical_json_bytes(payload))
    before = _disk(store.root)
    if version == "show-bank-v4":
        with pytest.raises(DataError) as failure:
            store.load(bank.bank_id)
        assert failure.value.context["category"] == "schema"
        assert store.list_banks() == ()
        assert store.scan_failures[0].bank_id == bank.bank_id
        assert store.scan_failures[0].category == "schema"
        with pytest.raises(FileExistsError):
            store.import_verified(
                bank,
                {
                    artifact.artifact_id: store.read_retained(artifact.retained)
                    for artifact in bank.sysex_artifacts()
                    if artifact.retained is not None
                },
            )
    else:
        migrated = store.load(bank.bank_id)
        assert migrated == bank
        restarted = ShowKitForgeWorkspace(store)
        for journey in (first, second):
            entry = migrated.entry(journey.entry_id)
            assert (
                restarted.original_source_frames(bank.bank_id, entry.entry_id) == journey.originals
            )
            assert (
                restarted.favorite_context(bank.bank_id, entry.entry_id)[1]
                == entry.favorite_candidate
            )
    assert json.loads(manifest.read_bytes())["schema_version"] == version
    assert _disk(store.root) == before
