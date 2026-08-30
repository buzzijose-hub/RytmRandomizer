"""Analog Four MKII message renderer Strategy."""

from __future__ import annotations

from ...mock_midi import MidiMessage, build_cc_message
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
        channel, control, value = self.to_cc_triple(evt, a4_plan)
        return build_cc_message(
            channel=channel,
            control=control,
            value=value,
            metadata={
                "device_id": "analog_four_mk2",
                "track": evt.track,
                "parameter": evt.parameter,
                "snapshot_slot": a4_plan.snapshot.slot,
            },
        )

    def to_cc_triple(self, event: object, plan: object) -> tuple[int, int, int]:
        """Render one event into a zero-based MIDI CC triple."""

        evt = _require_event(event)
        _require_plan(plan)
        self.track_domain.require_track(
            evt.track,
            context="AnalogFourMessageRenderer.to_cc_triple",
        )
        if evt.control < 0 or evt.control > 127:
            raise ValueError("AnalogFourMessageRenderer.to_cc_triple: control must be in [0, 127]")
        if evt.value < 0 or evt.value > 127:
            raise ValueError("AnalogFourMessageRenderer.to_cc_triple: value must be in [0, 127]")

        return (evt.track - 1, evt.control, evt.value)


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
