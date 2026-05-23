"""Top-level pack/unpack entrypoints for the cockpit ``ProfileModel`` export.

The wire format and CRC computation live in :mod:`.model_format`. This
module composes them into a single round-trip pair that takes a
:class:`~rytm_randomizer.cockpit.data.ProfileModel` on one side and produces
the portable byte string the embedded firmware will eventually consume.

MessagePack handles the variable-length payload (the result of
``ProfileModel.to_dict()``); the header + CRC discipline keeps the blob
self-describing and corruption-detectable.
"""

from __future__ import annotations

import msgpack

from rytm_randomizer.cockpit.data import ProfileModel

from .model_format import (
    SUPPORTED_FORMAT_VERSIONS,
    build_header,
    compute_crc,
    pack_crc,
    parse_header,
    unpack_crc,
)


def pack_profile_model(profile: ProfileModel, *, format_version: int = 1) -> bytes:
    """Serialize ``profile`` to the portable binary format.

    The returned bytes are ready to write to disk (``Path.write_bytes``) or
    ship over the wire. The format is documented in
    :mod:`rytm_randomizer.cockpit.export.model_format` and in
    ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
    §"Model Export".

    The ``model_version`` field on the wire is taken from
    ``profile.model_version`` — it travels with the payload so the embedded
    runtime can route a freshly loaded blob to the right inference code
    without first MessagePack-decoding the body.

    Args:
        profile: The model to serialize.
        format_version: The header ``format_version`` to emit. Defaults to
            the current :data:`~.model_format.FORMAT_VERSION`; callers can
            pin an older value to produce a blob a legacy reader will
            accept, or pass an unsupported value to exercise the parser's
            rejection path in tests.

    Returns:
        The full binary blob (header + MessagePack payload + CRC32 trailer).
    """

    payload = msgpack.packb(profile.to_dict(), use_bin_type=True)
    header = build_header(
        format_version=format_version,
        model_version=profile.model_version,
        payload_len=len(payload),
    )
    header_and_payload = header + payload
    crc = compute_crc(header_and_payload)
    return header_and_payload + pack_crc(crc)


def unpack_profile_model(blob: bytes) -> ProfileModel:
    """Parse the binary format back to a :class:`ProfileModel`.

    The parser checks, in order: magic prefix, header completeness,
    payload-region completeness, CRC trailer presence, ``format_version``
    against :data:`~.model_format.SUPPORTED_FORMAT_VERSIONS`, CRC match
    against the recomputed value, and finally MessagePack + dataclass
    decode of the payload. Any failure raises :class:`ValueError` with a
    one-line reason — the embedded firmware will behave the same way.

    Raises:
        ValueError: bad magic, header truncated, payload truncated, CRC
            trailer missing, unsupported ``format_version``, CRC mismatch,
            malformed MessagePack payload, or payload that does not match
            the :class:`ProfileModel` shape.
    """

    header = parse_header(blob)
    payload_start = header.header_len
    payload_end = payload_start + header.payload_len
    if len(blob) < payload_end + 4:
        raise ValueError(
            "truncated input: blob ends inside payload or CRC "
            f"(need {payload_end + 4} bytes, got {len(blob)})"
        )
    if header.format_version not in SUPPORTED_FORMAT_VERSIONS:
        raise ValueError(
            f"unsupported format_version {header.format_version}; "
            f"supported: {sorted(SUPPORTED_FORMAT_VERSIONS)}"
        )
    payload = blob[payload_start:payload_end]
    stored_crc = unpack_crc(blob, payload_end)
    expected_crc = compute_crc(blob[:payload_end])
    if stored_crc != expected_crc:
        raise ValueError(f"crc mismatch: stored=0x{stored_crc:08x}, computed=0x{expected_crc:08x}")
    try:
        decoded = msgpack.unpackb(payload, raw=False)
    except (
        ValueError,
        msgpack.exceptions.ExtraData,
        msgpack.exceptions.FormatError,
        msgpack.exceptions.StackError,
    ) as exc:
        raise ValueError(f"malformed payload: {exc}") from exc
    if not isinstance(decoded, dict):
        raise ValueError(
            f"malformed payload: expected MessagePack map, got {type(decoded).__name__}"
        )
    try:
        return ProfileModel.from_dict(decoded)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"malformed payload: {exc}") from exc


__all__ = ["pack_profile_model", "unpack_profile_model"]
