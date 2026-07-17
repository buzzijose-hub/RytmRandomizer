"""``AnalogFourDevice`` -- Analog Four composition surface."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import ClassVar, Final, Protocol, runtime_checkable

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
from .strategies.analog_four_saved_kit_writer import (
    AnalogFourSavedKitMutation,
    AnalogFourSavedKitRenderResult,
    is_analog_four_saved_kit_mutation,
    render_analog_four_saved_kit,
)

_REPORT_HEADER: Final[str] = "RytmRandomizer Analog Four MK2 Guarded Send"
_DEVICE_ID: Final[str] = "analog_four_mk2"
_DISPLAY_NAME: Final[str] = "Elektron Analog Four MKII"
_DEFAULT_MIDI_CHANNEL: Final[int] = 0
_TRACK_COUNT: Final[int] = 4


@runtime_checkable
class AnalogFourSavedKitCapability(Protocol):
    """Optional registered-device capability for complete saved-kit frames."""

    def is_saved_kit_mutation(
        self, mutation: object
    ) -> bool: ...  # pragma: no cover - protocol stub

    def render_saved_kit(
        self,
        raw: bytes,
        mutations: Sequence[AnalogFourSavedKitMutation],
    ) -> AnalogFourSavedKitRenderResult: ...  # pragma: no cover - protocol stub


class AnalogFourDevice:
    """The Analog Four MKII surfaced as a registered ``Device``."""

    device_id: ClassVar[str] = _DEVICE_ID
    display_name: ClassVar[str] = _DISPLAY_NAME
    default_midi_channel: ClassVar[int] = _DEFAULT_MIDI_CHANNEL
    track_count: ClassVar[int] = _TRACK_COUNT
    sysex_manufacturer_id: ClassVar[bytes] = ELEKTRON_MFR_ID
    report_header: ClassVar[str] = _REPORT_HEADER

    def __init__(self) -> None:
        """Compose the three capability strategies on this device instance."""

        self.snapshot_decoder: AnalogFourSnapshotDecoder = AnalogFourSnapshotDecoder()
        self.mutation_planner: AnalogFourMutationPlanner = AnalogFourMutationPlanner()
        self.message_renderer: AnalogFourMessageRenderer = AnalogFourMessageRenderer()

    def decode_snapshot(self, raw: bytes, slot: int) -> AnalogFourKitSnapshot:
        """Delegate to the Analog Four snapshot decoder strategy."""

        return self.snapshot_decoder.decode(raw, slot=slot)

    def plan_mutation(self, snapshot: AnalogFourKitSnapshot, depth: int) -> AnalogFourMutationPlan:
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

    def is_saved_kit_mutation(self, mutation: object) -> bool:
        """Return whether ``mutation`` is accepted by the saved-kit renderer."""

        return is_analog_four_saved_kit_mutation(mutation)

    def render_saved_kit(
        self,
        raw: bytes,
        mutations: Sequence[AnalogFourSavedKitMutation],
    ) -> AnalogFourSavedKitRenderResult:
        """Render a complete A4 saved-kit frame through the registered device."""

        return render_analog_four_saved_kit(raw, mutations)


registry.register_device(AnalogFourDevice())


def _assert_protocol_conformance() -> None:
    """Sanity-check the registered instance against the structural protocol."""

    if not isinstance(registry.get_device("analog_four_mk2"), Device):
        raise AssertionError(  # noqa: S101 - structural-typing invariant
            "AnalogFourDevice does not conform to Device protocol"
        )


_assert_protocol_conformance()


def get_analog_four_saved_kit_capability() -> AnalogFourSavedKitCapability:
    """Resolve the specialized saved-kit renderer from the device registry."""

    device = registry.get_device("analog_four_mk2")
    if not isinstance(device, AnalogFourSavedKitCapability):
        raise TypeError("registered Analog Four device lacks saved-kit rendering capability")
    return device


__all__ = [
    "AnalogFourDevice",
    "AnalogFourSavedKitCapability",
    "AnalogFourSavedKitMutation",
    "AnalogFourSavedKitRenderResult",
    "get_analog_four_saved_kit_capability",
]
