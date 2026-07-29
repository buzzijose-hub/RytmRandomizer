"""Kit morphing — deterministic interpolation between two Rytm states.

This is the passive, deterministic *preview* half of the single most-praised
Collider capability: turning one-shot randomization into a *playable*
dimension by interpolating between the current kit and a target (a saved
library snapshot or a randomized target), per track / per parameter group, at
a morph amount in ``0.0..1.0``.

It never sends MIDI, never opens a port, and never touches
:mod:`rytm_randomizer.randomization`. It produces a reproducible plan the
operator can audit and then arm-and-send through the existing ``senders``
ArmedApply seam.

Interpolation rules:

* **Continuous** parameters blend linearly:
  ``round(source + amount * (target - source))``.
* **Discrete** selector parameters (:data:`data.DISCRETE_PARAM_NAMES`) do not
  blend — an intermediate waveform/type index is meaningless. They threshold
  at the midpoint: ``amount < 0.5`` keeps the source value, ``amount >= 0.5``
  takes the target value.
* A parameter present in only one state cannot be morphed and is reported as
  ``unmatched`` (kept at whichever value exists), never invented.

Frozen dataclasses throughout; importing this module is side-effect free.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..data import PROFILES
from ..data.morph_scope_params import is_discrete_param

#: Morph amount bounds.
AMOUNT_MIN: Final[float] = 0.0
AMOUNT_MAX: Final[float] = 1.0

#: Discrete selectors flip to the target at or past this amount.
DISCRETE_THRESHOLD: Final[float] = 0.5


def _clamp_amount(amount: float) -> float:
    """Clamp ``amount`` into ``[AMOUNT_MIN, AMOUNT_MAX]``."""

    if amount < AMOUNT_MIN:
        return AMOUNT_MIN
    if amount > AMOUNT_MAX:
        return AMOUNT_MAX
    return amount


def interpolate_value(source: int, target: int, amount: float, *, discrete: bool) -> int:
    """Return the interpolated value for one parameter.

    Continuous: linear blend rounded to the nearest integer. Discrete: the
    source below :data:`DISCRETE_THRESHOLD`, the target at or above it.
    """

    clamped = _clamp_amount(amount)
    if discrete:
        return target if clamped >= DISCRETE_THRESHOLD else source
    return round(source + clamped * (target - source))


@dataclass(frozen=True)
class MorphTrack:
    """The source + target parameter states one track contributes to a morph.

    Injected so a caller can morph a captured kit snapshot toward a library
    snapshot or a randomized target. ``source`` and ``target`` each map
    parameter names to values; ``groups`` maps each parameter-group name to
    the parameter names it contains (drives ordering + per-group scoping).
    """

    track: int
    source_name: str
    target_name: str
    source: Mapping[str, int]
    target: Mapping[str, int]
    groups: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class MorphParam:
    """The interpolated value for one parameter under a morph plan."""

    name: str
    group: str
    source: int
    target: int
    interpolated: int
    discrete: bool

    @property
    def moved(self) -> bool:
        """True when the interpolated value differs from the source."""

        return self.interpolated != self.source


@dataclass(frozen=True)
class MorphTrackPlan:
    """The ordered per-parameter interpolation planned for one track.

    ``unmatched`` names appear in exactly one of source/target and so cannot
    be morphed; they are surfaced (not silently dropped) so the operator sees
    the two states are not fully aligned.
    """

    track: int
    source_name: str
    target_name: str
    params: tuple[MorphParam, ...]
    unmatched: tuple[str, ...]

    @property
    def moved_count(self) -> int:
        """Number of parameters whose interpolated value differs from source."""

        return sum(1 for param in self.params if param.moved)


@dataclass(frozen=True)
class MorphPlan:
    """A full deterministic kit-morph preview.

    Passive: a plan, not an action. ``ready`` / ``readiness_reason`` mirror the
    device strategy readiness contract so the generic guarded sender can accept
    the plan without morph-specific introspection.
    """

    amount: float
    groups: frozenset[str]
    track_plans: tuple[MorphTrackPlan, ...]
    ready: bool
    readiness_reason: str

    @property
    def total_moved(self) -> int:
        """Total parameters that would move across all tracks."""

        return sum(plan.moved_count for plan in self.track_plans)


def build_morph_track(
    track: int,
    source_key: str,
    target_key: str,
) -> MorphTrack:
    """Build a :class:`MorphTrack` from two V1.34 profile-registry anchors.

    ``source_key`` / ``target_key`` index :data:`data.PROFILES`; the anchors
    become the source/target states and the source profile's zones drive
    grouping. Raises ``KeyError`` for an unknown key (loud, not silent).
    """

    source = PROFILES[source_key]
    target = PROFILES[target_key]
    return MorphTrack(
        track=track,
        source_name=source["name"],
        target_name=target["name"],
        source=MappingProxyType(dict(source["anchor"])),
        target=MappingProxyType(dict(target["anchor"])),
        groups=MappingProxyType({name: tuple(params) for name, params in source["zones"].items()}),
    )


def plan_morph_track(track: MorphTrack, groups: frozenset[str], amount: float) -> MorphTrackPlan:
    """Return the deterministic per-parameter interpolation for one track.

    Only parameters in an in-scope group are morphed. A param present in only
    one of source/target is reported as ``unmatched``. Parameter order follows
    group order then param order, deduplicated across overlapping groups.
    """

    clamped = _clamp_amount(amount)
    params: list[MorphParam] = []
    unmatched: list[str] = []
    seen: set[str] = set()
    for group_name, param_names in track.groups.items():
        if group_name not in groups:
            continue
        for name in param_names:
            if name in seen:
                continue
            seen.add(name)
            in_source = name in track.source
            in_target = name in track.target
            if in_source and in_target:
                discrete = is_discrete_param(name)
                source_value = track.source[name]
                target_value = track.target[name]
                params.append(
                    MorphParam(
                        name=name,
                        group=group_name,
                        source=source_value,
                        target=target_value,
                        interpolated=interpolate_value(
                            source_value, target_value, clamped, discrete=discrete
                        ),
                        discrete=discrete,
                    )
                )
            elif in_source or in_target:
                unmatched.append(name)
    return MorphTrackPlan(
        track=track.track,
        source_name=track.source_name,
        target_name=track.target_name,
        params=tuple(params),
        unmatched=tuple(unmatched),
    )


def plan_morph(
    tracks: Sequence[MorphTrack],
    groups: frozenset[str],
    amount: float,
) -> MorphPlan:
    """Return the full deterministic kit-morph preview across ``tracks``.

    A plan is ``ready`` only when it would move at least one parameter — an
    empty group set, an amount of 0.0, or fully-aligned source==target states
    yield a not-ready plan with a reason.
    """

    track_plans = tuple(plan_morph_track(track, groups, amount) for track in tracks)
    total_moved = sum(plan.moved_count for plan in track_plans)
    if not groups:
        ready, reason = False, "no parameter groups selected"
    elif _clamp_amount(amount) == AMOUNT_MIN:
        ready, reason = False, "amount is 0.0 (source unchanged)"
    elif total_moved == 0:
        ready, reason = False, "source and target already match in scope"
    else:
        ready, reason = True, "ready"
    return MorphPlan(
        amount=_clamp_amount(amount),
        groups=groups,
        track_plans=track_plans,
        ready=ready,
        readiness_reason=reason,
    )


__all__ = [
    "AMOUNT_MAX",
    "AMOUNT_MIN",
    "DISCRETE_THRESHOLD",
    "MorphParam",
    "MorphPlan",
    "MorphTrack",
    "MorphTrackPlan",
    "build_morph_track",
    "interpolate_value",
    "plan_morph",
    "plan_morph_track",
]
