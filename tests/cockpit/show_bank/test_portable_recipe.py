"""Portable recipes preserve authored intelligence without hardware authority."""

from __future__ import annotations

from dataclasses import replace

import pytest

from rytm_randomizer.cockpit.data import ProfileModel
from rytm_randomizer.cockpit.data.show_bank import (
    A4_NATIVE_MUTATION_ALGORITHM,
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    ShowBank,
    ShowKitRecipe,
    ShowKitScope,
)

from .conftest import build_show_bank_harness

pytestmark = pytest.mark.fast


def test_portable_recipe_round_trip_preserves_profile_scope_and_algorithm(tmp_path) -> None:
    harness = build_show_bank_harness(tmp_path)
    recipe = ShowKitRecipe(
        profile_id=harness.profile.profile_id,
        depth_preset="small",
        depth=0.1,
        seed=123,
        rytm_scope=ShowKitScope(RYTM_SHOW_KIT_DEVICE_ID, (2,), (1,)),
        analog_four_scope=ShowKitScope(A4_SHOW_KIT_DEVICE_ID, (3,), (1, 2, 4)),
        profile=harness.profile,
        a4_algorithm=A4_NATIVE_MUTATION_ALGORITHM,
    )
    assert ShowKitRecipe.from_dict(recipe.to_dict()) == recipe
    assert recipe.profile == harness.profile
    assert recipe.profile is not harness.profile
    assert recipe.to_dict()["profile"] == harness.profile.to_dict()


def test_legacy_recipe_keeps_six_key_wire_form_without_fabricated_profile(tmp_path) -> None:
    harness = build_show_bank_harness(tmp_path)
    recipe = ShowKitRecipe(
        harness.profile.profile_id,
        "small",
        0.1,
        123,
        ShowKitScope(RYTM_SHOW_KIT_DEVICE_ID),
        ShowKitScope(A4_SHOW_KIT_DEVICE_ID),
    )
    assert len(recipe.to_dict()) == 6
    assert ShowKitRecipe.from_dict(recipe.to_dict()) == recipe
    assert recipe.profile is None
    with pytest.raises(ValueError, match="retained profile"):
        replace(recipe, a4_algorithm=A4_NATIVE_MUTATION_ALGORITHM)
    with pytest.raises(ValueError, match="unsupported A4"):
        replace(recipe, a4_algorithm="unverified-v99")
    with pytest.raises(ValueError, match="identity"):
        replace(recipe, profile=replace(harness.profile, profile_id="other"))
    with pytest.raises(ValueError, match="immutable"):
        replace(recipe, profile={})


@pytest.mark.parametrize("version", ["show-bank-v1", "show-bank-v2"])
def test_legacy_bank_read_is_explicit_and_does_not_rewrite_input_mapping(tmp_path, version) -> None:
    harness = build_show_bank_harness(tmp_path)
    raw = harness.workspace.bank(harness.bank_id).to_dict()
    raw["schema_version"] = version
    decoded = ShowBank.from_dict(raw)
    assert decoded.schema_version == "show-bank-v3"
    assert raw["schema_version"] == version
    raw["schema_version"] = "show-bank-v99"
    with pytest.raises(ValueError, match="schema"):
        ShowBank.from_dict(raw)


@pytest.mark.parametrize("corruption", ["unknown", "bool-id", "nan", "inf", "extra-trait"])
def test_strict_profile_refuses_corruption_without_scalar_coercion(tmp_path, corruption) -> None:
    raw = build_show_bank_harness(tmp_path).profile.to_dict()
    if corruption == "unknown":
        raw["unknown"] = True
    elif corruption == "bool-id":
        raw["pad_mappings"][0]["pad_id"] = True
    elif corruption == "nan":
        raw["traits"][0]["value"] = float("nan")
    elif corruption == "inf":
        raw["pad_mappings"][0]["weight"] = float("inf")
    else:
        raw["traits"][0]["extra"] = True
    with pytest.raises(ValueError):
        ProfileModel.from_strict_dict(raw)
