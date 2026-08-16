"""Shared machine-readable contracts for passive Analog Four exports."""

from __future__ import annotations

from pathlib import Path
from typing import Final, Literal, TypeAlias, cast

from ...observability.errors import BoundaryError
from .file_export_contracts import (
    LOCAL_FILE_EXPORT_ERROR_CODES,
    LocalFileExportErrorCode,
    classify_local_file_export_error,
    safe_local_file_export_artifact_name,
)

AnalogFourSpecificExportErrorCode: TypeAlias = Literal[
    "audio_read_failed",
    "dependency_missing",
    "inference_failed",
    "invalid_input",
    "publication_locked",
    "service_unavailable",
]
AnalogFourExportErrorCode: TypeAlias = LocalFileExportErrorCode | AnalogFourSpecificExportErrorCode
"""Bounded failure categories shared by A4 export services and CLIs."""

ANALOG_FOUR_EXPORT_ERROR_CODES: Final[frozenset[str]] = frozenset(
    LOCAL_FILE_EXPORT_ERROR_CODES
    | {
        "audio_read_failed",
        "dependency_missing",
        "inference_failed",
        "invalid_input",
        "publication_locked",
        "service_unavailable",
    }
)

_ERROR_CODE_ATTRIBUTE: Final[str] = "error_code"


def analog_four_export_path_name(value: object) -> str:
    """Return a bounded filename for telemetry without trusting caller types."""

    if not isinstance(value, Path):
        return "<invalid>"
    return safe_local_file_export_artifact_name(value, fallback="<invalid>")


def require_analog_four_export_path(value: object, *, field_name: str) -> Path:
    """Validate one public export path at the recorded service boundary."""

    if not isinstance(value, Path):
        raise TypeError(f"{field_name} must be a pathlib.Path")
    return value


def attach_analog_four_export_error_code(
    exc: Exception,
    error_code: AnalogFourExportErrorCode,
) -> None:
    """Attach one bounded classification while preserving the original exception."""

    exc.__dict__[_ERROR_CODE_ATTRIBUTE] = error_code


def analog_four_export_error_code(
    exc: Exception,
) -> AnalogFourExportErrorCode | None:
    """Return a propagated classification only when it belongs to the contract."""

    classified_code = getattr(exc, _ERROR_CODE_ATTRIBUTE, None)
    if isinstance(classified_code, str) and classified_code in ANALOG_FOUR_EXPORT_ERROR_CODES:
        return cast(AnalogFourExportErrorCode, classified_code)
    return None


def classify_analog_four_cli_error(
    exc: Exception,
    *,
    default_error_code: AnalogFourExportErrorCode,
) -> AnalogFourExportErrorCode:
    """Classify one A4 command failure through the shared passive contract."""

    propagated = analog_four_export_error_code(exc)
    if propagated is not None:
        return propagated

    from ...style_analysis.extractor import StyleAnalysisDependencyError

    if isinstance(exc, StyleAnalysisDependencyError):
        return "dependency_missing"
    if isinstance(exc, BoundaryError):
        return "inference_failed"
    if isinstance(exc, ImportError):
        return "service_unavailable"
    if isinstance(exc, RuntimeError):
        return "inference_failed"
    if isinstance(exc, FileNotFoundError):
        return "input_not_found"
    local_error = classify_local_file_export_error(exc, phase="output_write")
    return default_error_code if local_error == "validation" else local_error


__all__ = [
    "ANALOG_FOUR_EXPORT_ERROR_CODES",
    "AnalogFourExportErrorCode",
    "analog_four_export_path_name",
    "analog_four_export_error_code",
    "attach_analog_four_export_error_code",
    "classify_analog_four_cli_error",
    "require_analog_four_export_path",
]
