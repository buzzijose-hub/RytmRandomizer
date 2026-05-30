"""Tests for ``rytm_randomizer.cockpit.profiles.registry``.

``ProfileRegistry`` is the unified view over built-in scenes + on-disk
user profiles. The test surface covers:

* empty registry returns just the built-ins
* save → reload → get round-trip
* multiple user profiles, sorted-by-name listing
* built-ins always present and always first in ``list_profiles``
* ``get`` returns ``None`` for unknown ids
* ``save`` creates ``{profiles_dir}/user/`` if missing
* malformed JSON files are skipped with a logged warning
* ``reload()`` re-reads disk and drops cached entries
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data import ProfileModel, StyleTrait, TraitPadWeight
from rytm_randomizer.cockpit.profiles.builtin import BUILTIN_SCENES
from rytm_randomizer.cockpit.profiles.registry import ProfileRegistry

pytestmark = pytest.mark.fast


@pytest.fixture
def registry_warning_caplog(
    caplog: pytest.LogCaptureFixture,
) -> pytest.LogCaptureFixture:
    """Capture registry warnings even after package logging disables propagation."""

    logger = logging.getLogger("rytm_randomizer.cockpit.profiles.registry")
    logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_user_profile(
    *,
    profile_id: str = "01HXY5Q9PJM0123456789ABCD0",
    name: str = "buzzi",
    trait_name: str = "rolling_low_end",
) -> ProfileModel:
    return ProfileModel(
        profile_id=profile_id,
        name=name,
        kind="user",
        model_version="1.0.0",
        traits=(StyleTrait(name=trait_name, value=0.8),),
        pad_mappings=(TraitPadWeight(trait=trait_name, pad_id=1, weight=0.7),),
        transition_curve="linear",
        source_summary=f"test profile {name}",
    )


# ---------------------------------------------------------------------------
# Construction and built-ins
# ---------------------------------------------------------------------------


def test_construction_does_not_touch_disk(tmp_path: Path) -> None:
    """Building a registry on a nonexistent dir is fine until you read/write."""

    nonexistent = tmp_path / "does_not_exist_yet"
    registry = ProfileRegistry(profiles_dir=nonexistent)
    # No exception, no directory created.
    assert not nonexistent.exists()
    # And built-ins are still listable without any disk interaction.
    assert len(registry.builtin_scenes) == len(BUILTIN_SCENES)


def test_built_in_scenes_property_is_sorted_by_name(tmp_path: Path) -> None:
    registry = ProfileRegistry(profiles_dir=tmp_path)
    scenes = registry.builtin_scenes
    names = [s.name for s in scenes]
    assert names == sorted(names)


def test_built_in_scenes_property_returns_fresh_list(tmp_path: Path) -> None:
    """Mutating the returned list must not affect the registry."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    first = registry.builtin_scenes
    first.clear()
    second = registry.builtin_scenes
    assert len(second) == len(BUILTIN_SCENES)


def test_empty_registry_lists_only_built_ins(tmp_path: Path) -> None:
    registry = ProfileRegistry(profiles_dir=tmp_path)
    profiles = registry.list_profiles()
    assert len(profiles) == len(BUILTIN_SCENES)
    assert all(p.kind == "scene" for p in profiles)


