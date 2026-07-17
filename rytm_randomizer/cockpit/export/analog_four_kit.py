"""Guarded file export for rendered Analog Four MKII saved kits."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from rytm_randomizer.data.analog_four_sysex_calibration import (
    A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED,
    analog_four_sysex_calibration_for,
)
from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
    AnalogFourSavedKitMutation,
    AnalogFourSavedKitRenderResult,
    render_analog_four_saved_kit,
)

from .writer import WriteResult, atomic_write


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

    for mutation in mutations:
        if not isinstance(mutation, AnalogFourSavedKitMutation):
            raise TypeError("mutations must contain AnalogFourSavedKitMutation records")
        calibration = analog_four_sysex_calibration_for(mutation.parameter)
        if calibration.status != A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED:
            raise ValueError(
                f"{mutation.parameter} is not hardware-write-validated for file export"
            )

    source_sysex = source_path.read_bytes()
    render = render_analog_four_saved_kit(source_sysex, mutations)
    write = atomic_write(output_path, render.framed_sysex, overwrite=overwrite)
    return AnalogFourSavedKitExportResult(render=render, write=write)


__all__ = [
    "AnalogFourSavedKitExportResult",
    "export_analog_four_saved_kit",
]
