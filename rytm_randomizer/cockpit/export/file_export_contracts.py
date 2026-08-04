"""Shared failure contracts for passive local-file export services."""

from __future__ import annotations

from typing import Literal, TypeAlias

LocalFileExportErrorCode: TypeAlias = Literal[
    "input_not_found",
    "interrupted",
    "overwrite_refused",
    "permission_denied",
    "source_read_failed",
    "validation",
    "write_failed",
]


def classify_local_file_export_error(
    exc: BaseException,
    *,
    source_read_completed: bool,
) -> LocalFileExportErrorCode:
    """Classify one passive export failure by its local file-I/O phase."""

    if isinstance(exc, (KeyboardInterrupt, SystemExit)):
        return "interrupted"
    if isinstance(exc, FileNotFoundError):
        return "write_failed" if source_read_completed else "input_not_found"
    if isinstance(exc, PermissionError):
        return "permission_denied"
    if isinstance(exc, FileExistsError):
        return "overwrite_refused"
    if isinstance(exc, OSError):
        return "write_failed" if source_read_completed else "source_read_failed"
    return "validation"


__all__ = ["LocalFileExportErrorCode", "classify_local_file_export_error"]
