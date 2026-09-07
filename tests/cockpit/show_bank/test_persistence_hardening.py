from __future__ import annotations

import dataclasses
import hashlib
import json
from datetime import timedelta
from pathlib import Path

import pytest

from conftest import (
    analog_four_saved_kit_frame,
    elektron_syx_message,
    rytm_real_layout_kit_payload,
)
from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    cockpit_snapshot_from_rytm_capture,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    ShowBank,
    ShowKitRecipe,
    ShowKitScope,
)
from rytm_randomizer.cockpit.export import writer as writer_module
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.show_bank import export as export_module
from rytm_randomizer.cockpit.show_bank import store as store_module
from rytm_randomizer.cockpit.show_bank.export import (
    SHOW_PACK_CHECKSUMS_NAME,
    SHOW_PACK_CUE_ORDER_NAME,
    SHOW_PACK_MANIFEST_NAME,
    ShowPackArtifact,
    ShowPackService,
    ShowPackStoredImportResult,
)
from rytm_randomizer.cockpit.show_bank.forge import (
    analog_four_capture_semantic_fingerprint,
    build_source_entry,
    capture_reference,
    forge_candidate_pair,
    rytm_capture_semantic_fingerprint,
)
from rytm_randomizer.cockpit.show_bank.readiness import (
    add_candidate,
    add_entry,
    attest_hardware_save,
    create_show_bank,
    is_catalog_only_show_bank,
    mark_favorite,
    record_recapture,
    record_rytm_live_audition,
    update_bank_metadata,
)
from rytm_randomizer.cockpit.show_bank.store import (
    ShowBankStore,
    show_bank_corruption_category,
)
from rytm_randomizer.observability.errors import DataError

from ._real_capture_support import capture_matching_rytm_candidate
from ._support import (
    LATER,
    NOW,
    PREFLIGHT_CAPTURED_AT,
    PREFLIGHT_CHECKED_AT,
    RECAPTURED_AT,
    RECORDED_AT,
    SAVE_AT,
    frame,
    source_entry,
)

pytestmark = pytest.mark.fast


def _source_bank() -> ShowBank:
    return add_entry(
        create_show_bank(bank_id="show", name="Show", clock=lambda: NOW),
        source_entry(),
        clock=lambda: LATER,
    )


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _strict_bank_and_frames(tmp_path: Path) -> tuple[ShowBank, dict[str, bytes]]:
    captured_at = NOW - timedelta(minutes=1)
    rytm_frame = elektron_syx_message(rytm_real_layout_kit_payload(b"STRICT RYTM"))
    a4_frame = analog_four_saved_kit_frame(name=b"STRICT A4")
    rytm = dataclasses.replace(
        decode_kit_capture_frame(ANALOG_RYTM_DEVICE_ID, rytm_frame),
        captured_at=captured_at,
    )
    analog_four = dataclasses.replace(
        decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, a4_frame),
        captured_at=captured_at,
    )
    snapshot = cockpit_snapshot_from_rytm_capture(rytm)
    entry = build_source_entry(
        entry_id="entry-strict",
        cue_index=1,
        name="Strict codec cue",
        description="Real registered-codec fixtures",
        rytm_capture=rytm,
        analog_four_capture=analog_four,
        rytm_slot=20,
        analog_four_slot=21,
        rytm_snapshot_id=snapshot.snapshot_id,
        now=NOW,
    )
    bank = add_entry(
        create_show_bank(bank_id="strict-bank", name="Strict", clock=lambda: NOW),
        entry,
        clock=lambda: NOW,
    )
    profile = ProfileRegistry(tmp_path / "profiles").list_profiles()[0]
    recipe = ShowKitRecipe(
        profile_id=profile.profile_id,
        depth_preset="small",
        depth=0.25,
        seed=22,
        rytm_scope=ShowKitScope(
            device_id=RYTM_SHOW_KIT_DEVICE_ID,
            target_ids=(1,),
        ),
        analog_four_scope=ShowKitScope(
            device_id=A4_SHOW_KIT_DEVICE_ID,
            target_ids=(1,),
        ),
    )
    forged = forge_candidate_pair(
        entry=entry,
        rytm_source_snapshot=snapshot,
        analog_four_source_frame=a4_frame,
        profile=profile,
        recipe=recipe,
        now=NOW,
    )
    bank = add_candidate(
        bank,
        entry.entry_id,
        forged.candidate,
        select=True,
        clock=lambda: NOW,
    )
    bank = record_rytm_live_audition(bank, entry.entry_id, clock=lambda: NOW)
    frames = {
        entry.rytm_source.sysex.artifact_id: rytm_frame,
        entry.analog_four_source.sysex.artifact_id: a4_frame,
        forged.candidate.analog_four_candidate.sysex.artifact_id: forged.analog_four_frame,
    }
    return bank, frames


