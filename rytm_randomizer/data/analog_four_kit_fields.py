"""Immutable target-unit-verified Analog Four saved-Kit field facts."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Final

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
A4_FIXED_8_8_RAW_MAX: Final[int] = 0x7FFF


def format_a4_fixed_8_8(
    raw: object, *, minimum: int = 0, maximum: int = A4_FIXED_8_8_RAW_MAX
) -> str:
    """Format an exact native Q8.8 value independently of Decimal context."""

    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError("Q8.8 value must be an integer")
    if not minimum <= raw <= maximum:
        raise ValueError(f"Q8.8 value must be in 0x{minimum:04X}..0x{maximum:04X}")
    integer, fraction = divmod(raw, A4_FIXED_8_8_SCALE)
    decimal_fraction = fraction * (10**8 // A4_FIXED_8_8_SCALE)
    return f"{integer}.{decimal_fraction:08d}".rstrip("0").rstrip(".")


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
    smallest = Decimal("0.00390625")
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

__all__ = [
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
    "parse_a4_fixed_8_8",
]
