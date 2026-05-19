"""Generic senders that consume registered Device strategies."""

from __future__ import annotations

from .guarded import GuardedSendResult, guarded_send

__all__ = ["GuardedSendResult", "guarded_send"]
