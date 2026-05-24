"""Tests for ``rytm_randomizer.cockpit.export.verifier``.

The verifier is the safe receiver-side entry point for cockpit profile
blobs. It never raises — every malformed-input path returns a
structured :class:`VerificationResult` with a categorical ``reason``
string so receivers can log / display the failure mode without
``try/except`` plumbing.

These tests pin every (reason, key_id, algorithm, payload_size) tuple
the verifier promises to produce. Per the spec they must cover the
unsigned-payload path (CRC + magic of the inner ``RYMP`` blob), the
signed-envelope path with and without a key, key mismatch, key_id
mismatch, signature tampering, and structural breakage at the envelope
boundary.
"""

from __future__ import annotations

import struct

import pytest

from rytm_randomizer.cockpit.data import (
    ProfileModel,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.export.serialize import pack_profile_model
from rytm_randomizer.cockpit.export.signing import (
    SIGNATURE_ALGO_HMAC_SHA256,
    SIGNATURE_FORMAT_VERSION,
    SIGNATURE_HEADER_MAGIC,
    pack_signed,
    sign_profile_blob,
)
from rytm_randomizer.cockpit.export.verifier import (
    VerificationResult,
    verify_signed_blob,
    verify_unsigned_payload,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_KEY: bytes = b"buzzi-secret-key-2026"
_KEY_ID: str = "buzzi-2026-key"


def _make_profile() -> ProfileModel:
    return ProfileModel(
        profile_id="01HXY5Q9PJM0123456789ABCD0",
        name="buzzi",
        kind="user",
        model_version="1.2.0",
        traits=(StyleTrait("rolling_low_end", 0.85),),
        pad_mappings=(TraitPadWeight("rolling_low_end", 1, 0.6),),
        transition_curve="linear",
        source_summary="5 sources",
    )


def _packed_profile_bytes() -> bytes:
    return pack_profile_model(_make_profile())


def _signed_wire(
    *, payload: bytes | None = None, key: bytes = _KEY, key_id: str = _KEY_ID
) -> bytes:
    payload = _packed_profile_bytes() if payload is None else payload
    return pack_signed(sign_profile_blob(payload, key=key, key_id=key_id))


# ---------------------------------------------------------------------------
# VerificationResult dataclass shape
# ---------------------------------------------------------------------------


def test_verification_result_is_frozen_dataclass() -> None:
    result = verify_unsigned_payload(_packed_profile_bytes())
    assert isinstance(result, VerificationResult)
    with pytest.raises((AttributeError, Exception)):
        result.ok = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# verify_unsigned_payload — happy path + every failure path
# ---------------------------------------------------------------------------


def test_verify_unsigned_payload_returns_ok_for_valid_packed_blob() -> None:
    payload = _packed_profile_bytes()
    result = verify_unsigned_payload(payload)
    assert result.ok is True
    assert result.reason == "ok"
    assert result.expected_key_id is None
    assert result.expected_algorithm is None
    assert result.payload_size == len(payload)


def test_verify_unsigned_payload_reports_magic_mismatch() -> None:
    payload = bytearray(_packed_profile_bytes())
    payload[:4] = b"NOPE"
    result = verify_unsigned_payload(bytes(payload))
    assert result.ok is False
    assert result.reason == "magic_mismatch"
    assert result.expected_key_id is None
    assert result.expected_algorithm is None
    assert result.payload_size is None


def test_verify_unsigned_payload_reports_version_unsupported() -> None:
    payload = bytearray(_packed_profile_bytes())
    # Stomp on the inner RYMP format_version at offset 4..6.
    payload[4:6] = struct.pack(">H", 99)
    result = verify_unsigned_payload(bytes(payload))
    assert result.ok is False
    assert result.reason == "version_unsupported"


def test_verify_unsigned_payload_reports_payload_crc_mismatch() -> None:
    payload = bytearray(_packed_profile_bytes())
    # Flip a byte deep in the msgpack payload region (past header).
    ver_len = payload[6]
    payload_start = 7 + ver_len + 4
    payload[payload_start] ^= 0xFF
    result = verify_unsigned_payload(bytes(payload))
    assert result.ok is False
    assert result.reason == "payload_crc_mismatch"


def test_verify_unsigned_payload_reports_truncated_for_empty_input() -> None:
    result = verify_unsigned_payload(b"")
    assert result.ok is False
    assert result.reason == "truncated"


def test_verify_unsigned_payload_reports_truncated_for_short_input() -> None:
    payload = _packed_profile_bytes()
    result = verify_unsigned_payload(payload[:-5])
    assert result.ok is False
    assert result.reason == "truncated"


# ---------------------------------------------------------------------------
# verify_signed_blob — happy path
# ---------------------------------------------------------------------------


def test_verify_signed_blob_returns_ok_with_correct_key() -> None:
    wire = _signed_wire()
    result = verify_signed_blob(wire, key=_KEY)
    assert result.ok is True
    assert result.reason == "ok"
    assert result.expected_key_id == _KEY_ID
    assert result.expected_algorithm == SIGNATURE_ALGO_HMAC_SHA256
    assert result.payload_size == len(_packed_profile_bytes())


def test_verify_signed_blob_returns_ok_with_correct_key_and_matching_key_id() -> None:
    wire = _signed_wire()
    result = verify_signed_blob(wire, key=_KEY, expected_key_id=_KEY_ID)
    assert result.ok is True
    assert result.reason == "ok"


def test_verify_signed_blob_without_key_reports_unsigned_payload_on_valid_envelope() -> None:
    # When the caller supplies no key we still parse the envelope, verify
    # the inner RYMP payload, and report unsigned_payload to make it clear
    # the signature itself was not checked.
    wire = _signed_wire()
    result = verify_signed_blob(wire)
    assert result.ok is True
    assert result.reason == "unsigned_payload"
    assert result.expected_key_id == _KEY_ID
    assert result.expected_algorithm == SIGNATURE_ALGO_HMAC_SHA256
    assert result.payload_size == len(_packed_profile_bytes())


# ---------------------------------------------------------------------------
# verify_signed_blob — key / signature mismatch paths
# ---------------------------------------------------------------------------


def test_verify_signed_blob_reports_signature_mismatch_for_wrong_key() -> None:
    wire = _signed_wire()
    result = verify_signed_blob(wire, key=b"wrong-key")
    assert result.ok is False
    assert result.reason == "signature_mismatch"
    assert result.expected_key_id == _KEY_ID
    assert result.expected_algorithm == SIGNATURE_ALGO_HMAC_SHA256


def test_verify_signed_blob_reports_signature_mismatch_for_tampered_payload() -> None:
    # Sign the original payload, then tamper with the payload region of
    # the wire frame so the recomputed HMAC won't match the stored one.
    wire = bytearray(_signed_wire())
    # Last byte of the wire is inside the payload — flip it.
    wire[-1] ^= 0xFF
    result = verify_signed_blob(bytes(wire), key=_KEY)
    assert result.ok is False
    assert result.reason == "signature_mismatch"


def test_verify_signed_blob_reports_key_id_mismatch_for_wrong_expected_id() -> None:
    wire = _signed_wire()
    result = verify_signed_blob(wire, key=_KEY, expected_key_id="other-key")
    assert result.ok is False
    assert result.reason == "key_id_mismatch"
    assert result.expected_key_id == _KEY_ID


def test_verify_signed_blob_reports_key_id_mismatch_even_without_key() -> None:
    # key_id is structural; mismatch is reported even before we'd attempt
    # signature verification.
    wire = _signed_wire()
    result = verify_signed_blob(wire, expected_key_id="other-key")
    assert result.ok is False
    assert result.reason == "key_id_mismatch"
    assert result.expected_key_id == _KEY_ID


# ---------------------------------------------------------------------------
# verify_signed_blob — envelope structure failures
# ---------------------------------------------------------------------------


def test_verify_signed_blob_reports_magic_mismatch() -> None:
    wire = bytearray(_signed_wire())
    wire[:4] = b"NOPE"
    result = verify_signed_blob(bytes(wire), key=_KEY)
    assert result.ok is False
    assert result.reason == "magic_mismatch"
    assert result.expected_key_id is None
    assert result.expected_algorithm is None
    assert result.payload_size is None


def test_verify_signed_blob_reports_version_unsupported_for_unknown_envelope_version() -> None:
    wire = bytearray(_signed_wire())
    wire[4:6] = struct.pack(">H", 99)
    result = verify_signed_blob(bytes(wire), key=_KEY)
    assert result.ok is False
    assert result.reason == "version_unsupported"


def test_verify_signed_blob_reports_truncated_for_short_input() -> None:
    result = verify_signed_blob(b"\x00" * 3, key=_KEY)
    assert result.ok is False
    assert result.reason == "truncated"


def test_verify_signed_blob_reports_truncated_for_empty_input() -> None:
    result = verify_signed_blob(b"", key=_KEY)
    assert result.ok is False
    assert result.reason == "truncated"


def test_verify_signed_blob_reports_truncated_when_inner_payload_field_cut() -> None:
    wire = _signed_wire()
    # Drop the last 5 bytes — the inner RYMP payload cannot be read.
    result = verify_signed_blob(wire[:-5], key=_KEY)
    assert result.ok is False
    assert result.reason == "truncated"


# ---------------------------------------------------------------------------
# verify_signed_blob — inner payload integrity (after envelope OK)
# ---------------------------------------------------------------------------


def test_verify_signed_blob_reports_payload_crc_mismatch_when_inner_blob_tampered_and_resigned() -> (
    None
):
    # If a malicious party tampers with the inner RYMP payload AND
    # re-signs the envelope with their own key matching the expected
    # key_id, the inner RYMP CRC32 still catches the corruption — as
    # long as they corrupted the inner blob WITHOUT updating its CRC.
    inner = bytearray(_packed_profile_bytes())
    # Corrupt one msgpack byte (past the inner header).
    ver_len = inner[6]
    payload_start = 7 + ver_len + 4
    inner[payload_start] ^= 0xFF
    wire = pack_signed(sign_profile_blob(bytes(inner), key=_KEY, key_id=_KEY_ID))
    result = verify_signed_blob(wire, key=_KEY)
    assert result.ok is False
    assert result.reason == "payload_crc_mismatch"


def test_verify_signed_blob_reports_payload_crc_mismatch_when_inner_blob_has_bad_magic() -> None:
    inner = b"NOPE" + _packed_profile_bytes()[4:]
    wire = pack_signed(sign_profile_blob(inner, key=_KEY, key_id=_KEY_ID))
    result = verify_signed_blob(wire, key=_KEY)
    assert result.ok is False
    # The inner blob no longer carries a valid RYMP magic; the verifier
    # surfaces the magic mismatch from the inner check.
    assert result.reason == "magic_mismatch"


# ---------------------------------------------------------------------------
# Constants re-exports stay alive via this module path
# ---------------------------------------------------------------------------


def test_signing_constants_are_accessible_through_signing_module() -> None:
    # Sanity that the verifier's contract pieces all import cleanly.
    assert SIGNATURE_HEADER_MAGIC == b"RYMS"
    assert SIGNATURE_FORMAT_VERSION == 1
    assert SIGNATURE_ALGO_HMAC_SHA256 == "hmac-sha256"
