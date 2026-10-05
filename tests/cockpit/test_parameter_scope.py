"""Scope is enforced before proposals and independently before SEND."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data import PadDelta, PadState, ProfileModel, Snapshot, StyleTrait
from rytm_randomizer.cockpit.data.parameter_scope import ParameterCell, ParameterSelection
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.engine import mutate, prepare_send_plan
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.library import LibraryStore
from rytm_randomizer.cockpit.parameter_scope import (
    pad2_rehearsal_selection,
    performance_parameter_controls,
    rytm_parameter_depths,
    validate_parameter_selection,
)
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.session import CockpitSession

from .conftest import make_default_snapshot

pytestmark = pytest.mark.fast


@pytest.fixture
def scope_source() -> Snapshot:
    source = make_default_snapshot()
    pads = list(source.pads)
    pads[1] = replace(
        pads[1],
        params={
            **pads[1].params,
            "amp_decay": 60,
            "overdrive": 30,
            "reverb": 40,
            "lfo_depth": 64,
            "lev": 100,
        },
    )
    return replace(source, pads=tuple(pads))


@pytest.fixture
def scope_profile() -> ProfileModel:
    return ProfileModel(
        profile_id="scope-profile",
        name="Scope rehearsal",
        kind="user",
        model_version="1.0.0",
        traits=(StyleTrait("drive", 0.5),),
        pad_mappings=(),
        transition_curve="linear",
        source_summary="software fixture",
    )


def test_scope_preserves_every_excluded_native_value(scope_source, scope_profile) -> None:
    pads = list(scope_source.pads)
    pads[1] = replace(pads[1], params={**pads[1].params, "native_unknown": 16257})
    source = replace(scope_source, pads=tuple(pads))
    selection = pad2_rehearsal_selection(source)
    depths = rytm_parameter_depths(source, selection, 0.10)
    candidate = mutate(source, scope_profile, 0.10, 42, frozenset({2}), parameter_depths=depths)
    delta = candidate.pad_deltas[0]
    assert candidate.estimated_midi_msgs > 0
    assert delta.changed_keys <= {"flt", "amp_decay", "overdrive", "reverb"}
    for key, value in source.pads[1].params.items():
        if not selection.includes(2, key):
            assert delta.proposed_params[key] == value
    assert delta.proposed_params["native_unknown"] == 16257
    plan = prepare_send_plan(
        source, scope_profile, candidate, frozenset(), frozenset({2}), parameter_selection=selection
    )
    assert plan.ready
    assert {packet.control for packet in plan.packets} <= {74, 80, 81, 83}


@pytest.mark.parametrize("empty", [False, True])
def test_scope_zero_depth_or_no_cells_is_exact_identity(scope_source, scope_profile, empty) -> None:
    depth = 0.1 if empty else 0.0
    selection = ParameterSelection(()) if empty else pad2_rehearsal_selection(scope_source)
    candidate = mutate(
        scope_source,
        scope_profile,
        depth,
        42,
        parameter_depths=rytm_parameter_depths(scope_source, selection, depth),
    )
    assert candidate.estimated_midi_msgs == 0
    assert all(not delta.changed_keys for delta in candidate.pad_deltas)
    assert all(
        dict(delta.proposed_params) == dict(scope_source.pads[delta.pad_id - 1].params)
        for delta in candidate.pad_deltas
    )


def test_scope_locks_win_without_changing_rng_draws(scope_source, scope_profile) -> None:
    selection = pad2_rehearsal_selection(scope_source)
    depths = rytm_parameter_depths(scope_source, selection, 0.10)
    candidate = mutate(
        scope_source,
        scope_profile,
        0.10,
        42,
        frozenset({2}),
        frozenset({2}),
        parameter_depths=depths,
    )
    assert candidate.pad_deltas == ()


def test_scope_forged_unselected_change_is_whole_plan_refused(scope_source, scope_profile) -> None:
    selection = pad2_rehearsal_selection(scope_source)
    candidate = mutate(
        scope_source,
        scope_profile,
        0.10,
        42,
        frozenset({2}),
        parameter_depths=rytm_parameter_depths(scope_source, selection, 0.10),
    )
    delta = candidate.pad_deltas[0]
    forged = replace(
        candidate,
        pad_deltas=(replace(delta, proposed_params={**delta.proposed_params, "dec": 61}),),
    )
    plan = prepare_send_plan(
        scope_source, scope_profile, forged, frozenset(), parameter_selection=selection
    )
    assert not plan.ready
    assert "parameter_scope_mismatch" in plan.blocked_reasons
    assert plan.packets  # No trimming a mixed plan into false readiness.


@pytest.mark.parametrize("key", ["lfo_depth", "native_unknown"])
def test_scope_paired_or_unknown_change_refuses_whole_plan(
    scope_source, scope_profile, key
) -> None:
    params = {**scope_source.pads[1].params, key: 63}
    candidate = mutate(scope_source, scope_profile, 0.1, 42, frozenset({2}))
    candidate = replace(candidate, pad_deltas=(PadDelta(2, params, frozenset({key, "flt"})),))
    plan = prepare_send_plan(scope_source, scope_profile, candidate, frozenset())
    assert not plan.ready
    expected = (
        "paired_control_precision_unverified"
        if key == "lfo_depth"
        else "unsupported_control_changed"
    )
    assert expected in plan.blocked_reasons


@pytest.mark.parametrize(
    "raw",
    [
        True,
        {},
        ["flt"],
        [{"item_id": True, "parameter_key": "flt"}],
        [{"item_id": 2, "parameter_key": "flt", "cc": 74}],
        [{"item_id": 2, "parameter_key": "flt"}] * 2,
    ],
)
def test_scope_malformed_input_is_not_a_selection(raw) -> None:
    with pytest.raises((TypeError, ValueError)):
        ParameterSelection.parse(raw)


@pytest.mark.parametrize(
    "cell",
    [
        ParameterCell(2, "lev"),
        ParameterCell(2, "absent"),
        ParameterCell(13, "flt"),
        ParameterCell(1, "Filter1 Frequency"),
    ],
)
def test_scope_server_rejects_protected_unknown_or_wrong_owner(scope_source, cell) -> None:
    with pytest.raises(ValueError):
        validate_parameter_selection(
            ParameterSelection((cell,)),
            performance_parameter_controls(scope_source),
            "analog_rytm_mk2",
        )


def test_scope_change_invalidates_old_confirmation(
    scope_source, scope_profile, tmp_path: Path
) -> None:
    session = CockpitSession(
        ProfileRegistry(tmp_path), HistoryStore(), MockDeviceAdapter(scope_source)
    )
    session.active_profile = scope_profile
    session.seed = 42

    def request(kind: str, **body: object):
        return asyncio.run(
            handle_command({"request_id": kind, "command": {"type": kind, **body}}, session)
        )

    assert request("set_rehearsal_preset", preset_id="rytm_pad2_common")["ok"]
    assert session.a4_track_locks == {1, 2, 3, 4}
    assert session.pad_locks == set(range(1, 13)) - {2}
    prepared = request("prepare_send_plan")["send_plan"]
    assert prepared["ready"]
    assert request("set_mutation_parameters", device_id="analog_rytm_mk2", parameter_cells=[])["ok"]
    assert session.current_send_plan is None
    assert not request("send", send_plan_id=prepared["plan_id"])["ok"]
    assert session.current_candidate.estimated_midi_msgs == 0


def test_local_favorite_reopens_exact_values_and_scope_after_restart(
    scope_source, scope_profile, tmp_path: Path
) -> None:
    def session():
        state = CockpitSession(
            ProfileRegistry(tmp_path / "profiles"),
            HistoryStore(),
            MockDeviceAdapter(scope_source),
            library_store=LibraryStore(tmp_path / "library"),
        )
        state.active_profile = scope_profile
        state.seed = 42
        return state

    def request(state, kind, **body):
        return asyncio.run(
            handle_command({"request_id": kind, "command": {"type": kind, **body}}, state)
        )

    first = session()
    assert request(first, "set_rehearsal_preset", preset_id="rytm_pad2_common")["ok"]
    retained = first.current_candidate.to_dict()
    original_scope = first.rytm_parameters
    saved = request(first, "retain_rehearsal_favorite", name="Pad 2 rehearsal")
    assert saved["ok"]
    record_id = saved["library_record"]["record_id"]
    prepared = request(first, "prepare_send_plan")["send_plan"]
    second = session()
    ack = request(second, "recall_rehearsal_favorite", record_id=record_id)
    assert ack["ok"]
    assert second.current_candidate.to_dict() == retained
    assert second.device.capture_snapshot() == scope_source
    assert second.rytm_parameters == original_scope
    assert second.pad_locks == first.pad_locks
    assert second.a4_track_locks == {1, 2, 3, 4}
    assert second.depth == 0.1 and second.seed == 42
    assert second.armed_apply is None and not second.hardware_intent
    assert second.current_send_plan is None and second.recalled_offline_favorite
    assert not request(second, "send", send_plan_id=prepared["plan_id"])["ok"]
    assert request(second, "prepare_send_plan")["send_plan"]["ready"]
