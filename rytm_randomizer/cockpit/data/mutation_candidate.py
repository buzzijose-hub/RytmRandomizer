"""``PadDelta`` and ``MutationCandidate`` frozen dataclasses.

A ``MutationCandidate`` is the deterministic output of
``mutate(snapshot, profile, depth, seed)`` (WS-B). It is not yet sent to
the device — SEND fires it, the UI previews against it. Two facts the
dataclass enforces structurally:

1. Every changed key in a ``PadDelta`` must also appear in the proposed
   parameter set — a delta whose ``changed_keys`` references a missing
   key is malformed.
2. ``depth`` lives in the closed interval [0.10, 0.90] per spec; the
   UI's slider snaps to that range, and out-of-range candidates are
   refused at construction time.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"MutationCandidate" for the authoritative shape.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Self, TypedDict

from .types import STATUS_VALUES, Status, narrow_status


class PadDeltaDict(TypedDict):
    """Wire shape of :class:`PadDelta` (M1/P2)."""

    pad_id: int
    proposed_params: Mapping[str, int]
    changed_keys: list[str]


class MutationCandidateDict(TypedDict):
    """Wire shape of :class:`MutationCandidate` (M1/P2).

    ``safety_status`` is typed as plain ``str`` because the wire layer
    may receive any value; runtime narrowing in
    :meth:`MutationCandidate.from_dict` is the validation boundary.
    """

    candidate_id: str
    source_snapshot_id: str
    profile_id: str
    depth: float
    seed: int
    pad_deltas: list[PadDeltaDict]
    safety_status: str
    estimated_midi_msgs: int


_PAD_ID_MIN: Final[int] = 1
_PAD_ID_MAX: Final[int] = 12
_DEPTH_MIN: Final[float] = 0.10
_DEPTH_MAX: Final[float] = 0.90


@dataclass(frozen=True)
class PadDelta:
    """One pad's contribution to a mutation candidate.

    Carries the proposed (target) parameter set for the pad plus a
    ``changed_keys`` view — the subset of parameter names that actually
    differ from the source snapshot. Empty ``changed_keys`` is legal
    (e.g., a locked pad whose target equals the current value).
    """

    pad_id: int
    proposed_params: Mapping[str, int]
    changed_keys: frozenset[str]

    def __post_init__(self) -> None:
        if not (_PAD_ID_MIN <= self.pad_id <= _PAD_ID_MAX):
            raise ValueError(f"pad_id must be in [{_PAD_ID_MIN}, {_PAD_ID_MAX}]; got {self.pad_id}")
        proposed_keys = set(self.proposed_params.keys())
        unknown = self.changed_keys - proposed_keys
        if unknown:
            raise ValueError(
                "changed_keys must be a subset of proposed_params keys; "
                f"unknown: {sorted(unknown)}"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "pad_id": self.pad_id,
            "proposed_params": dict(self.proposed_params),
            "changed_keys": sorted(self.changed_keys),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        proposed_obj = data["proposed_params"]
        changed_obj = data["changed_keys"]
        if not isinstance(proposed_obj, Mapping):
            raise TypeError(f"proposed_params must be a Mapping; got {type(proposed_obj).__name__}")
        if not isinstance(changed_obj, (list, tuple, frozenset, set)):
            raise TypeError(f"changed_keys must be an iterable; got {type(changed_obj).__name__}")
        return cls(
            pad_id=int(data["pad_id"]),  # type: ignore[arg-type]
            proposed_params={str(k): int(v) for k, v in proposed_obj.items()},
            changed_keys=frozenset(str(k) for k in changed_obj),
        )


@dataclass(frozen=True)
class MutationCandidate:
    """The deterministic output of the mutation engine, ready to preview/send.

    The same (snapshot, profile, depth, seed) tuple always produces an
    equal candidate; REGEN bumps the seed to vary the output without
    moving the depth slider.
    """

    candidate_id: str
    source_snapshot_id: str
    profile_id: str
    depth: float
    seed: int
    pad_deltas: tuple[PadDelta, ...]
    safety_status: Status
    estimated_midi_msgs: int

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id must be a non-empty string")
        if not self.source_snapshot_id:
            raise ValueError("source_snapshot_id must be a non-empty string")
        if not self.profile_id:
            raise ValueError("profile_id must be a non-empty string")
        if not (_DEPTH_MIN <= self.depth <= _DEPTH_MAX):
            raise ValueError(f"depth must be in [{_DEPTH_MIN}, {_DEPTH_MAX}]; got {self.depth}")
        if self.safety_status not in STATUS_VALUES:
            raise ValueError(
                f"safety_status must be one of {STATUS_VALUES}; got {self.safety_status!r}"
            )
        if self.estimated_midi_msgs < 0:
            raise ValueError(f"estimated_midi_msgs must be >= 0; got {self.estimated_midi_msgs}")

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "source_snapshot_id": self.source_snapshot_id,
            "profile_id": self.profile_id,
            "depth": self.depth,
            "seed": self.seed,
            "pad_deltas": [d.to_dict() for d in self.pad_deltas],
            "safety_status": self.safety_status,
            "estimated_midi_msgs": self.estimated_midi_msgs,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        deltas_obj = data["pad_deltas"]
        if not isinstance(deltas_obj, (list, tuple)):
            raise TypeError(f"pad_deltas must be a list/tuple; got {type(deltas_obj).__name__}")
        return cls(
            candidate_id=str(data["candidate_id"]),
            source_snapshot_id=str(data["source_snapshot_id"]),
            profile_id=str(data["profile_id"]),
            depth=float(data["depth"]),  # type: ignore[arg-type]
            seed=int(data["seed"]),  # type: ignore[arg-type]
            pad_deltas=tuple(PadDelta.from_dict(d) for d in deltas_obj),
            safety_status=narrow_status(str(data["safety_status"])),
            estimated_midi_msgs=int(data["estimated_midi_msgs"]),  # type: ignore[arg-type]
        )


__all__ = [
    "MutationCandidate",
    "MutationCandidateDict",
    "PadDelta",
    "PadDeltaDict",
]