def _strict_package(tmp_path: Path, package_id: str = "strict"):
    bank, frames = _strict_bank_and_frames(tmp_path)
    store = ShowBankStore(tmp_path / "source-store", clock=lambda: LATER)
    bank = store.retain_sysex_set(bank, frames)
    service = ShowPackService(tmp_path / "packages", store=store, clock=lambda: LATER)
    exported = service.export(bank, package_id=package_id)
    return service, exported, bank, frames


def _strict_recapture_package(tmp_path: Path, package_id: str = "recaptures"):
    bank, frames = _strict_bank_and_frames(tmp_path)
    entry = bank.entry("entry-strict")
    candidate = entry.candidates[0]
    bank = mark_favorite(bank, entry.entry_id, clock=lambda: LATER)
    for device_id in (RYTM_SHOW_KIT_DEVICE_ID, A4_SHOW_KIT_DEVICE_ID):
        bank = attest_hardware_save(
            bank,
            entry.entry_id,
            device_id=device_id,
            hardware_slot=64,
            note="saved on disposable test slot",
            clock=lambda: SAVE_AT,
        )

    source_rytm = decode_kit_capture_frame(
        ANALOG_RYTM_DEVICE_ID,
        frames[entry.rytm_source.sysex.artifact_id],
    )
    source_a4 = decode_kit_capture_frame(
        ANALOG_FOUR_DEVICE_ID,
        frames[entry.analog_four_source.sysex.artifact_id],
    )
    rytm_result = capture_matching_rytm_candidate(
        source_rytm,
        candidate.rytm_candidate,
        captured_at=RECAPTURED_AT,
    )
    a4_result = dataclasses.replace(
        decode_kit_capture_frame(
            ANALOG_FOUR_DEVICE_ID,
            frames[candidate.analog_four_candidate.sysex.artifact_id],
        ),
        captured_at=RECAPTURED_AT,
    )
    rytm_reference = capture_reference(
        rytm_result,
        hardware_slot=64,
        snapshot_id=cockpit_snapshot_from_rytm_capture(rytm_result).snapshot_id,
    )
    a4_reference = capture_reference(
        a4_result,
        hardware_slot=64,
        snapshot_id=None,
    )
    bank = record_recapture(
        bank,
        entry.entry_id,
        rytm_reference,
        source_semantic_fingerprint=rytm_capture_semantic_fingerprint(source_rytm),
        observed_semantic_fingerprint=rytm_capture_semantic_fingerprint(rytm_result),
        comparison_reason="real saved-KIT candidate semantics matched",
        clock=lambda: RECORDED_AT,
    )
    source_a4_semantic = analog_four_capture_semantic_fingerprint(
        source_a4,
        candidate.analog_four_candidate,
    )
    assert source_a4_semantic is not None
    bank = record_recapture(
        bank,
        entry.entry_id,
        a4_reference,
        source_semantic_fingerprint=source_a4_semantic,
        observed_semantic_fingerprint=analog_four_capture_semantic_fingerprint(
            a4_result,
            candidate.analog_four_candidate,
        ),
        comparison_reason="real saved-KIT Filter 1 Frequency semantics matched",
        clock=lambda: RECORDED_AT,
    )
    frames[rytm_reference.sysex.artifact_id] = rytm_result.frame
    frames[a4_reference.sysex.artifact_id] = a4_result.frame

    store = ShowBankStore(tmp_path / "source-store", clock=lambda: PREFLIGHT_CAPTURED_AT)
    bank = store.retain_sysex_set(bank, frames)
    service = ShowPackService(
        tmp_path / "packages",
        store=store,
        clock=lambda: PREFLIGHT_CHECKED_AT,
    )
    exported = service.export(bank, package_id=package_id)
    return service, exported, bank


