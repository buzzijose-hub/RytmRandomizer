"""Pure CockpitSendPlan builder.

The send plan is the preflight object between a previewed
``MutationCandidate`` and the SEND command. It is deterministic and inert:
building one never opens MIDI ports, never touches hardware, and never
mutates the active device state.
"""

from __future__ import annotations

import hashlib
import json

from ...observability.logging import get_logger
from ..data import (
    CockpitSendPlan,
    MutationCandidate,
    ProfileModel,
    ReadinessReason,
    SendPlanPacket,
    Snapshot,
    synthetic_parameter_cc,
)

_logger = get_logger(__name__)
"""Module logger for the cockpit send-plan builder. Bound here so future
structured log calls (per-plan packet/blocked-reason breadcrumbs) can
land in the package's structured stream without touching this file's
imports. See ``OBSERVABILITY_REVIEW.md`` Phase 5."""

_DEFAULT_MIDI_CHANNEL = 0


def prepare_send_plan(
    snapshot: Snapshot,
    profile: ProfileModel | None,
    candidate: MutationCandidate | None,
    pad_locks: frozenset[int],
) -> CockpitSendPlan | None:
    """Build a deterministic inert send plan, or ``None`` when not stageable."""

    if profile is None or candidate is None:
        return None

    packets = _candidate_packets(candidate, pad_locks)
    blocked_reasons = _blocked_reasons(snapshot, profile, candidate, packets)
    ready = not blocked_reasons
    readiness_reason: ReadinessReason = "ready" if ready else blocked_reasons[0]

    plan = CockpitSendPlan(
        plan_id=_plan_id(candidate, pad_locks, blocked_reasons, packets),
        candidate_id=candidate.candidate_id,
        source_snapshot_id=candidate.source_snapshot_id,
        profile_id=candidate.profile_id,
        ready=ready,
        readiness_reason=readiness_reason,
        safety_status=candidate.safety_status,
        packets=packets,
        locked_pad_ids=pad_locks,
        blocked_reasons=blocked_reasons,
    )
    return plan


def _candidate_packets(
    candidate: MutationCandidate,
    pad_locks: frozenset[int],
) -> tuple[SendPlanPacket, ...]:
    packets: list[SendPlanPacket] = []
    for delta in sorted(candidate.pad_deltas, key=lambda item: item.pad_id):
        if delta.pad_id in pad_locks:
            continue
        for parameter in sorted(delta.changed_keys):
            packets.append(
                SendPlanPacket(
                    pad_id=delta.pad_id,
                    parameter=parameter,
                    channel=_DEFAULT_MIDI_CHANNEL,
                    control=synthetic_parameter_cc(parameter),
                    value=int(delta.proposed_params[parameter]),
                )
            )
    return tuple(packets)


def _blocked_reasons(
    snapshot: Snapshot,
    profile: ProfileModel,
    candidate: MutationCandidate,
    packets: tuple[SendPlanPacket, ...],
) -> tuple[ReadinessReason, ...]:
    reasons: list[ReadinessReason] = []
    if candidate.profile_id != profile.profile_id:
        reasons.append("profile_mismatch")
    if candidate.source_snapshot_id != snapshot.snapshot_id:
        reasons.append("source_snapshot_mismatch")
    if candidate.safety_status == "high_risk":
        reasons.append("candidate_high_risk")
    if not packets:
        reasons.append("no_sendable_changes")
    return tuple(reasons)


def _plan_id(
    candidate: MutationCandidate,
    pad_locks: frozenset[int],
    blocked_reasons: tuple[ReadinessReason, ...],
    packets: tuple[SendPlanPacket, ...],
) -> str:
    payload = {
        "blocked_reasons": list(blocked_reasons),
        "candidate_id": candidate.candidate_id,
        "locked_pad_ids": sorted(pad_locks),
        "packets": [packet.to_dict() for packet in packets],
        "profile_id": candidate.profile_id,
        "safety_status": candidate.safety_status,
        "source_snapshot_id": candidate.source_snapshot_id,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sendplan-{hashlib.sha256(encoded).hexdigest()[:16]}"


__all__ = ["prepare_send_plan"]
