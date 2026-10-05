"""Tests for the cockpit Analog Rytm parameter lookup."""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.data import rytm_parameter_map as mapmod
from rytm_randomizer.cockpit.data.rytm_parameter_map import (
    cockpit_default_machine_label,
    cockpit_machine_is_allowed_on_pad,
    cockpit_pad_channel,
    cockpit_parameter_control,
    cockpit_parameter_key,
    cockpit_parameter_live_blockers,
    cockpit_parameter_mapping,
)
from rytm_randomizer.data.analog_rytm_midi import (
    ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER,
    ANALOG_RYTM_MACHINE_SRC_BY_MACHINE,
    AnalogRytmCcMapping,
)

pytestmark = pytest.mark.fast


@pytest.mark.parametrize(
    ("machine", "pad_id", "allowed"),
    (
        ("CH Closed", 9, True),
        ("CH Closed", 3, False),
        ("SY Dual VCO", 4, True),
        ("XT Classic", 6, True),
        ("CY Classic", 11, True),
        ("unknown future machine", 1, False),
        ("BD Hard", 0, False),
        ("BD Hard", 13, False),
        ("BD Hard", True, False),
        ("BD Hard", 1.0, False),
    ),
)
def test_cockpit_pad_compatibility_uses_canonical_facts(
    machine: str, pad_id: int, allowed: bool
) -> None:
    assert cockpit_machine_is_allowed_on_pad(machine, pad_id) is allowed


def test_cockpit_mock_default_labels_use_each_pads_canonical_primary_family() -> None:
    for pad_id in range(1, 13):
        assert cockpit_machine_is_allowed_on_pad(cockpit_default_machine_label(pad_id), pad_id)
    assert cockpit_default_machine_label(11) == "CY Classic"
    with pytest.raises(KeyError, match="Unknown Rytm pad"):
        cockpit_default_machine_label(13)


def test_cockpit_pad_channel_maps_12_tracks_to_zero_based_mido_channels() -> None:
    assert cockpit_pad_channel(1) == 0
    assert cockpit_pad_channel(12) == 11


def test_cockpit_pad_channel_rejects_invalid_pad_ids() -> None:
    with pytest.raises(ValueError, match="pad_id must be in \\[1, 12\\]"):
        cockpit_pad_channel(0)

    with pytest.raises(ValueError, match="pad_id must be in \\[1, 12\\]"):
        cockpit_pad_channel(13)


def test_cockpit_parameter_control_maps_machine_specific_and_common_pages() -> None:
    assert cockpit_parameter_control("BD Hard", "tun") == 17
    assert cockpit_parameter_control("bd_hard", "snap") == 21
    assert cockpit_parameter_control("FX Metal", "dec") == 18
    assert cockpit_parameter_control("BD Acoustic", "filter_resonance") == 75
    assert cockpit_parameter_control("BD Acoustic", "lfo_speed") == 102
    assert cockpit_parameter_control("BD Acoustic", "sample_tune") == 24


def test_cockpit_parameter_control_returns_none_for_unsendable_keys() -> None:
    assert cockpit_parameter_control("SD Classic", "swt") is None
    assert cockpit_parameter_control("unknown future machine", "tun") is None
    assert cockpit_parameter_control("unknown future machine", "flt") == 74


def test_cockpit_parameter_mapping_returns_canonical_catalog_rows() -> None:
    tune = cockpit_parameter_mapping("XT Classic", "target_note")
    decay = cockpit_parameter_mapping("XT Classic", "decay")
    amp_volume = cockpit_parameter_mapping("XT Classic", "amp_volume")

    assert tune is not None
    assert tune.parameter == "Tune"
    assert tune.nrpn_lsb == 1
    assert decay is not None
    assert decay.parameter == "Decay"
    assert decay.nrpn_lsb == 2
    assert amp_volume is ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("AMP", "Amp Volume")]


def test_cockpit_parameter_mapping_rejects_a_dangling_alias(monkeypatch) -> None:
    catalog = dict(mapmod.ANALOG_RYTM_MACHINE_SRC_BY_MACHINE)
    catalog["bd_hard"] = ()
    monkeypatch.setattr(mapmod, "ANALOG_RYTM_MACHINE_SRC_BY_MACHINE", catalog)

    with pytest.raises(ValueError, match="missing Analog Rytm catalog row"):
        mapmod.cockpit_parameter_mapping("BD Hard", "tun")


