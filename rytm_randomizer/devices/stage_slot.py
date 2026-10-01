"""Optional live-stage slot capability resolved through the device registry.

A device that can fill a slot on the dual-machine stage declares it with a
``stage_slot`` attribute (see :mod:`rytm_randomizer.snapshot.stage_slots`). A
device without one -- the passive Digitakt families today -- is simply not a
stage device. The mandatory :class:`~rytm_randomizer.devices.base.Device`
protocol is unchanged, mirroring :mod:`rytm_randomizer.devices.saved_kit_capture`.

**The device is the source of truth.** ``cockpit/data/stage.py`` keeps a
static mirror (``STAGE_SLOT_BY_DEVICE_ID``) because that layer may not import
the registry; ``tests/architecture/test_stage_slots_match_devices.py`` fails
whenever the mirror and these declarations disagree, and names every place to
update. Putting a device on stage is therefore: declare ``stage_slot`` on the
device, then follow the guard.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from ..snapshot.stage_slots import StageSlot
from .registry import all_devices, get_device


@runtime_checkable
class StageSlotCapability(Protocol):
    """A registered device that can fill one live-stage slot."""

    @property
    def stage_slot(self) -> StageSlot:
        """The stage slot this device fills."""

        ...


def stage_slot_for(device_id: str) -> StageSlot | None:
    """Return the slot ``device_id`` fills, or ``None`` if it is not a stage device.

    Raises :class:`ValueError` for an unregistered id: an unknown device is a
    caller bug, not a passive "no slot".
    """

    try:
        device = get_device(device_id)
    except KeyError as exc:
        raise ValueError(f"unregistered device: {device_id}") from exc
    if isinstance(device, StageSlotCapability):
        return device.stage_slot
    return None


def stage_slot_assignments() -> Mapping[str, StageSlot]:
    """Return ``{device_id: slot}`` for every registered stage device."""

    return MappingProxyType(
        {
            device_id: device.stage_slot
            for device_id, device in all_devices().items()
            if isinstance(device, StageSlotCapability)
        }
    )


__all__ = ["StageSlotCapability", "stage_slot_assignments", "stage_slot_for"]
