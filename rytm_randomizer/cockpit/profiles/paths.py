"""Per-platform default location for the cockpit profile registry.

The default profiles directory honors the freedesktop XDG Base Directory
specification on Linux (``$XDG_CONFIG_HOME`` if set, else ``~/.config``),
and uses platform-conventional locations on macOS and Windows.

A caller (typically the WS-E WebSocket server) may override the default by
constructing ``ProfileRegistry(profiles_dir=...)`` with any path; this
module only supplies the fallback when no override is given.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Final

_APP_DIR_NAME: Final[str] = "rytm-randomizer"
_PROFILES_LEAF: Final[str] = "profiles"


def default_profiles_dir() -> Path:
    """Return the platform-default profiles directory (no I/O performed).

    The returned path is **not** created on disk — that is the registry's
    responsibility on first ``save()``. The function is pure: it reads
    ``sys.platform`` and a small set of environment variables and returns
    an in-memory ``Path``.

    Resolution order, per platform:

    * **Linux** (``sys.platform == "linux"``): ``$XDG_CONFIG_HOME/rytm-randomizer/profiles``
      if ``XDG_CONFIG_HOME`` is set to a non-empty value, else
      ``~/.config/rytm-randomizer/profiles``.
    * **macOS** (``sys.platform == "darwin"``): ``~/Library/Application Support/rytm-randomizer/profiles``.
    * **Windows** (``sys.platform == "win32"``): ``$APPDATA/rytm-randomizer/profiles``
      if ``APPDATA`` is set, else ``~/AppData/Roaming/rytm-randomizer/profiles``.
    * **Other / unknown platforms:** fall back to the Linux/XDG resolution
      (``$XDG_CONFIG_HOME`` honored if set).
    """

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / _APP_DIR_NAME / _PROFILES_LEAF

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        return base / _APP_DIR_NAME / _PROFILES_LEAF

    # Linux + any other POSIX-flavored platform: XDG.
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / _APP_DIR_NAME / _PROFILES_LEAF


__all__ = ["default_profiles_dir"]
