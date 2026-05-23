"""Binary header layout for the cockpit ``ProfileModel`` export format.

This module owns the byte-level shape — the ``RYMP`` magic, the format
version, the per-payload ``model_version`` string, the payload length, and
the CRC32 trailer. It deliberately has **no dependency on the data layer**;
the payload is treated as opaque bytes here. ``serialize.py`` builds those
bytes from a :class:`~rytm_randomizer.cockpit.data.ProfileModel` via
MessagePack.

Format (big-endian, per spec §"Model Export"):

    Header:
        magic:              4 bytes  ("RYMP" ascii)
        format_version:     uint16   (currently 1)
        model_version_len:  uint8    (length of the version string)
        model_version:      utf-8 bytes (e.g. ``"1.2.0"`` -> 5 bytes)
        payload_len:        uint32
    Payload:
        MessagePack-encoded ``ProfileModel.to_dict()``
    Trailer:
        crc32:              uint32   (CRC32 of header + payload via :func:`zlib.crc32`)

The fixed header prefix (magic + format_version + model_version_len) is 7
bytes; total header length depends on ``model_version_len``. The trailer is
always 4 bytes. The shape is intentionally narrow — the embedded loader
(Phase 4) parses these bytes with a hand-written C reader; widening the
header here means widening the firmware too.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from typing import Final

# ---------------------------------------------------------------------------
# Format constants
# ---------------------------------------------------------------------------

MAGIC: Final[bytes] = b"RYMP"
"""Four-byte magic prefix identifying a cockpit ``ProfileModel`` blob."""

FORMAT_VERSION: Final[int] = 1
"""Current format version emitted by :func:`pack_profile_model`."""

SUPPORTED_FORMAT_VERSIONS: Final[frozenset[int]] = frozenset({1})
"""Format versions :func:`unpack_profile_model` will accept.

