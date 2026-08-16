"""Analog Rytm MKII cockpit parameter-to-CC lookup.

The cockpit works with compact UI parameter keys (``tun``, ``dec``,
``sample_tune``) while the outbound MIDI path needs the Rytm's real CC
numbers and per-track MIDI channels. The CC facts come from
``rytm_randomizer.data.analog_rytm_midi`` so this module stays a thin
projection from cockpit names to the manual-backed catalog.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from ...data.analog_rytm_midi import (
    ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER,
    ANALOG_RYTM_MACHINE_SRC_BY_MACHINE,
    AnalogRytmCcMapping,
)

_PAD_ID_MIN: Final[int] = 1
_PAD_ID_MAX: Final[int] = 12

_COMMON_ALIASES: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "sample_tune": ("SAMPLE", "Sample Tune"),
        "sample_fine": ("SAMPLE", "Sample Fine tune"),
        "sample_bit": ("SAMPLE", "Sample Bit Reduction"),
        "sample_slot": ("SAMPLE", "Sample Slot"),
        "sample_start": ("SAMPLE", "Sample Start"),
        "sample_end": ("SAMPLE", "Sample End"),
        "sample_loop": ("SAMPLE", "Sample Loop"),
        "sample_level": ("SAMPLE", "Sample Level"),
        "filter_attack": ("FILTER", "Filter Attack Time"),
        "filter_decay": ("FILTER", "Filter Decay Time"),
        "filter_sustain": ("FILTER", "Filter Sustain Level"),
        "filter_release": ("FILTER", "Filter Release Time"),
        "flt": ("FILTER", "Filter Frequency"),
        "filter_resonance": ("FILTER", "Filter Resonance"),
        "filter_type": ("FILTER", "Filter Mode"),
        "filter_env": ("FILTER", "Filter Env Depth"),
        "amp_attack": ("AMP", "Amp Attack Time"),
        "amp_hold": ("AMP", "Amp Hold Time"),
        "amp_decay": ("AMP", "Amp Decay Time"),
        "overdrive": ("AMP", "Amp Overdrive"),
        "delay": ("AMP", "Amp Delay Send"),
        "reverb": ("AMP", "Amp Reverb Send"),
        "pan": ("AMP", "Amp Pan"),
        "amp_volume": ("AMP", "Amp Volume"),
        "lfo_speed": ("LFO", "LFO Speed"),
        "lfo_mult": ("LFO", "LFO Multiplier"),
        "lfo_fade": ("LFO", "LFO Fade In/Out"),
        "lfo_destination": ("LFO", "LFO Destination"),
        "lfo_wave": ("LFO", "LFO Waveform"),
        "lfo_phase": ("LFO", "LFO Start Phase"),
        "lfo_trig": ("LFO", "LFO Trig Mode"),
        "lfo_depth": ("LFO", "LFO Depth"),
    }
)

_BD_HARD_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "hld": "Hold",
        "hold": "Hold",
        "swt": "Sweep Time",
        "swd": "Sweep Depth",
        "sweep_depth": "Sweep Depth",
        "snap": "Sweep Depth",
        "wav": "Waveform",
        "wave": "Waveform",
        "trn": "Transient Tick",
        "tick": "Transient Tick",
    }
)
_BD_SHARP_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "sweep_depth": "Sweep Depth",
        "snap": "Sweep Depth",
        "swt": "Sweep Time",
        "hold": "Hold Time",
        "tick": "Tick Level",
        "wave": "Waveform",
    }
)
_BD_PLASTIC_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay Time",
        "sweep_depth": "Sweep Depth",
        "swt": "Sweep Time",
        "hold": "Hold Time",
        "vco_click": "VCO Click",
        "dust": "Dust Level",
    }
)
_BD_SILKY_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "sweep_depth": "Sweep Depth",
        "swt": "Sweep Time",
        "hold": "Hold",
        "vco_click": "VCO Click",
        "dust": "Dust Level",
    }
)
_BD_FM_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "fm_amount": "FM Amount",
        "swt": "Sweep Time",
        "fm_sweep_time": "FM Sweep Time",
        "fm_decay": "FM Decay Time",
        "fm_tune": "FM Tune",
    }
)
_BD_ACOUSTIC_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "sweep_depth": "Sweep Depth",
        "swt": "Sweep Time",
        "hold": "Hold Time",
        "impact": "Impact",
        "wave": "Waveform",
    }
)
_SD_NATURAL_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Body Decay",
        "noise_decay": "Noise Decay",
        "noise_lpf": "Noise LPF",
        "noise_balance": "Noise Balance",
        "noise_resonance": "Noise Resonance",
        "noise_hpf": "Noise HPF",
    }
)
_SD_HARD_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "sweep_depth": "Sweep Depth",
        "tick": "Tick Level",
        "noise_decay": "Noise Decay",
        "noise_level": "Noise Level",
        "swt": "Sweep Time",
    }
)
_SD_CLASSIC_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "detune": "Detune",
        "snap": "Snap Amount",
        "noise_decay": "Noise Decay",
        "noise_level": "Noise Level",
        "balance": "Osc Balance",
    }
)
_SD_FM_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "fm_tune": "FM Tune",
        "fm_decay": "FM Decay Time",
        "noise_decay": "Noise Decay",
        "noise_level": "Noise Level",
        "fm_amount": "FM Amount",
    }
)
_SD_ACOUSTIC_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "noise_decay": "Noise Decay",
        "hold": "Hold Time",
        "noise_level": "Noise Level",
        "impact": "Impact",
        "sweep_depth": "Sweep Depth",
    }
)
_RS_HARD_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "sweep_depth": "Sweep Depth",
        "tick": "Tick Level",
        "noise_level": "Noise Level",
        "symmetry": "Symmetry",
        "swt": "Sweep Time",
    }
)
_RS_CLASSIC_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune Osc 1",
        "dec": "Decay",
        "balance": "Osc Balance",
        "tune_2": "Tune Osc 2",
        "symmetry": "Symmetry",
        "noise_level": "Noise Level",
        "tick": "Tick Level",
    }
)
_BT_CLASSIC_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "sweep_depth": "Sweep Depth",
        "noise_level": "Noise Level",
        "snap": "Snap Type",
    }
)
_XT_CLASSIC_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "target_note": "Tune",
        "dec": "Decay",
        "decay": "Decay",
        "sweep_depth": "Sweep Depth",
        "swt": "Sweep Time",
        "noise_decay": "Noise Decay",
        "noise_level": "Noise Level",
        "noise_tone": "Noise Tone",
    }
)
_CH_CLASSIC_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "color": "Color",
    }
)
_METALLIC_HAT_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay Time",
    }
)
_CP_CLASSIC_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Noise Tone",
        "dec": "Noise Decay",
        "clap_number": "Clap Number",
        "clap_rate": "Clap Rate",
        "noise_level": "Noise Level",
        "random_claps": "Random Claps",
        "clap_decay": "Clap Decay",
    }
)
_SY_RAW_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "lev": "Level",
        "tun": "Tune",
        "dec": "Decay",
        "noise_level": "Noise Level",
        "detune": "Osc 2 Detune",
        "wave": "Waveform 1",
        "wave_2": "Waveform 2",
        "balance": "Balance",
    }
)

_MACHINE_PARAMETER_ALIASES: Final[Mapping[str, Mapping[str, str]]] = MappingProxyType(
    {
        "bd_hard": _BD_HARD_ALIASES,
        "bd_classic": _BD_HARD_ALIASES,
        "bd_sharp": _BD_SHARP_ALIASES,
        "bd_plastic": _BD_PLASTIC_ALIASES,
        "bd_silky": _BD_SILKY_ALIASES,
        "bd_fm": _BD_FM_ALIASES,
        "bd_acoustic": _BD_ACOUSTIC_ALIASES,
        "sd_natural": _SD_NATURAL_ALIASES,
        "sd_hard": _SD_HARD_ALIASES,
        "sd_classic": _SD_CLASSIC_ALIASES,
        "sd_acoustic": _SD_ACOUSTIC_ALIASES,
        "sd_fm": _SD_FM_ALIASES,
        "rs_classic": _RS_CLASSIC_ALIASES,
        "rs_hard": _RS_HARD_ALIASES,
        "bt_classic": _BT_CLASSIC_ALIASES,
        "xt_classic": _XT_CLASSIC_ALIASES,
        "ch_classic": _CH_CLASSIC_ALIASES,
        "oh_classic": _CH_CLASSIC_ALIASES,
        "ch_metallic": _METALLIC_HAT_ALIASES,
        "oh_metallic": _METALLIC_HAT_ALIASES,
        "cp_classic": _CP_CLASSIC_ALIASES,
        "sy_raw": _SY_RAW_ALIASES,
    }
)

_MACHINE_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "bd": "bd_hard",
        "bd hard": "bd_hard",
        "bd classic": "bd_classic",
        "bd sharp": "bd_sharp",
        "bd plastic": "bd_plastic",
        "bd silky": "bd_silky",
        "bd fm": "bd_fm",
        "bd acoustic": "bd_acoustic",
        "sd": "sd_classic",
        "sd natural": "sd_natural",
        "sd hard": "sd_hard",
        "sd classic": "sd_classic",
        "sd acoustic": "sd_acoustic",
        "sd fm": "sd_fm",
        "rs": "rs_classic",
        "rs riser": "rs_classic",
        "rs classic": "rs_classic",
        "rs hard": "rs_hard",
        "bt": "bt_classic",
        "bt rim": "bt_classic",
        "bt classic": "bt_classic",
        "lt low": "xt_classic",
        "mt mid": "xt_classic",
        "ht high": "xt_classic",
        "xt classic": "xt_classic",
        "ch": "ch_classic",
        "ch closed": "ch_classic",
        "ch classic": "ch_classic",
        "ch metallic": "ch_metallic",
        "oh": "oh_classic",
        "oh open": "oh_classic",
        "oh classic": "oh_classic",
        "oh metallic": "oh_metallic",
        "fx metal": "oh_metallic",
        "cp": "cp_classic",
        "cp clap": "cp_classic",
        "cp classic": "cp_classic",
        "sy": "sy_raw",
        "sy raw": "sy_raw",
    }
)


def cockpit_pad_channel(pad_id: int) -> int:
    """Return the zero-based Rytm track MIDI channel for a 1-based pad id."""

    if not (_PAD_ID_MIN <= pad_id <= _PAD_ID_MAX):
        raise ValueError(f"pad_id must be in [{_PAD_ID_MIN}, {_PAD_ID_MAX}]; got {pad_id}")
    return pad_id - 1


def cockpit_parameter_control(machine: str, parameter: str) -> int | None:
    """Return the real Rytm CC for ``parameter`` on ``machine``.

    ``None`` means the cockpit does not have a safe compact-key mapping for
    that machine/key pair yet; callers should omit the packet instead of
    falling back to a synthetic CC.
    """

    mapping = cockpit_parameter_mapping(machine, parameter)
    return None if mapping is None else mapping.cc_msb


def cockpit_parameter_mapping(machine: str, parameter: str) -> AnalogRytmCcMapping | None:
    """Return the canonical manual-backed mapping for one cockpit field."""

    machine_key = _machine_key(machine)
    aliases = _MACHINE_PARAMETER_ALIASES.get(machine_key)
    if aliases is not None:
        catalog_parameter = aliases.get(parameter)
        if catalog_parameter is not None:
            for mapping in ANALOG_RYTM_MACHINE_SRC_BY_MACHINE[machine_key]:
                if mapping.parameter == catalog_parameter:
                    return mapping
            raise ValueError(
                f"missing Analog Rytm catalog row for {machine_key}:{catalog_parameter}"
            )

    catalog_key = _COMMON_ALIASES.get(parameter)
    if catalog_key is None:
        return None
    return ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[catalog_key]


def cockpit_machine_is_known(machine: str) -> bool:
    """Return whether ``machine`` resolves to the canonical source catalog."""

    return _machine_key(machine) in ANALOG_RYTM_MACHINE_SRC_BY_MACHINE


def _machine_key(machine: str) -> str:
    normalized = _normalize_label(machine)
    alias = _MACHINE_ALIASES.get(normalized)
    if alias is not None:
        return alias
    return normalized.replace(" ", "_")


def _normalize_label(label: str) -> str:
    return " ".join(label.lower().replace("_", " ").replace("-", " ").split())


__all__ = [
    "cockpit_machine_is_known",
    "cockpit_pad_channel",
    "cockpit_parameter_control",
    "cockpit_parameter_mapping",
]
