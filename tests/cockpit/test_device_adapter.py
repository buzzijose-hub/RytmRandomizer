"""Tests for ``rytm_randomizer.cockpit.device.adapter`` — the Protocol contract.

The ``DeviceAdapter`` Protocol is the cockpit's only handle on hardware.
Both ``MockDeviceAdapter`` and ``RealMidiDeviceAdapter`` must satisfy it via
``isinstance(adapter, DeviceAdapter)`` (the Protocol is ``@runtime_checkable``).

These tests intentionally exercise only the Protocol surface — the per-
adapter behavior tests live in ``test_device_mock.py`` and ``test_device_real.py``.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rytm_randomizer.cockpit.data import PadState, Snapshot
from rytm_randomizer.cockpit.device import (
    DeviceAdapter,
    MockDeviceAdapter,
    RealMidiDeviceAdapter,
)

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


class _FakeMidoProvider:
    """Minimal fake that duck-types ``MidoMidiPortProvider``.

    Used by adapter-conformance tests only — no ports opened, no ``mido``
    imported.
    """

    def list_output_names(self) -> tuple[str, ...]:
        return ()

    def open_output(self, port_name: str) -> object:  # pragma: no cover - unused here
        raise RuntimeError("not used in conformance tests")


# ---------------------------------------------------------------------------
# Protocol conformance: both adapters satisfy the runtime-checkable Protocol.
# ---------------------------------------------------------------------------


def test_mock_adapter_satisfies_device_adapter_protocol() -> None:
    adapter = MockDeviceAdapter(initial=_make_snapshot())

    assert isinstance(adapter, DeviceAdapter)


def test_real_midi_adapter_satisfies_device_adapter_protocol() -> None:
    adapter = RealMidiDeviceAdapter(midi_provider=_FakeMidoProvider())

    assert isinstance(adapter, DeviceAdapter)


# ---------------------------------------------------------------------------
# Surface stability — the Protocol exposes exactly the four documented
# members; the package re-export is the only public seam.
# ---------------------------------------------------------------------------


def test_device_adapter_protocol_exposes_documented_surface() -> None:
    """The Protocol carries the four members downstream code consumes."""

    expected = {"is_armed", "capture_snapshot", "apply", "commit_kit"}
    actual = {name for name in dir(DeviceAdapter) if not name.startswith("_")}
    assert expected <= actual


def test_device_package_re_exports_three_public_names() -> None:
    """``__all__`` is stable so callers can ``from ... import DeviceAdapter``."""

    import rytm_randomizer.cockpit.device as device_pkg

    assert set(device_pkg.__all__) == {
        "DeviceAdapter",
        "MockDeviceAdapter",
        "RealMidiDeviceAdapter",
    }


def test_mock_and_real_disagree_on_is_armed() -> None:
    """Sanity check: the two adapters expose different ``is_armed`` truthiness."""

    mock = MockDeviceAdapter(initial=_make_snapshot())
    real = RealMidiDeviceAdapter(midi_provider=_FakeMidoProvider())

    assert mock.is_armed is False
    assert real.is_armed is True


def test_a_bare_object_does_not_satisfy_device_adapter() -> None:
    """A bare object that lacks the four members fails the ``isinstance`` check."""

    assert not isinstance(object(), DeviceAdapter)
