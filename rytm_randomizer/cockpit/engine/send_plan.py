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
from ...snapshot.mutation_scope import MutationScope
from ..data import (
    CockpitSendPlan,
    MutationCandidate,
    ProfileModel,
    ReadinessReason,
    SendPlanPacket,
    Snapshot,
)
from ..data.rytm_parameter_map import (
    cockpit_machine_is_allowed_on_pad,
    cockpit_pad_channel,
    cockpit_parameter_live_blockers,
    cockpit_parameter_mapping,
)
from ..mutation_targets import MutationTargets

_logger = get_logger(__name__)
"""Module logger for the cockpit send-plan builder. Bound here so future
structured log calls (per-plan packet/blocked-reason breadcrumbs) can
land in the package's structured stream without touching this file's
imports. See ``OBSERVABILITY_REVIEW.md`` Phase 5."""


def prepare_send_plan(
    snapshot: Snapshot,
    profile: ProfileModel | None,
    candidate: MutationCandidate | None,
    pad_locks: frozenset[int],
    pad_targets: frozenset[int] = frozenset(),
) -> CockpitSendPlan | None:
    """Build a deterministic inert send plan, or ``None`` when not stageable."""

    if profile is None or candidate is None:
        return None

    scope = MutationTargets(rytm_pad_targets=pad_targets).rytm_scope(pad_locks)
    packets, paired_control_unverified, protected_control_changed = _candidate_packets(
        snapshot, candidate, scope
    )
    blocked_reasons = _blocked_reasons(
        snapshot, profile, candidate, packets, paired_control_unverified, protected_control_changed
    )
    ready = not blocked_reasons
    readiness_reason: ReadinessReason = "ready" if ready else blocked_reasons[0]

    plan = CockpitSendPlan(
        plan_id=_plan_id(candidate, pad_locks, pad_targets, blocked_reasons, packets),
        candidate_id=candidate.candidate_id,
        source_snapshot_id=candidate.source_snapshot_id,
        profile_id=candidate.profile_id,
        ready=ready,
        readiness_reason=readiness_reason,
        safety_status=candidate.safety_status,
        packets=packets,
        locked_pad_ids=pad_locks,
        target_pad_ids=pad_targets,
        blocked_reasons=blocked_reasons,
    )
    _logger.info(
        "cockpit_send_plan_prepared",
        extra={
            "blocked_reasons": list(blocked_reasons),
            "candidate_id": candidate.candidate_id,
            "locked_pad_ids": sorted(pad_locks),
            "packet_count": len(packets),
            "ready": ready,
            "sendable_pad_ids": sorted({packet.pad_id for packet in packets}),
            "target_pad_ids": sorted(pad_targets),
        },
    )
    return plan


def _candidate_packets(
    snapshot: Snapshot,
    candidate: MutationCandidate,
    scope: MutationScope,
) -> tuple[tuple[SendPlanPacket, ...], bool, bool]:
    machines_by_pad = {pad.pad_id: pad.machine for pad in snapshot.pads}
    sendable_pad_ids = scope.effective_ids(machines_by_pad)
    packets: list[SendPlanPacket] = []
    paired_control_unverified = False
    protected_control_changed = False
    for delta in sorted(candidate.pad_deltas, key=lambda item: item.pad_id):
        if delta.pad_id not in sendable_pad_ids:
            continue
        machine = machines_by_pad[delta.pad_id]
        for parameter in sorted(delta.changed_keys):
            mapping = cockpit_parameter_mapping(machine, parameter)
            if mapping is None:
                continue
            if cockpit_parameter_live_blockers(machine, parameter) or (
                mapping.machine_key is not None
                and not cockpit_machine_is_allowed_on_pad(machine, delta.pad_id)
            ):
                protected_control_changed = True
                continue
            if mapping.cc_lsb is not None:
                # A seven-bit projection cannot prove the paired value or its
                # restore. Block the whole plan rather than send its MSB alone.
                paired_control_unverified = True
                continue
            packets.append(
                SendPlanPacket(
                    pad_id=delta.pad_id,
                    parameter=parameter,
                    channel=cockpit_pad_channel(delta.pad_id),
                    control=mapping.cc_msb,
                    value=int(delta.proposed_params[parameter]),
                )
            )
    return tuple(packets), paired_control_unverified, protected_control_changed


def _blocked_reasons(
    snapshot: Snapshot,
    profile: ProfileModel,
    candidate: MutationCandidate,
    packets: tuple[SendPlanPacket, ...],
    paired_control_unverified: bool,
    protected_control_changed: bool,
) -> tuple[ReadinessReason, ...]:
    reasons: list[ReadinessReason] = []
    if candidate.profile_id != profile.profile_id:
        reasons.append("profile_mismatch")
    if candidate.source_snapshot_id != snapshot.snapshot_id:
        reasons.append("source_snapshot_mismatch")
    if candidate.safety_status == "high_risk" or protected_control_changed:
        reasons.append("candidate_high_risk")
    if paired_control_unverified:
        reasons.append("paired_control_precision_unverified")
    if not packets:
        reasons.append("no_sendable_changes")
    return tuple(reasons)


def _plan_id(
    candidate: MutationCandidate,
    pad_locks: frozenset[int],
    pad_targets: frozenset[int],
    blocked_reasons: tuple[ReadinessReason, ...],
    packets: tuple[SendPlanPacket, ...],
) -> str:
    payload = {
        "blocked_reasons": list(blocked_reasons),
        "candidate_id": candidate.candidate_id,
        "locked_pad_ids": sorted(pad_locks),
        "target_pad_ids": sorted(pad_targets),
        "packets": [packet.to_dict() for packet in packets],
        "profile_id": candidate.profile_id,
        "safety_status": candidate.safety_status,
        "source_snapshot_id": candidate.source_snapshot_id,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sendplan-{hashlib.sha256(encoded).hexdigest()[:16]}"


__all__ = ["prepare_send_plan"]
