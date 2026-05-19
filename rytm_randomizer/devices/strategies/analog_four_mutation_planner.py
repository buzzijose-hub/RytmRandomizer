"""Analog Four MKII mutation planner Strategy."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Final

from .analog_four_snapshot_decoder import AnalogFourKitSnapshot

MAX_A4_DEPTH: Final[int] = 7


@dataclass(frozen=True)
class AnalogFourPlanEvent:
    """One target change in an Analog Four mutation plan."""

    track: int
    parameter: str
    control: int
    value: int


@dataclass(frozen=True)
class AnalogFourMutationPlan:
    """Complete A4 mutation plan for one snapshot and depth."""

    snapshot: AnalogFourKitSnapshot
    depth: int
    events: tuple[AnalogFourPlanEvent, ...] = field(default_factory=tuple)
    ready: bool = True
    readiness_reason: str = ""


class AnalogFourMutationPlanner:
    """Mutation planner for candidate Analog Four snapshots."""

    def __init__(self, *, seed: int = 0) -> None:
        self._seed = seed

    def plan(self, snapshot: AnalogFourKitSnapshot, depth: int) -> AnalogFourMutationPlan:
        """Build an A4 mutation plan from a decoded snapshot."""

        if not isinstance(snapshot, AnalogFourKitSnapshot):
            raise ValueError(
                "AnalogFourMutationPlanner.plan: snapshot must be an "
                f"AnalogFourKitSnapshot, got {type(snapshot).__name__}"
            )
        if depth < 0 or depth > MAX_A4_DEPTH:
            raise ValueError(
                f"AnalogFourMutationPlanner.plan: depth must be in [0, {MAX_A4_DEPTH}], "
                f"got {depth}"
            )
        if not snapshot.offsets_promoted:
            return AnalogFourMutationPlan(
                snapshot=snapshot,
                depth=depth,
                events=(),
                ready=False,
                readiness_reason=(
                    "Analog Four offsets are candidate-only; promote offsets before real send"
                ),
            )

        rng_seed = (self._seed * 1_000_003) ^ (snapshot.slot * 1009) ^ depth
        rng = random.Random(rng_seed)  # noqa: S311 - non-crypto mutation planning
        events = tuple(
            AnalogFourPlanEvent(
                track=track,
                parameter="Filter 1 Frequency",
                control=74,
                value=rng.randint(48, 96) if depth else 64,
            )
            for track in range(1, 5)
        )
        return AnalogFourMutationPlan(
            snapshot=snapshot,
            depth=depth,
            events=events,
            ready=True,
            readiness_reason="",
        )
