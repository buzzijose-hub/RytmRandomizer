"""``DeviceAdapter`` Protocol — the cockpit's PASSIVE device-state projection.

The cockpit engine, history store, and WebSocket layer all consume the
device through this Protocol. One implementation lives alongside it:

* :class:`~rytm_randomizer.cockpit.device.mock.MockDeviceAdapter` — the
  always-on, in-memory device for development and tests.

Passive by construction — this is not a transport
--------------------------------------------------

**No method on this Protocol may reach hardware.** The adapter models the
cockpit's *view* of device state: what the pads currently hold, and what
they would hold after a candidate or a prepared plan is applied. Every
outbound byte goes through the ArmedApply seam
(:mod:`rytm_randomizer.senders.armed_apply`), which owns the single real
output port. Keeping the two apart is what makes "exactly one armed
output handle" checkable, and it is why the arm handler deliberately does
*not* swap in a live adapter.

Consequently :meth:`DeviceAdapter.apply` and
:meth:`DeviceAdapter.apply_send_plan` are **session-local state
projections**: they fold a mutation into the adapter's in-memory snapshot
and hand back the result. They are named "apply" because that is what
they do to the projection, not because they transmit — an implementation
that opened a port inside either would violate the Live-but-Passive rule
and the transmit whitelist in
``tests/architecture/test_armed_entry_points.py``.

There is deliberately **no** persistent-write method on this Protocol. An
earlier revision carried ``commit_kit``, whose only implementation was a
mock log line while the WS ``save`` handler acked durable success — the
adapter looked like a second transport-capable surface and promised a
persistence nothing delivered. Persistent kit/sound writes are refused
outright (see
:class:`~rytm_randomizer.senders.armed_apply.KitMutationUnsupportedError`)
until a real capture-before-write plus restore path exists.

The Protocol is ``@runtime_checkable`` so tests can confirm an adapter
satisfies it via :func:`isinstance` without inheritance. Per
``.claude/rules/architecture.md`` rule "Protocol (Duck Typing)" and the
existing :class:`~rytm_randomizer.real_midi_adapter.RealMidiOutputPort`
precedent, the shape is the contract — concrete adapters do not subclass.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..data import CockpitSendPlan, MutationCandidate, Snapshot


@runtime_checkable
class DeviceAdapter(Protocol):
    """Cockpit-facing **passive** device-state boundary.

    Implementations fold a
    :class:`~rytm_randomizer.cockpit.data.MutationCandidate` (or a
    prepared plan) into their in-memory projection of device state,
    honoring the pad-lock contract, and return a fresh
    :class:`~rytm_randomizer.cockpit.data.Snapshot` describing the result.

    No method here transmits. See the module docstring.
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
        """Fold ``candidate`` into this adapter's session-local state.

        For each :class:`~rytm_randomizer.cockpit.data.PadDelta` whose
        ``pad_id`` is **not** in ``pad_locks``, the ``proposed_params``
        replace that pad's params in the projection. Pads in
        ``pad_locks`` are skipped — the operator has explicitly held them.

        **Never transmits.** Returns the resulting state as a fresh
        :class:`~rytm_randomizer.cockpit.data.Snapshot`.
        """
        ...

    def apply_send_plan(self, send_plan: CockpitSendPlan) -> Snapshot:
        """Fold a prepared, ready ``CockpitSendPlan`` into session-local state.

        SEND uses this method once the UI/server preflight has produced a
        ready inert plan, so the cockpit's own view matches what the
        operator asked for. Implementations must reject blocked plans and
        must not recompute packet contents.

        **Never transmits.** When the session is armed, the same plan is
        additionally handed to the ArmedApply seam — that call, not this
        one, is what reaches the wire.
        """
        ...


__all__ = ["DeviceAdapter"]
