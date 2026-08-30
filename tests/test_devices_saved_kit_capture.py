"""Registered optional saved-KIT capture capability tests."""

from __future__ import annotations

import pytest

from conftest import (
    analog_four_saved_kit_frame,
    elektron_syx_message,
    rytm_real_layout_kit_payload,
)
from rytm_randomizer.devices import (
    SavedKitCaptureCapability,
    SavedKitCaptureFrame,
    resolve_saved_kit_capture_capability,
    saved_kit_capture,
)

pytestmark = pytest.mark.fast


@pytest.mark.parametrize("device_id", ["analog_rytm_mk2", "analog_four_mk2"])
def test_registered_device_exposes_optional_saved_kit_capture_capability(
    device_id: str,
) -> None:
    registered = resolve_saved_kit_capture_capability(device_id)

    assert registered.device.device_id == device_id
    assert registered.capability is registered.device
    assert isinstance(registered.capability, SavedKitCaptureCapability)


@pytest.mark.parametrize(
    ("device_id", "frame", "expected_slot"),
    [
        (
            "analog_rytm_mk2",
            elektron_syx_message(rytm_real_layout_kit_payload()),
            0,
        ),
        ("analog_four_mk2", analog_four_saved_kit_frame(), 0),
    ],
)
def test_registered_capture_capability_round_trips_canonical_frame(
    device_id: str,
    frame: bytes,
    expected_slot: int,
) -> None:
    capability = resolve_saved_kit_capture_capability(device_id).capability

    decoded = capability.decode_saved_kit_capture(frame)

    assert decoded.payload == frame[1:-1]
    assert decoded.snapshot_slot == expected_slot
    assert capability.encode_saved_kit_capture(decoded) == frame


@pytest.mark.parametrize("device_id", ["analog_rytm_mk2", "analog_four_mk2"])
def test_registered_capture_capability_rejects_unknown_decoded_shape(
    device_id: str,
) -> None:
    capability = resolve_saved_kit_capture_capability(device_id).capability

    with pytest.raises(TypeError, match="capture capability received an unsupported frame"):
        capability.encode_saved_kit_capture(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "frame",
    [
        b"",
        bytes((0x00, 0xF7)),
        bytes((0xF0, 0x00)),
    ],
)
def test_analog_four_capture_capability_rejects_invalid_sysex_framing(
    frame: bytes,
) -> None:
    capability = resolve_saved_kit_capture_capability("analog_four_mk2").capability

    with pytest.raises(ValueError, match="framing is invalid"):
        capability.decode_saved_kit_capture(frame)


def test_capture_capability_resolver_rejects_unknown_registry_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_device(_device_id: str) -> object:
        raise KeyError("missing")

    monkeypatch.setattr(saved_kit_capture, "get_device", missing_device)

    with pytest.raises(ValueError, match="unsupported capture device: missing"):
        resolve_saved_kit_capture_capability("missing")


def test_capture_capability_resolver_rejects_device_without_optional_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(saved_kit_capture, "get_device", lambda _device_id: object())

    with pytest.raises(TypeError, match="lacks saved-KIT capture capability"):
        resolve_saved_kit_capture_capability("no_capture")


def test_saved_kit_capture_frame_is_immutable() -> None:
    decoded = SavedKitCaptureFrame(
        payload=b"payload",
        snapshot_slot=0,
        header=b"header",
        unpacked=b"unpacked",
    )

    with pytest.raises(AttributeError):
        decoded.snapshot_slot = 1  # type: ignore[misc]
