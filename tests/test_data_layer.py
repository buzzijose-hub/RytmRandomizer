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
import rytm_randomizer.data.analog_four_patch_templates as a4_patch_templates
import rytm_randomizer.data.audio_patch_dna as audio_patch_dna_data
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


def test_a4_sysex_calibration_tracks_filter2_resonance_capture():
    calibration = data.ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS["Filter2 Resonance"]

    assert calibration.status == "hardware-write-validated"
    assert calibration.track_1_primary_raw_offset == 170
    assert data.ANALOG_FOUR_SYSEX_WRITE_VALIDATIONS["Filter2 Resonance"]


def test_a4_saved_kit_layout_is_canonical_data() -> None:
    assert data.A4_CHECKSUM_PACKED_OFFSET == 8
    assert data.A4_SAVED_KIT_TRAILER_SIZE == 4
    assert data.A4_SAVED_KIT_UNPACKED_SIZE == 2415
    assert data.A4_SAVED_KIT_PACKED_SIZE == 2760
    assert data.A4_SAVED_KIT_FRAMED_SIZE == 2770


def test_a4_audio_inference_model_is_canonical_immutable_data() -> None:
    model = data.ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER

    assert len(model) == 28
    assert model["Filter2 Resonance"].intercept == 6.0
    assert model["LFO1 Depth B"].terms[0].feature_keys == ("animation", "noise")
    assert model["OSC1 Pulsewidth"] is model["OSC2 Pulsewidth"]
    with pytest.raises(TypeError):
        model["Filter2 Resonance"] = model["Volume"]  # type: ignore[index]


def test_a4_patch_family_order_is_canonical_data() -> None:
    expected = ("Oscillators", "Envelope and LFO", "Filter and effects")

    assert expected == data.ANALOG_FOUR_PATCH_FAMILY_ORDER
    assert expected == a4_patch_templates.ANALOG_FOUR_PATCH_FAMILY_ORDER
    assert "ANALOG_FOUR_PATCH_FAMILY_ORDER" in data.__all__
    assert "ANALOG_FOUR_PATCH_FAMILY_ORDER" in a4_patch_templates.__all__


def test_a4_audio_inference_model_rejects_unknown_keys_at_construction() -> None:
    from rytm_randomizer.data.analog_four_audio_inference import (
        A4_AUDIO_INFERENCE_UNIPOLAR,
        AnalogFourAudioInferenceSpec,
        AnalogFourAudioInferenceTerm,
    )

    assert set(data.ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER) == set(
        data.ANALOG_FOUR_INFERENCE_PARAMETERS
    )
    with pytest.raises(ValueError, match="feature keys"):
        AnalogFourAudioInferenceTerm(("typo",), 1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="at least one feature"):
        AnalogFourAudioInferenceTerm((), 1.0)
    with pytest.raises(ValueError, match="at least one parameter"):
        AnalogFourAudioInferenceSpec((), A4_AUDIO_INFERENCE_UNIPOLAR, 0.0, ())
    with pytest.raises(ValueError, match="must be unique"):
        AnalogFourAudioInferenceSpec(
            ("Volume", "Volume"),
            A4_AUDIO_INFERENCE_UNIPOLAR,
            0.0,
            (AnalogFourAudioInferenceTerm(("brightness",), 1.0),),
        )
    with pytest.raises(ValueError, match="parameters"):
        AnalogFourAudioInferenceSpec(
            ("Filter2 Resonanse",),  # type: ignore[arg-type]
            A4_AUDIO_INFERENCE_UNIPOLAR,
            0.0,
            (AnalogFourAudioInferenceTerm(("brightness",), 1.0),),
        )
    with pytest.raises(ValueError, match="weighted term"):
        AnalogFourAudioInferenceSpec(
            ("Filter2 Resonance",),
            A4_AUDIO_INFERENCE_UNIPOLAR,
            0.0,
            (),
        )


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


