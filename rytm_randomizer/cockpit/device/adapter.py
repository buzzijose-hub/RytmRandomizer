"""``DeviceAdapter`` Protocol — the cockpit's only handle on hardware.

The cockpit engine, history store, and WebSocket layer all consume the
device through this Protocol. One implementation lives alongside it:

* :class:`~rytm_randomizer.cockpit.device.mock.MockDeviceAdapter` — the
  always-on, in-memory device for development and tests.

There is no real-MIDI adapter. The adapter models cockpit *state*; the
ArmedApply seam (:mod:`rytm_randomizer.senders.armed_apply`) is the only
thing that transmits, and it owns the single real output port. Keeping the
two apart is what makes "exactly one armed output handle" checkable.

The Protocol is ``@runtime_checkable`` so tests can confirm both adapters
satisfy it via :func:`isinstance` without inheritance. Per
``.claude/rules/architecture.md`` rule "Protocol (Duck Typing)" and the
existing :class:`~rytm_randomizer.real_midi_adapter.RealMidiOutputPort`
precedent, the shape is the contract — concrete adapters do not subclass.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..data import CockpitSendPlan, MutationCandidate, Snapshot


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

        ``False`` for the mock. Whether a *session* is armed is answered by
        :func:`rytm_randomizer.cockpit.ws.handlers.session_is_armed`, which
        consults the ArmedApply seam — an adapter no longer changes on arm.
        The cockpit UI uses that to label the device pill (``MOCK`` vs
        ``LIVE``) and to gate the "commit to kit" button.
        """
        ...

    def capture_snapshot(self) -> Snapshot:
        """Read the current device state and return a
        :class:`~rytm_randomizer.cockpit.data.Snapshot`.

        The mock returns its in-memory state. Real SysEx-driven readback
        from hardware is not implemented — which is exactly why the armed
        seam refuses persistent kit/sound writes (there is no
        capture-before-write to make them reversible).
        """
        ...

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
        ...

    def apply_send_plan(self, send_plan: CockpitSendPlan) -> Snapshot:
        """Apply a prepared, ready ``CockpitSendPlan`` to the device.

        SEND uses this method once the UI/server preflight has produced
        a ready inert plan. Adapters must reject blocked plans and must
        not recompute packet contents at the hardware boundary.
        """
        ...

    def commit_kit(self, snapshot: Snapshot, label: str | None) -> None:
        """Write ``snapshot`` to the device's persistent kit memory.

        Mock: no-op (the mock has no persistence). There is no hardware
        implementation: writing a kit dump to a real device is a
        kit/sound mutation, and the armed seam refuses those outright
        until a real capture-before-write plus restore path exists.
        """


__all__ = ["DeviceAdapter"]
