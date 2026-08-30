"""Tests for registered-device-derived live-stage lane policy."""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.stage import (
    A4_LANE_POLICY,
    A4_MAPPING_BLOCK_REASON,
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    RYTM_LANE_POLICY,
    STAGE_LANE_POLICIES,
    stage_lane_policy,
)
from rytm_randomizer.devices import get_device

pytestmark = pytest.mark.fast


@pytest.mark.parametrize(
    "device_id",
    [ANALOG_RYTM_DEVICE_ID, ANALOG_FOUR_DEVICE_ID],
)
def test_lane_policy_cardinality_comes_from_registered_device(device_id: str) -> None:
    policy = STAGE_LANE_POLICIES[device_id]  # type: ignore[index]
    registered = get_device(device_id)

    assert policy.device_id == registered.device_id
    assert policy.available_ids == frozenset(range(1, registered.track_count + 1))
    assert policy.minimum_id == 1
    assert policy.maximum_id == registered.track_count
    assert stage_lane_policy(policy.device_id) is policy


def test_lane_policies_keep_machine_authority_distinct() -> None:
    assert RYTM_LANE_POLICY.item_label == "Rytm pad"
    assert RYTM_LANE_POLICY.output_authority_supported is True
    assert RYTM_LANE_POLICY.persistent_block_reason is None
    assert A4_LANE_POLICY.item_label == "A4 track"
    assert A4_LANE_POLICY.output_authority_supported is False
    assert A4_LANE_POLICY.persistent_block_reason == A4_MAPPING_BLOCK_REASON