def test_bulk_retention_publishes_one_manifest_and_persists_idempotent_transition(
    tmp_path: Path,
) -> None:
    store = ShowBankStore(tmp_path / "banks", clock=lambda: LATER)
    bank = _source_bank()
    frames = {"rytm-source-frame": frame(1), "a4-source-frame": frame(2)}

    retained = store.retain_sysex_set(bank, frames)

    assert retained.revision == bank.revision + 2
    assert store.latest_revision("show") == retained.revision
    assert len(tuple(store.root.glob("*.show-bank.json"))) == 1
    assert store.retain_sysex_set(retained, frames) is retained

    advanced = update_bank_metadata(
        retained,
        name="Renamed",
        description="",
        notes=(),
        clock=lambda: LATER + timedelta(minutes=1),
    )
    published = store.retain_sysex_set(advanced, frames)
    assert published is advanced
    assert store.latest_revision("show") == advanced.revision
    assert store.load("show").name == "Renamed"


def test_store_rejects_duplicate_noncanonical_and_nonforward_manifests(tmp_path: Path) -> None:
    duplicate_store = ShowBankStore(tmp_path / "duplicate")
    result = duplicate_store.save(_source_bank())
    result.path.write_bytes(b'{"bank_id":"show",' + result.path.read_bytes()[1:])
    with pytest.raises(DataError) as duplicate:
        duplicate_store.load("show")
    assert show_bank_corruption_category(duplicate.value) == "malformed-json"

    noncanonical_store = ShowBankStore(tmp_path / "noncanonical")
    result = noncanonical_store.save(_source_bank())
    result.path.write_bytes(result.path.read_bytes() + b" ")
    with pytest.raises(DataError) as noncanonical:
        noncanonical_store.load("show")
    assert show_bank_corruption_category(noncanonical.value) == "schema"

    lineage_store = ShowBankStore(tmp_path / "lineage")
    bank = _source_bank()
    lineage_store.save(bank)
    gap = dataclasses.replace(
        bank,
        revision=bank.revision + 3,
        updated_at=LATER + timedelta(minutes=1),
    )
    lineage_store.save(gap)
    changed_entry = dataclasses.replace(
        gap.entries[0],
        rytm_source=dataclasses.replace(gap.entries[0].rytm_source, fingerprint="deadbeef"),
        updated_at=LATER + timedelta(minutes=2),
    )
    changed_source = dataclasses.replace(
        gap,
        revision=gap.revision + 1,
        entries=(changed_entry,),
        updated_at=LATER + timedelta(minutes=2),
    )
    with pytest.raises(ValueError, match="source anchors"):
        lineage_store.save(changed_source)


def test_catalog_scan_isolates_one_corrupt_bank(tmp_path: Path) -> None:
    store = ShowBankStore(tmp_path / "banks")
    corrupt = _source_bank()
    valid = dataclasses.replace(corrupt, bank_id="valid")
    corrupt_path = store.save(corrupt).path
    store.save(valid)
    corrupt_path.write_bytes(b"not-json")

    assert store.list_banks() == (valid,)
    assert tuple((failure.bank_id, failure.category) for failure in store.scan_failures) == (
        ("show", "malformed-json"),
    )


