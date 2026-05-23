"""Cockpit data model — frozen dataclasses + Literal types + ULID helper.

Re-exports the public surface so callers can ``from rytm_randomizer.cockpit.data
import Snapshot`` without reaching into each submodule. See
``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Core Data Abstractions" for the authoritative shape.
"""

from __future__ import annotations

from .snapshot import PadState, Snapshot
from .types import (
    HISTORY_KIND_VALUES,
    KIND_VALUES,
    STATUS_VALUES,
    TRANSITION_CURVE_VALUES,
    VIA_VALUES,
    HistoryKind,
    Kind,
    Status,
    TransitionCurve,
    Via,
)
from .ulid import new_ulid

__all__ = [
    "HISTORY_KIND_VALUES",
    "HistoryKind",
    "KIND_VALUES",
    "Kind",
    "PadState",
    "STATUS_VALUES",
    "Snapshot",
    "Status",
    "TRANSITION_CURVE_VALUES",
    "TransitionCurve",
    "VIA_VALUES",
    "Via",
    "new_ulid",
]
