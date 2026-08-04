"""Atomic file writer for cockpit ``ProfileModel`` exports (WS-B, Phase 3).

This module sits one layer above :mod:`.signing` and :mod:`.serialize` and is
the single point of truth for *how* a finished export blob reaches disk. The
three guarantees the writer must satisfy:

1. **Never leave a half-written file on error.** If the bytes write, fsync,
   or atomic publication fails for any reason, callers must observe the
   destination path in its prior state (either absent or with the prior
   bytes intact).
2. **Never publish unflushed file data.** The bytes are flushed with
   :func:`os.fsync` before atomic publication. Directory metadata is not
   fsynced, so persistence of a newly published name across sudden power
   loss remains filesystem-dependent.
3. **Fail closed on every supported platform.** Overwriting uses
   :func:`os.replace`. No-overwrite publication uses :func:`os.link` so
   destination creation stays race-safe. Filesystems without hard-link
   support return a write failure rather than weakening the guarantee.

Public surface:

* :func:`atomic_write` — write ``bytes`` to ``path`` atomically.
* :func:`atomic_write_set` — publish a same-directory set transactionally.
* :func:`write_signed_export` — convenience wrapper that derives the
  canonical export filename from ``(profile_id, model_version)``.
* :func:`default_export_dir` — platform-default location exports land in.
* :class:`WriteResult` — frozen dataclass returned by both writers.
* :class:`WriteError` — raised on any non-validation write failure.
* :data:`DEFAULT_EXPORT_SUBDIR` — the trailing ``"exports"`` directory
  name appended to the per-platform base directory.

Stdlib-only: ``os`` / ``tempfile`` / ``pathlib`` / ``sys`` /
``dataclasses`` / ``typing``. No third-party dependencies.
"""

from __future__ import annotations

import os
import shutil
import stat
import sys
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Final, Literal, TypeAlias

from ...observability.errors import DataError
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from .file_export_contracts import safe_local_file_export_artifact_name

_logger = get_logger(__name__)
"""Module logger for the atomic export writer. Bound here so future
structured log calls (durability breadcrumbs around fsync / atomic
replace, disk-full / permission-denied diagnostics) can land in the
package's structured stream without touching this file's imports.
See ``OBSERVABILITY_REVIEW.md`` Phase 5."""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_EXPORT_SUBDIR: Final[str] = "exports"
"""Trailing directory name appended to the per-platform base directory."""

_APP_DIR_NAME: Final[str] = "rytm-randomizer"
"""Application directory name nested under the per-platform base dir."""

_TEMP_FILE_SUFFIX: Final[str] = ".tmp"
"""Suffix the sibling temp file is created with so leaked artifacts are
visually obvious to a human inspecting the directory."""

_WRITE_SET_DIR_PREFIX: Final[str] = ".write-set-"
"""Prefix for retained transaction directories after incomplete rollback."""

_WRITE_SET_CONTEXT_LIMIT: Final[int] = 120
"""Maximum artifact-name length exposed in bounded failure diagnostics."""


# ---------------------------------------------------------------------------
# Result + error types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WriteResult:
    """The structured outcome of a successful atomic write.

    Attributes:
        path: The resolved absolute path of the written file.
        bytes_written: The length of the ``data`` written (matches
            ``len(data)``).
        overwrote_existing: ``True`` only when the destination already
            existed at write time and was replaced atomically.
    """

    path: Path
    bytes_written: int
    overwrote_existing: bool


class WriteError(DataError, OSError):
    """Atomic write failed for a non-user-input reason.

    Examples include disk full, permission denied, and underlying
    filesystem errors during write / fsync / replace.

    Multi-inheritance under :class:`DataError` + :class:`OSError` so:

    * ``except OSError:`` callers continue to work without import
      changes (idiomatic Python file-error handling);
    * the observability conformance test
      (``tests/architecture/test_observability.py``) recognises the
      raise as a taxonomy member.

    Mirrors the multi-inheritance pattern used by :mod:`.signing` for
    its own ``DataError``-tagged failures (the primary consumer of this
    writer).
    """

    fingerprint: ClassVar[str] = "export.write.failed"