def test_failed_import_rolls_back_every_capture_manifest_and_namespace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frames = {"rytm-source-frame": frame(1), "a4-source-frame": frame(2)}
    source = ShowBankStore(tmp_path / "source", clock=lambda: LATER)
    bank = source.retain_sysex_set(_source_bank(), frames)
    target = ShowBankStore(tmp_path / "target")
    original_publish = writer_module._publish_no_overwrite
    calls = 0

    def fail_second_publish(tmp_name, path, *, on_published=None):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected publication failure")
        return original_publish(tmp_name, path, on_published=on_published)

    monkeypatch.setattr(writer_module, "_publish_no_overwrite", fail_second_publish)
    with pytest.raises(DataError, match="atomic write set failed"):
        target.import_verified(bank, frames)

    assert target.latest_revision(bank.bank_id) is None
    assert tuple(target.root.iterdir()) == ()


def test_real_family_codecs_and_candidate_fingerprints_are_verified(tmp_path: Path) -> None:
    service, exported, bank, _frames = _strict_package(tmp_path)
    corrupt_sibling = service.package_root / "corrupt-sibling.show-pack"
    corrupt_sibling.mkdir()
    (corrupt_sibling / SHOW_PACK_MANIFEST_NAME).write_bytes(b"not-json")

    verified = service.verify(exported.package_id)

    assert verified.bank == bank
    raw = exported.manifest.to_dict()
    raw["bank"]["entries"][0]["candidates"][0]["analog_four_candidate"][
        "artifact_fingerprint"
    ] = "deadbeef"
    (exported.package_dir / SHOW_PACK_MANIFEST_NAME).write_bytes(_canonical(raw))
    with pytest.raises(DataError, match="A4 candidate fingerprint"):
        service.verify(exported.package_id)


def test_real_family_codecs_verify_paired_recapture_semantic_evidence(
    tmp_path: Path,
) -> None:
    service, exported, bank = _strict_recapture_package(tmp_path)

    verified = service.verify(exported.package_id)

    assert verified.bank == bank
    entry = verified.bank.entry("entry-strict")
    assert entry.status == "verified"
    assert entry.rytm_recapture is not None
    assert entry.rytm_recapture.matches_candidate is True
    assert entry.rytm_recapture.matches_source is False
    assert entry.analog_four_recapture is not None
    assert entry.analog_four_recapture.matches_candidate is True


@pytest.mark.parametrize(
    ("recapture_key", "fingerprint_key"),
    (
        ("rytm_recapture", "observed_semantic_fingerprint"),
        ("rytm_recapture", "source_semantic_fingerprint"),
        ("analog_four_recapture", "observed_semantic_fingerprint"),
        ("analog_four_recapture", "source_semantic_fingerprint"),
    ),
)
def test_verify_rejects_each_corrupt_recapture_semantic_claim(
    tmp_path: Path,
    recapture_key: str,
    fingerprint_key: str,
) -> None:
    service, exported, _bank = _strict_recapture_package(tmp_path)
    raw = exported.manifest.to_dict()
    recapture_raw = raw["bank"]["entries"][0][recapture_key]
    assert recapture_raw is not None
    recapture_raw[fingerprint_key] = "d" * 16
    recapture_raw["matches_source"] = False
    if fingerprint_key == "observed_semantic_fingerprint":
        recapture_raw["matches_candidate"] = False
        raw["bank"]["entries"][0]["status"] = "hardware-saved"
        raw["bank"]["status"] = "hardware-saved"
        # Keep the envelope internally consistent so verification reaches
        # the false semantic claim rather than stopping at the cue sheet.
        cue_payload = export_module._cue_order_payload(ShowBank.from_dict(raw["bank"]))
        (exported.package_dir / SHOW_PACK_CUE_ORDER_NAME).write_bytes(cue_payload)
        for artifact in raw["artifacts"]:
            if artifact["name"] == SHOW_PACK_CUE_ORDER_NAME:
                artifact["sha256"] = hashlib.sha256(cue_payload).hexdigest()
                artifact["byte_count"] = len(cue_payload)
        artifacts = tuple(ShowPackArtifact.from_dict(item) for item in raw["artifacts"])
        (exported.package_dir / SHOW_PACK_CHECKSUMS_NAME).write_bytes(
            export_module._checksums_payload(artifacts)
        )
    (exported.package_dir / SHOW_PACK_MANIFEST_NAME).write_bytes(_canonical(raw))

    with pytest.raises(DataError, match="recapture semantic evidence") as exc_info:
        service.verify(exported.package_id)

    assert show_bank_corruption_category(exc_info.value) == "cross-reference"


