"""``ProfileRegistry`` — disk-backed user profiles + built-in scenes.

The registry presents a single unified view: built-in scenes always come
first (sorted by name), followed by user-authored profiles loaded from
``{profiles_dir}/user/*.json`` (also sorted by name). The same
``ProfileModel`` dataclass carries both kinds — only ``kind`` differs.

Disk layout::

    {profiles_dir}/
      user/
        <profile_id>.json       # one file per user profile

Built-in scenes are **never** written to disk: they live in code under
``builtin.py`` and are re-loaded on every process start, ensuring they
cannot drift via stray edits.

Persistence guarantees (PR 7 — M7 + M6 + IH2)
---------------------------------------------

* :meth:`ProfileRegistry.save` routes through
  :func:`cockpit.export.writer.atomic_write` so a half-written file or a
  crash mid-write can never corrupt the destination — the bytes are
  written to a sibling temp file, ``fsync``-ed, and atomically renamed
  onto the target path.
* :meth:`save` refuses to overwrite an existing file by default (a fresh
  ULID collision is astronomically unlikely, but a retried
  ``wizard_save`` should not silently nuke prior user content). Pass
  ``overwrite=True`` to allow replacement.
* :meth:`save` returns :data:`None` — the prior ``-> Path`` return value
  was dead surface (no caller used it). Callers that need the on-disk
  path can derive it from ``{profiles_dir}/user/{profile_id}.json``.

Load-error classification policy
--------------------------------

The registry tolerates **per-file data problems** (malformed JSON,
missing keys, invalid trait values, etc.) and **refuses to start** on
**infrastructure problems** (permission denied on the profiles
directory). The two classes are deliberately distinguished — a
permission-denied error presenting as a quiet warning followed by an
empty registry has been a recurring source of confused boot-time
incidents in similar systems. See :func:`_safe_load_profile` for the
exact mapping.
"""

from __future__ import annotations

import errno
import json
import logging
from pathlib import Path
from typing import ClassVar, Final

from rytm_randomizer.cockpit.data import ProfileModel
from rytm_randomizer.cockpit.export.writer import atomic_write
from rytm_randomizer.observability.errors import DataError

from .builtin import BUILTIN_SCENES

_logger: Final[logging.Logger] = logging.getLogger(__name__)
"""Per-module logger used to report skipped malformed profile files."""

_USER_SUBDIR: Final[str] = "user"
"""Sub-directory under ``profiles_dir`` that holds operator-authored JSON."""

_USER_GLOB: Final[str] = "*.json"
"""Glob pattern used to discover user-profile files."""


# ---------------------------------------------------------------------------
# Errors — taxonomy-aligned dual-inheritance (mirrors WriteError,
# EmptyAnalysisError, WizardSourcePathError patterns).
# ---------------------------------------------------------------------------


class ProfileAlreadyExistsError(DataError, FileExistsError):
    """Raised by :meth:`ProfileRegistry.save` when the target file exists.

    Multi-inheritance via :class:`DataError` (the RytmRandomizerError
    taxonomy branch for missing / malformed data) AND
    :class:`FileExistsError` (stdlib) means:

    * ``except FileExistsError:`` callers continue to work without
      import changes (idiomatic Python file-collision handling);
    * The observability conformance test
      (``tests/architecture/test_observability.py``) recognises the
      raise as a taxonomy member.

    Mirrors :class:`rytm_randomizer.cockpit.wizard.builder.
    EmptyAnalysisError` and
    :class:`rytm_randomizer.cockpit.export.writer.WriteError`, which use
    the same dual-inheritance pattern.
    """

    fingerprint: ClassVar[str] = "profile.registry.already_exists"


class ProfileRegistryAccessError(DataError, PermissionError):
    """Raised on infrastructure-level failures reading the profiles dir.

    Surfaces when a permission error (EACCES / EPERM) prevents the
    registry from reading a profile file the operator owns. Treated as
    "refuse to boot with a confusing empty registry" rather than the
    per-file "warn + skip" policy that covers malformed JSON.

    Multi-inheritance via :class:`DataError` + :class:`PermissionError`
    keeps stdlib ``except PermissionError:`` callers working AND lets the
    observability conformance test recognise it as a taxonomy member.
    """

    fingerprint: ClassVar[str] = "profile.registry.access_denied"


