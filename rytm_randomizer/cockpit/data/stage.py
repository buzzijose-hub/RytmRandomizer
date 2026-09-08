"""Frozen, hardware-inert dual-machine Cockpit stage data transfer objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, TypedDict

StageDeviceId = Literal["analog_rytm_mk2", "analog_four_mk2"]
STAGE_DEVICE_IDS: Final[tuple[StageDeviceId, ...]] = ("analog_rytm_mk2", "analog_four_mk2")
ANALOG_RYTM_DEVICE_ID: Final[StageDeviceId] = STAGE_DEVICE_IDS[0]
ANALOG_FOUR_DEVICE_ID: Final[StageDeviceId] = STAGE_DEVICE_IDS[1]
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


__all__ = [
    "STAGE_DEVICE_IDS",
    "ANALOG_RYTM_DEVICE_ID",
    "ANALOG_FOUR_DEVICE_ID",
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
