"""Fleet-wide conformance contract for every registered ``Device``.

Two jobs, both aimed at making the *next* device family cheap to add:

1. **One roster tripwire.** ``test_registered_device_roster`` is the single
   place that pins which devices exist. Adding a family updates exactly one
   assertion here -- not a scattering of ``device_count == N`` checks across
   the report-model tests.
2. **Contract, not census.** Every other test is parametrized over
   ``all_devices()`` and asserts invariants that must hold for *any* device.
   A new family inherits this whole suite for free, and a family that
   violates the seam fails here rather than in a downstream report test.

See ``.claude/rules/device-protocol-strategy.md`` for the seam these
invariants enforce.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast

from rytm_randomizer.devices import Device, all_devices
from rytm_randomizer.snapshot.decoder import SnapshotDecoder
from rytm_randomizer.snapshot.envelope import ELEKTRON_MFR_ID
from rytm_randomizer.snapshot.planner import MutationPlanner

#: The one place the device census is pinned. Adding a family updates this
#: tuple (and the README, per .claude/rules/readme-freshness.md) -- nothing
#: else in the test suite should hardcode the roster or its size.
EXPECTED_DEVICE_IDS: tuple[str, ...] = (
    "analog_rytm_mk2",
    "analog_four_mk2",
    "digitakt_mk1",
    "digitakt_ii",
)

_DEVICE_IDS = sorted(all_devices())


def _device(device_id: str) -> Device:
    return all_devices()[device_id]


def test_registered_device_roster() -> None:
    """The deliberate tripwire: exactly these families are registered."""

    assert sorted(all_devices()) == sorted(EXPECTED_DEVICE_IDS)


# ---------------------------------------------------------------------------
# Identity contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_device_id_is_its_registry_key(device_id: str) -> None:
    assert _device(device_id).device_id == device_id


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_device_id_is_lowercase_snake_case(device_id: str) -> None:
    assert device_id == device_id.lower()
    assert " " not in device_id
    assert "-" not in device_id


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_display_name_is_operator_readable(device_id: str) -> None:
    display_name = _device(device_id).display_name
    assert display_name.strip() == display_name
    assert display_name


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_every_device_is_elektron(device_id: str) -> None:
    assert _device(device_id).sysex_manufacturer_id == ELEKTRON_MFR_ID


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_track_count_is_a_positive_midi_addressable_count(device_id: str) -> None:
    track_count = _device(device_id).track_count
    assert isinstance(track_count, int)
    assert 1 <= track_count <= 16


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_default_midi_channel_is_zero_based_and_valid(device_id: str) -> None:
    channel = _device(device_id).default_midi_channel
    assert isinstance(channel, int)
    assert 0 <= channel <= 15


# ---------------------------------------------------------------------------
# Presentation contract (owned by the device, not by the reports layer)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_role_summary_is_declared_not_inferred(device_id: str) -> None:
    """Each device states its own role; consumers must not guess from tracks."""

    role_summary = _device(device_id).role_summary
    assert role_summary.strip() == role_summary
    assert role_summary


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_report_header_is_present(device_id: str) -> None:
    assert _device(device_id).report_header.strip()


def test_display_order_is_unique_across_the_fleet() -> None:
    """Unique orders keep operator-facing listings deterministic."""

    orders = [device.display_order for device in all_devices().values()]
    assert len(orders) == len(set(orders)), f"duplicate display_order values: {sorted(orders)}"


# ---------------------------------------------------------------------------
# Strategy-seam contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_device_satisfies_the_structural_protocol(device_id: str) -> None:
    assert isinstance(_device(device_id), Device)


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_capability_strategies_satisfy_their_protocols(device_id: str) -> None:
    device = _device(device_id)
    assert isinstance(device.snapshot_decoder, SnapshotDecoder)
    assert isinstance(device.mutation_planner, MutationPlanner)
    assert hasattr(device.message_renderer, "to_mock_message")
    assert hasattr(device.message_renderer, "to_cc_triple")


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_decoder_rejects_a_foreign_manufacturer_id(device_id: str) -> None:
    """No device may decode a payload that is not Elektron SysEx."""

    foreign = b"\x00\x00\x41" + bytes(64)
    with pytest.raises(ValueError):
        _device(device_id).decode_snapshot(foreign, 0)


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_decoder_rejects_a_negative_slot(device_id: str) -> None:
    with pytest.raises(ValueError):
        _device(device_id).decode_snapshot(ELEKTRON_MFR_ID + bytes(64), -1)


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_plan_mutation_rejects_a_foreign_snapshot_type(device_id: str) -> None:
    """A device never plans against another family's snapshot."""

    with pytest.raises((TypeError, ValueError)):
        _device(device_id).plan_mutation(object(), 1)


@pytest.mark.parametrize("device_id", _DEVICE_IDS)
def test_render_paths_reject_a_foreign_plan_type(device_id: str) -> None:
    device = _device(device_id)
    with pytest.raises((TypeError, ValueError)):
        device.to_mock_messages(object())
    with pytest.raises((TypeError, ValueError)):
        tuple(device.to_cc_messages(object()))
