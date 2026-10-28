"""Path-free presentation facts for existing local artifact error categories."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

_MISSING: Final[str] = (
    "Local artifact is missing. Restore the complete package or retained source, then retry."
)
_CORRUPT: Final[str] = (
    "Local artifact failed integrity checks. Restore a verified copy or re-export it, then retry."
)
_SCHEMA: Final[str] = (
    "Local artifact schema is incompatible or invalid. Use a compatible app or re-export a verified package."
)
_MISMATCH: Final[str] = (
    "Local artifact does not match its source or manifest. Restore matching source files or re-export the package."
)
_ACCESS: Final[str] = (
    "Local artifact could not be accessed or changed during reading. Check folder access and retry."
)
_PATH: Final[str] = (
    "Local artifact location is unsafe. Use a regular local file or package directory, then retry."
)
_SIZE: Final[str] = (
    "Local artifact size exceeds supported bounds or differs from its manifest. Restore a verified copy or export a smaller package."
)
_WRITE: Final[str] = (
    "Local files could not be saved. Check available space and folder access, then retry."
)
_EXISTS: Final[str] = (
    "Local destination already exists. Choose a new bank or package ID; existing files were not replaced."
)

LOCAL_ARTIFACT_RECOVERY_MESSAGES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "missing": _MISSING,
        "malformed-json": _CORRUPT,
        "schema": _SCHEMA,
        "cross-reference": _MISMATCH,
        "size": _SIZE,
        "path": _PATH,
        "hash": _CORRUPT,
        "framing": _CORRUPT,
        "access": _ACCESS,
    }
)
LOCAL_SOURCE_RECOVERY_MESSAGES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "invalid_record_id": "Library source ID is invalid. Select a retained source from the Library.",
        "access": _ACCESS,
        "path": _PATH,
        "size": _SIZE,
        "missing": _MISSING,
        "record_shape": _CORRUPT,
        "record_schema": _SCHEMA,
        "frame_integrity": _CORRUPT,
        "payload_identity": _MISMATCH,
        "codec": _CORRUPT,
        "metadata": _MISMATCH,
        "timestamp": _CORRUPT,
        "provenance": _MISMATCH,
        "input_only": _MISMATCH,
        "identity_collision": _MISMATCH,
        "legacy_reconstruction_required": "Library source has no retained original frame. Explicitly reconstruct the legacy source or import its original KIT file.",
        "no_original_source": _MISSING,
        "validation": "Library source is invalid. Select a verified retained source, then retry.",
        "schema_newer_than_app": _SCHEMA,
    }
)
LOCAL_EXPORT_RECOVERY_MESSAGES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "input_not_found": _MISSING,
        "interrupted": "Local file operation was interrupted. Review the destination before retrying.",
        "overwrite_refused": _EXISTS,
        "permission_denied": _ACCESS,
        "source_read_failed": _ACCESS,
        "validation": "Local file request is invalid. Review the selected source and destination, then retry.",
        "write_failed": _WRITE,
    }
)

__all__ = [
    "LOCAL_ARTIFACT_RECOVERY_MESSAGES",
    "LOCAL_SOURCE_RECOVERY_MESSAGES",
    "LOCAL_EXPORT_RECOVERY_MESSAGES",
]
