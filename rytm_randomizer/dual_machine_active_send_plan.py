"""Passive active-send planning for dual-machine Live Snapshot previews.

This module classifies inert dual-machine bridge messages by whether a future
guarded active sender may send them. It does not import MIDI libraries, open
ports, send MIDI, request or receive SysEx, write SysEx, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dual_machine_live_snapshot_readiness import (
    DualMachineLiveSnapshotReadiness,
    evaluate_dual_machine_live_snapshot_readiness,
)
from .dual_machine_mock_bridge import (
    DualMachineMockBridge,
    capture_dual_machine_mock_messages,
)


@dataclass(frozen=True)
class DualMachineSendPlanEvent:
    """One passive bridge event classified for future active-send eligibility."""

    device: str
    source: str
    message_type: str
    channel: int
    control: int
    value: int
    eligible: bool
    reason: str
    label: str
    midi_channel: int | None = None


@dataclass(frozen=True)
class DualMachineActiveSendPlan:
    """Passive active-send plan for an existing dual-machine bridge preview."""

    target: str
    ready: bool
    readiness_reason: str
    events: tuple[DualMachineSendPlanEvent, ...]
    analog_four_starter_profile_key: str | None = None
    analog_four_starter_profile_label: str | None = None

    @property
    def eligible_message_count(self) -> int:
        return sum(1 for event in self.events if event.eligible)

    @property
    def blocked_event_count(self) -> int:
        return sum(1 for event in self.events if not event.eligible)

    @property
    def combined_event_count(self) -> int:
        return len(self.events)


def build_dual_machine_active_send_plan(
    bridge: DualMachineMockBridge,
) -> DualMachineActiveSendPlan:
    """Build a passive event-level send plan from a dual-machine bridge."""

    if not isinstance(bridge, DualMachineMockBridge):
        raise TypeError("bridge must be a DualMachineMockBridge")

    readiness = evaluate_dual_machine_live_snapshot_readiness(bridge)
    events = tuple(
        _event_from_message(message)
        for message in capture_dual_machine_mock_messages(bridge).sent_messages
    )
    ready = readiness.ready and all(event.eligible for event in events)
    return DualMachineActiveSendPlan(
        target=readiness.target,
        ready=ready,
        readiness_reason=_plan_reason(readiness, events, ready),
        events=events,
        analog_four_starter_profile_key=bridge.analog_four_starter_profile_key,
        analog_four_starter_profile_label=bridge.analog_four_starter_profile_label,
    )


def format_dual_machine_active_send_plan_report(
    plan: DualMachineActiveSendPlan,
) -> list[str]:
    """Format a deterministic passive dual-machine active-send plan report."""

    lines = [
        "RytmRandomizer passive Dual-Machine Active Send Plan Report",
        f"Target: {plan.target}",
        *(_analog_four_starter_profile_lines(plan)),
        f"Send plan ready: {plan.ready}",
        f"Readiness reason: {plan.readiness_reason}",
        f"Eligible mapped CC messages: {plan.eligible_message_count}",
        f"Blocked candidate events: {plan.blocked_event_count}",
        f"Combined planned events: {plan.combined_event_count}",
        "Event plan:",
    ]
    if plan.events:
        lines.extend(_format_event_line(event) for event in plan.events)
    else:
        lines.append("- no planned events")
    lines.extend(
        [
            "Mapping policy:",
            "- passive active-send planning only",
            "- eligible messages are mapped CC mock events only",
            "- saved-offset candidate events are blocked",
            "- blocked events must not reach a hardware sender",
            "Safety:",
            "- passive/read-only",
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


def format_dual_machine_active_send_plan_error(message: str) -> list[str]:
    """Format deterministic passive dual-machine send-plan errors."""

    return [
        "RytmRandomizer passive Dual-Machine Active Send Plan Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- active-send planning only",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


def _event_from_message(message) -> DualMachineSendPlanEvent:
    metadata = message.metadata
    message_type = message.type
    if message_type == "cc":
        eligible = True
        reason = "mapped_cc_message"
    elif message_type == "saved_offset_candidate":
        eligible = False
        reason = "candidate_unverified_no_cc_mapping"
    else:
        eligible = False
        reason = "unsupported_message_type"

    return DualMachineSendPlanEvent(
        device=str(metadata.get("device", "<unknown>")),
        source=str(metadata.get("source") or metadata.get("parameter_source") or "<unknown>"),
        message_type=message_type,
        channel=message.channel,
        control=message.control,
        value=message.value,
        eligible=eligible,
        reason=reason,
        label=_message_label(message),
        midi_channel=_optional_int(metadata.get("midi_channel")),
    )


def _plan_reason(
    readiness: DualMachineLiveSnapshotReadiness,
    events: tuple[DualMachineSendPlanEvent, ...],
    ready: bool,
) -> str:
    if ready:
        return readiness.reason
    if any(event.reason == "candidate_unverified_no_cc_mapping" for event in events):
        return "blocked_by_unverified_candidates"
    if any(not event.eligible for event in events):
        return "blocked_by_uneligible_events"
    return readiness.reason


def _analog_four_starter_profile_lines(plan: DualMachineActiveSendPlan) -> list[str]:
    if plan.analog_four_starter_profile_key is None:
        return []
    return [
        "Analog Four starter profile: "
        f"{plan.analog_four_starter_profile_label} / "
        f"{plan.analog_four_starter_profile_key}"
    ]


def _message_label(message) -> str:
    metadata = message.metadata
    device = metadata.get("device")
    if device == "Analog Rytm MKII":
        return (
            f"Rytm Pad {metadata.get('pad')} / "
            f"{metadata.get('machine')} / {metadata.get('parameter')}"
        )
    if message.type == "saved_offset_candidate":
        return f"Track {metadata.get('track')} / {metadata.get('role')}"
    if device == "Analog Four MKII":
        return (
            f"Track {metadata.get('track')} / "
            f"{metadata.get('role')} / {metadata.get('parameter')}"
        )
    return "<unknown>"


def _format_event_line(event: DualMachineSendPlanEvent) -> str:
    status = "eligible" if event.eligible else "blocked"
    if event.message_type == "cc":
        midi_channel = event.midi_channel if event.midi_channel is not None else event.channel + 1
        return (
            f"- {status} / {event.device} / ch {midi_channel} wire {event.channel} / "
            f"CC{event.control} -> {event.value} / {event.label} / "
            f"{event.source} ({event.reason})"
        )
    return (
        f"- {status} / {event.device} / {event.label} / wire {event.channel} / "
        f"Offset +{event.control} -> {event.value} / "
        f"{event.reason} / {event.source}"
    )


def _optional_int(value) -> int | None:
    if isinstance(value, int):
        return value
    return None


__all__ = [
    "DualMachineActiveSendPlan",
    "DualMachineSendPlanEvent",
    "build_dual_machine_active_send_plan",
    "format_dual_machine_active_send_plan_error",
    "format_dual_machine_active_send_plan_report",
]