WriteSetPhase: TypeAlias = Literal["staging", "backup", "publication"]
"""Transaction phase in which a write-set failure originated."""


@dataclass(frozen=True)
class WriteSetRollbackFailure:
    """One bounded rollback failure retained for operator diagnostics."""

    artifact_name: str
    operation: Literal["remove_new_file", "restore_backup"]
    error_type: str


@dataclass(frozen=True)
class WriteSetFailureContext:
    """Path-safe context attached to :class:`WriteSetError`."""

    phase: WriteSetPhase
    artifact_name: str
    rollback_failures: tuple[WriteSetRollbackFailure, ...] = ()
    recovery_directory_name: str | None = None


class WriteSetError(WriteError):
    """A transactional artifact-set publication failed.

    The exception message and :attr:`failure_context` intentionally expose only
    bounded basenames. The parent directory remains private to the caller.
    """

    fingerprint: ClassVar[str] = "export.write_set.failed"

    def __init__(self, failure_context: WriteSetFailureContext) -> None:
        self.failure_context = failure_context
        super().__init__(
            "atomic write set failed during "
            f"{failure_context.phase} for {failure_context.artifact_name}"
        )
        if failure_context.rollback_failures:
            self.add_note(
                "Rollback was incomplete; recovery data remains in the bounded "
                "transaction directory named by error.failure_context."
            )


# ---------------------------------------------------------------------------
# Default export directory
# ---------------------------------------------------------------------------


def default_export_dir() -> Path:
    """Return the platform-default directory cockpit exports land in.

    Resolution order (no I/O performed):

    * **Windows** (``sys.platform == "win32"``):
      ``$APPDATA/rytm-randomizer/exports`` if ``APPDATA`` is set,
      else ``~/rytm-randomizer/exports``.
    * **Linux / other POSIX:** ``$XDG_CONFIG_HOME/rytm-randomizer/exports``
      if ``XDG_CONFIG_HOME`` is set to a non-empty value, else
      ``~/.config/rytm-randomizer/exports``.

    The returned path is **not** created on disk; :func:`atomic_write`
    creates the parents lazily on first write.
    """

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home()
        return base / _APP_DIR_NAME / DEFAULT_EXPORT_SUBDIR

    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / _APP_DIR_NAME / DEFAULT_EXPORT_SUBDIR


# ---------------------------------------------------------------------------
# Atomic write
# ---------------------------------------------------------------------------


