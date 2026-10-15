"""Pure local artifact reader contracts, with deterministic filesystem faults."""

from __future__ import annotations

import json
import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import BinaryIO

import pytest

from rytm_randomizer.cockpit.export import reader
from rytm_randomizer.observability.errors import DataError

pytestmark = pytest.mark.fast


@dataclass(frozen=True)
class _FileIdentity:
    st_mode: int
    st_dev: int
    st_ino: int
    st_size: int
    st_mtime_ns: int

    @classmethod
    def from_stat(cls, metadata: os.stat_result) -> _FileIdentity:
        return cls(
            metadata.st_mode,
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
        )


class _ReadProbe:
    def __init__(
        self,
        handle: BinaryIO,
        sizes: list[int],
        *,
        payload: bytes | None = None,
        fault: OSError | None = None,
    ) -> None:
        self.handle = handle
        self.sizes = sizes
        self.payload = payload
        self.fault = fault

    def fileno(self) -> int:
        return self.handle.fileno()

    def read(self, size: int) -> bytes:
        self.sizes.append(size)
        if self.fault is not None:
            raise self.fault
        return self.handle.read(size) if self.payload is None else self.payload[:size]


def _probe_reads(
    monkeypatch: pytest.MonkeyPatch,
    *,
    payload: bytes | None = None,
    fault: OSError | None = None,
) -> tuple[list[int], list[BinaryIO]]:
    fdopen = reader.os.fdopen
    sizes: list[int] = []
    handles: list[BinaryIO] = []

    @contextmanager
    def probed_fdopen(descriptor: int, mode: str) -> Iterator[_ReadProbe]:
        assert mode == "rb"
        with fdopen(descriptor, mode) as handle:
            handles.append(handle)
            yield _ReadProbe(handle, sizes, payload=payload, fault=fault)

    monkeypatch.setattr(reader.os, "fdopen", probed_fdopen)
    return sizes, handles


def _assert_private_refusal(error: DataError, path: Path, category: str) -> None:
    assert dict(error.context) == {"category": category, "artifact_name": path.name}
    assert str(path.parent) not in str(error)


@pytest.mark.parametrize("maximum", [4, 128])
def test_bounded_reader_returns_exact_bytes_without_changing_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, maximum: int
) -> None:
    path = tmp_path / "capture.syx"
    payload = b"\xf0\x00\x7f\xf7"
    path.write_bytes(payload)
    os.utime(path, ns=(1_700_000_000_000_000_000, 1_700_000_001_123_456_789))
    before = path.stat()
    sizes, handles = _probe_reads(monkeypatch)
    os_open = reader.os.open
    flags_seen: list[int] = []

    def inspect_open(candidate: Path, flags: int) -> int:
        assert candidate == path
        flags_seen.append(flags)
        return os_open(candidate, flags)

    monkeypatch.setattr(reader.os, "open", inspect_open)
    assert reader.read_bounded_artifact(path, maximum=maximum) == payload
    assert sizes == [maximum + 1]
    assert len(handles) == 1 and handles[0].closed
    assert len(flags_seen) == 1
    for flag in ("O_BINARY", "O_NOINHERIT", "O_NOFOLLOW", "O_NONBLOCK"):
        required = getattr(os, flag, 0)
        assert flags_seen[0] & required == required
    assert flags_seen[0] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC) == 0
    after = path.stat()
    assert _FileIdentity.from_stat(after) == _FileIdentity.from_stat(before)
    assert after.st_ctime_ns == before.st_ctime_ns
    assert path.read_bytes() == payload


def test_bounded_reader_refuses_missing_artifact_without_creating_it(tmp_path: Path) -> None:
    path = tmp_path / "missing.syx"
    with pytest.raises(DataError, match="is missing") as raised:
        reader.read_bounded_artifact(path, maximum=16)
    _assert_private_refusal(raised.value, path, "missing")
    assert tuple(tmp_path.iterdir()) == ()


@pytest.mark.parametrize("mode", [stat.S_IFDIR, stat.S_IFLNK, stat.S_IFIFO, stat.S_IFSOCK])
def test_bounded_reader_refuses_nonregular_files_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: int
) -> None:
    path = tmp_path / "unsafe.syx"
    path.write_bytes(b"safe")
    metadata = replace(_FileIdentity.from_stat(path.stat()), st_mode=mode | 0o600)

    def inspect(_path: Path, *, follow_symlinks: bool) -> _FileIdentity:
        assert _path == path and follow_symlinks is False
        return metadata

    def forbidden_open(*_args: object) -> int:
        raise AssertionError("nonregular artifacts must never be opened")

    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "stat", inspect)
        scoped.setattr(reader.os, "open", forbidden_open)
        with pytest.raises(DataError, match="not a regular file") as raised:
            reader.read_bounded_artifact(path, maximum=16)
    _assert_private_refusal(raised.value, path, "path")
    assert path.read_bytes() == b"safe"


@pytest.mark.parametrize("payload", [b"", b"12345"])
def test_bounded_reader_refuses_invalid_size_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: bytes
) -> None:
    path = tmp_path / "size.syx"
    path.write_bytes(payload)

    def forbidden_open(*_args: object) -> int:
        raise AssertionError("out-of-bound artifacts must never be opened")

    monkeypatch.setattr(reader.os, "open", forbidden_open)
    with pytest.raises(DataError, match="size is outside") as raised:
        reader.read_bounded_artifact(path, maximum=4)
    _assert_private_refusal(raised.value, path, "size")
    assert path.read_bytes() == payload


