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


class ApplianceProfileDocumentRecord(TypedDict):
    schema_version: int
    profiles: dict[str, ApplianceProfileRecord]


class ApplianceProfileSummaryRecord(TypedDict):
    name: str
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


class ApplianceProvenanceRecord(TypedDict):
    source_type: Literal["simulation", "saved_kit", "disconnected"]
    fingerprint: str | None
    captured_at: str | None
    kit_name: str | None
    working_state_verified: Literal[False]


class ApplianceParameterRecord(TypedDict):
    parameter_id: str
    page: str
    parameter: str
    cockpit_key: str | None
    machine_key: str | None
    value: int | None
    values_by_track: dict[str, int]
    display_value: str | None
    display_values_by_track: dict[str, str]
    default_protected: bool
    categorical: bool
    protection_reasons: list[str]
    blockers: list[str]


class ApplianceLaneRecord(TypedDict):
    device_id: StageDeviceId
    reference_track_id: int | None
    scope: ApplianceScopeRecord
    provenance: ApplianceProvenanceRecord
    parameters: list[ApplianceParameterRecord]
    blocked_reasons: list[str]


class ApplianceHistoryRecord(TypedDict):
    can_undo: bool
    can_redo: bool
    count: int
    anchor_captured: bool
    hardware_restore_supported: Literal[False]


class ApplianceStateRecord(TypedDict):
    schema_version: int
    revision: int
    mode: Literal["simulation", "production"]
    target: ApplianceTarget
    master_depth: float
    armed: bool
    lanes: dict[StageDeviceId, ApplianceLaneRecord]
    candidate: ApplianceCandidateRecord | None
    history: ApplianceHistoryRecord
    profiles: list[ApplianceProfileSummaryRecord]
    last_receipt: ApplianceReceiptRecord | None
    blocked_reasons: list[str]
