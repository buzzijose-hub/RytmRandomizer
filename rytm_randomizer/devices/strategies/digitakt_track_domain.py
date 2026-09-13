"""Shared Digitakt track domain for planning and rendering.

Both Digitakt generations use this domain; they differ only in
``track_count`` (8 for the MK1's audio tracks, 16 for the Digitakt II).
The validation logic itself is device-neutral and lives once in
:mod:`rytm_randomizer.devices.strategies.elektron_track_domain`.

This module also re-exports the two per-generation identity facts that
``devices/digitakt.py`` needs to compose its strategies. That indirection is
deliberate: the import-direction matrix lets ``devices.strategies`` read
``data`` fact tables but does **not** let ``devices`` do so, and device
composition belongs in ``devices/``. Reading the facts here keeps the
declared layering intact without re-typing any of them.
"""

from __future__ import annotations

from typing import Final

from ...data.digitakt_midi import (
    DIGITAKT_II_AUDIO_TRACK_COUNT,
    DIGITAKT_MK1_AUDIO_TRACK_COUNT,
)
from ...data.digitakt_saved_kit_layout import (
    DIGITAKT_II_FAMILY_BYTE,
    DIGITAKT_MK1_FAMILY_BYTE,
)
from .elektron_track_domain import ElektronTrackDomain

#: Digitakt track domain. A thin alias of the shared implementation --
#: not a second copy of the validation rules.
DigitaktTrackDomain = ElektronTrackDomain

#: Per-generation identity, re-exported for ``devices/digitakt.py``.
DIGITAKT_MK1_TRACK_COUNT: Final[int] = DIGITAKT_MK1_AUDIO_TRACK_COUNT
DIGITAKT_II_TRACK_COUNT: Final[int] = DIGITAKT_II_AUDIO_TRACK_COUNT
DIGITAKT_MK1_FAMILY: Final[int] = DIGITAKT_MK1_FAMILY_BYTE
DIGITAKT_II_FAMILY: Final[int] = DIGITAKT_II_FAMILY_BYTE


__all__ = [
    "DIGITAKT_II_FAMILY",
    "DIGITAKT_II_TRACK_COUNT",
    "DIGITAKT_MK1_FAMILY",
    "DIGITAKT_MK1_TRACK_COUNT",
    "DigitaktTrackDomain",
]
