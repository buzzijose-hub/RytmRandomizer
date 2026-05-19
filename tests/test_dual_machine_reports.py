"""Tests for dual-machine reports."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_target_report_lists_devices_for_both_target() -> None:
    from rytm_randomizer.dual_machine.reports import target_report

    text = target_report("both")

    assert "Target: both" in text
    assert "analog_rytm_mk2" in text
    assert "analog_four_mk2" in text
    assert "Rytm" in text
    assert "Analog Four" in text


def test_target_report_lists_single_a4_target() -> None:
    from rytm_randomizer.dual_machine.reports import target_report

    text = target_report("a4")

    assert "Target: a4" in text
    assert "analog_four_mk2" in text
    assert "analog_rytm_mk2" not in text
