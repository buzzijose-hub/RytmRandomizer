"""Passive mock preview for Rytm style mutation render plans."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ...data.style_discovery import DEFAULT_STYLE_DISCOVERY_AMOUNT
from ...mock_midi import MidiMessage
from .analog_rytm_message_renderer import AnalogRytmMessageRenderer
from .analog_rytm_mutation_planner import RytmMutationPlan, RytmPlanEvent
from .analog_rytm_snapshot_decoder import RytmKitSnapshot
from .analog_rytm_style_mutation_render_plan import (
    RytmStyleMutationRenderEvent,
    RytmStyleMutationRenderPlan,
    plan_rytm_style_mutation_render_plan,
)

_DEPTH_VALUES: Final[Mapping[str, int]] = MappingProxyType(
    {
        "micro": 1,
        "groove": 2,
        "strong": 5,
        "wild": 7,
    }
)


@dataclass(frozen=True)
class RytmStyleMutationMockPreviewEvent:
    """One passive mock CC row resolved from a style render-plan event."""

    pad: int
    profile_key: str
    zone: str
    parameter: str
    channel: int
    control: int
    value: int
    target_value: int
    window_low: int
    window_high: int
    mutation_depth: str
    target_direction: str


@dataclass(frozen=True)
class RytmStyleMutationMockPreview:
    """Mock-safe style mutation preview for one captured Rytm kit."""

    kit_name: str
    slot: int
    style_key: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    preview_ready: bool
    readiness_reason: str
    ready_pad_count: int
    blocked_pad_count: int
    render_event_count: int
    mock_message_count: int
    planned_pads: tuple[int, ...]
    event_rows: tuple[RytmStyleMutationMockPreviewEvent, ...]


def _metadata_int(message: MidiMessage, key: str) -> int:
    value = message.metadata.get(key)
    if not isinstance(value, int):
        raise TypeError(f"mock message metadata {key!r} must be an int")
    return value


def _metadata_str(message: MidiMessage, key: str) -> str:
    value = message.metadata.get(key)
    if not isinstance(value, str):
        raise TypeError(f"mock message metadata {key!r} must be a str")
    return value


def _mutation_depth_value(depth: str) -> int:
    return _DEPTH_VALUES.get(depth, 2)


def _plan_events(
    render_plan: RytmStyleMutationRenderPlan,
) -> tuple[tuple[RytmPlanEvent, RytmStyleMutationRenderEvent], ...]:
    pairs: list[tuple[RytmPlanEvent, RytmStyleMutationRenderEvent]] = []
    for pad in sorted(render_plan.pads_by_pad):
        pad_plan = render_plan.pads_by_pad[pad]
        if not pad_plan.render_ready or pad_plan.profile_key is None:
            continue
        for render_event in pad_plan.render_events:
            pairs.append(
                (
                    RytmPlanEvent(
                        pad=pad_plan.pad,
                        profile_key=pad_plan.profile_key,
                        parameter=render_event.parameter,
                        value=render_event.target_value,
                    ),
                    render_event,
                )
            )
    return tuple(pairs)


def _event_row(
    *,
    message: MidiMessage,
    render_event: RytmStyleMutationRenderEvent,
) -> RytmStyleMutationMockPreviewEvent:
    return RytmStyleMutationMockPreviewEvent(
        pad=_metadata_int(message, "pad"),
        profile_key=_metadata_str(message, "profile_key"),
        zone=render_event.zone,
        parameter=_metadata_str(message, "parameter"),
        channel=message.channel,
        control=message.control,
        value=message.value,
        target_value=render_event.target_value,
        window_low=render_event.window_low,
        window_high=render_event.window_high,
        mutation_depth=render_event.mutation_depth,
        target_direction=render_event.target_direction,
    )


def _render_mock_rows(
    *,
    snapshot: RytmKitSnapshot,
    render_plan: RytmStyleMutationRenderPlan,
) -> tuple[RytmStyleMutationMockPreviewEvent, ...]:
    pairs = _plan_events(render_plan)
    if not pairs:
        return ()

    mutation_plan = RytmMutationPlan(
        snapshot=snapshot,
        depth=_mutation_depth_value(render_plan.mutation_depth),
        events=tuple(plan_event for plan_event, render_event in pairs),
        ready=True,
        readiness_reason="",
    )
    renderer = AnalogRytmMessageRenderer()
    messages = tuple(
        renderer.to_mock_message(plan_event, mutation_plan) for plan_event, render_event in pairs
    )
    return tuple(
        _event_row(message=message, render_event=render_event)
        for message, (plan_event, render_event) in zip(messages, pairs, strict=True)
    )


def build_rytm_style_mutation_mock_preview(
    snapshot: RytmKitSnapshot,
    style_key: str,
    *,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> RytmStyleMutationMockPreview:
    """Return passive mock CC rows for a Rytm style mutation render plan."""

    render_plan = plan_rytm_style_mutation_render_plan(
        snapshot,
        style_key,
        discovery_amount=discovery_amount,
    )
    rows = _render_mock_rows(snapshot=snapshot, render_plan=render_plan)
    planned_pads = tuple(sorted({row.pad for row in rows}))
    preview_ready = bool(rows)
    return RytmStyleMutationMockPreview(
        kit_name=render_plan.kit_name,
        slot=render_plan.slot,
        style_key=render_plan.style_key,
        discovery_amount=render_plan.discovery_amount,
        discovery_band=render_plan.discovery_band,
        mutation_depth=render_plan.mutation_depth,
        preview_ready=preview_ready,
        readiness_reason="ready" if preview_ready else "no style render events available",
        ready_pad_count=render_plan.ready_pad_count,
        blocked_pad_count=render_plan.blocked_pad_count,
        render_event_count=render_plan.render_event_count,
        mock_message_count=len(rows),
        planned_pads=planned_pads,
        event_rows=rows,
    )


__all__ = [
    "RytmStyleMutationMockPreview",
    "RytmStyleMutationMockPreviewEvent",
    "build_rytm_style_mutation_mock_preview",
]
