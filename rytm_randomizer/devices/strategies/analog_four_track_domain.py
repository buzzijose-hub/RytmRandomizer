"""Shared Analog Four track domain for planning and rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

MAX_MIDI_TRACK_COUNT: Final[int] = 16


@dataclass(frozen=True)
class AnalogFourTrackDomain:
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


__all__ = ["AnalogFourTrackDomain", "MAX_MIDI_TRACK_COUNT"]
