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


def test_analog_four_device_renders_ready_plan_messages() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot

    a4 = get_device("analog_four_mk2")
    snapshot = AnalogFourKitSnapshot(slot=1, kit_name="A4", raw=b"", offsets_promoted=True)
    plan = a4.plan_mutation(snapshot, depth=1)

    assert plan.ready is True
    assert len(a4.to_mock_messages(plan)) == len(plan.events)
    assert len(tuple(a4.to_cc_messages(plan))) == len(plan.events)


def test_analog_four_ready_plan_uses_manual_backed_osc1_pwm_depth_mapping() -> None:
    from rytm_randomizer import data
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot

    a4 = get_device("analog_four_mk2")
    snapshot = AnalogFourKitSnapshot(slot=1, kit_name="A4", raw=b"", offsets_promoted=True)
    plan = a4.plan_mutation(snapshot, depth=1)
    mapping = data.ANALOG_FOUR_SYNTH_TRACK_CC["OSC1 PWM Depth"]

    assert {event.parameter for event in plan.events} == {"OSC1 PWM Depth"}
    assert {event.control for event in plan.events} == {mapping.cc_msb}


def test_analog_four_device_rejects_wrong_plan_type_for_mock_messages() -> None:
    from rytm_randomizer.devices import get_device

    a4 = get_device("analog_four_mk2")

    with pytest.raises(TypeError, match="AnalogFourMutationPlan"):
        a4.to_mock_messages(object())  # type: ignore[arg-type]


def test_analog_four_device_rejects_wrong_plan_type_for_cc_messages() -> None:
    from rytm_randomizer.devices import get_device

    a4 = get_device("analog_four_mk2")

    with pytest.raises(TypeError, match="AnalogFourMutationPlan"):
        tuple(a4.to_cc_messages(object()))  # type: ignore[arg-type]


def test_saved_kit_capability_resolver_rejects_incompatible_registry_device(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.devices import analog_four

    monkeypatch.setattr(analog_four.registry, "get_device", lambda _device_id: object())

    with pytest.raises(TypeError, match="lacks saved-kit rendering capability"):
        analog_four.get_analog_four_saved_kit_capability()
