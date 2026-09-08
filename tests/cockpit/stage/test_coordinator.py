"""Tests for the hardware-inert dual-machine stage coordinator."""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

from rytm_randomizer.cockpit.stage import DualMachineStageCoordinator

pytestmark = pytest.mark.fast


@pytest.fixture
def capture_stage_logs(
    caplog: pytest.LogCaptureFixture,
) -> Iterator[pytest.LogCaptureFixture]:
    """Capture structured stage transitions despite package log isolation."""

    logger = logging.getLogger("rytm_randomizer.cockpit.stage.coordinator")
    prior_level = logger.level
    prior_propagate = logger.propagate
    logger.setLevel(logging.INFO)
    # Capture through exactly one handler even if a prior test changed the
    # package logger's propagation setting.  xdist schedules files differently
    # across platforms, so relying on ambient logger ancestry double-counted
    # each transition on macOS CI.
    logger.propagate = False
    logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)
        logger.propagate = prior_propagate
        logger.setLevel(prior_level)


def test_stage_bootstrap_keeps_oxi_adjacent_and_a4_unsendable() -> None:
    state = DualMachineStageCoordinator(rytm_send_armed=True).state.to_dict()

    assert state["oxi_owns_sequencing"] is True
    assert state["direct_oxi_control"] is False
    assert state["rytm"]["authority_state"] == "armed"
    assert state["analog_four"]["authority_state"] == "blocked"
    assert state["analog_four"]["plan_state"] == "blocked"
    assert state["analog_four"]["blocked_reasons"] == ["a4_hardware_audition_validation_pending"]


def test_partial_capture_failure_does_not_corrupt_other_machine() -> None:
    coordinator = DualMachineStageCoordinator(rytm_send_armed=True)
    coordinator.record_capture(
        "analog_rytm_mk2",
        succeeded=True,
        connected=True,
    )
    captured_rytm = coordinator.state.rytm

    coordinator.record_capture(
        "analog_four_mk2",
        succeeded=False,
        connected=False,
        error="A4 capture timed out",
    )

    assert coordinator.state.rytm == captured_rytm
    assert coordinator.state.rytm.authority_state == "armed"
    assert coordinator.state.analog_four.capture_state == "failed"
    assert coordinator.state.analog_four.connection_state == "disconnected"
    assert coordinator.state.analog_four.last_error == "A4 capture timed out"


def test_target_or_lock_change_marks_only_that_machine_stale() -> None:
    coordinator = DualMachineStageCoordinator(rytm_send_armed=True)
    coordinator.record_candidate("analog_rytm_mk2", ready=True)
    coordinator.record_plan("analog_rytm_mk2", ready=True)
    coordinator.record_candidate(
        "analog_four_mk2",
        ready=False,
        blocked_reason="a4_hardware_audition_validation_pending",
    )
    a4_before = coordinator.state.analog_four

    coordinator.record_scope(
        "analog_rytm_mk2",
        target_ids=frozenset({1, 2}),
        locked_ids=frozenset({2}),
        effective_ids=frozenset({1}),
    )

    assert coordinator.state.rytm.candidate_state == "stale"
    assert coordinator.state.rytm.plan_state == "stale"
    assert coordinator.state.rytm.effective_ids == frozenset({1})
    assert coordinator.state.analog_four == a4_before


def test_disconnect_revokes_one_lane_and_reconnect_requires_reprepare() -> None:
    coordinator = DualMachineStageCoordinator(rytm_send_armed=True)
    coordinator.record_capture("analog_rytm_mk2", succeeded=True, connected=True)
    coordinator.record_candidate("analog_rytm_mk2", ready=True)
    coordinator.record_plan("analog_rytm_mk2", ready=True)
    a4_before = coordinator.state.analog_four

    coordinator.record_connection("analog_rytm_mk2", connected=False)

    assert coordinator.state.rytm.connection_state == "disconnected"
    assert coordinator.state.rytm.candidate_state == "stale"
    assert coordinator.state.rytm.plan_state == "stale"
    assert coordinator.state.rytm.authority_state == "blocked"
    assert "prepare_again" in coordinator.state.rytm.recovery_actions
    assert coordinator.state.analog_four == a4_before

    coordinator.record_connection("analog_rytm_mk2", connected=True)

    assert coordinator.state.rytm.connection_state == "connected"
    assert coordinator.state.rytm.authority_state == "armed"
    assert coordinator.state.rytm.plan_state == "stale"
    assert "prepare_again" in coordinator.state.rytm.recovery_actions


def test_a4_prepare_remains_zero_authority_until_mapping_is_promoted() -> None:
    coordinator = DualMachineStageCoordinator()
    coordinator.record_capture("analog_four_mk2", succeeded=True, connected=True)
    coordinator.record_scope(
        "analog_four_mk2",
        target_ids=frozenset({1}),
        locked_ids=frozenset(),
        effective_ids=frozenset({1}),
    )
    coordinator.record_candidate(
        "analog_four_mk2",
        ready=False,
        blocked_reason="zero_semantic_events",
    )
    coordinator.record_plan("analog_four_mk2", ready=False)

    assert coordinator.state.analog_four.candidate_state == "blocked"
    assert coordinator.state.analog_four.plan_state == "blocked"
    assert coordinator.state.analog_four.authority_state == "blocked"
    assert (
        "a4_hardware_audition_validation_pending" in coordinator.state.analog_four.blocked_reasons
    )


