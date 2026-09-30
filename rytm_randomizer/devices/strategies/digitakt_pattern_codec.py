"""Digitakt PATTERN dump codec.

Reads and writes the SysEx envelope a Digitakt sends from SETTINGS > SYSEX
DUMP > SYSEX SEND > PATTERN. Every envelope rule is the shared Elektron one
in :mod:`rytm_randomizer.snapshot.elektron_packed_payload`; this module owns
only the Digitakt facts from :mod:`rytm_randomizer.data.digitakt_saved_kit_layout`.

Decoding validates the header, checksum, length field and exact sizes, and
encoding reproduces a verified dump byte for byte. It performs no MIDI I/O
and grants no send authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Final

from ...data.digitakt_saved_kit_layout import (
    DIGITAKT_MK1_FAMILY_BYTE,
    DIGITAKT_MK1_PATTERN_PACKED_SIZE,
    DIGITAKT_MK1_PATTERN_UNPACKED_SIZE,
    DIGITAKT_PATTERN_CHECKSUM_PACKED_OFFSET,
    DIGITAKT_PATTERN_HEADER_SIZE_WITHOUT_F0,
    DIGITAKT_PATTERN_LENGTH_ADJUSTMENT,
    DIGITAKT_PATTERN_OBJECT_BYTE,
    DIGITAKT_PATTERN_TRAILER_SIZE,
)
from ...observability.errors import BoundaryError
from ...snapshot.elektron_packed_payload import (
    encode_elektron_packed_payload,
    validate_elektron_packed_payload,
)
from ...snapshot.envelope import ELEKTRON_MFR_ID, Elektron7BitMaskOrder, unpack_elektron_7bit

_DEVICE_LABEL: Final[str] = "Digitakt pattern"
_FAMILY_INDEX: Final[int] = len(ELEKTRON_MFR_ID)
_OBJECT_INDEX: Final[int] = 5
#: Verified by the ``BE EF BA CE`` kit marker, which unpacks only MSB-first.
_MASK_ORDER: Final[Elektron7BitMaskOrder] = Elektron7BitMaskOrder.MSB_FIRST


class DigitaktPatternCodecError(BoundaryError, ValueError):
    """Expected malformed-input failure at the Digitakt pattern boundary."""

    fingerprint: ClassVar[str] = "snapshot.digitakt_pattern.invalid"


@dataclass(frozen=True, slots=True)
class DigitaktPatternLayout:
    """Exact envelope sizes for one hardware-verified Digitakt generation."""

    family_byte: int
    packed_size: int
    unpacked_size: int


#: The only verified layout. The Digitakt II has none until it is captured.
DIGITAKT_MK1_PATTERN_LAYOUT: Final[DigitaktPatternLayout] = DigitaktPatternLayout(
    family_byte=DIGITAKT_MK1_FAMILY_BYTE,
    packed_size=DIGITAKT_MK1_PATTERN_PACKED_SIZE,
    unpacked_size=DIGITAKT_MK1_PATTERN_UNPACKED_SIZE,
)


@dataclass(frozen=True, slots=True)
class DigitaktPatternPayload:
    """A validated, unpacked Digitakt pattern dump."""

    prefix: bytes
    packed: bytes
    unpacked: bytes
    checksum: int


def is_digitakt_pattern_payload(payload: bytes, layout: DigitaktPatternLayout) -> bool:
    """Return whether ``payload``'s header claims to be a pattern for ``layout``.

    A claim, not validation: :func:`decode_digitakt_pattern_payload` checks
    the integrity trailer and sizes.
    """

    return (
        len(payload) > _OBJECT_INDEX
        and payload.startswith(ELEKTRON_MFR_ID)
        and payload[_FAMILY_INDEX] == layout.family_byte
        and payload[_OBJECT_INDEX] == DIGITAKT_PATTERN_OBJECT_BYTE
    )


def _require_pattern_prefix(prefix: bytes, layout: DigitaktPatternLayout) -> None:
    if len(prefix) != DIGITAKT_PATTERN_HEADER_SIZE_WITHOUT_F0 or not is_digitakt_pattern_payload(
        prefix, layout
    ):
        raise DigitaktPatternCodecError(
            f"not a Digitakt pattern header for family 0x{layout.family_byte:02x}"
        )


def decode_digitakt_pattern_payload(
    payload: bytes,
    layout: DigitaktPatternLayout,
) -> DigitaktPatternPayload:
    """Validate and unpack one unframed Digitakt pattern payload."""

    expected = (
        DIGITAKT_PATTERN_HEADER_SIZE_WITHOUT_F0 + layout.packed_size + DIGITAKT_PATTERN_TRAILER_SIZE
    )
    if len(payload) != expected:
        raise DigitaktPatternCodecError(
            f"Digitakt pattern payload is {len(payload)} bytes; expected {expected}"
        )
    prefix = payload[:DIGITAKT_PATTERN_HEADER_SIZE_WITHOUT_F0]
    _require_pattern_prefix(prefix, layout)
    packed = payload[DIGITAKT_PATTERN_HEADER_SIZE_WITHOUT_F0:-DIGITAKT_PATTERN_TRAILER_SIZE]
    trailer = payload[-DIGITAKT_PATTERN_TRAILER_SIZE:]
    try:
        validated = validate_elektron_packed_payload(
            packed,
            trailer,
            checksum_start=DIGITAKT_PATTERN_CHECKSUM_PACKED_OFFSET,
            length_adjustment=DIGITAKT_PATTERN_LENGTH_ADJUSTMENT,
            expected_packed_size=layout.packed_size,
            expected_trailer_size=DIGITAKT_PATTERN_TRAILER_SIZE,
            device_label=_DEVICE_LABEL,
        )
        unpacked = unpack_elektron_7bit(packed, mask_order=_MASK_ORDER)
    except ValueError as exc:
        # ElektronPackedPayloadError and the unpacker's ValueError alike.
        raise DigitaktPatternCodecError(str(exc)) from exc
    if len(unpacked) != layout.unpacked_size:
        raise DigitaktPatternCodecError(
            f"Digitakt pattern unpacks to {len(unpacked)} bytes; expected {layout.unpacked_size}"
        )
    return DigitaktPatternPayload(
        prefix=prefix,
        packed=packed,
        unpacked=unpacked,
        checksum=validated.checksum,
    )


def encode_digitakt_pattern_payload(
    prefix: bytes,
    unpacked: bytes,
    layout: DigitaktPatternLayout,
) -> bytes:
    """Pack ``unpacked`` behind ``prefix`` with a fresh checksum/length trailer."""

    _require_pattern_prefix(prefix, layout)
    if len(unpacked) != layout.unpacked_size:
        raise DigitaktPatternCodecError(
            f"Digitakt pattern body is {len(unpacked)} bytes; expected {layout.unpacked_size}"
        )
    # The size check above is the encoder's only failure mode.
    encoded = encode_elektron_packed_payload(
        unpacked,
        checksum_start=DIGITAKT_PATTERN_CHECKSUM_PACKED_OFFSET,
        length_adjustment=DIGITAKT_PATTERN_LENGTH_ADJUSTMENT,
        expected_packed_size=layout.packed_size,
        device_label=_DEVICE_LABEL,
        mask_order=_MASK_ORDER,
    )
    return prefix + encoded.packed + encoded.trailer


__all__ = [
    "DIGITAKT_MK1_PATTERN_LAYOUT",
    "DigitaktPatternCodecError",
    "DigitaktPatternLayout",
    "DigitaktPatternPayload",
    "decode_digitakt_pattern_payload",
    "encode_digitakt_pattern_payload",
    "is_digitakt_pattern_payload",
]
