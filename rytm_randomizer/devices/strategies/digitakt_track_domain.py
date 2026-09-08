"""Shared Digitakt track domain for planning and rendering.

Both Digitakt generations share this domain type; they differ only in
``track_count`` (8 for the MK1's audio tracks, 16 for the Digitakt II).
Reusing the same validated domain object across both devices is the
point -- it is why adding the second generation costs a constructor
argument rather than a parallel module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from ...data.digitakt_midi import (
    DIGITAKT_II_AUDIO_TRACK_COUNT,
    DIGITAKT_MK1_AUDIO_TRACK_COUNT,
)
from ...data.digitakt_saved_kit_layout import (
    DIGITAKT_II_FAMILY_BYTE,
    DIGITAKT_MK1_FAMILY_BYTE,
)
from .analog_four_track_domain import MAX_MIDI_TRACK_COUNT

#: Per-generation identity, re-exported through the strategies layer so
#: ``devices/digitakt.py`` composes strategies without importing ``data``
#: directly -- the ``devices`` row of the import-direction matrix allows
#: ``devices.strategies`` to read fact tables, but not ``devices`` itself.
DIGITAKT_MK1_TRACK_COUNT: Final[int] = DIGITAKT_MK1_AUDIO_TRACK_COUNT
DIGITAKT_II_TRACK_COUNT: Final[int] = DIGITAKT_II_AUDIO_TRACK_COUNT
DIGITAKT_MK1_FAMILY: Final[int] = DIGITAKT_MK1_FAMILY_BYTE
DIGITAKT_II_FAMILY: Final[int] = DIGITAKT_II_FAMILY_BYTE


@dataclass(frozen=True)
class DigitaktTrackDomain:
    """One validated Digitakt track domain shared by capability strategies."""

    track_count: int

    def __post_init__(self) -> None:
        if type(self.track_count) is not int or self.track_count < 1:
            raise ValueError(f"track_count must be a positive integer; got {self.track_count!r}")
        if self.track_count > MAX_MIDI_TRACK_COUNT:
            raise ValueError(
                f"track_count must not exceed {MAX_MIDI_TRACK_COUNT} MIDI channels; "
                f"got {self.track_count}"
            )

    @property
    def track_ids(self) -> range:
        """Return the complete one-based track domain."""

        return range(1, self.track_count + 1)

    def require_track(self, track: object, *, context: str) -> int:
        """Return ``track`` when it belongs to this domain, else fail closed."""

        if type(track) is not int or track not in self.track_ids:
            raise ValueError(f"{context}: track must be in [1, {self.track_count}], got {track!r}")
        return track


__all__ = [
    "DIGITAKT_II_FAMILY",
    "DIGITAKT_II_TRACK_COUNT",
    "DIGITAKT_MK1_FAMILY",
    "DIGITAKT_MK1_TRACK_COUNT",
    "DigitaktTrackDomain",
]
