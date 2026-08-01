"""Tests for the WS-4 kit/sound library store + captures importer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "tests") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "tests"))

from conftest import rytm_real_layout_kit_payload  # noqa: E402 - path bootstrap above
from rytm_randomizer.cockpit.library import (  # noqa: E402
    LibraryImportResult,
    LibraryRecord,
    LibraryStore,
    default_captures_dir,
    default_library_dir,
    payload_fingerprint,
)
from rytm_randomizer.cockpit.profiles.paths import default_profiles_dir  # noqa: E402

pytestmark = pytest.mark.fast


def _record(record_id: str = "abc123", tags: tuple[str, ...] = ("techno",)) -> LibraryRecord:
    return LibraryRecord(
        record_id=record_id,
        device_id="analog_rytm_mk2",
        kit_name="MYKIT",
        fingerprint=record_id,
        captured_at="2026-07-28T00:00:00+00:00",
        tags=tags,
        payload_hex="00203c",
    )


def _write_record(library_dir: Path, record: LibraryRecord) -> None:
    library_dir.mkdir(parents=True, exist_ok=True)
    (library_dir / f"{record.record_id}.json").write_text(
        json.dumps(record.to_dict()), encoding="utf-8"
    )


def _syx_file(directory: Path, name: str, payload: bytes) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_bytes(b"\xf0" + payload + b"\xf7")
    return path


# ---------------------------------------------------------------------------
# Paths + record shape.
# ---------------------------------------------------------------------------


def test_default_library_dir_is_sibling_of_profiles_leaf() -> None:
    assert default_library_dir() == default_profiles_dir().parent / "library"


def test_default_captures_dir_is_cwd_captures() -> None:
    assert default_captures_dir() == Path.cwd() / "captures"


def test_record_round_trips_through_dict() -> None:
    record = _record()
    assert LibraryRecord.from_dict(record.to_dict()) == record


def test_record_from_dict_rejects_bad_record_id() -> None:
    raw = _record().to_dict()
    raw["record_id"] = "../evil"
    with pytest.raises(ValueError, match="invalid library record_id"):
        LibraryRecord.from_dict(raw)


def test_record_from_dict_rejects_non_list_tags() -> None:
    raw = _record().to_dict()
    raw["tags"] = "techno"
    with pytest.raises(ValueError, match="non-list tags"):
        LibraryRecord.from_dict(raw)


def test_record_matches_searches_all_fields_case_insensitively() -> None:
    record = _record(tags=("Rolling", "Hypnotic"))
    assert record.matches("") is True
    assert record.matches("mykit") is True
    assert record.matches("RYTM") is True
    assert record.matches("abc12") is True
    assert record.matches("hypno") is True
    assert record.matches("nope") is False


def test_payload_fingerprint_is_stable_16_hex_chars() -> None:
    fp = payload_fingerprint(b"\x00\x20\x3c")
    assert fp == payload_fingerprint(b"\x00\x20\x3c")
    assert len(fp) == 16
    assert int(fp, 16) >= 0


# ---------------------------------------------------------------------------
# Store CRUD.
# ---------------------------------------------------------------------------


def test_list_records_empty_when_dir_missing(tmp_path: Path) -> None:
    store = LibraryStore(tmp_path / "library")
    assert store.list_records() == ()


def test_list_records_sorted_and_skips_malformed(tmp_path: Path) -> None:
    library_dir = tmp_path / "library"
    _write_record(library_dir, _record("bbb1"))
    _write_record(library_dir, _record("aaa1"))
    (library_dir / "junk.json").write_text("{not json", encoding="utf-8")
    (library_dir / "wrongshape.json").write_text('["list"]', encoding="utf-8")
    (library_dir / "badid.json").write_text(json.dumps({"record_id": "../evil"}), encoding="utf-8")
    store = LibraryStore(library_dir)
    assert [r.record_id for r in store.list_records()] == ["aaa1", "bbb1"]


def test_get_returns_record_or_none(tmp_path: Path) -> None:
    library_dir = tmp_path / "library"
    record = _record()
    _write_record(library_dir, record)
    store = LibraryStore(library_dir)
    assert store.get("abc123") == record
    assert store.get("missing1") is None


def test_get_rejects_traversal_record_id(tmp_path: Path) -> None:
    store = LibraryStore(tmp_path / "library")
    with pytest.raises(ValueError, match="invalid library record_id"):
        store.get("../secrets")


def test_search_filters_records(tmp_path: Path) -> None:
    library_dir = tmp_path / "library"
    _write_record(library_dir, _record("aaa1", tags=("rolling",)))
    _write_record(library_dir, _record("bbb1", tags=("peaktime",)))
    store = LibraryStore(library_dir)
    assert [r.record_id for r in store.search("peaktime")] == ["bbb1"]
    assert len(store.search("")) == 2


def test_tag_replaces_tags_atomically(tmp_path: Path) -> None:
    library_dir = tmp_path / "library"
    _write_record(library_dir, _record())
    store = LibraryStore(library_dir)
    updated = store.tag("abc123", ["birmingham", "peak"])
    assert updated.tags == ("birmingham", "peak")
    # Persisted on disk, not only in memory.
    assert store.get("abc123").tags == ("birmingham", "peak")


def test_tag_unknown_record_raises(tmp_path: Path) -> None:
    store = LibraryStore(tmp_path / "library")
    with pytest.raises(ValueError, match="unknown library record_id"):
        store.tag("missing1", ["x"])


def test_delete_removes_record_and_reports(tmp_path: Path) -> None:
    library_dir = tmp_path / "library"
    _write_record(library_dir, _record())
    store = LibraryStore(library_dir)
    assert store.delete("abc123") is True
    assert store.get("abc123") is None
    assert store.delete("abc123") is False


def test_delete_rejects_traversal_record_id(tmp_path: Path) -> None:
    store = LibraryStore(tmp_path / "library")
    with pytest.raises(ValueError, match="invalid library record_id"):
        store.delete("../../etc/passwd")


# ---------------------------------------------------------------------------
# Captures importer — device-generic decode through the registry.
# ---------------------------------------------------------------------------


def test_import_requires_configured_captures_dir(tmp_path: Path) -> None:
    store = LibraryStore(tmp_path / "library")
    with pytest.raises(ValueError, match="not configured"):
        store.import_captures()


def test_import_requires_existing_captures_dir(tmp_path: Path) -> None:
    store = LibraryStore(tmp_path / "library", captures_dir=tmp_path / "nope")
    with pytest.raises(ValueError, match="does not exist"):
        store.import_captures()


def test_import_decodes_rytm_capture_via_devices_registry(tmp_path: Path) -> None:
    payload = rytm_real_layout_kit_payload(name=b"MYKIT")
    captures = tmp_path / "captures"
    _syx_file(captures, "kit.syx", payload)
    store = LibraryStore(tmp_path / "library", captures_dir=captures)
    result = store.import_captures()
    assert isinstance(result, LibraryImportResult)
    assert result.failed_files == ()
    assert result.skipped_existing == 0
    assert len(result.imported) == 1
    record = result.imported[0]
    assert record.device_id == "analog_rytm_mk2"
    assert record.kit_name == "MYKIT"
    assert record.record_id == payload_fingerprint(payload)
    assert record.fingerprint == record.record_id
    assert record.payload_hex == payload.hex()
    assert record.tags == ()
    assert record.captured_at  # mtime-derived ISO timestamp
    # Persisted: a fresh store over the same dir sees it.
    assert LibraryStore(tmp_path / "library").get(record.record_id) == record


def test_import_skips_already_imported_payloads(tmp_path: Path) -> None:
    payload = rytm_real_layout_kit_payload(name=b"MYKIT")
    captures = tmp_path / "captures"
    _syx_file(captures, "kit.syx", payload)
    store = LibraryStore(tmp_path / "library", captures_dir=captures)
    first = store.import_captures()
    assert len(first.imported) == 1
    second = store.import_captures()
    assert second.imported == ()
    assert second.skipped_existing == 1
    assert second.failed_files == ()


def test_import_dedupes_same_payload_across_files(tmp_path: Path) -> None:
    payload = rytm_real_layout_kit_payload(name=b"MYKIT")
    captures = tmp_path / "captures"
    _syx_file(captures, "a.syx", payload)
    _syx_file(captures, "b.syx", payload)
    store = LibraryStore(tmp_path / "library", captures_dir=captures)
    result = store.import_captures()
    assert len(result.imported) == 1
    assert result.skipped_existing == 1


def test_import_reports_undecodable_files(tmp_path: Path) -> None:
    captures = tmp_path / "captures"
    captures.mkdir()
    (captures / "junk.syx").write_bytes(b"\xf0\x01\x02\x03\xf7")
    (captures / "empty.syx").write_bytes(b"")
    (captures / "unterminated.syx").write_bytes(b"\xf0\x01\x02")
    store = LibraryStore(tmp_path / "library", captures_dir=captures)
    result = store.import_captures()
    assert result.imported == ()
    assert sorted(result.failed_files) == ["empty.syx", "junk.syx", "unterminated.syx"]


def test_import_result_to_dict_shape(tmp_path: Path) -> None:
    payload = rytm_real_layout_kit_payload(name=b"MYKIT")
    captures = tmp_path / "captures"
    _syx_file(captures, "kit.syx", payload)
    store = LibraryStore(tmp_path / "library", captures_dir=captures)
    packet = store.import_captures().to_dict()
    assert packet["imported_count"] == 1
    assert packet["skipped_existing"] == 0
    assert packet["failed_files"] == []
    assert packet["imported"][0]["kit_name"] == "MYKIT"


def test_decode_falls_back_to_first_candidate_when_no_clean_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.library import store as store_module

    class _JunkDevice:
        def decode_snapshot(self, _raw: bytes, _slot: int) -> object:
            class _Snap:
                kit_name = "\x00JUNK\x01"

            return _Snap()

    monkeypatch.setattr(store_module, "all_devices", lambda: {"junk_device": _JunkDevice()})
    assert store_module._decode_with_any_device(b"\x00\x20\x3c") == (
        "junk_device",
        "\x00JUNK\x01",
    )


def test_decode_returns_none_when_no_device_accepts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.library import store as store_module

    class _RefusingDevice:
        def decode_snapshot(self, _raw: bytes, _slot: int) -> object:
            raise ValueError("not mine")

    monkeypatch.setattr(store_module, "all_devices", lambda: {"refusing": _RefusingDevice()})
    assert store_module._decode_with_any_device(b"\x00\x20\x3c") is None


def test_capture_timestamp_falls_back_to_now_when_stat_fails() -> None:
    from rytm_randomizer.cockpit.library.store import _capture_timestamp

    class _StatlessPath:
        def stat(self) -> object:
            raise OSError("gone")

    stamp = _capture_timestamp(_StatlessPath())  # type: ignore[arg-type]
    assert stamp.endswith("+00:00")


def test_store_properties_expose_configuration(tmp_path: Path) -> None:
    library_dir = tmp_path / "library"
    captures = tmp_path / "captures"
    store = LibraryStore(library_dir, captures_dir=captures)
    assert store.library_dir == library_dir
    assert store.captures_dir == captures
    assert LibraryStore(library_dir).captures_dir is None
