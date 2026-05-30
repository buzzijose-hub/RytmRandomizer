"""Tests for the cockpit Analog Rytm parameter lookup."""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.data.rytm_parameter_map import (
    cockpit_pad_channel,
    cockpit_parameter_control,
)
from rytm_randomizer.data.analog_rytm_midi import (
    ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER,
    ANALOG_RYTM_MACHINE_SRC_BY_MACHINE,
)

pytestmark = pytest.mark.fast


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
