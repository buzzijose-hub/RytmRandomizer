"""``MockDeviceAdapter`` — in-memory, mock-safe device adapter.

Default adapter for cockpit development and tests. Holds a single
:class:`~rytm_randomizer.cockpit.data.Snapshot` in memory and applies
mutation candidates by replacing each non-locked pad's params with the
candidate's ``proposed_params``. Locked pads keep their current params
unchanged.

``is_armed`` is always ``False`` — this adapter never talks to hardware.
``commit_kit`` is a no-op (mock has no persistent kit memory) but logs at
INFO so operators see the intent in dev mode.
"""

from __future__ import annotations

import logging

from ..data import MutationCandidate, PadState, Snapshot, new_ulid

_logger = logging.getLogger(__name__)


class MockDeviceAdapter:
    """In-memory device adapter; never opens a MIDI port.

    Satisfies the :class:`~rytm_randomizer.cockpit.device.adapter.DeviceAdapter`
    Protocol via duck typing — not by inheritance.

    Constructor takes the initial snapshot that the mock starts in. Every
    :meth:`apply` produces a fresh snapshot (frozen dataclass) and stores
    it as the new ``_state``; subsequent :meth:`capture_snapshot` calls
    return that updated state.
    """

    def __init__(self, initial: Snapshot) -> None:
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

    def commit_kit(self, snapshot: Snapshot, label: str | None) -> None:
        """No-op for the mock; logs the intent at INFO for visibility."""

        _logger.info(
            "mock_commit_kit",
            extra={
                "snapshot_id": snapshot.snapshot_id,
                "device": snapshot.device,
                "label": label,
            },
        )


__all__ = ["MockDeviceAdapter"]
