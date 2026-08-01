"""Pure RUSH01 plan validation and rendering for the armed send seam."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final, Protocol, runtime_checkable

from .armed_apply import PlanRenderer

_STATUS_READY: Final[str] = "ready"


class _Rush01MidiFieldLike(Protocol):
    """Read-only field surface consumed by the passive renderer."""

    status: str
    ordered_midi_bytes: tuple[tuple[int, int, int], ...] | None


@runtime_checkable
class _Rush01MidiPlanLike(Protocol):
    """Structural plan contract that keeps senders independent of compilers."""

    @property
    def ready(self) -> bool:
        """Whether the compiler approved the plan for armed delivery."""

        ...

    @property
    def readiness_reason(self) -> str:
        """Return the compiler's first fail-closed readiness reason."""

        ...

    @property
    def fields(self) -> Sequence[_Rush01MidiFieldLike]:
        """Return the compiled semantic fields in deterministic order."""

        ...


def render_rush01_plan(plan: object) -> tuple[tuple[int, int, int], ...]:
    """Render configured ready fields as neutral CC triples without I/O."""

    if not isinstance(plan, _Rush01MidiPlanLike):
        raise TypeError("plan must be a Rush01MidiPlan")
    validate_rush01_plan_for_apply(plan)
    messages: list[tuple[int, int, int]] = []
    for field in plan.fields:
        if field.status != _STATUS_READY:
            continue
        if not field.ordered_midi_bytes:
            raise ValueError("ready RUSH01 fields require compiled MIDI messages")
        for message in field.ordered_midi_bytes:
            status, controller, value = message
            if status & 0xF0 != 0xB0:
                raise ValueError("only MIDI control-change messages are allowed")
            if not 0 <= controller <= 119:
                raise ValueError("MIDI channel-mode and system messages are forbidden")
            if not 0 <= value <= 127:
                raise ValueError("MIDI data bytes must be in 0..127")
            messages.append((status & 0x0F, controller, value))
    if not messages:
        raise ValueError("RUSH01 plan has no configured ready MIDI messages")
    return tuple(messages)


def validate_rush01_plan_for_apply(plan: object) -> None:
    """Fail closed before an armed session constructs or queries a provider."""

    if not isinstance(plan, _Rush01MidiPlanLike):
        raise TypeError("plan must be a Rush01MidiPlan")
    if not plan.ready:
        raise ValueError(plan.readiness_reason or "RUSH01 plan is not ready for apply")


RUSH01_PLAN_RENDERER: PlanRenderer = render_rush01_plan

__all__ = [
    "RUSH01_PLAN_RENDERER",
    "render_rush01_plan",
    "validate_rush01_plan_for_apply",
]
