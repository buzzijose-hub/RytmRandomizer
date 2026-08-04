"""Pure Analog Rytm MKII saved-kit SysEx frame codec."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Final

from ...data.analog_rytm_kit_layout import (
    RYTM_KIT_CHECKSUM_PACKED_START,
    RYTM_KIT_DUMP_ID,
    RYTM_KIT_FRAME_SIZE,
    RYTM_KIT_LENGTH_ADJUSTMENT,
    RYTM_KIT_PACKED_SIZE,
    RYTM_KIT_RAW_SIZE,
    RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0,
    RYTM_KIT_SYSEX_TRAILER_SIZE_WITHOUT_F7,
    RYTM_KIT_WORK_BUFFER_DUMP_ID,
    RYTM_SYSEX_PRODUCT_ID,
)
from ...observability.errors import BoundaryError
from ...snapshot import ELEKTRON_MFR_ID, unpack_elektron_7bit
from ...snapshot.elektron_packed_payload import (
    ElektronPackedPayloadError,
    elektron_packed_payload_checksum,
    encode_elektron_packed_payload,
    split_elektron_packed_payload_body,
    validate_elektron_packed_payload,
)

_DUMP_ID_INDEX: Final[int] = 5
_DEVICE_LABEL: Final[str] = "Analog Rytm saved-kit"


class AnalogRytmSavedKitCodecError(BoundaryError, ValueError):
    """Expected malformed-input failure at the Rytm saved-kit boundary."""

    fingerprint: ClassVar[str] = "snapshot.analog_rytm_saved_kit.invalid"


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

    return elektron_packed_payload_checksum(
        packed,
        checksum_start=RYTM_KIT_CHECKSUM_PACKED_START,
        device_label=_DEVICE_LABEL,
    )


def _validate_header(header: bytes) -> None:
    if len(header) != RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0:
        raise AnalogRytmSavedKitCodecError("Analog Rytm kit SysEx header has an unexpected length")
    if not header.startswith(ELEKTRON_MFR_ID + bytes((RYTM_SYSEX_PRODUCT_ID,))):
        raise AnalogRytmSavedKitCodecError("SysEx header is not an Analog Rytm Elektron kit header")
    if header[_DUMP_ID_INDEX] not in (RYTM_KIT_DUMP_ID, RYTM_KIT_WORK_BUFFER_DUMP_ID):
        raise AnalogRytmSavedKitCodecError("Analog Rytm SysEx object is not a kit dump")


def decode_analog_rytm_saved_kit_frame(frame: bytes) -> AnalogRytmSavedKitFrame:
    """Decode and validate one complete F0/F7-framed Rytm saved-kit dump."""

    if len(frame) != RYTM_KIT_FRAME_SIZE:
        raise AnalogRytmSavedKitCodecError(
            f"Analog Rytm saved-kit frame length is {len(frame)}; "
            f"expected {RYTM_KIT_FRAME_SIZE}"
        )
    if frame[0] != 0xF0 or frame[-1] != 0xF7:
        raise AnalogRytmSavedKitCodecError("Analog Rytm saved-kit SysEx framing is invalid")
    if any(value > 0x7F for value in frame[1:-1]):
        raise AnalogRytmSavedKitCodecError(
            "Analog Rytm saved-kit SysEx contains an illegal data byte"
        )

    try:
        body = split_elektron_packed_payload_body(
            frame[1:-1],
            header_size=RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0,
            trailer_size=RYTM_KIT_SYSEX_TRAILER_SIZE_WITHOUT_F7,
            device_label=_DEVICE_LABEL,
        )
    except ElektronPackedPayloadError as exc:
        raise AnalogRytmSavedKitCodecError(str(exc)) from exc
    _validate_header(body.header)

    try:
        validated = validate_elektron_packed_payload(
            body.packed,
            body.trailer,
            checksum_start=RYTM_KIT_CHECKSUM_PACKED_START,
            length_adjustment=RYTM_KIT_LENGTH_ADJUSTMENT,
            expected_packed_size=RYTM_KIT_PACKED_SIZE,
            expected_trailer_size=RYTM_KIT_SYSEX_TRAILER_SIZE_WITHOUT_F7,
            device_label=_DEVICE_LABEL,
        )
    except ElektronPackedPayloadError as exc:
        raise AnalogRytmSavedKitCodecError(str(exc)) from exc

    unpacked = unpack_elektron_7bit(body.packed)
    if len(unpacked) != RYTM_KIT_RAW_SIZE:
        raise AnalogRytmSavedKitCodecError(
            "Analog Rytm saved-kit payload has an unexpected unpacked length"
        )
    return AnalogRytmSavedKitFrame(
        header=body.header,
        packed=body.packed,
        unpacked=unpacked,
        checksum=validated.checksum,
        encoded_length=validated.encoded_length,
    )


def encode_analog_rytm_saved_kit_frame(header: bytes, unpacked: bytes) -> bytes:
    """Encode one validated Rytm kit body as a complete legal SysEx frame."""

    _validate_header(header)
    if len(unpacked) != RYTM_KIT_RAW_SIZE:
        raise AnalogRytmSavedKitCodecError(
            "Analog Rytm saved-kit body has an unexpected unpacked length"
        )
    try:
        encoded = encode_elektron_packed_payload(
            unpacked,
            checksum_start=RYTM_KIT_CHECKSUM_PACKED_START,
            length_adjustment=RYTM_KIT_LENGTH_ADJUSTMENT,
            expected_packed_size=RYTM_KIT_PACKED_SIZE,
            device_label=_DEVICE_LABEL,
        )
    except ElektronPackedPayloadError as exc:
        raise AnalogRytmSavedKitCodecError(str(exc)) from exc
    frame = bytes((0xF0,)) + header + encoded.packed + encoded.trailer + bytes((0xF7,))
    decode_analog_rytm_saved_kit_frame(frame)
    return frame


__all__ = [
    "AnalogRytmSavedKitCodecError",
    "AnalogRytmSavedKitFrame",
    "analog_rytm_saved_kit_checksum",
    "decode_analog_rytm_saved_kit_frame",
    "encode_analog_rytm_saved_kit_frame",
]
