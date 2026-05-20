"""Tests for passive Rytm snapshot-machine routing."""

from __future__ import annotations

from types import MappingProxyType

import pytest

pytestmark = pytest.mark.fast


def test_route_machine_values_accepts_mutable_legal_machine() -> None:
    from rytm_randomizer.devices.strategies import route_rytm_snapshot_machine_values

    result = route_rytm_snapshot_machine_values({1: 0, 2: 3, 3: 32})

    assert result.ready is True
    assert result.ready_pad_count == 3
    assert result.blocked_pad_count == 0
    assert result.profile_keys_by_pad == {1: "2", 2: "10", 3: "5"}
    assert result.routes_by_pad[1].machine_key == "bd_hard"
    assert result.routes_by_pad[2].machine_key == "sd_classic"
    assert result.routes_by_pad[3].machine_key == "sy_raw"


def test_route_machine_values_blocks_selectable_only_machine() -> None:
    from rytm_randomizer.devices.strategies import route_rytm_snapshot_machine_values

    result = route_rytm_snapshot_machine_values({10: 10})

    assert result.ready is False
    assert result.ready_pad_count == 0
    assert result.blocked_pad_count == 1
    route = result.routes_by_pad[10]
    assert route.ready is False
    assert route.profile_key is None
    assert route.machine_key == "oh_classic"
    assert "selectable-only" in route.reason


def test_route_machine_values_blocks_illegal_pad_machine_pair() -> None:
    from rytm_randomizer.devices.strategies import route_rytm_snapshot_machine_values

    result = route_rytm_snapshot_machine_values({10: 8})

    assert result.ready is False
    route = result.routes_by_pad[10]
    assert route.machine_key == "xt_classic"
    assert "not legal on Pad 10 / OH" in route.reason


def test_route_machine_values_blocks_unknown_pad_and_machine_value() -> None:
    from rytm_randomizer.devices.strategies import route_rytm_snapshot_machine_values

    result = route_rytm_snapshot_machine_values({0: 0, 1: 127})

    assert result.ready is False
    assert "Unknown Rytm pad: 0" in result.routes_by_pad[0].reason
    assert "Unknown Rytm machine value: 127" in result.routes_by_pad[1].reason


def test_route_machine_values_explains_empty_snapshot_facts() -> None:
    from rytm_randomizer.devices.strategies import route_rytm_snapshot_machine_values

    result = route_rytm_snapshot_machine_values({})

    assert result.ready is False
    assert result.ready_pad_count == 0
    assert result.blocked_pad_count == 0
    assert result.readiness_reason == "no snapshot machine values supplied"


def test_route_machine_values_blocks_mutable_machine_without_profile_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import rytm_randomizer.devices.strategies.analog_rytm_snapshot_routing as routing

    monkeypatch.setattr(
        routing,
        "_PROFILE_KEY_BY_MACHINE_VALUE",
        MappingProxyType({}),
    )

    result = routing.route_rytm_snapshot_machine_values({1: 0})

    assert result.ready is False
    assert result.routes_by_pad[1].machine_key == "bd_hard"
    assert result.routes_by_pad[1].profile_key is None
    assert "has no V1.34 profile key" in result.readiness_reason
