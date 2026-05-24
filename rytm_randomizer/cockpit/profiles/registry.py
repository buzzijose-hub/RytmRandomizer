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

The registry intentionally tolerates malformed user-profile JSON: a file
that fails to parse or to validate is **skipped with a warning**, so a
single corrupted profile does not take down the cockpit. The warning is
emitted through the stdlib ``logging`` module.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Final

from rytm_randomizer.cockpit.data import ProfileModel

from .builtin import BUILTIN_SCENES

_logger: Final[logging.Logger] = logging.getLogger(__name__)
"""Per-module logger used to report skipped malformed profile files."""

_USER_SUBDIR: Final[str] = "user"
"""Sub-directory under ``profiles_dir`` that holds operator-authored JSON."""

_USER_GLOB: Final[str] = "*.json"
"""Glob pattern used to discover user-profile files."""


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

    def save(self, profile: ProfileModel) -> Path:
        """Persist ``profile`` to ``{profiles_dir}/user/{profile_id}.json``.

        The parent directories are created if they do not exist. Returns
        the absolute on-disk path. The in-memory cache is updated so the
        next ``get()`` / ``list_profiles()`` reflects the new profile
        without an explicit ``reload()``.
        """

        user_dir = self._profiles_dir / _USER_SUBDIR
        user_dir.mkdir(parents=True, exist_ok=True)
        target = user_dir / f"{profile.profile_id}.json"
        # ``indent=2`` keeps the on-disk format git-friendly per spec
        # §"Open questions" (flat JSON, not SQLite).
        target.write_text(
            json.dumps(profile.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        # Keep the in-memory view in sync. If a reload happens later it
        # will repopulate from disk anyway.
        self._ensure_loaded()
        self._user_profiles[profile.profile_id] = profile
        return target

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

        Files that fail to parse or to validate are logged at WARNING and
        skipped — the registry refuses to crash on a single bad file.
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
    """Load a single profile JSON; return ``None`` on any failure.

    The "any failure" cases — malformed JSON, non-dict root, missing
    keys, invalid trait values, invalid kind, etc. — are all swallowed
    here so a single bad file cannot break registry loading. Each failure
    is logged at WARNING with the offending path + exception class so an
    operator can spot the problem.
    """

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        _logger.warning(
            "Skipping malformed profile file %s (%s: %s)",
            path,
            type(exc).__name__,
            exc,
        )
        return None
    if not isinstance(data, dict):
        _logger.warning(
            "Skipping profile file %s: top-level JSON must be an object, got %s",
            path,
            type(data).__name__,
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
        )
        return None


__all__ = ["ProfileRegistry"]
