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
from .elektron_u14 import ELEKTRON_U14_MAX, decode_elektron_u14, encode_elektron_u14
from .envelope import ELEKTRON_MFR_ID

_WIRE_HEADER_SIZE: Final[int] = 10
_WIRE_TRAILER_SIZE: Final[int] = 5


class ElektronNativeObjectError(BoundaryError, ValueError):
    """Malformed or unsupported Elektron native-object message."""

    fingerprint: ClassVar[str] = "boundary.elektron.native_object"


def pack_elektron_native_object(payload: bytes) -> bytes:
    """Pack native bytes with the target-validated Elektron MSB-mask order."""

    packed = bytearray()
    for start in range(0, len(payload), 7):
        group = payload[start : start + 7]
        mask = 0
        lows = bytearray()
        for index, value in enumerate(group):
            if value & 0x80:
                mask |= 1 << (6 - index)
            lows.append(value & 0x7F)
        packed.append(mask)
        packed.extend(lows)
    return bytes(packed)


def unpack_elektron_native_object(packed: bytes) -> bytes:
    """Unpack target-validated Elektron object bytes from MIDI-safe data."""

    if any(value > 0x7F for value in packed):
        raise ElektronNativeObjectError(
            "Packed Elektron native-object payload contains a non-MIDI-safe byte"
        )
    unpacked = bytearray()
    cursor = 0
    while cursor < len(packed):
        mask = packed[cursor]
        cursor += 1
        count = min(7, len(packed) - cursor)
        if count == 0:
            raise ElektronNativeObjectError(
                "Packed Elektron native-object payload ends with an empty mask group"
            )
        for index in range(count):
            value = packed[cursor + index]
            value |= ((mask >> (6 - index)) & 1) << 7
            unpacked.append(value)
        cursor += count
    return bytes(unpacked)


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

        packed = frame[_WIRE_HEADER_SIZE:-_WIRE_TRAILER_SIZE]
        stored_checksum = decode_elektron_u14(frame[-5], frame[-4])
        expected_checksum = sum(packed) & ELEKTRON_U14_MAX
        if stored_checksum != expected_checksum:
            raise ElektronNativeObjectError(
                "Elektron object checksum does not match the packed payload"
            )
        stored_length = decode_elektron_u14(frame[-3], frame[-2])
        expected_length = len(frame) - _WIRE_HEADER_SIZE
        if stored_length != expected_length:
            raise ElektronNativeObjectError(
                "Elektron object encoded length does not match the frame"
            )

        return cls(
            product_id=frame[4],
            device_id=frame[5],
            command=frame[6],
            format_version=frame[7],
            format_revision=frame[8],
            slot=frame[9],
            payload=unpack_elektron_native_object(packed),
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

        packed = pack_elektron_native_object(self.payload)
        checksum = sum(packed) & ELEKTRON_U14_MAX
        encoded_length = len(packed) + _WIRE_TRAILER_SIZE
        frame = (
            bytes((0xF0,))
            + ELEKTRON_MFR_ID
            + bytes(header_values)
            + packed
            + encode_elektron_u14(checksum)
            + encode_elektron_u14(encoded_length)
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
