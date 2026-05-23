"""Tests for ``rytm_randomizer.cockpit.export.model_format``.

The format module owns the byte-level header / CRC discipline of the
cockpit ``ProfileModel`` export pipeline. These tests cover its public
build/parse surface exhaustively (every guard branch) so the corresponding
end-to-end pack/unpack tests in ``test_export_serialize.py`` can stay
focused on the round-trip parity rather than re-asserting wire-format
mechanics.
"""

from __future__ import annotations

import struct
import zlib

import pytest

from rytm_randomizer.cockpit.export.model_format import (
    FORMAT_VERSION,
    MAGIC,
    SUPPORTED_FORMAT_VERSIONS,
    Header,
    build_header,
    compute_crc,
    pack_crc,
    parse_header,
    unpack_crc,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_magic_is_rymp_ascii() -> None:
    assert MAGIC == b"RYMP"
    assert len(MAGIC) == 4


def test_format_version_default_is_one() -> None:
    assert FORMAT_VERSION == 1


def test_supported_format_versions_includes_current() -> None:
    assert FORMAT_VERSION in SUPPORTED_FORMAT_VERSIONS


# ---------------------------------------------------------------------------
# build_header
# ---------------------------------------------------------------------------


def test_build_header_layout_matches_spec() -> None:
    blob = build_header(format_version=1, model_version="1.2.0", payload_len=42)
    # 4 magic + 2 fmt_ver + 1 ver_len + 5 ver_bytes + 4 payload_len = 16
    assert len(blob) == 4 + 2 + 1 + 5 + 4
    assert blob[:4] == MAGIC
    assert struct.unpack(">H", blob[4:6])[0] == 1
    assert blob[6] == 5  # model_version_len
    assert blob[7:12] == b"1.2.0"
    assert struct.unpack(">I", blob[12:16])[0] == 42


def test_build_header_accepts_empty_model_version_string() -> None:
    blob = build_header(format_version=1, model_version="", payload_len=0)
    # Header still validly parses; consumers (ProfileModel) reject empty
    # strings at the dataclass layer, but the format itself permits it.
    header = parse_header(blob)
    assert header.model_version == ""
    assert header.payload_len == 0


def test_build_header_accepts_unicode_model_version() -> None:
    # The spec says utf-8 — a non-ASCII semver-ish string must round-trip.
    label = "1.0.0-β"
    blob = build_header(format_version=1, model_version=label, payload_len=0)
    header = parse_header(blob)
    assert header.model_version == label


def test_build_header_rejects_negative_format_version() -> None:
    with pytest.raises(ValueError, match="format_version"):
        build_header(format_version=-1, model_version="1", payload_len=0)


def test_build_header_rejects_oversized_format_version() -> None:
    with pytest.raises(ValueError, match="format_version"):
        build_header(format_version=0x1_0000, model_version="1", payload_len=0)


def test_build_header_rejects_oversized_model_version() -> None:
    # A 256-byte ASCII string overflows uint8.
    too_long = "x" * 256
    with pytest.raises(ValueError, match="model_version"):
        build_header(format_version=1, model_version=too_long, payload_len=0)


def test_build_header_accepts_max_length_model_version() -> None:
    # Exactly 255 utf-8 bytes is the boundary case that MUST be accepted.
    boundary = "y" * 255
    blob = build_header(format_version=1, model_version=boundary, payload_len=0)
    header = parse_header(blob)
    assert header.model_version == boundary


def test_build_header_rejects_negative_payload_len() -> None:
    with pytest.raises(ValueError, match="payload_len"):
        build_header(format_version=1, model_version="1", payload_len=-1)


def test_build_header_rejects_oversized_payload_len() -> None:
    with pytest.raises(ValueError, match="payload_len"):
        build_header(format_version=1, model_version="1", payload_len=0x1_0000_0000)


# ---------------------------------------------------------------------------
# parse_header
# ---------------------------------------------------------------------------


def test_parse_header_returns_frozen_dataclass() -> None:
    blob = build_header(format_version=1, model_version="1.0", payload_len=7)
    header = parse_header(blob + b"\x00" * 11)  # trailing payload + crc area
    assert isinstance(header, Header)
    assert header.format_version == 1
    assert header.model_version == "1.0"
    assert header.payload_len == 7
    assert header.header_len == len(blob)


def test_parse_header_rejects_blob_shorter_than_fixed_prefix() -> None:
    # Fixed header is 7 bytes (4 magic + 2 fmt_ver + 1 ver_len). 6 bytes
    # should fail the first length check before any magic comparison.
    with pytest.raises(ValueError, match="truncated"):
        parse_header(b"\x00" * 6)


def test_parse_header_rejects_bad_magic() -> None:
    bad = b"NOPE" + b"\x00\x01" + b"\x00" + b"\x00\x00\x00\x00"
    with pytest.raises(ValueError, match="bad magic"):
        parse_header(bad)


def test_parse_header_rejects_blob_truncated_inside_model_version() -> None:
    # Declare model_version_len=10 but only supply 3 bytes after the
    # fixed header — the payload_len field cannot be read.
    truncated = MAGIC + struct.pack(">H", 1) + bytes([10]) + b"abc"
    with pytest.raises(ValueError, match="truncated"):
        parse_header(truncated)


def test_parse_header_rejects_invalid_utf8_in_model_version() -> None:
    # Declare model_version_len=2 and supply two bytes that aren't valid
    # utf-8 (0xff 0xff is never a legal utf-8 sequence).
    bad = MAGIC + struct.pack(">H", 1) + bytes([2]) + b"\xff\xff" + struct.pack(">I", 0)
    with pytest.raises(ValueError, match="utf-8"):
        parse_header(bad)


# ---------------------------------------------------------------------------
# CRC helpers
# ---------------------------------------------------------------------------


def test_compute_crc_matches_zlib_directly() -> None:
    data = b"\x00\x01\x02hello world"
    assert compute_crc(data) == zlib.crc32(data) & 0xFFFFFFFF


def test_compute_crc_returns_unsigned_int() -> None:
    # zlib.crc32 on Python 3 always returns unsigned; we still want a
    # mechanical guarantee that the value is in the uint32 range.
    crc = compute_crc(b"x" * 100)
    assert 0 <= crc <= 0xFFFFFFFF


def test_pack_crc_then_unpack_crc_round_trip() -> None:
    crc = 0xDEADBEEF
    blob = b"prefix" + pack_crc(crc)
    assert unpack_crc(blob, offset=len(b"prefix")) == crc


def test_unpack_crc_rejects_truncated_trailer() -> None:
    # Three bytes after the offset is one short — the 4-byte struct unpack
    # cannot complete.
    blob = b"prefix" + b"\x01\x02\x03"
    with pytest.raises(ValueError, match="truncated"):
        unpack_crc(blob, offset=len(b"prefix"))
