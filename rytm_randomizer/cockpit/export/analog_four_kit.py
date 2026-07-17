"""Guarded file export for rendered Analog Four MKII saved kits."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ...data.analog_four_sysex_calibration import (
    A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED,
    analog_four_sysex_calibration_for,
)
from ...devices.analog_four import (
    AnalogFourSavedKitMutation,
    AnalogFourSavedKitRenderResult,
    get_analog_four_saved_kit_capability,
)
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from .analog_four_export_contracts import (
    AnalogFourExportErrorCode,
    attach_analog_four_export_error_code,
)
from .writer import WriteResult, atomic_write

_logger = get_logger(__name__)


@dataclass(frozen=True)
class AnalogFourSavedKitExportResult:
    """Pure render metadata paired with the guarded disk-write result."""

    render: AnalogFourSavedKitRenderResult
    write: WriteResult


def _a4_export_error_code(
    exc: KeyError | ValueError | TypeError | OSError,
    *,
    source_read_completed: bool,
) -> AnalogFourExportErrorCode:
    if isinstance(exc, FileNotFoundError):
        return "input_not_found"
    if isinstance(exc, PermissionError):
        return "permission_denied"
    if isinstance(exc, FileExistsError):
        return "overwrite_refused"
    if isinstance(exc, OSError):
        return "write_failed" if source_read_completed else "source_read_failed"
    return "validation"


def export_analog_four_saved_kit(
    *,
    source_path: Path,
    output_path: Path,
    mutations: Sequence[AnalogFourSavedKitMutation],
    overwrite: bool = False,
) -> AnalogFourSavedKitExportResult:
    """Render an operator-selected A4 kit and atomically write a new file.

    Existing output files are refused unless ``overwrite`` is explicitly
    enabled. This function performs local file I/O only; it never opens or
    sends to a MIDI port.
    """

    metrics = get_metrics()
    started_at = time.perf_counter()
    source_read_completed = False
    capability = get_analog_four_saved_kit_capability()
    try:
        for mutation in mutations:
            if not capability.is_saved_kit_mutation(mutation):
                raise TypeError("mutations must contain AnalogFourSavedKitMutation records")
            calibration = analog_four_sysex_calibration_for(mutation.parameter)
            if calibration.status != A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED:
                raise ValueError(
                    f"{mutation.parameter} is not hardware-write-validated for file export"
                )

        source_sysex = source_path.read_bytes()
        source_read_completed = True
        render = capability.render_saved_kit(source_sysex, mutations)
        write = atomic_write(output_path, render.framed_sysex, overwrite=overwrite)
    except (KeyError, ValueError, TypeError, OSError) as exc:
        error_code = _a4_export_error_code(
            exc,
            source_read_completed=source_read_completed,
        )
        _logger.warning(
            "Analog Four saved-kit export failed",
            extra={
                "operation": "a4_saved_kit_export",
                "error_code": error_code,
                "source_path": str(source_path),
                "output_path": str(output_path),
            },
        )
        metrics.record_export(
            (time.perf_counter() - started_at) * 1000.0,
            error_code=error_code,
        )
        attach_analog_four_export_error_code(exc, error_code)
        raise

    metrics.record_export((time.perf_counter() - started_at) * 1000.0)
    _logger.info(
        "Analog Four saved-kit export completed",
        extra={
            "operation": "a4_saved_kit_export",
            "output_path": str(write.path),
            "sha256": render.sha256,
            "mutation_count": len(mutations),
        },
    )
    return AnalogFourSavedKitExportResult(render=render, write=write)


__all__ = [
    "AnalogFourSavedKitExportResult",
    "export_analog_four_saved_kit",
]
