"""Tests for ``rytm_randomizer.cockpit.export.writer``.

The writer turns "bytes + destination path" into a durable, partial-write-proof
file on disk. These tests pin:

* the atomic-write happy paths (creates parents, returns correct
  :class:`WriteResult`, replaces existing files when permitted);
* the failure-mode guarantees (no leaked temp files, ``WriteError``
  wrapping for any underlying ``OSError``, cleanup is best-effort);
* the platform-aware :func:`default_export_dir` resolution; and
* an end-to-end round-trip with WS-A's signing surface
  (``sign_profile_blob`` -> ``pack_signed`` -> ``write_signed_export`` ->
  read-from-disk -> ``unpack_signed`` -> ``verify_signed_blob``).

OS-specific resolution is exercised via ``monkeypatch.setattr`` against
``sys.platform`` so the suite is identical on every CI runner.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

import pytest

import rytm_randomizer.cockpit.export.writer as writer_module
from rytm_randomizer.cockpit.data import (
    ProfileModel,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.export.serialize import pack_profile_model
from rytm_randomizer.cockpit.export.signing import (
    pack_signed,
    sign_profile_blob,
    unpack_signed,
)
from rytm_randomizer.cockpit.export.verifier import verify_signed_blob
from rytm_randomizer.cockpit.export.writer import (
    DEFAULT_EXPORT_SUBDIR,
    WriteError,
    WriteResult,
    WriteSetError,
    atomic_write,
    atomic_write_set,
    default_export_dir,
    write_signed_export,
)
from rytm_randomizer.observability.errors import DataError

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_default_export_subdir_constant() -> None:
    assert DEFAULT_EXPORT_SUBDIR == "exports"


def test_bounded_artifact_name_delegates_to_shared_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def capture_name(path: Path, *, fallback: str, max_length: int) -> str:
        captured.update(
            path=path,
            fallback=fallback,
            max_length=max_length,
        )
        return "bounded-artifact"

    monkeypatch.setattr(
        writer_module,
        "safe_local_file_export_artifact_name",
        capture_name,
    )

    assert writer_module._bounded_artifact_name(Path("artifact.json")) == ("bounded-artifact")
    assert captured == {
        "path": Path("artifact.json"),
        "fallback": "unnamed-artifact",
        "max_length": 120,
    }


# ---------------------------------------------------------------------------
# WriteResult dataclass shape
# ---------------------------------------------------------------------------


def test_write_result_is_frozen_dataclass(tmp_path: Path) -> None:
    result = WriteResult(path=tmp_path / "x", bytes_written=3, overwrote_existing=False)
    with pytest.raises(AttributeError):
        result.bytes_written = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# WriteError taxonomy membership
# ---------------------------------------------------------------------------


def test_write_error_is_both_data_error_and_os_error() -> None:
    assert issubclass(WriteError, DataError)
    assert issubclass(WriteError, OSError)


def test_write_error_can_be_caught_as_os_error() -> None:
    try:
        raise WriteError("boom")
    except OSError as exc:  # noqa: BLE001 - precisely what we're verifying
        assert isinstance(exc, WriteError)


def test_write_error_can_be_caught_as_data_error() -> None:
    try:
        raise WriteError("boom")
    except DataError as exc:  # noqa: BLE001 - precisely what we're verifying
        assert isinstance(exc, WriteError)


# ---------------------------------------------------------------------------
# atomic_write — happy path
# ---------------------------------------------------------------------------


def test_atomic_write_happy_path_writes_correct_bytes(tmp_path: Path) -> None:
    dest = tmp_path / "out.bin"
    payload = b"hello world\x00\xff"

    result = atomic_write(dest, payload)

    assert dest.read_bytes() == payload
    assert isinstance(result, WriteResult)
    assert result.path == dest.resolve()
    assert result.bytes_written == len(payload)
    assert result.overwrote_existing is False


def test_atomic_write_returns_absolute_path(tmp_path: Path) -> None:
    dest = tmp_path / "out.bin"
    result = atomic_write(dest, b"x")
    assert result.path.is_absolute()


def test_atomic_write_creates_parent_directories(tmp_path: Path) -> None:
    dest = tmp_path / "a" / "b" / "c" / "deep.bin"
    assert not dest.parent.exists()

    result = atomic_write(dest, b"deep")

    assert dest.parent.is_dir()
    assert dest.read_bytes() == b"deep"
    assert result.bytes_written == 4


def test_atomic_write_empty_bytes(tmp_path: Path) -> None:
    dest = tmp_path / "empty.bin"
    result = atomic_write(dest, b"")
    assert dest.read_bytes() == b""
    assert result.bytes_written == 0


def test_atomic_write_leaves_no_temp_file_on_success(tmp_path: Path) -> None:
    dest = tmp_path / "out.bin"
    atomic_write(dest, b"x")
    leftover = [p.name for p in tmp_path.iterdir() if p.name != "out.bin"]
    assert leftover == []


# ---------------------------------------------------------------------------
# atomic_write — overwrite semantics
# ---------------------------------------------------------------------------


def test_atomic_write_overwrite_false_refuses_existing_file(tmp_path: Path) -> None:
    dest = tmp_path / "out.bin"
    dest.write_bytes(b"original")

    with pytest.raises(FileExistsError):
        atomic_write(dest, b"new", overwrite=False)

    assert dest.read_bytes() == b"original"


def test_atomic_write_overwrite_false_default_refuses_existing_file(
    tmp_path: Path,
) -> None:
    dest = tmp_path / "out.bin"
    dest.write_bytes(b"original")

    with pytest.raises(FileExistsError):
        atomic_write(dest, b"new")


def test_atomic_write_overwrite_false_does_not_leak_temp_file(tmp_path: Path) -> None:
    dest = tmp_path / "out.bin"
    dest.write_bytes(b"original")

    with pytest.raises(FileExistsError):
        atomic_write(dest, b"new", overwrite=False)

    leftover = sorted(p.name for p in tmp_path.iterdir())
    assert leftover == ["out.bin"]


def test_atomic_write_overwrite_true_replaces_existing(tmp_path: Path) -> None:
    dest = tmp_path / "out.bin"
    dest.write_bytes(b"original")

    result = atomic_write(dest, b"new", overwrite=True)

    assert dest.read_bytes() == b"new"
    assert result.overwrote_existing is True
    assert result.bytes_written == 3


def test_atomic_write_overwrite_true_no_temp_left_after_replace(tmp_path: Path) -> None:
    dest = tmp_path / "out.bin"
    dest.write_bytes(b"original")

    atomic_write(dest, b"new", overwrite=True)

    leftover = sorted(p.name for p in tmp_path.iterdir())
    assert leftover == ["out.bin"]


def test_atomic_write_overwrote_existing_false_when_new_file(tmp_path: Path) -> None:
    dest = tmp_path / "fresh.bin"
    result = atomic_write(dest, b"new", overwrite=True)
    assert result.overwrote_existing is False


# ---------------------------------------------------------------------------
# atomic_write — failure modes
# ---------------------------------------------------------------------------


def test_atomic_write_write_failure_raises_write_error_and_cleans_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the bytes write fails mid-flight, no temp file is left behind and a
    :class:`WriteError` is raised wrapping the underlying OSError."""

    dest = tmp_path / "out.bin"

    real_write = os.write

    def boom_write(fd: int, data: bytes) -> int:
        # Find any descriptor pointing at our tmp dir and fail.
        raise OSError("disk full")

    monkeypatch.setattr("os.write", boom_write)

    with pytest.raises(WriteError) as excinfo:
        atomic_write(dest, b"hello")

    # No temp file should be left behind in the destination directory.
    leftover = sorted(p.name for p in tmp_path.iterdir())
    assert leftover == []

    # The original OSError must be chained for diagnostics.
    assert excinfo.value.__cause__ is not None
    assert isinstance(excinfo.value.__cause__, OSError)

    # restore for any subsequent monkeypatch scope (autouse fixtures, etc.)
    _ = real_write