def test_verify_rejects_duplicate_keys_and_missing_required_retention(tmp_path: Path) -> None:
    service, exported, bank, _frames = _strict_package(tmp_path / "duplicate", "duplicate")
    manifest_path = exported.package_dir / SHOW_PACK_MANIFEST_NAME
    manifest_path.write_bytes(b'{"package_id":"duplicate",' + manifest_path.read_bytes()[1:])
    with pytest.raises(DataError) as duplicate:
        service.verify("duplicate")
    assert duplicate.value.context["category"] == "malformed-json"

    service, exported, bank, _frames = _strict_package(tmp_path / "parity", "parity")
    raw = exported.manifest.to_dict()
    source = bank.entry("entry-strict").rytm_source.sysex
    assert source.retained is not None
    raw_source = raw["bank"]["entries"][0]["rytm_source"]["sysex"]
    raw_source["retained"] = None
    raw["artifacts"] = [
        artifact
        for artifact in raw["artifacts"]
        if artifact["name"] != source.retained.artifact_name
    ]
    (exported.package_dir / source.retained.artifact_name).unlink()
    manifest_path = exported.package_dir / SHOW_PACK_MANIFEST_NAME
    manifest_path.write_bytes(_canonical(raw))
    artifacts = tuple(ShowPackArtifact.from_dict(item) for item in raw["artifacts"])
    (exported.package_dir / SHOW_PACK_CHECKSUMS_NAME).write_bytes(
        export_module._checksums_payload(artifacts)
    )
    with pytest.raises(DataError, match="missing required retained"):
        service.verify("parity")


def test_import_is_catalog_only_typed_and_rejects_existing_namespace(tmp_path: Path) -> None:
    _service, exported, bank, _frames = _strict_package(tmp_path / "package")
    target = ShowBankStore(tmp_path / "target")
    importing = ShowPackService(
        exported.package_dir.parent,
        store=target,
        clock=lambda: LATER,
    )

    result = importing.import_into_store(exported.package_id)

    assert isinstance(result, ShowPackStoredImportResult)
    assert result.bank.revision == bank.revision + 1
    assert is_catalog_only_show_bank(result.bank)
    entry = result.bank.entry("entry-strict")
    assert entry.selected_candidate_id is None
    assert entry.rytm_live_auditioned_at is None
    assert entry.candidates == bank.entry("entry-strict").candidates
    assert result.writes[-1].path.name.endswith("show-bank.json")
    with pytest.raises(FileExistsError, match="namespace"):
        importing.import_into_store(exported.package_id)


