"""``AnalogFourDevice`` -- Analog Four composition surface."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sequence
from typing import Final, Protocol, runtime_checkable

from ..mock_midi import MidiMessage
from ..snapshot.envelope import ELEKTRON_MFR_ID
from ..snapshot.mutation_scope import DEFAULT_MUTATION_SCOPE, MutationScope
from . import registry
from .base import Device
from .saved_kit_capture import SavedKitCaptureFrame
from .strategies import (
    AnalogFourKitSnapshot,
    AnalogFourMessageRenderer,
    AnalogFourMutationPlan,
    AnalogFourMutationPlanner,
    AnalogFourSnapshotDecoder,
)
from .strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)
from .strategies.analog_four_saved_kit_writer import (
    AnalogFourSavedKitMutation,
    AnalogFourSavedKitRenderResult,
    render_analog_four_saved_kit,
)
from .strategies.analog_four_track_domain import AnalogFourTrackDomain

_REPORT_HEADER: Final[str] = "RytmRandomizer Analog Four MK2 Guarded Send"
_DEVICE_ID: Final[str] = "analog_four_mk2"
_DISPLAY_NAME: Final[str] = "Elektron Analog Four MKII"
_DEFAULT_MIDI_CHANNEL: Final[int] = 0
_TRACK_COUNT: Final[int] = 4


def _require_analog_four_mutation_plan(
    value: object,
    *,
    method_name: str,
) -> AnalogFourMutationPlan:
    if not isinstance(value, AnalogFourMutationPlan):
        raise TypeError(
            f"AnalogFourDevice.{method_name} expected AnalogFourMutationPlan, got "
            f"{type(value).__name__}"
        )
    return value


def _require_analog_four_kit_snapshot(value: object) -> AnalogFourKitSnapshot:
    if not isinstance(value, AnalogFourKitSnapshot):
        raise TypeError(
            "AnalogFourDevice.plan_mutation expected AnalogFourKitSnapshot, got "
            f"{type(value).__name__}"
        )
    return value


def _is_analog_four_device(value: object) -> bool:
    return isinstance(value, Device)


@runtime_checkable
class AnalogFourSavedKitCapability(Protocol):
    """Optional registered-device capability for complete saved-kit frames."""

    @abstractmethod
    def render_saved_kit(
        self,
        raw: bytes,
        mutations: Sequence[AnalogFourSavedKitMutation],
    ) -> AnalogFourSavedKitRenderResult: ...


class AnalogFourDevice:
    """The Analog Four MKII surfaced as a registered ``Device``."""

    device_id: str = _DEVICE_ID
    display_name: str = _DISPLAY_NAME
    default_midi_channel: int = _DEFAULT_MIDI_CHANNEL
    track_count: int = _TRACK_COUNT
    sysex_manufacturer_id: bytes = ELEKTRON_MFR_ID
    report_header: str = _REPORT_HEADER

    def __init__(self) -> None:
        """Compose the three capability strategies on this device instance."""

        track_domain = AnalogFourTrackDomain(self.track_count)
        self.snapshot_decoder: AnalogFourSnapshotDecoder = AnalogFourSnapshotDecoder()
        self.mutation_planner: AnalogFourMutationPlanner = AnalogFourMutationPlanner(
            track_domain=track_domain
        )
        self.message_renderer: AnalogFourMessageRenderer = AnalogFourMessageRenderer(
            track_domain=track_domain
        )

    def decode_snapshot(self, raw: bytes, slot: int) -> AnalogFourKitSnapshot:
        """Delegate to the Analog Four snapshot decoder strategy."""

        return self.snapshot_decoder.decode(raw, slot=slot)

    def plan_mutation(
        self,
        snapshot: object,
        depth: int,
        *,
        scope: MutationScope = DEFAULT_MUTATION_SCOPE,
    ) -> AnalogFourMutationPlan:
        """Delegate to the Analog Four mutation planner strategy."""

        return self.mutation_planner.plan(
            _require_analog_four_kit_snapshot(snapshot),
            depth,
            scope=scope,
        )

    def to_mock_messages(self, plan: object) -> list[MidiMessage]:
        """Render ready plan events into inert mock MIDI messages."""

        checked_plan = _require_analog_four_mutation_plan(
            plan,
            method_name="to_mock_messages",
        )
        if not checked_plan.ready:
            return []
        return [
            self.message_renderer.to_mock_message(event, checked_plan)
            for event in checked_plan.events
        ]

    def to_cc_messages(self, plan: object) -> Iterable[tuple[int, int, int]]:
        """Render ready plan events into ``(channel, control, value)`` triples."""

        checked_plan = _require_analog_four_mutation_plan(
            plan,
            method_name="to_cc_messages",
        )
        if not checked_plan.ready:
            return ()
        return tuple(
            self.message_renderer.to_cc_triple(event, checked_plan) for event in checked_plan.events
        )

    def render_saved_kit(
        self,
        raw: bytes,
        mutations: Sequence[AnalogFourSavedKitMutation],
    ) -> AnalogFourSavedKitRenderResult:
        """Render a complete A4 saved-kit frame through the registered device."""

        return render_analog_four_saved_kit(raw, mutations)

    def decode_saved_kit_capture(self, frame: bytes) -> SavedKitCaptureFrame:
        """Decode a complete capture frame through the canonical A4 codec."""

        if len(frame) < 2 or frame[0] != 0xF0 or frame[-1] != 0xF7:
            raise ValueError("Analog Four saved-kit SysEx framing is invalid")
        decoded = decode_analog_four_saved_kit_payload(frame[1:-1], require_trailer=True)
        return SavedKitCaptureFrame(
            payload=frame[1:-1],
            snapshot_slot=0,
            header=decoded.prefix,
            unpacked=decoded.unpacked,
        )

    def encode_saved_kit_capture(self, decoded: object) -> bytes:
        """Re-encode a captured A4 frame for exact stability validation."""

        if not isinstance(decoded, SavedKitCaptureFrame):
            raise TypeError("A4 capture capability received an unsupported frame")
        encoded = encode_analog_four_saved_kit_payload(decoded.header, decoded.unpacked)
        return bytes((0xF0,)) + encoded.payload + bytes((0xF7,))


registry.register_device(AnalogFourDevice())


def _assert_protocol_conformance() -> None:
    """Sanity-check the registered instance against the structural protocol."""

    if not _is_analog_four_device(registry.get_device("analog_four_mk2")):
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
