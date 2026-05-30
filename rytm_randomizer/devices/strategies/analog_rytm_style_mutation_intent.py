"""Passive style mutation-intent planner for Analog Rytm snapshots."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ...data.profiles import PROFILES
from ...data.style_discovery import (
    DEFAULT_STYLE_DISCOVERY_AMOUNT,
    style_discovery_policy,
)
from ...data.style_targets import STYLE_TARGET_VECTORS, StyleTargetVector
from .analog_rytm_snapshot_decoder import RytmKitSnapshot
from .analog_rytm_style_snapshot_routing import (
    RytmStyleSnapshotPadPlan,
    plan_rytm_style_snapshot_routes,
)

_ZONE_PARAMETER_PREFIXES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "body": ("SRC Tune", "SRC Decay", "SRC Hold", "AMP Decay"),
        "amp": ("AMP Attack", "AMP Hold", "AMP Decay", "AMP Overdrive"),
        "filter": (
            "FLT Frequency",
            "FLT Resonance",
            "FLT Env Depth",
            "FLT Decay",
        ),
        "grit": (
            "AMP Overdrive",
            "SRC Snap",
            "SRC Transient",
            "SRC Noise Level",
            "SRC Impact",
        ),
        "lfo": ("LFO Speed", "LFO Depth", "LFO Fade", "LFO Destination"),
        "morph": (
            "SRC Balance",
            "SRC Detune",
            "SRC Osc 1 Wave",
            "SRC Osc 2 Wave",
        ),
    }
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

_GRIT_DIRECTION_PREFIXES: Final[tuple[str, ...]] = (
    "AMP Overdrive",
    "FLT Resonance",
    "SRC Snap",
    "SRC Transient",
    "SRC Noise",
    "SRC Tick",
    "SRC Impact",
    "SRC VCO Click",
    "SRC Dust",
    "SRC FM Amount",
)
_LFO_DIRECTION_ZONES: Final[frozenset[str]] = frozenset({"lfo"})
_GRIT_DIRECTION_ZONES: Final[frozenset[str]] = frozenset({"grit"})
_AMP_DIRECTION_ZONES: Final[frozenset[str]] = frozenset({"amp"})
_MORPH_DIRECTION_ZONES: Final[frozenset[str]] = frozenset({"morph"})


@dataclass(frozen=True)
class RytmStyleMutationIntentRow:
    """One passive parameter intent row for a style-routed Rytm pad."""

    zone: str
    parameter: str
    low: int
    high: int
    mutation_depth: str
    target_bias: int
    target_direction: str


@dataclass(frozen=True)
class RytmStyleMutationPadIntent:
    """One pad's passive style mutation intent."""

    pad: int
    track_code: str
    label: str
    current_machine_key: str | None
    profile_key: str | None
    route_ready: bool
    readiness_reason: str
    favored_zones: tuple[str, ...]
    intent_rows: tuple[RytmStyleMutationIntentRow, ...]
    intent_row_count: int


@dataclass(frozen=True)
class RytmStyleMutationIntentPlan:
    """Passive style mutation intent for one captured Rytm kit snapshot."""

    kit_name: str
    slot: int
    style_key: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    ready_pad_count: int
    blocked_pad_count: int
    intent_row_count: int
    pads_by_pad: Mapping[int, RytmStyleMutationPadIntent]


def _matches_zone(parameter: str, *, zone: str) -> bool:
    prefixes = _ZONE_PARAMETER_PREFIXES.get(zone, ())
    return any(parameter.startswith(prefix) for prefix in prefixes)


def _zone_bias(target: StyleTargetVector, zone: str) -> int:
    axes = _ZONE_AXIS_WEIGHTS.get(zone)
    if axes is None:
        return 50
    values = target.as_mapping()
    return round(sum(values[axis] for axis in axes) / len(axes))


