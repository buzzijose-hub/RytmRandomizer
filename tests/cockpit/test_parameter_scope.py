"""Scope is enforced before proposals and independently before SEND."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from conftest import analog_four_saved_kit_frame
from rytm_randomizer.cockpit.capture import ANALOG_FOUR_DEVICE_ID
from rytm_randomizer.cockpit.data import PadDelta, PadState, ProfileModel, Snapshot, StyleTrait
from rytm_randomizer.cockpit.data.parameter_scope import ParameterCell, ParameterSelection
from rytm_randomizer.cockpit.data.rytm_parameter_map import cockpit_parameter_mapping
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
from rytm_randomizer.data.analog_four_sysex_calibration import (
    A4_FILTER1_FREQUENCY_PARAMETER,
    analog_four_sysex_calibration_for,
)

from .conftest import capture_fixed_frame, make_default_snapshot

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
    second.history_store.initial(replace(scope_source, snapshot_id="different-startup-source"))
    ack = request(second, "recall_rehearsal_favorite", record_id=record_id)
    assert ack["ok"]
    assert second.current_candidate.to_dict() == retained
    assert second.device.capture_snapshot() == scope_source
    assert len(second.history_store.current.entries) == 2
    assert second.rytm_parameters == original_scope
    assert second.pad_locks == first.pad_locks
    assert second.a4_track_locks == {1, 2, 3, 4}
    assert second.depth == 0.1 and second.seed == 42
    assert second.armed_apply is None and not second.hardware_intent
    assert second.current_send_plan is None and second.recalled_offline_favorite
    assert not request(second, "send", send_plan_id=prepared["plan_id"])["ok"]
    assert request(second, "prepare_send_plan")["send_plan"]["ready"]


@pytest.mark.parametrize("key", ["amp_volume", "lfo_destination"])
def test_planner_refuses_changed_common_locked_default_controls(
    scope_source, scope_profile, key
) -> None:
    pad = scope_source.pads[1]
    mapping = cockpit_parameter_mapping(pad.machine, key)
    assert mapping is not None and mapping.machine_key is None
    assert mapping.mutation_status == "locked_default"
    original = {**pad.params, key: mapping.value_min}
    source = replace(
        scope_source,
        pads=tuple(
            replace(item, params=original) if item.pad_id == 2 else item
            for item in scope_source.pads
        ),
    )
    candidate = mutate(source, scope_profile, 0.1, 42, frozenset({2}))
    proposed = {**original, "flt": original["flt"] - 1, key: mapping.value_min + 1}
    candidate = replace(
        candidate,
        pad_deltas=(PadDelta(2, proposed, frozenset({"flt", key})),),
        estimated_midi_msgs=2,
    )
    plan = prepare_send_plan(source, scope_profile, candidate, frozenset(), frozenset({2}))
    assert plan is not None and not plan.ready
    assert "candidate_high_risk" in plan.blocked_reasons
    assert [(packet.parameter, packet.control) for packet in plan.packets] == [("flt", 74)]


@pytest.mark.parametrize("key", ["lfo_depth", "native_unknown"])
def test_all_scope_refuses_hidden_actual_changes_despite_safe_changed_keys(
    scope_source, scope_profile, key
) -> None:
    pad = scope_source.pads[1]
    original = {**pad.params, key: 64}
    source = replace(
        scope_source,
        pads=tuple(
            replace(item, params=original) if item.pad_id == 2 else item
            for item in scope_source.pads
        ),
    )
    candidate = mutate(source, scope_profile, 0.1, 42, frozenset({2}))
    forged = replace(
        candidate,
        pad_deltas=(PadDelta(2, {**original, "flt": 99, key: 63}, frozenset({"flt"})),),
        estimated_midi_msgs=1,
    )
    all_parameters = ParameterSelection()
    assert all_parameters.cells is None
    plan = prepare_send_plan(
        source,
        scope_profile,
        forged,
        frozenset(),
        frozenset({2}),
        parameter_selection=all_parameters,
    )
    assert plan is not None and not plan.ready
    assert "parameter_scope_mismatch" in plan.blocked_reasons
    assert [packet.parameter for packet in plan.packets] == ["flt"]


@pytest.mark.parametrize("forgery", ["foreign_pad", "missing_key"])
def test_exact_parameter_scope_refuses_foreign_pads_and_missing_source_keys(
    scope_source, scope_profile, forgery
) -> None:
    selection = pad2_rehearsal_selection(scope_source)
    candidate = mutate(
        scope_source,
        scope_profile,
        0.1,
        42,
        frozenset({2}),
        parameter_depths=rytm_parameter_depths(scope_source, selection, 0.1),
    )
    delta = candidate.pad_deltas[0]
    if forgery == "foreign_pad":
        delta = replace(delta, pad_id=12)
    else:
        proposed = dict(delta.proposed_params)
        proposed.pop("lev")
        delta = replace(delta, proposed_params=proposed)
    forged = replace(candidate, pad_deltas=(delta,))
    plan = prepare_send_plan(
        scope_source, scope_profile, forged, frozenset(), parameter_selection=selection
    )
    assert plan is not None and not plan.ready
    assert "parameter_scope_mismatch" in plan.blocked_reasons


@pytest.mark.parametrize("bad", [True, float("nan"), float("inf"), -0.1, 1.01])
def test_engine_rejects_invalid_per_cell_depth_before_proposals(
    scope_source, scope_profile, bad
) -> None:
    with pytest.raises(ValueError, match="parameter depths"):
        mutate(scope_source, scope_profile, 0.1, 42, parameter_depths={(2, "flt"): bad})


@pytest.mark.parametrize(
    "kwargs",
    [
        {"parameter_depths": {(13, "flt"): 0.1}},
        {"parameter_bounds": {(13, "flt"): (0, 127)}},
        {"parameter_bounds": {(2, "flt"): (True, 127)}},
        {"parameter_bounds": {(2, "flt"): (0, 127.0)}},
        {"parameter_bounds": {(2, "flt"): (128, 127)}},
    ],
)
def test_engine_rejects_foreign_cells_and_invalid_native_bounds(
    scope_source, scope_profile, kwargs
) -> None:
    with pytest.raises(ValueError):
        mutate(scope_source, scope_profile, 0.1, 42, **kwargs)


def test_engine_explicit_native_bounds_use_exact_integer_domain(
    scope_source, scope_profile
) -> None:
    native = 16257
    source = replace(
        scope_source, pads=(replace(scope_source.pads[1], params={"native_unknown": native}),)
    )
    candidate = mutate(
        source,
        scope_profile,
        0.1,
        42,
        parameter_depths={(2, "native_unknown"): 0.1},
        parameter_bounds={(2, "native_unknown"): (0, 32512)},
    )
    value = candidate.pad_deltas[0].proposed_params["native_unknown"]
    assert type(value) is int and 0 <= value <= 32512 and value > 127
    identity = mutate(
        source,
        scope_profile,
        0.1,
        42,
        parameter_depths={},
        parameter_bounds={(2, "native_unknown"): (0, 127)},
    )
    assert identity.pad_deltas[0].proposed_params["native_unknown"] == native
    assert identity.estimated_midi_msgs == 0
    fixed = mutate(scope_source, scope_profile, 0.1, 42, parameter_bounds={(2, "flt"): (65, 65)})
    assert fixed.pad_deltas[1].proposed_params["flt"] == 65


@pytest.mark.parametrize("bad", [True, -1, 128])
def test_scope_metadata_refuses_source_values_outside_verified_domain(scope_source, bad) -> None:
    source = replace(scope_source, pads=(replace(scope_source.pads[1], params={"flt": bad}),))
    row = next(
        item
        for item in performance_parameter_controls(source)
        if item["device_id"] == source.device and item["parameter_key"] == "flt"
    )
    assert not row["mutation_supported"] and not row["send_supported"]
    assert "source_value_outside_verified_domain" in row["reasons"]
    with pytest.raises(ValueError, match="protected_or_unavailable"):
        rytm_parameter_depths(source, ParameterSelection((ParameterCell(2, "flt"),)), 0.1)
    assert rytm_parameter_depths(source, ParameterSelection(), 0.1) == {}


def test_metadata_discloses_unmapped_precision_and_incompatible_machine(scope_source) -> None:
    source = replace(
        scope_source,
        pads=(
            replace(scope_source.pads[1], params={"native_unknown": 16257}),
            PadState(9, "BD Hard", {"dec": 32}),
        ),
    )
    controls = performance_parameter_controls(source)
    unknown = next(row for row in controls if row["parameter_key"] == "native_unknown")
    assert unknown["value"] == 16257
    assert unknown["native_precision"] == "retained source integer; encoding unavailable"
    assert not unknown["mutation_supported"] and unknown["protected"]
    incompatible = next(
        row for row in controls if row["item_id"] == 9 and row["parameter_key"] == "dec"
    )
    assert "machine_pad_incompatible" in incompatible["reasons"]
    assert not incompatible["mutation_supported"]


@pytest.mark.parametrize("raw", [16257, 65535])
def test_a4_metadata_decodes_native_width_and_fraction_without_granting_output(
    scope_source, raw
) -> None:
    calibration = analog_four_sysex_calibration_for(A4_FILTER1_FREQUENCY_PARAMETER)
    overrides: dict[int, int] = {}
    for track in range(1, 5):
        offset = calibration.native_offset_for_track(track)
        overrides.update(
            {
                offset + index: value
                for index, value in enumerate(raw.to_bytes(calibration.native_width, "big"))
            }
        )
    capture = capture_fixed_frame(
        ANALOG_FOUR_DEVICE_ID, analog_four_saved_kit_frame(unpacked_overrides=overrides)
    )
    rows = [
        row
        for row in performance_parameter_controls(scope_source, capture)
        if row["device_id"] == ANALOG_FOUR_DEVICE_ID
        and row["parameter_key"] == A4_FILTER1_FREQUENCY_PARAMETER
    ]
    assert len(rows) == 4
    assert all(
        row["value"] == raw
        and row["native_precision"] == "unsigned Q8.8"
        and not row["send_supported"]
        for row in rows
    )
    if raw <= calibration.native_raw_max:
        assert all(
            row["mutation_supported"]
            and row["display_value"] == calibration.format_native_screen_value(raw)
            for row in rows
        )
    else:
        assert all(
            not row["mutation_supported"]
            and "source_value_outside_verified_domain" in row["reasons"]
            for row in rows
        )
    missing = [
        row
        for row in performance_parameter_controls(scope_source)
        if row["device_id"] == ANALOG_FOUR_DEVICE_ID
        and row["parameter_key"] == A4_FILTER1_FREQUENCY_PARAMETER
    ]
    assert all(
        row["value"] is None and "source_value_unavailable" in row["reasons"] for row in missing
    )


@pytest.mark.parametrize(
    "cells",
    [
        [ParameterCell(1, "flt")],
        ("flt",),
        tuple(ParameterCell(index + 1, "flt") for index in range(2049)),
    ],
)
def test_scope_dto_rejects_mutable_untyped_or_unbounded_cells(cells) -> None:
    with pytest.raises((TypeError, ValueError)):
        ParameterSelection(cast(tuple[ParameterCell, ...], cells))


@pytest.mark.parametrize(
    "item,key", [(0, "flt"), (1, ""), (1, " "), (1, "x" * 129), (True, "flt"), (1, None)]
)
def test_scope_cell_requires_strict_positive_owner_and_bounded_key(item, key) -> None:
    with pytest.raises((TypeError, ValueError)):
        ParameterCell(item, key)


def test_scope_parse_refuses_over_limit_array() -> None:
    with pytest.raises(ValueError, match="bounded array"):
        ParameterSelection.parse([{"item_id": 2, "parameter_key": "flt"}] * 2049)


def test_scope_missing_source_or_mapping_fails_without_guessing(scope_source, monkeypatch) -> None:
    with pytest.raises(ValueError, match="pad2_source_unavailable"):
        pad2_rehearsal_selection(replace(scope_source, pads=scope_source.pads[:1]))
    from rytm_randomizer.cockpit.capture import parameter_scope as metadata

    monkeypatch.setattr(metadata, "cockpit_parameter_key", lambda *_args: None)
    with pytest.raises(ValueError, match="mapping_unavailable"):
        pad2_rehearsal_selection(scope_source)


def test_scope_unknown_engine_cell_is_refused(scope_source) -> None:
    with pytest.raises(ValueError, match="unknown_control"):
        rytm_parameter_depths(scope_source, ParameterSelection((ParameterCell(2, "absent"),)), 0.1)


def test_scope_truthfully_declared_unselected_change_is_refused(
    scope_source, scope_profile
) -> None:
    selection = pad2_rehearsal_selection(scope_source)
    candidate = mutate(
        scope_source,
        scope_profile,
        0.1,
        42,
        frozenset({2}),
        parameter_depths=rytm_parameter_depths(scope_source, selection, 0.1),
    )
    delta = candidate.pad_deltas[0]
    forged = replace(
        candidate,
        pad_deltas=(
            replace(
                delta,
                proposed_params={
                    **delta.proposed_params,
                    "dec": scope_source.pads[1].params["dec"] + 1,
                },
                changed_keys=delta.changed_keys | {"dec"},
            ),
        ),
    )
    plan = prepare_send_plan(
        scope_source, scope_profile, forged, frozenset(), parameter_selection=selection
    )
    assert plan is not None and not plan.ready
    assert "parameter_scope_mismatch" in plan.blocked_reasons


def test_favorite_persistence_failure_logs_no_private_path(
    scope_source, scope_profile, tmp_path, monkeypatch, ws_handler_caplog
) -> None:
    import logging

    ws_handler_caplog.set_level(logging.INFO, logger="rytm_randomizer.cockpit.ws.handlers")
    store = LibraryStore(tmp_path / "library")
    session = CockpitSession(
        ProfileRegistry(tmp_path / "profiles"),
        HistoryStore(),
        MockDeviceAdapter(scope_source),
        library_store=store,
    )
    session.active_profile = scope_profile

    def request(kind, **body):
        return asyncio.run(
            handle_command({"request_id": kind, "command": {"type": kind, **body}}, session)
        )

    assert request("set_rehearsal_preset", preset_id="rytm_pad2_common")["ok"]
    sentinel = "PRIVATE-FAVORITE-PATH-DO-NOT-LOG"

    def fail(*_args, **_kwargs):
        raise OSError(f"C:/private/{sentinel}/favorite.json")

    monkeypatch.setattr(store, "retain_rehearsal", fail)
    original = session.current_candidate
    ack = request("retain_rehearsal_favorite", name="failure proof")
    assert not ack["ok"]
    assert sentinel not in str(ack)
    assert session.current_candidate is original
    assert not (tmp_path / "library").exists()
    serialized = repr([record.__dict__ for record in ws_handler_caplog.records])
    assert sentinel not in serialized
    assert "favorite_persistence_failed" in serialized
    assert sentinel not in repr(session.error_journal)


def test_scope_failure_paths_preserve_or_revoke_only_the_intended_context(
    scope_source, scope_profile, tmp_path
):
    store = LibraryStore(tmp_path / "library")
    session = CockpitSession(
        ProfileRegistry(tmp_path / "profiles"),
        HistoryStore(),
        MockDeviceAdapter(scope_source),
        library_store=store,
    )

    def request(kind, **body):
        return asyncio.run(
            handle_command({"request_id": kind, "command": {"type": kind, **body}}, session)
        )

    assert not request("retain_rehearsal_favorite", name="no candidate")["ok"]
    assert not request("recall_rehearsal_favorite", record_id="missing")["ok"]
    assert not request("set_depth", depth=1.0)["ok"]
    assert not request("set_rehearsal_preset", preset_id="unknown")["ok"]
    assert not request(
        "set_mutation_parameters",
        device_id="analog_rytm_mk2",
        parameter_cells=[{"item_id": 2, "parameter_key": "lev"}],
    )["ok"]
    assert session.rytm_parameters.cells is None
    session.active_profile = scope_profile
    assert request("set_rehearsal_preset", preset_id="rytm_pad2_common")["ok"]
    assert request("set_mutation_parameters", device_id="analog_four_mk2", parameter_cells=[])["ok"]
    assert session.a4_parameters.cells == ()
    session.rytm_parameters = ParameterSelection((ParameterCell(2, "old-machine-key"),))
    assert request("set_depth", depth=0.1)["ok"]
    assert session.rytm_parameters.cells == ()
    assert session.current_candidate.estimated_midi_msgs == 0
    saved = request("retain_rehearsal_favorite", name="empty exact rehearsal")
    assert saved["ok"]
    cold = CockpitSession(
        ProfileRegistry(tmp_path / "cold-profiles"),
        HistoryStore(),
        MockDeviceAdapter(scope_source),
        library_store=LibraryStore(tmp_path / "library"),
    )
    ack = asyncio.run(
        handle_command(
            {
                "request_id": "cold",
                "command": {
                    "type": "recall_rehearsal_favorite",
                    "record_id": saved["library_record"]["record_id"],
                },
            },
            cold,
        )
    )
    assert ack["ok"] and len(cold.history_store.current.entries) == 1
    assert cold.current_send_plan is None and cold.recalled_offline_favorite
