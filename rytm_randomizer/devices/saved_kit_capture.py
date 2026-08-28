"""Optional saved-KIT capture capability resolved through the device registry.

The mandatory :class:`~rytm_randomizer.devices.base.Device` protocol stays
small and stable.  Device families that can validate an input-only saved-KIT
SysEx frame opt into this structural capability instead.  Cockpit capture can
therefore use the registered device without importing a concrete family codec.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .base import Device
from .registry import get_device


@dataclass(frozen=True)
class SavedKitCaptureFrame:
    """Canonical decoded state needed to round-trip one saved-KIT frame."""

    payload: bytes
    snapshot_slot: int
    header: bytes
    unpacked: bytes


@runtime_checkable
class SavedKitCaptureCapability(Protocol):
    """Optional pure codec surface for complete saved-KIT capture frames."""

    def decode_saved_kit_capture(self, frame: bytes) -> SavedKitCaptureFrame:
        """Validate and decode one complete family-specific SysEx frame."""

        ...

    def encode_saved_kit_capture(self, decoded: SavedKitCaptureFrame) -> bytes:
        """Re-encode a decoded frame for canonical byte-stability checks."""

        ...


@dataclass(frozen=True)
class RegisteredSavedKitCaptureCapability:
    """A registry-backed Device paired with its optional capture capability."""

    device: Device
    capability: SavedKitCaptureCapability


def resolve_saved_kit_capture_capability(
    device_id: str,
) -> RegisteredSavedKitCaptureCapability:
    """Resolve ``device_id`` and fail closed when capture is unsupported."""

    try:
        device = get_device(device_id)
    except KeyError as exc:
        raise ValueError(f"unsupported capture device: {device_id}") from exc
    if not isinstance(device, SavedKitCaptureCapability):
        raise TypeError(f"registered device {device_id!r} lacks saved-KIT capture capability")
    return RegisteredSavedKitCaptureCapability(device=device, capability=device)


__all__ = [
    "RegisteredSavedKitCaptureCapability",
    "SavedKitCaptureCapability",
    "SavedKitCaptureFrame",
    "resolve_saved_kit_capture_capability",
]
