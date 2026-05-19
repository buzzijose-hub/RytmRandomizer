from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast

from rytm_randomizer.data.rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES,
    RYTM_MACHINE_PROFILES_BY_KEY,
    RYTM_PAD_CAPABILITIES,
    allowed_machine_profiles_for_pad,
    get_rytm_machine_profile,
    get_rytm_pad_capability,
    is_machine_allowed_on_pad,
)

EXPECTED_MACHINE_CC15_VALUES = {
    "bd_hard": 0,
    "bd_classic": 1,
    "sd_hard": 2,
    "sd_classic": 3,
    "rs_hard": 4,
    "rs_classic": 5,
    "cp_classic": 6,
    "bt_classic": 7,
    "xt_classic": 8,
    "ch_classic": 9,
    "oh_classic": 10,
    "cy_classic": 11,
    "cb_classic": 12,
    "bd_fm": 13,
    "sd_fm": 14,
    "ut_noise": 15,
    "ut_impulse": 16,
    "ch_metallic": 17,
    "oh_metallic": 18,
    "cy_metallic": 19,
    "cb_metallic": 20,
    "bd_plastic": 21,
    "bd_silky": 22,
    "sd_natural": 23,
    "hh_basic": 24,
    "cy_ride": 25,
    "bd_sharp": 26,
    "dual_vco": 28,
    "sy_chip": 29,
    "bd_acoustic": 30,
    "sd_acoustic": 31,
    "sy_raw": 32,
    "hh_lab": 33,
}


def test_machine_and_pad_catalog_sizes() -> None:
    assert len(RYTM_MACHINE_PROFILES) == 33
    assert len(RYTM_PAD_CAPABILITIES) == 12


def test_total_legal_pad_machine_slots() -> None:
    assert sum(len(pad.allowed_machine_keys) for pad in RYTM_PAD_CAPABILITIES) == 116


def test_all_pad_machine_references_resolve_and_values_are_midi_cc_safe() -> None:
    for pad in RYTM_PAD_CAPABILITIES:
        for machine_key in pad.allowed_machine_keys:
            profile = get_rytm_machine_profile(machine_key)
            assert profile is RYTM_MACHINE_PROFILES_BY_KEY[machine_key]
            assert isinstance(profile.machine_value, int)
            assert 0 <= profile.machine_value <= 127


def test_expected_machine_cc15_values() -> None:
    actual = {profile.key: profile.machine_value for profile in RYTM_MACHINE_PROFILES}
    assert actual == EXPECTED_MACHINE_CC15_VALUES


def test_pad_10_open_hihat_capability() -> None:
    pad = get_rytm_pad_capability(10)

    assert pad.track_code == "OH"
    assert pad.label == "Open Hihat"
    for machine_key in (
        "oh_classic",
        "oh_metallic",
        "hh_basic",
        "hh_lab",
        "ch_classic",
        "ch_metallic",
        "ut_noise",
        "ut_impulse",
    ):
        assert is_machine_allowed_on_pad(10, machine_key)
    assert not is_machine_allowed_on_pad(10, "xt_classic")


def test_dual_vco_uses_sy_prefixed_label() -> None:
    assert get_rytm_machine_profile("dual_vco").label == "SY Dual VCO"


@pytest.mark.parametrize("pad", (6, 7, 8))
def test_tom_pads_allow_xt_classic_and_reject_oh_classic(pad: int) -> None:
    assert is_machine_allowed_on_pad(pad, "xt_classic")
    assert not is_machine_allowed_on_pad(pad, "oh_classic")


def test_allowed_machine_profiles_for_pad_11_preserves_catalog_order() -> None:
    labels = [profile.label for profile in allowed_machine_profiles_for_pad(11)]

    assert labels == [
        "CY Classic",
        "CY Metallic",
        "CY Ride",
        "CB Classic",
        "CB Metallic",
        "UT Noise",
        "UT Impulse",
    ]


def test_unknown_pad_raises_clear_key_error() -> None:
    with pytest.raises(KeyError, match="Unknown Rytm pad"):
        get_rytm_pad_capability(99)


def test_unknown_machine_raises_clear_key_error() -> None:
    with pytest.raises(KeyError, match="Unknown Rytm machine key"):
        get_rytm_machine_profile("not_a_machine")


def test_is_machine_allowed_on_pad_rejects_unknown_machine_key() -> None:
    with pytest.raises(KeyError, match="Unknown Rytm machine key"):
        is_machine_allowed_on_pad(1, "not_a_machine")
