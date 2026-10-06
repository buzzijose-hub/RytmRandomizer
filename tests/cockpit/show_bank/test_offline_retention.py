"""Exact local retention with real retained fixtures and no transport authority."""

from __future__ import annotations

import builtins
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.export import writer as writer_module
from rytm_randomizer.cockpit.library import LibraryStore
from rytm_randomizer.cockpit.library import store as library_module
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.show_bank.export import ShowPackService
from rytm_randomizer.cockpit.show_bank.readiness import is_catalog_only_show_bank
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore, canonical_show_bank_json
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.observability.errors import DataError, PersistedStateVersionError

pytestmark = pytest.mark.fast
FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "rio145"


@pytest.fixture(autouse=True)
def refuse_hardware_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def checked_import(name, *args, **kwargs):
        if name.split(".")[0] in ("mido", "rtmidi"):
            raise AssertionError("offline retention must not load a hardware backend")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", checked_import)


def library_sources(root: Path):
    frames = {
        ANALOG_RYTM_DEVICE_ID: (FIXTURES / "RYTM_RIO145_AR_CORE_RETURN_Kit.syx").read_bytes(),
        ANALOG_FOUR_DEVICE_ID: (FIXTURES / "A4_RIO145_CORE_RETURN_Kit.syx").read_bytes(),
    }
    library = LibraryStore(root)
    records = {
        device: library.retain_source(decode_kit_capture_frame(device, frame), origin="file_import")
        for device, frame in frames.items()
    }
    return library, records, frames


def offline_workspace(root: Path):
    library, records, frames = library_sources(root / "library")
    ids = iter(("offline-bank", "first-cue", "second-cue"))
    store = ShowBankStore(root / "banks")
    workspace = ShowKitForgeWorkspace(store, id_factory=lambda _prefix: next(ids))
    bank = workspace.create_bank(name="Offline set", description="", notes=())
    entry = workspace.adopt_retained_sources(
        bank.bank_id,
        bank.revision,
        library=library,
        rytm_record_id=records[ANALOG_RYTM_DEVICE_ID].record_id,
        analog_four_record_id=records[ANALOG_FOUR_DEVICE_ID].record_id,
        rytm_slot=20,
        analog_four_slot=21,
    )
    return workspace, entry, frames


def generate_offline(workspace: ShowKitForgeWorkspace, entry_id: str, root: Path):
    bank = workspace.bank("offline-bank")
    return workspace.generate_candidates(
        bank.bank_id,
        entry_id,
        bank.revision,
        profile=ProfileRegistry(root / "profiles").list_profiles()[0],
        depth_preset="small",
        depth=0.25,
        seed=99,
        candidate_count=2,
        rytm_targets=(),
        rytm_locks=tuple(range(1, 13)),
        analog_four_targets=(1,),
        analog_four_locks=(),
        offline_only=True,
    )


def test_retained_library_sources_survive_restart_and_keep_full_framed_identity(tmp_path: Path):
    library, records, frames = library_sources(tmp_path)
    restarted = LibraryStore(tmp_path)
    for device, record in records.items():
        assert restarted.read_source_frame(record.record_id) == frames[device]
        assert record.source_frame.sha256 == hashlib.sha256(frames[device]).hexdigest()
        assert record.source_origin == "file_import"
        assert bytes.fromhex(record.payload_hex) == frames[device][1:-1]
        assert len(record.source_frame.sha256) == 64
        library.tag(record.record_id, ("set",))
        assert restarted.read_source_frame(record.record_id) == frames[device]


@pytest.mark.parametrize(
    "device,filename",
    (
        (ANALOG_RYTM_DEVICE_ID, "RYTM_Test1_Init_Kit.syx"),
        (ANALOG_FOUR_DEVICE_ID, "A4_Test1_Init_Kit.syx"),
    ),
)
def test_unnamed_real_init_kit_retains_exact_bytes_without_fabricated_name(
    tmp_path, device, filename
):
    frame = (FIXTURES / filename).read_bytes()
    result = decode_kit_capture_frame(device, frame)
    assert result.kit_name == ""
    record = LibraryStore(tmp_path).retain_source(result, origin="file_import")
    assert record.kit_name == ""
    assert LibraryStore(tmp_path).read_source_frame(record.record_id) == frame


def test_capture_file_import_retains_exact_framing_and_no_input_provenance(tmp_path):
    captures = tmp_path / "captures"
    captures.mkdir()
    frame = (FIXTURES / "A4_RIO145_CORE_RETURN_Kit.syx").read_bytes()
    (captures / "source.syx").write_bytes(frame)
    store = LibraryStore(tmp_path / "library", captures_dir=captures)
    outcome = store.import_captures()
    assert len(outcome.imported) == 1
    assert outcome.imported[0].source_origin == "file_import"
    assert store.read_source_frame(outcome.imported[0].record_id) == frame


