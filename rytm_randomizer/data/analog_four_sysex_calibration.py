"""Promoted Analog Four MKII SysEx calibration facts.

The facts in this module come from passive, operator-supplied kit exports.
They are data only: no MIDI ports are opened, no SysEx is written, and no
hardware state is mutated.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED: Final[str] = "candidate-promoted"
A4_SYSEX_CALIBRATION_STATUS_PENDING: Final[str] = "pending"

A4_SYNTH_TRACK_MIN: Final[int] = 1
A4_SYNTH_TRACK_MAX: Final[int] = 4


@dataclass(frozen=True)
class AnalogFourSysexCalibrationEvidence:
    """One passive hardware-export observation for an A4 SysEx field."""

    track: int
    screen_value: str
    primary_raw_value: int
    kit_name: str
    source_file: str
    payload_fingerprint: str


@dataclass(frozen=True)
class AnalogFourSysexFieldCalibration:
    """Promoted or candidate-promoted A4 SysEx field location."""

    parameter: str
    section: str
    status: str
    screen_min: str
    screen_mid: str
    screen_max: str
    primary_raw_values: Mapping[str, int]
    track_1_primary_raw_offset: int
    track_raw_stride: int
    track_1_raw_group_start: int
    raw_group_width: int
    track_1_unpacked_group_start: int
    unpacked_group_width: int
    track_unpacked_stride: int
    evidence: tuple[AnalogFourSysexCalibrationEvidence, ...]
    notes: tuple[str, ...]

    def primary_raw_offset_for_track(self, track: int) -> int:
        """Return the packed primary value offset for ``track``."""

        _validate_a4_sysex_calibration_track(track)
        return self.track_1_primary_raw_offset + ((track - 1) * self.track_raw_stride)

    def raw_group_range_for_track(self, track: int) -> tuple[int, int]:
        """Return the half-open packed group range for ``track``."""

        _validate_a4_sysex_calibration_track(track)
        start = self.track_1_raw_group_start + ((track - 1) * self.track_raw_stride)
        return start, start + self.raw_group_width

    def unpacked_group_range_for_track(self, track: int) -> tuple[int, int]:
        """Return the half-open decoded-byte group range for ``track``."""

        _validate_a4_sysex_calibration_track(track)
        start = self.track_1_unpacked_group_start + ((track - 1) * self.track_unpacked_stride)
        return start, start + self.unpacked_group_width


def _validate_a4_sysex_calibration_track(track: int) -> None:
    if not A4_SYNTH_TRACK_MIN <= track <= A4_SYNTH_TRACK_MAX:
        raise ValueError("track must be in 1..4")


def _screen_value_map(values: Mapping[str, int]) -> Mapping[str, int]:
    return MappingProxyType(dict(values))


_FILTER1_FREQUENCY_EVIDENCE: Final[tuple[AnalogFourSysexCalibrationEvidence, ...]] = (
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="0.00",
        primary_raw_value=0x00,
        kit_name="KIT 1",
        source_file="A4_Test1_T1_Filter1Freq_000_Kit.syx",
        payload_fingerprint="f1a52fd48b776c6b",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="63.50",
        primary_raw_value=0x3F,
        kit_name="KIT 1",
        source_file="A4_Test1_T1_Filter1Freq_063_50_Kit.syx",
        payload_fingerprint="a8b78f42f690cd4c",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="127.00",
        primary_raw_value=0x7F,
        kit_name="KIT 1",
        source_file="A4_Test1_T1_Filter1Freq_127_Kit.syx",
        payload_fingerprint="af74207af735fe2c",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=2,
        screen_value="0.00",
        primary_raw_value=0x00,
        kit_name="KIT 1",
        source_file="A4_Test1_T2_Filter1Freq_000_Kit.syx",
        payload_fingerprint="ff5c907bf4a1d2cd",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=2,
        screen_value="63.50",
        primary_raw_value=0x3F,
        kit_name="KIT 1",
        source_file="A4_Test1_T2_Filter1Freq_63_50_Kit.syx",
        payload_fingerprint="beb62ae217dedc30",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=2,
        screen_value="127.00",
        primary_raw_value=0x7F,
        kit_name="KIT 1",
        source_file="A4_Test1_T2_Filter1Freq_127_Kit.syx",
        payload_fingerprint="ecdbd1bcea9dd440",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=3,
        screen_value="0.00",
        primary_raw_value=0x00,
        kit_name="KIT 1",
        source_file="A4_Test1_T3_Filter1Freq_000_Kit.syx",
        payload_fingerprint="9b0044f5fa86ae5d",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=4,
        screen_value="0.00",
        primary_raw_value=0x00,
        kit_name="KIT 1",
        source_file="A4_Test1_T4_Filter1Freq_000_Kit.syx",
        payload_fingerprint="67a43e126f4d0f85",
    ),
)

ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS: Final[Mapping[str, AnalogFourSysexFieldCalibration]] = (
    MappingProxyType(
        {
            "Filter1 Frequency": AnalogFourSysexFieldCalibration(
                parameter="Filter1 Frequency",
                section="FILTERS",
                status=A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED,
                screen_min="0.00",
                screen_mid="63.50",
                screen_max="127.00",
                primary_raw_values=_screen_value_map(
                    {
                        "0.00": 0x00,
                        "63.50": 0x3F,
                        "127.00": 0x7F,
                    }
                ),
                track_1_primary_raw_offset=156,
                track_raw_stride=400,
                track_1_raw_group_start=152,
                raw_group_width=8,
                track_1_unpacked_group_start=130,
                unpacked_group_width=10,
                track_unpacked_stride=350,
                evidence=_FILTER1_FREQUENCY_EVIDENCE,
                notes=(
                    "Primary packed byte verified across Track 1 and Track 2 at 0.00, 63.50, 127.00.",
                    "Track 3 and Track 4 zero-value captures confirm the +400 packed-byte stride.",
                    "SysEx checksum trailer bytes must be ignored or recomputed by future writers.",
                ),
            )
        }
    )
)


def analog_four_sysex_calibration_for(parameter: str) -> AnalogFourSysexFieldCalibration:
    """Return promoted A4 SysEx calibration metadata for ``parameter``."""

    try:
        return ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS[parameter]
    except KeyError as exc:
        raise KeyError(f"Unknown Analog Four SysEx calibration: {parameter}") from exc


__all__ = [
    "A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED",
    "A4_SYSEX_CALIBRATION_STATUS_PENDING",
    "ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS",
    "AnalogFourSysexCalibrationEvidence",
    "AnalogFourSysexFieldCalibration",
    "analog_four_sysex_calibration_for",
]
