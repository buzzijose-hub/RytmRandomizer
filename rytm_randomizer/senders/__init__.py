"""Generic senders that consume registered Device strategies."""

from __future__ import annotations

from ..behavior.midi_event_plan import CcNrpnEvent
from .armed_apply import (
    ArmedApplyError,
    ArmedApplyResult,
    ArmedApplySession,
    ExactPortOpener,
    KitMutationUnsupportedError,
    OutputPortLike,
    PlanRenderer,
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
from .midi_event_plan import send_cc_nrpn_event_plan

__all__ = [
    "ArmedApplyError",
    "ArmedApplyResult",
    "ArmedApplySession",
    "CcNrpnEvent",
    "ExactOutputOpener",
    "ExactPortOpener",
    "GuardedSendResult",
    "HardwareSendResult",
    "KitMutationUnsupportedError",
    "OutputOpeningProvider",
    "OutputPortLike",
    "PlanRenderer",
    "TripleSender",
    "guarded_send",
    "hardware_send",
    "plan_readiness",
    "send_cc_nrpn_event_plan",
]
