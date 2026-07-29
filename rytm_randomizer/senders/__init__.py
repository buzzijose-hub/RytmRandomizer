"""Generic senders that consume registered Device strategies."""

from __future__ import annotations

from .armed_apply import (
    ArmedApplyError,
    ArmedApplyResult,
    ArmedApplySession,
    BackupHook,
    ExactPortOpener,
    OutputPortLike,
    plan_readiness,
)
from .guarded import GuardedSendResult, guarded_send
from .hardware import (
    ExactOutputOpener,
    HardwareSendResult,
    OutputOpeningProvider,
    TripleSender,
    hardware_send,
)
from .midi_event_plan import (
    CcNrpnSendEvent,
    send_cc_nrpn_event_plan,
)

__all__ = [
    "ArmedApplyError",
    "ArmedApplyResult",
    "ArmedApplySession",
    "BackupHook",
    "CcNrpnSendEvent",
    "ExactOutputOpener",
    "ExactPortOpener",
    "GuardedSendResult",
    "HardwareSendResult",
    "OutputOpeningProvider",
    "OutputPortLike",
    "TripleSender",
    "guarded_send",
    "hardware_send",
    "plan_readiness",
    "send_cc_nrpn_event_plan",
]
