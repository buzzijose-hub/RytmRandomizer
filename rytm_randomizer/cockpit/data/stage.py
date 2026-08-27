"""Authoritative, hardware-inert dual-machine Cockpit stage state.

The coordinator records Rytm and Analog Four lifecycle state independently.
It never opens a port or renders MIDI; WebSocket handlers feed it facts after
their existing capture, preview, and PREPARE boundaries have succeeded.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final, Literal, Self, TypedDict

_RYTM_PAD_IDS: Final[frozenset[int]] = frozenset(range(1, 13))
_A4_TRACK_IDS: Final[frozenset[int]] = frozenset(range(1, 5))
_A4_MAPPING_BLOCK: Final[str] = "a4_semantic_mapping_unpromoted"
_TRANSIENT_BLOCKS: Final[frozenset[str]] = frozenset(
    {"capture_failed", "device_disconnected", "send_failed"}
)

StageDeviceId = Literal["analog_rytm_mk2", "analog_four_mk2"]
StageConnectionState = Literal["unknown", "connected", "disconnected"]
StageCaptureState = Literal["not_captured", "captured", "failed"]
StageArtifactState = Literal["none", "ready", "stale", "blocked"]
StageAuthorityState = Literal["not_armed", "armed", "blocked"]


class MachineStageStateDict(TypedDict):
    """Stable WebSocket shape for one machine's stage state."""

    device_id: StageDeviceId
    connection_state: StageConnectionState
    capture_state: StageCaptureState
    target_ids: list[int]
    locked_ids: list[int]
    effective_ids: list[int]
    candidate_state: StageArtifactState
    plan_state: StageArtifactState
    authority_state: StageAuthorityState
    blocked_reasons: list[str]
    recovery_actions: list[str]
    last_error: str | None


class DualMachineStageStateDict(TypedDict):
    """Whole-state payload used for bootstrap and every stage revision."""

    revision: int
    rytm: MachineStageStateDict
    analog_four: MachineStageStateDict
    oxi_owns_sequencing: bool
    direct_oxi_control: bool


@dataclass(frozen=True)
class MachineStageState:
    """One independently revocable machine lane in the live stage."""

    device_id: StageDeviceId
    connection_state: StageConnectionState = "unknown"
    capture_state: StageCaptureState = "not_captured"
    target_ids: frozenset[int] = frozenset()
    locked_ids: frozenset[int] = frozenset()
    effective_ids: frozenset[int] = frozenset()
    candidate_state: StageArtifactState = "none"
    plan_state: StageArtifactState = "none"
    authority_state: StageAuthorityState = "not_armed"
    blocked_reasons: tuple[str, ...] = ()
    recovery_actions: tuple[str, ...] = ("capture_current_kit",)
    last_error: str | None = None

    def to_dict(self) -> MachineStageStateDict:
        """Serialize with deterministic ordering for reconnect hydration."""

        return {
            "device_id": self.device_id,
            "connection_state": self.connection_state,
            "capture_state": self.capture_state,
            "target_ids": sorted(self.target_ids),
            "locked_ids": sorted(self.locked_ids),
            "effective_ids": sorted(self.effective_ids),
            "candidate_state": self.candidate_state,
            "plan_state": self.plan_state,
            "authority_state": self.authority_state,
            "blocked_reasons": list(self.blocked_reasons),
            "recovery_actions": list(self.recovery_actions),
            "last_error": self.last_error,
        }


@dataclass(frozen=True)
class DualMachineStageState:
    """Immutable snapshot of the coordinated stage at one revision."""

    revision: int
    rytm: MachineStageState
    analog_four: MachineStageState
    oxi_owns_sequencing: bool = True
    direct_oxi_control: bool = False

    def to_dict(self) -> DualMachineStageStateDict:
        """Return the complete state; clients never merge partial authority."""

        return {
            "revision": self.revision,
            "rytm": self.rytm.to_dict(),
            "analog_four": self.analog_four.to_dict(),
            "oxi_owns_sequencing": self.oxi_owns_sequencing,
            "direct_oxi_control": self.direct_oxi_control,
        }