def atomic_write(path: Path, data: bytes, *, overwrite: bool = False) -> WriteResult:
    """Atomically write ``data`` to ``path``.

    Sequence:

    1. Ensure parent directories exist
       (:meth:`Path.mkdir(parents=True, exist_ok=True)`).
    2. If ``overwrite`` is :data:`False` and the destination already
       exists, raise :class:`FileExistsError` *before* writing the temp
       file (we know we'd fail at the rename step anyway).
    3. Create a sibling temp file in the destination directory with
       :func:`tempfile.mkstemp`.
       The temp file must live in the same directory as the destination
       so :func:`os.replace` stays atomic — atomic rename only holds
       within a single filesystem.
    4. Write ``data`` to the temp file, :func:`os.fsync` the descriptor
       *before* close (durability — survives a crash between write and
       rename), then close.
    5. Publish the temp atomically. With ``overwrite=True``, use
       :func:`os.replace`. Otherwise, use :func:`os.link`, which fails if
       another process created the destination after the initial existence
       check.
    6. On any exception during steps 3-5, the temp file is best-effort
       unlinked (cleanup failures are swallowed silently — losing a
       single orphan ``.tmp`` is dramatically better than masking the
       original write error) and the original :class:`OSError` is
       re-raised wrapped in :class:`WriteError`.

    Args:
        path: The destination path. Parent directories are created on
            demand. The path is resolved to an absolute path in the
            returned :class:`WriteResult`.
        data: The exact bytes to land on disk. Empty input is permitted.
        overwrite: When :data:`False` (the default), an existing
            destination is rejected with :class:`FileExistsError`. When
            :data:`True`, an existing destination is atomically replaced
            and :attr:`WriteResult.overwrote_existing` is :data:`True`.

    Returns:
        A :class:`WriteResult` with the resolved absolute path, the byte
        count, and whether an existing file was replaced.

    Raises:
        FileExistsError: ``overwrite`` is :data:`False` and the
            destination exists either before writing starts or when the
            completed temp file is published.
        WriteError: Any underlying :class:`OSError` from write / fsync /
            replace. The temp file is best-effort cleaned up. The
            original :class:`OSError` is attached via ``__cause__``.
    """

    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)

    overwrote_existing = path.exists()
    if overwrote_existing and not overwrite:
        raise FileExistsError(
            f"refusing to overwrite existing file: {path} (pass overwrite=True to allow)"
        )

    # Create the sibling temp file. delete=False keeps it on disk after
    # close() so os.replace can rename it atomically onto the destination.
    tmp_fd, tmp_name = tempfile.mkstemp(
        suffix=_TEMP_FILE_SUFFIX,
        prefix=path.name + ".",
        dir=str(parent),
    )
    try:
        try:
            try:
                remaining = memoryview(data)
                while remaining:
                    bytes_written = os.write(tmp_fd, remaining)
                    if bytes_written <= 0:
                        raise WriteError("write made no progress")
                    remaining = remaining[bytes_written:]
                os.fsync(tmp_fd)
            finally:
                os.close(tmp_fd)
        except WriteError:
            raise
        except OSError as exc:
            raise WriteError(f"atomic_write failed for {path}: {exc}") from exc

        _publish_temp_file(tmp_name, path, overwrite=overwrite)
    finally:
        # Also runs for KeyboardInterrupt/SystemExit without broadly catching
        # them. Cleanup must never mask the active publication outcome.
        active_exception = sys.exception()
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        except OSError as exc:
            _record_temp_cleanup_failure(
                tmp_name,
                path,
                exc,
                active_exception=active_exception,
            )

    return WriteResult(
        path=path.resolve(),
        bytes_written=len(data),
        overwrote_existing=overwrote_existing,
    )


def _publish_temp_file(tmp_name: str, path: Path, *, overwrite: bool) -> None:
    """Publish a completed temp file with collision-specific error handling."""

    if overwrite:
        try:
            os.replace(tmp_name, str(path))
        except OSError as exc:
            raise WriteError(f"atomic_write failed for {path}: {exc}") from exc
        return
    try:
        _publish_no_overwrite(tmp_name, path)
    except FileExistsError:
        raise
    except OSError as exc:
        raise WriteError(f"atomic_write failed for {path}: {exc}") from exc


def _publish_no_overwrite(
    tmp_name: str,
    path: Path,
    *,
    on_published: Callable[[], None] | None = None,
) -> None:
    """Publish ``tmp_name`` without replacing a concurrent destination."""

    os.link(tmp_name, path)
    if on_published is not None:
        on_published()


def _record_temp_cleanup_failure(
    tmp_name: str,
    path: Path,
    exc: OSError,
    *,
    active_exception: BaseException | None,
) -> None:
    """Record retained temp-file residue without masking the active outcome."""

    metrics = get_metrics()
    metrics.record_error("atomic_write_temp_cleanup")
    _logger.warning(
        "Atomic write temp cleanup failed",
        extra={
            "operation": "atomic_write_cleanup",
            "outcome": "residue_retained",
            "error_code": "temp_cleanup_failed",
            "fingerprint": "export.write.temp_cleanup_failed",
            "temp_name": Path(tmp_name).name,
            "output_name": path.name,
            "error_type": type(exc).__name__,
            "metrics_summary": metrics.format_summary(),
        },
    )
    if active_exception is not None:
        active_exception.add_note(
            "Atomic-write temp cleanup also failed; a sibling .tmp file may remain."
        )


