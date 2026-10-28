"""Content-addressed sound artifacts using the canonical bounded atomic writer."""

from __future__ import annotations

import hashlib
import os
import re
import stat
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from itertools import islice
from pathlib import Path
from typing import Final, Literal, cast

from ...data.persisted_state import (
    PERSISTED_STATE_REFUSAL_METRIC_CODES,
    classify_payload,
    require_schema_version,
)
from ...observability.errors import BoundaryError, DataError, PersistedStateVersionError
from ...observability.metrics import get_metrics
from ..data import canonical_json_bytes, require_object
from ..profiles.paths import default_profiles_dir
from .reader import decode_json_rejecting_duplicate_keys, read_bounded_artifact
from .reference_sound_audio import REFERENCE_AUDIO_MAX_BYTES
from .reference_sound_errors import (
    REFERENCE_SOUND_FAILURE_MESSAGES,
    reference_sound_error_context,
)
from .writer import atomic_write_set, guard_atomic_write_tree

REFERENCE_SOUND_STORE_ID: Final[str] = "reference_sound_store"
REFERENCE_SOUND_SCHEMA: Final[int] = require_schema_version(REFERENCE_SOUND_STORE_ID)
REFERENCE_SOUND_MAX_MANIFEST_BYTES: Final[int] = 1024 * 1024
REFERENCE_SOUND_MAX_FILES: Final[int] = 2048
REFERENCE_SOUND_MAX_TOTAL_BYTES: Final[int] = 256 * 1024 * 1024
REFERENCE_SOUND_MAX_SESSIONS: Final[int] = 64
_DIGEST: Final[re.Pattern[str]] = re.compile(r"^[a-f0-9]{64}$")
_SESSION_ID: Final[re.Pattern[str]] = re.compile(r"^sound-[a-f0-9]{32}$")
_EXTENSIONS: Final[tuple[str, ...]] = ("wav", "syx")
_PUBLICATION_LOCK_NAME: Final[str] = ".sound-publication.lock"
_WINDOWS_PUBLICATION_LOCK: Final[bool] = os.name == "nt"


def reference_sound_digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def reference_sound_json(value: Mapping[str, object]) -> bytes:
    return canonical_json_bytes(value)


def default_reference_sound_dir() -> Path:
    return default_profiles_dir().parent / "reference-sounds"


def require_sound_session_id(value: object) -> str:
    if not isinstance(value, str) or _SESSION_ID.fullmatch(value) is None:
        raise ValueError("Choose an existing reference-sound session.")
    return value


def sound_artifact_name(digest: str, extension: str) -> str:
    if _DIGEST.fullmatch(digest) is None or extension not in _EXTENSIONS:
        raise ValueError("Reference-sound artifact identity is invalid.")
    return f"{digest}.{extension}"


