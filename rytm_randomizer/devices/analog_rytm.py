"""``AnalogRytmDevice`` -- the canonical Rytm ``Device`` (WS-S5 + Strategy).

Composes the three Strategy capabilities (``snapshot_decoder``,
``mutation_planner``, ``message_renderer``) into one ``Device`` instance
that registers with the canonical
:func:`rytm_randomizer.devices.registry.register_device` lookup at import
time.

Single-responsibility: this module is *composition only*. The decoding,
planning, and rendering bodies live in ``devices/strategies/``; the
Device class wires them together and exposes the WS-S5 convenience
methods that delegate to the strategies.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final, Protocol, runtime_checkable

from ..mock_midi import MidiMessage
from ..snapshot.mutation_scope import DEFAULT_MUTATION_SCOPE, MutationScope
from . import registry
from .base import Device
from .saved_kit_capture import SavedKitCaptureFrame
from .strategies import (
    AnalogRytmMessageRenderer,
    AnalogRytmMutationPlanner,
    AnalogRytmSnapshotDecoder,
    RytmKitSnapshot,
    RytmMutationPlan,
)
from .strategies.analog_rytm_saved_kit_codec import (
    AnalogRytmSavedKitCodecError,
    AnalogRytmSavedKitFrame,
    decode_analog_rytm_saved_kit_frame,
    encode_analog_rytm_saved_kit_frame,
)

#: Elektron's 3-byte SysEx manufacturer ID. Documented in the Analog Rytm
#: MKII MIDI spec and reused across every Elektron device. NOT secret.
_ELEKTRON_MFR_ID: Final[bytes] = bytes([0x00, 0x20, 0x3C])

#: Operator-facing report header line for guarded / hardware sends.
_REPORT_HEADER: Final[str] = "RytmRandomizer Analog Rytm MK2 Guarded Send"
_ROLE_SUMMARY: Final[str] = "12-pad drum and sample performance surface"
_DISPLAY_ORDER: Final[int] = 0
_DEVICE_ID: Final[str] = "analog_rytm_mk2"
_DISPLAY_NAME: Final[str] = "Elektron Analog Rytm MKII"
_DEFAULT_MIDI_CHANNEL: Final[int] = 0
_TRACK_COUNT: Final[int] = 12


@runtime_checkable
class AnalogRytmSavedKitCodecCapability(Protocol):
    """Specialized pure saved-KIT codec exposed through the device boundary."""

    def decode_saved_kit_frame(self, frame: bytes) -> AnalogRytmSavedKitFrame:
        """Decode one validated Analog Rytm saved-KIT SysEx frame."""

        ...

    def encode_saved_kit_frame(self, header: bytes, unpacked: bytes) -> bytes:
        """Encode one validated Analog Rytm saved-KIT SysEx frame."""

        ...


def _require_analog_rytm_mutation_plan(
    value: object,
    *,
    method_name: str,
) -> RytmMutationPlan:
    if not isinstance(value, RytmMutationPlan):
        raise TypeError(
            f"AnalogRytmDevice.{method_name} expected RytmMutationPlan, got "
            f"{type(value).__name__}"
        )
    return value


def _require_analog_rytm_kit_snapshot(value: object) -> RytmKitSnapshot:
    if not isinstance(value, RytmKitSnapshot):
        raise TypeError(
            "AnalogRytmDevice.plan_mutation expected RytmKitSnapshot, got "
            f"{type(value).__name__}"
        )
    return value


def _is_analog_rytm_device(value: object) -> bool:
    return isinstance(value, Device)


class AnalogRytmDevice:
    """The Analog Rytm MK2 surfaced as a :class:`Device`.

    The four capability strategies are constructed eagerly at instance
    creation. Each ``AnalogRytmDevice`` is effectively a singleton -- the
    module's import-time ``register_device`` call wires one instance into
    the registry.
    """

    device_id: str = _DEVICE_ID
    display_name: str = _DISPLAY_NAME
    default_midi_channel: int = _DEFAULT_MIDI_CHANNEL
    track_count: int = _TRACK_COUNT
    sysex_manufacturer_id: bytes = _ELEKTRON_MFR_ID
    report_header: str = _REPORT_HEADER
    role_summary: str = _ROLE_SUMMARY
    display_order: int = _DISPLAY_ORDER

    def __init__(self) -> None:
        """Compose the three capability strategies on this device instance."""

        self.snapshot_decoder: AnalogRytmSnapshotDecoder = AnalogRytmSnapshotDecoder()
        self.mutation_planner: AnalogRytmMutationPlanner = AnalogRytmMutationPlanner()
        self.message_renderer: AnalogRytmMessageRenderer = AnalogRytmMessageRenderer()

    def decode_saved_kit_frame(self, frame: bytes) -> AnalogRytmSavedKitFrame:
        """Delegate saved-KIT decoding to the pure Rytm codec strategy."""

        return decode_analog_rytm_saved_kit_frame(frame)

    def encode_saved_kit_frame(self, header: bytes, unpacked: bytes) -> bytes:
        """Delegate saved-KIT encoding to the pure Rytm codec strategy."""

        return encode_analog_rytm_saved_kit_frame(header, unpacked)

    def decode_saved_kit_capture(self, frame: bytes) -> SavedKitCaptureFrame:
        """Decode a complete capture frame through the canonical Rytm codec."""

        decoded = self.decode_saved_kit_frame(frame)
        return SavedKitCaptureFrame(
            payload=frame[1:-1],
            snapshot_slot=decoded.header[-1],
            header=decoded.header,
            unpacked=decoded.unpacked,
        )

    def encode_saved_kit_capture(self, decoded: object) -> bytes:
        """Re-encode a captured Rytm frame for exact stability validation."""

        if not isinstance(decoded, SavedKitCaptureFrame):
            raise TypeError("Rytm capture capability received an unsupported frame")
        return self.encode_saved_kit_frame(decoded.header, decoded.unpacked)

    # ------------------------------------------------------------------
    # WS-S5 convenience methods. Each delegates to the matching strategy
    # so old callers keep working byte-identically.
    # ------------------------------------------------------------------

    def decode_snapshot(self, raw: bytes, slot: int) -> RytmKitSnapshot:
        """Delegate to :attr:`snapshot_decoder` (the WS-S6 ``decode``)."""

        return self.snapshot_decoder.decode(raw, slot=slot)

    def plan_mutation(
        self,
        snapshot: object,
        depth: int,
        *,
        scope: MutationScope = DEFAULT_MUTATION_SCOPE,
    ) -> RytmMutationPlan:
        """Delegate to :attr:`mutation_planner` (the WS-S6 ``plan``)."""

        return self.mutation_planner.plan(
            _require_analog_rytm_kit_snapshot(snapshot),
            depth,
            scope=scope,
        )

    def to_mock_messages(self, plan: object) -> list[MidiMessage]:
        """Render every event in ``plan`` into an inert ``MidiMessage``.

        Calls :meth:`AnalogRytmMessageRenderer.to_mock_message` once per
        event and returns the materialized list. The caller (test harness
        or mock sender) holds the list, so we can't lazily generate it.
        """

        checked_plan = _require_analog_rytm_mutation_plan(
            plan,
            method_name="to_mock_messages",
        )
        return [
            self.message_renderer.to_mock_message(event, checked_plan)
            for event in checked_plan.events
        ]

    def to_cc_messages(self, plan: object) -> Iterable[tuple[int, int, int]]:
        """Render every event in ``plan`` into a ``(channel, control, value)``.

        Returns a tuple (eager materialization) so callers can iterate
        twice and assert against the same sequence.
        """

        checked_plan = _require_analog_rytm_mutation_plan(
            plan,
            method_name="to_cc_messages",
        )
        return tuple(
            self.message_renderer.to_cc_triple(event, checked_plan) for event in checked_plan.events
        )


# Register at import time so consumers see a non-empty registry.
registry.register_device(AnalogRytmDevice())


def _assert_protocol_conformance() -> None:
    """Compile-time-ish sanity check: ``AnalogRytmDevice`` satisfies ``Device``.

    Runs once at module import (it's cheap) so a structural mismatch is
    caught at import rather than at first ``isinstance(device, Device)``
    call from a consumer.
    """

    if not _is_analog_rytm_device(registry.get_device(_DEVICE_ID)):
        raise AssertionError(  # noqa: S101 - structural-typing invariant
            "AnalogRytmDevice does not conform to Device protocol -- check "
            "the attribute / method surface in rytm_randomizer/devices/base.py "
            "against the strategy attributes wired in AnalogRytmDevice.__init__."
        )


_assert_protocol_conformance()


def get_analog_rytm_saved_kit_codec_capability() -> AnalogRytmSavedKitCodecCapability:
    """Resolve the specialized saved-KIT codec from the device registry."""

    device = registry.get_device(_DEVICE_ID)
    if not isinstance(device, AnalogRytmSavedKitCodecCapability):
        raise TypeError("registered Analog Rytm device lacks saved-KIT codec capability")
    return device


__all__ = [
    "AnalogRytmDevice",
    "AnalogRytmSavedKitCodecCapability",
    "AnalogRytmSavedKitCodecError",
    "get_analog_rytm_saved_kit_codec_capability",
]
