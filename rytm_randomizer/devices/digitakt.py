"""``DigitaktDevice`` -- Digitakt composition surface.

Two Digitakt generations register from this one module:

* ``digitakt_mk1`` -- Elektron Digitakt, 8 audio tracks.
* ``digitakt_ii`` -- Elektron Digitakt II, 16 audio tracks.

They share one device class and one strategy set, parameterized by track
count and SysEx family byte. Per
``.claude/rules/device-protocol-strategy.md`` this is one
``devices/<family>.py`` plus strategy modules under
``devices/strategies/`` -- never a sibling subpackage at the package root.

**Send authority: none.** Both devices decode snapshots but plan
zero-event, not-ready mutations, because Digitakt saved-project offsets
have never been validated against hardware. See
:mod:`rytm_randomizer.devices.strategies.digitakt_mutation_planner`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from ..mock_midi import MidiMessage
from ..snapshot.envelope import ELEKTRON_MFR_ID
from ..snapshot.mutation_scope import DEFAULT_MUTATION_SCOPE, MutationScope
from . import registry
from .base import Device
from .strategies.digitakt_message_renderer import DigitaktMessageRenderer
from .strategies.digitakt_mutation_planner import (
    DigitaktMutationPlan,
    DigitaktMutationPlanner,
)
from .strategies.digitakt_snapshot_decoder import (
    DigitaktKitSnapshot,
    DigitaktSnapshotDecoder,
)
from .strategies.digitakt_track_domain import (
    DIGITAKT_II_FAMILY,
    DIGITAKT_II_TRACK_COUNT,
    DIGITAKT_MK1_FAMILY,
    DIGITAKT_MK1_TRACK_COUNT,
    DigitaktTrackDomain,
)

_MK1_DEVICE_ID: Final[str] = "digitakt_mk1"
_MK1_DISPLAY_NAME: Final[str] = "Elektron Digitakt"
_MK1_REPORT_HEADER: Final[str] = "RytmRandomizer Digitakt Guarded Send"
_MK1_ROLE_SUMMARY: Final[str] = "8-track drum and sample performance surface"
_MK1_DISPLAY_ORDER: Final[int] = 2

_II_DEVICE_ID: Final[str] = "digitakt_ii"
_II_DISPLAY_NAME: Final[str] = "Elektron Digitakt II"
_II_REPORT_HEADER: Final[str] = "RytmRandomizer Digitakt II Guarded Send"
_II_ROLE_SUMMARY: Final[str] = "16-track drum and sample performance surface"
_II_DISPLAY_ORDER: Final[int] = 3

_DEFAULT_MIDI_CHANNEL: Final[int] = 0


def _require_digitakt_mutation_plan(
    value: object,
    *,
    method_name: str,
) -> DigitaktMutationPlan:
    if not isinstance(value, DigitaktMutationPlan):
        raise TypeError(
            f"DigitaktDevice.{method_name} expected DigitaktMutationPlan, got "
            f"{type(value).__name__}"
        )
    return value


def _is_digitakt_device(value: object) -> bool:
    """Structural check kept behind an ``object`` parameter.

    Taking ``object`` (rather than the concrete class) is deliberate: it
    stops the type checker from statically narrowing the argument and
    reporting the runtime conformance assertion as unnecessary. Mirrors
    ``_is_analog_four_device`` in ``devices/analog_four.py``.
    """

    return isinstance(value, Device)


def _require_digitakt_kit_snapshot(value: object) -> DigitaktKitSnapshot:
    if not isinstance(value, DigitaktKitSnapshot):
        raise TypeError(
            f"DigitaktDevice.plan_mutation expected DigitaktKitSnapshot, got "
            f"{type(value).__name__}"
        )
    return value


class DigitaktDevice:
    """A Digitakt generation surfaced as a registered ``Device``."""

    sysex_manufacturer_id: bytes = ELEKTRON_MFR_ID
    default_midi_channel: int = _DEFAULT_MIDI_CHANNEL

    def __init__(
        self,
        *,
        device_id: str,
        display_name: str,
        report_header: str,
        role_summary: str,
        display_order: int,
        track_count: int,
        family_byte: int,
    ) -> None:
        """Compose the three capability strategies for one generation."""

        self.device_id = device_id
        self.display_name = display_name
        self.report_header = report_header
        self.role_summary = role_summary
        self.display_order = display_order
        self.track_count = track_count
        self.family_byte = family_byte

        track_domain = DigitaktTrackDomain(track_count)
        self.snapshot_decoder: DigitaktSnapshotDecoder = DigitaktSnapshotDecoder(
            family_byte=family_byte,
            device_id=device_id,
        )
        self.mutation_planner: DigitaktMutationPlanner = DigitaktMutationPlanner(
            track_domain=track_domain,
            device_id=device_id,
        )
        self.message_renderer: DigitaktMessageRenderer = DigitaktMessageRenderer(
            track_domain=track_domain,
            device_id=device_id,
        )

    def decode_snapshot(self, raw: bytes, slot: int) -> DigitaktKitSnapshot:
        """Delegate to the Digitakt snapshot decoder strategy."""

        return self.snapshot_decoder.decode(raw, slot=slot)

    def plan_mutation(
        self,
        snapshot: object,
        depth: int,
        *,
        scope: MutationScope = DEFAULT_MUTATION_SCOPE,
    ) -> DigitaktMutationPlan:
        """Delegate to the Digitakt mutation planner strategy."""

        return self.mutation_planner.plan(
            _require_digitakt_kit_snapshot(snapshot),
            depth,
            scope=scope,
        )

    def to_mock_messages(self, plan: object) -> list[MidiMessage]:
        """Render ready plan events into inert mock MIDI messages."""

        checked_plan = _require_digitakt_mutation_plan(plan, method_name="to_mock_messages")
        if not checked_plan.ready:
            return []
        return [
            self.message_renderer.to_mock_message(event, checked_plan)
            for event in checked_plan.events
        ]

    def to_cc_messages(self, plan: object) -> Iterable[tuple[int, int, int]]:
        """Render ready plan events into ``(channel, control, value)`` triples."""

        checked_plan = _require_digitakt_mutation_plan(plan, method_name="to_cc_messages")
        if not checked_plan.ready:
            return ()
        return tuple(
            self.message_renderer.to_cc_triple(event, checked_plan) for event in checked_plan.events
        )


def build_digitakt_mk1_device() -> DigitaktDevice:
    """Construct the Digitakt (MK1) device instance."""

    return DigitaktDevice(
        device_id=_MK1_DEVICE_ID,
        display_name=_MK1_DISPLAY_NAME,
        report_header=_MK1_REPORT_HEADER,
        role_summary=_MK1_ROLE_SUMMARY,
        display_order=_MK1_DISPLAY_ORDER,
        track_count=DIGITAKT_MK1_TRACK_COUNT,
        family_byte=DIGITAKT_MK1_FAMILY,
    )


def build_digitakt_ii_device() -> DigitaktDevice:
    """Construct the Digitakt II device instance."""

    return DigitaktDevice(
        device_id=_II_DEVICE_ID,
        display_name=_II_DISPLAY_NAME,
        report_header=_II_REPORT_HEADER,
        role_summary=_II_ROLE_SUMMARY,
        display_order=_II_DISPLAY_ORDER,
        track_count=DIGITAKT_II_TRACK_COUNT,
        family_byte=DIGITAKT_II_FAMILY,
    )


registry.register_device(build_digitakt_mk1_device())
registry.register_device(build_digitakt_ii_device())


def _assert_registered_digitakt_generations_conform() -> None:
    """Sanity-check both registered instances against the structural protocol."""

    registered = registry.all_devices()
    for device_id in (_MK1_DEVICE_ID, _II_DEVICE_ID):
        # Look the id up rather than calling ``registry.get_device``: a missing
        # registration must surface as a named, diagnosable failure here, not
        # as a bare ``KeyError`` raised while importing ``devices/__init__``.
        # An import-time KeyError cascades into hundreds of unrelated-looking
        # collection errors (including a misleading "already registered" from
        # the retry), burying the real signal.
        device = registered.get(device_id)
        if device is None:
            raise AssertionError(  # pragma: no cover - registration invariant
                f"{device_id} is not registered; devices/digitakt.py must call "
                "register_device() for every generation it declares"
            )
        if not _is_digitakt_device(device):
            # Structural-typing invariant; see docs/ARCHITECTURE.md §8 (parity
            # API surface). Unreachable unless the Device Protocol changes.
            raise AssertionError(  # pragma: no cover - structural-typing invariant
                f"{device_id} does not conform to Device protocol"
            )


_assert_registered_digitakt_generations_conform()


__all__ = [
    "DigitaktDevice",
    "build_digitakt_ii_device",
    "build_digitakt_mk1_device",
]
