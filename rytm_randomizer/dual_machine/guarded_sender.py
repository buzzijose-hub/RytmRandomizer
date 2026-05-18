"""Mock-only guarded sender for dual-machine active-send plans.

This module proves the active-send guard without opening MIDI ports or sending
hardware MIDI. It accepts only a ``MockMidiSender`` and emits only eligible CC
events from a ready ``DualMachineActiveSendPlan``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ..mock_midi import MidiMessage, MockMidiSender, build_cc_message
from .active_send_plan import (
    DualMachineActiveSendPlan,
    DualMachineSendPlanEvent,
    build_dual_machine_active_send_plan,
)
from .mock_bridge import DualMachineMockBridge

GUARD_NAME = "dual_machine_guarded_send_dry_run"


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class DualMachineGuardedSendResult:
    """Result from a mock-only guarded send attempt."""

    target: str
    accepted: bool
    reason: str
    plan_ready: bool
    eligible_message_count: int
    blocked_event_count: int
    emitted_messages: tuple[MidiMessage, ...]
    analog_four_starter_profile_key: str | None = None
    analog_four_starter_profile_label: str | None = None
    mock_only: bool = True
    sends_real_midi: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def emitted_message_count(self) -> int:
        return len(self.emitted_messages)


def execute_dual_machine_guarded_send(
    plan: DualMachineActiveSendPlan,
    sender: MockMidiSender,
    *,
    armed: bool,
    dry_run_confirmed: bool,
) -> DualMachineGuardedSendResult:
    """Execute a ready active-send plan into an injected mock sender."""

    if not isinstance(plan, DualMachineActiveSendPlan):
        raise TypeError("plan must be a DualMachineActiveSendPlan")
    if not isinstance(sender, MockMidiSender):
        raise TypeError("sender must be a MockMidiSender")

    if not armed:
        return _blocked_result(plan, "missing_arming")
    if not dry_run_confirmed:
        return _blocked_result(plan, "missing_dry_run_confirmation")
    if not plan.ready:
        return _blocked_result(plan, plan.readiness_reason)

    messages = tuple(_message_from_event(event, plan.target) for event in plan.events)
    sender.send_many(messages)
    return DualMachineGuardedSendResult(
        target=plan.target,
        accepted=True,
        reason="accepted_guarded_mock_only",
        plan_ready=plan.ready,
        eligible_message_count=plan.eligible_message_count,
        blocked_event_count=plan.blocked_event_count,
        emitted_messages=messages,
        analog_four_starter_profile_key=plan.analog_four_starter_profile_key,
        analog_four_starter_profile_label=plan.analog_four_starter_profile_label,
        metadata=_result_metadata(plan, "accepted_guarded_mock_only"),
    )


def build_dual_machine_guarded_send_dry_run(
    bridge: DualMachineMockBridge,
) -> DualMachineGuardedSendResult:
    """Build a plan and execute it into a fresh mock sender."""

    if not isinstance(bridge, DualMachineMockBridge):
        raise TypeError("bridge must be a DualMachineMockBridge")

    plan = build_dual_machine_active_send_plan(bridge)
    sender = MockMidiSender()
    return execute_dual_machine_guarded_send(
        plan,
        sender,
        armed=True,
        dry_run_confirmed=True,
    )


def format_dual_machine_guarded_send_dry_run_report(
    result: DualMachineGuardedSendResult,
) -> list[str]:
    """Format a deterministic passive guarded send dry-run report."""

    lines = [
        "RytmRandomizer passive Dual-Machine Guarded Send Dry-Run Report",
        f"Target: {result.target}",
        *(_analog_four_starter_profile_lines(result)),
        f"Accepted: {result.accepted}",
        f"Reason: {result.reason}",
        f"Plan ready: {result.plan_ready}",
        f"Eligible mapped CC messages: {result.eligible_message_count}",
        f"Blocked candidate events: {result.blocked_event_count}",
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
            "- emits mapped CC messages only when the whole target plan is ready",
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


def format_dual_machine_guarded_send_error(message: str) -> list[str]:
    """Format deterministic guarded dry-run errors."""

    return [
        "RytmRandomizer passive Dual-Machine Guarded Send Dry-Run Report",
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
    plan: DualMachineActiveSendPlan,
    reason: str,
) -> DualMachineGuardedSendResult:
    return DualMachineGuardedSendResult(
        target=plan.target,
        accepted=False,
        reason=reason,
        plan_ready=plan.ready,
        eligible_message_count=plan.eligible_message_count,
        blocked_event_count=plan.blocked_event_count,
        emitted_messages=(),
        analog_four_starter_profile_key=plan.analog_four_starter_profile_key,
        analog_four_starter_profile_label=plan.analog_four_starter_profile_label,
        metadata=_result_metadata(plan, reason),
    )


def _result_metadata(plan: DualMachineActiveSendPlan, reason: str) -> dict[str, object]:
    return {
        "guard": GUARD_NAME,
        "target": plan.target,
        "reason": reason,
        "plan_ready": plan.ready,
        "eligible_message_count": plan.eligible_message_count,
        "blocked_event_count": plan.blocked_event_count,
        "mock_only": True,
        "sends_real_midi": False,
    }


def _message_from_event(event: DualMachineSendPlanEvent, target: str) -> MidiMessage:
    if not event.eligible or event.message_type != "cc":
        raise ValueError("only eligible mapped CC events can be emitted")
    return build_cc_message(
        channel=event.channel,
        control=event.control,
        value=event.value,
        metadata={
            "guard": GUARD_NAME,
            "target": target,
            "device": event.device,
            "source": event.source,
            "label": event.label,
            "eligible_reason": event.reason,
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


def _analog_four_starter_profile_lines(result: DualMachineGuardedSendResult) -> list[str]:
    if result.analog_four_starter_profile_key is None:
        return []
    return [
        "Analog Four starter profile: "
        f"{result.analog_four_starter_profile_label} / "
        f"{result.analog_four_starter_profile_key}"
    ]


def _format_message_line(message: MidiMessage) -> str:
    metadata = message.metadata
    midi_channel = message.channel + 1
    return (
        f"- {metadata.get('device')} / ch {midi_channel} wire {message.channel} / "
        f"CC{message.control} -> {message.value} / {metadata.get('label')}"
    )


__all__ = [
    "DualMachineGuardedSendResult",
    "build_dual_machine_guarded_send_dry_run",
    "execute_dual_machine_guarded_send",
    "format_dual_machine_guarded_send_dry_run_report",
    "format_dual_machine_guarded_send_error",
]