class ReferenceSoundStore:
    """Store immutable inputs and exact candidates; publication never grants SEND."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory if directory is not None else default_reference_sound_dir()

    @contextmanager
    def _publication_guard(self) -> Generator[None, None, None]:
        """A crash releases the OS lock; the inert namespace file may remain."""
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / _PUBLICATION_LOCK_NAME
        descriptor = os.open(
            path,
            os.O_CREAT
            | os.O_RDWR
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NOINHERIT", 0),
            0o600,
        )
        with os.fdopen(descriptor, "r+b") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ValueError("Reference-sound publication namespace is invalid.")
            if _WINDOWS_PUBLICATION_LOCK:
                import msvcrt  # noqa: PLC0415

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl  # noqa: PLC0415

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                if _WINDOWS_PUBLICATION_LOCK:
                    import msvcrt  # noqa: PLC0415

                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl  # noqa: PLC0415

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @contextmanager
    def _guard(self, *, create: bool = False) -> Generator[None, None, None]:
        if create:
            self.directory.mkdir(parents=True, exist_ok=True)
        metadata = self.directory.stat(follow_symlinks=False)
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValueError("Reference-sound storage must be a regular directory.")
        with guard_atomic_write_tree(self.directory, (metadata.st_dev, metadata.st_ino)):
            yield

    def read_artifact(self, digest: str, extension: str) -> bytes:
        path = self.directory / sound_artifact_name(digest, extension)
        with self._guard():
            value = read_bounded_artifact(path, maximum=REFERENCE_AUDIO_MAX_BYTES)
        if reference_sound_digest(value) != digest:
            raise DataError(
                "Retained sound artifact changed; recover the original copy.",
                context={"category": "hash"},
            )
        return value

    def load(self, session_id: str) -> dict[str, object]:
        session_id = require_sound_session_id(session_id)
        path = self.directory / f"{session_id}.sound.json"
        with self._guard():
            encoded = read_bounded_artifact(path, maximum=REFERENCE_SOUND_MAX_MANIFEST_BYTES)
        readable = True
        try:
            value = decode_json_rejecting_duplicate_keys(encoded)
        except (ValueError, RecursionError):
            value = None
            readable = False
        if isinstance(value, Mapping):
            # Authenticate the original envelope before the registry can stamp
            # a newer version. Reading never replaces the retained manifest.
            original = dict(
                require_object(cast(object, value), "Reference-sound manifest", ValueError)
            )
            checksum = original.pop("content_sha256", None)
            if original.get("session_id") != session_id or checksum != reference_sound_digest(
                reference_sound_json(original)
            ):
                raise ValueError("Reference-sound session is incompatible or corrupt.")
            value = original
        decision = classify_payload(REFERENCE_SOUND_STORE_ID, value, readable=readable)
        if decision.refused:
            get_metrics().record_persisted_state_refusal(
                REFERENCE_SOUND_STORE_ID, PERSISTED_STATE_REFUSAL_METRIC_CODES[decision.code]
            )
            if decision.code == "persisted_state.schema_newer_than_app":
                raise PersistedStateVersionError(
                    "Reference-sound schema was written by a newer app; keep the saved files and use a compatible app.",
                    context={
                        "store_id": REFERENCE_SOUND_STORE_ID,
                        **decision.detail,
                        "error_code": "schema_newer",
                    },
                )
            raise DataError(
                "Reference-sound session is corrupt or incompatible; recover its manifest.",
                context={
                    "category": "schema",
                    "reason": decision.code,
                    "error_code": "session_corrupt",
                },
            )
        if decision.payload is None:
            raise ValueError("Reference-sound session is incompatible or corrupt.")
        payload = dict(decision.payload)
        if (
            type(payload.get("schema_version")) is not int
            or payload.get("schema_version") != REFERENCE_SOUND_SCHEMA
            or payload.get("session_id") != session_id
        ):
            raise ValueError("Reference-sound session is incompatible or corrupt.")
        if decision.code == "persisted_state.migrated":
            get_metrics().record_persisted_state_migration(
                REFERENCE_SOUND_STORE_ID,
                int(decision.from_version or 0),
                int(decision.to_version or 0),
            )
        return payload

    def publish(
        self,
        payload: Mapping[str, object],
        artifacts: Mapping[str, object],
        *,
        expected_manifest: str | None | Literal["unconditional"] = "unconditional",
    ) -> None:
        with self._guard(create=True), self._publication_guard():
            session_id = require_sound_session_id(payload.get("session_id"))
            manifest = self.directory / f"{session_id}.sound.json"
            if expected_manifest != "unconditional":
                current = (
                    reference_sound_digest(reference_sound_json(self.load(session_id)))
                    if manifest.exists()
                    else None
                )
                if current != expected_manifest:
                    raise BoundaryError(
                        REFERENCE_SOUND_FAILURE_MESSAGES["session_changed"],
                        context=reference_sound_error_context("session_changed"),
                    )
            self._publish_verified(payload, artifacts)

    def _publish_verified(
        self, payload: Mapping[str, object], artifacts: Mapping[str, object]
    ) -> None:
        session_id = require_sound_session_id(payload.get("session_id"))
        if (
            type(payload.get("schema_version")) is not int
            or payload.get("schema_version") != REFERENCE_SOUND_SCHEMA
        ):
            raise ValueError("Reference-sound schema is incompatible.")
        document = dict(payload)
        document["content_sha256"] = reference_sound_digest(reference_sound_json(payload))
        encoded = reference_sound_json(document)
        if len(encoded) > REFERENCE_SOUND_MAX_MANIFEST_BYTES:
            raise BoundaryError(
                REFERENCE_SOUND_FAILURE_MESSAGES["manifest_limit"],
                context=reference_sound_error_context("manifest_limit"),
            )
        manifest = self.directory / f"{session_id}.sound.json"
        with self._guard(create=True):
            existing = tuple(
                islice(
                    (
                        path
                        for path in self.directory.iterdir()
                        if path.name != _PUBLICATION_LOCK_NAME
                    ),
                    REFERENCE_SOUND_MAX_FILES + 1,
                )
            )
            if len(existing) > REFERENCE_SOUND_MAX_FILES:
                raise BoundaryError(
                    REFERENCE_SOUND_FAILURE_MESSAGES["storage_limit"],
                    context=reference_sound_error_context("storage_limit"),
                )
            manifests = tuple(path for path in existing if path.name.endswith(".sound.json"))
            if not manifest.exists() and len(manifests) >= REFERENCE_SOUND_MAX_SESSIONS:
                raise BoundaryError(
                    REFERENCE_SOUND_FAILURE_MESSAGES["session_limit"],
                    context=reference_sound_error_context("session_limit"),
                )
            writes: dict[Path, bytes] = {}
            for name, data in artifacts.items():
                digest, separator, extension = name.rpartition(".")
                if separator != ".":
                    raise ValueError("Reference-sound artifact name is invalid.")
                sound_artifact_name(digest, extension)
                if not isinstance(data, bytes) or not 1 <= len(data) <= REFERENCE_AUDIO_MAX_BYTES:
                    raise ValueError("Reference-sound artifact size is invalid.")
                if reference_sound_digest(data) != digest:
                    raise ValueError("Reference-sound artifact hash does not match.")
                path = self.directory / name
                if path.exists():
                    self.read_artifact(digest, extension)
                else:
                    writes[path] = data
            if len(existing) + len(writes) + int(not manifest.exists()) > REFERENCE_SOUND_MAX_FILES:
                raise BoundaryError(
                    REFERENCE_SOUND_FAILURE_MESSAGES["storage_limit"],
                    context=reference_sound_error_context("storage_limit"),
                )
            total = sum(path.stat(follow_symlinks=False).st_size for path in existing)
            if (
                total + sum(len(data) for data in writes.values()) + len(encoded)
                > REFERENCE_SOUND_MAX_TOTAL_BYTES
            ):
                raise BoundaryError(
                    REFERENCE_SOUND_FAILURE_MESSAGES["storage_limit"],
                    context=reference_sound_error_context("storage_limit"),
                )
            writes[manifest] = encoded
            atomic_write_set(writes, overwrite=True, redact_diagnostics=True)

    def catalog(self) -> tuple[dict[str, object], ...]:
        if not self.directory.exists():
            return ()
        paths = tuple(islice(self.directory.glob("*.sound.json"), REFERENCE_SOUND_MAX_SESSIONS + 1))
        if len(paths) > REFERENCE_SOUND_MAX_SESSIONS:
            raise BoundaryError(
                REFERENCE_SOUND_FAILURE_MESSAGES["session_limit"],
                context=reference_sound_error_context("session_limit"),
            )
        return tuple(self.load(path.name.removesuffix(".sound.json")) for path in sorted(paths))
