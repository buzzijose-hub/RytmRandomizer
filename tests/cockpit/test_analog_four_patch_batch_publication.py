"""Observability coverage for immutable Analog Four batch publication."""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path
from typing import TypedDict

import pytest

from rytm_randomizer.cockpit.export.writer import WriteResult

pytestmark = [
    pytest.mark.fast,
    pytest.mark.usefixtures("isolated_observability"),
]


class _LockOwner(TypedDict):
    generation_id: str
    publication_nonce: str
    audio_sha256: str
    source_kit_sha256: str


def test_export_path_name_uses_shared_filename_safety() -> None:
    from rytm_randomizer.cockpit.export.analog_four_export_contracts import (
        analog_four_export_path_name,
    )

    assert analog_four_export_path_name(Path("unsafe\nname.wav")) == "<invalid>"
    assert analog_four_export_path_name(Path("safe.wav")) == "safe.wav"
    assert analog_four_export_path_name(object()) == "<invalid>"


def _lock_owner(seed: str = "a") -> _LockOwner:
    return {
        "generation_id": seed * 32,
        "publication_nonce": chr(ord(seed) + 1) * 32,
        "audio_sha256": chr(ord(seed) + 2) * 64,
        "source_kit_sha256": chr(ord(seed) + 3) * 64,
    }


def test_immutable_publication_records_publish_and_reuse_without_payload_bytes(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        publish_immutable_artifact,
    )
    from rytm_randomizer.observability.logging import configure_logging
    from rytm_randomizer.observability.metrics import get_metrics

    log_stream = io.StringIO()
    configure_logging(level=logging.DEBUG, json=True, stream=log_stream)
    artifact_path = tmp_path / "candidate.syx"
    private_payload = b"private-sysex-payload"

    publish_immutable_artifact(artifact_path, private_payload)
    publish_immutable_artifact(artifact_path, private_payload)

    metrics = get_metrics()
    assert metrics.a4_patch_publication_count["artifact_publish"] == 2
    assert not metrics.a4_patch_publication_errors_by_code
    log_output = log_stream.getvalue()
    assert '"outcome": "published"' in log_output
    assert '"outcome": "reused"' in log_output
    assert "operation_end a4_patch_artifact_publish" in log_output
    assert private_payload.decode("ascii") not in log_output
    records = [json.loads(line) for line in log_output.splitlines()]
    terminal_ids = {
        record["op_id"]
        for record in records
        if record["message"] == "Analog Four batch publication operation completed"
    }
    span_ids = {
        record["op_id"]
        for record in records
        if record["message"].startswith("operation_end a4_patch_artifact_publish")
    }
    assert terminal_ids == span_ids


def test_immutable_publication_collision_records_failed_trace(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        AnalogFourPatchBatchPublicationError,
        publish_immutable_artifact,
    )
    from rytm_randomizer.observability.logging import configure_logging
    from rytm_randomizer.observability.metrics import get_metrics

    log_stream = io.StringIO()
    configure_logging(level=logging.DEBUG, stream=log_stream)
    artifact_path = tmp_path / "candidate.syx"
    publish_immutable_artifact(artifact_path, b"first")

    with pytest.raises(AnalogFourPatchBatchPublicationError):
        publish_immutable_artifact(artifact_path, b"second")

    metrics = get_metrics()
    assert metrics.a4_patch_publication_count["artifact_publish"] == 2
    assert metrics.a4_patch_publication_errors_by_code["artifact_collision"] == 1
    assert "operation_error a4_patch_artifact_publish" in log_stream.getvalue()


def test_lock_lifecycle_records_acquire_contention_and_release(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        AnalogFourPatchBatchLockedError,
        acquire_batch_lock,
        release_batch_lock,
    )
    from rytm_randomizer.observability.metrics import get_metrics

    lock_path = tmp_path / "batch.lock"
    lock_args = _lock_owner()

    acquire_batch_lock(lock_path, **lock_args)
    with pytest.raises(AnalogFourPatchBatchLockedError):
        acquire_batch_lock(lock_path, **lock_args)
    assert release_batch_lock(lock_path, **lock_args) is None

    metrics = get_metrics()
    assert metrics.a4_patch_publication_count["lock_acquire"] == 2
    assert metrics.a4_patch_publication_errors_by_code["lock_exists"] == 1
    assert metrics.a4_patch_publication_count["lock_release"] == 1


