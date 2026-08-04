"""Shared Elektron packed-payload checksum and trailer contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .elektron_u14 import ELEKTRON_U14_MAX, decode_elektron_u14, encode_elektron_u14
from .envelope import pack_elektron_7bit

_TRAILER_SIZE: Final[int] = 4


@dataclass(frozen=True)
class ElektronPackedPayload:
    """One packed body plus its verified checksum/length trailer metadata."""

    packed: bytes
    checksum: int
    encoded_length: int
    trailer: bytes


def elektron_packed_payload_checksum(
    packed: bytes,
    *,
    checksum_start: int,
    device_label: str,
) -> int:
    """Return the 14-bit checksum for a device-defined packed-body slice."""

    if checksum_start < 0:
        raise ValueError(f"{device_label} checksum start cannot be negative")
    return sum(packed[checksum_start:]) & ELEKTRON_U14_MAX


def encode_elektron_packed_payload(
    unpacked: bytes,
    *,
    checksum_start: int,
    length_adjustment: int,
    expected_packed_size: int,
    device_label: str,
) -> ElektronPackedPayload:
    """Pack one body and append its device-defined checksum/length trailer."""

    packed = pack_elektron_7bit(unpacked)
    if len(packed) != expected_packed_size:
        raise ValueError(f"{device_label} repacking changed the packed payload length")
    checksum = elektron_packed_payload_checksum(
        packed,
        checksum_start=checksum_start,
        device_label=device_label,
    )
    encoded_length = len(packed) + length_adjustment
    trailer = encode_elektron_u14(checksum) + encode_elektron_u14(encoded_length)
    return ElektronPackedPayload(
        packed=packed,
        checksum=checksum,
        encoded_length=encoded_length,
        trailer=trailer,
    )


def validate_elektron_packed_payload(
    packed: bytes,
    trailer: bytes,
    *,
    checksum_start: int,
    length_adjustment: int,
    expected_packed_size: int,
    device_label: str,
) -> ElektronPackedPayload:
    """Validate one packed body against its device-defined integrity trailer."""

    if len(packed) != expected_packed_size:
        raise ValueError(f"{device_label} packed payload has an unexpected length")
    if len(trailer) != _TRAILER_SIZE:
        raise ValueError(f"{device_label} integrity trailer has an unexpected length")

    checksum = decode_elektron_u14(trailer[0], trailer[1])
    expected_checksum = elektron_packed_payload_checksum(
        packed,
        checksum_start=checksum_start,
        device_label=device_label,
    )
    if checksum != expected_checksum:
        raise ValueError(f"{device_label} checksum does not match the packed payload")

    encoded_length = decode_elektron_u14(trailer[2], trailer[3])
    expected_length = len(packed) + length_adjustment
    if encoded_length != expected_length:
        length_name = "packed length" if length_adjustment == 0 else "encoded length"
        raise ValueError(f"{device_label} {length_name} does not match its trailer")

    return ElektronPackedPayload(
        packed=packed,
        checksum=checksum,
        encoded_length=encoded_length,
        trailer=trailer,
    )


__all__ = [
    "ElektronPackedPayload",
    "elektron_packed_payload_checksum",
    "encode_elektron_packed_payload",
    "validate_elektron_packed_payload",
]
