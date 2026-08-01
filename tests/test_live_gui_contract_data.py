"""Tests for declarative live-GUI data tables."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast


def test_live_gui_contract_data_exposes_screen_component_specs():
    from rytm_randomizer.data.live_gui_contracts import LIVE_GUI_SCREEN_COMPONENT_SPECS

    assert [spec.key for spec in LIVE_GUI_SCREEN_COMPONENT_SPECS] == [
        "selected-arc",
        "sidecar-status",
        "current-cue",
        "next-cues",
    ]
    assert {spec.region_key for spec in LIVE_GUI_SCREEN_COMPONENT_SPECS} == {
        "header",
        "cue-strip",
    }
