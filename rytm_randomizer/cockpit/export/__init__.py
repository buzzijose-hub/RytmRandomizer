"""Cockpit model export pipeline — portable binary serialization for ``ProfileModel``.

This subpackage is Phase 3 of the cockpit/profile-model design (WS-G). It
produces and consumes the deployable artifact format described in
``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Model Export":

* :func:`pack_profile_model` — turn a :class:`~rytm_randomizer.cockpit.data.ProfileModel`
  into a versioned binary blob (header + MessagePack payload + CRC32).
* :func:`unpack_profile_model` — round-trip the binary back to a
  ``ProfileModel`` (used by tests today, and by the embedded hardware runtime
  in Phase 4).

The on-disk shape is intentionally tiny (typical profile < 100 KB), versioned
(header carries format and model versions), forward-compatible (new optional
fields don't break old loaders), and language-agnostic (MessagePack has
implementations in C, Rust, Python, JavaScript) so the GUI-produced model
runs identically on the embedded firmware.
"""

from __future__ import annotations

from .model_format import (
    FORMAT_VERSION,
    MAGIC,
    SUPPORTED_FORMAT_VERSIONS,
    Header,
)
from .serialize import pack_profile_model, unpack_profile_model
from .signing import (
    SIGNATURE_ALGO_HMAC_SHA256,
    SIGNATURE_FORMAT_VERSION,
    SIGNATURE_HEADER_MAGIC,
    SignedBlob,
    pack_signed,
    sign_profile_blob,
    unpack_signed,
)
from .verifier import (
    VerificationResult,
    verify_signed_blob,
    verify_unsigned_payload,
)

__all__ = [
    "FORMAT_VERSION",
    "Header",
    "MAGIC",
    "SIGNATURE_ALGO_HMAC_SHA256",
    "SIGNATURE_FORMAT_VERSION",
    "SIGNATURE_HEADER_MAGIC",
    "SUPPORTED_FORMAT_VERSIONS",
    "SignedBlob",
    "VerificationResult",
    "pack_profile_model",
    "pack_signed",
    "sign_profile_blob",
    "unpack_profile_model",
    "unpack_signed",
    "verify_signed_blob",
    "verify_unsigned_payload",
]