def test_atomic_write_wraps_nonpublication_file_exists_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dest = tmp_path / "out.bin"
    monkeypatch.setattr(
        "os.write",
        lambda _fd, _data: (_ for _ in ()).throw(FileExistsError("write failed")),
    )

    with pytest.raises(WriteError) as exc_info:
        atomic_write(dest, b"payload")

    assert isinstance(exc_info.value.__cause__, FileExistsError)
    assert not dest.exists()
    assert list(tmp_path.iterdir()) == []


def test_atomic_write_wraps_overwrite_replace_file_exists_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dest = tmp_path / "out.bin"
    monkeypatch.setattr(
        "os.replace",
        lambda _src, _dst: (_ for _ in ()).throw(FileExistsError("replace failed")),
    )

    with pytest.raises(WriteError) as exc_info:
        atomic_write(dest, b"payload", overwrite=True)

    assert isinstance(exc_info.value.__cause__, FileExistsError)
    assert not dest.exists()
    assert list(tmp_path.iterdir()) == []


def test_atomic_write_wraps_noncollision_publish_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dest = tmp_path / "out.bin"
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr(
        "os.link",
        lambda _src, _dst: (_ for _ in ()).throw(OSError("publish failed")),
    )

    with pytest.raises(WriteError) as exc_info:
        atomic_write(dest, b"payload")

    assert isinstance(exc_info.value.__cause__, OSError)
    assert not isinstance(exc_info.value.__cause__, FileExistsError)
    assert not dest.exists()
    assert list(tmp_path.iterdir()) == []