class ProfileRegistry:
    """Unified view over built-in scenes + on-disk user profiles.

    Construction does not touch the filesystem; the first
    ``list_profiles`` / ``get`` call lazily scans ``{profiles_dir}/user/``.
    Call ``reload()`` to force a re-scan after files change on disk.
    """

    def __init__(self, profiles_dir: Path) -> None:
        """Bind the registry to a profiles directory (no I/O performed).

        ``profiles_dir`` itself does not need to exist yet — it is created
        on the first ``save()`` call. The ``user/`` subdirectory is what
        the registry actually reads from / writes to.
        """

        self._profiles_dir: Path = profiles_dir
        self._user_profiles: dict[str, ProfileModel] = {}
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------

    @property
    def builtin_scenes(self) -> list[ProfileModel]:
        """Return the built-in scenes as a fresh list (sorted by name)."""

        return sorted(BUILTIN_SCENES, key=lambda p: p.name)

    def list_profiles(self) -> list[ProfileModel]:
        """Return the union: built-in scenes first, then user profiles.

        Each sub-list is sorted by ``name``. The result is a new list on
        every call; mutating it does not affect the registry.
        """

        self._ensure_loaded()
        scenes = self.builtin_scenes
        users = sorted(self._user_profiles.values(), key=lambda p: p.name)
        return scenes + users

    def get(self, profile_id: str) -> ProfileModel | None:
        """Return the profile with this ``profile_id``, or ``None``.

        Built-in scenes are checked first (they cannot be shadowed by a
        user profile with a colliding id because their ids are namespaced
        ``scene-*``).
        """

        for scene in BUILTIN_SCENES:
            if scene.profile_id == profile_id:
                return scene
        self._ensure_loaded()
        return self._user_profiles.get(profile_id)

    def save(self, profile: ProfileModel, *, overwrite: bool = False) -> None:
        """Persist ``profile`` to ``{profiles_dir}/user/{profile_id}.json``.

        The write goes through
        :func:`cockpit.export.writer.atomic_write` so a crash, ``EIO``,
        or ``ENOSPC`` mid-write leaves the prior on-disk file (if any)
        intact — never a half-written corrupted destination.

        Args:
            profile: The :class:`ProfileModel` to persist.
            overwrite: When :data:`False` (the default), an existing
                file at the target path is refused with
                :class:`ProfileAlreadyExistsError`. When :data:`True`,
                the existing file is atomically replaced. The wizard
                save handler relies on the default — a retried
                ``wizard_save`` for a profile id that already exists
                should fail loudly, not silently obliterate prior user
                content.

        Raises:
            ProfileAlreadyExistsError: ``overwrite`` is :data:`False`
                and the destination already exists. Subclass of
                :class:`DataError` + :class:`FileExistsError`.
            WriteError: The atomic write itself failed (disk full,
                permission denied, fsync failure, etc.). Bubbles up
                from :func:`atomic_write` unchanged — it is already a
                member of the taxonomy.
        """

        user_dir = self._profiles_dir / _USER_SUBDIR
        target = user_dir / f"{profile.profile_id}.json"
        # ``indent=2`` keeps the on-disk format git-friendly per spec
        # §"Open questions" (flat JSON, not SQLite).
        encoded = json.dumps(profile.to_dict(), indent=2, sort_keys=True).encode("utf-8")
        try:
            atomic_write(target, encoded, overwrite=overwrite)
        except FileExistsError as exc:
            # ``atomic_write`` raises plain :class:`FileExistsError` so
            # general-purpose callers can ``except FileExistsError:``;
            # we re-raise as the taxonomy-aligned variant so the
            # observability conformance check is satisfied AND the
            # ``except FileExistsError:`` callers continue to work
            # (dual-inheritance preserves the stdlib catch).
            raise ProfileAlreadyExistsError(
                f"profile {profile.profile_id!r} already exists at {target} "
                "(pass overwrite=True to replace)"
            ) from exc
        # Keep the in-memory view in sync. If a reload happens later it
        # will repopulate from disk anyway.
        self._ensure_loaded()
        self._user_profiles[profile.profile_id] = profile

    def reload(self) -> None:
        """Re-scan the user directory from disk (drops the in-memory cache)."""

        self._user_profiles = {}
        self._loaded = False
        self._ensure_loaded()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        """Lazy-load user profiles on first access (idempotent)."""

        if self._loaded:
            return
        self._user_profiles = self._scan_user_profiles()
        self._loaded = True

    def _scan_user_profiles(self) -> dict[str, ProfileModel]:
        """Scan ``{profiles_dir}/user/*.json`` and return a fresh dict.

        See :func:`_safe_load_profile` for the per-file error
        classification policy (data-shape problems warn + skip;
        permission-denied infrastructure problems are loud and refuse
        to start).
        """

        user_dir = self._profiles_dir / _USER_SUBDIR
        result: dict[str, ProfileModel] = {}
        if not user_dir.is_dir():
            return result
        for path in sorted(user_dir.glob(_USER_GLOB)):
            profile = _safe_load_profile(path)
            if profile is None:
                continue
            result[profile.profile_id] = profile
        return result


