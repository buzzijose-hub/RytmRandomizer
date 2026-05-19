"""Passive Analog Rytm MK2 OS 1.72 machine compatibility catalog."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal

SupportStatus = Literal["mutable_v134", "machine_selectable"]


@dataclass(frozen=True)
class RytmMachineProfile:
    key: str
    label: str
    family: str
    machine_value: int
    support_status: SupportStatus
    role_tags: tuple[str, ...]


@dataclass(frozen=True)
class RytmPadCapability:
    pad: int
    track_code: str
    label: str
    allowed_machine_keys: tuple[str, ...]


BD_MACHINE_KEYS: Final = (
    "bd_hard",
    "bd_classic",
    "bd_fm",
    "bd_plastic",
    "bd_silky",
    "bd_sharp",
    "bd_acoustic",
)
SD_MACHINE_KEYS: Final = (
    "sd_hard",
    "sd_classic",
    "sd_fm",
    "sd_natural",
    "sd_acoustic",
)
SY_MACHINE_KEYS: Final = ("dual_vco", "sy_chip", "sy_raw")
RS_MACHINE_KEYS: Final = ("rs_hard", "rs_classic")
CP_MACHINE_KEYS: Final = ("cp_classic",)
BT_MACHINE_KEYS: Final = ("bt_classic",)
XT_MACHINE_KEYS: Final = ("xt_classic",)
CH_MACHINE_KEYS: Final = ("ch_classic", "ch_metallic")
OH_MACHINE_KEYS: Final = ("oh_classic", "oh_metallic")
HH_MACHINE_KEYS: Final = ("hh_basic", "hh_lab")
CY_MACHINE_KEYS: Final = ("cy_classic", "cy_metallic", "cy_ride")
CB_MACHINE_KEYS: Final = ("cb_classic", "cb_metallic")
UT_MACHINE_KEYS: Final = ("ut_noise", "ut_impulse")


RYTM_MACHINE_PROFILES: Final = (
    RytmMachineProfile("bd_hard", "BD Hard", "BD", 0, "mutable_v134", ("kick",)),
    RytmMachineProfile("bd_classic", "BD Classic", "BD", 1, "mutable_v134", ("kick",)),
    RytmMachineProfile("sd_hard", "SD Hard", "SD", 2, "mutable_v134", ("snare",)),
    RytmMachineProfile("sd_classic", "SD Classic", "SD", 3, "mutable_v134", ("snare",)),
    RytmMachineProfile("rs_hard", "RS Hard", "RS", 4, "machine_selectable", ("rim",)),
    RytmMachineProfile("rs_classic", "RS Classic", "RS", 5, "machine_selectable", ("rim",)),
    RytmMachineProfile("cp_classic", "CP Classic", "CP", 6, "machine_selectable", ("clap",)),
    RytmMachineProfile("bt_classic", "BT Classic", "BT", 7, "machine_selectable", ("tom",)),
    RytmMachineProfile("xt_classic", "XT Classic", "XT", 8, "machine_selectable", ("tom",)),
    RytmMachineProfile("ch_classic", "CH Classic", "CH", 9, "machine_selectable", ("hihat",)),
    RytmMachineProfile("oh_classic", "OH Classic", "OH", 10, "machine_selectable", ("hihat",)),
    RytmMachineProfile("cy_classic", "CY Classic", "CY", 11, "machine_selectable", ("cymbal",)),
    RytmMachineProfile("cb_classic", "CB Classic", "CB", 12, "machine_selectable", ("cowbell",)),
    RytmMachineProfile("bd_fm", "BD FM", "BD", 13, "mutable_v134", ("kick", "fm")),
    RytmMachineProfile("sd_fm", "SD FM", "SD", 14, "mutable_v134", ("snare", "fm")),
    RytmMachineProfile(
        "ut_noise", "UT Noise", "UT", 15, "machine_selectable", ("utility", "noise")
    ),
    RytmMachineProfile(
        "ut_impulse", "UT Impulse", "UT", 16, "machine_selectable", ("utility", "impulse")
    ),
    RytmMachineProfile(
        "ch_metallic", "CH Metallic", "CH", 17, "machine_selectable", ("hihat", "metallic")
    ),
    RytmMachineProfile(
        "oh_metallic", "OH Metallic", "OH", 18, "machine_selectable", ("hihat", "metallic")
    ),
    RytmMachineProfile(
        "cy_metallic", "CY Metallic", "CY", 19, "machine_selectable", ("cymbal", "metallic")
    ),
    RytmMachineProfile(
        "cb_metallic", "CB Metallic", "CB", 20, "machine_selectable", ("cowbell", "metallic")
    ),
    RytmMachineProfile("bd_plastic", "BD Plastic", "BD", 21, "mutable_v134", ("kick",)),
    RytmMachineProfile("bd_silky", "BD Silky", "BD", 22, "mutable_v134", ("kick",)),
    RytmMachineProfile("sd_natural", "SD Natural", "SD", 23, "machine_selectable", ("snare",)),
    RytmMachineProfile("hh_basic", "HH Basic", "HH", 24, "machine_selectable", ("hihat",)),
    RytmMachineProfile("cy_ride", "CY Ride", "CY", 25, "machine_selectable", ("cymbal", "ride")),
    RytmMachineProfile("bd_sharp", "BD Sharp", "BD", 26, "mutable_v134", ("kick",)),
    RytmMachineProfile("dual_vco", "Dual VCO", "SY", 28, "machine_selectable", ("synth",)),
    RytmMachineProfile("sy_chip", "SY Chip", "SY", 29, "machine_selectable", ("synth",)),
    RytmMachineProfile(
        "bd_acoustic", "BD Acoustic", "BD", 30, "mutable_v134", ("kick", "acoustic")
    ),
    RytmMachineProfile(
        "sd_acoustic", "SD Acoustic", "SD", 31, "machine_selectable", ("snare", "acoustic")
    ),
    RytmMachineProfile("sy_raw", "SY Raw", "SY", 32, "mutable_v134", ("synth",)),
    RytmMachineProfile("hh_lab", "HH Lab", "HH", 33, "machine_selectable", ("hihat",)),
)

RYTM_MACHINE_PROFILES_BY_KEY: Final[Mapping[str, RytmMachineProfile]] = MappingProxyType(
    {profile.key: profile for profile in RYTM_MACHINE_PROFILES}
)

RYTM_PAD_CAPABILITIES: Final = (
    RytmPadCapability(
        1,
        "BD",
        "Bass Drum",
        BD_MACHINE_KEYS + SY_MACHINE_KEYS + SD_MACHINE_KEYS + UT_MACHINE_KEYS,
    ),
    RytmPadCapability(
        2,
        "SD",
        "Snare Drum",
        SD_MACHINE_KEYS + SY_MACHINE_KEYS + BD_MACHINE_KEYS + UT_MACHINE_KEYS,
    ),
    RytmPadCapability(
        3,
        "RS",
        "Rim Shot",
        RS_MACHINE_KEYS
        + SY_MACHINE_KEYS
        + BD_MACHINE_KEYS
        + SD_MACHINE_KEYS
        + CP_MACHINE_KEYS
        + UT_MACHINE_KEYS,
    ),
    RytmPadCapability(
        4,
        "CP",
        "Hand Clap",
        CP_MACHINE_KEYS
        + SY_MACHINE_KEYS
        + BD_MACHINE_KEYS
        + SD_MACHINE_KEYS
        + RS_MACHINE_KEYS
        + UT_MACHINE_KEYS,
    ),
    RytmPadCapability(5, "BT", "Bass Tom", BT_MACHINE_KEYS + UT_MACHINE_KEYS),
    RytmPadCapability(6, "LT", "Low Tom", XT_MACHINE_KEYS + UT_MACHINE_KEYS),
    RytmPadCapability(7, "MT", "Mid Tom", XT_MACHINE_KEYS + UT_MACHINE_KEYS),
    RytmPadCapability(8, "HT", "Hi Tom", XT_MACHINE_KEYS + UT_MACHINE_KEYS),
    RytmPadCapability(
        9,
        "CH",
        "Closed Hihat",
        CH_MACHINE_KEYS + HH_MACHINE_KEYS + OH_MACHINE_KEYS + UT_MACHINE_KEYS,
    ),
    RytmPadCapability(
        10,
        "OH",
        "Open Hihat",
        OH_MACHINE_KEYS + HH_MACHINE_KEYS + CH_MACHINE_KEYS + UT_MACHINE_KEYS,
    ),
    RytmPadCapability(11, "CY", "Cymbal", CY_MACHINE_KEYS + CB_MACHINE_KEYS + UT_MACHINE_KEYS),
    RytmPadCapability(12, "CB", "Cow Bell", CB_MACHINE_KEYS + CY_MACHINE_KEYS + UT_MACHINE_KEYS),
)

RYTM_PAD_CAPABILITIES_BY_PAD: Final[Mapping[int, RytmPadCapability]] = MappingProxyType(
    {capability.pad: capability for capability in RYTM_PAD_CAPABILITIES}
)


def get_rytm_machine_profile(machine_key: str) -> RytmMachineProfile:
    try:
        return RYTM_MACHINE_PROFILES_BY_KEY[machine_key]
    except KeyError as exc:
        raise KeyError(f"Unknown Rytm machine key: {machine_key}") from exc


def get_rytm_pad_capability(pad: int) -> RytmPadCapability:
    try:
        return RYTM_PAD_CAPABILITIES_BY_PAD[pad]
    except KeyError as exc:
        raise KeyError(f"Unknown Rytm pad: {pad}") from exc


def allowed_machine_profiles_for_pad(pad: int) -> tuple[RytmMachineProfile, ...]:
    capability = get_rytm_pad_capability(pad)
    return tuple(get_rytm_machine_profile(key) for key in capability.allowed_machine_keys)


def is_machine_allowed_on_pad(pad: int, machine_key: str) -> bool:
    get_rytm_machine_profile(machine_key)
    capability = get_rytm_pad_capability(pad)
    return machine_key in capability.allowed_machine_keys
