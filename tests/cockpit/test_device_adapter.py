"""Tests for ``rytm_randomizer.cockpit.device.adapter`` — the Protocol contract.

The ``DeviceAdapter`` Protocol is how the cockpit models device state.
``MockDeviceAdapter`` — the only implementation — must satisfy it via
``isinstance(adapter, DeviceAdapter)`` (the Protocol is ``@runtime_checkable``).

There is deliberately no real-MIDI adapter: transmitting is the ArmedApply
seam's exclusive job, so an adapter never holds an output port.

These tests intentionally exercise only the Protocol surface — the
adapter behavior tests live in ``test_device_mock.py``.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rytm_randomizer.cockpit.data import PadState, Snapshot
from rytm_randomizer.cockpit.device import DeviceAdapter, MockDeviceAdapter

pytestmark = pytest.mark.fast


_FIXED_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


def _make_snapshot() -> Snapshot:
    return Snapshot(
        snapshot_id="01HXY5Q9PJM0123456789ABCD0",
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=(PadState(pad_id=1, machine="BD Hard", params={"tun": 28, "dec": 80}),),
        scene_slot=None,
        bpm=None,
    )


# ---------------------------------------------------------------------------
# Protocol conformance: both adapters satisfy the runtime-checkable Protocol.
# ---------------------------------------------------------------------------


def test_mock_adapter_satisfies_device_adapter_protocol() -> None:
    adapter = MockDeviceAdapter(initial=_make_snapshot())

    assert isinstance(adapter, DeviceAdapter)


# ---------------------------------------------------------------------------
# Surface stability — the Protocol exposes exactly the four documented
# members; the package re-export is the only public seam.
# ---------------------------------------------------------------------------


def test_device_adapter_protocol_exposes_documented_surface() -> None:
    """The Protocol carries the four members downstream code consumes."""

    expected = {"is_armed", "capture_snapshot", "apply", "apply_send_plan"}
    actual = {name for name in dir(DeviceAdapter) if not name.startswith("_")}
    assert expected <= actual


def test_device_adapter_protocol_has_no_persistent_write_member() -> None:
    """The adapter is a PASSIVE state projection — not a second transport.

    ``commit_kit`` was the Protocol's only persistent-write member. Its
    sole implementation was a mock log line, while the WS ``save``
    handler acked durable success on the strength of it. Removing it
    keeps the adapter's surface honest: nothing here reaches hardware,
    and nothing here promises persistence.
    """

    surface = {name for name in dir(DeviceAdapter) if not name.startswith("_")}
    assert "commit_kit" not in surface


def test_device_package_re_exports_two_public_names() -> None:
    """``__all__`` is stable so callers can ``from ... import DeviceAdapter``.

    ``RealMidiDeviceAdapter`` is deliberately absent: it was deleted once the
    ArmedApply seam became the cockpit's only output handle.
    """

    import rytm_randomizer.cockpit.device as device_pkg

    assert set(device_pkg.__all__) == {
        "DeviceAdapter",
        "MockDeviceAdapter",
    }


def test_the_adapter_is_never_armed() -> None:
    """An adapter models state, never a live output handle."""

    assert MockDeviceAdapter(initial=_make_snapshot()).is_armed is False


def test_a_bare_object_does_not_satisfy_device_adapter() -> None:
    """A bare object that lacks the four members fails the ``isinstance`` check."""

    assert not isinstance(object(), DeviceAdapter)
