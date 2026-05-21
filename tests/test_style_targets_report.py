import pytest

from rytm_randomizer.data.style_profiles import STYLE_PROFILES

pytestmark = pytest.mark.fast


def test_style_target_vectors_cover_every_style_profile():
    from rytm_randomizer.data.style_targets import STYLE_TARGET_VECTORS

    assert set(STYLE_TARGET_VECTORS) == set(STYLE_PROFILES)


def test_style_target_vector_axes_are_stable_and_bounded():
    from rytm_randomizer.data.style_targets import (
        STYLE_TARGET_VECTOR_AXES,
        STYLE_TARGET_VECTORS,
    )

    assert STYLE_TARGET_VECTOR_AXES == (
        "low_end_weight",
        "transient_density",
        "attack_sharpness",
        "decay_tail",
        "darkness",
        "metallicity",
        "noise_grit",
        "drive_pressure",
        "space_depth",
        "motion_amount",
        "repetition_hypnosis",
        "percussive_density",
        "tonal_center_weight",
        "industrial_edge",
        "minimal_restraint",
        "warehouse_intensity",
    )

    for key, vector in STYLE_TARGET_VECTORS.items():
        assert vector.key == key
        mapping = vector.as_mapping()
        assert tuple(mapping) == STYLE_TARGET_VECTOR_AXES
        for axis in STYLE_TARGET_VECTOR_AXES:
            assert 0 <= mapping[axis] <= 100


def test_style_target_vectors_encode_expected_musical_intent():
    from rytm_randomizer.data.style_targets import STYLE_TARGET_VECTORS

    birmingham = STYLE_TARGET_VECTORS["birmingham_pressure"]
    detroit = STYLE_TARGET_VECTORS["detroit_minimal"]
    industrial = STYLE_TARGET_VECTORS["industrial_dark"]
    hardgroove = STYLE_TARGET_VECTORS["hardgroove_percussive"]

    assert birmingham.drive_pressure >= 85
    assert industrial.noise_grit == 100
    assert hardgroove.percussive_density >= 85
    assert detroit.minimal_restraint >= 85
    assert detroit.space_depth < industrial.space_depth