class DualMachineStageCoordinator:
    """Hardware-inert state machine for independent Rytm and A4 lanes."""

    def __init__(self, *, rytm_send_armed: bool = False) -> None:
        self._revision = 0
        self._rytm_send_armed = rytm_send_armed
        self._rytm = MachineStageState(
            device_id="analog_rytm_mk2",
            effective_ids=_RYTM_PAD_IDS,
            authority_state="armed" if rytm_send_armed else "not_armed",
        )
        self._analog_four = MachineStageState(
            device_id="analog_four_mk2",
            effective_ids=_A4_TRACK_IDS,
            plan_state="blocked",
            authority_state="blocked",
            blocked_reasons=(_A4_MAPPING_BLOCK,),
            recovery_actions=("capture_current_kit", "run_a4_mapping_gap_procedure"),
        )

    @property
    def state(self) -> DualMachineStageState:
        """Return the current immutable whole-state snapshot."""

        return DualMachineStageState(
            revision=self._revision,
            rytm=self._rytm,
            analog_four=self._analog_four,
        )

    def _machine(self, device_id: StageDeviceId) -> MachineStageState:
        return self._rytm if device_id == "analog_rytm_mk2" else self._analog_four

    def _store(
        self,
        device_id: StageDeviceId,
        state: MachineStageState,
        *,
        force_revision: bool = False,
    ) -> None:
        if state == self._machine(device_id) and not force_revision:
            return
        if device_id == "analog_rytm_mk2":
            self._rytm = state
        else:
            self._analog_four = state
        self._revision += 1

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
        if succeeded:
            retained_reasons = tuple(
                reason for reason in current.blocked_reasons if reason not in _TRANSIENT_BLOCKS
            )
            authority: StageAuthorityState = "blocked"
            if device_id == "analog_rytm_mk2":
                authority = "armed" if self._rytm_send_armed else "not_armed"
            next_state = replace(
                current,
                connection_state="connected",
                capture_state="captured",
                candidate_state="none",
                plan_state="blocked" if device_id == "analog_four_mk2" else "none",
                authority_state=authority,
                blocked_reasons=retained_reasons,
                last_error=None,
                recovery_actions=(
                    ("restore_captured_kit", "run_a4_mapping_gap_procedure")
                    if device_id == "analog_four_mk2"
                    else ("restore_captured_kit", "preview")
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
                plan_state="blocked" if device_id == "analog_four_mk2" else "none",
                authority_state="blocked",
                blocked_reasons=reasons,
                recovery_actions=(
                    ("reconnect_device", "capture_current_kit")
                    if connected is False
                    else ("capture_current_kit",)
                ),
                last_error=error or "capture failed",
            )
        self._store(device_id, next_state, force_revision=True)
        return self

    def record_connection(self, device_id: StageDeviceId, *, connected: bool) -> Self:
        """Revoke only the disconnected lane and make stale artifacts explicit."""

        current = self._machine(device_id)
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
            if device_id == "analog_four_mk2" or current.capture_state == "failed":
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
        self._store(device_id, next_state, force_revision=True)
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
                "blocked"
                if device_id == "analog_four_mk2"
                else (
                    "stale"
                    if changed and current.plan_state in ("ready", "blocked")
                    else current.plan_state
                )
            ),
            recovery_actions=(
                ("preview_again", "prepare_again") if changed else current.recovery_actions
            ),
        )
        self._store(device_id, next_state)
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
            plan_state="blocked" if device_id == "analog_four_mk2" else "none",
            blocked_reasons=reasons,
            recovery_actions=(
                ("prepare",)
                if ready
                else ("preview",) if ready is None else ("adjust_scope_or_depth",)
            ),
        )
        self._store(device_id, next_state, force_revision=True)
        return self

    def record_plan(self, device_id: StageDeviceId, *, ready: bool) -> Self:
        """Record PREPARE result while keeping machine authorities separate."""

        current = self._machine(device_id)
        if device_id == "analog_four_mk2":
            next_state = replace(
                current,
                plan_state="blocked",
                authority_state="blocked",
                blocked_reasons=tuple(
                    dict.fromkeys((*current.blocked_reasons, "a4_semantic_mapping_unpromoted"))
                ),
                recovery_actions=("run_a4_mapping_gap_procedure",),
            )
        else:
            next_state = replace(
                current,
                plan_state="ready" if ready else "blocked",
                recovery_actions=("confirm_exact_plan",) if ready else ("preview_again",),
            )
        self._store(device_id, next_state, force_revision=True)
        return self

    def record_rytm_authority(
        self,
        *,
        armed: bool,
        blocked_reason: str | None = None,
    ) -> Self:
        """Record only Rytm transmit authority; A4 remains isolated."""

        self._rytm_send_armed = armed
        unavailable_reason: str | None = None
        if armed and self._rytm.capture_state == "failed":
            unavailable_reason = "capture_failed"
        elif armed and self._rytm.connection_state == "disconnected":
            unavailable_reason = "device_disconnected"
        effective_block = blocked_reason or unavailable_reason
        reasons = tuple(reason for reason in self._rytm.blocked_reasons if reason != "send_failed")
        if effective_block is not None:
            reasons = tuple(dict.fromkeys((*reasons, effective_block)))
        authority: StageAuthorityState
        if effective_block is not None:
            authority = "blocked"
        else:
            authority = "armed" if armed else "not_armed"
        self._store(
            "analog_rytm_mk2",
            replace(
                self._rytm,
                authority_state=authority,
                blocked_reasons=reasons,
                recovery_actions=(
                    ("confirm_exact_plan",)
                    if armed and self._rytm.plan_state == "ready"
                    else ("re_arm", "prepare_again") if effective_block is not None else ("arm",)
                ),
            ),
        )
        return self

    def record_send(self, device_id: StageDeviceId, *, succeeded: bool) -> Self:
        """Consume one lane's prepared artifacts without touching its sibling."""

        current = self._machine(device_id)
        if device_id == "analog_four_mk2":
            next_state = replace(
                current,
                candidate_state="blocked",
                plan_state="blocked",
                authority_state="blocked",
                blocked_reasons=tuple(dict.fromkeys((*current.blocked_reasons, _A4_MAPPING_BLOCK))),
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
        self._store(device_id, next_state, force_revision=True)
        return self


__all__ = [
    "DualMachineStageCoordinator",
    "DualMachineStageState",
    "DualMachineStageStateDict",
    "MachineStageState",
    "MachineStageStateDict",
    "StageArtifactState",
    "StageAuthorityState",
    "StageCaptureState",
    "StageConnectionState",
    "StageDeviceId",
]
