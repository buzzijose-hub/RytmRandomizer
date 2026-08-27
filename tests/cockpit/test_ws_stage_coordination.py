"""Focused WebSocket integration tests for dual-machine stage coordination."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data import PadState, Snapshot
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.protocol import INITIAL_EVENT_COUNT
from rytm_randomizer.cockpit.ws.session import CockpitSession

pytestmark = pytest.mark.fast


@dataclass
class _Recorder:
    events: list[dict[str, object]] = field(default_factory=list)

    async def send_event(self, event: dict[str, object]) -> None:
        self.events.append(event)


class _FailedCaptureService:
    def capture(self, _device_id: str, _input_port: str) -> None:
        raise ValueError("private device detail must not cross the wire")


def _snapshot() -> Snapshot:
    return Snapshot(
        snapshot_id="stage-root",
        device="analog_rytm_mk2",
        captured_at=datetime(2026, 8, 27, tzinfo=timezone.utc),
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": 32, "dec": 80}),
            PadState(pad_id=2, machine="SD Classic", params={"tun": 40, "dec": 60}),
        ),
        scene_slot="A01",
        bpm=128.0,
    )


def _session(tmp_path: Path) -> CockpitSession:
    snapshot = _snapshot()
    history = HistoryStore()
    history.initial(snapshot)
    return CockpitSession(
        profile_registry=ProfileRegistry(tmp_path),
        history_store=history,
        device=MockDeviceAdapter(snapshot),
        seed=1234,
    )


def _dispatch(
    session: CockpitSession,
    command: dict[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    ack = asyncio.run(
        handlers.handle_command(
            {"request_id": "stage-test", "command": command},
            session,
        )
    )
    events = list(session.pending_events)
    session.pending_events.clear()
    return ack, events


def test_bootstrap_emits_exact_whole_stage_and_lock_wrappers(tmp_path: Path) -> None:
    session = _session(tmp_path)
    recorder = _Recorder()

    asyncio.run(handlers.emit_initial_events(recorder, session))

    assert len(recorder.events) == INITIAL_EVENT_COUNT == 11
    locks = next(event for event in recorder.events if event["type"] == "mutation_locks_changed")
    stage_event = next(
        event for event in recorder.events if event["type"] == "dual_machine_stage_changed"
    )
    assert locks == {
        "type": "mutation_locks_changed",
        "rytm_pad_locks": [],
        "a4_track_locks": [],
    }
    assert set(stage_event) == {"type", "stage"}
    stage = stage_event["stage"]
    assert isinstance(stage, dict)
    assert stage["rytm"]["effective_ids"] == [1, 2]
    assert stage["analog_four"]["effective_ids"] == [1, 2, 3, 4]
    assert stage["analog_four"]["plan_state"] == "blocked"
    assert stage["analog_four"]["authority_state"] == "blocked"
    assert stage["oxi_owns_sequencing"] is True
    assert stage["direct_oxi_control"] is False


def test_rytm_lock_invalidates_plan_and_recomputes_fresh_candidate(tmp_path: Path) -> None:
    session = _session(tmp_path)
    assert (
        _dispatch(
            session,
            {"type": "select_profile", "profile_id": "scene-industrial"},
        )[
            0
        ]["ok"]
        is True
    )
    prepare_ack, _ = _dispatch(session, {"type": "prepare_send_plan"})
    assert prepare_ack["ok"] is True
    assert session.current_candidate is not None
    old_candidate_id = session.current_candidate.candidate_id
    assert session.current_send_plan is not None

    ack, events = _dispatch(
        session,
        {"type": "set_pad_lock", "pad_id": 2, "locked": True},
    )

    assert ack["ok"] is True
    assert session.current_send_plan is None
    assert session.current_candidate is not None
    assert session.current_candidate.candidate_id != old_candidate_id
    assert [event["type"] for event in events] == [
        "send_plan_changed",
        "mutation_locks_changed",
        "dual_machine_stage_changed",
    ]
    assert events[1] == {
        "type": "mutation_locks_changed",
        "rytm_pad_locks": [2],
        "a4_track_locks": [],
    }
    stage = events[-1]["stage"]
    assert isinstance(stage, dict)
    assert stage["rytm"]["effective_ids"] == [1]
    assert stage["rytm"]["candidate_state"] == "ready"
    assert stage["rytm"]["plan_state"] == "none"


def test_a4_scope_and_analysis_remain_blocked_without_touching_rytm(tmp_path: Path) -> None:
    session = _session(tmp_path)
    rytm_before = session.stage_coordinator.state.rytm

    assert (
        _dispatch(
            session,
            {
                "type": "set_mutation_targets",
                "device_id": "analog_four_mk2",
                "target_ids": [1, 2],
            },
        )[0]["ok"]
        is True
    )
    assert (
        _dispatch(
            session,
            {"type": "set_a4_track_lock", "track": 2, "locked": True},
        )[
            0
        ]["ok"]
        is True
    )
    ack, events = _dispatch(
        session,
        {"type": "analyze_patch_genome", "description": "tight pressure", "track": 1},
    )

    assert ack["ok"] is True
    stage = events[-1]["stage"]
    assert isinstance(stage, dict)
    assert stage["analog_four"]["target_ids"] == [1, 2]
    assert stage["analog_four"]["locked_ids"] == [2]
    assert stage["analog_four"]["effective_ids"] == [1]
    assert stage["analog_four"]["candidate_state"] == "blocked"
    assert stage["analog_four"]["plan_state"] == "blocked"
    assert stage["analog_four"]["authority_state"] == "blocked"
    assert session.stage_coordinator.state.rytm == rytm_before


def test_capture_failure_blocks_only_requested_machine_and_is_wire_safe(tmp_path: Path) -> None:
    session = _session(tmp_path)
    session.kit_capture_service = _FailedCaptureService()  # type: ignore[assignment]
    rytm_before = session.stage_coordinator.state.rytm

    ack, events = _dispatch(
        session,
        {
            "type": "capture_current_kit",
            "device_id": "analog_four_mk2",
            "input_port": "A4 input",
        },
    )

    assert ack == {
        "request_id": "stage-test",
        "ok": False,
        "code": "validation_error",
        "message": "current-kit capture failed",
    }
    assert [event["type"] for event in events] == ["dual_machine_stage_changed"]
    assert session.stage_coordinator.state.rytm == rytm_before
    assert session.stage_coordinator.state.analog_four.capture_state == "failed"
    assert session.stage_coordinator.state.analog_four.authority_state == "blocked"
    assert session.stage_coordinator.state.analog_four.last_error == "current-kit capture failed"
