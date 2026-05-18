"""WS-S5 tests: Device protocol + registry + AnalogRytmDevice wrapper.

The Device protocol is the cross-machine boundary that PR #21's planned
Analog Four work collapses around (the 8 hand-rolled ``analog_four_*.py``
files become one module that registers an ``AnalogFourDevice`` against
this protocol).

Test naming: test_<unit>_<behavior>_when_<condition> per Gate 8.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# 1. Subpackage surface
# ---------------------------------------------------------------------------


def test_devices_subpackage_exports_expected_public_names() -> None:
    import rytm_randomizer.devices as devices

    expected = {"Device", "MidiOutbox", "all_devices", "get_device", "register_device"}
    assert expected.issubset(set(devices.__all__))


# ---------------------------------------------------------------------------
# 2. Device protocol
# ---------------------------------------------------------------------------


def test_device_protocol_is_runtime_checkable() -> None:
    """``isinstance(obj, Device)`` must not raise TypeError."""

    from rytm_randomizer.devices import Device, get_device

    rytm = get_device("analog_rytm_mk2")
    assert isinstance(rytm, Device)


def test_analog_rytm_device_satisfies_protocol_attributes() -> None:
    from rytm_randomizer.devices import get_device

    rytm = get_device("analog_rytm_mk2")

    assert rytm.device_id == "analog_rytm_mk2"
    assert rytm.display_name == "Elektron Analog Rytm MKII"
    assert rytm.default_midi_channel == 0
    assert rytm.track_count == 12
    assert rytm.sysex_manufacturer_id == bytes([0x00, 0x20, 0x3C])


# ---------------------------------------------------------------------------
# 3. Registry
# ---------------------------------------------------------------------------


def test_registry_contains_analog_rytm_out_of_the_box() -> None:
    """Importing the package registers AnalogRytmDevice as a side effect."""

    from rytm_randomizer.devices import all_devices, get_device

    assert "analog_rytm_mk2" in all_devices()
    assert get_device("analog_rytm_mk2") is not None


def test_get_device_raises_keyerror_on_unknown_id() -> None:
    from rytm_randomizer.devices import get_device

    with pytest.raises(KeyError):
        get_device("nonexistent_device_id")


def test_all_devices_returns_mapping_proxy() -> None:
    """``all_devices()`` must return an immutable view (Gate 12 spirit)."""

    from types import MappingProxyType

    from rytm_randomizer.devices import all_devices

    devices = all_devices()
    assert isinstance(devices, MappingProxyType)
    with pytest.raises(TypeError):
        devices["should_fail"] = None  # type: ignore[index]


def test_register_device_rejects_duplicate_id() -> None:
    """Re-registering the same device_id surfaces accidental collision."""

    from rytm_randomizer.devices import register_device
    from rytm_randomizer.devices.analog_rytm import AnalogRytmDevice

    with pytest.raises(ValueError, match="already registered"):
        register_device(AnalogRytmDevice())


# ---------------------------------------------------------------------------
# 4. AnalogRytmDevice stub methods (Protocol contract proof)
# ---------------------------------------------------------------------------


def test_analog_rytm_decode_snapshot_returns_internal_snapshot_shape() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.analog_rytm import _RytmSnapshot

    rytm = get_device("analog_rytm_mk2")
    snap = rytm.decode_snapshot(b"\x00\x20\x3c\xff", slot=3)

    assert isinstance(snap, _RytmSnapshot)
    assert snap.slot == 3
    assert snap.raw == b"\x00\x20\x3c\xff"


def test_analog_rytm_plan_mutation_returns_plan_with_depth() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.analog_rytm import _RytmMutationPlan

    rytm = get_device("analog_rytm_mk2")
    snap = rytm.decode_snapshot(b"\x00\x20\x3c", slot=1)
    plan = rytm.plan_mutation(snap, depth=2)

    assert isinstance(plan, _RytmMutationPlan)
    assert plan.depth == 2
    assert plan.snapshot is snap


def test_analog_rytm_plan_mutation_rejects_wrong_snapshot_type() -> None:
    from rytm_randomizer.devices import get_device

    rytm = get_device("analog_rytm_mk2")
    with pytest.raises(TypeError, match="_RytmSnapshot"):
        rytm.plan_mutation("not a snapshot", depth=1)


def test_analog_rytm_to_mock_messages_raises_not_implemented() -> None:
    """The renderer is not wired yet; raise loudly rather than silently emit ``[]``.

    Codex review P1: a silently-empty render is a false positive (tests
    could pass while the machine would not move). The live mutation path
    goes through ``engines/pad*.py``; this snapshot-facing renderer raises
    until the snapshot decoder is wired.
    """
    from rytm_randomizer.devices import get_device

    rytm = get_device("analog_rytm_mk2")
    snap = rytm.decode_snapshot(b"\x00", slot=0)
    plan = rytm.plan_mutation(snap, depth=1)

    with pytest.raises(NotImplementedError, match="snapshot-to-mock rendering"):
        rytm.to_mock_messages(plan)


def test_analog_rytm_to_cc_messages_raises_not_implemented() -> None:
    """The renderer is not wired yet; raise loudly rather than silently emit ``()``.

    Codex review P1: same rationale as ``to_mock_messages`` above.
    """
    from rytm_randomizer.devices import get_device

    rytm = get_device("analog_rytm_mk2")
    snap = rytm.decode_snapshot(b"\x00", slot=0)
    plan = rytm.plan_mutation(snap, depth=1)

    with pytest.raises(NotImplementedError, match="snapshot-to-CC rendering"):
        rytm.to_cc_messages(plan)


def test_analog_rytm_renderers_still_type_check_plan_first() -> None:
    """Wrong-type guards must precede the NotImplementedError raise."""
    from rytm_randomizer.devices import get_device

    rytm = get_device("analog_rytm_mk2")
    with pytest.raises(TypeError, match="_RytmMutationPlan"):
        rytm.to_mock_messages("not a plan")
    with pytest.raises(TypeError, match="_RytmMutationPlan"):
        rytm.to_cc_messages("not a plan")


# ---------------------------------------------------------------------------
# 5. PR #21 forward-compat: a hand-written stub Device satisfies the Protocol
# ---------------------------------------------------------------------------


def test_arbitrary_compliant_device_class_satisfies_protocol() -> None:
    """A hand-rolled Device implementation must satisfy isinstance(...).

    This is the PR #21 acceptance test in miniature: codex's
    ``AnalogFourDevice`` will look like this stub, just with real bodies.
    """

    from rytm_randomizer.devices import Device

    class _StubAnalogFourDevice:
        device_id = "stub_a4"
        display_name = "Stub Analog Four"
        default_midi_channel = 1
        track_count = 4  # A4 has 4 tracks vs. Rytm's 12 pads
        sysex_manufacturer_id = bytes([0x00, 0x20, 0x3C])

        def decode_snapshot(self, raw, slot):
            return ("stub", raw, slot)

        def plan_mutation(self, snapshot, depth):
            return ("plan", snapshot, depth)

        def to_mock_messages(self, plan):
            return []

        def to_cc_messages(self, plan):
            return ()

    assert isinstance(_StubAnalogFourDevice(), Device)
