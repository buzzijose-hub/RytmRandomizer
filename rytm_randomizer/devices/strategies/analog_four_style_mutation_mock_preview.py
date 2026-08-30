"""Passive mock preview for Analog Four style mutation intent."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ...data.style_discovery import DEFAULT_STYLE_DISCOVERY_AMOUNT
from ...mock_midi import MidiMessage
from .analog_four_message_renderer import AnalogFourMessageRenderer
from .analog_four_mutation_planner import AnalogFourMutationPlan, AnalogFourPlanEvent
from .analog_four_offset_manifest import A4_SNAPSHOT_LAYOUT_SAVED_KIT
from .analog_four_snapshot_decoder import AnalogFourKitSnapshot
from .analog_four_style_mutation_intent import (
    AnalogFourStyleMutationIntentPlan,
    AnalogFourStyleMutationIntentRow,
    AnalogFourStyleMutationTrackIntent,
    plan_analog_four_style_mutation_intent,
)
from .analog_four_track_domain import AnalogFourTrackDomain

_DEPTH_VALUES: Final[Mapping[str, int]] = MappingProxyType(
    {
        "micro": 1,
        "groove": 2,
        "strong": 5,
        "wild": 7,
    }
)
_ZONE_CC_TARGETS: Final[Mapping[str, tuple[str, int]]] = MappingProxyType(
    {
        "oscillator": ("OSC1 Level", 69),
        "filter": ("Filter 1 Frequency", 18),
        "envelope": ("Amp Env Decay", 105),
        "modulation": ("LFO1 Speed", 116),
        "effects": ("Amp Delay Send", 92),
    }
)
_NRPN_ONLY_REASON: Final[str] = "NRPN-only A4 zone; no CC mock row rendered"
_CANDIDATE_ONLY_REASON: Final[str] = "Analog Four offsets are candidate-only"
_CANDIDATE_PREVIEW_REASON: Final[str] = (
    "Analog Four offsets are candidate-only; promote offsets before mock CC preview"
)
_SAVED_KIT_PREVIEW_REASON: Final[str] = (
    "Analog Four saved-kit SysEx decoded; offsets remain candidate-only; "
    "promote offsets before mock CC preview"
)


@dataclass(frozen=True)
class AnalogFourStyleMutationMockPreviewEvent:
    """One passive mock CC row resolved from an A4 style intent row."""

    track: int
    role_key: str
    zone: str
    parameter: str
    channel: int
    control: int
    value: int
    target_bias: int
    mutation_depth: str
    target_direction: str


@dataclass(frozen=True)
class AnalogFourStyleMutationMockPreviewDeferredRow:
    """One A4 style intent row that cannot be rendered as a mock CC row yet."""

    track: int
    role_key: str
    zone: str
    target_bias: int
    mutation_depth: str
    target_direction: str
    reason: str


@dataclass(frozen=True)
class AnalogFourStyleMutationMockPreview:
    """Mock-safe style mutation preview for one captured Analog Four kit."""

    kit_name: str
    slot: int
    snapshot_layout: str
    style_key: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    preview_ready: bool
    readiness_reason: str
    ready_track_count: int
    blocked_track_count: int
    intent_row_count: int
    mock_message_count: int
    deferred_row_count: int
    planned_tracks: tuple[int, ...]
    event_rows: tuple[AnalogFourStyleMutationMockPreviewEvent, ...]
    deferred_rows: tuple[AnalogFourStyleMutationMockPreviewDeferredRow, ...]


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


def _target_value(row: AnalogFourStyleMutationIntentRow) -> int:
    if row.target_direction in {"lower", "shorter"}:
        return max(0, min(127, 127 - row.target_bias))
    if row.target_direction == "center":
        return 64
    return max(0, min(127, row.target_bias))


def _deferred_row(
    *,
    track_intent: AnalogFourStyleMutationTrackIntent,
    intent_row: AnalogFourStyleMutationIntentRow,
    reason: str,
) -> AnalogFourStyleMutationMockPreviewDeferredRow:
    return AnalogFourStyleMutationMockPreviewDeferredRow(
        track=track_intent.track,
        role_key=track_intent.role_key,
        zone=intent_row.zone,
        target_bias=intent_row.target_bias,
        mutation_depth=intent_row.mutation_depth,
        target_direction=intent_row.target_direction,
        reason=reason,
    )


def _plan_pairs(
    intent_plan: AnalogFourStyleMutationIntentPlan,
) -> tuple[
    tuple[
        AnalogFourPlanEvent,
        AnalogFourStyleMutationTrackIntent,
        AnalogFourStyleMutationIntentRow,
    ],
    ...,
]:
    pairs: list[
        tuple[
            AnalogFourPlanEvent,
            AnalogFourStyleMutationTrackIntent,
            AnalogFourStyleMutationIntentRow,
        ]
    ] = []
    for track in sorted(intent_plan.tracks_by_track):
        track_intent = intent_plan.tracks_by_track[track]
        if not track_intent.route_ready:
            continue
        for intent_row in track_intent.intent_rows:
            target = _ZONE_CC_TARGETS.get(intent_row.zone)
            if target is None:
                continue
            parameter, control = target
            pairs.append(
                (
                    AnalogFourPlanEvent(
                        track=track_intent.track,
                        parameter=parameter,
                        control=control,
                        value=_target_value(intent_row),
                    ),
                    track_intent,
                    intent_row,
                )
            )
    return tuple(pairs)


def _deferred_rows(
    intent_plan: AnalogFourStyleMutationIntentPlan,
    *,
    reason_for_all: str | None,
) -> tuple[AnalogFourStyleMutationMockPreviewDeferredRow, ...]:
    rows: list[AnalogFourStyleMutationMockPreviewDeferredRow] = []
    for track in sorted(intent_plan.tracks_by_track):
        track_intent = intent_plan.tracks_by_track[track]
        for intent_row in track_intent.intent_rows:
            reason = reason_for_all
            if reason is None and intent_row.zone not in _ZONE_CC_TARGETS:
                reason = _NRPN_ONLY_REASON
            if reason is not None:
                rows.append(
                    _deferred_row(
                        track_intent=track_intent,
                        intent_row=intent_row,
                        reason=reason,
                    )
                )
    return tuple(rows)


def _event_row(
    *,
    message: MidiMessage,
    track_intent: AnalogFourStyleMutationTrackIntent,
    intent_row: AnalogFourStyleMutationIntentRow,
) -> AnalogFourStyleMutationMockPreviewEvent:
    return AnalogFourStyleMutationMockPreviewEvent(
        track=_metadata_int(message, "track"),
        role_key=track_intent.role_key,
        zone=intent_row.zone,
        parameter=_metadata_str(message, "parameter"),
        channel=message.channel,
        control=message.control,
        value=message.value,
        target_bias=intent_row.target_bias,
        mutation_depth=intent_row.mutation_depth,
        target_direction=intent_row.target_direction,
    )


def _render_mock_rows(
    *,
    snapshot: AnalogFourKitSnapshot,
    intent_plan: AnalogFourStyleMutationIntentPlan,
) -> tuple[AnalogFourStyleMutationMockPreviewEvent, ...]:
    pairs = _plan_pairs(intent_plan)
    if not pairs:
        return ()

    mutation_plan = AnalogFourMutationPlan(
        snapshot=snapshot,
        depth=_mutation_depth_value(intent_plan.mutation_depth),
        events=tuple(plan_event for plan_event, _track_intent, _intent_row in pairs),
        ready=True,
        readiness_reason="",
    )
    renderer = AnalogFourMessageRenderer(
        track_domain=AnalogFourTrackDomain(max(plan_event.track for plan_event, _, _ in pairs))
    )
    messages = tuple(
        renderer.to_mock_message(plan_event, mutation_plan)
        for plan_event, _track_intent, _intent_row in pairs
    )
    return tuple(
        _event_row(
            message=message,
            track_intent=track_intent,
            intent_row=intent_row,
        )
        for message, (_plan_event, track_intent, intent_row) in zip(messages, pairs, strict=True)
    )


def _candidate_preview_reason(snapshot: AnalogFourKitSnapshot) -> str:
    if snapshot.snapshot_layout == A4_SNAPSHOT_LAYOUT_SAVED_KIT:
        return _SAVED_KIT_PREVIEW_REASON
    return _CANDIDATE_PREVIEW_REASON


def build_analog_four_style_mutation_mock_preview(
    snapshot: AnalogFourKitSnapshot,
    style_key: str,
    *,
    discovery_amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> AnalogFourStyleMutationMockPreview:
    """Return passive mock CC rows for an Analog Four style mutation intent."""

    intent_plan = plan_analog_four_style_mutation_intent(
        snapshot,
        style_key,
        discovery_amount=discovery_amount,
    )
    blocked_reason = None if snapshot.offsets_promoted else _CANDIDATE_ONLY_REASON
    rows = (
        ()
        if blocked_reason is not None
        else _render_mock_rows(
            snapshot=snapshot,
            intent_plan=intent_plan,
        )
    )
    deferred = _deferred_rows(intent_plan, reason_for_all=blocked_reason)
    planned_tracks = tuple(sorted({row.track for row in rows}))
    preview_ready = bool(rows)
    readiness_reason = "ready" if preview_ready else "no CC-renderable style zones available"
    if blocked_reason is not None:
        readiness_reason = _candidate_preview_reason(snapshot)
    return AnalogFourStyleMutationMockPreview(
        kit_name=intent_plan.kit_name,
        slot=intent_plan.slot,
        snapshot_layout=snapshot.snapshot_layout,
        style_key=intent_plan.style_key,
        discovery_amount=intent_plan.discovery_amount,
        discovery_band=intent_plan.discovery_band,
        mutation_depth=intent_plan.mutation_depth,
        preview_ready=preview_ready,
        readiness_reason=readiness_reason,
        ready_track_count=intent_plan.ready_track_count,
        blocked_track_count=intent_plan.blocked_track_count,
        intent_row_count=intent_plan.intent_row_count,
        mock_message_count=len(rows),
        deferred_row_count=len(deferred),
        planned_tracks=planned_tracks,
        event_rows=rows,
        deferred_rows=deferred,
    )


__all__ = [
    "AnalogFourStyleMutationMockPreview",
    "AnalogFourStyleMutationMockPreviewDeferredRow",
    "AnalogFourStyleMutationMockPreviewEvent",
    "build_analog_four_style_mutation_mock_preview",
]