def test_analog_rytm_manual_catalog_pins_os172_rows_and_safety_statuses():
    """Rytm OS 1.72 manual rows are documented without widening live mutation."""

    assert len(data.ANALOG_RYTM_MANUAL_CC) == 323
    assert len(data.ANALOG_RYTM_VALIDATED_RUNTIME_CC) == 99
    assert len(data.ANALOG_RYTM_MANUAL_NOTE_TRIGGERS) == 13

    track_machine = data.ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("COMMON", "Track Machine Type")]
    assert track_machine.cc_msb == 15
    assert track_machine.nrpn_msb == 1
    assert track_machine.nrpn_lsb == 103
    assert track_machine.risk == "high"
    assert track_machine.mutation_status == "locked_default"

    delay_feedback = data.ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("DELAY", "Delay Feedback")]
    assert delay_feedback.cc_msb == 19
    assert delay_feedback.risk == "high"
    assert delay_feedback.mutation_status == "locked_default"

    bd_hard_tune = data.ANALOG_RYTM_MACHINE_SRC_BY_MACHINE["bd_hard"][1]
    assert bd_hard_tune.parameter == "Tune"
    assert bd_hard_tune.cc_msb == 17
    assert bd_hard_tune.mutation_status == "validated_runtime"


def test_analog_rytm_kit_layout_pins_current_sound_offsets():
    """Raw-kit offsets must stay aligned with the Rytm track sound layout."""

    assert data.RYTM_KIT_RAW_SIZE == 0x0A32
    assert data.RYTM_KIT_TRACKS_OFFSET == 0x002E
    assert data.RYTM_KIT_TRACK_SOUND_SIZE == 162
    assert data.RYTM_KIT_TRACK_MACHINE_VALUE_OFFSET == 0x00AA
    assert data.RYTM_SOUND_FIELD_BY_NRPN_LSB[1].sound_offset == 0x001E
    assert data.RYTM_SOUND_FIELD_BY_NRPN_LSB[20].sound_offset == 0x0044
    assert data.RYTM_SOUND_FIELD_BY_NRPN_LSB[27].sound_offset == 0x0052


def test_analog_four_manual_cc_mapping_matches_pwm_depth_and_filter_frequency():
    """A4 CC labels must follow the Analog Four MKII manual, not MIDI convention."""

    pulsewidth = data.ANALOG_FOUR_SYNTH_TRACK_CC["OSC1 Pulsewidth"]
    assert pulsewidth.section == "OSC 1"
    assert pulsewidth.encoder == "H"
    assert pulsewidth.cc_msb == 72
    assert pulsewidth.cc_lsb is None
    assert pulsewidth.nrpn_msb == 1
    assert pulsewidth.nrpn_lsb == 7

    pwm_speed = data.ANALOG_FOUR_SYNTH_TRACK_CC["OSC1 PWM Speed"]
    assert pwm_speed.section == "OSC 1"
    assert pwm_speed.encoder == "I"
    assert pwm_speed.cc_msb == 73
    assert pwm_speed.cc_lsb is None
    assert pwm_speed.nrpn_msb == 1
    assert pwm_speed.nrpn_lsb == 8

    pwm_depth = data.ANALOG_FOUR_SYNTH_TRACK_CC["OSC1 PWM Depth"]
    assert pwm_depth.section == "OSC 1"
    assert pwm_depth.encoder == "J"
    assert pwm_depth.cc_msb == 74
    assert pwm_depth.cc_lsb is None
    assert pwm_depth.nrpn_msb == 1
    assert pwm_depth.nrpn_lsb == 9

    filter_frequency = data.ANALOG_FOUR_SYNTH_TRACK_CC["Filter1 Frequency"]
    assert filter_frequency.section == "FILTERS"
    assert filter_frequency.encoder == "A"
    assert filter_frequency.cc_msb == 18
    assert filter_frequency.cc_lsb == 50
    assert filter_frequency.nrpn_msb == 1
    assert filter_frequency.nrpn_lsb == 40


def test_analog_four_cc_lookup_maps_msb_to_manual_entry():
    pulsewidth = data.ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB[72]
    pwm_speed = data.ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB[73]
    pwm_depth = data.ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB[74]

    assert pulsewidth.parameter == "OSC1 Pulsewidth"
    assert pwm_speed.parameter == "OSC1 PWM Speed"
    assert pwm_depth.parameter == "OSC1 PWM Depth"


