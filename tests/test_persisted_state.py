"""Unit tests for the persisted-state registry (spec §11 Contract A).

The registry is pure policy — no filesystem, no exceptions from the
classification path — which is exactly what makes the update system's
central promise ("your state survives the binary swapping under it")
exhaustively testable. Every branch of :mod:`rytm_randomizer.data.persisted_state`
is exercised here, plus the two store integrations that consume it.

The tests are organised by the contract's five rules rather than by
function, so a reader can check the promise instead of the code.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest

from rytm_randomizer.data import persisted_state
from rytm_randomizer.data.persisted_state import (
    PERSISTED_STATE_CODES,
    PERSISTED_STATE_STORES,
    PERSISTED_STATE_VERSION_FIELD,
    PersistedStateDecision,
    PersistedStateMigration,
    PersistedStateMigrationFn,
    PersistedStateStore,
    apply_migration_plan,
    classify_payload,
    current_schema_version,
    plan_migration,
    read_schema_version,
    registered_store,
    registered_store_ids,
    require_schema_version,
)
from rytm_randomizer.observability.errors import PersistedStateVersionError
from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

pytestmark = pytest.mark.fast


def _store(
    *,
    store_id: str = "probe",
    schema_version: int = 1,
    migrations: tuple[PersistedStateMigration, ...] = (),
) -> PersistedStateStore:
    """A throwaway store declaration for policy tests.

    Explicitly typed keyword parameters rather than ``**overrides:
    object`` — the loose signature forced a ``# type: ignore`` on every
    call site, which is exactly the annotation-erasure the house style
    forbids.
    """

    return PersistedStateStore(
        store_id=store_id,
        schema_version=schema_version,
        owner_module="rytm_randomizer.data.persisted_state",
        description="probe store",
        migrations=migrations,
    )


def _bump(key: str) -> PersistedStateMigrationFn:
    """A migration function that stamps ``key`` onto the payload."""

    def _migrate(payload: Mapping[str, object]) -> Mapping[str, object]:
        return {**payload, key: True}

    return _migrate


def _returns(value: object) -> PersistedStateMigrationFn:
    """A migration that returns ``value``, whatever its runtime type.

    Used to prove the policy's ``isinstance(migrated, Mapping)`` guard
    fires. The inner function is annotated ``-> object`` and the cast to
    the migration type happens once, here, with a stated reason — rather
    than sprinkling ``# type: ignore[return-value]`` at each call site,
    which would suppress the checker on lines where it is doing real
    work. A migration author *can* return the wrong thing (that is why
    the runtime guard exists); this helper models that honestly.
    """

    def _migrate(_payload: Mapping[str, object]) -> object:
        return value

    return cast("PersistedStateMigrationFn", _migrate)


# ---------------------------------------------------------------------------
# Declaration-time validation.
# ---------------------------------------------------------------------------


def test_a_store_may_not_declare_version_zero() -> None:
    with pytest.raises(ValueError, match="must be >= 1"):
        _store(schema_version=0)


def test_migration_chain_must_start_at_version_one() -> None:
    with pytest.raises(ValueError, match="unbroken chain"):
        _store(
            schema_version=3,
            migrations=(PersistedStateMigration(2, _bump("a"), "skip"),),
        )


def test_migration_chain_must_reach_the_declared_version() -> None:
    with pytest.raises(ValueError, match="reaches 2"):
        _store(
            schema_version=5,
            migrations=(PersistedStateMigration(1, _bump("a"), "one"),),
        )


def test_a_version_bump_without_a_migration_is_refused() -> None:
    """A bump with no chain at all is the common forgetful case."""

    with pytest.raises(ValueError, match="needs its forward migration"):
        _store(schema_version=2)


def test_a_contiguous_chain_is_accepted() -> None:
    store = _store(
        schema_version=3,
        migrations=(
            PersistedStateMigration(1, _bump("a"), "one"),
            PersistedStateMigration(2, _bump("b"), "two"),
        ),
    )
    assert store.migrations[0].to_version == 2
    assert store.migrations[1].to_version == 3


# ---------------------------------------------------------------------------
# Registry accessors.
# ---------------------------------------------------------------------------


def test_registered_store_ids_are_sorted_and_match_the_table() -> None:
    ids = registered_store_ids()
    assert ids == tuple(sorted(PERSISTED_STATE_STORES))


def test_registered_store_returns_the_declaration_or_none() -> None:
    known = registered_store_ids()[0]
    assert registered_store(known) is PERSISTED_STATE_STORES[known]
    assert registered_store("nope") is None


def test_current_schema_version_returns_none_for_an_unknown_store() -> None:
    assert current_schema_version("nope") is None
    assert current_schema_version(registered_store_ids()[0]) == 1


def test_require_schema_version_returns_the_version_or_raises() -> None:
    assert require_schema_version(registered_store_ids()[0]) == 1
    with pytest.raises(ValueError, match="not registered"):
        require_schema_version("nope")


def test_every_declared_code_is_in_the_closed_vocabulary() -> None:
    assert len(PERSISTED_STATE_CODES) == 7
    assert "persisted_state.schema_newer_than_app" in PERSISTED_STATE_CODES
    assert "persisted_state.migration_failed" in PERSISTED_STATE_CODES


# ---------------------------------------------------------------------------
# Rule 3 — a missing version field means version 1, not corruption.
# ---------------------------------------------------------------------------


def test_absent_version_field_reads_as_version_one() -> None:
    assert read_schema_version({"unrelated": 1}) == 1


def test_present_integer_version_reads_back_verbatim() -> None:
    assert read_schema_version({PERSISTED_STATE_VERSION_FIELD: 4}) == 4


@pytest.mark.parametrize("bad", ["1", 1.5, None, [], {}])
def test_a_non_integer_version_field_is_a_shape_problem(bad: object) -> None:
    assert read_schema_version({PERSISTED_STATE_VERSION_FIELD: bad}) is None


def test_a_boolean_version_field_is_rejected_not_read_as_one() -> None:
    """``True`` is an ``int`` subclass; treating it as v1 would be wrong."""

    assert read_schema_version({PERSISTED_STATE_VERSION_FIELD: True}) is None


def test_a_zero_or_negative_version_field_is_rejected() -> None:
    assert read_schema_version({PERSISTED_STATE_VERSION_FIELD: 0}) is None
    assert read_schema_version({PERSISTED_STATE_VERSION_FIELD: -3}) is None


def test_a_pre_envelope_file_migrates_rather_than_being_discarded() -> None:
    """The headline of rule 3, end to end through ``classify_payload``."""

    known = registered_store_ids()[0]
    decision = classify_payload(known, {"kit_name": "AL02"})
    assert decision.code == "persisted_state.ok"
    assert decision.accepted and not decision.refused
    assert decision.payload == {"kit_name": "AL02"}


# ---------------------------------------------------------------------------
# Rule 1 — never silently reset.
# ---------------------------------------------------------------------------


def test_an_unknown_store_is_refused() -> None:
    decision = classify_payload("nope", {})
    assert decision.code == "persisted_state.unknown_store"
    assert decision.payload is None
    assert decision.to_version is None
    assert decision.detail == {"reason": "store_not_registered"}


def test_an_unreadable_file_is_refused_not_reset() -> None:
    known = registered_store_ids()[0]
    decision = classify_payload(known, None, readable=False)
    assert decision.code == "persisted_state.unreadable"
    assert decision.payload is None
    assert decision.detail["reason"] == "read_or_decode_failed"


@pytest.mark.parametrize("payload", [["a"], "text", 7, None])
def test_a_non_mapping_payload_is_refused(payload: object) -> None:
    known = registered_store_ids()[0]
    decision = classify_payload(known, payload)
    assert decision.code == "persisted_state.unknown_shape"
    assert decision.detail["reason"] == "payload_not_a_mapping"


def test_a_junk_version_field_is_refused() -> None:
    known = registered_store_ids()[0]
    decision = classify_payload(known, {PERSISTED_STATE_VERSION_FIELD: "one"})
    assert decision.code == "persisted_state.unknown_shape"
    assert decision.detail["reason"] == "schema_version_not_a_positive_int"


# ---------------------------------------------------------------------------
# Rule 2 — the downgrade-refusal rule.
# ---------------------------------------------------------------------------


def test_state_from_a_newer_app_is_refused_with_both_versions_named() -> None:
    known = registered_store_ids()[0]
    decision = classify_payload(known, {PERSISTED_STATE_VERSION_FIELD: 9})
    assert decision.code == "persisted_state.schema_newer_than_app"
    assert decision.from_version == 9
    assert decision.to_version == 1
    assert decision.payload is None, "a refusal must never hand back truncated state"
    assert decision.detail == {
        "reason": "state_written_by_newer_app",
        "found_version": 9,
        "app_version": 1,
    }


# ---------------------------------------------------------------------------
# Rule 4 — migrations are explicit, ordered, recorded.
# ---------------------------------------------------------------------------


def test_plan_migration_is_empty_when_already_current() -> None:
    store = _store(
        schema_version=2,
        migrations=(PersistedStateMigration(1, _bump("a"), "one"),),
    )
    assert plan_migration(store, 2) == ()


def test_plan_migration_selects_only_the_remaining_hops() -> None:
    store = _store(
        schema_version=4,
        migrations=(
            PersistedStateMigration(1, _bump("a"), "one"),
            PersistedStateMigration(2, _bump("b"), "two"),
            PersistedStateMigration(3, _bump("c"), "three"),
        ),
    )
    assert [m.summary for m in plan_migration(store, 3)] == ["three"]


def test_a_full_chain_runs_in_order_and_stamps_the_new_version() -> None:
    store = _store(
        schema_version=3,
        migrations=(
            PersistedStateMigration(1, _bump("a"), "add a"),
            PersistedStateMigration(2, _bump("b"), "add b"),
        ),
    )
    decision = apply_migration_plan(store, {"seed": 1}, from_version=1)
    assert decision.code == "persisted_state.migrated"
    assert decision.accepted
    assert decision.steps == ("add a", "add b")
    assert decision.payload == {
        "seed": 1,
        "a": True,
        "b": True,
        PERSISTED_STATE_VERSION_FIELD: 3,
    }
    assert decision.detail == {"reason": "migrated_forward", "steps": 2}


def test_classify_routes_an_older_payload_into_the_migration_chain() -> None:
    """The seam between classification and migration.

    Every store registered today is at version 1, so this hand-off has
    no natural caller yet — it is the path the *first* real bump will
    take, and it must be proven now rather than discovered then. A
    hypothetical v2 store is supplied through ``classify_payload``'s
    ``store=`` parameter; the registry itself is a read-only
    ``MappingProxyType`` and is never mutated by a test.
    """

    store = _store(
        store_id="chained",
        schema_version=2,
        migrations=(PersistedStateMigration(1, _bump("a"), "add a"),),
    )

    decision = classify_payload("chained", {"seed": 1}, store=store)
    assert decision.code == "persisted_state.migrated"
    assert decision.from_version == 1
    assert decision.payload == {"seed": 1, "a": True, PERSISTED_STATE_VERSION_FIELD: 2}

    direct = apply_migration_plan(store, {}, from_version=1)
    assert direct.payload == {"a": True, PERSISTED_STATE_VERSION_FIELD: 2}


def test_the_registry_mapping_cannot_be_mutated_at_runtime() -> None:
    """House rule: no mutable module-level globals; the fact table is frozen.

    A test that reaches for ``monkeypatch.setitem`` on the registry is a
    test working around this, so the door is nailed shut and
    ``classify_payload(store=...)`` is the supported way to exercise a
    hypothetical store.
    """

    with pytest.raises(TypeError):
        persisted_state.PERSISTED_STATE_STORES["injected"] = _store()  # type: ignore[index]


def test_an_explicit_store_must_agree_with_the_store_id() -> None:
    """A caller bug is raised, not laundered into a data refusal."""

    with pytest.raises(ValueError, match="disagrees with the supplied"):
        classify_payload("other", {}, store=_store(store_id="probe"))


def test_an_older_payload_with_no_declared_migration_fails_closed() -> None:
    """Accepting it silently is the data loss rule 1 forbids."""

    store = _store(schema_version=1)
    decision = apply_migration_plan(store, {"x": 1}, from_version=1)
    assert decision.code == "persisted_state.migration_failed"
    assert decision.payload is None
    assert decision.detail == {
        "reason": "no_migration_declared",
        "found_version": 1,
        "app_version": 1,
    }


@pytest.mark.parametrize("boom", [ValueError, TypeError, KeyError, IndexError])
def test_a_raising_migration_becomes_a_bounded_refusal(boom: type[Exception]) -> None:
    def _explode(_payload: Mapping[str, object]) -> Mapping[str, object]:
        raise boom("detail that must not reach the journal")

    store = _store(
        schema_version=2,
        migrations=(PersistedStateMigration(1, _explode, "boom"),),
    )
    decision = apply_migration_plan(store, {}, from_version=1)
    assert decision.code == "persisted_state.migration_failed"
    assert decision.payload is None
    assert decision.steps == ()
    assert decision.detail == {
        "reason": "migration_raised",
        "failed_from_version": 1,
        "failed_to_version": 2,
    }
    assert "detail that must not reach" not in repr(dict(decision.detail))


def test_an_unexpected_exception_family_propagates_rather_than_laundering() -> None:
    """Only the named families become refusals; anything else is a real bug."""

    def _explode(_payload: Mapping[str, object]) -> Mapping[str, object]:
        raise RuntimeError("programmer error")

    store = _store(
        schema_version=2,
        migrations=(PersistedStateMigration(1, _explode, "boom"),),
    )
    with pytest.raises(RuntimeError, match="programmer error"):
        apply_migration_plan(store, {}, from_version=1)


def test_a_migration_returning_a_non_mapping_fails_closed() -> None:
    store = _store(
        schema_version=2,
        migrations=(PersistedStateMigration(1, _returns(["not", "a", "mapping"]), "wrong"),),
    )
    decision = apply_migration_plan(store, {}, from_version=1)
    assert decision.code == "persisted_state.migration_failed"
    assert decision.detail["reason"] == "migration_returned_non_mapping"


def test_steps_recorded_before_a_mid_chain_failure_are_preserved() -> None:
    """The journal must show how far the migration got."""

    def _explode(_payload: Mapping[str, object]) -> Mapping[str, object]:
        raise ValueError("second hop")

    store = _store(
        schema_version=3,
        migrations=(
            PersistedStateMigration(1, _bump("a"), "add a"),
            PersistedStateMigration(2, _explode, "explode"),
        ),
    )
    decision = apply_migration_plan(store, {}, from_version=1)
    assert decision.steps == ("add a",)
    assert decision.detail["failed_from_version"] == 2


def test_steps_are_preserved_when_a_later_hop_returns_a_non_mapping() -> None:
    store = _store(
        schema_version=3,
        migrations=(
            PersistedStateMigration(1, _bump("a"), "add a"),
            PersistedStateMigration(2, _returns(7), "wrong"),
        ),
    )
    decision = apply_migration_plan(store, {}, from_version=1)
    assert decision.steps == ("add a",)
    assert decision.detail["failed_to_version"] == 3


# ---------------------------------------------------------------------------
# Decision DTO surface.
# ---------------------------------------------------------------------------


def test_decision_defaults_are_a_bare_refusal() -> None:
    decision = PersistedStateDecision(code="persisted_state.unreadable", store_id="x")
    assert decision.refused and not decision.accepted
    assert decision.from_version is None
    assert decision.to_version is None
    assert decision.payload is None
    assert decision.steps == ()
    assert dict(decision.detail) == {}


def test_accepted_and_refused_are_exact_complements() -> None:
    for code in PERSISTED_STATE_CODES:
        decision = PersistedStateDecision(code=code, store_id="x")
        assert decision.accepted is not decision.refused


# ---------------------------------------------------------------------------
# Store integrations — the registry is actually honoured on disk.
# ---------------------------------------------------------------------------


def test_library_store_stamps_the_envelope_and_reads_it_back(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.library.store import (
        LIBRARY_STORE_SCHEMA_VERSION,
        LibraryRecord,
        LibraryStore,
    )

    store = LibraryStore(tmp_path)
    record = LibraryRecord(
        record_id="abc123",
        device_id="analog_rytm_mk2",
        kit_name="AL02",
        fingerprint="abc123",
        captured_at="2026-09-07T00:00:00Z",
        tags=(),
        payload_hex="f0f7",
    )
    store._write_record(record, overwrite=False)

    on_disk = json.loads((tmp_path / "abc123.json").read_text(encoding="utf-8"))
    assert on_disk[PERSISTED_STATE_VERSION_FIELD] == LIBRARY_STORE_SCHEMA_VERSION
    assert store.get("abc123") == record


def test_library_store_reads_a_pre_envelope_record_as_version_one(tmp_path: Path) -> None:
    """The unversioned files already on operators' disks must still load."""

    from rytm_randomizer.cockpit.library.store import LibraryStore

    legacy = {
        "record_id": "legacy01",
        "device_id": "analog_rytm_mk2",
        "kit_name": "OLD",
        "fingerprint": "legacy01",
        "captured_at": "2026-01-01T00:00:00Z",
        "tags": [],
        "payload_hex": "f0f7",
    }
    (tmp_path / "legacy01.json").write_text(json.dumps(legacy), encoding="utf-8")

    loaded = LibraryStore(tmp_path).get("legacy01")
    assert loaded is not None and loaded.kit_name == "OLD"