def _safe_load_profile(path: Path) -> ProfileModel | None:
    """Load a single profile JSON; classify errors by severity.

    Error policy (PR 7 — M6):

    * :class:`PermissionError` (EACCES / EPERM) → log ERROR with the
      offending path and raise :class:`ProfileRegistryAccessError`. This
      is an *infrastructure* problem — the cockpit must refuse to boot
      with a confusing empty registry rather than presenting it as a
      mere warning.
    * :class:`FileNotFoundError` → DEBUG log + return :data:`None`. The
      file vanished between the directory scan and the read (a benign
      race condition, e.g. another process tidying up). The caller
      simply skips it.
    * Other :class:`OSError` (EIO, ENAMETOOLONG, transient FS errors,
      etc.) → WARNING log + return :data:`None`. The caller skips it.
    * :class:`json.JSONDecodeError`, :class:`KeyError`,
      :class:`TypeError`, :class:`ValueError` → WARNING log + return
      :data:`None`. These are *data-shape* problems with a single
      profile (corrupted JSON, missing required fields, invalid
      ``kind`` literal, etc.). A single bad file must not take down the
      cockpit.

    The split between "warn + skip" (the file is broken) and "refuse to
    start" (the directory is unreadable) is the M6 fix: the prior
    handler swallowed every error class identically, so a
    permission-denied directory looked exactly like a single corrupted
    JSON — quiet warning, empty registry, no signal that the operator's
    work was actually inaccessible.
    """

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except PermissionError as exc:
        _logger.error(
            "Permission denied reading profile file %s (%s: %s) — "
            "refusing to continue with an incomplete registry.",
            path,
            type(exc).__name__,
            exc,
            extra={"event": "profile_registry.file_read.permission_denied"},
        )
        raise ProfileRegistryAccessError(f"permission denied reading {path}") from exc
    except FileNotFoundError as exc:
        # File disappeared between directory scan and read. Benign race;
        # surface at DEBUG so a curious operator can spot it without
        # cluttering normal logs.
        _logger.debug(
            "Profile file %s vanished before read (%s: %s); skipping.",
            path,
            type(exc).__name__,
            exc,
            extra={"event": "profile_registry.file_read.vanished"},
        )
        return None
    except OSError as exc:
        # Non-permission infrastructure errors (transient FS hiccups,
        # ENAMETOOLONG, EIO during read, etc.). Warn + skip — these
        # tend to be per-file and we'd rather load the rest of the
        # registry than refuse to start. A permission error masquerading
        # as a generic OSError is defended against below.
        if exc.errno in (errno.EACCES, errno.EPERM):  # pragma: no cover - defensive
            _logger.error(
                "Permission denied reading profile file %s (%s, errno=%s) — "
                "refusing to continue with an incomplete registry.",
                path,
                type(exc).__name__,
                exc.errno,
                extra={"event": "profile_registry.file_read.permission_denied"},
            )
            raise ProfileRegistryAccessError(f"permission denied reading {path}") from exc
        _logger.warning(
            "Skipping unreadable profile file %s (%s: %s)",
            path,
            type(exc).__name__,
            exc,
            extra={"event": "profile_registry.file_read.os_error"},
        )
        return None
    except json.JSONDecodeError as exc:
        _logger.warning(
            "Skipping malformed profile file %s (%s: %s)",
            path,
            type(exc).__name__,
            exc,
            extra={"event": "profile_registry.file_parse.malformed_json"},
        )
        return None
    if not isinstance(data, dict):
        _logger.warning(
            "Skipping profile file %s: top-level JSON must be an object, got %s",
            path,
            type(data).__name__,
            extra={"event": "profile_registry.file_parse.non_object_root"},
        )
        return None
    try:
        return ProfileModel.from_dict(data)
    except (KeyError, TypeError, ValueError) as exc:
        _logger.warning(
            "Skipping invalid profile file %s (%s: %s)",
            path,
            type(exc).__name__,
            exc,
            extra={"event": "profile_registry.file_parse.invalid_profile"},
        )
        return None


__all__ = [
    "ProfileAlreadyExistsError",
    "ProfileRegistry",
    "ProfileRegistryAccessError",
]
