"""Pure canonical preflight for bounded unqualified A4 RAM auditions.

This path consumes neither serialized offline reports nor their readiness
flags. It reconstructs bytes and scalar transport facts on every invocation,
and never discovers, opens or transmits to a MIDI port.
"""

from __future__ import annotations

import hashlib

from ...data.analog_four_native_transport import A4_NATIVE_TRANSPORT_CONTRACT_REASON
from ...guardrails.input_validation import canonical_json_bytes, require_boolean, require_int
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ..data.a4_studio_audition import A4StudioAuditionPlan, A4StudioRouting
from ..data.send_plan import CockpitSendPlan, SendPlanPacket
from ..data.show_bank import ShowBankEntry, validate_show_bank_id
from .a4_preparation import A4CanonicalReview, A4PreparationContext, review_a4_canonical_evidence

_logger = get_logger(__name__)


def _resolved_packets(
    review: A4CanonicalReview, routing: A4StudioRouting, blockers: list[str]
) -> tuple[SendPlanPacket, ...]:
    preview = review.transport_preview
    if preview is None:
        return ()
    packets: list[SendPlanPacket] = []
    for row in preview.changes:
        blockers.extend(row.blockers)
        if (
            not row.roundtrip_exact
            or row.cc_number is None
            or row.before_cc7 is None
            or row.after_cc7 is None
        ):
            blockers.append(A4_NATIVE_TRANSPORT_CONTRACT_REASON)
            continue
        packets.append(
            SendPlanPacket(
                pad_id=row.track_id,
                parameter=row.parameter,
                channel=routing.track_channels[row.track_id - 1] - 1,
                control=row.cc_number,
                value=row.after_cc7,
            )
        )
    return () if blockers else tuple(packets)


def prepare_a4_studio_audition(  # noqa: PLR0913 - explicit studio preflight integration contract
    *,
    bank_id: str,
    bank_revision: int,
    entry: ShowBankEntry,
    source_frame: bytes | None,
    candidate_frame: bytes | None,
    context: A4PreparationContext,
    routing: A4StudioRouting,
    session_generation: int,
    acknowledge_unvalidated_hardware: bool,
) -> A4StudioAuditionPlan:
    """Rebuild an all-or-nothing RAM-only plan from exact bytes and fresh context.

    ``checked_at`` constrains capture freshness but is deliberately absent from
    identity and serialization so an unchanged SEND-time recheck is identical.
    Capture identity uses every existing public capture field plus frame SHA256;
    KitCaptureResult has no UUID or source port. No hardware claim is promoted.
    """
    validate_show_bank_id(bank_id, "bank_id")
    if require_int(bank_revision, "bank_revision", ValueError) < 0:
        raise ValueError("bank_revision must be nonnegative")
    if require_int(session_generation, "session_generation", ValueError) < 0:
        raise ValueError("session_generation must be nonnegative")
    require_boolean(
        acknowledge_unvalidated_hardware, "acknowledge_unvalidated_hardware", ValueError
    )
    # Revalidate routing/context even when supplied by a typed caller.
    routing = A4StudioRouting(routing.output_port_name, routing.track_channels)
    context.__post_init__()
    review = review_a4_canonical_evidence(
        entry=entry, source_frame=source_frame, candidate_frame=candidate_frame, context=context
    )
    blockers: list[str] = list(review.blocked_reasons)
    candidate = review.candidate
    high_risk = candidate is not None and candidate.rytm_candidate.safety_status == "high_risk"
    if high_risk:
        blockers.append("candidate_high_risk")
    if routing.output_port_name != context.output_port_name:
        blockers.append("output_port_mismatch")
    if not acknowledge_unvalidated_hardware:
        blockers.append("unvalidated_hardware_acknowledgment_required")
    packets = _resolved_packets(review, routing, blockers)
    if not packets and not blockers:
        blockers.append("no_a4_changes")
    reasons = tuple(dict.fromkeys(blockers))
    capture = context.current_capture
    binding: dict[str, object] = {
        "bank_id": bank_id,
        "bank_revision": bank_revision,
        "entry_id": entry.entry_id,
        "source": entry.analog_four_source.to_dict(),
        "candidate": None if candidate is None else candidate.to_dict(),
        "source_frame_sha256": (
            None if source_frame is None else hashlib.sha256(source_frame).hexdigest()
        ),
        "candidate_frame_sha256": (
            None if candidate_frame is None else hashlib.sha256(candidate_frame).hexdigest()
        ),
        "current_capture": None if capture is None else capture.to_dict(),
        "current_frame_sha256": (
            None if capture is None else hashlib.sha256(capture.frame).hexdigest()
        ),
        "session_generation": session_generation,
        "routing": routing.to_dict(),
        "capture_after": context.capture_after.isoformat(),
        "target_ids": sorted(context.scope.target_ids),
        "locked_ids": sorted(context.scope.locked_ids),
        "effective_ids": sorted(review.effective_ids),
        "source_reloaded": context.source_reloaded,
        "candidate_is_local": context.candidate_is_local,
        "active_candidate_id": context.active_candidate_id,
        "selected_candidate_id": entry.selected_candidate_id,
        "session_connected": context.session_connected,
        "output_port_name": context.output_port_name,
        "acknowledge_unvalidated_hardware": acknowledge_unvalidated_hardware,
        "packets": [packet.to_dict() for packet in packets],
        "blocked_reasons": list(reasons),
    }
    plan_id = f"a4-studio-{hashlib.sha256(canonical_json_bytes(binding)).hexdigest()}"
    ready = not reasons
    send_plan = CockpitSendPlan(
        plan_id=plan_id,
        candidate_id="unselected-a4" if candidate is None else candidate.candidate_id,
        source_snapshot_id=entry.analog_four_source.capture_id,
        profile_id="unselected-a4" if candidate is None else candidate.recipe.profile_id,
        ready=ready,
        readiness_reason=(
            "ready"
            if ready
            else "candidate_high_risk" if high_risk else "unsupported_control_changed"
        ),
        # The shared Status vocabulary has no caution value. This is an
        # unqualified trial, never the physical-safety claim implied by safe.
        safety_status="high_risk" if high_risk else "armed",
        packets=packets,
        locked_pad_ids=context.scope.locked_ids,
        target_pad_ids=context.scope.target_ids,
        blocked_reasons=(
            ()
            if ready
            else ("candidate_high_risk",) if high_risk else ("unsupported_control_changed",)
        ),
    )
    if not ready:
        get_metrics().record_error("a4_studio_audition_refused")
    _logger.info(
        "a4_studio_audition_prepared",
        extra={
            "plan_id": plan_id,
            "bank_revision": bank_revision,
            "session_generation": session_generation,
            "ready": ready,
            "blocked_reasons": list(reasons),
            "packet_count": len(packets),
        },
    )
    return A4StudioAuditionPlan(
        bank_id=bank_id,
        bank_revision=bank_revision,
        entry_id=entry.entry_id,
        candidate_id=None if candidate is None else candidate.candidate_id,
        session_generation=session_generation,
        routing=routing,
        send_plan=send_plan,
        blocked_reasons=reasons,
    )


__all__ = ["prepare_a4_studio_audition"]
