"""Device-neutral Elektron track domain shared by every family's strategies.

Every Elektron family validates its track / pad ids the same way: a
one-based range bounded by the machine's own track count, itself bounded by
the 16 addressable MIDI channels. That logic is not device knowledge, so it
lives here once rather than being re-typed per family.

Rendering one plan event into a CC is equally family-neutral -- one-based
track to zero-based channel, 7-bit control and value -- so
:meth:`ElektronTrackDomain.cc_triple` and :meth:`ElektronTrackDomain.cc_message`
are the single implementation every family's message renderer calls.

Per-family aliases (``AnalogFourTrackDomain``, ``DigitaktTrackDomain``) stay
in their own modules so call sites and error messages keep naming the
machine they are about; they are thin aliases of :class:`ElektronTrackDomain`,
not copies of its behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from ...mock_midi import MidiMessage, build_cc_message

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

    def cc_triple(
        self, *, track: int, control: int, value: int, context: str
    ) -> tuple[int, int, int]:
        """Return the zero-based ``(channel, control, value)`` for one track change.

        The track must belong to this domain and the control and value must be
        7-bit; ``context`` names the caller in every error.
        """

        self.require_track(track, context=context)
        if control < 0 or control > 127:
            raise ValueError(f"{context}: control must be in [0, 127]")
        if value < 0 or value > 127:
            raise ValueError(f"{context}: value must be in [0, 127]")
        return (track - 1, control, value)

    def cc_message(
        self,
        *,
        track: int,
        parameter: str,
        control: int,
        value: int,
        device_id: str,
        snapshot_slot: int,
        context: str,
    ) -> MidiMessage:
        """Return the inert mock CC message for one validated track change."""

        channel, checked_control, checked_value = self.cc_triple(
            track=track, control=control, value=value, context=context
        )
        return build_cc_message(
            channel=channel,
            control=checked_control,
            value=checked_value,
            metadata={
                "device_id": device_id,
                "track": track,
                "parameter": parameter,
                "snapshot_slot": snapshot_slot,
            },
        )


__all__ = ["MAX_MIDI_TRACK_COUNT", "ElektronTrackDomain"]
