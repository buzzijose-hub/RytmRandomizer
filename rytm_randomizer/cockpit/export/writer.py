"""Atomic file writer for cockpit ``ProfileModel`` exports (WS-B, Phase 3).

This module sits one layer above :mod:`.signing` and :mod:`.serialize` and is
the single point of truth for *how* a finished export blob reaches disk. The
three guarantees the writer must satisfy:

1. **Never leave a half-written file on error.** If the bytes write, fsync,
   or :func:`os.replace` fails for any reason, callers must observe the
   destination path in its prior state (either absent or with the prior
   bytes intact).
2. **Survive a crash mid-write.** The bytes are durably flushed to the OS
   (:func:`os.fsync`) *before* the atomic rename, so a power loss between
   write and rename leaves only an orphaned temp file — not a corrupted
   destination.
3. **Behave identically on POSIX and Windows.** The implementation relies
   on :func:`os.replace`, which is portable atomic replace on both
   families (NTFS provides atomic replace at the filesystem level on
   Windows, satisfying the same observable contract as ``rename(2)`` on
   POSIX).

Public surface (re-exported from :mod:`rytm_randomizer.cockpit.export`):

* :func:`atomic_write` — write ``bytes`` to ``path`` atomically.
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

import contextlib
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ...observability.errors import DataError
from ...observability.logging import get_logger

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

    Mirrors :class:`rytm_randomizer.cockpit.wizard.errors.WizardSourcePathError`
    (``DataError`` + :class:`FileNotFoundError`) and
    :class:`rytm_randomizer.cockpit.wizard.builder.EmptyAnalysisError`
    (``DataError`` + :class:`ValueError`).
    """


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
    3. Create a sibling temp file in the destination directory
       (:class:`tempfile.NamedTemporaryFile` with ``delete=False``).
       The temp file must live in the same directory as the destination
       so :func:`os.replace` stays atomic — atomic rename only holds
       within a single filesystem.
    4. Write ``data`` to the temp file, :func:`os.fsync` the descriptor
       *before* close (durability — survives a crash between write and
       rename), then close.
    5. :func:`os.replace` the temp onto the destination. ``os.replace``
       is portable atomic replace on both POSIX and Windows.
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
            destination already exists. No temp file is created in this
            path — we fail before writing anything.
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
            os.write(tmp_fd, data)
            os.fsync(tmp_fd)
        finally:
            os.close(tmp_fd)

        os.replace(tmp_name, str(path))
    except OSError as exc:
        # Best-effort cleanup of the orphan temp file. A failure here
        # (e.g. the temp was already gone, permissions revoked, etc.)
        # must NOT mask the original error.
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise WriteError(f"atomic_write failed for {path}: {exc}") from exc

    return WriteResult(
        path=path.resolve(),
        bytes_written=len(data),
        overwrote_existing=overwrote_existing,
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
    "atomic_write",
    "default_export_dir",
    "write_signed_export",
]
