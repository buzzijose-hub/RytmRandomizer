"""Tests for the cockpit Analog Rytm parameter lookup."""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.data.rytm_parameter_map import (
    cockpit_pad_channel,
    cockpit_parameter_control,
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
