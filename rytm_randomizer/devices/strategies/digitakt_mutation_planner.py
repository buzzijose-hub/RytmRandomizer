"""Digitakt mutation planner Strategy.

Structurally conforms to :class:`rytm_randomizer.snapshot.planner.MutationPlanner`.

**This planner is deliberately zero-event.** Every plan it returns carries
``ready=False`` and a ``readiness_reason``, because Digitakt saved-project
byte offsets have never been validated against hardware. This mirrors the
Analog Four precedent and satisfies
``.claude/rules/targeted-mutation-safety.md`` #6: offsets must be promoted
from real captures with exact re-encode evidence before anything becomes
sendable, and must never be inferred from live CC facts.

The scope / target / lock plumbing is fully wired even though no events
are emitted, so promoting offsets later is a one-flag change rather than a
rewrite -- and the refusal is visible and tested today.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from ...data.digitakt_saved_kit_layout import (
    DIGITAKT_OFFSETS_PROMOTED,
    DIGITAKT_UNPROMOTED_REASON,
)
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...snapshot.mutation_scope import DEFAULT_MUTATION_SCOPE, MutationScope
from ...snapshot.planner import MutationPlanner
from .digitakt_snapshot_decoder import DigitaktKitSnapshot
from .digitakt_track_domain import DigitaktTrackDomain

MAX_DIGITAKT_DEPTH: Final[int] = 7
_logger = get_logger(__name__)


@dataclass(frozen=True)
class DigitaktPlanEvent:
    """One target change in a Digitakt mutation plan.

    No planner path constructs these yet (plans are zero-event while
    offsets are unpromoted). The type exists so the renderer has a
    concrete contract to validate against and so promotion does not
    require inventing the shape under time pressure.
    """

    track: int
    parameter: str
    control: int
    value: int


@dataclass(frozen=True)
class DigitaktMutationPlan:
    """Complete Digitakt mutation plan for one snapshot and depth."""

    snapshot: DigitaktKitSnapshot
    depth: int
    events: tuple[DigitaktPlanEvent, ...] = field(default_factory=tuple)
    ready: bool = False
    readiness_reason: str = DIGITAKT_UNPROMOTED_REASON
    scope: MutationScope = DEFAULT_MUTATION_SCOPE


class DigitaktMutationPlanner:
    """Mutation planner for candidate Digitakt snapshots."""

    def __init__(self, *, track_domain: DigitaktTrackDomain, device_id: str) -> None:
        self.track_domain = track_domain
        self.device_id = device_id

    def plan(
        self,
        snapshot: object,
        depth: int,
        *,
        scope: MutationScope = DEFAULT_MUTATION_SCOPE,
    ) -> DigitaktMutationPlan:
        """Build a Digitakt mutation plan from a decoded snapshot.

        Validates inputs and scope, then refuses: the returned plan is
        always zero-event and not ready while offsets are unpromoted.
        """

        if not isinstance(snapshot, DigitaktKitSnapshot):
            raise ValueError(
                "DigitaktMutationPlanner.plan: snapshot must be a "
                f"DigitaktKitSnapshot, got {type(snapshot).__name__}"
            )
        if depth < 0 or depth > MAX_DIGITAKT_DEPTH:
            raise ValueError(
                f"DigitaktMutationPlanner.plan: depth must be in [0, {MAX_DIGITAKT_DEPTH}], "
                f"got {depth}"
            )

        # Validate targets/locks even though nothing is emitted, so an
        # out-of-domain target fails loudly now rather than at promotion.
        effective_tracks = scope.validated_effective_ids(
            self.track_domain.track_ids,
            item_label="Digitakt track",
        )

        if not DIGITAKT_OFFSETS_PROMOTED or not snapshot.offsets_promoted:
            get_metrics().record_error("digitakt_mutation_plan_semantic_offsets_unpromoted")
            _logger.warning(
                "digitakt_mutation_plan_blocked",
                extra={
                    "device_id": self.device_id,
                    "locked_track_ids": sorted(scope.locked_ids),
                    "reason": "semantic_offsets_unpromoted",
                    "target_track_ids": sorted(scope.target_ids),
                },
            )
            return DigitaktMutationPlan(
                snapshot=snapshot,
                depth=depth,
                events=(),
                ready=False,
                readiness_reason=DIGITAKT_UNPROMOTED_REASON,
                scope=scope,
            )

        if not effective_tracks:  # pragma: no cover - unreachable until offsets are promoted
            get_metrics().record_error("digitakt_mutation_plan_no_sendable_tracks")
            return DigitaktMutationPlan(
                snapshot=snapshot,
                depth=depth,
                events=(),
                ready=False,
                readiness_reason="no sendable Digitakt tracks after targets and locks",
                scope=scope,
            )

        # Reached only once offsets are promoted; event synthesis lands in
        # that same change set, with fixture-backed evidence.
        raise NotImplementedError(  # pragma: no cover - guarded by the flag above
            "Digitakt event synthesis lands with the offset-promotion workstream"
        )


def _satisfies_mutation_planner(value: object) -> bool:
    """Structural check behind an ``object`` parameter (see digitakt.py)."""

    return isinstance(value, MutationPlanner)


def _assert_planner_protocol_conformance() -> None:
    """Document structural conformance to the WS-S6 ``MutationPlanner``."""

    probe = DigitaktMutationPlanner(
        track_domain=DigitaktTrackDomain(track_count=8),
        device_id="_probe",
    )
    if not _satisfies_mutation_planner(probe):
        # Structural-typing invariant; see docs/ARCHITECTURE.md §8.
        raise AssertionError(  # pragma: no cover - structural-typing invariant
            "DigitaktMutationPlanner does not satisfy MutationPlanner"
        )


_assert_planner_protocol_conformance()


__all__ = [
    "MAX_DIGITAKT_DEPTH",
    "DigitaktMutationPlan",
    "DigitaktMutationPlanner",
    "DigitaktPlanEvent",
]
