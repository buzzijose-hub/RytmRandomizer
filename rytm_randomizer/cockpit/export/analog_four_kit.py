"""Guarded file export for rendered Analog Four MKII saved kits."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ...devices.analog_four import (
    AnalogFourSavedKitMutation,
    AnalogFourSavedKitRenderResult,
    get_analog_four_saved_kit_capability,
)
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...observability.tracing import operation
from .analog_four_export_contracts import (
    analog_four_export_path_name,
    attach_analog_four_export_error_code,
    require_analog_four_export_path,
)
from .file_export_contracts import LocalFileExportPhase, classify_local_file_export_error
from .writer import WriteResult, atomic_write

_logger = get_logger(__name__)
_A4_SAVED_KIT_EXPORT_FAILURE_FINGERPRINT: Final[str] = "a4.saved_kit_export.failed"


@dataclass(frozen=True)
class AnalogFourSavedKitExportResult:
    """Pure render metadata paired with the guarded disk-write result."""

    render: AnalogFourSavedKitRenderResult
    write: WriteResult


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
    export_phase: LocalFileExportPhase = "validation"
    source_name = analog_four_export_path_name(source_path)
    output_name = analog_four_export_path_name(output_path)
    operation_id = ""
    try:
        with operation(
            "a4_saved_kit_export",
            logger=_logger,
            source_name=source_name,
            output_name=output_name,
        ) as operation_id:
            source_path = require_analog_four_export_path(
                source_path,
                field_name="source_path",
            )
            output_path = require_analog_four_export_path(
                output_path,
                field_name="output_path",
            )
            capability = get_analog_four_saved_kit_capability()
            export_phase = "source_read"
            source_sysex = source_path.read_bytes()
            export_phase = "validation"
            render = capability.render_saved_kit(source_sysex, mutations)
            export_phase = "output_write"
            write = atomic_write(output_path, render.framed_sysex, overwrite=overwrite)
    except (KeyError, ValueError, TypeError, OSError, KeyboardInterrupt, SystemExit) as exc:
        error_code = classify_local_file_export_error(
            exc,
            phase=export_phase,
        )
        duration_ms = (time.perf_counter() - started_at) * 1000.0
        metrics.record_export(duration_ms, error_code=error_code)
        _logger.warning(
            "Analog Four saved-kit export failed",
            extra={
                "op_id": operation_id,
                "operation": "a4_saved_kit_export",
                "outcome": "failed",
                "error_code": error_code,
                "fingerprint": _A4_SAVED_KIT_EXPORT_FAILURE_FINGERPRINT,
                "source_name": source_name,
                "output_name": output_name,
                "error_type": type(exc).__name__,
                "duration_ms": duration_ms,
                "metrics_summary": metrics.format_summary(),
            },
        )
        if isinstance(exc, Exception):
            attach_analog_four_export_error_code(exc, error_code)
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics.record_export(duration_ms)
    _logger.info(
        "Analog Four saved-kit export completed",
        extra={
            "op_id": operation_id,
            "operation": "a4_saved_kit_export",
            "outcome": "completed",
            "output_name": write.path.name,
            "sha256": render.sha256,
            "mutation_count": len(mutations),
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )
    return AnalogFourSavedKitExportResult(render=render, write=write)


__all__ = [
    "AnalogFourSavedKitExportResult",
    "export_analog_four_saved_kit",
]
