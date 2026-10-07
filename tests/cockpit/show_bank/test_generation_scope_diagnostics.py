"""Retained-frame commands cannot broaden the operator's generation scope."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.protocol import ERR_VALIDATION
from rytm_randomizer.cockpit.ws.session import CockpitSession

from .test_native_offline_journey import _disk, _favorite, _generate, _journey, _session

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


def _generation(root: Path) -> tuple[CockpitSession, dict[str, object]]:
    journey = _journey(root)
    (favorite,) = _generate(journey, count=1)
    _favorite(journey, favorite)
    workspace = journey.workspace
    session = _session(workspace, journey.bank_id, journey.entry_id, root)
    selected = asyncio.run(
        handle_command(
            {
                "request_id": "scope-selection",
                "command": {
                    "type": "show_bank_select_candidate",
                    "bank_id": journey.bank_id,
                    "entry_id": journey.entry_id,
                    "candidate_id": favorite.candidate_id,
                    "expected_revision": workspace.bank(journey.bank_id).revision,
                },
            },
            session,
        )
    )
    assert selected["ok"] is True
    session.clear_pending_events()
    return session, {
        "type": "show_bank_generate_candidates",
        "bank_id": journey.bank_id,
        "entry_id": journey.entry_id,
        "expected_revision": workspace.bank(journey.bank_id).revision,
        "profile_id": favorite.recipe.profile_id,
        "depth_preset": "small",
        "depth": 0.25,
        "seed": 2028,
        "candidate_count": 1,
        "rytm_targets": sorted(session.rytm_pad_targets),
        "rytm_locks": sorted(session.pad_locks),
        "a4_targets": sorted(session.a4_track_targets),
        "a4_locks": sorted(session.a4_track_locks),
    }


@pytest.mark.parametrize(
    "field,requested,reason",
    [
        ("rytm_locks", [], "omits current operator locks"),
        ("a4_locks", [], "omits current operator locks"),
        ("rytm_targets", [1, 2, 3], "expands current operator targets"),
        ("rytm_targets", [], "expands current operator targets"),
        ("a4_targets", [1, 2, 3], "expands current operator targets"),
        ("a4_targets", [], "expands current operator targets"),
    ],
)
def test_generation_refuses_wire_scope_expansion_before_a_revision_or_recall(
    tmp_path: Path,
    package_logs: pytest.LogCaptureFixture,
    field: str,
    requested: list[int],
    reason: str,
) -> None:
    session, command = _generation(tmp_path)
    session.rytm_pad_targets = {1, 2}
    session.a4_track_targets = {1, 2}
    command["rytm_targets"] = [1, 2]
    command["a4_targets"] = [1, 2]
    command[field] = requested
    workspace = session.show_kit_forge
    assert workspace is not None
    state = workspace.state_dict()
    files = _disk(workspace.store.root)
    source = session.device.capture_snapshot()
    candidate = session.current_candidate
    locks = (set(session.pad_locks), set(session.a4_track_locks))
    ack = asyncio.run(handle_command({"request_id": "scope-refusal", "command": command}, session))
    assert ack["ok"] is False and ack["code"] == ERR_VALIDATION
    assert reason in str(ack["message"])
    assert workspace.state_dict() == state
    assert _disk(workspace.store.root) == files
    assert session.device.capture_snapshot() == source
    assert session.current_candidate == candidate
    assert (session.pad_locks, session.a4_track_locks) == locks
    assert session.rytm_pad_targets == {1, 2} and session.a4_track_targets == {1, 2}
    assert session.pending_events == [] and session.current_send_plan is None
    assert session.armed_apply is None and not session.hardware_intent
    records = [
        record
        for record in package_logs.records
        if record.getMessage() == "show_bank_generation_scope_refused"
    ]
    assert len(records) == 1
    context = records[0].__dict__
    is_rytm = field.startswith("rytm_")
    prefix = "rytm" if is_rytm else "a4"
    available_count = 12 if is_rytm else 4
    assert context["device_id"] == (ANALOG_RYTM_DEVICE_ID if is_rytm else ANALOG_FOUR_DEVICE_ID)
    assert context["requested_target_count"] == len(
        command[f"{prefix}_targets"] or range(available_count)
    )
    assert context["current_target_count"] == 2
    assert context["requested_lock_count"] == len(command[f"{prefix}_locks"])
    assert context["current_lock_count"] == len(locks[0 if is_rytm else 1])
    assert context["outcome"] == "refused"
    assert context["reason"] in {"operator_locks_omitted", "operator_targets_expanded"}
    assert not {"target_ids", "locked_ids", "parameter_values", "path", "token"} & context.keys()


@pytest.mark.parametrize("narrow", [False, True])
def test_generation_accepts_matching_scope_and_safe_narrowing_with_added_locks(
    tmp_path: Path, narrow: bool
) -> None:
    session, command = _generation(tmp_path)
    if narrow:
        session.rytm_pad_targets = {1, 2}
        session.a4_track_targets = {1, 2}
        command["rytm_targets"] = [1]
        command["a4_targets"] = [1]
        command["a4_locks"] = sorted(session.a4_track_locks | {3})
    locks = (set(session.pad_locks), set(session.a4_track_locks))
    workspace = session.show_kit_forge
    assert workspace is not None
    bank = workspace.banks[0]
    ack = asyncio.run(handle_command({"request_id": "scope-success", "command": command}, session))
    assert ack["ok"] is True, ack
    assert workspace.bank(bank.bank_id).revision > bank.revision
    assert locks[0] <= session.pad_locks and locks[1] <= session.a4_track_locks
    assert session.current_candidate is None
    assert session.preview_on is False
    assert session.stage_coordinator.state.rytm.candidate_state == "none"
    assert session.current_send_plan is None and session.armed_apply is None
    if narrow:
        assert session.rytm_pad_targets == {1, 2} and session.a4_track_targets == {1, 2}
        assert session.a4_track_locks == locks[1]
        generated = workspace.bank(bank.bank_id).entries[0].candidates[-1]
        assert generated.recipe.rytm_scope.target_ids == (1,)
        assert generated.recipe.analog_four_scope.target_ids == (1,)
        assert set(generated.recipe.analog_four_scope.locked_ids) == locks[1] | {3}


def test_generation_refuses_unknown_profile_without_revision_or_activation(tmp_path: Path) -> None:
    session, command = _generation(tmp_path)
    workspace = session.show_kit_forge
    assert workspace is not None
    original = workspace.banks[0]
    command["profile_id"] = "missing-profile"
    session.active_profile = None
    ack = asyncio.run(
        handle_command({"request_id": "unknown-profile", "command": command}, session)
    )
    assert ack["ok"] is False
    assert workspace.bank(original.bank_id) == original
    assert session.current_send_plan is None
    assert session.armed_apply is None and not session.hardware_intent
