"""Mock-only guarded sender for Rytm engine-cycle plans.

This module proves the Rytm engine-cycle send guard without opening MIDI ports
or sending hardware MIDI. It accepts only a ``MockMidiSender`` and emits only
top-candidate CC15 engine-select events from a fully resolved
``RytmEngineCyclePlan``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .data import MACHINE_CC
from .mock_midi import MidiMessage, MockMidiSender, build_cc_message
from .rytm_engine_cycle_plan import (
    RytmEngineCyclePadPlan,
    RytmEngineCyclePlan,
)
from .rytm_engine_cycle_starter_profiles import (
    RytmEngineCycleStarterEvent,
    RytmEngineCycleStarterPlan,
)

GUARD_NAME = "rytm_engine_cycle_guarded_send_dry_run"
RytmEngineCycleSendPlan = RytmEngineCyclePlan | RytmEngineCycleStarterPlan


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class RytmEngineCycleGuardedSendResult:
    """Result from a mock-only Rytm engine-cycle guarded send attempt."""

    accepted: bool
    reason: str
    style_prompt: str
    discovery: float
    planned_pad_count: int
    no_candidate_count: int
    emitted_messages: tuple[MidiMessage, ...]
    starter_profile_key: str | None = None
    starter_profile_label: str | None = None
    mock_only: bool = True
    sends_real_midi: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def emitted_message_count(self) -> int:
        return len(self.emitted_messages)


def execute_rytm_engine_cycle_guarded_send(
    plan: RytmEngineCycleSendPlan,
    sender: MockMidiSender,
    *,
    armed: bool,
    dry_run_confirmed: bool,
) -> RytmEngineCycleGuardedSendResult:
    """Execute a resolved engine-cycle plan into an injected mock sender."""

    if not _is_send_plan(plan):
        raise TypeError("plan must be a RytmEngineCyclePlan or RytmEngineCycleStarterPlan")
    if not isinstance(sender, MockMidiSender):
        raise TypeError("sender must be a MockMidiSender")

    if not armed:
        return _blocked_result(plan, "missing_arming")
    if not dry_run_confirmed:
        return _blocked_result(plan, "missing_dry_run_confirmation")
    if _no_candidate_count(plan):
        return _blocked_result(plan, "plan_has_unresolved_pads")

    messages = _messages_from_plan(plan)
    sender.send_many(messages)
    return RytmEngineCycleGuardedSendResult(
        accepted=True,
        reason="accepted_guarded_mock_only",
        style_prompt=plan.style_prompt,
        discovery=plan.discovery,
        planned_pad_count=_planned_pad_count(plan),
        no_candidate_count=_no_candidate_count(plan),
        emitted_messages=messages,
        starter_profile_key=_starter_profile_key(plan),
        starter_profile_label=_starter_profile_label(plan),
        metadata=_result_metadata(plan, "accepted_guarded_mock_only"),
    )


def build_rytm_engine_cycle_guarded_send_dry_run(
    plan: RytmEngineCycleSendPlan,
) -> RytmEngineCycleGuardedSendResult:
    """Execute a Rytm engine-cycle plan into a fresh mock sender."""

    if not _is_send_plan(plan):
        raise TypeError("plan must be a RytmEngineCyclePlan or RytmEngineCycleStarterPlan")

    sender = MockMidiSender()
    return execute_rytm_engine_cycle_guarded_send(
        plan,
        sender,
        armed=True,
        dry_run_confirmed=True,
    )


def format_rytm_engine_cycle_guarded_send_dry_run_report(
    result: RytmEngineCycleGuardedSendResult,
) -> list[str]:
    """Format a deterministic passive engine-cycle guarded send report."""

    lines = [
        "RytmRandomizer passive Rytm Engine Cycle Guarded Send Dry-Run Report",
        f"Style prompt: {result.style_prompt}",
        f"Discovery: {result.discovery:.2f}",
        f"Accepted: {result.accepted}",
        f"Reason: {result.reason}",
        f"Planned pads: {result.planned_pad_count}",
        f"Unresolved pads: {result.no_candidate_count}",
        f"Emitted mock messages: {result.emitted_message_count}",
    ]
    if result.starter_profile_key is not None:
        lines.append(
            f"Starter profile: {result.starter_profile_label} / {result.starter_profile_key}"
        )
    lines.append("Mock emission preview:")
    if result.emitted_messages:
        lines.extend(_format_message_line(message) for message in result.emitted_messages)
    else:
        lines.append("- no messages emitted")
    lines.extend(
        [
            "Guard policy:",
            "- mock-only guarded Rytm engine-cycle send",
            "- requires arming and dry-run confirmation",
            *(_emission_policy_lines(result)),
            "- unresolved plans emit no partial messages",
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


def format_rytm_engine_cycle_guarded_send_error(message: str) -> list[str]:
    """Format deterministic Rytm engine-cycle guarded dry-run errors."""

    return [
        "RytmRandomizer passive Rytm Engine Cycle Guarded Send Dry-Run Report",
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
    plan: RytmEngineCycleSendPlan,
    reason: str,
) -> RytmEngineCycleGuardedSendResult:
    return RytmEngineCycleGuardedSendResult(
        accepted=False,
        reason=reason,
        style_prompt=plan.style_prompt,
        discovery=plan.discovery,
        planned_pad_count=_planned_pad_count(plan),
        no_candidate_count=_no_candidate_count(plan),
        emitted_messages=(),
        starter_profile_key=_starter_profile_key(plan),
        starter_profile_label=_starter_profile_label(plan),
        metadata=_result_metadata(plan, reason),
    )


def _result_metadata(plan: RytmEngineCycleSendPlan, reason: str) -> dict[str, object]:
    return {
        "guard": GUARD_NAME,
        "reason": reason,
        "style_prompt": plan.style_prompt,
        "discovery": plan.discovery,
        "planned_pad_count": _planned_pad_count(plan),
        "no_candidate_count": _no_candidate_count(plan),
        "starter_profile_key": _starter_profile_key(plan),
        "starter_profile_label": _starter_profile_label(plan),
        "mock_only": True,
        "sends_real_midi": False,
    }


def _messages_from_plan(plan: RytmEngineCycleSendPlan) -> tuple[MidiMessage, ...]:
    if isinstance(plan, RytmEngineCycleStarterPlan):
        return tuple(
            _message_from_starter_event(event, plan)
            for pad in plan.pads
            for event in pad.events
        )
    return tuple(_message_from_pad(pad, plan) for pad in plan.pads)


def _message_from_pad(
    pad: RytmEngineCyclePadPlan,
    plan: RytmEngineCyclePlan,
) -> MidiMessage:
    candidate = pad.top_candidate
    return build_cc_message(
        channel=pad.wire_channel,
        control=MACHINE_CC,
        value=candidate.machine_value,
        metadata={
            "guard": GUARD_NAME,
            "source_kind": "rytm_engine_cycle_guarded_send_dry_run",
            "device": "Analog Rytm MKII",
            "style_prompt": plan.style_prompt,
            "discovery": plan.discovery,
            "pad": pad.pad,
            "midi_channel": pad.midi_channel,
            "role_key": pad.role_key,
            "role_label": pad.role_label,
            "event_role": "engine_cycle_top_candidate",
            "machine_key": candidate.machine_key,
            "machine_label": candidate.machine_label,
            "support_status": candidate.support_status,
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


def _message_from_starter_event(
    event: RytmEngineCycleStarterEvent,
    plan: RytmEngineCycleStarterPlan,
) -> MidiMessage:
    return build_cc_message(
        channel=event.wire_channel,
        control=event.cc,
        value=event.value,
        metadata={
            "guard": GUARD_NAME,
            "source_kind": "rytm_engine_cycle_guarded_send_dry_run",
            "source": event.source,
            "device": "Analog Rytm MKII",
            "style_prompt": plan.style_prompt,
            "discovery": plan.discovery,
            "pad": event.pad,
            "midi_channel": event.midi_channel,
            "role_key": event.role_key,
            "role_label": event.role_label,
            "event_role": event.event_role,
            "parameter": event.parameter_name,
            "machine_key": event.machine_key,
            "machine_label": event.machine_label,
            "machine_value": event.machine_value,
            "support_status": event.support_status,
            "starter_profile_key": plan.starter_profile_key,
            "starter_profile_label": plan.starter_profile_label,
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


def _format_message_line(message: MidiMessage) -> str:
    metadata = message.metadata
    midi_channel = metadata.get("midi_channel", message.channel + 1)
    event_role = metadata.get("event_role")
    if event_role == "starter_parameter":
        return (
            f"- Pad {metadata.get('pad')} / ch {midi_channel} wire {message.channel} / "
            f"starter_parameter / {metadata.get('parameter')} "
            f"CC{message.control} -> {message.value}"
        )
    if event_role == "machine_select":
        return (
            f"- Pad {metadata.get('pad')} / ch {midi_channel} wire {message.channel} / "
            f"machine_select / CC{message.control} -> {message.value} / "
            f"{metadata.get('machine_label')}"
        )
    return (
        f"- Pad {metadata.get('pad')} / ch {midi_channel} wire {message.channel} / "
        f"CC{message.control} -> {message.value} / "
        f"{metadata.get('machine_label')}"
    )


def _emission_policy_lines(result: RytmEngineCycleGuardedSendResult) -> list[str]:
    if result.starter_profile_key is None:
        return ["- emits top-candidate CC15 machine-select events only"]
    return ["- emits CC15 machine-select plus common filter/amp starter values"]


def _is_send_plan(plan: object) -> bool:
    return isinstance(plan, (RytmEngineCyclePlan, RytmEngineCycleStarterPlan))


def _planned_pad_count(plan: RytmEngineCycleSendPlan) -> int:
    if isinstance(plan, RytmEngineCycleStarterPlan):
        return plan.pad_count
    return plan.top_candidate_count


def _no_candidate_count(plan: RytmEngineCycleSendPlan) -> int:
    if isinstance(plan, RytmEngineCycleStarterPlan):
        return 0
    return plan.no_candidate_count


def _starter_profile_key(plan: RytmEngineCycleSendPlan) -> str | None:
    if isinstance(plan, RytmEngineCycleStarterPlan):
        return plan.starter_profile_key
    return None


def _starter_profile_label(plan: RytmEngineCycleSendPlan) -> str | None:
    if isinstance(plan, RytmEngineCycleStarterPlan):
        return plan.starter_profile_label
    return None


__all__ = [
    "GUARD_NAME",
    "RytmEngineCycleGuardedSendResult",
    "RytmEngineCycleSendPlan",
    "build_rytm_engine_cycle_guarded_send_dry_run",
    "execute_rytm_engine_cycle_guarded_send",
    "format_rytm_engine_cycle_guarded_send_dry_run_report",
    "format_rytm_engine_cycle_guarded_send_error",
]
