"""The installed package version — contract I7.

``rytm_randomizer._version.__version__`` is a **frozen import path**: the WS
bootstrap surfaces it as ``session_status.app_version`` (contract I1), the
update beacon reports it, and the update check compares against it. Do not
rename this module or the attribute.

Resolution order:

1. ``importlib.metadata.version("rytm-randomizer")`` — the installed
   distribution's metadata, which the build backend derived from the repo-root
   ``VERSION`` file (``[tool.hatch.version]`` in ``pyproject.toml``). This is
   the authoritative answer for an installed app, including the PyInstaller
   sidecar inside a shipped bundle.
2. The repo-root ``VERSION`` file — the source-checkout fallback for a
   contributor running from a tree that was never ``pip install``-ed.
3. ``"0.0.0"`` — the last-resort sentinel. It is deliberately a valid SemVer
   that sorts below every real release, so a version comparison against it
   degrades to "everything is newer" rather than raising. It means *the
   version could not be determined*, and diagnostics should read it that way.

Layering: this is a leaf. It imports only the standard library, performs no
I/O beyond a single small file read in the fallback path, and must never
import anything else from ``rytm_randomizer`` — every layer is allowed to
import it.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _distribution_version
from pathlib import Path
from typing import Final

#: The installed distribution name (``[project] name`` in ``pyproject.toml``).
DISTRIBUTION_NAME: Final[str] = "rytm-randomizer"

#: Returned when neither the distribution metadata nor the ``VERSION`` file is
#: readable. Valid SemVer, sorts below every real release.
UNKNOWN_VERSION: Final[str] = "0.0.0"

#: Repo-root ``VERSION`` file, used only in a source checkout.
_VERSION_FILE: Final[Path] = Path(__file__).resolve().parents[1] / "VERSION"


def _read_version_file() -> str | None:
    """Return the ``VERSION`` file's contents, or ``None`` if unusable.

    Never raises: a missing file, an unreadable file, or undecodable bytes all
    degrade to ``None`` so importing this module can never fail the app.
    """
    try:
        text = _VERSION_FILE.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    stripped = text.strip()
    return stripped or None


def _resolve_version() -> str:
    """Resolve the version through the documented three-step order."""
    try:
        return _distribution_version(DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return _read_version_file() or UNKNOWN_VERSION


#: The package version. Contract I7 — frozen name, frozen import path.
__version__: Final[str] = _resolve_version()
