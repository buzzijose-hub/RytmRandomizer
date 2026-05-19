"""Generic senders that consume registered Device strategies."""

from __future__ import annotations

from .guarded import GuardedSendResult, guarded_send
from .hardware import HardwareSendResult, TripleSender, hardware_send

__all__ = [
    "GuardedSendResult",
    "HardwareSendResult",
    "TripleSender",
    "guarded_send",
    "hardware_send",
]
