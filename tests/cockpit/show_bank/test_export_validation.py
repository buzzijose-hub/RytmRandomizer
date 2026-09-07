from __future__ import annotations

import dataclasses
import hashlib
import json
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from rytm_randomizer.cockpit.data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    ShowBank,
    ShowKitSysex,
)
from rytm_randomizer.cockpit.show_bank import export as export_module
from rytm_randomizer.cockpit.show_bank.export import (
    SHOW_PACK_CHECKSUMS_NAME,
    SHOW_PACK_CUE_ORDER_NAME,
    SHOW_PACK_MANIFEST_NAME,
    SHOW_PACK_RECOVERY_NAME,
    ShowPackArtifact,
    ShowPackManifest,
    ShowPackService,
    narrow_show_pack_artifact_kind,
)
from rytm_randomizer.cockpit.show_bank.readiness import (
    add_candidate,
    add_entry,
    attest_hardware_save,
    create_show_bank,
    mark_favorite,
    record_recapture,
)
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.observability.errors import DataError

from ._support import (
    A4_SEMANTIC_FINGERPRINT,
    A4_SOURCE_SEMANTIC_FINGERPRINT,
    LATER,
    NOW,
    RECORDED_AT,
    RYTM_SEMANTIC_FINGERPRINT,
    RYTM_SOURCE_SEMANTIC_FINGERPRINT,
    candidate,
    frame,
    recapture,
    source_entry,
)

pytestmark = pytest.mark.fast


def _clock():
    return LATER


def _source_bank() -> ShowBank:
    return add_entry(
        create_show_bank(bank_id="show", name="Show", clock=lambda: NOW),
        source_entry(),
        clock=_clock,
    )


def _retained_source_bank(store: ShowBankStore) -> ShowBank:
    bank = _source_bank()
    bank = store.retain_sysex(bank, "rytm-source-frame", frame(1))
    return store.retain_sysex(bank, "a4-source-frame", frame(2))


def _exported(tmp_path: Path, package_id: str = "package"):
    store = ShowBankStore(tmp_path / "store", clock=_clock)
    bank = _retained_source_bank(store)
    service = ShowPackService(tmp_path / "packages", store=store)
    result = service.export(bank, package_id=package_id)
    return service, result


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


def _rewrite_payload(package: Path, name: str, payload: bytes) -> None:
    (package / name).write_bytes(payload)
    manifest_path = package / SHOW_PACK_MANIFEST_NAME
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    for artifact in raw["artifacts"]:
        if artifact["name"] == name:
            artifact["sha256"] = hashlib.sha256(payload).hexdigest()
            artifact["byte_count"] = len(payload)
    manifest_path.write_bytes(_canonical(raw))
    artifacts = tuple(ShowPackArtifact.from_dict(item) for item in raw["artifacts"])
    (package / SHOW_PACK_CHECKSUMS_NAME).write_bytes(export_module._checksums_payload(artifacts))


def test_show_pack_artifact_validation_and_strict_decoding() -> None:
    digest = "a" * 64
    valid = ShowPackArtifact("a.syx", "capture", digest, 3, ("frame",))
    assert ShowPackArtifact.from_dict(valid.to_dict()) == valid
    assert narrow_show_pack_artifact_kind("capture") == "capture"
    with pytest.raises(ValueError, match="invalid"):
        narrow_show_pack_artifact_kind("other")

    changes = (
        {"name": "../a.syx"},
        {"name": SHOW_PACK_MANIFEST_NAME},
        {"kind": "other"},
        {"sha256": "bad"},
        {"byte_count": 0},
        {"artifact_ids": ("frame", "frame")},
        {"artifact_ids": ("Bad",)},
        {"artifact_ids": ()},
        {"name": "capture.bin"},
        {"kind": "cue-order", "artifact_ids": ("frame",)},
    )
    for change in changes:
        with pytest.raises(ValueError):
            dataclasses.replace(valid, **change)

    with pytest.raises(TypeError, match="object"):
        ShowPackArtifact.from_dict([])  # type: ignore[arg-type]
    raw = valid.to_dict()
    raw.pop("kind")
    with pytest.raises(ValueError, match="keys"):
        ShowPackArtifact.from_dict(raw)
    raw = valid.to_dict()
    raw["name"] = 1
    with pytest.raises(TypeError, match="string"):
        ShowPackArtifact.from_dict(raw)
    raw = valid.to_dict()
    raw["byte_count"] = True
    with pytest.raises(TypeError, match="integer"):
        ShowPackArtifact.from_dict(raw)
    raw = valid.to_dict()
    raw["artifact_ids"] = {}
    with pytest.raises(TypeError, match="list"):
        ShowPackArtifact.from_dict(raw)
    raw = valid.to_dict()
    raw["artifact_ids"] = [1]
    with pytest.raises(TypeError, match="strings"):
        ShowPackArtifact.from_dict(raw)


