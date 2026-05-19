"""Tests for registered AnalogFourDevice."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_analog_four_device_registers_with_device_registry() -> None:
    from rytm_randomizer.devices import all_devices, get_device

    assert "analog_four_mk2" in all_devices()
    assert get_device("analog_four_mk2").display_name == "Elektron Analog Four MKII"


def test_analog_four_device_satisfies_device_protocol() -> None:
    from rytm_randomizer.devices import Device, get_device

    assert isinstance(get_device("analog_four_mk2"), Device)


def test_analog_four_device_exposes_expected_identity_attributes() -> None:
    from rytm_randomizer.devices import get_device

    a4 = get_device("analog_four_mk2")

    assert a4.device_id == "analog_four_mk2"
    assert a4.default_midi_channel == 0
    assert a4.track_count == 4
    assert a4.sysex_manufacturer_id == bytes([0x00, 0x20, 0x3C])
    assert a4.report_header == "RytmRandomizer Analog Four MK2 Guarded Send"


def test_analog_four_device_convenience_methods_delegate_to_strategies() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlan

    raw = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4".ljust(16, b"\x00") + bytes(8)
    a4 = get_device("analog_four_mk2")

    snapshot = a4.decode_snapshot(raw, slot=1)
    plan = a4.plan_mutation(snapshot, depth=1)

    assert isinstance(plan, AnalogFourMutationPlan)
    assert plan.ready is False
    assert a4.to_mock_messages(plan) == []
    assert tuple(a4.to_cc_messages(plan)) == ()
