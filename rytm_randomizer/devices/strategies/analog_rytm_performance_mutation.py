"""Snapshot-grounded Analog Rytm performance mutation planning."""

from __future__ import annotations

from dataclasses import dataclass, replace
from random import Random
from types import MappingProxyType
from typing import Final, Literal, TypeAlias

from ...data.analog_rytm_midi import get_machine_src_mappings
from ...data.analog_rytm_style_recipes import (
    AnalogRytmRenderedStyleEvent,
    AnalogRytmStyleRecipe,
    render_analog_rytm_style_recipe,
)
from ...data.rytm_machine_catalog import RYTM_MACHINE_PROFILES, RytmMachineProfile
from .analog_rytm_snapshot_decoder import RytmKitSnapshot

RytmPerformanceMutationMode: TypeAlias = Literal["live-safe", "flow-shift"]
RytmPerformanceMutationDepth: TypeAlias = Literal["safe", "balanced", "studio"]
_ValueRange: TypeAlias = tuple[int, int]
_DEPTH_SAFE: Final[RytmPerformanceMutationDepth] = "safe"
_DEPTH_BALANCED: Final[RytmPerformanceMutationDepth] = "balanced"
_DEPTH_STUDIO: Final[RytmPerformanceMutationDepth] = "studio"

_MACHINE_PROFILE_BY_VALUE = MappingProxyType(
    {profile.machine_value: profile for profile in RYTM_MACHINE_PROFILES}
)


@dataclass(frozen=True)
class RytmPerformanceMutationPlan:
    """Performance-ready Rytm events derived from a captured kit snapshot."""

    snapshot: RytmKitSnapshot
    recipe: AnalogRytmStyleRecipe
    mode: RytmPerformanceMutationMode
    depth: RytmPerformanceMutationDepth
    seed: int
    events: tuple[AnalogRytmRenderedStyleEvent, ...]
    skipped_event_count: int
    machine_switching_allowed: bool
    ready: bool
    readiness_reason: str


def _range_for_depth(
    depth: RytmPerformanceMutationDepth,
    *,
    safe: _ValueRange,
    balanced: _ValueRange,
    studio: _ValueRange,
) -> _ValueRange:
    if depth == _DEPTH_SAFE:
        return safe
    if depth == _DEPTH_BALANCED:
        return balanced
    if depth == _DEPTH_STUDIO:
        return studio
    raise ValueError(f"unknown performance mutation depth: {depth}")


def _window_for_depth(depth: RytmPerformanceMutationDepth) -> int:
    if depth == _DEPTH_SAFE:
        return 6
    if depth == _DEPTH_BALANCED:
        return 14
    if depth == _DEPTH_STUDIO:
        return 32
    raise ValueError(f"unknown performance mutation depth: {depth}")


def _clamped_range(low: int, high: int) -> _ValueRange:
    return max(0, low), min(127, high)


def _anchor_range(
    value: int,
    depth: RytmPerformanceMutationDepth,
    *,
    safe_window: int | None = None,
    balanced_window: int | None = None,
    studio_window: int | None = None,
) -> _ValueRange:
    window = _window_for_depth(depth)
    if depth == _DEPTH_SAFE and safe_window is not None:
        window = safe_window
    if depth == _DEPTH_BALANCED and balanced_window is not None:
        window = balanced_window
    if depth == _DEPTH_STUDIO and studio_window is not None:
        window = studio_window
    return _clamped_range(value - window, value + window)


