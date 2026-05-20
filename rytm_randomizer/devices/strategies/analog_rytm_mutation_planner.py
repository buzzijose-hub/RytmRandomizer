"""Analog Rytm MK2 ``MutationPlanner`` strategy.

Implements :class:`rytm_randomizer.snapshot.planner.MutationPlanner` for
the Analog Rytm MK2. Consumes a :class:`RytmKitSnapshot` and a depth, and
produces a :class:`RytmMutationPlan` whose events describe the parameter
changes a renderer would emit.

Single-responsibility: this module decides *what* parameters to touch at
a given depth, drawing target ranges from the canonical
:mod:`rytm_randomizer.data` profiles. It does NOT decode SysEx, render
MIDI, or reach the registry. Random value selection is deterministic-on-
demand (seed-controlled via the planner's ``seed`` constructor argument)
so a snapshot+seed+depth tuple always produces the same plan.

Per Gate 6 the planner is structural (no inheritance); it satisfies the
WS-S6 ``MutationPlanner`` Protocol by exposing ``plan(snapshot, depth)``.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final

from ...data.profiles import PROFILES
from ...guardrails.validation import PAD_PROFILE_KEY
from .analog_rytm_snapshot_decoder import RytmKitSnapshot
from .analog_rytm_snapshot_routing import route_rytm_snapshot_machine_values

# ---------------------------------------------------------------------------
# Plan dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RytmPlanEvent:
    """One target change in a Rytm mutation plan.

    Attributes are immutable so plans can be safely shared across
    renderers / senders without aliasing.

    * ``pad`` -- 1-based pad index (1..track_count).
    * ``profile_key`` -- the matching key in ``data.PROFILES`` for the
      sound currently loaded on the pad (e.g. ``"2"`` for "My BD Hard").
    * ``parameter`` -- the parameter name from the profile's param map
      (e.g. ``"FLT Frequency"``).
    * ``value`` -- the target value in the parameter's safe range.
    """

    pad: int
    profile_key: str
    parameter: str
    value: int


@dataclass(frozen=True)
class RytmMutationPlan:
    """A complete Rytm mutation plan for one snapshot at one depth.

    * ``snapshot`` -- the originating snapshot (carried so senders can
      print "captured from kit X").
    * ``depth`` -- the depth the plan was generated for (non-negative).
    * ``events`` -- the ordered tuple of changes the renderer will emit.
    * ``ready`` -- ``True`` when the plan has at least one event and
      every event's pad / parameter resolves through ``PROFILES``. A
      ``ready=False`` plan tells the generic guarded sender to refuse.
    * ``readiness_reason`` -- human-readable explanation when
      ``ready=False`` (empty string when ready).
    """

    snapshot: RytmKitSnapshot
    depth: int
    events: tuple[RytmPlanEvent, ...] = field(default_factory=tuple)
    ready: bool = True
    readiness_reason: str = ""


# ---------------------------------------------------------------------------
# Depth bounds.
#
# Depth 0 = no mutation (every event collapses to its anchor value).
# Higher depths widen the random window inside each parameter's safe
# range. We cap at MAX_DEPTH to keep operator-facing behavior bounded;
# the V1.34 monolith and the existing engines use the same cap.
# ---------------------------------------------------------------------------

#: Maximum allowed depth. Matches the V1.34 monolith's documented range.
MAX_DEPTH: Final[int] = 7


# ---------------------------------------------------------------------------
# Strategy implementation.
# ---------------------------------------------------------------------------


class AnalogRytmMutationPlanner:
    """``MutationPlanner`` strategy for the Analog Rytm MK2.

    Stateless apart from the optional ``seed`` argument; one instance can
    be shared across the application. ``AnalogRytmDevice`` constructs one
    and holds it on its ``mutation_planner`` attribute.

    The planner produces one event per (pad, parameter) pair, drawing
    pads from ``PAD_PROFILE_KEY`` and parameter targets from each pad's
    profile's ``safe`` table. Values are picked via a seeded
    :class:`random.Random` instance so the plan is deterministic for a
    given ``(seed, snapshot.slot, depth)`` triple.
    """

    def __init__(self, *, seed: int = 0) -> None:
        """Initialize the planner with a deterministic-randomness seed."""

        self._seed = seed

    def plan(self, snapshot: RytmKitSnapshot, depth: int) -> RytmMutationPlan:
        """Build a :class:`RytmMutationPlan` from ``snapshot`` at ``depth``.

        ``depth`` must be in ``[0, MAX_DEPTH]``.

        At depth 0 every event collapses to the parameter's anchor value
        (the safe-range low bound). At higher depths the value is sampled
        from the safe range using the planner's seeded RNG, with the
        sampling window widened proportionally to ``depth / MAX_DEPTH``.

        Raises:
            ValueError: if ``snapshot`` is not a :class:`RytmKitSnapshot`
                or if ``depth`` is outside ``[0, MAX_DEPTH]``.
        """

        return self._plan_for_profile_keys(snapshot, depth, PAD_PROFILE_KEY)

    def plan_for_machine_values(
        self,
        snapshot: RytmKitSnapshot,
        depth: int,
        pad_machine_values: Mapping[int, int],
    ) -> RytmMutationPlan:
        """Build a plan from snapshot-derived ``pad -> machine_value`` facts."""

        self._validate_inputs(snapshot, depth)

        routing = route_rytm_snapshot_machine_values(pad_machine_values)
        if not routing.ready:
            return RytmMutationPlan(
                snapshot=snapshot,
                depth=depth,
                events=(),
                ready=False,
                readiness_reason=routing.readiness_reason,
            )

        return self._plan_for_profile_keys(snapshot, depth, routing.profile_keys_by_pad)

    def _validate_inputs(self, snapshot: RytmKitSnapshot, depth: int) -> None:
        if not isinstance(snapshot, RytmKitSnapshot):
            raise ValueError(
                "AnalogRytmMutationPlanner.plan: snapshot must be a "
                f"RytmKitSnapshot, got {type(snapshot).__name__}"
            )
        if depth < 0 or depth > MAX_DEPTH:
            raise ValueError(
                f"AnalogRytmMutationPlanner.plan: depth must be in [0, {MAX_DEPTH}], "
                f"got {depth}"
            )

    def _plan_for_profile_keys(
        self,
        snapshot: RytmKitSnapshot,
        depth: int,
        pad_profile_keys: Mapping[int, str],
    ) -> RytmMutationPlan:
        self._validate_inputs(snapshot, depth)

        # Derive a deterministic integer seed from (seed, slot, depth) so
        # the same triple always produces the same plan. Stuff the three
        # values into a single int via bit-shifting to keep the seed
        # space well-distributed.
        rng_seed = (self._seed * 1_000_003) ^ (snapshot.slot * 1009) ^ depth
        rng = random.Random(rng_seed)  # noqa: S311 - non-crypto, deterministic plan generation

        events: list[RytmPlanEvent] = []
        # Iterate pads in stable order so the plan is deterministic.
        for pad in sorted(pad_profile_keys):
            profile_key = pad_profile_keys[pad]
            profile = PROFILES.get(profile_key)
            if profile is None:
                # Should not happen with the canonical data, but guard so a
                # data drift gives a meaningful error rather than a None
                # dereference.
                return RytmMutationPlan(
                    snapshot=snapshot,
                    depth=depth,
                    events=tuple(events),
                    ready=False,
                    readiness_reason=(
                        f"pad {pad} references profile {profile_key!r} which "
                        "is not in PROFILES -- data drift"
                    ),
                )
            safe_table = profile["safe"]
            for parameter, (low, high) in safe_table.items():
                if depth == 0:
                    value = low
                else:
                    # Widen the sampling window proportionally to depth.
                    span = high - low
                    width = (span * depth) // MAX_DEPTH
                    pick_high = min(high, low + width)
                    value = rng.randint(low, pick_high)
                events.append(
                    RytmPlanEvent(
                        pad=pad,
                        profile_key=profile_key,
                        parameter=parameter,
                        value=value,
                    )
                )

        if not events:
            return RytmMutationPlan(
                snapshot=snapshot,
                depth=depth,
                events=(),
                ready=False,
                readiness_reason="no events produced -- PAD_PROFILE_KEY is empty",
            )

        return RytmMutationPlan(
            snapshot=snapshot,
            depth=depth,
            events=tuple(events),
            ready=True,
            readiness_reason="",
        )
