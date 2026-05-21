"""Drift-guard tests for the shared data layer (``rytm_randomizer.data``).

The shared data layer is the single source of truth for every piece of V1.34
domain data. ``rytm_randomizer.profiles`` / ``.scenes`` / ``.constants`` derive
their public names from ``rytm_randomizer.data`` instead of hand-re-typing
subsets.

These tests fail LOUDLY if:

* the package's derived views ever disagree with the data layer,
* a known-good constant (CC number, scene count, profile key) ever changes.

The V1.34 ``rytm_hybrid_randomizer_v134`` monolith that previously consumed
the same data layer has been retired; its frozen reference behavior now lives
as JSON goldens under ``tests/fixtures/v134_parity/`` (see
``tests/_parity_worker.py``).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import rytm_randomizer.constants as pkg_constants
import rytm_randomizer.data as data
import rytm_randomizer.profiles as pkg_profiles
import rytm_randomizer.scenes as pkg_scenes

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# 1. The data layer is internally non-empty.
# ---------------------------------------------------------------------------


def test_data_layer_exports_are_non_empty():
    """Sanity: the data layer actually carries data, not empty placeholders."""

    # BD_EXTRA_MACHINES is intentionally empty in V1.34; everything else is not.
    intentionally_empty = {"BD_EXTRA_MACHINES"}
    for name in data.__all__:
        value = getattr(data, name)
        if name in intentionally_empty:
            assert value == {}
            continue
        if isinstance(value, (dict, list, tuple)):
            assert len(value) > 0, f"data.{name} is unexpectedly empty"


# ---------------------------------------------------------------------------
# 3. Known-good constants - these must never silently change.
# ---------------------------------------------------------------------------


def test_machine_cc_is_15_everywhere():
    assert data.MACHINE_CC == 15
    assert pkg_constants.MACHINE_CC == 15


def test_profile_registry_has_expected_keys():
    """The canonical profile registry must carry all 11 V1.34 profiles."""

    assert set(data.PROFILES) == {
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
    }
    assert len(data.PROFILES) == 11


def test_profile_machine_values_are_known_good():
    """Spot-check the machine CC15 values of the four group profiles."""

    assert data.PROFILES["2"]["name"] == "My BD Hard"
    assert data.PROFILES["2"]["machine_value"] == 0
    assert data.PROFILES["3"]["name"] == "My BD Classic"
    assert data.PROFILES["3"]["machine_value"] == 1
    assert data.PROFILES["4"]["name"] == "My BD Acoustic"
    assert data.PROFILES["4"]["machine_value"] == 30
    assert data.PROFILES["5"]["name"] == "Pad 3 SY Raw Mid Bass"
    assert data.PROFILES["5"]["machine_value"] == 32


def test_profile_5_was_merged_into_the_registry():
    """The monolith historically extended PROFILES with ['5'] after the fact;
    the shared layer must already include it as a complete entry."""

    profile_5 = data.PROFILES["5"]
    assert profile_5["params"] is data.SY_RAW_PARAMS
    assert profile_5["order"] is data.SY_RAW_ORDER
    assert profile_5["anchor"] is data.PAD_3_SY_RAW_ANCHOR
    assert profile_5["zones"] is data.SY_RAW_ZONES
    assert profile_5["filter_style"] == "sy_raw_mid_bass"


def test_sy_raw_cc_numbers_are_known_good():
    """SY Raw SRC CC numbers must stay stable - the Pad 3 scaffold slices these."""

    assert data.SY_RAW_PARAMS["SRC Noise Level"] == 19
    assert data.SY_RAW_PARAMS["SRC Balance"] == 23
    assert data.SY_RAW_PARAMS["SRC Level"] == 16
    assert data.SY_RAW_PARAMS["FLT Type"] == 76


def test_scene_presets_has_14_entries_with_known_keys():
    assert len(data.SCENE_PRESETS) == 14
    assert set(data.SCENE_PRESETS) == {
        "s0",
        "s1",
        "s1a",
        "s1b",
        "s2",
        "s2a",
        "s2b",
        "s3",
        "s3a",
        "s3b",
        "s4",
        "s4a",
        "s4b",
        "s5",
    }
    assert data.SCENE_PRESETS["s0"]["name"] == "Home / Clean"
    assert data.SCENE_PRESETS["s0"]["action"] == "home"
    assert data.SCENE_PRESETS["s4b"]["name"] == "Wild Maximum"
    assert data.SCENE_PRESETS["s5"]["action"] == "clean"


def test_style_profiles_cover_core_techno_aesthetic_targets():
    assert set(data.STYLE_PROFILES) == {
        "detroit_minimal",
        "mills_hypnotic",
        "hood_stripped",
        "ur_machine_funk",
        "hardgroove_percussive",
        "birmingham_pressure",
        "industrial_dark",
        "deep_dark_hypnosis",
        "warehouse_peak",
    }
    assert data.STYLE_PROFILES["detroit_minimal"].name == "Detroit Minimal"
    assert data.STYLE_PROFILES["birmingham_pressure"].scores.grit == 9
    assert "snapshot" in data.STYLE_PROFILES["warehouse_peak"].analyzer_targets


def test_style_profiles_reference_existing_scene_presets():
    for profile in data.STYLE_PROFILES.values():
        assert profile.scene_keys
        for scene_key in profile.scene_keys:
            assert scene_key in data.SCENE_PRESETS


def test_style_profiles_are_complete_passive_design_records():
    for profile in data.STYLE_PROFILES.values():
        assert profile.key
        assert profile.name
        assert profile.summary
        assert profile.tags
        assert profile.rytm_focus
        assert profile.analog_four_focus
        assert profile.analyzer_targets
        for score in (
            profile.scores.energy,
            profile.scores.density,
            profile.scores.darkness,
            profile.scores.grit,
            profile.scores.groove,
            profile.scores.hypnosis,
            profile.scores.space,
        ):
            assert 0 <= score <= 10


def test_style_discovery_policy_maps_reference_to_wild_bands():
    from rytm_randomizer.data.style_discovery import (
        DEFAULT_STYLE_DISCOVERY_AMOUNT,
        STYLE_DISCOVERY_AMOUNT_MAX,
        STYLE_DISCOVERY_AMOUNT_MIN,
        style_discovery_policy,
    )

    assert STYLE_DISCOVERY_AMOUNT_MIN == 0
    assert STYLE_DISCOVERY_AMOUNT_MAX == 100
    assert DEFAULT_STYLE_DISCOVERY_AMOUNT == 75
    assert style_discovery_policy(0).band == "reference"
    assert style_discovery_policy(20).band == "reference"
    assert style_discovery_policy(21).band == "balanced"
    assert style_discovery_policy(60).band == "balanced"
    assert style_discovery_policy(61).band == "discovery"
    assert style_discovery_policy(85).band == "discovery"
    assert style_discovery_policy(86).band == "wild_discovery"
    assert style_discovery_policy(100).band == "wild_discovery"


@pytest.mark.parametrize("amount", [-1, 101])
def test_style_discovery_policy_rejects_out_of_range_amounts(amount):
    from rytm_randomizer.data.style_discovery import style_discovery_policy

    with pytest.raises(ValueError, match="discovery amount must be between 0 and 100"):
        style_discovery_policy(amount)


def test_style_discovery_policy_reports_internal_band_gap(monkeypatch):
    from rytm_randomizer.data import style_discovery

    monkeypatch.setattr(style_discovery, "STYLE_DISCOVERY_BANDS", ())

    with pytest.raises(ValueError, match="no discovery band covers amount 50"):
        style_discovery.style_discovery_policy(50)


def test_group_layout_maps_four_pads_to_known_profiles():
    assert set(data.GROUP_LAYOUT) == {1, 2, 3, 4}
    assert data.GROUP_LAYOUT[1]["profile"] == "2"
    assert data.GROUP_LAYOUT[2]["profile"] == "3"
    assert data.GROUP_LAYOUT[3]["profile"] == "5"
    assert data.GROUP_LAYOUT[4]["profile"] == "4"


def test_filter_type_names_derive_from_sy_raw_filter_names():
    assert data.FILTER_TYPE_NAMES == data.SY_RAW_FILTER_NAMES
    assert data.SY_RAW_FILTER_NAMES[1] == "LP1"
    assert data.SY_RAW_FILTER_NAMES[2] == "Bandpass"


def test_per_pad_mode_orders_are_known_good():
    assert data.PAD3_MODE_ORDER == ["anchor", "lp1", "bandpass", "wave", "scifi"]
    assert data.PAD4_MODE_ORDER == ["anchor", "tight", "long", "filter", "impact"]
    assert data.PAD1_BD_ROTATION_ORDER == ["2", "1", "3", "4", "6", "7", "8"]
    assert data.PAD2_PROFILE_KEYS == ["3", "9", "10", "11"]


# ---------------------------------------------------------------------------
# 4. Internal consistency of the param maps.
# ---------------------------------------------------------------------------


_PROFILE_MACHINE_KEYS = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11")


def test_every_profile_order_name_exists_in_its_param_map():
    """Each profile's ``order`` list must only name params present in its
    ``params`` CC map - otherwise the engine would KeyError at runtime."""

    for key in _PROFILE_MACHINE_KEYS:
        profile = data.PROFILES[key]
        params = profile["params"]
        for param_name in profile["order"]:
            assert (
                param_name in params
            ), f"PROFILES[{key!r}] order references unknown param {param_name!r}"


def test_every_profile_anchor_name_exists_in_its_param_map():
    for key in _PROFILE_MACHINE_KEYS:
        profile = data.PROFILES[key]
        params = profile["params"]
        for param_name in profile["anchor"]:
            assert (
                param_name in params
            ), f"PROFILES[{key!r}] anchor references unknown param {param_name!r}"


def test_param_cc_numbers_are_within_midi_range():
    """Every CC number in every param map must be a valid 0-127 MIDI control."""

    for name in data.__all__:
        value = getattr(data, name)
        if name.endswith("_PARAMS") and isinstance(value, dict):
            for param_name, cc in value.items():
                assert isinstance(cc, int), f"{name}[{param_name!r}] cc not int"
                assert 0 <= cc <= 127, f"{name}[{param_name!r}] cc {cc} out of range"


# ---------------------------------------------------------------------------
# 5. The package's derived views must agree with the shared data layer.
# ---------------------------------------------------------------------------


def test_package_group_layout_is_the_shared_object():
    assert pkg_profiles.GROUP_LAYOUT is data.GROUP_LAYOUT


def test_package_group_profile_metadata_derives_from_profiles():
    """GROUP_PROFILE_METADATA must be a faithful projection of PROFILES +
    GROUP_LAYOUT - if PROFILES changes, this must follow, not drift."""

    metadata = pkg_profiles.GROUP_PROFILE_METADATA
    assert set(metadata) == {"2", "3", "4", "5"}
    for key, entry in metadata.items():
        assert entry["name"] == data.PROFILES[key]["name"]
        assert entry["machine_value"] == data.PROFILES[key]["machine_value"]
        # group_pad must be the pad whose layout points back at this profile.
        assert data.GROUP_LAYOUT[entry["group_pad"]]["profile"] == key


def test_package_pad3_cc_map_is_sliced_from_sy_raw_params():
    cc_map = pkg_profiles.PAD_3_SY_RAW_CC_MAP
    assert cc_map == {"SRC Noise Level": 19, "SRC Balance": 23}
    for param_name, cc in cc_map.items():
        assert data.SY_RAW_PARAMS[param_name] == cc


def test_package_scene_commands_derive_from_scene_presets():
    """SCENE_COMMANDS (upper-case keys + scaffold flags) must be a faithful
    projection of the canonical SCENE_PRESETS - one source of truth."""

    commands = pkg_scenes.SCENE_COMMANDS
    assert len(commands) == len(data.SCENE_PRESETS) == 14
    for preset_key, preset in data.SCENE_PRESETS.items():
        command_key = preset_key.upper()
        assert command_key in commands
        command = commands[command_key]
        assert command["name"] == preset["name"]
        assert command["description"] == preset["description"]
        assert command["action"] == preset["action"]
        assert command["scope"] == "four_pad_group"
        assert command["executable"] is False
        assert command["v134_reference_command"] is True
        assert command["scaffold_only"] is True


if __name__ == "__main__":
    test_data_layer_exports_are_non_empty()
    test_machine_cc_is_15_everywhere()
    test_profile_registry_has_expected_keys()
    test_profile_machine_values_are_known_good()
    test_profile_5_was_merged_into_the_registry()
    test_sy_raw_cc_numbers_are_known_good()
    test_scene_presets_has_14_entries_with_known_keys()
    test_group_layout_maps_four_pads_to_known_profiles()
    test_filter_type_names_derive_from_sy_raw_filter_names()
    test_per_pad_mode_orders_are_known_good()
    test_every_profile_order_name_exists_in_its_param_map()
    test_every_profile_anchor_name_exists_in_its_param_map()
    test_param_cc_numbers_are_within_midi_range()
    test_package_group_layout_is_the_shared_object()
    test_package_group_profile_metadata_derives_from_profiles()
    test_package_pad3_cc_map_is_sliced_from_sy_raw_params()
    test_package_scene_commands_derive_from_scene_presets()
    print("all data-layer drift-guard tests passed")
