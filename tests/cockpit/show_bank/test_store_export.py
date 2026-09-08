from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from rytm_randomizer.cockpit.data.show_bank import (
    RetainedSysexArtifact,
)
from rytm_randomizer.cockpit.show_bank import export as export_module
from rytm_randomizer.cockpit.show_bank import store as store_module
from rytm_randomizer.cockpit.show_bank.export import (
    SHOW_PACK_CHECKSUMS_NAME,
    SHOW_PACK_MANIFEST_NAME,
    ShowPackManifest,
    ShowPackService,
)
from rytm_randomizer.cockpit.show_bank.readiness import (
    add_entry,
    create_show_bank,
    is_catalog_only_show_bank,
)
from rytm_randomizer.cockpit.show_bank.store import (
    ShowBankStore,
    canonical_show_bank_json,
    default_show_bank_dir,
    narrow_show_bank_corruption_category,
    read_bounded_show_bank_file,
    show_bank_corruption_category,
    validate_show_bank_sysex_frame,
)
from rytm_randomizer.observability.errors import DataError

from ._support import LATER, NOW, frame, source_entry

pytestmark = pytest.mark.fast


def clock():
    return LATER


def source_bank():
    bank = create_show_bank(bank_id="show", name="Show", clock=lambda: NOW)
    return add_entry(bank, source_entry(), clock=clock)


def retained_source_bank(store: ShowBankStore):
    bank = source_bank()
    store.save(bank)
    bank = store.retain_sysex(bank, "rytm-source-frame", frame(1))
    return store.retain_sysex(bank, "a4-source-frame", frame(2))


def test_revision_store_is_canonical_atomic_and_never_overwrites(tmp_path: Path) -> None:
    store = ShowBankStore(tmp_path / "banks", clock=clock)
    bank = source_bank()
    result = store.save(bank)
    assert result.path.name == "show.r00000001.show-bank.json"
    assert result.path.read_bytes() == canonical_show_bank_json(bank)
    with pytest.raises(FileExistsError):
        store.save(bank)

    bank = store.retain_sysex(bank, "rytm-source-frame", frame(1))
    bank = store.retain_sysex(bank, "a4-source-frame", frame(2))
    assert bank.revision == 3
    assert store.latest_revision("show") == 3
    assert store.load("show") == bank
    assert store.load("show", revision=1, verify_retained=False).revision == 1
    assert store.list_banks() == (bank,)
    assert store.retain_sysex(bank, "a4-source-frame", frame(2)) is bank
    assert len(tuple((tmp_path / "banks").glob("*.syx"))) == 2


def test_retain_rejects_wrong_bytes_type_hash_and_framing(tmp_path: Path) -> None:
    store = ShowBankStore(tmp_path, clock=clock)
    bank = source_bank()
    with pytest.raises(TypeError):
        store.retain_sysex(bank, "rytm-source-frame", bytearray(frame(1)))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="framed"):
        store.retain_sysex(bank, "rytm-source-frame", b"not sysex")
    with pytest.raises(ValueError, match="hash"):
        store.retain_sysex(bank, "rytm-source-frame", frame(9))


@pytest.mark.parametrize(
    ("mutate", "category"),
    [
        (lambda path: path.write_bytes(b"not-json"), "malformed-json"),
        (lambda path: path.write_text("[]", encoding="utf-8"), "schema"),
    ],
)
def test_load_classifies_manifest_corruption(tmp_path: Path, mutate, category: str) -> None:
    store = ShowBankStore(tmp_path)
    bank = source_bank()
    result = store.save(bank)
    mutate(result.path)
    with pytest.raises(DataError) as exc_info:
        store.load("show")
    assert show_bank_corruption_category(exc_info.value) == category


