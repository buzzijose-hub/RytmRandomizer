"""Optional HMAC-SHA256 signing envelope for cockpit ``ProfileModel`` blobs.

The existing :func:`rytm_randomizer.cockpit.export.pack_profile_model`
already self-describes its content via the ``RYMP`` magic + format version
+ CRC32 trailer. This module sits one layer above that and adds an
*optional* tamper-evidence layer: an operator-supplied secret key is used
to HMAC-sign the already-packed binary blob, the signature travels in a
small additional envelope (``RYMS``), and the receiver can verify the
envelope without ever having to MessagePack-decode the inner payload.

The signing layer is stdlib-only (``hashlib`` + ``hmac``) so we do not
take a dependency on the ``cryptography`` package. The wire format mirrors
the discipline of :mod:`.model_format`:

    magic:              4 bytes     ("RYMS" ascii)
    format_version:     uint16  BE  (currently 1)
    algo_len:           uint8       (length of the algorithm-name string)
    algo:               utf-8 bytes (currently always "hmac-sha256")
    key_id_len:         uint8       (length of the key-id string)
    key_id:             utf-8 bytes (operator-supplied label)
    sig_len:            uint8       (length of the signature)
    signature:          sig_len bytes
    payload_len:        uint32  BE  (length of the inner packed-profile blob)
    payload:            payload_len bytes (the existing ``RYMP`` blob)

Only :func:`pack_signed` / :func:`unpack_signed` ever raise. The verifier
in :mod:`.verifier` is the safe entry point for receivers — it never
raises and always returns a structured :class:`.verifier.VerificationResult`.
"""

from __future__ import annotations

import hashlib
import hmac
import struct
from dataclasses import dataclass
from typing import Final

# ---------------------------------------------------------------------------
# Format constants
# ---------------------------------------------------------------------------

SIGNATURE_HEADER_MAGIC: Final[bytes] = b"RYMS"
"""Four-byte magic prefix identifying a signed-envelope blob."""

SIGNATURE_FORMAT_VERSION: Final[int] = 1
"""Current signed-envelope format version emitted by :func:`pack_signed`."""

SUPPORTED_SIGNATURE_FORMAT_VERSIONS: Final[frozenset[int]] = frozenset({1})
"""Format versions :func:`unpack_signed` will accept.

New versions are added here as the format evolves; older readers must
reject unknown versions with :class:`ValueError`.
"""

SIGNATURE_ALGO_HMAC_SHA256: Final[str] = "hmac-sha256"
"""Algorithm name written into every v1 envelope."""

# Struct format strings for the fixed-width prefix.
_FIXED_PREFIX_STRUCT: Final[struct.Struct] = struct.Struct(">4sH")
"""magic (4s) + format_version (uint16)."""

_PAYLOAD_LEN_STRUCT: Final[struct.Struct] = struct.Struct(">I")
"""payload_len (uint32) — final field before the payload bytes."""

_FIXED_PREFIX_LEN: Final[int] = _FIXED_PREFIX_STRUCT.size  # 6
_PAYLOAD_LEN_FIELD_LEN: Final[int] = _PAYLOAD_LEN_STRUCT.size  # 4

# uint8 length-prefix maxima for the three variable-length string/bytes fields.
_ALGO_MAX_LEN: Final[int] = 0xFF
_KEY_ID_MAX_LEN: Final[int] = 0xFF
_SIGNATURE_MAX_LEN: Final[int] = 0xFF

# uint32 maximum for the payload-length field.
_PAYLOAD_MAX_LEN: Final[int] = 0xFFFF_FFFF


# ---------------------------------------------------------------------------
# SignedBlob dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SignedBlob:
    """In-memory view of a signed cockpit-profile blob.

    Build one of these via :func:`sign_profile_blob` (which fills in
    :attr:`signature` and :attr:`algorithm` deterministically) or
    reconstruct one via :func:`unpack_signed` (which parses the wire
    format). The dataclass is :func:`~dataclasses.dataclass` ``frozen``
    so receivers cannot accidentally mutate a parsed envelope.
    """

    payload: bytes
    """The existing packed-profile binary (the output of
    :func:`rytm_randomizer.cockpit.export.pack_profile_model`)."""

    algorithm: str
    """The signing algorithm name. Always ``"hmac-sha256"`` in v1."""

    key_id: str
    """The operator-supplied key label (e.g. ``"buzzi-2026-key"``)."""

    signature: bytes
    """The raw signature bytes. 32 bytes for HMAC-SHA256."""


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------


