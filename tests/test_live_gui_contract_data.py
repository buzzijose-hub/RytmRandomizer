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


def test_live_gui_contract_data_exposes_desktop_regions_and_style_tokens():
    from rytm_randomizer.data.live_gui_contracts import (
        LIVE_GUI_DESKTOP_APP_STYLE_TOKEN_SPECS,
        LIVE_GUI_DESKTOP_REGION_SPECS,
    )

    assert [spec.region_key for spec in LIVE_GUI_DESKTOP_REGION_SPECS] == [
        "region-current-cue",
        "region-machine-grid",
        "region-analyzer",
        "region-capture-review",
        "region-controls",
        "region-harness",
    ]
    assert all(spec.min_width_px > 0 for spec in LIVE_GUI_DESKTOP_REGION_SPECS)
    assert [spec.token_key for spec in LIVE_GUI_DESKTOP_APP_STYLE_TOKEN_SPECS] == [
        "token-surface",
        "token-panel",
        "token-warning",
        "token-disabled",
    ]
