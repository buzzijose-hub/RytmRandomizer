"""``DeviceAdapter`` Protocol — the cockpit's only handle on hardware.

The cockpit engine, history store, and WebSocket layer all consume the
device through this Protocol. Two implementations live alongside it:

* :class:`~rytm_randomizer.cockpit.device.mock.MockDeviceAdapter` — the
  always-on, in-memory device for development and tests.
* :class:`~rytm_randomizer.cockpit.device.real.RealMidiDeviceAdapter` — the
  real-MIDI wrapper, constructed only when ``--arm`` is set.

The Protocol is ``@runtime_checkable`` so tests can confirm both adapters
satisfy it via :func:`isinstance` without inheritance. Per
``.claude/rules/architecture.md`` rule "Protocol (Duck Typing)" and the
existing :class:`~rytm_randomizer.real_midi_adapter.RealMidiOutputPort`
precedent, the shape is the contract — concrete adapters do not subclass.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..data import MutationCandidate, Snapshot


@runtime_checkable
class DeviceAdapter(Protocol):
    """Cockpit-facing device boundary.

    Implementations are responsible for translating a
    :class:`~rytm_randomizer.cockpit.data.MutationCandidate` into device
    state changes (mock memory, or real MIDI on the wire), honoring the
    pad-lock contract, and returning a fresh
    :class:`~rytm_randomizer.cockpit.data.Snapshot` that describes the
    post-apply device state.
    """

    @property
    def is_armed(self) -> bool:
        """True if this adapter actually talks to hardware.

        ``False`` for the mock; ``True`` for the real-MIDI adapter. The
        cockpit UI uses this to label the device pill (``MOCK`` vs ``LIVE``)
        and to gate the "commit to kit" button on the operator's intent.
        """

    def capture_snapshot(self) -> Snapshot:
        """Read the current device state and return a
        :class:`~rytm_randomizer.cockpit.data.Snapshot`.

        The mock returns its in-memory state; the real adapter (Phase 1)
        returns a placeholder because round-tripping a Rytm SysEx dump
        lands in Phase 1.x.
        """

    def apply(
        self,
        candidate: MutationCandidate,
        pad_locks: frozenset[int],
    ) -> Snapshot:
        """Apply ``candidate`` to the device.

        For each :class:`~rytm_randomizer.cockpit.data.PadDelta` whose
        ``pad_id`` is **not** in ``pad_locks``, send the
        ``proposed_params`` changes to the device. Pads in ``pad_locks``
        are skipped — the operator has explicitly held them.

        Returns the new device state as a fresh
        :class:`~rytm_randomizer.cockpit.data.Snapshot` (read back after
        apply).
        """

    def commit_kit(self, snapshot: Snapshot, label: str | None) -> None:
        """Write ``snapshot`` to the device's persistent kit memory.

        Real adapter: emits a Rytm kit-dump SysEx. Mock: no-op (mock has
        no persistence). Phase 1 leaves the real path as
        ``NotImplementedError`` — kit-dump SysEx writing lands in Phase 1.x.
        """


__all__ = ["DeviceAdapter"]
