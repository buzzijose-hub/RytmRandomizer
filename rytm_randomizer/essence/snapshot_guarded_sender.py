"""Mock-only guarded sender for Rytm snapshot essence send plans.

This module proves the snapshot essence send guard without opening MIDI ports
or sending hardware MIDI. It accepts only a ``MockMidiSender`` and emits only
eligible CC events from a ready ``SnapshotEssenceSendPlan``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ..mock_midi import MidiMessage, MockMidiSender, build_cc_message
from .snapshot_send_plan import (
    SnapshotEssenceSendPlan,
    SnapshotEssenceSendPlanEvent,
)

GUARD_NAME = "snapshot_essence_guarded_send_dry_run"


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class SnapshotEssenceGuardedSendResult:
    """Result from a mock-only snapshot essence guarded send attempt."""

    accepted: bool
    reason: str
    plan_ready: bool
    source_path: str
    slot_number: int
    kit_name: str
    style_prompt: str
    eligible_event_count: int
    blocked_event_count: int
    emitted_messages: tuple[MidiMessage, ...]
    mock_only: bool = True
    sends_real_midi: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def emitted_message_count(self) -> int:
        return len(self.emitted_messages)


def execute_snapshot_essence_guarded_send(
    plan: SnapshotEssenceSendPlan,
    sender: MockMidiSender,
    *,
    armed: bool,
    dry_run_confirmed: bool,
) -> SnapshotEssenceGuardedSendResult:
    """Execute a ready snapshot essence send plan into an injected mock sender."""

    if not isinstance(plan, SnapshotEssenceSendPlan):
        raise TypeError("plan must be a SnapshotEssenceSendPlan")
    if not isinstance(sender, MockMidiSender):
        raise TypeError("sender must be a MockMidiSender")

    if not armed:
        return _blocked_result(plan, "missing_arming")
    if not dry_run_confirmed:
        return _blocked_result(plan, "missing_dry_run_confirmation")
    if not plan.ready:
        return _blocked_result(plan, "plan_not_ready")
    if plan.blocked_event_count:
        return _blocked_result(plan, "blocked_by_ineligible_events")

    messages = tuple(_message_from_event(event, plan) for event in plan.events)
    sender.send_many(messages)
    return SnapshotEssenceGuardedSendResult(
        accepted=True,
        reason="accepted_guarded_mock_only",
        plan_ready=plan.ready,
        source_path=plan.source_path,
        slot_number=plan.slot_number,
        kit_name=plan.kit_name,
        style_prompt=plan.style_prompt,
        eligible_event_count=plan.eligible_event_count,
        blocked_event_count=plan.blocked_event_count,
        emitted_messages=messages,
        metadata=_result_metadata(plan, "accepted_guarded_mock_only"),
    )


def build_snapshot_essence_guarded_send_dry_run(
    plan: SnapshotEssenceSendPlan,
) -> SnapshotEssenceGuardedSendResult:
    """Execute a snapshot essence send plan into a fresh mock sender."""

    if not isinstance(plan, SnapshotEssenceSendPlan):
        raise TypeError("plan must be a SnapshotEssenceSendPlan")

    sender = MockMidiSender()
    return execute_snapshot_essence_guarded_send(
        plan,
        sender,
        armed=True,
        dry_run_confirmed=True,
    )


def format_snapshot_essence_guarded_send_dry_run_report(
    result: SnapshotEssenceGuardedSendResult,
) -> list[str]:
    """Format a deterministic passive snapshot essence guarded send report."""

    lines = [
        "RytmRandomizer passive Snapshot Essence Guarded Send Dry-Run Report",
        f"Source path: {result.source_path}",
        f"Source slot: {result.slot_number}",
        f"Kit: {result.kit_name or '<blank>'}",
        f"Style prompt: {result.style_prompt}",
        f"Accepted: {result.accepted}",
        f"Reason: {result.reason}",
        f"Plan ready: {result.plan_ready}",
        f"Eligible snapshot essence events: {result.eligible_event_count}",
        f"Blocked snapshot essence events: {result.blocked_event_count}",
        f"Emitted mock messages: {result.emitted_message_count}",
        "Mock emission preview:",
    ]
    if result.emitted_messages:
        lines.extend(_format_message_line(message) for message in result.emitted_messages)
    else:
        lines.append("- no messages emitted")
    lines.extend(
        [
            "Guard policy:",
            "- mock-only guarded dry-run",
            "- requires arming and dry-run confirmation",
            "- emits eligible snapshot essence CC events only when the whole plan is ready",
            "- blocked plans emit no partial messages",
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


def format_snapshot_essence_guarded_send_error(
    path: str,
    message: str,
) -> list[str]:
    """Format deterministic snapshot essence guarded dry-run errors."""

    return [
        "RytmRandomizer passive Snapshot Essence Guarded Send Dry-Run Report",
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


def _blocked_result(
    plan: SnapshotEssenceSendPlan,
    reason: str,
) -> SnapshotEssenceGuardedSendResult:
    return SnapshotEssenceGuardedSendResult(
        accepted=False,
        reason=reason,
        plan_ready=plan.ready,
        source_path=plan.source_path,
        slot_number=plan.slot_number,
        kit_name=plan.kit_name,
        style_prompt=plan.style_prompt,
        eligible_event_count=plan.eligible_event_count,
        blocked_event_count=plan.blocked_event_count,
        emitted_messages=(),
        metadata=_result_metadata(plan, reason),
    )


def _result_metadata(plan: SnapshotEssenceSendPlan, reason: str) -> dict[str, object]:
    return {
        "guard": GUARD_NAME,
        "reason": reason,
        "plan_ready": plan.ready,
        "source_path": plan.source_path,
        "slot_number": plan.slot_number,
        "kit_name": plan.kit_name,
        "style_prompt": plan.style_prompt,
        "eligible_event_count": plan.eligible_event_count,
        "blocked_event_count": plan.blocked_event_count,
        "mock_only": True,
        "sends_real_midi": False,
    }


def _message_from_event(
    event: SnapshotEssenceSendPlanEvent,
    plan: SnapshotEssenceSendPlan,
) -> MidiMessage:
    if not event.eligible:
        raise ValueError("only eligible snapshot essence events can be emitted")
    return build_cc_message(
        channel=event.wire_channel,
        control=event.control,
        value=event.value,
        metadata={
            "guard": GUARD_NAME,
            "source_kind": "snapshot_essence_guarded_send_dry_run",
            "source_path": plan.source_path,
            "slot_number": plan.slot_number,
            "style_prompt": plan.style_prompt,
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


def _format_message_line(message: MidiMessage) -> str:
    metadata = message.metadata
    midi_channel = metadata.get("midi_channel", message.channel + 1)
    return (
        f"- {metadata.get('device')} / Pad {metadata.get('pad')} / "
        f"ch {midi_channel} wire {message.channel} / "
        f"CC{message.control} -> {message.value} / "
        f"{metadata.get('event_role')} / {metadata.get('parameter')}"
    )


__all__ = [
    "GUARD_NAME",
    "SnapshotEssenceGuardedSendResult",
    "build_snapshot_essence_guarded_send_dry_run",
    "execute_snapshot_essence_guarded_send",
    "format_snapshot_essence_guarded_send_dry_run_report",
    "format_snapshot_essence_guarded_send_error",
]
