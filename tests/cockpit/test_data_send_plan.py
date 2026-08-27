"""Tests for ``rytm_randomizer.cockpit.data.send_plan``.

The send plan is the inert, deterministic object that sits between a
``MutationCandidate`` preview and the SEND action. It must be serialisable
for the WebSocket/desktop UI and safe to inspect without opening MIDI ports.
"""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.data import CockpitSendPlan, SendPlanPacket

pytestmark = pytest.mark.fast


def _packet(pad_id: int = 1, parameter: str = "tun", value: int = 64) -> SendPlanPacket:
    return SendPlanPacket(
        pad_id=pad_id,
        parameter=parameter,
        channel=0,
        control=74,
        value=value,
    )


def _plan(*packets: SendPlanPacket) -> CockpitSendPlan:
    return CockpitSendPlan(
        plan_id="sendplan-abcdef0123456789",
        candidate_id="candidate-1",
        source_snapshot_id="snapshot-1",
        profile_id="profile-1",
        ready=True,
        readiness_reason="ready",
        safety_status="safe",
        packets=packets or (_packet(),),
        locked_pad_ids=frozenset({2}),
        blocked_reasons=(),
    )


def test_send_plan_packet_round_trips_through_dict() -> None:
    packet = _packet(pad_id=3, parameter="dec", value=91)

    restored = SendPlanPacket.from_dict(packet.to_dict())

    assert restored == packet
    assert restored.to_dict() == {
        "pad_id": 3,
        "parameter": "dec",
        "channel": 0,
        "control": 74,
        "value": 91,
    }


def test_send_plan_packet_rejects_out_of_range_midi_values() -> None:
    with pytest.raises(ValueError, match="pad_id must be in \\[1, 12\\]"):
        _packet(pad_id=0)

    with pytest.raises(ValueError, match="parameter must be a non-empty string"):
        _packet(parameter="")

    with pytest.raises(ValueError, match="value must be in \\[0, 127\\]"):
        _packet(value=128)

    with pytest.raises(ValueError, match="control must be in \\[0, 127\\]"):
        SendPlanPacket(pad_id=1, parameter="tun", channel=0, control=128, value=64)

    with pytest.raises(ValueError, match="channel must be in \\[0, 15\\]"):
        SendPlanPacket(pad_id=1, parameter="tun", channel=16, control=74, value=64)


def test_send_plan_round_trips_and_exposes_ui_counts() -> None:
    plan = _plan(
        _packet(pad_id=1, parameter="dec", value=80),
        _packet(pad_id=3, parameter="lev", value=110),
    )

    restored = CockpitSendPlan.from_dict(plan.to_dict())

    assert restored == plan
    assert restored.to_dict()["estimated_midi_msgs"] == 2
    assert restored.to_dict()["pad_count"] == 2
    assert restored.to_dict()["locked_pad_ids"] == [2]


def test_blocked_plan_requires_blocked_reason() -> None:
    with pytest.raises(ValueError, match="blocked_reasons"):
        CockpitSendPlan(
            plan_id="sendplan-blocked",
            candidate_id="candidate-1",
            source_snapshot_id="snapshot-1",
            profile_id="profile-1",
            ready=False,
            readiness_reason="candidate_high_risk",
            safety_status="high_risk",
            packets=(),
            locked_pad_ids=frozenset(),
            blocked_reasons=(),
        )


def test_blocked_plan_allows_non_ready_reason_with_blocked_reason() -> None:
    plan = CockpitSendPlan(
        plan_id="sendplan-blocked",
        candidate_id="candidate-1",
        source_snapshot_id="snapshot-1",
        profile_id="profile-1",
        ready=False,
        readiness_reason="candidate_high_risk",
        safety_status="high_risk",
        packets=(),
        locked_pad_ids=frozenset(),
        blocked_reasons=("candidate_high_risk",),
    )

    assert plan.to_dict()["ready"] is False


def test_ready_plan_rejects_blocked_reason() -> None:
    with pytest.raises(ValueError, match="ready plans must not carry blocked_reasons"):
        CockpitSendPlan(
            plan_id="sendplan-ready",
            candidate_id="candidate-1",
            source_snapshot_id="snapshot-1",
            profile_id="profile-1",
            ready=True,
            readiness_reason="ready",
            safety_status="safe",
            packets=(_packet(),),
            locked_pad_ids=frozenset(),
            blocked_reasons=("candidate_high_risk",),
        )


def test_send_plan_rejects_empty_identity_fields() -> None:
    for field_name in ("plan_id", "candidate_id", "source_snapshot_id", "profile_id"):
        kwargs = {
            "plan_id": "sendplan-ready",
            "candidate_id": "candidate-1",
            "source_snapshot_id": "snapshot-1",
            "profile_id": "profile-1",
            "ready": True,
            "readiness_reason": "ready",
            "safety_status": "safe",
            "packets": (_packet(),),
            "locked_pad_ids": frozenset(),
            "blocked_reasons": (),
        }
        kwargs[field_name] = ""

        with pytest.raises(ValueError, match=field_name):
            CockpitSendPlan(**kwargs)


