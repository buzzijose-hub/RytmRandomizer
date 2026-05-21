"""WS-S5 + Strategy: Device Protocol + registry + AnalogRytmDevice surface.

The Device protocol is the cross-machine boundary that every Elektron
device family routes through. ``AnalogRytmDevice`` composes the three
Strategy capabilities (``snapshot_decoder``, ``mutation_planner``,
``message_renderer``) from
:mod:`rytm_randomizer.devices.strategies` into one registered Device.

This file holds the **device-surface** tests (Protocol conformance,
registry semantics, convenience-method delegation). The bodies of the
strategies themselves are tested in dedicated files
(``test_devices_strategies_*``).

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

    expected = {
        "Device",
        "MidiOutbox",
        "MessageRenderer",
        "MutationPlanner",
        "SnapshotDecoder",
        "all_devices",
        "get_device",
        "register_device",
    }
    assert expected.issubset(set(devices.__all__))


# ---------------------------------------------------------------------------
# 2. Device protocol (including Strategy capability attributes)
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
    assert rytm.report_header == "RytmRandomizer Analog Rytm MK2 Guarded Send"


def test_analog_rytm_device_exposes_strategy_attributes() -> None:
    """The four capability strategies must be live attributes on the device."""

    from rytm_randomizer.devices import (
        MessageRenderer,
        MutationPlanner,
        SnapshotDecoder,
        get_device,
    )

    rytm = get_device("analog_rytm_mk2")

    assert isinstance(rytm.snapshot_decoder, SnapshotDecoder)
    assert isinstance(rytm.mutation_planner, MutationPlanner)
    assert isinstance(rytm.message_renderer, MessageRenderer)


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
# 4. WS-S5 convenience methods now delegate to strategies and produce real
#    output. The decode_snapshot / plan_mutation / render-method contract is
#    asserted here at the device surface; strategy-body behavior lives in
#    the strategy-specific test files.
# ---------------------------------------------------------------------------


def _valid_rytm_sysex() -> bytes:
    """Build a minimal Rytm SysEx body the decoder accepts.

    Layout: Elektron prefix (3) + Rytm kit-type byte (1) + 7-bit-stuffed
    payload of 7-data-byte groups. ``unpack_elektron_7bit`` rejects a lone
    trailing header byte (per the codex-P2 envelope fix), so we ship four
    full groups (header + 7 data bytes) = 32 wire bytes of payload, which
    unpack to 28 data bytes -- enough to carry the real-layout 16-NUL
    kit-name field at offset 8.
    """

    # 4 groups x (1 header + 7 data) = 32 wire bytes after the kit-type
    # byte. Headers all-zero -> high bit of every data byte clears -> the
    # unpacked payload is all NULs. read_ascii_name then sees a 16-byte
    # NUL kit-name field and returns "".
    payload = bytes([0x00] * 32)  # 4 zero-header groups of 7 NUL data bytes each.
    return bytes([0x00, 0x20, 0x3C, 0x07]) + payload


def test_decode_snapshot_delegates_to_strategy_and_returns_kit_snapshot() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import RytmKitSnapshot

    rytm = get_device("analog_rytm_mk2")
    snap = rytm.decode_snapshot(_valid_rytm_sysex(), slot=3)

    assert isinstance(snap, RytmKitSnapshot)
    assert snap.slot == 3


def test_plan_mutation_delegates_to_strategy_and_returns_mutation_plan() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import RytmKitSnapshot, RytmMutationPlan

    rytm = get_device("analog_rytm_mk2")
    snap = RytmKitSnapshot(slot=1, kit_name="", raw=b"", unpacked=b"")
    plan = rytm.plan_mutation(snap, depth=2)

    assert isinstance(plan, RytmMutationPlan)
    assert plan.depth == 2
    assert plan.snapshot is snap
    assert plan.ready is True
    assert len(plan.events) > 0


def test_to_mock_messages_renders_one_message_per_plan_event() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import RytmKitSnapshot
    from rytm_randomizer.mock_midi import MidiMessage

    rytm = get_device("analog_rytm_mk2")
    snap = RytmKitSnapshot(slot=0, kit_name="", raw=b"", unpacked=b"")
    plan = rytm.plan_mutation(snap, depth=1)

    messages = rytm.to_mock_messages(plan)

    assert len(messages) == len(plan.events)
    assert all(isinstance(m, MidiMessage) for m in messages)
    # Metadata mirrors plan event identity (pad / profile_key / parameter).
    assert messages[0].metadata["pad"] == plan.events[0].pad
    assert messages[0].metadata["parameter"] == plan.events[0].parameter


def test_to_cc_messages_renders_one_triple_per_plan_event() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import RytmKitSnapshot

    rytm = get_device("analog_rytm_mk2")
    snap = RytmKitSnapshot(slot=0, kit_name="", raw=b"", unpacked=b"")
    plan = rytm.plan_mutation(snap, depth=1)

    triples = tuple(rytm.to_cc_messages(plan))

    assert len(triples) == len(plan.events)
    for triple in triples:
        assert len(triple) == 3
        channel, control, value = triple
        assert 0 <= channel <= 15
        assert 0 <= control <= 127
        assert 0 <= value <= 127


def test_to_mock_messages_rejects_wrong_plan_type() -> None:
    from rytm_randomizer.devices import get_device

    rytm = get_device("analog_rytm_mk2")
    with pytest.raises(TypeError, match="RytmMutationPlan"):
        rytm.to_mock_messages("not a plan")


def test_to_cc_messages_rejects_wrong_plan_type() -> None:
    from rytm_randomizer.devices import get_device

    rytm = get_device("analog_rytm_mk2")
    with pytest.raises(TypeError, match="RytmMutationPlan"):
        rytm.to_cc_messages("not a plan")


# ---------------------------------------------------------------------------
# 5. PR #21 forward-compat: a hand-written stub Device satisfies the Protocol
#
# A hand-rolled stub now has to expose the four Strategy capability
# attributes too. This is the explicit-contract win of the Strategy
# pattern -- a future ``AnalogFourDevice`` must wire its own
# snapshot_decoder / mutation_planner / message_renderer, not omit them.
# ---------------------------------------------------------------------------


def test_arbitrary_compliant_device_class_satisfies_protocol() -> None:
    """A hand-rolled Device with all 8 attributes + 4 methods satisfies
    ``isinstance(stub, Device)``."""

    from rytm_randomizer.devices import Device

    class _StubSnapshotDecoder:
        def decode(self, raw, slot):
            return ("snap", raw, slot)

    class _StubMutationPlanner:
        def plan(self, snapshot, depth):
            return ("plan", snapshot, depth)

    class _StubMessageRenderer:
        def to_mock_message(self, event, plan):
            return ("mock", event)

        def to_cc_triple(self, event, plan):
            return (1, 2, 3)

    class _StubAnalogFourDevice:
        device_id = "stub_a4"
        display_name = "Stub Analog Four"
        default_midi_channel = 1
        track_count = 4
        sysex_manufacturer_id = bytes([0x00, 0x20, 0x3C])
        report_header = "Stub A4 Guarded Send"

        snapshot_decoder = _StubSnapshotDecoder()
        mutation_planner = _StubMutationPlanner()
        message_renderer = _StubMessageRenderer()

        def decode_snapshot(self, raw, slot):
            return self.snapshot_decoder.decode(raw, slot)

        def plan_mutation(self, snapshot, depth):
            return self.mutation_planner.plan(snapshot, depth)

        def to_mock_messages(self, plan):
            return []

        def to_cc_messages(self, plan):
            return ()

    assert isinstance(_StubAnalogFourDevice(), Device)


def test_stub_missing_strategy_attribute_fails_protocol_check() -> None:
    """If a device omits one of the Strategy attributes, isinstance fails.

    This is the regression bar: a contributor adding a new Device family
    cannot ship without all four capabilities. The architecture test
    ``tests/architecture/test_device_protocol_enforcement.py`` adds an
    on-disk-pattern check; this test confirms the runtime check.
    """

    from rytm_randomizer.devices import Device

    class _StubMissingRenderer:
        device_id = "stub_missing"
        display_name = "Stub Missing Renderer"
        default_midi_channel = 0
        track_count = 4
        sysex_manufacturer_id = bytes([0x00, 0x20, 0x3C])
        report_header = "Missing Renderer Stub"

        snapshot_decoder = object()
        mutation_planner = object()
        # message_renderer attribute deliberately omitted!

        def decode_snapshot(self, raw, slot):
            return None

        def plan_mutation(self, snapshot, depth):
            return None

        def to_mock_messages(self, plan):
            return []

        def to_cc_messages(self, plan):
            return ()

    assert not isinstance(_StubMissingRenderer(), Device)
