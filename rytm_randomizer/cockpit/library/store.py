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
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Final

from ...devices import all_devices
from ...snapshot.sysex_file import extract_sysex_payloads
from ..export.writer import atomic_write
from ..profiles.paths import default_profiles_dir

__all__ = [
    "LibraryImportResult",
    "LibraryRecord",
    "LibraryStore",
    "default_captures_dir",
    "default_library_dir",
]

_LIBRARY_LEAF: Final[str] = "library"
_RECORD_SUFFIX: Final[str] = ".json"
_CAPTURES_LEAF: Final[str] = "captures"

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


def _validate_record_id(record_id: str) -> str:
    """Return ``record_id`` when it is filename-safe; raise otherwise."""

    if not isinstance(record_id, str) or _RECORD_ID_RE.match(record_id) is None:
        raise ValueError(f"invalid library record_id: {record_id!r}")
    return record_id


@dataclass(frozen=True)
class LibraryRecord:
    """One immutable library record (a captured kit/sound payload)."""

    record_id: str
    device_id: str
    kit_name: str
    fingerprint: str
    captured_at: str
    tags: tuple[str, ...]
    payload_hex: str

    def to_dict(self) -> dict:
        """JSON-safe dict form (the on-disk and on-wire shape)."""

        return {
            "record_id": self.record_id,
            "device_id": self.device_id,
            "kit_name": self.kit_name,
            "fingerprint": self.fingerprint,
            "captured_at": self.captured_at,
            "tags": list(self.tags),
            "payload_hex": self.payload_hex,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> LibraryRecord:
        """Rebuild a record from its dict form; raises ``ValueError`` on junk."""

        record_id = _validate_record_id(str(raw.get("record_id", "")))
        tags_raw = raw.get("tags", [])
        if not isinstance(tags_raw, (list, tuple)):
            raise ValueError(f"library record {record_id!r} has non-list tags")
        return cls(
            record_id=record_id,
            device_id=str(raw.get("device_id", "")),
            kit_name=str(raw.get("kit_name", "")),
            fingerprint=str(raw.get("fingerprint", "")),
            captured_at=str(raw.get("captured_at", "")),
            tags=tuple(str(tag) for tag in tags_raw),
            payload_hex=str(raw.get("payload_hex", "")),
        )

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

    def to_dict(self) -> dict:
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
        for path in sorted(self._library_dir.glob(f"*{_RECORD_SUFFIX}")):
            record = _safe_load_record(path)
            if record is not None:
                records.append(record)
        return tuple(sorted(records, key=lambda record: record.record_id))

    def get(self, record_id: str) -> LibraryRecord | None:
        """Return one record by id, or ``None`` when absent."""

        _validate_record_id(record_id)
        path = self._record_path(record_id)
        if not path.is_file():
            return None
        return _safe_load_record(path)

    def search(self, query: str) -> tuple[LibraryRecord, ...]:
        """Records whose searchable fields contain ``query`` (case-folded)."""

        return tuple(record for record in self.list_records() if record.matches(query))

    def tag(self, record_id: str, tags: Sequence[str]) -> LibraryRecord:
        """Replace a record's tags; returns the updated record.

        Raises ``ValueError`` for an unknown id or a non-string tag.
        """

        existing = self.get(record_id)
        if existing is None:
            raise ValueError(f"unknown library record_id: {record_id!r}")
        clean_tags = tuple(str(tag) for tag in tags)
        updated = LibraryRecord(
            record_id=existing.record_id,
            device_id=existing.device_id,
            kit_name=existing.kit_name,
            fingerprint=existing.fingerprint,
            captured_at=existing.captured_at,
            tags=clean_tags,
            payload_hex=existing.payload_hex,
        )
        self._write_record(updated, overwrite=True)
        return updated

    def delete(self, record_id: str) -> bool:
        """Delete one record; returns ``True`` when a file was removed."""

        _validate_record_id(record_id)
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
        for path in sorted(directory.glob("*.syx")):
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
            payloads = extract_sysex_payloads(path.read_bytes())
        except (OSError, ValueError):
            return LibraryImportResult(
                imported=(),
                skipped_existing=0,
                failed_files=(path.name,),
            )
        imported: list[LibraryRecord] = []
        skipped = 0
        decoded_any = False
        for payload in payloads:
            decoded = _decode_with_any_device(payload)
            if decoded is None:
                continue
            decoded_any = True
            device_id, kit_name = decoded
            record_id = payload_fingerprint(payload)
            if record_id in existing_ids:
                skipped += 1
                continue
            record = LibraryRecord(
                record_id=record_id,
                device_id=device_id,
                kit_name=kit_name,
                fingerprint=record_id,
                captured_at=_capture_timestamp(path),
                tags=(),
                payload_hex=payload.hex(),
            )
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

    def _write_record(self, record: LibraryRecord, *, overwrite: bool) -> None:
        """Persist one record atomically (sibling tempfile + rename)."""

        encoded = json.dumps(record.to_dict(), indent=2, sort_keys=True).encode("utf-8")
        atomic_write(self._record_path(record.record_id), encoded, overwrite=overwrite)


def _safe_load_record(path: Path) -> LibraryRecord | None:
    """Load one record file, or ``None`` when unreadable/malformed."""

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    try:
        return LibraryRecord.from_dict(raw)
    except ValueError:
        return None


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