def test_synthetic_capture_flags_and_family_mismatch_are_refused_without_files(tmp_path):
    frame = (FIXTURES / "A4_RIO145_CORE_RETURN_Kit.syx").read_bytes()
    result = decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, frame)
    for change in (
        {"frame": b"\xf0\x00\xf7"},
        {"frame_bytes": 3},
        {"kit_name": "FAKE"},
        {"fingerprint": "0" * 16},
        {"sent_midi": True},
        {"input_only": False},
        {"round_trip_verified": False},
    ):
        with pytest.raises((ValueError, DataError)):
            LibraryStore(tmp_path / "library").retain_source(replace(result, **change))
    assert not (tmp_path / "library").exists()


def test_library_publication_interrupt_restores_legacy_record_and_removes_new_frame(
    tmp_path, monkeypatch
):
    frame = (FIXTURES / "A4_RIO145_CORE_RETURN_Kit.syx").read_bytes()
    result = decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, frame)
    _, records, _ = library_sources(tmp_path / "source")
    raw = records[ANALOG_FOUR_DEVICE_ID].to_dict()
    raw.pop("source_frame")
    raw.pop("source_origin")
    raw["schema_version"] = 2
    library_dir = tmp_path / "legacy"
    library_dir.mkdir()
    path = library_dir / f'{raw["record_id"]}.json'
    original = json.dumps(raw).encode()
    path.write_bytes(original)
    replace_file = writer_module.os.replace

    def interrupted(source, destination):
        destination = Path(destination)
        if destination == path and Path(source).name.endswith(".stage"):
            raise KeyboardInterrupt("test record interruption")
        return replace_file(source, destination)

    monkeypatch.setattr(writer_module.os, "replace", interrupted)
    with pytest.raises(KeyboardInterrupt):
        LibraryStore(library_dir).retain_source(result, origin="file_import")
    assert tuple(library_dir.iterdir()) == (path,)
    assert path.read_bytes() == original
    assert LibraryStore(library_dir).get(str(raw["record_id"])).source_frame is None


def test_library_read_and_write_bounds_refuse_without_partial_publication(tmp_path, monkeypatch):
    _, records, _ = library_sources(tmp_path / "existing")
    record = records[ANALOG_FOUR_DEVICE_ID]
    monkeypatch.setattr(library_module, "LIBRARY_MAX_RECORD_BYTES", 10)
    assert LibraryStore(tmp_path / "existing").get(record.record_id) is None
    monkeypatch.setattr(library_module, "LIBRARY_MAX_FILES", 1)
    with pytest.raises(ValueError, match="file count"):
        LibraryStore(tmp_path / "existing").list_records()
    monkeypatch.setattr(library_module, "LIBRARY_MAX_FILES", 4096)
    monkeypatch.setattr(library_module, "LIBRARY_MAX_TOTAL_BYTES", 10)
    with pytest.raises(ValueError, match="aggregate size"):
        LibraryStore(tmp_path / "existing").get(record.record_id)


def test_legacy_payload_reconstruction_is_explicit_validated_and_never_rewrites(tmp_path: Path):
    _, records, frames = library_sources(tmp_path / "source")
    record = records[ANALOG_RYTM_DEVICE_ID]
    raw = record.to_dict()
    raw.pop("source_frame")
    raw.pop("source_origin")
    raw["schema_version"] = 2
    tmp_path.joinpath("legacy").mkdir()
    path = tmp_path / "legacy" / f"{record.record_id}.json"
    payload = json.dumps(raw).encode()
    path.write_bytes(payload)
    store = LibraryStore(path.parent)
    migrated = store.get(record.record_id)
    assert migrated.source_frame is None and migrated.source_origin is None
    with pytest.raises(ValueError, match="explicit reconstruction"):
        store.read_source_frame(record.record_id)
    assert (
        store.read_source_frame(record.record_id, allow_legacy_reconstruction=True)
        == frames[ANALOG_RYTM_DEVICE_ID]
    )
    assert path.read_bytes() == payload
    raw["fingerprint"] = "a" * 16
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        store.read_source_frame(record.record_id, allow_legacy_reconstruction=True)


