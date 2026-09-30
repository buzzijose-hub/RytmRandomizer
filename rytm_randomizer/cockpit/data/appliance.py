"""Validated appliance records; transient authority is absent from saved rules."""

from __future__ import annotations

from typing import Literal, TypedDict

from .stage import StageDeviceId

ApplianceTarget = Literal["rytm", "a4", "both"]


class ApplianceScopeRecord(TypedDict):
    target_ids: list[int]
    locked_ids: list[int]
    page_ids: list[str]
    track_depths: dict[str, float]
    page_depths: dict[str, float]
    parameter_locks: list[str]


class ApplianceAssociationRecord(TypedDict):
    device_ids: list[StageDeviceId]
    fingerprints: dict[StageDeviceId, str | None]


class ApplianceProfileRecord(TypedDict):
    target: ApplianceTarget
    master_depth: float
    lanes: dict[StageDeviceId, ApplianceScopeRecord]
    association: ApplianceAssociationRecord


class ApplianceChangeRecord(TypedDict):
    device_id: StageDeviceId
    track_id: int
    parameter_id: str
    parameter: str
    page: str
    before: int
    after: int
    before_display: str
    after_display: str


class ApplianceCandidateRecord(TypedDict):
    candidate_id: str
    revision: int
    changes: list[ApplianceChangeRecord]
    send_plan_id: str | None
    live_ready: bool
    blocked_reasons: list[str]


class ApplianceReceiptRecord(TypedDict):
    status: Literal["simulated_local_apply", "local_history_only"]
    sent_count: int
    expected_count: int
    hardware_verified: Literal[False]