def test_analog_four_manual_cc_table_covers_all_manual_cc_rows():
    """Appendix D rows with CC MSB values are represented exactly once."""

    assert len(data.ANALOG_FOUR_SYNTH_TRACK_CC) == 58
    assert len(data.ANALOG_FOUR_MANUAL_CC) == 72
    assert len(data.ANALOG_FOUR_MANUAL_CC_BY_MSB) == 72
    assert set(data.ANALOG_FOUR_SYNTH_TRACK_CC).issubset(data.ANALOG_FOUR_MANUAL_CC)
    assert {mapping.cc_msb for mapping in data.ANALOG_FOUR_MANUAL_CC.values()} == set(
        data.ANALOG_FOUR_MANUAL_CC_BY_MSB
    )

    track_mute = data.ANALOG_FOUR_MANUAL_CC["Track Mute"]
    assert track_mute.section == "TRACK"
    assert track_mute.cc_msb == 94
    assert track_mute.nrpn_msb == 1
    assert track_mute.nrpn_lsb == 101

    performance_a = data.ANALOG_FOUR_MANUAL_CC["Performance Parameter A"]
    assert performance_a.section == "PERFORMANCE"
    assert performance_a.encoder == "A"
    assert performance_a.cc_msb == 3
    assert performance_a.nrpn_msb == 0
    assert performance_a.nrpn_lsb == 0

    modwheel = data.ANALOG_FOUR_MANUAL_CC["Modwheel"]
    assert modwheel.section == "MODULATION"
    assert modwheel.cc_msb == 1
    assert modwheel.cc_lsb == 33
    assert modwheel.nrpn_msb is None
    assert modwheel.nrpn_lsb is None

    osc2_pwm_speed = data.ANALOG_FOUR_MANUAL_CC["OSC2 PWM Speed"]
    assert osc2_pwm_speed.section == "OSC 2"
    assert osc2_pwm_speed.cc_msb == 82
    assert osc2_pwm_speed.nrpn_msb == 1
    assert osc2_pwm_speed.nrpn_lsb == 28

    envf_depth_a = data.ANALOG_FOUR_MANUAL_CC["EnvF Depth A"]
    assert envf_depth_a.section == "ENVF"
    assert envf_depth_a.cc_msb == 20
    assert envf_depth_a.cc_lsb == 52
    assert envf_depth_a.nrpn_msb == 1
    assert envf_depth_a.nrpn_lsb == 67

    lfo2_depth_b = data.ANALOG_FOUR_MANUAL_CC["LFO2 Depth B"]
    assert lfo2_depth_b.section == "LFO2"
    assert lfo2_depth_b.cc_msb == 27
    assert lfo2_depth_b.cc_lsb == 59
    assert lfo2_depth_b.nrpn_msb == 1
    assert lfo2_depth_b.nrpn_lsb == 99


def test_analog_four_synth_track_nrpn_table_includes_nrpn_only_subpage_rows():
    """NRPN unlock exposes synth-track rows that have no direct CC MSB."""

    assert set(data.ANALOG_FOUR_SYNTH_TRACK_CC).issubset(data.ANALOG_FOUR_SYNTH_TRACK_NRPN)
    assert len(data.ANALOG_FOUR_SYNTH_TRACK_NRPN) > len(data.ANALOG_FOUR_SYNTH_TRACK_CC)

    sync_mode = data.ANALOG_FOUR_SYNTH_TRACK_NRPN["Sync Mode"]
    assert sync_mode.section == "OSC COMMON"
    assert sync_mode.encoder == "B"
    assert sync_mode.cc_msb is None
    assert sync_mode.nrpn_msb == 1
    assert sync_mode.nrpn_lsb == 31

    lfo1_waveform = data.ANALOG_FOUR_SYNTH_TRACK_NRPN["LFO1 Waveform"]
    assert lfo1_waveform.section == "LFO1"
    assert lfo1_waveform.encoder == "F"
    assert lfo1_waveform.cc_msb is None
    assert lfo1_waveform.nrpn_msb == 1
    assert lfo1_waveform.nrpn_lsb == 85

    assert data.ANALOG_FOUR_SYNTH_TRACK_NRPN_BY_ADDRESS[(1, 31)].parameter == "Sync Mode"
    assert data.ANALOG_FOUR_SYNTH_TRACK_NRPN_BY_ADDRESS[(1, 85)].parameter == "LFO1 Waveform"


