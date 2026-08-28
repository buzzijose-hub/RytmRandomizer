"""Analog Four MKII mutation planner Strategy."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Final

from ...data import ANALOG_FOUR_SYNTH_TRACK_CC
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...snapshot.mutation_scope import DEFAULT_MUTATION_SCOPE, MutationScope
from .analog_four_snapshot_decoder import AnalogFourKitSnapshot

MAX_A4_DEPTH: Final[int] = 7
_logger = get_logger(__name__)


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
    scope: MutationScope = DEFAULT_MUTATION_SCOPE


class AnalogFourMutationPlanner:
    """Mutation planner for candidate Analog Four snapshots."""

    def __init__(self, *, seed: int = 0) -> None:
        self._seed = seed

    def plan(
        self,
        snapshot: object,
        depth: int,
        *,
        scope: MutationScope = DEFAULT_MUTATION_SCOPE,
    ) -> AnalogFourMutationPlan:
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
        effective_tracks = scope.validated_effective_ids(range(1, 5), item_label="A4 track")
        if not snapshot.offsets_promoted:
            get_metrics().record_error("a4_mutation_plan_semantic_offsets_unpromoted")
            _logger.warning(
                "a4_mutation_plan_blocked",
                extra={
                    "locked_track_ids": sorted(scope.locked_ids),
                    "reason": "semantic_offsets_unpromoted",
                    "target_track_ids": sorted(scope.target_ids),
                },
            )
            return AnalogFourMutationPlan(
                snapshot=snapshot,
                depth=depth,
                events=(),
                ready=False,
                readiness_reason=(
                    "Analog Four offsets are candidate-only; saved-kit parameter byte offsets, "
                    "value encodings, and exact fixture evidence must be promoted before real send"
                ),
                scope=scope,
            )
        if not effective_tracks:
            get_metrics().record_error("a4_mutation_plan_no_sendable_tracks")
            _logger.warning(
                "a4_mutation_plan_blocked",
                extra={
                    "locked_track_ids": sorted(scope.locked_ids),
                    "reason": "no_sendable_tracks",
                    "target_track_ids": sorted(scope.target_ids),
                },
            )
            return AnalogFourMutationPlan(
                snapshot=snapshot,
                depth=depth,
                events=(),
                ready=False,
                readiness_reason="no sendable A4 tracks after targets and locks",
                scope=scope,
            )

        rng_seed = (self._seed * 1_000_003) ^ (snapshot.slot * 1009) ^ depth
        rng = random.Random(rng_seed)  # noqa: S311 - non-crypto mutation planning
        pwm_depth = ANALOG_FOUR_SYNTH_TRACK_CC["OSC1 PWM Depth"]
        pwm_control = pwm_depth.cc_msb
        if pwm_control is None:
            raise ValueError("OSC1 PWM Depth must have a promoted CC MSB")
        all_events = tuple(
            AnalogFourPlanEvent(
                track=track,
                parameter=pwm_depth.parameter,
                control=pwm_control,
                value=rng.randint(48, 96) if depth else 64,
            )
            for track in range(1, 5)
        )
        events = tuple(event for event in all_events if event.track in effective_tracks)
        return AnalogFourMutationPlan(
            snapshot=snapshot,
            depth=depth,
            events=events,
            ready=True,
            readiness_reason="",
            scope=scope,
        )
