"""Tests for ``rytm_randomizer.guardrails.store`` (WS-W Layer 3 persistence).

The store must:

* Save a profile to JSON, then load it back to a content-equal profile
  (round-trip with hash preservation).
* Reject illegal state transitions in :py:meth:`promote` and accept legal
  ones.
* :py:meth:`list_profiles` returns sorted, deduplicated, only-schema-version-matching
  files (filtering anything else out).
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from rytm_randomizer.guardrails import (
    LEGAL_STATE_TRANSITIONS,
    SCHEMA_VERSION,
    Confidence,
    GuardrailBound,
    GuardrailClass,
    GuardrailProfile,
    IllegalStateTransitionError,
    MusicalCharacter,
    ProfileState,
    ProfileStore,
    Provenance,
    RoleAssignment,
    RoleMapping,
    SceneGuardrail,
    SourceType,
    compute_content_hash,
    validate,
)
from rytm_randomizer.observability.errors import StateError

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _draft() -> GuardrailProfile:
    return GuardrailProfile(
        provenance=Provenance(
            profile_name="rolling-hypnotic",
            source_type=SourceType.SINGLE_TRACK,
            confidence=Confidence.HIGH,
            feature_report_hash="feat-hash-aaaa",
            derived_at="2026-05-14T12:00:00Z",
        ),
        character=MusicalCharacter(
            style_tags=("rolling", "hypnotic", "dark"),
            bpm_range=(128, 132),
            energy_profile="steady",
            density_profile="dense",
            musical_findings={"tempo_groove": "rock-steady"},
        ),
        role_mapping=RoleMapping(
            assignments={
                1: RoleAssignment(role="kick", mutation_direction="tighten"),
                2: RoleAssignment(role="snare", mutation_direction="open-mid"),
                3: RoleAssignment(role="bass", mutation_direction="filter-motion"),
                4: RoleAssignment(role="accent", mutation_direction="modulate-wide"),
            }
        ),
        bounds=(
            GuardrailBound(
                pad=1,
                parameter="FLT Frequency",
                low=25,
                high=33,
                guardrail_class=GuardrailClass.LIVE_SAFE,
                direction="tighten",
            ),
        ),
        locked_default=("track_volume",),
        forbidden=("kit_clear",),
        scenes=(
            SceneGuardrail(
                scene_key="A1",
                pads_allowed=(1, 2, 3, 4),
                mutation_depth="moderate",
                risk_class=GuardrailClass.LIVE_SAFE,
                locked_roles=("kick",),
            ),
        ),
        state=ProfileState.DRAFT,
        schema_version=SCHEMA_VERSION,
        content_hash="",
    )


def _validated() -> GuardrailProfile:
    return validate(_draft())


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_save_then_load_round_trips_the_profile(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()

    saved_path = store.save(profile)
    loaded = store.load(saved_path)

    assert loaded == profile
    assert loaded.content_hash == profile.content_hash


def test_save_creates_profiles_directory_on_demand(tmp_path):
    nested = tmp_path / "deep" / "nested" / "profiles"
    assert not nested.exists()

    store = ProfileStore(profiles_dir=nested)
    store.save(_validated())

    assert nested.is_dir()


def test_save_filename_includes_profile_name_and_content_hash_prefix(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()

    path = store.save(profile)

    assert path.name.startswith("rolling-hypnotic-")
    assert path.suffix == ".json"
    # Content hash prefix in filename matches the profile's actual hash.
    assert profile.content_hash[:8] in path.name


def test_save_rejects_profile_without_content_hash(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    bad = dataclasses.replace(_validated(), content_hash="")

    with pytest.raises(StateError):
        store.save(bad)


def test_load_rejects_unparseable_json(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    bad = tmp_path / "bad-deadbeef.json"
    bad.write_text("this is not JSON", encoding="utf-8")

    with pytest.raises(StateError):
        store.load(bad)


def test_load_rejects_top_level_non_object(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    bad = tmp_path / "bad-deadbeef.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(StateError):
        store.load(bad)


def test_load_rejects_hash_mismatch(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    # Tamper with the on-disk file: change the profile_name without
    # recomputing the hash. The next load must catch the integrity
    # violation.
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["provenance"]["profile_name"] = "TAMPERED"
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError) as exc:
        store.load(path)
    assert "content_hash" in str(exc.value)


# ---------------------------------------------------------------------------
# Promote -- state machine
# ---------------------------------------------------------------------------


def test_promote_legal_transitions_succeed():
    profile = _validated()  # state=VALIDATED

    studio = ProfileStore.promote(profile, ProfileState.STUDIO_TESTED)
    assert studio.state is ProfileState.STUDIO_TESTED

    live = ProfileStore.promote(studio, ProfileState.LIVE_APPROVED)
    assert live.state is ProfileState.LIVE_APPROVED

    archived = ProfileStore.promote(live, ProfileState.ARCHIVED)
    assert archived.state is ProfileState.ARCHIVED


def test_promote_recomputes_content_hash_on_state_flip():
    profile = _validated()
    promoted = ProfileStore.promote(profile, ProfileState.STUDIO_TESTED)

    assert promoted.content_hash != profile.content_hash
    assert promoted.content_hash == compute_content_hash(
        dataclasses.replace(promoted, content_hash="")
    )


def test_promote_rejects_illegal_transition_draft_to_live():
    draft = _draft()  # state=DRAFT
    with pytest.raises(IllegalStateTransitionError) as exc:
        ProfileStore.promote(draft, ProfileState.LIVE_APPROVED)
    ctx = exc.value.context
    assert ctx["from_state"] == "DRAFT"
    assert ctx["to_state"] == "LIVE_APPROVED"


def test_promote_rejects_transition_out_of_archived():
    profile = dataclasses.replace(_validated(), state=ProfileState.ARCHIVED)
    with pytest.raises(IllegalStateTransitionError):
        ProfileStore.promote(profile, ProfileState.VALIDATED)


def test_promote_rejects_transition_from_validated_to_live_directly():
    # Spec says VALIDATED -> STUDIO_TESTED -> LIVE_APPROVED. Direct hop is
    # forbidden.
    validated = _validated()
    with pytest.raises(IllegalStateTransitionError):
        ProfileStore.promote(validated, ProfileState.LIVE_APPROVED)


def test_promote_rejected_back_to_draft():
    profile = dataclasses.replace(_validated(), state=ProfileState.REJECTED)
    back = ProfileStore.promote(profile, ProfileState.DRAFT)
    assert back.state is ProfileState.DRAFT


def test_legal_state_transitions_cover_every_state():
    """Every ProfileState appears as a key in the transition table.

    Without this guarantee, ``ProfileStore.promote`` from an "unknown" state
    would silently fail rather than report the illegal transition. The
    fallback path in ``promote`` (``allowed = ... or frozenset()``) protects
    us either way, but the table should still be complete.
    """

    assert set(ProfileState) == set(LEGAL_STATE_TRANSITIONS)


# ---------------------------------------------------------------------------
# list_profiles
# ---------------------------------------------------------------------------


def test_list_profiles_returns_only_matching_schema_version(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    saved = store.save(profile)

    # Drop a legacy file with a different schema_version into the dir.
    legacy_payload = json.loads(saved.read_text(encoding="utf-8"))
    legacy_payload["schema_version"] = "0.0"
    legacy = tmp_path / "legacy-cafebabe.json"
    legacy.write_text(
        json.dumps(legacy_payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    results = store.list_profiles()
    assert saved in results
    assert legacy not in results


def test_list_profiles_ignores_unrelated_files(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    store.save(_validated())

    # Place a file that does not match the profile filename pattern.
    (tmp_path / "README.txt").write_text("not a profile", encoding="utf-8")
    (tmp_path / "junk.json").write_text("{}", encoding="utf-8")

    results = store.list_profiles()
    assert all(p.suffix == ".json" for p in results)
    for p in results:
        assert "-" in p.stem
        assert len(p.stem.rsplit("-", 1)[1]) == 8


def test_list_profiles_is_sorted(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile_a = _validated()
    profile_b_draft = dataclasses.replace(
        _draft(),
        provenance=dataclasses.replace(_draft().provenance, profile_name="aaa-other"),
    )
    profile_b = validate(profile_b_draft)

    store.save(profile_a)
    store.save(profile_b)

    results = store.list_profiles()
    names = [p.name for p in results]
    assert names == sorted(names)


def test_list_profiles_returns_empty_when_directory_missing(tmp_path):
    missing = tmp_path / "does-not-exist"
    store = ProfileStore(profiles_dir=missing)

    assert store.list_profiles() == []


def test_list_profiles_skips_unparseable_files(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    store.save(_validated())
    (tmp_path / "broken-12345678.json").write_text("{ not json", encoding="utf-8")

    # broken file is filtered; the good one is returned.
    results = store.list_profiles()
    assert len(results) == 1


def test_list_profiles_skips_files_with_non_object_payload(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    store.save(_validated())
    (tmp_path / "arr-12345678.json").write_text("[1, 2, 3]", encoding="utf-8")

    results = store.list_profiles()
    # The array file matches the regex but its payload is not an object.
    assert len(results) == 1


def test_list_profiles_skips_subdirectories(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    store.save(_validated())
    nested = tmp_path / "nested-12345678.json"
    nested.mkdir()

    results = store.list_profiles()
    assert nested not in results


# ---------------------------------------------------------------------------
# Profile filename hygiene
# ---------------------------------------------------------------------------


def test_save_sanitizes_profile_name_for_filename(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    weird = _draft()
    weird = dataclasses.replace(
        weird,
        provenance=dataclasses.replace(weird.provenance, profile_name="rolling/hypnotic v1"),
    )
    validated = validate(weird)

    path = store.save(validated)
    # Slashes and spaces sanitized to underscores; round trip still works.
    assert "/" not in path.name
    assert " " not in path.name


# ---------------------------------------------------------------------------
# Public surface coverage
# ---------------------------------------------------------------------------


def test_default_profiles_dir_is_under_user_home():
    from rytm_randomizer.guardrails.store import DEFAULT_PROFILES_DIR

    home_str = str(DEFAULT_PROFILES_DIR.expanduser())
    assert ".rytm-randomizer" in home_str
    assert "profiles" in home_str


def test_profiles_dir_property_returns_configured_path(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    assert store.profiles_dir == tmp_path


def test_store_uses_default_dir_when_none_passed():
    # Don't actually save; just confirm the property points at DEFAULT.
    from rytm_randomizer.guardrails.store import DEFAULT_PROFILES_DIR

    store = ProfileStore()
    assert store.profiles_dir == DEFAULT_PROFILES_DIR


# ---------------------------------------------------------------------------
# Coerce-error coverage (each missing/wrong-typed field raises)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key,replacement",
    [
        ("schema_version", 1),
        ("state", 5),
        ("locked_default", "not a list"),
        ("forbidden", 42),
    ],
)
def test_load_reports_field_specific_errors(tmp_path, key, replacement):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[key] = replacement
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


def test_load_reports_nested_field_errors(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    # Drop the bpm_range list -- coercion path must raise.
    payload["character"]["bpm_range"] = "not a tuple"
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


def test_load_rejects_non_object_provenance(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["provenance"] = "should be object"
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


def test_load_rejects_bound_with_wrong_types(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["bounds"][0]["low"] = "twenty"  # not int
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


def test_load_rejects_role_mapping_with_non_object_entry(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["role_mapping"]["assignments"]["1"] = "should be object"
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


def test_load_rejects_string_list_with_non_string(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["locked_default"] = ["valid", 123, "another"]
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


def test_load_rejects_int_list_with_non_int(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["character"]["bpm_range"] = [120, "fast"]
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


def test_load_rejects_character_with_non_object_findings(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["character"]["musical_findings"] = ["not", "an", "object"]
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


def test_load_rejects_non_object_character(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["character"] = "should be object"
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


def test_load_rejects_non_object_role_mapping(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["role_mapping"] = "should be object"
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


def test_load_rejects_non_list_bounds(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["bounds"] = "should be list"
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


def test_load_rejects_non_list_scenes(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["scenes"] = "should be list"
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


def test_load_rejects_non_object_role_mapping_assignments(tmp_path):
    store = ProfileStore(profiles_dir=tmp_path)
    profile = _validated()
    path = store.save(profile)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["role_mapping"]["assignments"] = "not a mapping"
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(StateError):
        store.load(path)


# ---------------------------------------------------------------------------
# Logging is wired (smoke)
# ---------------------------------------------------------------------------


def test_to_json_primitive_rejects_unsupported_value():
    """Cover the fall-through TypeError in ``_to_json_primitive``."""

    from rytm_randomizer.guardrails.store import _to_json_primitive

    with pytest.raises(TypeError):
        _to_json_primitive(object())


def test_save_emits_a_log_record(tmp_path):
    # The package logger has ``propagate = False`` once configured -- attach
    # a probe handler directly so a log record from ``store.save`` is
    # observable here.
    import logging

    from rytm_randomizer.guardrails.store import _logger

    records: list[logging.LogRecord] = []
    handler = logging.Handler()
    handler.emit = records.append  # type: ignore[method-assign]
    _logger.addHandler(handler)
    try:
        _logger.setLevel(logging.INFO)
        ProfileStore(profiles_dir=tmp_path).save(_validated())
    finally:
        _logger.removeHandler(handler)

    assert any("guardrails.store.save" in rec.getMessage() for rec in records)


def test_promote_emits_a_log_record():
    import logging

    from rytm_randomizer.guardrails.store import _logger

    records: list[logging.LogRecord] = []
    handler = logging.Handler()
    handler.emit = records.append  # type: ignore[method-assign]
    _logger.addHandler(handler)
    try:
        _logger.setLevel(logging.INFO)
        ProfileStore.promote(_validated(), ProfileState.STUDIO_TESTED)
    finally:
        _logger.removeHandler(handler)

    assert any("guardrails.store.promote" in rec.getMessage() for rec in records)
