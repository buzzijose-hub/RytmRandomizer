"""Passive send-plan bridge for Rytm snapshot essence overlays.

This module converts saved-kit snapshot essence decisions into inert CC event
plans. It does not import MIDI libraries, open ports, send real MIDI, receive
SysEx, write SysEx, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .data import MACHINE_CC, PROFILES
from .mock_midi import MockMidiSender, build_cc_message
from .observability.errors import DataError
from .snapshot_essence_overlay import (
    MACHINE_PROFILE_KEYS,
    SnapshotEssenceOverlayPlan,
    SnapshotEssenceOverlayPad,
    build_snapshot_essence_overlay_plan_from_file,
)
from .snapshot_mutation_planner import SnapshotPadMutationPlan


@dataclass(frozen=True)
class SnapshotEssenceSendPlanEvent:
    """One passive CC event in the Rytm snapshot essence send plan."""

    pad: int
    midi_channel: int
    wire_channel: int
    role_label: str
    machine_label: str
    event_role: str
    label: str
    control: int
    value: int
    eligible: bool
    reason: str
    source: str
    baseline_value: int | None = None
    delta: int | None = None


@dataclass(frozen=True)
class SnapshotEssenceSendPlan:
    """Passive Rytm send plan built from a saved-kit essence overlay."""

    source_path: str
    slot_number: int
    kit_name: str
    depth: str
    style_prompt: str
    matched_profile_labels: tuple[str, ...]
    essence_tags: tuple[str, ...]
    discovery: float
    same_engine_pad_count: int
    engine_switch_pad_count: int
    blocked_pad_count: int
    events: tuple[SnapshotEssenceSendPlanEvent, ...]

    @property
    def ready(self) -> bool:
        return self.blocked_pad_count == 0 and self.event_count > 0

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def eligible_event_count(self) -> int:
        return sum(1 for event in self.events if event.eligible)

    @property
    def blocked_event_count(self) -> int:
        return sum(1 for event in self.events if not event.eligible)

    @property
    def machine_switch_event_count(self) -> int:
        return sum(1 for event in self.events if event.event_role == "machine_switch")

    @property
    def selected_profile_anchor_event_count(self) -> int:
        return sum(1 for event in self.events if event.event_role == "selected_profile_anchor")

    @property
    def snapshot_mutation_event_count(self) -> int:
        return sum(1 for event in self.events if event.event_role == "snapshot_mutation")


def build_snapshot_essence_send_plan_from_file(
    path: str | Path,
    *,
    slot: int,
    depth: str,
    style: str,
    discovery: float | None = None,
) -> SnapshotEssenceSendPlan:
    """Build a passive Rytm send plan from an existing saved kit snapshot."""

    overlay = build_snapshot_essence_overlay_plan_from_file(
        path,
        slot=slot,
        depth=depth,
        style=style,
        discovery=discovery,
    )
    return build_snapshot_essence_send_plan(overlay)


def build_snapshot_essence_send_plan(
    overlay: SnapshotEssenceOverlayPlan,
) -> SnapshotEssenceSendPlan:
    """Build an ordered passive send plan from a snapshot essence overlay."""

    if not isinstance(overlay, SnapshotEssenceOverlayPlan):
        raise TypeError("overlay must be a SnapshotEssenceOverlayPlan")

    events: list[SnapshotEssenceSendPlanEvent] = []
    for overlay_pad in overlay.pads:
        if overlay_pad.status == "engine_switch_ready":
            events.extend(_engine_switch_events(overlay_pad))
        elif overlay_pad.status == "same_engine_snapshot_ready":
            events.extend(_snapshot_mutation_events(overlay_pad))

    return SnapshotEssenceSendPlan(
        source_path=overlay.source_path,
        slot_number=overlay.slot_number,
        kit_name=overlay.kit_name,
        depth=overlay.depth,
        style_prompt=overlay.style_prompt,
        matched_profile_labels=overlay.matched_profile_labels,
        essence_tags=overlay.essence_tags,
        discovery=overlay.discovery,
        same_engine_pad_count=overlay.same_engine_ready_count,
        engine_switch_pad_count=overlay.engine_switch_ready_count,
        blocked_pad_count=overlay.blocked_pad_count,
        events=tuple(events),
    )


def capture_snapshot_essence_send_mock_messages(
    plan: SnapshotEssenceSendPlan,
) -> MockMidiSender:
    """Capture eligible snapshot essence send events into an inert mock sender."""

    if not isinstance(plan, SnapshotEssenceSendPlan):
        raise TypeError("plan must be a SnapshotEssenceSendPlan")

    sender = MockMidiSender()
    if not plan.ready:
        return sender

    for event in plan.events:
        if not event.eligible:
            continue
        sender.send(
            build_cc_message(
                channel=event.wire_channel,
                control=event.control,
                value=event.value,
                metadata={
                    "source_kind": "snapshot_essence_send_plan",
                    "device": "Analog Rytm MKII",
                    "pad": event.pad,
                    "midi_channel": event.midi_channel,
                    "role_label": event.role_label,
                    "machine_label": event.machine_label,
                    "event_role": event.event_role,
                    "parameter": event.label,
                    "baseline_value": event.baseline_value,
                    "delta": event.delta,
                    "eligible_reason": event.reason,
                    "event_source": event.source,
                    "mock_only": True,
                    "sends_real_midi": False,
                },
            )
        )
    return sender


def format_snapshot_essence_send_plan_report(
    plan: SnapshotEssenceSendPlan,
    sender: MockMidiSender | None = None,
) -> list[str]:
    """Format a deterministic passive Rytm snapshot essence send-plan report."""

    if sender is None:
        sender = capture_snapshot_essence_send_mock_messages(plan)

    lines = [
        "RytmRandomizer passive Snapshot Essence Send Plan Report",
        f"Source path: {plan.source_path}",
        f"Source slot: {plan.slot_number}",
        f"Kit: {plan.kit_name or '<blank>'}",
        f"Depth: {plan.depth}",
        f"Style prompt: {plan.style_prompt}",
        f"Matched profiles: {_format_labels(plan.matched_profile_labels)}",
        f"Essence tags: {_format_labels(plan.essence_tags)}",
        f"Discovery: {plan.discovery:.2f}",
        f"Send plan ready: {plan.ready}",
        (
            "Pad counts: "
            f"same-engine {plan.same_engine_pad_count} / "
            f"engine-switch {plan.engine_switch_pad_count} / "
            f"blocked {plan.blocked_pad_count}"
        ),
        f"Machine switch events: {plan.machine_switch_event_count}",
        f"Selected profile anchor events: {plan.selected_profile_anchor_event_count}",
        f"Snapshot mutation events: {plan.snapshot_mutation_event_count}",
        f"Eligible events: {plan.eligible_event_count}",
        f"Blocked events: {plan.blocked_event_count}",
        f"Mock sender captured: {len(sender.sent_messages)} message(s)",
        "Event plan:",
    ]
    if plan.events:
        lines.extend(_format_event_line(event) for event in plan.events)
    else:
        lines.append("- no planned events")
    lines.extend(
        [
            "Send policy:",
            "- passive send-plan preview only",
            "- same-engine pads use captured snapshot mutation events",
            "- engine-switch pads send CC15 before selected profile anchors",
            "- captured old-engine parameter values are not reused after engine switches",
            "- blocked pads emit no events",
            "Safety:",
            "- passive/read-only",
            "- mock sender only",
            "- no MIDI sending",
            "- no MIDI receive",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
    return lines


def format_snapshot_essence_send_plan_error(
    path: str | Path,
    message: str,
) -> list[str]:
    """Format deterministic passive snapshot essence send-plan errors."""

    return [
        "RytmRandomizer passive Snapshot Essence Send Plan Report",
        f"Path: {path}",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- mock sender only",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


def _engine_switch_events(
    overlay_pad: SnapshotEssenceOverlayPad,
) -> tuple[SnapshotEssenceSendPlanEvent, ...]:
    profile_key = MACHINE_PROFILE_KEYS.get(overlay_pad.selected_machine_key)
    if profile_key is None:
        raise DataError(f"Selected machine is not mapped: {overlay_pad.selected_machine_key}")
    profile = PROFILES[profile_key]
    if overlay_pad.selected_machine_value is None:
        raise DataError(f"Selected machine has no CC15 value: {overlay_pad.selected_machine_label}")

    events = [
        SnapshotEssenceSendPlanEvent(
            pad=overlay_pad.pad,
            midi_channel=overlay_pad.midi_channel,
            wire_channel=overlay_pad.wire_channel,
            role_label=overlay_pad.role_label,
            machine_label=overlay_pad.selected_machine_label,
            event_role="machine_switch",
            label="machine",
            control=MACHINE_CC,
            value=overlay_pad.selected_machine_value,
            eligible=True,
            reason="mapped_machine_switch_required",
            source="style_engine_switch",
            baseline_value=overlay_pad.captured_machine_value,
            delta=overlay_pad.selected_machine_value - overlay_pad.captured_machine_value,
        )
    ]
    events.extend(_selected_profile_anchor_events(overlay_pad, profile))
    return tuple(events)


def _selected_profile_anchor_events(
    overlay_pad: SnapshotEssenceOverlayPad,
    profile: dict,
) -> tuple[SnapshotEssenceSendPlanEvent, ...]:
    anchor = profile["anchor"]
    params = profile["params"]
    events = []
    for name in profile["order"]:
        if name not in anchor:
            continue
        events.append(
            SnapshotEssenceSendPlanEvent(
                pad=overlay_pad.pad,
                midi_channel=overlay_pad.midi_channel,
                wire_channel=overlay_pad.wire_channel,
                role_label=overlay_pad.role_label,
                machine_label=overlay_pad.selected_machine_label,
                event_role="selected_profile_anchor",
                label=name,
                control=params[name],
                value=anchor[name],
                eligible=True,
                reason="selected_mapped_profile_anchor",
                source="selected_profile_anchor",
            )
        )
    return tuple(events)


def _snapshot_mutation_events(
    overlay_pad: SnapshotEssenceOverlayPad,
) -> tuple[SnapshotEssenceSendPlanEvent, ...]:
    snapshot_pad = overlay_pad.snapshot_pad
    if not isinstance(snapshot_pad, SnapshotPadMutationPlan):
        raise DataError("Overlay pad is missing snapshot mutation details")

    return tuple(
        SnapshotEssenceSendPlanEvent(
            pad=change.pad,
            midi_channel=change.midi_channel,
            wire_channel=change.midi_channel - 1,
            role_label=overlay_pad.role_label,
            machine_label=change.machine_label,
            event_role="snapshot_mutation",
            label=change.parameter_name,
            control=change.cc,
            value=change.planned_value,
            eligible=True,
            reason="captured_machine_matches_selected",
            source="captured_snapshot_mutation",
            baseline_value=change.baseline_value,
            delta=change.delta,
        )
        for change in snapshot_pad.changes
    )


def _format_event_line(event: SnapshotEssenceSendPlanEvent) -> str:
    return (
        f"- Pad {event.pad} ch {event.midi_channel} wire {event.wire_channel} "
        f"{event.event_role}: CC{event.control} -> {event.value} / "
        f"{event.machine_label} / {event.label} / {event.source} ({event.reason})"
    )


def _format_labels(labels: tuple[str, ...]) -> str:
    return ", ".join(labels) if labels else "none"


__all__ = [
    "SnapshotEssenceSendPlan",
    "SnapshotEssenceSendPlanEvent",
    "build_snapshot_essence_send_plan",
    "build_snapshot_essence_send_plan_from_file",
    "capture_snapshot_essence_send_mock_messages",
    "format_snapshot_essence_send_plan_error",
    "format_snapshot_essence_send_plan_report",
]
