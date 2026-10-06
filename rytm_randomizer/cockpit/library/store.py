"""JSON-record kit/sound library store + captures importer (WS-4).

Records live as one JSON file per record under the platform config dir,
following the ProfileRegistry precedent
(:func:`~rytm_randomizer.cockpit.profiles.paths.default_profiles_dir` —
the library sits in the sibling ``library`` leaf). Each record carries::

    {device_id, kit_name, fingerprint, captured_at, tags, payload_hex}

Store rules (all test-pinned):

* **Injected, never module-level.** The process's one
  :class:`LibraryStore` is constructed by the boot path and injected into
  the :class:`~rytm_randomizer.cockpit.ws.session.CockpitSession`; this
  module keeps zero module-level state.
* **Atomic writes only.** Every record write routes through
  :func:`~rytm_randomizer.cockpit.export.writer.atomic_write` (sibling
  tempfile + fsync + rename) so a crash can never truncate a record.
* **No wire-supplied paths.** The importer reads only the store's
  configured captures directory; record ids are validated against a
  strict charset before ever touching a filename (no traversal).
* **Device-generic decode.** Imported SysEx payloads are decoded through
  the :mod:`rytm_randomizer.devices` registry — every registered device
  family gets a decode attempt; no per-family branching here.

Backup-zip export is deferred to Wave 5 (recorded as a follow-up).
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Final, Literal, cast

from ...data.persisted_state import PERSISTED_STATE_REFUSAL_METRIC_CODES as _REFUSAL_METRIC_CODES
from ...data.persisted_state import (
    PERSISTED_STATE_VERSION_FIELD,
    classify_payload,
    require_schema_version,
)
from ...devices import all_devices
from ...observability.errors import DataError, PersistedStateVersionError
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...observability.tracing import trace
from ...snapshot.sysex_file import extract_sysex_payloads
from ..capture import KitCaptureResult, decode_kit_capture_frame
from ..data.rehearsal_favorite import LocalRehearsalFavorite
from ..data.show_bank import RetainedSysexArtifact
from ..data.stage import ANALOG_RYTM_DEVICE_ID
from ..engine import mutate
from ..engine.parameter_scope import rytm_parameter_depths
from ..export.reader import decode_json_rejecting_duplicate_keys, read_bounded_artifact
from ..export.writer import atomic_write_set, guard_atomic_write_tree
from ..profiles.paths import default_profiles_dir

__all__ = [
    "LIBRARY_STORE_ID",
    "LIBRARY_STORE_SCHEMA_VERSION",
    "LibraryImportResult",
    "LibraryRecord",
    "LibraryStore",
    "default_captures_dir",
    "default_library_dir",
]

LIBRARY_STORE_ID: Final[str] = "library_store"
"""Registry id in :mod:`rytm_randomizer.data.persisted_state` (spec §11 Contract A)."""

LIBRARY_STORE_SCHEMA_VERSION: Final[int] = require_schema_version(LIBRARY_STORE_ID)
"""The on-disk record version this module writes — sourced from the registry.

