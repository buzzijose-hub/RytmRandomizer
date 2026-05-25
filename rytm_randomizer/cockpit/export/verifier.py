"""Receiver-side integrity verifier for cockpit ``ProfileModel`` blobs.

This module is the *safe* receiver entry point — every public function
returns a :class:`VerificationResult` describing the outcome and never
raises. The two callers it exists for:

* The cockpit's load-from-file flow: read the bytes, call
  :func:`verify_signed_blob`, surface the ``reason`` in the GUI banner
  before deserializing the inner payload.
* The Phase-4 embedded firmware verifier: when porting this logic to
  hand-written C the categorical ``reason`` strings map 1:1 to a tiny
  enum so the C code can stay branch-free at the call site.

The verifier intentionally classifies *which* check failed (``"magic_mismatch"``
vs ``"signature_mismatch"`` vs ``"payload_crc_mismatch"``) so receivers can
make policy decisions (e.g. accept unsigned reads from local-disk paths but
demand signed reads from anywhere else) without having to re-parse the
envelope themselves.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

from ...observability.logging import get_logger
from .model_format import (
    MAGIC,
    SUPPORTED_FORMAT_VERSIONS,
    compute_crc,
    parse_header,
    unpack_crc,
)
from .signing import (
    SIGNATURE_HEADER_MAGIC,
    SUPPORTED_SIGNATURE_FORMAT_VERSIONS,
    unpack_signed,
)

_logger = get_logger(__name__)
"""Module logger for the cockpit ProfileModel verifier. Bound here so
future structured log calls (per-failure-reason metric increments,
verification breadcrumbs) can land in the package's structured stream
without touching this file's imports. See ``OBSERVABILITY_REVIEW.md``
Phase 5."""

# ---------------------------------------------------------------------------
# VerificationResult dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerificationResult:
    """Outcome of a verification call.

    Attributes:
        ok: ``True`` only when every applicable check passed.
        reason: A short category label for the outcome. One of:
            ``"ok"`` | ``"magic_mismatch"`` | ``"version_unsupported"``
            | ``"truncated"`` | ``"signature_mismatch"``
            | ``"key_id_mismatch"`` | ``"payload_crc_mismatch"``
            | ``"unsigned_payload"``. ``"unsigned_payload"`` is the
            specifically-friendly result for the caller-passed-no-key
            case where the envelope and inner payload are both
            structurally sound — i.e. "everything we *could* verify is
            fine, but you didn't ask us to verify the signature".
        expected_key_id: The ``key_id`` declared by the blob, when the
            envelope was parseable enough to read it. ``None`` for early
            magic-mismatch / truncated / version-unsupported failures and
            for the unsigned-payload path (no envelope at all).
        expected_algorithm: The algorithm name declared by the blob, when
            parseable. Same rules as ``expected_key_id``.
        payload_size: The size in bytes of the inner ``RYMP`` payload, when
            parseable. ``None`` if we never got that far.
        signed_envelope_present: ``True`` iff the verifier successfully
            parsed a signing envelope from the input bytes. Disambiguates
            two ``ok=True, reason="unsigned_payload"`` cases that PR-2-vintage
            verifier code couldn't tell apart (H3 from CODE_REVIEW.md):

            1. **Caller passed no key against an envelope that has one**:
               ``signed_envelope_present=True``. The bytes WERE signed; the
               receiver chose not to verify the signature. CRC-only assurance.
            2. **Bytes are a bare RYMP payload with no envelope**:
               ``signed_envelope_present=False``. There's no signature to
               verify; CRC is the only integrity check available regardless
               of whether a key was passed.

            Receivers that demand provenance for sensitive operations should
            reject cases 1 AND 2 (any ``reason="unsigned_payload"``). Receivers
            that ONLY care about non-tampered transport over a trusted
            channel can accept case 1 if the operator explicitly opted out
            of signature verification. The distinguisher gives them the
            information; the policy decision is theirs.
    """

    ok: bool
    reason: str
    expected_key_id: str | None
    expected_algorithm: str | None
    payload_size: int | None
    signed_envelope_present: bool = False


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def verify_signed_blob(
    data: bytes,
    *,
    key: bytes | None = None,
    expected_key_id: str | None = None,
) -> VerificationResult:
    """Verify a signed-envelope blob without ever raising.

    The verifier walks the wire format in this order:

    1. Parse the signing envelope (catches magic / version / truncation
       at the envelope layer).
    2. If ``expected_key_id`` was supplied, check it against the
       envelope's declared ``key_id``.
    3. If ``key`` was supplied, recompute the HMAC-SHA256 of the inner
       payload and compare it timing-safely to the stored signature.
    4. Verify the inner ``RYMP`` payload's magic, format version, and
       CRC32 trailer.

    Args:
        data: The full signed-envelope bytes.
        key: The HMAC-SHA256 secret. If ``None`` the signature check is
            skipped and the result reports ``"unsigned_payload"`` on
            otherwise-clean input.
        expected_key_id: If provided, the verifier requires the envelope
            to declare exactly this ``key_id``. Use this to route
            verification across multiple known keys without trial
            signing.
    """

    try:
        blob = unpack_signed(data)
    except ValueError as exc:
        return _classify_envelope_error(str(exc))

    # ``signed_envelope_present=True`` from here down — the envelope parsed
    # cleanly, so receivers can use ``result.signed_envelope_present`` to
    # tell "no key was provided to verify a signature THAT EXISTS" from
    # "the bytes were never signed in the first place" (H3 disambiguator).
    if expected_key_id is not None and blob.key_id != expected_key_id:
        return VerificationResult(
            ok=False,
            reason="key_id_mismatch",
            expected_key_id=blob.key_id,
            expected_algorithm=blob.algorithm,
            payload_size=len(blob.payload),
            signed_envelope_present=True,
        )

    if key is not None:
        expected_signature = hmac.new(key, blob.payload, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_signature, blob.signature):
            return VerificationResult(
                ok=False,
                reason="signature_mismatch",
                expected_key_id=blob.key_id,
                expected_algorithm=blob.algorithm,
                payload_size=len(blob.payload),
                signed_envelope_present=True,
            )

    inner = _check_unsigned_payload_bytes(blob.payload)
    if inner.reason != "ok":
        return VerificationResult(
            ok=False,
            reason=inner.reason,
            expected_key_id=blob.key_id,
            expected_algorithm=blob.algorithm,
            payload_size=inner.payload_size,
            signed_envelope_present=True,
        )

    reason = "ok" if key is not None else "unsigned_payload"
    return VerificationResult(
        ok=True,
        reason=reason,
        expected_key_id=blob.key_id,
        expected_algorithm=blob.algorithm,
        payload_size=len(blob.payload),
        signed_envelope_present=True,
    )


def verify_unsigned_payload(payload: bytes) -> VerificationResult:
    """Verify a raw packed-profile (``RYMP``) blob without ever raising.

    Performs the same three structural checks the embedded firmware
    performs on a load: magic prefix, supported format version, and
    CRC32 trailer match. Does *not* MessagePack-decode the payload;
    that is the responsibility of
    :func:`rytm_randomizer.cockpit.export.unpack_profile_model`.
    """

    inner = _check_unsigned_payload_bytes(payload)
    return VerificationResult(
        ok=inner.reason == "ok",
        reason=inner.reason,
        expected_key_id=None,
        expected_algorithm=None,
        payload_size=inner.payload_size,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _classify_envelope_error(message: str) -> VerificationResult:
    """Map an :func:`unpack_signed` error message to a verification reason.

    Order matters: ``signature_mismatch`` cannot come from this path
    (the envelope parser never checks signatures), and a bad magic
    superficially looks like a truncated read (4 bytes < magic length)
    so we test the magic-mismatch substring first.
    """

    if "bad magic" in message:
        reason = "magic_mismatch"
    elif "unsupported" in message:
        reason = "version_unsupported"
    elif "truncated" in message or "utf-8" in message:
        reason = "truncated"
    else:  # pragma: no cover - all known unpack_signed errors fall above
        reason = "truncated"
    return VerificationResult(
        ok=False,
        reason=reason,
        expected_key_id=None,
        expected_algorithm=None,
        payload_size=None,
    )


@dataclass(frozen=True)
class _InnerCheckResult:
    """Outcome of the inner ``RYMP`` blob structural check."""

    reason: str
    payload_size: int | None


def _check_unsigned_payload_bytes(payload: bytes) -> _InnerCheckResult:
    """Run magic / version / CRC32 checks on a raw packed-profile blob.

    Returns ``("ok", len(payload))`` for a valid blob, or one of
    ``("magic_mismatch", None)`` / ``("version_unsupported", n)`` /
    ``("payload_crc_mismatch", n)`` / ``("truncated", None)``.
    """

    try:
        header = parse_header(payload)
    except ValueError as exc:
        message = str(exc)
        if "bad magic" in message:
            return _InnerCheckResult(reason="magic_mismatch", payload_size=None)
        return _InnerCheckResult(reason="truncated", payload_size=None)

    payload_start = header.header_len
    payload_end = payload_start + header.payload_len
    if len(payload) < payload_end + 4:
        return _InnerCheckResult(reason="truncated", payload_size=len(payload))

    if header.format_version not in SUPPORTED_FORMAT_VERSIONS:
        return _InnerCheckResult(reason="version_unsupported", payload_size=len(payload))

    try:
        stored_crc = unpack_crc(payload, payload_end)
    except ValueError:  # pragma: no cover - covered by length check above
        return _InnerCheckResult(reason="truncated", payload_size=len(payload))

    expected_crc = compute_crc(payload[:payload_end])
    if stored_crc != expected_crc:
        return _InnerCheckResult(reason="payload_crc_mismatch", payload_size=len(payload))

    return _InnerCheckResult(reason="ok", payload_size=len(payload))


# Re-export inner-format constants the verifier consults, so callers that
# only import the verifier can still pattern-match on them.
__all__ = [
    "MAGIC",
    "SIGNATURE_HEADER_MAGIC",
    "SUPPORTED_FORMAT_VERSIONS",
    "SUPPORTED_SIGNATURE_FORMAT_VERSIONS",
    "VerificationResult",
    "verify_signed_blob",
    "verify_unsigned_payload",
]