@pytest.mark.parametrize("stage", ["inspect", "open", "fstat", "read", "after-stat"])
def test_bounded_reader_sanitizes_permission_faults_and_leaves_artifact_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    path = tmp_path / "private.syx"
    path.write_bytes(b"safe")
    before = _FileIdentity.from_stat(path.stat())
    fault = PermissionError(f"denied sensitive local path {path}")
    handles: list[BinaryIO] = []

    def denied(*_args: object, **_kwargs: object) -> object:
        raise fault

    with monkeypatch.context() as scoped:
        if stage in ("inspect", "after-stat"):
            path_stat = Path.stat
            calls = 0

            def inspect(candidate: Path, *, follow_symlinks: bool) -> os.stat_result:
                nonlocal calls
                assert candidate == path and follow_symlinks is False
                calls += 1
                if stage == "inspect" or calls == 2:
                    raise fault
                return path_stat(candidate, follow_symlinks=follow_symlinks)

            scoped.setattr(Path, "stat", inspect)
        elif stage == "open":
            scoped.setattr(reader.os, "open", denied)
        elif stage == "fstat":
            scoped.setattr(reader.os, "fstat", denied)
            _, handles = _probe_reads(scoped)
        else:
            sizes, handles = _probe_reads(scoped, fault=fault)
        with pytest.raises(DataError) as raised:
            reader.read_bounded_artifact(path, maximum=4, label="retained source")
    _assert_private_refusal(raised.value, path, "access")
    assert raised.value.__cause__ is fault
    assert str(path) not in str(raised.value)
    assert all(handle.closed for handle in handles)
    if stage == "read":
        assert sizes == [5]
    assert _FileIdentity.from_stat(path.stat()) == before
    assert path.read_bytes() == b"safe"


@pytest.mark.parametrize("change", ["device", "inode", "nonregular"])
def test_bounded_reader_refuses_changed_open_identity_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    path = tmp_path / "replaced.syx"
    path.write_bytes(b"safe")
    metadata = _FileIdentity.from_stat(path.stat())
    if change == "device":
        opened = replace(metadata, st_dev=metadata.st_dev + 1)
    elif change == "inode":
        opened = replace(metadata, st_ino=metadata.st_ino + 1)
    else:
        opened = replace(metadata, st_mode=stat.S_IFIFO | 0o600)
    sizes, handles = _probe_reads(monkeypatch)
    monkeypatch.setattr(reader.os, "fstat", lambda _descriptor: opened)
    with pytest.raises(DataError, match="changed during open") as raised:
        reader.read_bounded_artifact(path, maximum=4)
    _assert_private_refusal(raised.value, path, "access")
    assert sizes == []
    assert len(handles) == 1 and handles[0].closed
    assert path.read_bytes() == b"safe"


@pytest.mark.parametrize("field", ["st_dev", "st_ino", "st_size", "st_mtime_ns"])
def test_bounded_reader_refuses_identity_changes_after_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    path = tmp_path / "changed.syx"
    path.write_bytes(b"safe")
    before = _FileIdentity.from_stat(path.stat())
    after = replace(before, **{field: getattr(before, field) + 1})
    sizes, handles = _probe_reads(monkeypatch)
    calls = 0

    def inspect(candidate: Path, *, follow_symlinks: bool) -> _FileIdentity:
        nonlocal calls
        assert candidate == path and follow_symlinks is False
        calls += 1
        return before if calls == 1 else after

    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "stat", inspect)
        with pytest.raises(DataError, match="changed while it was read") as raised:
            reader.read_bounded_artifact(path, maximum=4)
    _assert_private_refusal(raised.value, path, "access")
    assert calls == 2 and sizes == [5]
    assert handles[0].closed
    assert _FileIdentity.from_stat(path.stat()) == before


def test_bounded_reader_refuses_growth_using_only_the_bound_plus_one_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "grown.syx"
    path.write_bytes(b"safe")
    sizes, handles = _probe_reads(monkeypatch, payload=b"123456789")
    with pytest.raises(DataError, match="exceeds the supported bound") as raised:
        reader.read_bounded_artifact(path, maximum=4)
    _assert_private_refusal(raised.value, path, "size")
    assert sizes == [5]
    assert handles[0].closed
    assert path.read_bytes() == b"safe"


@pytest.mark.parametrize(
    "payload, expected",
    [
        (
            b'{"a":1,"nested":{"a":2},"items":[{"a":3}]}',
            {"a": 1, "nested": {"a": 2}, "items": [{"a": 3}]},
        ),
        (b'[0,false,null,"text"]', [0, False, None, "text"]),
        (b'"caf\\u00e9"', "caf\u00e9"),
    ],
)
def test_json_reader_accepts_utf8_values_and_distinct_object_keys(
    payload: bytes, expected: object
) -> None:
    assert reader.decode_json_rejecting_duplicate_keys(payload) == expected


@pytest.mark.parametrize(
    "payload",
    [
        b'{"id":1,"id":1}',
        b'{"nested":{"id":1,"id":2}}',
        b'[{"id":1,"id":2}]',
        b'{"id":1,"\\u0069d":2}',
        b'{"schema_version":3,"schema_version":2}',
    ],
)
def test_json_reader_refuses_duplicate_keys_at_every_nesting_level(payload: bytes) -> None:
    with pytest.raises(ValueError, match="duplicate JSON object key"):
        reader.decode_json_rejecting_duplicate_keys(payload)


@pytest.mark.parametrize("payload", [b"", b"{", b'{"id":1} trailing'])
def test_json_reader_refuses_malformed_json(payload: bytes) -> None:
    with pytest.raises(json.JSONDecodeError):
        reader.decode_json_rejecting_duplicate_keys(payload)


def test_json_reader_refuses_non_utf8_bytes() -> None:
    with pytest.raises(UnicodeDecodeError):
        reader.decode_json_rejecting_duplicate_keys(b'{"id":"\xff"}')
