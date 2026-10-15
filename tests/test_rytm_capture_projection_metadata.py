"""Versioned recipe metadata preserves legacy candidate identity serialization."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from typing import cast, get_args

import pytest

from rytm_randomizer.cockpit.data.profile_model import ProfileModel
from rytm_randomizer.cockpit.data.show_bank import (
    A4_LEGACY_MUTATION_ALGORITHM,
    A4_NATIVE_MUTATION_ALGORITHM,
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    ShowKitRecipe,
    ShowKitScope,
)
from rytm_randomizer.data.analog_rytm_midi import (
    RYTM_CAPTURE_PROJECTION_V1,
    RYTM_CAPTURE_PROJECTION_V2,
    RYTM_CAPTURE_PROJECTIONS,
    RytmCaptureProjection,
)

pytestmark = pytest.mark.fast


@pytest.fixture(params=[None, A4_LEGACY_MUTATION_ALGORITHM, A4_NATIVE_MUTATION_ALGORITHM])
def recipe(request: pytest.FixtureRequest) -> ShowKitRecipe:
    algorithm = cast(str | None, request.param)
    profile = (
        None
        if algorithm is None
        else ProfileModel(
            profile_id="projection-profile",
            name="Projection profile",
            kind="user",
            model_version="1",
            traits=(),
            pad_mappings=(),
            transition_curve="linear",
            source_summary="Offline metadata test",
        )
    )
    return ShowKitRecipe(
        profile_id="projection-profile",
        depth_preset="small",
        depth=0.25,
        seed=613,
        rytm_scope=ShowKitScope(RYTM_SHOW_KIT_DEVICE_ID),
        analog_four_scope=ShowKitScope(A4_SHOW_KIT_DEVICE_ID),
        profile=profile,
        a4_algorithm=algorithm or A4_LEGACY_MUTATION_ALGORITHM,
    )


def test_projection_versions_are_an_immutable_literal_catalog() -> None:
    assert RYTM_CAPTURE_PROJECTION_V1 == "captured-cc7-v1"
    assert RYTM_CAPTURE_PROJECTION_V2 == "captured-cc7-sample-bit-v2"
    assert get_args(RytmCaptureProjection) == RYTM_CAPTURE_PROJECTIONS
    assert isinstance(RYTM_CAPTURE_PROJECTIONS, tuple)


def test_unversioned_legacy_round_trip_is_exact_and_does_not_promote(recipe: ShowKitRecipe) -> None:
    legacy: dict[str, object] = dict(recipe.to_dict())
    del legacy["rytm_projection"]
    original = deepcopy(legacy)
    original_bytes = json.dumps(legacy, separators=(",", ":"))

    restored = ShowKitRecipe.from_dict(legacy)

    assert restored.rytm_projection == RYTM_CAPTURE_PROJECTION_V1
    assert restored.to_dict() == original
    assert json.dumps(restored.to_dict(), separators=(",", ":")) == original_bytes
    assert legacy == original
    assert ("profile" in legacy) == (recipe.profile is not None)
    assert ("a4_algorithm" in legacy) == (recipe.profile is not None)


def test_new_recipe_defaults_to_explicit_v2_and_round_trips(recipe: ShowKitRecipe) -> None:
    assert recipe.rytm_projection == RYTM_CAPTURE_PROJECTION_V2
    raw = recipe.to_dict()
    assert raw.get("rytm_projection") == RYTM_CAPTURE_PROJECTION_V2
    assert ShowKitRecipe.from_dict(raw) == recipe
    assert ShowKitRecipe.from_dict(raw).to_dict() == raw
    assert ("profile" in raw) == (recipe.profile is not None)
    assert ("a4_algorithm" in raw) == (recipe.profile is not None)


def test_explicit_v1_normalizes_to_legacy_wire_shape(recipe: ShowKitRecipe) -> None:
    raw: dict[str, object] = dict(recipe.to_dict())
    raw["rytm_projection"] = RYTM_CAPTURE_PROJECTION_V1
    restored = ShowKitRecipe.from_dict(raw)
    assert restored == replace(recipe, rytm_projection=RYTM_CAPTURE_PROJECTION_V1)
    assert restored.to_dict() == {
        key: value for key, value in raw.items() if key != "rytm_projection"
    }
    assert raw["rytm_projection"] == RYTM_CAPTURE_PROJECTION_V1


@pytest.mark.parametrize("value", [True, False, 1, 0, "unknown-v99", [], {}, None])
def test_invalid_projection_rejected_by_constructor_and_reader(
    recipe: ShowKitRecipe, value: object
) -> None:
    with pytest.raises(ValueError, match="projection"):
        replace(recipe, rytm_projection=cast(RytmCaptureProjection, value))
    raw: dict[str, object] = dict(recipe.to_dict())
    raw["rytm_projection"] = value
    original = deepcopy(raw)
    with pytest.raises(ValueError, match="projection"):
        ShowKitRecipe.from_dict(raw)
    assert raw == original


def test_projection_field_is_frozen(recipe: ShowKitRecipe) -> None:
    with pytest.raises(FrozenInstanceError):
        recipe.__setattr__("rytm_projection", RYTM_CAPTURE_PROJECTION_V1)
    assert recipe.rytm_projection == RYTM_CAPTURE_PROJECTION_V2


def test_projection_does_not_relax_other_optional_keys(recipe: ShowKitRecipe) -> None:
    raw: dict[str, object] = dict(recipe.to_dict())
    if recipe.profile is None:
        raw["a4_algorithm"] = A4_LEGACY_MUTATION_ALGORITHM
    else:
        del raw["a4_algorithm"]
    with pytest.raises(ValueError):
        ShowKitRecipe.from_dict(raw)