def test_lock_release_requires_complete_owner_identity(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        release_batch_lock,
    )
    from rytm_randomizer.observability.metrics import get_metrics

    with pytest.raises(ValueError, match="requires all owner fields"):
        release_batch_lock(
            tmp_path / "batch.lock",
            generation_id="a" * 32,
        )

    metrics = get_metrics()
    assert metrics.a4_patch_publication_count["lock_release"] == 1
    assert (
        metrics.a4_patch_publication_errors_by_operation_and_code["lock_release:release_failed"]
        == 1
    )


def test_publication_interrupt_and_cleanup_failure_are_terminal_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        acquire_batch_lock,
        publish_immutable_artifact,
        release_batch_lock,
    )
    from rytm_randomizer.observability.metrics import get_metrics

    artifact_path = tmp_path / "candidate.syx"

    def interrupt_writer(
        path: Path,
        data: bytes,
        *,
        overwrite: bool = False,
    ) -> WriteResult:
        del path, data, overwrite
        raise KeyboardInterrupt("publication interrupted")

    with pytest.raises(KeyboardInterrupt, match="publication interrupted"):
        publish_immutable_artifact(
            artifact_path,
            b"private",
            writer=interrupt_writer,
        )

    lock_path = tmp_path / "batch.lock"
    lock_args = _lock_owner()
    acquire_batch_lock(lock_path, **lock_args)
    real_unlink = Path.unlink

    def fail_lock_cleanup(path: Path, *args: object, **kwargs: object) -> None:
        if path == lock_path:
            raise OSError("lock busy")
        real_unlink(path, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "unlink", fail_lock_cleanup)
    diagnostic = release_batch_lock(lock_path, **lock_args)
    assert diagnostic is not None
    assert diagnostic == f"{lock_path.name}: OSError; lock retained"
    assert str(tmp_path) not in diagnostic

    metrics = get_metrics()
    assert metrics.a4_patch_publication_errors_by_code["interrupted"] == 1
    assert metrics.a4_patch_publication_errors_by_code["release_failed"] == 1
    assert metrics.a4_patch_publication_count["artifact_publish"] == 1
    assert metrics.a4_patch_publication_count["lock_release"] == 1


def test_publication_classifies_existing_read_and_new_write_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        publish_immutable_artifact,
    )
    from rytm_randomizer.observability.metrics import get_metrics

    artifact_path = tmp_path / "candidate.syx"

    def existing_writer(
        path: Path,
        data: bytes,
        *,
        overwrite: bool = False,
    ) -> WriteResult:
        del path, data, overwrite
        raise FileExistsError("already published")

    real_read_bytes = Path.read_bytes

    def fail_existing_read(path: Path) -> bytes:
        if path == artifact_path:
            raise OSError("read failed")
        return real_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fail_existing_read)
    with pytest.raises(OSError, match="read failed"):
        publish_immutable_artifact(artifact_path, b"private", writer=existing_writer)

    def fail_new_write(
        path: Path,
        data: bytes,
        *,
        overwrite: bool = False,
    ) -> WriteResult:
        del path, data, overwrite
        raise OSError("write failed")

    with pytest.raises(OSError, match="write failed"):
        publish_immutable_artifact(artifact_path, b"private", writer=fail_new_write)

    metrics = get_metrics()
    assert metrics.a4_patch_publication_errors_by_code["read_failed"] == 1
    assert metrics.a4_patch_publication_errors_by_code["write_failed"] == 1


def test_publication_records_invalid_path_before_hashing_or_writing() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        publish_immutable_artifact,
    )
    from rytm_randomizer.observability.metrics import get_metrics

    with pytest.raises(TypeError, match="path must be a pathlib.Path"):
        publish_immutable_artifact("candidate.syx", b"private")  # type: ignore[arg-type]

    assert get_metrics().a4_patch_publication_errors_by_code["write_failed"] == 1


