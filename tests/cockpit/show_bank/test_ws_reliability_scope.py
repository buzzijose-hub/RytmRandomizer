"""Wire requests cannot overwrite authoritative locks or stale local revisions."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID
from rytm_randomizer.cockpit.data.parameter_scope import ParameterCell, ParameterSelection
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.session import CockpitSession

from .test_native_offline_journey import _disk, _favorite, _generate, _journey, _session

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


def _request(session: CockpitSession, command: dict[str, object]) -> dict[str, object]:
    result = asyncio.run(
        handlers.handle_command({"request_id": "reliability-scope", "command": command}, session)
    )
    session.clear_pending_events()
    return result


@pytest.mark.parametrize(
    "device,key",
    [(ANALOG_FOUR_DEVICE_ID, "filter2_resonance"), (ANALOG_RYTM_DEVICE_ID, "overdrive")],
)
def test_show_bank_generation_refuses_wire_unlock_of_authoritative_item(
    tmp_path: Path, device: str, key: str
) -> None:
    journey = _journey(tmp_path)
    favorite = _generate(journey, count=1)[0]
    _favorite(journey, favorite)
    workspace = journey.workspace
    session = _session(workspace, journey.bank_id, journey.entry_id, tmp_path)
    selected = _request(
        session,
        {
            "type": "show_bank_select_candidate",
            "bank_id": journey.bank_id,
            "entry_id": journey.entry_id,
            "candidate_id": favorite.candidate_id,
            "expected_revision": workspace.bank(journey.bank_id).revision,
        },
    )
    assert selected["ok"], selected
    session.rytm_parameters = ParameterSelection(())
    session.a4_parameters = ParameterSelection(())
    session.pad_locks = set(range(1, 13))
    session.a4_track_locks = set(range(1, 5))
    if device == ANALOG_FOUR_DEVICE_ID:
        session.a4_parameters = ParameterSelection((ParameterCell(2, key),))
    else:
        session.rytm_parameters = ParameterSelection((ParameterCell(2, key),))
    original = workspace.bank(journey.bank_id)
    before_disk = _disk(workspace.store.root)
    source = session.device.capture_snapshot()
    request: dict[str, object] = {
        "type": "show_bank_generate_candidates",
        "bank_id": journey.bank_id,
        "entry_id": journey.entry_id,
        "expected_revision": original.revision,
        "depth_preset": "large",
        "depth": 0.75,
        "seed": 2028,
        "profile_id": favorite.recipe.profile_id,
        "candidate_count": 1,
        "rytm_targets": [2],
        "rytm_locks": list(range(1, 13)),
        "a4_targets": [2],
        "a4_locks": list(range(1, 5)),
    }
    request["a4_locks" if device == ANALOG_FOUR_DEVICE_ID else "rytm_locks"] = []
    result = _request(session, request)
    assert result["ok"] is False, "an untrusted request silently replaced the operator's locks"
    assert workspace.bank(journey.bank_id) == original
    assert _disk(workspace.store.root) == before_disk
    assert session.device.capture_snapshot() == source
    assert session.pad_locks == set(range(1, 13))
    assert session.a4_track_locks == set(range(1, 5))
    assert session.armed_apply is None and not session.hardware_intent
    assert session.current_send_plan is None


def test_rapid_scope_commands_generate_only_final_server_selection(tmp_path: Path) -> None:
    journey = _journey(tmp_path)
    favorite = _generate(journey, count=1)[0]
    _favorite(journey, favorite)
    workspace = journey.workspace
    session = _session(workspace, journey.bank_id, journey.entry_id, tmp_path)
    assert _request(
        session,
        {
            "type": "show_bank_select_candidate",
            "bank_id": journey.bank_id,
            "entry_id": journey.entry_id,
            "candidate_id": favorite.candidate_id,
            "expected_revision": workspace.bank(journey.bank_id).revision,
        },
    )["ok"]
    original = workspace.bank(journey.bank_id)
    before = _disk(workspace.store.root)
    for index in range(30):
        key = "filter2_resonance" if index % 2 else "osc1_pwm_depth"
        result = _request(
            session,
            {
                "type": "set_mutation_parameters",
                "device_id": ANALOG_FOUR_DEVICE_ID,
                "parameter_cells": [{"item_id": 1, "parameter_key": key}],
            },
        )
        assert result["ok"], result
        assert session.current_send_plan is None
        assert session.armed_apply is None and not session.hardware_intent
    assert workspace.bank(journey.bank_id) == original
    assert _disk(workspace.store.root) == before
    generated = _request(
        session,
        {
            "type": "show_bank_generate_candidates",
            "bank_id": journey.bank_id,
            "entry_id": journey.entry_id,
            "expected_revision": original.revision,
            "depth_preset": "large",
            "depth": 0.75,
            "seed": 2050,
            "profile_id": favorite.recipe.profile_id,
            "candidate_count": 1,
            "rytm_targets": sorted(session.rytm_pad_targets),
            "rytm_locks": sorted(session.pad_locks),
            "a4_targets": sorted(session.a4_track_targets),
            "a4_locks": sorted(session.a4_track_locks),
        },
    )
    assert generated["ok"], generated
    candidate = workspace.bank(journey.bank_id).entry(journey.entry_id).candidates[-1]
    assert candidate.analog_four_candidate.values
    assert all(
        value.track_id == 1 and value.parameter == "filter2_resonance"
        for value in candidate.analog_four_candidate.values
    )
    assert candidate.recipe.analog_four_scope.parameters == session.a4_parameters
    assert (
        workspace.bank(journey.bank_id).entry(journey.entry_id).favorite
        == original.entry(journey.entry_id).favorite
    )
    assert session.current_send_plan is None and not session.hardware_intent
    assert session.current_candidate is None
    assert session.stage_coordinator.state.rytm.candidate_state == "none"


@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_generation_refuses_damaged_prior_favorite_before_any_publication(
    tmp_path: Path, damage: str
) -> None:
    journey = _journey(tmp_path)
    favorite = _generate(journey, count=1)[0]
    _favorite(journey, favorite)
    workspace = journey.workspace
    retained = favorite.analog_four_candidate.sysex.retained
    assert retained is not None
    frame = workspace.store.root / retained.artifact_name
    assert frame.is_relative_to(tmp_path) and frame.is_file()
    if damage == "missing":
        frame.unlink()
    else:
        frame.write_bytes(b"corrupt retained favorite")
    session = _session(workspace, journey.bank_id, journey.entry_id, tmp_path)
    session.active_profile = journey.profile
    original = workspace.bank(journey.bank_id)
    before = _disk(workspace.store.root)
    result = _request(
        session,
        {
            "type": "show_bank_generate_candidates",
            "bank_id": journey.bank_id,
            "entry_id": journey.entry_id,
            "expected_revision": original.revision,
            "depth_preset": "small",
            "depth": 0.25,
            "seed": 2099,
            "profile_id": journey.profile.profile_id,
            "candidate_count": 1,
            "rytm_targets": [],
            "rytm_locks": [],
            "a4_targets": [],
            "a4_locks": [],
        },
    )
    assert result["ok"] is False
    assert "Local artifact" in str(result["message"])
    assert workspace.bank(journey.bank_id) == original
    assert _disk(workspace.store.root) == before
    assert session.current_candidate is None and session.current_send_plan is None


def test_reconstructed_backend_refuses_old_revision_and_preparation_until_recall(
    tmp_path: Path,
) -> None:
    journey = _journey(tmp_path)
    favorite = _generate(journey, count=1)[0]
    original = _favorite(journey, favorite)
    restarted = ShowKitForgeWorkspace(ShowBankStore(journey.workspace.store.root))
    session = _session(restarted, journey.bank_id, journey.entry_id, tmp_path)
    before = _disk(restarted.store.root)
    stale = _request(
        session,
        {
            "type": "show_bank_mark_favorite",
            "bank_id": journey.bank_id,
            "entry_id": journey.entry_id,
            "candidate_id": favorite.candidate_id,
            "expected_revision": original.revision - 1,
        },
    )
    assert stale["ok"] is False
    assert _disk(restarted.store.root) == before
    prepared = _request(session, {"type": "prepare_send_plan"})
    assert prepared["ok"] is False
    assert session.current_send_plan is None
    recalled = _request(
        session,
        {
            "type": "show_bank_select_candidate",
            "bank_id": journey.bank_id,
            "entry_id": journey.entry_id,
            "candidate_id": favorite.candidate_id,
            "expected_revision": restarted.bank(journey.bank_id).revision,
        },
    )
    assert recalled["ok"], recalled
    assert session.current_candidate == favorite.rytm_candidate
    assert session.a4_parameters == favorite.recipe.analog_four_scope.parameters
    assert session.active_profile == favorite.recipe.profile
    assert session.current_send_plan is None
    assert (
        session.armed_apply is None and not session.hardware_intent and not session.device.is_armed
    )