def test_analog_four_detroit_minimal_recipe_is_manual_backed():
    recipe = data.ANALOG_FOUR_KIT_RECIPES["detroit-minimal"]

    assert recipe.name == "detroit-minimal"
    assert recipe.label == "Detroit Minimal"
    assert {event.track for event in recipe.events} == {1, 2, 3, 4}
    assert len(recipe.events) >= 32
    for event in recipe.events:
        assert 1 <= event.track <= 4
        assert 0 <= event.value <= 127
        assert event.parameter in data.ANALOG_FOUR_MANUAL_CC

    first_event = recipe.events[0]
    assert first_event.track == 1
    assert first_event.parameter == "OSC1 Level"
    assert first_event.value == 110


def test_analog_four_bell_techno_grid_recipe_is_manual_backed_and_controlled():
    recipe = data.ANALOG_FOUR_KIT_RECIPES["bell-techno-grid"]

    assert recipe.name == "bell-techno-grid"
    assert recipe.label == "Bell Techno Grid"
    assert {event.track for event in recipe.events} == {1, 2, 3, 4}
    assert 24 <= len(recipe.events) <= 32
    for event in recipe.events:
        assert 1 <= event.track <= 4
        assert 0 <= event.value <= 127
        assert event.parameter in data.ANALOG_FOUR_MANUAL_CC

    track_2_events = [event for event in recipe.events if event.track == 2]
    assert [event.parameter for event in track_2_events[:3]] == [
        "OSC1 Waveform",
        "OSC2 Level",
        "Sync Amount",
    ]


def test_analog_four_bell_techno_expanded_recipe_uses_full_cc_surface():
    recipe = data.ANALOG_FOUR_KIT_RECIPES["bell-techno-expanded"]

    assert recipe.name == "bell-techno-expanded"
    assert recipe.label == "Bell Techno Expanded"
    assert {event.track for event in recipe.events} == {1, 2, 3, 4}
    assert len(recipe.events) >= 96
    for event in recipe.events:
        assert 1 <= event.track <= 4
        assert 0 <= event.value <= 127
        assert event.parameter in data.ANALOG_FOUR_MANUAL_CC

    section_by_parameter = {
        mapping.parameter: mapping.section for mapping in data.ANALOG_FOUR_MANUAL_CC.values()
    }
    assert {section_by_parameter[event.parameter] for event in recipe.events}.issuperset(
        {
            "OSC 1",
            "NOISE",
            "OSC 2",
            "OSC COMMON",
            "FILTERS",
            "AMP",
            "ENVF",
            "ENV2",
            "LFO1",
            "LFO2",
        }
    )
    assert all(
        sum(1 for event in recipe.events if event.track == track) >= 20 for track in (1, 2, 3, 4)
    )


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
        "jose_core_techno",
    }
    assert data.STYLE_PROFILES["detroit_minimal"].name == "Detroit Minimal"
    assert data.STYLE_PROFILES["birmingham_pressure"].scores.grit == 9
    assert data.STYLE_PROFILES["jose_core_techno"].name == "Jose Core Techno"
    assert "jeff_mills" in data.STYLE_PROFILES["jose_core_techno"].tags
    assert "oscar_mulero" in data.STYLE_PROFILES["jose_core_techno"].tags
    assert (
        "A4 Track 1 bassline pressure" in data.STYLE_PROFILES["jose_core_techno"].analog_four_focus
    )
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


