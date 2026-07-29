"""Race-safe publication primitives for Analog Four patch batches."""

from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Final, Never, Protocol, TypedDict, cast

from ...observability.errors import BoundaryError
from ...observability.logging import get_logger
from ...observability.metrics import (
    AnalogFourPatchPublicationErrorCode,
    AnalogFourPatchPublicationOperation,
    get_metrics,
)
from ...observability.tracing import operation
from .analog_four_export_contracts import (
    AnalogFourExportErrorCode,
    analog_four_export_path_name,
    require_analog_four_export_path,
)
from .analog_four_patch_batch_codec import (
    analog_four_patch_batch_sha256,
    encode_analog_four_patch_batch_json,
)
from .writer import WriteResult, atomic_write

_logger = get_logger(__name__)
_LOCK_OWNERSHIP_CHANGED_ERROR: Final[str] = "publication lock ownership changed"
_LOCK_OWNER_FIELDS_REQUIRED_ERROR: Final[str] = (
    "lock ownership verification requires all owner fields"
)
_LOCK_OPERATION_GATE_SUFFIX: Final[str] = ".operation"


class AnalogFourPatchBatchPublicationError(BoundaryError, RuntimeError):
    """A generation artifact conflicts with an immutable published path."""

    fingerprint: ClassVar[str] = "a4.audio_patch_batch.publication_failed"

    def __init__(
        self,
        message: str,
        *,
        error_code: AnalogFourExportErrorCode,
        diagnostic: str | None = None,
    ) -> None:
        super().__init__(message, context={"error_code": error_code})
        self.error_code: AnalogFourExportErrorCode = error_code
        self.diagnostic = diagnostic


class AnalogFourPatchBatchLockedError(BoundaryError, FileExistsError):
    """A cooperative A4 batch publisher already owns the track lock."""

    fingerprint: ClassVar[str] = "a4.audio_patch_batch.publication_locked"
    error_code: ClassVar[AnalogFourExportErrorCode] = "publication_locked"


class _BatchLockPayload(TypedDict):
    schema_version: str
    generation_id: str
    publication_nonce: str
    process_id: int
    created_unix_seconds: float
    audio_sha256: str
    source_kit_sha256: str


if TYPE_CHECKING:

    class _AtomicWriter(Protocol):
        def __call__(
            self,
            path: Path,
            data: bytes,
            *,
            overwrite: bool = False,
        ) -> WriteResult: ...


