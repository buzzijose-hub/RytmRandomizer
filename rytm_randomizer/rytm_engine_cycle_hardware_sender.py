"""Guarded real-MIDI sender for Rytm engine-cycle plans.

This module is the active counterpart to ``rytm_engine_cycle_guarded_sender``.
It does not open ports or choose devices; callers inject an already-open output
port. The guard accepts only a fully resolved ``RytmEngineCyclePlan`` after
explicit arming and exact operator confirmation.

Import-safety: no real MIDI backend is imported at module load. ``mido`` is
only reached lazily inside ``midi_io.send_cc`` after all guards have accepted.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .data import MACHINE_CC
from .midi_io import send_cc
from .rytm_engine_cycle_plan import (
    RytmEngineCyclePadPlan,
    RytmEngineCyclePlan,
)

HARDWARE_SEND_NAME = "rytm_engine_cycle_hardware_send"


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class RytmEngineCycleHardwareEmission:
    """One real MIDI CC15 engine-select message emitted by the hardware sender."""

    pad: int
    role_label: str
    machine_key: str
    machine_label: str
    support_status: str
    channel: int
    control: int
    value: int
    midi_channel: int


@dataclass(frozen=True)
class RytmEngineCycleHardwareSendResult:
    """Result from a guarded Rytm engine-cycle hardware send attempt."""

    accepted: bool
    reason: str
    style_prompt: str
    discovery: float
    port_name: str
    planned_pad_count: int
    no_candidate_count: int
    emitted_messages: tuple[RytmEngineCycleHardwareEmission, ...]
    mock_only: bool = False
    sends_real_midi: bool = True
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def emitted_message_count(self) -> int:
        return len(self.emitted_messages)


def execute_rytm_engine_cycle_hardware_send(
    plan: RytmEngineCyclePlan,
    out: Any,
    *,
    port_name: str,
    armed: bool,
    operator_confirmed: bool,
    sleep: Callable[[float], Any],
) -> RytmEngineCycleHardwareSendResult:
    """Execute a Rytm engine-cycle plan through an injected output port."""

    if not isinstance(plan, RytmEngineCyclePlan):
        raise TypeError("plan must be a RytmEngineCyclePlan")
    if not hasattr(out, "send"):
        raise TypeError("out must expose a send(message) method")

    if not armed:
        return build_rytm_engine_cycle_hardware_send_refusal(
            plan,
            "missing_arming",
            port_name=port_name,
        )
    if not operator_confirmed:
        return build_rytm_engine_cycle_hardware_send_refusal(
            plan,
            "missing_operator_confirmation",
            port_name=port_name,
        )
    if plan.no_candidate_count:
        return build_rytm_engine_cycle_hardware_send_refusal(
            plan,
            "plan_has_unresolved_pads",
            port_name=port_name,
        )

    emitted = []
    for pad in plan.pads:
        emitted.append(_send_pad(pad, out, sleep=sleep))

    return RytmEngineCycleHardwareSendResult(
        accepted=True,
        reason="accepted_hardware_send",
        style_prompt=plan.style_prompt,
        discovery=plan.discovery,
        port_name=port_name,
        planned_pad_count=plan.top_candidate_count,
        no_candidate_count=plan.no_candidate_count,
        emitted_messages=tuple(emitted),
        metadata=_result_metadata(plan, "accepted_hardware_send", port_name),
    )


def build_rytm_engine_cycle_hardware_send_refusal(
    plan: RytmEngineCyclePlan,
    reason: str,
    *,
    port_name: str = "<not-opened>",
) -> RytmEngineCycleHardwareSendResult:
    """Build a deterministic refusal result without touching a port."""

    if not isinstance(plan, RytmEngineCyclePlan):
        raise TypeError("plan must be a RytmEngineCyclePlan")

    return RytmEngineCycleHardwareSendResult(
        accepted=False,
        reason=reason,
        style_prompt=plan.style_prompt,
        discovery=plan.discovery,
        port_name=port_name,
        planned_pad_count=plan.top_candidate_count,
        no_candidate_count=plan.no_candidate_count,
        emitted_messages=(),
        metadata=_result_metadata(plan, reason, port_name),
    )


def format_rytm_engine_cycle_hardware_send_report(
    result: RytmEngineCycleHardwareSendResult,
) -> list[str]:
    """Format a deterministic active Rytm engine-cycle send report."""

    lines = [
        "RytmRandomizer armed Rytm Engine Cycle Hardware Send Report",
        f"Style prompt: {result.style_prompt}",
        f"Discovery: {result.discovery:.2f}",
        f"Accepted: {result.accepted}",
        f"Reason: {result.reason}",
        f"Port: {result.port_name}",
        f"Planned pads: {result.planned_pad_count}",
        f"Unresolved pads: {result.no_candidate_count}",
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
            "- Rytm engine-cycle hardware send only",
            "- sends CC15 machine-select events only",
            "- requires --arm",
            "- requires exact SEND confirmation",
            "- real MIDI sending happened only after --arm and SEND confirmation",
            "- unresolved plans emit no partial messages",
            "Safety:",
            "- active guarded sender",
            "- no SysEx writes",
            "- no live SysEx receive",
            "- no command execution",
        ]
    )
    return lines


def format_rytm_engine_cycle_hardware_send_error(message: str) -> list[str]:
    """Format deterministic active hardware send errors."""

    return [
        "RytmRandomizer armed Rytm Engine Cycle Hardware Send Report",
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


def _send_pad(
    pad: RytmEngineCyclePadPlan,
    out: Any,
    *,
    sleep: Callable[[float], Any],
) -> RytmEngineCycleHardwareEmission:
    candidate = pad.top_candidate
    send_cc(
        out,
        MACHINE_CC,
        candidate.machine_value,
        channel=pad.wire_channel,
        sleep=sleep,
    )
    return RytmEngineCycleHardwareEmission(
        pad=pad.pad,
        role_label=pad.role_label,
        machine_key=candidate.machine_key,
        machine_label=candidate.machine_label,
        support_status=candidate.support_status,
        channel=pad.wire_channel,
        control=MACHINE_CC,
        value=candidate.machine_value,
        midi_channel=pad.midi_channel,
    )


def _result_metadata(
    plan: RytmEngineCyclePlan,
    reason: str,
    port_name: str,
) -> dict[str, object]:
    return {
        "guard": HARDWARE_SEND_NAME,
        "reason": reason,
        "style_prompt": plan.style_prompt,
        "discovery": plan.discovery,
        "port_name": port_name,
        "planned_pad_count": plan.top_candidate_count,
        "no_candidate_count": plan.no_candidate_count,
        "mock_only": False,
        "sends_real_midi": True,
    }


def _format_emission_line(message: RytmEngineCycleHardwareEmission) -> str:
    return (
        f"- Pad {message.pad} / ch {message.midi_channel} wire {message.channel} / "
        f"CC{message.control} -> {message.value} / {message.machine_label}"
    )


__all__ = [
    "HARDWARE_SEND_NAME",
    "RytmEngineCycleHardwareEmission",
    "RytmEngineCycleHardwareSendResult",
    "build_rytm_engine_cycle_hardware_send_refusal",
    "execute_rytm_engine_cycle_hardware_send",
    "format_rytm_engine_cycle_hardware_send_error",
    "format_rytm_engine_cycle_hardware_send_report",
]
