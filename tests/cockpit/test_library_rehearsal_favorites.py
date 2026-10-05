"""Scoped local retention is exact, durable and never hardware authority."""

from __future__ import annotations

import copy
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import cast

import pytest

from rytm_randomizer.cockpit.data import PadState
from rytm_randomizer.cockpit.data.parameter_scope import ParameterCell, ParameterSelection
from rytm_randomizer.cockpit.data.rehearsal_favorite import LocalRehearsalFavorite
from rytm_randomizer.cockpit.data.stage import ANALOG_FOUR_DEVICE_ID
from rytm_randomizer.cockpit.engine import mutate
from rytm_randomizer.cockpit.export import writer
from rytm_randomizer.cockpit.library import LibraryRecord, LibraryStore
from rytm_randomizer.cockpit.parameter_scope import pad2_rehearsal_selection, rytm_parameter_depths
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.data.analog_four_sysex_calibration import A4_FILTER1_FREQUENCY_PARAMETER
from rytm_randomizer.data.persisted_state import classify_payload
from rytm_randomizer.observability.errors import PersistedStateVersionError

from .conftest import make_default_snapshot

pytestmark = pytest.mark.fast


@pytest.fixture
def favorite(tmp_path: Path) -> LocalRehearsalFavorite:
    source = make_default_snapshot()
    source = replace(
        source,
        pads=tuple(
            (
                replace(
                    pad,
                    params={
                        **pad.params,
                        "amp_decay": 84,
                        "overdrive": 19,
                        "reverb": 0,
                        "retained_native": 16385,
                        "lev": 100,
                    },
                )
                if pad.pad_id == 2
                else pad
            )
            for pad in source.pads
        ),
    )
    selection = pad2_rehearsal_selection(source)
    profile = ProfileRegistry(tmp_path / "profiles").builtin_scenes[0]
    candidate = mutate(
        source,
        profile,
        0.10,
        42,
        target_pad_ids=frozenset((2,)),
        locked_pad_ids=frozenset((1,)),
        parameter_depths=rytm_parameter_depths(source, selection, 0.10),
    )
    return LocalRehearsalFavorite(
        source_snapshot=source,
        profile=profile,
        candidate=candidate,
        rytm_pad_targets=frozenset((2,)),
        locked_pad_ids=frozenset((1,)),
        a4_track_targets=frozenset((1, 2)),
        locked_a4_track_ids=frozenset((1, 2, 3, 4)),
        rytm_parameter_selection=selection,
        a4_parameter_selection=ParameterSelection(
            (ParameterCell(1, A4_FILTER1_FREQUENCY_PARAMETER),)
        ),
    )


def _mapping(value: object) -> dict[str, object]:
    return cast(dict[str, object], value)


def test_favorite_roundtrip_preserves_exact_source_recipe_candidate_and_native_ints(
    favorite: LocalRehearsalFavorite,
) -> None:
    raw = json.loads(json.dumps(favorite.to_dict(), allow_nan=False))
    restored = LocalRehearsalFavorite.from_dict(raw)
    assert restored == favorite
    assert restored.source_snapshot.pads[1].params["retained_native"] == 16385
    assert restored.candidate.pad_deltas[0].proposed_params["retained_native"] == 16385
    assert restored.candidate.seed == 42 and restored.candidate.depth == 0.10
    assert restored.candidate.source_snapshot_id == favorite.source_snapshot.snapshot_id
    assert {cell.parameter_key for cell in restored.parameter_selection.cells or ()} == {
        "flt",
        "amp_decay",
        "overdrive",
        "reverb",
    }
    assert not {"armed", "send_plan", "confirmation", "hardware_ready"} & set(raw)


def test_favorite_is_frozen_and_candidate_parameter_maps_are_defensive(
    favorite: LocalRehearsalFavorite,
) -> None:
    with pytest.raises(FrozenInstanceError):
        favorite.locked_pad_ids = frozenset()  # type: ignore[misc]
    with pytest.raises(TypeError):
        favorite.candidate.pad_deltas[0].proposed_params["flt"] = 1  # type: ignore[index]


