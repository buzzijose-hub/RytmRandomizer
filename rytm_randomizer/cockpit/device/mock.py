"""``MockDeviceAdapter`` — in-memory, mock-safe device adapter.

Default adapter for cockpit development and tests. Holds a single
:class:`~rytm_randomizer.cockpit.data.Snapshot` in memory and applies
mutation candidates by replacing each non-locked pad's params with the
candidate's ``proposed_params``. Locked pads keep their current params
unchanged.

``is_armed`` is always ``False`` — this adapter never talks to hardware.

There is no ``commit_kit``: the Protocol dropped its persistent-write
method because no implementation could deliver one (see
:mod:`rytm_randomizer.cockpit.device.adapter`). The mock's version was a
log line the WS ``save`` handler nonetheless acked as durable success.
"""

from __future__ import annotations

from ..data import CockpitSendPlan, MutationCandidate, PadState, Snapshot, new_ulid


class MockDeviceAdapter:
    """In-memory device adapter; never opens a MIDI port.

    Satisfies the :class:`~rytm_randomizer.cockpit.device.adapter.DeviceAdapter`
    Protocol via duck typing — not by inheritance.

    Constructor takes the initial snapshot that the mock starts in. Every
    :meth:`apply` produces a fresh snapshot (frozen dataclass) and stores
    it as the new ``_state``; subsequent :meth:`capture_snapshot` calls
    return that updated state.
    """

    def __init__(self, initial: object) -> None:
        """Seed the projection; refuse anything that is not a Snapshot.

        ``initial`` is typed ``object`` on purpose: the bootstrap snapshot
        reaches this constructor from ``__main__`` and from test
        harnesses, so the ``isinstance`` check below is genuine runtime
        validation rather than redundant narrowing of an already-``Snapshot``
        parameter. (Same reasoning as
        :class:`rytm_randomizer.senders.armed_apply.ArmedApplySession`'s
        ``port_name`` / ``arm_token``.)
        """

        if not isinstance(initial, Snapshot):
            raise TypeError(f"initial must be a Snapshot; got {type(initial).__name__}")
        self._state: Snapshot = initial

    @property
    def is_armed(self) -> bool:
        """Always ``False`` — mock adapter never talks to hardware."""

        return False

    def capture_snapshot(self) -> Snapshot:
        """Return the mock's current in-memory snapshot."""

        return self._state

    def adopt_snapshot(self, snapshot: object) -> None:
        """Replace mock state with a verified capture anchor, without I/O."""

        if not isinstance(snapshot, Snapshot):
            raise TypeError(f"snapshot must be a Snapshot; got {type(snapshot).__name__}")
        self._state = snapshot

    def apply(
        self,
        candidate: MutationCandidate,
        pad_locks: frozenset[int],
    ) -> Snapshot:
        """Build a new snapshot from ``candidate`` honoring ``pad_locks``.

        For each pad in the candidate's ``pad_deltas`` whose ``pad_id`` is
        **not** in ``pad_locks``, replace that pad's params with the
        candidate's ``proposed_params`` (machine name is preserved from
        the current state). Pads in ``pad_locks`` and pads not mentioned
        in the candidate are kept verbatim.

        Stores and returns the new snapshot.
        """

        # Index current pads by pad_id for O(1) lookup during apply.
        current_pads: dict[int, PadState] = {pad.pad_id: pad for pad in self._state.pads}

        # Index candidate deltas by pad_id (each delta is unique per pad_id).
        deltas_by_pad: dict[int, dict[str, int]] = {
            delta.pad_id: dict(delta.proposed_params) for delta in candidate.pad_deltas
        }

        new_pads: list[PadState] = []
        for pad_id, current_pad in current_pads.items():
            if pad_id in deltas_by_pad and pad_id not in pad_locks:
                # Mutation applies — replace params with proposed values.
                new_pads.append(
                    PadState(
                        pad_id=pad_id,
                        machine=current_pad.machine,
                        params=deltas_by_pad[pad_id],
                    )
                )
            else:
                # Either the candidate doesn't touch this pad, or it's locked.
                new_pads.append(current_pad)

        new_snapshot = Snapshot(
            snapshot_id=new_ulid(),
            device=self._state.device,
            captured_at=self._state.captured_at,
            pads=tuple(new_pads),
            scene_slot=self._state.scene_slot,
            bpm=self._state.bpm,
        )
        self._state = new_snapshot
        return new_snapshot

    def apply_send_plan(self, send_plan: CockpitSendPlan) -> Snapshot:
        """Apply a prepared SEND plan to the in-memory state.

        Only packets present in ``send_plan`` are applied, so locked pads
        excluded by preflight remain unchanged.
        """

        if not send_plan.ready:
            raise ValueError("send_plan_not_ready")

        updates_by_pad: dict[int, dict[str, int]] = {}
        for packet in send_plan.packets:
            updates_by_pad.setdefault(packet.pad_id, {})[packet.parameter] = packet.value

        new_pads: list[PadState] = []
        for current_pad in self._state.pads:
            updates = updates_by_pad.get(current_pad.pad_id)
            if updates is None:
                new_pads.append(current_pad)
                continue
            params = dict(current_pad.params)
            params.update(updates)
            new_pads.append(
                PadState(
                    pad_id=current_pad.pad_id,
                    machine=current_pad.machine,
                    params=params,
                )
            )

        new_snapshot = Snapshot(
            snapshot_id=new_ulid(),
            device=self._state.device,
            captured_at=self._state.captured_at,
            pads=tuple(new_pads),
            scene_slot=self._state.scene_slot,
            bpm=self._state.bpm,
        )
        self._state = new_snapshot
        return new_snapshot


__all__ = ["MockDeviceAdapter"]
