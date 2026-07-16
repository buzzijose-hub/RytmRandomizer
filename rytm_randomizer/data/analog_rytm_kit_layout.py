"""Analog Rytm MKII raw kit/Sound layout facts.

These offsets describe the decoded 8-bit kit payload used by Analog Rytm
firmware 1.70+ kit dumps. They are layout facts, not behavior. Runtime code
uses them after the generic Elektron 7-bit SysEx envelope has been removed.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final


@dataclass(frozen=True)
class AnalogRytmSoundField:
    """One CC-addressable field inside an ``ar_sound_t`` track record."""

    nrpn_lsb: int
    sound_offset: int


RYTM_SYSEX_PRODUCT_ID: Final[int] = 0x07
RYTM_KIT_DUMP_ID: Final[int] = 0x52
RYTM_KIT_WORK_BUFFER_DUMP_ID: Final[int] = 0x58
RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0: Final[int] = 9
RYTM_KIT_SYSEX_TRAILER_SIZE_WITHOUT_F7: Final[int] = 4
RYTM_KIT_CHECKSUM_PACKED_START: Final[int] = 0
RYTM_KIT_LENGTH_ADJUSTMENT: Final[int] = 5

RYTM_KIT_RAW_SIZE: Final[int] = 0x0A32
RYTM_KIT_NAME_OFFSET: Final[int] = 0x0004
RYTM_KIT_NAME_LENGTH: Final[int] = 16
RYTM_KIT_TRACKS_OFFSET: Final[int] = 0x002E
RYTM_KIT_TRACK_SOUND_SIZE: Final[int] = 162

RYTM_SOUND_MACHINE_TYPE_OFFSET: Final[int] = 0x007C
RYTM_KIT_TRACK_MACHINE_VALUE_OFFSET: Final[int] = (
    RYTM_KIT_TRACKS_OFFSET + RYTM_SOUND_MACHINE_TYPE_OFFSET
)

RYTM_SOUND_FIELD_BY_NRPN_LSB: Final[MappingProxyType[int, AnalogRytmSoundField]] = MappingProxyType(
    {
        0: AnalogRytmSoundField(nrpn_lsb=0, sound_offset=0x001C),
        1: AnalogRytmSoundField(nrpn_lsb=1, sound_offset=0x001E),
        2: AnalogRytmSoundField(nrpn_lsb=2, sound_offset=0x0020),
        3: AnalogRytmSoundField(nrpn_lsb=3, sound_offset=0x0022),
        4: AnalogRytmSoundField(nrpn_lsb=4, sound_offset=0x0024),
        5: AnalogRytmSoundField(nrpn_lsb=5, sound_offset=0x0026),
        6: AnalogRytmSoundField(nrpn_lsb=6, sound_offset=0x0028),
        7: AnalogRytmSoundField(nrpn_lsb=7, sound_offset=0x002A),
        8: AnalogRytmSoundField(nrpn_lsb=8, sound_offset=0x002C),
        9: AnalogRytmSoundField(nrpn_lsb=9, sound_offset=0x002E),
        10: AnalogRytmSoundField(nrpn_lsb=10, sound_offset=0x0032),
        11: AnalogRytmSoundField(nrpn_lsb=11, sound_offset=0x0030),
        12: AnalogRytmSoundField(nrpn_lsb=12, sound_offset=0x0034),
        13: AnalogRytmSoundField(nrpn_lsb=13, sound_offset=0x0036),
        14: AnalogRytmSoundField(nrpn_lsb=14, sound_offset=0x0038),
        15: AnalogRytmSoundField(nrpn_lsb=15, sound_offset=0x003A),
        16: AnalogRytmSoundField(nrpn_lsb=16, sound_offset=0x003C),
        17: AnalogRytmSoundField(nrpn_lsb=17, sound_offset=0x0040),
        18: AnalogRytmSoundField(nrpn_lsb=18, sound_offset=0x003E),
        19: AnalogRytmSoundField(nrpn_lsb=19, sound_offset=0x0042),
        20: AnalogRytmSoundField(nrpn_lsb=20, sound_offset=0x0044),
        21: AnalogRytmSoundField(nrpn_lsb=21, sound_offset=0x0046),
        22: AnalogRytmSoundField(nrpn_lsb=22, sound_offset=0x0048),
        23: AnalogRytmSoundField(nrpn_lsb=23, sound_offset=0x004A),
        24: AnalogRytmSoundField(nrpn_lsb=24, sound_offset=0x004C),
        25: AnalogRytmSoundField(nrpn_lsb=25, sound_offset=0x004E),
        26: AnalogRytmSoundField(nrpn_lsb=26, sound_offset=0x0050),
        27: AnalogRytmSoundField(nrpn_lsb=27, sound_offset=0x0052),
        28: AnalogRytmSoundField(nrpn_lsb=28, sound_offset=0x0054),
        29: AnalogRytmSoundField(nrpn_lsb=29, sound_offset=0x0056),
        30: AnalogRytmSoundField(nrpn_lsb=30, sound_offset=0x0058),
        31: AnalogRytmSoundField(nrpn_lsb=31, sound_offset=0x005A),
        32: AnalogRytmSoundField(nrpn_lsb=32, sound_offset=0x005E),
        33: AnalogRytmSoundField(nrpn_lsb=33, sound_offset=0x0060),
        34: AnalogRytmSoundField(nrpn_lsb=34, sound_offset=0x0062),
        35: AnalogRytmSoundField(nrpn_lsb=35, sound_offset=0x0064),
        36: AnalogRytmSoundField(nrpn_lsb=36, sound_offset=0x0066),
        37: AnalogRytmSoundField(nrpn_lsb=37, sound_offset=0x0068),
        38: AnalogRytmSoundField(nrpn_lsb=38, sound_offset=0x006A),
        39: AnalogRytmSoundField(nrpn_lsb=39, sound_offset=0x006C),
        103: AnalogRytmSoundField(nrpn_lsb=103, sound_offset=0x007C),
    }
)


__all__ = [
    "AnalogRytmSoundField",
    "RYTM_KIT_CHECKSUM_PACKED_START",
    "RYTM_KIT_DUMP_ID",
    "RYTM_KIT_LENGTH_ADJUSTMENT",
    "RYTM_KIT_NAME_LENGTH",
    "RYTM_KIT_NAME_OFFSET",
    "RYTM_KIT_RAW_SIZE",
    "RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0",
    "RYTM_KIT_SYSEX_TRAILER_SIZE_WITHOUT_F7",
    "RYTM_KIT_TRACKS_OFFSET",
    "RYTM_KIT_TRACK_MACHINE_VALUE_OFFSET",
    "RYTM_KIT_TRACK_SOUND_SIZE",
    "RYTM_KIT_WORK_BUFFER_DUMP_ID",
    "RYTM_SOUND_FIELD_BY_NRPN_LSB",
    "RYTM_SOUND_MACHINE_TYPE_OFFSET",
    "RYTM_SYSEX_PRODUCT_ID",
]
