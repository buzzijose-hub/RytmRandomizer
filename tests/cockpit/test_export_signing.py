"""Tests for ``rytm_randomizer.cockpit.export.signing``.

This module owns the stdlib-only HMAC-SHA256 signing envelope that sits
on top of the existing :func:`pack_profile_model` wire format. These tests
pin the wire layout, the round-trip discipline, and every guard branch in
:func:`pack_signed` / :func:`unpack_signed` so the corresponding verifier
tests in ``test_export_verifier.py`` can stay focused on the integrity
report rather than re-asserting envelope mechanics.
"""

from __future__ import annotations

import hashlib
import hmac
import struct

import pytest

from rytm_randomizer.cockpit.export.signing import (
    SIGNATURE_ALGO_HMAC_SHA256,
    SIGNATURE_FORMAT_VERSION,
    SIGNATURE_HEADER_MAGIC,
    SignedBlob,
    pack_signed,
    sign_profile_blob,
    unpack_signed,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_DEFAULT_KEY: bytes = b"buzzi-secret-key-2026"
_DEFAULT_KEY_ID: str = "buzzi-2026-key"
_DEFAULT_PAYLOAD: bytes = (
    b"RYMP" + b"\x00\x01" + b"\x03" + b"1.0" + b"\x00\x00\x00\x05hello" + b"\xde\xad\xbe\xef"
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_signature_header_magic_is_ryms_ascii() -> None:
    assert SIGNATURE_HEADER_MAGIC == b"RYMS"
    assert len(SIGNATURE_HEADER_MAGIC) == 4


def test_signature_format_version_default_is_one() -> None:
    assert SIGNATURE_FORMAT_VERSION == 1


def test_signature_algo_is_hmac_sha256() -> None:
    assert SIGNATURE_ALGO_HMAC_SHA256 == "hmac-sha256"


# ---------------------------------------------------------------------------
# sign_profile_blob
# ---------------------------------------------------------------------------


def test_sign_profile_blob_returns_signed_blob_with_expected_fields() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    assert isinstance(signed, SignedBlob)
    assert signed.payload == _DEFAULT_PAYLOAD
    assert signed.algorithm == SIGNATURE_ALGO_HMAC_SHA256
    assert signed.key_id == _DEFAULT_KEY_ID
    assert len(signed.signature) == hashlib.sha256().digest_size  # 32 bytes


def test_sign_profile_blob_matches_stdlib_hmac_sha256() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    expected = hmac.new(_DEFAULT_KEY, _DEFAULT_PAYLOAD, hashlib.sha256).digest()
    assert signed.signature == expected


def test_signed_blob_is_frozen_dataclass() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    with pytest.raises((AttributeError, Exception)):
        # Attempting to mutate a frozen dataclass raises FrozenInstanceError.
        signed.key_id = "other"  # type: ignore[misc]


def test_sign_profile_blob_with_empty_payload_still_produces_32_byte_signature() -> None:
    signed = sign_profile_blob(b"", key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    assert signed.payload == b""
    assert len(signed.signature) == 32


def test_sign_profile_blob_with_empty_key_id_round_trips_through_wire() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id="")
    wire = pack_signed(signed)
    assert unpack_signed(wire) == signed


# ---------------------------------------------------------------------------
# pack_signed / unpack_signed — round-trip
# ---------------------------------------------------------------------------


def test_pack_signed_then_unpack_signed_round_trip() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    wire = pack_signed(signed)
    decoded = unpack_signed(wire)
    assert decoded == signed


def test_pack_signed_layout_matches_spec() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    wire = pack_signed(signed)
    # magic(4) + format_version(2) + algo_len(1) + algo + key_id_len(1)
    # + key_id + sig_len(1) + sig + payload_len(4) + payload
    assert wire[:4] == SIGNATURE_HEADER_MAGIC
    assert struct.unpack(">H", wire[4:6])[0] == SIGNATURE_FORMAT_VERSION
    algo_len = wire[6]
    assert algo_len == len(SIGNATURE_ALGO_HMAC_SHA256)
    algo = wire[7 : 7 + algo_len].decode("utf-8")
    assert algo == SIGNATURE_ALGO_HMAC_SHA256
    key_id_len_off = 7 + algo_len
    key_id_len = wire[key_id_len_off]
    assert key_id_len == len(_DEFAULT_KEY_ID)
    key_id_off = key_id_len_off + 1
    assert wire[key_id_off : key_id_off + key_id_len].decode("utf-8") == _DEFAULT_KEY_ID
    sig_len_off = key_id_off + key_id_len
    sig_len = wire[sig_len_off]
    assert sig_len == 32
    sig_off = sig_len_off + 1
    assert wire[sig_off : sig_off + sig_len] == signed.signature
    payload_len_off = sig_off + sig_len
    payload_len = struct.unpack(">I", wire[payload_len_off : payload_len_off + 4])[0]
    assert payload_len == len(_DEFAULT_PAYLOAD)
    payload_off = payload_len_off + 4
    assert wire[payload_off : payload_off + payload_len] == _DEFAULT_PAYLOAD
    assert len(wire) == payload_off + payload_len


def test_pack_signed_with_unicode_key_id_round_trips() -> None:
    key_id = "ключ-β-2026"
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=key_id)
    wire = pack_signed(signed)
    assert unpack_signed(wire) == signed


def test_pack_signed_with_empty_payload_round_trips() -> None:
    signed = sign_profile_blob(b"", key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    wire = pack_signed(signed)
    assert unpack_signed(wire) == signed


def test_pack_signed_with_max_length_key_id_round_trips() -> None:
    # uint8 length prefix => 255 bytes max.
    key_id = "k" * 255
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=key_id)
    wire = pack_signed(signed)
    assert unpack_signed(wire) == signed


# ---------------------------------------------------------------------------
# pack_signed — guard branches
# ---------------------------------------------------------------------------


def test_pack_signed_rejects_oversized_key_id() -> None:
    too_long = "k" * 256
    signed = SignedBlob(
        payload=_DEFAULT_PAYLOAD,
        algorithm=SIGNATURE_ALGO_HMAC_SHA256,
        key_id=too_long,
        signature=b"\x00" * 32,
    )
    with pytest.raises(ValueError, match="key_id"):
        pack_signed(signed)


def test_pack_signed_rejects_oversized_algorithm_name() -> None:
    signed = SignedBlob(
        payload=_DEFAULT_PAYLOAD,
        algorithm="x" * 256,
        key_id=_DEFAULT_KEY_ID,
        signature=b"\x00" * 32,
    )
    with pytest.raises(ValueError, match="algorithm"):
        pack_signed(signed)


def test_pack_signed_rejects_oversized_signature() -> None:
    signed = SignedBlob(
        payload=_DEFAULT_PAYLOAD,
        algorithm=SIGNATURE_ALGO_HMAC_SHA256,
        key_id=_DEFAULT_KEY_ID,
        signature=b"\x00" * 256,
    )
    with pytest.raises(ValueError, match="signature"):
        pack_signed(signed)


def test_pack_signed_rejects_oversized_payload() -> None:
    # A 4 GiB+ payload cannot be represented; we don't actually allocate it,
    # we forge a SignedBlob whose payload length would overflow uint32.
    class _FakeBytes:
        """A bytes-like object that lies about its length."""

        def __len__(self) -> int:
            return 0x1_0000_0000

        def __eq__(self, other: object) -> bool:  # pragma: no cover - irrelevant
            return False

        def __hash__(self) -> int:  # pragma: no cover - irrelevant
            return 0

    signed = SignedBlob(
        payload=_FakeBytes(),  # type: ignore[arg-type]
        algorithm=SIGNATURE_ALGO_HMAC_SHA256,
        key_id=_DEFAULT_KEY_ID,
        signature=b"\x00" * 32,
    )
    with pytest.raises(ValueError, match="payload"):
        pack_signed(signed)


# ---------------------------------------------------------------------------
# unpack_signed — guard branches
# ---------------------------------------------------------------------------


def test_unpack_signed_rejects_bad_magic() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    wire = bytearray(pack_signed(signed))
    wire[:4] = b"NOPE"
    with pytest.raises(ValueError, match="bad magic"):
        unpack_signed(bytes(wire))


def test_unpack_signed_rejects_unsupported_format_version() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    wire = bytearray(pack_signed(signed))
    # Stomp on the format_version field at offset 4..6.
    wire[4:6] = struct.pack(">H", 99)
    with pytest.raises(ValueError, match="unsupported"):
        unpack_signed(bytes(wire))


def test_unpack_signed_rejects_blob_shorter_than_fixed_prefix() -> None:
    with pytest.raises(ValueError, match="truncated"):
        unpack_signed(b"\x00" * 5)


def test_unpack_signed_rejects_completely_empty_blob() -> None:
    with pytest.raises(ValueError, match="truncated"):
        unpack_signed(b"")


def test_unpack_signed_rejects_truncation_inside_algorithm_field() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    wire = pack_signed(signed)
    # Cut blob right after algo_len (offset 7), so algo bytes are missing.
    with pytest.raises(ValueError, match="truncated"):
        unpack_signed(wire[:7])


def test_unpack_signed_rejects_truncation_at_algorithm_length_prefix() -> None:
    # The fixed prefix is 6 bytes; passing exactly 6 bytes (valid magic +
    # supported format_version) leaves zero bytes for the algorithm length
    # prefix and must trip the length-prefix overrun guard.
    valid_prefix = SIGNATURE_HEADER_MAGIC + struct.pack(">H", SIGNATURE_FORMAT_VERSION)
    with pytest.raises(ValueError, match="truncated"):
        unpack_signed(valid_prefix)


def test_unpack_signed_rejects_truncation_inside_key_id_field() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    wire = pack_signed(signed)
    # The key_id_len byte sits at offset 7 + len(algo).
    key_id_len_off = 7 + len(SIGNATURE_ALGO_HMAC_SHA256)
    # Truncate one byte after key_id_len, so the key_id payload is short.
    with pytest.raises(ValueError, match="truncated"):
        unpack_signed(wire[: key_id_len_off + 1])


def test_unpack_signed_rejects_truncation_inside_signature_field() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    wire = pack_signed(signed)
    # Compute the offset of the sig_len byte.
    key_id_len_off = 7 + len(SIGNATURE_ALGO_HMAC_SHA256)
    key_id_off = key_id_len_off + 1
    sig_len_off = key_id_off + len(_DEFAULT_KEY_ID)
    # Truncate one byte past the sig_len, so the signature payload is short.
    with pytest.raises(ValueError, match="truncated"):
        unpack_signed(wire[: sig_len_off + 1])


def test_unpack_signed_rejects_truncation_inside_payload_length_field() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    wire = pack_signed(signed)
    key_id_len_off = 7 + len(SIGNATURE_ALGO_HMAC_SHA256)
    key_id_off = key_id_len_off + 1
    sig_len_off = key_id_off + len(_DEFAULT_KEY_ID)
    sig_off = sig_len_off + 1
    payload_len_off = sig_off + 32
    # Truncate two bytes into the payload-length field (need 4 bytes).
    with pytest.raises(ValueError, match="truncated"):
        unpack_signed(wire[: payload_len_off + 2])


def test_unpack_signed_rejects_truncation_inside_payload() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    wire = pack_signed(signed)
    # Drop the last 3 bytes of the payload.
    with pytest.raises(ValueError, match="truncated"):
        unpack_signed(wire[:-3])


def test_unpack_signed_rejects_invalid_utf8_in_algorithm() -> None:
    # Forge a wire frame with deliberately invalid utf-8 in the algo field.
    bad_algo = b"\xff\xff"
    wire = (
        SIGNATURE_HEADER_MAGIC
        + struct.pack(">H", SIGNATURE_FORMAT_VERSION)
        + bytes([len(bad_algo)])
        + bad_algo
        + bytes([len(_DEFAULT_KEY_ID)])
        + _DEFAULT_KEY_ID.encode("utf-8")
        + bytes([32])
        + b"\x00" * 32
        + struct.pack(">I", 0)
    )
    with pytest.raises(ValueError, match="utf-8"):
        unpack_signed(wire)


def test_unpack_signed_rejects_invalid_utf8_in_key_id() -> None:
    # Forge a wire frame with deliberately invalid utf-8 in the key_id field.
    bad_key_id = b"\xff\xff"
    algo = SIGNATURE_ALGO_HMAC_SHA256.encode("utf-8")
    wire = (
        SIGNATURE_HEADER_MAGIC
        + struct.pack(">H", SIGNATURE_FORMAT_VERSION)
        + bytes([len(algo)])
        + algo
        + bytes([len(bad_key_id)])
        + bad_key_id
        + bytes([32])
        + b"\x00" * 32
        + struct.pack(">I", 0)
    )
    with pytest.raises(ValueError, match="utf-8"):
        unpack_signed(wire)


# ---------------------------------------------------------------------------
# Tamper resistance — the round-trip catches in-flight corruption
# ---------------------------------------------------------------------------


def test_payload_tampering_after_signing_changes_recomputed_signature() -> None:
    signed = sign_profile_blob(_DEFAULT_PAYLOAD, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    tampered = b"\xff" + _DEFAULT_PAYLOAD[1:]
    fresh = sign_profile_blob(tampered, key=_DEFAULT_KEY, key_id=_DEFAULT_KEY_ID)
    assert fresh.signature != signed.signature


def test_different_key_produces_different_signature_for_same_payload() -> None:
    a = sign_profile_blob(_DEFAULT_PAYLOAD, key=b"key-a", key_id=_DEFAULT_KEY_ID)
    b = sign_profile_blob(_DEFAULT_PAYLOAD, key=b"key-b", key_id=_DEFAULT_KEY_ID)
    assert a.signature != b.signature
