"""Tests for ``rytm_randomizer.cockpit.data.profile_model``.

A ``ProfileModel`` is the deployable intelligence — same shape for built-in
scenes and user-authored profiles, distinguished only by ``kind``. It MUST
round-trip losslessly through ``to_dict`` / ``from_dict`` so the WS-G
export pipeline can produce a portable binary from the same instance the
engine consumes.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from rytm_randomizer.cockpit.data.profile_model import (
    ProfileModel,
    StyleTrait,
    TraitPadWeight,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_trait(name: str = "rolling_low_end", value: float = 0.85) -> StyleTrait:
    return StyleTrait(name=name, value=value)


def _make_pad_weight(
    *, trait: str = "rolling_low_end", pad_id: int = 1, weight: float = 0.6
) -> TraitPadWeight:
    return TraitPadWeight(trait=trait, pad_id=pad_id, weight=weight)


def _make_profile(
    *,
    kind: str = "user",
    name: str = "buzzi",
    traits: tuple[StyleTrait, ...] = (),
    pad_mappings: tuple[TraitPadWeight, ...] = (),
    transition_curve: str = "linear",
) -> ProfileModel:
    return ProfileModel(
        profile_id="01HXY5Q9PJM0123456789ABCD0",
        name=name,
        kind=kind,  # type: ignore[arg-type]
        model_version="1.2.0",
        traits=traits or (_make_trait(),),
        pad_mappings=pad_mappings or (_make_pad_weight(),),
        transition_curve=transition_curve,  # type: ignore[arg-type]
        source_summary="5 sources · 1,243 analyzed signals",
    )


# ---------------------------------------------------------------------------
# StyleTrait
# ---------------------------------------------------------------------------


def test_style_trait_is_frozen() -> None:
    trait = _make_trait()
    with pytest.raises(FrozenInstanceError):
        trait.value = 0.0  # type: ignore[misc]


@pytest.mark.parametrize("value", [-0.01, 1.01, 1.5, -10.0])
def test_style_trait_rejects_value_out_of_unit_range(value: float) -> None:
    with pytest.raises(ValueError, match="value"):
        StyleTrait(name="x", value=value)


@pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
def test_style_trait_accepts_value_inside_unit_range(value: float) -> None:
    trait = StyleTrait(name="rolling", value=value)
    assert trait.value == value


def test_style_trait_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name"):
        StyleTrait(name="", value=0.5)


def test_style_trait_to_dict_round_trip() -> None:
    trait = _make_trait()
    assert StyleTrait.from_dict(trait.to_dict()) == trait


# ---------------------------------------------------------------------------
# TraitPadWeight
# ---------------------------------------------------------------------------


def test_trait_pad_weight_is_frozen() -> None:
    weight = _make_pad_weight()
    with pytest.raises(FrozenInstanceError):
        weight.weight = 0.0  # type: ignore[misc]


@pytest.mark.parametrize("weight", [-0.01, 1.01])
def test_trait_pad_weight_rejects_out_of_range_weight(weight: float) -> None:
    with pytest.raises(ValueError, match="weight"):
        TraitPadWeight(trait="x", pad_id=1, weight=weight)


@pytest.mark.parametrize("pad_id", [0, 13])
def test_trait_pad_weight_rejects_out_of_range_pad_id(pad_id: int) -> None:
    with pytest.raises(ValueError, match="pad_id"):
        TraitPadWeight(trait="x", pad_id=pad_id, weight=0.5)


def test_trait_pad_weight_rejects_empty_trait_name() -> None:
    with pytest.raises(ValueError, match="trait"):
        TraitPadWeight(trait="", pad_id=1, weight=0.5)


def test_trait_pad_weight_to_dict_round_trip() -> None:
    pw = _make_pad_weight()
    assert TraitPadWeight.from_dict(pw.to_dict()) == pw


# ---------------------------------------------------------------------------
# ProfileModel
# ---------------------------------------------------------------------------


def test_profile_model_is_frozen() -> None:
    profile = _make_profile()
    with pytest.raises(FrozenInstanceError):
        profile.name = "kanye"  # type: ignore[misc]


def test_profile_model_traits_are_a_tuple() -> None:
    profile = _make_profile()
    assert isinstance(profile.traits, tuple)
    assert isinstance(profile.pad_mappings, tuple)


@pytest.mark.parametrize("kind", ["scene", "user"])
def test_profile_model_accepts_canonical_kinds(kind: str) -> None:
    profile = _make_profile(kind=kind)
    assert profile.kind == kind


def test_profile_model_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="kind"):
        _make_profile(kind="hybrid")


@pytest.mark.parametrize("curve", ["linear", "progressive", "progressive_w_release"])
def test_profile_model_accepts_canonical_transition_curve(curve: str) -> None:
    profile = _make_profile(transition_curve=curve)
    assert profile.transition_curve == curve


def test_profile_model_rejects_unknown_transition_curve() -> None:
    with pytest.raises(ValueError, match="transition_curve"):
        _make_profile(transition_curve="bezier")


def test_profile_model_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name"):
        _make_profile(name="")


def test_profile_model_rejects_empty_profile_id() -> None:
    with pytest.raises(ValueError, match="profile_id"):
        ProfileModel(
            profile_id="",
            name="x",
            kind="user",
            model_version="1.0.0",
            traits=(),
            pad_mappings=(),
            transition_curve="linear",
            source_summary="",
        )


def test_profile_model_rejects_empty_model_version() -> None:
    with pytest.raises(ValueError, match="model_version"):
        ProfileModel(
            profile_id="01H",
            name="x",
            kind="user",
            model_version="",
            traits=(),
            pad_mappings=(),
            transition_curve="linear",
            source_summary="",
        )


def test_profile_model_rejects_pad_mapping_with_unknown_trait() -> None:
    """Every ``TraitPadWeight.trait`` must reference an existing ``StyleTrait``."""

    with pytest.raises(ValueError, match="unknown trait"):
        _make_profile(
            traits=(_make_trait("rolling_low_end", 0.5),),
            pad_mappings=(_make_pad_weight(trait="metallic_tension"),),
        )


def test_profile_model_to_dict_round_trip_minimal() -> None:
    profile = _make_profile(
        traits=(),
        pad_mappings=(),
    )
    restored = ProfileModel.from_dict(profile.to_dict())
    assert restored == profile


def test_profile_model_to_dict_round_trip_full() -> None:
    profile = _make_profile(
        traits=(_make_trait("rolling_low_end", 0.9), _make_trait("metallic_tension", 0.4)),
        pad_mappings=(
            _make_pad_weight(trait="rolling_low_end", pad_id=1, weight=0.7),
            _make_pad_weight(trait="metallic_tension", pad_id=3, weight=0.3),
        ),
    )
    restored = ProfileModel.from_dict(profile.to_dict())
    assert restored == profile


def test_profile_model_from_dict_rejects_non_iterable_traits() -> None:
    bad = {
        "profile_id": "01H",
        "name": "x",
        "kind": "user",
        "model_version": "1.0.0",
        "traits": {"not": "a list"},
        "pad_mappings": [],
        "transition_curve": "linear",
        "source_summary": "",
    }
    with pytest.raises(TypeError, match="traits"):
        ProfileModel.from_dict(bad)


def test_profile_model_from_dict_rejects_non_iterable_pad_mappings() -> None:
    bad = {
        "profile_id": "01H",
        "name": "x",
        "kind": "user",
        "model_version": "1.0.0",
        "traits": [],
        "pad_mappings": {"not": "a list"},
        "transition_curve": "linear",
        "source_summary": "",
    }
    with pytest.raises(TypeError, match="pad_mappings"):
        ProfileModel.from_dict(bad)


def test_profile_model_to_dict_key_set_is_stable() -> None:
    profile = _make_profile()
    data = profile.to_dict()
    assert set(data.keys()) == {
        "profile_id",
        "name",
        "kind",
        "model_version",
        "traits",
        "pad_mappings",
        "transition_curve",
        "source_summary",
    }