def test_show_pack_manifest_validation_is_exhaustive(tmp_path: Path) -> None:
    _, exported = _exported(tmp_path)
    manifest = exported.manifest

    for change in (
        {"schema_version": "other"},
        {"checksums_file": "other"},
        {"artifacts": ()},
        {"artifacts": (manifest.artifacts[0],) * 3},
        {"cue_order": ("missing",)},
        {"recovery": tuple("line" for _ in range(257))},
        {"recovery": ("",)},
        {"recovery": ("x" * 513,)},
        {"recovery": ("nul\x00",)},
    ):
        with pytest.raises(ValueError):
            dataclasses.replace(manifest, **change)

    cue = next(item for item in manifest.artifacts if item.kind == "cue-order")
    recovery = next(item for item in manifest.artifacts if item.kind == "recovery")
    capture_artifacts = tuple(item for item in manifest.artifacts if item.kind == "capture")
    with pytest.raises(ValueError, match="cue-order"):
        dataclasses.replace(
            manifest,
            artifacts=(*capture_artifacts, dataclasses.replace(cue, kind="recovery"), recovery),
        )
    replacement_capture = dataclasses.replace(
        capture_artifacts[0],
        name="extra.syx",
        artifact_ids=("extra",),
    )
    with pytest.raises(ValueError, match="recovery"):
        dataclasses.replace(
            manifest,
            artifacts=(*capture_artifacts, cue, replacement_capture),
        )
    with pytest.raises(ValueError, match="retained bank evidence"):
        dataclasses.replace(
            manifest,
            artifacts=(
                dataclasses.replace(capture_artifacts[0], artifact_ids=("other",)),
                *capture_artifacts[1:],
                cue,
                recovery,
            ),
        )

    with pytest.raises(TypeError, match="object"):
        ShowPackManifest.from_dict([])  # type: ignore[arg-type]
    raw = manifest.to_dict()
    raw.pop("format")
    with pytest.raises(ValueError, match="keys"):
        ShowPackManifest.from_dict(raw)


def test_export_includes_favorite_candidate_and_recapture_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = ShowBankStore(tmp_path / "store", clock=_clock)
    bank = add_candidate(_source_bank(), "entry-one", candidate(), select=True, clock=_clock)
    bank = mark_favorite(bank, "entry-one", clock=_clock)
    for device_id in (RYTM_SHOW_KIT_DEVICE_ID, A4_SHOW_KIT_DEVICE_ID):
        bank = attest_hardware_save(
            bank,
            "entry-one",
            device_id=device_id,
            hardware_slot=64,
            note="saved",
            clock=_clock,
        )
    bank = record_recapture(
        bank,
        "entry-one",
        recapture(RYTM_SHOW_KIT_DEVICE_ID),
        source_semantic_fingerprint=RYTM_SOURCE_SEMANTIC_FINGERPRINT,
        observed_semantic_fingerprint=RYTM_SEMANTIC_FINGERPRINT,
        comparison_reason="matched",
        clock=lambda: RECORDED_AT,
    )
    bank = record_recapture(
        bank,
        "entry-one",
        recapture(A4_SHOW_KIT_DEVICE_ID),
        source_semantic_fingerprint=A4_SOURCE_SEMANTIC_FINGERPRINT,
        observed_semantic_fingerprint=A4_SEMANTIC_FINGERPRINT,
        comparison_reason="matched",
        clock=lambda: RECORDED_AT,
    )
    frames = {
        "rytm-source-frame": frame(1),
        "a4-source-frame": frame(2),
        "candidate-one-a4-frame": frame(3),
        "rytm-favorite-capture-frame": frame(4),
        "a4-favorite-capture-frame": frame(5),
    }
    for artifact_id, payload in frames.items():
        bank = store.retain_sysex(bank, artifact_id, payload)
    service = ShowPackService(tmp_path / "packages", store=store)
    result = service.export(bank)
    monkeypatch.setattr(export_module, "_verify_package_device_claims", lambda bank, frames: None)
    assert service.package_root == tmp_path / "packages"
    verified = service.verify(result.package_id)
    assert verified.frames_by_artifact_id == frames


