"""Shared failure contracts for passive local-file export services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, TypeAlias, cast

LocalFileExportErrorCode: TypeAlias = Literal[
    "input_not_found",
    "interrupted",
    "overwrite_refused",
    "permission_denied",
    "source_read_failed",
    "validation",
    "write_failed",
]

LOCAL_FILE_EXPORT_ERROR_CODES: Final[frozenset[str]] = frozenset(
    {
        "input_not_found",
        "interrupted",
        "overwrite_refused",
        "permission_denied",
        "source_read_failed",
        "validation",
        "write_failed",
    }
)

LocalFileExportPhase: TypeAlias = Literal[
    "validation",
    "source_read",
    "output_write",
]

LOCAL_FILE_EXPORT_PHASES: Final[frozenset[str]] = frozenset(
    {"validation", "source_read", "output_write"}
)
_ERROR_CODE_ATTRIBUTE: Final[str] = "local_file_export_error_code"
_ERROR_PHASE_ATTRIBUTE: Final[str] = "local_file_export_phase"
_ERROR_ARTIFACT_ATTRIBUTE: Final[str] = "local_file_export_artifact_name"


@dataclass(frozen=True)
class LocalFileExportErrorContext:
    """Bounded operator-safe metadata attached to one export exception."""

    error_code: LocalFileExportErrorCode
    phase: LocalFileExportPhase
    artifact_name: str


def _is_safe_artifact_name(value: object) -> bool:
    return isinstance(value, str) and bool(value) and Path(value).name == value


def attach_local_file_export_error_context(
    exc: BaseException,
    *,
    error_code: LocalFileExportErrorCode,
    phase: LocalFileExportPhase,
    artifact_name: str,
) -> None:
    """Attach validated, path-free failure metadata without wrapping the exception."""

    if error_code not in LOCAL_FILE_EXPORT_ERROR_CODES:
        raise ValueError("local file export error code is not recognized")
    if phase not in LOCAL_FILE_EXPORT_PHASES:
        raise ValueError("local file export phase is not recognized")
    if not _is_safe_artifact_name(artifact_name):
        raise ValueError("local file export artifact must be a filename without a path")
    exc.__dict__[_ERROR_CODE_ATTRIBUTE] = error_code
    exc.__dict__[_ERROR_PHASE_ATTRIBUTE] = phase
    exc.__dict__[_ERROR_ARTIFACT_ATTRIBUTE] = artifact_name


def local_file_export_error_context(
    exc: BaseException,
) -> LocalFileExportErrorContext | None:
    """Return attached failure metadata only when every field remains bounded."""

    error_code = getattr(exc, _ERROR_CODE_ATTRIBUTE, None)
    phase = getattr(exc, _ERROR_PHASE_ATTRIBUTE, None)
    artifact_name = getattr(exc, _ERROR_ARTIFACT_ATTRIBUTE, None)
    if (
        not isinstance(error_code, str)
        or error_code not in LOCAL_FILE_EXPORT_ERROR_CODES
        or not isinstance(phase, str)
        or phase not in LOCAL_FILE_EXPORT_PHASES
        or not _is_safe_artifact_name(artifact_name)
    ):
        return None
    return LocalFileExportErrorContext(
        error_code=cast(LocalFileExportErrorCode, error_code),
        phase=cast(LocalFileExportPhase, phase),
        artifact_name=cast(str, artifact_name),
    )


def classify_local_file_export_error(
    exc: BaseException,
    *,
    phase: LocalFileExportPhase,
) -> LocalFileExportErrorCode:
    """Classify one passive export failure by its local file-I/O phase."""

    if isinstance(exc, (KeyboardInterrupt, SystemExit)):
        return "interrupted"
    if isinstance(exc, FileNotFoundError):
        return "write_failed" if phase == "output_write" else "input_not_found"
    if isinstance(exc, PermissionError):
        return "permission_denied"
    if isinstance(exc, FileExistsError):
        return "overwrite_refused"
    if isinstance(exc, OSError):
        if phase == "output_write":
            return "write_failed"
        if phase == "source_read":
            return "source_read_failed"
    return "validation"


__all__ = [
    "LOCAL_FILE_EXPORT_ERROR_CODES",
    "LOCAL_FILE_EXPORT_PHASES",
    "LocalFileExportErrorCode",
    "LocalFileExportErrorContext",
    "LocalFileExportPhase",
    "attach_local_file_export_error_context",
    "classify_local_file_export_error",
    "local_file_export_error_context",
]
