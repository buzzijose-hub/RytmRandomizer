"""Shared failure contracts for passive local-file export services."""

from __future__ import annotations

import os
from collections.abc import Mapping
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
MAX_LOCAL_FILE_EXPORT_ARTIFACT_NAME_LENGTH: Final[int] = 255


@dataclass(frozen=True)
class LocalFileExportErrorContext:
    """Bounded operator-safe metadata attached to one export exception."""

    error_code: LocalFileExportErrorCode
    phase: LocalFileExportPhase
    artifact_name: str


def _has_safe_artifact_name_syntax(value: object) -> bool:
    return (
        isinstance(value, str)
        and value not in {"", ".", ".."}
        and "/" not in value
        and "\\" not in value
        and ":" not in value
        and all(ord(character) >= 32 and ord(character) != 127 for character in value)
        and Path(value).name == value
    )


def _is_safe_artifact_name(value: object) -> bool:
    return (
        _has_safe_artifact_name_syntax(value)
        and isinstance(value, str)
        and len(value) <= MAX_LOCAL_FILE_EXPORT_ARTIFACT_NAME_LENGTH
    )


def safe_local_file_export_artifact_name(
    path: Path,
    *,
    fallback: str,
    max_length: int = MAX_LOCAL_FILE_EXPORT_ARTIFACT_NAME_LENGTH,
) -> str:
    """Return one bounded filename for logs and attached failure context."""

    if (
        isinstance(max_length, bool)
        or max_length < 7
        or max_length > MAX_LOCAL_FILE_EXPORT_ARTIFACT_NAME_LENGTH
    ):
        raise ValueError("local file export artifact length bound is invalid")
    if not _has_safe_artifact_name_syntax(fallback) or len(fallback) > max_length:
        raise ValueError("local file export fallback artifact name is not safe")
    candidate = path.name if _has_safe_artifact_name_syntax(path.name) else fallback
    if len(candidate) <= max_length:
        return candidate
    prefix_length = (max_length - 3) // 2
    suffix_length = max_length - 3 - prefix_length
    return f"{candidate[:prefix_length]}...{candidate[-suffix_length:]}"


def validate_local_file_export_artifact_path(path: Path, *, label: str) -> None:
    """Reject paths whose final component cannot be reported safely."""

    if not _is_safe_artifact_name(path.name):
        raise ValueError(f"{label} must identify a safe filename")


def validate_distinct_local_file_export_paths(paths: Mapping[str, Path]) -> None:
    """Reject canonical path aliases across named input and output roles."""

    canonical_roles: dict[str, str] = {}
    for label, path in paths.items():
        canonical_path = os.path.normcase(str(path.resolve(strict=False)))
        previous_label = canonical_roles.get(canonical_path)
        if previous_label is not None:
            raise ValueError(f"{label} path collides with {previous_label}")
        canonical_roles[canonical_path] = label


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
    "MAX_LOCAL_FILE_EXPORT_ARTIFACT_NAME_LENGTH",
    "LocalFileExportErrorCode",
    "LocalFileExportErrorContext",
    "LocalFileExportPhase",
    "attach_local_file_export_error_context",
    "classify_local_file_export_error",
    "local_file_export_error_context",
    "safe_local_file_export_artifact_name",
    "validate_distinct_local_file_export_paths",
    "validate_local_file_export_artifact_path",
]