def test_load_detects_missing_hash_size_and_framing(tmp_path: Path) -> None:
    store = ShowBankStore(tmp_path, clock=clock)
    bank = store.retain_sysex(source_bank(), "rytm-source-frame", frame(1))
    artifact = bank.sysex_artifact("rytm-source-frame").retained
    assert artifact is not None
    path = tmp_path / artifact.artifact_name

    path.unlink()
    with pytest.raises(DataError) as exc_info:
        store.load("show")
    assert show_bank_corruption_category(exc_info.value) == "missing"

    path.write_bytes(b"\xf0\xf7")
    with pytest.raises(DataError) as exc_info:
        store.load("show")
    assert show_bank_corruption_category(exc_info.value) == "size"

    digest = hashlib.sha256(b"abc").hexdigest()
    bad_artifact = RetainedSysexArtifact(
        artifact_name=f"{digest}.syx",
        sha256=digest,
        byte_count=3,
    )
    (tmp_path / bad_artifact.artifact_name).write_bytes(b"abc")
    assert bad_artifact.byte_count == 3
    with pytest.raises(DataError) as exc_info:
        store.read_retained(bad_artifact)
    assert show_bank_corruption_category(exc_info.value) == "framing"


def test_show_pack_export_verify_and_import_are_self_contained(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_store = ShowBankStore(tmp_path / "source", clock=clock)
    bank = retained_source_bank(source_store)
    service = ShowPackService(tmp_path / "packages", store=source_store)

    exported = service.export(bank)

    assert exported.package_dir.name == "show-r00000003.show-pack"
    assert exported.writes[-1].path.name == SHOW_PACK_MANIFEST_NAME
    assert (exported.package_dir / SHOW_PACK_CHECKSUMS_NAME).is_file()
    monkeypatch.setattr(export_module, "_verify_package_device_claims", lambda bank, frames: None)
    verified = service.verify(exported.package_id)
    assert verified.bank == bank
    assert set(verified.frames_by_artifact_id) == {
        "rytm-source-frame",
        "a4-source-frame",
    }

    target_store = ShowBankStore(tmp_path / "target")
    importing = ShowPackService(tmp_path / "packages", store=target_store)
    stored = importing.import_into_store(exported.package_id)
    assert stored.writes[-1].path.name == "show.r00000000.show-bank.json"
    assert stored.bank.revision == 0
    assert is_catalog_only_show_bank(stored.bank)
    assert target_store.load("show") == stored.bank


def test_show_pack_refuses_unretained_required_evidence_and_overwrite(tmp_path: Path) -> None:
    store = ShowBankStore(tmp_path / "store")
    service = ShowPackService(tmp_path / "packages", store=store)
    with pytest.raises(ValueError, match="empty"):
        service.export(create_show_bank(bank_id="empty", name="Empty", clock=lambda: NOW))
    with pytest.raises(ValueError, match="explicitly retained"):
        service.export(source_bank())
    bank = retained_source_bank(store)
    service.export(bank, package_id="package")
    with pytest.raises(FileExistsError):
        service.export(bank, package_id="package")


def test_show_pack_verifier_rejects_extra_hash_and_cross_reference_corruption(
    tmp_path: Path,
) -> None:
    store = ShowBankStore(tmp_path / "store", clock=clock)
    bank = retained_source_bank(store)

    def exported(name: str):
        service = ShowPackService(tmp_path / name, store=store)
        result = service.export(bank, package_id=name)
        return service, result.package_dir

    service, package = exported("extra")
    (package / "surprise.txt").write_text("x", encoding="utf-8")
    with pytest.raises(DataError, match="file set"):
        service.verify("extra")

    service, package = exported("hash")
    capture_path = next(package.glob("*.syx"))
    capture_path.write_bytes(frame(9))
    with pytest.raises(DataError, match="hash mismatch"):
        service.verify("hash")

    service, package = exported("cue")
    cue_path = package / "cue-order.json"
    changed = cue_path.read_bytes().replace(b"Opening pressure", b"Wrong pressure__")
    cue_path.write_bytes(changed)
    manifest_path = package / SHOW_PACK_MANIFEST_NAME
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    for artifact in raw["artifacts"]:
        if artifact["name"] == "cue-order.json":
            artifact["sha256"] = hashlib.sha256(changed).hexdigest()
            artifact["byte_count"] = len(changed)
    manifest_path.write_bytes(
        (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    )
    checksums = package / SHOW_PACK_CHECKSUMS_NAME
    lines = checksums.read_text(encoding="ascii").splitlines()
    lines = [
        (
            f"{hashlib.sha256(changed).hexdigest()}  cue-order.json"
            if line.endswith("  cue-order.json")
            else line
        )
        for line in lines
    ]
    checksums.write_bytes(("\n".join(lines) + "\n").encode("ascii"))
    with pytest.raises(DataError, match="cue order"):
        service.verify("cue")


def test_manifest_round_trip_and_strict_schema(tmp_path: Path) -> None:
    store = ShowBankStore(tmp_path / "store", clock=clock)
    bank = retained_source_bank(store)
    service = ShowPackService(tmp_path / "packages", store=store)
    result = service.export(bank)
    restored = ShowPackManifest.from_dict(result.manifest.to_dict())
    assert restored == result.manifest
    raw = result.manifest.to_dict()
    raw["format"] = "other"
    with pytest.raises(ValueError, match="format"):
        ShowPackManifest.from_dict(raw)


def test_store_public_validation_helpers_are_strict(tmp_path: Path) -> None:
    assert default_show_bank_dir().name == "show-banks"
    assert narrow_show_bank_corruption_category("hash") == "hash"
    with pytest.raises(ValueError, match="invalid"):
        narrow_show_bank_corruption_category("maybe")
    assert show_bank_corruption_category(DataError("plain")) is None
    with pytest.raises(ValueError, match="filename-safe"):
        ShowBankStore(tmp_path).latest_revision("Bad ID")
    with pytest.raises(ValueError, match="revision"):
        ShowBankStore(tmp_path).load("bank", revision=-1)
    with pytest.raises(ValueError, match="size"):
        validate_show_bank_sysex_frame(b"")
    with pytest.raises(ValueError, match="exactly one"):
        validate_show_bank_sysex_frame(frame(1) + frame(2))


def test_bounded_reader_categorizes_path_access_size_and_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(DataError) as exc_info:
        read_bounded_show_bank_file(missing, maximum=10)
    assert show_bank_corruption_category(exc_info.value) == "missing"

    with pytest.raises(DataError) as exc_info:
        read_bounded_show_bank_file(tmp_path, maximum=10)
    assert show_bank_corruption_category(exc_info.value) == "path"

    target = tmp_path / "payload"
    target.write_bytes(b"")
    with pytest.raises(DataError) as exc_info:
        read_bounded_show_bank_file(target, maximum=10)
    assert show_bank_corruption_category(exc_info.value) == "size"
    target.write_bytes(b"payload")
    assert read_bounded_show_bank_file(target, maximum=10) == b"payload"

    original_stat = Path.stat
    original_open = store_module.os.open

    def broken_stat(path: Path, *, follow_symlinks: bool = True):
        if path == target:
            raise OSError("blocked")
        return original_stat(path, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(Path, "stat", broken_stat)
    with pytest.raises(DataError) as exc_info:
        read_bounded_show_bank_file(target, maximum=10)
    assert show_bank_corruption_category(exc_info.value) == "access"

    target.write_bytes(b"1234567890")
    monkeypatch.setattr(Path, "stat", original_stat)

    def growing_open(path: Path, *args, **kwargs):
        if path == target:
            with open(path, "ab") as handle:
                handle.write(b"x")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(store_module.os, "open", growing_open)
    with pytest.raises(DataError) as exc_info:
        read_bounded_show_bank_file(target, maximum=10)
    assert show_bank_corruption_category(exc_info.value) == "size"
    monkeypatch.setattr(store_module.os, "open", original_open)
    target.write_bytes(b"payload")

    def broken_open(path: Path, *args, **kwargs):
        if path == target:
            raise OSError("blocked")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(store_module.os, "open", broken_open)
    with pytest.raises(DataError) as exc_info:
        read_bounded_show_bank_file(target, maximum=10)
    assert show_bank_corruption_category(exc_info.value) == "access"
    monkeypatch.setattr(store_module.os, "open", original_open)

    stat_calls = 0

    def changing_stat(path: Path, *, follow_symlinks: bool = True):
        nonlocal stat_calls
        result = original_stat(path, follow_symlinks=follow_symlinks)
        if path != target:
            return result
        stat_calls += 1
        if stat_calls == 1:
            return result
        return SimpleNamespace(
            st_mode=result.st_mode,
            st_dev=result.st_dev,
            st_ino=result.st_ino,
            st_size=result.st_size,
            st_mtime_ns=result.st_mtime_ns + 1,
        )

    monkeypatch.setattr(Path, "stat", changing_stat)
    with pytest.raises(DataError) as exc_info:
        read_bounded_show_bank_file(target, maximum=10)
    assert show_bank_corruption_category(exc_info.value) == "access"


def test_store_root_and_listing_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ShowBankStore(tmp_path / "new")
    assert store.root == tmp_path / "new"
    assert store.latest_revision("bank") is None
    assert store.list_banks() == ()
    with pytest.raises(DataError, match="does not exist"):
        store.load("bank")

    regular_file = tmp_path / "file"
    regular_file.write_text("x", encoding="utf-8")
    with pytest.raises(DataError) as exc_info:
        store_module._show_bank_directory_identity(regular_file)
    assert show_bank_corruption_category(exc_info.value) == "path"

    root = tmp_path / "root"
    root.mkdir()
    linked = ShowBankStore(root)
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda path: path == root or original_is_symlink(path),
    )
    with pytest.raises(DataError) as exc_info:
        linked.latest_revision("bank")
    assert show_bank_corruption_category(exc_info.value) == "path"
    with pytest.raises(DataError) as exc_info:
        linked.list_banks()
    assert show_bank_corruption_category(exc_info.value) == "path"
    with pytest.raises(DataError) as exc_info:
        linked.save(source_bank())
    assert show_bank_corruption_category(exc_info.value) == "path"
    monkeypatch.setattr(Path, "is_symlink", original_is_symlink)

    original_iterdir = Path.iterdir

    def broken_iterdir(path: Path):
        if path == root:
            raise OSError("blocked")
        return original_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", broken_iterdir)
    with pytest.raises(DataError) as exc_info:
        linked.latest_revision("bank")
    assert show_bank_corruption_category(exc_info.value) == "access"
    with pytest.raises(DataError) as exc_info:
        linked.list_banks()
    assert show_bank_corruption_category(exc_info.value) == "access"


def test_store_creation_schema_and_identity_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "blocked"
    original_mkdir = Path.mkdir

    def broken_mkdir(path: Path, *args, **kwargs):
        if path == root:
            raise OSError("blocked")
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", broken_mkdir)
    with pytest.raises(DataError) as exc_info:
        ShowBankStore(root).save(source_bank())
    assert show_bank_corruption_category(exc_info.value) == "access"
    monkeypatch.setattr(Path, "mkdir", original_mkdir)

    store = ShowBankStore(tmp_path / "store")
    store.root.mkdir()
    schema_path = store.root / "bank.r00000001.show-bank.json"
    schema_path.write_bytes(b"{}")
    with pytest.raises(DataError) as exc_info:
        store.load("bank", revision=1)
    assert show_bank_corruption_category(exc_info.value) == "schema"

    bank = source_bank()
    other_path = store.root / "other.r00000001.show-bank.json"
    other_path.write_bytes(canonical_show_bank_json(bank))
    with pytest.raises(DataError) as exc_info:
        store.load("other", revision=1)
    assert show_bank_corruption_category(exc_info.value) == "cross-reference"
    with pytest.raises(DataError) as exc_info:
        store_module._raise_show_bank_corruption("schema", "plain")
    assert "artifact_name" not in exc_info.value.context


def test_store_detects_retained_hash_and_collision_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ShowBankStore(tmp_path, clock=clock)
    source = source_bank()
    retained = store.retain_sysex(source, "rytm-source-frame", frame(1))
    artifact = retained.sysex_artifact("rytm-source-frame").retained
    assert artifact is not None
    (tmp_path / artifact.artifact_name).write_bytes(frame(9))
    with pytest.raises(DataError) as exc_info:
        store.read_retained(artifact)
    assert show_bank_corruption_category(exc_info.value) == "hash"

    (tmp_path / artifact.artifact_name).write_bytes(frame(1))
    with pytest.raises(ValueError, match="different exact bytes"):
        store.retain_sysex(retained, "rytm-source-frame", frame(9))

    preexisting = ShowBankStore(tmp_path / "preexisting", clock=clock)
    preexisting.root.mkdir()
    expected = source.sysex_artifact("rytm-source-frame")
    capture_path = preexisting.root / f"{expected.frame_sha256}.syx"
    capture_path.write_bytes(frame(1))
    updated = preexisting.retain_sysex(source, "rytm-source-frame", frame(1))
    assert updated.sysex_artifact("rytm-source-frame").retained is not None

    collision = ShowBankStore(tmp_path / "collision", clock=clock)
    collision.root.mkdir()
    collision_path = collision.root / f"{expected.frame_sha256}.syx"
    collision_path.write_bytes(frame(1))
    monkeypatch.setattr(collision, "read_retained", lambda artifact: frame(9))
    with pytest.raises(DataError, match="collision"):
        collision.retain_sysex(source, "rytm-source-frame", frame(1))


def test_import_verified_validates_exact_set_types_identity_and_existing_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_store = ShowBankStore(tmp_path / "source", clock=clock)
    bank = retained_source_bank(source_store)
    frames = {
        "rytm-source-frame": frame(1),
        "a4-source-frame": frame(2),
    }
    target = ShowBankStore(tmp_path / "target")
    with pytest.raises(ValueError, match="exactly match"):
        target.import_verified(bank, {})
    with pytest.raises(TypeError, match="bytes"):
        target.import_verified(
            bank,
            {"rytm-source-frame": "bad", "a4-source-frame": frame(2)},  # type: ignore[dict-item]
        )
    with pytest.raises(ValueError, match="declared identity"):
        target.import_verified(
            bank,
            {"rytm-source-frame": frame(9), "a4-source-frame": frame(2)},
        )

    writes = target.import_verified(bank, frames)
    assert writes[-1].path.name.endswith("show-bank.json")
    with pytest.raises(FileExistsError):
        target.import_verified(bank, frames)

    collision = ShowBankStore(tmp_path / "collision")
    collision.root.mkdir()
    retained = bank.sysex_artifact("a4-source-frame").retained
    assert retained is not None
    (collision.root / retained.artifact_name).write_bytes(frame(2))
    monkeypatch.setattr(collision, "read_retained", lambda artifact: frame(9))
    with pytest.raises(DataError, match="collision"):
        collision.import_verified(bank, frames)


@pytest.mark.parametrize("operation", ["manifest", "retained"])
def test_reads_reject_store_directory_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    store = ShowBankStore(tmp_path / "store", clock=clock)
    bank = retained_source_bank(store)
    artifact = bank.sysex_artifact("rytm-source-frame").retained
    assert artifact is not None
    original_read = store_module.read_bounded_show_bank_file
    displaced = tmp_path / "displaced-store"

    def replace_root_after_read(path: Path, *, maximum: int) -> bytes:
        payload = original_read(path, maximum=maximum)
        store.root.rename(displaced)
        store.root.mkdir()
        return payload

    monkeypatch.setattr(store_module, "read_bounded_show_bank_file", replace_root_after_read)
    with pytest.raises(DataError, match="store changed"):
        if operation == "manifest":
            store.load(bank.bank_id, revision=bank.revision, verify_retained=False)
        else:
            store.read_retained(artifact)
    assert (displaced / artifact.artifact_name).read_bytes() == frame(1)
    assert tuple(store.root.iterdir()) == ()


def test_reads_reject_unavailable_or_linked_store_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ShowBankStore(tmp_path / "store", clock=clock)
    bank = retained_source_bank(store)
    artifact = bank.sysex_artifact("rytm-source-frame").retained
    assert artifact is not None
    with pytest.raises(DataError, match="root is unavailable"):
        ShowBankStore(tmp_path / "missing").read_retained(artifact)
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path, "is_symlink", lambda path: path == store.root or original_is_symlink(path)
    )
    with pytest.raises(DataError, match="root cannot be a symlink"):
        store.load(bank.bank_id)
    with pytest.raises(DataError, match="root is unavailable"):
        store.read_retained(artifact)


@pytest.mark.parametrize("limit", ["manifest", "declared", "retained"])
def test_serialization_and_retention_size_limits_fail_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    store = ShowBankStore(tmp_path / "store", clock=clock)
    bank = source_bank()
    with pytest.raises(ValueError, match="cannot be empty"):
        store.retain_sysex_set(bank, {})
    if limit == "manifest":
        monkeypatch.setattr(store_module, "SHOW_BANK_MANIFEST_MAX_BYTES", 1)
        with pytest.raises(ValueError, match="manifest exceeds"):
            store.save(bank)
    else:
        monkeypatch.setattr(store_module, "SHOW_BANK_MAX_DECLARED_SYSEX_BYTES", 1)
        with pytest.raises(ValueError, match="aggregate size"):
            if limit == "declared":
                store.save(bank)
            else:
                store.retain_sysex_set(bank, {"rytm-source-frame": frame(1)})
    assert not store.root.exists()


def test_import_reuses_identical_existing_capture_without_overwriting_it(tmp_path: Path) -> None:
    source = ShowBankStore(tmp_path / "source", clock=clock)
    bank = retained_source_bank(source)
    target = ShowBankStore(tmp_path / "target")
    target.root.mkdir()
    artifact = bank.sysex_artifact("rytm-source-frame").retained
    assert artifact is not None
    existing = target.root / artifact.artifact_name
    existing.write_bytes(frame(1))
    before = existing.stat()
    writes = target.import_verified(
        bank, {"rytm-source-frame": frame(1), "a4-source-frame": frame(2)}
    )
    assert existing not in {write.path for write in writes}
    assert existing.stat().st_mtime_ns == before.st_mtime_ns
    assert target.load(bank.bank_id) == bank


def test_import_rechecks_namespace_reservation_under_publication_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = ShowBankStore(tmp_path / "source", clock=clock)
    bank = retained_source_bank(source)
    target = ShowBankStore(tmp_path / "target")
    original_publish = target._publish

    def reserve_before_publish(*args, **kwargs):
        marker = target.root / f"{bank.bank_id}{store_module.SHOW_BANK_NAMESPACE_SUFFIX}"
        marker.write_bytes(store_module.SHOW_BANK_NAMESPACE_PAYLOAD)
        return original_publish(*args, **kwargs)

    monkeypatch.setattr(target, "_publish", reserve_before_publish)
    with pytest.raises(FileExistsError, match="namespace already exists"):
        target.import_verified(bank, {"rytm-source-frame": frame(1), "a4-source-frame": frame(2)})
    assert tuple(target.root.glob("*.syx")) == ()
    assert target.latest_revision(bank.bank_id) is None


def test_retention_rejects_distinct_frames_colliding_in_one_write_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bank = source_bank()
    entry = bank.entries[0]
    digest = "a" * 64
    entry = replace(
        entry,
        rytm_source=replace(
            entry.rytm_source, sysex=replace(entry.rytm_source.sysex, frame_sha256=digest)
        ),
        analog_four_source=replace(
            entry.analog_four_source,
            sysex=replace(entry.analog_four_source.sysex, frame_sha256=digest),
        ),
    )
    bank = replace(bank, entries=(entry,))
    # Exercise the content-address collision boundary without depending on
    # an actual collision in SHA-256 or relaxing the exact-byte comparison.
    monkeypatch.setattr(
        store_module.hashlib, "sha256", lambda payload: SimpleNamespace(hexdigest=lambda: digest)
    )
    store = ShowBankStore(tmp_path / "store", clock=clock)
    with pytest.raises(DataError, match="content-addressed capture collision"):
        store.retain_sysex_set(bank, {"rytm-source-frame": frame(1), "a4-source-frame": frame(2)})
    assert tuple(store.root.iterdir()) == ()
