"""Immutable target-unit-verified Analog Rytm saved-Kit field facts."""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

RYTM_SOUND_NAME_OFFSET: Final[int] = 0x0C
RYTM_SOUND_NAME_STORAGE_LENGTH: Final[int] = 16
RYTM_SOUND_NAME_VISIBLE_LENGTH: Final[int] = 15

RYTM_MACHINE_PARAMETER_NAMES: Final[MappingProxyType[int, tuple[str, ...]]] = MappingProxyType(
    {
        26: ("LEV", "TUN", "DEC", "HLD", "SWT", "SWD", "WAV", "TIC"),
        2: ("LEV", "TUN", "DEC", "SWD", "TIC", "NOD", "NOL", "SWT"),
        4: ("LEV", "TUN", "DEC", "SWD", "TIC", "NOL", "SYM", "SWT"),
        6: ("LEV", "TON", "NOD", "NUM", "RAT", "NOL", "RND", "CPD"),
        7: ("LEV", "TUN", "DEC", "_", "NOL", "SNP", "SWD", "_"),
        8: ("LEV", "TUN", "DEC", "SWD", "SWT", "NOD", "NOL", "TON"),
        9: ("LEV", "TUN", "DEC", "COL", "_", "_", "_", "_"),
        10: ("LEV", "TUN", "DEC", "COL", "_", "_", "_", "_"),
        25: ("LEV", "TUN", "DEC", "TYP", "HIT", "C1", "C2", "C3"),
        20: ("LEV", "TUN", "DEC", "DET", "PW1", "PW2", "_", "_"),
    }
)

RYTM_SOUND_U7_FIELDS: Final[MappingProxyType[str, int]] = MappingProxyType(
    {
        "sample_tune": 0x2C,
        "sample_fine": 0x2E,
        "sample_number": 0x30,
        "sample_bit_reduction": 0x32,
        "sample_loop": 0x38,
        "sample_level": 0x3A,
        "filter_attack": 0x3C,
        "filter_sustain": 0x3E,
        "filter_decay": 0x40,
        "filter_release": 0x42,
        "filter_frequency": 0x44,
        "filter_resonance": 0x46,
        "filter_type": 0x48,
        "filter_envelope_depth": 0x4A,
        "amp_attack": 0x4C,
        "amp_hold": 0x4E,
        "amp_decay": 0x50,
        "amp_overdrive": 0x52,
        "amp_delay_send": 0x54,
        "amp_reverb_send": 0x56,
        "amp_pan": 0x58,
        "amp_volume": 0x5A,
        "accent_level": 0x5C,
        "lfo_speed": 0x5E,
        "lfo_multiplier": 0x60,
        "lfo_fade": 0x62,
        "lfo_destination": 0x64,
        "lfo_waveform": 0x66,
        "lfo_phase_or_slew": 0x68,
        "lfo_mode": 0x6A,
        "default_note": 0x6E,
    }
)

RYTM_FX_OFFSETS: Final[MappingProxyType[str, int]] = MappingProxyType(
    {
        "delay_time": 0x07CA,
        "delay_pingpong": 0x07CC,
        "delay_width": 0x07CE,
        "delay_feedback": 0x07D0,
        "delay_hpf": 0x07D2,
        "delay_lpf": 0x07D4,
        "delay_reverb_send": 0x07D6,
        "delay_volume": 0x07D8,
        "delay_overdrive": 0x07DA,
        "distortion_delay_overdrive": 0x07DA,
        "delay_dist_comp_route": 0x07DC,
        "distortion_delay_pre_post": 0x07DC,
        "reverb_predelay": 0x07DE,
        "reverb_decay": 0x07E0,
        "reverb_shelving_frequency": 0x07E2,
        "reverb_shelving_gain": 0x07E4,
        "reverb_hpf": 0x07E6,
        "reverb_lpf": 0x07E8,
        "reverb_volume": 0x07EA,
        "reverb_dist_comp_route": 0x07EC,
        "distortion_reverb_pre_post": 0x07EC,
        "distortion_amount": 0x07EE,
        "distortion_symmetry": 0x07F0,
        "compressor_threshold": 0x07F4,
        "compressor_attack": 0x07F6,
        "compressor_release": 0x07F8,
        "compressor_ratio": 0x07FA,
        "compressor_sidechain_eq": 0x07FC,
        "compressor_makeup_gain": 0x07FE,
        "compressor_mix": 0x0800,
        "compressor_volume": 0x0802,
        "fx_lfo_speed": 0x0804,
        "fx_lfo_multiplier": 0x0806,
        "fx_lfo_fade": 0x0808,
        "fx_lfo_destination": 0x080A,
        "fx_lfo_waveform": 0x080C,
        "fx_lfo_phase": 0x080E,
        "fx_lfo_mode": 0x0810,
    }
)

