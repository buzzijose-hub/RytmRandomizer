"""Touch actions exercise real shared services with no hardware authority."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import cast

import pytest

from rytm_randomizer.cockpit.appliance import (
    DEVICE_IDS,
    HISTORY_LIMIT,
    ApplianceWorkspace,
    context_digest,
)
from rytm_randomizer.cockpit.data import PadState, Snapshot
from rytm_randomizer.cockpit.engine import mutate
from rytm_randomizer.cockpit.profiles import ProfileRegistry

pytestmark = pytest.mark.fast


@pytest.fixture
def workspace(tmp_path: Path) -> ApplianceWorkspace:
    value = ApplianceWorkspace(simulation=True, profile_file=tmp_path / "profiles.json")
    snapshot = Snapshot(
        "source",
        "analog_rytm_mk2",
        datetime.now(timezone.utc),
        tuple(
            PadState(i, "BD Hard", {"dec": 64, "tun": 64, "flt": 64, "amp_decay": 75})
            for i in range(1, 13)
        ),
        None,
        None,
    )
    value.sync(snapshot, context="initial")
    return value


def test_empty_appliance_targets_mean_none_without_changing_legacy_scope(
    workspace: ApplianceWorkspace,
) -> None:
    workspace.change_scope({"lanes": {DEVICE_IDS[0]: {"target_ids": []}}})
    assert workspace.scopes[DEVICE_IDS[0]].effective_ids(DEVICE_IDS[0]) == frozenset()


@pytest.mark.parametrize(
    "patch",
    [
        {"master_depth": True},
        {"master_depth": float("nan")},
        {"master_depth": float("inf")},
        {"master_depth": -0.1},
        {"master_depth": 1.1},
        {"target": "invalid"},
        {"lanes": {"wrong": {}}},
        {"lanes": {DEVICE_IDS[0]: {"target_ids": [True]}}},
        {"lanes": {DEVICE_IDS[1]: {"target_ids": [5]}}},
        {"lanes": {DEVICE_IDS[0]: {"target_ids": [1, 1]}}},
        {"lanes": {DEVICE_IDS[0]: {"page_ids": ["not-a-page"]}}},
        {"lanes": {DEVICE_IDS[0]: {"parameter_locks": ["unknown"]}}},
        {"lanes": {DEVICE_IDS[0]: {"track_depths": {"13": 0.5}}}},
        {"lanes": {DEVICE_IDS[0]: {"page_depths": {"unknown": 0.5}}}},
    ],
)
def test_invalid_scope_is_rejected_atomically(
    workspace: ApplianceWorkspace, patch: dict[str, object]
) -> None:
    before = (workspace.revision, workspace.master_depth, dict(workspace.scopes))
    with pytest.raises(ValueError):
        workspace.change_scope(patch)
    assert (workspace.revision, workspace.master_depth, workspace.scopes) == before


def test_zero_depth_and_all_locked_do_not_stage_roll(
    workspace: ApplianceWorkspace, tmp_path: Path
) -> None:
    profile = ProfileRegistry(tmp_path / "registry").list_profiles()[0]
    workspace.change_scope({"master_depth": 0})
    before = workspace.revision
    workspace.roll(profile, 1234)
    assert workspace.candidate is None and workspace.revision == before
    workspace.change_scope(
        {"master_depth": 0.5, "lanes": {DEVICE_IDS[0]: {"locked_ids": list(range(1, 13))}}}
    )
    before = workspace.revision
    workspace.roll(profile, 1234)
    assert workspace.candidate is None and workspace.revision == before


def test_scoped_roll_respects_locks_targets_and_zero_page_depth(
    workspace: ApplianceWorkspace, tmp_path: Path
) -> None:
    profile = ProfileRegistry(tmp_path / "registry").list_profiles()[0]
    workspace.change_scope(
        {
            "lanes": {
                DEVICE_IDS[0]: {"target_ids": [1, 2], "locked_ids": [2], "track_depths": {"1": 0.5}}
            }
        }
    )
    workspace.roll(profile, 1234)
    assert workspace.candidate is not None
    changes = workspace.candidate["changes"]
    assert isinstance(changes, list) and changes
    assert all(item["track_id"] == 1 and item["parameter"] != "Tune" for item in changes)
    old = dict(workspace.candidate)
    workspace.change_scope({"master_depth": 0.25})
    assert workspace.candidate is None
    assert old["changes"] == changes  # slider change does not apply or undo past rolls


def test_parameter_depth_keeps_protected_unknown_baseline_exact(
    workspace: ApplianceWorkspace, tmp_path: Path
) -> None:
    profile = ProfileRegistry(tmp_path / "registry").list_profiles()[0]
    snapshot = workspace.sources[DEVICE_IDS[0]]
    a = mutate(snapshot, profile, 0.45, 456, parameter_depths={(1, "dec"): 0.25})
    b = mutate(snapshot, profile, 0.45, 456, parameter_depths={(1, "dec"): 0.25})
    assert a.pad_deltas == b.pad_deltas
    assert a.pad_deltas[0].proposed_params["tun"] == 64
    assert all(not delta.changed_keys for delta in a.pad_deltas if delta.pad_id != 1)
    for depth in (True, float("nan"), -1, 2):
        with pytest.raises(ValueError):
            mutate(snapshot, profile, 0.45, 456, parameter_depths={(1, "dec"): depth})


def test_both_local_apply_exact_confirmation_history_and_duplicate_refusal(
    workspace: ApplianceWorkspace, tmp_path: Path
) -> None:
    profile = ProfileRegistry(tmp_path / "registry").list_profiles()[0]
    workspace.change_scope({"target": "both"})
    workspace.navigate("anchor")
    initial = dict(workspace.sources)
    workspace.roll(profile, 1234)
    assert workspace.candidate is not None
    assert {change["device_id"] for change in workspace.candidate["changes"]} == set(DEVICE_IDS)
    payload = {"candidate_id": workspace.candidate["candidate_id"], "confirmed": True}
    for rejected in ({}, {**payload, "confirmed": False}, {**payload, "candidate_id": "old"}):
        with pytest.raises(ValueError):
            workspace.apply_local(rejected, hardware_intent=False)
    with pytest.raises(ValueError):
        workspace.apply_local(payload, hardware_intent=True)
    workspace.apply_local(payload, hardware_intent=False)
    applied = dict(workspace.sources)
    assert applied != initial and workspace.last_receipt["sent_count"] == 0
    with pytest.raises(ValueError):
        workspace.apply_local(payload, hardware_intent=False)
    workspace.navigate("undo")
    assert workspace.sources == initial
    workspace.navigate("redo")
    assert workspace.sources == applied
    workspace.navigate("return_anchor")
    assert workspace.sources == initial
    assert workspace.last_receipt["status"] == "local_history_only"


def test_profiles_persist_only_rules_and_import_is_validated(workspace: ApplianceWorkspace) -> None:
    identity = dict.fromkeys(DEVICE_IDS, None)
    workspace.profile_action("profile_save", {"name": "SHOW"}, identity)
    document = workspace.profile_action("profile_export", {"name": "SHOW"}, identity)
    restarted = ApplianceWorkspace(simulation=True, profile_file=workspace.profile_file)
    assert restarted.profiles == workspace.profiles
    assert restarted.candidate is None and restarted.anchor is None
    restarted.profile_action("profile_load", {"name": "SHOW"}, identity)
    restarted.profile_action("profile_delete", {"name": "SHOW"}, identity)
    restarted.profile_action("profile_import", {"document": document}, identity)
    assert "SHOW" in restarted.profiles
    for invalid in (
        {"schema_version": True, "profiles": {}},
        {"schema_version": 2, "profiles": {}},
        {},
    ):
        with pytest.raises(ValueError):
            restarted.profile_action("profile_import", {"document": invalid}, identity)


def test_corrupt_profile_storage_preserves_original(tmp_path: Path) -> None:
    target = tmp_path / "corrupt.json"
    target.write_bytes(b"corrupt")
    workspace = ApplianceWorkspace(simulation=False, profile_file=target)
    assert workspace.storage_error == "profile_storage_corrupt_or_unreadable"
    assert target.read_bytes() == b"corrupt"


def test_production_both_refuses_before_creating_any_lane_candidate(
    workspace: ApplianceWorkspace, tmp_path: Path
) -> None:
    profile = ProfileRegistry(tmp_path / "registry").list_profiles()[0]
    source = workspace.sources[DEVICE_IDS[0]]
    workspace = ApplianceWorkspace(simulation=False)
    workspace.sync(source, context="only-rytm-saved-capture")
    workspace.change_scope({"target": "both"})
    with pytest.raises(ValueError, match="all selected lanes"):
        workspace.roll(profile, 1234)
    assert not workspace.candidates and workspace.candidate is None


def test_master_track_and_page_depth_compose_before_rounding_and_zero_page_is_exact(
    workspace: ApplianceWorkspace, tmp_path: Path
) -> None:
    source = workspace.sources[DEVICE_IDS[0]]
    profile = ProfileRegistry(tmp_path / "registry").list_profiles()[0]
    workspace.change_scope(
        {
            "master_depth": 0.83,
            "lanes": {
                DEVICE_IDS[0]: {
                    "target_ids": [1],
                    "track_depths": {"1": 0.71},
                    "page_depths": {"SRC": 0.61, "AMP": 0, "FILTER": 0},
                }
            },
        }
    )
    workspace.roll(profile, 1234)
    actual = workspace.candidates[DEVICE_IDS[0]].pad_deltas[0]
    equivalent = ApplianceWorkspace(simulation=True)
    equivalent.sync(source, context="equivalent-product")
    equivalent.change_scope(
        {
            "master_depth": 0.83 * 0.71 * 0.61,
            "lanes": {DEVICE_IDS[0]: {"target_ids": [1], "page_ids": ["SRC"]}},
        }
    )
    equivalent.roll(profile, 1234)
    assert actual == equivalent.candidates[DEVICE_IDS[0]].pad_deltas[0]
    assert actual.changed_keys == frozenset({"dec"})
    assert actual.proposed_params["amp_decay"] == source.pads[0].params["amp_decay"]
    assert actual.proposed_params["flt"] == source.pads[0].params["flt"]


def test_context_digest_changes_and_sync_revokes_transient_authority(
    workspace: ApplianceWorkspace,
) -> None:
    workspace.navigate("anchor")
    source = workspace.sources[DEVICE_IDS[0]]
    workspace.sync(source, context="initial")
    assert workspace.anchor is not None
    workspace.sync(source, context="reconnect")
    assert workspace.anchor is None and workspace.candidate is None
    assert context_digest({"connection": 1}) != context_digest({"connection": 2})


def test_local_history_is_bounded(workspace: ApplianceWorkspace, tmp_path: Path) -> None:
    profile = ProfileRegistry(tmp_path / "registry").list_profiles()[0]
    for seed in range(HISTORY_LIMIT + 3):
        workspace.roll(profile, seed + 1)
        if workspace.candidate is not None:
            workspace.apply_local(
                {"candidate_id": workspace.candidate["candidate_id"], "confirmed": True},
                hardware_intent=False,
            )
    assert len(workspace.timeline) == HISTORY_LIMIT
    for _ in range(HISTORY_LIMIT - 1):
        workspace.navigate("undo")
    for device, snapshot in workspace.sources.items():
        assert snapshot.snapshot_id == workspace.timeline[0][device]
        assert workspace.histories[device].current.current_id == snapshot.snapshot_id
        assert len(workspace.histories[device].current.entries) <= HISTORY_LIMIT
    with pytest.raises(ValueError, match="no local history"):
        workspace.navigate("undo")
    workspace.navigate("redo")
    assert workspace.cursor == 1


@pytest.mark.parametrize("navigation", ["undo", "return_anchor"])
def test_roll_after_history_navigation_uses_selected_parent_and_discards_redo(
    workspace: ApplianceWorkspace, tmp_path: Path, navigation: str
) -> None:
    profile = ProfileRegistry(tmp_path / "registry").list_profiles()[0]
    workspace.change_scope({"target": "both"})
    workspace.navigate("anchor")
    baseline = dict(workspace.sources)
    workspace.roll(profile, 1234)
    workspace.apply_local(
        {"candidate_id": workspace.candidate["candidate_id"], "confirmed": True},
        hardware_intent=False,
    )
    discarded = dict(workspace.sources)
    workspace.navigate(navigation)
    assert workspace.sources == baseline
    workspace.roll(profile, 5678)
    workspace.apply_local(
        {"candidate_id": workspace.candidate["candidate_id"], "confirmed": True},
        hardware_intent=False,
    )
    for device, history in workspace.histories.items():
        entries = history.current.entries
        assert len(entries) == 2
        assert entries[-1].parent_id == baseline[device].snapshot_id
        assert entries[-1].snapshot == workspace.sources[device]
        assert discarded[device].snapshot_id not in {
            entry.snapshot.snapshot_id for entry in entries
        }
    with pytest.raises(ValueError, match="no local history"):
        workspace.navigate("redo")
    workspace.navigate("undo")
    assert workspace.sources == baseline


def test_native_bounds_preserve_fixed_point_precision_and_zero_depth(tmp_path: Path) -> None:
    profile = ProfileRegistry(tmp_path / "registry").list_profiles()[0]
    snapshot = Snapshot(
        "native",
        DEVICE_IDS[1],
        datetime.now(timezone.utc),
        (PadState(1, "A4 native", {"fixed": 16391, "protected": 30000}),),
        None,
        None,
    )
    bounds = {(1, "fixed"): (0, 32767), (1, "protected"): (0, 32767)}
    candidate = mutate(
        snapshot,
        profile,
        0.45,
        456,
        parameter_bounds=bounds,
        parameter_depths={(1, "fixed"): 0.01},
    )
    values = candidate.pad_deltas[0].proposed_params
    assert 16000 < values["fixed"] < 16800
    assert values["fixed"] != snapshot.pads[0].params["fixed"]
    assert values["fixed"] % 256 != 0  # Native Q8.8 precision is not truncated to CC7.
    assert values["protected"] == 30000
    unchanged = mutate(snapshot, profile, 0.45, 456, parameter_bounds=bounds, parameter_depths={})
    assert unchanged.pad_deltas[0].changed_keys == frozenset()
    full = mutate(snapshot, profile, 0.45, 456, parameter_bounds=bounds)
    assert full.pad_deltas[0].proposed_params["fixed"] > 127


@pytest.mark.parametrize("limits", [(True, 127), (0, False), (0.5, 127), (0, 127.5), (100, 1)])
def test_native_bounds_reject_invalid_domains(
    workspace: ApplianceWorkspace, tmp_path: Path, limits: tuple[object, object]
) -> None:
    profile = ProfileRegistry(tmp_path / "registry").list_profiles()[0]
    with pytest.raises(ValueError, match="ordered integer limits"):
        mutate(
            workspace.sources[DEVICE_IDS[0]],
            profile,
            0.45,
            1,
            parameter_bounds={(1, "dec"): cast(tuple[int, int], limits)},
        )
    with pytest.raises(ValueError, match="known cell"):
        mutate(
            workspace.sources[DEVICE_IDS[0]],
            profile,
            0.45,
            1,
            parameter_bounds={(1, "unknown"): (0, 127)},
        )
