"""Analog Four MKII message renderer Strategy."""

from __future__ import annotations

from ...mock_midi import MidiMessage
from .analog_four_mutation_planner import AnalogFourMutationPlan, AnalogFourPlanEvent
from .analog_four_track_domain import AnalogFourTrackDomain


class AnalogFourMessageRenderer:
    """Render Analog Four plan events into mock messages or CC triples."""

    def __init__(self, *, track_domain: AnalogFourTrackDomain) -> None:
        self.track_domain = track_domain

    def to_mock_message(self, event: object, plan: object) -> MidiMessage:
        """Render one event into an inert mock MIDI message."""

        evt = _require_event(event)
        a4_plan = _require_plan(plan)
        return self.track_domain.cc_message(
            track=evt.track,
            parameter=evt.parameter,
            control=evt.control,
            value=evt.value,
            device_id="analog_four_mk2",
            snapshot_slot=a4_plan.snapshot.slot,
            context="AnalogFourMessageRenderer.to_cc_triple",
        )

    def to_cc_triple(self, event: object, plan: object) -> tuple[int, int, int]:
        """Render one event into a zero-based MIDI CC triple."""

        evt = _require_event(event)
        _require_plan(plan)
        return self.track_domain.cc_triple(
            track=evt.track,
            control=evt.control,
            value=evt.value,
            context="AnalogFourMessageRenderer.to_cc_triple",
        )


def _require_event(event: object) -> AnalogFourPlanEvent:
    """Narrow ``event`` to an Analog Four plan event."""

    if not isinstance(event, AnalogFourPlanEvent):
        raise TypeError(
            "AnalogFourMessageRenderer expected AnalogFourPlanEvent, " f"got {type(event).__name__}"
        )
    return event


def _require_plan(plan: object) -> AnalogFourMutationPlan:
    """Narrow ``plan`` to an Analog Four mutation plan."""

    if not isinstance(plan, AnalogFourMutationPlan):
        raise TypeError(
            "AnalogFourMessageRenderer expected AnalogFourMutationPlan, "
            f"got {type(plan).__name__}"
        )
    return plan