def test_favorite_hashes_are_deterministic_and_provenance_sensitive(
    favorite: LocalRehearsalFavorite,
) -> None:
    assert LocalRehearsalFavorite.from_dict(favorite.to_dict()).to_dict() == favorite.to_dict()
    assert len(favorite.source_hash) == len(favorite.recipe_hash) == 64
    new_source = replace(favorite.source_snapshot, scene_slot="B02")
    changed = replace(favorite, source_snapshot=new_source)
    assert changed.source_hash != favorite.source_hash
    assert changed.recipe_hash != favorite.recipe_hash
    assert changed.favorite_id != favorite.favorite_id
    fresh_identity = replace(
        favorite, candidate=replace(favorite.candidate, candidate_id="fresh-id")
    )
    assert fresh_identity.recipe_hash == favorite.recipe_hash
    assert fresh_identity.favorite_id != favorite.favorite_id


@pytest.mark.parametrize("bad", [True, False, 1.5, "63", None, float("nan"), float("inf")])
@pytest.mark.parametrize("container", ["source", "candidate"])
def test_favorite_rejects_coercing_native_values_before_model_load(
    favorite: LocalRehearsalFavorite,
    bad: object,
    container: str,
) -> None:
    raw = copy.deepcopy(favorite.to_dict())
    if container == "source":
        pad = _mapping(_mapping(raw["source_snapshot"])["pads"][1])
        _mapping(pad["params"])["flt"] = bad
    else:
        delta = _mapping(_mapping(raw["candidate"])["pad_deltas"][0])
        _mapping(delta["proposed_params"])["flt"] = bad
    with pytest.raises(ValueError, match="native value must be an integer"):
        LocalRehearsalFavorite.from_dict(raw)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("seed", True),
        ("depth", True),
        ("depth", float("nan")),
        ("depth", float("inf")),
        ("estimated_midi_msgs", False),
    ],
)
def test_favorite_rejects_invalid_recipe_numbers(
    favorite: LocalRehearsalFavorite,
    field: str,
    bad: object,
) -> None:
    raw = copy.deepcopy(favorite.to_dict())
    _mapping(raw["candidate"])[field] = bad
    with pytest.raises(ValueError):
        LocalRehearsalFavorite.from_dict(raw)


@pytest.mark.parametrize("field", ["source_hash", "recipe_hash", "favorite_id"])
def test_favorite_rejects_forged_hashes(favorite: LocalRehearsalFavorite, field: str) -> None:
    raw = favorite.to_dict()
    raw[field] = "forged"
    with pytest.raises(ValueError, match="integrity"):
        LocalRehearsalFavorite.from_dict(raw)


@pytest.mark.parametrize("field", ["source_snapshot_id", "profile_id"])
def test_favorite_rejects_wrong_candidate_identity(
    favorite: LocalRehearsalFavorite,
    field: str,
) -> None:
    with pytest.raises(ValueError, match="identity"):
        replace(favorite, candidate=replace(favorite.candidate, **{field: "wrong"}))


def test_favorite_rejects_excluded_change_instead_of_trimming_candidate(
    favorite: LocalRehearsalFavorite,
) -> None:
    with pytest.raises(ValueError, match="excluded"):
        replace(favorite, rytm_parameter_selection=ParameterSelection(()))


@pytest.mark.parametrize(
    "field,ids",
    [
        ("locked_pad_ids", frozenset((2,))),
        ("rytm_pad_targets", frozenset((1,))),
        ("a4_track_targets", frozenset((5,))),
        ("locked_a4_track_ids", frozenset((True,))),
    ],
)
def test_favorite_rejects_scope_forgery_and_invalid_partner_ids(
    favorite: LocalRehearsalFavorite,
    field: str,
    ids: frozenset[int],
) -> None:
    with pytest.raises(ValueError):
        replace(favorite, **{field: ids})


def test_favorite_rejects_absent_selected_parameter(favorite: LocalRehearsalFavorite) -> None:
    with pytest.raises(ValueError, match="absent"):
        replace(favorite, rytm_parameter_selection=ParameterSelection((ParameterCell(2, "nope"),)))