# ---------------------------------------------------------------------------
# Transactional artifact-set publication
# ---------------------------------------------------------------------------


def atomic_write_set(
    artifacts: Mapping[Path, object],
    *,
    overwrite: bool = False,
) -> tuple[WriteResult, ...]:
    """Publish a same-directory set of byte artifacts transactionally.

    Every payload is first staged with :func:`atomic_write` inside a sibling
    transaction directory. Existing destinations are then moved into that
    directory before the staged files are published. If staging, backup, or
    publication fails, prior files are restored and newly published files are
    removed. A rollback failure never replaces the original exception; the
    transaction directory is retained when it still contains recovery data.

    Failure diagnostics expose the actual destination basename and phase via
    :class:`WriteSetFailureContext`. Parent paths and raw filesystem messages
    are intentionally excluded from the public exception text.

    Args:
        artifacts: Ordered mapping of destination paths to exact byte payloads.
            All destinations must share one parent directory.
        overwrite: Permit replacement of existing destinations when true.

    Returns:
        One :class:`WriteResult` per mapping entry, in insertion order.

    Raises:
        ValueError: The mapping is empty, contains duplicate destinations, or
            spans multiple parent directories.
        TypeError: A payload is not :class:`bytes`.
        FileExistsError: A destination exists while ``overwrite`` is false.
        WriteSetError: Staging, backup, or publication failed.
    """

    if not artifacts:
        raise ValueError("atomic_write_set requires at least one artifact")

    raw_items: tuple[tuple[Path, object], ...] = tuple(
        (Path(path).absolute(), payload) for path, payload in artifacts.items()
    )
    typed_items: list[tuple[Path, bytes]] = []
    for path, payload in raw_items:
        if not isinstance(payload, bytes):
            raise TypeError("atomic_write_set payloads must be bytes")
        typed_items.append((path, payload))
    items = tuple(typed_items)
    destinations = tuple(path for path, _payload in items)
    if any(not path.name for path in destinations):
        raise ValueError("atomic_write_set destinations must name files")
    if len(set(destinations)) != len(destinations):
        raise ValueError("atomic_write_set destinations must be unique")
    if len({path.parent for path in destinations}) != 1:
        raise ValueError("atomic_write_set destinations must share one parent")
    parent = destinations[0].parent
    first_destination = destinations[0]
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise WriteSetError(
            WriteSetFailureContext(
                phase="staging",
                artifact_name=_bounded_artifact_name(first_destination),
            )
        ) from exc

    existed = {path: os.path.lexists(path) for path in destinations}
    if overwrite:
        for path in destinations:
            if existed[path]:
                _require_regular_overwrite_destination(path)
    if not overwrite:
        for path in destinations:
            if existed[path]:
                raise FileExistsError(
                    "refusing to overwrite existing artifact: " f"{_bounded_artifact_name(path)}"
                )

    try:
        transaction_dir = Path(tempfile.mkdtemp(prefix=_WRITE_SET_DIR_PREFIX, dir=str(parent)))
    except OSError as exc:
        raise WriteSetError(
            WriteSetFailureContext(
                phase="staging",
                artifact_name=_bounded_artifact_name(first_destination),
            )
        ) from exc

    staged: dict[Path, Path] = {}
    backups: dict[Path, Path] = {}
    published: set[Path] = set()
    phase: WriteSetPhase = "staging"
    active_destination = first_destination

    try:
        for index, (destination, payload) in enumerate(items):
            active_destination = destination
            stage_path = transaction_dir / f"{index:04d}.stage"
            atomic_write(stage_path, payload)
            staged[destination] = stage_path

        phase = "backup"
        for index, destination in enumerate(destinations):
            active_destination = destination
            if existed[destination]:
                _require_regular_overwrite_destination(destination)
                backup_path = transaction_dir / f"{index:04d}.backup"
                backups[destination] = backup_path
                os.replace(destination, backup_path)

        phase = "publication"
        for destination in destinations:
            active_destination = destination
            if overwrite:
                os.replace(staged[destination], destination)
                published.add(destination)
            else:
                _publish_no_overwrite(
                    str(staged[destination]),
                    destination,
                    on_published=lambda destination=destination: published.add(destination),
                )
    except (OSError, KeyboardInterrupt, SystemExit) as exc:
        rollback_failures = _rollback_write_set(
            items,
            backups=backups,
            published=published,
            staged=staged,
        )
        recovery_name = transaction_dir.name if rollback_failures else None
        if rollback_failures:
            _record_write_set_rollback_failures(
                transaction_dir,
                rollback_failures,
                active_exception=exc,
            )
        else:
            _cleanup_write_set_directory(transaction_dir, active_exception=exc)

        context = WriteSetFailureContext(
            phase=phase,
            artifact_name=_bounded_artifact_name(active_destination),
            rollback_failures=rollback_failures,
            recovery_directory_name=recovery_name,
        )
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            exc.add_note(
                "Atomic write-set failure context: " f"{context.phase} for {context.artifact_name}."
            )
            raise
        if isinstance(exc, FileExistsError) and not overwrite and not rollback_failures:
            raise FileExistsError(
                f"refusing to overwrite existing artifact: {context.artifact_name}"
            ) from exc
        raise WriteSetError(context) from exc

    results = tuple(
        WriteResult(
            path=destination.resolve(),
            bytes_written=len(payload),
            overwrote_existing=existed[destination],
        )
        for destination, payload in items
    )
    _cleanup_write_set_directory(transaction_dir, active_exception=None)
    return results