def _parameter_direction(
    parameter: str,
    *,
    zone: str,
    target: StyleTargetVector,
) -> str:
    if parameter == "FLT Frequency":
        if target.darkness >= 65:
            return "lower"
        if target.darkness <= 35:
            return "higher"
        return "center"
    if "Decay" in parameter or "Hold" in parameter:
        if target.decay_tail >= 65 and target.transient_density <= 60:
            return "longer"
        if target.decay_tail <= 35 and target.attack_sharpness >= 70:
            return "shorter"
        return "center"
    if zone in _LFO_DIRECTION_ZONES or parameter.startswith("LFO "):
        return "higher" if target.motion_amount >= 65 else "center"
    if zone in _GRIT_DIRECTION_ZONES or parameter.startswith(_GRIT_DIRECTION_PREFIXES):
        grit_pressure = max(
            target.noise_grit,
            target.drive_pressure,
            target.industrial_edge,
            target.metallicity,
        )
        return "higher" if grit_pressure >= 65 else "center"
    if zone in _AMP_DIRECTION_ZONES:
        return (
            "higher"
            if target.drive_pressure >= 70 or target.warehouse_intensity >= 80
            else "center"
        )
    if zone in _MORPH_DIRECTION_ZONES:
        return "higher" if target.motion_amount >= 65 or target.metallicity >= 65 else "center"
    return "center"


def _intent_rows_for_pad(
    pad_plan: RytmStyleSnapshotPadPlan,
    *,
    mutation_depth: str,
    target: StyleTargetVector,
) -> tuple[RytmStyleMutationIntentRow, ...]:
    if not pad_plan.route_ready or pad_plan.profile_key is None:
        return ()

    profile = PROFILES.get(pad_plan.profile_key)
    if profile is None:
        return ()

    rows: list[RytmStyleMutationIntentRow] = []
    seen_parameters: set[str] = set()
    safe_table = profile["safe"]
    for zone in pad_plan.favored_zones:
        for parameter, (low, high) in safe_table.items():
            if parameter in seen_parameters:
                continue
            if _matches_zone(parameter, zone=zone):
                rows.append(
                    RytmStyleMutationIntentRow(
                        zone=zone,
                        parameter=parameter,
                        low=low,
                        high=high,
                        mutation_depth=mutation_depth,
                        target_bias=_zone_bias(target, zone),
                        target_direction=_parameter_direction(
                            parameter,
                            zone=zone,
                            target=target,
                        ),
                    )
                )
                seen_parameters.add(parameter)
    return tuple(rows)


def _pad_intent(
    pad_plan: RytmStyleSnapshotPadPlan,
    *,
    mutation_depth: str,
    target: StyleTargetVector,
) -> RytmStyleMutationPadIntent:
    rows = _intent_rows_for_pad(
        pad_plan,
        mutation_depth=mutation_depth,
        target=target,
    )
    return RytmStyleMutationPadIntent(
        pad=pad_plan.pad,
        track_code=pad_plan.track_code,
        label=pad_plan.label,
        current_machine_key=pad_plan.current_machine_key,
        profile_key=pad_plan.profile_key,
        route_ready=pad_plan.route_ready,
        readiness_reason=pad_plan.readiness_reason,
        favored_zones=pad_plan.favored_zones,
        intent_rows=rows,
        intent_row_count=len(rows),
    )


def plan_rytm_style_mutation_intent(
    snapshot: RytmKitSnapshot,
    style_key: str,
    *,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> RytmStyleMutationIntentPlan:
    """Return passive style mutation intent rows for one Rytm snapshot."""

    policy = style_discovery_policy(discovery_amount)
    routing_plan = plan_rytm_style_snapshot_routes(
        snapshot,
        style_key,
        discovery_amount=discovery_amount,
    )
    target = STYLE_TARGET_VECTORS[style_key]
    pads = {
        pad: _pad_intent(
            pad_plan,
            mutation_depth=policy.mutation_depth,
            target=target,
        )
        for pad, pad_plan in routing_plan.pads_by_pad.items()
    }
    intent_row_count = sum(pad.intent_row_count for pad in pads.values())
    return RytmStyleMutationIntentPlan(
        kit_name=routing_plan.kit_name,
        slot=routing_plan.slot,
        style_key=routing_plan.style_key,
        discovery_amount=routing_plan.discovery_amount,
        discovery_band=routing_plan.discovery_band,
        mutation_depth=policy.mutation_depth,
        ready_pad_count=routing_plan.ready_pad_count,
        blocked_pad_count=routing_plan.blocked_pad_count,
        intent_row_count=intent_row_count,
        pads_by_pad=MappingProxyType(pads),
    )


__all__ = [
    "RytmStyleMutationIntentPlan",
    "RytmStyleMutationIntentRow",
    "RytmStyleMutationPadIntent",
    "plan_rytm_style_mutation_intent",
]
