"""Observed Analog Four MKII saved-kit SysEx layout facts."""

from __future__ import annotations

from typing import Final

A4_FAMILY_BYTE: Final[int] = 0x06
A4_CANDIDATE_KIT_TYPE_BYTE: Final[int] = 0x07
A4_KIT_OBJECT_BYTE: Final[int] = 0x52
A4_SAVED_KIT_HEADER_SIZE_WITHOUT_F0: Final[int] = 9
A4_SAVED_KIT_TRAILER_SIZE_WITHOUT_F7: Final[int] = 4
A4_SAVED_KIT_LENGTH_ADJUSTMENT: Final[int] = 5
A4_PACKED_PAYLOAD_OFFSET: Final[int] = A4_SAVED_KIT_HEADER_SIZE_WITHOUT_F0
A4_CHECKSUM_PACKED_OFFSET: Final[int] = 0
A4_SAVED_KIT_TRAILER_SIZE: Final[int] = 4
A4_SAVED_KIT_UNPACKED_SIZE: Final[int] = 2410
A4_SAVED_KIT_OBJECT_SIZE: Final[int] = 2410
A4_SAVED_KIT_PACKED_SIZE: Final[int] = 2755
A4_SAVED_KIT_FRAMED_SIZE: Final[int] = 2770
A4_KIT_NAME_OFFSET: Final[int] = 4
A4_KIT_NAME_LENGTH: Final[int] = 16
A4_KIT_OBJECT_NAME_OFFSET: Final[int] = 4
A4_KIT_OBJECT_TRACKS_OFFSET: Final[int] = 0x20
A4_KIT_OBJECT_TRACK_SOUND_SIZE: Final[int] = 350

A4_SNAPSHOT_LAYOUT_CANDIDATE: Final[str] = "candidate"
A4_SNAPSHOT_LAYOUT_SAVED_KIT: Final[str] = "saved_kit"


def wire_address_to_track_raw_offset(address: int) -> int:
    """Translate a packed standalone-Sound address to a saved-Kit track offset."""

    if address < 10:
        raise ValueError("wire address must point into packed payload at byte 10 or later")
    relative = address - 10
    remainder = relative % 8
    if remainder == 0:
        raise ValueError(f"wire address {address} is a 7-bit packing mask, not a raw field")
    raw_offset = (relative // 8) * 7 + (remainder - 1)
    if not 0 <= raw_offset < A4_KIT_OBJECT_TRACK_SOUND_SIZE:
        raise ValueError(
            f"translated raw offset {raw_offset} is outside a "
            f"{A4_KIT_OBJECT_TRACK_SOUND_SIZE}-byte A4 Sound"
        )
    return raw_offset


__all__ = [
    "A4_CANDIDATE_KIT_TYPE_BYTE",
    "A4_CHECKSUM_PACKED_OFFSET",
    "A4_FAMILY_BYTE",
    "A4_KIT_NAME_LENGTH",
    "A4_KIT_NAME_OFFSET",
    "A4_KIT_OBJECT_NAME_OFFSET",
    "A4_KIT_OBJECT_TRACKS_OFFSET",
    "A4_KIT_OBJECT_TRACK_SOUND_SIZE",
    "A4_KIT_OBJECT_BYTE",
    "A4_PACKED_PAYLOAD_OFFSET",
    "A4_SAVED_KIT_HEADER_SIZE_WITHOUT_F0",
    "A4_SAVED_KIT_LENGTH_ADJUSTMENT",
    "A4_SAVED_KIT_TRAILER_SIZE",
    "A4_SAVED_KIT_TRAILER_SIZE_WITHOUT_F7",
    "A4_SAVED_KIT_UNPACKED_SIZE",
    "A4_SAVED_KIT_PACKED_SIZE",
    "A4_SAVED_KIT_FRAMED_SIZE",
    "A4_SAVED_KIT_OBJECT_SIZE",
    "A4_SNAPSHOT_LAYOUT_CANDIDATE",
    "A4_SNAPSHOT_LAYOUT_SAVED_KIT",
    "wire_address_to_track_raw_offset",
]
