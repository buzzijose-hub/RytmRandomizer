"""Race-safe publication primitives for Analog Four patch batches."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Protocol, TypedDict

from ...observability.errors import BoundaryError
from .analog_four_export_contracts import AnalogFourExportErrorCode
from .analog_four_patch_batch_codec import (
    analog_four_patch_batch_sha256,
    encode_analog_four_patch_batch_json,
)
from .writer import WriteResult, atomic_write


class AnalogFourPatchBatchPublicationError(BoundaryError, RuntimeError):
    """A generation artifact conflicts with an immutable published path."""

    fingerprint = "a4.audio_patch_batch.publication_failed"

    def __init__(self, message: str, *, error_code: AnalogFourExportErrorCode) -> None:
        super().__init__(message, context={"error_code": error_code})
        self.error_code: AnalogFourExportErrorCode = error_code


class AnalogFourPatchBatchLockedError(BoundaryError, FileExistsError):
    """A cooperative A4 batch publisher already owns the track lock."""

    fingerprint = "a4.audio_patch_batch.publication_locked"
    error_code: AnalogFourExportErrorCode = "publication_locked"


class _BatchLockPayload(TypedDict):
    schema_version: str
    generation_id: str
    publication_nonce: str
    process_id: int
    created_unix_seconds: float
    audio_sha256: str
    source_kit_sha256: str


class _AtomicWriter(Protocol):  # pragma: no cover - typing-only callback shape
    def __call__(
        self,
        path: Path,
        data: bytes,
        *,
        overwrite: bool = False,
    ) -> WriteResult: ...


def publish_immutable_artifact(
    path: Path,
    data: bytes,
    *,
    writer: _AtomicWriter = atomic_write,
) -> WriteResult:
    """Publish generation-addressed bytes or reuse an identical artifact."""

    expected_sha256 = analog_four_patch_batch_sha256(data)
    try:
        return writer(path, data)
    except FileExistsError as exc:
        existing_sha256 = analog_four_patch_batch_sha256(path.read_bytes())
        if existing_sha256 != expected_sha256:
            raise AnalogFourPatchBatchPublicationError(
                f"generation artifact collision at {path}: existing bytes do not match",
                error_code="write_failed",
            ) from exc
        return WriteResult(
            path=path.resolve(),
            bytes_written=len(data),
            overwrote_existing=False,
        )


def release_batch_lock(lock_path: Path) -> str | None:
    """Release a cooperative publication lock, returning cleanup diagnostics."""

    try:
        lock_path.unlink(missing_ok=True)
    except OSError as exc:
        return f"{lock_path}: {exc}"
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

    payload: _BatchLockPayload = {
        "schema_version": "analog-four-audio-patch-batch-lock-v1",
        "generation_id": generation_id,
        "publication_nonce": publication_nonce,
        "process_id": os.getpid(),
        "created_unix_seconds": time.time(),
        "audio_sha256": audio_sha256,
        "source_kit_sha256": source_kit_sha256,
    }
    try:
        return writer(lock_path, encode_analog_four_patch_batch_json(payload))
    except FileExistsError as exc:
        try:
            metadata = lock_path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError):
            metadata = "unavailable"
        raise AnalogFourPatchBatchLockedError(
            f"batch publication lock already exists: {lock_path}; "
            "remove it only after confirming its process is no longer running; "
            f"lock metadata: {metadata}"
        ) from exc


def batch_lock_matches_request(
    lock_path: Path,
    *,
    generation_id: str,
    publication_nonce: str,
    audio_sha256: str,
    source_kit_sha256: str,
) -> bool:
    """Return whether a recoverable lock belongs to this publication attempt."""

    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeError):
        return False
    return bool(
        isinstance(payload, dict)
        and payload.get("generation_id") == generation_id
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
