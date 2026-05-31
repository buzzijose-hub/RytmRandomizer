"""Cockpit data model — frozen dataclasses + Literal types + ULID helper.

Re-exports the public surface so callers can ``from rytm_randomizer.cockpit.data
import Snapshot`` without reaching into each submodule. See
``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Core Data Abstractions" for the authoritative shape.
"""

from __future__ import annotations

from .history import History, HistoryEntry
from .mutation_candidate import MutationCandidate, PadDelta
from .profile_model import ProfileModel, StyleTrait, TraitPadWeight
from .send_plan import (
    READINESS_REASON_VALUES,
    CockpitSendPlan,
    ReadinessReason,
    SendPlanPacket,
    narrow_readiness_reason,
)
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
    narrow_history_kind,
    narrow_kind,
    narrow_status,
    narrow_transition_curve,
    narrow_via,
)
from .ulid import new_ulid

__all__ = [
    "HISTORY_KIND_VALUES",
    "History",
    "HistoryEntry",
    "HistoryKind",
    "KIND_VALUES",
    "READINESS_REASON_VALUES",
    "Kind",
    "CockpitSendPlan",
    "MutationCandidate",
    "PadDelta",
    "PadState",
    "ProfileModel",
    "ReadinessReason",
    "STATUS_VALUES",
    "SendPlanPacket",
    "Snapshot",
    "Status",
    "StyleTrait",
    "TRANSITION_CURVE_VALUES",
    "TraitPadWeight",
    "TransitionCurve",
    "VIA_VALUES",
    "Via",
    "narrow_history_kind",
    "narrow_kind",
    "narrow_readiness_reason",
    "narrow_status",
    "narrow_transition_curve",
    "narrow_via",
    "new_ulid",
]