def test_aggregate_scan_bounds_and_failed_export_reservation_are_enforced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = ShowBankStore(tmp_path / "store", clock=lambda: LATER)
    bank = store.retain_sysex_set(
        _source_bank(),
        {"rytm-source-frame": frame(1), "a4-source-frame": frame(2)},
    )
    service = ShowPackService(tmp_path / "packages", store=store)

    monkeypatch.setattr(export_module, "SHOW_PACK_MAX_TOTAL_BYTES", 5)
    with pytest.raises(DataError) as oversized:
        service.export(bank, package_id="oversized")
    assert oversized.value.context["category"] == "size"
    assert not (service.package_root / "oversized.show-pack").exists()
    monkeypatch.setattr(export_module, "SHOW_PACK_MAX_TOTAL_BYTES", 64 * 1024 * 1024)

    def fail_publication(_artifacts, *, overwrite=False):
        raise RuntimeError(f"publication failed: {overwrite}")

    monkeypatch.setattr(export_module, "atomic_write_set", fail_publication)
    with pytest.raises(RuntimeError, match="publication failed"):
        service.export(bank, package_id="failed")
    assert not (service.package_root / "failed.show-pack").exists()

    monkeypatch.setattr(store_module, "SHOW_BANK_MAX_DIRECTORY_ENTRIES", 0)
    with pytest.raises(DataError) as scan:
        store.latest_revision("show")
    assert show_bank_corruption_category(scan.value) == "size"


@pytest.mark.parametrize("claim", ["fingerprint", "kit_name", "rytm_semantic_fingerprint"])
def test_verify_rejects_false_capture_or_candidate_claim_in_valid_envelope(
    tmp_path: Path, claim: str
) -> None:
    service, exported, _bank, _frames = _strict_package(tmp_path)
    raw = exported.manifest.to_dict()
    entry = raw["bank"]["entries"][0]
    if claim == "rytm_semantic_fingerprint":
        entry["candidates"][0][claim] = "d" * 16
        expected = "Rytm candidate semantic fingerprint"
    else:
        # Changing A4 metadata avoids the Rytm snapshot-id/model constraint;
        # the package still must compare this claim with decoded source bytes.
        entry["analog_four_source"][claim] = "deadbeef" if claim == "fingerprint" else "FALSE"
        if claim == "fingerprint":
            entry["candidates"][0]["source_a4_fingerprint"] = "deadbeef"
            entry["candidates"][0]["analog_four_candidate"]["source_fingerprint"] = "deadbeef"
        expected = "metadata disagrees"
    (exported.package_dir / SHOW_PACK_MANIFEST_NAME).write_bytes(_canonical(raw))
    with pytest.raises(DataError, match=expected) as failure:
        service.verify(exported.package_id)
    assert failure.value.context["category"] == "cross-reference"


@pytest.mark.parametrize("damage", ["malformed", "different-frame", "unverified"])
def test_capture_codec_failure_cannot_produce_verified_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    service, exported, bank, frames = _strict_package(tmp_path)
    source_frame = frames[bank.entries[0].rytm_source.sysex.artifact_id]
    original_decode = export_module.decode_kit_capture_frame

    def damaged_decode(device_id, frame_bytes):
        if frame_bytes == source_frame:
            if damage == "malformed":
                return original_decode(device_id, b"\xf0\x01\xf7")
            decoded = original_decode(device_id, frame_bytes)
            return dataclasses.replace(
                decoded,
                **(
                    {"frame": b"\xf0\x01\xf7"}
                    if damage == "different-frame"
                    else {"round_trip_verified": False}
                ),
            )
        return original_decode(device_id, frame_bytes)

    monkeypatch.setattr(export_module, "decode_kit_capture_frame", damaged_decode)
    with pytest.raises(DataError, match="codec") as failure:
        service.verify(exported.package_id)
    assert failure.value.context["category"] == "framing"


def test_device_claim_validation_rejects_missing_packaged_capture(tmp_path: Path) -> None:
    _service, _exported, bank, frames = _strict_package(tmp_path)
    missing_id = bank.entries[0].rytm_source.sysex.artifact_id
    del frames[missing_id]
    with pytest.raises(DataError, match="missing required retained") as failure:
        export_module._verify_package_device_claims(bank, frames)
    assert failure.value.context["category"] == "cross-reference"