def test_export_skips_unretained_nonfavorite_candidate(tmp_path: Path) -> None:
    store = ShowBankStore(tmp_path / "store", clock=_clock)
    bank = add_candidate(_source_bank(), "entry-one", candidate(), clock=_clock)
    bank = store.retain_sysex(bank, "rytm-source-frame", frame(1))
    bank = store.retain_sysex(bank, "a4-source-frame", frame(2))
    result = ShowPackService(tmp_path / "packages", store=store).export(bank)
    assert "candidate-one-a4-frame" not in {item.name for item in result.manifest.artifacts}


def test_export_rejects_one_retained_name_resolving_to_conflicting_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = source_entry()
    shared_sysex = ShowKitSysex(
        artifact_id="a4-source-frame",
        frame_sha256=base.rytm_source.sysex.frame_sha256,
        frame_bytes=base.rytm_source.sysex.frame_bytes,
    )
    entry = dataclasses.replace(
        base,
        analog_four_source=dataclasses.replace(base.analog_four_source, sysex=shared_sysex),
    )
    bank = add_entry(
        create_show_bank(bank_id="show", name="Show", clock=lambda: NOW),
        entry,
        clock=_clock,
    )
    store = ShowBankStore(tmp_path / "store", clock=_clock)
    bank = store.retain_sysex(bank, "rytm-source-frame", frame(1))
    bank = store.retain_sysex(bank, "a4-source-frame", frame(1))
    reads = iter((frame(1), frame(9)))
    monkeypatch.setattr(store, "read_retained", lambda artifact: next(reads))
    with pytest.raises(DataError, match="conflicting bytes"):
        ShowPackService(tmp_path / "packages", store=store).export(bank)


def test_export_directory_failures_are_categorical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ShowBankStore(tmp_path / "store", clock=_clock)
    bank = _retained_source_bank(store)

    root = tmp_path / "linked"
    root.mkdir()
    service = ShowPackService(root, store=store)
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda path: path == root or original_is_symlink(path),
    )
    with pytest.raises(DataError, match="symlink"):
        service.export(bank)
    monkeypatch.setattr(Path, "is_symlink", original_is_symlink)

    blocked = tmp_path / "blocked"
    service = ShowPackService(blocked, store=store)
    original_mkdir = Path.mkdir

    def blocked_mkdir(path: Path, *args, **kwargs):
        if path == blocked:
            raise OSError("blocked")
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", blocked_mkdir)
    with pytest.raises(DataError, match="root cannot be created"):
        service.export(bank)
    monkeypatch.setattr(Path, "mkdir", original_mkdir)

    root = tmp_path / "packages"
    package = root / "package.show-pack"

    def package_mkdir(path: Path, *args, **kwargs):
        if path == package:
            raise OSError("blocked")
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", package_mkdir)
    with pytest.raises(DataError, match="package directory"):
        ShowPackService(root, store=store).export(bank, package_id="package")
    monkeypatch.setattr(Path, "mkdir", original_mkdir)

    original_stat = Path.stat

    def regular_stat(path: Path, *, follow_symlinks: bool = True):
        result = original_stat(path, follow_symlinks=follow_symlinks)
        if path != package:
            return result
        return SimpleNamespace(st_mode=stat.S_IFREG, st_dev=result.st_dev, st_ino=result.st_ino)

    monkeypatch.setattr(Path, "stat", regular_stat)
    with pytest.raises(DataError, match="not a directory"):
        ShowPackService(root, store=store).export(bank, package_id="package")


