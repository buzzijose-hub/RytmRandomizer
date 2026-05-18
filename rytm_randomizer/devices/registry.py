"""In-memory device registry (WS-S5).

Effectively a singleton-keyed-by-device-id pattern: every concrete
:class:`~rytm_randomizer.devices.base.Device` implementation calls
:func:`register_device` once at import time, and consumers look the
instance up by ``device_id`` via :func:`get_device` or iterate the full
set via :func:`all_devices`.

Per Gate 9 (subpackage by default) the registry lives inside the
``devices`` subpackage; per Gate 12 the underlying mapping is
``MappingProxyType``-wrapped on read so callers cannot mutate it.

Thread-safety: the registry is populated at import time (single-threaded
for the foreseeable future -- the project is a CLI). If the project ever
gains concurrent registration, wrap ``_DEVICES`` mutation in a lock.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from .base import Device

_DEVICES: dict[str, Device] = {}


def register_device(device: Device) -> None:
    """Register ``device`` under its ``device_id`` key.

    Re-registration with the same ``device_id`` is rejected to surface
    accidental collisions (two modules independently registering the same
    device family). If a test needs to override, it does so by importing
    ``_DEVICES`` directly and mutating the dict in a fixture.
    """

    key = device.device_id
    if key in _DEVICES:
        raise ValueError(
            f"Device {key!r} is already registered (existing: "
            f"{_DEVICES[key].display_name!r}). Use a distinct device_id "
            "or delete the prior registration in a test fixture."
        )
    _DEVICES[key] = device


def get_device(device_id: str) -> Device:
    """Return the registered ``Device`` for ``device_id``.

    Raises ``KeyError`` if no device has been registered under that id --
    consistent with stdlib mapping semantics.
    """

    return _DEVICES[device_id]


def all_devices() -> Mapping[str, Device]:
    """Return an immutable view of every registered device.

    Returned mapping is a ``MappingProxyType`` over the registry so
    callers cannot accidentally mutate the registry by writing through
    the returned object.
    """

    return MappingProxyType(_DEVICES)
