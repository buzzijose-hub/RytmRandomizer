"""Digitakt message renderer Strategy.

Renders plan events into inert mock messages or CC triples. Because the
Digitakt planner is zero-event while offsets are unpromoted, the renderer
has no live caller on the mutation path today -- it is exercised directly
by its tests. It exists now so the ``Device`` surface is complete and so
promotion does not need to invent the rendering contract later.
"""

from __future__ import annotations

from typing import TypeVar

from ...mock_midi import MidiMessage
from .digitakt_mutation_planner import DigitaktMutationPlan, DigitaktPlanEvent
from .digitakt_track_domain import DigitaktTrackDomain

_T = TypeVar("_T")


def _narrowed(value: object, expected: type[_T], *, context: str) -> _T:
    """Return ``value`` when it is an ``expected`` instance, else fail closed.

    One generic narrowing helper replaces the per-type ``_require_event`` /
    ``_require_plan`` pair the older renderers each hand-rolled (Gate 17 --
    abstraction reuse). Those two survive in the A4 / Rytm renderers only as
    grandfathered duplicates; new device families use this instead.
    """

    if not isinstance(value, expected):
        raise TypeError(f"{context} expected {expected.__name__}, got {type(value).__name__}")
    return value


class DigitaktMessageRenderer:
    """Render Digitakt plan events into mock messages or CC triples."""

    def __init__(self, *, track_domain: DigitaktTrackDomain, device_id: str) -> None:
        self.track_domain = track_domain
        self.device_id = device_id

    def to_mock_message(self, event: object, plan: object) -> MidiMessage:
        """Render one event into an inert mock MIDI message."""

        evt = _narrowed(event, DigitaktPlanEvent, context="DigitaktMessageRenderer")
        dt_plan = _narrowed(plan, DigitaktMutationPlan, context="DigitaktMessageRenderer")
        return self.track_domain.cc_message(
            track=evt.track,
            parameter=evt.parameter,
            control=evt.control,
            value=evt.value,
            device_id=self.device_id,
            snapshot_slot=dt_plan.snapshot.slot,
            context="DigitaktMessageRenderer.to_cc_triple",
        )

    def to_cc_triple(self, event: object, plan: object) -> tuple[int, int, int]:
        """Render one event into a zero-based MIDI CC triple."""

        evt = _narrowed(event, DigitaktPlanEvent, context="DigitaktMessageRenderer")
        _narrowed(plan, DigitaktMutationPlan, context="DigitaktMessageRenderer")
        return self.track_domain.cc_triple(
            track=evt.track,
            control=evt.control,
            value=evt.value,
            context="DigitaktMessageRenderer.to_cc_triple",
        )


__all__ = ["DigitaktMessageRenderer"]
