"""Typed Analog Four MKII kit-object views and mapped synth-sound fields.

These copy-on-edit views layer the RIO145 target-unit-return-validated field
map over the repository's canonical saved-kit envelope codec. Unknown bytes
remain untouched. This module performs no SysEx framing and no hardware I/O.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from enum import IntEnum
from typing import Final

from ...data.analog_four_saved_kit_layout import (
    A4_KIT_OBJECT_TRACK_SOUND_SIZE,
    A4_KIT_OBJECT_TRACKS_OFFSET,
    A4_SAVED_KIT_OBJECT_SIZE,
)

A4_KIT_TRACKS_START = A4_KIT_OBJECT_TRACKS_OFFSET
A4_SOUND_SIZE = A4_KIT_OBJECT_TRACK_SOUND_SIZE


def _check_u8(value: int, label: str = "value") -> int:
    if not 0 <= value <= 255:
        raise ValueError(f"{label} must be in 0..255, got {value}")
    return value


def _check_a4_u7(value: int, label: str = "value") -> int:
    if not 0 <= value <= 127:
        raise ValueError(f"{label} must be in 0..127, got {value}")
    return value


def encode_bipolar(value: int, *, minimum: int = -64, maximum: int = 63) -> int:
    if not minimum <= value <= maximum:
        raise ValueError(f"bipolar value must be in {minimum}..{maximum}, got {value}")
    return value + 64


def decode_bipolar(value: int) -> int:
    return value - 64


# OSC TUN and FIN are adjacent parts of one centered 16-bit pitch word. One
# coarse semitone is 0x0100 native units. FIN occupies the signed residual
# interval -128..+127 around the nearest coarse semitone; its screen value is
# arithmetic-floor-divided by two. Therefore two neighboring native residuals
# display the same FIN integer. Controlled target-unit captures prove:
#   TUN 0 / FIN +1 -> 0x4003
#   TUN 0 / FIN +2 -> 0x4004
#   TUN 0 / FIN -1 -> 0x3FFE
#   TUN 0 / FIN -2 -> 0x3FFC
# This also reconciles the older public Sound table, whose documented examples
# select the other member of some two-code display buckets. Generation uses the
# canonical even residual 2*n; untouched dumps preserve their exact hidden half
# step.
A4_PITCH_ZERO: Final[int] = 0x4000
A4_PITCH_UNITS_PER_SEMITONE: Final[int] = 0x0100
A4_FINE_NATIVE_MIN: Final[int] = -128
A4_FINE_NATIVE_MAX: Final[int] = 127
A4_FINE_DISPLAY_MIN: Final[int] = -64
A4_FINE_DISPLAY_MAX: Final[int] = 63

# ENV/LFO modulation depths use a signed Q8.7-style representation centered at
# 0x4000: one displayed unit equals 0x0080 native units. Controlled target-unit
# captures prove +1.00 = 0x4080 and -1.00 = 0x3F80.
A4_MOD_DEPTH_ZERO: Final[int] = 0x4000
A4_MOD_DEPTH_UNITS_PER_DISPLAY: Final[int] = 0x0080


def decode_a4_pitch_components(raw: int) -> tuple[int, int, int, int]:
    """Return ``(TUN, FIN, hidden_half_step, native_fine_residual)``.

    The decomposition chooses the nearest coarse semitone so that the residual
    always lies in -128..+127. ``hidden_half_step`` is 0 or 1 and records which
    of the two native values representing the same displayed FIN number was
    present in the source dump.
    """
    if not 0 <= raw <= 0x7FFF:
        raise ValueError("raw oscillator pitch must be in 0x0000..0x7FFF")
    delta = raw - A4_PITCH_ZERO
    tune = math.floor((delta + 128) / A4_PITCH_UNITS_PER_SEMITONE)
    residual = delta - tune * A4_PITCH_UNITS_PER_SEMITONE
    # The floor-based decomposition above proves this range; retain the guard
    # as a backstop if the pitch constants ever change.
    if not A4_FINE_NATIVE_MIN <= residual <= A4_FINE_NATIVE_MAX:  # pragma: no cover
        raise AssertionError(f"pitch decomposition produced invalid residual {residual}")
    fine = residual // 2
    hidden_half_step = residual - fine * 2
    return tune, fine, hidden_half_step, residual


def encode_a4_pitch_raw(tune_semitones: int, fine_value: int, *, hidden_half_step: int = 0) -> int:
    """Encode the OSC TUN/FIN display pair into the native pitch word.

    ``hidden_half_step`` may be 0 or 1. Normal generation uses 0, the canonical
    even representative. Use 1 only when reproducing an observed encoder state
    byte-for-byte.
    """
    if not -64 <= tune_semitones <= 63:
        raise ValueError(f"TUN must be in -64..63, got {tune_semitones}")
    if not A4_FINE_DISPLAY_MIN <= fine_value <= A4_FINE_DISPLAY_MAX:
        raise ValueError(
            f"FIN must be in {A4_FINE_DISPLAY_MIN}..{A4_FINE_DISPLAY_MAX}, got {fine_value}"
        )
    if hidden_half_step not in (0, 1):
        raise ValueError("hidden_half_step must be 0 or 1")
    residual = fine_value * 2 + hidden_half_step
    raw = A4_PITCH_ZERO + tune_semitones * A4_PITCH_UNITS_PER_SEMITONE + residual
    if not 0 <= raw <= 0x7FFF:
        raise ValueError(f"TUN {tune_semitones:+d} / FIN {fine_value:+d} is outside native range")
    return raw


def decode_a4_pitch_semitones(raw: int) -> float:
    if not 0 <= raw <= 0x7FFF:
        raise ValueError("raw oscillator pitch must be in 0x0000..0x7FFF")
    return (raw - A4_PITCH_ZERO) / A4_PITCH_UNITS_PER_SEMITONE


def encode_a4_mod_depth(value: float) -> int:
    """Encode ENV/LFO destination depth in the confirmed native Q8.7 format."""
    if not -128.0 <= value <= 127.9921875:
        raise ValueError("modulation depth must be in -128.0..127.9921875")
    scaled = value * A4_MOD_DEPTH_UNITS_PER_DISPLAY
    rounded = int(round(scaled))
    if not math.isclose(scaled, rounded, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("modulation depth must be representable in 1/128 increments")
    raw = A4_MOD_DEPTH_ZERO + rounded
    # The accepted display range and exact 1/128 quantization prove this range.
    if not 0 <= raw <= 0x7FFF:  # pragma: no cover
        raise ValueError(f"encoded modulation depth is outside native range: 0x{raw:04X}")
    return raw


def decode_a4_mod_depth(raw: int) -> float:
    if not 0 <= raw <= 0x7FFF:
        raise ValueError("raw modulation depth must be in 0x0000..0x7FFF")
    return (raw - A4_MOD_DEPTH_ZERO) / A4_MOD_DEPTH_UNITS_PER_DISPLAY


def wire_address_to_track_raw_offset(address: int) -> int:
    """Translate an older standalone A4 Sound wire address into kit-track raw offset.

    Addresses that point to a 7-bit packing mask have no standalone raw byte and
    raise ValueError. The resulting unpacked index is the offset inside the 350-byte
    track block; this was empirically validated against the user-supplied target-unit kit.
    """
    if address < 10:
        raise ValueError("wire address must point into packed payload at byte 10 or later")
    relative = address - 10
    remainder = relative % 8
    if remainder == 0:
        raise ValueError(f"wire address {address} is a 7-bit packing mask, not a raw field")
    unpacked_index = (relative // 8) * 7 + (remainder - 1)
    raw_offset = unpacked_index
    if not 0 <= raw_offset < A4_SOUND_SIZE:
        raise ValueError(f"translated raw offset {raw_offset} is outside a 350-byte A4 Sound")
    return raw_offset


class A4SyncMode(IntEnum):
    OFF = 0
    OSC1_SYNCS_OSC2 = 1
    OSC2_SYNCS_OSC1 = 2
    METAL = 3


class A4EnvelopeShape(IntEnum):
    LINEAR_LINEAR_CONTINUE = 0
    LINEAR_LINEAR_RESTART = 1
    STANDARD_CONTINUE = 2
    STANDARD_RESTART = 3
    EXP_ATTACK_LINEAR_RELEASE_CONTINUE = 4
    EXP_ATTACK_LINEAR_RELEASE_RESTART = 5
    EXP_ATTACK_EXP_RELEASE_CONTINUE = 6
    EXP_ATTACK_EXP_RELEASE_RESTART = 7
    FULL_ATTACK_LINEAR_RELEASE_CONTINUE = 8
    FULL_ATTACK_LINEAR_RELEASE_RESTART = 9
    FULL_ATTACK_EXP_RELEASE_CONTINUE = 10
    FULL_ATTACK_EXP_RELEASE_RESTART = 11


class A4Portamento(IntEnum):
    OFF = 0
    ON = 1
    LEGATO = 2


class A4Waveform(IntEnum):
    SAW = 0
    TRP = 1
    PULSE = 2
    TRIANGLE = 3
    INPUT_LEFT = 4
    INPUT_RIGHT = 5
    FEEDBACK_OR_NEIGHBOR = 6
    OFF = 7


class A4SubOscillator(IntEnum):
    OFF = 0
    OCTAVE_1 = 1
    OCTAVE_2 = 2
    PULSE_2 = 3
    FIFTH = 4


class A4Filter2Type(IntEnum):
    LP2 = 0
    LP1 = 1
    BP = 2
    HP1 = 3
    HP2 = 4
    BS = 5
    PK = 6


class A4LfoWave(IntEnum):
    TRI = 0
    SIN = 1
    SQR = 2
    SAW = 3
    EXP = 4
    RMP = 5
    RND = 6


class A4LfoMode(IntEnum):
    FREE = 0
    TRIG = 1
    HOLD = 2
    ONE = 3
    HALF = 4


class A4LfoMultiplier(IntEnum):
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
    TRIPLET_1 = 0x18
    TRIPLET_2 = 0x19
    TRIPLET_4 = 0x1A
    TRIPLET_8 = 0x1B
    TRIPLET_16 = 0x1C
    TRIPLET_32 = 0x1D
    TRIPLET_64 = 0x1E
    TRIPLET_128 = 0x1F
    TRIPLET_256 = 0x20
    TRIPLET_512 = 0x21
    TRIPLET_1K = 0x22
    TRIPLET_2K = 0x23


class A4Destination(IntEnum):
    NONE = 0x60
    OSC1_DETUNE = 0x02
    OSC2_DETUNE = 0x03
    OSC1_KEYTRACK = 0x04
    OSC2_KEYTRACK = 0x05
    OSC1_LEVEL = 0x06
    OSC2_LEVEL = 0x07
    OSC1_WAVEFORM = 0x08
    OSC2_WAVEFORM = 0x09
    OSC1_SUB = 0x0A
    OSC2_SUB = 0x0B
    OSC1_PW = 0x0C
    OSC2_PW = 0x0D
    OSC1_PWM_SPEED = 0x0E
    OSC2_PWM_SPEED = 0x0F
    OSC1_PWM_DEPTH = 0x10
    OSC2_PWM_DEPTH = 0x11
    OSC1_PITCH = 0x12
    OSC2_PITCH = 0x13
    BOTH_OSC_PITCH = 0x14
    NOISE_SAMPLE_HOLD = 0x15
    NOISE_FADE = 0x16
    NOISE_LEVEL = 0x17
    OSC1_AM = 0x18
    OSC2_AM = 0x19
    SYNC_MODE = 0x1A
    SYNC_AMOUNT = 0x1B
    BEND_DEPTH = 0x1C
    NOTE_SLIDE_TIME = 0x1D
    VIBRATO_FADE = 0x1F
    VIBRATO_SPEED = 0x20
    VIBRATO_DEPTH = 0x21
    FILTER1_FREQUENCY = 0x22
    FILTER1_RESONANCE = 0x23
    FILTER1_OVERDRIVE = 0x24
    FILTER1_ENV_DEPTH = 0x26
    FILTER2_FREQUENCY = 0x27
    FILTER2_RESONANCE = 0x28
    FILTER2_ENV_DEPTH = 0x2B
    BOTH_FILTER_FREQUENCY = 0x2C
    AMP_CHORUS_SEND = 0x2D
    AMP_DELAY_SEND = 0x2E
    AMP_REVERB_SEND = 0x2F
    AMP_PAN = 0x30
    AMP_VOLUME = 0x31
    AMP_ACCENT = 0x32
    ENVF_ATTACK = 0x33
    ENV2_ATTACK = 0x34
    AMP_ATTACK = 0x35
    ENVF_DECAY = 0x36
    ENV2_DECAY = 0x37
    AMP_DECAY = 0x38
    ENVF_SUSTAIN = 0x39
    ENV2_SUSTAIN = 0x3A
    AMP_SUSTAIN = 0x3B
    ENVF_RELEASE = 0x3C
    ENV2_RELEASE = 0x3D
    AMP_RELEASE = 0x3E
    ENVF_SHAPE = 0x3F
    ENV2_SHAPE = 0x40
    AMP_SHAPE = 0x41
    ENVF_DEPTH_A = 0x48
    ENVF_DEPTH_B = 0x49
    ENV2_DEPTH_A = 0x4A
    ENV2_DEPTH_B = 0x4B
    LFO1_SPEED = 0x4C
    LFO1_MULTIPLIER = 0x4E
    LFO1_FADE = 0x50
    LFO1_PHASE = 0x52
    LFO1_DEPTH_A = 0x5C
    LFO1_DEPTH_B = 0x5D
    OSC1_FREQUENCY = 0x61
    OSC2_FREQUENCY = 0x62
    BOTH_OSC_FREQUENCY = 0x63
    NOISE_COLOR = 0x64


# Public table wire addresses, translated at import time into target-unit track offsets.
_WIRE_ADDRESSES: Final[dict[str, int]] = {
    "osc1_tune": 43,
    "osc1_fine": 44,
    "osc2_tune": 45,
    "osc2_fine": 46,
    "osc1_detune": 47,
    "osc2_detune": 49,
    "osc1_tracking": 52,
    "osc2_tracking": 54,
    "osc1_level": 56,
    "osc2_level": 59,
    "osc1_waveform": 61,
    "osc2_waveform": 63,
    "osc1_sub": 65,
    "osc2_sub": 68,
    "osc1_pw": 70,
    "osc2_pw": 72,
    "osc1_pwm_speed": 75,
    "osc2_pwm_speed": 77,
    "osc1_pwm_depth": 79,
    "osc2_pwm_depth": 81,
    "noise_sample_hold": 91,
    "noise_fade": 93,
    "noise_level": 95,
    "osc1_am": 97,
    "osc2_am": 100,
    "sync_mode": 102,
    "sync_amount": 104,
    "bend_depth": 107,
    "slide_time": 109,
    "osc_retrigger": 111,
    "vibrato_fade": 113,
    "vibrato_speed": 116,
    "vibrato_depth": 118,
    "filter1_frequency": 120,
    "filter1_resonance": 123,
    "filter1_overdrive": 125,
    "filter1_tracking": 127,
    "filter1_env_depth": 129,
    "filter2_frequency": 132,
    "filter2_resonance": 134,
    "filter2_type": 136,
    "filter2_tracking": 139,
    "filter2_env_depth": 141,
    "amp_chorus_send": 145,
    "amp_delay_send": 148,
    "amp_reverb_send": 150,
    "amp_pan": 152,
    "amp_volume": 155,
    "envf_attack": 159,
    "env2_attack": 161,
    "amp_attack": 164,
    "envf_decay": 166,
    "env2_decay": 168,
    "amp_decay": 171,
    "envf_sustain": 173,
    "env2_sustain": 175,
    "amp_sustain": 177,
    "envf_release": 180,
    "env2_release": 182,
    "amp_release": 184,
    "envf_shape": 187,
    "env2_shape": 189,
    "amp_shape": 191,
    "envf_length": 193,
    "env2_length": 196,
    "envf_destination_a": 198,
    "envf_destination_b": 200,
    "env2_destination_a": 203,
    "env2_destination_b": 205,
    "envf_depth_a": 207,
    "envf_depth_a_fraction": 208,
    "envf_depth_b": 209,
    "envf_depth_b_fraction": 211,
    "env2_depth_a": 212,
    "env2_depth_a_fraction": 213,
    "env2_depth_b": 214,
    "env2_depth_b_fraction": 215,
    "lfo1_speed": 216,
    "lfo2_speed": 219,
    "lfo1_multiplier": 221,
    "lfo2_multiplier": 223,
    "lfo1_fade": 225,
    "lfo2_fade": 228,
    "lfo1_phase": 230,
    "lfo2_phase": 232,
    "lfo1_mode": 235,
    "lfo2_mode": 237,
    "lfo1_waveform": 239,
    "lfo2_waveform": 241,
    "lfo1_destination_a": 244,
    "lfo1_destination_b": 246,
    "lfo2_destination_a": 248,
    "lfo2_destination_b": 251,
    "lfo1_depth_a": 253,
    "lfo1_depth_a_fraction": 254,
    "lfo1_depth_b": 255,
    "lfo1_depth_b_fraction": 256,
    "lfo2_depth_a": 257,
    "lfo2_depth_a_fraction": 259,
    "lfo2_depth_b": 260,
    "lfo2_depth_b_fraction": 261,
    "noise_color": 271,
    "oscillator_drift": 280,
    "portamento": 281,
    "legato_mode": 283,
    "filter1_resonance_boost": 285,
}

A4_TRACK_OFFSETS = {
    name: wire_address_to_track_raw_offset(address) for name, address in _WIRE_ADDRESSES.items()
}

# Two-byte 8.8 fixed-point cutoff values begin at these fields.
A4_TWO_BYTE_FIELDS: Final[set[str]] = {"filter1_frequency", "filter2_frequency"}
A4_BIPOLAR_FIELDS: Final[set[str]] = {
    "osc1_detune",
    "osc2_detune",
    "osc1_pw",
    "osc2_pw",
    "noise_fade",
    "noise_color",
    "bend_depth",
    "vibrato_fade",
    "filter1_overdrive",
    "filter1_tracking",
    "filter1_env_depth",
    "filter2_tracking",
    "filter2_env_depth",
    "amp_pan",
    "lfo1_speed",
    "lfo2_speed",
    "lfo1_fade",
    "lfo2_fade",
}

A4_MOD_DEPTH_FIELDS: Final[dict[str, str]] = {
    "envf_depth_a": "envf_depth_a_fraction",
    "envf_depth_b": "envf_depth_b_fraction",
    "env2_depth_a": "env2_depth_a_fraction",
    "env2_depth_b": "env2_depth_b_fraction",
    "lfo1_depth_a": "lfo1_depth_a_fraction",
    "lfo1_depth_b": "lfo1_depth_b_fraction",
    "lfo2_depth_a": "lfo2_depth_a_fraction",
    "lfo2_depth_b": "lfo2_depth_b_fraction",
}


@dataclass(slots=True)
class A4Sound:
    _data: bytearray

    SIGNATURE = bytes.fromhex("be ef ba ba")
    NAME_OFFSET = 0x0C
    NAME_LENGTH = 16

    def __post_init__(self) -> None:
        if len(self._data) != A4_SOUND_SIZE:
            raise ValueError(f"A4 sound block must be {A4_SOUND_SIZE} bytes")
        if bytes(self._data[:4]) != self.SIGNATURE:
            raise ValueError(f"Unexpected A4 track signature {self._data[:4].hex(' ')}")
        if bytes(self._data[4:8]) != bytes.fromhex("00 00 00 06"):
            raise ValueError(f"Unexpected A4 track format marker {self._data[4:8].hex(' ')}")

    @classmethod
    def from_bytes(cls, data: bytes | bytearray | memoryview) -> A4Sound:
        return cls(bytearray(data))

    def to_bytes(self) -> bytes:
        return bytes(self._data)

    @property
    def name(self) -> str:
        raw = bytes(self._data[self.NAME_OFFSET : self.NAME_OFFSET + self.NAME_LENGTH])
        return raw.split(b"\x00", 1)[0].decode("ascii", errors="replace").rstrip()

    @name.setter
    def name(self, value: str) -> None:
        encoded = value.encode("ascii", errors="strict")[: self.NAME_LENGTH]
        self._data[self.NAME_OFFSET : self.NAME_OFFSET + self.NAME_LENGTH] = encoded.ljust(
            self.NAME_LENGTH, b"\x00"
        )

    def offset(self, field: str) -> int:
        try:
            return A4_TRACK_OFFSETS[field]
        except KeyError as exc:
            raise KeyError(f"Unknown mapped A4 field {field!r}") from exc

    def get_raw_u8(self, field: str) -> int:
        return self._data[self.offset(field)]

    def set_raw_u8(self, field: str, value: int) -> None:
        self._data[self.offset(field)] = _check_u8(value, field)

    def get_u7(self, field: str) -> int:
        value = self.get_raw_u8(field)
        if value > 127:
            raise ValueError(f"Mapped field {field!r} currently contains 8-bit raw value {value}")
        return value

    def set_u7(self, field: str, value: int) -> None:
        self.set_raw_u8(field, _check_a4_u7(value, field))

    def get_bipolar(self, field: str) -> int:
        if field not in A4_BIPOLAR_FIELDS:
            raise ValueError(f"{field!r} is not registered as a simple bipolar field")
        return decode_bipolar(self.get_u7(field))

    def set_bipolar(self, field: str, value: int) -> None:
        if field not in A4_BIPOLAR_FIELDS:
            raise ValueError(f"{field!r} is not registered as a simple bipolar field")
        self.set_u7(field, encode_bipolar(value))

    @staticmethod
    def _validate_oscillator(oscillator: int) -> None:
        if oscillator not in (1, 2):
            raise ValueError("oscillator must be 1 or 2")

    def get_oscillator_pitch_raw(self, oscillator: int) -> int:
        self._validate_oscillator(oscillator)
        offset = self.offset(f"osc{oscillator}_tune")
        return (self._data[offset] << 8) | self._data[offset + 1]

    def set_oscillator_pitch_raw(self, oscillator: int, raw: int) -> None:
        self._validate_oscillator(oscillator)
        if not 0 <= raw <= 0x7FFF:
            raise ValueError("raw oscillator pitch must be in 0x0000..0x7FFF")
        offset = self.offset(f"osc{oscillator}_tune")
        self._data[offset] = (raw >> 8) & 0xFF
        self._data[offset + 1] = raw & 0xFF

    def get_oscillator_pitch_components(self, oscillator: int) -> tuple[int, int, int, int]:
        return decode_a4_pitch_components(self.get_oscillator_pitch_raw(oscillator))

    def get_oscillator_tune(self, oscillator: int) -> int:
        return self.get_oscillator_pitch_components(oscillator)[0]

    def get_oscillator_fine(self, oscillator: int) -> int:
        return self.get_oscillator_pitch_components(oscillator)[1]

    def get_oscillator_fine_hidden_half_step(self, oscillator: int) -> int:
        return self.get_oscillator_pitch_components(oscillator)[2]

    def get_oscillator_fine_native_residual(self, oscillator: int) -> int:
        return self.get_oscillator_pitch_components(oscillator)[3]

    def set_oscillator_tune(self, oscillator: int, tune_semitones: int) -> None:
        _, fine, hidden_half_step, _ = self.get_oscillator_pitch_components(oscillator)
        self.set_oscillator_pitch_raw(
            oscillator,
            encode_a4_pitch_raw(tune_semitones, fine, hidden_half_step=hidden_half_step),
        )

    def set_oscillator_fine(
        self, oscillator: int, fine_value: int, *, hidden_half_step: int = 0
    ) -> None:
        tune, _, _, _ = self.get_oscillator_pitch_components(oscillator)
        self.set_oscillator_pitch_raw(
            oscillator,
            encode_a4_pitch_raw(tune, fine_value, hidden_half_step=hidden_half_step),
        )

    def set_oscillator_tune_fine(
        self,
        oscillator: int,
        tune_semitones: int,
        fine_value: int,
        *,
        hidden_half_step: int = 0,
    ) -> None:
        self.set_oscillator_pitch_raw(
            oscillator,
            encode_a4_pitch_raw(tune_semitones, fine_value, hidden_half_step=hidden_half_step),
        )

    def get_oscillator_tune_fine(self, oscillator: int) -> tuple[int, int]:
        tune, fine, _, _ = self.get_oscillator_pitch_components(oscillator)
        return tune, fine

    def get_oscillator_pitch_semitones(self, oscillator: int) -> float:
        return decode_a4_pitch_semitones(self.get_oscillator_pitch_raw(oscillator))

    def get_fixed_8_8(self, field: str) -> float:
        if field not in A4_TWO_BYTE_FIELDS:
            raise ValueError(f"{field!r} is not a mapped 8.8 fixed-point field")
        offset = self.offset(field)
        return self._data[offset] + self._data[offset + 1] / 256.0

    def set_fixed_8_8(self, field: str, value: float) -> None:
        if field not in A4_TWO_BYTE_FIELDS:
            raise ValueError(f"{field!r} is not a mapped 8.8 fixed-point field")
        if not 0.0 <= value <= 127.99609375:
            raise ValueError("8.8 display value must be between 0.0 and 127.99609375")
        scaled = int(round(value * 256.0))
        # The validated maximum is exactly 0x7FFF after 8.8 conversion.
        if scaled > 0x7FFF:  # pragma: no cover
            scaled = 0x7FFF
        offset = self.offset(field)
        self._data[offset] = (scaled >> 8) & 0xFF
        self._data[offset + 1] = scaled & 0xFF

    def set_destination(self, field: str, destination: A4Destination | int) -> None:
        self.set_u7(field, int(A4Destination(destination)))

    def get_mod_depth_raw(self, field: str) -> int:
        try:
            fraction_field = A4_MOD_DEPTH_FIELDS[field]
        except KeyError as exc:
            raise ValueError(f"{field!r} is not a mapped modulation-depth field") from exc
        return (self.get_raw_u8(field) << 8) | self.get_raw_u8(fraction_field)

    def get_mod_depth(self, field: str) -> float:
        return decode_a4_mod_depth(self.get_mod_depth_raw(field))

    def set_mod_depth(self, field: str, value: float) -> None:
        try:
            fraction_field = A4_MOD_DEPTH_FIELDS[field]
        except KeyError as exc:
            raise ValueError(f"{field!r} is not a mapped modulation-depth field") from exc
        raw = encode_a4_mod_depth(value)
        self.set_raw_u8(field, (raw >> 8) & 0xFF)
        self.set_raw_u8(fraction_field, raw & 0xFF)

    def set_integer_mod_depth(self, field: str, value: int) -> None:
        """Backward-compatible integer wrapper around the confirmed Q8.7 encoder."""
        self.set_mod_depth(field, float(value))


@dataclass(slots=True)
class A4Kit:
    _data: bytearray

    NAME_OFFSET = 0x04
    NAME_LENGTH = 16
    TRACK_LEVELS_OFFSET = 0x14

    def __post_init__(self) -> None:
        if len(self._data) != A4_SAVED_KIT_OBJECT_SIZE:
            raise ValueError(
                "A4 kit object must be " f"{A4_SAVED_KIT_OBJECT_SIZE} bytes, got {len(self._data)}"
            )

    @classmethod
    def from_bytes(cls, data: bytes | bytearray | memoryview) -> A4Kit:
        return cls(bytearray(data))

    def to_bytes(self) -> bytes:
        return bytes(self._data)

    @property
    def name(self) -> str:
        raw = bytes(self._data[self.NAME_OFFSET : self.NAME_OFFSET + self.NAME_LENGTH])
        return raw.split(b"\x00", 1)[0].decode("ascii", errors="replace").rstrip()

    @name.setter
    def name(self, value: str) -> None:
        encoded = value.encode("ascii", errors="strict")[: self.NAME_LENGTH]
        self._data[self.NAME_OFFSET : self.NAME_OFFSET + self.NAME_LENGTH] = encoded.ljust(
            self.NAME_LENGTH, b"\x00"
        )

    def track_level(self, track_index: int) -> int:
        if not 0 <= track_index < 6:
            raise ValueError("track level index must be 0..5 (T1-T4, FX, CV/kit slot)")
        return self._data[self.TRACK_LEVELS_OFFSET + track_index * 2]

    def set_track_level(self, track_index: int, value: int) -> None:
        _check_a4_u7(value, "track level")
        if not 0 <= track_index < 6:
            raise ValueError("track level index must be 0..5")
        offset = self.TRACK_LEVELS_OFFSET + track_index * 2
        self._data[offset] = value
        self._data[offset + 1] = 0

    def sound(self, track_index: int) -> A4Sound:
        if not 0 <= track_index < 4:
            raise ValueError("synth track index must be 0..3")
        start = A4_KIT_TRACKS_START + track_index * A4_SOUND_SIZE
        return A4Sound.from_bytes(self._data[start : start + A4_SOUND_SIZE])

    def replace_sound(self, track_index: int, sound: A4Sound) -> None:
        if not 0 <= track_index < 4:
            raise ValueError("synth track index must be 0..3")
        start = A4_KIT_TRACKS_START + track_index * A4_SOUND_SIZE
        self._data[start : start + A4_SOUND_SIZE] = sound.to_bytes()

    def iter_sounds(self) -> Iterator[A4Sound]:
        for track_index in range(4):
            yield self.sound(track_index)