def test_library_store_refuses_a_record_from_a_newer_app(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.library.store import LibraryStore

    future = {"record_id": "future01", PERSISTED_STATE_VERSION_FIELD: 99}
    target = tmp_path / "future01.json"
    target.write_text(json.dumps(future), encoding="utf-8")

    reset_metrics()
    with pytest.raises(PersistedStateVersionError) as excinfo:
        LibraryStore(tmp_path).get("future01")

    message = str(excinfo.value)
    assert str(tmp_path) not in message, "the refusal must not leak a filesystem path"
    assert "99" in message
    assert target.read_text(encoding="utf-8") == json.dumps(
        future
    ), "a refusal must leave the operator's bytes exactly as found"
    summary = get_metrics().format_summary()
    assert "library_store:schema_newer_than_app:1" in summary
    reset_metrics()


def test_library_store_still_skips_a_merely_corrupt_record(tmp_path: Path) -> None:
    """Per-file corruption keeps the pre-existing warn-and-skip policy."""

    from rytm_randomizer.cockpit.library.store import LibraryStore

    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "shapeless.json").write_text("[1, 2, 3]", encoding="utf-8")

    assert LibraryStore(tmp_path).list_records() == ()


def test_library_store_skips_a_record_whose_fields_are_invalid(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.library.store import LibraryStore

    (tmp_path / "bad.json").write_text(json.dumps({"record_id": "!!"}), encoding="utf-8")
    assert LibraryStore(tmp_path).list_records() == ()


def test_profile_registry_stamps_the_envelope(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.data import ProfileModel
    from rytm_randomizer.cockpit.profiles.registry import (
        PROFILE_REGISTRY_SCHEMA_VERSION,
        ProfileRegistry,
    )

    registry = ProfileRegistry(tmp_path)
    # Round-trip a built-in scene into a user profile so the test uses a
    # real, fully-populated ProfileModel rather than a hand-built stub.
    seed = {**registry.builtin_scenes[0].to_dict(), "kind": "user"}
    saved = ProfileModel.from_dict(seed)  # type: ignore[arg-type]
    registry.save(saved)

    written = tmp_path / "user" / f"{saved.profile_id}.json"
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload[PERSISTED_STATE_VERSION_FIELD] == PROFILE_REGISTRY_SCHEMA_VERSION
    assert registry.get(saved.profile_id) is not None


def test_profile_registry_refuses_a_profile_from_a_newer_app(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.profiles.registry import ProfileRegistry

    user_dir = tmp_path / "user"
    user_dir.mkdir(parents=True)
    future = {"profile_id": "p1", PERSISTED_STATE_VERSION_FIELD: 42}
    (user_dir / "p1.json").write_text(json.dumps(future), encoding="utf-8")

    reset_metrics()
    with pytest.raises(PersistedStateVersionError) as excinfo:
        ProfileRegistry(tmp_path).list_profiles()
    assert str(tmp_path) not in str(excinfo.value)
    assert "profile_registry:schema_newer_than_app:1" in get_metrics().format_summary()
    reset_metrics()


def test_profile_registry_still_skips_a_malformed_profile(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.profiles.registry import ProfileRegistry

    user_dir = tmp_path / "user"
    user_dir.mkdir(parents=True)
    (user_dir / "junk.json").write_text(json.dumps({"profile_id": "x"}), encoding="utf-8")

    registry = ProfileRegistry(tmp_path)
    assert registry.list_profiles() == registry.builtin_scenes


# ---------------------------------------------------------------------------
# The first-real-bump paths, exercised before the first real bump.
# ---------------------------------------------------------------------------
#
# Both registered stores are at version 1 today, so their ``migrated``
# arms — the ones that call ``record_persisted_state_migration`` — have no
# natural caller yet. They are also the arms that will run, on every
# operator's machine, the first time a store's schema_version is bumped.
# Discovering a bug in them *then* means discovering it in production, so
# each store's seam is driven here with a stubbed decision.


def _migrated_decision(store_id: str, payload: Mapping[str, object]) -> PersistedStateDecision:
    """A ``persisted_state.migrated`` decision shaped as the real policy builds one."""

    return PersistedStateDecision(
        code="persisted_state.migrated",
        store_id=store_id,
        from_version=1,
        to_version=2,
        payload={**payload, PERSISTED_STATE_VERSION_FIELD: 2},
        steps=("probe hop",),
        detail={"reason": "migrated_forward", "steps": 1},
    )


def test_library_store_counts_a_migration_and_still_returns_the_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The library store's ``migrated`` arm: count the hop, hand back the payload."""

    from rytm_randomizer.cockpit.library import store as library_store

    record = {
        "record_id": "mig01",
        "device_id": "analog_rytm_mk2",
        "kit_name": "MIG",
        "fingerprint": "mig01",
        "captured_at": "2026-01-01T00:00:00Z",
        "tags": [],
        "payload_hex": "f0f7",
    }
    (tmp_path / "mig01.json").write_text(json.dumps(record), encoding="utf-8")

    monkeypatch.setattr(
        library_store,
        "classify_payload",
        lambda store_id, _payload, **_kwargs: _migrated_decision(store_id, record),
    )

    reset_metrics()
    loaded = library_store.LibraryStore(tmp_path).get("mig01")
    assert loaded is not None and loaded.kit_name == "MIG"
    assert "library_store:1->2:1" in get_metrics().format_summary()
    reset_metrics()


def test_profile_registry_counts_a_migration_and_still_returns_the_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The profile registry's ``migrated`` arm, same shape as the library store's."""

    from rytm_randomizer.cockpit.data import ProfileModel
    from rytm_randomizer.cockpit.profiles import registry as profile_registry

    registry = profile_registry.ProfileRegistry(tmp_path)
    seed = {**registry.builtin_scenes[0].to_dict(), "kind": "user"}
    saved = ProfileModel.from_dict(cast("dict[str, object]", seed))
    registry.save(saved)

    monkeypatch.setattr(
        profile_registry,
        "classify_payload",
        lambda store_id, _payload, **_kwargs: _migrated_decision(store_id, seed),
    )

    reset_metrics()
    reloaded = profile_registry.ProfileRegistry(tmp_path)
    # ``list_profiles`` (not ``get``) is what forces the disk scan: ``get``
    # answers a ``scene-*`` id from the built-ins and returns before
    # touching the user directory at all.
    assert (
        len(reloaded.list_profiles()) == len(reloaded.builtin_scenes) + 1
    ), "the migrated profile must still appear in the registry"
    assert "profile_registry:1->2:1" in get_metrics().format_summary()
    reset_metrics()


def test_profile_registry_logs_and_skips_a_non_version_refusal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A refusal that is NOT the downgrade case keeps the warn-and-skip policy.

    Only ``schema_newer_than_app`` is fatal to the whole registry — losing
    one unreadable profile must not take the operator's entire profile
    list down, which is the pre-existing per-file policy this change
    deliberately preserved rather than escalated.
    """

    from rytm_randomizer.cockpit.data import ProfileModel
    from rytm_randomizer.cockpit.profiles import registry as profile_registry

    registry = profile_registry.ProfileRegistry(tmp_path)
    seed = {**registry.builtin_scenes[0].to_dict(), "kind": "user"}
    registry.save(ProfileModel.from_dict(cast("dict[str, object]", seed)))

    monkeypatch.setattr(
        profile_registry,
        "classify_payload",
        lambda store_id, _payload, **_kwargs: PersistedStateDecision(
            code="persisted_state.unknown_shape",
            store_id=store_id,
            to_version=1,
            detail={"reason": "payload_not_a_mapping"},
        ),
    )

    reset_metrics()
    reloaded = profile_registry.ProfileRegistry(tmp_path)
    assert reloaded.list_profiles() == reloaded.builtin_scenes
    assert "profile_registry:unknown_shape:1" in get_metrics().format_summary()
    reset_metrics()