New versions are added here as the format evolves; older readers must reject
unknown versions with :class:`ValueError` (the embedded firmware does the
same).
"""

# Struct format strings for the two fixed-width pieces of the header. Using
# explicit big-endian (``>``) keeps the wire-format identical across
# big-/little-endian host machines and across language runtimes.
_FIXED_HEADER_STRUCT: Final[struct.Struct] = struct.Struct(">4sHB")
"""magic (4s) + format_version (uint16) + model_version_len (uint8)."""

_PAYLOAD_LEN_STRUCT: Final[struct.Struct] = struct.Struct(">I")
"""payload_len (uint32) — read after the variable-length model_version."""

_CRC_STRUCT: Final[struct.Struct] = struct.Struct(">I")
"""crc32 trailer (uint32)."""

# Fixed-width sub-lengths in bytes.
_FIXED_HEADER_LEN: Final[int] = _FIXED_HEADER_STRUCT.size  # 7
_PAYLOAD_LEN_FIELD_LEN: Final[int] = _PAYLOAD_LEN_STRUCT.size  # 4
_CRC_LEN: Final[int] = _CRC_STRUCT.size  # 4

# A uint8 holds [0, 255]; ``model_version`` strings cannot exceed 255 utf-8
# bytes. Semver strings are tiny so this is generous; the cap exists to keep
# the wire format unambiguous.
_MODEL_VERSION_MAX_LEN: Final[int] = 0xFF

# A uint32 holds [0, 4_294_967_295]; payloads must fit. Profiles are < 100 KB
# in practice; the cap exists for the same wire-format reason.
_PAYLOAD_MAX_LEN: Final[int] = 0xFFFF_FFFF


# ---------------------------------------------------------------------------
# Header dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Header:
    """Parsed view of the export-format header.

    Returned by :func:`parse_header` so callers can validate the magic,
    format-version, and the location of the payload (its offset and length)
    without re-doing the byte arithmetic inline.
    """

    format_version: int
    model_version: str
    payload_len: int
    header_len: int
    """Total byte length of the header on the wire (fixed prefix +
    ``model_version`` bytes + payload-length field). The payload starts at
    this offset within the blob."""


# ---------------------------------------------------------------------------
# Build / parse — header only
# ---------------------------------------------------------------------------


def build_header(*, format_version: int, model_version: str, payload_len: int) -> bytes:
    """Serialize the header for a given payload.

    Validates the field widths so callers (here in ``serialize.py``, and any
    future direct user) cannot accidentally emit a blob the parser would
    reject as truncated.

    Raises:
        ValueError: ``format_version`` does not fit in a uint16, the encoded
            ``model_version`` exceeds 255 bytes, or ``payload_len`` does not
            fit in a uint32.
    """

    if not (0 <= format_version <= 0xFFFF):
        raise ValueError(f"format_version must fit in uint16 [0, 65535]; got {format_version}")
    model_version_bytes = model_version.encode("utf-8")
    if len(model_version_bytes) > _MODEL_VERSION_MAX_LEN:
        raise ValueError(
            "model_version must encode to at most "
            f"{_MODEL_VERSION_MAX_LEN} utf-8 bytes; got {len(model_version_bytes)}"
        )
    if not (0 <= payload_len <= _PAYLOAD_MAX_LEN):
        raise ValueError(
            f"payload_len must fit in uint32 [0, {_PAYLOAD_MAX_LEN}]; got {payload_len}"
        )
    fixed = _FIXED_HEADER_STRUCT.pack(MAGIC, format_version, len(model_version_bytes))
    return fixed + model_version_bytes + _PAYLOAD_LEN_STRUCT.pack(payload_len)


def parse_header(blob: bytes) -> Header:
    """Parse the header from the front of ``blob``.

    Does not validate ``format_version`` against :data:`SUPPORTED_FORMAT_VERSIONS`
    — that policy lives in :func:`~rytm_randomizer.cockpit.export.serialize.unpack_profile_model`
    so the format-version error message can name the supported set.

    Raises:
        ValueError: ``blob`` is shorter than the fixed header prefix, the
            magic does not match ``RYMP``, the ``model_version`` declared in
            the header would run past the end of the blob, or the
            payload-length field is truncated.
    """

    if len(blob) < _FIXED_HEADER_LEN:
        raise ValueError(
            "truncated input: blob shorter than fixed header "
            f"({len(blob)} < {_FIXED_HEADER_LEN} bytes)"
        )
    magic, format_version, model_version_len = _FIXED_HEADER_STRUCT.unpack_from(blob, 0)
    if magic != MAGIC:
        raise ValueError(f"bad magic: expected {MAGIC!r}, got {magic!r}")
    model_version_start = _FIXED_HEADER_LEN
    model_version_end = model_version_start + model_version_len
    payload_len_field_end = model_version_end + _PAYLOAD_LEN_FIELD_LEN
    if len(blob) < payload_len_field_end:
        raise ValueError(
            "truncated input: blob ends inside header "
            f"(need {payload_len_field_end} bytes for header, got {len(blob)})"
        )
    try:
        model_version = blob[model_version_start:model_version_end].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"malformed header: model_version is not valid utf-8: {exc}") from exc
    (payload_len,) = _PAYLOAD_LEN_STRUCT.unpack_from(blob, model_version_end)
    return Header(
        format_version=format_version,
        model_version=model_version,
        payload_len=payload_len,
        header_len=payload_len_field_end,
    )


# ---------------------------------------------------------------------------
# CRC trailer
# ---------------------------------------------------------------------------


def compute_crc(header_and_payload: bytes) -> int:
    """Compute the CRC32 trailer of ``header_and_payload`` via :func:`zlib.crc32`.

    Wraps :func:`zlib.crc32` so the call site is self-documenting and so the
    masking to a 32-bit unsigned int is in exactly one place (zlib returns a
    signed int on some historical platforms; ``& 0xFFFFFFFF`` is the
    standard normalization).
    """

    return zlib.crc32(header_and_payload) & 0xFFFFFFFF


def pack_crc(crc: int) -> bytes:
    """Serialize ``crc`` as the 4-byte big-endian trailer."""

    return _CRC_STRUCT.pack(crc)


def unpack_crc(blob: bytes, offset: int) -> int:
    """Parse the 4-byte CRC trailer from ``blob`` at ``offset``.

    Raises:
        ValueError: ``blob`` does not contain a full 4 bytes at ``offset``.
    """

    if len(blob) < offset + _CRC_LEN:
        raise ValueError(
            "truncated input: blob ends before CRC trailer "
            f"(need {offset + _CRC_LEN} bytes, got {len(blob)})"
        )
    (crc,) = _CRC_STRUCT.unpack_from(blob, offset)
    return crc


__all__ = [
    "FORMAT_VERSION",
    "Header",
    "MAGIC",
    "SUPPORTED_FORMAT_VERSIONS",
    "build_header",
    "compute_crc",
    "pack_crc",
    "parse_header",
    "unpack_crc",
]
