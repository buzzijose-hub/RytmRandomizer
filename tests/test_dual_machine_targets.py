"""Tests for dual-machine target resolution."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_resolve_target_accepts_rytm_aliases() -> None:
    from rytm_randomizer.dual_machine.targets import resolve_target_devices

    for alias in ("rytm", "rytm-only"):
        devices = resolve_target_devices(alias)
        assert tuple(devices) == ("analog_rytm_mk2",)


def test_resolve_target_accepts_a4_aliases() -> None:
    from rytm_randomizer.dual_machine.targets import resolve_target_devices

    for alias in ("a4", "a4-only"):
        devices = resolve_target_devices(alias)
        assert tuple(devices) == ("analog_four_mk2",)


def test_resolve_target_accepts_both_alias() -> None:
    from rytm_randomizer.dual_machine.targets import resolve_target_devices

    devices = resolve_target_devices("both")

    assert tuple(devices) == ("analog_rytm_mk2", "analog_four_mk2")


def test_resolve_target_rejects_unknown_alias() -> None:
    from rytm_randomizer.dual_machine.targets import resolve_target_devices

    with pytest.raises(ValueError, match="unknown target"):
        resolve_target_devices("octatrack")
