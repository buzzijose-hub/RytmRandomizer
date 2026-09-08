"""Revisioned, atomic local persistence for immutable show banks.

The store is deliberately flat: revision manifests and content-addressed
``.syx`` files share one configured directory.  That lets the existing
``atomic_write_set`` primitive publish a retained frame and its new manifest
as one transaction without pretending a nested directory tree is atomic.

Every mutation writes a new ``<bank>.rNNNNNNNN.show-bank.json`` revision.
Prior revisions and content-addressed captures are never overwritten.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final, Literal, NoReturn, cast

from ...guardrails.input_validation import canonical_json_bytes
from ...observability.errors import DataError
from ...observability.logging import get_logger
from ...observability.tracing import trace
from ...snapshot.sysex_file import extract_sysex_payloads
from ..data.show_bank import (
    SHOW_BANK_ID_MAX_LENGTH,
    SHOW_BANK_REVISION_MAX,
    RetainedSysexArtifact,
    ShowBank,
    ShowKitCapture,
    validate_show_bank_id,
)
from ..export.writer import WriteResult, atomic_write_set, guard_atomic_write_tree
from ..profiles.paths import default_profiles_dir
from .readiness import Clock, attach_retained_sysex, utc_now

SHOW_BANK_STORE_LEAF: Final[str] = "show-banks"
SHOW_BANK_MANIFEST_SUFFIX: Final[str] = ".show-bank.json"
SHOW_BANK_MANIFEST_MAX_BYTES: Final[int] = 2 * 1024 * 1024
SHOW_BANK_SYSEX_MAX_BYTES: Final[int] = 2 * 1024 * 1024
SHOW_BANK_MAX_DECLARED_SYSEX_BYTES: Final[int] = 64 * 1024 * 1024
SHOW_BANK_MAX_DIRECTORY_ENTRIES: Final[int] = 65_536
SHOW_BANK_MAX_BANKS: Final[int] = 256
SHOW_BANK_MAX_REVISIONS_PER_BANK: Final[int] = 4_096
SHOW_BANK_NAMESPACE_SUFFIX: Final[str] = ".show-bank.namespace"
SHOW_BANK_NAMESPACE_PAYLOAD: Final[bytes] = b"rytm-randomizer-show-bank-namespace-v1\n"
SHOW_BANK_LOCK_SUFFIX: Final[str] = ".show-bank.lock"
_SYSEX_START: Final[int] = 0xF0
_SYSEX_END: Final[int] = 0xF7

ShowBankCorruptionCategory = Literal[
    "missing",
    "malformed-json",
    "schema",
    "cross-reference",
    "size",
    "path",
    "hash",
    "framing",
    "access",
]
SHOW_BANK_CORRUPTION_CATEGORY_VALUES: Final[tuple[ShowBankCorruptionCategory, ...]] = (
    "missing",
    "malformed-json",
    "schema",
    "cross-reference",
    "size",
    "path",
    "hash",
    "framing",
    "access",
)

_MANIFEST_RE: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<bank_id>[a-z0-9][a-z0-9_-]{{0,{SHOW_BANK_ID_MAX_LENGTH - 1}}})\.r(?P<revision>[0-9]{{8}})\.show-bank\.json$"
)


@dataclass(frozen=True)
class ShowBankScanFailure:
    """One isolated bank that could not be loaded during a catalog scan."""

    bank_id: str
    category: ShowBankCorruptionCategory


_logger = get_logger(__name__)


def default_show_bank_dir() -> Path:
    """Return the show-bank sibling under the platform app-data root."""

    return default_profiles_dir().parent / SHOW_BANK_STORE_LEAF


def narrow_show_bank_corruption_category(value: str) -> ShowBankCorruptionCategory:
    """Narrow a diagnostic category read from structured error context."""

    if value in SHOW_BANK_CORRUPTION_CATEGORY_VALUES:
        return value
    raise ValueError(
        f"invalid show-bank corruption category {value!r}; "
        f"expected one of {SHOW_BANK_CORRUPTION_CATEGORY_VALUES}"
    )


def show_bank_corruption_category(error: DataError) -> ShowBankCorruptionCategory | None:
    """Return the typed category carried by a store/import error, if present."""

    value = error.context.get("category")
    if not isinstance(value, str) or value not in SHOW_BANK_CORRUPTION_CATEGORY_VALUES:
        return None
    return value


def _raise_show_bank_corruption(
    category: ShowBankCorruptionCategory,
    message: str,
    *,
    artifact_name: str | None = None,
) -> NoReturn:
    context: dict[str, object] = {"category": category}
    if artifact_name is not None:
        context["artifact_name"] = artifact_name
    raise DataError(message, context=context)


def _require_bytes(value: object, label: str) -> bytes:
    if not isinstance(value, bytes):
        raise TypeError(f"{label} must be bytes")
    return value


def canonical_show_bank_json(bank: ShowBank) -> bytes:
    """Serialize a bank to deterministic UTF-8 JSON with one trailing newline."""

    payload = canonical_json_bytes(cast(Mapping[str, object], bank.to_dict()))
    if len(payload) > SHOW_BANK_MANIFEST_MAX_BYTES:
        raise ValueError("show-bank manifest exceeds the supported size bound")
    declared_bytes = sum(item.frame_bytes for item in bank.sysex_artifacts())
    if declared_bytes > SHOW_BANK_MAX_DECLARED_SYSEX_BYTES:
        raise ValueError("show-bank declared SysEx exceeds the aggregate size bound")
    return payload


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def decode_json_rejecting_duplicate_keys(payload: bytes) -> object:
    """Decode UTF-8 JSON while rejecting every duplicate object key."""

    return json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=_unique_json_object,
    )


def _manifest_name(bank_id: str, revision: int) -> str:
    validate_show_bank_id(bank_id, "bank_id")
    if isinstance(revision, bool) or not 0 <= revision <= SHOW_BANK_REVISION_MAX:
        raise ValueError("revision must be in 0..99999999")
    return f"{bank_id}.r{revision:08d}{SHOW_BANK_MANIFEST_SUFFIX}"


def _namespace_name(bank_id: str) -> str:
    validate_show_bank_id(bank_id, "bank_id")
    return f"{bank_id}{SHOW_BANK_NAMESPACE_SUFFIX}"


def validate_show_bank_sysex_frame(frame: bytes) -> None:
    if not 1 <= len(frame) <= SHOW_BANK_SYSEX_MAX_BYTES:
        raise ValueError("SysEx frame size is outside the supported bound")
    if frame[0] != _SYSEX_START or frame[-1] != _SYSEX_END:
        raise ValueError("retained bytes are not complete framed SysEx")
    frames = extract_sysex_payloads(frame, keep_framing=True)
    if frames != (frame,):
        raise ValueError("retained bytes must contain exactly one isolated SysEx frame")


def _show_bank_directory_identity(path: Path) -> tuple[int, int]:
    metadata = path.stat(follow_symlinks=False)
    if not stat.S_ISDIR(metadata.st_mode):
        _raise_show_bank_corruption(
            "path", "show-bank store root is not a directory", artifact_name=path.name
        )
    return metadata.st_dev, metadata.st_ino


def read_bounded_show_bank_file(path: Path, *, maximum: int) -> bytes:
    try:
        before = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        _raise_show_bank_corruption(
            "missing", "show-bank artifact is missing", artifact_name=path.name
        )
    except OSError as exc:
        raise DataError(
            "show-bank artifact cannot be inspected",
            context={"category": "access", "artifact_name": path.name},
        ) from exc
    if not stat.S_ISREG(before.st_mode):
        _raise_show_bank_corruption(
            "path", "show-bank artifact is not a regular file", artifact_name=path.name
        )
    if before.st_size < 1 or before.st_size > maximum:
        _raise_show_bank_corruption(
            "size",
            "show-bank artifact size is outside the supported bound",
            artifact_name=path.name,
        )
    try:
        flags = (
            os.O_RDONLY
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_NOINHERIT", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
                before.st_dev,
                before.st_ino,
            ):
                _raise_show_bank_corruption(
                    "access", "show-bank artifact changed during open", artifact_name=path.name
                )
            payload = handle.read(maximum + 1)
        after = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise DataError(
            "show-bank artifact cannot be read",
            context={"category": "access", "artifact_name": path.name},
        ) from exc
    if len(payload) > maximum:
        _raise_show_bank_corruption(
            "size", "show-bank artifact exceeds the supported bound", artifact_name=path.name
        )
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if before_identity != after_identity:
        _raise_show_bank_corruption(
            "access", "show-bank artifact changed while it was read", artifact_name=path.name
        )
    return payload


def _capture_source_anchor(capture: ShowKitCapture) -> ShowKitCapture:
    """Return capture metadata with retention publication state removed."""

    return replace(capture, sysex=replace(capture.sysex, retained=None))


def _validate_source_anchor_lineage(previous: ShowBank, updated: ShowBank) -> None:
    if updated.revision <= previous.revision:
        raise ValueError("show-bank revision must move strictly forward")
    if updated.created_at != previous.created_at:
        raise ValueError("show-bank created_at is immutable across revisions")
    previous_entries = {entry.entry_id: entry for entry in previous.entries}
    for entry in updated.entries:
        prior = previous_entries.get(entry.entry_id)
        if prior is None:
            continue
        if _capture_source_anchor(entry.rytm_source) != _capture_source_anchor(
            prior.rytm_source
        ) or _capture_source_anchor(entry.analog_four_source) != _capture_source_anchor(
            prior.analog_four_source
        ):
            raise ValueError("show-bank source anchors are immutable across revisions")


def _decode_show_bank_manifest(payload: bytes, path: Path, bank_id: str, revision: int) -> ShowBank:
    """Validate one manifest envelope and its immutable filename identity."""

    try:
        decoded = decode_json_rejecting_duplicate_keys(payload)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise DataError(
            "show-bank manifest is not valid UTF-8 JSON",
            context={"category": "malformed-json", "artifact_name": path.name},
        ) from exc
    if not isinstance(decoded, Mapping):
        _raise_show_bank_corruption(
            "schema", "show-bank manifest root must be an object", artifact_name=path.name
        )
    try:
        bank = ShowBank.from_dict(cast(Mapping[str, object], decoded))
    except (KeyError, TypeError, ValueError) as exc:
        raise DataError(
            "show-bank manifest failed schema validation",
            context={"category": "schema", "artifact_name": path.name},
        ) from exc
    if bank.bank_id != bank_id or bank.revision != revision:
        _raise_show_bank_corruption(
            "cross-reference",
            "show-bank manifest identity does not match its filename",
            artifact_name=path.name,
        )
    if payload != canonical_show_bank_json(bank):
        _raise_show_bank_corruption(
            "schema",
            "show-bank manifest is not canonical JSON",
            artifact_name=path.name,
        )
    return bank


class ShowBankStore:
    """Injected revision store with explicit exact-SysEx retention."""

    def __init__(self, root: Path, *, clock: Clock = utc_now) -> None:
        self._root = Path(root).absolute()
        self._clock = clock
        self._scan_failures: tuple[ShowBankScanFailure, ...] = ()

    @property
    def root(self) -> Path:
        return self._root

    @property
    def scan_failures(self) -> tuple[ShowBankScanFailure, ...]:
        """Return categorical failures from the most recent bank scan."""

        return self._scan_failures

    def _prepare_root(self) -> tuple[int, int]:
        if self._root.exists() and self._root.is_symlink():
            _raise_show_bank_corruption(
                "path", "show-bank store root cannot be a symlink", artifact_name=self._root.name
            )
        try:
            self._root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DataError(
                "show-bank store root cannot be created",
                context={"category": "access", "artifact_name": self._root.name},
            ) from exc
        return _show_bank_directory_identity(self._root)

    def _manifest_path(self, bank_id: str, revision: int) -> Path:
        return self._root / _manifest_name(bank_id, revision)

    def _namespace_path(self, bank_id: str) -> Path:
        return self._root / _namespace_name(bank_id)

    @contextmanager
    def _exclusive_bank_lock(self, bank_id: str) -> Generator[None, None, None]:
        lock_path = self._root / f".{_namespace_name(bank_id)}{SHOW_BANK_LOCK_SUFFIX}"
        try:
            lock_path.mkdir()
        except FileExistsError as exc:
            raise FileExistsError(f"show-bank publication is already locked: {bank_id}") from exc
        try:
            yield
        finally:
            active_exception = sys.exception()
            try:
                lock_path.rmdir()
            except OSError as exc:
                if active_exception is not None:
                    active_exception.add_note(
                        f"Show-bank publication lock cleanup also failed: {lock_path.name}."
                    )
                else:
                    raise DataError(
                        "show-bank publication lock cannot be released",
                        context={"category": "access", "artifact_name": lock_path.name},
                    ) from exc

    def _root_paths(self) -> tuple[Path, ...]:
        if not self._root.exists():
            return ()
        if self._root.is_symlink():
            _raise_show_bank_corruption(
                "path", "show-bank store root cannot be a symlink", artifact_name=self._root.name
            )
        _show_bank_directory_identity(self._root)
        try:
            paths: list[Path] = []
            for path in self._root.iterdir():
                paths.append(path)
                if len(paths) > SHOW_BANK_MAX_DIRECTORY_ENTRIES:
                    _raise_show_bank_corruption(
                        "size",
                        "show-bank store contains too many directory entries",
                        artifact_name=self._root.name,
                    )
        except OSError as exc:
            raise DataError(
                "show-bank store root cannot be listed",
                context={"category": "access", "artifact_name": self._root.name},
            ) from exc
        return tuple(paths)

    def _namespace_exists(self, bank_id: str) -> bool:
        path = self._namespace_path(bank_id)
        if not os.path.lexists(path):
            return False
        try:
            metadata = path.stat(follow_symlinks=False)
        except OSError as exc:
            raise DataError(
                "show-bank namespace cannot be inspected",
                context={"category": "access", "artifact_name": path.name},
            ) from exc
        if not stat.S_ISREG(metadata.st_mode):
            _raise_show_bank_corruption(
                "path", "show-bank namespace is not a regular file", artifact_name=path.name
            )
        payload = read_bounded_show_bank_file(
            path,
            maximum=len(SHOW_BANK_NAMESPACE_PAYLOAD),
        )
        if payload != SHOW_BANK_NAMESPACE_PAYLOAD:
            _raise_show_bank_corruption(
                "schema", "show-bank namespace marker is invalid", artifact_name=path.name
            )
        return True

    @trace("show_bank.persist")
    def _publish(
        self,
        bank: ShowBank,
        extra_artifacts: Mapping[Path, bytes] | None = None,
        *,
        require_new_namespace: bool = False,
    ) -> tuple[WriteResult, ...]:
        manifest_payload = canonical_show_bank_json(bank)
        identity = self._prepare_root()
        with self._exclusive_bank_lock(bank.bank_id):
            manifest_path = self._manifest_path(bank.bank_id, bank.revision)
            if os.path.lexists(manifest_path):
                raise FileExistsError(f"show-bank revision already exists: {manifest_path.name}")
            namespace_exists = self._namespace_exists(bank.bank_id)
            latest = self.latest_revision(bank.bank_id)
            has_revisions = latest is not None
            if require_new_namespace and (namespace_exists or has_revisions):
                raise FileExistsError(f"show-bank namespace already exists: {bank.bank_id}")
            if namespace_exists and not has_revisions:
                # A valid marker without a manifest is a conservatively
                # reserved namespace left by an interrupted first publish.
                raise FileExistsError(f"show-bank namespace already exists: {bank.bank_id}")
            if latest is not None:
                previous = self.load(bank.bank_id, revision=latest, verify_retained=False)
                _validate_source_anchor_lineage(previous, bank)
            artifacts: dict[Path, object] = dict(extra_artifacts or {})
            if not namespace_exists:
                artifacts[self._namespace_path(bank.bank_id)] = SHOW_BANK_NAMESPACE_PAYLOAD
            artifacts[manifest_path] = manifest_payload
            paths = self._root_paths()
            manifests = tuple(
                match for path in paths if (match := _MANIFEST_RE.fullmatch(path.name)) is not None
            )
            bank_ids = {match.group("bank_id") for match in manifests}
            if len(bank_ids | {bank.bank_id}) > SHOW_BANK_MAX_BANKS:
                _raise_show_bank_corruption("size", "show-bank store cannot accept another bank")
            revision_count = sum(match.group("bank_id") == bank.bank_id for match in manifests)
            if revision_count >= SHOW_BANK_MAX_REVISIONS_PER_BANK:
                _raise_show_bank_corruption(
                    "size", "show-bank store cannot accept another revision"
                )
            new_names = {path.name for path in artifacts} - {path.name for path in paths}
            if len(paths) + len(new_names) > SHOW_BANK_MAX_DIRECTORY_ENTRIES:
                _raise_show_bank_corruption(
                    "size", "show-bank store cannot accept more directory entries"
                )
            with guard_atomic_write_tree(self._root, identity):
                writes = atomic_write_set(artifacts, overwrite=False)
        _logger.info(
            "show_bank_revision_persisted",
            extra={
                "bank_id": bank.bank_id,
                "revision": bank.revision,
                "artifact_count": len(writes),
                "outcome": "published",
            },
        )
        return writes

    def save(self, bank: ShowBank) -> WriteResult:
        """Persist one immutable revision; an existing revision is never replaced."""

        writes = self._publish(bank)
        return writes[-1]

    def _available_revisions(self, bank_id: str) -> tuple[int, ...]:
        validate_show_bank_id(bank_id, "bank_id")
        revisions: list[int] = []
        for path in self._root_paths():
            match = _MANIFEST_RE.fullmatch(path.name)
            if match is not None and match.group("bank_id") == bank_id:
                revisions.append(int(match.group("revision")))
                if len(revisions) > SHOW_BANK_MAX_REVISIONS_PER_BANK:
                    _raise_show_bank_corruption(
                        "size",
                        "show-bank revision history exceeds the supported bound",
                        artifact_name=bank_id,
                    )
        return tuple(sorted(revisions))

    def latest_revision(self, bank_id: str) -> int | None:
        """Return the latest stored revision number without loading its JSON."""

        revisions = self._available_revisions(bank_id)
        return None if not revisions else revisions[-1]

    def load(
        self,
        bank_id: str,
        *,
        revision: int | None = None,
        verify_retained: bool = True,
    ) -> ShowBank:
        """Load one revision and optionally verify every retained SysEx artifact."""

        validate_show_bank_id(bank_id, "bank_id")
        root_identity: tuple[int, int] | None = None
        if self._root.exists():
            if self._root.is_symlink():
                _raise_show_bank_corruption(
                    "path",
                    "show-bank store root cannot be a symlink",
                    artifact_name=self._root.name,
                )
            root_identity = _show_bank_directory_identity(self._root)
        selected_revision = revision
        if selected_revision is None:
            selected_revision = self.latest_revision(bank_id)
            if selected_revision is None:
                _raise_show_bank_corruption(
                    "missing", "show bank does not exist", artifact_name=bank_id
                )
        path = self._manifest_path(bank_id, selected_revision)
        payload = read_bounded_show_bank_file(path, maximum=SHOW_BANK_MANIFEST_MAX_BYTES)
        bank = _decode_show_bank_manifest(payload, path, bank_id, selected_revision)
        if verify_retained:
            for sysex in bank.sysex_artifacts():
                if sysex.retained is not None:
                    self.read_retained(sysex.retained)
        if root_identity is not None and _show_bank_directory_identity(self._root) != root_identity:
            _raise_show_bank_corruption(
                "access",
                "show-bank store changed while its manifest was read",
                artifact_name=path.name,
            )
        return bank

    def list_banks(self, *, verify_retained: bool = True) -> tuple[ShowBank, ...]:
        """Load the latest revision of each bank in stable id order."""

        paths = self._root_paths()
        bank_ids = sorted(
            {
                match.group("bank_id")
                for path in paths
                if (match := _MANIFEST_RE.fullmatch(path.name)) is not None
            }
        )
        if len(bank_ids) > SHOW_BANK_MAX_BANKS:
            _raise_show_bank_corruption(
                "size",
                "show-bank store contains too many banks",
                artifact_name=self._root.name,
            )
        loaded: list[ShowBank] = []
        failures: list[ShowBankScanFailure] = []
        for bank_id in bank_ids:
            try:
                loaded.append(self.load(bank_id, verify_retained=verify_retained))
            except DataError as exc:
                category: ShowBankCorruptionCategory = (
                    show_bank_corruption_category(exc) or "access"
                )
                failures.append(ShowBankScanFailure(bank_id=bank_id, category=category))
                _logger.warning(
                    "show_bank_scan_isolated_corruption",
                    extra={"bank_id": bank_id, "category": category},
                )
        self._scan_failures = tuple(failures)
        return tuple(loaded)

    def read_retained(self, artifact: RetainedSysexArtifact) -> bytes:
        """Read and re-verify one content-addressed retained frame."""

        if not self._root.exists() or self._root.is_symlink():
            _raise_show_bank_corruption(
                "path", "show-bank store root is unavailable", artifact_name=self._root.name
            )
        identity = _show_bank_directory_identity(self._root)
        path = self._root / artifact.artifact_name
        frame = read_bounded_show_bank_file(path, maximum=SHOW_BANK_SYSEX_MAX_BYTES)
        if _show_bank_directory_identity(self._root) != identity:
            _raise_show_bank_corruption(
                "access", "show-bank store changed while it was read", artifact_name=path.name
            )
        if len(frame) != artifact.byte_count:
            _raise_show_bank_corruption(
                "size", "retained SysEx size does not match its manifest", artifact_name=path.name
            )
        digest = hashlib.sha256(frame).hexdigest()
        if digest != artifact.sha256:
            _raise_show_bank_corruption(
                "hash", "retained SysEx hash does not match its manifest", artifact_name=path.name
            )
        try:
            validate_show_bank_sysex_frame(frame)
        except ValueError as exc:
            raise DataError(
                "retained SysEx framing is invalid",
                context={"category": "framing", "artifact_name": path.name},
            ) from exc
        return frame

    def retain_sysex(
        self,
        bank: ShowBank,
        artifact_id: str,
        frame: bytes,
    ) -> ShowBank:
        """Retain one exact frame through the atomic bulk-retention contract."""

        return self.retain_sysex_set(bank, {artifact_id: frame})

    def _validate_retention_frames(
        self, bank: ShowBank, frames_by_artifact_id: Mapping[str, bytes]
    ) -> dict[str, tuple[bytes, RetainedSysexArtifact]]:
        """Bind a bounded retention request to declared and existing exact bytes."""

        if not frames_by_artifact_id:
            raise ValueError("retained SysEx set cannot be empty")
        input_frames = {
            artifact_id: _require_bytes(frame, "retained SysEx frame")
            for artifact_id, frame in frames_by_artifact_id.items()
        }
        if sum(len(frame) for frame in input_frames.values()) > (
            SHOW_BANK_MAX_DECLARED_SYSEX_BYTES
        ):
            raise ValueError("retained SysEx set exceeds the aggregate size bound")

        validated: dict[str, tuple[bytes, RetainedSysexArtifact]] = {}
        for artifact_id in sorted(input_frames):
            frame = input_frames[artifact_id]
            declared = bank.sysex_artifact(artifact_id)
            validate_show_bank_sysex_frame(frame)
            if declared.retained is not None:
                existing = self.read_retained(declared.retained)
                if existing != frame:
                    raise ValueError("artifact is already retained with different exact bytes")
            digest = hashlib.sha256(frame).hexdigest()
            if digest != declared.frame_sha256 or len(frame) != declared.frame_bytes:
                raise ValueError("retained frame does not match the declared hash and byte count")
            retained = RetainedSysexArtifact(
                artifact_name=f"{digest}.syx",
                sha256=digest,
                byte_count=len(frame),
            )
            validated[artifact_id] = (frame, retained)
        return validated

    def retain_sysex_set(
        self,
        bank: ShowBank,
        frames_by_artifact_id: Mapping[str, bytes],
    ) -> ShowBank:
        """Retain a bounded frame set and publish exactly one new manifest.

        All identities and existing content-addressed files are verified before
        the write set is staged.  Repeated retention of an already-persisted
        revision is a no-op; an otherwise-unsaved transition is still
        published even when every frame was retained by an earlier revision.
        """

        validated = self._validate_retention_frames(bank, frames_by_artifact_id)

        updated = bank
        attached = False
        for artifact_id, (_frame, retained) in validated.items():
            if updated.sysex_artifact(artifact_id).retained is not None:
                continue
            updated = attach_retained_sysex(
                updated,
                artifact_id,
                retained,
                clock=self._clock,
            )
            attached = True

        latest = self.latest_revision(updated.bank_id)
        if not attached and latest == updated.revision:
            return bank

        self._prepare_root()
        artifacts: dict[Path, bytes] = {}
        for frame, retained in validated.values():
            capture_path = self._root / retained.artifact_name
            if os.path.lexists(capture_path):
                on_disk = self.read_retained(retained)
                if on_disk != frame:
                    _raise_show_bank_corruption(
                        "hash",
                        "content-addressed capture collision",
                        artifact_name=capture_path.name,
                    )
            else:
                previous = artifacts.setdefault(capture_path, frame)
                if previous != frame:
                    _raise_show_bank_corruption(
                        "hash",
                        "content-addressed capture collision",
                        artifact_name=capture_path.name,
                    )
        self._publish(updated, artifacts)
        return updated

    def import_verified(
        self,
        bank: ShowBank,
        frames_by_artifact_id: Mapping[str, bytes],
    ) -> tuple[WriteResult, ...]:
        """Atomically import a pre-verified manifest and all retained frames."""

        canonical_show_bank_json(bank)
        retained = {
            sysex.artifact_id: sysex
            for sysex in bank.sysex_artifacts()
            if sysex.retained is not None
        }
        supplied_ids = frozenset(frames_by_artifact_id)
        if supplied_ids != frozenset(retained):
            raise ValueError("imported frames must exactly match retained artifact ids")
        self._prepare_root()
        if self.latest_revision(bank.bank_id) is not None or self._namespace_exists(bank.bank_id):
            raise FileExistsError(f"show-bank namespace already exists: {bank.bank_id}")
        artifacts: dict[Path, bytes] = {}
        for artifact_id in sorted(retained):
            sysex = retained[artifact_id]
            frame = _require_bytes(
                frames_by_artifact_id[artifact_id],
                "imported SysEx frame",
            )
            validate_show_bank_sysex_frame(frame)
            if (
                hashlib.sha256(frame).hexdigest() != sysex.frame_sha256
                or len(frame) != sysex.frame_bytes
            ):
                raise ValueError("imported frame does not match its declared identity")
            retained_record = cast(RetainedSysexArtifact, sysex.retained)
            destination = self._root / retained_record.artifact_name
            if os.path.lexists(destination):
                if self.read_retained(retained_record) != frame:
                    _raise_show_bank_corruption(
                        "hash",
                        "content-addressed capture collision",
                        artifact_name=destination.name,
                    )
            else:
                artifacts[destination] = frame
        return self._publish(bank, artifacts, require_new_namespace=True)


__all__ = [
    "SHOW_BANK_CORRUPTION_CATEGORY_VALUES",
    "SHOW_BANK_LOCK_SUFFIX",
    "SHOW_BANK_MAX_BANKS",
    "SHOW_BANK_MAX_DECLARED_SYSEX_BYTES",
    "SHOW_BANK_MAX_DIRECTORY_ENTRIES",
    "SHOW_BANK_MAX_REVISIONS_PER_BANK",
    "SHOW_BANK_MANIFEST_MAX_BYTES",
    "SHOW_BANK_MANIFEST_SUFFIX",
    "SHOW_BANK_NAMESPACE_SUFFIX",
    "SHOW_BANK_STORE_LEAF",
    "SHOW_BANK_SYSEX_MAX_BYTES",
    "ShowBankCorruptionCategory",
    "ShowBankScanFailure",
    "ShowBankStore",
    "canonical_show_bank_json",
    "decode_json_rejecting_duplicate_keys",
    "default_show_bank_dir",
    "narrow_show_bank_corruption_category",
    "read_bounded_show_bank_file",
    "show_bank_corruption_category",
    "validate_show_bank_sysex_frame",
]
