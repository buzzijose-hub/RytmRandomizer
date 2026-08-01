"""Cockpit kit/sound library subpackage (WS-4).

JSON-record library store following the ProfileRegistry platform-dir
precedent, plus a device-generic importer for captured ``*.syx`` dumps.
See :mod:`rytm_randomizer.cockpit.library.store` for the full contract.
"""

from __future__ import annotations

from .store import (
    LibraryImportResult,
    LibraryRecord,
    LibraryStore,
    default_captures_dir,
    default_library_dir,
    payload_fingerprint,
)

__all__ = [
    "LibraryImportResult",
    "LibraryRecord",
    "LibraryStore",
    "default_captures_dir",
    "default_library_dir",
    "payload_fingerprint",
]