@pytest.mark.parametrize(
    ("boundary", "message"),
    [
        ("cockpit_snapshot_from_rytm_capture", "source cannot reconstruct"),
        ("rytm_semantic_fingerprint", "candidate cannot be reproduced"),
        ("analog_four_capture_semantic_fingerprint", "candidate failed registered codec"),
    ],
)
def test_semantic_boundary_failures_are_categorized_without_accepting_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, boundary: str, message: str
) -> None:
    service, exported, _bank, _frames = _strict_package(tmp_path)

    def unavailable_semantics(*args, **kwargs):
        raise ValueError("registered semantic projection unavailable")

    monkeypatch.setattr(export_module, boundary, unavailable_semantics)
    with pytest.raises(DataError, match=message) as failure:
        service.verify(exported.package_id)
    assert isinstance(failure.value.__cause__, ValueError)


def test_packages_allow_unretained_nonfavorite_and_favorite_before_recapture(
    tmp_path: Path,
) -> None:
    bank, frames = _strict_bank_and_frames(tmp_path)
    entry = bank.entries[0]
    sources = {
        capture.sysex.artifact_id: frames[capture.sysex.artifact_id] for capture in bank.captures()
    }
    store = ShowBankStore(tmp_path / "store", clock=lambda: LATER)
    bank = store.retain_sysex_set(bank, sources)
    service = ShowPackService(tmp_path / "packages", store=store, clock=lambda: LATER)
    first = service.export(bank, package_id="nonfavorite")
    assert service.verify(first.package_id).bank == bank
    assert bank.entries[0].candidates[0].analog_four_candidate.sysex.retained is None
    bank = store.retain_sysex_set(bank, frames)
    bank = mark_favorite(bank, entry.entry_id, clock=lambda: LATER)
    second = service.export(bank, package_id="favorite")
    verified = service.verify(second.package_id).bank
    assert verified == bank
    assert verified.entries[0].rytm_recapture is None
    assert verified.entries[0].analog_four_recapture is None


def test_verify_rejects_package_directory_replacement_after_codec_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, exported, _bank, _frames = _strict_package(tmp_path)
    original_verify = export_module._verify_package_device_claims
    displaced = tmp_path / "verified-original"

    def replace_directory_after_claims(*args, **kwargs):
        original_verify(*args, **kwargs)
        exported.package_dir.rename(displaced)
        exported.package_dir.mkdir()

    monkeypatch.setattr(
        export_module, "_verify_package_device_claims", replace_directory_after_claims
    )
    with pytest.raises(DataError, match="directory changed during verification"):
        service.verify(exported.package_id)
    assert (displaced / SHOW_PACK_MANIFEST_NAME).is_file()
    assert tuple(exported.package_dir.iterdir()) == ()


@pytest.mark.parametrize("family", ["rytm", "analog_four"])
def test_recapture_projection_failure_is_bound_to_the_recorded_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, family: str
) -> None:
    service, exported, bank = _strict_recapture_package(tmp_path)
    recapture = getattr(bank.entries[0], f"{family}_recapture")
    assert recapture is not None
    original_capture = export_module._decoded_capture
    boundary = f"{family}_capture_semantic_fingerprint"
    original_semantics = getattr(export_module, boundary)
    recorded_result = None

    def remember_recorded_result(capture, frame_bytes):
        nonlocal recorded_result
        result = original_capture(capture, frame_bytes)
        if capture.capture_id == recapture.capture.capture_id:
            recorded_result = result
        return result

    def unavailable_recapture_projection(result, *args):
        # Source and candidate projections still use the real implementation.
        if result is recorded_result:
            raise ValueError("registered recapture projection unavailable")
        return original_semantics(result, *args)

    monkeypatch.setattr(export_module, "_decoded_capture", remember_recorded_result)
    monkeypatch.setattr(export_module, boundary, unavailable_recapture_projection)
    with pytest.raises(DataError, match="recapture semantic comparison failed") as failure:
        service.verify(exported.package_id)
    assert failure.value.context["category"] == "cross-reference"
    assert failure.value.context["artifact_name"] == recapture.capture.sysex.artifact_id
    assert isinstance(failure.value.__cause__, ValueError)
