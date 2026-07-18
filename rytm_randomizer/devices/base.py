"""``Device`` Protocol -- the cross-machine boundary (WS-S5 + Strategy capabilities).

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
  (for ``--arm``),
* four **capability strategies** (Strategy pattern): a ``SnapshotDecoder``,
  a ``RuntimePlanBuilder``, a ``MessageRenderer``, and a per-device
  ``report_header`` string. These are the single seam through which the
  generic guarded / hardware senders consume device-specific behavior.

The capability strategies are what make the ``dual_machine/`` orchestrator
collapse from "import each device family directly" to "fan out over
``devices.all_devices()``". Adding a new family (Syntakt, Digitone, ...)
becomes "implement four strategies + register" -- no edits to senders or
orchestrators.

Per Gate 6 (PLAN_REQUIREMENTS) the surface is a ``@runtime_checkable``
``Protocol`` (not an ABC) so structural typing admits hand-rolled and
generated device wrappers without inheritance.

Per Gate 7 the surface is intentionally narrow: snapshot decode +
mutation planning + message rendering. The actual MIDI write (real or
mock) is the caller's responsibility via the existing ``MidiSender``
protocol in ``rytm_randomizer.midi_io``. Devices do not own the MIDI
boundary; they describe a translation.

PR #21 forward-compat: codex's planned Analog Four engine collapses from
8 hand-rolled top-level files into one module that registers a single
``AnalogFourDevice`` instance against this protocol. The hand-rolled
``analog_four_snapshot_decoder.py`` / ``_mutation_planner.py`` /
``_mock_runtime.py`` triple becomes the body of ``AnalogFourDevice``'s
``snapshot_decoder``, ``runtime_plan_builder``, and ``message_renderer``
strategies; the eight per-device ``*_sender.py`` modules collapse into the
two generic senders (``senders/guarded.py``, ``senders/hardware.py``)
that consume those strategies.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar, Protocol, runtime_checkable

# Capability sub-protocols (Strategy pattern). We REUSE the WS-S6 Protocols
# at ``rytm_randomizer.snapshot.{decoder,planner}`` instead of redefining
# them here -- a single Protocol per concept is the whole point. Re-export
# them under the ``devices`` namespace so consumers can import everything
# they need from one place (``from rytm_randomizer.devices import Device,
# SnapshotDecoder, MutationPlanner, MessageRenderer``).
from ..snapshot.decoder import SnapshotDecoder
from ..snapshot.planner import MutationPlanner


class MidiOutbox(Protocol):
    """Anything that records or sends MIDI for a Device's rendered plan.

    Satisfied by ``rytm_randomizer.mock_midi.MockMidiSender`` (test path)
    and the real-MIDI path (production). Devices write here without
    knowing which one they are talking to.
    """

    def send(self, message: object) -> None: ...


@runtime_checkable
class MessageRenderer(Protocol):
    """Render one plan event into one MIDI message (mock or real-CC).

    The third leg of the Strategy stack alongside
    :class:`~rytm_randomizer.snapshot.decoder.SnapshotDecoder` and
    :class:`~rytm_randomizer.snapshot.planner.MutationPlanner`.

    The two methods stay separate (instead of an ``armed`` boolean) so the
    type system distinguishes the two output shapes and the test harness
    can verify each independently.

    Renderers are pure: same ``(event, plan)`` in -> same message out.
    Renderers do NOT call ``send()`` -- they construct the message; the
    sender owns the dispatch.
    """

    def to_mock_message(self, event: Any, plan: Any) -> Any: ...

    def to_cc_triple(self, event: Any, plan: Any) -> tuple[int, int, int]: ...


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
    * ``snapshot_decoder`` -- the device's ``SnapshotDecoder`` strategy
      (the WS-S6 Protocol re-exported from
      :mod:`rytm_randomizer.snapshot.decoder`).
    * ``mutation_planner`` -- the device's ``MutationPlanner`` strategy
      (the WS-S6 Protocol re-exported from
      :mod:`rytm_randomizer.snapshot.planner`).
    * ``message_renderer`` -- the device's ``MessageRenderer`` strategy.
    * ``report_header`` -- the operator-facing header line for guarded
      and hardware send reports (e.g.
      ``"RytmRandomizer passive Snapshot Essence Guarded Send"``).

    Method contract (convenience wrappers that delegate to the strategies;
    they remain on the Protocol so the WS-S5 surface is byte-stable for
    callers that already use it):

    * ``decode_snapshot(raw, slot)`` -- equivalent to
      ``snapshot_decoder.decode(raw, slot)``.
    * ``plan_mutation(snapshot, depth)`` -- equivalent to
      ``mutation_planner.plan(snapshot, depth)``.
    * ``to_mock_messages(plan)`` -- render every event in ``plan`` via
      ``message_renderer.to_mock_message``.
    * ``to_cc_messages(plan)`` -- render every event in ``plan`` via
      ``message_renderer.to_cc_triple``.

    New code SHOULD prefer the strategy attributes (they expose the
    individual capabilities directly; the generic senders consume them).
    The convenience methods are kept so WS-S5 callers do not break.
    """

    device_id: ClassVar[str]
    display_name: ClassVar[str]
    default_midi_channel: ClassVar[int]
    track_count: ClassVar[int]
    sysex_manufacturer_id: ClassVar[bytes]

    @property
    def snapshot_decoder(self) -> SnapshotDecoder: ...  # pragma: no cover - protocol stub

    @property
    def mutation_planner(self) -> MutationPlanner: ...  # pragma: no cover - protocol stub

    @property
    def message_renderer(self) -> MessageRenderer: ...  # pragma: no cover - protocol stub

    report_header: ClassVar[str]

    def decode_snapshot(self, raw: bytes, slot: int) -> Any: ...

    def plan_mutation(self, snapshot: Any, depth: int) -> Any: ...

    def to_mock_messages(self, plan: Any) -> list[Any]: ...

    def to_cc_messages(self, plan: Any) -> Iterable[tuple[int, int, int]]: ...
