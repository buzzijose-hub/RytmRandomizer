"""Passive style-aware Analog Four snapshot routing helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ...data.style_discovery import (
    DEFAULT_STYLE_DISCOVERY_AMOUNT,
    StyleDiscoveryPolicy,
    style_discovery_policy,
)
from ...data.style_profiles import STYLE_PROFILES
from ...data.style_targets import STYLE_TARGET_VECTORS, StyleTargetVector
from .analog_four_snapshot_decoder import AnalogFourKitSnapshot

_ZONE_AXIS_WEIGHTS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "drive": (
            "drive_pressure",
            "industrial_edge",
            "warehouse_intensity",
            "noise_grit",
        ),
        "oscillator": (
            "low_end_weight",
            "tonal_center_weight",
            "metallicity",
            "noise_grit",
        ),
        "filter": (
            "darkness",
            "drive_pressure",
            "space_depth",
        ),
        "envelope": (
            "transient_density",
            "attack_sharpness",
            "decay_tail",
        ),
        "modulation": (
            "motion_amount",
            "repetition_hypnosis",
            "space_depth",
        ),
        "effects": (
            "space_depth",
            "decay_tail",
            "darkness",
        ),
    }
)

_TRACK_ROLE_AXIS_WEIGHTS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "bass_foundation": (
            "low_end_weight",
            "drive_pressure",
            "tonal_center_weight",
        ),
        "stab_pulse": (
            "transient_density",
            "attack_sharpness",
            "repetition_hypnosis",
        ),
        "texture_motion": (
            "motion_amount",
            "noise_grit",
            "metallicity",
        ),
        "space_accent": (
            "space_depth",
            "decay_tail",
            "darkness",
        ),
    }
)

_TRACK_ROLES: Final[Mapping[int, tuple[str, str]]] = MappingProxyType(
    {
        1: ("bass_foundation", "Bass / low pulse"),
        2: ("stab_pulse", "Stab / pulse"),
        3: ("texture_motion", "Texture / motion"),
        4: ("space_accent", "Space / accent"),
    }
)

_MAX_FAVORED_ZONES: Final[int] = 4


@dataclass(frozen=True)
class AnalogFourStyleTrackPlan:
    """One track's passive style-aware routing preview."""

    track: int
    role_key: str
    label: str
    route_ready: bool
    readiness_reason: str
    discovery_band: str
    favored_zones: tuple[str, ...]
    score: int


@dataclass(frozen=True)
class AnalogFourStyleSnapshotRoutingPlan:
    """Passive style-aware routing plan for one Analog Four kit snapshot."""

    kit_name: str
    slot: int
    style_key: str
    style_focus: tuple[str, ...]
    discovery_amount: int
    discovery_band: str
    machine_switching_allowed: bool
    favored_zones: tuple[str, ...]
    ready_track_count: int
    blocked_track_count: int
    partial_snapshot_mutation_ready: bool
    tracks_by_track: Mapping[int, AnalogFourStyleTrackPlan]


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
    return tuple(zone for zone, score in scored if score >= 150)[
        : min(policy.zone_limit, _MAX_FAVORED_ZONES)
    ]


def _track_score(role_key: str, target: StyleTargetVector) -> int:
    return _axis_sum(target, _TRACK_ROLE_AXIS_WEIGHTS[role_key])


def _track_plan(
    *,
    track: int,
    target: StyleTargetVector,
    policy: StyleDiscoveryPolicy,
    favored_zones: tuple[str, ...],
    offsets_promoted: bool,
) -> AnalogFourStyleTrackPlan:
    role_key, label = _TRACK_ROLES[track]
    return AnalogFourStyleTrackPlan(
        track=track,
        role_key=role_key,
        label=label,
        route_ready=offsets_promoted,
        readiness_reason=("" if offsets_promoted else "Analog Four offsets are candidate-only"),
        discovery_band=policy.band,
        favored_zones=favored_zones,
        score=_track_score(role_key, target),
    )


def plan_analog_four_style_snapshot_routes(
    snapshot: AnalogFourKitSnapshot,
    style_key: str,
    *,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> AnalogFourStyleSnapshotRoutingPlan:
    """Return a passive style-aware routing preview for one Analog Four snapshot."""

    if not isinstance(snapshot, AnalogFourKitSnapshot):
        raise ValueError(
            "plan_analog_four_style_snapshot_routes: snapshot must be an "
            f"AnalogFourKitSnapshot, got {type(snapshot).__name__}"
        )
    normalized_key = style_key.strip().lower()
    target = STYLE_TARGET_VECTORS.get(normalized_key)
    profile = STYLE_PROFILES.get(normalized_key)
    if target is None or profile is None:
        raise ValueError(f"Unknown style target key: {style_key}")

    policy = style_discovery_policy(discovery_amount)
    favored_zones = _favored_zones(target, policy=policy)
    tracks = {
        track: _track_plan(
            track=track,
            target=target,
            policy=policy,
            favored_zones=favored_zones,
            offsets_promoted=snapshot.offsets_promoted,
        )
        for track in sorted(_TRACK_ROLES)
    }
    ready_count = sum(1 for track_plan in tracks.values() if track_plan.route_ready)
    return AnalogFourStyleSnapshotRoutingPlan(
        kit_name=snapshot.kit_name,
        slot=snapshot.slot,
        style_key=normalized_key,
        style_focus=profile.analog_four_focus,
        discovery_amount=policy.amount,
        discovery_band=policy.band,
        machine_switching_allowed=policy.machine_switching_allowed,
        favored_zones=favored_zones,
        ready_track_count=ready_count,
        blocked_track_count=len(tracks) - ready_count,
        partial_snapshot_mutation_ready=ready_count > 0,
        tracks_by_track=MappingProxyType(tracks),
    )


__all__ = [
    "AnalogFourStyleSnapshotRoutingPlan",
    "AnalogFourStyleTrackPlan",
    "plan_analog_four_style_snapshot_routes",
]
