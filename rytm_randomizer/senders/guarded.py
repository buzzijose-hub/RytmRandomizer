"""Generic guarded sender for Device mutation plans."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..devices import Device


@dataclass(frozen=True)
class GuardedSendResult:
    """Result of a dry-run/readiness-checked send attempt."""

    device_id: str
    ready: bool
    sent_count: int
    reason: str = ""
    messages: tuple[object, ...] = field(default_factory=tuple)


def guarded_send(device: Device, plan: object) -> GuardedSendResult:
    """Render ``plan`` through ``device`` without opening hardware."""

    ready = bool(getattr(plan, "ready", False))
    reason = str(getattr(plan, "readiness_reason", "plan is not ready"))
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
