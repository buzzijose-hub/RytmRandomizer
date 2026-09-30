"""Candidate Digitakt saved-project SysEx layout facts.

**Promotion status: CANDIDATE.** Unlike
:mod:`rytm_randomizer.data.analog_four_saved_kit_layout`, nothing in this
module is promoted. The one hardware-verified fact is the MK1 family byte
(``0x0A``), read from real PATTERN dumps pinned by
``tests/test_digitakt_real_captures.py``. The name position is still the
repository's synthetic candidate format: on a real dump it reads header
bytes, not a name. ``DIGITAKT_II_FAMILY_BYTE`` is an unverified guess.

Deliberately **absent** here, and required before any Digitakt mutation can
become sendable (``.claude/rules/targeted-mutation-safety.md`` #6):

* saved-project parameter byte offsets,
* per-track stride and value encodings,
* unpacked / packed / framed payload sizes,
* fixture-backed byte-diff isolation and exact re-encode evidence.

Those must be promoted from real captures. Inferring them from the live CC
facts in :mod:`rytm_randomizer.data.digitakt_midi` is explicitly forbidden
by that rule -- CC assignments describe working-RAM dials, not the layout
of a stored project.
"""

from __future__ import annotations

from typing import Final

#: Candidate family selectors, used only by synthetic-layout intake.
#: Real captures must validate these values and positions before promotion.
DIGITAKT_MK1_FAMILY_BYTE: Final[int] = 0x0A  # verified: real MK1 PATTERN dump, OS 1.52A
DIGITAKT_II_FAMILY_BYTE: Final[int] = 0x10

#: Candidate payload type byte, mirroring the A4 candidate-kit convention.
DIGITAKT_CANDIDATE_KIT_TYPE_BYTE: Final[int] = 0x07

#: Snapshot layout discriminators, mirroring the A4 vocabulary so reports
#: and decoders speak one language across device families.
DIGITAKT_SNAPSHOT_LAYOUT_CANDIDATE: Final[str] = "candidate"
DIGITAKT_SNAPSHOT_LAYOUT_SAVED_KIT: Final[str] = "saved_kit"

#: Kit-name field in a candidate payload: ASCII in the clear immediately
#: after the 3-byte manufacturer id + 1 family/type byte, matching the
#: shape the shared ``read_ascii_name`` helper already handles.
DIGITAKT_KIT_NAME_OFFSET: Final[int] = 4
DIGITAKT_KIT_NAME_LENGTH: Final[int] = 16

#: Flipped to ``True`` only by the change set that lands hardware-verified
#: offsets together with their capture fixtures. The current planner is
#: independently hard-blocked; changing this flag alone cannot enable sends.
DIGITAKT_OFFSETS_PROMOTED: Final[bool] = False

#: Operator-facing explanation used verbatim as a plan ``readiness_reason``.
DIGITAKT_UNPROMOTED_REASON: Final[str] = (
    "Digitakt offsets are candidate-only; saved-project parameter byte offsets, "
    "value encodings, per-track stride, and exact fixture evidence must be "
    "promoted before real send"
)


__all__ = [
    "DIGITAKT_CANDIDATE_KIT_TYPE_BYTE",
    "DIGITAKT_II_FAMILY_BYTE",
    "DIGITAKT_KIT_NAME_LENGTH",
    "DIGITAKT_KIT_NAME_OFFSET",
    "DIGITAKT_MK1_FAMILY_BYTE",
    "DIGITAKT_OFFSETS_PROMOTED",
    "DIGITAKT_SNAPSHOT_LAYOUT_CANDIDATE",
    "DIGITAKT_SNAPSHOT_LAYOUT_SAVED_KIT",
    "DIGITAKT_UNPROMOTED_REASON",
]
