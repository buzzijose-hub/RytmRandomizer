"""Digitakt snapshot decoder Strategy.

Structurally conforms to :class:`rytm_randomizer.snapshot.decoder.SnapshotDecoder`.

One decoder class serves both Digitakt generations; the family byte it
accepts, and the pattern layout it can fully validate, are supplied at
construction. Only the Digitakt MK1 has a verified layout
(:data:`~rytm_randomizer.devices.strategies.digitakt_pattern_codec.DIGITAKT_MK1_PATTERN_LAYOUT`):

* a MK1 PATTERN dump is checksum-, length- and size-validated and unpacked
  (layout ``"pattern"``);
* anything else carrying the right family byte -- another object type, or
  any Digitakt II dump -- is accepted for evidence intake only, undecoded
  (layout ``"unverified"``).

No layout yields a name: where a Digitakt stores one has not been verified,
and reading guessed bytes as text produced control-character "names" on
real hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Final

from ...data.digitakt_saved_kit_layout import (
    DIGITAKT_MK1_FAMILY_BYTE,
    DIGITAKT_SNAPSHOT_LAYOUT_PATTERN,
    DIGITAKT_SNAPSHOT_LAYOUT_UNVERIFIED,
)
from ...snapshot.decoder import SnapshotDecoder
from ...snapshot.envelope import ELEKTRON_MFR_ID
from .digitakt_pattern_codec import (
    DIGITAKT_MK1_PATTERN_LAYOUT,
    DigitaktPatternLayout,
    decode_digitakt_pattern_payload,
    is_digitakt_pattern_payload,
)

_FAMILY_BYTE_INDEX: Final[int] = len(ELEKTRON_MFR_ID)


@dataclass(frozen=True)
class DigitaktKitSnapshot:
    """A Digitakt dump captured from a SysEx payload.

    ``unpacked`` holds the decoded body for a verified pattern and is empty
    otherwise. ``offsets_promoted`` stays ``False``: the mutation planner
    reads it and refuses to emit sendable events while it is unset.
    """

    slot: int
    kit_name: str
    raw: bytes
    device_id: str
    offsets_promoted: bool = False
    unpacked: bytes = b""
    snapshot_layout: str = DIGITAKT_SNAPSHOT_LAYOUT_UNVERIFIED


class DigitaktSnapshotDecoder:
    """Decode a Digitakt dump from an unframed SysEx payload."""

    def __init__(
        self,
        *,
        family_byte: int,
        device_id: str,
        pattern_layout: DigitaktPatternLayout | None = None,
    ) -> None:
        if pattern_layout is not None and pattern_layout.family_byte != family_byte:
            raise ValueError("DigitaktSnapshotDecoder: pattern layout is for another family")
        self.family_byte = family_byte
        self.device_id = device_id
        self.pattern_layout = pattern_layout

    def decode(self, raw: bytes, slot: int) -> DigitaktKitSnapshot:
        """Decode ``raw`` into a :class:`DigitaktKitSnapshot`.

        Raises :class:`ValueError` for a bad slot, a non-Elektron or
        other-family payload, or a pattern that fails validation.
        """

        if type(slot) is not int or slot < 0:
            raise ValueError("DigitaktSnapshotDecoder.decode: slot must be non-negative integer")
        if not raw.startswith(ELEKTRON_MFR_ID):
            raise ValueError("DigitaktSnapshotDecoder.decode: missing Elektron manufacturer id")
        if len(raw) <= _FAMILY_BYTE_INDEX:
            raise ValueError("DigitaktSnapshotDecoder.decode: payload too short for family byte")
        family = raw[_FAMILY_BYTE_INDEX]
        if family != self.family_byte:
            raise ValueError(
                "DigitaktSnapshotDecoder.decode: expected Digitakt family byte "
                f"0x{self.family_byte:02x}, got 0x{family:02x}"
            )

        if self.pattern_layout is not None and is_digitakt_pattern_payload(
            raw, self.pattern_layout
        ):
            pattern = decode_digitakt_pattern_payload(raw, self.pattern_layout)
            return DigitaktKitSnapshot(
                slot=slot,
                kit_name="",
                raw=bytes(raw),
                device_id=self.device_id,
                unpacked=pattern.unpacked,
                snapshot_layout=DIGITAKT_SNAPSHOT_LAYOUT_PATTERN,
            )
        return DigitaktKitSnapshot(
            slot=slot,
            kit_name="",
            raw=bytes(raw),
            device_id=self.device_id,
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

    probe = DigitaktSnapshotDecoder(
        family_byte=DIGITAKT_MK1_FAMILY_BYTE,
        device_id="_probe",
        pattern_layout=DIGITAKT_MK1_PATTERN_LAYOUT,
    )
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
