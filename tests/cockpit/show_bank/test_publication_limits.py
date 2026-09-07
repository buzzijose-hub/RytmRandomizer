from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.show_bank import store as store_module
from rytm_randomizer.cockpit.show_bank.readiness import add_entry, create_show_bank
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore, read_bounded_show_bank_file
from rytm_randomizer.observability.errors import DataError

from ._support import LATER, NOW, source_entry

pytestmark = pytest.mark.fast


@pytest.mark.parametrize("limit", ["banks", "revisions", "files"])
def test_publication_refuses_over_capacity_without_breaking_existing_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    store = ShowBankStore(tmp_path / "store")
    bank = create_show_bank(bank_id="first", name="First", clock=lambda: NOW)
    store.save(bank)
    original_names = sorted(path.name for path in store.root.iterdir())
    if limit == "banks":
        monkeypatch.setattr(store_module, "SHOW_BANK_MAX_BANKS", 1)
        proposed = replace(bank, bank_id="second")
    elif limit == "revisions":
        monkeypatch.setattr(store_module, "SHOW_BANK_MAX_REVISIONS_PER_BANK", 1)
        proposed = replace(bank, revision=bank.revision + 1)
    else:
        # Two existing files + the transient cooperative lock fit. The next
        # revision would exceed this bound while publication is in progress.
        monkeypatch.setattr(store_module, "SHOW_BANK_MAX_DIRECTORY_ENTRIES", 3)
        proposed = replace(bank, revision=bank.revision + 1)
    with pytest.raises(DataError, match="cannot accept") as failure:
        store.save(proposed)
    assert failure.value.context["category"] == "size"
    assert sorted(path.name for path in store.root.iterdir()) == original_names
    assert store.list_banks() == (bank,)


def test_bounded_read_rejects_replacement_open_before_reading_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = tmp_path / "expected"
    replacement = tmp_path / "replacement"
    expected.write_bytes(b"expected")
    replacement.write_bytes(b"untrusted")
    original_open = store_module.os.open

    def replaced_open(path, flags):
        return original_open(replacement if path == expected else path, flags)

    monkeypatch.setattr(store_module.os, "open", replaced_open)
    with pytest.raises(DataError, match="changed during open"):
        read_bounded_show_bank_file(expected, maximum=16)


def test_publication_preserves_revision_and_creation_lineage(tmp_path: Path) -> None:
    store = ShowBankStore(tmp_path / "store")
    bank = create_show_bank(bank_id="first", name="First", clock=lambda: NOW)
    store.save(bank)
    advanced = replace(bank, revision=4, updated_at=LATER)
    store.save(advanced)
    with pytest.raises(ValueError, match="strictly forward"):
        store.save(replace(bank, revision=2))
    with pytest.raises(ValueError, match="created_at is immutable"):
        store.save(replace(advanced, revision=5, created_at=LATER))
    added = add_entry(advanced, source_entry(), clock=lambda: LATER)
    store.save(added)
    assert store.load(bank.bank_id) == added
    assert len(tuple(store.root.glob("*.show-bank.json"))) == 3


def test_publication_refuses_concurrent_lock_without_touching_catalog(tmp_path: Path) -> None:
    store = ShowBankStore(tmp_path / "store")
    bank = create_show_bank(bank_id="first", name="First", clock=lambda: NOW)
    store.save(bank)
    lock = (
        store.root
        / f".first{store_module.SHOW_BANK_NAMESPACE_SUFFIX}{store_module.SHOW_BANK_LOCK_SUFFIX}"
    )
    lock.mkdir()
    with pytest.raises(FileExistsError, match="already locked"):
        store.save(replace(bank, revision=2))
    assert store.load(bank.bank_id) == bank
    assert lock.is_dir()


@pytest.mark.parametrize("publication_fails", [False, True])
def test_lock_cleanup_failure_preserves_original_publication_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, publication_fails: bool
) -> None:
    store = ShowBankStore(tmp_path / "store")
    bank = create_show_bank(bank_id="first", name="First", clock=lambda: NOW)
    original_rmdir = Path.rmdir

    def blocked_lock_cleanup(path: Path) -> None:
        if path.name.endswith(store_module.SHOW_BANK_LOCK_SUFFIX):
            raise PermissionError("lock directory busy")
        original_rmdir(path)

    monkeypatch.setattr(Path, "rmdir", blocked_lock_cleanup)
    if publication_fails:
        failure = OSError("publication unavailable")

        def fail_publication(*args, **kwargs):
            raise failure

        monkeypatch.setattr(store_module, "atomic_write_set", fail_publication)
        with pytest.raises(OSError, match="publication unavailable") as raised:
            store.save(bank)
        assert raised.value is failure
        assert "lock cleanup also failed" in raised.value.__notes__[0]
        assert store.latest_revision(bank.bank_id) is None
    else:
        with pytest.raises(DataError, match="lock cannot be released"):
            store.save(bank)
        assert store.load(bank.bank_id) == bank


@pytest.mark.parametrize("damage", ["unreadable", "directory", "invalid", "reserved"])
def test_namespace_damage_cannot_be_reused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    store = ShowBankStore(tmp_path / "store")
    store.root.mkdir()
    bank = create_show_bank(bank_id="first", name="First", clock=lambda: NOW)
    marker = store.root / f"first{store_module.SHOW_BANK_NAMESPACE_SUFFIX}"
    if damage == "directory":
        marker.mkdir()
    else:
        marker.write_bytes(
            b"invalid" if damage == "invalid" else store_module.SHOW_BANK_NAMESPACE_PAYLOAD
        )
    original_stat = Path.stat

    def inaccessible_marker(path: Path, *args, **kwargs):
        if path == marker:
            raise PermissionError("marker unavailable")
        return original_stat(path, *args, **kwargs)

    if damage == "unreadable":
        monkeypatch.setattr(Path, "stat", inaccessible_marker)
    expected = FileExistsError if damage == "reserved" else DataError
    with pytest.raises(expected):
        store.save(bank)
    assert tuple(store.root.glob("*.show-bank.json")) == ()


@pytest.mark.parametrize("limit", ["banks", "revisions"])
def test_scan_refuses_an_existing_catalog_above_its_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    store = ShowBankStore(tmp_path / "store")
    bank = create_show_bank(bank_id="first", name="First", clock=lambda: NOW)
    store.save(bank)
    store.save(replace(bank, bank_id="second"))
    store.save(replace(bank, revision=2))
    if limit == "banks":
        monkeypatch.setattr(store_module, "SHOW_BANK_MAX_BANKS", 1)
        with pytest.raises(DataError, match="too many banks"):
            store.list_banks()
    else:
        monkeypatch.setattr(store_module, "SHOW_BANK_MAX_REVISIONS_PER_BANK", 1)
        with pytest.raises(DataError, match="revision history"):
            store.latest_revision(bank.bank_id)
