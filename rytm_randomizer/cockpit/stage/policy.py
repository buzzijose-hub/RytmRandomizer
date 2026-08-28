"""Immutable live-stage lane policy derived from registered devices."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, cast

from ...devices import get_device
from ..data.stage import StageDeviceId

ANALOG_RYTM_DEVICE_ID: Final[StageDeviceId] = "analog_rytm_mk2"
ANALOG_FOUR_DEVICE_ID: Final[StageDeviceId] = "analog_four_mk2"
A4_MAPPING_BLOCK_REASON: Final[str] = "a4_semantic_mapping_unpromoted"


@dataclass(frozen=True)
class StageLanePolicy:
    """Stable per-device facts needed by targeting and stage orchestration."""

    device_id: StageDeviceId
    item_label: str
    available_ids: frozenset[int]
    output_authority_supported: bool
    persistent_block_reason: str | None = None

    @property
    def minimum_id(self) -> int:
        """Return the first registered target identifier."""

        return min(self.available_ids)

    @property
    def maximum_id(self) -> int:
        """Return the last registered target identifier."""

        return max(self.available_ids)


def _registered_lane_policy(
    registry_key: StageDeviceId,
    *,
    item_label: str,
    output_authority_supported: bool,
    persistent_block_reason: str | None = None,
) -> StageLanePolicy:
    device = get_device(registry_key)
    return StageLanePolicy(
        device_id=cast(StageDeviceId, device.device_id),
        item_label=item_label,
        available_ids=frozenset(range(1, device.track_count + 1)),
        output_authority_supported=output_authority_supported,
        persistent_block_reason=persistent_block_reason,
    )


RYTM_LANE_POLICY: Final[StageLanePolicy] = _registered_lane_policy(
    ANALOG_RYTM_DEVICE_ID,
    item_label="Rytm pad",
    output_authority_supported=True,
)
A4_LANE_POLICY: Final[StageLanePolicy] = _registered_lane_policy(
    ANALOG_FOUR_DEVICE_ID,
    item_label="A4 track",
    output_authority_supported=False,
    persistent_block_reason=A4_MAPPING_BLOCK_REASON,
)

STAGE_LANE_POLICIES: Final[Mapping[StageDeviceId, StageLanePolicy]] = MappingProxyType(
    {
        RYTM_LANE_POLICY.device_id: RYTM_LANE_POLICY,
        A4_LANE_POLICY.device_id: A4_LANE_POLICY,
    }
)


def stage_lane_policy(device_id: StageDeviceId) -> StageLanePolicy:
    """Return the immutable policy for one canonical registered device id."""

    return STAGE_LANE_POLICIES[device_id]


__all__ = [
    "A4_LANE_POLICY",
    "A4_MAPPING_BLOCK_REASON",
    "ANALOG_FOUR_DEVICE_ID",
    "ANALOG_RYTM_DEVICE_ID",
    "RYTM_LANE_POLICY",
    "STAGE_LANE_POLICIES",
    "StageLanePolicy",
    "stage_lane_policy",
]
