"""Analog Rytm MKII cockpit parameter-to-CC lookup.

The cockpit works with compact UI parameter keys (``tun``, ``dec``,
``sample_tune``) while the outbound MIDI path needs the Rytm's real CC
numbers and per-track MIDI channels. This module keeps that translation in
the cockpit data layer so SEND preflight can stay deterministic and inert.
"""

from __future__ import annotations

from typing import Final

_PAD_ID_MIN: Final[int] = 1
_PAD_ID_MAX: Final[int] = 12

_COMMON_CONTROLS: Final[dict[str, int]] = {
    "sample_tune": 24,
    "sample_fine": 25,
    "sample_bit": 26,
    "sample_slot": 27,
    "sample_start": 28,
    "sample_end": 29,
    "sample_loop": 30,
    "sample_level": 31,
    "filter_attack": 70,
    "filter_decay": 71,
    "filter_sustain": 72,
    "filter_release": 73,
    "flt": 74,
    "filter_resonance": 75,
    "filter_type": 76,
    "filter_env": 77,
    "amp_attack": 78,
    "amp_hold": 79,
    "amp_decay": 80,
    "overdrive": 81,
    "delay": 82,
    "reverb": 83,
    "pan": 10,
    "amp_volume": 7,
    "lfo_speed": 102,
    "lfo_mult": 103,
    "lfo_fade": 104,
    "lfo_destination": 105,
    "lfo_wave": 106,
    "lfo_phase": 107,
    "lfo_trig": 108,
    "lfo_depth": 109,
}

_BD_HARD_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "hold": 19,
    "swt": 20,
    "snap": 21,
    "wave": 22,
    "tick": 23,
}

_BD_ACOUSTIC_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "sweep_depth": 19,
    "swt": 20,
    "hold": 21,
    "impact": 22,
    "wave": 23,
}

_BD_FM_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "fm_amount": 19,
    "swt": 20,
    "fm_sweep_time": 21,
    "fm_decay": 22,
    "fm_tune": 23,
}

_BD_SILKY_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "sweep_depth": 19,
    "swt": 20,
    "hold": 21,
    "vco_click": 22,
    "dust": 23,
}

_SD_CLASSIC_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "detune": 19,
    "snap": 20,
    "noise_decay": 21,
    "noise_level": 22,
    "balance": 23,
}

_SD_ACOUSTIC_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "noise_decay": 19,
    "hold": 20,
    "noise_level": 21,
    "impact": 22,
    "sweep_depth": 23,
}

_SD_FM_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "fm_tune": 19,
    "fm_decay": 20,
    "noise_decay": 21,
    "noise_level": 22,
    "fm_amount": 23,
}

_RS_CLASSIC_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "balance": 19,
    "tune_2": 20,
    "symmetry": 21,
    "noise_level": 22,
    "tick": 23,
}

_RS_HARD_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "sweep_depth": 19,
    "tick": 20,
    "noise_level": 21,
    "symmetry": 22,
    "swt": 23,
}

_BT_CLASSIC_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "sweep_depth": 19,
    "noise_level": 20,
    "snap": 21,
}

_XT_CLASSIC_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "sweep_depth": 19,
    "swt": 20,
    "noise_decay": 21,
    "noise_level": 22,
    "noise_tone": 23,
}

_CH_CLASSIC_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "color": 19,
}

_METALLIC_HAT_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
}

_CP_CLASSIC_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "clap_number": 19,
    "clap_rate": 20,
    "noise_level": 21,
    "random_claps": 22,
    "clap_decay": 23,
}

_SY_RAW_CONTROLS: Final[dict[str, int]] = {
    "lev": 16,
    "tun": 17,
    "dec": 18,
    "noise_level": 19,
    "detune": 20,
    "wave": 21,
    "wave_2": 22,
    "balance": 23,
}

_MACHINE_CONTROLS: Final[dict[str, dict[str, int]]] = {
    "bd_hard": _BD_HARD_CONTROLS,
    "bd_classic": _BD_HARD_CONTROLS,
    "bd_sharp": _BD_HARD_CONTROLS,
    "bd_plastic": _BD_SILKY_CONTROLS,
    "bd_silky": _BD_SILKY_CONTROLS,
    "bd_fm": _BD_FM_CONTROLS,
    "bd_acoustic": _BD_ACOUSTIC_CONTROLS,
    "sd_classic": _SD_CLASSIC_CONTROLS,
    "sd_acoustic": _SD_ACOUSTIC_CONTROLS,
    "sd_fm": _SD_FM_CONTROLS,
    "rs_classic": _RS_CLASSIC_CONTROLS,
    "rs_hard": _RS_HARD_CONTROLS,
    "bt_classic": _BT_CLASSIC_CONTROLS,
    "xt_classic": _XT_CLASSIC_CONTROLS,
    "ch_classic": _CH_CLASSIC_CONTROLS,
    "oh_classic": _CH_CLASSIC_CONTROLS,
    "ch_metallic": _METALLIC_HAT_CONTROLS,
    "oh_metallic": _METALLIC_HAT_CONTROLS,
    "cp_classic": _CP_CLASSIC_CONTROLS,
    "sy_raw": _SY_RAW_CONTROLS,
}

_MACHINE_ALIASES: Final[dict[str, str]] = {
    "bd": "bd_hard",
    "bd hard": "bd_hard",
    "bd classic": "bd_classic",
    "bd sharp": "bd_sharp",
    "bd plastic": "bd_plastic",
    "bd silky": "bd_silky",
    "bd fm": "bd_fm",
    "bd acoustic": "bd_acoustic",
    "sd": "sd_classic",
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


def cockpit_pad_channel(pad_id: int) -> int:
    """Return the zero-based Rytm track MIDI channel for a 1-based pad id."""

    if not (_PAD_ID_MIN <= pad_id <= _PAD_ID_MAX):
        raise ValueError(f"pad_id must be in [{_PAD_ID_MIN}, {_PAD_ID_MAX}]; got {pad_id}")
    return pad_id - 1


def cockpit_parameter_control(machine: str, parameter: str) -> int | None:
    """Return the real Rytm CC for ``parameter`` on ``machine``.

    ``None`` means the cockpit does not have a safe mapping for that
    machine/key pair yet; callers should omit the packet instead of falling
    back to a synthetic CC.
    """

    machine_key = _machine_key(machine)
    controls = _MACHINE_CONTROLS.get(machine_key)
    if controls is not None and parameter in controls:
        return controls[parameter]
    return _COMMON_CONTROLS.get(parameter)


def _machine_key(machine: str) -> str:
    normalized = _normalize_label(machine)
    alias = _MACHINE_ALIASES.get(normalized)
    if alias is not None:
        return alias
    return normalized.replace(" ", "_")


def _normalize_label(label: str) -> str:
    return " ".join(label.lower().replace("_", " ").replace("-", " ").split())


__all__ = ["cockpit_pad_channel", "cockpit_parameter_control"]
