"""Shared Elektron packed-payload checksum and trailer contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from ..observability.errors import BoundaryError
from .elektron_u14 import ELEKTRON_U14_MAX, decode_elektron_u14, encode_elektron_u14
from .envelope import pack_elektron_7bit

ELEKTRON_CHECKSUM_LENGTH_TRAILER_SIZE: Final[int] = 4


class ElektronPackedPayloadError(BoundaryError, ValueError):
    """Expected validation failure at the packed-payload boundary."""

    fingerprint = "snapshot.elektron_packed_payload.invalid"


@dataclass(frozen=True)
class ElektronPackedPayload:
    """One packed body plus its verified checksum/length trailer metadata."""

    packed: bytes
    checksum: int
    encoded_length: int
    trailer: bytes


@dataclass(frozen=True)
class ElektronPackedPayloadBody:
    """One device envelope body split around its packed payload."""

    header: bytes
    packed: bytes
    trailer: bytes


def split_elektron_packed_payload_body(
    body: bytes,
    *,
    header_size: int,
    trailer_size: int,
    device_label: str,
) -> ElektronPackedPayloadBody:
    """Split a device body using explicit, device-owned envelope sizes."""

    if header_size < 0:
        raise ElektronPackedPayloadError(f"{device_label} header size cannot be negative")
    if trailer_size <= 0:
        raise ElektronPackedPayloadError(f"{device_label} trailer size must be positive")
    if len(body) < header_size + trailer_size:
        raise ElektronPackedPayloadError(f"{device_label} body is too short for its envelope")
    packed_end = len(body) - trailer_size
    return ElektronPackedPayloadBody(
        header=body[:header_size],
        packed=body[header_size:packed_end],
        trailer=body[packed_end:],
    )


def elektron_packed_payload_checksum(
    packed: bytes,
    *,
    checksum_start: int,
    device_label: str,
) -> int:
    """Return the 14-bit checksum for a device-defined packed-body slice."""

    if checksum_start < 0:
        raise ElektronPackedPayloadError(f"{device_label} checksum start cannot be negative")
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
        raise ElektronPackedPayloadError(
            f"{device_label} repacking changed the packed payload length"
        )
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
    expected_trailer_size: int,
    device_label: str,
) -> ElektronPackedPayload:
    """Validate one packed body against its device-defined integrity trailer."""

    if len(packed) != expected_packed_size:
        raise ElektronPackedPayloadError(f"{device_label} packed payload has an unexpected length")
    if expected_trailer_size != ELEKTRON_CHECKSUM_LENGTH_TRAILER_SIZE:
        raise ElektronPackedPayloadError(
            f"{device_label} expected trailer size must be "
            f"{ELEKTRON_CHECKSUM_LENGTH_TRAILER_SIZE}"
        )
    if len(trailer) != expected_trailer_size:
        raise ElektronPackedPayloadError(
            f"{device_label} integrity trailer has an unexpected length"
        )

    try:
        checksum = decode_elektron_u14(trailer[0], trailer[1])
        encoded_length = decode_elektron_u14(trailer[2], trailer[3])
    except ValueError as exc:
        raise ElektronPackedPayloadError(
            f"{device_label} integrity trailer contains an invalid 14-bit value"
        ) from exc
    expected_checksum = elektron_packed_payload_checksum(
        packed,
        checksum_start=checksum_start,
        device_label=device_label,
    )
    if checksum != expected_checksum:
        raise ElektronPackedPayloadError(
            f"{device_label} checksum does not match the packed payload"
        )

    expected_length = len(packed) + length_adjustment
    if encoded_length != expected_length:
        length_name = "packed length" if length_adjustment == 0 else "encoded length"
        raise ElektronPackedPayloadError(f"{device_label} {length_name} does not match its trailer")

    return ElektronPackedPayload(
        packed=packed,
        checksum=checksum,
        encoded_length=encoded_length,
        trailer=trailer,
    )


__all__ = [
    "ELEKTRON_CHECKSUM_LENGTH_TRAILER_SIZE",
    "ElektronPackedPayload",
    "ElektronPackedPayloadBody",
    "ElektronPackedPayloadError",
    "elektron_packed_payload_checksum",
    "encode_elektron_packed_payload",
    "split_elektron_packed_payload_body",
    "validate_elektron_packed_payload",
]
