"""``Device`` Protocol -- the cross-machine boundary (WS-S5).

The ``Device`` protocol describes what every Elektron device an operator can
target through RytmRandomizer must provide:

* a stable string identifier (``"analog_rytm_mk2"``, ``"analog_four_mk2"``,
  ``"digitakt_mk2"``, ...),
* a human-readable display name,
* the default MIDI channel the operator picks if they don't override,
* the track / pad count (4 for Analog Four, 12 for the full Rytm pad grid,
  etc.),
* the manufacturer-id bytes the device's SysEx envelope opens with,
* a contract for decoding a snapshot from a SysEx kit dump, planning a
  mutation against that snapshot, and rendering the plan into either mock
  ``MidiMessage`` instances (for ``--dry-run``) or real CC byte streams
  (for ``--arm``).

Per Gate 6 (PLAN_REQUIREMENTS) the surface is a ``@runtime_checkable``
``Protocol`` (not an ABC) so structural typing admits hand-rolled and
generated device wrappers without inheritance.

Per Gate 7 the surface is intentionally narrow: snapshot decode +
mutation planning + message rendering. The actual MIDI write (real or
mock) is the caller's responsibility via the existing ``MidiSender``
protocol in ``rytm_randomizer.midi_io``. Devices do not own the MIDI
boundary; they describe a translation.

PR #21 forward-compat: codex's planned Analog Four engine collapses from
the hand-rolled ``analog_four`` helper package into one module that registers
a single ``AnalogFourDevice`` instance against this protocol. The
``analog_four.snapshot_decoder`` / ``snapshot_mutation_planner`` /
``snapshot_mock_runtime`` triple becomes the body of ``AnalogFourDevice``'s
``decode_snapshot`` / ``plan_mutation`` / ``to_mock_messages`` methods.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol, runtime_checkable


class MidiOutbox(Protocol):
    """Anything that records or sends MIDI for a Device's rendered plan.

    Satisfied by ``rytm_randomizer.mock_midi.MockMidiSender`` (test path)
    and the real-MIDI path (production). Devices write here without
    knowing which one they are talking to.
    """

    def send(self, message: object) -> None: ...


@runtime_checkable
class Device(Protocol):
    """Cross-machine boundary for an Elektron device family.

    Implementations are expected to be effectively singletons -- one
    ``Device`` instance per machine family registered with
    :func:`rytm_randomizer.devices.registry.register_device`.

    Attribute contract:

    * ``device_id`` -- stable, lowercase, snake_case identifier
      (``"analog_rytm_mk2"``). Used as the registry key.
    * ``display_name`` -- human-readable label
      (``"Elektron Analog Rytm MKII"``). Used in operator UI.
    * ``default_midi_channel`` -- 0-based MIDI channel the device listens
      on out of the factory (or the project's convention).
    * ``track_count`` -- number of independently-targetable tracks /
      pads. 4 for Analog Four; 12 for the Rytm MKII pad grid.
    * ``sysex_manufacturer_id`` -- the 3-byte Elektron manufacturer ID
      sequence (``b"\\x00\\x20\\x3c"``).

    Method contract:

    * ``decode_snapshot(raw, slot)`` -- parse a SysEx kit/pattern dump.
      Returns a device-specific dataclass; callers treat it opaque.
    * ``plan_mutation(snapshot, depth)`` -- produce a mutation plan from
      the snapshot at the given depth. Returns a device-specific plan.
    * ``to_mock_messages(plan)`` -- render a plan into a list of inert
      :class:`~rytm_randomizer.mock_midi.MidiMessage` instances.
    * ``to_cc_messages(plan)`` -- render a plan into an iterable of
      ``(channel, control, value)`` triples for a real port to forward.

    The two render methods are kept separate (instead of returning a
    single sequence routed by an ``armed`` boolean) so the type system can
    distinguish the two output shapes and the test harness can verify each
    independently.
    """

    device_id: str
    display_name: str
    default_midi_channel: int
    track_count: int
    sysex_manufacturer_id: bytes

    def decode_snapshot(self, raw: bytes, slot: int) -> Any: ...

    def plan_mutation(self, snapshot: Any, depth: int) -> Any: ...

    def to_mock_messages(self, plan: Any) -> list[Any]: ...

    def to_cc_messages(self, plan: Any) -> Iterable[tuple[int, int, int]]: ...
