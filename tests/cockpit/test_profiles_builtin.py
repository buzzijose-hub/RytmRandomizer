"""Tests for ``rytm_randomizer.cockpit.profiles.builtin``.

The seven built-in scenes are the cockpit's bootstrap profile catalog.
They MUST have deterministic ids (no ULID drift across runs), be
classified as ``kind="scene"``, validate as well-formed ``ProfileModel``
instances, and round-trip through ``to_dict``/``from_dict``.
"""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.data import ProfileModel
from rytm_randomizer.cockpit.profiles.builtin import BUILTIN_SCENES

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Catalog shape
# ---------------------------------------------------------------------------


_EXPECTED_NAMES = frozenset(
    {
        "industrial",
        "hypnotic",
        "garage",
        "peak_time",
        "rolling",
        "birmingham",
        "drone",
    }
)


def test_seven_built_in_scenes() -> None:
    assert len(BUILTIN_SCENES) == 7


def test_built_in_names_are_the_expected_seven() -> None:
    assert {s.name for s in BUILTIN_SCENES} == _EXPECTED_NAMES


def test_built_in_collection_is_a_tuple() -> None:
    """Immutability at the container level — no append() at runtime."""

    assert isinstance(BUILTIN_SCENES, tuple)


def test_built_in_collection_is_sorted_by_name() -> None:
    names = [s.name for s in BUILTIN_SCENES]
    assert names == sorted(names)


# ---------------------------------------------------------------------------
# Per-scene invariants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scene", BUILTIN_SCENES, ids=lambda s: s.name)
def test_built_in_scene_kind_is_scene(scene: ProfileModel) -> None:
    assert scene.kind == "scene"


@pytest.mark.parametrize("scene", BUILTIN_SCENES, ids=lambda s: s.name)
def test_built_in_scene_id_is_deterministic(scene: ProfileModel) -> None:
    """``profile_id`` must be ``scene-<name>`` — no ULIDs."""

    assert scene.profile_id == f"scene-{scene.name}"


@pytest.mark.parametrize("scene", BUILTIN_SCENES, ids=lambda s: s.name)
def test_built_in_scene_has_traits(scene: ProfileModel) -> None:
    assert len(scene.traits) > 0


@pytest.mark.parametrize("scene", BUILTIN_SCENES, ids=lambda s: s.name)
def test_built_in_scene_has_pad_mappings(scene: ProfileModel) -> None:
    assert len(scene.pad_mappings) > 0


@pytest.mark.parametrize("scene", BUILTIN_SCENES, ids=lambda s: s.name)
def test_built_in_scene_pad_mappings_cover_4_pads(scene: ProfileModel) -> None:
    """Every scene targets the canonical 4-pad reference layout."""

    pad_ids = {m.pad_id for m in scene.pad_mappings}
    assert pad_ids == {1, 2, 3, 4}


@pytest.mark.parametrize("scene", BUILTIN_SCENES, ids=lambda s: s.name)
def test_built_in_scene_round_trips_through_dict(scene: ProfileModel) -> None:
    restored = ProfileModel.from_dict(scene.to_dict())
    assert restored == scene


@pytest.mark.parametrize("scene", BUILTIN_SCENES, ids=lambda s: s.name)
def test_built_in_scene_model_version_is_non_empty(scene: ProfileModel) -> None:
    assert scene.model_version


def test_built_in_scene_ids_are_unique() -> None:
    ids = [s.profile_id for s in BUILTIN_SCENES]
    assert len(set(ids)) == len(ids)


# ---------------------------------------------------------------------------
# Curated trait selections — locks the "rough character" per spec
# ---------------------------------------------------------------------------


def _scene_by_name(name: str) -> ProfileModel:
    for scene in BUILTIN_SCENES:
        if scene.name == name:
            return scene
    raise AssertionError(f"missing built-in scene {name!r}")


def test_industrial_carries_metallic_tension() -> None:
    scene = _scene_by_name("industrial")
    trait_names = {t.name for t in scene.traits}
    assert "metallic_tension" in trait_names


def test_hypnotic_carries_dry_space() -> None:
    scene = _scene_by_name("hypnotic")
    trait_names = {t.name for t in scene.traits}
    assert "dry_space" in trait_names


def test_garage_carries_swing_emphasis() -> None:
    scene = _scene_by_name("garage")
    trait_names = {t.name for t in scene.traits}
    assert "swing_emphasis" in trait_names


def test_peak_time_uses_linear_transition_curve() -> None:
    assert _scene_by_name("peak_time").transition_curve == "linear"


def test_rolling_carries_sub_bass() -> None:
    scene = _scene_by_name("rolling")
    trait_names = {t.name for t in scene.traits}
    assert "sub_bass" in trait_names


def test_birmingham_uses_linear_transition_curve() -> None:
    assert _scene_by_name("birmingham").transition_curve == "linear"


def test_drone_uses_progressive_w_release_transition_curve() -> None:
    assert _scene_by_name("drone").transition_curve == "progressive_w_release"
