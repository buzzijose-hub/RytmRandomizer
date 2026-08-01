"""Generic guarded sender for Device mutation plans."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..devices import Device
from .armed_apply import plan_readiness


@dataclass(frozen=True)
class GuardedSendResult:
    """Result of a dry-run/readiness-checked send attempt."""

    device_id: str
    ready: bool
    sent_count: int
    reason: str = ""
    messages: tuple[object, ...] = field(default_factory=tuple)


def guarded_send(device: Device, plan: object) -> GuardedSendResult:
    """Render ``plan`` through ``device`` without opening hardware.

    Plan readiness is validated through the ArmedApply seam's shared
    :func:`~rytm_randomizer.senders.armed_apply.plan_readiness` duck so
    the guarded (mock) and armed (hardware) paths can never drift apart.
    """

    ready, reason = plan_readiness(plan)
    if not ready:
        return GuardedSendResult(
            device_id=device.device_id,
            ready=False,
            sent_count=0,
            reason=reason,
            messages=(),
        )

    messages = tuple(device.to_mock_messages(plan))
    return GuardedSendResult(
        device_id=device.device_id,
        ready=True,
        sent_count=len(messages),
        reason="",
        messages=messages,
    )