def sign_profile_blob(
    payload: bytes,
    *,
    key: bytes,
    key_id: str,
) -> SignedBlob:
    """HMAC-SHA256 sign an existing packed-profile binary.

    The signature is computed over the raw ``payload`` bytes — typically
    the output of :func:`rytm_randomizer.cockpit.export.pack_profile_model`
    — using ``key`` as the HMAC secret. The signature is deterministic
    given the same ``(payload, key)`` pair (HMAC has no nonce).

    Args:
        payload: The packed-profile binary to sign.
        key: The operator's HMAC secret. Keep this off-device and out of
            source control; the cockpit never persists it.
        key_id: A short operator-chosen label that travels with the
            envelope so the receiver can route between multiple known
            keys without trial-and-error verification.

    Returns:
        A :class:`SignedBlob` ready to be :func:`pack_signed`-ed.
    """

    signature = hmac.new(key, payload, hashlib.sha256).digest()
    return SignedBlob(
        payload=payload,
        algorithm=SIGNATURE_ALGO_HMAC_SHA256,
        key_id=key_id,
        signature=signature,
    )


# ---------------------------------------------------------------------------
# Wire format — pack
# ---------------------------------------------------------------------------


def pack_signed(blob: SignedBlob) -> bytes:
    """Serialize ``blob`` to the wire format documented at module level.

    Raises:
        ValueError: ``blob.algorithm`` exceeds 255 utf-8 bytes,
            ``blob.key_id`` exceeds 255 utf-8 bytes, ``blob.signature``
            exceeds 255 bytes, or ``blob.payload`` exceeds the uint32
            payload-length cap.
    """

    algo_bytes = blob.algorithm.encode("utf-8")
    if len(algo_bytes) > _ALGO_MAX_LEN:
        raise ValueError(
            "algorithm must encode to at most "
            f"{_ALGO_MAX_LEN} utf-8 bytes; got {len(algo_bytes)}"
        )
    key_id_bytes = blob.key_id.encode("utf-8")
    if len(key_id_bytes) > _KEY_ID_MAX_LEN:
        raise ValueError(
            "key_id must encode to at most "
            f"{_KEY_ID_MAX_LEN} utf-8 bytes; got {len(key_id_bytes)}"
        )
    if len(blob.signature) > _SIGNATURE_MAX_LEN:
        raise ValueError(
            f"signature must fit in {_SIGNATURE_MAX_LEN} bytes; got {len(blob.signature)}"
        )
    payload_len = len(blob.payload)
    if not (0 <= payload_len <= _PAYLOAD_MAX_LEN):
        raise ValueError(f"payload must fit in uint32 [0, {_PAYLOAD_MAX_LEN}]; got {payload_len}")

    return (
        _FIXED_PREFIX_STRUCT.pack(SIGNATURE_HEADER_MAGIC, SIGNATURE_FORMAT_VERSION)
        + bytes([len(algo_bytes)])
        + algo_bytes
        + bytes([len(key_id_bytes)])
        + key_id_bytes
        + bytes([len(blob.signature)])
        + blob.signature
        + _PAYLOAD_LEN_STRUCT.pack(payload_len)
        + blob.payload
    )


# ---------------------------------------------------------------------------
# Wire format — unpack
# ---------------------------------------------------------------------------