def _pad_1_kick_range(
    event: AnalogRytmRenderedStyleEvent,
    depth: RytmPerformanceMutationDepth,
) -> _ValueRange | None:
    if event.pad != 1:
        return None

    if event.source == "machine_src" and event.parameter == "Tune":
        return _range_for_depth(
            depth,
            safe=(58, 66),
            balanced=(52, 74),
            studio=(32, 96),
        )
    if event.source == "machine_src" and event.parameter == "Decay":
        return _range_for_depth(
            depth,
            safe=(52, 74),
            balanced=(42, 88),
            studio=(20, 110),
        )
    if event.section == "FILTER" and event.parameter == "Filter Frequency":
        return _anchor_range(
            event.value,
            depth,
            safe_window=4,
            balanced_window=10,
            studio_window=32,
        )
    if event.section == "FILTER" and event.parameter == "Filter Resonance":
        return _range_for_depth(
            depth,
            safe=(0, 24),
            balanced=(0, 40),
            studio=(0, 96),
        )
    if event.section == "AMP" and event.parameter == "Amp Overdrive":
        return _range_for_depth(
            depth,
            safe=(0, 38),
            balanced=(0, 58),
            studio=(0, 96),
        )
    if event.section == "AMP" and event.parameter in {"Amp Delay Send", "Amp Reverb Send"}:
        return _range_for_depth(
            depth,
            safe=(0, 8),
            balanced=(0, 20),
            studio=(0, 64),
        )
    return None


def _guardrail_range_for_event(
    event: AnalogRytmRenderedStyleEvent,
    depth: RytmPerformanceMutationDepth,
) -> _ValueRange:
    pad_1_range = _pad_1_kick_range(event, depth)
    if pad_1_range is not None:
        return pad_1_range

    parameter = event.parameter
    if parameter == "Filter Resonance":
        return _range_for_depth(
            depth,
            safe=_clamped_range(event.value - 4, min(event.value + 4, 30)),
            balanced=_clamped_range(event.value - 10, min(event.value + 10, 48)),
            studio=_clamped_range(event.value - 28, event.value + 28),
        )
    if parameter in {"Amp Delay Send", "Amp Reverb Send"}:
        return _range_for_depth(
            depth,
            safe=_clamped_range(event.value - 6, min(event.value + 6, 38)),
            balanced=_clamped_range(event.value - 14, min(event.value + 14, 58)),
            studio=_clamped_range(event.value - 32, event.value + 32),
        )
    if parameter == "Amp Pan":
        return _anchor_range(
            event.value,
            depth,
            safe_window=8,
            balanced_window=18,
            studio_window=36,
        )
    if "Tune" in parameter:
        return _anchor_range(
            event.value,
            depth,
            safe_window=6,
            balanced_window=14,
            studio_window=30,
        )
    if "Decay" in parameter or parameter in {"Hold", "Hold Time"}:
        return _anchor_range(
            event.value,
            depth,
            safe_window=8,
            balanced_window=18,
            studio_window=36,
        )
    if parameter in {"Waveform", "Mod Type", "Osc Config", "Polarity"}:
        return _anchor_range(
            event.value,
            depth,
            safe_window=2,
            balanced_window=6,
            studio_window=18,
        )
    if any(
        token in parameter
        for token in (
            "Balance",
            "Bend",
            "Detune",
            "FM",
            "Impact",
            "Level",
            "Sweep",
        )
    ):
        return _anchor_range(
            event.value,
            depth,
            safe_window=5,
            balanced_window=12,
            studio_window=28,
        )
    return _anchor_range(event.value, depth)


def _mutated_live_safe_event(
    event: AnalogRytmRenderedStyleEvent,
    rng: Random,
    depth: RytmPerformanceMutationDepth,
) -> AnalogRytmRenderedStyleEvent:
    low, high = _guardrail_range_for_event(event, depth)
    return replace(
        event,
        value=rng.randint(low, high),
        intent=f"{event.intent}; {depth} live-safe seeded guardrail",
    )


def _current_machine_profile(snapshot: RytmKitSnapshot, pad: int) -> RytmMachineProfile | None:
    fact = snapshot.machine_facts.facts_by_pad.get(pad)
    if fact is None or not fact.promoted or fact.decoded_machine_value is None:
        return None
    return _MACHINE_PROFILE_BY_VALUE.get(fact.decoded_machine_value)


