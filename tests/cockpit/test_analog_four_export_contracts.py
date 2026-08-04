"""Tests for passive Analog Four export-contract helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from rytm_randomizer.cockpit.export.analog_four_export_contracts import (
    analog_four_export_path_name,
)

pytestmark = pytest.mark.fast


def test_export_path_name_uses_shared_filename_safety() -> None:
    assert analog_four_export_path_name(Path("unsafe\nname.wav")) == "<invalid>"
    assert analog_four_export_path_name(Path("safe.wav")) == "safe.wav"
    assert analog_four_export_path_name(object()) == "<invalid>"
