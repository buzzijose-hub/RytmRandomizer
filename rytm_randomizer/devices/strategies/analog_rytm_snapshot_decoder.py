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

from ...data.analog_rytm_kit_layout import (
    RYTM_KIT_DUMP_ID,
    RYTM_KIT_NAME_LENGTH,
    RYTM_KIT_NAME_OFFSET,
    RYTM_KIT_RAW_SIZE,
    RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0,
    RYTM_KIT_SYSEX_TRAILER_SIZE_WITHOUT_F7,
    RYTM_KIT_TRACK_COUNT,
    RYTM_KIT_WORK_BUFFER_DUMP_ID,
    RYTM_SOUND_MACHINE_TYPE_OFFSET,
    RYTM_SYSEX_PRODUCT_ID,
    analog_rytm_track_sound_offset,
)
from ...snapshot.elektron_packed_payload import split_elektron_packed_payload_body
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
    * ``unpacked`` -- the decoded raw kit bytes the rest of the decoder
      operates on after the Elektron SysEx header/trailer and 7-bit packing
      are removed.
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
# The raw 8-bit kit record is decoded from the Elektron SysEx envelope and
# then interpreted through the shared Rytm kit-layout data table. The planner
# and snapshot shell need that raw kit record so we surface it as ``unpacked``
# on the snapshot for downstream slicing.
# ---------------------------------------------------------------------------

#: Product/type byte used by older minimal test payloads before the decoder
#: learned the full Elektron dump header/trailer shape.
RYTM_KIT_TYPE_BYTE: Final[int] = 0x07

#: Byte offset of the 16-byte ASCII kit name within the raw kit payload.
#: Observed in real Rytm MKII kit dumps captured from the hardware.
_KIT_NAME_OFFSET: Final[int] = RYTM_KIT_NAME_OFFSET

#: Fixed length of the ASCII kit-name field. Elektron pads with NULs; the
#: ``read_ascii_name`` helper strips trailing NULs to surface the clean
#: operator-facing name.
_KIT_NAME_LENGTH: Final[int] = RYTM_KIT_NAME_LENGTH

_CANDIDATE_ONLY_PADS: Final[frozenset[int]] = frozenset({6, 7, 8})
_FULL_KIT_DUMP_IDS: Final[frozenset[int]] = frozenset(
    {RYTM_KIT_DUMP_ID, RYTM_KIT_WORK_BUFFER_DUMP_ID}
)


def _extract_machine_facts(unpacked: bytes) -> RytmSnapshotMachineFacts:
    facts: dict[int, RytmSnapshotMachineFact] = {}
    for pad in range(1, RYTM_KIT_TRACK_COUNT + 1):
        offset = analog_rytm_track_sound_offset(pad, RYTM_SOUND_MACHINE_TYPE_OFFSET)
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
            decoded_value = raw_value & 0x7F
            promoted = pad not in _CANDIDATE_ONLY_PADS
            fact = RytmSnapshotMachineFact(
                pad=pad,
                raw_machine_value=raw_value,
                decoded_machine_value=decoded_value if promoted else None,
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


def _looks_like_full_kit_dump(raw: bytes) -> bool:
    min_length = RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0 + RYTM_KIT_SYSEX_TRAILER_SIZE_WITHOUT_F7
    return (
        len(raw) >= min_length
        and raw.startswith(ELEKTRON_MFR_ID)
        and raw[len(ELEKTRON_MFR_ID)] == RYTM_SYSEX_PRODUCT_ID
        and raw[5] in _FULL_KIT_DUMP_IDS
    )


def _unpack_full_kit_dump(raw: bytes) -> bytes:
    body = split_elektron_packed_payload_body(
        raw,
        header_size=RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0,
        trailer_size=RYTM_KIT_SYSEX_TRAILER_SIZE_WITHOUT_F7,
        device_label="Analog Rytm kit snapshot",
    )
    unpacked = unpack_elektron_7bit(body.packed)
    if len(unpacked) != RYTM_KIT_RAW_SIZE:
        raise ValueError(
            "AnalogRytmSnapshotDecoder.decode: decoded kit payload has "
            f"{len(unpacked)} byte(s), expected {RYTM_KIT_RAW_SIZE}"
        )
    return unpacked


def _unpack_legacy_kit_body(raw: bytes) -> bytes:
    record = find_kit_record(raw, slot=0, kit_type_byte=RYTM_KIT_TYPE_BYTE)
    unpacked = unpack_elektron_7bit(record[1:])
    if len(unpacked) >= RYTM_KIT_RAW_SIZE + 4 and unpacked[:4] == bytes(
        [RYTM_KIT_DUMP_ID, 0x01, 0x01, 0x00]
    ):
        return unpacked[4 : 4 + RYTM_KIT_RAW_SIZE]
    return unpacked


def _unpack_kit_payload(raw: bytes) -> bytes:
    if _looks_like_full_kit_dump(raw):
        return _unpack_full_kit_dump(raw)
    return _unpack_legacy_kit_body(raw)


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
        decoded operator-facing name and ``unpacked`` is the raw 8-bit kit
        payload for downstream planners to slice.

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

        unpacked = _unpack_kit_payload(raw)
        kit_name = _operator_kit_name(unpacked)
        machine_facts = _extract_machine_facts(unpacked)
        return RytmKitSnapshot(
            slot=slot,
            kit_name=kit_name,
            raw=raw,
            unpacked=unpacked,
            machine_facts=machine_facts,
        )
