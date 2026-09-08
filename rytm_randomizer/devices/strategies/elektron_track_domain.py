"""Device-neutral Elektron track domain shared by every family's strategies.

Every Elektron family validates its track / pad ids the same way: a
one-based range bounded by the machine's own track count, itself bounded by
the 16 addressable MIDI channels. That logic is not device knowledge, so it
lives here once rather than being re-typed per family.

Per-family aliases (``AnalogFourTrackDomain``, ``DigitaktTrackDomain``) stay
in their own modules so call sites and error messages keep naming the
machine they are about; they are thin aliases of :class:`ElektronTrackDomain`,
not copies of its behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

#: Number of addressable MIDI channels. A hard protocol ceiling, not an
#: attribute of any one Elektron machine -- which is why it is defined here
#: rather than in a family-named module.
MAX_MIDI_TRACK_COUNT: Final[int] = 16


@dataclass(frozen=True)
class ElektronTrackDomain:
    """One validated device track domain shared by capability strategies."""

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


__all__ = ["MAX_MIDI_TRACK_COUNT", "ElektronTrackDomain"]
