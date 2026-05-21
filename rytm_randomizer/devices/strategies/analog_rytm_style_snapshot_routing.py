"""Passive style-aware Analog Rytm snapshot routing helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ...data.rytm_machine_catalog import (
    MUTABLE_V134,
    RYTM_MACHINE_PROFILES_BY_KEY,
    RytmMachineProfile,
    allowed_machine_profiles_for_pad,
    get_rytm_pad_capability,
)
from ...data.style_discovery import (
    DEFAULT_STYLE_DISCOVERY_AMOUNT,
    StyleDiscoveryPolicy,
    style_discovery_policy,
)
from ...data.style_targets import STYLE_TARGET_VECTORS, StyleTargetVector
from .analog_rytm_snapshot_decoder import RytmKitSnapshot
from .analog_rytm_snapshot_routing import (
    RytmSnapshotMachineRoute,
    route_rytm_snapshot_machine_values,
)

_ZONE_AXIS_WEIGHTS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "body": (
            "low_end_weight",
            "drive_pressure",
            "warehouse_intensity",
            "decay_tail",
        ),
        "amp": (
            "transient_density",
            "attack_sharpness",
            "percussive_density",
        ),
        "filter": (
            "darkness",
            "space_depth",
            "tonal_center_weight",
        ),
        "grit": (
            "noise_grit",
            "industrial_edge",
            "metallicity",
            "drive_pressure",
        ),
        "lfo": (
            "motion_amount",
            "repetition_hypnosis",
            "space_depth",
        ),
        "morph": (
            "tonal_center_weight",
            "motion_amount",
            "metallicity",
        ),
    }
)

_ROLE_AXIS_WEIGHTS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "kick": ("low_end_weight", "drive_pressure", "warehouse_intensity"),
        "snare": ("transient_density", "attack_sharpness", "percussive_density"),
        "rim": ("transient_density", "attack_sharpness", "minimal_restraint"),
        "clap": ("transient_density", "space_depth", "percussive_density"),
        "tom": ("low_end_weight", "decay_tail", "percussive_density"),
        "hihat": ("transient_density", "metallicity", "percussive_density"),
        "cymbal": ("metallicity", "space_depth", "decay_tail"),
        "cowbell": ("metallicity", "attack_sharpness", "percussive_density"),
        "synth": ("tonal_center_weight", "motion_amount", "repetition_hypnosis"),
        "noise": ("noise_grit", "industrial_edge", "darkness"),
        "fm": ("metallicity", "attack_sharpness", "motion_amount"),
        "utility": ("noise_grit", "industrial_edge", "minimal_restraint"),
    }
)

_MAX_CANDIDATES: Final[int] = 5
_PRIMARY_FAMILY_BONUS: Final[int] = 40


@dataclass(frozen=True)
class RytmStyleMachineCandidate:
    """One legal machine candidate ranked for a style target."""

    machine_key: str
    label: str
    machine_value: int
    support_status: str
    score: int


@dataclass(frozen=True)
class RytmStyleSnapshotPadPlan:
    """One pad's style-aware snapshot routing preview."""

    pad: int
    track_code: str
    label: str
    current_machine_value: int | None
    current_machine_key: str | None
    profile_key: str | None
    route_ready: bool
    readiness_reason: str
    discovery_band: str
    machine_switching_allowed: bool
    favored_zones: tuple[str, ...]
    compatible_machine_candidates: tuple[RytmStyleMachineCandidate, ...]
    mutable_machine_candidates: tuple[RytmStyleMachineCandidate, ...]


@dataclass(frozen=True)
class RytmStyleSnapshotRoutingPlan:
    """Passive style-aware routing plan for one Rytm kit snapshot."""

    kit_name: str
    slot: int
    style_key: str
    discovery_amount: int
    discovery_band: str
    machine_switching_allowed: bool
    favored_zones: tuple[str, ...]
    ready_pad_count: int
    blocked_pad_count: int
    partial_snapshot_mutation_ready: bool
    pads_by_pad: Mapping[int, RytmStyleSnapshotPadPlan]


def _axis_sum(target: StyleTargetVector, axes: tuple[str, ...]) -> int:
    values = target.as_mapping()
    return sum(values[axis] for axis in axes)


def _favored_zones(
    target: StyleTargetVector,
    *,
    policy: StyleDiscoveryPolicy,
) -> tuple[str, ...]:
    scored = sorted(
        ((zone, _axis_sum(target, axes)) for zone, axes in _ZONE_AXIS_WEIGHTS.items()),
        key=lambda item: (-item[1], item[0]),
    )
    return tuple(zone for zone, score in scored if score >= 150)[: policy.zone_limit]


def _candidate_score(
    profile: RytmMachineProfile,
    target: StyleTargetVector,
    *,
    primary_family: str,
) -> int:
    score = 0
    for tag in profile.role_tags:
        axes = _ROLE_AXIS_WEIGHTS.get(tag)
        if axes is not None:
            score += _axis_sum(target, axes)
    if profile.family == primary_family:
        score += _PRIMARY_FAMILY_BONUS
    if profile.support_status == MUTABLE_V134:
        score += 25
    return score


