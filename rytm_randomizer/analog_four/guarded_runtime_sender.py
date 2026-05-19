"""Mock-only guarded sender for Analog Four runtime plans.

This module proves the A4 runtime guard without opening MIDI ports or sending
hardware MIDI. It accepts only a MockMidiSender and emits only mapped CC
events from an AnalogFourRuntimePlan.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ..mock_midi import MidiMessage, MockMidiSender, build_cc_message
from .runtime_plan import AnalogFourRuntimeEvent, AnalogFourRuntimePlan

GUARD_NAME = "analog_four_runtime_guarded_send_dry_run"


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class AnalogFourRuntimeGuardedSendResult:
    """Result from a mock-only A4 guarded runtime send attempt."""

    device: str
    accepted: bool
    reason: str
    plan_ready: bool
    eligible_message_count: int
    blocked_event_count: int
    emitted_messages: tuple[MidiMessage, ...]
    starter_profile_key: str
    starter_profile_label: str
    mock_only: bool = True
    sends_real_midi: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def emitted_message_count(self) -> int:
        return len(self.emitted_messages)

    @property
    def track_count(self) -> int:
        return len({message.metadata["track"] for message in self.emitted_messages})


def execute_analog_four_runtime_guarded_send(
    plan: AnalogFourRuntimePlan,
    sender: MockMidiSender,
    *,
    armed: bool,
    dry_run_confirmed: bool,
) -> AnalogFourRuntimeGuardedSendResult:
    """Execute an A4 runtime plan into an injected mock sender."""

    if not isinstance(plan, AnalogFourRuntimePlan):
        raise TypeError("plan must be an AnalogFourRuntimePlan")
    if not isinstance(sender, MockMidiSender):
        raise TypeError("sender must be a MockMidiSender")

    events = tuple(event for track in plan.tracks for event in track.events)
    if not armed:
        return _blocked_result(plan, events, "missing_arming")
    if not dry_run_confirmed:
        return _blocked_result(plan, events, "missing_dry_run_confirmation")

    messages = tuple(_message_from_event(plan, event) for event in events)
    sender.send_many(messages)
    return AnalogFourRuntimeGuardedSendResult(
        device=plan.device,
        accepted=True,
        reason="accepted_a4_guarded_mock_only",
        plan_ready=True,
        eligible_message_count=len(messages),
        blocked_event_count=0,
        emitted_messages=messages,
        starter_profile_key=plan.starter_profile_key,
        starter_profile_label=plan.starter_profile_label,
        metadata=_result_metadata(plan, "accepted_a4_guarded_mock_only", len(messages), 0),
    )


def build_analog_four_runtime_guarded_send_dry_run(
    plan: AnalogFourRuntimePlan,
) -> AnalogFourRuntimeGuardedSendResult:
    """Build and execute an A4 runtime guarded dry-run into a fresh mock sender."""

    sender = MockMidiSender()
    return execute_analog_four_runtime_guarded_send(
        plan,
        sender,
        armed=True,
        dry_run_confirmed=True,
    )


def format_analog_four_runtime_guarded_send_dry_run_report(
    result: AnalogFourRuntimeGuardedSendResult,
) -> list[str]:
    """Format a deterministic A4 guarded runtime dry-run report."""

    lines = [
        "RytmRandomizer passive Analog Four Guarded Runtime Dry-Run Report",
        f"Device: {result.device}",
        f"Starter profile: {result.starter_profile_label} / {result.starter_profile_key}",
        f"Accepted: {result.accepted}",
        f"Reason: {result.reason}",
        f"Plan ready: {result.plan_ready}",
        f"Eligible mapped CC messages: {result.eligible_message_count}",
        f"Blocked candidate events: {result.blocked_event_count}",
        f"Emitted mock messages: {result.emitted_message_count}",
        "Track coverage:",
    ]
    lines.extend(_track_coverage_lines(result))
    lines.append("Mock emission preview:")
    if result.emitted_messages:
        lines.extend(_format_message_line(message) for message in result.emitted_messages)
    else:
        lines.append("- no messages emitted")
    lines.extend(_safety_lines())
    return lines


def format_analog_four_runtime_guarded_send_error(message: str) -> list[str]:
    """Format deterministic A4 guarded dry-run errors."""

    return [
        "RytmRandomizer passive Analog Four Guarded Runtime Dry-Run Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        *_safety_lines(),
    ]


def _blocked_result(
    plan: AnalogFourRuntimePlan,
    events: tuple[AnalogFourRuntimeEvent, ...],
    reason: str,
) -> AnalogFourRuntimeGuardedSendResult:
    return AnalogFourRuntimeGuardedSendResult(
        device=plan.device,
        accepted=False,
        reason=reason,
        plan_ready=True,
        eligible_message_count=len(events),
        blocked_event_count=0,
        emitted_messages=(),
        starter_profile_key=plan.starter_profile_key,
        starter_profile_label=plan.starter_profile_label,
        metadata=_result_metadata(plan, reason, len(events), 0),
    )


def _message_from_event(
    plan: AnalogFourRuntimePlan,
    event: AnalogFourRuntimeEvent,
) -> MidiMessage:
    return build_cc_message(
        channel=event.wire_channel,
        control=event.cc,
        value=event.value,
        metadata={
            "guard": GUARD_NAME,
            "device": plan.device,
            "track": event.track,
            "midi_channel": event.midi_channel,
            "wire_channel": event.wire_channel,
            "role": event.role_label,
            "parameter": event.parameter_name,
            "starter_profile_key": plan.starter_profile_key,
            "starter_profile_label": plan.starter_profile_label,
            "eligible_reason": "mapped_cc_message",
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


def _result_metadata(
    plan: AnalogFourRuntimePlan,
    reason: str,
    eligible_message_count: int,
    blocked_event_count: int,
) -> dict[str, object]:
    return {
        "guard": GUARD_NAME,
        "device": plan.device,
        "reason": reason,
        "starter_profile_key": plan.starter_profile_key,
        "starter_profile_label": plan.starter_profile_label,
        "eligible_message_count": eligible_message_count,
        "blocked_event_count": blocked_event_count,
        "mock_only": True,
        "sends_real_midi": False,
    }


def _track_coverage_lines(result: AnalogFourRuntimeGuardedSendResult) -> list[str]:
    if not result.emitted_messages:
        return ["- no track messages emitted"]
    counts = Counter(message.metadata["track"] for message in result.emitted_messages)
    role_by_track = {}
    for message in result.emitted_messages:
        role_by_track.setdefault(message.metadata["track"], message.metadata["role"])
    return [
        f"- Track {track} / {role_by_track[track]}: {counts[track]} message(s)"
        for track in sorted(counts)
    ]


def _format_message_line(message: MidiMessage) -> str:
    metadata = message.metadata
    return (
        f"- Track {metadata['track']} ch {metadata['midi_channel']} "
        f"wire {metadata['wire_channel']} / {metadata['parameter']} "
        f"CC{message.control} -> {message.value}"
    )


def _safety_lines() -> list[str]:
    return [
        "Guard policy:",
        "- A4-only guarded dry-run",
        "- requires arming and dry-run confirmation",
        "- emits mapped CC messages only",
        "- blocked plans emit no partial messages",
        "Safety:",
        "- passive/read-only",
        "- A4-only guarded dry-run",
        "- mock sender only",
        "- no Rytm MIDI sending",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


__all__ = [
    "AnalogFourRuntimeGuardedSendResult",
    "GUARD_NAME",
    "build_analog_four_runtime_guarded_send_dry_run",
    "execute_analog_four_runtime_guarded_send",
    "format_analog_four_runtime_guarded_send_dry_run_report",
    "format_analog_four_runtime_guarded_send_error",
]