RYTM_MACHINE_BIPOLAR_PARAMETERS: Final[MappingProxyType[int, frozenset[str]]] = MappingProxyType(
    {
        26: frozenset({"TUN"}),
        2: frozenset({"TUN"}),
        4: frozenset({"TUN"}),
        6: frozenset(),
        7: frozenset({"TUN"}),
        8: frozenset({"TUN", "TON"}),
        9: frozenset({"TUN", "COL"}),
        10: frozenset({"TUN", "COL"}),
        25: frozenset({"TUN"}),
        20: frozenset({"TUN", "PW1", "PW2"}),
    }
)
RYTM_TRACK_MACHINE_COMPATIBILITY: Final[tuple[frozenset[int], ...]] = (
    frozenset({26}),
    frozenset({2}),
    frozenset({4}),
    frozenset({6}),
    frozenset({7}),
    frozenset({8}),
    frozenset({8}),
    frozenset({8}),
    frozenset({9}),
    frozenset({10}),
    frozenset({25}),
    frozenset({20}),
)

RYTM_SAMPLE_FIELDS: Final[frozenset[str]] = frozenset(
    {"tune", "fine", "bit_reduction", "slot", "start", "end", "loop", "level"}
)
RYTM_FILTER_FIELDS: Final[frozenset[str]] = frozenset(
    {"attack", "decay", "sustain", "release", "frequency", "resonance", "type", "envelope_depth"}
)
RYTM_AMP_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "attack",
        "hold",
        "decay",
        "overdrive",
        "delay_send",
        "reverb_send",
        "pan",
        "volume",
        "accent_level",
    }
)
RYTM_LFO_FIELDS: Final[frozenset[str]] = frozenset(
    {"speed", "multiplier", "fade", "destination", "waveform", "phase", "mode", "depth"}
)
RYTM_DELAY_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "time",
        "pingpong",
        "width",
        "feedback",
        "hpf",
        "lpf",
        "reverb_send",
        "volume",
        "overdrive",
        "route",
    }
)
RYTM_REVERB_FIELDS: Final[frozenset[str]] = frozenset(
    {"predelay", "decay", "shelving_frequency", "shelving_gain", "hpf", "lpf", "volume", "route"}
)
RYTM_DISTORTION_FIELDS: Final[frozenset[str]] = frozenset({"amount", "symmetry"})
RYTM_COMPRESSOR_FIELDS: Final[frozenset[str]] = frozenset(
    {"threshold", "attack", "release", "makeup_gain", "ratio", "sidechain", "mix", "volume"}
)

RYTM_COMPRESSOR_ATTACK_VALUES: Final[MappingProxyType[str, int]] = MappingProxyType(
    {"MS_0_03": 0, "MS_0_1": 1, "MS_0_3": 2, "MS_1": 3, "MS_3": 4, "MS_10": 5, "MS_30": 6}
)
RYTM_COMPRESSOR_RELEASE_VALUES: Final[MappingProxyType[str, int]] = MappingProxyType(
    {
        "SEC_0_1": 0,
        "SEC_0_2": 1,
        "SEC_0_4": 2,
        "SEC_0_6": 3,
        "SEC_1": 4,
        "SEC_2": 5,
        "A1": 6,
        "A2": 7,
    }
)
RYTM_COMPRESSOR_RATIO_VALUES: Final[MappingProxyType[str, int]] = MappingProxyType(
    {"RATIO_1_2": 0, "RATIO_1_4": 1, "RATIO_1_8": 2, "MAX": 3}
)
RYTM_COMPRESSOR_SIDECHAIN_VALUES: Final[MappingProxyType[str, int]] = MappingProxyType(
    {"OFF": 0, "LPF": 1, "HPF": 2, "HIT": 3}
)
RYTM_FX_ROUTE_VALUES: Final[MappingProxyType[str, int]] = MappingProxyType({"PRE": 0, "POST": 1})

__all__ = [
    "RYTM_AMP_FIELDS",
    "RYTM_COMPRESSOR_ATTACK_VALUES",
    "RYTM_COMPRESSOR_FIELDS",
    "RYTM_COMPRESSOR_RATIO_VALUES",
    "RYTM_COMPRESSOR_RELEASE_VALUES",
    "RYTM_COMPRESSOR_SIDECHAIN_VALUES",
    "RYTM_DELAY_FIELDS",
    "RYTM_DISTORTION_FIELDS",
    "RYTM_FILTER_FIELDS",
    "RYTM_FX_OFFSETS",
    "RYTM_FX_ROUTE_VALUES",
    "RYTM_LFO_FIELDS",
    "RYTM_MACHINE_BIPOLAR_PARAMETERS",
    "RYTM_MACHINE_PARAMETER_NAMES",
    "RYTM_REVERB_FIELDS",
    "RYTM_SAMPLE_FIELDS",
    "RYTM_SOUND_NAME_OFFSET",
    "RYTM_SOUND_NAME_STORAGE_LENGTH",
    "RYTM_SOUND_NAME_VISIBLE_LENGTH",
    "RYTM_SOUND_U7_FIELDS",
    "RYTM_TRACK_MACHINE_COMPATIBILITY",
]
