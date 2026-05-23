"""``PadState`` and ``Snapshot`` frozen dataclasses.

A ``Snapshot`` is the whole device's parameter state at a point in time —
the atomic unit the cockpit history walks and the mutation engine reads.

Both dataclasses are ``frozen=True`` and provide a stable ``to_dict`` /
``from_dict`` round-trip so the WebSocket Protocol (WS-E) and the in-process
History store (WS-D) can serialize without re-implementing the shape.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Snapshot" for the authoritative definition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Final, Mapping, Self

_PAD_ID_MIN: Final[int] = 1
_PAD_ID_MAX: Final[int] = 12


def _freeze_params(params: Mapping[str, int]) -> Mapping[str, int]:
    """Return a read-only proxy over a defensive copy of ``params``.

    Two concerns are addressed in one step:

    1. **Aliasing.** If the caller hands in a regular ``dict`` and later
       mutates it, we don't want the snapshot's view to change. We copy.
    2. **Mutation through the snapshot.** The copy is wrapped in
       ``MappingProxyType`` so callers can't reach in and mutate.
    """

    return MappingProxyType(dict(params))


@dataclass(frozen=True)
class PadState:
    """The full parameter state of one pad on the device.

    Pads are addressed by 1-based ``pad_id``; today's product scope is pads
    1..4 but the data model accepts up to 12 (Rytm hardware's full track count).
    """

    pad_id: int
    machine: str
    params: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (_PAD_ID_MIN <= self.pad_id <= _PAD_ID_MAX):
            raise ValueError(
                f"pad_id must be in [{_PAD_ID_MIN}, {_PAD_ID_MAX}]; got {self.pad_id}"
            )
        if not self.machine:
            raise ValueError("machine must be a non-empty string")
        # Re-wrap params so an external mutable dict can't leak through.
        # ``frozen=True`` blocks direct assignment, so we use object.__setattr__.
        object.__setattr__(self, "params", _freeze_params(self.params))

    def to_dict(self) -> dict[str, object]:
        """Serialize to a plain dict suitable for JSON / MessagePack."""

        return {
            "pad_id": self.pad_id,
            "machine": self.machine,
            "params": dict(self.params),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        """Restore from a dict produced by :meth:`to_dict` (or a JSON load)."""

        params_obj = data["params"]
        assert isinstance(params_obj, Mapping), "params must be a Mapping"
        return cls(
            pad_id=int(data["pad_id"]),  # type: ignore[arg-type]
            machine=str(data["machine"]),
            params={str(k): int(v) for k, v in params_obj.items()},
        )


@dataclass(frozen=True)
class Snapshot:
    """The whole device's parameter state at a point in time.

    Every SEND auto-creates one; SAVE promotes one to persistent device
    memory. ``pads`` must arrive sorted ascending by ``pad_id`` with no
    duplicates.
    """

    snapshot_id: str
    device: str
    captured_at: datetime
    pads: tuple[PadState, ...]
    scene_slot: str | None
    bpm: float | None

    def __post_init__(self) -> None:
        if not self.snapshot_id:
            raise ValueError("snapshot_id must be a non-empty string")
        if not self.device:
            raise ValueError("device must be a non-empty string")
        seen: set[int] = set()
        prev: int | None = None
        for pad in self.pads:
            if pad.pad_id in seen:
                raise ValueError(f"duplicate pad_id {pad.pad_id} in pads")
            seen.add(pad.pad_id)
            if prev is not None and pad.pad_id <= prev:
                raise ValueError("pads must be sorted ascending by pad_id")
            prev = pad.pad_id

    def to_dict(self) -> dict[str, object]:
        """Serialize to a plain dict (timestamps go to ISO 8601 strings)."""

        return {
            "snapshot_id": self.snapshot_id,
            "device": self.device,
            "captured_at": self.captured_at.isoformat(),
            "pads": [pad.to_dict() for pad in self.pads],
            "scene_slot": self.scene_slot,
            "bpm": self.bpm,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        """Restore from a dict produced by :meth:`to_dict`."""

        pads_obj = data["pads"]
        assert isinstance(pads_obj, (list, tuple)), "pads must be a list/tuple"
        pads = tuple(PadState.from_dict(p) for p in pads_obj)  # type: ignore[arg-type]
        scene_slot_obj = data["scene_slot"]
        bpm_obj = data["bpm"]
        return cls(
            snapshot_id=str(data["snapshot_id"]),
            device=str(data["device"]),
            captured_at=datetime.fromisoformat(str(data["captured_at"])),
            pads=pads,
            scene_slot=None if scene_slot_obj is None else str(scene_slot_obj),
            bpm=None if bpm_obj is None else float(bpm_obj),  # type: ignore[arg-type]
        )


__all__ = ["PadState", "Snapshot"]
