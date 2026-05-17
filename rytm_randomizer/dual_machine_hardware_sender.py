"""Guarded real-MIDI sender for dual-machine snapshot send plans.

This module is the active counterpart to ``dual_machine_guarded_sender``. It
does not open ports or choose devices; callers inject already-open output
ports. The guard accepts only ready ``DualMachineActiveSendPlan`` instances
after explicit arming and operator confirmation.

Import-safety: no real MIDI backend is imported at module load. ``mido`` is
only reached lazily inside ``midi_io.send_cc`` after all guards have accepted.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .dual_machine_active_send_plan import (
    DualMachineActiveSendPlan,
    DualMachineSendPlanEvent,
)
from .midi_io import send_cc

HARDWARE_SEND_NAME = "dual_machine_hardware_send"
ANALOG_RYTM_DEVICE = "Analog Rytm MKII"
ANALOG_FOUR_DEVICE = "Analog Four MKII"


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class HardwareMidiEmission:
    """One real MIDI message emitted by the guarded hardware sender."""

    device: str
    source: str
    label: str
    channel: int
    control: int
    value: int
    midi_channel: int | None = None


@dataclass(frozen=True)
class DualMachineHardwareSendResult:
    """Result from a guarded hardware send attempt."""

    target: str
    accepted: bool
    reason: str
    plan_ready: bool
    port_name: str
    eligible_message_count: int
    blocked_event_count: int
    emitted_messages: tuple[HardwareMidiEmission, ...]
    mock_only: bool = False
    sends_real_midi: bool = True
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def emitted_message_count(self) -> int:
        return len(self.emitted_messages)


def execute_dual_machine_hardware_send(
    plan: DualMachineActiveSendPlan,
    out: Any,
    *,
    port_name: str,
    armed: bool,
    operator_confirmed: bool,
    sleep: Callable[[float], Any],
) -> DualMachineHardwareSendResult:
    """Execute an active plan through an injected real MIDI output port."""

    if not isinstance(plan, DualMachineActiveSendPlan):
        raise TypeError("plan must be a DualMachineActiveSendPlan")
    if not hasattr(out, "send"):
        raise TypeError("out must expose a send(message) method")

    if not armed:
        return build_dual_machine_hardware_send_refusal(
            plan,
            "missing_arming",
            port_name=port_name,
        )
    if not operator_confirmed:
        return build_dual_machine_hardware_send_refusal(
            plan,
            "missing_operator_confirmation",
            port_name=port_name,
        )
    if plan.target == "both":
        return build_dual_machine_hardware_send_refusal(
            plan,
            "single_target_required",
            port_name=port_name,
        )
    if not plan.ready:
        return build_dual_machine_hardware_send_refusal(
            plan,
            plan.readiness_reason,
            port_name=port_name,
        )

    emitted = []
    for event in plan.events:
        emitted.append(_send_event(event, out, sleep=sleep))

    return DualMachineHardwareSendResult(
        target=plan.target,
        accepted=True,
        reason="accepted_hardware_send",
        plan_ready=plan.ready,
        port_name=port_name,
        eligible_message_count=plan.eligible_message_count,
        blocked_event_count=plan.blocked_event_count,
        emitted_messages=tuple(emitted),
        metadata=_result_metadata(plan, "accepted_hardware_send", port_name),
    )


def execute_dual_machine_dual_port_hardware_send(
    plan: DualMachineActiveSendPlan,
    outputs_by_device: Mapping[str, Any],
    *,
    port_names_by_device: Mapping[str, str],
    armed: bool,
    operator_confirmed: bool,
    sleep: Callable[[float], Any],
) -> DualMachineHardwareSendResult:
    """Execute a ready both-target plan through two injected output ports."""

    if not isinstance(plan, DualMachineActiveSendPlan):
        raise TypeError("plan must be a DualMachineActiveSendPlan")
    port_name = _format_dual_port_name(port_names_by_device)

    if not armed:
        return build_dual_machine_hardware_send_refusal(
            plan,
            "missing_arming",
            port_name=port_name,
        )
    if not operator_confirmed:
        return build_dual_machine_hardware_send_refusal(
            plan,
            "missing_operator_confirmation",
            port_name=port_name,
        )
    if plan.target != "both":
        return build_dual_machine_hardware_send_refusal(
            plan,
            "both_target_required",
            port_name=port_name,
        )
    if not plan.ready:
        return build_dual_machine_hardware_send_refusal(
            plan,
            plan.readiness_reason,
            port_name=port_name,
        )

    missing = _missing_device_outputs(plan, outputs_by_device)
    if missing:
        return build_dual_machine_hardware_send_refusal(
            plan,
            "missing_device_output",
            port_name=port_name,
        )

    emitted = []
    for event in plan.events:
        emitted.append(
            _send_event(
                event,
                outputs_by_device[event.device],
                sleep=sleep,
            )
        )

    return DualMachineHardwareSendResult(
        target=plan.target,
        accepted=True,
        reason="accepted_hardware_send",
        plan_ready=plan.ready,
        port_name=port_name,
        eligible_message_count=plan.eligible_message_count,
        blocked_event_count=plan.blocked_event_count,
        emitted_messages=tuple(emitted),
        metadata=_result_metadata(plan, "accepted_hardware_send", port_name),
    )


def build_dual_machine_hardware_send_refusal(
    plan: DualMachineActiveSendPlan,
    reason: str,
    *,
    port_name: str = "<not-opened>",
) -> DualMachineHardwareSendResult:
    """Build a deterministic refusal result without touching a port."""

    if not isinstance(plan, DualMachineActiveSendPlan):
        raise TypeError("plan must be a DualMachineActiveSendPlan")

    return DualMachineHardwareSendResult(
        target=plan.target,
        accepted=False,
        reason=reason,
        plan_ready=plan.ready,
        port_name=port_name,
        eligible_message_count=plan.eligible_message_count,
        blocked_event_count=plan.blocked_event_count,
        emitted_messages=(),
        metadata=_result_metadata(plan, reason, port_name),
    )


def format_dual_machine_hardware_send_report(
    result: DualMachineHardwareSendResult,
) -> list[str]:
    """Format a deterministic active hardware send report."""

    lines = [
        "RytmRandomizer armed Dual-Machine Hardware Send Report",
        f"Target: {result.target}",
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
            "- single-target hardware send or validated dual-port both-target send",
            "- requires --arm",
            "- requires exact SEND confirmation",
            "- real MIDI sending happened only after --arm and SEND confirmation",
            "- blocked plans emit no partial messages",
            "Safety:",
            "- active guarded sender",
            "- no SysEx writes",
            "- no live SysEx receive",
            "- no command execution",
        ]
    )
    return lines


def format_dual_machine_hardware_send_error(message: str) -> list[str]:
    """Format deterministic active hardware send errors."""

    return [
        "RytmRandomizer armed Dual-Machine Hardware Send Report",
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
    event: DualMachineSendPlanEvent,
    out: Any,
    *,
    sleep: Callable[[float], Any],
) -> HardwareMidiEmission:
    if not event.eligible or event.message_type != "cc":
        raise ValueError("only eligible mapped CC events can be emitted")

    send_cc(
        out,
        event.control,
        event.value,
        channel=event.channel,
        sleep=sleep,
    )
    return HardwareMidiEmission(
        device=event.device,
        source=event.source,
        label=event.label,
        channel=event.channel,
        control=event.control,
        value=event.value,
        midi_channel=event.midi_channel,
    )


def _result_metadata(
    plan: DualMachineActiveSendPlan,
    reason: str,
    port_name: str,
) -> dict[str, object]:
    return {
        "guard": HARDWARE_SEND_NAME,
        "target": plan.target,
        "reason": reason,
        "plan_ready": plan.ready,
        "port_name": port_name,
        "eligible_message_count": plan.eligible_message_count,
        "blocked_event_count": plan.blocked_event_count,
        "mock_only": False,
        "sends_real_midi": True,
    }


def _missing_device_outputs(
    plan: DualMachineActiveSendPlan,
    outputs_by_device: Mapping[str, Any],
) -> tuple[str, ...]:
    devices = tuple(dict.fromkeys(event.device for event in plan.events))
    return tuple(
        device
        for device in devices
        if device not in outputs_by_device or not hasattr(outputs_by_device[device], "send")
    )


def _format_dual_port_name(port_names_by_device: Mapping[str, str]) -> str:
    rytm_name = port_names_by_device.get(ANALOG_RYTM_DEVICE, "<missing-rytm>")
    a4_name = port_names_by_device.get(ANALOG_FOUR_DEVICE, "<missing-analog-four>")
    return f"{ANALOG_RYTM_DEVICE}={rytm_name}; {ANALOG_FOUR_DEVICE}={a4_name}"


def _format_emission_line(message: HardwareMidiEmission) -> str:
    midi_channel = message.midi_channel if message.midi_channel is not None else message.channel + 1
    return (
        f"- {message.device} / ch {midi_channel} wire {message.channel} / "
        f"CC{message.control} -> {message.value} / {message.label}"
    )


__all__ = [
    "ANALOG_FOUR_DEVICE",
    "ANALOG_RYTM_DEVICE",
    "DualMachineHardwareSendResult",
    "HardwareMidiEmission",
    "build_dual_machine_hardware_send_refusal",
    "execute_dual_machine_dual_port_hardware_send",
    "execute_dual_machine_hardware_send",
    "format_dual_machine_hardware_send_error",
    "format_dual_machine_hardware_send_report",
]