def test_whole_state_revision_advances_for_every_lane_transition() -> None:
    coordinator = DualMachineStageCoordinator()
    assert coordinator.state.revision == 0

    coordinator.record_capture("analog_rytm_mk2", succeeded=True, connected=True)
    coordinator.record_capture("analog_four_mk2", succeeded=True, connected=True)
    coordinator.record_connection("analog_four_mk2", connected=False)

    assert coordinator.state.revision == 3


def test_every_revision_emits_one_categorical_transition(
    capture_stage_logs: pytest.LogCaptureFixture,
) -> None:
    coordinator = DualMachineStageCoordinator()

    coordinator.record_capture("analog_rytm_mk2", succeeded=True, connected=True)
    coordinator.record_capture("analog_rytm_mk2", succeeded=True, connected=True)

    records = [
        record
        for record in capture_stage_logs.records
        if getattr(record, "event", None) == "cockpit_stage_transition"
    ]
    assert len(records) == 2
    first, forced = records
    assert first.transition == "capture"
    assert first.device_id == "analog_rytm_mk2"
    assert first.revision == 1
    assert first.state_changed is True
    assert first.from_connection_state == "unknown"
    assert first.to_connection_state == "connected"
    assert first.from_capture_state == "not_captured"
    assert first.to_capture_state == "captured"
    assert first.from_candidate_state == first.to_candidate_state == "none"
    assert first.from_plan_state == first.to_plan_state == "none"
    assert first.from_authority_state == first.to_authority_state == "not_armed"
    assert first.from_target_count == first.to_target_count == 0
    assert first.from_locked_count == first.to_locked_count == 0
    assert first.from_effective_count == first.to_effective_count == 12
    assert forced.revision == 2
    assert forced.state_changed is False


def test_unchanged_scope_is_not_a_transition(
    capture_stage_logs: pytest.LogCaptureFixture,
) -> None:
    coordinator = DualMachineStageCoordinator()

    coordinator.record_scope(
        "analog_rytm_mk2",
        target_ids=frozenset(),
        locked_ids=frozenset(),
        effective_ids=frozenset(range(1, 13)),
    )

    assert coordinator.state.revision == 0
    assert capture_stage_logs.records == []


def test_capture_recovery_clears_only_transient_a4_failure() -> None:
    coordinator = DualMachineStageCoordinator(rytm_send_armed=True)
    coordinator.record_capture("analog_rytm_mk2", succeeded=True, connected=True)
    rytm_before = coordinator.state.rytm
    coordinator.record_capture(
        "analog_four_mk2",
        succeeded=False,
        connected=None,
        error="current-kit capture failed",
    )

    coordinator.record_capture("analog_four_mk2", succeeded=True, connected=True)

    assert coordinator.state.rytm == rytm_before
    assert coordinator.state.analog_four.capture_state == "captured"
    assert coordinator.state.analog_four.last_error is None
    assert coordinator.state.analog_four.plan_state == "blocked"
    assert coordinator.state.analog_four.authority_state == "blocked"
    assert coordinator.state.analog_four.blocked_reasons == (
        "a4_hardware_audition_validation_pending",
    )


def test_rytm_arm_and_send_failure_never_grant_a4_authority() -> None:
    coordinator = DualMachineStageCoordinator()
    a4_before = coordinator.state.analog_four

    coordinator.record_rytm_authority(armed=True)
    coordinator.record_send("analog_rytm_mk2", succeeded=False)
    coordinator.record_rytm_authority(armed=False)

    assert coordinator.state.analog_four == a4_before
    assert coordinator.state.rytm.authority_state == "not_armed"
    assert coordinator.state.analog_four.authority_state == "blocked"


def test_rytm_authority_stays_fail_closed_after_capture_failure() -> None:
    coordinator = DualMachineStageCoordinator()
    coordinator.record_capture(
        "analog_rytm_mk2",
        succeeded=False,
        connected=None,
        error="current-kit capture failed",
    )

    coordinator.record_rytm_authority(armed=True)

    assert coordinator.state.rytm.authority_state == "blocked"
    assert "capture_failed" in coordinator.state.rytm.blocked_reasons
    assert coordinator.state.analog_four.authority_state == "blocked"


def test_a4_connection_never_grants_output_authority() -> None:
    coordinator = DualMachineStageCoordinator()

    coordinator.record_connection("analog_four_mk2", connected=True)

    assert coordinator.state.analog_four.connection_state == "connected"
    assert coordinator.state.analog_four.authority_state == "blocked"


def test_rytm_arm_stays_blocked_while_device_is_disconnected() -> None:
    coordinator = DualMachineStageCoordinator()
    coordinator.record_connection("analog_rytm_mk2", connected=False)

    coordinator.record_rytm_authority(armed=True)

    assert coordinator.state.rytm.authority_state == "blocked"
    assert "device_disconnected" in coordinator.state.rytm.blocked_reasons


def test_a4_send_attempt_remains_mapping_blocked() -> None:
    coordinator = DualMachineStageCoordinator()

    coordinator.record_send("analog_four_mk2", succeeded=True)

    assert coordinator.state.analog_four.candidate_state == "blocked"
    assert coordinator.state.analog_four.plan_state == "blocked"
    assert coordinator.state.analog_four.authority_state == "blocked"
    assert coordinator.state.analog_four.recovery_actions == ("run_a4_mapping_gap_procedure",)