def test_lock_release_records_absent_lock_and_propagates_interrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        acquire_batch_lock,
        release_batch_lock,
    )
    from rytm_randomizer.observability.metrics import get_metrics

    lock_path = tmp_path / "batch.lock"
    assert release_batch_lock(lock_path) is None

    def interrupt_unlink(
        path: Path,
        *args: object,
        **kwargs: object,
    ) -> None:
        del path, args, kwargs
        raise KeyboardInterrupt("cleanup interrupted")

    monkeypatch.setattr(Path, "unlink", interrupt_unlink)
    lock_args = _lock_owner()
    acquire_batch_lock(lock_path, **lock_args)
    with pytest.raises(KeyboardInterrupt, match="cleanup interrupted"):
        release_batch_lock(lock_path, **lock_args)

    metrics = get_metrics()
    assert metrics.a4_patch_publication_count["lock_release"] == 2
    assert metrics.a4_patch_publication_errors_by_code["interrupted"] == 1


def test_lock_release_retains_replaced_owner_lock(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        acquire_batch_lock,
        release_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    original_owner: _LockOwner = {
        "generation_id": "a" * 32,
        "publication_nonce": "b" * 32,
        "audio_sha256": "c" * 64,
        "source_kit_sha256": "d" * 64,
    }
    replacement_owner: _LockOwner = {
        "generation_id": "e" * 32,
        "publication_nonce": "f" * 32,
        "audio_sha256": "1" * 64,
        "source_kit_sha256": "2" * 64,
    }
    acquire_batch_lock(lock_path, **original_owner)
    lock_path.unlink()
    acquire_batch_lock(lock_path, **replacement_owner)

    diagnostic = release_batch_lock(lock_path, **original_owner)

    assert diagnostic == f"{lock_path.name}: ownership changed; lock retained"
    assert lock_path.exists()
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    assert payload["publication_nonce"] == replacement_owner["publication_nonce"]


def test_lock_release_retains_non_object_owner_payload(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        release_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    lock_path.write_text("[]", encoding="utf-8")

    diagnostic = release_batch_lock(lock_path, **_lock_owner())

    assert diagnostic == f"{lock_path.name}: ownership changed; lock retained"
    assert lock_path.exists()


def test_lock_release_gate_prevents_replacement_before_unlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        AnalogFourPatchBatchLockedError,
        acquire_batch_lock,
        release_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    original_owner = _lock_owner("a")
    replacement_owner = _lock_owner("e")
    acquire_batch_lock(lock_path, **original_owner)
    real_unlink = Path.unlink
    replacement_attempts: list[str] = []

    def attempt_replacement(path: Path, *args: object, **kwargs: object) -> None:
        if path == lock_path:
            real_unlink(path, *args, **kwargs)  # type: ignore[arg-type]
            with pytest.raises(AnalogFourPatchBatchLockedError):
                acquire_batch_lock(lock_path, **replacement_owner)
            replacement_attempts.append("blocked")
            return
        real_unlink(path, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "unlink", attempt_replacement)
    assert release_batch_lock(lock_path, **original_owner) is None
    assert replacement_attempts == ["blocked"]
    assert not lock_path.exists()

    monkeypatch.setattr(Path, "unlink", real_unlink)
    acquire_batch_lock(lock_path, **replacement_owner)
    assert lock_path.exists()


def test_lock_acquire_rolls_back_when_operation_gate_cleanup_fails_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        AnalogFourPatchBatchPublicationError,
        acquire_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    gate_path = lock_path.with_name(lock_path.name + ".operation")
    lock_args = _lock_owner()
    real_rmdir = Path.rmdir
    cleanup_attempts = 0

    def fail_first_gate_cleanup(path: Path) -> None:
        nonlocal cleanup_attempts
        if path == gate_path:
            cleanup_attempts += 1
            if cleanup_attempts == 1:
                raise OSError("transient gate cleanup failure")
        real_rmdir(path)

    monkeypatch.setattr(Path, "rmdir", fail_first_gate_cleanup)

    with pytest.raises(
        AnalogFourPatchBatchPublicationError,
        match="operation gate cleanup failed",
    ):
        acquire_batch_lock(lock_path, **lock_args)

    assert cleanup_attempts == 2
    assert not lock_path.exists()
    assert not gate_path.exists()


def test_lock_release_reports_gate_cleanup_failure_without_rewriting_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        acquire_batch_lock,
        release_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    gate_path = lock_path.with_name(lock_path.name + ".operation")
    lock_args = _lock_owner()
    acquire_batch_lock(lock_path, **lock_args)
    real_rmdir = Path.rmdir
    cleanup_attempts = 0

    def fail_first_gate_cleanup(path: Path) -> None:
        nonlocal cleanup_attempts
        if path == gate_path:
            cleanup_attempts += 1
            if cleanup_attempts == 1:
                raise OSError("transient gate cleanup failure")
        real_rmdir(path)

    monkeypatch.setattr(Path, "rmdir", fail_first_gate_cleanup)

    diagnostic = release_batch_lock(lock_path, **lock_args)

    assert diagnostic is not None
    assert "operation gate cleanup retry completed" in diagnostic
    assert "lock retained" not in diagnostic
    assert cleanup_attempts == 2
    assert not lock_path.exists()
    assert not gate_path.exists()


@pytest.mark.parametrize("signal_type", [KeyboardInterrupt, SystemExit])
def test_lock_release_propagates_gate_cleanup_interruption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    signal_type: type[BaseException],
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        acquire_batch_lock,
        release_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    gate_path = lock_path.with_name(lock_path.name + ".operation")
    lock_args = _lock_owner()
    acquire_batch_lock(lock_path, **lock_args)
    real_rmdir = Path.rmdir
    cleanup_attempts = 0

    def interrupt_first_gate_cleanup(path: Path) -> None:
        nonlocal cleanup_attempts
        if path == gate_path:
            cleanup_attempts += 1
            if cleanup_attempts == 1:
                raise signal_type("release gate cleanup interrupted")
        real_rmdir(path)

    monkeypatch.setattr(Path, "rmdir", interrupt_first_gate_cleanup)

    with pytest.raises(signal_type, match="operation gate cleanup retry completed"):
        release_batch_lock(lock_path, **lock_args)

    assert cleanup_attempts == 2
    assert not lock_path.exists()
    assert not gate_path.exists()


def test_lock_release_reports_a_retained_operation_gate_after_retry_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        acquire_batch_lock,
        release_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    gate_path = lock_path.with_name(lock_path.name + ".operation")
    lock_args = _lock_owner()
    acquire_batch_lock(lock_path, **lock_args)
    real_rmdir = Path.rmdir
    cleanup_error = OSError("gate busy")
    cleanup_error.winerror = 5
    monkeypatch.setattr(
        Path,
        "rmdir",
        lambda _path: (_ for _ in ()).throw(cleanup_error),
    )

    diagnostic = release_batch_lock(lock_path, **lock_args)

    assert diagnostic is not None
    assert "OSError code=5" in diagnostic
    assert "operation gate retained" in diagnostic
    assert not lock_path.exists()
    assert gate_path.exists()
    monkeypatch.setattr(Path, "rmdir", real_rmdir)
    gate_path.rmdir()


def test_lock_acquire_preserves_writer_failure_and_notes_gate_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        acquire_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    gate_path = lock_path.with_name(lock_path.name + ".operation")
    lock_args = _lock_owner()
    real_rmdir = Path.rmdir

    def fail_writer(
        path: Path,
        data: bytes,
        *,
        overwrite: bool = False,
    ) -> WriteResult:
        del path, data, overwrite
        raise OSError("writer failed")

    monkeypatch.setattr(
        Path,
        "rmdir",
        lambda _path: (_ for _ in ()).throw(OSError("gate busy")),
    )

    with pytest.raises(OSError, match="writer failed") as exc_info:
        acquire_batch_lock(lock_path, writer=fail_writer, **lock_args)

    assert "batch lock operation gate cleanup failure" in exc_info.value.__notes__[0]
    assert gate_path.exists()
    monkeypatch.setattr(Path, "rmdir", real_rmdir)
    gate_path.rmdir()


def test_lock_contention_reports_gate_cleanup_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        AnalogFourPatchBatchLockedError,
        acquire_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    gate_path = lock_path.with_name(lock_path.name + ".operation")
    lock_args = _lock_owner()
    acquire_batch_lock(lock_path, **lock_args)
    real_rmdir = Path.rmdir
    monkeypatch.setattr(
        Path,
        "rmdir",
        lambda path: (
            (_ for _ in ()).throw(OSError("gate busy")) if path == gate_path else real_rmdir(path)
        ),
    )

    with pytest.raises(
        AnalogFourPatchBatchLockedError,
        match="batch lock operation gate cleanup failure",
    ):
        acquire_batch_lock(lock_path, **lock_args)

    assert gate_path.exists()
    monkeypatch.setattr(Path, "rmdir", real_rmdir)
    gate_path.rmdir()
    lock_path.unlink()


def test_lock_acquire_reports_failed_rollback_and_retained_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        AnalogFourPatchBatchPublicationError,
        acquire_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    gate_path = lock_path.with_name(lock_path.name + ".operation")
    lock_args = _lock_owner()
    real_rmdir = Path.rmdir
    real_unlink = Path.unlink
    monkeypatch.setattr(
        Path,
        "rmdir",
        lambda _path: (_ for _ in ()).throw(OSError("gate busy")),
    )

    def fail_lock_rollback(path: Path, *args: object, **kwargs: object) -> None:
        if path == lock_path:
            raise OSError("lock busy")
        real_unlink(path, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "unlink", fail_lock_rollback)

    with pytest.raises(
        AnalogFourPatchBatchPublicationError,
        match="operation gate cleanup failed",
    ) as exc_info:
        acquire_batch_lock(lock_path, **lock_args)

    assert "lock retained" in str(exc_info.value)
    assert "operation gate retained" in str(exc_info.value)
    assert lock_path.exists()
    assert gate_path.exists()
    monkeypatch.setattr(Path, "unlink", real_unlink)
    monkeypatch.setattr(Path, "rmdir", real_rmdir)
    lock_path.unlink()
    gate_path.rmdir()


def test_lock_acquire_propagates_gate_cleanup_interrupt_after_rollback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        acquire_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    gate_path = lock_path.with_name(lock_path.name + ".operation")
    lock_args = _lock_owner()
    real_rmdir = Path.rmdir
    cleanup_attempts = 0

    def interrupt_first_cleanup(path: Path) -> None:
        nonlocal cleanup_attempts
        if path == gate_path:
            cleanup_attempts += 1
            if cleanup_attempts == 1:
                raise KeyboardInterrupt("gate cleanup interrupted")
        real_rmdir(path)

    monkeypatch.setattr(Path, "rmdir", interrupt_first_cleanup)

    with pytest.raises(KeyboardInterrupt, match="gate cleanup interrupted") as exc_info:
        acquire_batch_lock(lock_path, **lock_args)

    assert "operation gate cleanup retry completed" in str(exc_info.value)
    assert cleanup_attempts == 2
    assert not lock_path.exists()
    assert not gate_path.exists()


def test_lock_acquire_classifies_unreadable_metadata_write_failure_and_interrupt(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        AnalogFourPatchBatchLockedError,
        acquire_batch_lock,
    )
    from rytm_randomizer.observability.metrics import get_metrics

    lock_path = tmp_path / "batch.lock"
    lock_args = _lock_owner()

    def unreadable_existing_writer(
        path: Path,
        data: bytes,
        *,
        overwrite: bool = False,
    ) -> WriteResult:
        del path, data, overwrite
        raise FileExistsError("already locked")

    with pytest.raises(
        AnalogFourPatchBatchLockedError,
        match="recovery metadata: unavailable",
    ):
        acquire_batch_lock(
            lock_path,
            writer=unreadable_existing_writer,
            **lock_args,
        )

    def fail_writer(
        path: Path,
        data: bytes,
        *,
        overwrite: bool = False,
    ) -> WriteResult:
        del path, data, overwrite
        raise OSError("lock write failed")

    with pytest.raises(OSError, match="lock write failed"):
        acquire_batch_lock(lock_path, writer=fail_writer, **lock_args)

    def interrupt_writer(
        path: Path,
        data: bytes,
        *,
        overwrite: bool = False,
    ) -> WriteResult:
        del path, data, overwrite
        raise KeyboardInterrupt("lock interrupted")

    with pytest.raises(KeyboardInterrupt, match="lock interrupted"):
        acquire_batch_lock(lock_path, writer=interrupt_writer, **lock_args)

    metrics = get_metrics()
    assert metrics.a4_patch_publication_errors_by_code["lock_exists"] == 1
    assert metrics.a4_patch_publication_errors_by_code["write_failed"] == 1
    assert metrics.a4_patch_publication_errors_by_code["interrupted"] == 1


def test_batch_lock_recovery_match_requires_every_owner_field(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        acquire_batch_lock,
        batch_lock_matches_request,
    )
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    lock_path = tmp_path / "batch.lock"
    lock_args = _lock_owner()
    reset_metrics()
    acquire_batch_lock(lock_path, **lock_args)
    assert batch_lock_matches_request(lock_path, **lock_args)

    original_payload = json.loads(lock_path.read_text(encoding="utf-8"))
    for field in (
        "generation_id",
        "publication_nonce",
        "process_id",
        "audio_sha256",
        "source_kit_sha256",
    ):
        mismatched_payload = dict(original_payload)
        mismatched_payload[field] = "mismatch"
        lock_path.write_text(json.dumps(mismatched_payload), encoding="utf-8")
        assert not batch_lock_matches_request(lock_path, **lock_args)

    lock_path.write_text("[]", encoding="utf-8")
    assert not batch_lock_matches_request(lock_path, **lock_args)
    lock_path.write_text("not-json", encoding="utf-8")
    assert not batch_lock_matches_request(lock_path, **lock_args)
    metrics = get_metrics()
    assert metrics.a4_patch_publication_count["lock_owner_check"] == 8
    assert (
        metrics.a4_patch_publication_errors_by_operation_and_code["lock_owner_check:read_failed"]
        == 2
    )


def test_lock_recovery_summary_rejects_non_object_and_invalid_metadata(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        _lock_recovery_summary,
    )

    lock_path = tmp_path / "batch.lock"
    lock_path.write_text("[]", encoding="utf-8")
    assert _lock_recovery_summary(lock_path) == "unavailable"

    lock_path.write_text(
        json.dumps(
            {
                "process_id": True,
                "created_unix_seconds": False,
                "generation_id": "short",
            }
        ),
        encoding="utf-8",
    )
    assert _lock_recovery_summary(lock_path) == "unavailable"


def test_lock_cleanup_diagnostic_bounds_lock_and_os_error_details(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        AnalogFourPatchBatchLockedError,
        _safe_lock_cleanup_diagnostic,
    )

    lock_path = tmp_path / "private" / "batch.lock"
    assert (
        _safe_lock_cleanup_diagnostic(
            lock_path,
            AnalogFourPatchBatchLockedError("busy"),
        )
        == "batch.lock: lock operation in progress; lock retained"
    )

    error = OSError("denied")
    error.winerror = 5
    diagnostic = _safe_lock_cleanup_diagnostic(lock_path, error)
    assert diagnostic == "batch.lock: OSError code=5; lock retained"
    assert str(tmp_path) not in diagnostic


def test_lock_release_without_owner_retains_existing_lock(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        acquire_batch_lock,
        release_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    lock_args = _lock_owner()
    acquire_batch_lock(lock_path, **lock_args)

    assert release_batch_lock(lock_path) == "batch.lock: ValueError; lock retained"
    assert lock_path.exists()


def test_lock_release_allows_a_new_owner_only_after_unlink(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_publication import (
        acquire_batch_lock,
        release_batch_lock,
    )

    lock_path = tmp_path / "batch.lock"
    original_owner = _lock_owner("a")
    replacement_owner = _lock_owner("e")
    acquire_batch_lock(lock_path, **original_owner)

    assert release_batch_lock(lock_path, **original_owner) is None
    acquire_batch_lock(lock_path, **replacement_owner)

    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    assert payload["publication_nonce"] == replacement_owner["publication_nonce"]