def test_cockpit_machine_known_uses_the_canonical_catalog() -> None:
    assert mapmod.cockpit_machine_is_known("BD Hard") is True
    assert mapmod.cockpit_machine_is_known("unknown future machine") is False


def test_cockpit_parameter_key_projects_and_rejects_machine_specific_rows() -> None:
    assert cockpit_parameter_key("BD Hard", "SRC", "Tune") == "tun"
    assert cockpit_parameter_key("BD Hard", "SRC", "unknown future parameter") is None


@pytest.mark.parametrize(
    ("machine", "section", "parameter", "expected"),
    (
        ("XT Classic", "xt_classic", "Tune", "tun"),
        ("BD Sharp", "bd_sharp", "Hold Time", "hold"),
        ("SD Hard", "sd_hard", "Noise Decay", "noise_decay"),
        ("XT Classic", "bd_hard", "Tune", None),
        ("BD Hard", "xt_classic", "Tune", None),
        ("XT Classic", "AMP", "Tune", None),
        ("XT Classic", "xt_classic", "unknown future parameter", None),
        ("unknown future machine", "SRC", "Tune", None),
        ("CY Ride", "cy_ride", "Tune", "src_cy_ride_1"),
    ),
)
def test_cockpit_parameter_key_accepts_only_the_owning_machine_src_section(
    machine: str, section: str, parameter: str, expected: str | None
) -> None:
    assert cockpit_parameter_key(machine, section, parameter) == expected


@pytest.mark.parametrize(
    ("machine", "compact_key", "catalog_machine", "catalog_parameter"),
    (
        ("BD FM", "dec", "bd_fm", "Decay"),
        ("BD FM", "fm_amount", "bd_fm", "FM Amount"),
        ("BD FM", "fm_decay", "bd_fm", "FM Decay Time"),
        ("BD FM", "fm_tune", "bd_fm", "FM Tune"),
        ("BD Classic", "sweep_depth", "bd_classic", "Sweep Depth"),
        ("BD Sharp", "hold", "bd_sharp", "Hold Time"),
        ("BD Sharp", "tick", "bd_sharp", "Tick Level"),
        ("BD Plastic", "vco_click", "bd_plastic", "VCO Click"),
        ("SD Hard", "tick", "sd_hard", "Tick Level"),
        ("SD Hard", "noise_decay", "sd_hard", "Noise Decay"),
        ("SD Hard", "swt", "sd_hard", "Sweep Time"),
    ),
)
def test_cockpit_parameter_control_projects_manual_backed_machine_src_catalog(
    machine: str,
    compact_key: str,
    catalog_machine: str,
    catalog_parameter: str,
) -> None:
    assert cockpit_parameter_control(machine, compact_key) == _machine_cc(
        catalog_machine,
        catalog_parameter,
    )


@pytest.mark.parametrize(
    ("compact_key", "section", "catalog_parameter"),
    (
        ("sample_tune", "SAMPLE", "Sample Tune"),
        ("sample_level", "SAMPLE", "Sample Level"),
        ("flt", "FILTER", "Filter Frequency"),
        ("filter_resonance", "FILTER", "Filter Resonance"),
        ("amp_decay", "AMP", "Amp Decay Time"),
        ("overdrive", "AMP", "Amp Overdrive"),
        ("lfo_speed", "LFO", "LFO Speed"),
        ("lfo_depth", "LFO", "LFO Depth"),
    ),
)
def test_cockpit_parameter_control_projects_manual_backed_general_catalog(
    compact_key: str,
    section: str,
    catalog_parameter: str,
) -> None:
    assert cockpit_parameter_control("BD Acoustic", compact_key) == _general_cc(
        section,
        catalog_parameter,
    )


def _machine_cc(machine_key: str, parameter: str) -> int:
    for row in ANALOG_RYTM_MACHINE_SRC_BY_MACHINE[machine_key]:
        if row.parameter == parameter:
            return row.cc_msb
    raise AssertionError(f"missing machine catalog row for {machine_key}:{parameter}")


def _general_cc(section: str, parameter: str) -> int:
    return ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[(section, parameter)].cc_msb


