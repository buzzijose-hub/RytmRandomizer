"""Guarded real-MIDI sender for Rytm snapshot essence send plans.

This module is the active counterpart to ``snapshot_essence_guarded_sender``.
It does not open ports or choose devices; callers inject an already-open output
port. The guard accepts only a ready ``SnapshotEssenceSendPlan`` after explicit
arming and exact operator confirmation.

Import-safety: no real MIDI backend is imported at module load. ``mido`` is
only reached lazily inside ``midi_io.send_cc`` after all guards have accepted.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from ..midi_io import send_cc
from .snapshot_send_plan import (
    SnapshotEssenceSendPlan,
    SnapshotEssenceSendPlanEvent,
)

HARDWARE_SEND_NAME = "snapshot_essence_hardware_send"


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class SnapshotEssenceHardwareEmission:
    """One real MIDI CC message emitted by the guarded hardware sender."""

    pad: int
    role_label: str
    machine_label: str
    event_role: str
    label: str
    channel: int
    control: int
    value: int
    midi_channel: int
    source: str
    baseline_value: int | None = None
    delta: int | None = None


@dataclass(frozen=True)
class SnapshotEssenceHardwareSendResult:
    """Result from a guarded snapshot essence hardware send attempt."""

    accepted: bool
    reason: str
    plan_ready: bool
    source_path: str
    slot_number: int
    kit_name: str
    style_prompt: str
    port_name: str
    eligible_event_count: int
    blocked_event_count: int
    emitted_messages: tuple[SnapshotEssenceHardwareEmission, ...]
    mock_only: bool = False
    sends_real_midi: bool = True
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def emitted_message_count(self) -> int:
        return len(self.emitted_messages)


def execute_snapshot_essence_hardware_send(
    plan: SnapshotEssenceSendPlan,
    out: Any,
    *,
    port_name: str,
    armed: bool,
    operator_confirmed: bool,
    sleep: Callable[[float], Any],
) -> SnapshotEssenceHardwareSendResult:
    """Execute a ready snapshot essence send plan through an injected port."""

    if not isinstance(plan, SnapshotEssenceSendPlan):
        raise TypeError("plan must be a SnapshotEssenceSendPlan")
    if not hasattr(out, "send"):
        raise TypeError("out must expose a send(message) method")

    if not armed:
        return build_snapshot_essence_hardware_send_refusal(
            plan,
            "missing_arming",
            port_name=port_name,
        )
    if not operator_confirmed:
        return build_snapshot_essence_hardware_send_refusal(
            plan,
            "missing_operator_confirmation",
            port_name=port_name,
        )
    if not plan.ready:
        return build_snapshot_essence_hardware_send_refusal(
            plan,
            "plan_not_ready",
            port_name=port_name,
        )
    if plan.blocked_event_count:
        return build_snapshot_essence_hardware_send_refusal(
            plan,
            "blocked_by_ineligible_events",
            port_name=port_name,
        )

    emitted = []
    for event in plan.events:
        emitted.append(_send_event(event, out, sleep=sleep))

    return SnapshotEssenceHardwareSendResult(
        accepted=True,
        reason="accepted_hardware_send",
        plan_ready=plan.ready,
        source_path=plan.source_path,
        slot_number=plan.slot_number,
        kit_name=plan.kit_name,
        style_prompt=plan.style_prompt,
        port_name=port_name,
        eligible_event_count=plan.eligible_event_count,
        blocked_event_count=plan.blocked_event_count,
        emitted_messages=tuple(emitted),
        metadata=_result_metadata(plan, "accepted_hardware_send", port_name),
    )


def build_snapshot_essence_hardware_send_refusal(
    plan: SnapshotEssenceSendPlan,
    reason: str,
    *,
    port_name: str = "<not-opened>",
) -> SnapshotEssenceHardwareSendResult:
    """Build a deterministic refusal result without touching a port."""

    if not isinstance(plan, SnapshotEssenceSendPlan):
        raise TypeError("plan must be a SnapshotEssenceSendPlan")

    return SnapshotEssenceHardwareSendResult(
        accepted=False,
        reason=reason,
        plan_ready=plan.ready,
        source_path=plan.source_path,
        slot_number=plan.slot_number,
        kit_name=plan.kit_name,
        style_prompt=plan.style_prompt,
        port_name=port_name,
        eligible_event_count=plan.eligible_event_count,
        blocked_event_count=plan.blocked_event_count,
        emitted_messages=(),
        metadata=_result_metadata(plan, reason, port_name),
    )


def format_snapshot_essence_hardware_send_report(
    result: SnapshotEssenceHardwareSendResult,
) -> list[str]:
    """Format a deterministic active hardware send report."""

    lines = [
        "RytmRandomizer armed Snapshot Essence Hardware Send Report",
        f"Source path: {result.source_path}",
        f"Source slot: {result.slot_number}",
        f"Kit: {result.kit_name or '<blank>'}",
        f"Style prompt: {result.style_prompt}",
        f"Accepted: {result.accepted}",
        f"Reason: {result.reason}",
        f"Plan ready: {result.plan_ready}",
        f"Port: {result.port_name}",
        f"Eligible snapshot essence events: {result.eligible_event_count}",
        f"Blocked snapshot essence events: {result.blocked_event_count}",
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
            "- Rytm snapshot essence hardware send only",
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


def format_snapshot_essence_hardware_send_error(message: str) -> list[str]:
    """Format deterministic active hardware send errors."""

    return [
        "RytmRandomizer armed Snapshot Essence Hardware Send Report",
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
    event: SnapshotEssenceSendPlanEvent,
    out: Any,
    *,
    sleep: Callable[[float], Any],
) -> SnapshotEssenceHardwareEmission:
    if not event.eligible:
        raise ValueError("only eligible snapshot essence events can be emitted")

    send_cc(
        out,
        event.control,
        event.value,
        channel=event.wire_channel,
        sleep=sleep,
    )
    return SnapshotEssenceHardwareEmission(
        pad=event.pad,
        role_label=event.role_label,
        machine_label=event.machine_label,
        event_role=event.event_role,
        label=event.label,
        channel=event.wire_channel,
        control=event.control,
        value=event.value,
        midi_channel=event.midi_channel,
        source=event.source,
        baseline_value=event.baseline_value,
        delta=event.delta,
    )


def _result_metadata(
    plan: SnapshotEssenceSendPlan,
    reason: str,
    port_name: str,
) -> dict[str, object]:
    return {
        "guard": HARDWARE_SEND_NAME,
        "reason": reason,
        "plan_ready": plan.ready,
        "source_path": plan.source_path,
        "slot_number": plan.slot_number,
        "kit_name": plan.kit_name,
        "style_prompt": plan.style_prompt,
        "port_name": port_name,
        "eligible_event_count": plan.eligible_event_count,
        "blocked_event_count": plan.blocked_event_count,
        "mock_only": False,
        "sends_real_midi": True,
    }


def _format_emission_line(message: SnapshotEssenceHardwareEmission) -> str:
    return (
        f"- Analog Rytm MKII / Pad {message.pad} / ch {message.midi_channel} "
        f"wire {message.channel} / CC{message.control} -> {message.value} / "
        f"{message.event_role} / {message.label}"
    )


__all__ = [
    "HARDWARE_SEND_NAME",
    "SnapshotEssenceHardwareEmission",
    "SnapshotEssenceHardwareSendResult",
    "build_snapshot_essence_hardware_send_refusal",
    "execute_snapshot_essence_hardware_send",
    "format_snapshot_essence_hardware_send_error",
    "format_snapshot_essence_hardware_send_report",
]
