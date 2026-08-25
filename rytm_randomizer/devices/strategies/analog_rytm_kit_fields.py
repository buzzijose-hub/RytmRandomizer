"""Typed Analog Rytm MKII kit-object views and mapped sound fields.

These copy-on-edit views layer the RIO145 target-unit-return-validated field
map over the repository's canonical saved-kit codec. Unknown bytes remain
untouched. Native pattern classes are intentionally absent because OXI One is
the sole sequencer. This module performs no SysEx framing and no hardware I/O.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import IntEnum
from typing import Final

from ...data.analog_rytm_kit_fields import (
    RYTM_FX_OFFSETS,
    RYTM_MACHINE_PARAMETER_NAMES,
    RYTM_SOUND_NAME_OFFSET,
    RYTM_SOUND_NAME_STORAGE_LENGTH,
    RYTM_SOUND_NAME_VISIBLE_LENGTH,
    RYTM_SOUND_U7_FIELDS,
)
from ...data.analog_rytm_kit_layout import (
    RYTM_KIT_NAME_LENGTH,
    RYTM_KIT_NAME_OFFSET,
    RYTM_KIT_NAME_VISIBLE_LENGTH,
    RYTM_KIT_RAW_SIZE,
    RYTM_KIT_TRACK_SOUND_SIZE,
    RYTM_KIT_TRACKS_OFFSET,
    RYTM_SOUND_MACHINE_TYPE_OFFSET,
)
from .elektron_kit_common import (
    ElektronKitFieldError,
    read_fixed_width_ascii,
    write_fixed_width_ascii,
)

RYTM_KIT_SIZE = RYTM_KIT_RAW_SIZE
RYTM_KIT_TRACKS_START = RYTM_KIT_TRACKS_OFFSET
RYTM_SOUND_SIZE = RYTM_KIT_TRACK_SOUND_SIZE


def _check_rytm_u7(value: int, label: str = "value") -> int:
    if not 0 <= value <= 127:
        raise ElektronKitFieldError(f"{label} must be in 0..127, got {value}")
    return value


def _encode_bipolar(value: int, *, minimum: int = -64, maximum: int = 63) -> int:
    if not minimum <= value <= maximum:
        raise ElektronKitFieldError(f"bipolar value must be in {minimum}..{maximum}, got {value}")
    return value + 64


def _decode_bipolar(raw: int) -> int:
    return raw - 64


def _read_u16_be(data: bytearray | bytes, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


def _write_u16_be(data: bytearray, offset: int, value: int) -> None:
    if not 0 <= value <= 0xFFFF:
        raise ElektronKitFieldError(f"16-bit value must be in 0..65535, got {value}")
    data[offset] = (value >> 8) & 0xFF
    data[offset + 1] = value & 0xFF


class RytmMachine(IntEnum):
    BD_HARD = 0
    BD_CLASSIC = 1
    SD_HARD = 2
    SD_CLASSIC = 3
    RS_HARD = 4
    RS_CLASSIC = 5
    CP_CLASSIC = 6
    BT_CLASSIC = 7
    XT_CLASSIC = 8
    CH_CLASSIC = 9
    OH_CLASSIC = 10
    CY_CLASSIC = 11
    CB_CLASSIC = 12
    BD_FM = 13
    SD_FM = 14
    UT_NOISE = 15
    UT_IMPULSE = 16
    CH_METALLIC = 17
    OH_METALLIC = 18
    CY_METALLIC = 19
    CB_METALLIC = 20
    BD_PLASTIC = 21
    BD_SILKY = 22
    SD_NATURAL = 23
    HH_BASIC = 24
    CY_RIDE = 25
    BD_SHARP = 26
    DISABLE = 27
    SY_DUAL_VCO = 28
    SY_CHIP = 29
    BD_ACOUSTIC = 30
    SD_ACOUSTIC = 31
    SY_RAW = 32
    HH_LAB = 33


class RytmFilterType(IntEnum):
    LP2 = 0
    LP1 = 1
    BP = 2
    HP1 = 3
    HP2 = 4
    BS = 5
    PK = 6


class RytmLfoWave(IntEnum):
    TRI = 0
    SIN = 1
    SQR = 2
    SAW = 3
    EXP = 4
    RMP = 5
    RND = 6


class RytmLfoMode(IntEnum):
    FREE = 0
    TRIG = 1
    HOLD = 2
    ONE = 3
    HALF = 4


class RytmLfoMultiplier(IntEnum):
    """Analog Rytm's 24 LFO multiplier choices.

    The first twelve follow tempo. The dotted/free group is represented by the
    second twelve values exactly as stored in the kit object.
    """

    X1 = 0x00
    X2 = 0x01
    X4 = 0x02
    X8 = 0x03
    X16 = 0x04
    X32 = 0x05
    X64 = 0x06
    X128 = 0x07
    X256 = 0x08
    X512 = 0x09
    X1K = 0x0A
    X2K = 0x0B
    DOT_1 = 0x0C
    DOT_2 = 0x0D
    DOT_4 = 0x0E
    DOT_8 = 0x0F
    DOT_16 = 0x10
    DOT_32 = 0x11
    DOT_64 = 0x12
    DOT_128 = 0x13
    DOT_256 = 0x14
    DOT_512 = 0x15
    DOT_1K = 0x16
    DOT_2K = 0x17


class RytmLfoDestination(IntEnum):
    SYNTH_PARAM_1 = 0
    SYNTH_PARAM_2 = 1
    SYNTH_PARAM_3 = 2
    SYNTH_PARAM_4 = 3
    SYNTH_PARAM_5 = 4
    SYNTH_PARAM_6 = 5
    SYNTH_PARAM_7 = 6
    SYNTH_PARAM_8 = 7
    SAMPLE_TUNE = 8
    SAMPLE_FINE = 9
    SAMPLE_SLOT = 10
    SAMPLE_BIT_REDUCTION = 11
    SAMPLE_START = 12
    SAMPLE_END = 13
    SAMPLE_LOOP = 14
    SAMPLE_LEVEL = 15
    FILTER_ATTACK = 16
    FILTER_SUSTAIN = 17
    FILTER_DECAY = 18
    FILTER_RELEASE = 19
    FILTER_FREQUENCY = 20
    FILTER_RESONANCE = 21
    FILTER_ENV_DEPTH = 23
    AMP_ATTACK = 24
    AMP_HOLD = 25
    AMP_DECAY = 26
    AMP_OVERDRIVE = 27
    AMP_DELAY_SEND = 28
    AMP_REVERB_SEND = 29
    AMP_PAN = 30
    AMP_VOLUME = 31
    AMP_ACCENT = 32
    NONE = 41


class RytmFxLfoDestination(IntEnum):
    DELAY_TIME = 0
    DELAY_PINGPONG = 1
    DELAY_WIDTH = 2
    DELAY_FEEDBACK = 3
    DELAY_HPF = 4
    DELAY_LPF = 5
    DELAY_REVERB_SEND = 6
    DELAY_VOLUME = 7
    DELAY_OVERDRIVE = 8
    REVERB_PREDELAY = 10
    REVERB_DECAY = 11
    REVERB_SHELVING_FREQUENCY = 12
    REVERB_SHELVING_GAIN = 13
    REVERB_HPF = 14
    REVERB_LPF = 15
    REVERB_VOLUME = 16
    DISTORTION_AMOUNT = 18
    DISTORTION_SYMMETRY = 19
    COMPRESSOR_THRESHOLD = 21
    COMPRESSOR_ATTACK = 22
    COMPRESSOR_RELEASE = 23
    COMPRESSOR_RATIO = 24
    COMPRESSOR_SIDECHAIN_EQ = 25
    COMPRESSOR_MAKEUP_GAIN = 26
    COMPRESSOR_MIX = 27
    COMPRESSOR_VOLUME = 28
    NONE = 37


RYTM_MOD_DEPTH_ZERO: Final[int] = 0x4000
RYTM_MOD_DEPTH_UNITS_PER_DISPLAY: Final[int] = 0x0080


def encode_rytm_mod_depth(value: float) -> int:
    """Encode a displayed Rytm LFO depth into the native centered word.

    The target-unit initialized dump uses 0x4000 for zero. The same Elektron
    high-resolution representation was confirmed on the companion Analog Four
    by controlled hardware captures. Until a dedicated Rytm +/-1 capture is
    made, generated files are explicitly marked experimental and return-tested.
    """

    scaled = value * RYTM_MOD_DEPTH_UNITS_PER_DISPLAY
    rounded = int(round(scaled))
    if abs(scaled - rounded) > 1e-9:
        raise ElektronKitFieldError("Rytm modulation depth must be representable in 1/128 steps")
    raw = RYTM_MOD_DEPTH_ZERO + rounded
    if not 0 <= raw <= 0x7FFF:
        raise ElektronKitFieldError("Rytm modulation depth is outside the native range")
    return raw


def decode_rytm_mod_depth(raw: int) -> float:
    if not 0 <= raw <= 0x7FFF:
        raise ElektronKitFieldError("raw Rytm modulation depth must be in 0x0000..0x7FFF")
    return (raw - RYTM_MOD_DEPTH_ZERO) / RYTM_MOD_DEPTH_UNITS_PER_DISPLAY


@dataclass(slots=True)
class RytmSound:
    _data: bytearray

    SIGNATURE = bytes.fromhex("be ef ba ce")
    NAME_OFFSET = RYTM_SOUND_NAME_OFFSET
    NAME_LENGTH = RYTM_SOUND_NAME_STORAGE_LENGTH
    NAME_VISIBLE_LENGTH = RYTM_SOUND_NAME_VISIBLE_LENGTH
    MACHINE_PARAM_OFFSET = 0x1C

    def __post_init__(self) -> None:
        if len(self._data) != RYTM_SOUND_SIZE:
            raise ElektronKitFieldError(f"Rytm sound block must be {RYTM_SOUND_SIZE} bytes")
        if bytes(self._data[:4]) != self.SIGNATURE:
            raise ElektronKitFieldError(
                f"Unexpected Rytm sound signature {self._data[:4].hex(' ')}"
            )

    @classmethod
    def from_bytes(cls, data: bytes | bytearray | memoryview) -> RytmSound:
        return cls(bytearray(data))

    def to_bytes(self) -> bytes:
        return bytes(self._data)

    @property
    def name(self) -> str:
        return read_fixed_width_ascii(self._data, offset=self.NAME_OFFSET, length=self.NAME_LENGTH)

    @name.setter
    def name(self, value: str) -> None:
        write_fixed_width_ascii(
            self._data,
            offset=self.NAME_OFFSET,
            storage_length=self.NAME_LENGTH,
            visible_length=self.NAME_VISIBLE_LENGTH,
            value=value,
            nul_terminated=True,
        )

    @property
    def machine(self) -> RytmMachine:
        try:
            return RytmMachine(self._data[RYTM_SOUND_MACHINE_TYPE_OFFSET])
        except ValueError as exc:
            raise ElektronKitFieldError(
                "unknown Rytm machine value " f"{self._data[RYTM_SOUND_MACHINE_TYPE_OFFSET]}"
            ) from exc

    @machine.setter
    def machine(self, value: RytmMachine | int) -> None:
        try:
            machine = RytmMachine(value)
        except ValueError as exc:
            raise ElektronKitFieldError(f"unknown Rytm machine value {value}") from exc
        self._data[RYTM_SOUND_MACHINE_TYPE_OFFSET] = int(machine)

    def machine_parameter_name(self, index: int) -> str | None:
        if not 1 <= index <= 8:
            raise ElektronKitFieldError("machine parameter index must be 1..8")
        names = RYTM_MACHINE_PARAMETER_NAMES.get(int(self.machine))
        return names[index - 1] if names else None

    def get_machine_parameter_raw16(self, index: int) -> int:
        if not 1 <= index <= 8:
            raise ElektronKitFieldError("machine parameter index must be 1..8")
        return _read_u16_be(self._data, self.MACHINE_PARAM_OFFSET + (index - 1) * 2)

    def set_machine_parameter_raw16(self, index: int, value: int) -> None:
        if not 1 <= index <= 8:
            raise ElektronKitFieldError("machine parameter index must be 1..8")
        _write_u16_be(self._data, self.MACHINE_PARAM_OFFSET + (index - 1) * 2, value)

    def get_machine_parameter_u7(self, index: int) -> int:
        return self._data[self.MACHINE_PARAM_OFFSET + (index - 1) * 2]

    def set_machine_parameter_u7(self, index: int, value: int, *, clear_lsb: bool = True) -> None:
        _check_rytm_u7(value)
        offset = self.MACHINE_PARAM_OFFSET + (index - 1) * 2
        self._data[offset] = value
        if clear_lsb:
            self._data[offset + 1] = 0

    def get_machine_parameter_bipolar(self, index: int) -> int:
        return _decode_bipolar(self.get_machine_parameter_u7(index))

    def set_machine_parameter_bipolar(self, index: int, value: int) -> None:
        self.set_machine_parameter_u7(index, _encode_bipolar(value))

    # General sound page fields. These are the high/display byte unless noted.
    def get_u7(self, field: str) -> int:
        try:
            return self._data[RYTM_SOUND_U7_FIELDS[field]]
        except KeyError as exc:
            raise ElektronKitFieldError(f"unknown Rytm sound field {field!r}") from exc

    def set_u7(self, field: str, value: int, *, clear_lsb: bool = True) -> None:
        _check_rytm_u7(value, field)
        try:
            offset = RYTM_SOUND_U7_FIELDS[field]
        except KeyError as exc:
            raise ElektronKitFieldError(f"unknown Rytm sound field {field!r}") from exc
        self._data[offset] = value
        if clear_lsb and offset % 2 == 0 and offset + 1 < len(self._data):
            self._data[offset + 1] = 0

    @classmethod
    def u7_field_offset(cls, field: str) -> int:
        """Return the verified payload offset for a named 7-bit field."""

        try:
            return RYTM_SOUND_U7_FIELDS[field]
        except KeyError as exc:
            raise ElektronKitFieldError(f"unknown Rytm sound field {field!r}") from exc

    def get_bipolar(self, field: str) -> int:
        return _decode_bipolar(self.get_u7(field))

    def set_bipolar(self, field: str, value: int) -> None:
        self.set_u7(field, _encode_bipolar(value))

    @property
    def sample_start_raw16(self) -> int:
        return _read_u16_be(self._data, 0x34)

    @sample_start_raw16.setter
    def sample_start_raw16(self, value: int) -> None:
        _write_u16_be(self._data, 0x34, value)

    @property
    def sample_end_raw16(self) -> int:
        return _read_u16_be(self._data, 0x36)

    @sample_end_raw16.setter
    def sample_end_raw16(self, value: int) -> None:
        _write_u16_be(self._data, 0x36, value)

    @property
    def lfo_depth_raw16(self) -> int:
        return _read_u16_be(self._data, 0x6C)

    @lfo_depth_raw16.setter
    def lfo_depth_raw16(self, value: int) -> None:
        _write_u16_be(self._data, 0x6C, value)

    @property
    def lfo_depth(self) -> float:
        return decode_rytm_mod_depth(self.lfo_depth_raw16)

    @lfo_depth.setter
    def lfo_depth(self, value: float) -> None:
        self.lfo_depth_raw16 = encode_rytm_mod_depth(value)


@dataclass(slots=True)
class RytmKit:
    _data: bytearray

    NAME_OFFSET = RYTM_KIT_NAME_OFFSET
    NAME_LENGTH = RYTM_KIT_NAME_LENGTH
    NAME_VISIBLE_LENGTH = RYTM_KIT_NAME_VISIBLE_LENGTH
    TRACK_LEVELS_OFFSET = 0x14

    def __post_init__(self) -> None:
        if len(self._data) != RYTM_KIT_SIZE:
            raise ElektronKitFieldError(
                f"Rytm kit object must be {RYTM_KIT_SIZE} bytes, got {len(self._data)}"
            )

    @classmethod
    def from_bytes(cls, data: bytes | bytearray | memoryview) -> RytmKit:
        return cls(bytearray(data))

    def to_bytes(self) -> bytes:
        return bytes(self._data)

    @property
    def name(self) -> str:
        return read_fixed_width_ascii(self._data, offset=self.NAME_OFFSET, length=self.NAME_LENGTH)

    @name.setter
    def name(self, value: str) -> None:
        write_fixed_width_ascii(
            self._data,
            offset=self.NAME_OFFSET,
            storage_length=self.NAME_LENGTH,
            visible_length=self.NAME_VISIBLE_LENGTH,
            value=value,
            nul_terminated=True,
        )

    def track_level(self, track_index: int) -> int:
        if not 0 <= track_index < 13:
            raise ElektronKitFieldError("track index must be 0..12 (12 is FX)")
        return self._data[self.TRACK_LEVELS_OFFSET + track_index * 2]

    def set_track_level(self, track_index: int, value: int) -> None:
        _check_rytm_u7(value, "track level")
        if not 0 <= track_index < 13:
            raise ElektronKitFieldError("track index must be 0..12 (12 is FX)")
        offset = self.TRACK_LEVELS_OFFSET + track_index * 2
        self._data[offset] = value
        self._data[offset + 1] = 0

    def sound(self, track_index: int) -> RytmSound:
        if not 0 <= track_index < 12:
            raise ElektronKitFieldError("drum track index must be 0..11")
        start = RYTM_KIT_TRACKS_START + track_index * RYTM_SOUND_SIZE
        return RytmSound.from_bytes(self._data[start : start + RYTM_SOUND_SIZE])

    def replace_sound(self, track_index: int, sound: RytmSound) -> None:
        if not 0 <= track_index < 12:
            raise ElektronKitFieldError("drum track index must be 0..11")
        start = RYTM_KIT_TRACKS_START + track_index * RYTM_SOUND_SIZE
        self._data[start : start + RYTM_SOUND_SIZE] = sound.to_bytes()

    def iter_sounds(self) -> Iterator[RytmSound]:
        for track_index in range(12):
            yield self.sound(track_index)

    def get_fx_u7(self, field: str) -> int:
        try:
            return self._data[RYTM_FX_OFFSETS[field]]
        except KeyError as exc:
            raise ElektronKitFieldError(f"unknown Rytm FX field {field!r}") from exc

    def set_fx_u7(self, field: str, value: int, *, clear_lsb: bool = True) -> None:
        _check_rytm_u7(value, field)
        try:
            offset = RYTM_FX_OFFSETS[field]
        except KeyError as exc:
            raise ElektronKitFieldError(f"unknown Rytm FX field {field!r}") from exc
        self._data[offset] = value
        if clear_lsb:
            self._data[offset + 1] = 0

    @classmethod
    def fx_field_offset(cls, field: str) -> int:
        """Return the verified payload offset for a named FX field."""

        try:
            return RYTM_FX_OFFSETS[field]
        except KeyError as exc:
            raise ElektronKitFieldError(f"unknown Rytm FX field {field!r}") from exc

    def get_fx_bipolar(self, field: str) -> int:
        return _decode_bipolar(self.get_fx_u7(field))

    def set_fx_bipolar(self, field: str, value: int) -> None:
        self.set_fx_u7(field, _encode_bipolar(value))

    @property
    def fx_lfo_depth_raw16(self) -> int:
        return _read_u16_be(self._data, 0x0812)

    @fx_lfo_depth_raw16.setter
    def fx_lfo_depth_raw16(self, value: int) -> None:
        _write_u16_be(self._data, 0x0812, value)

    @property
    def fx_lfo_depth(self) -> float:
        return decode_rytm_mod_depth(self.fx_lfo_depth_raw16)

    @fx_lfo_depth.setter
    def fx_lfo_depth(self, value: float) -> None:
        self.fx_lfo_depth_raw16 = encode_rytm_mod_depth(value)