def _lock_recovery_summary(lock_path: Path) -> str:
    try:
        decoded = cast(object, json.loads(lock_path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError, UnicodeError):
        return "unavailable"
    if not isinstance(decoded, dict):
        return "unavailable"
    payload = cast(dict[object, object], decoded)
    fields: list[str] = []
    process_id = payload.get("process_id")
    if isinstance(process_id, int) and not isinstance(process_id, bool):
        fields.append(f"process_id={process_id}")
    created = payload.get("created_unix_seconds")
    if isinstance(created, (int, float)) and not isinstance(created, bool):
        fields.append(f"created_unix_seconds={created}")
    generation_id = payload.get("generation_id")
    if isinstance(generation_id, str) and len(generation_id) == 32:
        fields.append(f"generation_id={generation_id}")
    return ", ".join(fields) if fields else "unavailable"


def _safe_lock_cleanup_diagnostic(lock_path: Path, exc: BaseException) -> str:
    if isinstance(exc, AnalogFourPatchBatchPublicationError) and exc.diagnostic is not None:
        return exc.diagnostic
    if isinstance(exc, ValueError) and exc.args == (_LOCK_OWNERSHIP_CHANGED_ERROR,):
        return f"{lock_path.name}: ownership changed; lock retained"
    if isinstance(exc, AnalogFourPatchBatchLockedError):
        return f"{lock_path.name}: lock operation in progress; lock retained"
    code = getattr(exc, "winerror", None)
    if not isinstance(code, int):
        code = getattr(exc, "errno", None)
    code_suffix = f" code={code}" if isinstance(code, int) else ""
    return f"{lock_path.name}: {type(exc).__name__}{code_suffix}; lock retained"


def _lock_operation_gate_path(lock_path: Path) -> Path:
    return lock_path.with_name(lock_path.name + _LOCK_OPERATION_GATE_SUFFIX)


def _acquire_lock_operation_gate(lock_path: Path) -> Path:
    gate_path = _lock_operation_gate_path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        gate_path.mkdir()
    except FileExistsError as exc:
        raise AnalogFourPatchBatchLockedError(
            f"batch publication lock operation already in progress: {gate_path.name}; "
            "retry only after confirming the owning process is no longer running"
        ) from exc
    return gate_path


def _release_lock_operation_gate(gate_path: Path) -> BaseException | None:
    try:
        gate_path.rmdir()
    except (OSError, KeyboardInterrupt, SystemExit) as exc:
        return exc
    return None


def _safe_gate_cleanup_diagnostic(gate_path: Path, exc: BaseException) -> str:
    code = getattr(exc, "winerror", None)
    if not isinstance(code, int):
        code = getattr(exc, "errno", None)
    code_suffix = f" code={code}" if isinstance(code, int) else ""
    return f"{gate_path.name}: {type(exc).__name__}{code_suffix}"


def _attach_gate_cleanup_note(
    exc: BaseException,
    *,
    gate_path: Path,
    cleanup_error: BaseException | None,
) -> None:
    if cleanup_error is not None:
        exc.add_note(
            "batch lock operation gate cleanup failure: "
            + _safe_gate_cleanup_diagnostic(gate_path, cleanup_error)
        )


def _raise_gate_cleanup_interruption(
    exc: KeyboardInterrupt | SystemExit,
    *,
    details: str,
) -> Never:
    if isinstance(exc, KeyboardInterrupt):
        raise KeyboardInterrupt(f"{exc}; {details}") from exc
    raise SystemExit(f"{exc}; {details}") from exc


def _record_publication_failure(
    *,
    publication_operation: AnalogFourPatchPublicationOperation,
    operation_id: str,
    started_at: float,
    error_code: AnalogFourPatchPublicationErrorCode,
    exc: BaseException,
    artifact_name: str,
) -> None:
    metrics = get_metrics()
    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics.record_a4_patch_publication(
        publication_operation,
        duration_ms,
        error_code=error_code,
    )
    _logger.warning(
        "Analog Four batch publication operation failed",
        extra={
            "op_id": operation_id,
            "operation": f"a4_patch_{publication_operation}",
            "publication_operation": publication_operation,
            "outcome": "failed",
            "error_code": error_code,
            "error_type": type(exc).__name__,
            "fingerprint": getattr(
                exc,
                "fingerprint",
                "a4.audio_patch_batch.publication_failed",
            ),
            "artifact_name": artifact_name,
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )


def _record_publication_success(
    *,
    publication_operation: AnalogFourPatchPublicationOperation,
    operation_id: str,
    started_at: float,
    outcome: str,
    artifact_name: str,
) -> None:
    metrics = get_metrics()
    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics.record_a4_patch_publication(publication_operation, duration_ms)
    _logger.info(
        "Analog Four batch publication operation completed",
        extra={
            "op_id": operation_id,
            "operation": f"a4_patch_{publication_operation}",
            "publication_operation": publication_operation,
            "outcome": outcome,
            "artifact_name": artifact_name,
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )


def publish_immutable_artifact(
    path: Path,
    data: bytes,
    *,
    writer: _AtomicWriter = atomic_write,
) -> WriteResult:
    """Publish generation-addressed bytes or reuse an identical artifact."""

    started_at = time.perf_counter()
    reading_existing = False
    outcome = "published"
    artifact_name = analog_four_export_path_name(path)
    operation_id = ""
    try:
        with operation(
            "a4_patch_artifact_publish",
            logger=_logger,
            artifact_name=artifact_name,
        ) as operation_id:
            path = require_analog_four_export_path(path, field_name="path")
            expected_sha256 = analog_four_patch_batch_sha256(data)
            try:
                result = writer(path, data)
            except FileExistsError as exc:
                reading_existing = True
                existing_sha256 = analog_four_patch_batch_sha256(path.read_bytes())
                if existing_sha256 != expected_sha256:
                    raise AnalogFourPatchBatchPublicationError(
                        f"generation artifact collision at {path}: existing bytes do not match",
                        error_code="write_failed",
                    ) from exc
                outcome = "reused"
                result = WriteResult(
                    path=path.resolve(),
                    bytes_written=len(data),
                    overwrote_existing=False,
                )
    except (
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        KeyboardInterrupt,
        SystemExit,
    ) as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            error_code: AnalogFourPatchPublicationErrorCode = "interrupted"
        elif isinstance(exc, AnalogFourPatchBatchPublicationError):
            error_code = "artifact_collision"
        elif reading_existing:
            error_code = "read_failed"
        else:
            error_code = "write_failed"
        _record_publication_failure(
            publication_operation="artifact_publish",
            operation_id=operation_id,
            started_at=started_at,
            error_code=error_code,
            exc=exc,
            artifact_name=artifact_name,
        )
        raise

    _record_publication_success(
        publication_operation="artifact_publish",
        operation_id=operation_id,
        started_at=started_at,
        outcome=outcome,
        artifact_name=artifact_name,
    )
    return result


def release_batch_lock(
    lock_path: Path,
    *,
    generation_id: str | None = None,
    publication_nonce: str | None = None,
    audio_sha256: str | None = None,
    source_kit_sha256: str | None = None,
) -> str | None:
    """Release a cooperative publication lock, returning cleanup diagnostics."""

    started_at = time.perf_counter()
    existed = False
    gate_path: Path | None = None
    operation_id = ""
    expected_values = (
        generation_id,
        publication_nonce,
        audio_sha256,
        source_kit_sha256,
    )
    try:
        with operation(
            "a4_patch_lock_release",
            logger=_logger,
            lock_name=lock_path.name,
        ) as operation_id:
            if any(value is not None for value in expected_values) and not all(
                value is not None for value in expected_values
            ):
                raise ValueError(_LOCK_OWNER_FIELDS_REQUIRED_ERROR)
            gate_path = _acquire_lock_operation_gate(lock_path)
            try:
                existed = lock_path.exists()
                if existed:
                    if publication_nonce is None:
                        raise ValueError(
                            "lock owner fields are required to release an existing lock"
                        )
                    with lock_path.open("r", encoding="utf-8") as lock_file:
                        decoded = cast(object, json.load(lock_file))
                    if not isinstance(decoded, dict):
                        raise ValueError(_LOCK_OWNERSHIP_CHANGED_ERROR)
                    payload = cast(dict[object, object], decoded)
                    if any(
                        payload.get(key) != expected
                        for key, expected in (
                            ("generation_id", generation_id),
                            ("publication_nonce", publication_nonce),
                            ("audio_sha256", audio_sha256),
                            ("source_kit_sha256", source_kit_sha256),
                        )
                    ):
                        raise ValueError(_LOCK_OWNERSHIP_CHANGED_ERROR)
                    lock_path.unlink()
            except (
                OSError,
                RuntimeError,
                ValueError,
                TypeError,
                KeyboardInterrupt,
                SystemExit,
            ) as exc:
                _attach_gate_cleanup_note(
                    exc,
                    gate_path=gate_path,
                    cleanup_error=_release_lock_operation_gate(gate_path),
                )
                raise
            gate_cleanup_error = _release_lock_operation_gate(gate_path)
            if gate_cleanup_error is not None:
                retry_cleanup_error = _release_lock_operation_gate(gate_path)
                details = _safe_gate_cleanup_diagnostic(gate_path, gate_cleanup_error)
                if retry_cleanup_error is None:
                    details += "; operation gate cleanup retry completed"
                else:
                    details += "; retry failed: " + _safe_gate_cleanup_diagnostic(
                        gate_path,
                        retry_cleanup_error,
                    )
                    details += "; operation gate retained"
                if isinstance(gate_cleanup_error, (KeyboardInterrupt, SystemExit)):
                    _raise_gate_cleanup_interruption(
                        gate_cleanup_error,
                        details=details,
                    )
                raise AnalogFourPatchBatchPublicationError(
                    f"batch lock operation gate cleanup failed: {details}",
                    error_code="write_failed",
                    diagnostic=details,
                )
    except (
        AnalogFourPatchBatchLockedError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyboardInterrupt,
        SystemExit,
    ) as exc:
        error_code: AnalogFourPatchPublicationErrorCode = (
            "interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "release_failed"
        )
        _record_publication_failure(
            publication_operation="lock_release",
            operation_id=operation_id,
            started_at=started_at,
            error_code=error_code,
            exc=exc,
            artifact_name=lock_path.name,
        )
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        if isinstance(exc, ValueError) and exc.args == (_LOCK_OWNER_FIELDS_REQUIRED_ERROR,):
            raise
        return _safe_lock_cleanup_diagnostic(lock_path, exc)

    _record_publication_success(
        publication_operation="lock_release",
        operation_id=operation_id,
        started_at=started_at,
        outcome="released" if existed else "already_absent",
        artifact_name=lock_path.name,
    )
    return None


def acquire_batch_lock(
    lock_path: Path,
    *,
    generation_id: str,
    publication_nonce: str,
    audio_sha256: str,
    source_kit_sha256: str,
    writer: _AtomicWriter = atomic_write,
) -> WriteResult:
    """Acquire a race-safe cooperative lock with recoverable owner metadata."""

    started_at = time.perf_counter()
    payload: _BatchLockPayload = {
        "schema_version": "analog-four-audio-patch-batch-lock-v1",
        "generation_id": generation_id,
        "publication_nonce": publication_nonce,
        "process_id": os.getpid(),
        "created_unix_seconds": time.time(),
        "audio_sha256": audio_sha256,
        "source_kit_sha256": source_kit_sha256,
    }
    gate_path: Path | None = None
    operation_id = ""
    try:
        with operation(
            "a4_patch_lock_acquire",
            logger=_logger,
            lock_name=lock_path.name,
            generation_id=generation_id,
        ) as operation_id:
            gate_path = _acquire_lock_operation_gate(lock_path)
            try:
                result = writer(lock_path, encode_analog_four_patch_batch_json(payload))
            except FileExistsError as exc:
                metadata = _lock_recovery_summary(lock_path)
                cleanup_error = _release_lock_operation_gate(gate_path)
                message = (
                    f"batch publication lock already exists: {lock_path.name}; "
                    "remove it only after confirming its process is no longer running; "
                    f"recovery metadata: {metadata}"
                )
                if cleanup_error is not None:
                    message += (
                        "; batch lock operation gate cleanup failure: "
                        + _safe_gate_cleanup_diagnostic(gate_path, cleanup_error)
                    )
                raise AnalogFourPatchBatchLockedError(message) from exc
            except (
                OSError,
                RuntimeError,
                TypeError,
                ValueError,
                KeyboardInterrupt,
                SystemExit,
            ) as exc:
                _attach_gate_cleanup_note(
                    exc,
                    gate_path=gate_path,
                    cleanup_error=_release_lock_operation_gate(gate_path),
                )
                raise
            gate_cleanup_error = _release_lock_operation_gate(gate_path)
            if gate_cleanup_error is not None:
                lock_cleanup_error: BaseException | None = None
                try:
                    lock_path.unlink()
                except (OSError, KeyboardInterrupt, SystemExit) as exc:
                    lock_cleanup_error = exc
                retry_cleanup_error = _release_lock_operation_gate(gate_path)
                details = _safe_gate_cleanup_diagnostic(gate_path, gate_cleanup_error)
                if lock_cleanup_error is not None:
                    details += "; " + _safe_lock_cleanup_diagnostic(
                        lock_path,
                        lock_cleanup_error,
                    )
                if retry_cleanup_error is not None:
                    details += "; retry failed: " + _safe_gate_cleanup_diagnostic(
                        gate_path,
                        retry_cleanup_error,
                    )
                    details += "; operation gate retained"
                else:
                    details += "; operation gate cleanup retry completed"
                if isinstance(gate_cleanup_error, (KeyboardInterrupt, SystemExit)):
                    _raise_gate_cleanup_interruption(
                        gate_cleanup_error,
                        details=details,
                    )
                raise AnalogFourPatchBatchPublicationError(
                    f"batch lock operation gate cleanup failed: {details}",
                    error_code="write_failed",
                )
    except (
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        KeyboardInterrupt,
        SystemExit,
    ) as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            error_code: AnalogFourPatchPublicationErrorCode = "interrupted"
        elif isinstance(exc, AnalogFourPatchBatchLockedError):
            error_code = "lock_exists"
        else:
            error_code = "write_failed"
        _record_publication_failure(
            publication_operation="lock_acquire",
            operation_id=operation_id,
            started_at=started_at,
            error_code=error_code,
            exc=exc,
            artifact_name=lock_path.name,
        )
        raise

    _record_publication_success(
        publication_operation="lock_acquire",
        operation_id=operation_id,
        started_at=started_at,
        outcome="acquired",
        artifact_name=lock_path.name,
    )
    return result


def batch_lock_matches_request(
    lock_path: Path,
    *,
    generation_id: str,
    publication_nonce: str,
    audio_sha256: str,
    source_kit_sha256: str,
) -> bool:
    """Return whether a recoverable lock belongs to this publication attempt."""

    started_at = time.perf_counter()
    operation_id = secrets.token_hex(8)
    try:
        decoded = cast(object, json.loads(lock_path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError, UnicodeError) as exc:
        _record_publication_failure(
            publication_operation="lock_release",
            operation_id=operation_id,
            started_at=started_at,
            error_code="read_failed",
            exc=exc,
            artifact_name=lock_path.name,
        )
        return False
    if not isinstance(decoded, dict):
        _record_publication_failure(
            publication_operation="lock_release",
            operation_id=operation_id,
            started_at=started_at,
            error_code="read_failed",
            exc=ValueError("batch lock ownership metadata must be a JSON object"),
            artifact_name=lock_path.name,
        )
        return False
    payload = cast(dict[object, object], decoded)
    return bool(
        payload.get("generation_id") == generation_id
        and payload.get("publication_nonce") == publication_nonce
        and payload.get("process_id") == os.getpid()
        and payload.get("audio_sha256") == audio_sha256
        and payload.get("source_kit_sha256") == source_kit_sha256
    )


__all__ = [
    "AnalogFourPatchBatchLockedError",
    "AnalogFourPatchBatchPublicationError",
    "acquire_batch_lock",
    "batch_lock_matches_request",
    "publish_immutable_artifact",
    "release_batch_lock",
]
