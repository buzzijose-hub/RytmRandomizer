"""Generic arm-gated hardware sender for Device mutation plans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..devices import Device


class TripleSender(Protocol):
    """Boundary for sending rendered CC triples in tests and production."""

    def send(self, message: tuple[int, int, int]) -> None: ...


@dataclass(frozen=True)
class HardwareSendResult:
    """Result of an arm-gated hardware send attempt."""

    device_id: str
    ready: bool
    sent_count: int
    reason: str = ""


def hardware_send(
    device: Device,
    plan: object,
    *,
    sender: TripleSender,
    armed: bool,
) -> HardwareSendResult:
    """Send a plan to hardware only when armed and ready."""

    if not armed:
        return HardwareSendResult(
            device_id=device.device_id,
            ready=False,
            sent_count=0,
            reason="hardware send requires --arm",
        )

    ready = bool(getattr(plan, "ready", False))
    reason = str(getattr(plan, "readiness_reason", "plan is not ready"))
    if not ready:
        return HardwareSendResult(
            device_id=device.device_id,
            ready=False,
            sent_count=0,
            reason=reason,
        )

    triples = tuple(device.to_cc_messages(plan))
    for triple in triples:
        sender.send(triple)
    return HardwareSendResult(
        device_id=device.device_id,
        ready=True,
        sent_count=len(triples),
        reason="",
    )