def test_built_ins_are_first_in_list_profiles(tmp_path: Path) -> None:
    """Built-in scenes come first regardless of how many user profiles exist."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    # Save several user profiles with names that would naively sort before
    # some of the scene names.
    for pid, name in [
        ("01HXY5Q9PJM0000000000000A1", "aardvark"),
        ("01HXY5Q9PJM0000000000000A2", "alpha"),
        ("01HXY5Q9PJM0000000000000A3", "zebra"),
    ]:
        registry.save(_make_user_profile(profile_id=pid, name=name))
    profiles = registry.list_profiles()
    n_scenes = len(BUILTIN_SCENES)
    assert all(p.kind == "scene" for p in profiles[:n_scenes])
    assert all(p.kind == "user" for p in profiles[n_scenes:])


# ---------------------------------------------------------------------------
# Save + reload + get
# ---------------------------------------------------------------------------


def test_save_creates_user_subdir_if_missing(tmp_path: Path) -> None:
    """First save() bootstraps {profiles_dir}/user/ even if the parent is empty."""

    profiles_dir = tmp_path / "fresh"
    registry = ProfileRegistry(profiles_dir=profiles_dir)
    assert not profiles_dir.exists()
    profile = _make_user_profile()
    result = registry.save(profile)
    # PR 7 — IH2: save() now returns None (the prior ``-> Path`` was
    # dead surface). The on-disk path is derivable from the profile id.
    assert result is None
    written = profiles_dir / "user" / f"{profile.profile_id}.json"
    assert (profiles_dir / "user").is_dir()
    assert written.exists()
    assert written.parent == profiles_dir / "user"


def test_save_writes_to_path_named_after_profile_id(tmp_path: Path) -> None:
    registry = ProfileRegistry(profiles_dir=tmp_path)
    profile = _make_user_profile(profile_id="01HXY5Q9PJM0000000000000ABC")
    registry.save(profile)
    written = tmp_path / "user" / "01HXY5Q9PJM0000000000000ABC.json"
    assert written.exists()


def test_save_writes_round_trippable_json(tmp_path: Path) -> None:
    registry = ProfileRegistry(profiles_dir=tmp_path)
    profile = _make_user_profile()
    registry.save(profile)
    written = tmp_path / "user" / f"{profile.profile_id}.json"
    raw = json.loads(written.read_text(encoding="utf-8"))
    assert ProfileModel.from_dict(raw) == profile


def test_get_returns_saved_user_profile(tmp_path: Path) -> None:
    registry = ProfileRegistry(profiles_dir=tmp_path)
    profile = _make_user_profile()
    registry.save(profile)
    fetched = registry.get(profile.profile_id)
    assert fetched == profile


def test_get_returns_built_in_scene_by_id(tmp_path: Path) -> None:
    registry = ProfileRegistry(profiles_dir=tmp_path)
    industrial = registry.get("scene-industrial")
    assert industrial is not None
    assert industrial.name == "industrial"
    assert industrial.kind == "scene"


def test_get_returns_none_for_unknown_id(tmp_path: Path) -> None:
    registry = ProfileRegistry(profiles_dir=tmp_path)
    assert registry.get("nope-does-not-exist") is None


def test_save_then_reload_picks_up_persisted_profile(tmp_path: Path) -> None:
    """A new registry pointed at the same dir sees the profile."""

    profile = _make_user_profile()
    registry1 = ProfileRegistry(profiles_dir=tmp_path)
    registry1.save(profile)
    registry2 = ProfileRegistry(profiles_dir=tmp_path)
    fetched = registry2.get(profile.profile_id)
    assert fetched == profile


def test_reload_drops_cached_entries(tmp_path: Path) -> None:
    """Removing a file from disk + reloading must drop the profile."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    profile = _make_user_profile()
    registry.save(profile)
    written = tmp_path / "user" / f"{profile.profile_id}.json"
    assert registry.get(profile.profile_id) == profile
    written.unlink()
    registry.reload()
    assert registry.get(profile.profile_id) is None


def test_save_followed_by_save_overwrites_same_file(tmp_path: Path) -> None:
    # PR 7 — M7: save defaults to overwrite=False so a retried save for
    # an existing profile_id must explicitly opt into replacement.
    registry = ProfileRegistry(profiles_dir=tmp_path)
    profile_a = _make_user_profile(name="buzzi")
    profile_b = _make_user_profile(name="buzzi-revised")
    registry.save(profile_a)
    registry.save(profile_b, overwrite=True)
    # Both writes land in the same file (keyed by profile_id).
    path_a = tmp_path / "user" / f"{profile_a.profile_id}.json"
    path_b = tmp_path / "user" / f"{profile_b.profile_id}.json"
    assert path_a == path_b
    # And the in-memory cache reflects the latest write.
    assert registry.get(profile_a.profile_id) == profile_b