def test_favorite_rejects_delta_key_and_parameter_identity_forgery(
    favorite: LocalRehearsalFavorite,
) -> None:
    delta = favorite.candidate.pad_deltas[0]
    with pytest.raises(ValueError, match="changed_keys"):
        replace(
            favorite,
            candidate=replace(
                favorite.candidate, pad_deltas=(replace(delta, changed_keys=frozenset()),)
            ),
        )
    with pytest.raises(ValueError, match="parameter identities"):
        replace(
            favorite,
            candidate=replace(
                favorite.candidate,
                pad_deltas=(
                    replace(delta, proposed_params={**delta.proposed_params, "invented": 2}),
                ),
            ),
        )


def test_favorite_rejects_partner_selection_outside_domain(
    favorite: LocalRehearsalFavorite,
) -> None:
    with pytest.raises(ValueError, match="outside the device domain"):
        replace(
            favorite,
            a4_parameter_selection=ParameterSelection((ParameterCell(5, "Filter1 Frequency"),)),
        )


def test_library_favorite_restarts_and_tags_without_losing_scope(
    favorite: LocalRehearsalFavorite,
    tmp_path: Path,
) -> None:
    store = LibraryStore(tmp_path)
    record = store.retain_rehearsal(favorite, "Pad 2 practice")
    assert record.rehearsal == favorite and record.payload_hex == ""
    assert record.to_dict()["record_kind"] == "rehearsal_favorite"
    assert json.loads((tmp_path / f"{record.record_id}.json").read_text())["schema_version"] == 2
    reopened = LibraryStore(tmp_path).get(record.record_id)
    assert reopened == record
    assert LibraryStore(tmp_path).retain_rehearsal(favorite, "different name") == record
    assert store.search("Pad 2") == (record,)
    tagged = store.tag(record.record_id, ["rehearsal", "small"])
    assert tagged.rehearsal == favorite
    assert LibraryStore(tmp_path).get(record.record_id) == tagged


def test_library_refuses_candidate_changed_after_integrity_recomputed_before_write(
    favorite: LocalRehearsalFavorite,
    tmp_path: Path,
) -> None:
    forged = replace(favorite, candidate=replace(favorite.candidate, seed=99))
    with pytest.raises(ValueError, match="deterministic_verification"):
        LibraryStore(tmp_path).retain_rehearsal(forged, "forged recipe")
    assert list(tmp_path.glob("*.json")) == []


def test_library_refuses_protected_selection_before_write(
    favorite: LocalRehearsalFavorite,
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="protected_or_unavailable"):
        forged = replace(
            favorite,
            rytm_parameter_selection=ParameterSelection(
                (*favorite.parameter_selection.cells, ParameterCell(2, "lev"))
            ),
        )
        LibraryStore(tmp_path).retain_rehearsal(forged, "protected")
    assert list(tmp_path.glob("*.json")) == []


@pytest.mark.parametrize("name", ["", " ", "x" * 129, 123, None])
def test_library_rejects_invalid_favorite_name_before_write(
    favorite: LocalRehearsalFavorite,
    tmp_path: Path,
    name: str,
) -> None:
    with pytest.raises(ValueError, match="favorite name"):
        LibraryStore(tmp_path).retain_rehearsal(favorite, name)
    assert list(tmp_path.glob("*.json")) == []


def test_library_corrupt_recall_does_not_rewrite_or_overwrite_prior_bytes(
    favorite: LocalRehearsalFavorite,
    tmp_path: Path,
) -> None:
    store = LibraryStore(tmp_path)
    record = store.retain_rehearsal(favorite, "exact")
    path = tmp_path / f"{record.record_id}.json"
    raw = json.loads(path.read_text())
    raw["rehearsal"]["candidate"]["candidate_id"] = "tampered"
    broken = json.dumps(raw).encode()
    path.write_bytes(broken)
    assert LibraryStore(tmp_path).get(record.record_id) is None
    with pytest.raises(FileExistsError):
        store.retain_rehearsal(favorite, "must not replace")
    assert path.read_bytes() == broken


@pytest.mark.parametrize(
    "field,bad",
    [
        ("record_kind", "capture"),
        ("device_id", "wrong"),
        ("fingerprint", "wrong"),
        ("captured_at", "wrong"),
        ("payload_hex", "f0f7"),
        ("kit_name", True),
    ],
)
def test_library_rejects_inconsistent_favorite_metadata(
    favorite: LocalRehearsalFavorite,
    tmp_path: Path,
    field: str,
    bad: object,
) -> None:
    record = LibraryStore(tmp_path).retain_rehearsal(favorite, "exact")
    raw = record.to_dict()
    raw[field] = bad
    with pytest.raises(ValueError):
        LibraryRecord.from_dict(raw)


