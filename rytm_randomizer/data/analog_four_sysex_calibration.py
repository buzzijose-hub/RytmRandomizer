"""Analog Four MKII SysEx calibration and write-validation facts.

The facts in this module come from passive, operator-supplied kit exports.
They are data only: no MIDI ports are opened, no SysEx is written, and no
hardware state is mutated.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, cast

from .analog_four_kit_fields import (
    A4_FIXED_8_8_ENCODING,
    A4_FIXED_8_8_RAW_MAX,
    A4_FIXED_8_8_SCALE,
    A4_FIXED_8_8_WIDTH,
    A4_TRACK_OFFSETS,
    A4_TWO_BYTE_FIELDS,
    format_a4_fixed_8_8,
    parse_a4_fixed_8_8,
)
from .analog_four_saved_kit_layout import (
    A4_KIT_OBJECT_TRACK_SOUND_SIZE,
    A4_KIT_OBJECT_TRACKS_OFFSET,
    A4_PACKED_PAYLOAD_OFFSET,
)

A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED: Final[str] = "candidate-promoted"
A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED: Final[str] = "hardware-write-validated"
A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED: Final[str] = (
    "offline-captured-kit-mutation-validated"
)
A4_SYSEX_CALIBRATION_STATUS_PENDING: Final[str] = "pending"

A4_SYNTH_TRACK_MIN: Final[int] = 1
A4_SYNTH_TRACK_MAX: Final[int] = 4
A4_FILTER1_FREQUENCY_PARAMETER: Final[str] = "Filter1 Frequency"
A4_FILTER2_RESONANCE_PARAMETER: Final[str] = "Filter2 Resonance"


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
    """A4 SysEx field location with its current promotion status."""

    parameter: str
    section: str
    status: str
    screen_min: str
    screen_mid: str
    screen_max: str
    primary_raw_values: Mapping[str, int]
    allow_uncaptured_integer_values: bool
    track_1_primary_raw_offset: int
    track_raw_stride: int
    track_1_raw_group_start: int
    raw_group_width: int
    track_1_unpacked_group_start: int
    unpacked_group_width: int
    track_unpacked_stride: int
    evidence: tuple[AnalogFourSysexCalibrationEvidence, ...]
    notes: tuple[str, ...]
    native_field: str | None = None
    native_encoding: str = A4_FIXED_8_8_ENCODING
    native_width: int = A4_FIXED_8_8_WIDTH
    native_raw_min: int = 0
    native_raw_max: int = A4_FIXED_8_8_RAW_MAX
    native_scale: int = A4_FIXED_8_8_SCALE

    def _validate_native_layout(self) -> str:
        if self.native_field is None or self.native_field not in A4_TWO_BYTE_FIELDS:
            raise ValueError(f"{self.parameter} has no calibrated native fixed-point field")
        native_numbers = cast(
            tuple[object, ...],
            (
                self.native_width,
                self.native_scale,
                self.native_raw_min,
                self.native_raw_max,
                self.track_1_primary_raw_offset,
                self.track_raw_stride,
                self.track_unpacked_stride,
            ),
        )
        if (
            self.native_encoding != A4_FIXED_8_8_ENCODING
            or self.native_width != A4_FIXED_8_8_WIDTH
            or self.native_scale != A4_FIXED_8_8_SCALE
            or any(
                isinstance(value, bool) or not isinstance(value, int) for value in native_numbers
            )
            or not 0 <= self.native_raw_min <= self.native_raw_max <= A4_FIXED_8_8_RAW_MAX
        ):
            raise ValueError(f"{self.parameter} native fixed-point calibration is invalid")
        if (
            parse_a4_fixed_8_8(self.screen_min) != self.native_raw_min
            or parse_a4_fixed_8_8(self.screen_max) != self.native_raw_max
        ):
            raise ValueError(
                f"{self.parameter} native range disagrees with calibrated screen bounds"
            )
        return self.native_field

    def native_offset_for_track(self, track: int) -> int:
        """Resolve calibrated packed addressing and reject drift from the field map."""

        field_name = self._validate_native_layout()
        packed_offset = self.primary_raw_offset_for_track(track)
        group, position = divmod(packed_offset - A4_PACKED_PAYLOAD_OFFSET, 8)
        native_offset = group * 7 + position - 1
        mapped_offset = (
            A4_KIT_OBJECT_TRACKS_OFFSET
            + (track - 1) * A4_KIT_OBJECT_TRACK_SOUND_SIZE
            + A4_TRACK_OFFSETS[field_name]
        )
        if (
            position == 0
            or native_offset != mapped_offset
            or self.track_unpacked_stride != A4_KIT_OBJECT_TRACK_SOUND_SIZE
            or self.track_raw_stride != A4_KIT_OBJECT_TRACK_SOUND_SIZE * 8 // 7
        ):
            raise ValueError(
                f"{self.parameter} calibration offset disagrees with mapped native field"
            )
        return native_offset

    def parse_native_screen_value(self, screen_value: str) -> int:
        """Parse a calibrated fixed-point value exactly, without Decimal rounding."""

        self._validate_native_layout()
        return parse_a4_fixed_8_8(
            screen_value, minimum=self.native_raw_min, maximum=self.native_raw_max
        )

    def format_native_screen_value(self, raw: object) -> str:
        """Format one calibrated native value with the shared exact field codec."""

        self._validate_native_layout()
        return format_a4_fixed_8_8(raw, minimum=self.native_raw_min, maximum=self.native_raw_max)

    @property
    def hardware_send_validated(self) -> bool:
        """Whether operator-confirmed generated bytes were received by hardware."""

        return self.status == A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED

    @property
    def offline_saved_kit_mutation_validated(self) -> bool:
        """Whether captured bytes authorize deterministic local-file mutation only."""

        return self.status == A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED

    def primary_raw_value_for_screen(self, screen_value: str) -> int:
        """Return the calibrated low-seven-bit value for a screen value."""

        captured = self.primary_raw_values.get(screen_value)
        if captured is not None:
            return captured
        if self.allow_uncaptured_integer_values:
            try:
                parsed = int(screen_value)
            except ValueError as exc:
                raise ValueError(
                    f"unsupported screen value {screen_value!r} for {self.parameter}"
                ) from exc
            if str(parsed) == screen_value and 0 <= parsed <= 0x7F:
                return parsed
        raise ValueError(f"unsupported screen value {screen_value!r} for {self.parameter}")

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


@dataclass(frozen=True)
class AnalogFourSysexWriteValidationEvidence:
    """One operator-confirmed A4 generated-kit receive observation."""

    parameter: str
    generated_file: str
    generated_sha256: str
    expected_track_values: tuple[tuple[int, str], ...]
    matched_reference_file: str | None
    operator_confirmed: bool
    notes: tuple[str, ...]


def _validate_a4_sysex_calibration_track(track: object) -> None:
    if (
        isinstance(track, bool)
        or not isinstance(track, int)
        or not A4_SYNTH_TRACK_MIN <= track <= A4_SYNTH_TRACK_MAX
    ):
        raise ValueError("track must be in 1..4")


def _screen_value_map(values: Mapping[str, int]) -> Mapping[str, int]:
    return MappingProxyType(dict(values))


_FILTER1_FREQUENCY_EVIDENCE: Final[tuple[AnalogFourSysexCalibrationEvidence, ...]] = (
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="0.00",
        primary_raw_value=0x00,
        kit_name="KIT 20",
        source_file="filter1_freq_000_expected.syx",
        payload_fingerprint="3834839047939f0a",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="63.50",
        primary_raw_value=0x3F,
        kit_name="KIT 20",
        source_file="filter1_freq_063_50_expected.syx",
        payload_fingerprint="89569c28ad1c6d3a",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="127.00",
        primary_raw_value=0x7F,
        kit_name="KIT 20",
        source_file="filter1_freq_127_source.syx",
        payload_fingerprint="ca77b13a6131a513",
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

_FILTER1_RESONANCE_EVIDENCE: Final[tuple[AnalogFourSysexCalibrationEvidence, ...]] = (
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="0",
        primary_raw_value=0x00,
        kit_name="KIT 1",
        source_file="A4_Test1_T1_Filter1Res_000_Kit.syx",
        payload_fingerprint="9a5da29b4ad37008",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="20",
        primary_raw_value=0x14,
        kit_name="KIT 1",
        source_file="A4_Test1_T1_Filter1Res_20_Kit.syx",
        payload_fingerprint="67a43e126f4d0f85",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="127",
        primary_raw_value=0x7F,
        kit_name="KIT 1",
        source_file="A4_Test1_T1_Filter1Res_127_Kit.syx",
        payload_fingerprint="9f4535115136f4ec",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=2,
        screen_value="0",
        primary_raw_value=0x00,
        kit_name="KIT 1",
        source_file="A4_Test1_T2_Filter1Res_000_Kit.syx",
        payload_fingerprint="950e8f5b65253fbb",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=3,
        screen_value="0",
        primary_raw_value=0x00,
        kit_name="KIT 1",
        source_file="A4_Test1_T3_Filter1Res_000_Kit.syx",
        payload_fingerprint="cc64427123887f89",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=4,
        screen_value="0",
        primary_raw_value=0x00,
        kit_name="KIT 1",
        source_file="A4_Test1_T4_Filter1Res_000_Kit.syx",
        payload_fingerprint="6818388c34db01b9",
    ),
)

_FILTER2_FREQUENCY_EVIDENCE: Final[tuple[AnalogFourSysexCalibrationEvidence, ...]] = (
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="0.00",
        primary_raw_value=0x00,
        kit_name="KIT 1",
        source_file="A4_Test1_T1_Filter2Freq_000_Kit.syx",
        payload_fingerprint="6818388c34db01b9",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="63.50",
        primary_raw_value=0x3F,
        kit_name="KIT 1",
        source_file="A4_Test1_T1_Filter2Freq_063_50_Kit.syx",
        payload_fingerprint="82c03587679c6ddc",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="127.00",
        primary_raw_value=0x7F,
        kit_name="KIT 1",
        source_file="A4_Test1_T1_Filter2Freq_127_Kit.syx",
        payload_fingerprint="9497709f8562f1ef",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=2,
        screen_value="127.00",
        primary_raw_value=0x7F,
        kit_name="KIT 1",
        source_file="A4_Test1_T2_Filter2Freq_127_Kit.syx",
        payload_fingerprint="1f15e21e281ce000",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=3,
        screen_value="127.00",
        primary_raw_value=0x7F,
        kit_name="KIT 1",
        source_file="A4_Test1_T3_Filter2Freq_127_Kit.syx",
        payload_fingerprint="fabeab5b95ed53e0",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=4,
        screen_value="127.00",
        primary_raw_value=0x7F,
        kit_name="KIT 1",
        source_file="A4_Test1_T4_Filter2Freq_127_Kit.syx",
        payload_fingerprint="a52174e811260978",
    ),
)

_FILTER2_RESONANCE_EVIDENCE: Final[tuple[AnalogFourSysexCalibrationEvidence, ...]] = (
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="0",
        primary_raw_value=0x00,
        kit_name="KIT 1",
        source_file="A4_Test1_T1_Filter2Res_000_Kit.syx",
        payload_fingerprint="4ec91a917cfaeab0",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="20",
        primary_raw_value=0x14,
        kit_name="KIT 1",
        source_file="A4_Test1_T1_Filter2Res_020_Kit.syx",
        payload_fingerprint="ccf0acb6bb32e1b3",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=1,
        screen_value="127",
        primary_raw_value=0x7F,
        kit_name="KIT 1",
        source_file="A4_Test1_T1_Filter2Res_127_Kit.syx",
        payload_fingerprint="c842a01f81f1eaa8",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=2,
        screen_value="127",
        primary_raw_value=0x7F,
        kit_name="KIT 1",
        source_file="A4_Test1_T2_Filter2Res_127_Kit.syx",
        payload_fingerprint="8de0161d9ffd0798",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=3,
        screen_value="127",
        primary_raw_value=0x7F,
        kit_name="KIT 1",
        source_file="A4_Test1_T3_Filter2Res_127_Kit.syx",
        payload_fingerprint="640e4443acf81ee4",
    ),
    AnalogFourSysexCalibrationEvidence(
        track=4,
        screen_value="127",
        primary_raw_value=0x7F,
        kit_name="KIT 1",
        source_file="A4_Test1_T4_Filter2Res_127_Kit.syx",
        payload_fingerprint="1f2160541d4204b0",
    ),
)

ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS: Final[Mapping[str, AnalogFourSysexFieldCalibration]] = (
    MappingProxyType(
        {
            A4_FILTER1_FREQUENCY_PARAMETER: AnalogFourSysexFieldCalibration(
                parameter=A4_FILTER1_FREQUENCY_PARAMETER,
                section="FILTERS",
                status=(A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED),
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
                allow_uncaptured_integer_values=False,
                track_1_primary_raw_offset=156,
                track_raw_stride=400,
                track_1_raw_group_start=152,
                raw_group_width=8,
                track_1_unpacked_group_start=130,
                unpacked_group_width=10,
                track_unpacked_stride=A4_KIT_OBJECT_TRACK_SOUND_SIZE,
                native_field="filter1_frequency",
                native_raw_max=0x7F00,
                evidence=_FILTER1_FREQUENCY_EVIDENCE,
                notes=(
                    "The 2026-08-28 KIT 20 captures isolate native bytes 128:130 as unsigned big-endian Q8.8.",
                    "Captured 0.00, 63.50, and 127.00 frames round-trip byte-identically through the canonical codec.",
                    "Track 3 and Track 4 zero-value captures confirm the +400 packed-byte stride.",
                    "Local saved-kit rendering is validated; generated bytes have not been received by hardware.",
                ),
            ),
            "Filter1 Resonance": AnalogFourSysexFieldCalibration(
                parameter="Filter1 Resonance",
                section="FILTERS",
                status=A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED,
                screen_min="0",
                screen_mid="20",
                screen_max="127",
                primary_raw_values=_screen_value_map(
                    {
                        "0": 0x00,
                        "20": 0x14,
                        "127": 0x7F,
                    }
                ),
                allow_uncaptured_integer_values=True,
                track_1_primary_raw_offset=158,
                track_raw_stride=400,
                track_1_raw_group_start=156,
                raw_group_width=8,
                track_1_unpacked_group_start=133,
                unpacked_group_width=7,
                track_unpacked_stride=350,
                evidence=_FILTER1_RESONANCE_EVIDENCE,
                notes=(
                    "Primary packed data byte verified on Track 1 at 0, 20, and 127.",
                    "Track 2, Track 3, and Track 4 zero-value captures confirm the +400 packed-byte stride.",
                    "The decoded byte appears as 0x80 plus the screen value when Filter1 Frequency leaves the shared 7-bit group header set.",
                    "SysEx checksum trailer bytes must be ignored or recomputed by future writers.",
                ),
            ),
            "Filter2 Frequency": AnalogFourSysexFieldCalibration(
                parameter="Filter2 Frequency",
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
                allow_uncaptured_integer_values=False,
                track_1_primary_raw_offset=167,
                track_raw_stride=400,
                track_1_raw_group_start=160,
                raw_group_width=12,
                track_1_unpacked_group_start=137,
                unpacked_group_width=7,
                track_unpacked_stride=350,
                evidence=_FILTER2_FREQUENCY_EVIDENCE,
                notes=(
                    "Primary packed data byte verified on Track 1 at 0.00, 63.50, and 127.00.",
                    "Track 2, Track 3, and Track 4 127.00 captures confirm the +400 packed-byte stride.",
                    "Neighboring packed bytes move with Elektron high-bit grouping; the direct screen value appears at packed offset 167 and unpacked offset 142.",
                    "SysEx checksum trailer bytes must be ignored or recomputed by future writers.",
                ),
            ),
            A4_FILTER2_RESONANCE_PARAMETER: AnalogFourSysexFieldCalibration(
                parameter=A4_FILTER2_RESONANCE_PARAMETER,
                section="FILTERS",
                status=A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED,
                screen_min="0",
                screen_mid="20",
                screen_max="127",
                primary_raw_values=_screen_value_map(
                    {
                        "0": 0x00,
                        "20": 0x14,
                        "127": 0x7F,
                    }
                ),
                allow_uncaptured_integer_values=True,
                track_1_primary_raw_offset=170,
                track_raw_stride=400,
                track_1_raw_group_start=168,
                raw_group_width=8,
                track_1_unpacked_group_start=144,
                unpacked_group_width=7,
                track_unpacked_stride=350,
                evidence=_FILTER2_RESONANCE_EVIDENCE,
                notes=(
                    "Primary packed data byte verified on Track 1 at 0, 20, and 127.",
                    "Track 2, Track 3, and Track 4 127 captures confirm the +400 packed-byte stride.",
                    "The direct screen value appears at packed offset 170 and unpacked offset 145.",
                    "Generated saved-kit writes were received and verified on hardware for reference, novel, and four-track values.",
                ),
            ),
        }
    )
)

ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS: Final[
    Mapping[str, tuple[AnalogFourSysexWriteValidationEvidence, ...]]
] = MappingProxyType(
    {
        A4_FILTER2_RESONANCE_PARAMETER: (
            AnalogFourSysexWriteValidationEvidence(
                parameter=A4_FILTER2_RESONANCE_PARAMETER,
                generated_file="A4_CODEX_TEST_T1_Filter2Res_127_GENERATED.syx",
                generated_sha256=(
                    "5ebb386677aff324ef96d631e7888a9681caefbd976bdc2eac69b52a0fb0e26b"
                ),
                expected_track_values=((1, "127"),),
                matched_reference_file="A4_Test1_T1_Filter2Res_127_Kit.syx",
                operator_confirmed=True,
                notes=(
                    "Generated frame was byte-identical to the hardware-exported reference.",
                    "Analog Four MKII received the file as KIT 1 and displayed Track 1 value 127.",
                ),
            ),
            AnalogFourSysexWriteValidationEvidence(
                parameter=A4_FILTER2_RESONANCE_PARAMETER,
                generated_file="A4_CODEX_TEST_T1_Filter2Res_064_GENERATED.syx",
                generated_sha256=(
                    "2fee1aa93c98e0221dbe7bac296c51268360c5c61e11c8eea77fd091cbbd94f7"
                ),
                expected_track_values=((1, "64"),),
                matched_reference_file=None,
                operator_confirmed=True,
                notes=(
                    "Novel value 64 was generated without a matching source capture.",
                    "Analog Four MKII received the file as KIT 1 and displayed Track 1 value 64.",
                ),
            ),
            AnalogFourSysexWriteValidationEvidence(
                parameter=A4_FILTER2_RESONANCE_PARAMETER,
                generated_file=("A4_CODEX_TEST_T1-4_Filter2Res_016_048_080_112_GENERATED.syx"),
                generated_sha256=(
                    "0e88aa6f15fd49c36696d5b8e09bda18ce5eeb8562c1a44ce46683c6deef819b"
                ),
                expected_track_values=(
                    (1, "16"),
                    (2, "48"),
                    (3, "80"),
                    (4, "112"),
                ),
                matched_reference_file=None,
                operator_confirmed=True,
                notes=(
                    "One generated frame carried four independent track mutations.",
                    "Analog Four MKII displayed the expected value on every synth track.",
                ),
            ),
        )
    }
)


def analog_four_sysex_calibration_for(parameter: str) -> AnalogFourSysexFieldCalibration:
    """Return A4 calibration metadata for ``parameter``."""

    try:
        return ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS[parameter]
    except KeyError as exc:
        raise KeyError(f"Unknown Analog Four SysEx calibration: {parameter}") from exc


__all__ = [
    "A4_FILTER1_FREQUENCY_PARAMETER",
    "A4_FILTER2_RESONANCE_PARAMETER",
    "A4_SYSEX_CALIBRATION_STATUS_CANDIDATE_PROMOTED",
    "A4_SYSEX_CALIBRATION_STATUS_HARDWARE_WRITE_VALIDATED",
    "A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED",
    "A4_SYSEX_CALIBRATION_STATUS_PENDING",
    "ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS",
    "ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS",
    "AnalogFourSysexCalibrationEvidence",
    "AnalogFourSysexFieldCalibration",
    "AnalogFourSysexWriteValidationEvidence",
    "analog_four_sysex_calibration_for",
]
