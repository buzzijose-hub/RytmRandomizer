"""Tests for Analog Four mutation planner Strategy."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _snapshot(*, offsets_promoted: bool = False):
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot

    return AnalogFourKitSnapshot(
        slot=1,
        kit_name="A4",
        raw=b"\x00\x20\x3c\x07" + bytes(32),
        offsets_promoted=offsets_promoted,
    )


def test_plan_returns_not_ready_when_offsets_are_candidate_only() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlanner

    plan = AnalogFourMutationPlanner(seed=0).plan(_snapshot(offsets_promoted=False), depth=1)

    assert plan.ready is False
    assert plan.events == ()
    assert "offsets are candidate" in plan.readiness_reason


def test_plan_returns_ready_events_when_offsets_are_promoted() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlanner

    plan = AnalogFourMutationPlanner(seed=0).plan(_snapshot(offsets_promoted=True), depth=1)

    assert plan.ready is True
    assert plan.readiness_reason == ""
    assert len(plan.events) == 4
    assert {event.track for event in plan.events} == {1, 2, 3, 4}


def test_plan_rejects_wrong_snapshot_type() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlanner

    with pytest.raises(ValueError, match="AnalogFourKitSnapshot"):
        AnalogFourMutationPlanner().plan("not a snapshot", depth=1)  # type: ignore[arg-type]


def test_plan_rejects_depth_outside_bounds() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlanner

    planner = AnalogFourMutationPlanner()

    with pytest.raises(ValueError, match=r"\[0,\s*7\]"):
        planner.plan(_snapshot(offsets_promoted=True), depth=-1)
    with pytest.raises(ValueError, match=r"\[0,\s*7\]"):
        planner.plan(_snapshot(offsets_promoted=True), depth=8)


def test_plan_is_deterministic_for_same_seed_slot_and_depth() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlanner

    planner = AnalogFourMutationPlanner(seed=99)
    snap = _snapshot(offsets_promoted=True)

    assert planner.plan(snap, depth=3) == planner.plan(snap, depth=3)
