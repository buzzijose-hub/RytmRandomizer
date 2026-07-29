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
from pathlib import Path

import pytest

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
    atomic_write,
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


def test_atomic_write_no_overwrite_closes_windows_publish_race(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "out.bin"
    monkeypatch.setattr("sys.platform", "win32")

    def racing_rename(_src: str, dst: str | Path) -> None:
        Path(dst).write_bytes(b"racer")
        raise FileExistsError(dst)

    monkeypatch.setattr("os.rename", racing_rename)

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