@pytest.mark.parametrize(
    "corruption", ("fingerprint", "family", "payload", "frame", "truncation", "duplicate", "schema")
)
def test_library_source_corruption_fails_closed_without_rewriting(tmp_path: Path, corruption: str):
    _, records, _ = library_sources(tmp_path)
    record = records[ANALOG_RYTM_DEVICE_ID]
    path = tmp_path / f"{record.record_id}.json"
    raw = json.loads(path.read_bytes())
    if corruption == "fingerprint":
        raw["fingerprint"] = "f" * 16
    elif corruption == "family":
        raw["device_id"] = ANALOG_FOUR_DEVICE_ID
    elif corruption == "payload":
        raw["payload_hex"] = "00"
    elif corruption == "schema":
        raw["schema_version"] = 999
    if corruption in ("fingerprint", "family", "payload", "schema"):
        path.write_text(json.dumps(raw))
    elif corruption == "frame":
        (tmp_path / record.source_frame.artifact_name).write_bytes(b"\xf0\x00\xf7")
    elif corruption == "truncation":
        path.write_bytes(path.read_bytes()[:-3])
    else:
        path.write_text('{"schema_version":3,"schema_version":2}')
    before = {item.name: item.read_bytes() for item in tmp_path.iterdir()}
    store = LibraryStore(tmp_path)
    if corruption == "schema":
        with pytest.raises(PersistedStateVersionError):
            store.get(record.record_id)
    else:
        assert store.get(record.record_id) is None
        with pytest.raises(ValueError, match="no exact source"):
            store.read_source_frame(record.record_id)
    assert {item.name: item.read_bytes() for item in tmp_path.iterdir()} == before


def test_exact_original_favorite_and_ordered_bank_roundtrip_disarmed(tmp_path: Path):
    workspace, entry, originals = offline_workspace(tmp_path / "source")
    candidates = generate_offline(workspace, entry.entry_id, tmp_path)
    assert all(item.analog_four_candidate.sysex.retained is not None for item in candidates)
    restarted = ShowKitForgeWorkspace(workspace.store)
    bank = restarted.bank("offline-bank")
    assert is_catalog_only_show_bank(bank)
    assert restarted.original_source_frames(bank.bank_id, entry.entry_id) == originals
    restarted.select_candidate(
        bank.bank_id, entry.entry_id, candidates[1].candidate_id, bank.revision, offline_only=True
    )
    bank = restarted.bank(bank.bank_id)
    restarted.mark_favorite(
        bank.bank_id, entry.entry_id, candidates[1].candidate_id, bank.revision, offline_only=True
    )
    favorite_source, favorite, favorite_frame = restarted.favorite_context(
        bank.bank_id, entry.entry_id
    )
    assert favorite.candidate_id == candidates[1].candidate_id
    assert favorite_source.snapshot_id == entry.rytm_source.snapshot_id
    bank = restarted.bank(bank.bank_id)
    copy = restarted.duplicate(bank.bank_id, entry.entry_id, bank.revision)
    bank = restarted.bank(bank.bank_id)
    bank = restarted.reorder(bank.bank_id, bank.revision, (copy.entry_id, entry.entry_id))
    assert all(
        item.rytm_hardware_save is None and item.rytm_recapture is None for item in bank.entries
    )
    exported = ShowPackService(tmp_path / "packs", store=workspace.store).export(bank)
    target_store = ShowBankStore(tmp_path / "target")
    importer = ShowPackService(tmp_path / "packs", store=target_store)
    imported = importer.import_into_store(exported.package_id)
    imported_workspace = ShowKitForgeWorkspace(target_store)
    assert tuple(item.entry_id for item in imported.bank.entries) == (copy.entry_id, entry.entry_id)
    assert imported_workspace.original_source_frames(bank.bank_id, entry.entry_id) == originals
    assert imported_workspace.favorite_context(bank.bank_id, entry.entry_id)[2] == favorite_frame
    imported_workspace.select_candidate(
        bank.bank_id,
        entry.entry_id,
        favorite.candidate_id,
        imported.bank.revision,
        offline_only=True,
    )
    with pytest.raises(ValueError, match="catalog-only"):
        imported_workspace.require_rytm_audition_source(
            favorite.candidate_id,
            {},
            manually_reloaded=True,
            source_snapshot_id=favorite_source.snapshot_id,
        )
    with pytest.raises(ValueError, match="catalog-only"):
        imported_workspace.audition_context(bank.bank_id, entry.entry_id)
    assert imported_workspace.record_live_rytm_audition(favorite.candidate_id) is None
    assert not imported_workspace.state_dict()["banks"][0]["readiness"]["show_ready"]


def test_source_association_is_checked_even_when_raw_hash_is_valid(tmp_path: Path):
    workspace, entry, _ = offline_workspace(tmp_path)
    forged_capture = replace(entry.rytm_source, fingerprint="a" * 16)
    with pytest.raises(DataError, match="metadata disagrees"):
        workspace.store.read_capture(forged_capture)


