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
from typing import Final

from ..mock_midi import MidiMessage
from . import registry
from .base import Device
from .strategies import (
    AnalogRytmMessageRenderer,
    AnalogRytmMutationPlanner,
    AnalogRytmSnapshotDecoder,
    RytmKitSnapshot,
    RytmMutationPlan,
)

#: Elektron's 3-byte SysEx manufacturer ID. Documented in the Analog Rytm
#: MKII MIDI spec and reused across every Elektron device. NOT secret.
_ELEKTRON_MFR_ID: Final[bytes] = bytes([0x00, 0x20, 0x3C])

#: Operator-facing report header line for guarded / hardware sends.
_REPORT_HEADER: Final[str] = "RytmRandomizer Analog Rytm MK2 Guarded Send"
_DEVICE_ID: Final[str] = "analog_rytm_mk2"
_DISPLAY_NAME: Final[str] = "Elektron Analog Rytm MKII"
_DEFAULT_MIDI_CHANNEL: Final[int] = 0
_TRACK_COUNT: Final[int] = 12


class AnalogRytmDevice:
    """The Analog Rytm MK2 surfaced as a :class:`Device`.

    The four capability strategies are constructed eagerly at instance
    creation. Each ``AnalogRytmDevice`` is effectively a singleton -- the
    module's import-time ``register_device`` call wires one instance into
    the registry.
    """

    @property
    def device_id(self) -> str:
        return _DEVICE_ID

    @property
    def display_name(self) -> str:
        return _DISPLAY_NAME

    @property
    def default_midi_channel(self) -> int:
        return _DEFAULT_MIDI_CHANNEL

    @property
    def track_count(self) -> int:
        return _TRACK_COUNT

    @property
    def sysex_manufacturer_id(self) -> bytes:
        return _ELEKTRON_MFR_ID

    @property
    def report_header(self) -> str:
        return _REPORT_HEADER

    def __init__(self) -> None:
        """Compose the three capability strategies on this device instance."""

        self.snapshot_decoder: AnalogRytmSnapshotDecoder = AnalogRytmSnapshotDecoder()
        self.mutation_planner: AnalogRytmMutationPlanner = AnalogRytmMutationPlanner()
        self.message_renderer: AnalogRytmMessageRenderer = AnalogRytmMessageRenderer()

    # ------------------------------------------------------------------
    # WS-S5 convenience methods. Each delegates to the matching strategy
    # so old callers keep working byte-identically.
    # ------------------------------------------------------------------

    def decode_snapshot(self, raw: bytes, slot: int) -> RytmKitSnapshot:
        """Delegate to :attr:`snapshot_decoder` (the WS-S6 ``decode``)."""

        return self.snapshot_decoder.decode(raw, slot=slot)

    def plan_mutation(self, snapshot: RytmKitSnapshot, depth: int) -> RytmMutationPlan:
        """Delegate to :attr:`mutation_planner` (the WS-S6 ``plan``)."""

        return self.mutation_planner.plan(snapshot, depth)

    def to_mock_messages(self, plan: RytmMutationPlan) -> list[MidiMessage]:
        """Render every event in ``plan`` into an inert ``MidiMessage``.

        Calls :meth:`AnalogRytmMessageRenderer.to_mock_message` once per
        event and returns the materialized list. The caller (test harness
        or mock sender) holds the list, so we can't lazily generate it.
        """

        if not isinstance(plan, RytmMutationPlan):
            raise TypeError(
                "AnalogRytmDevice.to_mock_messages expected RytmMutationPlan, got "
                f"{type(plan).__name__}"
            )
        return [self.message_renderer.to_mock_message(event, plan) for event in plan.events]

    def to_cc_messages(self, plan: RytmMutationPlan) -> Iterable[tuple[int, int, int]]:
        """Render every event in ``plan`` into a ``(channel, control, value)``.

        Returns a tuple (eager materialization) so callers can iterate
        twice and assert against the same sequence.
        """

        if not isinstance(plan, RytmMutationPlan):
            raise TypeError(
                "AnalogRytmDevice.to_cc_messages expected RytmMutationPlan, got "
                f"{type(plan).__name__}"
            )
        return tuple(self.message_renderer.to_cc_triple(event, plan) for event in plan.events)


# Register at import time so consumers see a non-empty registry.
registry.register_device(AnalogRytmDevice())


def _assert_protocol_conformance() -> None:
    """Compile-time-ish sanity check: ``AnalogRytmDevice`` satisfies ``Device``.

    Runs once at module import (it's cheap) so a structural mismatch is
    caught at import rather than at first ``isinstance(device, Device)``
    call from a consumer.
    """

    if not isinstance(registry.get_device("analog_rytm_mk2"), Device):
        raise AssertionError(  # noqa: S101 - structural-typing invariant
            "AnalogRytmDevice does not conform to Device protocol -- check "
            "the attribute / method surface in rytm_randomizer/devices/base.py "
            "against the strategy attributes wired in AnalogRytmDevice.__init__."
        )


_assert_protocol_conformance()
