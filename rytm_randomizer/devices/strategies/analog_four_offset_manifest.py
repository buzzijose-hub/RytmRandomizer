"""Candidate Analog Four MKII saved-kit offset manifest.

This manifest intentionally stops at file-shape intake. The constants here
let the snapshot decoder recognize real saved-kit SysEx frames and read the
kit name from the unpacked payload, while keeping parameter offsets
candidate-only until they are validated against hardware.
"""

from __future__ import annotations

from typing import Final

A4_FAMILY_BYTE: Final[int] = 0x06
A4_CANDIDATE_KIT_TYPE_BYTE: Final[int] = 0x07
A4_KIT_OBJECT_BYTE: Final[int] = 0x52
A4_PACKED_PAYLOAD_OFFSET: Final[int] = 4
A4_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0: Final[int] = 4
A4_KIT_SYSEX_TRAILER_SIZE_WITHOUT_F7: Final[int] = 4
A4_KIT_RAW_SIZE: Final[int] = 2415
A4_KIT_CHECKSUM_PACKED_START: Final[int] = 8
A4_KIT_LENGTH_ADJUSTMENT: Final[int] = 0
A4_KIT_NAME_OFFSET: Final[int] = 8
A4_KIT_NAME_LENGTH: Final[int] = 16

A4_SNAPSHOT_LAYOUT_CANDIDATE: Final[str] = "candidate"
A4_SNAPSHOT_LAYOUT_SAVED_KIT: Final[str] = "saved_kit"

__all__ = [
    "A4_CANDIDATE_KIT_TYPE_BYTE",
    "A4_FAMILY_BYTE",
    "A4_KIT_CHECKSUM_PACKED_START",
    "A4_KIT_LENGTH_ADJUSTMENT",
    "A4_KIT_NAME_LENGTH",
    "A4_KIT_NAME_OFFSET",
    "A4_KIT_OBJECT_BYTE",
    "A4_KIT_RAW_SIZE",
    "A4_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0",
    "A4_KIT_SYSEX_TRAILER_SIZE_WITHOUT_F7",
    "A4_PACKED_PAYLOAD_OFFSET",
    "A4_SNAPSHOT_LAYOUT_CANDIDATE",
    "A4_SNAPSHOT_LAYOUT_SAVED_KIT",
]
