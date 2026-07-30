"""Analog Four MKII snapshot decoder Strategy."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Final

from ...snapshot.envelope import ELEKTRON_MFR_ID, read_ascii_name
from .analog_four_offset_manifest import (
    A4_CANDIDATE_KIT_TYPE_BYTE,
    A4_FAMILY_BYTE,
    A4_KIT_NAME_LENGTH,
    A4_SNAPSHOT_LAYOUT_CANDIDATE,
    A4_SNAPSHOT_LAYOUT_SAVED_KIT,
)
from .analog_four_saved_kit_codec import decode_analog_four_saved_kit_payload

_CANDIDATE_KIT_NAME_OFFSET: Final[int] = 4


@dataclass(frozen=True)
class AnalogFourKitSnapshot:
    """Candidate Analog Four kit snapshot captured from a SysEx payload."""

    slot: int
    kit_name: str
    raw: bytes
    offsets_promoted: bool = False
    unpacked: bytes = b""
    snapshot_layout: str = A4_SNAPSHOT_LAYOUT_CANDIDATE


class AnalogFourSnapshotDecoder:
    """Decode a candidate Analog Four kit snapshot from raw bytes."""

    def decode(self, raw: bytes, slot: int) -> AnalogFourKitSnapshot:
        """Decode ``raw`` into an :class:`AnalogFourKitSnapshot`.

        The Analog Four offset map is candidate-level at this stage. This
        strategy validates the shared Elektron envelope, recognizes the real
        saved-kit SysEx frame shape, and preserves both raw and unpacked bytes.
        Promoted parameter extraction belongs to a later offset-promotion
        workstream.
        """

        if slot < 0:
            raise ValueError("AnalogFourSnapshotDecoder.decode: slot must be non-negative")
        if not raw.startswith(ELEKTRON_MFR_ID):
            raise ValueError("AnalogFourSnapshotDecoder.decode: missing Elektron manufacturer id")
        if len(raw) <= len(ELEKTRON_MFR_ID):
            raise ValueError(
                "AnalogFourSnapshotDecoder.decode: payload too short for family/type byte"
            )

        family_or_type = raw[3]
        if family_or_type == A4_CANDIDATE_KIT_TYPE_BYTE:
            return _decode_candidate_payload(raw, slot=slot)
        if family_or_type == A4_FAMILY_BYTE:
            return _decode_saved_kit_payload(raw, slot=slot)
        raise ValueError(
            "AnalogFourSnapshotDecoder.decode: candidate kit type byte 0x07 "
            "or Analog Four family byte 0x06 not present"
        )


def analog_four_snapshot_payload_fingerprint(snapshot: AnalogFourKitSnapshot) -> str:
    """Return a stable short digest for the decoded A4 kit payload."""

    payload = snapshot.unpacked or snapshot.raw
    return sha256(payload).hexdigest()[:16]


def _decode_candidate_payload(raw: bytes, *, slot: int) -> AnalogFourKitSnapshot:
    if len(raw) < _CANDIDATE_KIT_NAME_OFFSET + A4_KIT_NAME_LENGTH:
        raise ValueError("AnalogFourSnapshotDecoder.decode: payload too short for kit name")
    if raw[3] != A4_CANDIDATE_KIT_TYPE_BYTE:
        raise ValueError(
            "AnalogFourSnapshotDecoder.decode: candidate kit type byte 0x07 not present"
        )

    kit_name = read_ascii_name(
        raw,
        offset=_CANDIDATE_KIT_NAME_OFFSET,
        length=A4_KIT_NAME_LENGTH,
    )
    return AnalogFourKitSnapshot(
        slot=slot,
        kit_name=kit_name,
        raw=bytes(raw),
        offsets_promoted=False,
        unpacked=bytes(raw),
        snapshot_layout=A4_SNAPSHOT_LAYOUT_CANDIDATE,
    )


def _decode_saved_kit_payload(raw: bytes, *, slot: int) -> AnalogFourKitSnapshot:
    decoded = decode_analog_four_saved_kit_payload(raw, require_trailer=False)
    return AnalogFourKitSnapshot(
        slot=slot,
        kit_name=decoded.kit_name,
        raw=bytes(raw),
        offsets_promoted=False,
        unpacked=decoded.unpacked,
        snapshot_layout=A4_SNAPSHOT_LAYOUT_SAVED_KIT,
    )