def test_every_canonical_src_row_round_trips_without_inventing_addresses() -> None:
    count = 0
    fallback_count = 0
    for machine_key, rows in ANALOG_RYTM_MACHINE_SRC_BY_MACHINE.items():
        for row in rows:
            key = cockpit_parameter_key(machine_key, row.section, row.parameter)
            assert key is not None
            assert cockpit_parameter_mapping(machine_key, key) is row
            assert cockpit_parameter_key(machine_key, "SRC", row.parameter) == key
            assert cockpit_parameter_control(machine_key, key) == row.cc_msb
            count += 1
            fallback_count += key.startswith("src_")
    assert count == 224
    assert fallback_count == 68
    assert cockpit_parameter_key("SY Dual VCO", "dual_vco", "Osc 1 Decay") == "src_dual_vco_2"
    assert cockpit_parameter_mapping("SY Dual VCO", "src_dual_vco_2") is (
        ANALOG_RYTM_MACHINE_SRC_BY_MACHINE["dual_vco"][2]
    )


@pytest.mark.parametrize(
    "key",
    (
        "src_hh_lab_01",
        "src_hh_lab_8",
        "src_hh_lab_-1",
        "src_HH_LAB_1",
        "src_hh_lab_1_extra",
        "src_sy_chip_1",
        "src_bd_hard_1",
        "src_future_1",
    ),
)
def test_catalog_fallback_keys_require_exact_canonical_ownership(key: str) -> None:
    assert cockpit_parameter_mapping("HH Lab", key) is None
    assert cockpit_parameter_mapping("unknown future machine", key) is None
    assert cockpit_parameter_mapping("BD Hard", "src_bd_hard_1") is None


@pytest.mark.parametrize("row", ANALOG_RYTM_MACHINE_SRC_BY_MACHINE["cy_ride"])
@pytest.mark.parametrize("machine", ("CY Ride", "cy_ride", "CY-RIDE"))
@pytest.mark.parametrize("compact_alias", (False, True))
def test_every_cy_ride_src_binding_is_blocked_before_narrower_protections(
    monkeypatch: pytest.MonkeyPatch,
    row: AnalogRytmCcMapping,
    machine: str,
    compact_alias: bool,
) -> None:
    if compact_alias:
        aliases = dict(mapmod._MACHINE_PARAMETER_ALIASES)
        aliases["cy_ride"] = {"ride_probe": row.parameter}
        monkeypatch.setattr(mapmod, "_MACHINE_PARAMETER_ALIASES", aliases)
        key = "ride_probe"
    else:
        key = cockpit_parameter_key(machine, "SRC", row.parameter)
    assert key is not None
    assert cockpit_machine_is_allowed_on_pad(machine, 11)
    assert cockpit_parameter_mapping(machine, key) is row
    assert cockpit_parameter_live_blockers(machine, key) == ("src_cy_ride_slot_unverified",)
    assert cockpit_parameter_live_blockers(machine, "flt") == ()


@pytest.mark.parametrize(
    ("machine", "key", "blocker"),
    (
        ("UT Impulse", "src_ut_impulse_3", "src_selector_encoding_unverified"),
        ("CY Ride", "src_cy_ride_3", "src_cy_ride_slot_unverified"),
        ("CY Ride", "src_cy_ride_4", "src_cy_ride_slot_unverified"),
        ("SY Chip", "src_sy_chip_3", "src_selector_encoding_unverified"),
        ("SY Chip", "src_sy_chip_4", "src_mode_encoding_unverified"),
        ("SY Dual VCO", "src_dual_vco_4", "src_requires_guarded_detune_window"),
        ("SY Chip", "src_sy_chip_5", "src_pitch_protected"),
        ("HH Lab", "src_hh_lab_7", "src_pitch_protected"),
        ("HH Basic", "src_hh_basic_5", "src_selector_protected"),
        ("CY Classic", "src_cy_classic_0", "src_level_protected"),
        ("BD Hard", "lev", "src_level_protected"),
        ("SY Raw", "noise_level", "src_snapshot_projection_omitted"),
    ),
)
def test_live_blockers_do_not_erase_descriptive_bindings(
    machine: str, key: str, blocker: str
) -> None:
    assert cockpit_parameter_mapping(machine, key) is not None
    assert cockpit_parameter_live_blockers(machine, key) == (blocker,)
    assert cockpit_parameter_live_blockers(machine, "flt") == ()
    assert cockpit_parameter_live_blockers(machine, "unknown") == ()
