"""Cockpit's Rytm/A4 mutation target state and WebSocket shape."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final, Self, TypedDict

from ..snapshot.mutation_scope import MutationScope

RYTM_PAD_TARGET_MIN: Final[int] = 1
RYTM_PAD_TARGET_MAX: Final[int] = 12
A4_TRACK_TARGET_MIN: Final[int] = 1
A4_TRACK_TARGET_MAX: Final[int] = 4


class MutationTargetsDict(TypedDict):
    """Stable WebSocket shape for :class:`MutationTargets`."""

    rytm_pad_targets: list[int]
    a4_track_targets: list[int]


def _validated_ids(
    values: Iterable[object],
    *,
    field_name: str,
    minimum: int,
    maximum: int,
) -> frozenset[int]:
    normalized = frozenset(values)
    invalid: list[object] = []
    valid: set[int] = set()
    for value in normalized:
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            invalid.append(value)
        else:
            valid.add(value)
    if invalid:
        rendered = sorted(repr(value) for value in invalid)
        raise ValueError(f"{field_name} must contain ids in [{minimum}, {maximum}]; got {rendered}")
    return frozenset(valid)


@dataclass(frozen=True)
class MutationTargets:
    """Explicit mutation include-lists for both Cockpit live-kit devices."""

    rytm_pad_targets: frozenset[int] = frozenset()
    a4_track_targets: frozenset[int] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rytm_pad_targets",
            _validated_ids(
                self.rytm_pad_targets,
                field_name="rytm_pad_targets",
                minimum=RYTM_PAD_TARGET_MIN,
                maximum=RYTM_PAD_TARGET_MAX,
            ),
        )
        object.__setattr__(
            self,
            "a4_track_targets",
            _validated_ids(
                self.a4_track_targets,
                field_name="a4_track_targets",
                minimum=A4_TRACK_TARGET_MIN,
                maximum=A4_TRACK_TARGET_MAX,
            ),
        )

    def rytm_scope(self, locked_pad_ids: Iterable[int] = ()) -> MutationScope:
        """Build the canonical Rytm target-plus-lock scope."""

        locks = _validated_ids(
            locked_pad_ids,
            field_name="locked_pad_ids",
            minimum=RYTM_PAD_TARGET_MIN,
            maximum=RYTM_PAD_TARGET_MAX,
        )
        return MutationScope(target_ids=self.rytm_pad_targets, locked_ids=locks)

    def a4_scope(self, locked_track_ids: Iterable[int] = ()) -> MutationScope:
        """Build the canonical A4 target-plus-lock scope."""

        locks = _validated_ids(
            locked_track_ids,
            field_name="locked_track_ids",
            minimum=A4_TRACK_TARGET_MIN,
            maximum=A4_TRACK_TARGET_MAX,
        )
        return MutationScope(target_ids=self.a4_track_targets, locked_ids=locks)

    def effective_rytm_pads(
        self,
        available_pad_ids: Iterable[int],
        locked_pad_ids: Iterable[int] = (),
    ) -> frozenset[int]:
        """Resolve Rytm include targets minus the lock deny-list."""

        return self.rytm_scope(locked_pad_ids).effective_ids(
            available_pad_ids,
            item_label="Rytm pad",
        )

    def effective_a4_tracks(
        self,
        available_track_ids: Iterable[int],
        locked_track_ids: Iterable[int] = (),
    ) -> frozenset[int]:
        """Resolve A4 include targets minus the lock deny-list."""

        return self.a4_scope(locked_track_ids).effective_ids(
            available_track_ids,
            item_label="A4 track",
        )

    def to_dict(self) -> MutationTargetsDict:
        """Serialize both target dimensions in stable numeric order."""

        return {
            "rytm_pad_targets": sorted(self.rytm_pad_targets),
            "a4_track_targets": sorted(self.a4_track_targets),
        }

    @classmethod
    def from_dict(cls, data: MutationTargetsDict) -> Self:
        """Restore and validate a target model from its wire shape."""

        return cls(
            rytm_pad_targets=frozenset(data["rytm_pad_targets"]),
            a4_track_targets=frozenset(data["a4_track_targets"]),
        )


__all__ = [
    "A4_TRACK_TARGET_MAX",
    "A4_TRACK_TARGET_MIN",
    "MutationTargets",
    "MutationTargetsDict",
    "RYTM_PAD_TARGET_MAX",
    "RYTM_PAD_TARGET_MIN",
]
