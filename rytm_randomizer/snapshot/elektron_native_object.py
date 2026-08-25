"""Target-return-validated Elektron object-message codec.

This boundary preserves the native 8-bit object bytes exposed by current
Analog Four and Analog Rytm KIT dumps.  It intentionally lives alongside the
repository's frozen generic envelope helpers: changing those helpers would
alter established snapshot behavior, while semantic KIT editing needs the
MSB-mask order verified by the RIO145 return fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import ClassVar, Final

from ..observability.errors import BoundaryError
from .elektron_packed_payload import (
    ELEKTRON_CHECKSUM_LENGTH_TRAILER_SIZE,
    ElektronPackedPayloadError,
    encode_elektron_packed_payload,
    split_elektron_packed_payload_body,
    validate_elektron_packed_payload,
)
from .envelope import (
    ELEKTRON_MFR_ID,
    Elektron7BitMaskOrder,
    pack_elektron_7bit,
    unpack_elektron_7bit,
)

_WIRE_HEADER_SIZE: Final[int] = 10
_WIRE_TRAILER_SIZE: Final[int] = 5
_BODY_HEADER_SIZE: Final[int] = _WIRE_HEADER_SIZE - 1
_BODY_TRAILER_SIZE: Final[int] = _WIRE_TRAILER_SIZE - 1
_LENGTH_ADJUSTMENT: Final[int] = _WIRE_TRAILER_SIZE
_DEVICE_LABEL: Final[str] = "Elektron native object"


class ElektronNativeObjectError(BoundaryError, ValueError):
    """Malformed or unsupported Elektron native-object message."""

    fingerprint: ClassVar[str] = "boundary.elektron.native_object"


def pack_elektron_native_object(payload: bytes) -> bytes:
    """Pack native bytes with the target-validated Elektron MSB-mask order."""

    return pack_elektron_7bit(
        payload,
        mask_order=Elektron7BitMaskOrder.MSB_FIRST,
    )


def unpack_elektron_native_object(packed: bytes) -> bytes:
    """Unpack target-validated Elektron object bytes from MIDI-safe data."""

    try:
        return unpack_elektron_7bit(
            packed,
            mask_order=Elektron7BitMaskOrder.MSB_FIRST,
        )
    except ValueError as exc:
        raise ElektronNativeObjectError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class ElektronNativeObjectMessage:
    """One validated Elektron object dump with native 8-bit payload bytes."""

    product_id: int
    device_id: int
    command: int
    format_version: int
    format_revision: int
    slot: int
    payload: bytes

    @classmethod
    def from_bytes(cls, frame: bytes) -> ElektronNativeObjectMessage:
        """Parse and validate one complete F0/F7-framed object message."""

        if len(frame) < _WIRE_HEADER_SIZE + _WIRE_TRAILER_SIZE:
            raise ElektronNativeObjectError("Elektron object message is too short")
        if frame[0] != 0xF0 or frame[-1] != 0xF7:
            raise ElektronNativeObjectError("Elektron object message lacks F0/F7 framing")
        if frame[1:4] != ELEKTRON_MFR_ID:
            raise ElektronNativeObjectError("Elektron object manufacturer ID is invalid")
        if any(value > 0x7F for value in frame[1:-1]):
            raise ElektronNativeObjectError(
                "Elektron object message contains a non-MIDI-safe data byte"
            )

        try:
            body = split_elektron_packed_payload_body(
                frame[1:-1],
                header_size=_BODY_HEADER_SIZE,
                trailer_size=_BODY_TRAILER_SIZE,
                device_label=_DEVICE_LABEL,
            )
            validate_elektron_packed_payload(
                body.packed,
                body.trailer,
                checksum_start=0,
                length_adjustment=_LENGTH_ADJUSTMENT,
                expected_packed_size=None,
                expected_trailer_size=ELEKTRON_CHECKSUM_LENGTH_TRAILER_SIZE,
                device_label=_DEVICE_LABEL,
            )
        except ElektronPackedPayloadError as exc:
            raise ElektronNativeObjectError(str(exc)) from exc

        return cls(
            product_id=body.header[3],
            device_id=body.header[4],
            command=body.header[5],
            format_version=body.header[6],
            format_revision=body.header[7],
            slot=body.header[8],
            payload=unpack_elektron_native_object(body.packed),
        )

    def to_bytes(self) -> bytes:
        """Serialize with fresh packing, checksum, and encoded length."""

        header_values = (
            self.product_id,
            self.device_id,
            self.command,
            self.format_version,
            self.format_revision,
            self.slot,
        )
        if any(not 0 <= value <= 0x7F for value in header_values):
            raise ValueError("Elektron object header values must be in the range 0..127")

        try:
            encoded = encode_elektron_packed_payload(
                self.payload,
                checksum_start=0,
                length_adjustment=_LENGTH_ADJUSTMENT,
                expected_packed_size=None,
                device_label=_DEVICE_LABEL,
                mask_order=Elektron7BitMaskOrder.MSB_FIRST,
            )
        except ElektronPackedPayloadError as exc:
            raise ElektronNativeObjectError(str(exc)) from exc
        frame = (
            bytes((0xF0,))
            + ELEKTRON_MFR_ID
            + bytes(header_values)
            + encoded.packed
            + encoded.trailer
            + bytes((0xF7,))
        )
        ElektronNativeObjectMessage.from_bytes(frame)
        return frame

    def with_payload(self, payload: bytes) -> ElektronNativeObjectMessage:
        """Return a copy carrying replacement native object bytes."""

        return replace(self, payload=bytes(payload))

    def with_slot(self, slot: int) -> ElektronNativeObjectMessage:
        """Return a copy targeting a zero-based destination slot."""

        if not 0 <= slot <= 0x7F:
            raise ValueError("Elektron object slot must be in the range 0..127")
        return replace(self, slot=slot)


__all__ = [
    "ElektronNativeObjectError",
    "ElektronNativeObjectMessage",
    "pack_elektron_native_object",
    "unpack_elektron_native_object",
]
