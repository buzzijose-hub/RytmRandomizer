"""Shared Analog Four MKII saved-kit payload codec."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from ...data.analog_four_saved_kit_layout import (
    A4_CHECKSUM_PACKED_OFFSET,
    A4_FAMILY_BYTE,
    A4_KIT_NAME_LENGTH,
    A4_KIT_NAME_OFFSET,
    A4_KIT_OBJECT_BYTE,
    A4_PACKED_PAYLOAD_OFFSET,
    A4_SAVED_KIT_PACKED_SIZE,
    A4_SAVED_KIT_TRAILER_SIZE,
    A4_SAVED_KIT_UNPACKED_SIZE,
)
from ...snapshot import (
    ELEKTRON_MFR_ID,
    read_ascii_name,
    unpack_elektron_7bit,
)
from ...snapshot.elektron_packed_payload import (
    elektron_packed_payload_checksum,
    encode_elektron_packed_payload,
    validate_elektron_packed_payload,
)

_DEVICE_LABEL: Final[str] = "Analog Four saved-kit"


@dataclass(frozen=True)
class AnalogFourSavedKitPayload:
    """Decoded A4 saved-kit payload and its validated wire metadata."""

    prefix: bytes
    packed: bytes
    unpacked: bytes
    checksum: int
    packed_length: int
    kit_name: str
    trailer_validated: bool


@dataclass(frozen=True)
class AnalogFourEncodedSavedKitPayload:
    """Encoded A4 saved-kit payload ready for F0/F7 framing."""

    payload: bytes
    packed: bytes
    checksum: int


def analog_four_saved_kit_checksum(packed: bytes) -> int:
    """Return the observed 14-bit A4 saved-kit checksum."""

    return elektron_packed_payload_checksum(
        packed,
        checksum_start=A4_CHECKSUM_PACKED_OFFSET,
        device_label=_DEVICE_LABEL,
    )


def _clean_saved_kit_name(name: str) -> str:
    return name.replace("\x00", "").strip()


def _validated_trailer(packed: bytes, trailer: bytes) -> tuple[int, int]:
    validated = validate_elektron_packed_payload(
        packed,
        trailer,
        checksum_start=A4_CHECKSUM_PACKED_OFFSET,
        length_adjustment=0,
        expected_packed_size=A4_SAVED_KIT_PACKED_SIZE,
        expected_trailer_size=A4_SAVED_KIT_TRAILER_SIZE,
        device_label=_DEVICE_LABEL,
    )
    return validated.checksum, validated.encoded_length


def decode_analog_four_saved_kit_payload(
    payload: bytes,
    *,
    require_trailer: bool,
) -> AnalogFourSavedKitPayload:
    """Decode and validate one unframed A4 saved-kit SysEx payload."""

    if not payload.startswith(ELEKTRON_MFR_ID):
        raise ValueError("SysEx manufacturer is not Elektron 00:20:3C")
    if len(payload) <= A4_PACKED_PAYLOAD_OFFSET:
        raise ValueError("Analog Four saved-kit payload is too short")
    if payload[len(ELEKTRON_MFR_ID)] != A4_FAMILY_BYTE:
        raise ValueError("SysEx family is not Analog Four 0x06")

    body = payload[A4_PACKED_PAYLOAD_OFFSET:]
    has_hardware_trailer = len(body) == A4_SAVED_KIT_PACKED_SIZE + A4_SAVED_KIT_TRAILER_SIZE
    if require_trailer and len(body) <= A4_SAVED_KIT_TRAILER_SIZE:
        raise ValueError("Analog Four saved-kit payload is too short")
    if require_trailer or has_hardware_trailer:
        packed = body[:-A4_SAVED_KIT_TRAILER_SIZE]
        trailer = body[-A4_SAVED_KIT_TRAILER_SIZE:]
        checksum, packed_length = _validated_trailer(packed, trailer)
        trailer_validated = True
    else:
        packed = body
        checksum = analog_four_saved_kit_checksum(packed)
        packed_length = len(packed)
        trailer_validated = False

    unpacked = unpack_elektron_7bit(packed)
    if require_trailer and len(unpacked) != A4_SAVED_KIT_UNPACKED_SIZE:
        raise ValueError(
            "Analog Four saved-kit unpacked payload has unexpected length "
            f"{len(unpacked)}; expected {A4_SAVED_KIT_UNPACKED_SIZE}"
        )
    if len(unpacked) < A4_KIT_NAME_OFFSET + A4_KIT_NAME_LENGTH:
        raise ValueError("Analog Four saved-kit unpacked payload is too short for kit name")
    if unpacked[0] != A4_KIT_OBJECT_BYTE:
        raise ValueError("Analog Four kit object byte is not a saved kit")
    kit_name = _clean_saved_kit_name(
        read_ascii_name(unpacked, A4_KIT_NAME_OFFSET, A4_KIT_NAME_LENGTH)
    )
    return AnalogFourSavedKitPayload(
        prefix=payload[:A4_PACKED_PAYLOAD_OFFSET],
        packed=packed,
        unpacked=unpacked,
        checksum=checksum,
        packed_length=packed_length,
        kit_name=kit_name,
        trailer_validated=trailer_validated,
    )


def encode_analog_four_saved_kit_payload(
    prefix: bytes,
    unpacked: bytes,
) -> AnalogFourEncodedSavedKitPayload:
    """Encode one validated A4 saved-kit body with checksum/length trailer."""

    if not prefix.startswith(ELEKTRON_MFR_ID) or len(prefix) != A4_PACKED_PAYLOAD_OFFSET:
        raise ValueError("Analog Four saved-kit prefix is invalid")
    if prefix[len(ELEKTRON_MFR_ID)] != A4_FAMILY_BYTE:
        raise ValueError("Analog Four saved-kit prefix has the wrong family")
    if len(unpacked) != A4_SAVED_KIT_UNPACKED_SIZE:
        raise ValueError("Analog Four saved-kit body has an unexpected unpacked length")
    if unpacked[0] != A4_KIT_OBJECT_BYTE:
        raise ValueError("Analog Four kit object byte is not a saved kit")

    encoded = encode_elektron_packed_payload(
        unpacked,
        checksum_start=A4_CHECKSUM_PACKED_OFFSET,
        length_adjustment=0,
        expected_packed_size=A4_SAVED_KIT_PACKED_SIZE,
        device_label=_DEVICE_LABEL,
    )
    return AnalogFourEncodedSavedKitPayload(
        payload=prefix + encoded.packed + encoded.trailer,
        packed=encoded.packed,
        checksum=encoded.checksum,
    )


__all__ = [
    "AnalogFourEncodedSavedKitPayload",
    "AnalogFourSavedKitPayload",
    "analog_four_saved_kit_checksum",
    "decode_analog_four_saved_kit_payload",
    "encode_analog_four_saved_kit_payload",
]