def test_verify_categorizes_missing_schema_identity_canonical_and_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ShowBankStore(tmp_path / "store")
    missing = ShowPackService(tmp_path / "missing", store=store)
    with pytest.raises(DataError, match="missing"):
        missing.verify("package")

    service, result = _exported(tmp_path / "schema", "package")
    manifest_path = result.package_dir / SHOW_PACK_MANIFEST_NAME
    manifest_path.write_bytes(b"not json")
    with pytest.raises(DataError, match="schema validation"):
        service.verify("package")

    service, result = _exported(tmp_path / "identity", "package")
    raw = result.manifest.to_dict()
    raw["package_id"] = "other"
    (result.package_dir / SHOW_PACK_MANIFEST_NAME).write_bytes(_canonical(raw))
    with pytest.raises(DataError, match="does not match"):
        service.verify("package")

    service, result = _exported(tmp_path / "canonical", "package")
    manifest_path = result.package_dir / SHOW_PACK_MANIFEST_NAME
    manifest_path.write_bytes(manifest_path.read_bytes() + b" ")
    with pytest.raises(DataError, match="canonical JSON"):
        service.verify("package")

    service, result = _exported(tmp_path / "access", "package")
    original_iterdir = Path.iterdir

    def broken_iterdir(path: Path):
        if path == result.package_dir:
            raise OSError("blocked")
        return original_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", broken_iterdir)
    with pytest.raises(DataError, match="cannot be listed"):
        service.verify("package")


def test_verify_categorizes_size_checksums_recovery_and_framing(tmp_path: Path) -> None:
    service, result = _exported(tmp_path / "size", "package")
    cue = result.package_dir / SHOW_PACK_CUE_ORDER_NAME
    cue.write_bytes(cue.read_bytes()[:-1])
    with pytest.raises(DataError, match="size mismatch"):
        service.verify("package")

    service, result = _exported(tmp_path / "checksums", "package")
    checksums = result.package_dir / SHOW_PACK_CHECKSUMS_NAME
    checksums.write_bytes(checksums.read_bytes().replace(b"a", b"b", 1))
    with pytest.raises(DataError, match="checksum list"):
        service.verify("package")

    service, result = _exported(tmp_path / "recovery", "package")
    recovery = result.package_dir / SHOW_PACK_RECOVERY_NAME
    _rewrite_payload(
        result.package_dir, SHOW_PACK_RECOVERY_NAME, recovery.read_bytes() + b"changed\n"
    )
    with pytest.raises(DataError, match="recovery file"):
        service.verify("package")

    service, result = _exported(tmp_path / "framing", "package")
    capture_path = next(result.package_dir.glob("*.syx"))
    _rewrite_payload(result.package_dir, capture_path.name, b"abc")
    with pytest.raises(DataError, match="framing"):
        service.verify("package")


def test_manifest_rejects_non_string_keys_and_structurally_invalid_json(tmp_path: Path) -> None:
    with pytest.raises(DataError, match="directory cannot be inspected"):
        export_module._show_pack_directory_identity(tmp_path / "missing-directory")
    with pytest.raises(TypeError, match="string keys"):
        ShowPackManifest.from_dict({1: "untrusted"})  # type: ignore[dict-item]
    service, result = _exported(tmp_path)
    manifest = result.package_dir / SHOW_PACK_MANIFEST_NAME
    for payload in (b"[]\n", b"{}\n"):
        manifest.write_bytes(payload)
        with pytest.raises(DataError, match="schema validation") as failure:
            service.verify(result.package_id)
        assert failure.value.context["category"] == "schema"


