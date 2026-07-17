"""Generic senders that consume registered Device strategies."""

from __future__ import annotations

from .guarded import GuardedSendResult, guarded_send
from .hardware import HardwareSendResult, TripleSender, hardware_send
from .midi_event_plan import (
    CcNrpnSendEvent,
    send_cc_nrpn_event_plan,
)

__all__ = [
    "CcNrpnSendEvent",
    "GuardedSendResult",
    "HardwareSendResult",
    "TripleSender",
    "guarded_send",
    "hardware_send",
    "send_cc_nrpn_event_plan",
]
