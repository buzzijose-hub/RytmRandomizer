"""Analog Rytm MK2 ``SnapshotDecoder`` strategy.

Implements :class:`rytm_randomizer.snapshot.decoder.SnapshotDecoder` for the
Analog Rytm MK2. Consumes raw SysEx kit-dump bytes (already stripped of
``F0``/``F7`` framing) and produces a :class:`RytmKitSnapshot` carrying
slot, kit name, raw payload, and the unpacked 7-bit payload.

Single-responsibility: this module decodes Rytm SysEx into a Rytm
snapshot. It does NOT plan mutations, render messages, or touch the
device registry. The only inbound dependencies are the generic Elektron
envelope helpers in :mod:`rytm_randomizer.snapshot.envelope` (manufacturer
ID, 7-bit unpacking, kit-record location, ASCII name reading).

Per Gate 6 the decoder is structural (no inheritance); it satisfies the
WS-S6 ``SnapshotDecoder`` Protocol by exposing ``decode(raw, slot)``.

Per Gate 12 the kit-record offset constants are ``Final``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Final

from ...snapshot.envelope import (
    ELEKTRON_MFR_ID,
    find_kit_record,
    read_ascii_name,
    unpack_elektron_7bit,
)

# ---------------------------------------------------------------------------
# Snapshot dataclass -- the Rytm-specific shape callers treat opaque.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RytmSnapshotMachineFact:
    """One passive machine-value fact decoded from a Rytm kit snapshot."""

    pad: int
    raw_machine_value: int
    decoded_machine_value: int | None
    promoted: bool
    reason: str


@dataclass(frozen=True)
class RytmSnapshotMachineFacts:
    """Passive machine facts for all decoded Rytm pads."""

    facts_by_pad: Mapping[int, RytmSnapshotMachineFact]
    promoted: bool


def _empty_machine_facts() -> RytmSnapshotMachineFacts:
    return RytmSnapshotMachineFacts(facts_by_pad=MappingProxyType({}), promoted=False)


@dataclass(frozen=True)
class RytmKitSnapshot:
    """One Analog Rytm MK2 kit captured at a moment in time.

    Attributes are immutable so a snapshot taken at decode time can be
    safely passed to multiple planners / renderers without aliasing.

    * ``slot`` -- 0-based kit slot index this snapshot represents.
    * ``kit_name`` -- the 16-byte ASCII kit-name field, NUL-stripped.
    * ``raw`` -- the bytes the caller handed to the decoder (after F0/F7
      stripping).
    * ``unpacked`` -- the 7-bit-unstuffed payload bytes the rest of the
      decoder operates on.
    """

    slot: int
    kit_name: str
    raw: bytes
    unpacked: bytes
    machine_facts: RytmSnapshotMachineFacts = field(default_factory=_empty_machine_facts)


def rytm_snapshot_payload_fingerprint(snapshot: RytmKitSnapshot) -> str:
    """Return a stable short digest for the decoded Rytm kit payload."""

    payload = snapshot.unpacked or snapshot.raw
    return sha256(payload).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Elektron Rytm kit-record offsets (constants).
#
# The Analog Rytm MK2 MIDI implementation appendix documents the kit dump
# layout. After the manufacturer-id prefix, the kit record opens with a
# 1-byte kit-type byte (0x07 for Rytm kit) followed by the 16-byte kit
# name field. Subsequent fields (per-track sound records, level/mute/etc.)
# follow at documented offsets that the per-pad mutation planner consumes.
#
# We only decode the kit name in this WS to keep the strategy minimal.
# The planner needs the full kit record so we surface ``unpacked`` on the
# snapshot for it to slice.
# ---------------------------------------------------------------------------

#: The kit-record type byte that marks the start of an Analog Rytm MK2
#: kit dump (after the Elektron manufacturer-id prefix). Per the MK2 MIDI
#: implementation appendix; NOT secret -- any sniffer on the MIDI cable
#: sees the same byte in every Rytm kit-dump SysEx.
RYTM_KIT_TYPE_BYTE: Final[int] = 0x07

#: Byte offset of the 16-byte ASCII kit name within the unpacked kit payload.
#: Observed in real Rytm MKII kit dumps captured from the hardware.
_KIT_NAME_OFFSET: Final[int] = 8

#: Fixed length of the ASCII kit-name field. Elektron pads with NULs; the
#: ``read_ascii_name`` helper strips trailing NULs to surface the clean
#: operator-facing name.
_KIT_NAME_LENGTH: Final[int] = 16

_TRACK_COUNT: Final[int] = 12
_TRACK_MACHINE_VALUE_OFFSET: Final[int] = 174
_TRACK_SOUND_STRIDE: Final[int] = 162
_CANDIDATE_ONLY_PADS: Final[frozenset[int]] = frozenset({6, 7, 8})


def _extract_machine_facts(unpacked: bytes) -> RytmSnapshotMachineFacts:
    facts: dict[int, RytmSnapshotMachineFact] = {}
    for pad in range(1, _TRACK_COUNT + 1):
        offset = _TRACK_MACHINE_VALUE_OFFSET + (_TRACK_SOUND_STRIDE * (pad - 1))
        if offset >= len(unpacked):
            fact = RytmSnapshotMachineFact(
                pad=pad,
                raw_machine_value=-1,
                decoded_machine_value=None,
                promoted=False,
                reason=f"candidate machine offset {offset} is outside snapshot payload",
            )
        else:
            raw_value = unpacked[offset]
            promoted = pad not in _CANDIDATE_ONLY_PADS
            fact = RytmSnapshotMachineFact(
                pad=pad,
                raw_machine_value=raw_value,
                decoded_machine_value=raw_value if promoted else None,
                promoted=promoted,
                reason=(
                    "promoted machine fact" if promoted else "candidate-only tom-pad machine fact"
                ),
            )
        facts[pad] = fact
    return RytmSnapshotMachineFacts(
        facts_by_pad=MappingProxyType(facts),
        promoted=all(fact.promoted for fact in facts.values()),
    )


def _operator_kit_name(unpacked: bytes) -> str:
    """Return the display kit name from the unpacked Rytm kit payload."""

    return read_ascii_name(
        unpacked,
        offset=_KIT_NAME_OFFSET,
        length=_KIT_NAME_LENGTH,
    ).replace("\x00", "")


# ---------------------------------------------------------------------------
# Strategy implementation.
# ---------------------------------------------------------------------------


class AnalogRytmSnapshotDecoder:
    """``SnapshotDecoder`` strategy for the Analog Rytm MK2.

    The class is intentionally stateless -- one instance can be shared
    across the application. ``AnalogRytmDevice`` constructs one and holds
    it on its ``snapshot_decoder`` attribute.
    """

    def decode(self, raw: bytes, slot: int) -> RytmKitSnapshot:
        """Decode ``raw`` Rytm SysEx into a :class:`RytmKitSnapshot`.

        ``raw`` must:

        * start with the Elektron manufacturer-id prefix
          (``00 20 3C``) -- the caller has already stripped the
          surrounding ``F0`` / ``F7`` framing bytes,
        * contain a 7-bit-stuffed payload (high bit clear on every byte).

        Returns a :class:`RytmKitSnapshot` whose ``kit_name`` is the
        decoded operator-facing name and ``unpacked`` is the full 7-bit
        unstuffed payload for downstream planners to slice.

        Raises:
            ValueError: if the raw bytes do not start with the Elektron
                prefix, are not valid 7-bit data, or do not contain a
                Rytm kit-type byte; if ``slot`` is negative.
        """

        if slot < 0:
            raise ValueError(
                f"AnalogRytmSnapshotDecoder.decode: slot must be non-negative, got {slot}"
            )
        if not raw.startswith(ELEKTRON_MFR_ID):
            raise ValueError(
                "AnalogRytmSnapshotDecoder.decode: raw payload does not start "
                f"with Elektron manufacturer id 0x{ELEKTRON_MFR_ID.hex()} -- got "
                f"0x{raw[: len(ELEKTRON_MFR_ID)].hex()!r}. Strip the SysEx F0/F7 "
                "framing bytes before passing to decode()."
            )

        record = find_kit_record(raw, slot=0, kit_type_byte=RYTM_KIT_TYPE_BYTE)
        # ``find_kit_record`` returns the slice starting at the kit-type
        # byte; the 7-bit-stuffed payload follows immediately after.
        # Unpack the entire record so downstream planners see the full
        # parameter table, not just the prefix.
        unpacked = unpack_elektron_7bit(record[1:])
        kit_name = _operator_kit_name(unpacked)
        machine_facts = _extract_machine_facts(unpacked)
        return RytmKitSnapshot(
            slot=slot,
            kit_name=kit_name,
            raw=raw,
            unpacked=unpacked,
            machine_facts=machine_facts,
        )