def test_style_target_vectors_import_guard_rejects_profile_mismatch():
    source_path = PROJECT_ROOT / "rytm_randomizer" / "data" / "style_targets.py"
    source = source_path.read_text(encoding="utf-8").replace(
        "from .style_profiles import STYLE_PROFILES",
        "STYLE_PROFILES = {}",
    )
    module_name = "rytm_randomizer.data._style_targets_guard_probe"
    probe_module = type(sys)(module_name)
    probe_module.__dict__.update(
        {
            "__builtins__": __builtins__,
            "__name__": module_name,
            "__package__": "rytm_randomizer.data",
        }
    )
    sys.modules[module_name] = probe_module

    try:
        with pytest.raises(ValueError, match="style target vectors must cover every style profile"):
            exec(  # noqa: S102 - local source probe covers the import-time catalog guard.
                compile(source, str(source_path), "exec"),
                probe_module.__dict__,
            )
    finally:
        sys.modules.pop(module_name, None)


def test_style_discovery_policy_maps_reference_to_wild_bands():
    from rytm_randomizer.data.style_discovery import (
        DEFAULT_STYLE_DISCOVERY_AMOUNT,
        STYLE_DISCOVERY_AMOUNT_MAX,
        STYLE_DISCOVERY_AMOUNT_MIN,
        style_discovery_policy,
    )

    assert STYLE_DISCOVERY_AMOUNT_MIN == 0
    assert STYLE_DISCOVERY_AMOUNT_MAX == 100
    assert DEFAULT_STYLE_DISCOVERY_AMOUNT == 45
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


def test_audio_patch_dna_directions_are_canonical_immutable_data():
    direction_rows = tuple(
        (
            spec.key,
            spec.label,
            spec.role,
            spec.closeness,
            spec.duration,
            spec.attack,
            spec.decay,
            spec.sustain,
            spec.tail,
            spec.brightness,
            spec.noise,
            spec.low_end,
            spec.harmonicity,
            spec.transient,
            spec.modulation,
        )
        for spec in data.AUDIO_PATCH_DNA_DIRECTION_SPECS
    )

    assert data.AUDIO_PATCH_DNA_CANDIDATE_COUNT == 8
    assert direction_rows == (
        (
            "closest",
            "Closest",
            "closest measured match",
            96,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ),
        (
            "darker",
            "Darker",
            "reduced high-frequency energy",
            86,
            0.0,
            0.0,
            0.0,
            0.0,
            0.04,
            -0.22,
            0.0,
            0.10,
            0.0,
            0.0,
            0.0,
        ),
        (
            "brighter",
            "Brighter",
            "sharper and more exposed",
            84,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.22,
            0.04,
            0.0,
            0.0,
            0.04,
            0.0,
        ),
        (
            "metallic",
            "Metallic",
            "inharmonic infrastructure texture",
            80,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.16,
            0.14,
            0.0,
            0.08,
            0.0,
            0.10,
        ),
        (
            "percussive",
            "Percussive",
            "shorter and more transient-led",
            82,
            0.0,
            -0.12,
            -0.16,
            -0.16,
            -0.18,
            0.0,
            0.0,
            0.0,
            0.0,
            0.24,
            0.0,
        ),
        (
            "atmospheric",
            "Atmospheric",
            "slower envelope and longer pressure",
            76,
            0.0,
            0.16,
            0.18,
            0.18,
            0.28,
            0.0,
            0.0,
            0.0,
            0.0,
            -0.12,
            0.10,
        ),
        (
            "deeper",
            "Deeper",
            "heavier low-frequency body",
            81,
            0.08,
            0.0,
            0.0,
            0.0,
            0.0,
            -0.12,
            0.0,
            0.22,
            0.0,
            0.0,
            0.0,
        ),
        (
            "animated",
            "Animated",
            "more spectral motion and modulation",
            78,
            0.0,
            0.0,
            0.0,
            0.0,
            0.08,
            0.0,
            0.06,
            0.0,
            0.0,
            0.0,
            0.28,
        ),
    )
    assert {
        "AUDIO_PATCH_DNA_CANDIDATE_COUNT",
        "AUDIO_PATCH_DNA_DIRECTION_SPECS",
    }.issubset(data.__all__)
    assert "AudioPatchDnaDirectionSpec" in audio_patch_dna_data.__all__


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