# ---------------------------------------------------------------------------
# Listing semantics
# ---------------------------------------------------------------------------


def test_list_profiles_user_section_is_sorted_by_name(tmp_path: Path) -> None:
    registry = ProfileRegistry(profiles_dir=tmp_path)
    for pid, name in [
        ("01HXY5Q9PJM0000000000000Z01", "zebra"),
        ("01HXY5Q9PJM0000000000000A01", "alpha"),
        ("01HXY5Q9PJM0000000000000M01", "mango"),
    ]:
        registry.save(_make_user_profile(profile_id=pid, name=name))
    profiles = registry.list_profiles()
    n_scenes = len(BUILTIN_SCENES)
    user_names = [p.name for p in profiles[n_scenes:]]
    assert user_names == ["alpha", "mango", "zebra"]


def test_list_profiles_returns_new_list_each_call(tmp_path: Path) -> None:
    registry = ProfileRegistry(profiles_dir=tmp_path)
    a = registry.list_profiles()
    a.clear()
    b = registry.list_profiles()
    assert len(b) == len(BUILTIN_SCENES)


# ---------------------------------------------------------------------------
# Malformed-file tolerance
# ---------------------------------------------------------------------------


def test_malformed_json_file_is_skipped_with_warning(
    tmp_path: Path, registry_warning_caplog: pytest.LogCaptureFixture
) -> None:
    user_dir = tmp_path / "user"
    user_dir.mkdir()
    bad = user_dir / "broken.json"
    bad.write_text("{not valid json", encoding="utf-8")
    registry = ProfileRegistry(profiles_dir=tmp_path)
    with registry_warning_caplog.at_level(logging.WARNING):
        profiles = registry.list_profiles()
    # Built-ins survive; the bad file is silently absent.
    assert len(profiles) == len(BUILTIN_SCENES)
    assert any(
        "malformed profile file" in r.message.lower() for r in registry_warning_caplog.records
    )


def test_non_object_top_level_json_is_skipped_with_warning(
    tmp_path: Path, registry_warning_caplog: pytest.LogCaptureFixture
) -> None:
    user_dir = tmp_path / "user"
    user_dir.mkdir()
    bad = user_dir / "list.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    registry = ProfileRegistry(profiles_dir=tmp_path)
    with registry_warning_caplog.at_level(logging.WARNING):
        profiles = registry.list_profiles()
    assert len(profiles) == len(BUILTIN_SCENES)
    assert any("top-level JSON" in r.message for r in registry_warning_caplog.records)


def test_profile_missing_required_field_is_skipped_with_warning(
    tmp_path: Path, registry_warning_caplog: pytest.LogCaptureFixture
) -> None:
    user_dir = tmp_path / "user"
    user_dir.mkdir()
    bad = user_dir / "missing-name.json"
    bad.write_text(json.dumps({"profile_id": "01H"}), encoding="utf-8")
    registry = ProfileRegistry(profiles_dir=tmp_path)
    with registry_warning_caplog.at_level(logging.WARNING):
        profiles = registry.list_profiles()
    assert len(profiles) == len(BUILTIN_SCENES)
    assert any("invalid profile file" in r.message.lower() for r in registry_warning_caplog.records)


def test_profile_with_invalid_kind_is_skipped_with_warning(
    tmp_path: Path, registry_warning_caplog: pytest.LogCaptureFixture
) -> None:
    user_dir = tmp_path / "user"
    user_dir.mkdir()
    # Construct JSON with all required keys but an invalid ``kind`` literal.
    payload = {
        "profile_id": "01HXY5Q9PJM0000000000000BAD",
        "name": "bad-kind",
        "kind": "hybrid",  # not in {"scene", "user"}
        "model_version": "1.0.0",
        "traits": [],
        "pad_mappings": [],
        "transition_curve": "linear",
        "source_summary": "",
    }
    bad = user_dir / "bad-kind.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")
    registry = ProfileRegistry(profiles_dir=tmp_path)
    with registry_warning_caplog.at_level(logging.WARNING):
        profiles = registry.list_profiles()
    assert len(profiles) == len(BUILTIN_SCENES)
    assert any("invalid profile file" in r.message.lower() for r in registry_warning_caplog.records)