def test_send_plan_rejects_unknown_status_and_reasons() -> None:
    base = _plan().to_dict()

    invalid_reason = dict(base)
    invalid_reason["readiness_reason"] = "unknown"
    with pytest.raises(ValueError, match="readiness_reason"):
        CockpitSendPlan.from_dict(invalid_reason)

    invalid_status = dict(base)
    invalid_status["safety_status"] = "warming_up"
    with pytest.raises(ValueError, match="safety_status"):
        CockpitSendPlan.from_dict(invalid_status)

    invalid_blocked = dict(base)
    invalid_blocked.update(
        ready=False,
        readiness_reason="candidate_high_risk",
        safety_status="high_risk",
        blocked_reasons=["mystery"],
    )
    with pytest.raises(ValueError, match="blocked_reasons contains unknown values"):
        CockpitSendPlan.from_dict(invalid_blocked)

    with pytest.raises(ValueError, match="readiness_reason must be one of"):
        CockpitSendPlan(
            plan_id="sendplan-invalid-reason",
            candidate_id="candidate-1",
            source_snapshot_id="snapshot-1",
            profile_id="profile-1",
            ready=True,
            readiness_reason="unknown",  # type: ignore[arg-type]
            safety_status="safe",
            packets=(_packet(),),
            locked_pad_ids=frozenset(),
            blocked_reasons=(),
        )

    with pytest.raises(ValueError, match="safety_status must be one of"):
        CockpitSendPlan(
            plan_id="sendplan-invalid-status",
            candidate_id="candidate-1",
            source_snapshot_id="snapshot-1",
            profile_id="profile-1",
            ready=True,
            readiness_reason="ready",
            safety_status="unknown",  # type: ignore[arg-type]
            packets=(_packet(),),
            locked_pad_ids=frozenset(),
            blocked_reasons=(),
        )


def test_send_plan_rejects_inconsistent_ready_and_blocked_states() -> None:
    with pytest.raises(ValueError, match="ready plans must use readiness_reason"):
        CockpitSendPlan(
            plan_id="sendplan-ready",
            candidate_id="candidate-1",
            source_snapshot_id="snapshot-1",
            profile_id="profile-1",
            ready=True,
            readiness_reason="profile_mismatch",
            safety_status="safe",
            packets=(_packet(),),
            locked_pad_ids=frozenset(),
            blocked_reasons=(),
        )

    with pytest.raises(ValueError, match="ready plans must contain at least one packet"):
        CockpitSendPlan(
            plan_id="sendplan-ready",
            candidate_id="candidate-1",
            source_snapshot_id="snapshot-1",
            profile_id="profile-1",
            ready=True,
            readiness_reason="ready",
            safety_status="safe",
            packets=(),
            locked_pad_ids=frozenset(),
            blocked_reasons=(),
        )

    with pytest.raises(ValueError, match="blocked plans must not use readiness_reason"):
        CockpitSendPlan(
            plan_id="sendplan-blocked",
            candidate_id="candidate-1",
            source_snapshot_id="snapshot-1",
            profile_id="profile-1",
            ready=False,
            readiness_reason="ready",
            safety_status="safe",
            packets=(),
            locked_pad_ids=frozenset(),
            blocked_reasons=("candidate_high_risk",),
        )


def test_send_plan_rejects_packets_that_contradict_targets_or_locks() -> None:
    with pytest.raises(ValueError, match="locked pad ids"):
        CockpitSendPlan(
            plan_id="sendplan-locked-packet",
            candidate_id="candidate-1",
            source_snapshot_id="snapshot-1",
            profile_id="profile-1",
            ready=True,
            readiness_reason="ready",
            safety_status="safe",
            packets=(_packet(pad_id=1),),
            locked_pad_ids=frozenset({1}),
            blocked_reasons=(),
        )

    with pytest.raises(ValueError, match="untargeted pad ids"):
        CockpitSendPlan(
            plan_id="sendplan-untargeted-packet",
            candidate_id="candidate-1",
            source_snapshot_id="snapshot-1",
            profile_id="profile-1",
            ready=True,
            readiness_reason="ready",
            safety_status="safe",
            packets=(_packet(pad_id=1),),
            locked_pad_ids=frozenset(),
            blocked_reasons=(),
            target_pad_ids=frozenset({2}),
        )


def test_send_plan_from_dict_rejects_non_sequence_fields() -> None:
    base = _plan().to_dict()

    bad_packets = dict(base)
    bad_packets["packets"] = {"pad_id": 1}
    with pytest.raises(TypeError, match="packets must be a list/tuple"):
        CockpitSendPlan.from_dict(bad_packets)

    bad_locks = dict(base)
    bad_locks["locked_pad_ids"] = "2"
    with pytest.raises(TypeError, match="locked_pad_ids must be an iterable"):
        CockpitSendPlan.from_dict(bad_locks)

    bad_targets = dict(base)
    bad_targets["target_pad_ids"] = "2"
    with pytest.raises(TypeError, match="target_pad_ids must be an iterable"):
        CockpitSendPlan.from_dict(bad_targets)

    bad_blocked = dict(base)
    bad_blocked["blocked_reasons"] = {"reason": "candidate_high_risk"}
    with pytest.raises(TypeError, match="blocked_reasons must be a list/tuple"):
        CockpitSendPlan.from_dict(bad_blocked)


@pytest.mark.parametrize("field_name", ["locked_pad_ids", "target_pad_ids"])
@pytest.mark.parametrize("bad_id", [True, 1.5, "2", 13])
def test_send_plan_from_dict_rejects_non_integer_or_out_of_range_pad_ids(
    field_name: str,
    bad_id: object,
) -> None:
    payload = _plan().to_dict()
    payload[field_name] = [bad_id]

    with pytest.raises(ValueError, match=field_name):
        CockpitSendPlan.from_dict(payload)