def _candidate(
    profile: RytmMachineProfile,
    target: StyleTargetVector,
    *,
    primary_family: str,
) -> RytmStyleMachineCandidate:
    return RytmStyleMachineCandidate(
        machine_key=profile.key,
        label=profile.label,
        machine_value=profile.machine_value,
        support_status=profile.support_status,
        score=_candidate_score(profile, target, primary_family=primary_family),
    )


def _ranked_candidates(
    pad: int,
    target: StyleTargetVector,
    *,
    limit: int,
) -> tuple[RytmStyleMachineCandidate, ...]:
    primary_family = get_rytm_pad_capability(pad).track_code
    candidates = [
        _candidate(profile, target, primary_family=primary_family)
        for profile in allowed_machine_profiles_for_pad(pad)
    ]
    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                -candidate.score,
                candidate.support_status != MUTABLE_V134,
                candidate.machine_key,
            ),
        )[: min(limit, _MAX_CANDIDATES)]
    )


def _machine_key_for_route(route: RytmSnapshotMachineRoute) -> str | None:
    if route.machine_key is not None:
        return route.machine_key
    for profile in RYTM_MACHINE_PROFILES_BY_KEY.values():
        if profile.machine_value == route.machine_value:
            return profile.key
    return None


def _pad_plan(
    *,
    pad: int,
    route: RytmSnapshotMachineRoute,
    target: StyleTargetVector,
    policy: StyleDiscoveryPolicy,
    favored_zones: tuple[str, ...],
) -> RytmStyleSnapshotPadPlan:
    capability = get_rytm_pad_capability(pad)
    if policy.band == "reference" and route.machine_key is not None:
        profile = RYTM_MACHINE_PROFILES_BY_KEY.get(route.machine_key)
        candidates = (
            ()
            if profile is None
            else (_candidate(profile, target, primary_family=capability.track_code),)
        )
    else:
        candidates = _ranked_candidates(pad, target, limit=policy.candidate_limit)
    mutable_candidates = tuple(
        candidate for candidate in candidates if candidate.support_status == MUTABLE_V134
    )
    return RytmStyleSnapshotPadPlan(
        pad=pad,
        track_code=capability.track_code,
        label=capability.label,
        current_machine_value=route.machine_value,
        current_machine_key=_machine_key_for_route(route),
        profile_key=route.profile_key,
        route_ready=route.ready,
        readiness_reason=route.reason,
        discovery_band=policy.band,
        machine_switching_allowed=policy.machine_switching_allowed,
        favored_zones=favored_zones,
        compatible_machine_candidates=candidates,
        mutable_machine_candidates=mutable_candidates,
    )


def plan_rytm_style_snapshot_routes(
    snapshot: RytmKitSnapshot,
    style_key: str,
    *,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> RytmStyleSnapshotRoutingPlan:
    """Return a passive style-aware routing preview for one Rytm snapshot."""

    if not isinstance(snapshot, RytmKitSnapshot):
        raise ValueError(
            "plan_rytm_style_snapshot_routes: snapshot must be a "
            f"RytmKitSnapshot, got {type(snapshot).__name__}"
        )
    normalized_key = style_key.strip().lower()
    target = STYLE_TARGET_VECTORS.get(normalized_key)
    if target is None:
        raise ValueError(f"Unknown style target key: {style_key}")

    policy = style_discovery_policy(discovery_amount)
    favored_zones = _favored_zones(target, policy=policy)
    pads: dict[int, RytmStyleSnapshotPadPlan] = {}
    for pad, fact in sorted(snapshot.machine_facts.facts_by_pad.items()):
        if fact.decoded_machine_value is None:
            route = RytmSnapshotMachineRoute(
                pad=pad,
                machine_value=fact.raw_machine_value,
                machine_key=None,
                profile_key=None,
                ready=False,
                reason=fact.reason,
            )
        else:
            route = route_rytm_snapshot_machine_values(
                {pad: fact.decoded_machine_value}
            ).routes_by_pad[pad]
        pads[pad] = _pad_plan(
            pad=pad,
            route=route,
            target=target,
            policy=policy,
            favored_zones=favored_zones,
        )

    ready_count = sum(1 for pad_plan in pads.values() if pad_plan.route_ready)
    return RytmStyleSnapshotRoutingPlan(
        kit_name=snapshot.kit_name,
        slot=snapshot.slot,
        style_key=normalized_key,
        discovery_amount=policy.amount,
        discovery_band=policy.band,
        machine_switching_allowed=policy.machine_switching_allowed,
        favored_zones=favored_zones,
        ready_pad_count=ready_count,
        blocked_pad_count=len(pads) - ready_count,
        partial_snapshot_mutation_ready=ready_count > 0,
        pads_by_pad=MappingProxyType(pads),
    )


__all__ = [
    "RytmStyleMachineCandidate",
    "RytmStyleSnapshotPadPlan",
    "RytmStyleSnapshotRoutingPlan",
    "plan_rytm_style_snapshot_routes",
]