def _live_safe_src_event(
    snapshot: RytmKitSnapshot,
    event: AnalogRytmRenderedStyleEvent,
) -> AnalogRytmRenderedStyleEvent | None:
    profile = _current_machine_profile(snapshot, event.pad)
    if profile is None:
        return None

    source_mappings = {
        mapping.parameter: mapping for mapping in get_machine_src_mappings(profile.key)
    }
    mapping = source_mappings.get(event.parameter)
    if mapping is None:
        return None

    return AnalogRytmRenderedStyleEvent(
        pad=event.pad,
        channel=event.channel,
        machine_key=profile.key,
        section="SRC",
        parameter=mapping.parameter,
        cc_msb=mapping.cc_msb,
        value=event.value,
        risk=mapping.risk,
        mutation_status=mapping.mutation_status,
        source="machine_src",
        intent=f"live-safe current {profile.label}: {event.intent}",
    )


def _live_safe_manual_event(
    snapshot: RytmKitSnapshot,
    event: AnalogRytmRenderedStyleEvent,
) -> AnalogRytmRenderedStyleEvent:
    profile = _current_machine_profile(snapshot, event.pad)
    if profile is None:
        return event
    return replace(
        event,
        machine_key=profile.key,
        intent=f"live-safe current {profile.label}: {event.intent}",
    )


def _live_safe_events(
    snapshot: RytmKitSnapshot,
    rendered_events: tuple[AnalogRytmRenderedStyleEvent, ...],
    *,
    depth: RytmPerformanceMutationDepth,
    seed: int,
) -> tuple[tuple[AnalogRytmRenderedStyleEvent, ...], int]:
    rng = Random(seed)  # noqa: S311 - repeatable musical variation, not security randomness.
    events: list[AnalogRytmRenderedStyleEvent] = []
    skipped = 0
    for event in rendered_events:
        if event.parameter == "Track Machine Type":
            skipped += 1
            continue
        if event.source != "machine_src":
            anchored_event = _live_safe_manual_event(snapshot, event)
            events.append(_mutated_live_safe_event(anchored_event, rng, depth))
            continue
        retargeted = _live_safe_src_event(snapshot, event)
        if retargeted is None:
            skipped += 1
            continue
        events.append(_mutated_live_safe_event(retargeted, rng, depth))
    return tuple(events), skipped


def build_rytm_performance_mutation_plan(
    snapshot: RytmKitSnapshot,
    recipe: AnalogRytmStyleRecipe,
    *,
    mode: RytmPerformanceMutationMode,
    depth: RytmPerformanceMutationDepth = "safe",
    seed: int = 0,
) -> RytmPerformanceMutationPlan:
    """Return snapshot-grounded Rytm events for a performance mutation mode."""

    if not isinstance(snapshot, RytmKitSnapshot):
        raise ValueError("build_rytm_performance_mutation_plan: snapshot must be a RytmKitSnapshot")

    rendered_events = render_analog_rytm_style_recipe(recipe)
    if mode == "flow-shift":
        return RytmPerformanceMutationPlan(
            snapshot=snapshot,
            recipe=recipe,
            mode=mode,
            depth=depth,
            seed=seed,
            events=rendered_events,
            skipped_event_count=0,
            machine_switching_allowed=True,
            ready=bool(rendered_events),
            readiness_reason="ready" if rendered_events else "no rendered style events",
        )
    if mode == "live-safe":
        events, skipped = _live_safe_events(
            snapshot,
            rendered_events,
            depth=depth,
            seed=seed,
        )
        return RytmPerformanceMutationPlan(
            snapshot=snapshot,
            recipe=recipe,
            mode=mode,
            depth=depth,
            seed=seed,
            events=events,
            skipped_event_count=skipped,
            machine_switching_allowed=False,
            ready=bool(events),
            readiness_reason="ready" if events else "no live-safe events after filtering",
        )
    raise ValueError(f"unknown performance mutation mode: {mode}")


__all__ = [
    "RytmPerformanceMutationDepth",
    "RytmPerformanceMutationMode",
    "RytmPerformanceMutationPlan",
    "build_rytm_performance_mutation_plan",
]
