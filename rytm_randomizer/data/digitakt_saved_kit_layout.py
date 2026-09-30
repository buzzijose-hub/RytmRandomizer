"""Digitakt SysEx dump layout facts.

**Verified (Digitakt MK1, OS 1.52A)** from two real PATTERN dumps captured by
a hardware verifier and pinned byte for byte by
``tests/test_digitakt_real_captures.py`` and
``tests/test_devices_strategies_digitakt_pattern_codec.py``:

* the MK1 family byte, the PATTERN object byte and the 9-byte header,
* the envelope: MSB-first 7-bit packing (the ``BE EF BA CE`` kit marker
  unpacks only in that order), a 14-bit checksum over the whole packed body,
  and a 14-bit length field holding ``(packed + 5) & 0x3FFF``,
* the exact packed and unpacked sizes, and a byte-exact re-encode,
* **one** parameter's location: track 1 filter frequency. The two captures
  differ in exactly that unpacked byte (0 -> 127) plus the checksum.

A Digitakt has no separate KIT dump: SETTINGS > SYSEX DUMP > SYSEX SEND >
PATTERN sends the pattern together with the kit it plays, so "kit" in these
names means the sound data *inside* a pattern dump.

**Not verified, and deliberately absent as facts** (required before anything
beyond that one field can be written; ``.claude/rules/targeted-mutation-
safety.md`` #6):

* per-track stride. The dump strongly suggests eight 160-byte sound blocks
  starting at unpacked offset 25136, with filter frequency 68 bytes in -- but
  a stride is promoted only from a matched capture on another track,
* any other parameter, and mid-range value encoding (only 0 and 127 seen;
  a possible fine byte after the promoted one is unconfirmed),
* everything about the Digitakt II, including its family byte.

Never infer these from the live CC facts in
:mod:`rytm_randomizer.data.digitakt_midi`: CC assignments describe
working-RAM dials, not the layout of a stored dump.
"""

from __future__ import annotations

from typing import Final

#: Byte after the Elektron manufacturer id. MK1 verified from real dumps
#: (it was a 0x0C guess until then); the Digitakt II value is still a guess.
DIGITAKT_MK1_FAMILY_BYTE: Final[int] = 0x0A
DIGITAKT_II_FAMILY_BYTE: Final[int] = 0x10

#: Object byte at payload index 5 of a PATTERN dump.
DIGITAKT_PATTERN_OBJECT_BYTE: Final[int] = 0x50

#: Envelope, identical in shape to the Analog Four saved-kit envelope.
DIGITAKT_PATTERN_HEADER_SIZE_WITHOUT_F0: Final[int] = 9
DIGITAKT_PATTERN_TRAILER_SIZE: Final[int] = 4
DIGITAKT_PATTERN_CHECKSUM_PACKED_OFFSET: Final[int] = 0
DIGITAKT_PATTERN_LENGTH_ADJUSTMENT: Final[int] = 5

#: Exact MK1 PATTERN sizes (framed = F0 + header + packed + trailer + F7).
DIGITAKT_MK1_PATTERN_PACKED_SIZE: Final[int] = 31598
DIGITAKT_MK1_PATTERN_UNPACKED_SIZE: Final[int] = 27648
DIGITAKT_MK1_PATTERN_FRAMED_SIZE: Final[int] = 31613

#: The one promoted parameter: MK1 track 1 filter frequency, unpacked offset.
#: Observed values are the endpoints only: 0 (FREQ 0) and 127 (FREQ 127).
#: Mid-range encoding is unverified, and so is the next byte (25205, 0x00 in
#: both captures), which may be a fine/LSB half -- a writer must not assume
#: a single-byte 0..127 field until a mid-value capture settles both.
DIGITAKT_MK1_TRACK1_FILTER_FREQUENCY_OFFSET: Final[int] = 25204

#: Snapshot layout discriminators.
DIGITAKT_SNAPSHOT_LAYOUT_PATTERN: Final[str] = "pattern"
DIGITAKT_SNAPSHOT_LAYOUT_UNVERIFIED: Final[str] = "unverified"

#: Flipped to ``True`` only by the change set that lands a planner able to
#: emit the promoted field(s). The planner is independently hard-blocked;
#: changing this flag alone cannot enable sends.
DIGITAKT_OFFSETS_PROMOTED: Final[bool] = False

#: Operator-facing explanation used verbatim as a plan ``readiness_reason``.
DIGITAKT_UNPROMOTED_REASON: Final[str] = (
    "Digitakt sends are not enabled: no planner emits hardware-verified Digitakt "
    "fields yet, and the only verified location so far is Digitakt MK1 track 1 "
    "filter frequency; value encoding, per-track stride, and other parameters "
    "must be promoted before real send"
)


__all__ = [
    "DIGITAKT_II_FAMILY_BYTE",
    "DIGITAKT_MK1_FAMILY_BYTE",
    "DIGITAKT_MK1_PATTERN_FRAMED_SIZE",
    "DIGITAKT_MK1_PATTERN_PACKED_SIZE",
    "DIGITAKT_MK1_PATTERN_UNPACKED_SIZE",
    "DIGITAKT_MK1_TRACK1_FILTER_FREQUENCY_OFFSET",
    "DIGITAKT_OFFSETS_PROMOTED",
    "DIGITAKT_PATTERN_CHECKSUM_PACKED_OFFSET",
    "DIGITAKT_PATTERN_HEADER_SIZE_WITHOUT_F0",
    "DIGITAKT_PATTERN_LENGTH_ADJUSTMENT",
    "DIGITAKT_PATTERN_OBJECT_BYTE",
    "DIGITAKT_PATTERN_TRAILER_SIZE",
    "DIGITAKT_SNAPSHOT_LAYOUT_PATTERN",
    "DIGITAKT_SNAPSHOT_LAYOUT_UNVERIFIED",
    "DIGITAKT_UNPROMOTED_REASON",
]