def _rollback_write_set(
    items: tuple[tuple[Path, bytes], ...],
    *,
    backups: Mapping[Path, Path],
    published: set[Path],
    staged: Mapping[Path, Path],
) -> tuple[WriteSetRollbackFailure, ...]:
    """Best-effort rollback that retains every failed backup operation."""

    failures: list[WriteSetRollbackFailure] = []
    for destination, _payload in reversed(items):
        backup_path = backups.get(destination)
        if backup_path is not None and backup_path.exists():
            try:
                os.replace(backup_path, destination)
            except OSError as exc:  # rollback must not mask the first failure
                failures.append(
                    WriteSetRollbackFailure(
                        artifact_name=_bounded_artifact_name(destination),
                        operation="restore_backup",
                        error_type=type(exc).__name__,
                    )
                )
            continue
        if not _stage_reached_destination(
            destination,
            staged.get(destination),
            published=published,
        ):
            continue
        try:
            os.unlink(destination)
        except OSError as exc:  # rollback must not mask the first failure
            failures.append(
                WriteSetRollbackFailure(
                    artifact_name=_bounded_artifact_name(destination),
                    operation="remove_new_file",
                    error_type=type(exc).__name__,
                )
            )
    return tuple(failures)


def _require_regular_overwrite_destination(path: Path) -> None:
    """Reject directories, symlinks, and other non-regular artifacts."""

    try:
        mode = os.lstat(path).st_mode
    except FileNotFoundError:
        return
    if not stat.S_ISREG(mode):
        raise WriteSetError(
            WriteSetFailureContext(
                phase="backup",
                artifact_name=_bounded_artifact_name(path),
            )
        )


def _stage_reached_destination(
    destination: Path,
    stage_path: Path | None,
    *,
    published: set[Path],
) -> bool:
    """Infer publication when interruption precedes bookkeeping."""

    if destination in published:
        return True
    if stage_path is None or not destination.exists():
        return False
    if not stage_path.exists():
        return True
    try:
        return os.path.samefile(stage_path, destination)
    except OSError:
        return False


