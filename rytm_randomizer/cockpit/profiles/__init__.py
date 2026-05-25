"""Cockpit profile registry — disk-backed profiles + 7 built-in scenes.

This package exposes:

* ``ProfileRegistry`` — load ``ProfileModel`` instances from a profiles
  directory (one JSON file per user-authored profile), save new ones, and
  list the union of built-in scenes + on-disk user profiles.
* ``BUILTIN_SCENES`` — the seven developer-curated scenes
  (``industrial``, ``hypnotic``, ``garage``, ``peak_time``, ``rolling``,
  ``birmingham``, ``drone``). Each one is a ``ProfileModel`` with
  ``kind="scene"`` and a deterministic ``profile_id`` (``scene-<name>``).
* ``default_profiles_dir()`` — XDG-honoring per-platform default for the
  profiles directory (``$XDG_CONFIG_HOME/rytm-randomizer/profiles`` on
  Linux, ``~/Library/Application Support/rytm-randomizer/profiles`` on
  macOS, ``$APPDATA/rytm-randomizer/profiles`` on Windows).

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"ProfileModel" + the plan §"WS-C" for the contract.
"""

from __future__ import annotations

from .builtin import BUILTIN_SCENES
from .paths import default_profiles_dir
from .registry import (
    ProfileAlreadyExistsError,
    ProfileRegistry,
    ProfileRegistryAccessError,
)

__all__ = [
    "BUILTIN_SCENES",
    "ProfileAlreadyExistsError",
    "ProfileRegistry",
    "ProfileRegistryAccessError",
    "default_profiles_dir",
]
