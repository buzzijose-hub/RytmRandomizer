"""AL16 bank identity and positively mapped Rytm writer facts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final


@dataclass(frozen=True)
class Al16BankState:
    """One reserved operating state in the AL16 performance bank."""

    number: int
    name: str
    tonal_zone: str


@dataclass(frozen=True)
class RytmWritableField:
    """One saved-kit field supported by positive layout evidence."""

    nrpn_lsb: int
    converter: str


AL16_BANK_STATES: Final = (
    Al16BankState(1, "AIRLOCK", "F Phrygian"),
    Al16BankState(2, "LOCK", "F Phrygian"),
    Al16BankState(3, "ROTATION", "F Phrygian"),
    Al16BankState(4, "PRESSURE", "F Phrygian"),
    Al16BankState(5, "ORBIT", "F# Dorian"),
    Al16BankState(6, "OFFSET", "F# Dorian"),
    Al16BankState(7, "SURGE", "F# Dorian"),
    Al16BankState(8, "CROSSING", "F# Dorian into harmonic-minor tension"),
    Al16BankState(9, "COMPRESSION", "F# harmonic minor"),
    Al16BankState(10, "RITUAL", "F# harmonic minor"),
    Al16BankState(11, "APEX", "F# harmonic minor"),
    Al16BankState(12, "VACUUM", "reduced-pitch F# corridor"),
    Al16BankState(13, "REENTRY", "A minor"),
    Al16BankState(14, "TERMINAL", "A minor"),
    Al16BankState(15, "FRACTURE", "A minor with borrowed Bb/Eb friction"),
    Al16BankState(16, "SHUTDOWN", "ambiguous A-centered ending"),
)

AL16_PAD_ROLES: Final[Mapping[int, str]] = MappingProxyType(
    {
        1: "Main kick",
        2: "Secondary impact / restrained snare",
        3: "Rim / synth percussion / dry punctuation",
        4: "Clap / impulse / noise / transition utility",
        5: "Bass tom / primary tuned low body",
        6: "Low tom / secondary tuned body",
        7: "Mid tom / rotating tonal percussion",
        8: "High tom / transition accent",
        9: "Closed-hat clock",
        10: "Open hat / air",
        11: "Cymbal / ride / upper pressure",
        12: "Cowbell / metallic punctuation / alarm tone",
    }
)

AL16_RYTM_WRITABLE_FIELDS: Final[Mapping[str, RytmWritableField]] = MappingProxyType(
    {
        "filter.atk": RytmWritableField(16, "verified_7bit"),
        "filter.dec": RytmWritableField(17, "verified_7bit"),
        "filter.sus": RytmWritableField(18, "verified_7bit"),
        "filter.rel": RytmWritableField(19, "verified_7bit"),
        "filter.frq": RytmWritableField(20, "verified_7bit"),
        "filter.res": RytmWritableField(21, "verified_7bit"),
        "filter.type": RytmWritableField(22, "filter_type_enum"),
        "filter.env": RytmWritableField(23, "centered_7bit"),
        "amp.atk": RytmWritableField(24, "verified_7bit"),
        "amp.hld": RytmWritableField(25, "verified_7bit"),
        "amp.dec": RytmWritableField(26, "verified_7bit"),
        "amp.ovr": RytmWritableField(27, "verified_7bit"),
        "amp.del": RytmWritableField(28, "verified_7bit"),
        "amp.rev": RytmWritableField(29, "verified_7bit"),
        "amp.pan": RytmWritableField(30, "centered_7bit"),
    }
)

AL16_RYTM_FILTER_TYPES: Final[Mapping[str, int]] = MappingProxyType(
    {"LP2": 0, "LP1": 1, "BP": 2, "PK": 3, "HP2": 4, "HP1": 5, "BS": 6}
)

# Intentionally empty until a machine-specific hardware calibration is approved.
AL16_RYTM_APPROVED_TUNING: Final[Mapping[tuple[str, str], int]] = MappingProxyType({})

AL16_PRESERVED_GLOBAL_SECTIONS: Final = (
    "scenes",
    "performance_macros",
    "master_delay",
    "master_reverb",
    "master_distortion",
    "master_compressor",
    "routing",
    "retrig_configuration",
    "choke_configuration",
    "unknown_and_reserved_bytes",
)


__all__ = [
    "AL16_BANK_STATES",
    "AL16_PAD_ROLES",
    "AL16_PRESERVED_GLOBAL_SECTIONS",
    "AL16_RYTM_APPROVED_TUNING",
    "AL16_RYTM_FILTER_TYPES",
    "AL16_RYTM_WRITABLE_FIELDS",
    "Al16BankState",
    "RytmWritableField",
]