def test_unreadable_file_is_skipped_with_warning(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    registry_warning_caplog: pytest.LogCaptureFixture,
) -> None:
    """A file that raises a non-permission ``OSError`` on read is logged + skipped.

    PR 7 — M6: the classifier in ``_safe_load_profile`` distinguishes
    :class:`PermissionError` (refuse to start — see
    ``test_profile_registry_load_classification.py``) from a generic
    :class:`OSError` (skip with WARNING — this test).
    """

    user_dir = tmp_path / "user"
    user_dir.mkdir()
    target = user_dir / "ghost.json"
    target.write_text("{}", encoding="utf-8")

    real_read_text = Path.read_text

    def boom(self: Path, *args: object, **kwargs: object) -> str:
        if self == target:
            # Bare ``OSError`` without errno=EACCES — exercises the
            # generic-OSError branch (warn + skip), not the
            # ``PermissionError`` branch (raise).
            raise OSError("io error")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", boom)
    registry = ProfileRegistry(profiles_dir=tmp_path)
    with registry_warning_caplog.at_level(logging.WARNING):
        profiles = registry.list_profiles()
    assert len(profiles) == len(BUILTIN_SCENES)
    assert any(
        "unreadable profile file" in r.message.lower() for r in registry_warning_caplog.records
    )


def test_good_and_bad_files_coexist(
    tmp_path: Path,
    registry_warning_caplog: pytest.LogCaptureFixture,
) -> None:
    """Good profiles still load when sibling files are malformed."""

    user_dir = tmp_path / "user"
    user_dir.mkdir()
    (user_dir / "broken.json").write_text("not json", encoding="utf-8")
    good = _make_user_profile(profile_id="01HXY5Q9PJM0000000000000GOOD")
    (user_dir / f"{good.profile_id}.json").write_text(json.dumps(good.to_dict()), encoding="utf-8")
    registry = ProfileRegistry(profiles_dir=tmp_path)
    with registry_warning_caplog.at_level(logging.WARNING):
        profiles = registry.list_profiles()
    user_profiles = [p for p in profiles if p.kind == "user"]
    assert user_profiles == [good]


# ---------------------------------------------------------------------------
# Idempotence / lazy loading
# ---------------------------------------------------------------------------


def test_repeated_list_profiles_does_not_reread_disk(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Lazy load: second list_profiles() must not call _scan_user_profiles."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    registry.list_profiles()  # primes the cache

    real_scan = registry._scan_user_profiles
    calls: list[int] = []

    def counting_scan() -> dict[str, ProfileModel]:
        calls.append(1)
        return real_scan()

    monkeypatch.setattr(registry, "_scan_user_profiles", counting_scan)
    registry.list_profiles()
    registry.list_profiles()
    assert calls == []


def test_get_built_in_short_circuits_disk_scan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """get() on a known built-in must not trigger a disk scan."""

    registry = ProfileRegistry(profiles_dir=tmp_path)

    def explode() -> dict[str, ProfileModel]:
        raise AssertionError("disk scan should not have happened")

    monkeypatch.setattr(registry, "_scan_user_profiles", explode)
    fetched = registry.get("scene-rolling")
    assert fetched is not None and fetched.name == "rolling"


def test_reload_after_external_write_picks_up_new_file(tmp_path: Path) -> None:
    """A second process writing into the dir is visible after reload()."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    registry.list_profiles()  # primes empty cache
    user_dir = tmp_path / "user"
    user_dir.mkdir(exist_ok=True)
    profile = _make_user_profile()
    (user_dir / f"{profile.profile_id}.json").write_text(
        json.dumps(profile.to_dict()), encoding="utf-8"
    )
    # Without reload, get() does NOT see it (cache was primed).
    assert registry.get(profile.profile_id) is None
    registry.reload()
    assert registry.get(profile.profile_id) == profile
