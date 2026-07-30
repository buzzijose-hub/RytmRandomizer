"""Scoped randomization — a ScopeMask + depth macro over the anchor engine.

This is the passive, deterministic *preview* half of the classic Rytm
mask+intensity randomizer UX (the orphaned Strom/Collider "which tracks,
which parameter groups, how hard" surface). It never sends MIDI, never opens a
port, and never touches :mod:`rytm_randomizer.randomization` — it re-expresses
the anchor+depth idea as a pure, reproducible plan the operator can audit and
then arm-and-send through the existing ``senders`` ArmedApply seam.

The model:

* :class:`ScopeMask` picks exactly which of the 12 pads and which named
  parameter groups (``src`` / ``filter`` / ``amp`` / ...) are in scope.
* ``depth`` is a single macro in ``0.0..1.0``. ``0.0`` leaves every parameter
  on its anchor; ``1.0`` pushes each parameter the full distance to the
  *nearer* edge of its safe range. The move is deterministic (no RNG): the
  signed offset is ``round(depth * reach)`` toward the wider safe side, so the
  same mask + depth always yields the same plan — a previewable, testable
  intensity dimension rather than a one-shot dice roll.
* Discrete selector params (:data:`data.DISCRETE_PARAM_NAMES`) are held on
  their anchor — a scoped *intensity* sweep must not silently reindex a
  waveform/type selector; changing those is the morph surface's job.

Frozen dataclasses throughout; importing this module is side-effect free.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..data.morph_scope_params import is_discrete_param
from .profile_facts import (
    profile_anchor,
    profile_display_name,
    profile_safe_bounds,
    profile_zone_groups,
)

#: The Analog Rytm has 12 pads/tracks.
TRACK_COUNT: Final[int] = 12

#: Depth macro bounds.
DEPTH_MIN: Final[float] = 0.0
DEPTH_MAX: Final[float] = 1.0


def _clamp_depth(depth: float) -> float:
    """Clamp ``depth`` into ``[DEPTH_MIN, DEPTH_MAX]``."""

    if depth < DEPTH_MIN:
        return DEPTH_MIN
    if depth > DEPTH_MAX:
        return DEPTH_MAX
    return depth


@dataclass(frozen=True)
class ScopeMask:
    """Which tracks and parameter groups a scoped randomization touches.

    ``tracks`` is a frozenset of 1-based pad numbers (1..12). ``groups`` is a
    frozenset of parameter-group names (the profile ``zones`` keys, e.g.
    ``"src"``, ``"filter"``, ``"amp"``). An empty set means "nothing in that
    dimension is in scope" — a valid, no-op mask.
    """

    tracks: frozenset[int]
    groups: frozenset[str]

    def __post_init__(self) -> None:
        for track in self.tracks:
            if not (1 <= track <= TRACK_COUNT):
                raise ValueError(
                    f"track {track} out of range 1..{TRACK_COUNT}; "
                    "ScopeMask tracks are 1-based pad numbers"
                )

    def includes_track(self, track: int) -> bool:
        """Return True when ``track`` (1-based pad number) is in scope."""

        return track in self.tracks

    def includes_group(self, group: str) -> bool:
        """Return True when parameter group ``group`` is in scope."""

        return group in self.groups


@dataclass(frozen=True)
class TrackScope:
    """The anchor + safe-range facts one track contributes to a scope plan.

    Injected rather than looked up so a caller can preview against a captured
    kit snapshot instead of the built-in V1.34 profile registry. ``anchor``
    maps each parameter name to its current value; ``safe`` maps each
    parameter name to an inclusive ``(low, high)`` bound; ``groups`` maps each
    parameter-group name to the parameter names it contains.
    """

    track: int
    profile_name: str
    anchor: Mapping[str, int]
    safe: Mapping[str, tuple[int, int]]
    groups: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class ParamDelta:
    """The planned move for one parameter under a scope plan (deterministic)."""

    name: str
    group: str
    anchor: int
    planned: int

    @property
    def delta(self) -> int:
        """Signed change from anchor to planned value."""

        return self.planned - self.anchor


@dataclass(frozen=True)
class TrackScopePlan:
    """The ordered per-parameter deltas planned for one in-scope track."""

    track: int
    profile_name: str
    deltas: tuple[ParamDelta, ...]

    @property
    def changed_count(self) -> int:
        """Number of parameters whose planned value differs from the anchor."""

        return sum(1 for delta in self.deltas if delta.delta != 0)


@dataclass(frozen=True)
class ScopePlan:
    """A full deterministic scoped-randomization preview.

    Passive: this is a plan, not an action. ``ready`` mirrors the device
    strategy's readiness contract so the generic guarded sender can accept it
    without scope-specific introspection; ``readiness_reason`` explains a
    not-ready plan (e.g. an empty mask).
    """

    depth: float
    mask: ScopeMask
    track_plans: tuple[TrackScopePlan, ...]
    ready: bool
    readiness_reason: str

    @property
    def total_changed(self) -> int:
        """Total number of parameters that would move across all tracks."""

        return sum(plan.changed_count for plan in self.track_plans)


def _reach(anchor: int, low: int, high: int) -> int:
    """Return the signed maximum reach from ``anchor`` toward the wider side.

    Deterministic direction rule: move toward whichever safe edge is farther
    from the anchor (the side with the most headroom), so a full-depth sweep
    has the largest musical effect. Ties (equal headroom) resolve upward.
    """

    up = high - anchor
    down = anchor - low
    if up >= down:
        return up
    return -down


def _scaled_offset(reach: int, depth: float) -> int:
    """Return the depth-scaled signed offset (round-half-to-even is fine here)."""

    return round(reach * depth)


def build_track_scope(track: int, profile_key: str) -> TrackScope:
    """Build a :class:`TrackScope` from the built-in V1.34 profile registry.

    ``profile_key`` indexes :data:`data.PROFILES`. Raises ``KeyError`` for an
    unknown key (loud, not silent). The returned facts are read-only copies.
    """

    return TrackScope(
        track=track,
        profile_name=profile_display_name(profile_key),
        anchor=MappingProxyType(profile_anchor(profile_key)),
        safe=MappingProxyType(profile_safe_bounds(profile_key)),
        groups=MappingProxyType(profile_zone_groups(profile_key)),
    )


def plan_track_scope(scope: TrackScope, mask: ScopeMask, depth: float) -> TrackScopePlan:
    """Return the deterministic per-parameter plan for one in-scope track.

    Only parameters that live in an in-scope group *and* have a safe bound and
    are continuous move; everything else stays on its anchor. Parameter order
    follows the group order in ``scope.groups`` then param order within each
    group, deduplicated so a param appearing in two groups is planned once.
    """

    clamped_depth = _clamp_depth(depth)
    deltas: list[ParamDelta] = []
    seen: set[str] = set()
    for group_name, param_names in scope.groups.items():
        if not mask.includes_group(group_name):
            continue
        for name in param_names:
            if name in seen:
                continue
            seen.add(name)
            anchor_value = scope.anchor.get(name)
            bound = scope.safe.get(name)
            if anchor_value is None or bound is None or is_discrete_param(name):
                continue
            low, high = bound
            clamped_anchor = min(max(anchor_value, low), high)
            reach = _reach(clamped_anchor, low, high)
            planned = clamped_anchor + _scaled_offset(reach, clamped_depth)
            deltas.append(
                ParamDelta(name=name, group=group_name, anchor=anchor_value, planned=planned)
            )
    return TrackScopePlan(
        track=scope.track,
        profile_name=scope.profile_name,
        deltas=tuple(deltas),
    )


def plan_scope(
    scopes: Sequence[TrackScope],
    mask: ScopeMask,
    depth: float,
) -> ScopePlan:
    """Return the full deterministic scoped-randomization preview.

    ``scopes`` is the roster of tracks the operator could touch; only those in
    ``mask.tracks`` are planned. A plan is ``ready`` only when it would move at
    least one parameter — an empty mask, a zero depth, or a mask that selects
    no reachable parameter yields a not-ready plan with a reason.
    """

    track_plans = tuple(
        plan_track_scope(scope, mask, depth) for scope in scopes if mask.includes_track(scope.track)
    )
    total_changed = sum(plan.changed_count for plan in track_plans)
    if not mask.tracks:
        ready, reason = False, "no tracks selected"
    elif not mask.groups:
        ready, reason = False, "no parameter groups selected"
    elif _clamp_depth(depth) == DEPTH_MIN:
        ready, reason = False, "depth is 0.0 (no movement)"
    elif total_changed == 0:
        ready, reason = False, "mask selects no reachable continuous parameters"
    else:
        ready, reason = True, "ready"
    return ScopePlan(
        depth=_clamp_depth(depth),
        mask=mask,
        track_plans=track_plans,
        ready=ready,
        readiness_reason=reason,
    )


__all__ = [
    "DEPTH_MAX",
    "DEPTH_MIN",
    "TRACK_COUNT",
    "ParamDelta",
    "ScopeMask",
    "ScopePlan",
    "TrackScope",
    "TrackScopePlan",
    "build_track_scope",
    "plan_scope",
    "plan_track_scope",
]
