"""Verify the ``signed_envelope_present`` discriminator on VerificationResult (H3).

CODE_REVIEW.md finding H3 — the pre-PR verifier returned
``reason="unsigned_payload"`` for two semantically different cases:

1. The bytes were a signed envelope but the caller passed no key, so the
   signature couldn't be checked (CRC is the only assurance).
2. The bytes were a bare RYMP payload with no envelope at all.

Receivers that care about provenance (e.g. accepting signed-only loads
from external paths) need to tell them apart. This test pins the
``signed_envelope_present`` field as the H3 disambiguator.
"""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.export import (
    pack_profile_model,
    pack_signed,
    sign_profile_blob,
    verify_signed_blob,
    verify_unsigned_payload,
)

pytestmark = pytest.mark.fast


def _profile():
    from rytm_randomizer.cockpit.data import ProfileModel, StyleTrait, TraitPadWeight

    return ProfileModel(
        profile_id="profile-h3-test",
        name="H3 test",
        kind="user",
        model_version="1.0.0",
        traits=(StyleTrait(name="punchy", value=0.7),),
        pad_mappings=(TraitPadWeight(trait="punchy", pad_id=1, weight=1.0),),
        transition_curve="progressive",
        source_summary="H3 test profile",
    )


def test_signed_envelope_with_correct_key_carries_present_true() -> None:
    """A signed envelope verified with the right key reports
    ``signed_envelope_present=True``.
    """

    payload = pack_profile_model(_profile())
    key = b"\x42" * 32
    blob = sign_profile_blob(payload, key_id="test-key", key=key)
    wire = pack_signed(blob)

    result = verify_signed_blob(wire, key=key, expected_key_id="test-key")

    assert result.ok is True
    assert result.reason == "ok"
    assert (
        result.signed_envelope_present is True
    ), "Envelope parsed successfully → signed_envelope_present must be True"


def test_signed_envelope_with_no_key_provided_carries_present_true() -> None:
    """H3 disambiguator case 1: envelope HAS a signature; caller didn't verify it.

    Receivers can spot this via ``ok=True AND reason='unsigned_payload'
    AND signed_envelope_present=True`` and refuse to accept these bytes
    for sensitive operations (the signature is right there, but the
    caller declined to check).
    """

    payload = pack_profile_model(_profile())
    blob = sign_profile_blob(payload, key_id="test-key", key=b"\x42" * 32)
    wire = pack_signed(blob)

    # Verifier with key=None → does the unsigned-payload code path
    result = verify_signed_blob(wire, key=None)

    assert result.ok is True
    assert result.reason == "unsigned_payload"
    assert result.signed_envelope_present is True, (
        "The bytes carried a signing envelope; signed_envelope_present "
        "must be True even though the verifier skipped the signature check."
    )


def test_bare_unsigned_payload_carries_present_false() -> None:
    """H3 disambiguator case 2: bytes are a bare RYMP, no envelope at all.

    ``verify_unsigned_payload`` is the right entry point for this shape;
    it always reports ``signed_envelope_present=False`` because there
    is no envelope to begin with.
    """

    payload = pack_profile_model(_profile())

    result = verify_unsigned_payload(payload)

    assert result.ok is True
    assert result.reason == "ok"
    assert (
        result.signed_envelope_present is False
    ), "Bare RYMP payload — no envelope was present; the field must be False."


def test_envelope_with_wrong_key_id_carries_present_true() -> None:
    """A key_id mismatch still parses the envelope successfully → present=True.

    Pins that signed_envelope_present is not gated on the verification
    *succeeding*, only on the envelope having parsed.
    """

    payload = pack_profile_model(_profile())
    key = b"\x42" * 32
    blob = sign_profile_blob(payload, key_id="actual-key", key=key)
    wire = pack_signed(blob)

    result = verify_signed_blob(wire, key=key, expected_key_id="different-key")

    assert result.ok is False
    assert result.reason == "key_id_mismatch"
    assert result.signed_envelope_present is True


def test_truncated_envelope_carries_present_false() -> None:
    """If the envelope FAILS to parse, signed_envelope_present is False.

    A truncated / magic-mismatched / version-unsupported result means
    we never got an envelope; the discriminator stays False.
    """

    truncated = b"RYMS\x00\x00"  # magic + version but no content

    result = verify_signed_blob(truncated, key=b"\x00" * 32)

    assert result.ok is False
    assert (
        result.signed_envelope_present is False
    ), "Envelope failed to parse — discriminator must be False."
