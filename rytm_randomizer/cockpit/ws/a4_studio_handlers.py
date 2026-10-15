"""Explicit unqualified A4 RAM-only trials through the shared armed boundary."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from types import MappingProxyType
from typing import Final

from ...devices import get_device
from ...guardrails.input_validation import (
    require_boolean,
    require_exact_keys,
    require_int,
    require_integer_tuple,
    require_text,
)
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...senders.armed_apply import ArmedApplyError, ArmedApplyResult
from ..capture import ANALOG_FOUR_DEVICE_ID
from ..data.a4_studio_audition import (
    MIDI_MESSAGE_SETTLE_SECONDS,
    A4StudioAuditionPlan,
    A4StudioRouting,
)
from ..show_bank.workspace import ShowKitForgeWorkspace
from .protocol import (
    COMMAND_SHOW_BANK_PREPARE_A4_STUDIO_AUDITION,
    COMMAND_SHOW_BANK_SEND_A4_STUDIO_AUDITION,
    ERR_VALIDATION,
    EVENT_DUAL_MACHINE_STAGE_CHANGED,
    EVENT_MUTATION_PREVIEWED,
    EVENT_SEND_PLAN_CHANGED,
    EVENT_SHOW_BANK_CHANGED,
    A4StudioAuditionOutcome,
)
from .result import HandlerResult
from .session import CockpitSession

_logger = get_logger(__name__)
_PREPARE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "type",
        "bank_id",
        "entry_id",
        "expected_revision",
        "output_port_name",
        "track_channels",
        "source_reloaded",
        "acknowledge_unvalidated_hardware",
    }
)
_SEND_KEYS: Final[frozenset[str]] = frozenset(
    {"type", "send_plan_id", "confirm", "source_reloaded", "acknowledge_unvalidated_hardware"}
)


def _refused(message: str, *, reason: str) -> HandlerResult:
    get_metrics().record_error("cockpit.a4_studio_refused")
    _logger.warning("a4_studio_refused", extra={"outcome": "refused", "reason": reason})
    return HandlerResult(ack={"ok": False, "code": ERR_VALIDATION, "message": message})


def _record_outcome(
    session: CockpitSession, plan: A4StudioAuditionPlan, result: ArmedApplyResult
) -> None:
    for packet in plan.send_plan.packets[: result.sent_count]:
        get_metrics().record_cc_sent(packet.channel)
    context = {
        "plan_id": plan.plan_id,
        "status": result.status,
        "sent_count": str(result.sent_count),
        "expected_count": str(result.expected_count),
        "reason": result.reason,
    }
    session.error_journal.record(
        "cockpit.a4_studio_outcome",
        "Unqualified A4 RAM audition outcome; manual reload required",
        context=context,
    )
    _logger.info("a4_studio_outcome", extra=context)
    if not result.ok:
        get_metrics().record_error("cockpit.a4_studio_delivery_failed")


def _rebuild(
    session: CockpitSession, plan: A4StudioAuditionPlan
) -> tuple[A4StudioAuditionPlan, ShowKitForgeWorkspace]:
    workspace = session.show_kit_forge
    if workspace is None:
        raise ValueError("Show Kit Forge is unavailable")
    checked = workspace.prepare_a4_studio_plan(
        plan.bank_id,
        plan.entry_id,
        plan.bank_revision,
        captures=session.kit_captures,
        target_ids=tuple(session.a4_track_targets),
        locked_ids=tuple(session.a4_track_locks),
        parameter_selection=session.a4_parameters,
        active_candidate_id=(
            None if session.current_candidate is None else session.current_candidate.candidate_id
        ),
        routing=plan.routing,
        session_generation=session.a4_studio_generation,
        source_reloaded=True,
        acknowledge_unvalidated_hardware=True,
    )
    return checked, workspace


async def prepare_a4_studio(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    """Prepare from current trusted material; never accept inbound packets or reports."""
    session.a4_studio_plan = None
    require_exact_keys(cmd, _PREPARE_KEYS, "A4 studio preparation")
    workspace = session.show_kit_forge
    if workspace is None:
        return _refused("Show Kit Forge is unavailable", reason="workspace_unavailable")
    channels = require_integer_tuple(cmd["track_channels"], "track_channels", ValueError)
    if len(channels) != 4:
        raise ValueError("exactly four configured A4 track channels are required")
    routing = A4StudioRouting(
        output_port_name=require_text(cmd["output_port_name"], "output_port_name", ValueError),
        track_channels=(channels[0], channels[1], channels[2], channels[3]),
    )
    plan = workspace.prepare_a4_studio_plan(
        require_text(cmd["bank_id"], "bank_id", ValueError),
        require_text(cmd["entry_id"], "entry_id", ValueError),
        require_int(cmd["expected_revision"], "expected_revision", ValueError),
        captures=session.kit_captures,
        target_ids=tuple(session.a4_track_targets),
        locked_ids=tuple(session.a4_track_locks),
        parameter_selection=session.a4_parameters,
        active_candidate_id=(
            None if session.current_candidate is None else session.current_candidate.candidate_id
        ),
        routing=routing,
        session_generation=session.a4_studio_generation,
        source_reloaded=require_boolean(cmd["source_reloaded"], "source_reloaded", ValueError),
        acknowledge_unvalidated_hardware=require_boolean(
            cmd["acknowledge_unvalidated_hardware"], "acknowledge_unvalidated_hardware", ValueError
        ),
    )
    session.a4_studio_plan = plan
    _logger.info("a4_studio_prepared", extra={"plan_id": plan.plan_id, "ready": plan.ready})
    return HandlerResult(ack={"ok": True, "a4_studio_plan": plan.to_dict()})


async def send_a4_studio(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    """Re-prove the entire plan and consume it before a single paced attempt."""
    require_exact_keys(cmd, _SEND_KEYS, "A4 studio SEND")
    plan = session.a4_studio_plan
    if plan is None or not plan.ready:
        return _refused("Prepare a ready A4 studio plan before SEND", reason="plan_not_ready")
    if cmd["send_plan_id"] != plan.plan_id or any(
        cmd[key] is not True
        for key in ("confirm", "source_reloaded", "acknowledge_unvalidated_hardware")
    ):
        return _refused(
            "Confirm the exact A4 plan, manual source reload and unqualified studio trial",
            reason="confirmation_mismatch",
        )
    armed = session.armed_apply
    if (
        armed is None
        or not armed.is_armed
        or session.armed_device_id != ANALOG_FOUR_DEVICE_ID
        or armed.port_name != plan.routing.output_port_name
    ):
        return _refused(
            "Arm the exact configured A4 studio output before SEND", reason="armed_route_mismatch"
        )
    try:
        checked, workspace = _rebuild(session, plan)
    finally:
        session.a4_studio_plan = None
    if not checked.ready or checked.to_dict() != plan.to_dict():
        return _refused(
            "A4 studio plan is stale; reload, capture and prepare the exact current scope",
            reason="plan_stale",
        )
    # Revoke before the first byte, including zero-byte failures and cancellation.
    session.a4_studio_generation += 1
    session.current_send_plan = None
    revoked = workspace.revoke_hardware_evidence()
    revoked_events: list[dict[str, object]] = (
        [{"type": EVENT_SHOW_BANK_CHANGED, "show_bank": workspace.state_dict()}] if revoked else []
    )
    from .handlers import (  # noqa: PLC0415
        build_session_status,
        cockpit_send_plan_triples,
        disarm_session_on_teardown,
    )

    session.a4_studio_sending = True
    try:
        await asyncio.sleep(0)
        armed.confirm(plan.plan_id)
        result = await armed.apply_async(
            get_device(ANALOG_FOUR_DEVICE_ID),
            plan.send_plan,
            action_id=plan.plan_id,
            mutates_kit=False,
            renderer=cockpit_send_plan_triples,
            inter_message_delay_seconds=MIDI_MESSAGE_SETTLE_SECONDS,
        )
    except ArmedApplyError as exc:
        result = exc.partial_outcome or ArmedApplyResult(
            device_id=ANALOG_FOUR_DEVICE_ID,
            ok=False,
            sent_count=0,
            expected_count=len(plan.send_plan.packets),
            status="refused",
            reason="armed_send_refused",
        )
    except (
        asyncio.CancelledError,
        KeyboardInterrupt,
        SystemExit,
        LookupError,
        OSError,
        TypeError,
        ValueError,
        RuntimeError,
    ) as exc:
        interrupted = getattr(exc, "armed_apply_outcome", None)
        if not isinstance(interrupted, ArmedApplyResult):
            interrupted = ArmedApplyResult(
                device_id=ANALOG_FOUR_DEVICE_ID,
                ok=False,
                sent_count=0,
                expected_count=len(plan.send_plan.packets),
                status="interrupted",
                reason="a4_studio_interrupted_before_delivery",
            )
        disarm_session_on_teardown(session)
        _record_outcome(session, plan, interrupted)
        raise
    finally:
        session.a4_studio_sending = False
        if session.armed_apply is not None and not session.armed_apply.is_armed:
            disarm_session_on_teardown(session)
    _record_outcome(session, plan, result)
    outcome: A4StudioAuditionOutcome = {
        "status": result.status,
        "sent_count": result.sent_count,
        "expected_count": result.expected_count,
        "reason": result.reason,
    }
    if not result.ok:
        disarm_session_on_teardown(session)
    else:
        session.unsaved_sends += 1
    session.stage_coordinator.record_send(ANALOG_FOUR_DEVICE_ID, succeeded=result.ok)
    events: list[dict[str, object]] = [
        build_session_status(session),
        {"type": EVENT_SEND_PLAN_CHANGED, "send_plan": None},
        {
            "type": EVENT_DUAL_MACHINE_STAGE_CHANGED,
            "stage": session.stage_coordinator.state.to_dict(),
        },
        *revoked_events,
    ]
    if not result.ok:
        events.append({"type": EVENT_MUTATION_PREVIEWED, "candidate": None})
    ack: dict[str, object] = {
        "ok": result.ok,
        "a4_studio_outcome": outcome,
        "source_reload_required": True,
    }
    if not result.ok:
        ack.update(
            {
                "code": ERR_VALIDATION,
                "message": "A4 studio delivery stopped; manually reload and capture the source before another attempt",
            }
        )
    return HandlerResult(
        ack=ack,
        events=events,
    )


A4StudioHandler = Callable[[dict[str, object], CockpitSession], Awaitable[HandlerResult]]
A4_STUDIO_HANDLERS: Final[Mapping[str, A4StudioHandler]] = MappingProxyType(
    {
        COMMAND_SHOW_BANK_PREPARE_A4_STUDIO_AUDITION: prepare_a4_studio,
        COMMAND_SHOW_BANK_SEND_A4_STUDIO_AUDITION: send_a4_studio,
    }
)

__all__ = ["A4_STUDIO_HANDLERS"]
