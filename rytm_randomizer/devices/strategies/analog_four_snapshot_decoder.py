"""Analog Four MKII snapshot decoder Strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from ...snapshot.envelope import ELEKTRON_MFR_ID, read_ascii_name

A4_CANDIDATE_KIT_TYPE_BYTE: Final[int] = 0x07
_KIT_NAME_OFFSET: Final[int] = 4
_KIT_NAME_LENGTH: Final[int] = 16


@dataclass(frozen=True)
class AnalogFourKitSnapshot:
    """Candidate Analog Four kit snapshot captured from a SysEx payload."""

    slot: int
    kit_name: str
    raw: bytes
    offsets_promoted: bool = False


class AnalogFourSnapshotDecoder:
    """Decode a candidate Analog Four kit snapshot from raw bytes."""

    def decode(self, raw: bytes, slot: int) -> AnalogFourKitSnapshot:
        """Decode ``raw`` into an :class:`AnalogFourKitSnapshot`.

        The Analog Four offset map is candidate-level at this stage. This
        strategy validates the shared Elektron envelope and preserves the raw
        bytes; promoted field extraction belongs to the later offset-promotion
        workstream.
        """

        if slot < 0:
            raise ValueError("AnalogFourSnapshotDecoder.decode: slot must be non-negative")
        if not raw.startswith(ELEKTRON_MFR_ID):
            raise ValueError(
                "AnalogFourSnapshotDecoder.decode: missing Elektron manufacturer id"
            )
        if len(raw) < _KIT_NAME_OFFSET + _KIT_NAME_LENGTH:
            raise ValueError("AnalogFourSnapshotDecoder.decode: payload too short for kit name")
        if raw[3] != A4_CANDIDATE_KIT_TYPE_BYTE:
            raise ValueError(
                "AnalogFourSnapshotDecoder.decode: candidate kit type byte 0x07 not present"
            )

        kit_name = read_ascii_name(raw, offset=_KIT_NAME_OFFSET, length=_KIT_NAME_LENGTH)
        return AnalogFourKitSnapshot(
            slot=slot,
            kit_name=kit_name,
            raw=bytes(raw),
            offsets_promoted=False,
        )
