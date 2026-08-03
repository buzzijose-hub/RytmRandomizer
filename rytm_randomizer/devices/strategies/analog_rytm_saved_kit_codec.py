"""Pure Analog Rytm MKII saved-kit SysEx frame codec."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from ...data.analog_rytm_kit_layout import (
    RYTM_KIT_CHECKSUM_PACKED_START,
    RYTM_KIT_DUMP_ID,
    RYTM_KIT_FRAME_SIZE,
    RYTM_KIT_LENGTH_ADJUSTMENT,
    RYTM_KIT_PACKED_SIZE,
    RYTM_KIT_RAW_SIZE,
    RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0,
    RYTM_KIT_WORK_BUFFER_DUMP_ID,
    RYTM_SYSEX_PRODUCT_ID,
)
from ...snapshot import ELEKTRON_MFR_ID, pack_elektron_7bit, unpack_elektron_7bit
from ...snapshot.elektron_u14 import (
    ELEKTRON_U14_MAX,
    decode_elektron_u14,
    encode_elektron_u14,
)

_DUMP_ID_INDEX: Final[int] = 5


@dataclass(frozen=True)
class AnalogRytmSavedKitFrame:
    """Decoded Rytm saved-kit frame and validated integrity metadata."""

    header: bytes
    packed: bytes
    unpacked: bytes
    checksum: int
    encoded_length: int


def analog_rytm_saved_kit_checksum(packed: bytes) -> int:
    """Return the verified 14-bit checksum for a packed Rytm kit body."""

    return sum(packed[RYTM_KIT_CHECKSUM_PACKED_START:]) & ELEKTRON_U14_MAX


def _validate_header(header: bytes) -> None:
    if len(header) != RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0:
        raise ValueError("Analog Rytm kit SysEx header has an unexpected length")
    if not header.startswith(ELEKTRON_MFR_ID + bytes((RYTM_SYSEX_PRODUCT_ID,))):
        raise ValueError("SysEx header is not an Analog Rytm Elektron kit header")
    if header[_DUMP_ID_INDEX] not in (RYTM_KIT_DUMP_ID, RYTM_KIT_WORK_BUFFER_DUMP_ID):
        raise ValueError("Analog Rytm SysEx object is not a kit dump")


def decode_analog_rytm_saved_kit_frame(frame: bytes) -> AnalogRytmSavedKitFrame:
    """Decode and validate one complete F0/F7-framed Rytm saved-kit dump."""

    if len(frame) != RYTM_KIT_FRAME_SIZE:
        raise ValueError(
            f"Analog Rytm saved-kit frame length is {len(frame)}; "
            f"expected {RYTM_KIT_FRAME_SIZE}"
        )
    if frame[0] != 0xF0 or frame[-1] != 0xF7:
        raise ValueError("Analog Rytm saved-kit SysEx framing is invalid")
    if any(value > 0x7F for value in frame[1:-1]):
        raise ValueError("Analog Rytm saved-kit SysEx contains an illegal data byte")

    body = frame[1:-1]
    header = body[:RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0]
    _validate_header(header)
    packed = body[RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0:-4]
    trailer = body[-4:]
    if len(packed) != RYTM_KIT_PACKED_SIZE:
        raise ValueError("Analog Rytm saved-kit packed payload has an unexpected length")

    stored_checksum = decode_elektron_u14(trailer[0], trailer[1])
    expected_checksum = analog_rytm_saved_kit_checksum(packed)
    if stored_checksum != expected_checksum:
        raise ValueError("Analog Rytm saved-kit checksum does not match the packed payload")
    stored_length = decode_elektron_u14(trailer[2], trailer[3])
    expected_length = len(packed) + RYTM_KIT_LENGTH_ADJUSTMENT
    if stored_length != expected_length:
        raise ValueError("Analog Rytm saved-kit encoded length does not match its trailer")

    unpacked = unpack_elektron_7bit(packed)
    if len(unpacked) != RYTM_KIT_RAW_SIZE:
        raise ValueError("Analog Rytm saved-kit payload has an unexpected unpacked length")
    return AnalogRytmSavedKitFrame(
        header=header,
        packed=packed,
        unpacked=unpacked,
        checksum=stored_checksum,
        encoded_length=stored_length,
    )


def encode_analog_rytm_saved_kit_frame(header: bytes, unpacked: bytes) -> bytes:
    """Encode one validated Rytm kit body as a complete legal SysEx frame."""

    _validate_header(header)
    if len(unpacked) != RYTM_KIT_RAW_SIZE:
        raise ValueError("Analog Rytm saved-kit body has an unexpected unpacked length")
    packed = pack_elektron_7bit(unpacked)
    if len(packed) != RYTM_KIT_PACKED_SIZE:
        raise ValueError("Analog Rytm saved-kit repacking changed the packed payload length")
    checksum = analog_rytm_saved_kit_checksum(packed)
    encoded_length = len(packed) + RYTM_KIT_LENGTH_ADJUSTMENT
    frame = (
        bytes((0xF0,))
        + header
        + packed
        + encode_elektron_u14(checksum)
        + encode_elektron_u14(encoded_length)
        + bytes((0xF7,))
    )
    decode_analog_rytm_saved_kit_frame(frame)
    return frame


__all__ = [
    "AnalogRytmSavedKitFrame",
    "analog_rytm_saved_kit_checksum",
    "decode_analog_rytm_saved_kit_frame",
    "encode_analog_rytm_saved_kit_frame",
]
