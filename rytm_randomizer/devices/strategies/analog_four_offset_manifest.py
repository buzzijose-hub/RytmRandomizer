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
A4_CHECKSUM_PACKED_OFFSET: Final[int] = 8
A4_SAVED_KIT_TRAILER_SIZE: Final[int] = 4
A4_SAVED_KIT_UNPACKED_SIZE: Final[int] = 2415
A4_KIT_NAME_OFFSET: Final[int] = 8
A4_KIT_NAME_LENGTH: Final[int] = 16

A4_SNAPSHOT_LAYOUT_CANDIDATE: Final[str] = "candidate"
A4_SNAPSHOT_LAYOUT_SAVED_KIT: Final[str] = "saved_kit"

__all__ = [
    "A4_CANDIDATE_KIT_TYPE_BYTE",
    "A4_CHECKSUM_PACKED_OFFSET",
    "A4_FAMILY_BYTE",
    "A4_KIT_NAME_LENGTH",
    "A4_KIT_NAME_OFFSET",
    "A4_KIT_OBJECT_BYTE",
    "A4_PACKED_PAYLOAD_OFFSET",
    "A4_SAVED_KIT_TRAILER_SIZE",
    "A4_SAVED_KIT_UNPACKED_SIZE",
    "A4_SNAPSHOT_LAYOUT_CANDIDATE",
    "A4_SNAPSHOT_LAYOUT_SAVED_KIT",
]
