"""``AnalogFourDevice`` -- Analog Four composition surface."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from ..mock_midi import MidiMessage
from ..snapshot.envelope import ELEKTRON_MFR_ID
from . import registry
from .base import Device
from .strategies import (
    AnalogFourKitSnapshot,
    AnalogFourMessageRenderer,
    AnalogFourMutationPlan,
    AnalogFourMutationPlanner,
    AnalogFourSnapshotDecoder,
)

_REPORT_HEADER: Final[str] = "RytmRandomizer Analog Four MK2 Guarded Send"


class AnalogFourDevice:
    """The Analog Four MKII surfaced as a registered ``Device``."""

    device_id: Final[str] = "analog_four_mk2"
    display_name: Final[str] = "Elektron Analog Four MKII"
    default_midi_channel: Final[int] = 0
    track_count: Final[int] = 4
    sysex_manufacturer_id: Final[bytes] = ELEKTRON_MFR_ID
    report_header: Final[str] = _REPORT_HEADER

    def __init__(self) -> None:
        """Compose the three capability strategies on this device instance."""

        self.snapshot_decoder: AnalogFourSnapshotDecoder = AnalogFourSnapshotDecoder()
        self.mutation_planner: AnalogFourMutationPlanner = AnalogFourMutationPlanner()
        self.message_renderer: AnalogFourMessageRenderer = AnalogFourMessageRenderer()

    def decode_snapshot(self, raw: bytes, slot: int) -> AnalogFourKitSnapshot:
        """Delegate to the Analog Four snapshot decoder strategy."""

        return self.snapshot_decoder.decode(raw, slot=slot)

    def plan_mutation(
        self, snapshot: AnalogFourKitSnapshot, depth: int
    ) -> AnalogFourMutationPlan:
        """Delegate to the Analog Four mutation planner strategy."""

        return self.mutation_planner.plan(snapshot, depth)

    def to_mock_messages(self, plan: AnalogFourMutationPlan) -> list[MidiMessage]:
        """Render ready plan events into inert mock MIDI messages."""

        if not isinstance(plan, AnalogFourMutationPlan):
            raise TypeError(
                "AnalogFourDevice.to_mock_messages expected AnalogFourMutationPlan, got "
                f"{type(plan).__name__}"
            )
        if not plan.ready:
            return []
        return [self.message_renderer.to_mock_message(event, plan) for event in plan.events]

    def to_cc_messages(self, plan: AnalogFourMutationPlan) -> Iterable[tuple[int, int, int]]:
        """Render ready plan events into ``(channel, control, value)`` triples."""

        if not isinstance(plan, AnalogFourMutationPlan):
            raise TypeError(
                "AnalogFourDevice.to_cc_messages expected AnalogFourMutationPlan, got "
                f"{type(plan).__name__}"
            )
        if not plan.ready:
            return ()
        return tuple(self.message_renderer.to_cc_triple(event, plan) for event in plan.events)


registry.register_device(AnalogFourDevice())


def _assert_protocol_conformance() -> None:
    """Sanity-check the registered instance against the structural protocol."""

    if not isinstance(registry.get_device("analog_four_mk2"), Device):
        raise AssertionError(  # noqa: S101 - structural-typing invariant
            "AnalogFourDevice does not conform to Device protocol"
        )


_assert_protocol_conformance()