def test_atomic_write_retries_short_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = tmp_path / "out.bin"
    real_write = os.write

    def short_write(fd: int, data: bytes | memoryview) -> int:
        chunk_size = min(2, len(data))
        return real_write(fd, data[:chunk_size])

    monkeypatch.setattr("os.write", short_write)

    result = atomic_write(dest, b"abcdef")

    assert result.bytes_written == 6
    assert dest.read_bytes() == b"abcdef"


def test_atomic_write_zero_progress_raises_write_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "out.bin"
    monkeypatch.setattr("os.write", lambda _fd, _data: 0)

    with pytest.raises(WriteError, match="write made no progress"):
        atomic_write(dest, b"hello")

    assert list(tmp_path.iterdir()) == []


def test_atomic_write_cleans_temp_file_on_keyboard_interrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def interrupt_write(_fd: int, _data: bytes | memoryview) -> int:
        raise KeyboardInterrupt("operator interrupted write")

    monkeypatch.setattr("os.write", interrupt_write)
    with pytest.raises(KeyboardInterrupt, match="operator interrupted write"):
        atomic_write(tmp_path / "out.bin", b"payload")

    assert list(tmp_path.iterdir()) == []


def test_atomic_write_no_overwrite_closes_publish_race(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "out.bin"
    monkeypatch.setattr("sys.platform", "linux")

    def racing_link(_src: str, dst: str | Path) -> None:
        Path(dst).write_bytes(b"racer")
        raise FileExistsError(dst)

    monkeypatch.setattr("os.link", racing_link)

    with pytest.raises(FileExistsError):
        atomic_write(dest, b"ours")

    assert dest.read_bytes() == b"racer"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["out.bin"]


def test_atomic_write_no_overwrite_closes_publish_race_on_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "out.bin"
    monkeypatch.setattr("sys.platform", "win32")

    def racing_link(_src: str, dst: str | Path) -> None:
        Path(dst).write_bytes(b"racer")
        raise FileExistsError(dst)

    monkeypatch.setattr("os.link", racing_link)

    with pytest.raises(FileExistsError):
        atomic_write(dest, b"ours")

    assert dest.read_bytes() == b"racer"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["out.bin"]


def test_atomic_write_no_overwrite_cleanup_failure_keeps_published_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import rytm_randomizer.cockpit.export.writer as writer_module
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    dest = tmp_path / "out.bin"
    reset_metrics()
    monkeypatch.setattr("sys.platform", "linux")
    warnings: list[tuple[str, dict[str, object]]] = []

    def boom_unlink(_path: str, *args: object, **kwargs: object) -> None:
        raise OSError("cleanup failed")

    def capture_warning(message: str, *, extra: dict[str, object]) -> None:
        warnings.append((message, extra))

    monkeypatch.setattr("os.unlink", boom_unlink)
    monkeypatch.setattr(writer_module._logger, "warning", capture_warning)

    result = atomic_write(dest, b"published")

    assert result.path == dest.resolve()
    assert dest.read_bytes() == b"published"
    assert len(list(tmp_path.iterdir())) == 2
    assert warnings[0][0] == "Atomic write temp cleanup failed"
    assert warnings[0][1]["operation"] == "atomic_write_cleanup"
    assert warnings[0][1]["outcome"] == "residue_retained"
    assert warnings[0][1]["error_code"] == "temp_cleanup_failed"
    assert warnings[0][1]["fingerprint"] == "export.write.temp_cleanup_failed"
    assert get_metrics().errors_by_kind["atomic_write_temp_cleanup"] == 1


def test_atomic_write_replace_failure_raises_write_error_and_cleans_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "out.bin"

    def boom_replace(src: str, _dst: str) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr("os.replace", boom_replace)

    with pytest.raises(WriteError) as excinfo:
        atomic_write(dest, b"hello", overwrite=True)

    # Final file was never created.
    assert not dest.exists()
    # No temp file leaked.
    leftover = sorted(p.name for p in tmp_path.iterdir())
    assert leftover == []
    assert isinstance(excinfo.value.__cause__, OSError)


def test_atomic_write_cleanup_failure_does_not_mask_write_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The original WriteError must propagate even if the best-effort
    temp-file unlink also fails."""

    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    dest = tmp_path / "out.bin"
    reset_metrics()

    def boom_replace(src: str, _dst: str) -> None:
        raise OSError("replace failed")

    def boom_unlink(path: str, *args: object, **kwargs: object) -> None:
        raise OSError("unlink failed too")

    monkeypatch.setattr("os.replace", boom_replace)
    monkeypatch.setattr("os.unlink", boom_unlink)

    with pytest.raises(WriteError) as excinfo:
        atomic_write(dest, b"hello", overwrite=True)

    # The first OSError (from replace) is what we wrap; the unlink failure
    # is retained as an operator diagnostic without masking it.
    assert isinstance(excinfo.value.__cause__, OSError)
    assert "replace" in str(excinfo.value.__cause__).lower()
    assert any("sibling .tmp file may remain" in note for note in excinfo.value.__notes__)
    assert get_metrics().errors_by_kind["atomic_write_temp_cleanup"] == 1


def test_atomic_write_cleanup_failure_does_not_mask_keyboard_interrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    def interrupt_write(_fd: int, _data: bytes | memoryview) -> int:
        raise KeyboardInterrupt("operator interrupted write")

    def boom_unlink(_path: str, *args: object, **kwargs: object) -> None:
        raise OSError("unlink failed too")

    reset_metrics()
    monkeypatch.setattr("os.write", interrupt_write)
    monkeypatch.setattr("os.unlink", boom_unlink)

    with pytest.raises(KeyboardInterrupt, match="operator interrupted write") as excinfo:
        atomic_write(tmp_path / "out.bin", b"payload")

    assert any("sibling .tmp file may remain" in note for note in excinfo.value.__notes__)
    assert get_metrics().errors_by_kind["atomic_write_temp_cleanup"] == 1


def test_atomic_write_fsync_failure_raises_write_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "out.bin"

    def boom_fsync(fd: int) -> None:
        raise OSError("fsync failed")

    monkeypatch.setattr("os.fsync", boom_fsync)

    with pytest.raises(WriteError):
        atomic_write(dest, b"hello")

    assert not dest.exists()
    leftover = sorted(p.name for p in tmp_path.iterdir())
    assert leftover == []


# ---------------------------------------------------------------------------
# atomic_write_set — transactional multi-artifact publication
# ---------------------------------------------------------------------------


def test_atomic_write_set_publishes_all_bytes_in_mapping_order(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.md"
    first.write_bytes(b"old-first")

    results = atomic_write_set(
        {first: b"new-first", second: b"new-second"},
        overwrite=True,
    )

    assert first.read_bytes() == b"new-first"
    assert second.read_bytes() == b"new-second"
    assert tuple(result.path for result in results) == (
        first.resolve(),
        second.resolve(),
    )
    assert tuple(result.bytes_written for result in results) == (9, 10)
    assert tuple(result.overwrote_existing for result in results) == (True, False)
    assert not any(path.name.startswith(".write-set-") for path in tmp_path.iterdir())


def test_atomic_write_set_rejects_non_byte_payloads_before_staging(tmp_path: Path) -> None:
    destination = tmp_path / "report.json"
    artifacts: dict[Path, object] = {destination: "not bytes"}

    with pytest.raises(TypeError, match="payloads must be bytes"):
        atomic_write_set(artifacts)

    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


def test_atomic_write_set_rejects_empty_artifact_mapping() -> None:
    with pytest.raises(ValueError, match="at least one artifact"):
        atomic_write_set({})


def test_atomic_write_set_rejects_destination_without_filename() -> None:
    drive_root = Path(Path.cwd().anchor)

    with pytest.raises(ValueError, match="must name files"):
        atomic_write_set({drive_root: b"payload"})


def test_atomic_write_set_rejects_duplicate_canonical_destinations() -> None:
    relative = Path("duplicate-artifact.json")
    absolute = relative.absolute()

    with pytest.raises(ValueError, match="must be unique"):
        atomic_write_set({relative: b"first", absolute: b"second"})


def test_atomic_write_set_rejects_destinations_with_different_parents(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="share one parent"):
        atomic_write_set(
            {
                tmp_path / "first" / "artifact.json": b"first",
                tmp_path / "second" / "artifact.json": b"second",
            }
        )


def test_atomic_write_set_wraps_parent_creation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "blocked" / "artifact.json"
    real_mkdir = Path.mkdir

    def fail_target_mkdir(
        path: Path,
        *args: object,
        **kwargs: object,
    ) -> None:
        if path == destination.parent:
            raise PermissionError("parent creation denied")
        real_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail_target_mkdir)

    with pytest.raises(WriteSetError) as exc_info:
        atomic_write_set({destination: b"payload"})

    assert exc_info.value.failure_context.phase == "staging"
    assert exc_info.value.failure_context.artifact_name == "artifact.json"
    assert isinstance(exc_info.value.__cause__, PermissionError)


def test_atomic_write_set_refuses_existing_destination_without_overwrite(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "artifact.json"
    destination.write_bytes(b"existing")

    with pytest.raises(FileExistsError, match="artifact.json"):
        atomic_write_set({destination: b"replacement"})

    assert destination.read_bytes() == b"existing"


def test_atomic_write_set_refuses_concurrent_destination_without_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.md"
    publish_no_overwrite = writer_module._publish_no_overwrite

    def collide_on_second_publication(
        tmp_name: str,
        destination: Path,
        *,
        on_published: Callable[[], None] | None = None,
    ) -> None:
        if destination == second:
            destination.write_bytes(b"concurrent")
        publish_no_overwrite(
            tmp_name,
            destination,
            on_published=on_published,
        )

    monkeypatch.setattr(
        writer_module,
        "_publish_no_overwrite",
        collide_on_second_publication,
    )

    with pytest.raises(FileExistsError, match="second.md"):
        atomic_write_set({first: b"first", second: b"second"})

    assert not first.exists()
    assert second.read_bytes() == b"concurrent"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["second.md"]


def test_atomic_write_set_interrupt_after_link_rolls_back_published_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "artifact.json"
    publish_no_overwrite = writer_module._publish_no_overwrite

    def interrupt_after_link(
        tmp_name: str,
        path: Path,
        *,
        on_published: Callable[[], None] | None = None,
    ) -> None:
        publish_no_overwrite(
            tmp_name,
            path,
            on_published=on_published,
        )
        raise KeyboardInterrupt("operator interrupted after publication")

    monkeypatch.setattr(
        writer_module,
        "_publish_no_overwrite",
        interrupt_after_link,
    )

    with pytest.raises(
        KeyboardInterrupt,
        match="operator interrupted after publication",
    ):
        atomic_write_set({destination: b"payload"})

    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


def test_atomic_write_set_wraps_transaction_directory_creation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "artifact.json"

    def fail_mkdtemp(*_args: object, **_kwargs: object) -> str:
        raise PermissionError("transaction directory denied")

    monkeypatch.setattr(writer_module.tempfile, "mkdtemp", fail_mkdtemp)

    with pytest.raises(WriteSetError) as exc_info:
        atomic_write_set({destination: b"payload"})

    assert exc_info.value.failure_context.phase == "staging"
    assert exc_info.value.failure_context.artifact_name == "artifact.json"
    assert isinstance(exc_info.value.__cause__, PermissionError)


def test_atomic_write_set_staging_failure_names_actual_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.md"
    real_atomic_write = writer_module.atomic_write
    calls = 0

    def fail_second_stage(
        path: Path,
        data: bytes,
        *,
        overwrite: bool = False,
    ) -> WriteResult:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise WriteError("bounded staging failure")
        return real_atomic_write(path, data, overwrite=overwrite)

    monkeypatch.setattr(writer_module, "atomic_write", fail_second_stage)

    with pytest.raises(WriteSetError) as exc_info:
        atomic_write_set({first: b"first", second: b"second"}, overwrite=True)

    assert exc_info.value.failure_context.phase == "staging"
    assert exc_info.value.failure_context.artifact_name == "second.md"
    assert str(tmp_path) not in str(exc_info.value)
    assert not first.exists()
    assert not second.exists()
    assert list(tmp_path.iterdir()) == []


def test_atomic_write_set_keyboard_interrupt_rolls_back_staged_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.json"

    def interrupt_stage(
        _path: Path,
        _data: bytes,
        *,
        overwrite: bool = False,
    ) -> WriteResult:
        del overwrite
        raise KeyboardInterrupt("operator interrupted write set")

    monkeypatch.setattr(writer_module, "atomic_write", interrupt_stage)

    with pytest.raises(KeyboardInterrupt, match="operator interrupted write set") as exc_info:
        atomic_write_set({first: b"first"}, overwrite=True)

    assert any("staging for first.json" in note for note in exc_info.value.__notes__)
    assert not first.exists()
    assert list(tmp_path.iterdir()) == []


def test_atomic_write_set_backup_failure_restores_prior_files_and_names_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.md"
    first.write_bytes(b"old-first")
    second.write_bytes(b"old-second")
    real_replace = os.replace

    def fail_second_backup(source: str | Path, destination: str | Path) -> None:
        if Path(source).name == "second.md" and Path(destination).suffix == ".backup":
            raise OSError("backup failed")
        real_replace(source, destination)

    monkeypatch.setattr("os.replace", fail_second_backup)

    with pytest.raises(WriteSetError) as exc_info:
        atomic_write_set(
            {first: b"new-first", second: b"new-second"},
            overwrite=True,
        )

    assert exc_info.value.failure_context.phase == "backup"
    assert exc_info.value.failure_context.artifact_name == "second.md"
    assert str(tmp_path) not in str(exc_info.value)
    assert first.read_bytes() == b"old-first"
    assert second.read_bytes() == b"old-second"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["first.json", "second.md"]


def test_atomic_write_set_publication_failure_restores_all_prior_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.md"
    first.write_bytes(b"old-first")
    second.write_bytes(b"old-second")
    real_replace = os.replace

    def fail_second_publication(source: str | Path, destination: str | Path) -> None:
        if Path(source).suffix == ".stage" and Path(destination).name == "second.md":
            raise OSError("publication failed")
        real_replace(source, destination)

    monkeypatch.setattr("os.replace", fail_second_publication)

    with pytest.raises(WriteSetError) as exc_info:
        atomic_write_set(
            {first: b"new-first", second: b"new-second"},
            overwrite=True,
        )

    assert exc_info.value.failure_context.phase == "publication"
    assert exc_info.value.failure_context.artifact_name == "second.md"
    assert str(tmp_path) not in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, OSError)
    assert "publication failed" in str(exc_info.value.__cause__)
    assert first.read_bytes() == b"old-first"
    assert second.read_bytes() == b"old-second"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["first.json", "second.md"]


def test_atomic_write_set_publication_failure_removes_newly_created_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.md"
    real_replace = os.replace

    def fail_second_publication(source: str | Path, destination: str | Path) -> None:
        if Path(source).suffix == ".stage" and Path(destination).name == "second.md":
            raise OSError("publication failed")
        real_replace(source, destination)

    monkeypatch.setattr("os.replace", fail_second_publication)

    with pytest.raises(WriteSetError):
        atomic_write_set(
            {first: b"new-first", second: b"new-second"},
            overwrite=True,
        )

    assert not first.exists()
    assert not second.exists()
    assert list(tmp_path.iterdir()) == []


def test_atomic_write_set_rollback_failure_preserves_original_error_and_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.md"
    first.write_bytes(b"old-first")
    second.write_bytes(b"old-second")
    real_replace = os.replace

    def fail_publication_and_first_restore(
        source: str | Path,
        destination: str | Path,
    ) -> None:
        source_path = Path(source)
        destination_path = Path(destination)
        if source_path.suffix == ".stage" and destination_path.name == "second.md":
            raise OSError("original publication failure")
        if source_path.name == "0000.backup" and destination_path.name == "first.json":
            raise PermissionError("rollback restore failure")
        real_replace(source, destination)

    monkeypatch.setattr("os.replace", fail_publication_and_first_restore)

    with pytest.raises(WriteSetError) as exc_info:
        atomic_write_set(
            {first: b"new-first", second: b"new-second"},
            overwrite=True,
        )

    error = exc_info.value
    assert error.failure_context.phase == "publication"
    assert error.failure_context.artifact_name == "second.md"
    assert isinstance(error.__cause__, OSError)
    assert "original publication failure" in str(error.__cause__)
    assert error.failure_context.rollback_failures == (
        writer_module.WriteSetRollbackFailure(
            artifact_name="first.json",
            operation="restore_backup",
            error_type="PermissionError",
        ),
    )
    assert error.failure_context.recovery_directory_name is not None
    assert str(tmp_path) not in str(error)
    assert any("Rollback was incomplete" in note for note in error.__notes__)
    assert "/" not in error.failure_context.recovery_directory_name
    assert "\\" not in error.failure_context.recovery_directory_name

    recovery_dir = tmp_path / error.failure_context.recovery_directory_name
    assert recovery_dir.is_dir()
    assert (recovery_dir / "0000.backup").read_bytes() == b"old-first"
    assert first.read_bytes() == b"new-first"
    assert second.read_bytes() == b"old-second"


def test_atomic_write_set_records_new_file_removal_rollback_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "new-artifact.json"

    def fail_unlink(_path: str | Path) -> None:
        raise PermissionError("rollback removal denied")

    monkeypatch.setattr(os, "unlink", fail_unlink)

    failures = writer_module._rollback_write_set(
        ((destination, b"payload"),),
        backups={},
        published={destination},
    )

    assert failures == (
        writer_module.WriteSetRollbackFailure(
            artifact_name="new-artifact.json",
            operation="remove_new_file",
            error_type="PermissionError",
        ),
    )


def test_atomic_write_set_cleanup_ignores_missing_transaction_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_missing(_path: Path) -> None:
        raise FileNotFoundError("already removed")

    monkeypatch.setattr(writer_module.shutil, "rmtree", raise_missing)

    writer_module._cleanup_write_set_directory(
        tmp_path / ".write-set-missing",
        active_exception=None,
    )


@pytest.mark.parametrize("with_active_exception", [False, True])
def test_atomic_write_set_cleanup_failure_is_observable_without_masking_outcome(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    with_active_exception: bool,
) -> None:
    recorded_errors: list[str] = []
    warnings: list[tuple[str, dict[str, object]]] = []

    class FakeMetrics:
        def record_error(self, kind: str) -> None:
            recorded_errors.append(kind)

        def format_summary(self) -> dict[str, int]:
            return {"recorded_errors": len(recorded_errors)}

    def fail_cleanup(_path: Path) -> None:
        raise PermissionError("cleanup denied")

    def capture_warning(message: str, *, extra: dict[str, object]) -> None:
        warnings.append((message, extra))

    active_exception = RuntimeError("active failure") if with_active_exception else None
    monkeypatch.setattr(writer_module.shutil, "rmtree", fail_cleanup)
    monkeypatch.setattr(writer_module, "get_metrics", FakeMetrics)
    monkeypatch.setattr(writer_module._logger, "warning", capture_warning)

    writer_module._cleanup_write_set_directory(
        tmp_path / ".write-set-residue",
        active_exception=active_exception,
    )

    assert recorded_errors == ["atomic_write_set_cleanup"]
    assert warnings[0][0] == "Atomic write-set cleanup failed"
    assert warnings[0][1]["error_code"] == "transaction_cleanup_failed"
    assert warnings[0][1]["transaction_name"] == ".write-set-residue"
    if active_exception is None:
        return
    assert any("transaction residue may remain" in note for note in active_exception.__notes__)


# ---------------------------------------------------------------------------
# default_export_dir — platform resolution
# ---------------------------------------------------------------------------


def test_default_export_dir_always_ends_in_app_subdir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    result = default_export_dir()
    assert result.parts[-2:] == ("rytm-randomizer", "exports")


def test_default_export_dir_linux_uses_xdg_config_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    result = default_export_dir()
    assert result == tmp_path / "rytm-randomizer" / "exports"


def test_default_export_dir_linux_falls_back_to_home_config_when_xdg_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    result = default_export_dir()
    assert result == Path.home() / ".config" / "rytm-randomizer" / "exports"


def test_default_export_dir_linux_falls_back_to_home_config_when_xdg_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", "")
    result = default_export_dir()
    assert result == Path.home() / ".config" / "rytm-randomizer" / "exports"


def test_default_export_dir_windows_uses_appdata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    result = default_export_dir()
    assert result == tmp_path / "rytm-randomizer" / "exports"


def test_default_export_dir_windows_falls_back_to_home_when_appdata_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.delenv("APPDATA", raising=False)
    result = default_export_dir()
    assert result == Path.home() / "rytm-randomizer" / "exports"


def test_default_export_dir_does_not_create_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    result = default_export_dir()
    assert not result.exists()


# ---------------------------------------------------------------------------
# write_signed_export
# ---------------------------------------------------------------------------


def test_write_signed_export_default_filename_and_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    signed_bytes = b"signed-envelope"
    result = write_signed_export(signed_bytes, profile_id="buzzi", model_version="1.0")

    expected_path = (tmp_path / "rytm-randomizer" / "exports" / "buzzi-v1.0.rymp").resolve()
    assert result.path == expected_path
    assert result.bytes_written == len(signed_bytes)
    assert result.overwrote_existing is False
    assert expected_path.read_bytes() == signed_bytes


def test_write_signed_export_custom_export_dir(tmp_path: Path) -> None:
    signed_bytes = b"signed-envelope"
    custom_dir = tmp_path / "custom"

    result = write_signed_export(
        signed_bytes,
        profile_id="alice",
        model_version="2.3",
        export_dir=custom_dir,
    )

    expected = (custom_dir / "alice-v2.3.rymp").resolve()
    assert result.path == expected
    assert expected.read_bytes() == signed_bytes


def test_write_signed_export_filename_override(tmp_path: Path) -> None:
    signed_bytes = b"sig-bytes"
    result = write_signed_export(
        signed_bytes,
        profile_id="ignored",
        model_version="9.9",
        export_dir=tmp_path,
        filename_override="my-exact-name.bin",
    )
    expected = (tmp_path / "my-exact-name.bin").resolve()
    assert result.path == expected


def test_write_signed_export_overwrite_false_refuses_existing(tmp_path: Path) -> None:
    dest = tmp_path / "alice-v1.0.rymp"
    dest.write_bytes(b"already here")

    with pytest.raises(FileExistsError):
        write_signed_export(
            b"new",
            profile_id="alice",
            model_version="1.0",
            export_dir=tmp_path,
        )


def test_write_signed_export_overwrite_true_replaces(tmp_path: Path) -> None:
    dest = tmp_path / "alice-v1.0.rymp"
    dest.write_bytes(b"already here")

    result = write_signed_export(
        b"new",
        profile_id="alice",
        model_version="1.0",
        export_dir=tmp_path,
        overwrite=True,
    )

    assert dest.read_bytes() == b"new"
    assert result.overwrote_existing is True


# ---------------------------------------------------------------------------
# End-to-end round-trip with WS-A signing
# ---------------------------------------------------------------------------


def test_round_trip_sign_pack_write_read_unpack_verify(tmp_path: Path) -> None:
    """Pack a profile blob, sign it, write it, read it back, unpack, verify
    -- and assert the read-back bytes are byte-identical to what we wrote."""

    profile = ProfileModel(
        profile_id="01HXY5Q9PJM0123456789ABCD0",
        name="buzzi",
        kind="user",
        model_version="1.2.0",
        traits=(StyleTrait("rolling_low_end", 0.85),),
        pad_mappings=(TraitPadWeight("rolling_low_end", 1, 0.6),),
        transition_curve="linear",
        source_summary="5 sources",
    )
    inner_payload = pack_profile_model(profile)

    secret_key = b"buzzi-secret-key-2026"
    key_id = "buzzi-2026-key"

    signed_blob = sign_profile_blob(inner_payload, key=secret_key, key_id=key_id)
    envelope_bytes = pack_signed(signed_blob)

    result = write_signed_export(
        envelope_bytes,
        profile_id="buzzi",
        model_version="1.2.0",
        export_dir=tmp_path,
    )

    # Read-back is byte-identical to the envelope we wrote.
    on_disk = result.path.read_bytes()
    assert on_disk == envelope_bytes

    # Unpacks back to the same SignedBlob shape.
    reparsed = unpack_signed(on_disk)
    assert reparsed.payload == inner_payload
    assert reparsed.key_id == key_id

    # Verifier accepts the round-tripped envelope under the same key.
    verification = verify_signed_blob(on_disk, key=secret_key)
    assert verification.ok is True
