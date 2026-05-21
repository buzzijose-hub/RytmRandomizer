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


@dataclass(frozen=True)
class RytmStyleMutationIntentRow:
    """One passive parameter intent row for a style-routed Rytm pad."""

    zone: str
    parameter: str
    low: int
    high: int
    mutation_depth: str


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


def _intent_rows_for_pad(
    pad_plan: RytmStyleSnapshotPadPlan,
    *,
    mutation_depth: str,
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
                    )
                )
                seen_parameters.add(parameter)
    return tuple(rows)


def _pad_intent(
    pad_plan: RytmStyleSnapshotPadPlan,
    *,
    mutation_depth: str,
) -> RytmStyleMutationPadIntent:
    rows = _intent_rows_for_pad(pad_plan, mutation_depth=mutation_depth)
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
    pads = {
        pad: _pad_intent(pad_plan, mutation_depth=policy.mutation_depth)
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