@pytest.mark.parametrize("limit", ["json", "artifacts"])
def test_export_bounds_refuse_package_before_reserving_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    store = ShowBankStore(tmp_path / "store", clock=_clock)
    bank = _retained_source_bank(store)
    service = ShowPackService(tmp_path / "packages", store=store)
    if limit == "json":
        monkeypatch.setattr(export_module, "SHOW_PACK_MAX_ARTIFACT_BYTES", 1)
    else:
        monkeypatch.setattr(export_module, "SHOW_PACK_MAX_ARTIFACTS", 3)
    with pytest.raises(ValueError, match="supported.*bound"):
        service.export(bank, package_id="bounded")
    assert not service.package_root.exists()


def test_export_rejects_conflicting_sizes_for_one_content_address(tmp_path: Path) -> None:
    store = ShowBankStore(tmp_path / "store", clock=_clock)
    bank = _retained_source_bank(store)
    entry = bank.entries[0]
    rytm = entry.rytm_source.sysex
    assert rytm.retained is not None
    alias = dataclasses.replace(
        rytm,
        artifact_id=entry.analog_four_source.sysex.artifact_id,
        frame_bytes=rytm.frame_bytes + 1,
        retained=dataclasses.replace(rytm.retained, byte_count=rytm.frame_bytes + 1),
    )
    bank = dataclasses.replace(
        bank,
        entries=(
            dataclasses.replace(
                entry, analog_four_source=dataclasses.replace(entry.analog_four_source, sysex=alias)
            ),
        ),
    )
    service = ShowPackService(tmp_path / "packages", store=store)
    with pytest.raises(DataError, match="conflicting sizes"):
        service.export(bank)
    assert not service.package_root.exists()


@pytest.mark.parametrize("damage", ["linked-root", "unreadable", "not-directory", "too-many"])
def test_verify_rejects_unsafe_or_unbounded_package_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    service, result = _exported(tmp_path)
    original_stat = Path.stat
    original_symlink = Path.is_symlink

    def damaged_stat(path: Path, *, follow_symlinks: bool = True):
        metadata = original_stat(path, follow_symlinks=follow_symlinks)
        if path != result.package_dir or follow_symlinks:
            return metadata
        if damage == "unreadable":
            raise PermissionError("package cannot be inspected")
        return SimpleNamespace(st_mode=stat.S_IFREG)

    if damage == "linked-root":
        monkeypatch.setattr(
            Path, "is_symlink", lambda path: path == service.package_root or original_symlink(path)
        )
    elif damage == "too-many":
        monkeypatch.setattr(export_module, "SHOW_PACK_MAX_DIRECTORY_ENTRIES", 1)
    else:
        monkeypatch.setattr(Path, "stat", damaged_stat)
    with pytest.raises(DataError) as failure:
        service.verify(result.package_id)
    expected = {
        "linked-root": "path",
        "unreadable": "access",
        "not-directory": "path",
        "too-many": "size",
    }
    assert failure.value.context["category"] == expected[damage]


@pytest.mark.parametrize("damage", ["replaced", "nonempty", "missing"])
def test_failed_export_preserves_recovery_data_and_primary_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    store = ShowBankStore(tmp_path / "store", clock=_clock)
    bank = _retained_source_bank(store)
    service = ShowPackService(tmp_path / "packages", store=store)
    package = service.package_root / "interrupted.show-pack"
    displaced = tmp_path / "reserved-directory"
    failure = OSError("publication interrupted")

    def fail_publication(*args, **kwargs):
        if damage == "nonempty":
            (package / "recovery-payload").write_bytes(b"keep transaction evidence")
        else:
            package.rename(displaced)
            if damage == "replaced":
                package.mkdir()
        raise failure

    monkeypatch.setattr(export_module, "atomic_write_set", fail_publication)
    with pytest.raises(OSError, match="publication interrupted") as raised:
        service.export(bank, package_id="interrupted")
    assert raised.value is failure
    assert package.exists() is (damage != "missing")
    if damage == "nonempty":
        assert (package / "recovery-payload").read_bytes() == b"keep transaction evidence"
    else:
        assert displaced.is_dir()
