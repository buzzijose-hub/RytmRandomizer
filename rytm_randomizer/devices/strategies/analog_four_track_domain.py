"""Shared Analog Four track domain for planning and rendering.

The validation logic is device-neutral and lives once in
:mod:`rytm_randomizer.devices.strategies.elektron_track_domain`. This module
keeps the family-named alias so A4 call sites, type annotations, and error
context keep naming the machine they are about.

``MAX_MIDI_TRACK_COUNT`` is re-exported for backward compatibility: it was
originally defined here, but it is the 16-channel MIDI protocol ceiling, not
an Analog Four fact, so its canonical home is the neutral module.
"""

from __future__ import annotations

from .elektron_track_domain import MAX_MIDI_TRACK_COUNT, ElektronTrackDomain

#: Analog Four track domain. A thin alias of the shared implementation --
#: not a second copy of the validation rules.
AnalogFourTrackDomain = ElektronTrackDomain

__all__ = ["AnalogFourTrackDomain", "MAX_MIDI_TRACK_COUNT"]
