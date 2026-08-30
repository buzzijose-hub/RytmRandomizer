"""Hardware-inert orchestration for the dual-machine Cockpit stage."""

from __future__ import annotations

from dataclasses import replace
from typing import Final, Literal, Self

from ...observability.logging import get_logger
from ..data.stage import (
    DualMachineStageState,
    MachineStageState,
    StageArtifactState,
    StageAuthorityState,
    StageDeviceId,
)
from .policy import (
    A4_LANE_POLICY,
    A4_MAPPING_BLOCK_REASON,
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    RYTM_LANE_POLICY,
    stage_lane_policy,
)

_TRANSIENT_BLOCKS: Final[frozenset[str]] = frozenset(
    {"capture_failed", "device_disconnected", "send_failed"}
)
_logger = get_logger(__name__)

StageTransition = Literal[
    "capture", "connection", "scope", "candidate", "plan", "authority", "send"
]


class DualMachineStageCoordinator:
    """Hardware-inert state machine for independent Rytm and A4 lanes."""

    def __init__(self, *, rytm_send_armed: bool = False) -> None:
        self._revision = 0
        self._rytm_send_armed = rytm_send_armed
        self._machines: dict[StageDeviceId, MachineStageState] = {
            RYTM_LANE_POLICY.device_id: MachineStageState(
                device_id=RYTM_LANE_POLICY.device_id,
                effective_ids=RYTM_LANE_POLICY.available_ids,
                authority_state="armed" if rytm_send_armed else "not_armed",
            ),
            A4_LANE_POLICY.device_id: MachineStageState(
                device_id=A4_LANE_POLICY.device_id,
                effective_ids=A4_LANE_POLICY.available_ids,
                plan_state="blocked",
                authority_state="blocked",
                blocked_reasons=(A4_MAPPING_BLOCK_REASON,),
                recovery_actions=("capture_current_kit", "run_a4_mapping_gap_procedure"),
            ),
        }

    @property
    def state(self) -> DualMachineStageState:
        """Return the current immutable whole-state snapshot."""

        return DualMachineStageState(
            revision=self._revision,
            rytm=self._machine(ANALOG_RYTM_DEVICE_ID),
            analog_four=self._machine(ANALOG_FOUR_DEVICE_ID),
        )

    def _machine(self, device_id: StageDeviceId) -> MachineStageState:
        return self._machines[device_id]

    def _store(
        self,
        device_id: StageDeviceId,
        state: MachineStageState,
        *,
        transition: StageTransition,
        force_revision: bool = False,
    ) -> None:
        previous = self._machine(device_id)
        state_changed = state != previous
        if not state_changed and not force_revision:
            return
        self._machines[device_id] = state
        self._revision += 1
        _logger.info(
            "cockpit_stage_transition",
            extra={
                "event": "cockpit_stage_transition",
                "transition": transition,
                "device_id": device_id,
                "revision": self._revision,
                "state_changed": state_changed,
                "from_connection_state": previous.connection_state,
                "to_connection_state": state.connection_state,
                "from_capture_state": previous.capture_state,
                "to_capture_state": state.capture_state,
                "from_candidate_state": previous.candidate_state,
                "to_candidate_state": state.candidate_state,
                "from_plan_state": previous.plan_state,
                "to_plan_state": state.plan_state,
                "from_authority_state": previous.authority_state,
                "to_authority_state": state.authority_state,
                "from_target_count": len(previous.target_ids),
                "to_target_count": len(state.target_ids),
                "from_locked_count": len(previous.locked_ids),
                "to_locked_count": len(state.locked_ids),
                "from_effective_count": len(previous.effective_ids),
                "to_effective_count": len(state.effective_ids),
            },
        )

    def record_capture(
        self,
        device_id: StageDeviceId,
        *,
        succeeded: bool,
        connected: bool | None,
        error: str | None = None,
    ) -> Self:
        """Record one lane's capture result without altering the other lane."""

        current = self._machine(device_id)
        policy = stage_lane_policy(device_id)
        if succeeded:
            retained_reasons = tuple(
                reason for reason in current.blocked_reasons if reason not in _TRANSIENT_BLOCKS
            )
            authority: StageAuthorityState = "blocked"
            if policy.output_authority_supported:
                authority = "armed" if self._rytm_send_armed else "not_armed"
            next_state = replace(
                current,
                connection_state="connected",
                capture_state="captured",
                candidate_state="none",
                plan_state="none" if policy.output_authority_supported else "blocked",
                authority_state=authority,
                blocked_reasons=retained_reasons,
                last_error=None,
                recovery_actions=(
                    ("restore_captured_kit", "preview")
                    if policy.output_authority_supported
                    else ("restore_captured_kit", "run_a4_mapping_gap_procedure")
                ),
            )
        else:
            reasons = tuple(dict.fromkeys((*current.blocked_reasons, "capture_failed")))
            connection_state = current.connection_state
            if connected is not None:
                connection_state = "connected" if connected else "disconnected"
            next_state = replace(
                current,
                connection_state=connection_state,
                capture_state="failed",
                candidate_state="none",
                plan_state="none" if policy.output_authority_supported else "blocked",
                authority_state="blocked",
                blocked_reasons=reasons,
                recovery_actions=(
                    ("reconnect_device", "capture_current_kit")
                    if connected is False
                    else ("capture_current_kit",)
                ),
                last_error=error or "capture failed",
            )
        self._store(device_id, next_state, transition="capture", force_revision=True)
        return self

    def record_connection(self, device_id: StageDeviceId, *, connected: bool) -> Self:
        """Revoke only the disconnected lane and make stale artifacts explicit."""

        current = self._machine(device_id)
        policy = stage_lane_policy(device_id)
        if not connected:
            next_state = replace(
                current,
                connection_state="disconnected",
                candidate_state=(
                    "stale" if current.candidate_state == "ready" else current.candidate_state
                ),
                plan_state="stale" if current.plan_state == "ready" else current.plan_state,
                authority_state="blocked",
                blocked_reasons=tuple(
                    dict.fromkeys((*current.blocked_reasons, "device_disconnected"))
                ),
                recovery_actions=("reconnect_device", "capture_current_kit", "prepare_again"),
                last_error="device disconnected",
            )
        else:
            retained_reasons = tuple(
                reason for reason in current.blocked_reasons if reason != "device_disconnected"
            )
            authority: StageAuthorityState
            if not policy.output_authority_supported or current.capture_state == "failed":
                authority = "blocked"
            else:
                authority = "armed" if self._rytm_send_armed else "not_armed"
            next_state = replace(
                current,
                connection_state="connected",
                authority_state=authority,
                blocked_reasons=retained_reasons,
                recovery_actions=("capture_current_kit", "prepare_again"),
                last_error=None,
            )
        self._store(device_id, next_state, transition="connection", force_revision=True)
        return self

    def record_scope(
        self,
        device_id: StageDeviceId,
        *,
        target_ids: frozenset[int],
        locked_ids: frozenset[int],
        effective_ids: frozenset[int],
    ) -> Self:
        """Apply target/lock scope and invalidate artifacts from the old scope."""

        current = self._machine(device_id)
        policy = stage_lane_policy(device_id)
        changed = (current.target_ids, current.locked_ids, current.effective_ids) != (
            target_ids,
            locked_ids,
            effective_ids,
        )
        next_state = replace(
            current,
            target_ids=target_ids,
            locked_ids=locked_ids,
            effective_ids=effective_ids,
            candidate_state=(
                "stale"
                if changed and current.candidate_state in ("ready", "blocked")
                else current.candidate_state
            ),
            plan_state=(
                (
                    "stale"
                    if changed and current.plan_state in ("ready", "blocked")
                    else current.plan_state
                )
                if policy.output_authority_supported
                else "blocked"
            ),
            recovery_actions=(
                ("preview_again", "prepare_again") if changed else current.recovery_actions
            ),
        )
        self._store(device_id, next_state, transition="scope")
        return self

    def record_candidate(
        self,
        device_id: StageDeviceId,
        *,
        ready: bool | None,
        blocked_reason: str | None = None,
    ) -> Self:
        """Record preview readiness for one lane and revoke its older plan."""

        current = self._machine(device_id)
        policy = stage_lane_policy(device_id)
        reasons = current.blocked_reasons
        if blocked_reason is not None:
            reasons = tuple(dict.fromkeys((*reasons, blocked_reason)))
        candidate_state: StageArtifactState
        if ready is None:
            candidate_state = "none"
        else:
            candidate_state = "ready" if ready else "blocked"
        next_state = replace(
            current,
            candidate_state=candidate_state,
            plan_state="none" if policy.output_authority_supported else "blocked",
            blocked_reasons=reasons,
            recovery_actions=(
                ("prepare",)
                if ready
                else ("preview",) if ready is None else ("adjust_scope_or_depth",)
            ),
        )
        self._store(device_id, next_state, transition="candidate", force_revision=True)
        return self

    def record_plan(self, device_id: StageDeviceId, *, ready: bool) -> Self:
        """Record PREPARE result while keeping machine authorities separate."""

        current = self._machine(device_id)
        policy = stage_lane_policy(device_id)
        if not policy.output_authority_supported:
            next_state = replace(
                current,
                plan_state="blocked",
                authority_state="blocked",
                blocked_reasons=tuple(
                    dict.fromkeys((*current.blocked_reasons, A4_MAPPING_BLOCK_REASON))
                ),
                recovery_actions=("run_a4_mapping_gap_procedure",),
            )
        else:
            next_state = replace(
                current,
                plan_state="ready" if ready else "blocked",
                recovery_actions=("confirm_exact_plan",) if ready else ("preview_again",),
            )
        self._store(device_id, next_state, transition="plan", force_revision=True)
        return self

    def record_rytm_authority(
        self,
        *,
        armed: bool,
        blocked_reason: str | None = None,
    ) -> Self:
        """Record only Rytm transmit authority; A4 remains isolated."""

        self._rytm_send_armed = armed
        rytm = self._machine(ANALOG_RYTM_DEVICE_ID)
        unavailable_reason: str | None = None
        if armed and rytm.capture_state == "failed":
            unavailable_reason = "capture_failed"
        elif armed and rytm.connection_state == "disconnected":
            unavailable_reason = "device_disconnected"
        effective_block = blocked_reason or unavailable_reason
        reasons = tuple(reason for reason in rytm.blocked_reasons if reason != "send_failed")
        if effective_block is not None:
            reasons = tuple(dict.fromkeys((*reasons, effective_block)))
        authority: StageAuthorityState
        if effective_block is not None:
            authority = "blocked"
        else:
            authority = "armed" if armed else "not_armed"
        self._store(
            ANALOG_RYTM_DEVICE_ID,
            replace(
                rytm,
                authority_state=authority,
                blocked_reasons=reasons,
                recovery_actions=(
                    ("confirm_exact_plan",)
                    if armed and rytm.plan_state == "ready"
                    else ("re_arm", "prepare_again") if effective_block is not None else ("arm",)
                ),
            ),
            transition="authority",
        )
        return self

    def record_send(self, device_id: StageDeviceId, *, succeeded: bool) -> Self:
        """Consume one lane's prepared artifacts without touching its sibling."""

        current = self._machine(device_id)
        policy = stage_lane_policy(device_id)
        if not policy.output_authority_supported:
            next_state = replace(
                current,
                candidate_state="blocked",
                plan_state="blocked",
                authority_state="blocked",
                blocked_reasons=tuple(
                    dict.fromkeys((*current.blocked_reasons, A4_MAPPING_BLOCK_REASON))
                ),
                recovery_actions=("run_a4_mapping_gap_procedure",),
            )
        elif succeeded:
            next_state = replace(
                current,
                candidate_state="none",
                plan_state="none",
                recovery_actions=("preview",),
                last_error=None,
            )
        else:
            next_state = replace(
                current,
                plan_state="blocked",
                authority_state="blocked",
                blocked_reasons=tuple(dict.fromkeys((*current.blocked_reasons, "send_failed"))),
                recovery_actions=("re_arm", "prepare_again"),
                last_error="send failed",
            )
        self._store(device_id, next_state, transition="send", force_revision=True)
        return self


__all__ = ["DualMachineStageCoordinator"]
