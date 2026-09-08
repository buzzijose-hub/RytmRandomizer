"""Digitakt snapshot decoder Strategy.

Structurally conforms to :class:`rytm_randomizer.snapshot.decoder.SnapshotDecoder`.

One decoder class serves both Digitakt generations; the family byte it
accepts is supplied at construction. Decoding stops at envelope + name
intake because the saved-project parameter offsets are not promoted -- see
:mod:`rytm_randomizer.data.digitakt_saved_kit_layout`.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Final

from ...data.digitakt_saved_kit_layout import (
    DIGITAKT_CANDIDATE_KIT_TYPE_BYTE,
    DIGITAKT_KIT_NAME_LENGTH,
    DIGITAKT_KIT_NAME_OFFSET,
    DIGITAKT_SNAPSHOT_LAYOUT_CANDIDATE,
    DIGITAKT_SNAPSHOT_LAYOUT_SAVED_KIT,
)
from ...snapshot.decoder import SnapshotDecoder
from ...snapshot.envelope import ELEKTRON_MFR_ID, read_ascii_name

_FAMILY_BYTE_INDEX: Final[int] = 3


@dataclass(frozen=True)
class DigitaktKitSnapshot:
    """Candidate Digitakt kit snapshot captured from a SysEx payload.

    ``offsets_promoted`` stays ``False`` for every Digitakt snapshot until
    saved-project offsets are validated against hardware. The mutation
    planner reads it and refuses to emit sendable events while it is unset.
    """

    slot: int
    kit_name: str
    raw: bytes
    device_id: str
    offsets_promoted: bool = False
    unpacked: bytes = b""
    snapshot_layout: str = DIGITAKT_SNAPSHOT_LAYOUT_CANDIDATE


class DigitaktSnapshotDecoder:
    """Decode a candidate Digitakt kit snapshot from raw bytes."""

    def __init__(self, *, family_byte: int, device_id: str) -> None:
        self.family_byte = family_byte
        self.device_id = device_id

    def decode(self, raw: bytes, slot: int) -> DigitaktKitSnapshot:
        """Decode ``raw`` into a :class:`DigitaktKitSnapshot`.

        Validates the shared Elektron envelope and reads the in-the-clear
        ASCII kit name. Parameter extraction belongs to a later
        offset-promotion workstream and is deliberately absent.
        """

        if slot < 0:
            raise ValueError("DigitaktSnapshotDecoder.decode: slot must be non-negative")
        if not raw.startswith(ELEKTRON_MFR_ID):
            raise ValueError("DigitaktSnapshotDecoder.decode: missing Elektron manufacturer id")
        if len(raw) <= _FAMILY_BYTE_INDEX:
            raise ValueError(
                "DigitaktSnapshotDecoder.decode: payload too short for family/type byte"
            )

        family_or_type = raw[_FAMILY_BYTE_INDEX]
        if family_or_type == DIGITAKT_CANDIDATE_KIT_TYPE_BYTE:
            layout = DIGITAKT_SNAPSHOT_LAYOUT_CANDIDATE
        elif family_or_type == self.family_byte:
            layout = DIGITAKT_SNAPSHOT_LAYOUT_SAVED_KIT
        else:
            raise ValueError(
                "DigitaktSnapshotDecoder.decode: expected candidate kit type byte "
                f"0x{DIGITAKT_CANDIDATE_KIT_TYPE_BYTE:02x} or Digitakt family byte "
                f"0x{self.family_byte:02x}, got 0x{family_or_type:02x}"
            )

        if len(raw) < DIGITAKT_KIT_NAME_OFFSET + DIGITAKT_KIT_NAME_LENGTH:
            raise ValueError("DigitaktSnapshotDecoder.decode: payload too short for kit name")

        kit_name = read_ascii_name(
            raw,
            offset=DIGITAKT_KIT_NAME_OFFSET,
            length=DIGITAKT_KIT_NAME_LENGTH,
        )
        return DigitaktKitSnapshot(
            slot=slot,
            kit_name=kit_name,
            raw=bytes(raw),
            device_id=self.device_id,
            offsets_promoted=False,
            unpacked=bytes(raw),
            snapshot_layout=layout,
        )


def digitakt_snapshot_payload_fingerprint(snapshot: DigitaktKitSnapshot) -> str:
    """Return a stable short digest for the decoded Digitakt kit payload."""

    payload = snapshot.unpacked or snapshot.raw
    return sha256(payload).hexdigest()[:16]


def _satisfies_snapshot_decoder(value: object) -> bool:
    """Structural check behind an ``object`` parameter (see digitakt.py)."""

    return isinstance(value, SnapshotDecoder)


def _assert_decoder_protocol_conformance() -> None:
    """Document structural conformance to the WS-S6 ``SnapshotDecoder``."""

    probe = DigitaktSnapshotDecoder(family_byte=0x0C, device_id="_probe")
    if not _satisfies_snapshot_decoder(probe):
        # Structural-typing invariant; see docs/ARCHITECTURE.md §8.
        raise AssertionError(  # pragma: no cover - structural-typing invariant
            "DigitaktSnapshotDecoder does not satisfy SnapshotDecoder"
        )


_assert_decoder_protocol_conformance()


__all__ = [
    "DigitaktKitSnapshot",
    "DigitaktSnapshotDecoder",
    "digitakt_snapshot_payload_fingerprint",
]
