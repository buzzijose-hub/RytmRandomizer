"""Tests for the pure cockpit send-plan builder."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rytm_randomizer.cockpit.data import (
    MutationCandidate,
    PadDelta,
    PadState,
    ProfileModel,
    Snapshot,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.engine import prepare_send_plan

pytestmark = pytest.mark.fast

_FIXED_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


def _snapshot(snapshot_id: str = "snapshot-1") -> Snapshot:
    return Snapshot(
        snapshot_id=snapshot_id,
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": 32, "dec": 80}),
            PadState(pad_id=2, machine="SD Acoustic", params={"tun": 40, "dec": 60}),
        ),
        scene_slot="A01",
        bpm=124.0,
    )


def _profile(profile_id: str = "profile-1") -> ProfileModel:
    return ProfileModel(
        profile_id=profile_id,
        name="test profile",
        kind="user",
        model_version="1.0.0",
        traits=(StyleTrait(name="drive", value=0.5),),
        pad_mappings=(TraitPadWeight(trait="drive", pad_id=1, weight=1.0),),
        transition_curve="linear",
        source_summary="test",
    )


def _delta(pad_id: int, **params: int) -> PadDelta:
    params = params or {"tun": 70, "dec": 91}
    return PadDelta(
        pad_id=pad_id,
        proposed_params=params,
        changed_keys=frozenset(params),
    )


def _candidate(
    *,
    source_snapshot_id: str = "snapshot-1",
    profile_id: str = "profile-1",
    safety_status: str = "safe",
) -> MutationCandidate:
    return MutationCandidate(
        candidate_id="candidate-1",
        source_snapshot_id=source_snapshot_id,
        profile_id=profile_id,
        depth=0.5,
        seed=42,
        pad_deltas=(_delta(1, tun=70, dec=91), _delta(2, tun=51)),
        safety_status=safety_status,  # type: ignore[arg-type]
        estimated_midi_msgs=3,
    )


def test_prepare_send_plan_builds_ready_deterministic_packets() -> None:
    plan = prepare_send_plan(_snapshot(), _profile(), _candidate(), frozenset())
    again = prepare_send_plan(_snapshot(), _profile(), _candidate(), frozenset())

    assert plan is not None
    assert again is not None
    assert plan.ready is True
    assert plan.plan_id == again.plan_id
    assert [packet.to_dict() for packet in plan.packets] == [
        {"pad_id": 1, "parameter": "dec", "channel": 0, "control": 44, "value": 91},
        {"pad_id": 1, "parameter": "tun", "channel": 0, "control": 52, "value": 70},
        {"pad_id": 2, "parameter": "tun", "channel": 0, "control": 52, "value": 51},
    ]


def test_prepare_send_plan_excludes_locked_pads_but_stays_ready_for_remaining_packets() -> None:
    plan = prepare_send_plan(_snapshot(), _profile(), _candidate(), frozenset({2}))

    assert plan is not None
    assert plan.ready is True
    assert plan.locked_pad_ids == frozenset({2})
    assert {packet.pad_id for packet in plan.packets} == {1}
    assert plan.to_dict()["estimated_midi_msgs"] == 2


def test_prepare_send_plan_blocks_when_all_candidate_changes_are_locked() -> None:
    plan = prepare_send_plan(_snapshot(), _profile(), _candidate(), frozenset({1, 2}))

    assert plan is not None
    assert plan.ready is False
    assert plan.readiness_reason == "no_sendable_changes"
    assert plan.blocked_reasons == ("no_sendable_changes",)
    assert plan.packets == ()


def test_prepare_send_plan_blocks_high_risk_candidates() -> None:
    plan = prepare_send_plan(
        _snapshot(),
        _profile(),
        _candidate(safety_status="high_risk"),
        frozenset(),
    )

    assert plan is not None
    assert plan.ready is False
    assert plan.readiness_reason == "candidate_high_risk"
    assert "candidate_high_risk" in plan.blocked_reasons


def test_prepare_send_plan_blocks_profile_and_snapshot_mismatch() -> None:
    plan = prepare_send_plan(
        _snapshot(snapshot_id="snapshot-live"),
        _profile(profile_id="profile-live"),
        _candidate(source_snapshot_id="snapshot-old", profile_id="profile-old"),
        frozenset(),
    )

    assert plan is not None
    assert plan.ready is False
    assert plan.blocked_reasons == (
        "profile_mismatch",
        "source_snapshot_mismatch",
    )


def test_prepare_send_plan_returns_none_without_profile_or_candidate() -> None:
    assert prepare_send_plan(_snapshot(), None, _candidate(), frozenset()) is None
    assert prepare_send_plan(_snapshot(), _profile(), None, frozenset()) is None