def _bounded_artifact_name(path: Path) -> str:
    """Return a deterministic basename without exposing its parent path."""

    return safe_local_file_export_artifact_name(
        path,
        fallback="unnamed-artifact",
        max_length=_WRITE_SET_CONTEXT_LIMIT,
    )


def _cleanup_write_set_directory(
    transaction_dir: Path,
    *,
    active_exception: BaseException | None,
) -> None:
    """Remove transaction residue without changing an active outcome."""

    try:
        shutil.rmtree(transaction_dir)
    except FileNotFoundError:
        pass
    except OSError as exc:
        metrics = get_metrics()
        metrics.record_error("atomic_write_set_cleanup")
        _logger.warning(
            "Atomic write-set cleanup failed",
            extra={
                "operation": "atomic_write_set_cleanup",
                "outcome": "residue_retained",
                "error_code": "transaction_cleanup_failed",
                "fingerprint": "export.write_set.cleanup_failed",
                "transaction_name": transaction_dir.name,
                "error_type": type(exc).__name__,
                "metrics_summary": metrics.format_summary(),
            },
        )
        if active_exception is not None:
            active_exception.add_note(
                "Atomic write-set cleanup also failed; transaction residue may remain."
            )


def _record_write_set_rollback_failures(
    transaction_dir: Path,
    failures: tuple[WriteSetRollbackFailure, ...],
    *,
    active_exception: BaseException,
) -> None:
    """Record incomplete rollback while preserving the original exception."""

    metrics = get_metrics()
    metrics.record_error("atomic_write_set_rollback")
    _logger.error(
        "Atomic write-set rollback incomplete",
        extra={
            "operation": "atomic_write_set_rollback",
            "outcome": "recovery_data_retained",
            "error_code": "rollback_incomplete",
            "fingerprint": "export.write_set.rollback_incomplete",
            "transaction_name": transaction_dir.name,
            "artifacts": tuple(failure.artifact_name for failure in failures),
            "operations": tuple(failure.operation for failure in failures),
            "error_types": tuple(failure.error_type for failure in failures),
            "metrics_summary": metrics.format_summary(),
        },
    )
    active_exception.add_note(
        "Atomic write-set rollback was incomplete; recovery data was retained."
    )


# ---------------------------------------------------------------------------
# Canonical signed-export wrapper
# ---------------------------------------------------------------------------


def write_signed_export(
    signed_envelope: bytes,
    *,
    profile_id: str,
    model_version: str,
    export_dir: Path | None = None,
    filename_override: str | None = None,
    overwrite: bool = False,
) -> WriteResult:
    """Write a signed cockpit-profile envelope to the canonical export path.

    Filename convention: ``f"{profile_id}-v{model_version}.rymp"`` unless
    ``filename_override`` is supplied (in which case it is used verbatim).

    Args:
        signed_envelope: The already-packed signed envelope bytes — the
            output of :func:`rytm_randomizer.cockpit.export.pack_signed`.
        profile_id: The profile id segment of the canonical filename.
        model_version: The model-version segment of the canonical filename.
        export_dir: Override the destination directory. ``None`` (default)
            uses :func:`default_export_dir`.
        filename_override: Override the canonical filename entirely. Use
            with caution — the rest of the pipeline (loader, registry)
            expects the canonical pattern.
        overwrite: Passed through to :func:`atomic_write`.

    Returns:
        The :class:`WriteResult` from the underlying :func:`atomic_write`.
    """

    target_dir = export_dir if export_dir is not None else default_export_dir()
    filename = (
        filename_override
        if filename_override is not None
        else f"{profile_id}-v{model_version}.rymp"
    )
    return atomic_write(target_dir / filename, signed_envelope, overwrite=overwrite)


__all__ = [
    "DEFAULT_EXPORT_SUBDIR",
    "WriteError",
    "WriteResult",
    "WriteSetError",
    "WriteSetFailureContext",
    "WriteSetRollbackFailure",
    "atomic_write",
    "atomic_write_set",
    "default_export_dir",
    "write_signed_export",
]