def unpack_signed(data: bytes) -> SignedBlob:
    """Parse the wire format back to a :class:`SignedBlob`.

    The parser walks the envelope strictly left-to-right, validating
    that each declared variable-length field fits inside the remaining
    bytes before consuming it. Any deviation is a :class:`ValueError`
    with a one-line reason — :func:`verify_signed_blob` is the
    swallow-and-report wrapper for receivers who never want the parser
    to raise.

    Raises:
        ValueError: bad magic, unsupported format version, blob shorter
            than the fixed prefix, blob ends inside any variable-length
            field, or any of the utf-8 string fields contain invalid
            utf-8.
    """

    if len(data) < _FIXED_PREFIX_LEN:
        raise ValueError(
            "truncated input: blob shorter than fixed prefix "
            f"({len(data)} < {_FIXED_PREFIX_LEN} bytes)"
        )
    magic, format_version = _FIXED_PREFIX_STRUCT.unpack_from(data, 0)
    if magic != SIGNATURE_HEADER_MAGIC:
        raise ValueError(f"bad magic: expected {SIGNATURE_HEADER_MAGIC!r}, got {magic!r}")
    if format_version not in SUPPORTED_SIGNATURE_FORMAT_VERSIONS:
        raise ValueError(
            f"unsupported signature format_version {format_version}; "
            f"supported: {sorted(SUPPORTED_SIGNATURE_FORMAT_VERSIONS)}"
        )

    offset = _FIXED_PREFIX_LEN

    algo, offset = _read_length_prefixed_utf8(data, offset, field_name="algorithm")
    key_id, offset = _read_length_prefixed_utf8(data, offset, field_name="key_id")
    signature, offset = _read_length_prefixed_bytes(data, offset, field_name="signature")

    if len(data) < offset + _PAYLOAD_LEN_FIELD_LEN:
        raise ValueError(
            "truncated input: blob ends inside payload-length field "
            f"(need {offset + _PAYLOAD_LEN_FIELD_LEN} bytes, got {len(data)})"
        )
    (payload_len,) = _PAYLOAD_LEN_STRUCT.unpack_from(data, offset)
    offset += _PAYLOAD_LEN_FIELD_LEN

    if len(data) < offset + payload_len:
        raise ValueError(
            "truncated input: blob ends inside payload "
            f"(need {offset + payload_len} bytes, got {len(data)})"
        )
    payload = data[offset : offset + payload_len]

    return SignedBlob(
        payload=payload,
        algorithm=algo,
        key_id=key_id,
        signature=signature,
    )


# ---------------------------------------------------------------------------
# Internal length-prefixed readers
# ---------------------------------------------------------------------------


def _read_length_prefixed_bytes(data: bytes, offset: int, *, field_name: str) -> tuple[bytes, int]:
    """Read a single-byte length prefix followed by ``length`` payload bytes.

    Returns the payload and the offset positioned immediately past it.
    Raises :class:`ValueError` if either the length prefix itself or the
    payload bytes overrun the buffer.
    """

    if len(data) < offset + 1:
        raise ValueError(
            f"truncated input: blob ends inside {field_name} length prefix "
            f"(need {offset + 1} bytes, got {len(data)})"
        )
    length = data[offset]
    start = offset + 1
    end = start + length
    if len(data) < end:
        raise ValueError(
            f"truncated input: blob ends inside {field_name} payload "
            f"(need {end} bytes, got {len(data)})"
        )
    return data[start:end], end


def _read_length_prefixed_utf8(data: bytes, offset: int, *, field_name: str) -> tuple[str, int]:
    """Read a length-prefixed byte field and decode it as utf-8.

    Raises :class:`ValueError` on truncation or on invalid utf-8.
    """

    raw, end = _read_length_prefixed_bytes(data, offset, field_name=field_name)
    try:
        return raw.decode("utf-8"), end
    except UnicodeDecodeError as exc:
        raise ValueError(f"malformed header: {field_name} is not valid utf-8: {exc}") from exc


__all__ = [
    "SIGNATURE_ALGO_HMAC_SHA256",
    "SIGNATURE_FORMAT_VERSION",
    "SIGNATURE_HEADER_MAGIC",
    "SUPPORTED_SIGNATURE_FORMAT_VERSIONS",
    "SignedBlob",
    "pack_signed",
    "sign_profile_blob",
    "unpack_signed",
]