Never re-typed here: the registry is the single declaration, so bumping
it in one place is the only way to change what this store writes.
"""

_LIBRARY_LEAF: Final[str] = "library"
_RECORD_SUFFIX: Final[str] = ".json"
_CAPTURES_LEAF: Final[str] = "captures"
_FAVORITE_NAME_LIMIT: Final[int] = 128
LIBRARY_MAX_RECORD_BYTES: Final[int] = 4 * 1024 * 1024
LIBRARY_MAX_FILES: Final[int] = 4096
LIBRARY_MAX_CAPTURE_FILE_BYTES: Final[int] = 8 * 1024 * 1024
LIBRARY_MAX_SOURCE_FRAME_BYTES: Final[int] = 2 * 1024 * 1024
LIBRARY_MAX_TOTAL_BYTES: Final[int] = 64 * 1024 * 1024
SourceOrigin = Literal["input_capture", "file_import"]
_logger = get_logger(__name__)

_RECORD_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
"""Strict record-id charset — record ids become filenames, so no dots,
no separators, no traversal characters, bounded length."""

_DECODE_FAILURES: Final[tuple[type[BaseException], ...]] = (
    ValueError,
    KeyError,
    IndexError,
    NotImplementedError,
)
"""Exception families a device decoder raises on a payload it does not own."""


def default_library_dir() -> Path:
    """Platform-default library directory (ProfileRegistry precedent).

    Sibling of the profiles leaf under the same per-platform app config
    dir — e.g. ``~/Library/Application Support/rytm-randomizer/library``
    on macOS. Pure path computation; nothing is created on disk.
    """

    return default_profiles_dir().parent / _LIBRARY_LEAF


def default_captures_dir() -> Path:
    """Default captures directory the importer scans: ``./captures``.

    The repo (and the operator's working directory when launching the
    sidecar) keeps raw hardware dumps under ``captures/*.syx``.
    """

    return Path.cwd() / _CAPTURES_LEAF


def _validate_record_id(record_id: object) -> str:
    """Return ``record_id`` when it is filename-safe; raise otherwise.

    Typed ``object`` because ids arrive from wire/disk JSON — the
    ``isinstance`` check is genuine runtime validation.
    """

    if not isinstance(record_id, str) or _RECORD_ID_RE.fullmatch(record_id) is None:
        raise ValueError(f"invalid library record_id: {record_id!r}")
    return record_id


@dataclass(frozen=True)
class LibraryRecord:
    """One captured payload or inert Rytm semantic rehearsal favorite.

    Rehearsal source_hash is not a raw KIT frame fingerprint. Rehearsals
    retain exact semantic source/candidate values, not hardware restore bytes.
    """

    record_id: str
    device_id: str
    kit_name: str
    fingerprint: str
    captured_at: str
    tags: tuple[str, ...]
    payload_hex: str
    rehearsal: LocalRehearsalFavorite | None = None
    source_frame: RetainedSysexArtifact | None = None
    source_origin: SourceOrigin | None = None

    def to_dict(self) -> dict[str, object]:
        """JSON-safe dict form (the on-disk and on-wire shape)."""

        return {
            "record_id": self.record_id,
            "device_id": self.device_id,
            "kit_name": self.kit_name,
            "fingerprint": self.fingerprint,
            "captured_at": self.captured_at,
            "tags": list(self.tags),
            "payload_hex": self.payload_hex,
            "record_kind": "capture" if self.rehearsal is None else "rehearsal_favorite",
            "rehearsal": None if self.rehearsal is None else self.rehearsal.to_dict(),
            "source_frame": None if self.source_frame is None else self.source_frame.to_dict(),
            "source_origin": self.source_origin,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> LibraryRecord:
        """Rebuild a record from its dict form; raises ``ValueError`` on junk."""

        if raw.get(PERSISTED_STATE_VERSION_FIELD) == LIBRARY_STORE_SCHEMA_VERSION:
            required = {
                "record_id",
                "device_id",
                "kit_name",
                "fingerprint",
                "captured_at",
                "tags",
                "payload_hex",
                "record_kind",
                "rehearsal",
                "source_frame",
                "source_origin",
                PERSISTED_STATE_VERSION_FIELD,
            }
            if set(raw) != required:
                raise ValueError("library record fields differ from the schema")
        record_id = _validate_record_id(str(raw.get("record_id", "")))
        tags_raw = raw.get("tags", [])
        if not isinstance(tags_raw, (list, tuple)):
            raise ValueError(f"library record {record_id!r} has non-list tags")
        tag_values = cast("Sequence[object]", tags_raw)
        kind = raw.get("record_kind", "capture")
        rehearsal_raw = raw.get("rehearsal")
        if kind not in ("capture", "rehearsal_favorite") or (
            (kind == "capture") != (rehearsal_raw is None)
        ):
            raise ValueError("library record kind does not match rehearsal payload")
        rehearsal = (
            None if rehearsal_raw is None else LocalRehearsalFavorite.from_dict(rehearsal_raw)
        )
        frame_raw = raw.get("source_frame")
        if frame_raw is not None and not isinstance(frame_raw, Mapping):
            raise ValueError("library source frame must be an object")
        source_frame = (
            None
            if frame_raw is None
            else RetainedSysexArtifact.from_dict(cast(Mapping[str, object], frame_raw))
        )
        origin = raw.get("source_origin")
        if origin is not None and origin not in ("input_capture", "file_import"):
            raise ValueError("unsupported library source provenance")
        if (source_frame is None) != (origin is None) or (
            rehearsal is not None and source_frame is not None
        ):
            raise ValueError("library source provenance does not match record kind")
        if rehearsal is not None and (
            any(
                not isinstance(raw.get(key), str)
                for key in (
                    "record_id",
                    "device_id",
                    "kit_name",
                    "fingerprint",
                    "captured_at",
                    "payload_hex",
                )
            )
            or any(not isinstance(tag, str) for tag in tag_values)
        ):
            raise ValueError("library favorite metadata requires exact text fields")
        record = cls(
            record_id=record_id,
            device_id=str(raw.get("device_id", "")),
            kit_name=str(raw.get("kit_name", "")),
            fingerprint=str(raw.get("fingerprint", "")),
            captured_at=str(raw.get("captured_at", "")),
            tags=tuple(str(tag) for tag in tag_values),
            payload_hex=str(raw.get("payload_hex", "")),
            rehearsal=rehearsal,
            source_frame=source_frame,
            source_origin=origin,
        )
        if rehearsal is not None and (
            record.record_id != rehearsal.favorite_id
            or record.device_id != rehearsal.source_snapshot.device
            or record.fingerprint != rehearsal.source_hash
            or record.captured_at != rehearsal.source_snapshot.captured_at.isoformat()
            or record.payload_hex
        ):
            raise ValueError("library favorite metadata does not match retained source identity")
        return record

    def matches(self, query: str) -> bool:
        """Case-insensitive substring match over the searchable fields."""

        needle = query.lower()
        if not needle:
            return True
        haystacks = (
            self.kit_name,
            self.device_id,
            self.fingerprint,
            self.record_id,
            *self.tags,
        )
        return any(needle in value.lower() for value in haystacks)


@dataclass(frozen=True)
class LibraryImportResult:
    """Outcome of one :meth:`LibraryStore.import_captures` run."""

    imported: tuple[LibraryRecord, ...]
    skipped_existing: int
    failed_files: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """JSON-safe dict form for the ``library_import_captures`` ack."""

        return {
            "imported": [record.to_dict() for record in self.imported],
            "imported_count": len(self.imported),
            "skipped_existing": self.skipped_existing,
            "failed_files": list(self.failed_files),
        }


class LibraryStore:
    """Injected, file-backed library of captured kit/sound records.

    Args:
        library_dir: Directory holding one ``<record_id>.json`` per
            record. Created lazily on first write; construction performs
            no I/O.
        captures_dir: Directory :meth:`import_captures` scans for
            ``*.syx`` dumps. ``None`` means "importing is not configured"
            and :meth:`import_captures` raises ``ValueError``.
    """

    def __init__(self, library_dir: Path, *, captures_dir: Path | None = None) -> None:
        self._library_dir = Path(library_dir)
        self._captures_dir = None if captures_dir is None else Path(captures_dir)

    @property
    def library_dir(self) -> Path:
        """The record directory this store reads and writes."""

        return self._library_dir

    @property
    def captures_dir(self) -> Path | None:
        """The configured captures directory, or ``None`` when unset."""

        return self._captures_dir

    def list_records(self) -> tuple[LibraryRecord, ...]:
        """Every readable record, sorted by ``record_id`` (stable order).

        Unreadable / malformed record files are skipped — a corrupt file
        must never take the whole library surface down.
        """

        if not self._library_dir.is_dir():
            return ()
        records: list[LibraryRecord] = []
        for path in self._bounded_paths(self._library_dir, _RECORD_SUFFIX):
            record = _safe_load_record(path)
            if record is not None:
                records.append(record)
        return tuple(sorted(records, key=lambda record: record.record_id))

    def get(self, record_id: str) -> LibraryRecord | None:
        """Return one record by id, or ``None`` when absent."""

        _validate_record_id(record_id)
        self._bounded_paths(self._library_dir, _RECORD_SUFFIX)
        path = self._record_path(record_id)
        if not path.is_file():
            return None
        return _safe_load_record(path)

    @staticmethod
    def _bounded_paths(directory: Path, suffix: str) -> tuple[Path, ...]:
        if directory.is_symlink():
            raise ValueError("library directory cannot be a symlink")
        if not directory.exists():
            return ()
        paths: list[Path] = []
        total_bytes = 0
        for count, path in enumerate(directory.iterdir(), start=1):
            if count > LIBRARY_MAX_FILES:
                raise ValueError("library directory exceeds the file count bound")
            total_bytes += path.stat(follow_symlinks=False).st_size
            if total_bytes > LIBRARY_MAX_TOTAL_BYTES:
                raise ValueError("library directory exceeds the aggregate size bound")
            if path.suffix == suffix:
                paths.append(path)
        return tuple(sorted(paths))

    def retain_source(
        self, result: KitCaptureResult, *, origin: SourceOrigin = "input_capture"
    ) -> LibraryRecord:
        """Keep exact codec-verified bytes locally, without granting hardware authority."""
        if origin not in ("input_capture", "file_import"):
            raise ValueError("unsupported library source provenance")
        if not result.round_trip_verified or not result.input_only or result.sent_midi:
            raise ValueError("library source must be verified and input-only")
        decoded = decode_kit_capture_frame(result.device_id, result.frame)
        if (
            decoded.fingerprint != result.fingerprint
            or decoded.kit_name != result.kit_name
            or len(result.frame) != result.frame_bytes
        ):
            raise ValueError("library source metadata disagrees with exact bytes")
        payload = result.frame[1:-1]
        record_id = payload_fingerprint(payload)
        digest = sha256(result.frame).hexdigest()
        artifact = RetainedSysexArtifact(f"{digest}.syx", digest, len(result.frame))
        existing = self.get(record_id)
        if existing is not None:
            if existing.device_id != result.device_id or existing.payload_hex != payload.hex():
                raise ValueError("library source identity collision")
            if existing.source_frame is not None:
                if self.read_source_frame(record_id) != result.frame:
                    raise ValueError("library source identity collision")
                return existing
        record = LibraryRecord(
            record_id=record_id,
            device_id=result.device_id,
            kit_name=result.kit_name,
            fingerprint=record_id,
            captured_at=result.captured_at.isoformat(),
            tags=() if existing is None else existing.tags,
            payload_hex=payload.hex(),
            source_frame=artifact,
            source_origin=origin,
        )
        self._write_record(record, overwrite=existing is not None, frame=result.frame)
        return record

    def read_source_frame(
        self, record_id: str, *, allow_legacy_reconstruction: bool = False
    ) -> bytes:
        """Return inert source bytes; legacy envelope reconstruction is explicit.

        Legacy payloads lost only the F0/F7 delimiters, but have no retained
        framed-byte provenance. Reconstructing them never upgrades that claim.
        Semantic rehearsal favorites cannot be converted into real captures.
        """
        record = self.get(record_id)
        if record is None or record.rehearsal is not None:
            raise ValueError("library record has no exact source frame")
        if record.source_frame is not None:
            return _read_record_source_frame(self._library_dir, record)
        if not allow_legacy_reconstruction:
            raise ValueError("legacy source frame requires explicit reconstruction")
        payload = bytes.fromhex(record.payload_hex)
        if payload_fingerprint(payload) != record.fingerprint:
            raise ValueError("legacy source payload fingerprint mismatch")
        frame = b"\xf0" + payload + b"\xf7"
        decoded = decode_kit_capture_frame(record.device_id, frame)
        if decoded.kit_name != record.kit_name:
            raise ValueError("legacy source metadata mismatch")
        return frame

    def search(self, query: str) -> tuple[LibraryRecord, ...]:
        """Records whose searchable fields contain ``query`` (case-folded)."""

        return tuple(record for record in self.list_records() if record.matches(query))

    @staticmethod
    @trace("verify_rehearsal")
    def verify_rehearsal(favorite: LocalRehearsalFavorite) -> None:
        """Recompute retained values using canonical scope/engine, never send them.

        Candidate ULIDs are intentionally fresh on recomputation. The retained
        ULID is integrity-bound by the DTO hash; all deterministic values and
        provenance must agree independently of that nondeterministic field.
        """
        if favorite.source_snapshot.device != ANALOG_RYTM_DEVICE_ID:
            raise ValueError("favorite_a4_candidate_verification_unavailable")
        scope = favorite.mutation_scope()
        reproduced = mutate(
            favorite.source_snapshot,
            favorite.profile,
            favorite.candidate.depth,
            favorite.candidate.seed,
            target_pad_ids=scope.target_ids,
            locked_pad_ids=scope.locked_ids,
            parameter_depths=rytm_parameter_depths(
                favorite.source_snapshot, favorite.parameter_selection, favorite.candidate.depth
            ),
        )
        expected = favorite.candidate.to_dict()
        actual = reproduced.to_dict()
        expected.pop("candidate_id")
        actual.pop("candidate_id")
        if expected != actual:
            _logger.warning(
                "rehearsal_verification",
                extra={"decision": "deterministic_candidate", "outcome": "refused"},
            )
            raise ValueError("favorite_candidate_deterministic_verification_failed")
        _logger.debug(
            "rehearsal_verification",
            extra={
                "decision": "deterministic_candidate",
                "outcome": "verified",
                "item_count": len(favorite.candidate.pad_deltas),
            },
        )

    def retain_rehearsal(self, favorite: LocalRehearsalFavorite, name: str) -> LibraryRecord:
        """Retain an exact scoped candidate in the existing atomic JSON library."""
        if (
            not isinstance(cast(object, name), str)
            or not name.strip()
            or len(name) > _FAVORITE_NAME_LIMIT
        ):
            raise ValueError("favorite name must be nonempty text of at most 128 characters")
        self.verify_rehearsal(favorite)
        existing = self.get(favorite.favorite_id)
        if existing is not None:
            if existing.rehearsal != favorite:
                raise ValueError("favorite_record_identity_collision")
            return existing
        # Refused/corrupt records cannot be overwritten by a subsequent retain.
        record = LibraryRecord(
            record_id=favorite.favorite_id,
            device_id=favorite.source_snapshot.device,
            kit_name=name,
            fingerprint=favorite.source_hash,
            captured_at=favorite.source_snapshot.captured_at.isoformat(),
            tags=(),
            payload_hex="",
            rehearsal=favorite,
        )
        self._write_record(record, overwrite=False)
        return record

    def tag(self, record_id: str, tags: Sequence[str]) -> LibraryRecord:
        """Replace a record's tags; returns the updated record.

        Raises ``ValueError`` for an unknown id or a non-string tag.
        """

        existing = self.get(record_id)
        if existing is None:
            raise ValueError(f"unknown library record_id: {record_id!r}")
        clean_tags = tuple(str(tag) for tag in tags)
        updated = replace(existing, tags=clean_tags)
        self._write_record(updated, overwrite=True)
        return updated

    def delete(self, record_id: str) -> bool:
        """Delete one record; returns ``True`` when a file was removed."""

        _validate_record_id(record_id)
        self._bounded_paths(self._library_dir, _RECORD_SUFFIX)
        path = self._record_path(record_id)
        if not path.is_file():
            return False
        path.unlink()
        return True

    def import_captures(self) -> LibraryImportResult:
        """Import every ``*.syx`` under the configured captures directory.

        Per file: extract the SysEx payloads
        (:func:`~rytm_randomizer.snapshot.sysex_file.extract_sysex_payloads`),
        decode each payload through the devices registry (device-generic —
        first registered device whose decoder accepts the payload wins),
        fingerprint it, and persist a record keyed by the fingerprint.
        Payloads already in the library (same fingerprint) are skipped;
        files with no decodable payload are reported in ``failed_files``.
        """

        directory = self._captures_dir
        if directory is None:
            raise ValueError("library captures_dir is not configured")
        if not directory.is_dir():
            raise ValueError(f"library captures_dir does not exist: {directory}")

        existing_ids = {record.record_id for record in self.list_records()}
        imported: list[LibraryRecord] = []
        skipped = 0
        failed: list[str] = []
        for path in self._bounded_paths(directory, ".syx"):
            outcome = self._import_capture_file(path, existing_ids)
            imported.extend(outcome.imported)
            skipped += outcome.skipped_existing
            failed.extend(outcome.failed_files)
        return LibraryImportResult(
            imported=tuple(imported),
            skipped_existing=skipped,
            failed_files=tuple(failed),
        )

    # ------------------------------------------------------------------
    # Internal helpers.
    # ------------------------------------------------------------------

    def _import_capture_file(self, path: Path, existing_ids: set[str]) -> LibraryImportResult:
        """Import one ``*.syx`` file; never raises for a bad file."""

        try:
            raw = read_bounded_artifact(path, maximum=LIBRARY_MAX_CAPTURE_FILE_BYTES)
            frames = extract_sysex_payloads(raw, keep_framing=True)
        except (OSError, ValueError, DataError):
            return LibraryImportResult(
                imported=(),
                skipped_existing=0,
                failed_files=(path.name,),
            )
        imported: list[LibraryRecord] = []
        skipped = 0
        decoded_any = False
        for frame in frames:
            framed = frame.startswith(b"\xf0") and frame.endswith(b"\xf7")
            payload = frame[1:-1] if framed else frame
            decoded = _decode_with_any_device(payload)
            if decoded is None:
                continue
            decoded_any = True
            device_id, kit_name = decoded
            record_id = payload_fingerprint(payload)
            if record_id in existing_ids:
                skipped += 1
                continue
            result: KitCaptureResult | None = None
            if framed:
                try:
                    result = decode_kit_capture_frame(device_id, frame)
                except (DataError, KeyError, IndexError, TypeError, ValueError):
                    # Generic historical payload decoding is not exact KIT
                    # framing proof; never silently promote it to a capture.
                    pass
            record = LibraryRecord(
                record_id=record_id,
                device_id=device_id,
                kit_name=kit_name,
                fingerprint=record_id,
                captured_at=_capture_timestamp(path),
                tags=(),
                payload_hex=payload.hex(),
            )
            if result is not None:
                record = self.retain_source(
                    replace(result, captured_at=datetime.fromisoformat(record.captured_at)),
                    origin="file_import",
                )
            else:
                self._write_record(record, overwrite=False)
            existing_ids.add(record_id)
            imported.append(record)
        if not decoded_any:
            return LibraryImportResult(
                imported=(),
                skipped_existing=skipped,
                failed_files=(path.name,),
            )
        return LibraryImportResult(
            imported=tuple(imported),
            skipped_existing=skipped,
            failed_files=(),
        )

    def _record_path(self, record_id: str) -> Path:
        """Filesystem path for one (already validated) record id."""

        return self._library_dir / f"{record_id}{_RECORD_SUFFIX}"

    def _write_record(
        self, record: LibraryRecord, *, overwrite: bool, frame: bytes | None = None
    ) -> None:
        """Persist one record atomically (sibling tempfile + rename)."""

        # ``to_dict()`` is also the on-wire ack shape, so the persisted
        # envelope is stamped here (disk only) rather than in the DTO —
        # adding a field to the wire payload would change the WS contract.
        payload = record.to_dict()
        if record.rehearsal is not None:
            LibraryRecord.from_dict(payload)
            self.verify_rehearsal(record.rehearsal)
        payload[PERSISTED_STATE_VERSION_FIELD] = LIBRARY_STORE_SCHEMA_VERSION
        encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        if len(encoded) > LIBRARY_MAX_RECORD_BYTES:
            raise ValueError("library record exceeds the size bound")
        self._bounded_paths(self._library_dir, _RECORD_SUFFIX)
        self._library_dir.mkdir(parents=True, exist_ok=True)
        metadata = self._library_dir.stat(follow_symlinks=False)
        artifacts: dict[Path, object] = {}
        if record.source_frame is not None:
            artifact = record.source_frame
            destination = self._library_dir / artifact.artifact_name
            if os.path.lexists(destination):
                retained = _read_record_source_frame(self._library_dir, record)
                if frame is not None and retained != frame:
                    raise ValueError("library source content-address collision")
            elif frame is None:
                raise ValueError("library retained source frame is missing")
            else:
                _validate_record_source_frame(record, frame)
                artifacts[destination] = frame
        artifacts[self._record_path(record.record_id)] = encoded
        new_count = sum(not os.path.lexists(path) for path in artifacts)
        total_bytes = 0
        for count, _path in enumerate(self._library_dir.iterdir(), start=1):
            if count + new_count > LIBRARY_MAX_FILES:
                raise ValueError("library directory exceeds the file count bound")
            total_bytes += _path.stat(follow_symlinks=False).st_size
        total_bytes += sum(
            len(cast(bytes, content))
            - (path.stat(follow_symlinks=False).st_size if path.exists() else 0)
            for path, content in artifacts.items()
        )
        if total_bytes > LIBRARY_MAX_TOTAL_BYTES:
            raise ValueError("library directory exceeds the aggregate size bound")
        with guard_atomic_write_tree(self._library_dir, (metadata.st_dev, metadata.st_ino)):
            atomic_write_set(artifacts, overwrite=overwrite)


def _safe_load_record(path: Path) -> LibraryRecord | None:
    """Load one record file, or ``None`` when unreadable/malformed.

    Per-file data problems stay on the existing "warn and skip" policy —
    one corrupt record must not take the whole library surface down.

    The one outcome that is **not** skippable is the spec §11 downgrade
    case: a record written by a newer app. Skipping it would present the
    operator with a silently shorter library after a rollback, which is
    the silent data loss Contract A forbids, so it raises instead. The
    bytes on disk are never rewritten either way.
    """

    readable = True
    raw: object = None
    try:
        raw = decode_json_rejecting_duplicate_keys(
            read_bounded_artifact(path, maximum=LIBRARY_MAX_RECORD_BYTES)
        )
    except (OSError, ValueError, DataError, RecursionError):
        readable = False

    decision = classify_payload(LIBRARY_STORE_ID, raw, readable=readable)
    if decision.refused:
        get_metrics().record_persisted_state_refusal(
            LIBRARY_STORE_ID,
            _REFUSAL_METRIC_CODES[decision.code],
        )
        if decision.code == "persisted_state.schema_newer_than_app":
            # Path-free message: the store id and the two version numbers
            # are the whole diagnostic (the #224/#238 hygiene standard).
            raise PersistedStateVersionError(
                f"library record was written by a newer app "
                f"(found schema_version {decision.from_version}, "
                f"this build reads {decision.to_version}); "
                "leaving it untouched — update the app to read it",
                # ``store_id`` is what distinguishes this refusal from the
                # profile registry's — the taxonomy carries one shared
                # class and one shared fingerprint for the condition.
                context={"store_id": LIBRARY_STORE_ID, **decision.detail},
            )
        return None

    if decision.code == "persisted_state.migrated":
        get_metrics().record_persisted_state_migration(
            LIBRARY_STORE_ID,
            int(decision.from_version or 0),
            int(decision.to_version or 0),
        )

    payload = decision.payload
    if payload is None:  # pragma: no cover - accepted decisions always carry one
        return None
    try:
        record = LibraryRecord.from_dict(payload)
        if record.record_id != path.stem:
            raise ValueError("library record identity does not match filename")
        if record.rehearsal is not None:
            LibraryStore.verify_rehearsal(record.rehearsal)
        if record.source_frame is not None:
            _read_record_source_frame(path.parent, record)
        return record
    except (ValueError, TypeError, KeyError, OverflowError, DataError):
        get_metrics().record_persisted_state_refusal(LIBRARY_STORE_ID, "unknown_shape")
        return None


def _validate_record_source_frame(record: LibraryRecord, frame: bytes) -> None:
    artifact = record.source_frame
    if artifact is None:
        raise ValueError("library record is missing retained frame identity")
    if len(frame) != artifact.byte_count or sha256(frame).hexdigest() != artifact.sha256:
        raise ValueError("library retained frame hash or size mismatch")
    if artifact.artifact_name != f"{artifact.sha256}.syx":
        raise ValueError("library frame artifact is not content-addressed")
    captured_at = datetime.fromisoformat(record.captured_at)
    if captured_at.tzinfo is None or captured_at.utcoffset() is None:
        raise ValueError("library source timestamp must be timezone-aware")
    payload = frame[1:-1]
    if (
        payload.hex() != record.payload_hex
        or payload_fingerprint(payload) != record.fingerprint
        or record.record_id != record.fingerprint
    ):
        raise ValueError("library frame and payload identity mismatch")
    decoded = decode_kit_capture_frame(record.device_id, frame)
    if decoded.kit_name != record.kit_name:
        raise ValueError("library source metadata does not match registered codec")


def _read_record_source_frame(directory: Path, record: LibraryRecord) -> bytes:
    artifact = record.source_frame
    if artifact is None:
        raise ValueError("library record has no retained source frame")
    frame = read_bounded_artifact(
        directory / artifact.artifact_name, maximum=LIBRARY_MAX_SOURCE_FRAME_BYTES
    )
    _validate_record_source_frame(record, frame)
    return frame


def payload_fingerprint(payload: bytes) -> str:
    """Stable short digest for one SysEx payload.

    Same 16-hex-character sha256 convention the device snapshot decoders
    use (``rytm_snapshot_payload_fingerprint`` /
    ``analog_four_snapshot_payload_fingerprint``), applied to the raw
    payload so it is device-generic.
    """

    return sha256(payload).hexdigest()[:16]


def _is_clean_kit_name(kit_name: str) -> bool:
    """True for a non-empty, printable-ASCII operator-facing kit name."""

    return bool(kit_name) and all(32 <= ord(char) <= 126 for char in kit_name)


def _decode_with_any_device(payload: bytes) -> tuple[str, str] | None:
    """Decode ``payload`` through the devices registry (device-generic).

    Every registered device family gets a decode attempt; among the
    devices that accept the payload, the first one yielding a clean
    printable kit name wins (the Elektron envelope is shared across
    families, so a sibling decoder can technically "accept" another
    family's dump — the garbage name it produces is the tell). Falls
    back to the first accepting device, and returns ``None`` when no
    device family recognises the payload at all.
    """

    candidates: list[tuple[str, str]] = []
    for device_id, device in sorted(all_devices().items()):
        try:
            snapshot = device.decode_snapshot(bytes(payload), 0)
        except _DECODE_FAILURES:
            continue
        kit_name = str(getattr(snapshot, "kit_name", "")) or "unknown"
        candidates.append((device_id, kit_name))
    for device_id, kit_name in candidates:
        if _is_clean_kit_name(kit_name):
            return device_id, kit_name
    if candidates:
        return candidates[0]
    return None


def _capture_timestamp(path: Path) -> str:
    """ISO-8601 UTC timestamp from the capture file's mtime."""

    try:
        mtime = path.stat().st_mtime
    except OSError:
        return datetime.now(tz=timezone.utc).isoformat()
    return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