def test_reusing_library_originals_preserves_file_source_identity(tmp_path):
    workspace, first, originals = offline_workspace(tmp_path)
    library = LibraryStore(tmp_path / "library")
    records = {item.device_id: item for item in library.list_records()}
    bank = workspace.bank("offline-bank")
    second = workspace.adopt_retained_sources(
        bank.bank_id,
        bank.revision,
        library=library,
        rytm_record_id=records[ANALOG_RYTM_DEVICE_ID].record_id,
        analog_four_record_id=records[ANALOG_FOUR_DEVICE_ID].record_id,
        rytm_slot=20,
        analog_four_slot=21,
    )
    assert second.rytm_source == first.rytm_source
    assert second.analog_four_source == first.analog_four_source
    assert second.rytm_source.capture_id.startswith("file-")
    assert (
        ShowKitForgeWorkspace(workspace.store).original_source_frames(bank.bank_id, second.entry_id)
        == originals
    )


def test_public_import_result_cannot_bypass_source_codec_identity(tmp_path):
    workspace, entry, _ = offline_workspace(tmp_path / "source")
    service = ShowPackService(tmp_path / "packs", store=workspace.store)
    exported = service.export(workspace.bank("offline-bank"))
    verified = service.verify(exported.package_id)
    changed_entry = replace(entry, rytm_source=replace(entry.rytm_source, kit_name="FORGED"))
    forged = replace(verified, bank=replace(verified.bank, entries=(changed_entry,)))
    target = ShowBankStore(tmp_path / "target")
    importer = ShowPackService(tmp_path / "packs", store=target)
    with pytest.raises(DataError, match="metadata disagrees"):
        importer.store_verified_import(forged)
    assert not target.root.exists()


@pytest.mark.parametrize("version", ("show-bank-v1", "show-bank-v2"))
def test_canonical_legacy_store_and_package_migrate_read_only(tmp_path, version):
    workspace, entry, originals = offline_workspace(tmp_path / "source")
    bank = workspace.bank("offline-bank")
    payload = bank.to_dict()
    payload["schema_version"] = version
    canonical = (
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        )
        + "\n"
    ).encode()
    path = workspace.store.root / f"{bank.bank_id}.r{bank.revision:08d}.show-bank.json"
    path.write_bytes(canonical)
    migrated = workspace.store.load(bank.bank_id)
    assert migrated.schema_version == "show-bank-v3"
    assert path.read_bytes() == canonical
    assert (
        ShowKitForgeWorkspace(workspace.store).original_source_frames(bank.bank_id, entry.entry_id)
        == originals
    )
    service = ShowPackService(tmp_path / "packs", store=workspace.store)
    exported = service.export(migrated)
    manifest_path = exported.package_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["bank"]["schema_version"] = version
    original_manifest = (
        json.dumps(
            manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        )
        + "\n"
    ).encode()
    manifest_path.write_bytes(original_manifest)
    assert service.verify(exported.package_id).bank.schema_version == "show-bank-v3"
    assert manifest_path.read_bytes() == original_manifest


def test_full_profile_recipe_replay_detects_tampering_even_with_self_consistent_fingerprints(
    tmp_path,
):
    workspace, entry, _ = offline_workspace(tmp_path / "source")
    generated = generate_offline(workspace, entry.entry_id, tmp_path)
    bank = workspace.bank("offline-bank")
    assert generated[0].recipe.profile is not None
    service = ShowPackService(tmp_path / "packs", store=workspace.store)
    exported = service.export(bank)
    path = exported.package_dir / "manifest.json"
    raw = json.loads(path.read_bytes())
    raw["bank"]["entries"][0]["candidates"][0]["recipe"]["seed"] += 5
    raw["bank"]["entries"][0]["candidates"][0]["rytm_candidate"]["seed"] += 5
    modified = (
        json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()
    path.write_bytes(modified)
    with pytest.raises(DataError, match="deterministic recipe replay"):
        service.verify(exported.package_id)
    assert path.read_bytes() == modified


def test_interrupted_candidate_publish_leaves_previous_bank_and_frames(tmp_path: Path, monkeypatch):
    workspace, entry, _ = offline_workspace(tmp_path)
    previous_bank = workspace.bank("offline-bank")
    before = {path.name: path.read_bytes() for path in workspace.store.root.iterdir()}
    publish = writer_module._publish_no_overwrite
    destinations = []

    def interrupted(source, destination, *, on_published=None):
        if destination.parent == workspace.store.root:
            destinations.append(destination.name)
            if destination.name.endswith(".show-bank.json"):
                raise KeyboardInterrupt("test manifest interruption")
        return publish(source, destination, on_published=on_published)

    monkeypatch.setattr(writer_module, "_publish_no_overwrite", interrupted)
    with pytest.raises(KeyboardInterrupt):
        generate_offline(workspace, entry.entry_id, tmp_path)
    assert destinations[-1].endswith(".show-bank.json")
    assert workspace.bank(previous_bank.bank_id) == previous_bank
    assert ShowBankStore(workspace.store.root).load(previous_bank.bank_id) == previous_bank
    assert {path.name: path.read_bytes() for path in workspace.store.root.iterdir()} == before
    assert canonical_show_bank_json(previous_bank) in before.values()
