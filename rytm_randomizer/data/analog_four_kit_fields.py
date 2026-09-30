"""Immutable target-unit-verified Analog Four saved-Kit field facts."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Final, Literal, NamedTuple

from .analog_four_saved_kit_layout import wire_address_to_track_raw_offset

A4_SOUND_NAME_OFFSET: Final[int] = 0x0C
A4_SOUND_NAME_LENGTH: Final[int] = 16


A4_WIRE_ADDRESSES: Final[MappingProxyType[str, int]] = MappingProxyType(
    {
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
)

A4_TRACK_OFFSETS: Final[MappingProxyType[str, int]] = MappingProxyType(
    {name: wire_address_to_track_raw_offset(address) for name, address in A4_WIRE_ADDRESSES.items()}
)

A4_SOUND_SIGNATURE: Final[bytes] = bytes.fromhex("be ef ba ba")
A4_SOUND_FORMAT_MARKER: Final[bytes] = bytes.fromhex("00 00 00 06")
A4_TWO_BYTE_FIELDS: Final[frozenset[str]] = frozenset({"filter1_frequency", "filter2_frequency"})
A4_FIXED_8_8_ENCODING: Final[str] = "unsigned-big-endian-q8.8"
A4_FIXED_8_8_WIDTH: Final[int] = 2
A4_FIXED_8_8_SCALE: Final[int] = 0x100
A4_NATIVE_WORD_MIN: Final[int] = 0
A4_NATIVE_WORD_MAX: Final[int] = 0x7FFF
A4_NATIVE_BYTE_MIN: Final[int] = 0
A4_NATIVE_BYTE_MAX: Final[int] = 0x7F
A4_FIXED_8_8_RAW_MAX: Final[int] = A4_NATIVE_WORD_MAX
A4_BIPOLAR_ZERO: Final[int] = 0x40
A4_BIPOLAR_MIN: Final[int] = A4_NATIVE_BYTE_MIN - A4_BIPOLAR_ZERO
A4_BIPOLAR_MAX: Final[int] = A4_NATIVE_BYTE_MAX - A4_BIPOLAR_ZERO

# OSC TUN and FIN share a centered pitch word. Controlled target-unit captures
# prove TUN 0 / FIN +1 -> 0x4003, +2 -> 0x4004, -1 -> 0x3FFE, -2 -> 0x3FFC.
# FIN uses signed residuals around the nearest coarse semitone; two neighboring
# codes share a displayed FIN integer. Untouched dumps preserve the hidden bit.
A4_PITCH_ZERO: Final[int] = 0x4000
A4_PITCH_UNITS_PER_SEMITONE: Final[int] = 0x0100
A4_FINE_NATIVE_MIN: Final[int] = -128
A4_FINE_NATIVE_MAX: Final[int] = 127
A4_FINE_DISPLAY_MIN: Final[int] = -64
A4_FINE_DISPLAY_MAX: Final[int] = 63
A4_FINE_UNITS_PER_DISPLAY: Final[int] = 2
A4_PITCH_COARSE_MIN: Final[int] = -A4_PITCH_ZERO // A4_PITCH_UNITS_PER_SEMITONE
A4_PITCH_COARSE_MAX: Final[int] = (
    A4_NATIVE_WORD_MAX - A4_PITCH_ZERO
) // A4_PITCH_UNITS_PER_SEMITONE

# ENV/LFO destination depths are centered Q8.7: +1.00 = 0x4080 and -1.00 =
# 0x3F80 in the controlled target-unit captures. These are codec facts only.
A4_MOD_DEPTH_ZERO: Final[int] = 0x4000
A4_MOD_DEPTH_UNITS_PER_DISPLAY: Final[int] = 0x0080
A4_MOD_DEPTH_DISPLAY_MIN: Final[float] = (
    A4_NATIVE_WORD_MIN - A4_MOD_DEPTH_ZERO
) / A4_MOD_DEPTH_UNITS_PER_DISPLAY
A4_MOD_DEPTH_DISPLAY_MAX: Final[float] = (
    A4_NATIVE_WORD_MAX - A4_MOD_DEPTH_ZERO
) / A4_MOD_DEPTH_UNITS_PER_DISPLAY


def format_a4_native_number(value: int, *, scale: int, offset: int = 0) -> str:
    """Format a validated canonical integer domain without Decimal rounding.

    The caller supplies one of the power-of-two scales in the immutable native
    domain table. Value validation belongs to the field codec or projection.
    """

    delta = value - offset
    sign = "-" if delta < 0 else ""
    integer, fraction = divmod(abs(delta), scale)
    if fraction == 0:
        return f"{sign}{integer}"
    digits = scale.bit_length() - 1
    decimal_fraction = fraction * (10**digits // scale)
    return f"{sign}{integer}.{decimal_fraction:0{digits}d}".rstrip("0")


def format_a4_fixed_8_8(
    raw: object, *, minimum: int = 0, maximum: int = A4_FIXED_8_8_RAW_MAX
) -> str:
    """Format an exact native Q8.8 value independently of Decimal context."""

    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError("Q8.8 value must be an integer")
    if not minimum <= raw <= maximum:
        raise ValueError(f"Q8.8 value must be in 0x{minimum:04X}..0x{maximum:04X}")
    return format_a4_native_number(raw, scale=A4_FIXED_8_8_SCALE)


def parse_a4_fixed_8_8(
    screen_value: object, *, minimum: int = 0, maximum: int = A4_FIXED_8_8_RAW_MAX
) -> int:
    """Parse exact Q8.8 text without rounding or constructing unbounded ratios."""

    try:
        if not isinstance(screen_value, str):
            raise TypeError("screen value must be text")
        parsed = Decimal(screen_value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"unsupported screen value {screen_value!r} for unsigned Q8.8") from exc
    lower = Decimal(format_a4_fixed_8_8(minimum))
    upper = Decimal(format_a4_fixed_8_8(maximum))
    smallest = Decimal(format_a4_native_number(1, scale=A4_FIXED_8_8_SCALE))
    if not parsed.is_finite() or parsed < lower or parsed > upper or 0 < parsed < smallest:
        raise ValueError(f"unsupported screen value {screen_value!r} for unsigned Q8.8")
    numerator, denominator = parsed.as_integer_ratio()
    raw, remainder = divmod(numerator * A4_FIXED_8_8_SCALE, denominator)
    if remainder:
        raise ValueError(f"unsupported screen value {screen_value!r} for unsigned Q8.8")
    return raw


A4_BIPOLAR_FIELDS: Final[frozenset[str]] = frozenset(
    {
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
)
A4_MOD_DEPTH_FIELDS: Final[MappingProxyType[str, str]] = MappingProxyType(
    {
        "envf_depth_a": "envf_depth_a_fraction",
        "envf_depth_b": "envf_depth_b_fraction",
        "env2_depth_a": "env2_depth_a_fraction",
        "env2_depth_b": "env2_depth_b_fraction",
        "lfo1_depth_a": "lfo1_depth_a_fraction",
        "lfo1_depth_b": "lfo1_depth_b_fraction",
        "lfo2_depth_a": "lfo2_depth_a_fraction",
        "lfo2_depth_b": "lfo2_depth_b_fraction",
    }
)

A4_OSCILLATOR_PITCH_FIELDS: Final[frozenset[str]] = frozenset({"osc1_tune", "osc2_tune"})
A4_OSCILLATOR_FINE_FIELDS: Final[frozenset[str]] = frozenset({"osc1_fine", "osc2_fine"})
A4NativeEncoding = Literal["u7", "bipolar", "q8.8", "q8.7", "pitch_word", "fine_component"]


class A4NativeFieldDomain(NamedTuple):
    """One codec domain, distinguishing stored bits from projected integers."""

    encoding: A4NativeEncoding
    native_encoding: str
    native_minimum: int
    native_maximum: int
    value_minimum: int
    value_maximum: int
    display_encoding: str
    display_scale: int = 1
    display_offset: int = 0
    offline_mutable: bool = True


A4_NATIVE_FORMAT_DOMAINS: Final[MappingProxyType[A4NativeEncoding, A4NativeFieldDomain]] = (
    MappingProxyType(
        {
            "u7": A4NativeFieldDomain(
                "u7",
                "u7",
                A4_NATIVE_BYTE_MIN,
                A4_NATIVE_BYTE_MAX,
                A4_NATIVE_BYTE_MIN,
                A4_NATIVE_BYTE_MAX,
                "u7",
            ),
            "bipolar": A4NativeFieldDomain(
                "bipolar",
                "u7",
                A4_NATIVE_BYTE_MIN,
                A4_NATIVE_BYTE_MAX,
                A4_BIPOLAR_MIN,
                A4_BIPOLAR_MAX,
                "bipolar",
            ),
            "q8.8": A4NativeFieldDomain(
                "q8.8",
                A4_FIXED_8_8_ENCODING,
                A4_NATIVE_WORD_MIN,
                A4_FIXED_8_8_RAW_MAX,
                A4_NATIVE_WORD_MIN,
                A4_FIXED_8_8_RAW_MAX,
                "fixed_point",
                A4_FIXED_8_8_SCALE,
            ),
            "q8.7": A4NativeFieldDomain(
                "q8.7",
                "centered-q8.7",
                A4_NATIVE_WORD_MIN,
                A4_NATIVE_WORD_MAX,
                A4_NATIVE_WORD_MIN,
                A4_NATIVE_WORD_MAX,
                "fixed_point",
                A4_MOD_DEPTH_UNITS_PER_DISPLAY,
                A4_MOD_DEPTH_ZERO,
            ),
            "pitch_word": A4NativeFieldDomain(
                "pitch_word",
                "centered-pitch-word",
                A4_NATIVE_WORD_MIN,
                A4_NATIVE_WORD_MAX,
                A4_NATIVE_WORD_MIN,
                A4_NATIVE_WORD_MAX,
                "semitones",
                A4_PITCH_UNITS_PER_SEMITONE,
                A4_PITCH_ZERO,
            ),
            "fine_component": A4NativeFieldDomain(
                "fine_component",
                "centered-pitch-word",
                A4_NATIVE_WORD_MIN,
                A4_NATIVE_WORD_MAX,
                A4_FINE_DISPLAY_MIN,
                A4_FINE_DISPLAY_MAX,
                "fine_display",
                offline_mutable=False,
            ),
        }
    )
)

# Fraction bytes are members of their exact modulation-depth word. They have
# no independently projected or mutable control domain.
A4_NATIVE_FIELD_DOMAINS: Final[MappingProxyType[str, A4NativeFieldDomain]] = MappingProxyType(
    {
        field: A4_NATIVE_FORMAT_DOMAINS[
            (
                "bipolar"
                if field in A4_BIPOLAR_FIELDS
                else (
                    "q8.8"
                    if field in A4_TWO_BYTE_FIELDS
                    else (
                        "q8.7"
                        if field in A4_MOD_DEPTH_FIELDS
                        else (
                            "pitch_word"
                            if field in A4_OSCILLATOR_PITCH_FIELDS
                            else "fine_component" if field in A4_OSCILLATOR_FINE_FIELDS else "u7"
                        )
                    )
                )
            )
        ]
        for field in A4_TRACK_OFFSETS
        if field not in A4_MOD_DEPTH_FIELDS.values()
    }
)

__all__ = [
    "A4_BIPOLAR_ZERO",
    "A4_BIPOLAR_MIN",
    "A4_BIPOLAR_MAX",
    "A4_NATIVE_WORD_MIN",
    "A4_NATIVE_WORD_MAX",
    "A4_NATIVE_BYTE_MIN",
    "A4_NATIVE_BYTE_MAX",
    "A4_PITCH_ZERO",
    "A4_PITCH_UNITS_PER_SEMITONE",
    "A4_PITCH_COARSE_MIN",
    "A4_PITCH_COARSE_MAX",
    "A4_FINE_NATIVE_MIN",
    "A4_FINE_NATIVE_MAX",
    "A4_FINE_DISPLAY_MIN",
    "A4_FINE_DISPLAY_MAX",
    "A4_FINE_UNITS_PER_DISPLAY",
    "A4_MOD_DEPTH_ZERO",
    "A4_MOD_DEPTH_UNITS_PER_DISPLAY",
    "A4_MOD_DEPTH_DISPLAY_MIN",
    "A4_MOD_DEPTH_DISPLAY_MAX",
    "A4_OSCILLATOR_PITCH_FIELDS",
    "A4_OSCILLATOR_FINE_FIELDS",
    "A4_NATIVE_FIELD_DOMAINS",
    "A4_NATIVE_FORMAT_DOMAINS",
    "A4NativeEncoding",
    "A4NativeFieldDomain",
    "A4_BIPOLAR_FIELDS",
    "A4_FIXED_8_8_ENCODING",
    "A4_FIXED_8_8_RAW_MAX",
    "A4_FIXED_8_8_SCALE",
    "A4_FIXED_8_8_WIDTH",
    "A4_MOD_DEPTH_FIELDS",
    "A4_SOUND_NAME_LENGTH",
    "A4_SOUND_NAME_OFFSET",
    "A4_SOUND_SIGNATURE",
    "A4_SOUND_FORMAT_MARKER",
    "A4_TRACK_OFFSETS",
    "A4_TWO_BYTE_FIELDS",
    "A4_WIRE_ADDRESSES",
    "format_a4_fixed_8_8",
    "format_a4_native_number",
    "parse_a4_fixed_8_8",
]
