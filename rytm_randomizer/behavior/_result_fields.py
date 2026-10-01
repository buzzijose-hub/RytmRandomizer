"""Shared dataclass-field helpers for the behavior result types.

Every ``*BehaviorResult`` dataclass in this package carries a ``metadata``
mapping that defaults to empty. ``field(default_factory=dict)`` leaves that
default untyped under strict checking, so the factory is declared once here
with an explicit return type rather than repeated per module.
"""

from __future__ import annotations


def empty_metadata() -> dict[str, object]:
    """Return a fresh, empty metadata mapping for a behavior result."""

    return {}


__all__ = ["empty_metadata"]
