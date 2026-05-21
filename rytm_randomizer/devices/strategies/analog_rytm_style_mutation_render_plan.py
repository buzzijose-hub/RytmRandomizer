"""Passive Rytm style mutation render-plan envelopes.

This strategy is the bridge between style mutation intent and future MIDI
rendering. It turns ready intent rows into deterministic target-value
windows, but it does not resolve CC numbers, render mock messages, open MIDI
ports, or send hardware messages.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ...data.style_discovery import (
    DEFAULT_STYLE_DISCOVERY_AMOUNT,
)
from .analog_rytm_snapshot_decoder import RytmKitSnapshot
from .analog_rytm_style_mutation_intent import (
    RytmStyleMutationIntentPlan,
    RytmStyleMutationIntentRow,
    RytmStyleMutationPadIntent,
    plan_rytm_style_mutation_intent,
)

_DEPTH_WINDOW_FRACTIONS: Final[Mapping[str, tuple[int, int]]] = MappingProxyType(
    {
        "micro": (15, 100),
        "groove": (35, 100),
        "strong": (60, 100),
        "wild": (100, 100),
    }
)
_LOWER_DIRECTIONS: Final[frozenset[str]] = frozenset({"lower", "shorter"})
_HIGHER_DIRECTIONS: Final[frozenset[str]] = frozenset({"higher", "longer"})


@dataclass(frozen=True)
class RytmStyleMutationRenderEvent:
    """One passive target-value window for a Rytm style mutation row."""

    zone: str
    parameter: str
    low: int
    high: int
    mutation_depth: str
    target_bias: int
    target_direction: str
    target_value: int
    window_low: int
    window_high: int


@dataclass(frozen=True)
class RytmStyleMutationRenderPadPlan:
    """One pad's passive style mutation render-plan envelope."""

    pad: int
    track_code: str
    label: str
    current_machine_key: str | None
    profile_key: str | None
    route_ready: bool
    render_ready: bool
    readiness_reason: str
    favored_zones: tuple[str, ...]
    render_events: tuple[RytmStyleMutationRenderEvent, ...]
    render_event_count: int


@dataclass(frozen=True)
class RytmStyleMutationRenderPlan:
    """Passive style render-plan envelope for one captured Rytm snapshot."""

    kit_name: str
    slot: int
    style_key: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    render_ready: bool
    ready_pad_count: int
    blocked_pad_count: int
    render_event_count: int
    pads_by_pad: Mapping[int, RytmStyleMutationRenderPadPlan]


def _target_percent(row: RytmStyleMutationIntentRow) -> int:
    if row.target_direction in _LOWER_DIRECTIONS:
        return 100 - row.target_bias
    if row.target_direction in _HIGHER_DIRECTIONS:
        return row.target_bias
    return 50


def _target_value(row: RytmStyleMutationIntentRow) -> int:
    span = row.high - row.low
    if span <= 0:
        return row.low
    return row.low + round((span * _target_percent(row)) / 100)


def _window_radius(row: RytmStyleMutationIntentRow) -> int:
    span = row.high - row.low
    if span <= 0:
        return 0
    numerator, denominator = _DEPTH_WINDOW_FRACTIONS.get(row.mutation_depth, (35, 100))
    return (span * numerator + denominator) // (2 * denominator)


def _render_event(row: RytmStyleMutationIntentRow) -> RytmStyleMutationRenderEvent:
    target_value = _target_value(row)
    radius = _window_radius(row)
    return RytmStyleMutationRenderEvent(
        zone=row.zone,
        parameter=row.parameter,
        low=row.low,
        high=row.high,
        mutation_depth=row.mutation_depth,
        target_bias=row.target_bias,
        target_direction=row.target_direction,
        target_value=target_value,
        window_low=max(row.low, target_value - radius),
        window_high=min(row.high, target_value + radius),
    )


def _pad_render_plan(
    pad_intent: RytmStyleMutationPadIntent,
) -> RytmStyleMutationRenderPadPlan:
    events = tuple(_render_event(row) for row in pad_intent.intent_rows)
    render_ready = pad_intent.route_ready and bool(events)
    return RytmStyleMutationRenderPadPlan(
        pad=pad_intent.pad,
        track_code=pad_intent.track_code,
        label=pad_intent.label,
        current_machine_key=pad_intent.current_machine_key,
        profile_key=pad_intent.profile_key,
        route_ready=pad_intent.route_ready,
        render_ready=render_ready,
        readiness_reason=pad_intent.readiness_reason if not render_ready else "ready",
        favored_zones=pad_intent.favored_zones,
        render_events=events,
        render_event_count=len(events),
    )


def plan_rytm_style_mutation_render_plan(
    snapshot_or_intent: RytmKitSnapshot | RytmStyleMutationIntentPlan,
    style_key: str,
    *,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> RytmStyleMutationRenderPlan:
    """Return passive style mutation target-value envelopes for a Rytm snapshot."""

    intent_plan = (
        snapshot_or_intent
        if isinstance(snapshot_or_intent, RytmStyleMutationIntentPlan)
        else plan_rytm_style_mutation_intent(
            snapshot_or_intent,
            style_key,
            discovery_amount=discovery_amount,
        )
    )
    pads = {
        pad: _pad_render_plan(pad_intent) for pad, pad_intent in intent_plan.pads_by_pad.items()
    }
    render_event_count = sum(pad.render_event_count for pad in pads.values())
    ready_pad_count = sum(1 for pad in pads.values() if pad.render_ready)
    return RytmStyleMutationRenderPlan(
        kit_name=intent_plan.kit_name,
        slot=intent_plan.slot,
        style_key=intent_plan.style_key,
        discovery_amount=intent_plan.discovery_amount,
        discovery_band=intent_plan.discovery_band,
        mutation_depth=intent_plan.mutation_depth,
        render_ready=render_event_count > 0,
        ready_pad_count=ready_pad_count,
        blocked_pad_count=len(pads) - ready_pad_count,
        render_event_count=render_event_count,
        pads_by_pad=MappingProxyType(pads),
    )


__all__ = [
    "RytmStyleMutationRenderEvent",
    "RytmStyleMutationRenderPadPlan",
    "RytmStyleMutationRenderPlan",
    "plan_rytm_style_mutation_render_plan",
]
