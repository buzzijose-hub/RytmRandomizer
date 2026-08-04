"""Shared helpers for Elektron unsigned 14-bit wire values."""

from __future__ import annotations

from typing import Final

ELEKTRON_U14_MAX: Final[int] = 0x3FFF


def decode_elektron_u14(high: int, low: int) -> int:
    """Decode two legal 7-bit data bytes as one unsigned 14-bit value."""

    if not 0 <= high <= 0x7F or not 0 <= low <= 0x7F:
        raise ValueError("Elektron 14-bit bytes must each be in the range 0..127")
    return (high << 7) | low


def encode_elektron_u14(value: int) -> bytes:
    """Encode one unsigned 14-bit value as two legal 7-bit data bytes."""

    if not 0 <= value <= ELEKTRON_U14_MAX:
        raise ValueError("Elektron 14-bit value is outside 0..16383")
    return bytes(((value >> 7) & 0x7F, value & 0x7F))


__all__ = [
    "ELEKTRON_U14_MAX",
    "decode_elektron_u14",
    "encode_elektron_u14",
]
