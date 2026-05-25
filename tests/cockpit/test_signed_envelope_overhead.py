"""Tests for :func:`rytm_randomizer.cockpit.export.signed_envelope_overhead_bytes`.

The rehearsal report (:mod:`rytm_randomizer.reports.cockpit_export_rehearsal`)
used to carry a 256-byte hardcoded estimate of the signed-envelope
wrapper size. The analytic formula in :mod:`.signing` replaces it: for a
given ``(algo, key_id)`` the wrapper is fixed and computable from the
wire layout.

These tests pin the formula to the real :func:`pack_signed` output —
for several payload shapes and several key_id lengths (including
multibyte utf-8) the difference between the packed envelope and its
inner payload MUST equal the formula's return value byte-for-byte. If a
future signer change drifts the wire format, this test fails at the
first byte of slack instead of silently fitting inside an opaque budget.
"""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.export import (
    SIGNATURE_ALGO_HMAC_SHA256,
    pack_signed,
    sign_profile_blob,
    signed_envelope_overhead_bytes,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


_KEY: bytes = b"\x00" * 32
_DEFAULT_PAYLOAD: bytes = b"X" * 100


# ---------------------------------------------------------------------------
# Formula vs. wire layout
# ---------------------------------------------------------------------------


def test_signed_envelope_overhead_known_default_value() -> None:
    """Sanity check on the formula for the v1 default ``(algo, key_id)``.

    Catches a literal-typo regression in the formula: the v1 default of
    ``algo="hmac-sha256"`` (11 utf-8 bytes) and a typical short key_id
    of ``"test-key"`` (8 utf-8 bytes) should produce exactly
    ``4 + 2 + 1 + 11 + 1 + 8 + 1 + 32 + 4 = 64`` bytes.
    """

    assert signed_envelope_overhead_bytes(algo=SIGNATURE_ALGO_HMAC_SHA256, key_id="test-key") == 64


@pytest.mark.parametrize(
    "key_id",
    [
        "",
        "a",
        "test-key",
        "buzzi-2026-key",
        "x" * 32,
        "x" * 255,
        # Multibyte utf-8: each emoji is 4 utf-8 bytes; the formula
        # MUST track utf-8 byte length, not codepoint count.
        "buzzi-\U0001f941",
    ],
)
@pytest.mark.parametrize("payload_len", [0, 1, 100, 4096])
def test_signed_envelope_overhead_matches_pack_signed_byte_for_byte(
    key_id: str, payload_len: int
) -> None:
    """The analytic overhead MUST equal ``len(envelope) - len(payload)``.

    Builds a real :class:`SignedBlob` via :func:`sign_profile_blob`,
    packs it with :func:`pack_signed`, then asserts the difference
    between the packed bytes and the inner payload equals the formula's
    output. Parametrized over several key-id lengths (including the
    255-byte maximum and a multibyte utf-8 string) and several payload
    sizes (including the zero-length edge) so a single field-width drift
    is detected immediately.
    """

    payload = b"X" * payload_len
    blob = sign_profile_blob(payload, key=_KEY, key_id=key_id)
    envelope = pack_signed(blob)

    expected_overhead = signed_envelope_overhead_bytes(
        algo=SIGNATURE_ALGO_HMAC_SHA256,
        key_id=key_id,
    )
    actual_overhead = len(envelope) - len(payload)
    assert actual_overhead == expected_overhead, (
        f"envelope wrapper for key_id={key_id!r} payload_len={payload_len} "
        f"was {actual_overhead} bytes but formula predicted {expected_overhead}; "
        "the analytic formula has drifted from pack_signed's wire layout."
    )


def test_signed_envelope_overhead_does_not_depend_on_payload_size() -> None:
    """The formula is payload-independent — only ``(algo, key_id)`` matter.

    Regression guard against someone "fixing" the formula by sneaking a
    payload-len argument into it; the wire layout uses a fixed-width
    uint32 for the payload length so the overhead really is constant.
    """

    overhead_small = len(pack_signed(sign_profile_blob(b"a", key=_KEY, key_id="k"))) - 1
    overhead_large = (
        len(pack_signed(sign_profile_blob(b"a" * 10_000, key=_KEY, key_id="k"))) - 10_000
    )
    assert overhead_small == overhead_large
    assert overhead_small == signed_envelope_overhead_bytes(
        algo=SIGNATURE_ALGO_HMAC_SHA256, key_id="k"
    )


# ---------------------------------------------------------------------------
# Rejection paths
# ---------------------------------------------------------------------------


def test_signed_envelope_overhead_rejects_unsupported_algorithm() -> None:
    """An unsupported algorithm MUST raise; v1 only knows HMAC-SHA256."""

    with pytest.raises(ValueError, match="hmac-sha256"):
        signed_envelope_overhead_bytes(algo="ed25519", key_id="test-key")


def test_signed_envelope_overhead_rejects_overlong_key_id() -> None:
    """A key_id wider than uint8 cannot fit in the wire format."""

    with pytest.raises(ValueError, match="key_id"):
        signed_envelope_overhead_bytes(
            algo=SIGNATURE_ALGO_HMAC_SHA256,
            key_id="x" * 256,
        )
