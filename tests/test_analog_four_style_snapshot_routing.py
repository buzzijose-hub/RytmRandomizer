"""Tests for passive Analog Four style snapshot routing."""

from __future__ import annotations

from types import MappingProxyType

import pytest

pytestmark = pytest.mark.fast


def _snapshot(*, offsets_promoted: bool = False):
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot

    return AnalogFourKitSnapshot(
        slot=3,
        kit_name="A4STYLE",
        raw=b"\x00\x20\x3c\x07" + b"A4STYLE".ljust(16, b"\x00"),
        offsets_promoted=offsets_promoted,
    )


def test_analog_four_style_routes_block_candidate_only_offsets():
    from rytm_randomizer.devices.strategies import plan_analog_four_style_snapshot_routes

    plan = plan_analog_four_style_snapshot_routes(
        _snapshot(offsets_promoted=False),
        "birmingham_pressure",
    )

    assert plan.kit_name == "A4STYLE"
    assert plan.slot == 3
    assert plan.style_key == "birmingham_pressure"
    assert plan.style_focus == (
        "overdriven monotone stab",
        "dark filter pressure",
        "short metallic scrape",
    )
    assert plan.favored_zones[:3] == ("drive", "oscillator", "filter")
    assert plan.ready_track_count == 0
    assert plan.blocked_track_count == 4
    assert plan.partial_snapshot_mutation_ready is False
    assert tuple(plan.tracks_by_track) == (1, 2, 3, 4)
    assert all(not track.route_ready for track in plan.tracks_by_track.values())
    assert all(
        "offsets are candidate-only" in track.readiness_reason
        for track in plan.tracks_by_track.values()
    )


def test_analog_four_style_routes_promoted_offsets_to_four_ready_tracks():
    from rytm_randomizer.devices.strategies import plan_analog_four_style_snapshot_routes

    plan = plan_analog_four_style_snapshot_routes(
        _snapshot(offsets_promoted=True),
        "deep_dark_hypnosis",
    )

    assert plan.favored_zones[:3] == ("effects", "modulation", "filter")
    assert plan.ready_track_count == 4
    assert plan.blocked_track_count == 0
    assert plan.partial_snapshot_mutation_ready is True
    assert {track.role_key for track in plan.tracks_by_track.values()} == {
        "bass_foundation",
        "stab_pulse",
        "texture_motion",
        "space_accent",
    }
    assert all(track.route_ready for track in plan.tracks_by_track.values())
    assert all(track.readiness_reason == "" for track in plan.tracks_by_track.values())
    assert plan.tracks_by_track[4].score > plan.tracks_by_track[2].score


def test_analog_four_style_routes_reject_unknown_style_key():
    from rytm_randomizer.devices.strategies import plan_analog_four_style_snapshot_routes

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        plan_analog_four_style_snapshot_routes(_snapshot(), "ghost_style")


def test_analog_four_style_routes_reject_wrong_snapshot_type():
    from rytm_randomizer.devices.strategies import plan_analog_four_style_snapshot_routes

    with pytest.raises(ValueError, match="AnalogFourKitSnapshot"):
        plan_analog_four_style_snapshot_routes("not a snapshot", "detroit_minimal")


def test_analog_four_style_routes_are_deterministic_and_read_only():
    from rytm_randomizer.devices.strategies import (
        AnalogFourStyleSnapshotRoutingPlan,
        plan_analog_four_style_snapshot_routes,
    )

    snapshot = _snapshot(offsets_promoted=True)
    first = plan_analog_four_style_snapshot_routes(snapshot, "warehouse_peak")
    second = plan_analog_four_style_snapshot_routes(snapshot, "warehouse_peak")

    assert isinstance(first, AnalogFourStyleSnapshotRoutingPlan)
    assert first == second
    assert isinstance(first.tracks_by_track, MappingProxyType)
    with pytest.raises(TypeError):
        first.tracks_by_track[5] = first.tracks_by_track[1]
