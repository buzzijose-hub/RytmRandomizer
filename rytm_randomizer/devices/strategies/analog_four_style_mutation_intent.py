"""Passive style mutation-intent planner for Analog Four snapshots."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ...data.style_discovery import (
    DEFAULT_STYLE_DISCOVERY_AMOUNT,
    style_discovery_policy,
)
from ...data.style_targets import STYLE_TARGET_VECTORS, StyleTargetVector
from .analog_four_snapshot_decoder import AnalogFourKitSnapshot
from .analog_four_style_snapshot_routing import (
    AnalogFourStyleTrackPlan,
    analog_four_style_zone_bias,
    plan_analog_four_style_snapshot_routes,
)

_DRIVE_DIRECTION_ZONES: Final[frozenset[str]] = frozenset({"drive"})
_OSCILLATOR_DIRECTION_ZONES: Final[frozenset[str]] = frozenset({"oscillator"})
_FILTER_DIRECTION_ZONES: Final[frozenset[str]] = frozenset({"filter"})
_ENVELOPE_DIRECTION_ZONES: Final[frozenset[str]] = frozenset({"envelope"})
_MODULATION_DIRECTION_ZONES: Final[frozenset[str]] = frozenset({"modulation"})
_EFFECTS_DIRECTION_ZONES: Final[frozenset[str]] = frozenset({"effects"})


@dataclass(frozen=True)
class AnalogFourStyleMutationIntentRow:
    """One passive zone intent row for a style-routed Analog Four track."""

    zone: str
    mutation_depth: str
    target_bias: int
    target_direction: str


@dataclass(frozen=True)
class AnalogFourStyleMutationTrackIntent:
    """One track's passive style mutation intent."""

    track: int
    role_key: str
    label: str
    route_ready: bool
    readiness_reason: str
    favored_zones: tuple[str, ...]
    mutation_depth: str
    intent_rows: tuple[AnalogFourStyleMutationIntentRow, ...]
    intent_row_count: int


@dataclass(frozen=True)
class AnalogFourStyleMutationIntentPlan:
    """Passive style mutation intent for one captured Analog Four kit snapshot."""

    kit_name: str
    slot: int
    style_key: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    ready_track_count: int
    blocked_track_count: int
    intent_row_count: int
    tracks_by_track: Mapping[int, AnalogFourStyleMutationTrackIntent]


def _zone_direction(zone: str, target: StyleTargetVector) -> str:
    if zone in _FILTER_DIRECTION_ZONES:
        if target.darkness >= 65:
            return "lower"
        if target.darkness <= 35:
            return "higher"
        return "center"
    if zone in _ENVELOPE_DIRECTION_ZONES:
        if target.decay_tail >= 65 and target.transient_density <= 60:
            return "longer"
        if target.decay_tail <= 45 and target.attack_sharpness >= 70:
            return "shorter"
        return "center"
    if zone in _EFFECTS_DIRECTION_ZONES:
        return "longer" if target.space_depth >= 65 or target.decay_tail >= 65 else "center"
    if zone in _MODULATION_DIRECTION_ZONES:
        return "higher" if target.motion_amount >= 65 else "center"
    if zone in _DRIVE_DIRECTION_ZONES:
        drive_pressure = max(
            target.drive_pressure,
            target.industrial_edge,
            target.noise_grit,
            target.warehouse_intensity,
        )
        return "higher" if drive_pressure >= 65 else "center"
    if zone in _OSCILLATOR_DIRECTION_ZONES:
        if target.metallicity >= 65 or target.motion_amount >= 75:
            return "higher"
        if target.low_end_weight >= 85 and target.metallicity <= 45:
            return "lower"
        return "center"
    return "center"


def _intent_rows_for_track(
    track_plan: AnalogFourStyleTrackPlan,
    *,
    mutation_depth: str,
    target: StyleTargetVector,
) -> tuple[AnalogFourStyleMutationIntentRow, ...]:
    return tuple(
        AnalogFourStyleMutationIntentRow(
            zone=zone,
            mutation_depth=mutation_depth,
            target_bias=analog_four_style_zone_bias(target, zone),
            target_direction=_zone_direction(zone, target),
        )
        for zone in track_plan.favored_zones
    )


def _track_intent(
    track_plan: AnalogFourStyleTrackPlan,
    *,
    mutation_depth: str,
    target: StyleTargetVector,
) -> AnalogFourStyleMutationTrackIntent:
    rows = _intent_rows_for_track(
        track_plan,
        mutation_depth=mutation_depth,
        target=target,
    )
    return AnalogFourStyleMutationTrackIntent(
        track=track_plan.track,
        role_key=track_plan.role_key,
        label=track_plan.label,
        route_ready=track_plan.route_ready,
        readiness_reason=track_plan.readiness_reason,
        favored_zones=track_plan.favored_zones,
        mutation_depth=mutation_depth,
        intent_rows=rows,
        intent_row_count=len(rows),
    )


def plan_analog_four_style_mutation_intent(
    snapshot: AnalogFourKitSnapshot,
    style_key: str,
    *,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> AnalogFourStyleMutationIntentPlan:
    """Return passive style mutation intent rows for one A4 snapshot."""

    policy = style_discovery_policy(discovery_amount)
    routing_plan = plan_analog_four_style_snapshot_routes(
        snapshot,
        style_key,
        discovery_amount=discovery_amount,
    )
    target = STYLE_TARGET_VECTORS[routing_plan.style_key]
    tracks = {
        track: _track_intent(
            track_plan,
            mutation_depth=policy.mutation_depth,
            target=target,
        )
        for track, track_plan in routing_plan.tracks_by_track.items()
    }
    intent_row_count = sum(track.intent_row_count for track in tracks.values())
    return AnalogFourStyleMutationIntentPlan(
        kit_name=routing_plan.kit_name,
        slot=routing_plan.slot,
        style_key=routing_plan.style_key,
        discovery_amount=routing_plan.discovery_amount,
        discovery_band=routing_plan.discovery_band,
        mutation_depth=policy.mutation_depth,
        ready_track_count=routing_plan.ready_track_count,
        blocked_track_count=routing_plan.blocked_track_count,
        intent_row_count=intent_row_count,
        tracks_by_track=MappingProxyType(tracks),
    )


__all__ = [
    "AnalogFourStyleMutationIntentPlan",
    "AnalogFourStyleMutationIntentRow",
    "AnalogFourStyleMutationTrackIntent",
    "plan_analog_four_style_mutation_intent",
]
