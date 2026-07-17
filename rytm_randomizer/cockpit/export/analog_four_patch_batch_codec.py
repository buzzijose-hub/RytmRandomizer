"""Shared wire contract for immutable Analog Four patch-batch JSON artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Final, cast

BATCH_SCHEMA_VERSION: Final[str] = "analog-four-audio-patch-batch-v1"
CANDIDATE_SCHEMA_VERSION: Final[str] = "analog-four-audio-patch-candidate-v1"


def encode_analog_four_patch_batch_json(payload: Mapping[str, object]) -> bytes:
    """Return the canonical bytes used for storage and payload hashes."""

    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def decode_analog_four_patch_batch_json(data: bytes, *, label: str) -> Mapping[str, object]:
    """Decode one artifact object while preserving the reader's strict shape."""

    try:
        decoded = cast(object, json.loads(data.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict) or not all(isinstance(key, str) for key in decoded):
        raise ValueError(f"{label} must be a JSON object")
    return cast(dict[str, object], decoded)


def analog_four_patch_batch_sha256(data: bytes) -> str:
    """Return the lowercase SHA-256 digest for exact artifact bytes."""

    return hashlib.sha256(data).hexdigest()


def analog_four_patch_batch_payload_sha256(payload: Mapping[str, object]) -> str:
    """Hash a JSON object using the canonical artifact encoding."""

    return analog_four_patch_batch_sha256(encode_analog_four_patch_batch_json(payload))


__all__ = [
    "BATCH_SCHEMA_VERSION",
    "CANDIDATE_SCHEMA_VERSION",
    "analog_four_patch_batch_payload_sha256",
    "analog_four_patch_batch_sha256",
    "decode_analog_four_patch_batch_json",
    "encode_analog_four_patch_batch_json",
]
