"""Guarded real-MIDI sender for Analog Four runtime plans.

This module does not open ports or choose devices. Callers inject an already
open output port, and real MIDI sending is refused unless the caller supplies
explicit arming plus operator confirmation.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from ..midi_io import send_cc
from .runtime_plan import AnalogFourRuntimeEvent, AnalogFourRuntimePlan

HARDWARE_SEND_NAME = "analog_four_runtime_hardware_send"


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class AnalogFourRuntimeHardwareEmission:
    """One real MIDI CC message emitted by the A4 runtime hardware sender."""

    track: int
    midi_channel: int
    channel: int
    control: int
    value: int
    parameter_name: str
    role: str


@dataclass(frozen=True)
class AnalogFourRuntimeHardwareSendResult:
    """Result from a guarded A4 runtime hardware send attempt."""

    device: str
    accepted: bool
    reason: str
    plan_ready: bool
    port_name: str
    starter_profile_key: str
    starter_profile_label: str
    eligible_message_count: int
    blocked_event_count: int
    emitted_messages: tuple[AnalogFourRuntimeHardwareEmission, ...]
    mock_only: bool = False
    sends_real_midi: bool = True
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def emitted_message_count(self) -> int:
        return len(self.emitted_messages)


def execute_analog_four_runtime_hardware_send(
    plan: AnalogFourRuntimePlan,
    out: Any,
    *,
    port_name: str,
    armed: bool,
    operator_confirmed: bool,
    sleep: Callable[[float], Any],
) -> AnalogFourRuntimeHardwareSendResult:
    """Execute an A4 runtime plan through an injected output port."""

    if not isinstance(plan, AnalogFourRuntimePlan):
        raise TypeError("plan must be an AnalogFourRuntimePlan")
    if not hasattr(out, "send"):
        raise TypeError("out must expose a send(message) method")

    events = tuple(event for track in plan.tracks for event in track.events)
    if not armed:
        return build_analog_four_runtime_hardware_send_refusal(
            plan,
            "missing_arming",
            port_name=port_name,
        )
    if not operator_confirmed:
        return build_analog_four_runtime_hardware_send_refusal(
            plan,
            "missing_operator_confirmation",
            port_name=port_name,
        )

    emitted = tuple(_send_event(event, out, sleep=sleep) for event in events)
    return AnalogFourRuntimeHardwareSendResult(
        device=plan.device,
        accepted=True,
        reason="accepted_hardware_send",
        plan_ready=True,
        port_name=port_name,
        starter_profile_key=plan.starter_profile_key,
        starter_profile_label=plan.starter_profile_label,
        eligible_message_count=len(events),
        blocked_event_count=0,
        emitted_messages=emitted,
        metadata=_result_metadata(plan, "accepted_hardware_send", port_name, len(events), 0),
    )


def build_analog_four_runtime_hardware_send_refusal(
    plan: AnalogFourRuntimePlan,
    reason: str,
    *,
    port_name: str = "<not-opened>",
) -> AnalogFourRuntimeHardwareSendResult:
    """Build a deterministic refusal result without touching a port."""

    if not isinstance(plan, AnalogFourRuntimePlan):
        raise TypeError("plan must be an AnalogFourRuntimePlan")

    eligible_message_count = sum(len(track.events) for track in plan.tracks)
    return AnalogFourRuntimeHardwareSendResult(
        device=plan.device,
        accepted=False,
        reason=reason,
        plan_ready=True,
        port_name=port_name,
        starter_profile_key=plan.starter_profile_key,
        starter_profile_label=plan.starter_profile_label,
        eligible_message_count=eligible_message_count,
        blocked_event_count=0,
        emitted_messages=(),
        metadata=_result_metadata(plan, reason, port_name, eligible_message_count, 0),
    )


def format_analog_four_runtime_hardware_send_report(
    result: AnalogFourRuntimeHardwareSendResult,
) -> list[str]:
    """Format a deterministic active A4 runtime hardware send report."""

    lines = [
        "RytmRandomizer armed Analog Four Runtime Hardware Send Report",
        f"Device: {result.device}",
        f"Starter profile: {result.starter_profile_label} / {result.starter_profile_key}",
        f"Accepted: {result.accepted}",
        f"Reason: {result.reason}",
        f"Plan ready: {result.plan_ready}",
        f"Port: {result.port_name}",
        f"Eligible mapped CC messages: {result.eligible_message_count}",
        f"Blocked candidate events: {result.blocked_event_count}",
        f"Emitted real MIDI messages: {result.emitted_message_count}",
        "Hardware emission preview:",
    ]
    if result.emitted_messages:
        lines.extend(_format_emission_line(message) for message in result.emitted_messages)
    else:
        lines.append("- no messages emitted")
    lines.extend(
        [
            "Guard policy:",
            "- A4-only runtime hardware send",
            "- requires --arm",
            "- requires exact SEND confirmation",
            "- opens one selected Analog Four output only",
            "- real MIDI sending happened only after --arm and SEND confirmation",
            "- blocked plans emit no partial messages",
            "Safety:",
            "- active guarded sender",
            "- no Rytm MIDI sending",
            "- no SysEx writes",
            "- no live SysEx receive",
            "- no NRPN sending",
            "- no CV track mutation",
            "- no command execution",
        ]
    )
    return lines


def format_analog_four_runtime_hardware_send_error(message: str) -> list[str]:
    """Format deterministic active A4 runtime hardware send errors."""

    return [
        "RytmRandomizer armed Analog Four Runtime Hardware Send Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- active guarded sender",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
    ]


def _send_event(
    event: AnalogFourRuntimeEvent,
    out: Any,
    *,
    sleep: Callable[[float], Any],
) -> AnalogFourRuntimeHardwareEmission:
    send_cc(out, event.cc, event.value, channel=event.wire_channel, sleep=sleep)
    return AnalogFourRuntimeHardwareEmission(
        track=event.track,
        midi_channel=event.midi_channel,
        channel=event.wire_channel,
        control=event.cc,
        value=event.value,
        parameter_name=event.parameter_name,
        role=event.role_label,
    )


def _result_metadata(
    plan: AnalogFourRuntimePlan,
    reason: str,
    port_name: str,
    eligible_message_count: int,
    blocked_event_count: int,
) -> dict[str, object]:
    return {
        "guard": HARDWARE_SEND_NAME,
        "device": plan.device,
        "reason": reason,
        "port_name": port_name,
        "starter_profile_key": plan.starter_profile_key,
        "starter_profile_label": plan.starter_profile_label,
        "eligible_message_count": eligible_message_count,
        "blocked_event_count": blocked_event_count,
        "mock_only": False,
        "sends_real_midi": True,
    }


def _format_emission_line(message: AnalogFourRuntimeHardwareEmission) -> str:
    return (
        f"- Track {message.track} ch {message.midi_channel} wire {message.channel} / "
        f"{message.parameter_name} CC{message.control} -> {message.value}"
    )


__all__ = [
    "AnalogFourRuntimeHardwareEmission",
    "AnalogFourRuntimeHardwareSendResult",
    "HARDWARE_SEND_NAME",
    "build_analog_four_runtime_hardware_send_refusal",
    "execute_analog_four_runtime_hardware_send",
    "format_analog_four_runtime_hardware_send_error",
    "format_analog_four_runtime_hardware_send_report",
]
