"""Explicit, exact-port transport for a precompiled RUSH01 MIDI plan."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, cast

from ..midi_io import Sender, send_cc
from ..real_midi_adapter import RealMidiPortError
from ..style_analysis.rush01_midi_compiler import (
    STATUS_INVALID_SPEC_FIELD,
    STATUS_READY,
    Rush01MidiPlan,
    validate_rush01_plan_safety,
)


class Rush01OutputPort(Sender, Protocol):
    """Minimal send/close surface needed by the RUSH01 apply boundary."""

    def close(self) -> None:
        """Close the explicitly opened port."""


class Rush01PortProvider(Protocol):
    """Exact-name output discovery/opening surface used by the apply tool."""

    def list_output_names(self) -> tuple[str, ...]:
        """Return available output names without selecting one."""

    def open_output(self, port_name: str) -> Rush01OutputPort:
        """Open exactly ``port_name`` or fail."""


SleepCallable = Callable[[float], object]


@dataclass(frozen=True)
class Rush01ApplyResult:
    """Outcome of one explicitly confirmed transport operation."""

    device: str
    port_name: str
    field_count: int
    message_count: int
    sent_midi: bool


def open_exact_output(provider: Rush01PortProvider, port_name: str) -> Rush01OutputPort:
    """Open one exact, unique configured output name without fuzzy matching."""

    if not isinstance(port_name, str) or not port_name:
        raise RealMidiPortError("midi_output_port_required")
    matches = tuple(name for name in provider.list_output_names() if name == port_name)
    if not matches:
        raise RealMidiPortError(f"unknown_midi_output_port: {port_name}")
    if len(matches) > 1:
        raise RealMidiPortError(f"ambiguous_midi_output_port_name: {port_name}")
    return provider.open_output(port_name)


def send_rush01_plan(
    plan: Rush01MidiPlan,
    out: Sender,
    *,
    delay_ms: int,
    sleep: SleepCallable,
) -> Rush01ApplyResult:
    """Send only configured ready CC bytes from one reviewed plan."""

    if not isinstance(plan, Rush01MidiPlan):
        raise TypeError("plan must be a Rush01MidiPlan")
    if isinstance(delay_ms, bool) or not isinstance(delay_ms, int) or not 0 <= delay_ms <= 10_000:
        raise ValueError("delay_ms must be an integer in 0..10000")
    validate_rush01_plan_for_apply(plan)

    ready_fields = tuple(field for field in plan.fields if field.status == STATUS_READY)
    messages = tuple(
        message for field in ready_fields for message in (field.ordered_midi_bytes or ())
    )
    if not messages:
        raise ValueError("RUSH01 plan has no configured ready MIDI messages")

    delay_seconds = delay_ms / 1000.0
    for index, (status, controller, value) in enumerate(messages):
        send_cc(
            out,
            controller,
            value,
            channel=status & 0x0F,
            sleep=_no_sleep,
        )
        if index + 1 < len(messages):
            sleep(delay_seconds)
    return Rush01ApplyResult(
        device=plan.device,
        port_name=plan.output_port,
        field_count=len(ready_fields),
        message_count=len(messages),
        sent_midi=True,
    )


def apply_rush01_plan(
    plan: Rush01MidiPlan,
    provider: Rush01PortProvider,
    *,
    delay_ms: int,
    sleep: SleepCallable,
) -> Rush01ApplyResult:
    """Open the exact configured port, send, and always close it."""

    validate_rush01_plan_for_apply(plan)
    port = open_exact_output(provider, cast(str, plan.output_port))
    try:
        return send_rush01_plan(plan, port, delay_ms=delay_ms, sleep=sleep)
    finally:
        port.close()


def _no_sleep(_seconds: float) -> None:
    return None


def validate_rush01_plan_for_apply(plan: Rush01MidiPlan) -> None:
    """Fail closed before a real provider is constructed or queried."""

    if not isinstance(plan, Rush01MidiPlan):
        raise TypeError("plan must be a Rush01MidiPlan")
    if not plan.configuration_ready or plan.output_port is None:
        raise ValueError("RUSH01 plan requires exact port and track-channel configuration")
    if any(field.status == STATUS_INVALID_SPEC_FIELD for field in plan.fields):
        raise ValueError("RUSH01 plan contains invalid specification fields")
    validate_rush01_plan_safety(plan)


__all__ = [
    "Rush01ApplyResult",
    "Rush01OutputPort",
    "Rush01PortProvider",
    "apply_rush01_plan",
    "open_exact_output",
    "send_rush01_plan",
    "validate_rush01_plan_for_apply",
]