def test_library_write_failure_leaves_existing_favorite_exact(
    favorite: LocalRehearsalFavorite,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = LibraryStore(tmp_path)
    record = store.retain_rehearsal(favorite, "exact")
    path = tmp_path / f"{record.record_id}.json"
    original = path.read_bytes()

    def fail_replace(*_args: object) -> None:
        raise OSError("simulated publication failure")

    monkeypatch.setattr(writer.os, "replace", fail_replace)
    with pytest.raises(OSError):
        store.tag(record.record_id, ["not published"])
    assert path.read_bytes() == original
    assert list(tmp_path.glob("*.tmp")) == []


@pytest.mark.parametrize("version", [None, 1])
def test_library_capture_v1_migration_preserves_capture_payload_and_disk_bytes(
    tmp_path: Path,
    version: int | None,
) -> None:
    raw: dict[str, object] = {
        "record_id": "old",
        "device_id": "analog_rytm_mk2",
        "kit_name": "OLD",
        "fingerprint": "old",
        "captured_at": "2026-01-01T00:00:00Z",
        "tags": ["dry"],
        "payload_hex": "f0f7",
    }
    if version is not None:
        raw["schema_version"] = version
    encoded = json.dumps(raw).encode()
    path = tmp_path / "old.json"
    path.write_bytes(encoded)
    record = LibraryStore(tmp_path).get("old")
    assert record is not None and record.rehearsal is None
    assert record.payload_hex == "f0f7" and record.tags == ("dry",)
    assert record.to_dict()["record_kind"] == "capture"
    assert path.read_bytes() == encoded
    decision = classify_payload("library_store", raw)
    assert decision.code == "persisted_state.migrated"
    assert decision.payload["record_kind"] == "capture"


def test_library_future_schema_and_invalid_migration_leave_bytes_exact(tmp_path: Path) -> None:
    for raw in ({"schema_version": 99}, {"schema_version": 1, "rehearsal": {"forged": True}}):
        path = tmp_path / "probe.json"
        encoded = json.dumps(raw).encode()
        path.write_bytes(encoded)
        if raw["schema_version"] == 99:
            with pytest.raises(PersistedStateVersionError):
                LibraryStore(tmp_path).get("probe")
        else:
            assert LibraryStore(tmp_path).get("probe") is None
            assert classify_payload("library_store", raw).code == "persisted_state.migration_failed"
        assert path.read_bytes() == encoded


def test_library_refuses_renamed_favorite_file_without_rewriting(
    favorite: LocalRehearsalFavorite,
    tmp_path: Path,
) -> None:
    record = LibraryStore(tmp_path).retain_rehearsal(favorite, "exact")
    old = tmp_path / f"{record.record_id}.json"
    path = tmp_path / "different.json"
    old.rename(path)
    original = path.read_bytes()
    assert LibraryStore(tmp_path).get("different") is None
    assert path.read_bytes() == original


def test_library_refuses_capture_collision_without_overwriting(
    favorite: LocalRehearsalFavorite,
    tmp_path: Path,
) -> None:
    capture = LibraryRecord(
        favorite.favorite_id, "analog_rytm_mk2", "OLD", "capture", "old", (), "f0f7"
    )
    path = tmp_path / f"{favorite.favorite_id}.json"
    original = json.dumps(capture.to_dict()).encode()
    path.write_bytes(original)
    with pytest.raises(ValueError, match="identity_collision"):
        LibraryStore(tmp_path).retain_rehearsal(favorite, "must refuse")
    assert path.read_bytes() == original


def test_library_schema2_requires_explicit_record_kind_without_reset(tmp_path: Path) -> None:
    path = tmp_path / "legacy.json"
    original = b'{"schema_version":2,"record_id":"legacy"}'
    path.write_bytes(original)
    assert LibraryStore(tmp_path).get("legacy") is None
    assert path.read_bytes() == original


@pytest.mark.parametrize("selection", [ParameterSelection(), ParameterSelection(())])
def test_favorite_retains_distinction_between_legacy_all_and_none(
    favorite: LocalRehearsalFavorite,
    selection: ParameterSelection,
) -> None:
    source = make_default_snapshot()
    candidate = mutate(
        source,
        favorite.profile,
        0.10,
        42,
        parameter_depths=rytm_parameter_depths(source, selection, 0.10),
    )
    retained = LocalRehearsalFavorite(
        source, favorite.profile, candidate, rytm_parameter_selection=selection
    )
    assert LocalRehearsalFavorite.from_dict(retained.to_dict()).parameter_selection == selection
    LibraryStore.verify_rehearsal(retained)


def test_zero_depth_and_locked_selected_pad_retain_exact_source(
    favorite: LocalRehearsalFavorite,
) -> None:
    for depth, locks in ((0.0, favorite.locked_pad_ids), (0.1, frozenset((1, 2)))):
        candidate = mutate(
            favorite.source_snapshot,
            favorite.profile,
            depth,
            42,
            target_pad_ids=favorite.rytm_pad_targets,
            locked_pad_ids=locks,
            parameter_depths=rytm_parameter_depths(
                favorite.source_snapshot, favorite.parameter_selection, depth
            ),
        )
        retained = replace(favorite, candidate=candidate, locked_pad_ids=locks)
        assert all(not delta.changed_keys for delta in retained.candidate.pad_deltas)
        LibraryStore.verify_rehearsal(retained)


def test_a4_context_preserves_scope_and_precision_but_cannot_grant_verification(
    favorite: LocalRehearsalFavorite,
) -> None:
    source = replace(
        favorite.source_snapshot,
        device=ANALOG_FOUR_DEVICE_ID,
        pads=(PadState(1, "Analog Four synth track", {A4_FILTER1_FREQUENCY_PARAMETER: 16256}),),
        scene_slot=None,
        bpm=None,
    )
    retained = LocalRehearsalFavorite(
        source,
        favorite.profile,
        replace(favorite.candidate, pad_deltas=(), estimated_midi_msgs=0),
        a4_track_targets=frozenset((1,)),
        locked_a4_track_ids=frozenset((1,)),
        a4_parameter_selection=favorite.a4_parameter_selection,
    )
    assert LocalRehearsalFavorite.from_dict(retained.to_dict()) == retained
    assert retained.mutation_scope().effective_ids((1,)) == frozenset()
    with pytest.raises(ValueError, match="a4_candidate_verification_unavailable"):
        LibraryStore.verify_rehearsal(retained)


@pytest.mark.parametrize("kind", ["bpm", "trait", "weight", "trait_pad", "source_pad"])
def test_favorite_rejects_boolean_and_nonfinite_numeric_context(
    favorite: LocalRehearsalFavorite,
    kind: str,
) -> None:
    raw = copy.deepcopy(favorite.to_dict())
    if kind == "bpm":
        _mapping(raw["source_snapshot"])["bpm"] = True
    elif kind == "source_pad":
        _mapping(_mapping(raw["source_snapshot"])["pads"][0])["pad_id"] = True
    elif kind == "trait":
        _mapping(_mapping(raw["profile"])["traits"][0])["value"] = float("nan")
    else:
        _mapping(_mapping(raw["profile"])["pad_mappings"][0])[
            "pad_id" if kind == "trait_pad" else "weight"
        ] = True
    with pytest.raises(ValueError):
        LocalRehearsalFavorite.from_dict(raw)


@pytest.mark.parametrize("kind", ["duplicate", "absent", "wrong-device", "source-domain"])
def test_favorite_rejects_malformed_schema_and_delta_order(
    favorite: LocalRehearsalFavorite,
    kind: str,
) -> None:
    raw = copy.deepcopy(favorite.to_dict())
    if kind == "duplicate":
        delta = _mapping(raw["candidate"])["pad_deltas"][0]
        delta["changed_keys"].append(delta["changed_keys"][0])
    elif kind == "absent":
        raw.pop("profile")
    elif kind == "wrong-device":
        _mapping(raw["source_snapshot"])["device"] = "unknown"
    else:
        _mapping(raw["source_snapshot"])["device"] = ANALOG_FOUR_DEVICE_ID
    with pytest.raises(ValueError):
        LocalRehearsalFavorite.from_dict(raw)
